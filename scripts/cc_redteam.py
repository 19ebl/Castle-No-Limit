"""Phase 4 red team (claude-code) using robustness.red_team (adopted from codex)
on several base populations. Reports exact G1 damage and fresh paired G2 damage
when 20% / 40% of applicants play a targeted counter.
Usage: PYTHONPATH=src python scripts/cc_redteam.py --id CC-040 --bases best_guess,ai_heavy --pseed 7
"""
import argparse, json, subprocess, time
import numpy as np
from castles import populations as P
from castles.robustness import red_team

ap = argparse.ArgumentParser()
ap.add_argument("--id", default="CC-040")
ap.add_argument("--bases", default="best_guess,ai_heavy,levelk_tau3")
ap.add_argument("--pseed", type=int, default=7)
ap.add_argument("--g1", required=True)
ap.add_argument("--g2", required=True)
ap.add_argument("--n", type=int, default=100000)
a = ap.parse_args()
t0 = time.time()
out = {"id": a.id, "agent": "claude-code", "population_seed": a.pseed, "groups": a.n,
       "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "bases": {}}
for k, b in enumerate(a.bases.split(",")):
    base = P.get_population(b, a.pseed)
    r = red_team(json.loads(a.g1), json.loads(a.g2), base, seed=86001 + 1000 * k, n=a.n)
    out["bases"][b] = r
    print("==", b)
    for row in r["g1"]:
        print(" G1", row["allocation"], f"share={row['counter_share']} base={row['base_score']:.3f} stressed={row['stress_score']:.3f} damage={row['damage']:.3f}")
    for row in r["g2"]:
        print(" G2", row["allocation"], f"share={row['counter_share']} base={row['base_score']:.3f} stressed={row['stress_score']:.3f} damage={row['damage']:.3f}±{1.96*row['damage_se']:.3f}",
              "counters", row["counter_search"]["anchor_counters"][:2])
out["runtime_s"] = round(time.time() - t0, 1)
json.dump(out, open(f"results/experiments/{a.id}.json", "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
print("runtime", out["runtime_s"])
