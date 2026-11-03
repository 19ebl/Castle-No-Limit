# Strategy answer drafts

Question: "How did you approach each game, and did your strategy change?"

Two drafts for Emilio. Rewrite them in your own words and keep only what you can explain in an interview. The numbers come from RESULTS.md.

## Short draft (about 80 words)

I treated the two games differently because they reward different things. Game 1 pays average castle points per matchup, so I aimed to win castles 4 and 5 cheaply and gave up castle 3: 1, 11, 1, 36, 51. Game 2 pays by finishing place, and 1st is worth more than double 2nd, so I concentrated on winning castles 3 and 4 outright: 1, 0, 48, 51, 0. I directed AI coding agents that tested both against hundreds of modeled applicant pools.

## Longer draft (about 150 words)

My strategy changed between the games because the scoring changed. In Game 1 every matchup pays castle points, so the goal is a high average, not winning any single matchup. I set up and directed two AI coding agents that modeled the applicant pool as a mix of types: simple splits, chatbot answers, concentrated plays, and people who think a step ahead. They scored every possible allocation exactly. The best was 1, 11, 1, 36, 51: just above common counts like 35 and 50 on castles 4 and 5, with castle 3 conceded.

Game 2 pays 9, 4, 2 and 0 by place, so finishing first matters far more than total points. I switched to winning castles 3 and 4 outright with 1, 0, 48, 51, 0, putting 51 rather than 50 on castle 4 because many players pick round numbers. It finished first about three times in four in our simulations.

## Facts behind each claim (for interview prep)

- "Every possible allocation exactly": Game 1 is scored castle by castle, so all 4,598,126 allocations were scored exactly in every modeled pool (CX-020, CC-010).
- "Just above common counts": in the modeled pool, 36 on castle 4 beats 82% of applicants and 51 on castle 5 beats 91%.
- "1st is worth more than double 2nd": payouts are 9, 4, 2 and 0.
- "About three times in four": P(1st) = 0.748 on the 240-scenario prior, ties split (CX-050).
- "Hundreds of modeled applicant pools": 240 prior mixtures, 9 named scenarios and 4 holdout scenarios.
- The pick changes if the pool is very sophisticated (Game 2: use 0, 0, 35, 0, 65) or mostly chatbot answers (Game 1: use 1, 16, 1, 36, 46). See RESULTS.md section 6.
