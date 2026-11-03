#!/usr/bin/env python
"""Assemble compact publication tables from clean-pipeline outputs."""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

import pandas as pd


def load_refs(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _append_local_rows(
    rows: list[dict[str, object]],
    *,
    results: Path,
    dataset: str,
    n: int,
    m: int,
    response_window: int,
    status: str,
) -> None:
    directory = results / f"local_{dataset}"
    gain_path = directory / "local_information_gain.csv"
    within_path = directory / "within_state_gain.csv"

    if gain_path.is_file():
        for _, result in pd.read_csv(gain_path).iterrows():
            rows.append(
                {
                    "N": n,
                    "m": m,
                    "response_window": response_window,
                    "algorithm": str(result.algorithm),
                    "analysis": "MG->M2",
                    "gain": float(result.fraction_mse_removed),
                    "ci95_lower": float(result.ci95_lower),
                    "ci95_upper": float(result.ci95_upper),
                    "source": "clean_pipeline",
                    "status": status,
                    "dataset": dataset,
                }
            )

    if within_path.is_file():
        for _, result in pd.read_csv(within_path).iterrows():
            rows.append(
                {
                    "N": n,
                    "m": m,
                    "response_window": response_window,
                    "algorithm": str(result.algorithm),
                    "analysis": "within_state",
                    "gain": float(result.fraction_mse_removed),
                    "ci95_lower": float(result.ci95_lower),
                    "ci95_upper": float(result.ci95_upper),
                    "source": "clean_pipeline",
                    "status": status,
                    "dataset": dataset,
                }
            )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", default=str(root / "results" / "final"))
    parser.add_argument("--reference", default=str(root / "configs" / "reference_results.toml"))
    args = parser.parse_args()

    results = Path(args.results_root)
    refs = load_refs(Path(args.reference))
    tables = results / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Global results
    # ------------------------------------------------------------------
    global_rows: list[dict[str, object]] = []
    global_full_rows: list[dict[str, object]] = []
    comparisons = [
        ("M0", "M1", "linear_mesostructure", "robust"),
        ("P0", "Pk", "mean_degree_after_nonlinear_macro", "robust"),
        ("P0", "P1", "full_mesostructure_after_nonlinear_macro", "robust"),
    ]
    for n in (100, 400, 1600):
        path = results / f"global_N{n}" / "information_gains.csv"
        if not path.is_file():
            continue
        frame = pd.read_csv(path)
        for baseline, candidate, interpretation, default_status in comparisons:
            row = frame[
                (frame.baseline_model == baseline) & (frame.candidate_model == candidate)
            ]
            if len(row) != 1:
                continue
            result = row.iloc[0]
            status = (
                "legacy_sensitivity"
                if n == 400 and baseline == "P0" and candidate == "P1"
                else default_status
            )
            record = {
                "N": n,
                "comparison": f"{baseline}->{candidate}",
                "interpretation": interpretation,
                "gain": float(result.fraction_mse_removed),
                "ci95_lower": float(result.ci95_lower),
                "ci95_upper": float(result.ci95_upper),
                "bootstrap_fraction_positive": float(result.bootstrap_fraction_positive),
                "status": status,
                "source": "clean_pipeline",
            }
            global_full_rows.append(record)
            if (baseline, candidate) in {("M0", "M1"), ("P0", "Pk")}:
                global_rows.append(record)

    pd.DataFrame(global_rows).to_csv(tables / "global_information_summary.csv", index=False)
    pd.DataFrame(global_full_rows).to_csv(tables / "global_full_summary.csv", index=False)

    # ------------------------------------------------------------------
    # Local results
    # ------------------------------------------------------------------
    local_rows: list[dict[str, object]] = []

    # N=100 is retained only as historical context. The raw final replicate
    # dataset is not in the minimal frozen input set, so its response-window
    # semantics cannot be re-audited here and it is excluded from matched
    # cross-size figures.
    for algorithm in ("ridge", "hgb"):
        ref = refs["local"]["N100_m10"]
        for analysis, key in [
            ("MG->M2", f"{algorithm}_MG_to_M2"),
            ("within_state", f"{algorithm}_within"),
        ]:
            local_rows.append(
                {
                    "N": 100,
                    "m": 10,
                    "response_window": float("nan"),
                    "algorithm": algorithm,
                    "analysis": analysis,
                    "gain": float(ref[key]),
                    "ci95_lower": float("nan"),
                    "ci95_upper": float("nan"),
                    "source": "frozen_historical_benchmark",
                    "status": "historical_unmatched_window",
                    "dataset": "N100_m10_historical",
                }
            )

    # Historical/reproduced N=400 T=100 benchmark.
    _append_local_rows(
        local_rows,
        results=results,
        dataset="N400_m10",
        n=400,
        m=10,
        response_window=100,
        status="historical_T100",
    )

    # Matched-horizon T=300 analyses used for scientific scale comparisons.
    for dataset, n, m in [
        ("N400_m10_T300", 400, 10),
        ("N1600_m10", 1600, 10),
        ("N1600_m160", 1600, 160),
    ]:
        _append_local_rows(
            local_rows,
            results=results,
            dataset=dataset,
            n=n,
            m=m,
            response_window=300,
            status="matched_T300",
        )

    local = pd.DataFrame(local_rows)
    local.to_csv(tables / "local_scale_summary.csv", index=False)

    matched = local[
        (local["source"] == "clean_pipeline")
        & (local["response_window"] == 300)
        & (local["status"] == "matched_T300")
    ].copy()
    matched.to_csv(tables / "local_matched_horizon_summary.csv", index=False)

    # ------------------------------------------------------------------
    # Audits
    # ------------------------------------------------------------------
    validation = results / "reference_validation.csv"
    if validation.is_file():
        pd.read_csv(validation).to_csv(tables / "reproducibility_audit.csv", index=False)

    input_audit = results / "input_audit.csv"
    if input_audit.is_file():
        pd.read_csv(input_audit).to_csv(tables / "input_integrity_audit.csv", index=False)

    semantics_audit = results / "response_semantics_audit.csv"
    if semantics_audit.is_file():
        pd.read_csv(semantics_audit).to_csv(
            tables / "response_semantics_audit.csv", index=False
        )

    print(f"Final tables written to {tables}")


if __name__ == "__main__":
    main()
