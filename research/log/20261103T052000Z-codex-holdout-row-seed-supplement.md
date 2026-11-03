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
