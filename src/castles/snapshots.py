"""Persist exact applicant-model arrays for cross-version independent replication."""
from pathlib import Path
import hashlib,json,platform
import numpy as np
from .search import jsonable,save_json


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_sha256(array):
    array=np.ascontiguousarray(array)
    header=json.dumps([array.dtype.str,list(array.shape)],separators=(',',':')).encode()
    return hashlib.sha256(header+b'\0'+array.tobytes()).hexdigest()


def save_population_snapshot(path,populations,base_seed,source_sha256):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    arrays={};entries=[]
    for i,(name,p) in enumerate(populations.items()):
        meta=getattr(p,'meta',{})
        entry=dict(name=name,seed=int(p.seed),meta={k:v for k,v in meta.items() if not isinstance(v,np.ndarray)},meta_arrays={},arrays={})
        for attr,a in meta.items():
            if isinstance(a,np.ndarray):
                key=f'{i:03d}_meta_{attr}';arrays[key]=a
                entry['meta_arrays'][attr]=dict(key=key,dtype=a.dtype.str,shape=list(a.shape),sha256=array_sha256(a))
        for attr in ('g1','g2','w'):
            key=f'{i:03d}_{attr}'
            a=np.asarray(getattr(p,attr));arrays[key]=a
            entry['arrays'][attr]=dict(key=key,dtype=a.dtype.str,shape=list(a.shape),sha256=array_sha256(a))
        entries.append(entry)
    temp=path.with_suffix('.npz.tmp')
    with temp.open('wb') as f:np.savez_compressed(f,**arrays)
    temp.replace(path)
    manifest=dict(schema=1,base_seed=base_seed,source_sha256=source_sha256,
        python_version=platform.python_version(),numpy_version=np.__version__,
        archive_sha256=file_sha256(path),populations=entries)
    save_json(path.with_suffix('.manifest.json'),manifest)
    return manifest


def load_population_snapshot(path,names,base_seed,source_sha256,constructor):
    path=Path(path)
    manifest=json.loads(path.with_suffix('.manifest.json').read_text())
    if manifest['schema']!=1 or manifest['base_seed']!=base_seed or manifest['source_sha256']!=source_sha256:
        raise ValueError('Population snapshot source or seed differs; do not silently regenerate a frozen model')
    if [e['name'] for e in manifest['populations']]!=list(names):
        raise ValueError('Population snapshot scenario order differs')
    if file_sha256(path)!=manifest['archive_sha256']:raise ValueError('Population archive checksum differs')
    populations={}
    with np.load(path,allow_pickle=False) as data:
        for i,entry in enumerate(manifest['populations']):
            arrays={}
            if entry['seed']!=base_seed+i:raise ValueError('Population seed differs')
            for attr,record in entry['arrays'].items():
                a=data[record['key']]
                if a.dtype.str!=record['dtype'] or list(a.shape)!=record['shape'] or array_sha256(a)!=record['sha256']:
                    raise ValueError(f'Population array checksum differs: {entry["name"]}/{attr}')
                arrays[attr]=a
            meta=entry['meta'].copy()
            for attr,record in entry.get('meta_arrays',{}).items():
                a=data[record['key']]
                if a.dtype.str!=record['dtype'] or list(a.shape)!=record['shape'] or array_sha256(a)!=record['sha256']:
                    raise ValueError(f'Population metadata checksum differs: {entry["name"]}/{attr}')
                meta[attr]=a
            populations[entry['name']]=constructor(name=entry['name'],seed=entry['seed'],meta=meta,**arrays)
    return populations,manifest
