"""Differential test: engine.py vs reference.py (claude-code).

Gate from AGENTS.md section 6: the two must match exactly on 1,000,000 random
Game 2 groups, including tie-heavy groups built from round-number allocations.

Usage:
    PYTHONPATH=src python scripts/difftest.py --groups 1000000 --seed 20261103 --procs 4

What it checks
1. Per-group exact match (castle units and payout units for all 4 players) if
   engine exposes `g2_group_units(groups: (n,4,5)) -> (pts (n,4), pay (n,4))`.
2. Per-pair exact match for Game 1 if engine exposes
   `g1_pair_units(a: (n,5), b: (n,5)) -> (pa (n,), pb (n,))`.
3. Always: for a set of probe candidates, `engine.g2_eval(x, opps)` means
   (payout and castle points) equal the reference means over the same
   opponent triples to 1e-9, and `engine.g1_exact` matches the reference
   expected Game 1 points against an empirical marginal.
Writes results/experiments/<id>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

from castles import reference as ref

ROUND_POOL = np.array([
    (20, 20, 20, 20, 20), (0, 0, 0, 50, 50), (0, 0, 34, 33, 33), (0, 0, 30, 35, 35),
    (0, 25, 25, 25, 25), (10, 10, 20, 30, 30), (0, 0, 0, 0, 100), (100, 0, 0, 0, 0),
    (0, 0, 50, 0, 50), (10, 20, 20, 25, 25), (0, 20, 20, 30, 30), (25, 25, 25, 25, 0),
    (0, 0, 25, 35, 40), (5, 10, 20, 30, 35), (0, 10, 20, 30, 40), (0, 0, 33, 33, 34),
], dtype=np.int64)


def random_allocs(rng: np.random.Generator, n: int, step: int = 1) -> np.ndarray:
    """Uniform random compositions of 100 (in multiples of `step`) into 5 parts."""
    m = 100 // step
    keys = rng.random((n, m + 4))
    bars = np.sort(np.argsort(keys, axis=1)[:, :4], axis=1)
    edges = np.concatenate([np.full((n, 1), -1), bars, np.full((n, 1), m + 4)], axis=1)
    return (np.diff(edges, axis=1) - 1) * step


def make_groups(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    kind = rng.integers(0, 4, size=n)
    out = np.empty((n, 4, 5), dtype=np.int64)
    k0 = kind == 0  # uniform over all allocations
    out[k0] = random_allocs(rng, int(k0.sum()) * 4).reshape(-1, 4, 5)
    k1 = kind == 1  # multiples of 10 -> many ties
    out[k1] = random_allocs(rng, int(k1.sum()) * 4, 10).reshape(-1, 4, 5)
    k2 = kind == 2  # drawn from a handful of round allocations -> heavy ties, equal totals
    out[k2] = ROUND_POOL[rng.integers(0, len(ROUND_POOL), size=(int(k2.sum()), 4))]
    k3 = kind == 3  # mixed: some round, some multiples of 25
    a = random_allocs(rng, int(k3.sum()) * 4, 25).reshape(-1, 4, 5)
    b = ROUND_POOL[rng.integers(0, len(ROUND_POOL), size=(int(k3.sum()), 4))]
    mask = rng.random((int(k3.sum()), 4, 1)) < 0.5
    out[k3] = np.where(mask, a, b)
    assert (out.sum(axis=2) == 100).all() and (out >= 0).all()
    return out


def _ref_chunk(groups: np.ndarray):
    pts = np.empty((len(groups), 4), dtype=np.int64)
    pay = np.empty((len(groups), 4), dtype=np.int64)
    for i, g in enumerate(groups.tolist()):
        p, y = ref.game2_units(g)
        pts[i] = p
        pay[i] = y
    return pts, pay


def ref_groups(groups: np.ndarray, procs: int):
    chunks = np.array_split(groups, max(1, procs * 8))
    with Pool(procs) as pool:
        parts = pool.map(_ref_chunk, chunks)
    return np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--id", default="CC-000-difftest")
    ap.add_argument("--agent", default="claude-code")
    args = ap.parse_args()

    from castles import engine  # imported late so the reference path never touches it

    t0 = time.time()
    report = {"id": args.id, "agent": args.agent, "game": "both", "seed": args.seed,
              "groups": args.groups, "checks": {}}
    try:
        report["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        report["commit"] = None

    groups = make_groups(args.groups, args.seed)
    rpts, rpay = ref_groups(groups, args.procs)
    assert (rpts.sum(axis=1) == 180).all() and (rpay.sum(axis=1) == 180).all()
    report["checks"]["reference_invariants"] = "pass"

    ok = True
    # 1. per-group exact
    if hasattr(engine, "g2_group_units"):
        epts, epay = engine.g2_group_units(groups)
        epts, epay = np.asarray(epts), np.asarray(epay)
        bad = np.where((epts != rpts).any(axis=1) | (epay != rpay).any(axis=1))[0]
        report["checks"]["g2_group_units_mismatches"] = int(len(bad))
        if len(bad):
            ok = False
            report["checks"]["g2_first_mismatches"] = [
                {"group": groups[i].tolist(), "ref": [rpts[i].tolist(), rpay[i].tolist()],
                 "engine": [epts[i].tolist(), epay[i].tolist()]} for i in bad[:10]]
    else:
        report["checks"]["g2_group_units_mismatches"] = "engine has no g2_group_units"

    # 2. Game 1 per-pair exact
    a, b = groups[:, 0], groups[:, 1]
    rp = np.array([ref.game1_units(x, y) for x, y in zip(a[:200_000].tolist(), b[:200_000].tolist())])
    if hasattr(engine, "g1_pair_units"):
        pa, pb = engine.g1_pair_units(a[:200_000], b[:200_000])
        nbad = int(((np.asarray(pa) != rp[:, 0]) | (np.asarray(pb) != rp[:, 1])).sum())
        report["checks"]["g1_pair_units_mismatches"] = nbad
        ok &= nbad == 0
    else:
        report["checks"]["g1_pair_units_mismatches"] = "engine has no g1_pair_units"

    # 3. g2_eval means vs reference, probe candidates against groups' last 3 players
    probes = np.concatenate([ROUND_POOL[:6], random_allocs(np.random.default_rng(args.seed + 1), 4)])
    opps = groups[:200_000, 1:, :]
    res = engine.g2_eval(probes, opps)
    g2_mean_err = []
    for ci, x in enumerate(probes.tolist()):
        full = np.concatenate([np.broadcast_to(np.array(x), (len(opps), 1, 5)), opps], axis=1)
        p, y = _ref_chunk(full)
        rm_pay = y[:, 0].mean() / 12.0
        rm_pts = p[:, 0].mean() / 12.0
        em_pay = float(np.asarray(res["mean"])[ci])
        em_pts = float(np.asarray(res["mean_castle_points"])[ci]) if "mean_castle_points" in res else float("nan")
        g2_mean_err.append({"x": x, "ref_payout": rm_pay, "engine_payout": em_pay,
                            "ref_points": rm_pts, "engine_points": em_pts})
        if abs(rm_pay - em_pay) > 1e-9 or ("mean_castle_points" in res and abs(rm_pts - em_pts) > 1e-9):
            ok = False
    report["checks"]["g2_eval_probe"] = g2_mean_err

    # 4. g1_exact vs reference against an empirical marginal (opponents = groups[:, 1])
    from collections import Counter
    opp1 = groups[:20_000, 1]
    marg = np.zeros((5, 101))
    for j in range(5):
        c = np.bincount(opp1[:, j], minlength=101)
        marg[j] = c / c.sum()
    e1 = np.asarray(engine.g1_exact(probes, marg), dtype=float)
    g1_err = []
    for ci, x in enumerate(probes.tolist()):
        cnt = Counter(map(tuple, opp1.tolist()))
        tot = sum(ref.game1_units(x, y)[0] * k for y, k in cnt.items())
        rv = tot / len(opp1) / 12.0
        g1_err.append({"x": x, "ref": rv, "engine": float(e1[ci])})
        if abs(rv - e1[ci]) > 1e-9:
            ok = False
    report["checks"]["g1_exact_probe"] = g1_err

    report["pass"] = bool(ok)
    report["runtime_s"] = round(time.time() - t0, 1)
    os.makedirs("results/experiments", exist_ok=True)
    with open(f"results/experiments/{args.id}.json", "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=1))
    print("g2_group_units_mismatches:", report["checks"]["g2_group_units_mismatches"])
    print("g1_pair_units_mismatches:", report["checks"]["g1_pair_units_mismatches"])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
