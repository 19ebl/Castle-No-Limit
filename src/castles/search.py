"""Seeded candidate search and independent validation, with checkpointed results.

Scores are conditional on the specified applicant-population model. Monte Carlo
standard errors do not measure uncertainty about that model.
"""
from __future__ import annotations
import itertools
import hashlib
import json
from pathlib import Path
import subprocess
import time
import numpy as np
from .engine import (all_allocations, g1_exact, g1_marginals, g1_table, g1_top,
                     g2_eval, g2_sample_opponents, _payouts)


def jsonable(x):
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    if isinstance(x, dict): return {str(k):jsonable(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [jsonable(v) for v in x]
    return x


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(jsonable(obj), indent=2)+'\n')
    tmp.replace(path)


def provenance(experiment_id, game, **extra):
    commit = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
    root=Path(__file__).resolve().parents[2]
    hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
            for name in ('src/castles/engine.py','src/castles/search.py','src/castles/rules.py','src/castles/populations.py')
            if (root/name).exists()}
    return dict(id=experiment_id, agent='codex', commit_sha=commit, game=game,
                implementation_source_sha256=hashes,
                implementation='Codex search; independent implementation checks recorded separately', **extra)


def unique_allocations(*parts):
    arrays = [np.asarray(p,dtype=np.int16).reshape(-1,5) for p in parts if np.asarray(p).size]
    return np.unique(np.concatenate(arrays),axis=0) if arrays else np.empty((0,5),np.int16)


def neighbors(x, steps=(1,2,3,5,10)):
    x=np.asarray(x,dtype=np.int16)
    out=[]
    for k in steps:
        for a in range(5):
            if x[a]<k: continue
            for b in range(5):
                if a==b: continue
                y=x.copy();y[a]-=k;y[b]+=k;out.append(y)
    return unique_allocations(out)


def concentration_candidates():
    bases=[]
    values=np.arange(1,6)
    for n in (2,3,4):
        for support in itertools.combinations(range(5),n):
            if sum(values[list(support)])<8: continue
            for weights in (np.ones(n),values[list(support)]):
                raw=100*weights/weights.sum()
                y=np.zeros(5,dtype=np.int16)
                y[list(support)]=np.floor(raw).astype(np.int16)
                for j in np.argsort(-(raw-np.floor(raw)))[:100-y.sum()]:y[support[j]]+=1
                bases.append(y)
    return unique_allocations(bases, *(neighbors(x,(1,2,3)) for x in bases))


def prior_opponents(n, names, populations, seed):
    """Stratify groups across scenarios, drawing all three from one scenario.

    This preserves the nonlinear dependence on each modeled applicant pool.
    It is different from independently mixing scenario labels per opponent.
    """
    rng=np.random.default_rng(seed)
    q,r=divmod(n,len(names))
    chunks=[]
    for i,name in enumerate(names):
        count=q+(i<r)
        if count:chunks.append(g2_sample_opponents(populations[name],count,int(rng.integers(2**31))))
    return np.concatenate(chunks)


def evaluate_scenarios(candidates, names, populations, n, seed):
    results={}
    for i,name in enumerate(names):
        opps=g2_sample_opponents(populations[name],n,seed+i)
        result=g2_eval(candidates,opps)
        result.update(seed=seed+i, groups=n)
        results[name]=result
    return results


def scenario_matrix(results, names, key='mean'):
    return np.column_stack([results[name][key] for name in names])


