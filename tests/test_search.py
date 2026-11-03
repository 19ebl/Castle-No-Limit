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

def _validation_fixture():
    x=np.array([[20,20,20,20,20],[0,0,0,50,50]],np.int16)
    p=SimpleNamespace(g1=x[:1],g2=x[:1],w=np.array([1.]),seed=1)
    return dict(named=p,prior=p,holdout=p),dict(finalists=x.tolist()),dict(finalists=x.tolist(),candidates=x.tolist())

def test_validation_pipeline_deterministic_known_winner(tmp_path):
    from castles.search import validate_finalists
    populations,g1,g2=_validation_fixture()
    r=validate_finalists(populations,['named'],['prior'],['holdout'],g1,g2,
                          output=tmp_path/'validation.json',n=16)
    np.testing.assert_allclose(r['g2_prior_mean'],[3.75,9])
    assert r['decision']['g2_index']==1
    assert r['decision']['g1_index']==1
    assert all(np.all(c['pass_3se']) for c in r['g1_crosschecks'].values())
    assert len(r['named_regret_benchmark']['candidates'])==2

def test_validation_deterministic_mismatch_fails_zero_se(tmp_path,monkeypatch):
    import castles.search as search
    original=search.g1_exact
    monkeypatch.setattr(search,'g1_exact',lambda x,m:original(x,m)+.01)
    populations,g1,g2=_validation_fixture()
    r=search.validate_finalists(populations,['named'],['prior'],['holdout'],g1,g2,
                                output=tmp_path/'validation.json',n=16)
    assert not any(np.any(c['pass_3se']) for c in r['g1_crosschecks'].values())
    assert all(np.all(np.isinf(c['z'])) for c in r['g1_crosschecks'].values())

def test_promotion_preserves_historically_strong_candidates():
    from castles.search import promote_local_history
    endpoint=[1,0,48,51,0]
    earlier=[0,0,48,52,0]
    old=[0,0,50,50,0]
    runner=[0,0,35,0,65]
    candidates=promote_local_history([endpoint],[dict(old=old,new=earlier)],
                                     [dict(leader=earlier,runner_up=runner)])
    for x in (endpoint,earlier,old,runner):assert np.any(np.all(candidates==x,axis=1))
    assert len(candidates)==4
