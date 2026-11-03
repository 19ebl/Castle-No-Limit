"""Fixed fresh diagnostic streams; never replace the original failed crosscheck."""
import hashlib,json,subprocess,time
from pathlib import Path
import numpy as np
from castles.reference import game1_units
from castles.populations import Population
from castles.snapshots import load_population_snapshot,file_sha256

started=time.perf_counter()
final=json.loads(Path('results/experiments/CX-050.json').read_text())
manifest=json.loads(Path('results/frozen_populations/holdout.manifest.json').read_text())
names=[p['name'] for p in manifest['populations']]
pops,_=load_population_snapshot('results/frozen_populations/holdout.npz',names,110549,manifest['source_sha256'],Population)
p=pops['holdout_sophisticated']
xs=final['candidates']['g1']
lut=np.array([[game1_units(x,y)[0] for x in xs] for y in p.g1],dtype=np.int16)
exact=p.w@lut/12
# These two streams and sample sizes are fixed before either outcome is read.
streams=[(780001,0),(780001,1)]
rows=[]
for seed in streams:
    ids=np.random.default_rng(seed).choice(len(p.w),size=1_000_000,p=p.w)
    scores=lut[ids].astype(float)/12
    mean=scores.mean(0);se=scores.std(0,ddof=1)/np.sqrt(len(scores))
    z=(mean-exact)/se
    rows.append(dict(seed=list(seed),matchups=len(scores),mean=mean.tolist(),se=se.tolist(),z=z.tolist(),pass_3se=(np.abs(z)<=3).tolist()))
theoretical_se=np.sqrt(p.w@(lut/12-exact)**2/1_000_000)
r={'id':'CX-052','agent':'codex','scorer_author':'claude-code','game':1,
   'commit_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
   'source_sha256':{'benchmark':file_sha256(__file__),'reference':file_sha256('src/castles/reference.py')},
   'scenarios':['holdout_sophisticated'],'candidates':xs,'sample_counts':{'fresh_streams':2,'matchups_per_stream':1_000_000},
   'exact_reference':exact.tolist(),'theoretical_se_1m':theoretical_se.tolist(),'streams':rows,
   'frozen_archive_sha256':manifest['archive_sha256'],'runtime_seconds':time.perf_counter()-started,
   'notes':['Prespecified two fresh diagnostic streams, not rerolls until passing.','Original CX050 z=-3.301923 and its failed flag remain unchanged.','Codex executes the independently authored Claude Fraction reference via exact per-row lookup; no engine scorer used.','This does not substitute for a Claude-run independent replication.']}
Path('results/experiments/CX-052-g1-fresh-diagnostic.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'exact':r['exact_reference'],'streams':rows},indent=2))
