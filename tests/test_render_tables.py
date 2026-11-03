"""Fixture checks for saved-result table calculations, with no research run."""
import importlib.util
import csv
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

spec = importlib.util.spec_from_file_location("render_tables", Path(__file__).parents[1]/"scripts/render_tables.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def test_saved_table_prior_intervals_and_exact_values(tmp_path):
    candidates = [[20]*5, [0, 0, 0, 50, 50]]
    ranking = [dict(allocation=x, prior_mean=7.5, prior_p10=7.0, max_named_regret=0.1,
                    max_named_candidate_regret=0.1, named_scores={"named": 7.4}) for x in candidates]
    g1 = dict(id="CX-020", scenarios=["named", "prior0", "prior1"], top100=ranking)
    g2 = dict(id="CX-030", ranking=ranking)
    final = dict(id="CX-050", scenarios=g1["scenarios"]+["holdout"], candidates=dict(g1=candidates,g2=candidates),
                 g1_prior_mean=[7.5, 8.0],g1_exact={"holdout":[7.0,8.5]},g1_crosschecks={},
                 g2_prior_mean=[4.5,5.0],g2_prior_mc_se=[0.1,0.2],g2={},paired_g2={},
                 decision=dict(g1_index=1,g2_index=1,paired_prior_mean_difference=0.5,paired_prior_se=0.1,
                               statistical_tie=False,tie_break="lower regret"))
    for i, name in enumerate(final["scenarios"]):
        final["g2"][name]=dict(mean=[4.0,5.0],se=[0.1,0.2],place=[[0.25]*4]*2,mean_castle_points=[4.0,5.0])
        final["paired_g2"][name]={"0-1":dict(mean=-1.0,se=0.2 if name=="prior0" else 0.4)}
    markdown, records = renderer.render(g1,g2,final)
    exact = next(r for r in records if r["table"]=="validation" and r["game"]==1 and r["scenario"]=="prior_average" and r["candidate_index"]==1)
    assert exact["mean"] == exact["ci95_low"] == exact["ci95_high"] == 8.0
    paired = next(r for r in records if r["table"]=="paired_g2" and r["scenario"]=="prior_average")
    assert paired["mean"] == -1.0
    np.testing.assert_allclose(paired["se"], np.sqrt(0.2**2+0.4**2)/2)
    assert "search" in markdown.lower() and "not final validation" in markdown
    assert "lower bound on unrestricted regret" in markdown
    assert "do not give the probability of sole first" in markdown
    assert "(0, 0, 0, 50, 50)" in markdown
    for phase, run in zip(("020", "030", "050"), (g1, g2, final)):
        (tmp_path/f"CX-{phase}.json").write_text(json.dumps(run))
    output, csv_path = tmp_path/"tables.md", tmp_path/"scores.csv"
    subprocess.run([sys.executable, str(Path(__file__).parents[1]/"scripts/render_tables.py"),
                    "--input-dir", str(tmp_path), "--output", str(output), "--csv", str(csv_path)], check=True)
    assert output.read_text() == markdown
    with csv_path.open(newline="") as stream:
        exported = list(csv.DictReader(stream))
    assert len(exported) == len(records)


def test_supplemental_stress_stays_separate_from_primary():
    text, rows = renderer.supplemental_equilibrium_table(dict(
        candidates=[[20]*5], means=[7.51], certificate=dict(
            empirical_self_play_score=7.5, exact_best_response_score=7.549,
            exact_exploitability_above_symmetric_value=0.049)))
    assert "not used for primary selection" in text
    assert "0.049000" in text
    assert rows[0]["table"] == "supplemental_g1_equilibrium"
    assert rows[0]["ci95_low"] == rows[0]["mean"] == rows[0]["ci95_high"]
