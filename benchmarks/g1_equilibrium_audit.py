#!/usr/bin/env python3
"""Supplemental Game 1 fictitious-play stress test, outside the frozen prior.

Run: OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
     PYTHONPATH=src python benchmarks/g1_equilibrium_audit.py

This does not change the frozen populations, search, or primary selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from castles.engine import all_allocations, g1_exact, g1_table, g1_top


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=610300)
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--tolerance", type=float, default=0.05)
    parser.add_argument("--output", type=Path, default=Path("results/experiments/CX-061.json"))
    parser.add_argument("--pool", type=Path, default=Path("results/experiments/CX-061-g1pool.npz"))
    parser.add_argument("--search", type=Path, default=Path("results/experiments/CX-020.json"))
    args = parser.parse_args()
    if args.iterations < 1 or args.tolerance < 0:
        parser.error("iterations must be positive and tolerance nonnegative")
    started = time.perf_counter()
    rng = np.random.default_rng(args.seed)
    actions = [rng.multinomial(100, np.ones(5)/5).astype(np.int16)]
    counts = np.zeros((5, 101), dtype=np.int64)
    counts[np.arange(5), actions[0]] = 1
    trace = []
    for iteration in range(args.iterations + 1):
        marginals = counts / len(actions)
        best, value = g1_top(g1_table(marginals), 1)
        exploitability = float(value[0] - 7.5)
        if iteration % 250 == 0 or iteration == args.iterations or exploitability <= args.tolerance:
            trace.append(dict(iteration=iteration, support_samples=len(actions),
                              best_response=best[0].tolist(), exact_best_response_score=float(value[0]),
                              exploitability=exploitability))
        if exploitability <= args.tolerance or iteration == args.iterations:
            break
        action = best[0].copy()
        actions.append(action)
        counts[np.arange(5), action] += 1

    all_actions = np.asarray(actions, dtype=np.int16)
    support, multiplicity = np.unique(all_actions, axis=0, return_counts=True)
    weights = multiplicity / multiplicity.sum()
    self_score = float(np.dot(g1_exact(support, marginals), weights))
    np.testing.assert_allclose(self_score, 7.5, atol=1e-12, rtol=0)
    np.testing.assert_allclose(g1_exact(best, marginals)[0], value[0], atol=1e-12, rtol=0)
    # Independently verify the DP certificate by scanning every feasible action.
    exhaustive_best = float(np.max(g1_exact(all_allocations(), marginals)))
    np.testing.assert_allclose(exhaustive_best, value[0], atol=1e-12, rtol=0)
    args.pool.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.pool, g1=support, w=weights, multiplicity=multiplicity,
                        actions=all_actions, seed=np.array(args.seed), marginals=marginals)
    search = json.loads(args.search.read_text())
    fixed = np.asarray(search["finalists"], dtype=np.int16)
    scores = g1_exact(fixed, marginals)
    canonical = search["scenario_best"].get("equilibrium", {})
    canonical_value = canonical.get("mean")
    result = dict(
        id="CX-061", agent="codex", game=1,
        commit_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        implementation_source_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path("src/castles/engine.py"), Path("src/castles/rules.py"))},
        seed=args.seed, scenarios=["supplemental_exact_best_response_fictitious_play"],
        sample_counts=dict(fictitious_play_updates=iteration, empirical_actions=len(actions),
                           unique_support=len(support), feasible_best_response_allocations=4_598_126),
        candidates=fixed.tolist(), means=scores.tolist(), standard_errors=[0.0]*len(fixed),
        method="Symmetric fictitious play: one exact unrestricted integer-allocation best response per iteration; uniform empirical past actions including seeded initializer; incremental marginal counts.",
        stopping=dict(max_iterations=args.iterations, tolerance=args.tolerance,
                      attained_tolerance=exploitability <= args.tolerance),
        certificate=dict(exact_best_response=best[0].tolist(), exact_best_response_score=float(value[0]),
                         empirical_self_play_score=self_score,
                         exhaustive_allocation_scan_best=exhaustive_best,
                         exhaustive_verification_passed=True,
                         exact_exploitability_above_symmetric_value=exploitability),
        source_search=dict(path=str(args.search), sha256=hashlib.sha256(args.search.read_bytes()).hexdigest(),
                           fixed_finalists="CX-020 finalists; no tuning or primary selection on this supplemental stress"),
        canonical_equilibrium_named_scenario=dict(best_response=canonical.get("allocation"),
            exact_best_response_score=canonical_value,
            exploitability_above_7_5=None if canonical_value is None else canonical_value-7.5),
        pool=dict(path=str(args.pool), sha256=hashlib.sha256(args.pool.read_bytes()).hexdigest(),
                  weighting="multiplicity / total empirical actions", initializer=all_actions[0].tolist()),
        trace=trace, runtime_seconds=time.perf_counter()-started,
        notes=["Supplemental stress only: outside canonical populations, preregistered prior, holdout, and primary selection.",
               "Exact exploitability certificate is conditional on this finite empirical population and the Game 1 rules; it is not a proof of an exact Nash equilibrium or a forecast of actual applicants.",
               "The canonical named equilibrium scenario is a coarse approximation: its unrestricted best response can score materially above the symmetric 7.5-point benchmark.",
               "Finite-support fictitious play with exact best responses is stronger evidence of equilibrium-like play only to the extent the saved exploitability certificate is small.",
               "Game 2 equilibrium behavior is not assessed by this audit."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(dict(id=result["id"], updates=iteration, exploitability=exploitability,
                          scores=scores.tolist(), runtime_seconds=result["runtime_seconds"], output=str(args.output))))


if __name__ == "__main__":
    main()
