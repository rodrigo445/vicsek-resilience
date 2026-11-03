#!/usr/bin/env python
"""Capture the small set of package versions relevant to final reproducibility."""

from __future__ import annotations

import argparse
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PACKAGES = [
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "scikit-learn",
    "pytest",
    "ruff",
    "setuptools",
]


def installed_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "not installed"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(root / "results" / "final" / "environment_snapshot.txt"),
    )
    args = parser.parse_args()

    lines = [
        f"Python: {platform.python_version()}",
        f"Implementation: {platform.python_implementation()}",
        f"Platform: {platform.platform()}",
        "",
        "Relevant packages:",
    ]
    lines.extend(f"{package}=={installed_version(package)}" for package in PACKAGES)
    text = "\n".join(lines) + "\n"

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    print(f"Saved to {output}")


if __name__ == "__main__":
    main()
