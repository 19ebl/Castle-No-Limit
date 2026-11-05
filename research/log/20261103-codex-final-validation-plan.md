# Final validation plan

Recorded 2026-11-03T05:12:45.997688+00:00 before opening holdout models.

The authoritative frozen finalists, primary metric, tie-break, source hashes and seeds are in `CX-050-preregistration.json`. Primary selection is highest mean over the original frozen 240 prior scenarios; a paired 95% sampling tie uses lower maximum named-scenario candidate-set regret. Holdouts are diagnostic and never select or tune the allocation.

Baseline validation: five fixed candidates per game; one million Game 2 groups per candidate for each prior, named and holdout scenario; exact Game 1 expectations and one-million-matchup crosschecks. Independently reproduce headline results with fresh draw seeds.

Supplemental robustness: CX-063 compares seven prespecified nearleaders across three row-population seeds on the 240 prior scenarios, 200000 groups per scenario. Four of the corrected five finalists are included; the fifth lower-ranked candidate is not included, so this is explicitly nearleader stability, not an all-finalist check. No primary-rule change follows this check.

Each of the four holdout specifications will additionally use two fresh row-population seeds, 210549+i and 310549+i, in addition to baseline 110549+i. Use one million Game 2 groups per corrected fixed candidate per supplemental seed. Report three-seed ranges/SD separately from matchup Monte Carlo intervals; three seeds do not establish the actual applicant population or a reliable model-uncertainty confidence interval. No tuning or selection on holdout.

Game 2 search stopped at its ten-round local-search cap; the leader was stable after the first round, but the top two were statistically distinguishable. This is a search limitation and is not described as proof of global optimality or fulfillment of the planned statistical-tie stopping condition. The promotion defect was corrected before any holdout evaluation, with original artifacts retained as superseded.
