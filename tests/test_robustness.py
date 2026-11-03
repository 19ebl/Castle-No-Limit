import numpy as np
import pytest
from castles.robustness import StressPopulation, combine_populations, _jitter_bank, _target_candidates


def fixture_pop(x,name):
    bank=np.asarray([x],dtype=np.int16)
    return StressPopulation(name,1,bank,bank,np.array([1.]))


def test_mixture_retains_applicant_weights_and_budget():
    a=fixture_pop([20]*5,"a")
    b=fixture_pop([0,0,0,50,50],"b")
    result=combine_populations([a,b],[.6,.4])
    assert np.array_equal(result.g1,[[20]*5,[0,0,0,50,50]])
    assert np.allclose(result.w,[.6,.4])
    assert np.isclose(result.w.sum(),1)
    with pytest.raises(ValueError):
        combine_populations([a,b],[-.2,1.2])


def test_counter_variation_valid_and_seeded():
    anchors=np.array([[1,1,1,46,51],[0,0,34,33,33]],dtype=np.int16)
    a=_jitter_bank(anchors,342)
    assert np.array_equal(a,_jitter_bank(anchors,342))
    assert np.all(a.sum(1)==100) and a.min()>=0
    assert len(a)>len(anchors)


def test_target_candidates_include_cheap_plus_one_counters():
    leader=np.array([0,0,34,33,33],dtype=np.int16)
    c=_target_candidates(leader)
    assert np.all(c.sum(1)==100) and c.min()>=0
    assert any(np.array_equal(x,[1,1,35,63,0]) for x in c)
    assert any(np.array_equal(x,leader) for x in c)
    assert len(c)>1000
