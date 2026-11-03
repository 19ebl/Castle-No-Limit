# RESULTS

Castle allocation research by two coding agents (codex, claude-code), directed by Emilio. Every number below is computed from saved experiment files and is conditional on our modeled applicant pool (`src/castles/populations.py`). It is not a prediction about real applicants.

Status: final draft by claude-code. Headline numbers are codex's final validation (CX-050), independently reproduced by claude-code with different draw seeds and its own scorer (CC-050, CC-051, CC-052). Awaiting codex approval (AGENTS.md section 7).

## 1. Final answers

- **Game 1:** Castle 1 = 1, Castle 2 = 11, Castle 3 = 1, Castle 4 = 36, Castle 5 = 51 (total 100)
- **Game 2:** Castle 1 = 1, Castle 2 = 0, Castle 3 = 48, Castle 4 = 51, Castle 5 = 0 (total 100)

Both were chosen by the pre-registered rule (CX-050 pre-registration, frozen before any holdout was opened): highest mean over the 240 prior scenarios, with lower maximum named-scenario regret used only for a statistical tie. The tie-break was not needed. Game 1 values are exact, and the leader is 0.016 castle points ahead of (6,3,2,38,51). In Game 2 the leader beats the runner-up (0,0,48,52,0) by 0.00343 payout points, paired 95% interval [0.00337, 0.00350].

## 2. Headline table

### Headline: Game 1 (1,11,1,36,51) (expected castle points, exact; codex CX-050 / claude-code CC-050-051)

| Scenario | codex exact | claude-code exact | 1M-matchup Monte Carlo cross-check (95%) |
|---|---|---|---|
| prior (240, mean) | 9.709725 | 9.709725 | exact |
| holdout_best_guess | 9.9459 | 9.9459 | codex MC 9.9428±0.0037 (z -1.63); claude-code MC 9.9457±0.0037 |
| holdout_ai2_heavy | 10.3452 | 10.3452 | codex MC 10.3468±0.0034 (z +0.94); claude-code MC 10.3454±0.0034 |
| holdout_contrarian | 9.7119 | 9.7119 | codex MC 9.7100±0.0035 (z -1.07); claude-code MC 9.7118±0.0035 |
| holdout_sophisticated | 8.7694 | 8.7694 | codex MC 8.7617±0.0046 (z -3.30); claude-code MC 8.7689±0.0046 |

Game 1 values are exact expectations, so they carry no sampling error. The codex and claude-code exact values agree to every printed digit (prior mean 9.709725 in both). Monte Carlo cross-checks: 155 independent claude-code checks of 1,000,000 matchups each (12 holdout units, 9 named scenarios, 10 extra seeds on holdout_sophisticated; 5 finalists each) all land within 3 standard errors. One of codex's 25 original checks missed (holdout_sophisticated, finalist 1, z = -3.30). Its exact value 8.7694375 was confirmed by brute force over every pool row with the independent reference scorer, and 11 fresh claude-code checks on that unit gave |z| at most 2.35. We read it as a sampling-tail event (the five finalists' errors in one draw are strongly correlated) and report it rather than re-rolling it.

### Headline: Game 2 (1,0,48,51,0) (expected payout, 95% Monte Carlo CI; place shares split ties)

| Scenario | codex (1M groups/scenario) | claude-code (prior 200k, holdout 1M) | P(1st/2nd/3rd/4th), codex | Mean castle points, codex |
|---|---|---|---|---|
| prior (240, mean) | 7.4703 [7.4700, 7.4706] | 7.4705 [7.4698, 7.4712] | 0.748 / 0.133 / 0.105 / 0.014 | 6.429 |
| holdout_best_guess | 7.7137 [7.7090, 7.7183] | 7.7137 [7.7090, 7.7184] | 0.780 / 0.135 / 0.077 / 0.008 | 6.625 |
| holdout_ai2_heavy | 8.2270 [8.2234, 8.2306] | 8.2268 [8.2232, 8.2304] | 0.858 / 0.113 / 0.028 / 0.001 | 7.071 |
| holdout_contrarian | 7.9630 [7.9588, 7.9672] | 7.9644 [7.9602, 7.9686] | 0.816 / 0.134 / 0.042 / 0.008 | 6.718 |
| holdout_sophisticated | 5.4541 [5.4475, 5.4606] | 5.4624 [5.4559, 5.4689] | 0.462 / 0.164 / 0.319 / 0.055 | 5.242 |

