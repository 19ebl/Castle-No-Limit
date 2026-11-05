"""Check the exact research leader with Claude's independent exhaustive kernel."""
import json,time,hashlib,subprocess
from pathlib import Path
import numpy as np
from castles import populations as P
from castles.snapshots import load_population_snapshot,file_sha256

start=time.perf_counter()
names=P.list_scenarios('named')+P.list_scenarios('prior')
pops,manifest=load_population_snapshot('results/frozen_populations/training.npz',names,110300,file_sha256(P.__file__),P.Population)
prior=P.list_scenarios('prior')
marg=np.mean([P.g1_marginals_rows(pops[n].g1,pops[n].w) for n in prior],axis=0)
scores=P.g1_scores_all(marg)
best=int(np.argmax(scores))
x=P.all_allocations()[best]
search=json.loads(Path('results/experiments/CX-020.json').read_text())
assert x.tolist()==search['prior_optimum']['allocation']
assert abs(float(scores[best])-search['prior_optimum']['mean'])<1e-11
r={'id':'CX-062','agent':'codex','scorer_author':'claude-code','game':1,
   'commit_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
   'scenarios':prior,'seeds':{n:pops[n].seed for n in prior},
   'sample_counts':{'feasible_allocations_exhaustively_scored':len(scores),'prior_scenarios':len(prior)},
   'candidates':[x.tolist()],'means':[float(scores[best])],'standard_errors':[0],
   'population_archive_sha256':manifest['archive_sha256'],
   'source_sha256':{str(Path(__file__).relative_to(Path.cwd())):file_sha256(__file__),'src/castles/populations.py':file_sha256(P.__file__)},
   'maximum_score_difference_from_engine':abs(float(scores[best])-search['prior_optimum']['mean']),
   'pass':True,'runtime_seconds':time.perf_counter()-start,
   'notes':'Codex executed Claude independent exhaustive kernel on the exact frozen model inputs; this is not a new Claude-run replication.'}
Path('results/experiments/CX-062.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['candidates','means','pass','runtime_seconds']}))
