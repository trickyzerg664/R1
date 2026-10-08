"""C500兼容的常驻FP32分片内积索引；不改变语料、编码或距离定义。"""
from concurrent.futures import ThreadPoolExecutor
import threading
import numpy as np
import torch

def merge_topk(scores, ids, k):
    """
    @brief 合并局部候选，按内积降序返回全局前k名。
    @param scores 二维有限分数数组。
    @param ids 与scores同形状的全局文档编号数组。
    @param k 正整数，返回候选数不超过现有列数。
    @return 分数和编号两个二维数组。
    @raises ValueError 形状、分数或k无效时抛出。
    @note 并列分数按候选原顺序稳定处理；CPU/GPU浮点差异另行核对。
    """
    # 输入边界独立于GPU，便于CPU单测和服务错误定位。
    if scores.ndim!=2 or ids.shape!=scores.shape or not np.isfinite(scores).all() or k<1:
        raise ValueError('Invalid top-k candidates')
    pos=np.argsort(-scores,axis=1,kind='stable')[:,:k]
    return np.take_along_axis(scores,pos,1),np.take_along_axis(ids,pos,1)

class TorchGPUFlatIP:
    def __init__(self,cpu_index,devices,chunk_rows=262144,query_batch_size=256):
        """
        @brief 将原CPU FlatIP索引等分并常驻指定GPU，建立复用线程池。
        @param cpu_index 原faiss.IndexFlatIP对象，向量保持FP32。
        @param devices 不重复的可见GPU整数编号列表。
        @param chunk_rows 每块最大文档数，至少1。
        @param query_batch_size 单次搜索计算批量上限，至少1；不减少查询总量。
        @return 无。
        @raises ValueError 索引类型、设备或批量配置无效时抛出。
        @note 只在初始化复制索引；释放CPU索引由调用者负责。
        """
        import faiss
        # 拒绝悄悄切换距离或精度；设备范围和分片大小初始化时校验。
        if not isinstance(cpu_index,faiss.IndexFlatIP) or cpu_index.metric_type!=faiss.METRIC_INNER_PRODUCT:
            raise ValueError('GPU backend requires FP32 IndexFlatIP')
        if not devices or len(set(devices))!=len(devices) or chunk_rows<1 or query_batch_size<1:
            raise ValueError('Invalid GPU partition settings')
        if any(d<0 or d>=torch.cuda.device_count() for d in devices) or cpu_index.ntotal<len(devices):
            raise ValueError('GPU unavailable or too few index vectors')
        self.ntotal,self.d=cpu_index.ntotal,cpu_index.d
        self.devices,self.chunk_rows,self.query_batch_size=list(devices),chunk_rows,query_batch_size
        self.lock=threading.RLock()
        self.pool=ThreadPoolExecutor(max_workers=len(devices))
        self.shards,self.offsets=[],[]
        # 关闭TF32，沿用已验证的FP32搜索和262144行块大小。
        torch.backends.cuda.matmul.allow_tf32=False
        vectors=faiss.rev_swig_ptr(cpu_index.get_xb(),self.ntotal*self.d).reshape(self.ntotal,self.d)
        for rank,device in enumerate(devices):
            left,right=self.ntotal*rank//len(devices),self.ntotal*(rank+1)//len(devices)
            with torch.cuda.device(device):
                self.shards.append(torch.from_numpy(vectors[left:right]).to('cuda:%d'%device))
                torch.cuda.synchronize(device)
            self.offsets.append(left)
            print('GPU index shard ready',device,left,right,flush=True)

    def _search_shard(self,shard,query,offset,k):
        """
        @brief 在单设备分块计算内积并合并局部前k名。
        @param shard GPU上的FP32二维索引分片。
        @param query CPU上的连续FP32二维查询数组。
        @param offset 分片全局编号起点。
        @param k 正整数检索数量。
        @return CPU上的局部分数及全局编号数组。
        @note 逐块释放大分数矩阵，传回CPU时同步实际计算。
        """
        with torch.cuda.device(shard.device),torch.inference_mode():
            q=torch.from_numpy(query).to(shard.device)
            best_s=best_i=None
            # 每块仅保留前k名，再合并；完整扫描所有向量，不使用近似索引。
            for start in range(0,len(shard),self.chunk_rows):
                scores=q@shard[start:start+self.chunk_rows].T
                s,i=torch.topk(scores,min(k,scores.shape[1]),dim=1,sorted=True)
                del scores
                i+=offset+start
                if best_s is None:
                    best_s,best_i=s,i
                else:
                    merged_s=torch.cat([best_s,s],dim=1)
                    merged_i=torch.cat([best_i,i],dim=1)
                    best_s,pos=torch.topk(merged_s,min(k,merged_s.shape[1]),dim=1,sorted=True)
                    best_i=torch.gather(merged_i,1,pos)
            return best_s.cpu().numpy(),best_i.cpu().numpy()

    def search(self,queries,k=3):
        """
        @brief 搜索全部查询，八卡并发并在CPU合并全局前k名。
        @param queries 形状[查询数,d]的有限FP32数组。
        @param k 正整数且不超过完整索引大小。
        @return 形状[查询数,k]的FP32分数及int64编号数组。
        @raises ValueError 查询形状、有限性或k无效时抛出。
        @note 计算批量分块不改变查询总数；锁限制同时搜索的临时显存。
        """
        q=np.asarray(queries,dtype=np.float32,order='C')
        if q.ndim!=2 or q.shape[1]!=self.d or not np.isfinite(q).all() or not 1<=k<=self.ntotal:
            raise ValueError('Invalid GPU search query')
        # 空查询沿用批量接口，返回正确形状；不触发GPU计算。
        if not len(q):
            return np.empty((0,k),np.float32),np.empty((0,k),np.int64)
        all_s,all_i=[],[]
        with self.lock:
            for start in range(0,len(q),self.query_batch_size):
                part=q[start:start+self.query_batch_size]
                jobs=[self.pool.submit(self._search_shard,s,part,o,k) for s,o in zip(self.shards,self.offsets)]
                values=[job.result() for job in jobs]
                scores=np.concatenate([x[0] for x in values],axis=1)
                ids=np.concatenate([x[1] for x in values],axis=1)
                scores,ids=merge_topk(scores,ids,k)
                all_s.append(scores);all_i.append(ids)
        return np.concatenate(all_s),np.concatenate(all_i)

