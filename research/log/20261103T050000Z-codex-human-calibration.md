# Historical human tendencies: descriptive calibration only

Codex downloaded the public FiveThirtyEight `riddler-castles` CSVs at upstream
commit `4c1ff5e3aef1816ae04af63218015066e186c147`, using verified HTTPS through
the existing proxy. Full URLs, SHA256 hashes, retrieval timestamp, histogram
counts and denominators are in `results/experiments/CX-060-human-calibration.json`.
Reproduce with:

```bash
/workspace/castle-venv/bin/python scripts/calibrate_human_data.py
```

The repository contains **five** rounds: rounds 1–4 have ten castles, round 5 has
thirteen. All 5,405 downloaded submissions are valid nonnegative integer vectors
summing to 100; none was excluded. Exact duplicates remain because the purpose
is frequencies among submissions rather than unique strategic choices.

| Round | Valid submissions / raw rows | Multiples of 5 among counts ≥5 | One above a multiple of 5 among counts ≥5 | Both cheapest castles abandoned |
|---|---:|---:|---:|---:|
| 1 (10 castles) | 1,349 / 1,349 | 2,322 / 7,403 = 31.37% | 1,906 / 7,403 = 25.75% | 291 / 1,349 = 21.57% |
| 2 (10 castles) | 902 / 902 | 1,556 / 5,478 = 28.40% | 1,488 / 5,478 = 27.16% | 113 / 902 = 12.53% |
| 3 (10 castles) | 1,321 / 1,321 | 2,344 / 7,366 = 31.82% | 1,630 / 7,366 = 22.13% | 186 / 1,321 = 14.08% |
| 4 (10 castles) | 938 / 938 | 1,778 / 5,349 = 33.24% | 1,025 / 5,349 = 19.16% | 235 / 938 = 25.05% |
| 5 (13 castles) | 895 / 895 | 1,614 / 5,714 = 28.25% | 1,301 / 5,714 = 22.77% | 298 / 895 = 33.30% |

The slot denominator for the middle columns excludes zeros and counts 1–4.
The +1 category is 6, 11, 16, …, 96, so it does not count the special choice
of one soldier. Among all positive slots, one-soldier deployments appear at
7.66%–17.00% across rounds (individual counts and denominators are in the JSON).
Allocations made entirely of multiples of five are only 3.69%–9.49% of all rows,
so rounding is a component of behavior rather than an adequate whole model.

This supports including varied round-number heaps, zero/one probes on cheap
castles, and edge-seeking families instead of exclusively smooth random draws.
It does **not** estimate any five-castle archetype weight. A residue one above
a multiple of five does not establish intent to beat round-number opponents.
Rates change across rounds without a monotone pattern; returning-player learning
cannot be identified because participant identities were removed.

The source's objective was head-to-head **war wins**, while our Game 1 objective
is average castle points and Game 2 is a four-way payout. The source is also a
self-selected historical puzzle audience, not finance applicants in 2026. No
human allocation is directly mapped into our game, no canonical population
was altered, and no final pick was selected using these data. These descriptive
frequencies do not have inferential confidence intervals because independent
sampling from our target audience is not established.

Verification: for every round, histogram entries sum to valid rows × castle
count, weighted histogram counts sum to valid rows ×100, and the reported heap
and +1 numerators/denominators exactly reconstruct from the saved histogram.
