"""Canonical dataset loading for the final analysis.

The exploratory project accumulated many superseded files.  The publishable
pipeline therefore uses an explicit TOML registry instead of heuristic file
searches.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

GLOBAL_MESO = [
    "mean_degree_0",
    "f_lcc_0",
    "sigma_local_density_0",
    "components_per_particle_0",
    "component_entropy_0",
]
LOCAL_FEATURES = [
    "selected_polarization",
    "selected_mean_degree",
    "selected_fraction_in_lcc",
    "effective_target_radius",
    "mean_distance_from_centre",
]


@dataclass(frozen=True)
class InputRegistry:
    """Parsed canonical-input registry."""

    data: dict

    @classmethod
    def from_file(cls, path: str | Path) -> "InputRegistry":
        with Path(path).open("rb") as handle:
            return cls(tomllib.load(handle))

    def section(self, family: str, name: str) -> dict[str, object]:
        try:
            return dict(self.data[family][name])
        except KeyError as exc:
            raise KeyError(f"unknown input section {family}.{name}") from exc


def resolve_input(project_root: str | Path, relative_path: str) -> Path:
    """Resolve and require one canonical input path."""
    if not relative_path:
        raise FileNotFoundError("canonical input path is intentionally empty")
    path = Path(project_root).expanduser().resolve() / Path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"canonical input not found: {path}")
    return path


def condition_id_from_rho_eta(frame: pd.DataFrame) -> pd.Series:
    """Create a stable condition label when older data do not contain one."""
    return frame.apply(lambda row: f"rho={float(row.rho):g}|eta={float(row.eta):g}", axis=1)


def _standardize_state_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "condition_id" not in frame:
        frame["condition_id"] = condition_id_from_rho_eta(frame)
    required = ["state_id", "run_id", "rho", "eta", "phi_0", *GLOBAL_MESO]
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"state dataset is missing columns: {missing}")
    return frame


def load_global_dataset(
    project_root: str | Path,
    registry: InputRegistry,
    system_size: int,
) -> pd.DataFrame:
    """Load the final state-level response dataset for ``N``."""
    name = f"N{int(system_size)}"
    spec = registry.section("global", name)

    if system_size == 100:
        data = pd.read_csv(resolve_input(project_root, spec["state_response"]))
        data = _standardize_state_columns(data)
        if "state_mean_response" not in data:
            raise ValueError("N100 state response lacks state_mean_response")
        data["N"] = 100
        return data

    states = pd.read_csv(resolve_input(project_root, spec["states"]))
    response = pd.read_csv(resolve_input(project_root, spec["state_response"]))
    states = _standardize_state_columns(states)
    join_keys = [key for key in ["state_index", "state_id", "run_id"] if key in states and key in response]
    if not join_keys:
        raise ValueError("no safe keys available to merge states and responses")
    response_columns = [*join_keys, "state_mean_response"]
    data = states.merge(
        response[response_columns],
        on=join_keys,
        how="inner",
        validate="one_to_one",
    )
    if len(data) != len(states):
        raise ValueError(f"state/response merge lost rows for N={system_size}")
    data["N"] = int(system_size)
    return data


def load_fold_assignment(
    project_root: str | Path,
    registry: InputRegistry,
    system_size: int,
) -> pd.DataFrame | None:
    """Load the historical outer-fold assignment when it was preserved."""
    spec = registry.section("global", f"N{int(system_size)}")
    relative = spec.get("fold_assignment", "")
    if not relative:
        return None
    folds = pd.read_csv(resolve_input(project_root, relative))
    if not {"run_id", "outer_fold"}.issubset(folds.columns):
        raise ValueError("fold assignment must contain run_id and outer_fold")
    return folds[["run_id", "outer_fold"]].drop_duplicates()


def load_local_dataset(
    project_root: str | Path,
    registry: InputRegistry,
    dataset_name: str,
) -> tuple[pd.DataFrame, str]:
    """Load one final replicate-level local-response dataset.

    Global state descriptors are merged from the canonical state table rather
    than copied from whichever replicate file happened to contain them.
    """
    spec = registry.section("local", dataset_name)
    states = _standardize_state_columns(pd.read_csv(resolve_input(project_root, spec["states"])))
    replicates = pd.read_csv(resolve_input(project_root, spec["replicates"]), low_memory=False)
    target = spec["target"]
    if target not in replicates:
        raise ValueError(f"{dataset_name}: target column {target!r} is missing")

    join_keys = [key for key in ["state_index", "state_id", "run_id"] if key in states and key in replicates]
    state_columns = [*join_keys, "phi_0", *GLOBAL_MESO]
    # condition/rho/eta come from the replicate table when available; otherwise from states.
    for column in ["condition_id", "rho", "eta"]:
        if column not in replicates and column in states:
            state_columns.append(column)

    data = replicates.merge(
        states[state_columns].drop_duplicates(join_keys),
        on=join_keys,
        how="left",
        validate="many_to_one",
        suffixes=("", "_state"),
    )
    if data["phi_0"].isna().any():
        raise ValueError(f"{dataset_name}: failed to attach state-level descriptors")
    if "condition_id" not in data:
        data["condition_id"] = condition_id_from_rho_eta(data)

    missing_local = [column for column in LOCAL_FEATURES if column not in data]
    if missing_local:
        raise ValueError(f"{dataset_name}: local features missing: {missing_local}")
    return data, target


def load_input_manifest(path: str | Path) -> dict[str, dict[str, object]]:
    """Load the frozen byte-level manifest keyed by relative path."""
    with Path(path).open("rb") as handle:
        raw = tomllib.load(handle)
    records = raw.get("file", [])
    if not isinstance(records, list):
        raise ValueError("input manifest must contain [[file]] records")
    manifest: dict[str, dict[str, object]] = {}
    for record in records:
        relative = str(record["path"])
        if relative in manifest:
            raise ValueError(f"duplicate input-manifest path: {relative}")
        manifest[relative] = dict(record)
    return manifest


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of a file without loading it fully into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def audit_canonical_inputs(
    project_root: str | Path,
    registry: InputRegistry,
    *,
    frozen_manifest: dict[str, dict[str, object]] | None = None,
    verify_hashes: bool = True,
) -> pd.DataFrame:
    """Audit every runtime input for existence, size, rows and optional SHA-256.

    ``final_inputs.toml`` may reuse one physical file in several analyses. The
    returned audit contains each physical path only once. Historical result
    tables are deliberately not runtime inputs and therefore do not belong in
    this registry.
    """
    records: list[dict[str, object]] = []
    entries: dict[str, list[str]] = {}
    for family, section in registry.data.items():
        for name, values in section.items():
            for field, relative in values.items():
                if field in {"target", "response_window"} or not relative:
                    continue
                entries.setdefault(str(relative), []).append(f"{family}.{name}.{field}")

    root = Path(project_root).expanduser().resolve()
    for relative, labels in entries.items():
        path = root / relative
        expected = (frozen_manifest or {}).get(relative, {})
        exists = path.is_file()
        row: dict[str, object] = {
            "input": ";".join(labels),
            "relative_path": relative,
            "exists": exists,
            "rows": None,
            "expected_rows": expected.get("rows"),
            "size_bytes": path.stat().st_size if exists else None,
            "expected_size_bytes": expected.get("size_bytes"),
            "sha256": None,
            "expected_sha256": expected.get("sha256"),
        }
        if exists and path.suffix.lower() == ".csv":
            try:
                row["rows"] = sum(1 for _ in path.open("rb")) - 1
            except OSError:
                pass
        if exists and verify_hashes and expected.get("sha256"):
            row["sha256"] = sha256_file(path)

        row["rows_match"] = (
            row["expected_rows"] is None or row["rows"] == row["expected_rows"]
        )
        row["size_match"] = (
            row["expected_size_bytes"] is None
            or row["size_bytes"] == row["expected_size_bytes"]
        )
        row["sha256_match"] = (
            row["expected_sha256"] is None
            or not verify_hashes
            or row["sha256"] == row["expected_sha256"]
        )
        row["valid"] = bool(
            exists and row["rows_match"] and row["size_match"] and row["sha256_match"]
        )
        records.append(row)
    return pd.DataFrame(records)
