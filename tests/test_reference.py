"""Tests for the reference scorer: AGENTS.md test vectors and invariants (claude-code)."""
import itertools
import random
from fractions import Fraction

import pytest

from castles.reference import game1_units, game2_units

U = 12


def u(points):
    v = Fraction(points) * U
    assert v.denominator == 1
    return int(v)


G1 = [
    ("G1-a", (20, 20, 20, 20, 20), (0, 0, 30, 35, 35), (3, 12)),
    ("G1-b", (0, 25, 25, 25, 25), (0, 25, 25, 50, 0), (8, 7)),
]

G2 = [
    ("G2-a", [(0, 0, 0, 50, 50), (0, 0, 34, 33, 33), (20, 20, 20, 20, 20), (1, 1, 1, 1, 96)],
     (4, 3, 3, 5), (4, 1, 1, 9)),
    ("G2-b", [(10, 30, 30, 30, 0), (10, 30, 30, 0, 30), (10, 30, 0, 30, 30), (70, 10, 10, 10, 0)],
     (Fraction(50, 12), Fraction(56, 12), Fraction(62, 12), 1), (2, 4, 9, 0)),
    ("G2-c", [(0, 0, 0, 50, 50), (0, 0, 0, 50, 50), (50, 50, 0, 0, 0), (0, 0, 100, 0, 0)],
     (Fraction(9, 2), Fraction(9, 2), 3, 3), (Fraction(13, 2), Fraction(13, 2), 1, 1)),
    ("G2-d", [(20, 20, 20, 20, 20)] * 4,
     (Fraction(15, 4),) * 4, (Fraction(15, 4),) * 4),
    ("G2-e", [(0, 0, 0, 0, 100), (100, 0, 0, 0, 0), (0, 100, 0, 0, 0), (0, 0, 100, 0, 0)],
     (6, 2, 3, 4), (9, 0, 2, 4)),
]


@pytest.mark.parametrize("vid,a,b,exp", G1, ids=[g[0] for g in G1])
def test_game1_vectors(vid, a, b, exp):
    assert game1_units(a, b) == (u(exp[0]), u(exp[1]))


@pytest.mark.parametrize("vid,group,pts,pay", G2, ids=[g[0] for g in G2])
def test_game2_vectors(vid, group, pts, pay):
    got_pts, got_pay = game2_units(group)
    assert got_pts == [u(p) for p in pts]
    assert got_pay == [u(p) for p in pay]


def rand_alloc(rng, round_to=1):
    # uniform composition of 100/round_to into 5 parts, scaled
    n = 100 // round_to
    bars = sorted(rng.sample(range(n + 4), 4))
    parts, prev = [], -1
    for b in bars + [n + 4]:
        parts.append(b - prev - 1)
        prev = b
    return tuple(p * round_to for p in parts)


def test_rand_alloc_valid():
    rng = random.Random(0)
    for _ in range(1000):
        x = rand_alloc(rng, rng.choice([1, 5, 10, 25]))
        assert sum(x) == 100 and min(x) >= 0


def test_invariants_random():
    rng = random.Random(12345)
    for _ in range(3000):
        r = rng.choice([1, 5, 10, 20, 25, 50])
        a, b = rand_alloc(rng, r), rand_alloc(rng, r)
        pa, pb = game1_units(a, b)
        assert pa + pb == 180
        assert game1_units(b, a) == (pb, pa)
        group = [rand_alloc(rng, rng.choice([1, 10, 25, 50])) for _ in range(4)]
        pts, pay = game2_units(group)
        assert sum(pts) == 180 and sum(pay) == 180
        for perm in itertools.permutations(range(4)):
            p2, y2 = game2_units([group[i] for i in perm])
            assert p2 == [pts[i] for i in perm]
            assert y2 == [pay[i] for i in perm]


def test_eight_points_is_sole_first():
    rng = random.Random(7)
    for _ in range(3000):
        group = [rand_alloc(rng, rng.choice([1, 10, 25])) for _ in range(4)]
        pts, pay = game2_units(group)
        for i in range(4):
            if pts[i] >= 8 * U:
                assert pay[i] == 9 * U


def test_identical_players_split_evenly():
    x = (10, 20, 30, 40, 0)
    pts, pay = game2_units([x] * 4)
    assert pts == [45] * 4 and pay == [45] * 4
    assert game1_units(x, x) == (90, 90)


def test_rejects_invalid():
    with pytest.raises(ValueError):
        game1_units((20, 20, 20, 20, 19), (20,) * 5)
    with pytest.raises(ValueError):
        game1_units((-1, 21, 20, 30, 30), (20,) * 5)
    with pytest.raises(ValueError):
        game2_units([(20,) * 5] * 3)
    with pytest.raises(ValueError):
        game1_units((20.5, 19.5, 20, 20, 20), (20,) * 5)
