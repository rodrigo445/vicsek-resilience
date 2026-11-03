#!/usr/bin/env python
"""Reproduce final state-level global/mesoscopic predictive analyses."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from vicsek.datasets import InputRegistry, load_fold_assignment, load_global_dataset
from vicsek.prediction import (
    bootstrap_mse_gain,
    combine_oof,
    model_metrics_from_combined,
    run_nested_model,
)
from vicsek.validation import attach_outer_folds, make_balanced_run_assignment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--N", type=int, choices=[100, 400, 1600], required=True)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "configs" / "final_inputs.toml"),
    )
    parser.add_argument(
        "--output-root",
        default=str(Path(__file__).resolve().parents[1] / "results" / "final"),
    )
    args = parser.parse_args()

    registry = InputRegistry.from_file(args.config)
    frame = load_global_dataset(args.project_root, registry, args.N)
    assignment = load_fold_assignment(args.project_root, registry, args.N)
    if assignment is None:
        # N=100: the old repository retained only the fold-design summary, not
        # the run-to-fold mapping. Recreate a deterministic balanced 10-fold CV.
        assignment = make_balanced_run_assignment(frame, 10, seed=28100)
    frame = attach_outer_folds(frame, assignment)

    output = Path(args.output_root) / f"global_N{args.N}"
    output.mkdir(parents=True, exist_ok=True)

    # Preserve the historically validated hyperparameter protocol.
    # N=400 was analysed with 20 logarithmically spaced Ridge penalties;
    # the later N=1600 confirmatory pipeline used 30.  Keeping this
    # size-specific choice is important for the relatively unstable P1 model.
    ridge_alphas = (
        np.logspace(-4, 3, 20)
        if args.N == 400
        else np.logspace(-4, 3, 30)
    )

    models = ["M0", "Mk", "M1", "P0", "Pk", "P1"]
    results = {
        model: run_nested_model(
            frame,
            "state_mean_response",
            model,
            algorithm="ridge",
            inner_seed=311650 if args.N == 1600 else 310000 + args.N,
            ridge_alphas=ridge_alphas,
        )
        for model in models
    }
    combined = combine_oof(results)
    metrics = model_metrics_from_combined(combined, models)
    comparisons = pd.DataFrame(
        [
            bootstrap_mse_gain(combined, "M0", "M1", n_bootstrap=args.bootstrap, seed=101 + args.N),
            bootstrap_mse_gain(combined, "P0", "Pk", n_bootstrap=args.bootstrap, seed=201 + args.N),
            bootstrap_mse_gain(combined, "P0", "P1", n_bootstrap=args.bootstrap, seed=301 + args.N),
        ]
    )

    combined.to_csv(output / "oof_predictions.csv", index=False)
    metrics.to_csv(output / "model_metrics.csv", index=False)
    comparisons.to_csv(output / "information_gains.csv", index=False)
    pd.concat([r.fold_metrics for r in results.values()], ignore_index=True).to_csv(
        output / "outer_fold_metrics.csv", index=False
    )

    print(f"\nN={args.N} global analysis")
    print(metrics.to_string(index=False))
    print("\nInformation gains")
    print(comparisons.to_string(index=False))
    print(f"\nSaved to {output}")


if __name__ == "__main__":
    main()
