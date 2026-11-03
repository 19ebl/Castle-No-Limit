"""Tests for the applicant pool model (claude-code).
Cheap archetypes run in CI; scenarios that need the level-k / equilibrium
libraries are skipped unless CASTLES_SLOW=1 (they build caches, ~1-2 minutes cold)."""
import os

import numpy as np
import pytest

from castles import populations as P


def _check(pop):
    assert pop.g1.shape == pop.g2.shape and pop.g1.shape[1] == 5
    assert len(pop.w) == len(pop.g1)
    assert np.isclose(pop.w.sum(), 1.0) and (pop.w > 0).all()
    for g in (pop.g1, pop.g2):
        assert g.dtype.kind == "i"
        assert (g >= 0).all() and (g.sum(axis=1) == 100).all()


def test_all_allocations_count():
    X = P.all_allocations()
    assert len(X) == 4_598_126
    assert (X.sum(axis=1) == 100).all() and (X >= 0).all()
    assert len(np.unique(X.astype(np.int64) @ (101 ** np.arange(5)))) == len(X)
    assert len(P.grid5()) == 10_626


def test_list_scenarios():
    assert len(P.list_scenarios("named")) >= 8
    assert "best_guess" in P.list_scenarios("named")
    assert len(P.list_scenarios("prior")) >= 200
    assert len(P.list_scenarios("holdout")) >= 1


@pytest.mark.parametrize("name", ["naive_heavy", "concentration_heavy"])
def test_cheap_named(name):
    pop = P.get_population(name, 3)
    _check(pop)
    again = P.build_population(name, 3, *P.NAMED[name])
    assert (again.g1 == pop.g1).all() and (again.g2 == pop.g2).all()
    other = P.build_population(name, 4, *P.NAMED[name])
    assert not (other.g1 == pop.g1).all()


def test_archetypes_have_variation():
    rng = np.random.default_rng(0)
    for fn in (P.arch_A, P.arch_B, P.arch_C, P.arch_E, P.arch_X_contrarian, P.arch_X_ai2):
        for game in (1, 2):
            x = fn(rng, 300, game, {"noise": 1.0, "round_prob": 0.5})
            assert (x.sum(axis=1) == 100).all() and (x >= 0).all()
            assert len(np.unique(x, axis=0)) > 20, fn.__name__


def test_reuse_share():
    pop = P.build_population("t", 1, {"A": 0.5, "E": 0.5}, {"reuse": 0.8})
    same = (pop.g1 == pop.g2).all(axis=1).mean()
    assert 0.7 < same < 0.95
    pop = P.build_population("t", 1, {"A": 0.5, "E": 0.5}, {"reuse": 0.2})
    assert (pop.g1 == pop.g2).all(axis=1).mean() < 0.4


def test_g2_payout_kernel_matches_reference():
    from castles.reference import game2_units
    rng = np.random.default_rng(5)
    pop = P.get_population("naive_heavy", 1)
    opps = P.sample_opps(pop.g2, pop.w, 300, rng)
    cands = np.array([[20, 20, 20, 20, 20], [0, 0, 0, 50, 50], [1, 1, 31, 31, 36]])
    got = P.g2_mean_payout(cands, opps)
    for c, x in enumerate(cands.tolist()):
        ref = np.mean([game2_units([x] + o)[1][0] for o in opps.tolist()]) / 12
        assert abs(got[c] - ref) < 1e-12


@pytest.mark.skipif(not os.environ.get("CASTLES_SLOW"), reason="set CASTLES_SLOW=1")
def test_all_scenarios_build():
    for kind in ("named", "holdout"):
        for name in P.list_scenarios(kind):
            _check(P.get_population(name, 1))
    for name in P.list_scenarios("prior")[:20]:
        _check(P.get_population(name, 1))
