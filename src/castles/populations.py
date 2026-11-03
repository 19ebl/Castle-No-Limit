"""Applicant pool model: archetypes and the scenario registry (claude-code).

A scenario is a named, seeded population. Each row is an applicant type with a
Game 1 allocation, a Game 2 allocation and a weight. See PLAN.md Phase 1.

Archetypes (letters as in PLAN.md):
  A naive heuristics, B concentrators, C edge seekers, D level-k / cognitive
  hierarchy, E AI-assisted (chatbot answers), F game-theory literate
  (fictitious-play self-play, separate per game), G reuse (applied as a
  population-level share: some rows submit one allocation in both games).
  H adversarial populations live in robustness.py (Phase 4).

Every archetype has internal variation (noise moves, rounding habits). Costly
pieces (level-k best responses, fictitious play) are built once per library
seed and cached under results/cache/ (gitignored).

This module carries its own small scorers for the best responses it needs, so
it does not depend on engine.py; the engine is differential-tested separately.
"""
from __future__ import annotations

import functools
import hashlib
import os
from dataclasses import dataclass, field

import numpy as np

VALUES = np.array([1, 2, 3, 4, 5], dtype=np.int64)
TOTAL = 100
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "cache")
POP_VERSION = "v1"


@dataclass
class Population:
    name: str
    seed: int
    g1: np.ndarray  # (N, 5) int
    g2: np.ndarray  # (N, 5) int
    w: np.ndarray   # (N,) weights summing to 1
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# allocation helpers
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def all_allocations() -> np.ndarray:
    """All 4,598,126 allocations of 100 into 5 nonnegative parts, (M, 5) int16."""
    out = []
    for a in range(101):
        for b in range(101 - a):
            r = 100 - a - b
            c = np.arange(r + 1)
            for_c = []
            # d ranges 0..r-c ; e = r-c-d
            lens = r - c + 1
            cc = np.repeat(c, lens)
            starts = np.cumsum(lens) - lens
            d = np.arange(lens.sum()) - np.repeat(starts, lens)
            e = r - cc - d
            blk = np.empty((len(cc), 5), dtype=np.int16)
            blk[:, 0] = a
            blk[:, 1] = b
            blk[:, 2] = cc
            blk[:, 3] = d
            blk[:, 4] = e
            out.append(blk)
            del for_c
    X = np.concatenate(out)
    assert len(X) == 4_598_126
    return X


@functools.lru_cache(maxsize=1)
def grid5() -> np.ndarray:
    X = all_allocations()
    return X[(X % 5 == 0).all(axis=1)].astype(np.int64)


