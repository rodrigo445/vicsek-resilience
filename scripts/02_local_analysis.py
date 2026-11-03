#!/usr/bin/env python
"""Reproduce final local-region predictive analyses for preserved raw datasets."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from vicsek.datasets import InputRegistry, load_fold_assignment, load_local_dataset
from vicsek.prediction import (
    bootstrap_mse_gain,
    bootstrap_within_state_gain,
    combine_oof,
    model_metrics_from_combined,
    run_nested_model,
    run_within_state,
)
from vicsek.validation import attach_outer_folds

DATASET_TO_N = {
    "N400_m10": 400,
    "N400_m10_T300": 400,
    "N1600_m10": 1600,
    "N1600_m160": 1600,
}


def run_algorithm(frame: pd.DataFrame, target: str, algorithm: str, bootstrap: int) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    mg = run_nested_model(frame, target, "MG", algorithm=algorithm, inner_seed=510000)
    m2 = run_nested_model(frame, target, "M2", algorithm=algorithm, inner_seed=510000)
    combined = combine_oof({"MG": mg, "M2": m2})
    metrics = model_metrics_from_combined(combined, ["MG", "M2"])
    gain = bootstrap_mse_gain(
        combined,
        "MG",
        "M2",
        n_bootstrap=bootstrap,
        seed=520000,
    )
    within_result, within_point = run_within_state(frame, target, algorithm=algorithm)
    within_bootstrap = bootstrap_within_state_gain(
        within_result.oof,
        n_bootstrap=bootstrap,
        seed=530000 if algorithm == "ridge" else 530100,
    )
    within = {
        **within_bootstrap,
        "algorithm": algorithm,
        "point_estimate_crosscheck": within_point["fraction_mse_removed"],
        "within_oof": within_result.oof,
    }
    return combined, metrics, gain, within


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dataset", choices=sorted(DATASET_TO_N), required=True)
    parser.add_argument("--algorithm", choices=["ridge", "hgb", "both"], default="ridge")
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
    frame, target = load_local_dataset(args.project_root, registry, args.dataset)
    spec = registry.section("local", args.dataset)
    response_window = int(spec["response_window"]) if "response_window" in spec else None
    system_size = DATASET_TO_N[args.dataset]
    assignment = load_fold_assignment(args.project_root, registry, system_size)
    if assignment is None:
        raise RuntimeError("local analysis requires a preserved run-level outer-fold assignment")
    frame = attach_outer_folds(frame, assignment)

    output = Path(args.output_root) / f"local_{args.dataset}"
    output.mkdir(parents=True, exist_ok=True)
    algorithms = [args.algorithm] if args.algorithm != "both" else ["ridge", "hgb"]
    gain_rows = []
    within_rows = []

    for algorithm in algorithms:
        combined, metrics, gain, within = run_algorithm(frame, target, algorithm, args.bootstrap)
        combined.to_csv(output / f"{algorithm}_oof_predictions.csv", index=False)
        metrics.assign(algorithm=algorithm).to_csv(output / f"{algorithm}_model_metrics.csv", index=False)
        within_oof = within.pop("within_oof")
        within_oof.to_csv(output / f"{algorithm}_within_oof.csv", index=False)
        gain_rows.append({**gain, "algorithm": algorithm})
        within_rows.append(within)

    gain_table = pd.DataFrame(gain_rows)
    within_table = pd.DataFrame(within_rows)
    gain_table.to_csv(output / "local_information_gain.csv", index=False)
    within_table.to_csv(output / "within_state_gain.csv", index=False)
    pd.DataFrame(
        [{
            "dataset": args.dataset,
            "N": system_size,
            "target": target,
            "response_window": response_window,
            "algorithms": ",".join(algorithms),
            "bootstrap": args.bootstrap,
        }]
    ).to_csv(output / "analysis_metadata.csv", index=False)

    print(f"\n{args.dataset}: target={target}, response_window={response_window}")
    print("\nMG -> M2")
    print(gain_table.to_string(index=False))
    print("\nWithin-state")
    print(within_table.to_string(index=False))
    print(f"\nSaved to {output}")


if __name__ == "__main__":
    main()
