import json
import os
import warnings
from typing import List, Dict, Optional
import argparse
import threading

import faiss
import torch
import numpy as np
from transformers import AutoConfig, AutoTokenizer, AutoModel
from tqdm import tqdm
import datasets

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

def load_corpus(corpus_path: str):
    corpus = datasets.load_dataset(
        'json', 
        data_files=corpus_path,
        split="train",
        num_proc=4
    )
    return corpus

def read_jsonl(file_path):
    data = []
    with open(file_path, "r") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def load_docs(corpus, doc_idxs):
    results = [corpus[int(idx)] for idx in doc_idxs]
    return results

def load_model(model_path: str, use_fp16: bool = False):
    model_config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_path, trust_remote_code=True)
    model.eval()
    model.cuda()
    if use_fp16: 
        model = model.half()
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True, trust_remote_code=True)
    return model, tokenizer

def pooling(
    pooler_output,
    last_hidden_state,
    attention_mask = None,
    pooling_method = "mean"
):
    if pooling_method == "mean":
        last_hidden = last_hidden_state.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
    elif pooling_method == "cls":
        return last_hidden_state[:, 0]
    elif pooling_method == "pooler":
        return pooler_output
    else:
        raise NotImplementedError("Pooling method not implemented!")

class Encoder:
    def __init__(self, model_name, model_path, pooling_method, max_length, use_fp16):
        self.model_name = model_name
        self.model_path = model_path
        self.pooling_method = pooling_method
        self.max_length = max_length
        self.use_fp16 = use_fp16

        self.model, self.tokenizer = load_model(model_path=model_path, use_fp16=use_fp16)
        self.model.eval()

    @torch.no_grad()
    def encode(self, query_list: List[str], is_query=True) -> np.ndarray:
        """@brief 按既有E5前缀和池化规则编码，输入跟随模型设备。
        @param query_list 字符串或字符串列表。
        @param is_query 是否使用查询前缀；False时使用文档前缀。
        @return 连续FP32查询向量数组。
        @note 编码精度、归一化及截断规则沿用原实现。
        """
        # processing query for different encoders
        if isinstance(query_list, str):
            query_list = [query_list]

        if "e5" in self.model_name.lower():
            if is_query:
                query_list = [f"query: {query}" for query in query_list]
            else:
                query_list = [f"passage: {query}" for query in query_list]

        if "bge" in self.model_name.lower():
            if is_query:
                query_list = [f"Represent this sentence for searching relevant passages: {query}" for query in query_list]

        inputs = self.tokenizer(query_list,
                                max_length=self.max_length,
                                padding=True,
                                truncation=True,
                                return_tensors="pt"
                                )
        # 服务线程的默认设备可能不同；输入必须跟随已加载的E5模型设备。
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        if "T5" in type(self.model).__name__:
            # T5-based retrieval model
            decoder_input_ids = torch.zeros(
                (inputs['input_ids'].shape[0], 1), dtype=torch.long
            ).to(inputs['input_ids'].device)
            output = self.model(
                **inputs, decoder_input_ids=decoder_input_ids, return_dict=True
            )
            query_emb = output.last_hidden_state[:, 0, :]
        else:
            output = self.model(**inputs, return_dict=True)
            query_emb = pooling(output.pooler_output,
                                output.last_hidden_state,
                                inputs['attention_mask'],
                                self.pooling_method)
            if "dpr" not in self.model_name.lower():
                query_emb = torch.nn.functional.normalize(query_emb, dim=-1)

        query_emb = query_emb.detach().cpu().numpy()
        query_emb = query_emb.astype(np.float32, order="C")
        
        del inputs, output
        torch.cuda.empty_cache()

        return query_emb

class BaseRetriever:
    def __init__(self, config):
        self.config = config
        self.retrieval_method = config.retrieval_method
        self.topk = config.retrieval_topk
        
        self.index_path = config.index_path
        self.corpus_path = config.corpus_path

    def _search(self, query: str, num: int, return_score: bool):
        raise NotImplementedError

    def _batch_search(self, query_list: List[str], num: int, return_score: bool):
        raise NotImplementedError

    def search(self, query: str, num: int = None, return_score: bool = False):
        return self._search(query, num, return_score)
    
    def batch_search(self, query_list: List[str], num: int = None, return_score: bool = False):
        return self._batch_search(query_list, num, return_score)

