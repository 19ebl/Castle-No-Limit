# RESULTS (DRAFT, claude-code)

Status: draft. Sections marked **PENDING** wait for the Phase 5 final validation (codex runs it, claude-code reproduces it). Screening numbers below are labelled as screening and are not final numbers.

All scores are conditional on our modeled applicant pool (`src/castles/populations.py`), not predictions about real applicants.

## 1. Final answers

**PENDING Phase 5.** Current leaders (screening):

- Game 1: Castle 1 = 1, Castle 2 = 11, Castle 3 = 1, Castle 4 = 36, Castle 5 = 51 (total 100)
- Game 2: Castle 1 = 1, Castle 2 = 0, Castle 3 = 48, Castle 4 = 51, Castle 5 = 0 (total 100), statistically tied with (0,0,48,52,0)

## 2. Headline table

**PENDING Phase 5** (fresh seeds, holdout scenarios, ≥1,000,000 Game 2 groups per finalist per holdout scenario, Game 1 exact plus a 1,000,000-matchup Monte Carlo cross-check).

## 3. Top candidates (screening and exact evidence so far)

### Game 1 (exact)

Two independent computations agree on the leader:
- codex CX-020 (engine, population seed base 110300+i): (1,11,1,36,51), 9.7097 mean castle points over the 240-scenario prior.
- claude-code CC-010 (populations' own scorer, population seed 1): (1,11,1,36,51), 9.7114.

CC-010 top 4 by prior mean: (1,11,1,36,51) 9.7114 · (6,3,2,38,51) 9.6954 · (6,3,3,37,51) 9.6945 · (1,16,1,36,46) 9.6912.

Against a strong ε-equilibrium pool (codex CX-061, exploitability ≤ 0.049), (1,11,1,36,51) scores 7.5067, where 7.5 is break-even. The named `equilibrium` scenario is coarse self-play (exploitability about 2.0), not a near-Nash pool.

### Game 2 (Monte Carlo, common random numbers)

CC-034, on codex's exact frozen training populations, 100,000 groups per scenario, mean over 240 priors (95% CI on the paired difference vs leader):

| Allocation | Prior mean payout | Diff vs leader | Prior P10 | Max named regret (within set) |
|---|---|---|---|---|
| (1,0,48,51,0) | 7.4714 | — | 6.433 | 0.977 |
| (0,0,48,52,0) | 7.4677 | −0.004 ± 0.005 | 6.478 | 0.955 |
| (0,1,48,51,0) | 7.4601 | −0.011 ± 0.002 | 6.423 | 0.985 |
| (0,0,49,51,0) | 7.4452 | −0.026 ± 0.003 | 6.409 | 0.995 |
| (0,0,35,0,65) | 7.4299 | −0.042 ± 0.041 | 6.616 | 0.689 |
| (2,1,41,56,0) | 7.4106 | −0.061 ± 0.036 | 6.677 | 0.743 |

The same ordering holds on three other population-seed sets (CC-032, CC-033).

## 4. Game 1 vs Game 2

| | Game 1 | Game 2 |
|---|---|---|
| Objective | average castle points per head-to-head matchup | average place payout (9/4/2/0) in groups of 4 |
| Recommended | (1,11,1,36,51) (pending) | (1,0,48,51,0) or (0,0,48,52,0) (pending) |
| Expected score | about 9.71 castle points (prior mean, exact) | about 7.47 payout points (prior mean, screening) |
| Main advantage | wins castles 4 and 5 against most modeled plays (beats 35 and 50) | wins castles 3 and 4 outright often enough to take 1st place |
| Main weakness | gives up castle 3 almost entirely | collapses if many applicants play the +1 neighbour |
| Robustness | within about 0.15 of the best in every sensitivity variant (CC-020) | leader changes with the AI share; within about 0.5 of the best everywhere (CC-031) |

## 5. Why it works (draft)

- Game 1 is scored castle by castle, so only how often each castle count is beaten matters. Most modeled applicants put 20 to 35 on castle 4 and up to 50 on castle 5, so 36 and 51 win those castles cheaply, and castle 3 is conceded.
- Game 2 pays for place, not points. 1st is worth 9 and 2nd only 4, so a play that often wins two big castles outright beats a play that spreads soldiers and finishes 2nd.
- Avoid round numbers in Game 2: 50/50 loses about 0.34 payout points vs 48/52 (CC-033), because many applicants put exactly 50 on a castle.

## 6. What would change the pick

- Game 1: the share of AI-assisted applicants. At 0 to 15% the best is (6,3,2,38,51); at 33 to 50%, (1,16,1,36,46); at 70%, (1,1,21,36,41) (CC-020). (1,11,1,36,51) stays within about 0.15 of each.
- Game 2: the same assumption plus how sophisticated the pool is. With many level-k thinkers (tau 3) or game-theory players, (0,0,35,0,65) and (2,1,41,56,0) do much better than the 48/52 split (CC-032 named scores). Red team (CC-040): if 20% of applicants play the +1 counter to our pick, Game 2 payout drops by about 2.4 to 2.9 for every contender.

## 7. Reproduction

**PENDING**: seeds, commit SHA, sample counts per phase, and one command that regenerates every table.

## 8. Limitations

- The applicant pool is modeled, not observed. The AI-assisted cluster (E) is written from general knowledge of chatbot answers, not by querying chatbots.
- With 400 rows per archetype, population-sampling noise in Game 2 is up to about 0.11 payout points between population seeds (CC-031), larger than Monte Carlo error at 1M groups. Final picks are checked across several population seeds.
