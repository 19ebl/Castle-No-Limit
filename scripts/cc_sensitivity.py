"""Phase 4 sensitivity (claude-code): how candidates reorder as the AI-assisted
share, the reuse share and tau change around the best_guess mix.
Game 1 is exact (populations scorer). Game 2 uses common random numbers via
populations.g2_mean_payout (numba kernel tested against reference).
Usage: PYTHONPATH=src python scripts/cc_sensitivity.py --game 1 --cands '[[1,11,1,36,51],...]' --id CC-020
"""
import argparse, json, subprocess, time
import numpy as np
from castles import populations as P

BASE_W, BASE_P = P.NAMED["best_guess"]


def variants():
    out = []
    for s in (0.0, 0.15, 0.33, 0.5, 0.7):
        w = {k: v * (1 - s) / (1 - BASE_W["E"]) for k, v in BASE_W.items() if k != "E"}
        w["E"] = s
        out.append((f"ai_share={s}", w, dict(BASE_P)))
    for tau in (0.5, 1.5, 3.0):
        for dw in (0.15, 0.4):
            w = {k: v * (1 - dw) / (1 - BASE_W["D"]) for k, v in BASE_W.items() if k != "D"}
            w["D"] = dw
            out.append((f"tau={tau},D={dw}", w, dict(BASE_P, tau=tau)))
    for r in (0.2, 0.45, 0.8):
        out.append((f"reuse={r}", dict(BASE_W), dict(BASE_P, reuse=r)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=int, required=True)
    ap.add_argument("--cands", required=True)
    ap.add_argument("--seeds", default="101,102,103")
    ap.add_argument("--groups", type=int, default=200_000)
    ap.add_argument("--id", required=True)
    a = ap.parse_args()
    cands = np.array(json.loads(a.cands), dtype=np.int64)
    seeds = [int(s) for s in a.seeds.split(",")]
    t0 = time.time()
    res = []
    for label, w, p in variants():
        per_seed = []
        for s in seeds:
            pop = P.build_population(f"sens:{label}", s, w, p)
            if a.game == 1:
                m = P.g1_marginals_rows(pop.g1, pop.w)
                cdf = np.cumsum(m, 1); below = np.concatenate([np.zeros((5, 1)), cdf[:, :-1]], 1)
                tab = P.VALUES[:, None] * (below + 0.5 * m)
                per_seed.append(sum(tab[j][cands[:, j]] for j in range(5)))
            else:
                rng = np.random.default_rng([s, 4242])
                opps = P.sample_opps(pop.g2, pop.w, a.groups, rng)
                per_seed.append(P.g2_mean_payout(cands, opps))
        sc = np.mean(per_seed, axis=0)
        sd = np.std(per_seed, axis=0, ddof=1) / np.sqrt(len(seeds)) if len(seeds) > 1 else np.zeros(len(cands))
        order = np.argsort(-sc)
        res.append({"variant": label, "scores": sc.tolist(), "seed_se": sd.tolist(),
                    "ranking": [cands[i].tolist() for i in order]})
        print(f"{label:22s} best={cands[order[0]].tolist()} " +
              " ".join(f"{sc[i]:.3f}" for i in range(len(cands))))
    out = {"id": a.id, "agent": "claude-code", "game": a.game, "seeds": seeds,
           "groups_per_seed": a.groups if a.game == 2 else None,
           "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
           "candidates": cands.tolist(), "variants": res, "runtime_s": round(time.time() - t0, 1),
           "notes": "seed_se is the spread across population seeds (population-sampling noise), not MC noise."}
    json.dump(out, open(f"results/experiments/{a.id}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
