import math
import pytest
from search_sft.preflight import training_disk_budget


def test_checkpoint_and_export_are_separate_phases():
    budget=training_disk_budget(100,0)
    assert budget['checkpoint_bytes']==1200
    assert budget['saving_peak_bytes']==2400
    assert budget['export_peak_bytes']==1600
    assert budget['required_free_bytes']==2400


def test_qwen7b_budget_and_margin():
    n=7615616512
    budget=training_disk_budget(n,.1)
    assert budget['required_free_bytes']==math.ceil(24*n*1.1)
    assert 187 < budget['required_free_bytes']/2**30 < 188
    assert budget['required_free_bytes'] < 214*2**30


@pytest.mark.parametrize('n,margin',[(0,.1),(1,-.1),(1,float('nan'))])
def test_invalid_disk_inputs(n,margin):
    with pytest.raises(ValueError):training_disk_budget(n,margin)
