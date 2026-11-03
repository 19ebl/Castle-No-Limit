# Strategy answer drafts

Question: "How did you approach each game, and did your strategy change?"

Status: draft. The allocations match the current leaders and are updated after the Phase 5 final validation. Rewrite in your own words and keep only what you can explain.

## Short draft (about 80 words)

I treated the two games differently because they reward different things. Game 1 pays average castle points per matchup, so I aimed to win castles 4 and 5 cheaply against typical answers and gave up castle 3: 1, 11, 1, 36, 51. Game 2 pays by finishing place, and 1st is worth more than double 2nd, so I concentrated on winning two castles outright: 1, 0, 48, 51, 0. I directed AI coding agents that tested both against hundreds of modeled applicant pools.

## Longer draft (about 150 words)

My strategy changed between the games because the scoring changed. In Game 1, every matchup pays castle points, so the goal is a high average, not winning any single matchup. I set up and directed two AI coding agents to model the applicant pool as a mix of types: simple splits, chatbot answers, concentrated plays, and people who think a step ahead. They then scored every possible allocation exactly. The best was 1, 11, 1, 36, 51: just above common counts on castles 4 and 5, with castle 3 conceded.

Game 2 pays 9, 4, 2 and 0 by place, so finishing 1st matters far more than total points. Spreading soldiers tends to finish 2nd or 3rd. I switched to winning two castles outright, 1, 0, 48, 51, 0, and avoided 50, since many players pick round numbers. The main risk is many players choosing almost the same plan.
