# Castle allocation research

Research for two distinct allocation games: maximize expected castle points in
head-to-head play, and maximize expected finishing-place payout in four-player
play. The unknown applicant population is modeled explicitly; simulated scores
are conditional on these assumptions, not predictions about actual applicants.

## Development

Python 3.11+ is required. From the repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -e '.[test,fast]'
OMP_NUM_THREADS=2 NUMBA_NUM_THREADS=2 .venv/bin/python -m pytest -q
PYTHONPATH=src OMP_NUM_THREADS=2 NUMBA_NUM_THREADS=2 .venv/bin/python scripts/difftest.py --groups 1000000 --procs 2 --id CX-local-difftest
```

Numba acceleration is optional for correctness but recommended for the full
search. `src/castles/reference.py` is the independently written Claude reference;
`src/castles/engine.py` implements integer scoring and accelerated evaluation.
Never compare floating-point castle totals to decide ties. All scoring uses
integer twelfths.

Read `AGENTS.md` and `PLAN.md` for the research protocol, lane ownership, model
assumptions and validation requirements. The cloud task already has an isolated
checkout; use it directly without creating another worktree.

GitHub's REST API can be used through `gh api` if the GraphQL-based `gh issue`
and `gh pr` commands are denied. Never put credentials into repository files.