claude-code prior place shares 0.748 / 0.133 / 0.105 / 0.014, castle points 6.429.

All 20 holdout comparisons between codex and claude-code (5 finalists x 4 holdouts) agree within 1.93 combined standard errors, and all 5 prior means agree within 0.83. Place probabilities split ties: a player tied for 1st and 2nd counts half in each, so the four sum to 1 and 9 x P(1st) + 4 x P(2nd) + 2 x P(3rd) equals the expected payout.

### Finalists on the prior and holdouts (codex CX-050)

| Game | Allocation | Prior mean | best_guess | ai2_heavy | contrarian | sophisticated |
|---|---|---|---|---|---|---|
| G1 | (1,11,1,36,51) | 9.7097 | 9.946 | 10.345 | 9.712 | 8.769 |
| G1 | (6,3,2,38,51) | 9.6940 | 9.892 | 10.095 | 9.821 | 8.666 |
| G1 | (1,16,1,36,46) | 9.6929 | 9.950 | 10.630 | 9.573 | 8.283 |
| G1 | (6,3,3,37,51) | 9.6921 | 9.899 | 10.057 | 9.884 | 8.658 |
| G1 | (6,4,1,38,51) | 9.6920 | 9.896 | 10.146 | 9.805 | 8.653 |
| G2 | (1,0,48,51,0) | 7.4703 | 7.714 | 8.227 | 7.963 | 5.454 |
| G2 | (0,0,48,52,0) | 7.4669 | 7.693 | 8.237 | 7.955 | 5.454 |
| G2 | (0,0,35,0,65) | 7.4301 | 7.718 | 8.042 | 7.686 | 5.747 |
| G2 | (1,0,47,52,0) | 7.4300 | 7.667 | 8.355 | 7.888 | 5.486 |
| G2 | (0,0,47,53,0) | 7.4242 | 7.627 | 8.287 | 7.879 | 5.493 |

Game 2 leader minus runner-up on the prior: 0.00343, paired 95% [0.00337, 0.00350], statistical tie: False.

## 3. Top 10 per game

Named scenarios: naive = naive_heavy, ai = ai_heavy, conc = concentration_heavy, lk = level-k (tau 0.5, 1.5, 3), eq = equilibrium (coarse self-play), edge = edge_heavy, best = best_guess.

### Top 10, Game 1 (codex CX-020, exact). Regret is vs the exact best response in each named scenario.

| Allocation | Prior mean | Prior P10 | Max named regret | naive | ai | conc | lk0.5 | lk1.5 | lk3 | eq | edge | best |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (1,11,1,36,51) | 9.7097 | 9.225 | 2.539 | 10.10 | 10.12 | 10.26 | 9.97 | 9.12 | 7.45 | 8.79 | 9.51 | 9.89 |
| (6,3,2,38,51) | 9.6940 | 9.274 | 2.585 | 10.00 | 9.91 | 10.30 | 10.11 | 9.31 | 7.40 | 8.78 | 9.57 | 9.82 |
| (1,16,1,36,46) | 9.6929 | 9.001 | 3.179 | 10.54 | 10.39 | 9.95 | 10.21 | 8.16 | 6.81 | 8.86 | 9.48 | 9.97 |
| (6,3,3,37,51) | 9.6921 | 9.259 | 2.596 | 9.99 | 9.89 | 10.34 | 10.07 | 9.25 | 7.39 | 8.84 | 9.54 | 9.84 |
| (6,4,1,38,51) | 9.6920 | 9.259 | 2.638 | 10.00 | 9.92 | 10.31 | 10.11 | 9.24 | 7.35 | 8.74 | 9.60 | 9.81 |
| (6,4,2,37,51) | 9.6913 | 9.248 | 2.608 | 10.00 | 9.92 | 10.35 | 10.08 | 9.25 | 7.38 | 8.74 | 9.57 | 9.83 |
| (6,5,1,37,51) | 9.6879 | 9.229 | 2.650 | 10.00 | 9.94 | 10.33 | 10.09 | 9.22 | 7.34 | 8.70 | 9.59 | 9.82 |
| (6,3,1,39,51) | 9.6850 | 9.261 | 2.570 | 10.00 | 9.91 | 10.27 | 10.10 | 9.35 | 7.42 | 8.78 | 9.59 | 9.81 |
| (7,3,1,38,51) | 9.6842 | 9.248 | 2.701 | 10.03 | 9.93 | 10.29 | 10.13 | 9.17 | 7.29 | 8.75 | 9.56 | 9.82 |
| (7,3,2,37,51) | 9.6836 | 9.236 | 2.671 | 10.02 | 9.92 | 10.32 | 10.10 | 9.18 | 7.32 | 8.75 | 9.54 | 9.83 |

