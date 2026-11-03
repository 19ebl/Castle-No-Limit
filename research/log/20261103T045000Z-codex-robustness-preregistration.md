# Robustness checks before candidate selection

Codex subagent, not independent Claude Code. No recommendation or search result
was available when these checks were designed. Actual execution timestamps and
seeds belong in the experiment JSON.

For each game's fixed five finalists, construct a targeted counter population,
then mix 20% and 40% counters with the same baseline applicant model. Counters
retain internal variation through budget-preserving 1-3 soldier transfers.
These are deliberately adversarial conditional scenarios, not forecasts of
coordinated real applicants.

Game 1 counters are noisy members of the top eight exact responses to the
leader viewed as a point population. Report exact baseline and stress score.
Game 2 candidate counters include every allocation in multiples of ten and
allocations spending leader+1 on subsets of castles with the residual assigned
to one castle. Screen 3,000 groups at 40% counter share, race 12 counters on
12,000 fresh groups, retain four anchors and jitter. Optimize harm to the
leader's payout, not the counter's own payout. Use 100,000 independent fresh
groups for reported damage, with identical baseline draws and counter uniforms
for 20% and 40% shares. Report paired 95% intervals for damage.

Sensitivity compares only a fixed finalist list across AI-share, reuse, and tau
scenario variants. It does not use holdout outcomes to generate new candidates.
The actual Claude population API will determine the transparent scenario
construction; any mismatch with a pure one-parameter sweep must be disclosed.

For Game 2, mixing applicants before drawing triples differs from averaging
scores over uncertain scenarios. Both operations are useful, but they answer
different questions. The primary prior objective averages scenario scores.
