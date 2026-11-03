#!/usr/bin/env python3
"""Run one reproducible research phase from the repository root."""
import argparse,hashlib,json
from pathlib import Path
from castles.search import g1_search,g2_search,validate_finalists,save_json
from castles.populations import get_population,list_scenarios
import castles.populations as population_module

parser=argparse.ArgumentParser()
parser.add_argument('phase',choices=['g1','g2','preregister','validate'])
parser.add_argument('--population-seed',type=int,default=110300)
parser.add_argument('--seed',type=int)
parser.add_argument('--groups',type=int,default=1000000)
args=parser.parse_args()
named=list_scenarios('named');prior=list_scenarios('prior');holdout=list_scenarios('holdout')
prereg_path=Path('research/log/CX-050-preregistration.json')
if args.phase in ('preregister','validate'):
    g1=json.loads(Path('results/experiments/CX-020.json').read_text())
    g2=json.loads(Path('results/experiments/CX-030.json').read_text())
    frozen=dict(finalists_g1=g1['finalists'],finalists_g2=g2['finalists'],
        population_seed=args.population_seed,validation_seed=args.seed or 505000,
        groups=args.groups,named=named,prior=prior,holdout=holdout,
        implementation_source_sha256={name:hashlib.sha256(Path(name).read_bytes()).hexdigest()
            for name in ('src/castles/engine.py','src/castles/search.py','src/castles/rules.py','src/castles/populations.py','scripts/run_research.py')},
        primary_metric='arithmetic mean of scores over the frozen 200 prior scenarios',
        tie_break='lower maximum named-scenario regret against the frozen search benchmark candidate set',
        benchmark_candidates=g2['candidates'])
    if args.phase=='preregister':
        if prereg_path.exists() and json.loads(prereg_path.read_text())!=frozen:
            raise SystemExit('Existing preregistration differs. Do not overwrite a frozen analysis.')
        save_json(prereg_path,frozen)
        print('Saved frozen finalists, populations, seeds and decision rule to',prereg_path)
        raise SystemExit(0)
    if not prereg_path.exists():
        raise SystemExit('Missing finalist preregistration; run preregister before validation')
    if json.loads(prereg_path.read_text())!=frozen:
        raise SystemExit('Finalists, population source, scenario names, seeds, count or decision rule changed after preregistration')
needed=named+prior+(holdout if args.phase=='validate' else [])
populations={name:get_population(name,args.population_seed+i) for i,name in enumerate(needed)}
if args.phase=='g1':
    r=g1_search(populations,named,prior,seed=args.seed or 20261103)
elif args.phase=='g2':
    g1=json.loads(Path('results/experiments/CX-020.json').read_text())
    r=g2_search(populations,named,prior,g1,seed=args.seed or 203000)
else:
    r=validate_finalists(populations,named,prior,holdout,g1,g2,seed=args.seed or 505000,n=args.groups)
print(json.dumps(dict(id=r['id'],runtime_seconds=r['runtime_seconds'],finalists=r.get('finalists'),decision=r.get('decision')),default=lambda x:x.tolist()))