### Top 10, Game 2 (codex CX-031, 100k CRN groups per scenario; screening grade). Regret is vs the best of the 72-candidate benchmark set.

| Allocation | Prior mean | MC SE | Prior P10 | Max named regret | naive | ai | conc | lk0.5 | lk1.5 | lk3 | eq | edge | best |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (1,0,48,51,0) | 7.4710 | 0.0005 | 6.431 | 2.592 | 8.69 | 8.17 | 8.33 | 7.90 | 5.99 | 4.83 | 4.72 | 7.89 | 7.61 |
| (0,0,48,52,0) | 7.4677 | 0.0005 | 6.471 | 2.573 | 8.67 | 8.11 | 8.26 | 7.90 | 5.96 | 4.85 | 4.73 | 7.87 | 7.60 |
| (0,0,35,0,65) | 7.4308 | 0.0006 | 6.608 | 2.341 | 8.60 | 8.15 | 7.75 | 7.82 | 6.40 | 5.08 | 4.94 | 7.42 | 7.43 |
| (1,0,47,52,0) | 7.4308 | 0.0005 | 6.473 | 2.564 | 8.59 | 8.18 | 8.01 | 7.88 | 5.97 | 4.86 | 4.77 | 7.89 | 7.55 |
| (0,0,47,53,0) | 7.4249 | 0.0005 | 6.514 | 2.551 | 8.57 | 8.12 | 7.93 | 7.91 | 5.96 | 4.87 | 4.79 | 7.90 | 7.52 |
| (2,0,47,51,0) | 7.4199 | 0.0005 | 6.410 | 2.594 | 8.60 | 8.19 | 8.07 | 7.87 | 5.98 | 4.83 | 4.74 | 7.91 | 7.55 |
| (2,1,41,56,0) | 7.4103 | 0.0005 | 6.692 | 1.645 | 8.40 | 8.10 | 7.58 | 7.73 | 6.30 | 5.78 | 4.94 | 7.93 | 7.41 |
| (3,0,41,56,0) | 7.4078 | 0.0005 | 6.676 | 1.654 | 8.41 | 8.10 | 7.57 | 7.73 | 6.32 | 5.77 | 4.89 | 7.95 | 7.41 |
| (3,0,46,51,0) | 7.4026 | 0.0005 | 6.409 | 2.598 | 8.58 | 8.20 | 7.95 | 7.85 | 5.97 | 4.82 | 4.75 | 7.93 | 7.52 |
| (0,0,34,0,66) | 7.3878 | 0.0005 | 6.646 | 2.109 | 8.53 | 8.17 | 7.71 | 7.78 | 6.53 | 5.31 | 4.89 | 7.39 | 7.44 |

The large "max named regret" values come from the two most sophisticated named pools (level-k tau 3, equilibrium), where a specialised counter does much better than any broad allocation.

## 4. Game 1 vs Game 2

