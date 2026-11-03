#!/usr/bin/env python
"""Audit clean-pipeline outputs against the frozen exploratory benchmarks.

Only scientifically robust comparisons are *blocking* gates.  Historical
quantities known to be unstable (notably N=400 P0->P1) are retained as a
non-blocking legacy sensitivity audit rather than being tuned-to-match.
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

import pandas as pd


def read_references(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def close_enough(observed: float, expected: float, absolute_tolerance: float) -> bool:
    return abs(observed - expected) <= absolute_tolerance


def add_row(
    rows: list[dict[str, object]],
    *,
    analysis: str,
    expected: float,
    observed: float,
    tolerance: float,
    gate_type: str,
    note: str = "",
) -> None:
    rows.append(
        {
            "analysis": analysis,
            "expected": expected,
            "observed": observed,
            "difference": observed - expected,
            "tolerance": tolerance,
            "within_tolerance": close_enough(observed, expected, tolerance),
            "gate_type": gate_type,
            "note": note,
        }
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", default=str(root / "results" / "final"))
    parser.add_argument("--reference", default=str(root / "configs" / "reference_results.toml"))
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.01,
        help="Absolute tolerance on fractional MSE removed (default 0.01 = one percentage point)",
    )
    args = parser.parse_args()

    references = read_references(Path(args.reference))
    results_root = Path(args.results_root)
    rows: list[dict[str, object]] = []

    # Robust global claims used in the final interpretation.
    for n in [100, 400, 1600]:
        path = results_root / f"global_N{n}" / "information_gains.csv"
        if not path.is_file():
            continue
        data = pd.read_csv(path)
        for baseline, candidate, key in [
            ("M0", "M1", "M0_to_M1"),
            ("P0", "Pk", "P0_to_Pk"),
        ]:
            match = data[(data.baseline_model == baseline) & (data.candidate_model == candidate)]
            if len(match) != 1:
                continue
            add_row(
                rows,
                analysis=f"N{n} {baseline}->{candidate}",
                expected=float(references["global"][f"N{n}"][key]),
                observed=float(match.iloc[0].fraction_mse_removed),
                tolerance=args.tolerance,
                gate_type="robust_gate",
            )

        # P0->P1 is robust for N=100 and N=1600, but historically uncertain
        # for N=400 and sensitive to the exact regularized basis used in Day 32.
        match = data[(data.baseline_model == "P0") & (data.candidate_model == "P1")]
        if len(match) == 1:
            gate_type = "robust_gate" if n in {100, 1600} else "legacy_sensitivity"
            note = "" if n != 400 else (
                "Historical Day-32 P1 gain had considerable uncertainty; exact Day-32 "
                "regularized-design implementation was not retained. Report, do not tune-to-match."
            )
            add_row(
                rows,
                analysis=f"N{n} P0->P1",
                expected=float(references["global"][f"N{n}"]["P0_to_P1"]),
                observed=float(match.iloc[0].fraction_mse_removed),
                tolerance=args.tolerance,
                gate_type=gate_type,
                note=note,
            )

    # Local claims with preserved raw replicate datasets.
    # N1600_m160 is validated when that optional/full analysis has been recomputed.
    for dataset in ["N400_m10", "N1600_m10", "N1600_m160"]:
        directory = results_root / f"local_{dataset}"
        gain_path = directory / "local_information_gain.csv"
        within_path = directory / "within_state_gain.csv"
        if not gain_path.is_file():
            continue
        gains = pd.read_csv(gain_path)
        within = pd.read_csv(within_path) if within_path.is_file() else pd.DataFrame()
        ref = references["local"][dataset]
        for _, row in gains.iterrows():
            algorithm = str(row.algorithm).lower()
            key = f"{algorithm}_MG_to_M2"
            if key not in ref:
                continue
            add_row(
                rows,
                analysis=f"{dataset} {algorithm} MG->M2",
                expected=float(ref[key]),
                observed=float(row.fraction_mse_removed),
                tolerance=args.tolerance,
                gate_type="robust_gate",
            )
        for _, row in within.iterrows():
            algorithm = str(row.algorithm).lower()
            key = f"{algorithm}_within"
            if key not in ref:
                continue
            add_row(
                rows,
                analysis=f"{dataset} {algorithm} within",
                expected=float(ref[key]),
                observed=float(row.fraction_mse_removed),
                tolerance=args.tolerance,
                gate_type="robust_gate",
            )

    table = pd.DataFrame(rows)
    if table.empty:
        print("No clean-pipeline outputs found yet.")
        return

    table["pass"] = table["within_tolerance"] | (table["gate_type"] != "robust_gate")
    print(table.to_string(index=False))
    results_root.mkdir(parents=True, exist_ok=True)
    table.to_csv(results_root / "reference_validation.csv", index=False)

    failures = table[(table["gate_type"] == "robust_gate") & (~table["within_tolerance"].astype(bool))]
    if len(failures):
        raise SystemExit(
            f"\n{len(failures)} robust comparison(s) exceed tolerance. Do not make final figures yet."
        )

    sensitivities = table[(table["gate_type"] == "legacy_sensitivity") & (~table["within_tolerance"].astype(bool))]
    if len(sensitivities):
        print(
            "\nRobust validation passed. Non-blocking legacy sensitivity differences are "
            "documented in reference_validation.csv."
        )
    else:
        print("\nAll robust comparisons are within tolerance.")


if __name__ == "__main__":
    main()
