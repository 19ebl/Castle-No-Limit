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


def test_nearleader_population_seed_sd_is_not_a_mc_interval():
    audit=dict(complete=True,candidates=[[20]*5,[0,0,0,50,50]],
        sample_counts=dict(groups_per_candidate_per_scenario_per_replica=200000,prior_scenarios=240),
        replicas=[dict(population_seed_base=seed,mean=[4.+i,5.+i],mc_se=[.01,.02],
            pairwise_mean_difference=[[0,-1],[1,0]],pairwise_mc_se=[[0,.03],[.03,0]])
            for i,seed in enumerate((1,2,3))],summary=dict(
                mean_over_three_row_replicas=[5.,6.],row_replica_sd_of_240_scenario_average=[1.,1.],
                row_replica_range_low=[4.,5.],row_replica_range_high=[6.,7.],
                paired_row_replica_sd_of_240_scenario_average=[[0,0],[0,0]],
                paired_row_replica_difference_range_low=[[0,-1],[1,0]],
                paired_row_replica_difference_range_high=[[0,-1],[1,0]]))
    text,rows=renderer.population_seed_stability_tables(audit,dict(candidates=dict(g2=[[1,1,1,1,96]])))
    assert "not the complete corrected finalist set" in text
    assert "fifth corrected candidate" in text
    assert "(1, 1, 1, 1, 96)" in text
    spread=next(r for r in rows if r['table']=='nearleader_row_seed_spread')
    assert spread['row_seed_sd']==1. and 'se' not in spread and 'ci95_low' not in spread
    mc=next(r for r in rows if r['table']=='nearleader_row_seed_mc')
    assert mc['se']==.01 and mc['ci95_low']==4.-1.96*.01


def test_completed_holdout_supplement_preserves_primary_and_separates_uncertainty():
    # Entirely synthetic fixture: it neither reads nor generates research holdouts.
    candidates=dict(g1=[[20]*5],g2=[[20]*5,[0,0,0,50,50]])
    decision=dict(g1_index=0,g2_index=1)
    final=dict(candidates=candidates,decision=decision)
    summary=dict(g2_three_row_seed_means=[[4.,5.],[5.,6.],[6.,7.]],
        g2_mean_across_row_seeds=[5.,6.],g2_row_seed_sd=[1.,1.],g2_row_seed_range_low=[4.,5.],g2_row_seed_range_high=[6.,7.],
        g1_three_row_seed_exact_scores=[[7.],[7.5],[8.]],g1_mean_across_row_seeds=[7.5],g1_row_seed_sd=[.5],
        g1_row_seed_range_low=[7.],g1_row_seed_range_high=[8.],
        g2_paired_difference_vs_primary_by_row_seed=[[-1.,0.]]*3,
        g2_paired_mc_se_by_row_seed=[[.03,0.]]*3,g2_paired_row_seed_sd=[0.,0.],
        g2_paired_row_seed_range_low=[-1.,0.],g2_paired_row_seed_range_high=[-1.,0.])
    audit=dict(complete=True,candidates=candidates,primary_decision_unchanged=decision,scenarios=['synthetic_holdout'],
        holdout_summary=dict(synthetic_holdout=summary),replicas=[dict(population_seed_base=i,
            scenario_results=[dict(name='synthetic_holdout',mean=[4.+i,5.+i],mc_se=[.01,.02],groups=1000000)]) for i in range(3)])
    text,rows=renderer.holdout_population_seed_tables(audit,final)
    assert "authoritative primary decision" in text
    assert "not inferential confidence intervals" in text
    spread=next(r for r in rows if r['table']=='holdout_row_seed_spread' and r['game']==1)
    assert spread['row_seed_sd']==.5 and 'se' not in spread
    paired=next(r for r in rows if r['table']=='holdout_row_seed_paired_mc')
    assert paired['mean']==-1. and paired['ci95_low']==-1.-1.96*.03
    import pytest
    with pytest.raises(ValueError,match='authoritative'):
        renderer.holdout_population_seed_tables(audit,dict(candidates=candidates,decision=dict(g1_index=0,g2_index=0)))
    assert renderer.holdout_population_seed_tables(dict(complete=False),final)==('',[])