| Game | Objective | Recommended | Expected score (prior) | Main advantage | Main weakness | Robustness |
|---|---|---|---|---|---|---|
| 1 | Average castle points per head-to-head matchup | (1,11,1,36,51) | 9.710 castle points of 15 (exact) | Wins castles 4 and 5 (9 points) against most applicants | Concedes castle 3 almost every time | Best on prior mean and on the average over 12 holdout units; 0.19 to 0.40 behind the best of its set when chatbot or naive answers dominate |
| 2 | Average place payout (9/4/2/0) in groups of 4 | (1,0,48,51,0) | 7.470 payout points (MC 95% [7.4700, 7.4706]) | Usually wins castles 3 and 4 outright; finishes 1st about 75% of the time (tie-split) | Gives up castle 5 and depends on few others making the same two-castle play | Leader on prior and on the 12-unit holdout average; up to 0.60 behind the best when the pool is mostly deep level-k thinkers |

## 5. Why it works

- **Game 1 is scored castle by castle**, so all that matters is how often each count beats an opponent's count. In the modeled pool, 36 on castle 4 beats 82% of applicants and 51 on castle 5 beats 91%, so those 9 points come cheaply. Winning castle 3 reliably would cost 35 or more soldiers, so it is conceded.
- **Game 2 pays for place, not points.** 1st pays 9 and 2nd only 4, so the target is winning, not a high total. 48 on castle 3 and 51 on castle 4 each beat about 96 to 97% of applicants, giving 7 of the 15 points while the other three players split the rest.
- **Odd numbers beat round numbers.** 51 beats everyone who put 50 on castle 4. Moving from (0,0,48,52,0) to (0,0,50,50,0) costs about 0.34 payout points (CC-033).
- **The two games need different answers.** On the same 240-scenario prior, the Game 1 pick would score 6.13 payout points in Game 2 (vs 7.47), and the Game 2 pick would score 7.51 castle points in Game 1 (vs 9.71) (CC-053).
- **Both answers held up across checks.** Two independent implementations, three population-row replicas (CX-063), and every holdout-unit average gave the same leaders.

## 6. What would change the pick

- **Game 2, most likely flip: how sophisticated the pool is.** If many applicants think several steps ahead (level-k tau 3, game-theory literate), (0,0,35,0,65) is better: +0.29 payout on holdout_sophisticated, better on the level-k tau 1.5 / tau 3 and equilibrium named pools, and the smallest worst-case shortfall in the sensitivity set (0.16 vs 0.60). It costs 0.040 on the prior mean. **Runner-up to use if Emilio believes the pool is sophisticated: Castle 1 = 0, Castle 2 = 0, Castle 3 = 35, Castle 4 = 0, Castle 5 = 65.**
- **Game 1, most likely flip: the share of chatbot and naive answers.** At an AI-assisted share of 0.5 to 0.7, (1,16,1,36,46) or (1,1,21,36,41) do 0.19 to 0.40 better. They do much worse on sophisticated pools (holdout_sophisticated 8.28 vs 8.77). **Runner-up if Emilio believes most applicants paste a chatbot answer: Castle 1 = 1, Castle 2 = 16, Castle 3 = 1, Castle 4 = 36, Castle 5 = 46.**
- **Copycat risk (red team, CC-042).** If 20% of applicants played a near-copy that beats ours on one castle, such as (0,0,48,52,0) or (0,0,49,51,0), the Game 2 payout would fall by about 2.5 points; at 40%, by about 4.2. Every two-castle contender has the same weakness, so it does not change the ranking, but it is the main way the pick fails.

### Sensitivity, Game 1 (CC-020; best_guess mix with one knob moved; population seeds [101, 102, 103])

