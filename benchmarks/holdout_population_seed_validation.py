#!/usr/bin/env python3
"""Supplement fixed-finalist holdout validation with two fresh applicant-row seeds.

Requires completed primary CX-050 and its frozen holdout archive. Does not search,
rank for selection, change priors, or override the primary decision. Run only
after the parent has completed finalist preregistration and opened holdouts.
"""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import sys
import json
import time

os.environ.setdefault('NUMBA_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'benchmarks'))
import numpy as np
from castles.engine import g1_exact,g1_marginals
from castles.populations import Population,get_population,POP_VERSION
from castles.search import save_json,provenance
from castles.snapshots import load_population_snapshot,file_sha256
from population_seed_stability import make_or_load,evaluate


def baseline_covariance(validation,name,k):
    """Recover covariance of sample means from marginal and paired SEs."""
    variances=np.asarray(validation['g2'][name]['se'])**2
    cov=np.diag(variances)
    for a in range(k):
        for b in range(a+1,k):
            dvar=validation['paired_g2'][name][f'{a}-{b}']['se']**2
            cov[a,b]=cov[b,a]=(variances[a]+variances[b]-dvar)/2
    return cov


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--validation',default='results/experiments/CX-050.json')
    parser.add_argument('--preregistration',default='research/log/CX-050-preregistration.json')
    parser.add_argument('--groups',type=int,default=1000000)
    parser.add_argument('--output',default='results/experiments/CX-064.json')
    args=parser.parse_args()
    if args.groups<1000000:
        raise ValueError('Supplemental holdout validation requires at least1m groups per candidate per scenario')
    os.chdir(ROOT);start=time.perf_counter()
    validation_path=Path(args.validation);prereg_path=Path(args.preregistration)
    validation=json.loads(validation_path.read_text());prereg=json.loads(prereg_path.read_text())
    candidates=np.asarray(prereg['finalists_g2'],dtype=np.int64)
    g1candidates=np.asarray(prereg['finalists_g1'],dtype=np.int64)
    if not np.array_equal(validation['candidates']['g2'],candidates) or not np.array_equal(validation['candidates']['g1'],g1candidates):
        raise ValueError('Primary validation does not match frozen finalists')
    if 'decision' not in validation:
        raise ValueError('Primary validation must be complete before this supplement')
    names=prereg['holdout']
    source_hash=file_sha256('src/castles/populations.py')
    if validation['implementation_source_sha256']['src/castles/populations.py']!=source_hash:
        raise ValueError('Population source differs from completed primary validation')
    original_path=Path('results/frozen_populations/holdout.npz')
    original_manifest=json.loads(original_path.with_suffix('.manifest.json').read_text())
    base_seed=original_manifest['base_seed']
    if base_seed!=110549:
        raise ValueError('Unexpected primary holdout seedbase; review requested extra seed plan')
    original,original_manifest=load_population_snapshot(original_path,names,base_seed,source_hash,Population)
    fixed_index=int(validation['decision']['g2_index'])
    report=provenance('CX-064','supplemental fixed-finalist holdout row-seed validation',
        generated_at=datetime.now(timezone.utc).isoformat(),
        candidates=dict(g1=g1candidates,g2=candidates),scenarios=names,
        seeds=dict(population_seed_bases=[110549,210549,310549],extra_draw_seed_bases=[664000,665000]),
        sample_counts=dict(row_population_replicas_per_holdout=3,groups_per_candidate_per_scenario_per_extra_replica=args.groups),
        primary_validation_path=str(validation_path),primary_validation_sha256=file_sha256(validation_path),
        preregistration_path=str(prereg_path),preregistration_sha256=file_sha256(prereg_path),
        population_source_sha256=source_hash,population_version=POP_VERSION,
        supplemental_script_sha256=file_sha256(__file__),helper_script_sha256=file_sha256('benchmarks/population_seed_stability.py'),
        primary_decision_unchanged=validation['decision'],replicas=[],
        notes=[
            'Supplemental sensitivity evidence only. No holdout-based candidate selection or parameter tuning.',
            'The original holdout scores are copied exactly from completed CX-050, not replaced or rescored.',
            'Extra row-population seeds preserve each holdout specification, weights, parameters and strategic library seed2.',
            'Every candidate gets the same1m opponent triples per scenario per fresh row-population replicate.',
            'Three row-population seeds give rough SD/range diagnostics, not reliable model-uncertainty confidence intervals.',
            'Monte Carlo SEs and intervals remain conditional on fixed finite-row populations.',
            'The primary decision and prior objective remain unchanged.'])
    # Incorporate the primary frozen-model holdout results with their exact
    # paired MC errors and original draw seeds. No new groups are drawn here.
    first_means=np.asarray([validation['g2'][name]['mean'] for name in names])
    first_cov=np.asarray([baseline_covariance(validation,name,len(candidates)) for name in names])
    first_g1=np.asarray([validation['g1_exact'][name] for name in names])
    original_details=[]
    for i,name in enumerate(names):
        if validation['g2'][name]['groups']<1000000:
            raise ValueError('Primary holdout has fewer than1m groups')
        original_details.append(dict(name=name,population_seed=original[name].seed,
            draw_seed=validation['g2'][name]['seed'],groups=validation['g2'][name]['groups'],
            mean=first_means[i],mc_se=validation['g2'][name]['se'],g1_exact=first_g1[i]))
    report['replicas'].append(dict(population_seed_base=base_seed,
        snapshot_path=str(original_path),snapshot_archive_sha256=original_manifest['archive_sha256'],
        snapshot_manifest_sha256=file_sha256(original_path.with_suffix('.manifest.json')),
        scenario_results=original_details,source='Copied from completed primary CX-050'))
    all_means=[first_means];all_cov=[first_cov];all_g1=[first_g1]
    for base_seed,draw_base in [(210549,664000),(310549,665000)]:
        path=Path(f'results/frozen_populations/holdout_row_seed_{base_seed}.npz')
        populations,manifest,_=make_or_load(path,names,base_seed,source_hash)
        for name in names:
            for key in ['weights','params','lib_seed']:
                if populations[name].meta[key]!=original[name].meta[key]:
                    raise ValueError(f'Holdout parameter drift in {name}/{key}')
            if populations[name].meta['lib_seed']!=2 or populations[name].g2.shape!=original[name].g2.shape:
                raise ValueError('Holdout library seed or row count changed')
        result,means,aggregate_cov=evaluate(candidates,populations,names,args.groups,draw_base)
        exact1=np.asarray([g1_exact(g1candidates,g1_marginals(populations[name])) for name in names])
        # evaluate() stores the scenario-level SEs but only returns aggregate
        # covariance. Reconstruct per-scenario pair covariances explicitly by
        # retaining the same CRN draw seeds and payouts, without fresh sampling.
        # A separate helper below calculates these at the same time on rerun;
        # only scenario paired differences vs the fixed primary pick are needed.
        from castles.engine import _payouts,g2_sample_opponents
        covs=[]
        for i,name in enumerate(names):
            opps=g2_sample_opponents(populations[name],args.groups,draw_base+i)
            scores=np.asarray([_payouts(x,opps)[0].astype(float)/12 for x in candidates])
            covs.append(np.cov(scores,ddof=1)/args.groups)
            result['scenario_results'][i].update(groups=args.groups,g1_exact=exact1[i])
        result.update(population_seed_base=base_seed,draw_seed_base=draw_base,
            snapshot_path=str(path),snapshot_archive_sha256=manifest['archive_sha256'],
            snapshot_manifest_sha256=file_sha256(path.with_suffix('.manifest.json')))
        # Descriptive aggregate ranking from the shared helper is removed: this
        # supplement reports held-out behavior without choosing a new strategy.
        result.pop('ranking',None)
        report['replicas'].append(result)
        all_means.append(means);all_cov.append(np.asarray(covs));all_g1.append(exact1)
        report['runtime_seconds']=time.perf_counter()-start
        save_json(args.output,report)
    all_means=np.asarray(all_means);all_cov=np.asarray(all_cov);all_g1=np.asarray(all_g1)
    paired=all_means-all_means[:,:,fixed_index,None]
    pair_var=np.maximum(0,np.diagonal(all_cov,axis1=2,axis2=3)+all_cov[:,:,fixed_index,fixed_index,None]-2*all_cov[:,:,:,fixed_index])
    paired_mc_se=np.sqrt(pair_var)
    report['holdout_summary']={}
    for i,name in enumerate(names):
        report['holdout_summary'][name]=dict(
            g2_three_row_seed_means=all_means[:,i],g2_mean_across_row_seeds=all_means[:,i].mean(0),
            g2_row_seed_sd=all_means[:,i].std(0,ddof=1),
            g2_row_seed_range_low=all_means[:,i].min(0),g2_row_seed_range_high=all_means[:,i].max(0),
            g2_paired_difference_vs_primary_by_row_seed=paired[:,i],
            g2_paired_mc_se_by_row_seed=paired_mc_se[:,i],
            g2_paired_row_seed_sd=paired[:,i].std(0,ddof=1),
            g2_paired_row_seed_range_low=paired[:,i].min(0),g2_paired_row_seed_range_high=paired[:,i].max(0),
            g1_three_row_seed_exact_scores=all_g1[:,i],g1_mean_across_row_seeds=all_g1[:,i].mean(0),
            g1_row_seed_sd=all_g1[:,i].std(0,ddof=1),
            g1_row_seed_range_low=all_g1[:,i].min(0),g1_row_seed_range_high=all_g1[:,i].max(0))
    if file_sha256('src/castles/populations.py')!=source_hash:
        raise RuntimeError('Population source changed during supplement')
    report['runtime_seconds']=time.perf_counter()-start;report['complete']=True
    save_json(args.output,report)
    print('complete',args.output,'seconds',report['runtime_seconds'],flush=True)


if __name__=='__main__':
    main()
