#!/usr/bin/env python3
"""Render saved scores without sampling or rerunning a research phase.

From the repository root: python scripts/render_tables.py
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def allocation(values):
    return "(" + ", ".join(str(int(x)) for x in values) + ")"


def number(value):
    return f"{float(value):.6f}"


def interval(mean, se):
    return f"[{number(mean - 1.96 * se)}, {number(mean + 1.96 * se)}]"


def markdown_table(headers, rows):
    def clean(cell):
        return str(cell).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(map(clean, headers)) + " |",
                       "| " + " | ".join("---" for _ in headers) + " |"] +
                      ["| " + " | ".join(map(clean, row)) + " |" for row in rows])


def render(g1, g2, final):
    """Return Markdown and normalized CSV records from the three saved runs."""
    named = list(g1["top100"][0]["named_scores"])
    prior = [name for name in g1["scenarios"] if name not in named]
    holdout = [name for name in final["scenarios"] if name not in g1["scenarios"]]
    if not prior:
        raise ValueError("No prior scenarios found in the saved Game 1 search")
    records = []
    sections = ["# Saved-score tables", f"Generated from CX-020, {g2.get('id','CX-030')}, and CX-050. "
                "Regenerate with `python scripts/render_tables.py`; this reads saved scores and performs no simulation."]
    selected = {1: final["decision"]["g1_index"], 2: final["decision"]["g2_index"]}
    sections += ["## Recommended allocations", markdown_table(
        ["Game", "Allocation", "Objective"],
        [[1, allocation(final["candidates"]["g1"][selected[1]]), "Expected castle points"],
         [2, allocation(final["candidates"]["g2"][selected[2]]), "Expected placement payout"]])]

    def add_score(game, scenario, index, mean, se, points=None, places=None, kind="validation"):
        candidate = final["candidates"][f"g{game}"][index]
        record = dict(table=kind, game=game, scenario=scenario, candidate=allocation(candidate),
                      candidate_index=index, selected=index == selected[game], mean=float(mean),
                      se=float(se), ci95_low=float(mean - 1.96*se), ci95_high=float(mean + 1.96*se))
        if places is not None:
            record.update({f"place_{rank+1}": float(value) for rank, value in enumerate(places)})
        if points is not None:
            record["mean_castle_points"] = float(points)
        records.append(record)
        return [index, allocation(candidate), number(mean), interval(mean, se)]

    # The prior is a fixed, equally weighted set of scenarios, not a random
    # sample from a known distribution of real applicants.
    g2_prior_places = [[sum(final["g2"][name]["place"][i][r] for name in prior)/len(prior)
                        for r in range(4)] for i in range(len(final["candidates"]["g2"]))]
    g2_prior_points = [sum(final["g2"][name]["mean_castle_points"][i] for name in prior)/len(prior)
                       for i in range(len(final["candidates"]["g2"]))]
    sections.append("## Final validation: fixed prior and untouched holdouts")
    for scenario in ["prior_average"] + holdout:
        rows = []
        for game in (1, 2):
            count = len(final["candidates"][f"g{game}"])
            for i in range(count):
                if game == 1:
                    mean = (final["g1_prior_mean"] if scenario == "prior_average" else final["g1_exact"][scenario])[i]
                    row = add_score(game, scenario, i, mean, 0.0)
                    extras = ["exact", "", "", "", "", number(mean)]
                else:
                    if scenario == "prior_average":
                        mean, se = final["g2_prior_mean"][i], final["g2_prior_mc_se"][i]
                        places, points = g2_prior_places[i], g2_prior_points[i]
                    else:
                        data = final["g2"][scenario]
                        mean, se = data["mean"][i], data["se"][i]
                        places, points = data["place"][i], data["mean_castle_points"][i]
                    row = add_score(game, scenario, i, mean, se, points, places)
                    extras = ["Monte Carlo"] + [number(p) for p in places] + [number(points)]
                rows.append([game, "yes" if i == selected[game] else ""] + row + extras)
        sections += [f"### {scenario}", markdown_table(
            ["Game", "Selected", "Index", "Allocation", "Mean", "95% interval", "Score basis",
             "P(rank 1)", "P(rank 2)", "P(rank 3)", "P(rank 4)", "Mean castle points"], rows)]

    sections.append("## Game 1 Monte Carlo cross-checks of exact values")
    cross_rows = []
    for scenario, check in final["g1_crosschecks"].items():
        for i, candidate in enumerate(final["candidates"]["g1"]):
            cross_rows.append([scenario, allocation(candidate), number(check["exact"][i]),
                number(check["mean"][i]), interval(check["mean"][i], check["se"][i]),
                number(check["z"][i]), "pass" if check["pass_3se"][i] else "FAIL", check["matchups"]])
            add_score(1, scenario, i, check["mean"][i], check["se"][i], kind="g1_crosscheck")
    sections.append(markdown_table(["Scenario", "Allocation", "Exact", "MC mean", "MC 95% interval", "z", "Within 3 SE", "Matchups"], cross_rows))

    sections.append("## Paired Game 2 finalist differences")
    pair_rows = []
    pair_keys = list(final["paired_g2"][prior[0]])
    for scenario in ["prior_average"] + holdout:
        for key in pair_keys:
            if scenario == "prior_average":
                mean = sum(final["paired_g2"][s][key]["mean"] for s in prior)/len(prior)
                se = math.sqrt(sum(final["paired_g2"][s][key]["se"]**2 for s in prior))/len(prior)
            else:
                mean, se = (final["paired_g2"][scenario][key][field] for field in ("mean", "se"))
            a, b = map(int, key.split("-"))
            pair_rows.append([scenario, f"{a} minus {b}", number(mean), number(se), interval(mean, se)])
            records.append(dict(table="paired_g2", game=2, scenario=scenario, candidate=f"{a} minus {b}",
                                mean=mean, se=se, ci95_low=mean-1.96*se, ci95_high=mean+1.96*se))
    sections.append(markdown_table(["Scenario", "Candidate indices", "Mean difference", "Paired SE", "Paired 95% interval"], pair_rows))

    sections.append("## Search rankings: estimates used for selection, not final validation")
    for game, ranking, regret_key in ((1, g1["top100"], "max_named_regret"),
                                      (2, g2["ranking"], "max_named_candidate_regret")):
        rows = []
        for rank, item in enumerate(ranking[:10], 1):
            rows.append([rank, allocation(item["allocation"]), number(item["prior_mean"]),
                         number(item["prior_p10"]), number(item[regret_key])] +
                        [number(item["named_scores"][name]) for name in named])
            records.append(dict(table="search_top10", game=game, candidate=allocation(item["allocation"]),
                                candidate_index=rank-1, mean=item["prior_mean"], max_named_regret=item[regret_key],
                                prior_p10=item["prior_p10"]))
        sections += [f"### Game {game}", markdown_table(
            ["Rank", "Allocation", "Prior mean", "Prior 10th percentile", "Maximum named regret"] + named, rows)]
    benchmark_count = len(g2.get("candidates", g2["ranking"]))
    sections.append("Game 1 scores and unrestricted scenario best responses are exact. Game 2 search means are Monte Carlo estimates; "
                    f"its regret is measured against the saved {benchmark_count}-candidate benchmark set "
                    "(prior leaders plus named-scenario screening leaders). Candidate-set regret is a lower bound on unrestricted regret "
                    "when evaluated exactly; the reported estimates also contain Monte Carlo error.")

    decision = final["decision"]
    sections += ["## Decision and provenance", f"Game 2 paired prior leader-minus-runner-up interval: "
        f"{interval(decision['paired_prior_mean_difference'], decision['paired_prior_se'])}. "
        f"Statistical tie: {decision['statistical_tie']}. Tie-break: {decision['tie_break']}.",
        markdown_table(["Run", "Commit", "Runtime seconds", "Sample counts", "Seeds"],
                       [[run.get("id", ""), run.get("commit_sha", ""), number(run.get("runtime_seconds", 0)),
                         json.dumps(run.get("sample_counts", {}), sort_keys=True),
                         json.dumps(run.get("seeds", run.get("seed", "")), sort_keys=True)] for run in (g1,g2,final)]),
        ]
    hashes = [[run.get("id", ""), source, digest]
              for run in (g1, g2, final)
              for source, digest in run.get("implementation_source_sha256", {}).items()]
    if hashes:
        sections += ["### Implementation source SHA-256", markdown_table(["Run", "Source", "SHA-256"], hashes)]
    sections += ["## Assumptions and limits",
        "Scores are conditional on finite, seeded, hypothetical applicant populations. The fixed prior gives equal weight to its saved scenarios; "
        "it is a modeling choice rather than an empirically calibrated applicant forecast. Game 2 draws all three opponents from the same scenario. "
        "The prior Monte Carlo SE combines independent scenario errors as sqrt(sum(SE²))/number of scenarios. "
        "Intervals quantify simulation noise only; they exclude uncertainty about applicant behavior, population construction, "
        "and candidate selection. Game 1 exact intervals are degenerate because no Monte Carlo is used to compute the expectation. "
        "Game 2 rank probabilities divide tied occupied ranks equally and do not give the probability of sole first. "
        "Finalists were chosen using search runs; only fresh validation estimates should be quoted as final scores. "
        "Search did not establish a global Game 2 optimum, and candidate-set regret may understate true regret. "
        "One-million-group checks do not resolve uncertainty about the real applicant pool."]
    return "\n\n".join(sections) + "\n", records


def supplemental_equilibrium_table(audit):
    """Render the optional, post-search stress separately from primary results."""
    rows, records = [], []
    for i, (candidate, mean) in enumerate(zip(audit["candidates"], audit["means"])):
        rows.append([i, allocation(candidate), number(mean)])
        records.append(dict(table="supplemental_g1_equilibrium", game=1,
                            scenario="supplemental_exact_best_response_fictitious_play",
                            candidate=allocation(candidate), candidate_index=i, mean=mean, se=0.0,
                            ci95_low=mean, ci95_high=mean))
    certificate = audit["certificate"]
    text = "\n\n".join([
        "## Supplemental Game 1 equilibrium-like stress: not used for primary selection",
        f"CX-061 uses exact-best-response fictitious play outside the frozen prior and holdouts. "
        f"The empirical pool has self-play score {number(certificate['empirical_self_play_score'])}; "
        f"its unrestricted best response scores {number(certificate['exact_best_response_score'])}, "
        f"for exploitability {number(certificate['exact_exploitability_above_symmetric_value'])}. "
        "The certificate is conditional on this finite pool and does not establish an exact Nash equilibrium "
        "or describe the real applicant population. Scores below concern the previously fixed CX-020 finalists; "
        "they do not replace the preregistered primary decision.",
        markdown_table(["CX-020 finalist index", "Allocation", "Exact castle-point expectation"], rows)])
    return text+"\n", records


def population_seed_stability_tables(audit, final):
    """CX-063 near-leader sensitivity, keeping MC and between-seed spread apart."""
    if not audit.get("complete"):
        return "", []
    candidates, replicas, summary = audit["candidates"], audit["replicas"], audit["summary"]
    missing = [x for x in final["candidates"]["g2"] if x not in candidates]
    rows, records = [], []
    sections = ["## Supplemental Game 2 near-leader population-row-seed stability (CX-063)",
        "This diagnostic covers the exact seven saved near-leader allocations below, not the complete corrected finalist set. "
        "It predates the corrected promotion artifact and does not cover its fifth corrected candidate. "
        "The primary decision in CX-050 remains authoritative. Population-row seeds change the finite applicant rows while "
        "preserving scenario weights, parameters, and the strategic library. "
        f"Each replica uses {audit['sample_counts']['groups_per_candidate_per_scenario_per_replica']:,} groups per candidate "
        f"per prior scenario across {audit['sample_counts']['prior_scenarios']} prior scenarios. "
        "Monte Carlo intervals below are conditional on one fixed row-population replica. Across the three row seeds, "
        "SD and min/max are descriptive sensitivity diagnostics, not confidence intervals or uncertainty bounds for real applicants."]
    if missing:
        sections.append("Frozen CX-050 finalists absent from this near-leader diagnostic: " + ", ".join(map(allocation, missing)) + ".")
    for i, candidate in enumerate(candidates):
        means = [replica["mean"][i] for replica in replicas]
        rows.append([i, allocation(candidate)] + [number(x) for x in means] + [
            number(summary["mean_over_three_row_replicas"][i]),
            number(summary["row_replica_sd_of_240_scenario_average"][i]),
            f"[{number(summary['row_replica_range_low'][i])}, {number(summary['row_replica_range_high'][i])}]"])
        records.append(dict(table="nearleader_row_seed_spread", game=2, candidate=allocation(candidate), candidate_index=i,
            mean=summary["mean_over_three_row_replicas"][i], row_seed_sd=summary["row_replica_sd_of_240_scenario_average"][i],
            range_low=summary["row_replica_range_low"][i], range_high=summary["row_replica_range_high"][i]))
    sections.append(markdown_table(["Index", "Near-leader allocation"] +
        [f"Prior mean, row seed {r['population_seed_base']}" for r in replicas] +
        ["Mean of three seeds", "Three-seed SD", "Three-seed min/max (not CI)"], rows))
    mc_rows, paired_rows = [], []
    for replica in replicas:
        base = replica["population_seed_base"]
        for i, candidate in enumerate(candidates):
            mean, se = replica["mean"][i], replica["mc_se"][i]
            mc_rows.append([base, i, number(mean), number(se), interval(mean, se)])
            records.append(dict(table="nearleader_row_seed_mc", game=2, scenario="prior_average", population_seed_base=base,
                candidate=allocation(candidate), candidate_index=i, mean=mean, se=se,
                ci95_low=mean-1.96*se, ci95_high=mean+1.96*se))
        for a in range(len(candidates)):
            for b in range(a+1,len(candidates)):
                mean = replica["pairwise_mean_difference"][a][b]
                se = replica["pairwise_mc_se"][a][b]
                paired_rows.append([base, f"{a} minus {b}", number(mean), number(se), interval(mean,se)])
                records.append(dict(table="nearleader_row_seed_paired_mc", game=2, scenario="prior_average",
                    population_seed_base=base, candidate=f"{a} minus {b}", mean=mean, se=se,
                    ci95_low=mean-1.96*se, ci95_high=mean+1.96*se))
    sections += ["### Within-row-seed Monte Carlo intervals", markdown_table(
        ["Population seed base", "Candidate index", "Prior mean", "MC SE", "MC 95% interval"], mc_rows),
        "### Paired near-leader gaps on common opponent groups", markdown_table(
        ["Population seed base", "Candidate indices", "Paired prior gap", "Paired MC SE", "MC 95% interval"], paired_rows)]
    spread_rows = []
    for a in range(len(candidates)):
        for b in range(a+1,len(candidates)):
            sd = summary["paired_row_replica_sd_of_240_scenario_average"][a][b]
            lo, hi = (summary[k][a][b] for k in ("paired_row_replica_difference_range_low", "paired_row_replica_difference_range_high"))
            spread_rows.append([f"{a} minus {b}", number(sd), f"[{number(lo)}, {number(hi)}]"])
            records.append(dict(table="nearleader_paired_row_seed_spread", game=2,candidate=f"{a} minus {b}",
                                row_seed_sd=sd,range_low=lo,range_high=hi))
    sections += ["### Paired-gap spread across three row seeds", markdown_table(
        ["Candidate indices", "Three-seed gap SD", "Three-seed gap min/max (not CI)"], spread_rows)]
    return "\n\n".join(sections)+"\n", records


def holdout_population_seed_tables(audit, final):
    """Render a completed CX-064 supplement; never generate or evaluate holdouts."""
    if not audit.get("complete"):
        return "", []
    if audit["candidates"] != final["candidates"] or audit["primary_decision_unchanged"] != final["decision"]:
        raise ValueError("CX-064 candidates or primary decision differ from authoritative CX-050")
    replicas = audit["replicas"]
    selected = audit["primary_decision_unchanged"]
    records = []
    sections = ["## Supplemental fixed-finalist holdout row-seed validation (CX-064)",
        "This completed supplement evaluates the frozen CX-050 finalists on the original holdout rows and two extra row-population seeds. "
        "The original scores are copied from CX-050. It does not search, tune, or choose allocations from holdout behavior. "
        "CX-050 remains the authoritative primary decision. Three-seed SD and range are descriptive model-seed sensitivity diagnostics, "
        "not inferential confidence intervals. The separately labeled Monte Carlo intervals are conditional on fixed finite-row populations."]
    for name in audit["scenarios"]:
        summary = audit["holdout_summary"][name]
        rows = []
        for game in (1,2):
            values = summary[f"g{game}_three_row_seed_" + ("exact_scores" if game==1 else "means")]
            for i, candidate in enumerate(audit["candidates"][f"g{game}"]):
                mean = summary[f"g{game}_mean_across_row_seeds"][i]
                sd = summary[f"g{game}_row_seed_sd"][i]
                lo, hi = (summary[f"g{game}_row_seed_range_{bound}"][i] for bound in ("low","high"))
                rows.append([game, i, allocation(candidate), "yes" if i==selected[f"g{game}_index"] else ""]+
                            [number(seed_values[i]) for seed_values in values]+[number(mean),number(sd),f"[{number(lo)}, {number(hi)}]"])
                records.append(dict(table="holdout_row_seed_spread",game=game,scenario=name,candidate=allocation(candidate),
                    candidate_index=i,selected=i==selected[f"g{game}_index"],mean=mean,row_seed_sd=sd,range_low=lo,range_high=hi))
        sections += [f"### {name}: three-row-seed score sensitivity", markdown_table(
            ["Game","Index","Frozen allocation","Primary pick"]+
            [f"Score, row seed {r['population_seed_base']}" for r in replicas]+
            ["Mean of three seeds","Three-seed SD","Three-seed min/max (not CI)"],rows)]
        mc_rows, pair_rows = [], []
        for replica_index, replica in enumerate(replicas):
            detail = next(x for x in replica["scenario_results"] if x["name"]==name)
            base = replica["population_seed_base"]
            for i, candidate in enumerate(audit["candidates"]["g2"]):
                mean, se = detail["mean"][i], detail["mc_se"][i]
                mc_rows.append([base,i,number(mean),number(se),interval(mean,se),detail["groups"]])
                records.append(dict(table="holdout_row_seed_mc",game=2,scenario=name,population_seed_base=base,
                    candidate=allocation(candidate),candidate_index=i,mean=mean,se=se,ci95_low=mean-1.96*se,ci95_high=mean+1.96*se))
                gap = summary["g2_paired_difference_vs_primary_by_row_seed"][replica_index][i]
                gap_se = summary["g2_paired_mc_se_by_row_seed"][replica_index][i]
                pair_rows.append([base,f"{i} minus primary {selected['g2_index']}",number(gap),number(gap_se),interval(gap,gap_se)])
                records.append(dict(table="holdout_row_seed_paired_mc",game=2,scenario=name,population_seed_base=base,
                    candidate=f"{i} minus primary {selected['g2_index']}",mean=gap,se=gap_se,
                    ci95_low=gap-1.96*gap_se,ci95_high=gap+1.96*gap_se))
        sections += [f"### {name}: conditional Game 2 Monte Carlo intervals",markdown_table(
            ["Population seed base","Candidate index","Mean payout","MC SE","MC 95% interval","Groups"],mc_rows),
            f"### {name}: paired gaps versus the frozen primary pick",markdown_table(
            ["Population seed base","Candidate indices","Paired gap","Paired MC SE","MC 95% interval"],pair_rows)]
        spread_rows=[]
        for i in range(len(audit["candidates"]["g2"])):
            sd=summary["g2_paired_row_seed_sd"][i]
            lo,hi=(summary[f"g2_paired_row_seed_range_{bound}"][i] for bound in ("low","high"))
            spread_rows.append([f"{i} minus primary {selected['g2_index']}",number(sd),f"[{number(lo)}, {number(hi)}]"])
            records.append(dict(table="holdout_paired_row_seed_spread",game=2,scenario=name,
                candidate=f"{i} minus primary {selected['g2_index']}",row_seed_sd=sd,range_low=lo,range_high=hi))
        sections += [f"### {name}: paired-gap spread across three row seeds",markdown_table(
            ["Candidate indices","Three-seed gap SD","Three-seed gap min/max (not CI)"],spread_rows)]
    return "\n\n".join(sections)+"\n",records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("results/experiments"))
    parser.add_argument("--output", type=Path, default=Path("results/TABLES.md"))
    parser.add_argument("--csv", type=Path, default=Path("results/tables.csv"))
    args = parser.parse_args()
    g2_phase = "031" if (args.input_dir/"CX-031.json").exists() else "030"
    runs = [json.loads((args.input_dir/f"CX-{phase}.json").read_text()) for phase in ("020", g2_phase, "050")]
    markdown, records = render(*runs)
    supplemental = args.input_dir/"CX-061.json"
    if supplemental.exists():
        text, extra = supplemental_equilibrium_table(json.loads(supplemental.read_text()))
        markdown += "\n" + text
        records.extend(extra)
    for filename, formatter in (("CX-063.json",population_seed_stability_tables),
                                ("CX-064.json",holdout_population_seed_tables)):
        path=args.input_dir/filename
        if path.exists():
            text,extra=formatter(json.loads(path.read_text()),runs[2])
            if text:
                markdown+="\n"+text
                records.extend(extra)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for record in records for key in record))
    with args.csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {args.output} and {args.csv} ({len(records)} records)")


if __name__ == "__main__":
    main()
