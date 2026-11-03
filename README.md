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

## Research and reproduction

The completed run saves experiment JSON under `results/experiments/` and the
exact synthetic applicant distributions under `results/frozen_populations/`.
These arrays, not regenerated approximations, are the inputs for independent
replication. Their manifests record seeds, parameters, and SHA256 checksums.

Regenerate tables from saved scores, without running another search:

```sh
python scripts/render_tables.py
```

The research phases run in this order:

```sh
python scripts/run_research.py g1
python scripts/run_research.py g2
python scripts/run_research.py preregister
python scripts/run_research.py validate
```

The runner currently writes fixed artifact paths: preserve an existing run's
artifacts before beginning a new run. It checks the frozen finalists, source
hashes, model inputs, seeds, and decision rule before holdout validation. A
population library cold build takes a few minutes; subsequent phases reuse
verified input snapshots. No persistent application server is required.

The supplemental Game 1 equilibrium stress can be reproduced with:

```sh
python benchmarks/g1_equilibrium_audit.py --iterations 100000 --tolerance 0.049
python benchmarks/check_g1_snapshot.py
```

Expected scores and confidence intervals are conditional on the modeled applicant
pools. Matchup sampling intervals do not quantify uncertainty about the real
applicant mix. The named `equilibrium` scenario is coarse self-play; `CX-061`
provides a separate stronger Game 1 stress with an exact exploitability bound.
Neither is empirical evidence about applicants' actual choices.
