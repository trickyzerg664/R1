"""真实CPU更新核验所有微批的指标覆盖和总损失恒等式。"""
import copy
import unittest
import torch
import tests.test_stability_phase1 as fixtures
from verl.trainer.ppo.ray_trainer import reduce_metrics
from verl.experimental.stability.loss_observations import loss_observations

class ActorObservationTests(unittest.TestCase):
    def test_real_update_covers_all_micro_batches_and_loss(self):
        """@brief 实际更新入口四微批均有PG/熵/KL/总Loss，分量恒等式正确。
        @return 无。
        """
        torch.manual_seed(7); initial=copy.deepcopy(torch.nn.Linear(2,2).state_dict())
        helper=fixtures.DiagnosticTests()
        _,metrics,_=helper.run_actor_update(initial,False,False)
        # 与真实微批数核对，避免仅首尾值存在却遗漏中间微批。
        for key in ('actor/pg_loss','actor/entropy_loss','actor/kl_loss','actor/total_loss'):
            self.assertEqual(len(metrics[key]),4)
        for pg,h,kl,total in zip(metrics['actor/pg_loss'],metrics['actor/entropy_loss'],
                                metrics['actor/kl_loss'],metrics['actor/total_loss']):
            self.assertAlmostEqual(total,pg-.001*h+.001*kl,places=6)
        reduced=reduce_metrics(metrics)
        self.assertEqual(reduced['actor/observations/micro_batches_sum'],4)
        self.assertEqual(reduced['actor/observations/model_tokens_sum'],8)

    def test_token_weighted_entropy_excludes_environment(self):
        """@brief 长短微批按真实token加权，环境大熵不进入观察统计。
        @return 无。
        """
        metrics={}
        # 两个有效token熵1与一个有效token熵4的全局均值为2，不能平均成2.5。
        for values,mask in (([[1.,1.,999.]],[ [1,1,0] ]),([[4.,999.,999.]],[[1,0,0]])):
            item=loss_observations(torch.tensor(1.),
                                   torch.tensor(values),torch.tensor(mask))
            for key,value in item.items():metrics.setdefault(key,[]).append(value)
        reduced=reduce_metrics(metrics)
        self.assertEqual(reduced['actor/entropy_token_weighted'],2.)
        self.assertEqual(reduced['actor/observations/model_tokens_sum'],3)

    def test_observations_detach_without_parameter_gradients(self):
        """@brief 展示统计不保留计算图或写梯度，输入掩码保持原值。
        @return 无。
        """
        entropy=torch.tensor([[2.,3.]],requires_grad=True);mask=torch.tensor([[1,0]])
        output=loss_observations(entropy.sum(),entropy,mask)
        self.assertTrue(all(not torch.is_tensor(v) for v in output.values()))
        self.assertIsNone(entropy.grad);self.assertEqual(mask.tolist(),[[1,0]])
