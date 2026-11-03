"""Independent Game 2 search (claude-code) using populations.g2_mean_payout
(numba kernel, tested vs reference). Common random numbers per scenario.
Stage 1: candidate pool (multiples of 5 + concentration offsets + extra) on every
named + prior scenario at --g1 groups. Stage 2: top --k2 at --g2 groups on fresh
draws. Stage 3: local search (moves of 1,2,3,5 soldiers) around the top --k3 on
stage-2 draws, accepting only paired gains > 2 SE; then re-score finalists on
fresh draws.
Usage: PYTHONPATH=src python scripts/cc_g2_independent.py --id CC-030 --seed 1
"""
import argparse, json, subprocess, time
import numpy as np
from castles import populations as P


def scen_opps(names, pseed, n, sseed):
    out = []
    for k, nm in enumerate(names):
        p = P.get_population(nm, pseed)
        out.append(P.sample_opps(p.g2, p.w, n, np.random.default_rng([sseed, k])))
    return out


def score(cands, opps_list):
    return np.stack([P.g2_mean_payout(cands, o) for o in opps_list], axis=1)  # (C, S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="CC-030")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--g1", type=int, default=4000)
    ap.add_argument("--k2", type=int, default=200)
    ap.add_argument("--g2", type=int, default=40000)
    ap.add_argument("--k3", type=int, default=12)
    ap.add_argument("--extra", default="[]")
    a = ap.parse_args()
    t0 = time.time()
    named, prior = P.list_scenarios("named"), P.list_scenarios("prior")
    names = named + prior
    nN = len(named)
    pool = np.unique(np.concatenate([P.g2_candidate_pool(),
                                     np.array(json.loads(a.extra), dtype=np.int64).reshape(-1, 5)]), axis=0)
    o1 = scen_opps(names, a.seed, a.g1, a.seed * 1000 + 1)
    S1 = score(pool, o1)
    m1 = S1[:, nN:].mean(1)
    top = pool[np.argsort(-m1)[: a.k2]]
    print("stage1", round(time.time() - t0), "s; top5", top[:5].tolist(), np.sort(m1)[::-1][:5].round(3))
    o2 = scen_opps(names, a.seed, a.g2, a.seed * 1000 + 2)
    S2 = score(top, o2)
    m2 = S2[:, nN:].mean(1)
    order = np.argsort(-m2)
    print("stage2", round(time.time() - t0), "s;", [(top[i].tolist(), round(m2[i], 3)) for i in order[:8]])
    # stage 3: local search, paired on stage-2 draws (prior-mean objective)
    def prior_mean(x):
        return np.array([P.g2_mean_payout(x, o)[None] for o in o2[nN:]])[:, 0, :].mean(0)
    seen = {tuple(x) for x in top.tolist()}
    leaders = [top[i].copy() for i in order[: a.k3]]
    improved = []
    for x in leaders:
        cur = x.copy()
        for it in range(6):
            nb = []
            for i in range(5):
                for j in range(5):
                    if i == j:
                        continue
                    for k in (1, 2, 3, 5):
                        if cur[i] >= k:
                            y = cur.copy(); y[i] -= k; y[j] += k
                            nb.append(y)
            nb = np.array(nb)
            # paired per-group difference needs per-group payouts; use per-scenario means
            # across the 240 prior scenarios as the paired unit
            sc = np.stack([P.g2_mean_payout(np.vstack([cur, nb]), o) for o in o2[nN:]], axis=1)
            d = sc[1:] - sc[0]
            md = d.mean(1); se = d.std(1, ddof=1) / np.sqrt(d.shape[1])
            b = np.argmax(md)
            if md[b] > 2 * se[b] and md[b] > 0:
                cur = nb[b]
            else:
                break
        improved.append(cur)
        seen.add(tuple(cur.tolist()))
    fin = np.unique(np.concatenate([np.array(improved), top[order[:20]]]), axis=0)
    o3 = scen_opps(names, a.seed + 50, a.g2, a.seed * 1000 + 3)  # fresh population seed + draws
    S3 = score(fin, o3)
    m3 = S3[:, nN:].mean(1)
    best_named = S3[:, :nN].max(0)
    reg = (best_named[None, :] - S3[:, :nN]).max(1)
    p10 = np.percentile(S3[:, nN:], 10, axis=1)
    o = np.argsort(-m3)
    rows = [{"x": fin[i].tolist(), "prior_mean": float(m3[i]), "prior_p10": float(p10[i]),
             "max_named_regret_within_set": float(reg[i]),
             "named": dict(zip(named, map(float, S3[i, :nN])))} for i in o]
    for r in rows[:12]:
        print(r["x"], f"mean={r['prior_mean']:.4f} p10={r['prior_p10']:.3f} reg={r['max_named_regret_within_set']:.3f}")
    out = {"id": a.id, "agent": "claude-code", "game": 2, "population_seed": a.seed,
           "fresh_population_seed": a.seed + 50,
           "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
           "groups": {"stage1": a.g1, "stage2": a.g2, "final": a.g2}, "pool_size": len(pool),
           "scenarios": {"named": named, "prior": len(prior)}, "top": rows,
           "runtime_s": round(time.time() - t0, 1),
           "notes": "Screening-grade estimates (winner's curse in stages 1-2); final table on fresh population seed and fresh draws."}
    json.dump(out, open(f"results/experiments/{a.id}.json", "w"), indent=1)
    print("runtime", out["runtime_s"])


if __name__ == "__main__":
    main()
