#!/usr/bin/env python3
"""Fixed-contender row-population seed stability over all 240 prior scenarios.

The prior weights/parameters and strategic library seed stay fixed. Only the
finite applicant rows are regenerated. No holdout models are loaded or scored.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

os.environ.setdefault("NUMBA_NUM_THREADS","1")
os.environ.setdefault("OMP_NUM_THREADS","1")
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import numpy as np
from castles.engine import _payouts, g2_sample_opponents
from castles.populations import Population, get_population, list_scenarios, POP_VERSION
from castles.search import save_json, provenance
from castles.snapshots import load_population_snapshot, save_population_snapshot, file_sha256


def stable_union(rows):
    seen=set();out=[]
    for row in rows:
        key=tuple(int(v) for v in row)
        if key not in seen:
            seen.add(key);out.append(key)
    return np.asarray(out,dtype=np.int64)


def candidate_union(search):
    rows=list(search['finalists'])+[[0,0,48,52,0]]
    for record in search.get('local_rounds',[]):
        rows += [record[k] for k in ('leader','runner_up') if k in record]
    result=stable_union(rows)
    if len(result)>10:
        raise ValueError('More than10 fixed candidates; inspect manually instead of dropping actual leaders')
    if result.shape[1]!=5 or np.any(result<0) or np.any(result.sum(1)!=100):
        raise ValueError('invalid fixed candidate list')
    return result


def make_or_load(path,names,base_seed,source_hash):
    if path.exists():
        populations,manifest=load_population_snapshot(path,names,base_seed,source_hash,Population)
        return populations,manifest,False
    populations={}
    for i,name in enumerate(names):
        populations[name]=get_population(name,base_seed+i)
        if i%50==0:
            print(f'building seedbase{base_seed}: {i+1}/{len(names)}',flush=True)
    manifest=save_population_snapshot(path,populations,base_seed,source_hash)
    # Round-trip through strict checksum validation before using new snapshots.
    populations,manifest=load_population_snapshot(path,names,base_seed,source_hash,Population)
    return populations,manifest,True


def evaluate(candidates,populations,prior,n,draw_base):
    k=len(candidates);m=len(prior)
    means=np.empty((m,k));covariances=np.empty((m,k,k));details=[]
    for i,name in enumerate(prior):
        opponents=g2_sample_opponents(populations[name],n,draw_base+i)
        scores=np.asarray([_payouts(x,opponents)[0].astype(float)/12 for x in candidates])
        means[i]=scores.mean(1)
        covariances[i]=np.cov(scores,ddof=1)/n
        details.append(dict(name=name,population_seed=populations[name].seed,
                            draw_seed=draw_base+i,mean=means[i],
                            mc_se=np.sqrt(np.diag(covariances[i]))))
        if i%40==0:
            print(f'drawbase{draw_base}: {i+1}/{m}',flush=True)
    aggregate=means.mean(0)
    aggregate_cov=covariances.sum(0)/m**2
    pair_diff=aggregate[:,None]-aggregate[None,:]
    pair_var=np.maximum(0,np.diag(aggregate_cov)[:,None]+np.diag(aggregate_cov)[None,:]-2*aggregate_cov)
    pair_se=np.sqrt(pair_var)
    return dict(mean=aggregate,ranking=np.argsort(-aggregate),
                mc_se=np.sqrt(np.diag(aggregate_cov)),
                pairwise_mean_difference=pair_diff,pairwise_mc_se=pair_se,
                pairwise_mc_ci95_low=pair_diff-1.96*pair_se,
                pairwise_mc_ci95_high=pair_diff+1.96*pair_se,
                scenario_results=details),means,aggregate_cov


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--search',default='results/experiments/CX-030.json')
    parser.add_argument('--groups',type=int,default=200000)
    parser.add_argument('--output',default='results/experiments/CX-063.json')
    args=parser.parse_args()
    start=time.perf_counter()
    root=Path(__file__).resolve().parents[1]
    os.chdir(root)
    search_path=Path(args.search)
    search_hash=file_sha256(search_path)
    search=json.loads(search_path.read_text())
    candidates=candidate_union(search)
    prior=list_scenarios('prior');training=list_scenarios('named')+prior
    if len(prior)!=240:
        raise ValueError('Expected original240-prior design')
    source_path=Path('src/castles/populations.py')
    source_hash=file_sha256(source_path)
    original_path=Path('results/frozen_populations/training.npz')
    original,original_manifest=load_population_snapshot(original_path,training,110300,source_hash,Population)
    report=provenance('CX-063','Game2 fixed-contender row-population stability',
        generated_at=datetime.now(timezone.utc).isoformat(),
        candidates=candidates,scenarios=prior,seeds=dict(population_seed_bases=[110300,210300,310300],
        draw_seed_bases=[630000,640000,650000]),
        sample_counts=dict(groups_per_candidate_per_scenario_per_replica=args.groups,
                           prior_scenarios=len(prior),replicas=3),
        source_search_path=str(search_path),source_search_sha256=search_hash,
        population_module_sha256=source_hash,population_version=POP_VERSION,
        python_version=platform.python_version(),numpy_version=np.__version__,
        replicas=[],notes=[
            'Fixed candidate list from pre-holdout search; no candidate search or holdout evaluation here.',
            'The original240 prior weights, parameters and lib_seed1 are fixed in every replica.',
            'Each group draws all3 applicants from its own scenario, with CRN across candidates.',
            'MC confidence intervals are conditional on each fixed finite-row model.',
            'Only3 row-population replicas: between-replica SD/range are rough diagnostics, not reliable confidence intervals.',
            'Per-scenario variation is distinct from variation of the equally weighted240-scenario average.',
            'These checks do not change prior specification or primary decision rule.'])
    scenario_means=[];aggregate_covariances=[];metadata_reference=None
    for replica,(base_seed,draw_base) in enumerate(zip([110300,210300,310300],[630000,640000,650000])):
        if replica==0:
            populations,manifest,path=original,original_manifest,original_path
        else:
            path=Path(f'results/frozen_populations/training_row_seed_{base_seed}.npz')
            populations,manifest,_=make_or_load(path,training,base_seed,source_hash)
        # Strictly verify that a new row seed did not mutate the model weights,
        # parameters, strategic library seed, or per-archetype row counts.
        for name in prior:
            for key in ['weights','params','lib_seed']:
                if populations[name].meta[key]!=original[name].meta[key]:
                    raise ValueError(f'model parameter drift in {name}/{key}')
            if populations[name].meta['lib_seed']!=1:
                raise ValueError('Prior strategic library must remain1')
            if populations[name].g1.shape!=original[name].g1.shape:
                raise ValueError('row count changed')
        r,means,cov=evaluate(candidates,populations,prior,args.groups,draw_base)
        r.update(population_seed_base=base_seed,draw_seed_base=draw_base,
                 snapshot_path=str(path),snapshot_archive_sha256=manifest['archive_sha256'],
                 snapshot_manifest_sha256=file_sha256(path.with_suffix('.manifest.json')),
                 population_source_sha256=manifest['source_sha256'])
        report['replicas'].append(r)
        scenario_means.append(means);aggregate_covariances.append(cov)
        report['runtime_seconds']=time.perf_counter()-start
        save_json(args.output,report)
        print(f'replica{replica}: means={r["mean"]}; ranking={r["ranking"]}',flush=True)
    seed_means=np.asarray([r['mean'] for r in report['replicas']])
    all_scenario=np.asarray(scenario_means)
    aggregate_seed_diff=seed_means[:,:,None]-seed_means[:,None,:]
    pair_seed_sd=aggregate_seed_diff.std(0,ddof=1)
    pair_monte_carlo_var=np.mean([np.diag(c)[:,None]+np.diag(c)[None,:]-2*c for c in aggregate_covariances],axis=0)
    # Subtract estimated MC noise only as a rough variance diagnostic. With3
    # replicas zero after clipping does NOT establish no model uncertainty.
    corrected_sd=np.sqrt(np.maximum(0,pair_seed_sd**2-pair_monte_carlo_var))
    report['summary']=dict(
        mean_over_three_row_replicas=seed_means.mean(0),
        ranking_of_three_replica_average=np.argsort(-seed_means.mean(0)),
        row_replica_sd_of_240_scenario_average=seed_means.std(0,ddof=1),
        row_replica_range_low=seed_means.min(0),row_replica_range_high=seed_means.max(0),
        paired_row_replica_sd_of_240_scenario_average=pair_seed_sd,
        paired_rough_mc_variance_subtracted_row_sd=corrected_sd,
        paired_row_replica_difference_range_low=aggregate_seed_diff.min(0),
        paired_row_replica_difference_range_high=aggregate_seed_diff.max(0),
        per_scenario_row_replica_sd_mean=all_scenario.std(0,ddof=1).mean(0),
        per_scenario_row_replica_sd_max=all_scenario.std(0,ddof=1).max(0),
        warning='Three replicas only: SD/range are sensitivity diagnostics, not inferential CIs or uncertainty about real applicants.')
    if file_sha256(source_path)!=source_hash:
        raise RuntimeError('Population source changed during run; saved replica outputs remain identifiable but comparison requires review')
    report['runtime_seconds']=time.perf_counter()-start
    report['complete']=True
    save_json(args.output,report)
    print('complete',args.output,'seconds',report['runtime_seconds'],flush=True)


if __name__=='__main__':
    main()
