# Fixed-candidate population-row seed stability

Requested after Claude reported that some individual scenarios move by about
0.11 payout points across finite-row population seeds. That number need not be
the standard deviation of the mean across all 240 fixed prior scenarios.

`benchmarks/population_seed_stability.py` evaluates seven already-generated
candidates, without new search and without loading holdouts:

- (1,0,48,51,0)
- (0,0,35,0,65)
- (2,1,41,56,0)
- (3,0,41,56,0)
- (0,0,38,0,62)
- (0,0,48,52,0)
- (1,0,47,52,0)

The list is the union of provisional top five, every local-round leader and
runner-up, and the mistakenly dropped (0,0,48,52,0). The source is the preserved
`CX-030-superseded-promotion.json`, with its SHA256 recorded in CX-063. This use
does not treat its provisional ranking as final; it recovers a fixed candidate
union that includes the actual local leaders.

Replica 0 strictly loads the exact original frozen training archive with
population seed base 110300. Replicas 1 and 2 regenerate applicant rows with
seed bases 210300 and 310300, maintaining the global training-scenario index:
prior_000 uses seed 110309/210309/310309 because nine named scenarios precede it.
The prior weights and noise/rounding/tau/reuse parameters are checked for exact
equality across replicas; strategic library seed remains 1. Each replica is
saved as a checksum-validated population snapshot for reuse. No holdout is
loaded. Library seed uncertainty is outside this check.

Each candidate receives 200,000 common-random-number groups in every one of
240 priors per replica. The primary statistic is the equally weighted mean
of the 240 scenario means. Conditional Monte Carlo covariance matrices are
summed across independently sampled scenarios to obtain paired Monte Carlo
standard errors for the aggregate differences. These conditional intervals do
not capture population-row uncertainty or uncertainty about real applicants.

Across the three row-population replicas, report SD and range of the 240-scenario
averages and of paired candidate differences. Also report the mean and maximum
per-scenario row-replica SD, explicitly separated from aggregate-average SD.
Three replicas give rough sensitivity diagnostics, not reliable inferential
confidence intervals. The original row seed participated in candidate selection;
the two new row seeds provide an out-of-row-sample check, not a full independent
repetition of the entire model-selection procedure.

Reproduce after dependencies are installed:

```bash
NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /workspace/castle-venv/bin/python benchmarks/population_seed_stability.py \
 --search results/experiments/CX-030-superseded-promotion.json
```

Detailed results and source/snapshot hashes are saved in
`results/experiments/CX-063.json`. This supplemental check does not change the
prior specification, the primary objective, or any final pick automatically.

## Completed observations

The full run completed in 153.23 seconds. (1,0,48,51,0) ranked first in all
three replicas; (0,0,48,52,0) ranked second. Their paired mean differences were
0.003350, 0.004448 and 0.003681 payout points, with conditional MC SE about
0.000074 each. The across-three-replica SD of that paired difference was
0.000563, with range [0.003350, 0.004448]. The lead over (0,0,35,0,65) ranged
from 0.03884 to 0.05444 across the three replicas.

For (1,0,48,51,0), mean per-scenario row-replica SD was 0.07615 and the maximum
was 0.24586, whereas the SD of the **240-scenario average** across row replicas
was 0.00804. All three are different diagnostics. This check found stable
ordering of the two closest candidates under finite-row resampling conditional
on these fixed prior specifications and shared strategic library, without
establishing the correctness of the applicant model.