def g1_search(populations, named, prior, output='results/experiments/CX-020.json', seed=20261103):
    started=time.perf_counter()
    names=named+prior
    marginals={name:g1_marginals(populations[name]) for name in names}
    avg=np.mean([marginals[name] for name in prior],axis=0)
    top={}
    for name in names:
        xs,ss=g1_top(g1_table(marginals[name]),100)
        top[name]=dict(candidates=xs,mean=ss)
    avg_x,avg_s=g1_top(g1_table(avg),100)
    candidates=unique_allocations(*(v['candidates'] for v in top.values()),avg_x)
    matrix=np.column_stack([g1_exact(candidates,marginals[name]) for name in names])
    primary=np.mean(matrix[:,len(named):],axis=1)
    regrets=np.array([top[name]['mean'][0] for name in named])[None,:]-matrix[:,:len(named)]
    max_regret=regrets.max(axis=1)
    order=np.lexsort((max_regret,-primary))
    finalists=candidates[order[:5]]
    top100=[]
    for idx in order[:100]:
        top100.append(dict(allocation=candidates[idx],prior_mean=primary[idx],
            prior_p10=np.quantile(matrix[idx,len(named):],.1),
            max_named_regret=max_regret[idx],named_scores=dict(zip(named,matrix[idx,:len(named)]))))
    result=provenance('CX-020',1,seed=seed,scenarios=names,sample_counts={'exact_feasible_allocations_per_scenario':4598126},
        method='Exact k-best dynamic programming for all feasible allocations; additional exact solve of prior-average marginals',
        scenario_seeds={name:populations[name].seed for name in names},
        candidates=candidates,finalists=finalists,top100=top100,
        scenario_best={name:dict(allocation=top[name]['candidates'][0],mean=top[name]['mean'][0]) for name in names},
        prior_optimum=dict(allocation=avg_x[0],mean=avg_s[0]),
        runtime_seconds=time.perf_counter()-started,
        notes=['Model scores are exact conditional on finite seeded populations; no claim that assumed populations describe actual applicants.'])
    save_json(output,result)
    return result


