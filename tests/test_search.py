import numpy as np
from types import SimpleNamespace
from castles.search import neighbors,concentration_candidates,prior_opponents,unique_allocations

def test_neighbors_conserve_budget_and_do_not_alias():
    x=np.array([0,10,20,30,40])
    hood=neighbors(x)
    assert np.all(hood>=0)
    assert np.all(hood.sum(axis=1)==100)
    assert not np.any(np.all(hood==x,axis=1))
    assert len(hood)==len(np.unique(hood,axis=0))

def test_concentration_candidates_legal():
    xs=concentration_candidates()
    assert len(xs)>100
    assert np.all(xs>=0)
    assert np.all(xs.sum(axis=1)==100)

def test_prior_groups_preserve_one_scenario_per_group():
    a=SimpleNamespace(g2=np.array([[100,0,0,0,0]],np.int16),w=np.array([1.]))
    b=SimpleNamespace(g2=np.array([[0,0,0,0,100]],np.int16),w=np.array([1.]))
    opps=prior_opponents(100,['a','b'],dict(a=a,b=b),6)
    assert np.array_equal(opps[:,0],opps[:,1])
    assert np.array_equal(opps[:,1],opps[:,2])
    assert (opps[:,0,0]==100).sum()==50

def test_top100_dp_against_complete_grid_oracle():
    from castles.engine import all_allocations,g1_top
    rng=np.random.default_rng(600)
    table=np.full((5,101),-1e6)
    table[:,::5]=rng.normal(size=(5,21))
    xs=all_allocations(5)
    scores=table[np.arange(5),xs].sum(axis=1)
    got_x,got_s=g1_top(table,100)
    np.testing.assert_allclose(got_s,np.sort(scores)[::-1][:100],rtol=0,atol=1e-12)
    assert np.all(got_x%5==0)
    assert len(np.unique(got_x,axis=0))==100