class BM25Retriever(BaseRetriever):
    def __init__(self, config):
        super().__init__(config)
        from pyserini.search.lucene import LuceneSearcher
        self.searcher = LuceneSearcher(self.index_path)
        self.contain_doc = self._check_contain_doc()
        if not self.contain_doc:
            self.corpus = load_corpus(self.corpus_path)
        self.max_process_num = 8
    
    def _check_contain_doc(self):
        return self.searcher.doc(0).raw() is not None

    def _search(self, query: str, num: int = None, return_score: bool = False):
        if num is None:
            num = self.topk
        hits = self.searcher.search(query, num)
        if len(hits) < 1:
            if return_score:
                return [], []
            else:
                return []
        scores = [hit.score for hit in hits]
        if len(hits) < num:
            warnings.warn('Not enough documents retrieved!')
        else:
            hits = hits[:num]

        if self.contain_doc:
            all_contents = [
                json.loads(self.searcher.doc(hit.docid).raw())['contents'] 
                for hit in hits
            ]
            results = [
                {
                    'title': content.split("\n")[0].strip("\""),
                    'text': "\n".join(content.split("\n")[1:]),
                    'contents': content
                } 
                for content in all_contents
            ]
        else:
            results = load_docs(self.corpus, [hit.docid for hit in hits])

        if return_score:
            return results, scores
        else:
            return results

    def _batch_search(self, query_list: List[str], num: int = None, return_score: bool = False):
        results = []
        scores = []
        for query in query_list:
            item_result, item_score = self._search(query, num, True)
            results.append(item_result)
            scores.append(item_score)
        if return_score:
            return results, scores
        else:
            return results

class DenseRetriever(BaseRetriever):
    def __init__(self, config):
        """@brief 保留既有编码与文档读取，按显式后端选择CPU或GPU精确搜索。
        @param config 检索配置，GPU只支持FP32 FlatIP且设备/显存预算必须有效。
        @return 无。
        @raises ValueError 后端配置、索引类型或设备无效时抛出。
        @note GPU索引初始化后常驻，串行请求限制临时显存；默认CPU流程不变。
        """
        super().__init__(config)
        self.request_lock = threading.RLock()
        # 语料缓存先于CUDA初始化加载，避免缓存重建时fork继承GPU上下文。
        self.corpus = load_corpus(self.corpus_path)
        self.index = faiss.read_index(self.index_path)
        if config.faiss_gpu:
            co = faiss.GpuMultipleClonerOptions()
            co.useFloat16 = True
            co.shard = True
            self.index = faiss.index_cpu_to_all_gpus(self.index, co=co)

        if config.search_backend == "torch_gpu":
            if config.faiss_gpu:
                raise ValueError("torch_gpu cannot combine with faiss_gpu")
            from search_r1.search.gpu_flat_index import TorchGPUFlatIP
            devices = ([int(x) for x in config.gpu_device_ids.split(",")]
                       if config.gpu_device_ids else list(range(torch.cuda.device_count())))
            # 检索进程每卡最多申请18%显存；并发请求由锁串行，不挤占训练预算。
            if not 0 < config.gpu_memory_fraction < 1:
                raise ValueError("Invalid GPU memory fraction")
            for device in devices:
                torch.cuda.set_per_process_memory_fraction(config.gpu_memory_fraction, device)
            self.index = TorchGPUFlatIP(self.index, devices, config.gpu_chunk_rows, config.gpu_query_batch_size)
            # E5沿用单卡编码，放在最后一张可见卡；搜索分片仍覆盖全部设备。
            torch.cuda.set_device(devices[-1])
        elif config.search_backend != "cpu":
            raise ValueError("Unknown search backend")
        self.encoder = Encoder(
            model_name = self.retrieval_method,
            model_path = config.retrieval_model_path,
            pooling_method = config.retrieval_pooling_method,
            max_length = config.retrieval_query_max_length,
            use_fp16 = config.retrieval_use_fp16
        )
        self.topk = config.retrieval_topk
        self.batch_size = config.retrieval_batch_size

    def _search(self, query: str, num: int = None, return_score: bool = False):
        if num is None:
            num = self.topk
        query_emb = self.encoder.encode(query)
        scores, idxs = self.index.search(query_emb, k=num)
        idxs = idxs[0]
        scores = scores[0]
        results = load_docs(self.corpus, idxs)
        if return_score:
            return results, scores.tolist()
        else:
            return results

    def _batch_search(self, query_list: List[str], num: int = None, return_score: bool = False):
        if isinstance(query_list, str):
            query_list = [query_list]
        if num is None:
            num = self.topk
        
        results = []
        scores = []
        for start_idx in tqdm(range(0, len(query_list), self.batch_size), desc='Retrieval process: '):
            query_batch = query_list[start_idx:start_idx + self.batch_size]
            batch_emb = self.encoder.encode(query_batch)
            batch_scores, batch_idxs = self.index.search(batch_emb, k=num)
            batch_scores = batch_scores.tolist()
            batch_idxs = batch_idxs.tolist()

            # load_docs is not vectorized, but is a python list approach
            flat_idxs = sum(batch_idxs, [])
            batch_results = load_docs(self.corpus, flat_idxs)
            # chunk them back
            batch_results = [batch_results[i*num : (i+1)*num] for i in range(len(batch_idxs))]
            
            results.extend(batch_results)
            scores.extend(batch_scores)
            
            del batch_emb, batch_scores, batch_idxs, query_batch, flat_idxs, batch_results
            torch.cuda.empty_cache()
            
        if return_score:
            return results, scores
        else:
            return results

