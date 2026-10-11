"""监督入口CPU核验：默认只检查、冻结失败、日志完整性与精准进程身份。"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import scripts.difficulty.stability_trial as trial

class TrialSupervisorTests(unittest.TestCase):
    def test_complete_rows_only(self):
        """@brief 未换行尾部不作为训练或评价完成记录。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'log';path.write_text('{"step":1}\n{"step":')
            self.assertEqual(trial.rows(path),[dict(step=1)])

    def test_owned_processes_exact_environment_and_start_identity(self):
        """@brief 仅完整匹配本阶段Ray环境，其他任务和检索环境不选入。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for pid,value in ((991001,'/tmp/ours'),(991002,'/tmp/ours-other'),(991003,'/tmp/retriever')):
                entry=root/str(pid);entry.mkdir()
                entry.joinpath('environ').write_bytes(('RAY_TMPDIR='+value+'\0TOKEN=hidden\0').encode())
                entry.joinpath('stat').write_text(str(pid)+' (ray worker name) '+' '.join(['0']*19+['12345']+['0']*5))
            self.assertEqual(trial.owned_processes('/tmp/ours',root),[(991001,'12345')])

    def test_default_check_does_not_spawn_gpu(self):
        """@brief 未指定launch时只核验冻结文件，不创建训练进程。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);(run/'plan.json').write_text('{}')
            with patch('sys.argv',['trial','--run-directory',tmp]),patch.object(trial,'verify'),\
                 patch.object(trial.subprocess,'Popen',side_effect=AssertionError('GPU spawn')):
                trial.main()

    def test_phase_overrides_inherited_ray_environment(self):
        """@brief 原配置已有RAY_TMPDIR时仍能正确创建独占阶段环境，并移除外部Ray地址。
        @return 无。
        """
        import os
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);phase=dict(name='probe',kind='eval',directory=str(run/'probe'),argv=['unused'])
            plan=dict(repository=tmp,ray_base='/tmp/unique',environment={'RAY_TMPDIR':'/tmp/old','RAY_ADDRESS':'external'})
            child=__import__('unittest.mock',fromlist=['MagicMock']).MagicMock()
            child.pid=os.getpid();child.poll.return_value=0;child.wait.return_value=0
            with patch.object(trial,'verify'),patch.object(trial.subprocess,'Popen',return_value=child) as spawn,\
                 patch.object(trial,'evaluation_summary',return_value={'count':256}),patch.object(trial,'cleanup_owned'):
                result=trial.run_phase(run,phase,plan,__import__('time').time()+10)
            self.assertEqual(result['count'],256)
            self.assertEqual(spawn.call_args.kwargs['env']['RAY_TMPDIR'],'/tmp/unique-probe')
            self.assertNotIn('RAY_ADDRESS',spawn.call_args.kwargs['env'])

    def test_freeze_mismatch_fails(self):
        """@brief 代码/配置文件变更须在GPU启动前失败。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source';path.write_text('changed')
            with self.assertRaisesRegex(RuntimeError,'Frozen content'):
                trial.verify(dict(hashes={str(path):'wrong'},parent_verification='unused'))

    def test_training_summary_rejects_skip_or_partial_micro_coverage(self):
        """@brief 真正训练事件的跳过更新或微批缺失必须触发停止。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'metrics.jsonl'
            metrics={'actor/optimizer_step':1,'actor/optimizer_updates_per_rank':2,
                     'actor/observations/micro_batches_sum':256,'actor/total_loss':.1,
                     'actor/grad_norm':2.,'actor/entropy_token_weighted':1.,'actor/kl_loss':.2}
            path.write_text(json.dumps(dict(event='train',step=1,metrics=metrics))+'\n')
            self.assertEqual(trial.training_summary(root)['trained_step'],1)
            for change in ({'actor/optimizer_step':0},{'actor/observations/micro_batches_sum':128}):
                path.write_text(json.dumps(dict(event='train',step=1,metrics=dict(metrics,**change)))+'\n')
                with self.assertRaises(RuntimeError):trial.training_summary(root)

    def test_independent_eval_requires_unique_complete_zero_updates(self):
        """@brief 独立评价须完整唯一且没有训练事件。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'answers.jsonl').write_text(''.join(json.dumps(dict(question_id=str(i),reward=1.,extracted_answer='yes'))+'\n' for i in range(2)))
            result=trial.evaluation_summary(root,2)
            self.assertEqual(result['correct'],2);self.assertEqual(result['parameter_updates'],0)
            (root/'metrics.jsonl').write_text('{"event":"train"}\n')
            with self.assertRaisesRegex(RuntimeError,'performed training'):trial.evaluation_summary(root,2)

    def test_cached_parent_requires_frozen_raw_evidence(self):
        """@brief 父评价只允许复用冻结原始记录，缺失证据时拒绝。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cached=root/'old';cached.mkdir()
            plan=dict(verified_parent_evaluation=str(cached),hashes={},
                      phases=[dict(directory=str(root/'new'))])
            with patch.object(trial,'verify'), self.assertRaisesRegex(RuntimeError,'not frozen'):
                trial.parent_evaluation(root,plan,0)

    def test_cached_parent_rechecks_without_gpu_spawn(self):
        """@brief 完整冻结父评价重验后复用，不创建GPU任务或伪称新评分。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cached=root/'old';cached.mkdir()
            hashes={str(cached/name):'verified' for name in ('answers.jsonl','metrics.jsonl','process-audit.jsonl')}
            plan=dict(verified_parent_evaluation=str(cached),hashes=hashes,
                      phases=[dict(directory=str(root/'new'))])
            with patch.object(trial,'verify'), patch.object(trial,'evaluation_summary',return_value={'count':256}) as check, \
                 patch.object(trial,'run_phase',side_effect=AssertionError('GPU spawn')):
                result=trial.parent_evaluation(root,plan,0)
            check.assert_called_once_with(cached,256)
            self.assertEqual(result['count'],256)
            self.assertTrue((root/'new/reused-evaluation.json').exists())
