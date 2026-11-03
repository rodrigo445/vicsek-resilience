#!/usr/bin/env python
"""Audit the exact canonical files required by the clean pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from vicsek.datasets import InputRegistry, audit_canonical_inputs, load_input_manifest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, help="Path to the frozen exploratory project")
    parser.add_argument(
        "--config",
        default=str(root / "configs" / "final_inputs.toml"),
        help="Canonical runtime-input registry.",
    )
    parser.add_argument(
        "--manifest",
        default=str(root / "configs" / "input_manifest.toml"),
        help="Frozen row/size/SHA-256 manifest for exact input verification.",
    )
    parser.add_argument(
        "--output",
        default=str(root / "results" / "final" / "input_audit.csv"),
        help="CSV audit written before analysis.",
    )
    parser.add_argument(
        "--skip-hash",
        action="store_true",
        help="Check existence, row counts and byte sizes but skip SHA-256 calculation.",
    )
    args = parser.parse_args()

    registry = InputRegistry.from_file(args.config)
    manifest = load_input_manifest(args.manifest)
    audit = audit_canonical_inputs(
        args.project_root,
        registry,
        frozen_manifest=manifest,
        verify_hashes=not args.skip_hash,
    )

    display_columns = [
        "relative_path",
        "exists",
        "rows",
        "expected_rows",
        "size_match",
        "sha256_match",
        "valid",
    ]
    print(audit[display_columns].to_string(index=False))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output, index=False)

    invalid = audit.loc[~audit["valid"].astype(bool)]
    if len(invalid):
        raise SystemExit(
            f"\n{len(invalid)} canonical input(s) are missing or differ from the frozen manifest. "
            "Do not run the final analysis until this is resolved."
        )
    print("\nAll canonical runtime inputs match the frozen manifest.")


if __name__ == "__main__":
    main()
