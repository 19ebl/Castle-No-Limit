"""Independent Game 1 exact analysis (claude-code), using populations' own scorer
(not engine.py). Mean over the prior for every allocation, top-k, then named-scenario
scores, max regret, and prior P10 for the top candidates.
Usage: PYTHONPATH=src python scripts/cc_g1_independent.py --seed 1 --id CC-010
"""
import argparse, json, subprocess, time
import numpy as np
from castles import populations as P

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--id", default="CC-010")
ap.add_argument("--top", type=int, default=30)
a = ap.parse_args()
t0 = time.time()
X = P.all_allocations()
prior = P.list_scenarios("prior")
named = P.list_scenarios("named")
acc = np.zeros(len(X))
for n in prior:
    p = P.get_population(n, a.seed)
    acc += P.g1_scores_all(P.g1_marginals_rows(p.g1, p.w))
acc /= len(prior)
top = np.argsort(-acc)[: a.top]
cand = X[top].astype(np.int64)
S_prior = np.zeros((len(cand), len(prior)))
best_named, S_named = {}, np.zeros((len(cand), len(named)))
for k, n in enumerate(prior):
    p = P.get_population(n, a.seed)
    m = P.g1_marginals_rows(p.g1, p.w)
    cdf = np.cumsum(m, 1); below = np.concatenate([np.zeros((5, 1)), cdf[:, :-1]], 1)
    tab = P.VALUES[:, None] * (below + 0.5 * m)
    S_prior[:, k] = sum(tab[j][cand[:, j]] for j in range(5))
for k, n in enumerate(named):
    p = P.get_population(n, a.seed)
    s = P.g1_scores_all(P.g1_marginals_rows(p.g1, p.w))
    best_named[n] = (X[np.argmax(s)].tolist(), float(s.max()))
    S_named[:, k] = s[top]
regret = np.array([best_named[n][1] for n in named])[None, :] - S_named
rows = []
for i in range(len(cand)):
    rows.append({"x": cand[i].tolist(), "prior_mean": float(acc[top[i]]),
                 "prior_p10": float(np.percentile(S_prior[i], 10)),
                 "max_named_regret": float(regret[i].max()),
                 "named": dict(zip(named, map(float, S_named[i])))})
out = {"id": a.id, "agent": "claude-code", "game": 1, "seed": a.seed,
       "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
       "scenarios": {"prior": len(prior), "named": named}, "method": "exact (populations scorer)",
       "named_best": best_named, "top": rows, "runtime_s": round(time.time() - t0, 1)}
json.dump(out, open(f"results/experiments/{a.id}.json", "w"), indent=1)
for r in rows[:15]:
    print(r["x"], f"mean={r['prior_mean']:.4f} p10={r['prior_p10']:.3f} maxreg={r['max_named_regret']:.3f}")
print("named best:", {k: (v[0], round(v[1], 3)) for k, v in best_named.items()})
print("runtime", out["runtime_s"])
