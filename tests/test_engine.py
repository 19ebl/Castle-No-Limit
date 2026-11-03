import numpy as np
from castles.engine import score_g1_units, score_g2_units, g1_top, g1_table, g1_exact, g2_eval

def test_g1_vectors():
    assert tuple(score_g1_units([20]*5,[0,0,30,35,35])) == (36,144)
    assert tuple(score_g1_units([0,25,25,25,25],[0,25,25,50,0])) == (96,84)

def test_g2_vectors():
    cases = [
      ([[0,0,0,50,50],[0,0,34,33,33],[20]*5,[1,1,1,1,96]], [48,36,36,60],[48,12,12,108]),
      ([[10,30,30,30,0],[10,30,30,0,30],[10,30,0,30,30],[70,10,10,10,0]],[50,56,62,12],[24,48,108,0]),
      ([[0,0,0,50,50]]*2+[[50,50,0,0,0],[0,0,100,0,0]],[54,54,36,36],[78,78,12,12]),
      ([[20]*5]*4,[45]*4,[45]*4),
      ([[0,0,0,0,100],[100,0,0,0,0],[0,100,0,0,0],[0,0,100,0,0]],[72,24,36,48],[108,0,24,48])]
    for g,p,r in cases:
        a,b=score_g2_units(g)
        np.testing.assert_array_equal(a,p)
        np.testing.assert_array_equal(b,r)
        out=g2_eval(np.array(g[:1]),np.array([g[1:]]*2))
        assert out['mean'][0] == r[0]/12

def test_top_k_dp_matches_exhaustive_restricted_budget():
    rng=np.random.default_rng(5)
    m=rng.dirichlet(np.ones(101),size=5)
    xs,ss=g1_top(g1_table(m),5)
    np.testing.assert_allclose(g1_exact(xs,m),ss)
    assert np.all(xs.sum(axis=1)==100)
    assert len(np.unique(xs,axis=0))==5
    assert np.all(np.diff(ss)<=0)

def test_top100_dp_matches_all_4598126_allocations():
    """Independent full feasible-set check of the k-best DP recurrence."""
    from castles.engine import all_allocations
    rng = np.random.default_rng(1681)
    marginals = rng.dirichlet(np.ones(101), size=5)
    allocations = all_allocations()
    assert allocations.shape == (4_598_126, 5)
    scores = g1_exact(allocations, marginals)
    expected = np.sort(scores)[-100:][::-1]
    paths, actual = g1_top(g1_table(marginals), 100)
    np.testing.assert_allclose(actual, expected, atol=2e-14, rtol=0)
    np.testing.assert_allclose(g1_exact(paths, marginals), actual, atol=2e-14, rtol=0)
    assert len(np.unique(paths, axis=0)) == 100