| Variant | Best of set | (1,11,1,36,51) | (6,3,2,38,51) | (6,3,3,37,51) | (1,16,1,36,46) | (1,1,21,36,41) | (1,9,39,5,46) | (8,16,6,7,63) | (7,3,1,39,50) |
|---|---|---|---|---|---|---|---|---|---|
| ai_share=0.0 | (6,3,2,38,51) | 9.557 | 9.661 | 9.658 | 9.345 | 9.275 | 8.657 | 8.175 | 9.581 |
| ai_share=0.15 | (6,3,2,38,51) | 9.728 | 9.748 | 9.742 | 9.649 | 9.538 | 8.770 | 8.165 | 9.706 |
| ai_share=0.33 | (1,16,1,36,46) | 9.865 | 9.812 | 9.810 | 9.896 | 9.886 | 8.770 | 8.150 | 9.759 |
| ai_share=0.5 | (1,16,1,36,46) | 10.061 | 9.920 | 9.921 | 10.249 | 10.217 | 8.869 | 8.100 | 9.894 |
| ai_share=0.7 | (1,1,21,36,41) | 10.239 | 10.004 | 10.004 | 10.609 | 10.639 | 8.962 | 8.035 | 10.011 |
| tau=0.5,D=0.15 | (1,1,21,36,41) | 10.020 | 9.962 | 9.951 | 10.242 | 10.299 | 8.904 | 7.961 | 9.947 |
| tau=0.5,D=0.4 | (1,16,1,36,46) | 9.962 | 9.973 | 9.942 | 10.186 | 10.121 | 8.886 | 7.896 | 9.978 |
| tau=1.5,D=0.15 | (1,16,1,36,46) | 9.870 | 9.820 | 9.824 | 9.924 | 9.876 | 8.787 | 8.155 | 9.769 |
| tau=1.5,D=0.4 | (6,3,2,38,51) | 9.597 | 9.660 | 9.652 | 9.421 | 9.057 | 8.598 | 8.352 | 9.596 |
| tau=3.0,D=0.15 | (1,16,1,36,46) | 9.648 | 9.522 | 9.524 | 9.689 | 9.643 | 8.673 | 8.282 | 9.476 |
| tau=3.0,D=0.4 | (1,11,1,36,51) | 9.000 | 8.921 | 8.918 | 8.802 | 8.485 | 8.255 | 8.771 | 8.854 |
| reuse=0.2 | (1,16,1,36,46) | 9.868 | 9.816 | 9.811 | 9.990 | 9.917 | 8.824 | 8.093 | 9.796 |
| reuse=0.45 | (1,16,1,36,46) | 9.857 | 9.821 | 9.822 | 9.921 | 9.874 | 8.795 | 8.153 | 9.772 |
| reuse=0.8 | (1,16,1,36,46) | 9.824 | 9.776 | 9.776 | 9.827 | 9.781 | 8.754 | 8.206 | 9.714 |

Max shortfall vs best of set: (1,11,1,36,51) 0.399; (6,3,2,38,51) 0.635; (6,3,3,37,51) 0.635; (1,16,1,36,46) 0.317; (1,1,21,36,41) 0.603; (1,9,39,5,46) 1.676; (8,16,6,7,63) 2.604; (7,3,1,39,50) 0.628

### Sensitivity, Game 2 (CC-041; best_guess mix with one knob moved; population seeds [301, 302, 303])

