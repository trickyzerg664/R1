"""MetaX FSDP→vLLM 权重同步只在参数变化后执行。"""

import unittest
from unittest.mock import MagicMock, patch

from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

from verl.workers.sharding_manager.metax_vllm import MetaxFSDPVLLMShardingManager


class MetaxSyncCacheTest(unittest.TestCase):
    def setUp(self):
        self.module = MagicMock()
        self.module.state_dict.return_value = {'weight': object()}
        self.engine = MagicMock()
        self.engine._sleep_enabled = False
        self.state_type = patch.object(FSDP, 'set_state_dict_type')
        self.empty_cache = patch('verl.workers.sharding_manager.metax_vllm.torch.cuda.empty_cache')
        self.state_type.start()
        self.empty_cache.start()
        self.addCleanup(self.state_type.stop)
        self.addCleanup(self.empty_cache.stop)
        self.manager = MetaxFSDPVLLMShardingManager(self.module, self.engine)

    def test_unchanged_weights_sync_once_until_invalidated(self):
        with self.manager:
            pass
        with self.manager:
            pass
        self.assertEqual(self.module.state_dict.call_count, 1)
        self.assertEqual(self.engine.sync_model_weights.call_count, 1)
        self.manager.invalidate_weights()
        with self.manager:
            pass
        self.assertEqual(self.module.state_dict.call_count, 2)
        self.assertEqual(self.engine.sync_model_weights.call_count, 2)

    def test_sleep_or_failed_sync_requires_new_export(self):
        self.engine._sleep_enabled = True
        with self.manager:
            pass
        with self.manager:
            pass
        self.assertEqual(self.module.state_dict.call_count, 2)

        self.engine.sync_model_weights.side_effect = RuntimeError('sync failed')
        with self.assertRaisesRegex(RuntimeError, 'sync failed'):
            with self.manager:
                pass
        self.assertFalse(self.manager._weights_synced)


if __name__ == '__main__':
    unittest.main()
