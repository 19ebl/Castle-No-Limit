# Supplemental holdout row-population seed check

Designed after the training-only CX-063 seed-stability check and before this
subagent opened any holdout outcomes. It uses the exact fixed finalists and
primary decision from the completed CX-050 preregistration/validation. The
parent must signal that the canonical holdout archive and strategic library
seed 2 are ready before the script is run, to avoid a cache-building race.

The script `benchmarks/holdout_population_seed_validation.py`:

1. Copies the four original frozen-population holdout results from completed
   CX-050, preserving their exact means, conditional MC standard errors, paired
   differences, draw seeds and one-million-group counts.
2. Generates two extra finite-row populations per holdout with seed bases
   210549 and 310549 (plus the zero-based holdout index), preserving the same
   weights, noise/rounding/tau/reuse parameters, 400 rows per archetype and
   strategic library seed 2. It saves checksum-validated population archives.
3. Runs one million CRN groups per candidate per extra model and computes exact
   Game 1 values on those extra models. The candidate lists remain frozen.
4. Reports each holdout separately: three-seed mean, range, SD and paired
   differences versus the already-chosen primary candidate. Conditional Monte
   Carlo errors are kept separate from across-row-seed sensitivity. Three
   seeds are too few for a reliable model-uncertainty confidence interval.

The output is `results/experiments/CX-064.json`. It includes source, primary
validation, preregistration and model snapshot hashes. It is a supplemental
diagnostic: no candidate search, holdout tuning, model reweighting or replacement
of the primary prior-based decision is performed.

```bash
NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /workspace/castle-venv/bin/python benchmarks/holdout_population_seed_validation.py
```

Only import/shape/covariance reconstruction checks were run at script creation;
those checks did not read holdout arrays or outcomes. Actual execution status
and results must be established from the completed CX-064 JSON, not this plan.

## Completed after explicit parent go

CX-064 completed in 10.51 seconds after primary CX-050 finished. It evaluated
all eight extra model units (four holdouts × two new row seeds), with one million
groups for every fixed candidate in each model. The four original baseline
units were copied from CX-050. All three population archives were rechecked
against their saved SHA256 hashes after the run.

For the fixed primary Game 2 allocation (1,0,48,51,0), the following are
descriptive finite-row-model sensitivity diagnostics, **not confidence intervals**:

| Holdout | Mean over three row seeds | Across-row-seed SD | Range of three row-seed means |
|---|---:|---:|---:|
| best_guess | 7.759414 | 0.046314 | 7.713654–7.806262 |
| ai2_heavy | 8.298898 | 0.072334 | 8.227001–8.371661 |
| contrarian | 7.937238 | 0.046961 | 7.883036–7.965725 |
| sophisticated | 5.612952 | 0.158615 | 5.454059–5.771287 |

The sophisticated holdout has substantial sensitivity to the finite applicant
rows, much larger than its conditional Monte Carlo error. Candidate ordering
also depends on the scenario; those held-out outcomes are reported without
changing the primary prior-based pick. Exact Game 1 scores for the two extra
row models are included in CX-064. The original Game 1 cross-check and its
previously diagnosed 3-SE tail event remain unchanged.
