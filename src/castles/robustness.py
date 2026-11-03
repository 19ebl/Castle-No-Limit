"""Targeted counter-populations and transparent population sensitivity checks.

These stress tests are conditional scenarios, never empirical applicant forecasts.
Counter searches are in-sample; reported damage uses fresh independent draws.
"""
from dataclasses import dataclass
from itertools import combinations
import numpy as np
from .engine import (all_allocations, g1_exact, g1_marginals, g1_table,
                     g1_top, g2_eval, g2_sample_opponents, _payouts)


@dataclass
class StressPopulation:
    name: str
    seed: int
    g1: np.ndarray
    g2: np.ndarray
    w: np.ndarray


def combine_populations(populations, weights, name="sensitivity", seed=0):
    """Mix applicants within one scenario, NOT scores across scenario beliefs."""
    weights = np.asarray(weights, dtype=float)
    if len(weights) != len(populations) or not np.isfinite(weights).all() or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("invalid mixture weights")
    weights = weights/weights.sum()
    return StressPopulation(name, seed,
                            np.concatenate([p.g1 for p in populations]),
                            np.concatenate([p.g2 for p in populations]),
                            np.concatenate([p.w * w for p,w in zip(populations,weights)]))


def _jitter_bank(anchors, seed, copies=16):
    rng = np.random.default_rng(seed)
    bank = np.repeat(np.asarray(anchors, dtype=np.int16), copies, axis=0)
    # Retain anchor itself and generate budget-preserving +/-1..3 offsets.
    for i in range(len(bank)):
        for _ in range(int(rng.integers(0, 4))):
            a,b = rng.choice(5,2,replace=False)
            amount = min(int(bank[i,a]), int(rng.integers(1,4)))
            bank[i,a] -= amount
            bank[i,b] += amount
    return np.unique(bank,axis=0)


def _target_candidates(leader):
    leader = np.asarray(leader,dtype=np.int16)
    bank = [all_allocations(10), leader[None,:]]
    edges = []
    for count in range(1,6):
        for subset in combinations(range(5),count):
            x = np.zeros(5,dtype=np.int16)
            x[list(subset)] = leader[list(subset)]+1
            if x.sum() <= 100:
                leftover = 100-int(x.sum())
                for recipient in range(5):
                    y=x.copy()
                    y[recipient] += leftover
                    edges.append(y)
    if edges:
        bank.append(np.asarray(edges))
    return np.unique(np.concatenate(bank),axis=0)


def g1_counter_bank(leader, seed=84001, k=8):
    """Noisy near-best responses to a point mass at the proposed leader."""
    leader = np.asarray(leader,dtype=np.int16)
    # Opponent score is exactly 15 minus leader score in Game 1.
    m = np.zeros((5,101))
    m[np.arange(5),leader]=1
    anchors,_ = g1_top(g1_table(m), k)
    return _jitter_bank(anchors,seed)


def g2_counter_bank(leader, base, seed=85001, search_groups=3000):
    """Find counters that damage leader when 40% of applicants use them.

    This models all three opponents as independent applicants from the same
    mixture. It does not force a single coordinating counter into every group.
    """
    rng = np.random.default_rng(seed)
    candidates = _target_candidates(leader)
    raw = g2_sample_opponents(base,search_groups,seed+1)
    replace = rng.random((search_groups,3)) < .4
    means=[]
    for counter in candidates:
        opps=raw.copy()
        opps[replace]=counter
        means.append(g2_eval([leader],opps)["mean"][0])
    top=candidates[np.argsort(means)[:12]]
    # Fresh samples for a second-stage counter race.
    raw = g2_sample_opponents(base,search_groups*4,seed+2)
    replace = rng.random((search_groups*4,3)) < .4
    race=[]
    for counter in top:
        opps=raw.copy()
        opps[replace]=counter
        race.append(g2_eval([leader],opps)["mean"][0])
    anchors=top[np.argsort(race)[:4]]
    return _jitter_bank(anchors,seed+3), {
        "candidate_count":len(candidates),"screen_groups":search_groups,
        "race_groups":search_groups*4,"search_seed":seed,
        "anchor_counters":anchors.tolist(),"objective":"minimize leader payout at 40% counter share"}