| Variant | Best of set | (1,0,48,51,0) | (0,0,48,52,0) | (0,0,35,0,65) | (2,1,41,56,0) | (3,0,41,56,0) | (0,0,38,0,62) |
|---|---|---|---|---|---|---|---|
| ai_share=0.0 | (0,0,35,0,65) | 6.960 | 6.995 | 7.153 | 7.038 | 7.038 | 7.048 |
| ai_share=0.15 | (0,0,35,0,65) | 7.284 | 7.295 | 7.298 | 7.273 | 7.272 | 7.203 |
| ai_share=0.33 | (1,0,48,51,0) | 7.596 | 7.578 | 7.562 | 7.480 | 7.480 | 7.494 |
| ai_share=0.5 | (0,0,35,0,65) | 7.853 | 7.813 | 7.865 | 7.709 | 7.711 | 7.822 |
| ai_share=0.7 | (0,0,35,0,65) | 8.170 | 8.088 | 8.181 | 7.926 | 7.929 | 8.173 |
| tau=0.5,D=0.15 | (1,0,48,51,0) | 7.952 | 7.948 | 7.865 | 7.691 | 7.686 | 7.910 |
| tau=0.5,D=0.4 | (1,0,48,51,0) | 8.000 | 7.998 | 7.836 | 7.755 | 7.749 | 7.855 |
| tau=1.5,D=0.15 | (0,0,35,0,65) | 7.569 | 7.553 | 7.602 | 7.488 | 7.488 | 7.511 |
| tau=1.5,D=0.4 | (0,0,35,0,65) | 7.060 | 7.063 | 7.333 | 7.155 | 7.164 | 7.037 |
| tau=3.0,D=0.15 | (2,1,41,56,0) | 7.250 | 7.231 | 7.254 | 7.306 | 7.305 | 7.142 |
| tau=3.0,D=0.4 | (2,1,41,56,0) | 6.098 | 6.081 | 6.650 | 6.701 | 6.699 | 6.378 |
| reuse=0.2 | (1,0,48,51,0) | 7.406 | 7.368 | 7.322 | 7.274 | 7.259 | 7.222 |
| reuse=0.45 | (1,0,48,51,0) | 7.567 | 7.554 | 7.535 | 7.448 | 7.446 | 7.440 |
| reuse=0.8 | (0,0,35,0,65) | 7.830 | 7.837 | 7.866 | 7.760 | 7.771 | 7.845 |

Max shortfall vs best of set: (1,0,48,51,0) 0.603; (0,0,48,52,0) 0.620; (0,0,35,0,65) 0.164; (2,1,41,56,0) 0.261; (3,0,41,56,0) 0.266; (0,0,38,0,62) 0.323

### Red team (CC-042): payout lost when 20% / 40% of applicants play a targeted counter (100k fresh paired groups)

| Base | Allocation | Base payout | Loss at 20% | Loss at 40% | Main counter |
|---|---|---|---|---|---|
| best_guess | (1,0,48,51,0) | 7.562 | 2.50 | 4.22 | (0,0,48,52,0) |
| best_guess | (0,0,48,52,0) | 7.545 | 2.62 | 4.23 | (10,20,0,60,10) |
| best_guess | (0,0,35,0,65) | 7.601 | 2.58 | 4.19 | (1,32,0,1,66) |
| best_guess | (2,1,41,56,0) | 7.478 | 2.52 | 4.31 | (0,1,42,57,0) |
| best_guess | (3,0,41,56,0) | 7.481 | 2.56 | 4.39 | (0,0,42,58,0) |
| best_guess | (0,0,38,0,62) | 7.431 | 2.15 | 3.60 | (1,35,0,1,63) |
| ai_heavy | (1,0,48,51,0) | 8.113 | 2.63 | 4.46 | (0,0,48,52,0) |
| ai_heavy | (0,0,48,52,0) | 8.051 | 2.75 | 4.47 | (10,20,0,60,10) |
| ai_heavy | (0,0,35,0,65) | 8.119 | 2.47 | 4.14 | (1,32,0,1,66) |
| ai_heavy | (2,1,41,56,0) | 7.969 | 2.76 | 4.73 | (0,1,42,57,0) |
| ai_heavy | (3,0,41,56,0) | 7.986 | 2.86 | 4.85 | (0,0,42,57,1) |
| ai_heavy | (0,0,38,0,62) | 8.030 | 2.72 | 4.47 | (1,35,0,1,63) |
| levelk_tau3 | (1,0,48,51,0) | 4.336 | 0.82 | 1.46 | (0,0,49,51,0) |
| levelk_tau3 | (0,0,48,52,0) | 4.358 | 1.01 | 1.60 | (10,20,0,60,10) |
| levelk_tau3 | (0,0,35,0,65) | 5.065 | 1.34 | 2.14 | (10,10,0,10,70) |
| levelk_tau3 | (2,1,41,56,0) | 5.688 | 1.63 | 2.84 | (0,1,42,57,0) |
| levelk_tau3 | (3,0,41,56,0) | 5.683 | 2.03 | 3.46 | (0,0,42,57,1) |
| levelk_tau3 | (0,0,38,0,62) | 4.578 | 1.06 | 1.68 | (1,35,0,1,63) |
| equilibrium | (1,0,48,51,0) | 4.805 | 1.51 | 2.51 | (0,0,48,52,0) |
| equilibrium | (0,0,48,52,0) | 4.870 | 1.43 | 2.27 | (10,20,0,60,10) |
| equilibrium | (0,0,35,0,65) | 4.440 | 0.92 | 1.52 | (1,32,0,1,66) |
| equilibrium | (2,1,41,56,0) | 5.170 | 1.48 | 2.58 | (0,1,42,57,0) |
| equilibrium | (3,0,41,56,0) | 5.125 | 1.82 | 3.04 | (0,0,42,57,1) |
| equilibrium | (0,0,38,0,62) | 4.616 | 0.87 | 1.45 | (1,35,0,1,63) |