def g2_search(populations, named, prior, g1, output='results/experiments/CX-030.json', seed=203000):
    started=time.perf_counter()
    seeds=dict(screen=seed,race=seed+1000,local=seed+2000,confirmation=seed+3000,full=seed+10000)
    # All grid allocations, focal-count offsets, exact G1 leaders, population self-play support.
    sophisticated=[]
    for name in named:
        if 'equil' in name or 'self' in name:
            p=populations[name]
            ix=np.argsort(p.w)[-100:]
            sophisticated.append(p.g2[ix])
    candidates=unique_allocations(all_allocations(5),concentration_candidates(),
        np.array([x['allocation'] for x in g1['top100']]),*sophisticated)
    reduced=[prior[int(i)] for i in np.linspace(0,len(prior)-1,8,dtype=int)]
    screen=evaluate_scenarios(candidates,reduced+named,populations,5000,seeds['screen'])
    screen_mean=scenario_matrix(screen,reduced).mean(axis=1)
    keep=set(np.argsort(screen_mean)[-2000:].tolist())
    for name in named:keep.update(np.argsort(screen[name]['mean'])[-10:].tolist())
    raced=candidates[sorted(keep)]
    race_opps=prior_opponents(50000,prior,populations,seeds['race'])
    race=g2_eval(raced,race_opps)
    order=np.argsort(race['mean'])[::-1]
    local_starts=raced[order[:50]]
    current_starts=local_starts.copy()
    accepted=[]
    round_stats=[]
    stale_rounds=0
    leader=local_starts[0].copy()
    search_deadline=time.monotonic()+3600  # bounded independently of global owner budget
    stop_reason='ten_round_cap'
    # Every global round uses fresh local draws, fresh per-move confirmation,
    # and a third bank for the leader comparison that controls stopping.
    for round_i in range(10):
        local_opps=prior_opponents(50000,prior,populations,seeds['local']+round_i)
        old_leader=leader.copy()
        accepted_this_round=0
        for start_i,current in enumerate(current_starts):
            hood=unique_allocations([current],neighbors(current))
            res=g2_eval(hood,local_opps)
            best=hood[np.argmax(res['mean'])]
            if np.array_equal(best,current):continue
            a=_payouts(best,local_opps)[0].astype(float)
            b=_payouts(current,local_opps)[0].astype(float)
            d=(a-b)/12
            se=d.std(ddof=1)/np.sqrt(len(d))
            if d.mean()<=2*se:continue
            fresh_confirm=prior_opponents(100000,prior,populations,seeds['confirmation']+100+round_i*100+start_i)
            a=_payouts(best,fresh_confirm)[0].astype(float)
            b=_payouts(current,fresh_confirm)[0].astype(float)
            d2=(a-b)/12
            se2=d2.std(ddof=1)/np.sqrt(len(d2))
            if d2.mean()<=2*se2:continue
            accepted.append(dict(start=start_i,round=round_i,old=current.copy(),new=best.copy(),
                                 paired_gain=d.mean(),paired_se=se,confirmation_gain=d2.mean(),confirmation_se=se2))
            current_starts[start_i]=best
            accepted_this_round+=1
        leader_opps=prior_opponents(200000,prior,populations,seeds['confirmation']+2000+round_i)
        leaders=unique_allocations([old_leader],current_starts)
        leader_eval=g2_eval(leaders,leader_opps)
        leader=leaders[np.argmax(leader_eval['mean'])].copy()
        diff=(_payouts(leader,leader_opps)[0].astype(float)-_payouts(old_leader,leader_opps)[0])/12
        gain=float(diff.mean());gain_se=float(diff.std(ddof=1)/np.sqrt(len(diff)))
        statistically_tied=abs(gain)<=1.96*gain_se
        small_tied=gain<.01 and statistically_tied
        stale_rounds=stale_rounds+1 if small_tied else 0
        round_stats.append(dict(round=round_i,leader=leader.copy(),prior_mean=float(np.max(leader_eval['mean'])),
            paired_gain=gain,paired_se=gain_se,statistically_tied=statistically_tied,
            accepted=accepted_this_round,consecutive_small_tied_rounds=stale_rounds))
        if stale_rounds>=2:
            stop_reason='two_consecutive_rounds_below_0.01_and_statistically_tied'
            break
        if time.monotonic()>=search_deadline:
            stop_reason='one_hour_local_search_deadline'
            break
    # Preserve specialized named-scenario responses, even if their prior mean
    # is low, to avoid understating regret against concentrated scenarios.
    named_leaders=np.array([candidates[np.argmax(screen[name]['mean'])] for name in named])
    contenders=unique_allocations(raced[order[:200]],current_starts,[leader],named_leaders)
    confirm_opps=prior_opponents(100000,prior,populations,seeds['confirmation'])
    rerace=g2_eval(contenders,confirm_opps)
    keep=np.argsort(rerace['mean'])[::-1][:30]
    top30=unique_allocations(contenders[keep],named_leaders)
    full={}
    checkpoint=Path(output).with_suffix('.checkpoint.json')
    checkpoint_config=jsonable(dict(candidates=top30,seeds=seeds,names=named+prior,
        population_seeds={name:populations[name].seed for name in named+prior}))
    if checkpoint.exists():
        previous=json.loads(checkpoint.read_text())
        if previous.get('configuration')==checkpoint_config:
            full=previous['scenarios']
    for i,name in enumerate(named+prior):
        if name in full:continue
        opps=g2_sample_opponents(populations[name],100000,seeds['full']+i)
        full[name]=g2_eval(top30,opps)
        full[name].update(seed=seeds['full']+i,groups=100000)
        if (i+1)%20==0:
            save_json(checkpoint,dict(configuration=checkpoint_config,scenarios=full))
    prior_scores=scenario_matrix(full,prior)
    named_scores=scenario_matrix(full,named)
    primary=prior_scores.mean(axis=1)
    max_regret=(named_scores.max(axis=0)[None,:]-named_scores).max(axis=1)
    order=np.lexsort((max_regret,-primary))
    finalists=top30[order[:5]]
    ranking=[]
    for idx in order:
        ranking.append(dict(allocation=top30[idx],prior_mean=primary[idx],
            prior_mc_se=np.sqrt(sum(full[n]['se'][idx]**2 for n in prior))/len(prior),
            prior_p10=np.quantile(prior_scores[idx],.1),max_named_candidate_regret=max_regret[idx],
            named_scores=dict(zip(named,named_scores[idx]))))
    result=provenance('CX-030',2,seeds=seeds,scenarios=named+prior,scenario_seeds={n:populations[n].seed for n in named+prior},
        sample_counts=dict(screen_per_candidate_per_reduced_scenario=5000,race_prior_groups=50000,
                          local_prior_groups=50000,local_confirmation_prior_groups=100000,top30_per_scenario=100000),
        counts=dict(initial_candidates=len(candidates),grid_candidates=len(all_allocations(5)),race_candidates=len(raced),
                    local_starts=50,local_accepted=len(accepted),prior_top30_plus_named_benchmarks=len(top30)),
        reduced_prior=reduced,screen_named_best={n:candidates[np.argmax(screen[n]['mean'])] for n in named},
        candidates=top30,finalists=finalists,ranking=ranking,scenario_results=full,local_accepted=accepted,
        local_rounds=round_stats,local_stop_reason=stop_reason,
        runtime_seconds=time.perf_counter()-started,
        notes=['Search estimates are not final headline numbers.',
               'Named regret is measured against the prior top30 plus named screening leaders; it is a lower bound on unrestricted regret.',
               'A group always uses three opponents from the same population scenario.',
               'Each accepted local move is confirmed on a fresh independently seeded bank; fresh final validation is mandatory.'])
    save_json(output,result)
    if checkpoint.exists():checkpoint.unlink()
    return result