def _counter_population(bank, name, seed):
    return StressPopulation(name,seed,bank,bank,np.full(len(bank),1/len(bank)))


def red_team(finalists_g1, finalists_g2, base, seed=86001, n=100000, shares=(.2,.4)):
    """Return exact G1 stress scores and fresh paired G2 damage intervals."""
    g1rows,g2rows=[],[]
    for i,leader in enumerate(np.asarray(finalists_g1,dtype=np.int16)):
        bank=g1_counter_bank(leader,seed+i)
        counter=_counter_population(bank,"targeted_g1_counter",seed+i)
        original=float(g1_exact([leader],g1_marginals(base))[0])
        for share in shares:
            stressed=combine_populations([base,counter],[1-share,share])
            score=float(g1_exact([leader],g1_marginals(stressed))[0])
            g1rows.append({"allocation":leader.tolist(),"counter_share":share,
                           "base_score":original,"stress_score":score,"damage":original-score,
                           "counter_bank_size":len(bank),"counter_examples":bank[:5].tolist(),
                           "exact":True})
    rng=np.random.default_rng(seed+10000)
    for i,leader in enumerate(np.asarray(finalists_g2,dtype=np.int16)):
        bank,search_info=g2_counter_bank(leader,base,seed+100+i)
        raw=g2_sample_opponents(base,n,seed+200+i)
        # Reuse underlying groups and uniforms across stress shares for a paired
        # baseline comparison; final draws are distinct from counter search.
        uniforms=rng.random((n,3))
        alternatives=bank[rng.integers(len(bank),size=(n,3))]
        baseline=_payouts(leader,raw)[0].astype(float)/12
        for share in shares:
            mixed=raw.copy()
            mixed[uniforms<share]=alternatives[uniforms<share]
            stress=_payouts(leader,mixed)[0].astype(float)/12
            damage=baseline-stress
            mean=float(damage.mean())
            se=float(damage.std(ddof=1)/np.sqrt(n))
            g2rows.append({"allocation":leader.tolist(),"counter_share":share,
                           "base_score":float(baseline.mean()),"stress_score":float(stress.mean()),
                           "damage":mean,"damage_se":se,"damage_ci95":[mean-1.96*se,mean+1.96*se],
                           "groups":n,"validation_seed":seed+200+i,
                           "counter_bank_size":len(bank),"counter_search":search_info})
    return {"g1":g1rows,"g2":g2rows,"seed":seed,
            "notes":"Conditional adversarial scenarios, not calibrated applicant forecasts; no holdout tuning."}


def sensitivity(finalists_g1, finalists_g2, scenarios, seed=87001, n=100000):
    """Compare a fixed candidate list across explicitly supplied scenarios.

    Callers name each scenario with its actual AI/reuse/tau assumptions. Holding
    candidate lists fixed prevents sensitivity results feeding another search.
    """
    rows=[]
    for index,(label,pop) in enumerate(scenarios.items()):
        g1=g1_exact(finalists_g1,g1_marginals(pop))
        opps=g2_sample_opponents(pop,n,seed+index)
        g2=g2_eval(finalists_g2,opps)
        payouts=[_payouts(np.asarray(x),opps)[0].astype(float)/12 for x in finalists_g2]
        differences=[]
        for scores in payouts:
            d=scores-payouts[0]
            mean,se=float(d.mean()),float(d.std(ddof=1)/np.sqrt(n))
            differences.append({"mean":mean,"se":se,"ci95":[mean-1.96*se,mean+1.96*se]})
        rows.append({"scenario":label,"g1_mean":g1.tolist(),
                     "g1_ranking":np.argsort(-g1).tolist(),
                     "g2_mean":g2["mean"].tolist(),"g2_se":g2["se"].tolist(),
                     "g2_ranking":np.argsort(-g2["mean"]).tolist(),
                     "g2_paired_difference_vs_first":differences,
                     "groups":n,"seed":seed+index})
    return rows
