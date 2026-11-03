"""Independent reproduction of Phase 5 headline numbers (claude-code).

Uses only populations.py and its own scorers (no engine.py), with draw seeds
different from codex's.
- Game 1: exact expected castle points on each scenario, plus a Monte Carlo
  cross-check with N sampled matchups per finalist (own vectorized scorer).
- Game 2: N groups per finalist per scenario with common random numbers, mean
  payout, SE, P(1st..4th) and mean castle points, plus paired 95% CIs on the
  differences vs the first finalist.

Scenario sets: "prior" (240 priors at seed base), "holdout" (each holdout spec at
the given population seeds), or "named".

Usage:
  PYTHONPATH=src python scripts/cc_replicate.py --id CC-050 --kind holdout \
      --pop-seeds 410300,510300,610300 --draw-seed 777001 --groups 1000000 \
      --g1 '[[1,11,1,36,51],...]' --g2 '[[1,0,48,51,0],...]'
For --kind prior, --pop-seeds is a seed BASE (scenario i uses base+i, as in the
frozen training snapshot when base=110300).
"""
import argparse
import json
import subprocess
import time

import numpy as np

from castles import populations as P

V12 = np.array([12, 24, 36, 48, 60])
CS = np.array([0, 108, 156, 180, 180, 180])


def g1_exact(cands, pop):
    m = P.g1_marginals_rows(pop.g1, pop.w)
    cdf = np.cumsum(m, 1)
    below = np.concatenate([np.zeros((5, 1)), cdf[:, :-1]], 1)
    tab = P.VALUES[:, None] * (below + 0.5 * m)
    return sum(tab[j][cands[:, j]] for j in range(5))


