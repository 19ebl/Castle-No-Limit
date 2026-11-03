"""Regenerate every table in RESULTS.md from saved experiment JSON (claude-code).
No simulation is run.

    python scripts/cc_results_tables.py [--cx-dir results/experiments] [--cc-dir results/experiments]

Reads codex CX-020 (exact Game 1 search), CX-031 (Game 2 rerace), CX-050 (final
validation) and claude-code CC-050/CC-051 (independent reproduction), CC-020/CC-041
(sensitivity) and CC-042 (red team).
"""
import argparse
import json
import os

import numpy as np

NAMED = ["naive_heavy", "ai_heavy", "concentration_heavy", "levelk_tau0.5", "levelk_tau1.5",
         "levelk_tau3", "equilibrium", "edge_heavy", "best_guess"]
SHORT = ["naive", "ai", "conc", "lk0.5", "lk1.5", "lk3", "eq", "edge", "best"]
HOLD = ["holdout_best_guess", "holdout_ai2_heavy", "holdout_contrarian", "holdout_sophisticated"]


def A(x):
    return "(" + ",".join(str(int(v)) for v in x) + ")"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx-dir", default="results/experiments")
    ap.add_argument("--cc-dir", default="results/experiments")
    a = ap.parse_args()
    cx = lambda n: json.load(open(os.path.join(a.cx_dir, n)))
    cc = lambda n: json.load(open(os.path.join(a.cc_dir, n)))
    F, G1S, G2S = cx("CX-050.json"), cx("CX-020.json"), cx("CX-031.json")
    RP, RH = cc("CC-051-prior.json"), cc("CC-050-holdout.json")
    g1c, g2c = F["candidates"]["g1"], F["candidates"]["g2"]
    i1, i2 = F["decision"]["g1_index"], F["decision"]["g2_index"]

    print("## Headline: Game 1", A(g1c[i1]), "(expected castle points, exact; codex CX-050 / claude-code CC-050-051)\n")
    rows = [["prior (240, mean)", f"{F['g1_prior_mean'][i1]:.6f}",
             f"{np.mean([u['g1'][i1]['exact'] for u in RP['units']]):.6f}", "exact"]]
    for h in HOLD:
        ex = F["g1_exact"][h][i1] if isinstance(F["g1_exact"][h], list) else F["g1_exact"][h]["exact"][i1]
        cxc = F["g1_crosschecks"][h]
        mine = next(u for u in RH["units"] if u["scenario"] == h and u["pop_seed"] < 200000)["g1"][i1]
        rows.append([h, f"{ex:.4f}", f"{mine['exact']:.4f}",
                     f"codex MC {cxc['mean'][i1]:.4f}±{1.96*cxc['se'][i1]:.4f} (z {cxc['z'][i1]:+.2f}); "
                     f"claude-code MC {mine['mc_mean']:.4f}±{1.96*mine['mc_se']:.4f}"])
    print(table(["Scenario", "codex exact", "claude-code exact", "1M-matchup Monte Carlo cross-check (95%)"], rows))

    print("\n## Headline: Game 2", A(g2c[i2]), "(expected payout, 95% Monte Carlo CI; place shares split ties)\n")
    m = F["g2_prior_mean"][i2]; s = F["g2_prior_mc_se"][i2]
    pm = np.mean([u["g2"][i2]["mean"] for u in RP["units"]])
    ps = np.sqrt(sum(u["g2"][i2]["se"] ** 2 for u in RP["units"])) / len(RP["units"])
    pl = np.mean([u["g2"][i2]["p_place_1to4"] for u in RP["units"]], axis=0)
    pts = np.mean([u["g2"][i2]["mean_castle_points"] for u in RP["units"]])
    prior_codex_place = np.mean([F["g2"][n]["place"][i2] for n in F["g2"] if n.startswith("prior_")], axis=0)
    prior_codex_pts = np.mean([F["g2"][n]["mean_castle_points"][i2] for n in F["g2"] if n.startswith("prior_")])
    rows = [["prior (240, mean)", f"{m:.4f} [{m-1.96*s:.4f}, {m+1.96*s:.4f}]", f"{pm:.4f} [{pm-1.96*ps:.4f}, {pm+1.96*ps:.4f}]",
             " / ".join(f"{v:.3f}" for v in prior_codex_place), f"{prior_codex_pts:.3f}"]]
    for h in HOLD:
        c = F["g2"][h]
        mine = next(u for u in RH["units"] if u["scenario"] == h and u["pop_seed"] < 200000)["g2"][i2]
        rows.append([h, f"{c['mean'][i2]:.4f} [{c['mean'][i2]-1.96*c['se'][i2]:.4f}, {c['mean'][i2]+1.96*c['se'][i2]:.4f}]",
                     f"{mine['mean']:.4f} [{mine['ci95'][0]:.4f}, {mine['ci95'][1]:.4f}]",
                     " / ".join(f"{v:.3f}" for v in c["place"][i2]), f"{c['mean_castle_points'][i2]:.3f}"])
    print(table(["Scenario", "codex (1M groups/scenario)", "claude-code (prior 200k, holdout 1M)", "P(1st/2nd/3rd/4th), codex", "Mean castle points, codex"], rows))
    print(f"\nclaude-code prior place shares {' / '.join(f'{v:.3f}' for v in pl)}, castle points {pts:.3f}.")

    print("\n## Finalists on the prior and holdouts (codex CX-050)\n")
    rows = []
    for i, x in enumerate(g1c):
        rows.append(["G1", A(x), f"{F['g1_prior_mean'][i]:.4f}"] +
                    [f"{(F['g1_exact'][h][i] if isinstance(F['g1_exact'][h], list) else F['g1_exact'][h]['exact'][i]):.3f}" for h in HOLD])
    for i, x in enumerate(g2c):
        rows.append(["G2", A(x), f"{F['g2_prior_mean'][i]:.4f}"] + [f"{F['g2'][h]['mean'][i]:.3f}" for h in HOLD])
    print(table(["Game", "Allocation", "Prior mean"] + [h.replace("holdout_", "") for h in HOLD], rows))
    d = F["decision"]
    print(f"\nGame 2 leader minus runner-up on the prior: {d['paired_prior_mean_difference']:.5f}, paired 95% "
          f"[{d['paired_prior_ci95'][0]:.5f}, {d['paired_prior_ci95'][1]:.5f}], statistical tie: {d['statistical_tie']}.")

    print("\n## Top 10, Game 1 (codex CX-020, exact). Regret is vs the exact best response in each named scenario.\n")
    rows = [[A(r["allocation"]), f"{r['prior_mean']:.4f}", f"{r['prior_p10']:.3f}", f"{r['max_named_regret']:.3f}"] +
            [f"{r['named_scores'][n]:.2f}" for n in NAMED] for r in G1S["top100"][:10]]
    print(table(["Allocation", "Prior mean", "Prior P10", "Max named regret"] + SHORT, rows))

    print("\n## Top 10, Game 2 (codex CX-031, 100k CRN groups per scenario; screening grade). Regret is vs the best of the 72-candidate benchmark set.\n")
    rows = [[A(r["allocation"]), f"{r['prior_mean']:.4f}", f"{r['prior_mc_se']:.4f}", f"{r['prior_p10']:.3f}", f"{r['max_named_candidate_regret']:.3f}"] +
            [f"{r['named_scores'][n]:.2f}" for n in NAMED] for r in G2S["ranking"][:10]]
    print(table(["Allocation", "Prior mean", "MC SE", "Prior P10", "Max named regret"] + SHORT, rows))

    for fid, game in (("CC-020.json", 1), ("CC-041.json", 2)):
        S = cc(fid)
        V = np.array([v["scores"] for v in S["variants"]])
        print(f"\n## Sensitivity, Game {game} ({fid[:-5]}; best_guess mix with one knob moved; population seeds {S['seeds']})\n")
        rows = [[v["variant"], A(v["ranking"][0])] + [f"{s:.3f}" for s in v["scores"]] for v in S["variants"]]
        print(table(["Variant", "Best of set"] + [A(c) for c in S["candidates"]], rows))
        print("\nMax shortfall vs best of set: " + "; ".join(f"{A(c)} {r:.3f}" for c, r in zip(S["candidates"], (V.max(1, keepdims=True) - V).max(0))))

    R = cc("CC-042.json")
    print("\n## Red team (CC-042): payout lost when 20% / 40% of applicants play a targeted counter (100k fresh paired groups)\n")
    rows = []
    for b, r in R["bases"].items():
        for row in r["g2"]:
            if row["counter_share"] == 0.2:
                r40 = next(q for q in r["g2"] if q["allocation"] == row["allocation"] and q["counter_share"] == 0.4)
                rows.append([b, A(row["allocation"]), f"{row['base_score']:.3f}", f"{row['damage']:.2f}", f"{r40['damage']:.2f}",
                             A(row["counter_search"]["anchor_counters"][0])])
    print(table(["Base", "Allocation", "Base payout", "Loss at 20%", "Loss at 40%", "Main counter"], rows))


if __name__ == "__main__":
    main()