## 7. Reproduction

Sample counts per phase:
- Phase 0 (scorer agreement): differential test of engine vs independent reference on 1,000,000 random and tie-heavy groups, 0 mismatches (codex CX-002; claude-code CC-001, seed 9917).
- Phase 1 (pool model): 9 named, 240 prior, 4 holdout scenarios, 400 rows per archetype. The frozen arrays (`results/frozen_populations/training.npz`, `holdout.npz`) regenerate bit-identically on both machines.
- Phase 2 (Game 1): exact scores of all 4,598,126 allocations on all 249 training scenarios (CX-020; independent CC-010). Strong near-equilibrium stress: 64,663 exact best-response updates, exploitability at most 0.049 (CX-061).
- Phase 3 (Game 2): 21,016 initial candidates, 2,021 raced, 50 local-search starts over 10 rounds, then 72 candidates x 249 scenarios x 100,000 groups (CX-031). Independent search: CC-030.
- Phase 4: sensitivity CC-020, CC-031, CC-041 (3 population seeds; 200,000 groups per variant for Game 2); red team CC-040, CC-042 (100,000 fresh paired groups); row-seed stability CX-063 (3 replicas x 240 x 200,000 groups).
- Phase 5: CX-050, 1,000,000 Game 2 groups per finalist for each of 253 scenarios and 1,000,000-matchup Game 1 cross-checks. Reproduction CC-050 (12 holdout units x 1,000,000 groups; 9 named x 1,000,000), CC-051 (240 prior x 200,000), CC-052 (50 extra Game 1 cross-checks).

Seeds: populations use base 110300 plus the scenario's global index (named, prior, holdout), so holdouts are 110549 to 110552, with supplemental row seeds 210549+i and 310549+i. Codex validation seed 505000. claude-code draw seeds 777001 to 777003 and 777101 to 777110.

Commit: frozen implementation at 16e7ada (CX-050), `populations.py` SHA-256 bee92b5b5fcc278f6958bfa6aa608827ddf6f688905a05faaa32b21058a18366.

Regenerate every table in this file from saved results, with no simulation:

```bash
python scripts/cc_results_tables.py
```

## 8. Unfinished work and limitations

- The applicant pool is modeled, not observed. The AI-assisted cluster (E) was written from general knowledge of chatbot answers; no chatbots were queried. FiveThirtyEight Riddler data (CX-060) was used only as qualitative support for human habits.
- Monte Carlo intervals are conditional on the modeled populations. Resampling population rows moves the 240-scenario average by about 0.008 payout points (SD, CX-063), and single holdouts by up to 0.31 across row seeds (holdout_sophisticated: 5.46 to 5.77 for the Game 2 pick).
- The Game 2 local search stopped at its 10-round cap; the leader was stable after round 1, but this is not proof of a global optimum.
- The named `equilibrium` scenario is coarse self-play (Game 1 exploitability about 2.0). The strong near-equilibrium stress (CX-061) exists only for Game 1, where the pick scores 7.5067 against a 7.5 break-even. No comparable near-equilibrium check was run for Game 2.
- One of codex's 25 original Game 1 Monte Carlo cross-checks failed at 3 standard errors (see section 2). It is preserved, not re-rolled.
