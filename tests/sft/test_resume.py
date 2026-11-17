import json
from pathlib import Path
import torch
import torch.distributed as dist
import pytest
from search_sft.checkpoint import load,save,verify_signature


class CPUCheckpointEngine:
    """真实 CPU AdamW 与状态序列化；不冒充 DeepSpeed/GPU 验收。"""
    def __init__(self):
        self.model=torch.nn.Linear(3,1)
        self.optimizer=torch.optim.AdamW(self.model.parameters(),lr=.01)
        self.scheduler=torch.optim.lr_scheduler.StepLR(self.optimizer,step_size=1,gamma=.9)
    def step(self):
        self.optimizer.zero_grad();loss=self.model(torch.randn(2,3)).square().mean()
        loss.backward();self.optimizer.step();self.scheduler.step()
    def save_checkpoint(self,root,tag,client_state,save_latest=False):
        p=Path(root)/tag;p.mkdir()
        torch.save({'model':self.model.state_dict(),'optim':self.optimizer.state_dict(),'scheduler':self.scheduler.state_dict(),'client':client_state},p/'engine.pt')
        return True
    def load_checkpoint(self,root,tag):
        state=torch.load(Path(root)/tag/'engine.pt',weights_only=False)
        self.model.load_state_dict(state['model']);self.optimizer.load_state_dict(state['optim']);self.scheduler.load_state_dict(state['scheduler'])
        return str(Path(root)/tag),dict(state['client'],ds_version='engine_metadata')


def test_checkpoint_resume_matches_continuous_cpu_training(tmp_path):
    dist.init_process_group('gloo',init_method='file://'+str(tmp_path/'pg'),rank=0,world_size=1)
    try:
        torch.manual_seed(2);reference=CPUCheckpointEngine()
        for _ in range(4):reference.step()
        torch.manual_seed(2);interrupted=CPUCheckpointEngine()
        for _ in range(2):interrupted.step()
        signature={'data':'same','world_size':1}
        root=tmp_path/'checkpoints';save(interrupted,root,2,2,signature)
        resumed=CPUCheckpointEngine();state=load(resumed,root,signature)
        assert state['cursor']==2
        for _ in range(2):resumed.step()
        for a,b in zip(reference.model.parameters(),resumed.model.parameters()):torch.testing.assert_close(a,b,rtol=0,atol=0)
        assert reference.scheduler.state_dict()==resumed.scheduler.state_dict()
        save(resumed,root,4,4,signature)
        assert not (root/'step_00000002').exists() and (root/'step_00000004'/'complete.json').exists()
        with pytest.raises(ValueError,match='identity mismatch'):load(resumed,root,{'data':'different','world_size':1})
    finally:dist.destroy_process_group()
