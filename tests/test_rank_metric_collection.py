"""跨rank指标汇集回归；使用真实DataProto拼接路径，不创建GPU或Ray任务。"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from verl.protocol import DataProto
from verl.trainer.ppo.ray_trainer import reduce_metrics
from scripts.difficulty.stability_trial import training_summary

class RankMetricCollectionTests(unittest.TestCase):
    def test_eight_rank_collection_reaches_supervisor(self):
        """@brief 八rank各32微批必须汇集为256，原监督门限直接验收。
        @return 无。
        """
        outputs=[]
        # 每rank以不同token数和熵总量验证加权统计，避免乘八伪造全局指标。
        for rank in range(8):
            tokens=float(rank+1)
            metrics={'actor/observations/micro_batches_sum':[1.]*32,
                'actor/observations/model_tokens_sum':[tokens]*32,
                'actor/observations/entropy_sum':[tokens*(rank+1.)]*32,
                'actor/optimizer_step':[1.,1.], 'actor/optimizer_updates_per_rank':2.,
                'actor/total_loss':[.1]*32, 'actor/grad_norm':[2.,2.],
                'actor/kl_loss':[.2]*32}
            outputs.append(DataProto(meta_info={'metrics':metrics,'source':'rank0'}))
        reduced=reduce_metrics(DataProto.concat(outputs).meta_info['metrics'])
        self.assertEqual(reduced['actor/observations/micro_batches_sum'],256)
        self.assertEqual(reduced['actor/observations/model_tokens_sum'],1152)
        self.assertAlmostEqual(reduced['actor/entropy_token_weighted'],sum(i*i for i in range(1,9))/36)
        # 经真实监督读取入口验证，防止只检查孤立聚合函数。
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            (path/'metrics.jsonl').write_text(json.dumps(dict(event='train',step=1,metrics=reduced))+'\n')
            self.assertEqual(training_summary(path)['trained_step'],1)

    def test_all_rank_means_and_extremes_are_retained(self):
        """@brief 不同rank的旧均值、显式极值及计数均按原聚合器处理。
        @return 无。
        """
        outputs=[DataProto(meta_info={'metrics':{
            'actor/pg_loss':[float(rank)]*2,
            'actor/reference_delta_abs_max':[float(rank)],
            'actor/stability/valid_tokens_sum':[rank+1]}}) for rank in range(8)]
        reduced=reduce_metrics(DataProto.concat(outputs).meta_info['metrics'])
        self.assertEqual(reduced['actor/pg_loss'],3.5)
        self.assertEqual(reduced['actor/reference_delta_abs_max'],7)
        self.assertEqual(reduced['actor/stability/valid_tokens_sum'],36)

    def test_concat_does_not_mutate_worker_metrics(self):
        """@brief 拼接只建立新的指标容器，保留其他metadata首份兼容语义。
        @return 无。
        """
        outputs=[DataProto(meta_info={'metrics':{'loss':[1.,2.],'lr':.1},'tag':'first'}),
                 DataProto(meta_info={'metrics':{'loss':[3.],'lr':.2},'tag':'second'})]
        before=copy.deepcopy([d.meta_info for d in outputs])
        result=DataProto.concat(outputs)
        self.assertEqual(result.meta_info['metrics'],{'loss':[1.,2.,3.],'lr':[.1,.2]})
        self.assertEqual(result.meta_info['tag'],'first')
        self.assertEqual([d.meta_info for d in outputs],before)
        plain=DataProto.concat([DataProto(meta_info={'tag':'first'}),DataProto(meta_info={'tag':'second'})])
        self.assertEqual(plain.meta_info,{'tag':'first'})

    def test_missing_rank_metric_is_rejected(self):
        """@brief rank缺失metrics或字段不一致必须拒绝，禁止输出部分覆盖假象。
        @return 无。
        """
        # 字段缺失会使计数和均值的分母失真，必须明确失败。
        for second in ({}, {'metrics':{'other':[2.]}}):
            with self.assertRaises(ValueError):
                DataProto.concat([DataProto(meta_info={'metrics':{'loss':[1.]}}),
                                  DataProto(meta_info=second)])
