# AGENTS.md: Castle allocation research (shared brief)

Two coding agents work in this repository at the same time: OpenAI Codex (agent id `codex`) and Anthropic Claude Code (agent id `claude-code`). This file is the source of truth for both. Read it fully at the start of every session, and read PLAN.md before you claim or start a task. The owner is Emilio; his latest instruction overrides this file. Agents change AGENTS.md or PLAN.md only after a DECISION both have posted.

Owner settings (Emilio may edit):
- Time budget: 3 hours of wall-clock time from the first HELLO. Reserve the last 25% for final validation and write-up.
- Coordination issue title: `Coordination`

## 1. Mission

A job application asks for two allocations of 100 soldiers across five castles, each scored against the other applicants. Find the single best allocation for each game and back it with evidence. The hard part is not simulation noise. It is not knowing what the other applicants submitted. Assume the pool is applicants to a competitive finance program: quantitatively minded students, many of them using AI tools, in an unknown mix. An allocation that only beats random or naive opponents is a failure.

Deliver two allocations (five integers each, summing to 100), the evidence behind them, and a short, truthful answer to the application's strategy question.

## 2. Rules (implement exactly)

Castles 1 to 5 are worth 1, 2, 3, 4, 5 points (15 in total). Each player submits nonnegative integers (x1, ..., x5) that sum to exactly 100. There are 4,598,126 valid allocations.

Game 1, head to head. My Game 1 allocation is compared with every other applicant's Game 1 allocation. On each castle, more soldiers wins its points and a tie (including 0 vs 0) splits them evenly. My score is my average castle points per matchup. Maximize expected castle points, not the chance of winning a matchup.

Game 2, four-way battle. Applicants are put in random groups of 4 (using their Game 2 allocations), reshuffled thousands of times. On each castle, the highest count wins its points; if k players tie for highest (including all four at 0), each gets value/k. Players are ranked by total castle points and paid by place: 1st 9, 2nd 4, 3rd 2, 4th 0. Players tied on total split the payouts of the places they jointly occupy (two tied for 1st get (9+4)/2 = 6.5 each). My score is my average payout. Maximize expected payout, not castle points.

Exact arithmetic: score in integer units of 1/12 point (12 is the lcm of 1, 2, 3, 4), so every castle share and every split payout is an integer. Never test float totals for equality. Invariants: Game 1 points in a matchup sum to 180 units; Game 2 castle points and payouts in a group each sum to 180 units.

Test vectors (castles listed in order 1 to 5; both implementations must reproduce these exactly):

| ID | Allocations | Castle points | Payouts |
|---|---|---|---|
| G1-a | A (20,20,20,20,20) vs B (0,0,30,35,35) | A 3, B 12 | n/a |
| G1-b | A (0,25,25,25,25) vs B (0,25,25,50,0) | A 8, B 7 | n/a |
| G2-a | (0,0,0,50,50), (0,0,34,33,33), (20,20,20,20,20), (1,1,1,1,96) | 4, 3, 3, 5 | 4, 1, 1, 9 |
| G2-b | (10,30,30,30,0), (10,30,30,0,30), (10,30,0,30,30), (70,10,10,10,0) | 50/12, 56/12, 62/12, 1 | 2, 4, 9, 0 |
| G2-c | (0,0,0,50,50), (0,0,0,50,50), (50,50,0,0,0), (0,0,100,0,0) | 4.5, 4.5, 3, 3 | 6.5, 6.5, 1, 1 |
| G2-d | four copies of (20,20,20,20,20) | 3.75 each | 3.75 each |
| G2-e | (0,0,0,0,100), (100,0,0,0,0), (0,100,0,0,0), (0,0,100,0,0) | 6, 2, 3, 4 | 9, 0, 2, 4 |

## 3. Structure to exploit (verified)

1. Game 1 is additive by castle. Against any opponent distribution, E[score(x)] = sum over castles j of v_j * (P(Y_j < x_j) + 0.5 * P(Y_j = x_j)), where Y_j is an opponent's count on castle j. Only the per-castle marginals matter. For any modeled pool, Game 1 is solved exactly by scoring all 4,598,126 allocations (vectorized numpy takes about a second) or by dynamic programming. Monte Carlo is only a cross-check.
2. Game 2 is not additive, because placement depends on everyone's totals. Use Monte Carlo over groups with common random numbers: every candidate faces the identical sampled opponent triples, and comparisons use paired differences. In a pilot run, 1,000,000 groups gave a standard error of about 0.003 payout points or less per candidate.
3. For any fixed belief about the pool, expected score is linear in the opponent mix, so no randomized strategy beats the best single allocation. Use equilibrium and self-play only to build sophisticated opponent populations and to stress-test. We submit one allocation per game.
4. In Game 2, any player with 8 or more castle points is guaranteed sole 1st (the other three share at most 7). The 9/4/2/0 payout is top-heavy: 1st is worth 5 more than 2nd.
5. The dominant risk is a wrong model of the applicant pool. Spend effort there, not on more decimal places.

## 4. Lanes

Defaults; reassign through the Coordination issue when it speeds things up.

`codex`: engine and search.
- `src/castles/engine.py`: fast scoring (numpy; numba optional with a numpy fallback), exact Game 1 evaluator over all allocations, Game 2 Monte Carlo with common random numbers, paired comparisons.
- `src/castles/search.py`: candidate generation, racing, local search, final validation runner.
- `pyproject.toml`, `src/castles/__init__.py`, `src/castles/rules.py`, `.github/workflows/tests.yml` (fast tests only), `benchmarks/`.

