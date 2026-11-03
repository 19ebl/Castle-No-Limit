"""Game 2 contenders averaged over several population seeds (claude-code).
Per (scenario, population seed): fresh CRN groups shared by all candidates.
Reports prior mean with a 95% CI from the per-(scenario,seed) paired spread,
paired differences vs the leader, and named-scenario scores.
Usage: PYTHONPATH=src python scripts/cc_g2_multiseed.py --id CC-032 --seeds 201,202,203 --groups 50000 --cands '[...]'
"""
import argparse, json, subprocess, time
import numpy as np
from castles import populations as P

ap = argparse.ArgumentParser()
ap.add_argument("--id", required=True)
ap.add_argument("--seeds", default="201,202,203")
ap.add_argument("--groups", type=int, default=50000)
ap.add_argument("--cands", required=True)
ap.add_argument("--kind", default="prior")
a = ap.parse_args()
t0 = time.time()
C = np.array(json.loads(a.cands), dtype=np.int64)
seeds = [int(s) for s in a.seeds.split(",")]
names = P.list_scenarios(a.kind)
named = P.list_scenarios("named")
S = []  # (units, C)
for s in seeds:
    for k, n in enumerate(names):
        p = P.get_population(n, s)
        o = P.sample_opps(p.g2, p.w, a.groups, np.random.default_rng([s, k, 99]))
        S.append(P.g2_mean_payout(C, o))
S = np.array(S)
SN = np.array([[P.g2_mean_payout(C, P.sample_opps(P.get_population(n, s).g2, P.get_population(n, s).w, a.groups,
               np.random.default_rng([s, 500 + k])))
                for k, n in enumerate(named)] for s in seeds]).mean(0)  # (named, C)
m = S.mean(0)
se = S.std(0, ddof=1) / np.sqrt(len(S))
L = int(np.argmax(m))
d = S - S[:, [L]]
dm, dse = d.mean(0), d.std(0, ddof=1) / np.sqrt(len(S))
reg = (SN.max(1, keepdims=True) - SN).max(0)
rows = []
for i in np.argsort(-m):
    rows.append({"x": C[i].tolist(), "mean": float(m[i]), "se_over_units": float(se[i]),
                 "diff_vs_leader": float(dm[i]), "diff_ci95": [float(dm[i] - 1.96 * dse[i]), float(dm[i] + 1.96 * dse[i])],
                 "max_named_regret_within_set": float(reg[i]), "named": dict(zip(named, map(float, SN[:, i])))})
    print(C[i].tolist(), f"mean={m[i]:.4f} diff={dm[i]:+.4f} [{dm[i]-1.96*dse[i]:+.4f},{dm[i]+1.96*dse[i]:+.4f}] reg={reg[i]:.3f}")
json.dump({"id": a.id, "agent": "claude-code", "game": 2, "kind": a.kind, "population_seeds": seeds,
           "groups_per_unit": a.groups, "units": len(S),
           "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
           "rows": rows, "runtime_s": round(time.time() - t0, 1),
           "notes": "Units are (scenario, population seed) pairs; CI uses spread across units so it includes population-sampling noise."},
          open(f"results/experiments/{a.id}.json", "w"), indent=1)
print("runtime", round(time.time() - t0, 1))