def g1_mc(cands, pop, n, rng):
    idx = rng.choice(len(pop.w), size=n, p=pop.w / pop.w.sum())
    opp = pop.g1[idx]
    out = []
    for x in cands:
        u = ((x > opp) * V12 + (x == opp) * (V12 // 2)).sum(1) / 12.0
        out.append((u.mean(), u.std(ddof=1) / np.sqrt(n)))
    return out


def g2_detail(cands, opps):
    """Per-group payout units (C, n) and castle units (C, n) for each candidate."""
    n = len(opps)
    pay = np.empty((len(cands), n), dtype=np.int64)
    pts = np.empty((len(cands), n), dtype=np.int64)
    for c, x in enumerate(cands):
        g = np.concatenate([np.broadcast_to(x, (n, 1, 5)), opps], axis=1)
        top = g.max(axis=1, keepdims=True)
        win = g == top
        u = (win * (V12 // win.sum(axis=1, keepdims=True))).sum(axis=2)
        above = (u[:, 1:] > u[:, :1]).sum(1)
        eq = (u[:, 1:] == u[:, :1]).sum(1)
        pay[c] = (CS[above + eq + 1] - CS[above]) // (eq + 1)
        pts[c] = u[:, 0]
    return pay, pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--kind", choices=["prior", "holdout", "named"], required=True)
    ap.add_argument("--pop-seeds", required=True)
    ap.add_argument("--draw-seed", type=int, default=777001)
    ap.add_argument("--groups", type=int, default=1_000_000)
    ap.add_argument("--g1mc", type=int, default=1_000_000)
    ap.add_argument("--chunk", type=int, default=250_000)
    ap.add_argument("--g1", required=True)
    ap.add_argument("--g2", required=True)
    a = ap.parse_args()
    t0 = time.time()
    G1 = np.array(json.loads(a.g1), dtype=np.int64)
    G2 = np.array(json.loads(a.g2), dtype=np.int64)
    seeds = [int(s) for s in a.pop_seeds.split(",")]
    units = []  # (scenario name, population seed)
    if a.kind == "prior":
        units = [(n, seeds[0] + i) for i, n in enumerate(P.list_scenarios("prior"))]
    else:
        for s in seeds:
            units += [(n, s) for n in P.list_scenarios(a.kind)]
    res = {"id": a.id, "agent": "claude-code", "kind": a.kind, "pop_seeds": seeds,
           "draw_seed": a.draw_seed, "groups": a.groups, "g1_mc_matchups": a.g1mc,
           "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
           "g1_finalists": G1.tolist(), "g2_finalists": G2.tolist(), "units": []}
    for k, (name, ps) in enumerate(units):
        pop = P.get_population(name, ps)
        rng = np.random.default_rng([a.draw_seed, k])
        ex = g1_exact(G1, pop)
        mc = g1_mc(G1, pop, a.g1mc, rng) if a.g1mc else []
        # Game 2: chunked so 1M groups fit in memory; CRN across finalists
        n_done = 0
        sum_pay = np.zeros(len(G2)); sum_pts = np.zeros(len(G2))
        sum_d = np.zeros(len(G2)); sum_d2 = np.zeros(len(G2)); sum_p2 = np.zeros(len(G2))
        place = np.zeros((len(G2), 4))
        while n_done < a.groups:
            m = min(a.chunk, a.groups - n_done)
            opps = P.sample_opps(pop.g2, pop.w, m, rng)
            pay, pts = g2_detail(G2, opps)
            pay_f = pay / 12.0
            sum_pay += pay_f.sum(1); sum_p2 += (pay_f ** 2).sum(1); sum_pts += (pts / 12.0).sum(1)
            d = pay_f - pay_f[:1]
            sum_d += d.sum(1); sum_d2 += (d ** 2).sum(1)
            # place probabilities, ties split fractionally by payout-share convention:
            # report P(sole or shared k-th) as payout-equivalent counts for exact places
            for p_i, val in enumerate((108, 48, 24, 0)):
                place[:, p_i] += (pay == val).sum(1)
            n_done += m
        n = a.groups
        mean = sum_pay / n
        se = np.sqrt(np.maximum(sum_p2 / n - mean ** 2, 0) * n / (n - 1) / n)
        dm = sum_d / n
        dse = np.sqrt(np.maximum(sum_d2 / n - dm ** 2, 0) * n / (n - 1) / n)
        u = {"scenario": name, "pop_seed": ps,
             "g1": [{"x": G1[i].tolist(), "exact": float(ex[i]),
                     "mc_mean": float(mc[i][0]) if mc else None, "mc_se": float(mc[i][1]) if mc else None,
                     "mc_within_3se": bool(abs(mc[i][0] - ex[i]) <= 3 * mc[i][1]) if mc else None}
                    for i in range(len(G1))],
             "g2": [{"x": G2[i].tolist(), "mean": float(mean[i]), "se": float(se[i]),
                     "ci95": [float(mean[i] - 1.96 * se[i]), float(mean[i] + 1.96 * se[i])],
                     "diff_vs_first": float(dm[i]),
                     "diff_ci95": [float(dm[i] - 1.96 * dse[i]), float(dm[i] + 1.96 * dse[i])],
                     "p_sole_place_1to4": (place[i] / n).tolist(),
                     "mean_castle_points": float(sum_pts[i] / n)} for i in range(len(G2))]}
        res["units"].append(u)
        print(f"[{time.time()-t0:6.0f}s] {name}@{ps}: G1 " +
              " ".join(f"{e['exact']:.3f}" for e in u["g1"]) + " | G2 " +
              " ".join(f"{e['mean']:.3f}" for e in u["g2"]), flush=True)
    # aggregate over units: mean of unit means, CI from spread across units
    agg = {"g1": [], "g2": []}
    E = np.array([[e["exact"] for e in u["g1"]] for u in res["units"]])
    M = np.array([[e["mean"] for e in u["g2"]] for u in res["units"]])
    for i in range(len(G1)):
        agg["g1"].append({"x": G1[i].tolist(), "mean_over_units": float(E[:, i].mean()),
                          "min_over_units": float(E[:, i].min()),
                          "mc_all_within_3se": all(u["g1"][i]["mc_within_3se"] for u in res["units"]) if a.g1mc else None})
    D = M - M[:, :1]
    for i in range(len(G2)):
        dse_u = D[:, i].std(ddof=1) / np.sqrt(len(D)) if len(D) > 1 else float("nan")
        agg["g2"].append({"x": G2[i].tolist(), "mean_over_units": float(M[:, i].mean()),
                          "diff_vs_first": float(D[:, i].mean()),
                          "diff_ci95_across_units": [float(D[:, i].mean() - 1.96 * dse_u), float(D[:, i].mean() + 1.96 * dse_u)],
                          "min_over_units": float(M[:, i].min())})
    res["aggregate"] = agg
    res["runtime_s"] = round(time.time() - t0, 1)
    json.dump(res, open(f"results/experiments/{a.id}.json", "w"), indent=1)
    print(json.dumps(agg, indent=1))
    print("runtime", res["runtime_s"])


if __name__ == "__main__":
    main()
