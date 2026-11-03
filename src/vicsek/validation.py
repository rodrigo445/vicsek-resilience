"""Grouped, condition-balanced validation utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def validate_run_independence(frame: pd.DataFrame, fold_column: str = "outer_fold") -> None:
    """Require every run to belong to exactly one outer fold."""
    counts = frame[["run_id", fold_column]].drop_duplicates().groupby("run_id")[fold_column].nunique()
    if not (counts == 1).all():
        raise ValueError("a run appears in more than one fold")


def make_balanced_run_assignment(
    frame: pd.DataFrame,
    n_splits: int,
    *,
    seed: int,
    condition_column: str = "condition_id",
) -> pd.DataFrame:
    """Assign complete runs to approximately balanced folds within each condition."""
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    runs = frame[["run_id", condition_column]].drop_duplicates()
    records: list[dict[str, object]] = []

    for condition_index, (condition, group) in enumerate(runs.groupby(condition_column, sort=True)):
        run_ids = group["run_id"].astype(str).to_numpy()
        if len(run_ids) < n_splits:
            raise ValueError(f"{condition}: fewer runs than folds")
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), condition_index]))
        shuffled = run_ids[rng.permutation(len(run_ids))]
        for position, run_id in enumerate(shuffled):
            records.append(
                {
                    "run_id": run_id,
                    "outer_fold": int(position % n_splits),
                    condition_column: condition,
                }
            )
    return pd.DataFrame(records)


def attach_outer_folds(
    frame: pd.DataFrame,
    assignment: pd.DataFrame,
) -> pd.DataFrame:
    """Attach a one-row-per-run fold assignment and validate no leakage."""
    assignment = assignment[["run_id", "outer_fold"]].drop_duplicates().copy()
    left = frame.copy()
    # CSV type inference can differ between state tables; joining on strings is safer.
    left["_run_key"] = left["run_id"].astype(str)
    assignment["_run_key"] = assignment["run_id"].astype(str)
    left = left.merge(
        assignment[["_run_key", "outer_fold"]],
        on="_run_key",
        how="left",
        validate="many_to_one",
    ).drop(columns="_run_key")
    if left["outer_fold"].isna().any():
        missing = left.loc[left["outer_fold"].isna(), "run_id"].drop_duplicates().tolist()
        raise ValueError(f"fold assignment is missing runs: {missing[:5]}")
    left["outer_fold"] = left["outer_fold"].astype(int)
    validate_run_independence(left)
    return left


def make_inner_splits(
    training_frame: pd.DataFrame,
    n_splits: int = 5,
    *,
    seed: int,
    context: int = 0,
    condition_column: str = "condition_id",
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create condition-balanced inner folds with run-level independence.

    When the number of runs per condition is divisible by ``n_splits`` this
    reproduces the historical convention: independently shuffle each
    ``(rho, eta)`` condition and assign consecutive equal-sized blocks to folds.
    """
    columns = ["run_id", condition_column]
    for column in ["rho", "eta"]:
        if column in training_frame:
            columns.append(column)
    runs = training_frame[columns].drop_duplicates().copy()
    minimum_runs = int(runs.groupby(condition_column).size().min())
    actual_splits = min(int(n_splits), minimum_runs)
    if actual_splits < 2:
        raise ValueError("not enough runs per condition for inner CV")

    group_columns = [condition_column]
    if {"rho", "eta"}.issubset(runs.columns):
        group_columns = ["rho", "eta", condition_column]

    records: list[dict[str, object]] = []
    for group_number, (group_key, group) in enumerate(runs.groupby(group_columns, sort=True)):
        group = group.reset_index(drop=True)
        if isinstance(group_key, tuple) and len(group_key) >= 2:
            rho_value, eta_value = float(group_key[0]), float(group_key[1])
            sequence = np.random.SeedSequence(
                [int(seed), int(context), int(round(rho_value * 1000)), int(round(eta_value * 1000))]
            )
        else:
            sequence = np.random.SeedSequence([int(seed), int(context), group_number])
        rng = np.random.default_rng(sequence)
        shuffled = group.iloc[rng.permutation(len(group))]["run_id"].tolist()

        if len(group) % actual_splits == 0:
            per_fold = len(group) // actual_splits
            folds = [min(position // per_fold, actual_splits - 1) for position in range(len(group))]
        else:
            folds = [position % actual_splits for position in range(len(group))]

        for run_id, fold in zip(shuffled, folds, strict=True):
            records.append({"run_id": run_id, "inner_fold": int(fold)})

    assignment = pd.DataFrame(records)
    mapping = dict(zip(assignment["run_id"].astype(str), assignment["inner_fold"], strict=True))
    labels = training_frame["run_id"].astype(str).map(mapping).to_numpy(dtype=int)

    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for fold in range(actual_splits):
        train_idx = np.flatnonzero(labels != fold)
        validation_idx = np.flatnonzero(labels == fold)
        train_runs = set(training_frame.iloc[train_idx]["run_id"].astype(str))
        validation_runs = set(training_frame.iloc[validation_idx]["run_id"].astype(str))
        if not train_runs.isdisjoint(validation_runs):
            raise RuntimeError("run leakage in inner CV")
        splits.append((train_idx, validation_idx))
    return splits


def fold_balance_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Count test runs per condition and outer fold."""
    return (
        frame[["run_id", "condition_id", "outer_fold"]]
        .drop_duplicates()
        .groupby(["outer_fold", "condition_id"], as_index=False)
        .size()
        .rename(columns={"size": "test_runs"})
    )
