# Handoff to Claude

The owner explicitly requested that remaining usage-heavy work move to Claude.
Do not rerun the completed search. Finish the write-up and publication work.

## Completed and independently confirmed

- Game 1: **(1, 11, 1, 36, 51)**. Exact frozen 240-prior mean **9.709725370503282** castle points.
- Game 2: **(1, 0, 48, 51, 0)**. Frozen prior mean **7.470302983333334** payout points; conditional matchup-MC 95% interval **[7.4699857844, 7.4706201823]**.
- Runner-up **(0, 0, 48, 52, 0)**: paired leader gain **0.00343315729**, interval **[0.00336821769, 0.00349809689]**. No conditional MC tie.
- Codex signed DECISION already posted on Coordination issue #1.
- Claude independently confirmed these picks and exact frozen-array equality in its 2026-11-03 05:23:41 UTC Coordination comment (CC-050/051/052).
- All **39 code/model tests passed**, including CASTLES_SLOW=1. Both million-group scoring gates had zero mismatches.

## Authoritative artifacts

- `results/experiments/CX-020.json`: exact Game 1 search.
- `results/experiments/CX-031.json`: corrected Game 2 promotion, 72 candidates, 249 scenarios, 100k groups each.
- `research/log/CX-050-preregistration.json`: authoritative frozen finalists, source hashes, seeds, decision rule; committed before any holdout opened.
- `results/experiments/CX-050.json`: fresh final validation, five finalists, 1m groups per scenario across 253 scenarios, plus fresh named regret benchmarks.
- `results/experiments/CX-051-g1-crosscheck-diagnostic.json`: original isolated sampling-tail diagnostic.
- `results/experiments/CX-052-g1-fresh-diagnostic.json`: two predetermined fresh 1m diagnostic streams using Claude's independent Fraction reference; all ten candidate checks passed. Does not replace the original failure or pretend to be a Claude-run replication.
- `results/experiments/CX-061.json`: stronger Game 1 epsilon-equilibrium stress, exploitability 0.04899944; leader exact score 7.50670388.
- `results/experiments/CX-063.json`: seven nearleaders across three population-row seeds; leader and nearest runner-up retained their ordering in all three. Covers four corrected finalists, not the fifth lower-ranked finalist.
- `results/experiments/CX-064.json`: COMPLETE. Eight extra holdout models at 1m groups per fixed candidate; baseline four copied unchanged, so three row seeds per holdout specification. All frozen input archives/manifests retained.
- `results/frozen_populations/`: original and supplemental exact inputs with hashes.
- `results/TABLES.md`, `results/tables.csv`: regenerate using **`python scripts/render_tables.py`**. Renderer selects corrected CX-031 and includes CX-061/063/064.

## Preserve these limitations

1. Original Game 1 crosschecks: **24/25 pass, one fails** its three-SE band, sophisticated holdout finalist zero, z=-3.301923. Exact engine and independent Fraction expectations agree within 2e-15; the same sampled rows reproduce the deviation. Keep this failed flag. Claude's fresh independent checks also support a correlated sampling-tail explanation; never claim all original checks passed.
2. Applicant populations are assumed. Separate conditional matchup-MC intervals from variation across scenarios and population-row seeds. The latter is not calibrated uncertainty about real applicants.
3. Primary choice uses the original frozen 240-prior mean and conditional paired MC tie-break. Holdouts diagnose robustness and never select or tune the allocation.
4. Game 2 local search reached its ten-round cap; no global optimum or fulfilled statistical-tie stopping condition is claimed. A historical-candidate promotion defect was fixed and reranked BEFORE holdout access; original artifacts are explicitly superseded.
5. Named `equilibrium` is coarse self-play. CX-061 is a separate stronger Game 1 stress. Game 2 is vulnerable to targeted +1 counters and a more sophisticated applicant mix.
6. Rank probabilities in Codex tables fractionally share occupied tied ranks, rather than counting only sole places.

## Remaining work for Claude

1. Finalize `RESULTS.md` and `STRATEGY_ANSWER.md` from C050/C064 and your independent CC results, sensitivity, and red-team evidence. Keep the 80/150-word strategy drafts truthful about Emilio directing AI coding agents.
2. Preserve original failures and model limitations, distinguish search estimates from final validation, and give the conditional allocation recommendation plainly.
3. Post your signed final DECISION, complete the result PR(s), and merge as permitted by the owner's handoff and repository protocol. Current results PR is #5, branch `codex/research`; do not overwrite other work or force-push.
4. Codex has approved the numerical picks above; do not claim Codex read or approved prose written after this handoff. The owner requested delegation because Codex usage is low.
5. Setup `install_script` and `start_skill` are saved in the environment draft. Saving is not publication: the owner can review/save environment settings and publish the prepared snapshot. No persistent server is required.
