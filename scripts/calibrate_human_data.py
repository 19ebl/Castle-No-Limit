#!/usr/bin/env python3
"""Describe historical human allocation tendencies without porting strategies.

Downloads public, commit-pinned CSVs using inherited HTTPS proxy and CA trust.
Never disables verification. Explanatory free text is not copied into outputs.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone
import numpy as np

UPSTREAM_COMMIT="4c1ff5e3aef1816ae04af63218015066e186c147"
BASE=f"https://raw.githubusercontent.com/fivethirtyeight/data/{UPSTREAM_COMMIT}/riddler-castles/"


def rate(mask):
    mask=np.asarray(mask,dtype=bool)
    return {"count":int(mask.sum()),"denominator":int(mask.size),
            "fraction":float(mask.mean()) if mask.size else None}


def parse_csv(payload):
    rows=list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    if not rows:
        raise ValueError("empty CSV")
    columns=[x for x in rows[0] if x.startswith("Castle ")]
    valid=[]
    invalid=[]
    for index,row in enumerate(rows):
        try:
            x=np.array([float(row[c]) for c in columns])
            if not np.isfinite(x).all() or np.any(x<0) or np.any(x!=np.floor(x)) or x.sum()!=100:
                raise ValueError("not a nonnegative integer allocation totaling100")
            valid.append(x.astype(np.int16))
        except (TypeError,ValueError):
            invalid.append(index+2)
    return np.array(valid,dtype=np.int16),len(rows),columns,invalid


def describe(x):
    positive=x[x>0]
    at_least5=x[x>=5]
    at_least10=x[x>=10]
    return {
        "valid_submissions":len(x),"castle_count":x.shape[1],
        "unique_allocations":int(len(np.unique(x,axis=0))),
        "occupied_castles_mean":float((x>0).sum(1).mean()),
        "zero_slots":rate(x==0),
        "first_castle_abandoned":rate(x[:,0]==0),
        "first_two_castles_both_abandoned":rate((x[:,:2]==0).all(1)),
        "first_three_castles_all_abandoned":rate((x[:,:3]==0).all(1)),
        "at_least_one_of_first_three_abandoned":rate((x[:,:3]==0).any(1)),
        "all_positive_counts_multiple_of_five":rate(((x==0)|(x%5==0)).all(1)),
        "all_positive_counts_multiple_of_ten":rate(((x==0)|(x%10==0)).all(1)),
        "positive_counts_multiple_of_five":rate(positive%5==0),
        "positive_counts_multiple_of_ten":rate(positive%10==0),
        "counts_ge5_multiple_of_five":rate(at_least5%5==0),
        "counts_ge5_one_above_multiple_of_five":rate(at_least5%5==1),
        "counts_ge10_multiple_of_ten":rate(at_least10%10==0),
        "counts_ge10_one_above_multiple_of_ten":rate(at_least10%10==1),
        "positive_counts_equal_one":rate(positive==1),
        "last_three_castles_at_least70_soldiers":rate(x[:,-3:].sum(1)>=70),
        "castle_mean_counts":x.mean(0).tolist(),
        "castle_zero_rates":[rate(x[:,i]==0) for i in range(x.shape[1])],
        "count_histogram":np.bincount(x.ravel(),minlength=101).tolist(),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="results/experiments/CX-060-human-calibration.json")
    parser.add_argument("--cache",default="/workspace/castle-public-calibration")
    args=parser.parse_args()
    start=time.perf_counter()
    cache=Path(args.cache); cache.mkdir(parents=True,exist_ok=True)
    results=[]
    for round_number in range(1,6):
        filename="castle-solutions.csv" if round_number==1 else f"castle-solutions-{round_number}.csv"
        url=BASE+filename
        local=cache/filename
        # Download on each run to ensure the command actually verifies network
        # retrieval and TLS. Commit pin and SHA256 identify exact source bytes.
        subprocess.run(["curl","--fail","--silent","--show-error",url,"--output",str(local)],check=True)
        payload=local.read_bytes()
        x,total,columns,invalid=parse_csv(payload)
        row={"round":round_number,"file":filename,"url":url,
             "sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload),
             "raw_submissions":total,"invalid_submissions":len(invalid),
             "invalid_csv_row_numbers":invalid,"castle_columns":columns,
             **describe(x)}
        results.append(row)
        print(f"round{round_number}: valid={len(x)}/{total}, castles={x.shape[1]}, "
              f"ge5 multiple5={row['counts_ge5_multiple_of_five']['fraction']:.3%}, "
              f"ge5 plus1={row['counts_ge5_one_above_multiple_of_five']['fraction']:.3%}, "
              f"first2zero={row['first_two_castles_both_abandoned']['fraction']:.3%}",flush=True)
    report={"id":"CX-060","agent":"codex","game":"historical-human-tendencies-only",
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "commit_sha":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "upstream_repository":"fivethirtyeight/data","upstream_commit":UPSTREAM_COMMIT,
            "scenarios":[],"seeds":[],"sample_counts":{"historical_submissions":sum(r['valid_submissions'] for r in results)},
            "candidates":[],"means":[],"standard_errors":[],
            "runtime_seconds":time.perf_counter()-start,"rounds":results,
            "denominator_definitions":{
                "submission_metrics":"One row per valid submission; duplicates retained because repeat submissions represent empirical frequencies.",
                "positive_counts":"All castle slots with count>0, pooled within that round.",
                "counts_ge5":"All castle slots with count>=5; +1 means counts6,11,16,...,96, not count1.",
                "counts_ge10":"All castle slots with count>=10; +1 means counts11,21,...,91.",
                "cheap_abandonment":"Zero soldiers in the explicitly listed lowest-value castles.",
            },
            "notes":[
                "Historical voluntary puzzle submissions, not a representative sample of finance applicants in2026.",
                "Rounds1–4 have10 castles; round5 has13. Their rates are described separately.",
                "Historical objective is head-to-head war wins, unlike this task's average castle points and four-way payouts.",
                "One-above-round-number residues describe allocations, not proven intent to undercut.",
                "Repeated rounds may contain returning players; no participant identifiers exist to estimate independence.",
                "No standard errors or population inference reported for this descriptive convenience sample.",
                "No allocations or coefficients are directly transferred to the five-castle model; canonical populations and final picks unchanged.",
            ]}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(output)


if __name__=="__main__":
    main()
