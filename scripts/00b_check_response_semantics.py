#!/usr/bin/env python
"""Audit response-window semantics before cross-size local comparisons.

The final exploratory project preserved different response-column names across
phases. This audit verifies that the rows used for the matched-horizon analyses
really correspond to the full T=300 response, rather than relying only on a
column name.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from vicsek.datasets import InputRegistry, resolve_input


def _row(check: str, value: object, passed: bool, note: str = "") -> dict[str, object]:
    return {"check": check, "value": value, "pass": bool(passed), "note": note}


def _full_horizon_ratio(frame: pd.DataFrame, horizon: float) -> np.ndarray:
    """Compare integrated response with mean absolute difference * horizon.

    With unit-spaced samples, trapezoidal integration over the full horizon
    should be very close to mean(abs difference) * horizon. The tolerance used
    below is deliberately broad because endpoints make these quantities not
    algebraically identical.
    """
    response = pd.to_numeric(frame["response"], errors="coerce").to_numpy(float)
    mean_abs = pd.to_numeric(frame["mean_abs_phi_difference"], errors="coerce").to_numpy(float)
    denom = mean_abs * float(horizon)
    mask = np.isfinite(response) & np.isfinite(denom) & (np.abs(denom) > 1e-12)
    return response[mask] / denom[mask]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument(
        "--config",
        default=str(root / "configs" / "final_inputs.toml"),
    )
    parser.add_argument(
        "--output",
        default=str(root / "results" / "final" / "response_semantics_audit.csv"),
    )
    args = parser.parse_args()

    registry = InputRegistry.from_file(args.config)
    records: list[dict[str, object]] = []

    # N=400: both windows are explicitly stored in the same frozen replicate file.
    spec400 = registry.section("local", "N400_m10")
    file400 = resolve_input(args.project_root, str(spec400["replicates"]))
    n400 = pd.read_csv(
        file400,
        usecols=["auc_abs_delta_phi_0_100", "auc_abs_delta_phi_0_300"],
    )
    complete400 = bool(n400.notna().all().all())
    monotonic = bool(
        (
            pd.to_numeric(n400["auc_abs_delta_phi_0_300"], errors="coerce")
            + 1e-12
            >= pd.to_numeric(n400["auc_abs_delta_phi_0_100"], errors="coerce")
        ).all()
    )
    records.append(
        _row(
            "N400_has_complete_T100_and_T300_AUC",
            len(n400),
            complete400,
            "Both precomputed response windows must be present for every replicate.",
        )
    )
    records.append(
        _row(
            "N400_AUC_T300_ge_T100",
            float(
                (
                    n400["auc_abs_delta_phi_0_300"]
                    >= n400["auc_abs_delta_phi_0_100"] - 1e-12
                ).mean()
            ),
            monotonic,
            "Absolute-integral response over 0..300 cannot be smaller than over 0..100.",
        )
    )

    for dataset in ("N1600_m10", "N1600_m160"):
        spec = registry.section("local", dataset)
        path = resolve_input(args.project_root, str(spec["replicates"]))
        header = pd.read_csv(path, nrows=0).columns.tolist()
        needed = ["response", "horizon", "mean_abs_phi_difference"]
        missing = [column for column in needed if column not in header]
        if missing:
            records.append(
                _row(
                    f"{dataset}_required_semantic_columns",
                    ",".join(missing),
                    False,
                    "Missing columns needed to verify full-horizon response semantics.",
                )
            )
            continue

        optional = [
            column
            for column in [
                "auc_abs_delta_phi_0_300",
                "response_original_column",
                "source_response",
            ]
            if column in header
        ]
        frame = pd.read_csv(path, usecols=[*needed, *optional], low_memory=False)

        horizons = sorted(
            pd.to_numeric(frame["horizon"], errors="coerce").dropna().unique().tolist()
        )
        horizon_ok = horizons == [300]
        records.append(
            _row(
                f"{dataset}_horizon_is_300",
                ",".join(str(int(x)) if float(x).is_integer() else str(x) for x in horizons),
                horizon_ok,
                "The matched-horizon comparison requires every replicate to declare horizon=300.",
            )
        )

        ratio = _full_horizon_ratio(frame, 300.0)
        median_ratio = float(np.nanmedian(ratio)) if len(ratio) else float("nan")
        ratio_ok = bool(np.isfinite(median_ratio) and 0.80 <= median_ratio <= 1.20)
        records.append(
            _row(
                f"{dataset}_response_consistent_with_full_T300",
                median_ratio,
                ratio_ok,
                "Median response / (mean_abs_phi_difference * 300); ~1 indicates full-horizon integration.",
            )
        )

        if "auc_abs_delta_phi_0_300" in frame:
            auc = pd.to_numeric(frame["auc_abs_delta_phi_0_300"], errors="coerce")
            response = pd.to_numeric(frame["response"], errors="coerce")
            mask = auc.notna() & response.notna()
            coverage = float(mask.mean())
            if mask.any():
                equality_fraction = float(
                    np.isclose(
                        response[mask].to_numpy(float),
                        auc[mask].to_numpy(float),
                        rtol=1e-10,
                        atol=1e-10,
                    ).mean()
                )
                equality_ok = equality_fraction >= 0.999
            else:
                equality_fraction = float("nan")
                equality_ok = True
            records.append(
                _row(
                    f"{dataset}_response_equals_explicit_T300_where_available",
                    equality_fraction,
                    equality_ok,
                    f"Explicit T300 AUC coverage={coverage:.3f}.",
                )
            )

        if "response_original_column" in frame:
            counts = frame["response_original_column"].astype("string").value_counts(dropna=False)
            records.append(
                _row(
                    f"{dataset}_response_original_columns",
                    "; ".join(f"{idx}:{int(value)}" for idx, value in counts.items()),
                    True,
                    "Provenance only; retained to make any mixed historical source explicit.",
                )
            )
        if "source_response" in frame:
            counts = frame["source_response"].astype("string").value_counts(dropna=False)
            records.append(
                _row(
                    f"{dataset}_source_response",
                    "; ".join(f"{idx}:{int(value)}" for idx, value in counts.items()),
                    True,
                    "Provenance only.",
                )
            )

    audit = pd.DataFrame(records)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output, index=False)
    print(audit.to_string(index=False))

    failed = audit[~audit["pass"]]
    if not failed.empty:
        raise SystemExit(
            "\nResponse-semantics audit failed. Do not interpret cross-size local figures until resolved."
        )

    print("\nResponse-semantics audit passed.")


if __name__ == "__main__":
    main()
