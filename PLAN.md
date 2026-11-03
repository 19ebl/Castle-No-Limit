# PLAN.md: Research method

Read after AGENTS.md, which has the rules, lanes, and protocol. This file is the method and the deliverable templates.

## Phase 0: Preflight and bootstrap (first 20 minutes)

Both agents:
1. Check what works: pushing a scratch branch, `gh` issue and PR access, Python version, numpy, numba, CPU cores, RAM.
2. Find or create the Coordination issue and post HELLO with those results, then CLAIM your Phase 0 work.

`codex` first PR: package skeleton (`pyproject.toml`, empty `src/castles/__init__.py`, `rules.py`, stub modules matching the interface contract), CI that runs pytest, and `engine.py` passing every test vector in AGENTS.md.

`claude-code` first PR: `reference.py`, tests for every test vector, invariant tests (totals of 180 units; relabeling players permutes the outputs), and the differential-test harness that will run against `engine.py`. Don't create `pyproject.toml`; run tests with `PYTHONPATH=src` until the skeleton merges, then rebase.

Gate: no optimization result counts until the differential test passes with zero mismatches.

## Phase 1: Applicant pool model (claude-code leads, codex reviews)

A scenario is a named, seeded population whose rows are applicant types, each with a Game 1 allocation, a Game 2 allocation, and a weight. Build archetypes with internal variation (noise, rounding habits), never single fixed points:

- A. Naive heuristics: equal split (20 each); value-proportional (about 7/13/20/27/33) and its rounded versions; skipping cheap castles (for example 0/0/25/35/40); allocations in multiples of 5 or 10.
- B. Concentrators: win two or three castles outright (castles 4+5, 3+5, 3+4+5, 2+3+5, and so on), including plays aimed at 8 or more points.
- C. Edge seekers: beat common focal counts by 1 to 3 (21, 26, 31, 34, 36, 51) and grab cheap castles with tiny forces.
- D. Level-k / cognitive hierarchy: level 0 is a mix of A; level k is a noisy (softmax) best response to the mix of lower levels; level weights follow Poisson(tau) with tau in {0.5, 1.5, 3}. Keep responses noisy so populations aren't unrealistically spiky.
- E. AI-assisted applicants: many applicants in 2026 will paste these rules into a chatbot and submit what it says. Write down, from your own knowledge, a spread of answers a general-purpose chatbot plausibly gives, with variation. Don't call external model APIs. Treat this cluster as possibly large.
- F. Game-theory literate: approximate symmetric equilibrium of each game via fictitious play or replicator dynamics over a large candidate set (self-play). Build Game 1 and Game 2 populations separately.
- G. Reuse: some applicants submit the same allocation in both games. Vary that share from 20% to 80%.
- H. Adversarial: populations tuned to beat our current leader (built in Phase 4).

Calibration (recommended): FiveThirtyEight's "Battle for Riddler Nation" submissions are public at https://github.com/fivethirtyeight/data/tree/master/riddler-castles (10 castles worth 1 to 10, 100 soldiers, with free-text reasoning). It is a different game, so use it only for human tendencies: round-number heaping, how often cheap castles are abandoned, +1 undercutting, and how play shifted between rounds. Don't map its allocations directly.

Scenario sets:
- Named: mostly naive; mostly AI-assisted; concentration heavy; level-k at each tau; equilibrium/self-play; and a "best guess" mix whose weights and reasons are written in a log entry before any results are seen.
- Prior: at least 200 random mixtures of archetypes A to G (Dirichlet weights, perturbed parameters). The primary objective is the average score over this prior.
- Holdout: different seeds plus at least one archetype variant never used during search. Freeze it in a log entry before final validation and never tune against it.

## Phase 2: Game 1 search (codex leads)