def fix_sum(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Clip to >= 0 and repair rows so each sums to 100 (adds/removes on random castles,
    favouring castles that already hold soldiers)."""
    x = np.maximum(np.asarray(x, dtype=np.int64), 0).copy()
    for i in range(len(x)):
        d = TOTAL - int(x[i].sum())
        while d != 0:
            if d > 0:
                p = x[i] + 1.0
                j = rng.choice(5, p=p / p.sum())
                x[i, j] += d
                d = 0
            else:
                nz = np.flatnonzero(x[i] > 0)
                p = x[i, nz].astype(float)
                j = nz[rng.choice(len(nz), p=p / p.sum())]
                take = min(-d, int(x[i, j]))
                x[i, j] -= take
                d += take
    return x


def humanize(rng: np.random.Generator, base: np.ndarray, noise: float, round_prob: float) -> np.ndarray:
    """Add human-style variation to rows of `base`:
    - Poisson(noise) moves of 1, 2, 3 or 5 soldiers between random castles;
    - with prob round_prob, round every castle to a multiple of 5 and repair the sum.
    """
    x = np.asarray(base, dtype=np.int64).copy()
    n = len(x)
    moves = rng.poisson(noise, size=n)
    for i in np.flatnonzero(moves):
        for _ in range(moves[i]):
            src = rng.integers(5)
            dst = rng.integers(5)
            k = int(rng.choice([1, 1, 2, 2, 3, 5]))
            k = min(k, int(x[i, src]))
            if src != dst and k > 0:
                x[i, src] -= k
                x[i, dst] += k
    r = rng.random(n) < round_prob
    if r.any():
        x[r] = fix_sum(np.round(x[r] / 5) * 5, rng)
        # rounding repair may leave non-multiples; snap the largest castle
    return fix_sum(x, rng)


def _pick(rng, bases, n, probs=None):
    bases = np.asarray(bases, dtype=np.int64)
    if probs is not None:
        probs = np.asarray(probs, float)
        probs = probs / probs.sum()
    idx = rng.choice(len(bases), size=n, p=probs)
    return bases[idx]


# ---------------------------------------------------------------------------
# A. naive heuristics
# ---------------------------------------------------------------------------

NAIVE_BASES = [
    ((20, 20, 20, 20, 20), 3.0),
    ((7, 13, 20, 27, 33), 2.5),   # value-proportional
    ((6, 13, 20, 27, 34), 1.0),
    ((7, 13, 20, 26, 34), 0.7),
    ((5, 15, 20, 25, 35), 0.8),
    ((5, 10, 20, 30, 35), 1.2),
    ((10, 15, 20, 25, 30), 1.2),
    ((0, 10, 20, 30, 40), 1.2),
    ((0, 0, 25, 35, 40), 1.0),    # skip cheap castles
    ((0, 0, 30, 30, 40), 0.7),
    ((0, 0, 20, 35, 45), 0.5),
    ((0, 0, 33, 33, 34), 0.6),
    ((10, 10, 20, 30, 30), 0.6),
    ((0, 20, 20, 30, 30), 0.5),
    ((0, 25, 25, 25, 25), 0.5),
    ((10, 20, 20, 20, 30), 0.4),
    ((15, 15, 20, 25, 25), 0.4),
]


def arch_A(rng, n, game, p):
    b, w = zip(*NAIVE_BASES)
    x = _pick(rng, b, n, w)
    return humanize(rng, x, p.get("noise", 1.0) * 0.6, p.get("round_prob", 0.5))


# ---------------------------------------------------------------------------
# B. concentrators
# ---------------------------------------------------------------------------

# target castle sets (0-based) with Game 1 / Game 2 weights; Game 2 favours 8+ points
CONC_SETS = [
    ((3, 4), 2.0, 3.0),        # 9 pts
    ((2, 4), 1.2, 2.0),        # 8 pts
    ((2, 3, 4), 2.5, 2.0),     # 12 pts
    ((1, 2, 4), 0.8, 0.8),     # 10 pts
    ((0, 3, 4), 0.5, 0.8),     # 10 pts
    ((1, 3, 4), 1.0, 1.2),     # 11 pts
    ((0, 1, 2, 3), 0.4, 0.3),  # 10 pts (abandon the 5)
    ((1, 2, 3), 0.5, 0.4),     # 9 pts
    ((2, 3), 0.3, 0.3),        # 7 pts
    ((4,), 0.1, 0.4),          # all-in on 5
    ((3, 4, 1), 0.0, 0.0),
]


def arch_B(rng, n, game, p):
    sets = [s for s, w1, w2 in CONC_SETS if (w1 if game == 1 else w2) > 0]
    ws = [(w1 if game == 1 else w2) for s, w1, w2 in CONC_SETS if (w1 if game == 1 else w2) > 0]
    pick = rng.choice(len(sets), size=n, p=np.array(ws) / sum(ws))
    x = np.zeros((n, 5), dtype=np.int64)
    for i, k in enumerate(pick):
        tgt = list(sets[k])
        # sometimes keep tiny forces on non-targets
        rest = 0
        if rng.random() < 0.35:
            for j in range(5):
                if j not in tgt:
                    t = int(rng.integers(1, 4))
                    x[i, j] = t
                    rest += t
        left = TOTAL - rest
        # near-even split over targets, slightly more on valuable ones sometimes
        wts = np.ones(len(tgt)) + (rng.random() < 0.4) * (np.array(tgt) * 0.05)
        share = np.floor(left * wts / wts.sum()).astype(int)
        share[np.argmax(np.array(tgt))] += left - share.sum()
        x[i, tgt] = share
    return humanize(rng, x, p.get("noise", 1.0) * 0.4, p.get("round_prob", 0.5) * 0.3)


# ---------------------------------------------------------------------------
# C. edge seekers
# ---------------------------------------------------------------------------

FOCAL = np.array([20, 21, 25, 26, 30, 31, 33, 34, 35, 36, 40, 50, 51])
EDGE_PATTERNS = [((4, 3, 2), 3.0), ((4, 3), 1.5), ((4, 2), 1.0), ((4, 3, 1), 1.0), ((3, 2, 1), 0.4), ((4, 3, 2, 1), 1.0)]


def arch_C(rng, n, game, p):
    pats, w = zip(*EDGE_PATTERNS)
    w = np.array(w) / sum(w)
    out = np.zeros((n, 5), dtype=np.int64)
    focal_beats = np.array([21, 22, 23, 26, 27, 28, 31, 32, 33, 34, 35, 36, 37, 38])
    for i in range(n):
        tgt = list(pats[rng.choice(len(pats), p=w)])
        for _ in range(20):
            vals = rng.choice(focal_beats, size=len(tgt))
            tiny = {j: int(rng.integers(1, 7)) if rng.random() < 0.8 else 0 for j in range(5) if j not in tgt}
            if vals.sum() + sum(tiny.values()) <= TOTAL:
                break
        else:
            vals = np.full(len(tgt), TOTAL // len(tgt))
            tiny = {}
        x = np.zeros(5, dtype=np.int64)
        x[tgt] = vals
        for j, t in tiny.items():
            x[j] = t
        left = TOTAL - x.sum()
        if left < 0:
            x = fix_sum(x[None], rng)[0]
        else:
            # leftovers go to the top target or are spread as +1s on cheap castles
            if rng.random() < 0.5:
                x[max(tgt)] += left
            else:
                for _ in range(left):
                    x[rng.integers(5)] += 1
        out[i] = x
    return humanize(rng, out, p.get("noise", 1.0) * 0.3, 0.0)


# ---------------------------------------------------------------------------
# E. AI-assisted (plausible chatbot answers, written from general knowledge)
# ---------------------------------------------------------------------------

AI_G1 = [
    ((7, 13, 20, 27, 33), 3.0), ((5, 10, 20, 30, 35), 2.0), ((0, 10, 20, 30, 40), 1.5),
    ((0, 0, 25, 35, 40), 1.2), ((2, 8, 20, 30, 40), 0.8), ((0, 15, 25, 30, 30), 0.8),
    ((10, 15, 20, 25, 30), 1.0), ((4, 12, 20, 28, 36), 0.8), ((1, 11, 21, 31, 36), 1.0),
    ((3, 7, 20, 30, 40), 0.6), ((0, 0, 33, 33, 34), 1.0), ((0, 5, 25, 32, 38), 0.6),
    ((6, 13, 20, 27, 34), 1.0), ((0, 12, 22, 30, 36), 0.6), ((2, 11, 21, 31, 35), 0.8),
    ((0, 10, 25, 30, 35), 0.8), ((1, 2, 27, 33, 37), 0.6), ((0, 0, 30, 35, 35), 0.8),
    ((2, 3, 25, 33, 37), 0.6), ((1, 1, 31, 31, 36), 0.6), ((3, 12, 21, 28, 36), 0.5),
    ((20, 20, 20, 20, 20), 0.5),
]
AI_G2 = [
    ((0, 0, 0, 50, 50), 2.0), ((0, 0, 34, 33, 33), 2.0), ((0, 0, 45, 0, 55), 1.0),
    ((0, 0, 0, 48, 52), 1.0), ((0, 0, 30, 35, 35), 1.5), ((0, 5, 30, 30, 35), 0.8),
    ((0, 0, 40, 0, 60), 0.6), ((0, 0, 0, 45, 55), 0.8), ((1, 1, 32, 32, 34), 1.0),
    ((0, 10, 0, 40, 50), 0.6), ((0, 0, 25, 35, 40), 1.0), ((5, 10, 20, 30, 35), 1.0),
    ((7, 13, 20, 27, 33), 1.2), ((2, 3, 30, 30, 35), 0.8), ((0, 20, 0, 40, 40), 0.5),
    ((1, 2, 31, 32, 34), 0.8), ((0, 0, 35, 30, 35), 0.6), ((0, 15, 25, 0, 60), 0.3),
    ((1, 1, 1, 48, 49), 0.6), ((0, 0, 30, 30, 40), 0.8), ((0, 1, 33, 0, 66), 0.3),
    ((0, 10, 20, 30, 40), 0.8),
]


def arch_E(rng, n, game, p):
    bases = AI_G1 if game == 1 else AI_G2
    b, w = zip(*bases)
    x = _pick(rng, b, n, w)
    # chatbot outputs are mostly verbatim; some users tweak a little
    return humanize(rng, x, p.get("noise", 1.0) * 0.3, 0.1)


# ---------------------------------------------------------------------------
# scorers used for best responses (independent of engine.py)
# ---------------------------------------------------------------------------

def g1_marginals_rows(rows: np.ndarray, w: np.ndarray) -> np.ndarray:
    m = np.zeros((5, 101))
    for j in range(5):
        m[j] = np.bincount(rows[:, j], weights=w, minlength=101)[:101]
    return m / m.sum(axis=1, keepdims=True)


def g1_scores_all(marg: np.ndarray) -> np.ndarray:
    """Expected Game 1 castle points of every allocation vs per-castle marginals."""
    X = all_allocations()
    cdf = np.cumsum(marg, axis=1)
    below = np.concatenate([np.zeros((5, 1)), cdf[:, :-1]], axis=1)
    tab = VALUES[:, None] * (below + 0.5 * marg)
    s = tab[0][X[:, 0]]
    for j in range(1, 5):
        s += tab[j][X[:, j]]
    return s


try:  # numba kernel for Game 2 payouts; numpy fallback below
    from numba import njit, prange

    @njit(parallel=True, cache=True)
    def _g2_kernel(cands, opps):
        C = cands.shape[0]
        n = opps.shape[0]
        cs = np.array([0, 108, 156, 180, 180, 180])
        out = np.zeros(C)
        for c in prange(C):
            acc = 0
            for g in range(n):
                t = np.zeros(4, dtype=np.int64)
                for j in range(5):
                    v12 = (j + 1) * 12
                    m = cands[c, j]
                    for k in range(3):
                        if opps[g, k, j] > m:
                            m = opps[g, k, j]
                    cnt = 0
                    if cands[c, j] == m:
                        cnt += 1
                    for k in range(3):
                        if opps[g, k, j] == m:
                            cnt += 1
                    sh = v12 // cnt
                    if cands[c, j] == m:
                        t[0] += sh
                    for k in range(3):
                        if opps[g, k, j] == m:
                            t[k + 1] += sh
                above = 0
                eq = 0
                for k in range(1, 4):
                    if t[k] > t[0]:
                        above += 1
                    elif t[k] == t[0]:
                        eq += 1
                acc += (cs[above + eq + 1] - cs[above]) // (eq + 1)
            out[c] = acc / n / 12.0
        return out

    HAVE_NUMBA = True
except Exception:  # pragma: no cover
    HAVE_NUMBA = False


def g2_mean_payout(cands: np.ndarray, opps: np.ndarray) -> np.ndarray:
    """Mean Game 2 payout (points) of each candidate against fixed opponent triples."""
    cands = np.ascontiguousarray(cands, dtype=np.int64)
    opps = np.ascontiguousarray(opps, dtype=np.int64)
    if HAVE_NUMBA:
        return _g2_kernel(cands, opps)
    cs = np.array([0, 108, 156, 180, 180, 180])
    out = np.empty(len(cands))
    v12 = VALUES * 12
    for c, x in enumerate(cands):
        g = np.concatenate([np.broadcast_to(x, (len(opps), 1, 5)), opps], axis=1)
        top = g.max(axis=1, keepdims=True)
        win = g == top
        pts = (win * (v12 // win.sum(axis=1, keepdims=True))).sum(axis=2)
        above = (pts[:, 1:] > pts[:, :1]).sum(axis=1)
        eq = (pts[:, 1:] == pts[:, :1]).sum(axis=1)
        out[c] = ((cs[above + eq + 1] - cs[above]) // (eq + 1)).mean() / 12.0
    return out


def sample_opps(rows: np.ndarray, w: np.ndarray, n: int, rng) -> np.ndarray:
    idx = rng.choice(len(rows), size=(n, 3), p=w / w.sum())
    return rows[idx]


def softmax_sample(rng, cands, scores, temp, n, top=5000):
    order = np.argsort(-scores)[:top]
    s = scores[order]
    p = np.exp((s - s[0]) / temp)
    p /= p.sum()
    return cands[order[rng.choice(len(order), size=n, p=p)]].astype(np.int64)


@functools.lru_cache(maxsize=1)
def g2_candidate_pool() -> np.ndarray:
    """Candidate set for Game 2 best responses: multiples-of-5 grid, plus +-1/2
    offsets of concentration plays."""
    base = [grid5()]
    extra = []
    for s in [(3, 4), (2, 4), (2, 3, 4), (1, 3, 4), (1, 2, 4), (0, 3, 4), (1, 2, 3), (0, 2, 4)]:
        for tiny in range(0, 4):
            left = 100 - tiny * (5 - len(s))
            q, r = divmod(left, len(s))
            for bump in range(-3, 4):
                x = np.full(5, tiny)
                x[list(s)] = q
                x[s[-1]] += r
                if len(s) >= 2:
                    x[s[0]] += bump
                    x[s[-1]] -= bump
                if (x >= 0).all() and x.sum() == 100:
                    extra.append(x)
    pool = np.unique(np.concatenate(base + [np.array(extra)]), axis=0)
    return pool.astype(np.int64)


# ---------------------------------------------------------------------------
# caching of costly libraries
# ---------------------------------------------------------------------------

def _cache_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    h = hashlib.sha1(f"{POP_VERSION}:{key}".encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{h}.npz")


def _cached(key, builder):
    path = _cache_path(key)
    if os.path.exists(path):
        with np.load(path) as z:
            return {k: z[k] for k in z.files}
    res = builder()
    np.savez_compressed(path, **res)
    return res


# ---------------------------------------------------------------------------
# D. level-k / cognitive hierarchy
# ---------------------------------------------------------------------------

LEVELK_MAX = 4


def levelk_library(tau: float, lib_seed: int, rows_per_level: int = 400,
                   temp1: float = 0.15, temp2: float = 0.15, g2_groups: int = 3000):
    """Rows for levels 0..LEVELK_MAX for each game. Level 0 is the naive mix (A);
    level k is a softmax best response to the Poisson(tau) mix of levels < k."""
    def build():
        rng = np.random.default_rng([lib_seed, int(tau * 100), 11])
        from math import exp, factorial
        pw = np.array([exp(-tau) * tau ** k / factorial(k) for k in range(LEVELK_MAX + 1)])
        res = {"pw": pw}
        for game in (1, 2):
            levels = [arch_A(rng, rows_per_level, game, {"noise": 1.0, "round_prob": 0.5})]
            for k in range(1, LEVELK_MAX + 1):
                lw = pw[:k] / pw[:k].sum()
                rows = np.concatenate(levels)
                w = np.concatenate([np.full(rows_per_level, lw[i] / rows_per_level) for i in range(k)])
                if game == 1:
                    sc = g1_scores_all(g1_marginals_rows(rows, w))
                    br = softmax_sample(rng, all_allocations(), sc, temp1, rows_per_level)
                else:
                    pool = g2_candidate_pool()
                    opps = sample_opps(rows, w, g2_groups, rng)
                    sc = g2_mean_payout(pool, opps)
                    br = softmax_sample(rng, pool, sc, temp2, rows_per_level, top=2000)
                levels.append(humanize(rng, br, 1.5, 0.0))
            res[f"g{game}"] = np.stack(levels)  # (L+1, rows, 5)
        return res
    return _cached(f"levelk:{tau}:{lib_seed}:{rows_per_level}:{temp1}:{temp2}:{g2_groups}", build)


def arch_D(rng, n, game, p, lib_seed):
    tau = p.get("tau", 1.5)
    lib = levelk_library(tau, lib_seed)
    L = lib[f"g{game}"]
    pw = lib["pw"] / lib["pw"].sum()
    lev = rng.choice(len(pw), size=n, p=pw)
    pick = rng.integers(0, L.shape[1], size=n)
    return L[lev, pick].astype(np.int64)


def arch_D_levels(rng, n, game, p, lib_seed):
    """Return (rows, level) so reuse can keep the same applicant's level in both games."""
    tau = p.get("tau", 1.5)
    lib = levelk_library(tau, lib_seed)
    pw = lib["pw"] / lib["pw"].sum()
    lev = rng.choice(len(pw), size=n, p=pw)
    return lev


# ---------------------------------------------------------------------------
# F. game-theory literate: fictitious play self-play
# ---------------------------------------------------------------------------

def equilibrium_library(lib_seed: int, iters1: int = 150, iters2: int = 40, g2_groups: int = 2500):
    """Approximate symmetric equilibria by smoothed fictitious play.
    Game 1: exact best responses over all allocations to the running mix.
    Game 2: Monte Carlo best responses over the Game 2 candidate pool."""
    def build():
        rng = np.random.default_rng([lib_seed, 22])
        X = all_allocations()
        # Game 1
        hist = [arch_A(rng, 50, 1, {"noise": 1.0, "round_prob": 0.5})]
        marg = g1_marginals_rows(hist[0], np.ones(len(hist[0])))
        n_seen = 1
        for it in range(iters1):
            sc = g1_scores_all(marg)
            br = softmax_sample(rng, X, sc, 0.02, 4, top=500)
            bm = g1_marginals_rows(br, np.ones(len(br)))
            n_seen += 1
            marg = marg + (bm - marg) / n_seen
            hist.append(br)
        g1rows = np.concatenate(hist[len(hist) // 3:])  # drop early transient
        # Game 2
        pool = g2_candidate_pool()
        hist2 = [arch_A(rng, 50, 2, {"noise": 1.0, "round_prob": 0.5})]
        for it in range(iters2):
            mix = np.concatenate(hist2)
            opps = sample_opps(mix, np.ones(len(mix)), g2_groups, rng)
            sc = g2_mean_payout(pool, opps)
            hist2.append(np.repeat(softmax_sample(rng, pool, sc, 0.05, 25, top=300), 2, axis=0))
        g2rows = np.concatenate(hist2[len(hist2) // 3:])
        return {"g1": g1rows, "g2": g2rows}
    return _cached(f"equilibrium:{lib_seed}:{iters1}:{iters2}:{g2_groups}", build)


def arch_F(rng, n, game, p, lib_seed):
    lib = equilibrium_library(lib_seed)
    rows = lib[f"g{game}"]
    x = rows[rng.integers(0, len(rows), size=n)].astype(np.int64)
    return humanize(rng, x, p.get("noise", 1.0) * 0.3, 0.0)


# ---------------------------------------------------------------------------
# holdout-only archetypes (never used during search)
# ---------------------------------------------------------------------------

HOLDOUT_CONTRARIAN = [
    ((15, 25, 0, 30, 30), 1.0), ((10, 30, 30, 0, 30), 1.0), ((12, 22, 32, 34, 0), 1.0),
    ((25, 25, 0, 0, 50), 0.8), ((3, 24, 3, 35, 35), 0.8), ((11, 21, 31, 2, 35), 0.8),
    ((30, 30, 40, 0, 0), 0.4), ((8, 16, 3, 36, 37), 0.8), ((4, 17, 27, 4, 48), 0.6),
]


def arch_X_contrarian(rng, n, game, p):
    """Holdout variant: applicants who deliberately abandon a high-value castle
    to win the cheap ones and two others."""
    b, w = zip(*HOLDOUT_CONTRARIAN)
    return humanize(rng, _pick(rng, b, n, w), 1.0, 0.2)


def arch_X_ai2(rng, n, game, p):
    """Holdout variant: a second chatbot generation that 'reasons about
    opponents' and shades the standard answers by +1 to +3 on castles 3 to 5."""
    bases = AI_G1 if game == 1 else AI_G2
    b, w = zip(*bases)
    x = _pick(rng, b, n, w).copy()
    for i in range(n):
        add = rng.integers(1, 4, size=3) * (x[i, 2:] > 0)
        x[i, 2:] += add
        need = int(add.sum())
        for j in (0, 1):
            take = min(need, int(x[i, j]))
            x[i, j] -= take
            need -= take
        if need:
            x[i, 2 + int(np.argmax(add))] -= need
    return humanize(rng, x, 0.4, 0.0)


# ---------------------------------------------------------------------------
# population assembly
# ---------------------------------------------------------------------------

ARCHES = ("A", "B", "C", "D", "E", "F")


def build_population(name: str, seed: int, weights: dict, params: dict | None = None,
                     rows_per_arch: int = 400, lib_seed: int = 1) -> Population:
    """weights: archetype letter -> weight (also 'XC' contrarian, 'XA' ai2 for holdout).
    params: noise, round_prob, tau, reuse (share of applicants submitting one
    allocation in both games)."""
    p = {"noise": 1.0, "round_prob": 0.5, "tau": 1.5, "reuse": 0.4}
    p.update(params or {})
    rng = np.random.default_rng([seed, int(hashlib.sha1(name.encode()).hexdigest()[:8], 16)])
    G1, G2, W, tags = [], [], [], []
    tot = sum(v for v in weights.values() if v > 0)
    for a, wa in weights.items():
        if wa <= 0:
            continue
        n = rows_per_arch
        if a == "D":
            g1 = arch_D(rng, n, 1, p, lib_seed)
            g2 = arch_D(rng, n, 2, p, lib_seed)
        elif a == "F":
            g1 = arch_F(rng, n, 1, p, lib_seed)
            g2 = arch_F(rng, n, 2, p, lib_seed)
        else:
            fn = {"A": arch_A, "B": arch_B, "C": arch_C, "E": arch_E,
                  "XC": arch_X_contrarian, "XA": arch_X_ai2}[a]
            g1 = fn(rng, n, 1, p)
            g2 = fn(rng, n, 2, p)
        # G. reuse: same allocation in both games (mostly the Game 1 answer copied)
        reuse = rng.random(n) < p["reuse"]
        from_g1 = rng.random(n) < 0.7
        g2 = np.where((reuse & from_g1)[:, None], g1, g2)
        g1 = np.where((reuse & ~from_g1)[:, None], g2, g1)
        G1.append(g1)
        G2.append(g2)
        W.append(np.full(n, wa / tot / n))
        tags += [a] * n
    g1 = np.concatenate(G1).astype(np.int64)
    g2 = np.concatenate(G2).astype(np.int64)
    w = np.concatenate(W)
    w = w / w.sum()
    assert (g1.sum(axis=1) == TOTAL).all() and (g2.sum(axis=1) == TOTAL).all()
    assert (g1 >= 0).all() and (g2 >= 0).all()
    return Population(name=name, seed=seed, g1=g1, g2=g2, w=w,
                      meta={"weights": dict(weights), "params": p, "arch": np.array(tags),
                            "lib_seed": lib_seed})


# named scenarios: (weights, params)
NAMED = {
    "naive_heavy": ({"A": 0.6, "B": 0.1, "C": 0.1, "E": 0.2}, {}),
    "ai_heavy": ({"E": 0.6, "A": 0.15, "C": 0.1, "D": 0.15}, {}),
    "concentration_heavy": ({"B": 0.5, "A": 0.2, "E": 0.2, "C": 0.1}, {}),
    "levelk_tau0.5": ({"D": 1.0}, {"tau": 0.5}),
    "levelk_tau1.5": ({"D": 1.0}, {"tau": 1.5}),
    "levelk_tau3": ({"D": 1.0}, {"tau": 3.0}),
    "equilibrium": ({"F": 1.0}, {}),
    "edge_heavy": ({"C": 0.5, "D": 0.2, "E": 0.2, "A": 0.1}, {}),
    # best guess: weights and reasons are in research/log (written before any results)
    "best_guess": ({"A": 0.20, "B": 0.12, "C": 0.10, "D": 0.15, "E": 0.33, "F": 0.10},
                   {"tau": 1.5, "reuse": 0.45}),
}

N_PRIOR = 240
PRIOR_ALPHA = {"A": 1.0, "B": 0.8, "C": 0.8, "D": 1.0, "E": 1.3, "F": 0.6}


def prior_spec(i: int):
    rng = np.random.default_rng([777, i])
    alpha = np.array([PRIOR_ALPHA[a] for a in ARCHES])
    w = rng.dirichlet(alpha)
    params = {
        "noise": float(rng.uniform(0.5, 2.0)),
        "round_prob": float(rng.uniform(0.2, 0.7)),
        "tau": float(rng.choice([0.5, 1.5, 3.0])),
        "reuse": float(rng.uniform(0.2, 0.8)),
    }
    return dict(zip(ARCHES, map(float, w))), params


HOLDOUT = {
    # different library seed (lib_seed=2) and holdout-only archetypes XC / XA
    "holdout_best_guess": ({"A": 0.18, "B": 0.12, "C": 0.10, "D": 0.12, "E": 0.25, "F": 0.08, "XA": 0.10, "XC": 0.05},
                           {"tau": 1.5, "reuse": 0.5}),
    "holdout_ai2_heavy": ({"XA": 0.45, "E": 0.2, "A": 0.15, "D": 0.1, "C": 0.1}, {"tau": 1.5}),
    "holdout_contrarian": ({"XC": 0.3, "A": 0.2, "E": 0.2, "B": 0.1, "C": 0.1, "F": 0.1}, {}),
    "holdout_sophisticated": ({"F": 0.35, "D": 0.35, "C": 0.15, "XA": 0.15}, {"tau": 3.0}),
}


def list_scenarios(kind: str) -> list[str]:
    if kind == "named":
        return list(NAMED)
    if kind == "prior":
        return [f"prior_{i:03d}" for i in range(N_PRIOR)]
    if kind == "holdout":
        return list(HOLDOUT)
    raise ValueError(kind)


@functools.lru_cache(maxsize=512)
def get_population(name: str, seed: int) -> Population:
    if name in NAMED:
        w, p = NAMED[name]
        return build_population(name, seed, w, p, lib_seed=1)
    if name.startswith("prior_"):
        w, p = prior_spec(int(name.split("_")[1]))
        return build_population(name, seed, w, p, lib_seed=1)
    if name in HOLDOUT:
        w, p = HOLDOUT[name]
        return build_population(name, seed, w, p, lib_seed=2)
    raise KeyError(name)
