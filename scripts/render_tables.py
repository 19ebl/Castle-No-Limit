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