def get_retriever(config):
    if config.retrieval_method == "bm25":
        return BM25Retriever(config)
    else:
        return DenseRetriever(config)


#####################################
# FastAPI server below
#####################################

class Config:
    """
    Minimal config class (simulating your argparse) 
    Replace this with your real arguments or load them dynamically.
    """
    def __init__(
        self, 
        retrieval_method: str = "bm25", 
        retrieval_topk: int = 10,
        index_path: str = "./index/bm25",
        corpus_path: str = "./data/corpus.jsonl",
        dataset_path: str = "./data",
        data_split: str = "train",
        faiss_gpu: bool = True,
        retrieval_model_path: str = "./model",
        retrieval_pooling_method: str = "mean",
        retrieval_query_max_length: int = 256,
        retrieval_use_fp16: bool = False,
        retrieval_batch_size: int = 128,
        search_backend: str = "cpu",
        gpu_device_ids: str = "",
        gpu_chunk_rows: int = 262144,
        gpu_query_batch_size: int = 256,
        gpu_memory_fraction: float = 0.18
    ):
        """@brief 保存CPU或GPU检索配置，默认CPU行为兼容。
        @param retrieval_method 检索名称，e5等稠密编码或bm25。
        @param retrieval_topk 默认返回文档数，正整数。
        @param index_path 既有FAISS或BM25索引路径。
        @param corpus_path 原语料JSONL路径，文档顺序不得改变。
        @param dataset_path 兼容既有数据集目录字段。
        @param data_split 兼容既有数据集分割名称。
        @param faiss_gpu 旧FAISS GPU开关，不可与torch_gpu组合。
        @param retrieval_model_path 既有查询编码模型目录。
        @param retrieval_pooling_method 原池化方法，e5使用mean。
        @param retrieval_query_max_length 编码查询截断长度，正整数。
        @param retrieval_use_fp16 编码器是否半精度，搜索索引仍FP32。
        @param retrieval_batch_size 查询编码分批数，正整数，不减少总查询。
        @param search_backend cpu默认兼容，torch_gpu显式启用FP32分片。
        @param gpu_device_ids 可见GPU编号的逗号列表，空字符串使用全部可见卡。
        @param gpu_chunk_rows 每块向量数，正整数；验证选定262144。
        @param gpu_query_batch_size 每次GPU计算查询数，正整数；全部查询分批完成。
        @param gpu_memory_fraction 检索进程每卡PyTorch预算比例，必须在0和1之间。
        @return 无。
        """
        self.retrieval_method = retrieval_method
        self.retrieval_topk = retrieval_topk
        self.index_path = index_path
        self.corpus_path = corpus_path
        self.dataset_path = dataset_path
        self.data_split = data_split
        self.faiss_gpu = faiss_gpu
        self.retrieval_model_path = retrieval_model_path
        self.retrieval_pooling_method = retrieval_pooling_method
        self.retrieval_query_max_length = retrieval_query_max_length
        self.retrieval_use_fp16 = retrieval_use_fp16
        self.retrieval_batch_size = retrieval_batch_size
        # 新后端显式启用，默认CPU与原启动参数兼容。
        self.search_backend = search_backend
        self.gpu_device_ids = gpu_device_ids
        self.gpu_chunk_rows = gpu_chunk_rows
        self.gpu_query_batch_size = gpu_query_batch_size
        self.gpu_memory_fraction = gpu_memory_fraction


class QueryRequest(BaseModel):
    queries: List[str]
    topk: Optional[int] = None
    return_scores: bool = False


app = FastAPI()