def validate_finalists(populations,named,prior,holdout,g1,g2,
        output='results/experiments/CX-050.json',seed=505000,n=1000000):
    started=time.perf_counter()
    x1=np.asarray(g1['finalists'],np.int16)
    x2=np.asarray(g2['finalists'],np.int16)
    all_names=named+prior+holdout
    result=provenance('CX-050','both',seed=seed,scenarios=all_names,
        scenario_seeds={name:populations[name].seed for name in all_names},
        sample_counts=dict(g2_groups_per_candidate_per_scenario=n,g1_matchups_per_candidate_per_crosscheck=n),
        candidates=dict(g1=x1,g2=x2),g1_exact={},g1_crosschecks={},g2={},
        paired_g2={},notes=['Fresh seeds, fixed finalists, no tuning on holdout.',
            'Confidence intervals quantify Monte Carlo sampling only, conditional on the modeled populations.',
            'Place probabilities split tied occupied ranks equally; they are not the probability of sole first.'])
    checkpoint=Path(output).with_suffix('.checkpoint.json')
    if checkpoint.exists():
        previous=json.loads(checkpoint.read_text())
        signature_keys=('commit_sha','implementation_source_sha256','seed','scenarios','scenario_seeds','sample_counts','candidates')
        if all(previous.get(key)==jsonable(result[key]) for key in signature_keys):
            result['g2']=previous.get('g2',{})
            result['paired_g2']=previous.get('paired_g2',{})
    for name in all_names:
        result['g1_exact'][name]=g1_exact(x1,g1_marginals(populations[name]))
    # One direct mixture of scenarios is valid for additive Game1 expectations.
    prior_m=np.mean([g1_marginals(populations[name]) for name in prior],axis=0)
    result['g1_prior_mean']=g1_exact(x1,prior_m)
    # Each holdout and the prior average have a one-million-matchup check.
    rng=np.random.default_rng(seed)
    crosschecks=holdout+['prior_average']
    for i,name in enumerate(crosschecks):
        rg=np.random.default_rng(seed+500+i)
        if name=='prior_average':
            pop_ids=rg.integers(len(prior),size=n)
            opponents=np.empty((n,5),np.int16)
            for j,pname in enumerate(prior):
                mask=pop_ids==j
                p=populations[pname]
                opponents[mask]=p.g1[rg.choice(len(p.w),size=mask.sum(),p=p.w)]
            exact=result['g1_prior_mean']
        else:
            p=populations[name]
            opponents=p.g1[rg.choice(len(p.w),size=n,p=p.w)]
            exact=result['g1_exact'][name]
        means=[];ses=[]
        for x in x1:
            scores=(((x>opponents)*12+(x==opponents)*6)*np.arange(1,6)).sum(axis=1)/12
            means.append(scores.mean());ses.append(scores.std(ddof=1)/np.sqrt(n))
        diff=np.asarray(means)-exact
        z=np.divide(diff,ses,out=np.full(len(x1),np.inf),where=np.asarray(ses)>0)
        z[(np.asarray(ses)==0)&(np.abs(diff)<=1e-12)]=0
        result['g1_crosschecks'][name]=dict(mean=means,se=ses,exact=exact,z=z,pass_3se=np.abs(z)<=3,
                                           seed=seed+500+i,matchups=n)
    # Store paired differences for every finalist pair on the same groups.
    pairs=list(itertools.combinations(range(len(x2)),2))
    for i,name in enumerate(all_names):
        if name in result['g2'] and name in result['paired_g2']:continue
        opps=g2_sample_opponents(populations[name],n,seed+1000+i)
        result['g2'][name]=g2_eval(x2,opps)
        result['g2'][name].update(seed=seed+1000+i,groups=n)
        payouts=[_payouts(x,opps)[0].astype(float)/12 for x in x2]
        result['paired_g2'][name]={}
        for a,b in pairs:
            d=payouts[a]-payouts[b]
            result['paired_g2'][name][f'{a}-{b}']=dict(mean=d.mean(),se=d.std(ddof=1)/np.sqrt(n))
        if (i+1)%10==0:save_json(Path(output).with_suffix('.checkpoint.json'),result)
    # Keep the same regret benchmark set as search, but re-estimate it on fresh
    # named-scenario groups shared with the finalists. Reducing to five finalists
    # would artificially shrink regret and could reverse the tie-break.
    benchmark_candidates=np.asarray(g2['candidates'],np.int16)
    result['named_regret_benchmark']=dict(candidates=benchmark_candidates,scenarios={})
    for i,name in enumerate(named):
        opps=g2_sample_opponents(populations[name],n,seed+1000+i)
        result['named_regret_benchmark']['scenarios'][name]=g2_eval(benchmark_candidates,opps)
    g2_prior=scenario_matrix(result['g2'],prior)
    g2_named=scenario_matrix(result['g2'],named)
    named_best=np.array([np.max(result['named_regret_benchmark']['scenarios'][name]['mean']) for name in named])
    primary=g2_prior.mean(axis=1)
    max_regret=(named_best[None,:]-g2_named).max(axis=1)
    order=np.lexsort((max_regret,-primary))
    first,second=int(order[0]),int(order[1])
    key=f'{min(first,second)}-{max(first,second)}'
    sign=1 if first<second else -1
    pair_mean=sign*np.mean([result['paired_g2'][s][key]['mean'] for s in prior])
    pair_se=np.sqrt(sum(result['paired_g2'][s][key]['se']**2 for s in prior))/len(prior)
    tied=pair_mean<=1.96*pair_se
    chosen=int(min((first,second),key=lambda i:max_regret[i])) if tied else first
    result['g2_prior_mean']=primary
    result['g2_prior_mc_se']=np.sqrt(np.sum(scenario_matrix(result['g2'],prior,'se')**2,axis=1))/len(prior)
    result['g2_named_candidate_max_regret']=max_regret
    result['decision']=dict(g1_index=int(np.argmax(result['g1_prior_mean'])),g2_index=chosen,
        g2_prior_leader=first,g2_prior_runner_up=second,paired_prior_mean_difference=pair_mean,
        paired_prior_se=pair_se,paired_prior_ci95=[pair_mean-1.96*pair_se,pair_mean+1.96*pair_se],
        statistical_tie=tied,tie_break='lower maximum named-scenario candidate-set regret')
    result['runtime_seconds']=time.perf_counter()-started
    save_json(output,result)
    checkpoint=Path(output).with_suffix('.checkpoint.json')
    if checkpoint.exists():checkpoint.unlink()
    return result
