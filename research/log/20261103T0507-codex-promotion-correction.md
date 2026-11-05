# Candidate-promotion correction before holdout

The initial search CX-030 dropped historical accepted local-search states when it built the full-scenario candidate pool from only the final endpoints. For example, `(0,0,48,52,0)` was a closely competitive global leader/runner-up in rounds 0–8, but was absent from its final 35 candidates. Those scored initial results remain valid for their listed candidate set, but are superseded as the finalist-selection analysis.

No holdout population has been generated or examined. The initial result is preserved byte-for-byte as `results/experiments/CX-030-superseded-promotion.json`; its provisional preregistration is preserved as `research/log/CX-050-superseded-promotion-preregistration.json` and is explicitly withdrawn before any validation.

Correction: retain every accepted old/new state and every recorded global leader/runner-up, union them with the initial full-scenario pool, and score this union against all 9 named and 240 prior scenarios on 100,000 newly seeded common opponent groups per scenario. Save this distinct experiment as CX-031. Select five finalists by the same prior-mean objective and named-regret tie-break, then create a new preregistration before opening holdout. The screening and local-search stages do not need to be rerun because their recorded outputs suffice to correct promotion.