def _retrieve_endpoint_unlocked(request: QueryRequest):
    """@brief 复用原批量检索、文档内容及可选分数响应。
    @param request 原queries/topk/return_scores请求对象。
    @return 原result格式字典。
    @note 不改变语料、E5向量或客户端响应结构。
    Endpoint that accepts queries and performs retrieval.
    Input format:
    {
      "queries": ["What is Python?", "Tell me about neural networks."],
      "topk": 3,
      "return_scores": true
    }
    """
    if not request.topk:
        request.topk = config.retrieval_topk  # fallback to default

    # Perform batch retrieval
    # 不请求分数时底层只返回文档列表；按请求分支解包，避免 HTTP 500。
    search_output = retriever.batch_search(
        query_list=request.queries,
        num=request.topk,
        return_score=request.return_scores
    )
    if request.return_scores:
        results, scores = search_output
    else:
        results, scores = search_output, None
    
    # Format response
    resp = []
    for i, single_result in enumerate(results):
        if request.return_scores:
            # If scores are returned, combine them with results
            combined = []
            for doc, score in zip(single_result, scores[i]):
                combined.append({"document": doc, "score": score})
            resp.append(combined)
        else:
            resp.append(single_result)
    return {"result": resp}


@app.post("/retrieve")
def retrieve_endpoint(request: QueryRequest):
    """@brief 复用原检索响应格式，GPU请求串行以限制编码和搜索临时显存。
    @param request 含queries、topk及return_scores的原请求对象。
    @return 原结构的result字典，不增加客户端必需字段。
    @note CPU默认后端仍直接执行；不缓存或减少查询。
    """
    if config.search_backend == "torch_gpu":
        with retriever.request_lock:
            return _retrieve_endpoint_unlocked(request)
    return _retrieve_endpoint_unlocked(request)


@app.get("/health")
def health_endpoint():
    """@brief 返回后端、完整索引数量和GPU进程显存统计供验收。
    @return 健康状态字典，CPU不触发GPU查询。
    @note 进程显存不等于驱动总占用，联合验证使用mx-smi。
    """
    result = {"ready": True, "search_backend": config.search_backend,
              "vectors": getattr(getattr(retriever, "index", None), "ntotal", None)}
    if config.search_backend == "torch_gpu":
        result["devices"] = retriever.index.devices
        result["chunk_rows"] = retriever.index.chunk_rows
        result["memory"] = [{"device": i,
                            "allocated_GiB": torch.cuda.memory_allocated(i)/1024**3,
                            "peak_allocated_GiB": torch.cuda.max_memory_allocated(i)/1024**3,
                            "reserved_GiB": torch.cuda.memory_reserved(i)/1024**3}
                           for i in retriever.index.devices]
    return result


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Launch the local faiss retriever.")
    parser.add_argument("--index_path", type=str, default="/home/peterjin/mnt/index/wiki-18/e5_Flat.index", help="Corpus indexing file.")
    parser.add_argument("--corpus_path", type=str, default="/home/peterjin/mnt/data/retrieval-corpus/wiki-18.jsonl", help="Local corpus file.")
    parser.add_argument("--topk", type=int, default=3, help="Number of retrieved passages for one query.")
    parser.add_argument("--retriever_name", type=str, default="e5", help="Name of the retriever model.")
    parser.add_argument("--retriever_model", type=str, default="intfloat/e5-base-v2", help="Path of the retriever model.")
    parser.add_argument('--faiss_gpu', action='store_true', help='Use GPU for computation')

    # CPU默认值兼容既有启动；GPU方案必须显式选择，端口支持先候选验证后切换。
    parser.add_argument("--search_backend", choices=["cpu", "torch_gpu"], default="cpu")
    parser.add_argument("--gpu_device_ids", default="")
    parser.add_argument("--gpu_chunk_rows", type=int, default=262144)
    parser.add_argument("--gpu_query_batch_size", type=int, default=256)
    parser.add_argument("--gpu_memory_fraction", type=float, default=0.18)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    
    # 1) Build a config (could also parse from arguments).
    #    In real usage, you'd parse your CLI arguments or environment variables.
    config = Config(
        retrieval_method = args.retriever_name,  # or "dense"
        index_path=args.index_path,
        corpus_path=args.corpus_path,
        retrieval_topk=args.topk,
        faiss_gpu=args.faiss_gpu,
        retrieval_model_path=args.retriever_model,
        retrieval_pooling_method="mean",
        retrieval_query_max_length=256,
        retrieval_use_fp16=True,
        retrieval_batch_size=512,
        search_backend=args.search_backend,
        gpu_device_ids=args.gpu_device_ids,
        gpu_chunk_rows=args.gpu_chunk_rows,
        gpu_query_batch_size=args.gpu_query_batch_size,
        gpu_memory_fraction=args.gpu_memory_fraction,
    )

    # 2) Instantiate a global retriever so it is loaded once and reused.
    retriever = get_retriever(config)
    
    # 3) Launch the server. By default, it listens on http://127.0.0.1:8000
    uvicorn.run(app, host=args.host, port=args.port)