1. For every named scenario and prior draw, score all 4,598,126 allocations exactly and keep the top 100.
2. Candidate set: the union of those, plus every named-scenario best response and current leaders.
3. Build the exact score matrix S[candidate, scenario] and regret R = (best score in that scenario) minus (candidate score).
4. Rank by mean over the prior. Also report max regret over named scenarios and the 10th-percentile score over prior draws.
5. Cross-check each finalist with 1,000,000 sampled matchups; the Monte Carlo mean must land within 3 standard errors of the exact value.

## Phase 3: Game 2 search (codex leads, claude-code proposes families)

1. Candidates: Game 1 finalists, concentration families with small offsets, every allocation in multiples of 5 (10,626 of them) for coverage, local-search outputs, and self-play leaders.
2. Screen with common random numbers: start around 5,000 groups per candidate on a reduced scenario set, then use successive halving to push samples (50,000 or more) toward contenders.
3. Local search on the top 50: move k in {1, 2, 3, 5, 10} soldiers between any two castles. Accept a move only if the paired improvement exceeds 2 standard errors, and re-sample before trusting a chain of small gains.
4. Score the top 30 on every named scenario and prior draw (100,000 or more groups each) to build the same regret table as Game 1.
5. Optional exact check: for a scenario with at most about 300 distinct allocations, enumerate opponent multisets to compute Game 2 exactly and confirm the Monte Carlo.

## Phase 4: Red team and robustness (claude-code leads)

- For each game's top 5, build the plausible population that hurts it most (for example 20% to 40% of applicants playing a counter) and report the damage.
- Sensitivity: show how the top 5 reorder as the AI-assisted share, the reuse share, and tau change. Name the assumption that would flip the recommendation.

## Phase 5: Final validation (codex runs it, claude-code reproduces it)

1. Pre-register in a log entry: the finalists (at most 5 per game), the primary metric (mean over the prior), and the tie-break (lower max regret over named scenarios).
2. Use fresh seeds and the holdout scenarios. Game 2: at least 1,000,000 groups per finalist per holdout scenario, common random numbers across finalists, paired 95% confidence intervals on the differences. Game 1: exact values plus the 1,000,000-matchup cross-check.
3. claude-code reproduces the headline numbers independently with different seeds before anything goes into RESULTS.md.
4. Decision rule: highest mean over the prior. If the top two are within the paired 95% interval, pick the one with lower max regret and say so. Screening estimates never appear as final numbers (winner's curse).

## Stopping

Stop searching when two consecutive rounds improve the leader by less than 0.005 castle points (Game 1) or 0.01 payout points (Game 2) and the top candidates are statistically tied, or when 75% of the time budget is gone. Then validate and write up.

## RESULTS.md template

1. Final answers, exactly as they will be typed into the application:
   - Game 1: Castle 1 = a, Castle 2 = b, Castle 3 = c, Castle 4 = d, Castle 5 = e (total 100)
   - Game 2: same format
2. Headline table: expected score with 95% confidence interval on the prior and on each holdout scenario. For Game 2, also P(1st), P(2nd), P(3rd), P(4th) and mean castle points.
3. Top 10 per game: score on each named scenario, mean over the prior, max regret.
4. Comparison table (Game 1 vs Game 2): objective, recommended allocation, expected score, main advantage, main weakness, robustness. One line each.
5. Why it works: at most 5 plain-English bullets.
6. What would change the pick: the assumption most likely to flip it, and the runner-up to use if Emilio believes that assumption.
7. Sample counts per phase, seeds, commit SHA, and one command that regenerates every table from saved results.
8. Unfinished work and known limitations.

## STRATEGY_ANSWER.md

Answers the application question "How did you approach each game, and did your strategy change?" Write two drafts: about 80 words and about 150 words.
- First person, as Emilio (a finance student). Direct and plain, with specific numbers. No buzzwords, no hype, no em dashes.
- Explain the shift: Game 1 rewards average castle points, while Game 2 rewards finishing place with a top-heavy payout, and say how that changed the allocation.
- Be truthful about the process: Emilio set up and directed AI coding agents that built and ran the simulations. Don't imply he hand-wrote the code. Include only claims he can explain in an interview.