`claude-code`: opponents, robustness, write-up.
- `src/castles/reference.py`: slow, obviously correct scorer, written independently (it must not import engine.py or rules.py), used to differential-test the engine.
- `src/castles/populations.py`: archetypes and the scenario registry (see PLAN.md).
- `src/castles/robustness.py`: regret tables, red-team populations, sensitivity analysis.
- `RESULTS.md` and `STRATEGY_ANSWER.md` drafts.

Shared: `tests/` (add your own files; don't edit the other agent's), `rules.py` (constants; change only by agreement).

Interface contract (build against it before the other side exists; post a REQUEST before changing it):

```python
# rules.py
VALUES = (1, 2, 3, 4, 5); TOTAL = 100; UNIT = 12; PAYOUTS_UNITS = (108, 48, 24, 0)

# populations.py
@dataclass
class Population:
    name: str
    seed: int
    g1: np.ndarray   # (N, 5) int, each applicant type's Game 1 allocation
    g2: np.ndarray   # (N, 5) int, the same applicant type's Game 2 allocation
    w: np.ndarray    # (N,) weights summing to 1

def get_population(name: str, seed: int) -> Population
def list_scenarios(kind: str) -> list[str]        # kind in {"named", "prior", "holdout"}

# engine.py
def g1_marginals(pop: Population) -> np.ndarray   # (5, 101), P(Y_j = k)
def g1_exact(x_batch: np.ndarray, marginals: np.ndarray) -> np.ndarray       # (n,) expected castle points
def g2_sample_opponents(pop: Population, n: int, seed: int) -> np.ndarray    # (n, 3, 5)
def g2_eval(x_batch: np.ndarray, opps: np.ndarray) -> dict   # per candidate: mean, se, P(place 1..4), mean castle points
def g2_paired(x_a, x_b, opps: np.ndarray) -> tuple[float, float]             # mean difference, its standard error
```

## 5. Collaboration protocol

Identity. You know whether you are Codex or Claude Code; use the matching agent id. You may both post through the same GitHub account, so sign everything:
- Commit subjects start with `[codex]` or `[claude-code]`.
- Every issue or PR comment starts with a header line such as `[claude-code -> codex] FINDING`.

Channel. The GitHub issue titled `Coordination` is the message board. On start, run `gh issue list --search "Coordination in:title" --state all`. If none exists, create it. If two exist, use the lower number and close the other with a link. Message types: HELLO, CLAIM, DONE, FINDING, REQUEST, CHALLENGE, DECISION, BLOCKED. Keep messages short and concrete: allocations, scores with confidence intervals, experiment ids, commit SHAs.

Sync. Nothing notifies you; you only see the other agent's messages when you look. Sync (git fetch, read new Coordination comments, check open PRs and review requests) at session start, before claiming work, after finishing any task, before merging, and about every 20 minutes during long runs. Answer what is addressed to you first. Never busy-wait: if you are blocked, take the next unblocked task. Never say the other agent agreed unless its comment says so.

Branches and PRs.
- Work on branches named `codex/<topic>` or `claude-code/<topic>`, in your own clone or worktree. Never commit directly to main, never push to the other agent's branches, never force-push a shared branch, never resolve a conflict by dropping the other agent's work.
- Keep PRs small and tests passing, then post a REQUEST for review. A PR that stays inside your lane may be squash-merged at your next sync if nobody objected. A PR that touches the other lane or shared files needs the other agent's explicit approval comment.
- No shared append-only files. Log entries are one file each: `research/log/<UTC timestamp>-<agent id>-<slug>.md`. Experiment ids carry a prefix (`CX-001` for codex, `CC-001` for claude-code), and results go to `results/experiments/<id>.json`.

Verification norms.
- Re-run before you trust: a headline number from the other agent goes into RESULTS.md only after you reproduce it with a different seed.
- Red-team duty: each agent tries to beat the other's current leader, either with a plausible scenario where it does badly or a nearby allocation that does better.
- Disagreements: open an issue titled `Disagreement: <topic>`, state both claims, run one controlled experiment (paired, fresh seeds, full scenario set), and record a DECISION. Never average conflicting estimates.

Fallbacks. If you can push but `gh` doesn't work, send messages by appending to `coord/<agent id>.md` on a branch named `coord-<agent id>`, and read the other side with `git fetch origin coord-<other id>` then `git show origin/coord-<other id>:coord/<other id>.md`. If you can't reach GitHub at all, work your lane solo, keep messages in that file locally, and tell the owner. Never pretend a message was sent.

## 6. Standards

- Python 3.11 or later, numpy, pytest; numba optional. Keep dependencies minimal.
- Seeded `numpy.random.Generator` everywhere. Every experiment writes JSON with: id, agent, commit SHA, game, scenarios and seeds, sample counts, candidates, means, standard errors or confidence intervals, runtime, notes.
- Differential test gate: engine and reference must match exactly on 1,000,000 random groups, including tie-heavy groups drawn from a handful of round-number allocations. Run it as a script or a slow-marked test, not in CI. Optimization results don't count until it passes.
- If both agents share one computer, each uses at most half the CPU cores (`NUMBA_NUM_THREADS`, `OMP_NUM_THREADS`). Checkpoint long runs so they can resume.
- Run what you write. Never invent, estimate, or round up a result you didn't compute. Report failures and unfinished runs plainly.

## 7. Definition of done

- RESULTS.md following the template in PLAN.md: codex runs the final validation, claude-code reproduces the headline numbers with different seeds and drafts the file, codex approves it. It must show at least 1,000,000 fresh Game 2 groups per finalist per holdout scenario, and a 1,000,000-matchup Monte Carlo cross-check of the exact Game 1 numbers.
- STRATEGY_ANSWER.md following PLAN.md.
- A DECISION comment on the Coordination issue from each agent with the final picks, or a clearly documented disagreement.
