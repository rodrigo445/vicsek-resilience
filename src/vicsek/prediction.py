"""Predictive models used in the final global and local analyses."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .datasets import GLOBAL_MESO, LOCAL_FEATURES
from .validation import make_inner_splits


@dataclass(frozen=True)
class PredictionResult:
    """Out-of-fold predictions and per-fold diagnostics."""

    oof: pd.DataFrame
    fold_metrics: pd.DataFrame


def fractional_mse_removed(mse_baseline: float, mse_candidate: float) -> float:
    """Fraction of baseline MSE removed by the candidate model."""
    return float((mse_baseline - mse_candidate) / mse_baseline)


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Standard OOF regression metrics."""
    return {
        "mse": float(mean_squared_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _condition_basis(frame: pd.DataFrame) -> pd.DataFrame:
    """Full-rank condition intercept basis with a deterministic reference level."""
    dummies = pd.get_dummies(frame["condition_id"].astype(str), prefix="condition", dtype=float)
    if dummies.shape[1] <= 1:
        return pd.DataFrame(index=frame.index)
    return dummies.iloc[:, 1:]


def _condition_specific_cubic(frame: pd.DataFrame) -> pd.DataFrame:
    """Design equivalent to a separate cubic Phi curve in each condition."""
    phi = frame["phi_0"].astype(float)
    design = pd.DataFrame(
        {
            "phi_0": phi,
            "phi_0_sq": phi**2,
            "phi_0_cu": phi**3,
        },
        index=frame.index,
    )
    conditions = _condition_basis(frame)
    design = pd.concat([design, conditions], axis=1)
    for column in conditions:
        design[f"{column}:phi"] = conditions[column] * phi
        design[f"{column}:phi2"] = conditions[column] * phi**2
        design[f"{column}:phi3"] = conditions[column] * phi**3
    return design


def build_design_matrix(frame: pd.DataFrame, model_name: str) -> pd.DataFrame:
    """Build the deterministic, outcome-independent feature matrix for a named model."""
    condition = _condition_basis(frame)

    if model_name in {"M0", "Mk", "MkL", "M1"}:
        columns = ["phi_0"]
        if model_name in {"Mk", "MkL", "M1"}:
            columns.append("mean_degree_0")
        if model_name in {"MkL", "M1"}:
            columns.append("f_lcc_0")
        if model_name == "M1":
            columns.extend([c for c in GLOBAL_MESO if c not in columns])
        return pd.concat([frame[columns].astype(float), condition], axis=1)

    if model_name in {"P0", "Pk", "P1"}:
        design = _condition_specific_cubic(frame)
        if model_name in {"Pk", "P1"}:
            design["mean_degree_0"] = frame["mean_degree_0"].astype(float)
        if model_name == "P1":
            for column in GLOBAL_MESO:
                if column != "mean_degree_0":
                    design[column] = frame[column].astype(float)
        return design

    if model_name in {"MG", "M2"}:
        columns = ["phi_0", "mean_degree_0", "f_lcc_0"]
        if model_name == "M2":
            columns.extend(LOCAL_FEATURES)
        return pd.concat([frame[columns].astype(float), condition], axis=1)

    if model_name == "LOCAL_WITHIN":
        return frame[LOCAL_FEATURES].astype(float).copy()

    raise KeyError(f"unknown model {model_name!r}")


def _ridge_search(
    inner_splits: list[tuple[np.ndarray, np.ndarray]],
    feature_columns: list[str],
    alphas: np.ndarray | None = None,
) -> GridSearchCV:
    if alphas is None:
        alphas = np.logspace(-4, 3, 30)

    # Historical pipeline: continuous predictors are standardized, while
    # condition dummy intercepts are left on their 0/1 scale.
    condition_columns = [
        column for column in feature_columns
        if column.startswith("condition_") and ":" not in column
    ]
    numeric_columns = [column for column in feature_columns if column not in condition_columns]
    preprocessor = ColumnTransformer(
        [
            ("numeric", StandardScaler(), numeric_columns),
            ("condition", "passthrough", condition_columns),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", Ridge())])
    return GridSearchCV(
        pipeline,
        {"model__alpha": alphas},
        scoring="neg_mean_squared_error",
        cv=inner_splits,
        n_jobs=-1,
        refit=True,
    )


def _hgb_search(inner_splits: list[tuple[np.ndarray, np.ndarray]], random_state: int) -> GridSearchCV:
    model = HistGradientBoostingRegressor(
        loss="squared_error",
        random_state=random_state,
        early_stopping=False,
    )
    grid = {
        "learning_rate": [0.03, 0.08],
        "max_leaf_nodes": [7, 15],
        "l2_regularization": [0.0, 1.0, 10.0],
        "max_iter": [250],
    }
    return GridSearchCV(
        model,
        grid,
        scoring="neg_mean_squared_error",
        cv=inner_splits,
        n_jobs=-1,
        refit=True,
    )


def run_nested_model(
    frame: pd.DataFrame,
    target: str,
    model_name: str,
    *,
    algorithm: str = "ridge",
    inner_seed: int = 311650,
    random_state: int = 311800,
    ridge_alphas: np.ndarray | None = None,
) -> PredictionResult:
    """Run grouped nested CV using the already attached ``outer_fold`` column."""
    required = {"run_id", "condition_id", "outer_fold", target}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"analysis frame lacks required columns: {sorted(missing)}")

    design = build_design_matrix(frame, model_name)
    y = frame[target].to_numpy(dtype=float)
    prediction = np.full(len(frame), np.nan, dtype=float)
    fold_records: list[dict[str, object]] = []

    for outer_fold in sorted(frame["outer_fold"].unique()):
        train_mask = frame["outer_fold"].to_numpy() != outer_fold
        test_mask = ~train_mask
        train_idx = np.flatnonzero(train_mask)
        test_idx = np.flatnonzero(test_mask)
        training_frame = frame.iloc[train_idx].reset_index(drop=True)
        inner = make_inner_splits(
            training_frame,
            seed=int(inner_seed),
            context=int(outer_fold),
        )

        x_train = design.iloc[train_idx].reset_index(drop=True)
        x_test = design.iloc[test_idx]
        y_train = y[train_idx]

        if algorithm.lower() == "ridge":
            search = _ridge_search(inner, list(x_train.columns), alphas=ridge_alphas)
        elif algorithm.lower() == "hgb":
            search = _hgb_search(inner, random_state + int(outer_fold))
        else:
            raise ValueError("algorithm must be 'ridge' or 'hgb'")

        search.fit(x_train, y_train)
        fold_prediction = search.predict(x_test)
        prediction[test_idx] = fold_prediction
        fold_records.append(
            {
                "model": model_name,
                "algorithm": algorithm,
                "outer_fold": int(outer_fold),
                **regression_metrics(y[test_idx], fold_prediction),
                "best_params": repr(search.best_params_),
                "number_train_runs": int(frame.iloc[train_idx]["run_id"].nunique()),
                "number_test_runs": int(frame.iloc[test_idx]["run_id"].nunique()),
            }
        )

    if np.isnan(prediction).any():
        raise RuntimeError("some observations did not receive an OOF prediction")

    metadata = [
        column
        for column in ["state_index", "state_id", "run_id", "condition_id", "rho", "eta", "replicate"]
        if column in frame
    ]
    oof = frame[metadata].copy()
    oof["observed"] = y
    oof["predicted"] = prediction
    oof["model"] = model_name
    oof["algorithm"] = algorithm
    oof["outer_fold"] = frame["outer_fold"].to_numpy()
    return PredictionResult(oof=oof, fold_metrics=pd.DataFrame(fold_records))


def combine_oof(results: dict[str, PredictionResult]) -> pd.DataFrame:
    """Merge predictions from models evaluated on exactly the same rows."""
    first_name = next(iter(results))
    first = results[first_name].oof.copy().reset_index(drop=True)
    keys = [c for c in first.columns if c not in {"predicted", "model", "algorithm"}]
    combined = first[keys].copy()
    combined[f"predicted_{first_name}"] = first["predicted"].to_numpy()
    for name, result in list(results.items())[1:]:
        current = result.oof.reset_index(drop=True)
        if len(current) != len(combined) or not np.allclose(
            current["observed"].to_numpy(), combined["observed"].to_numpy()
        ):
            raise ValueError("OOF results are not row-aligned")
        combined[f"predicted_{name}"] = current["predicted"].to_numpy()
    return combined


def model_metrics_from_combined(oof: pd.DataFrame, model_names: list[str]) -> pd.DataFrame:
    """Compute whole-dataset OOF metrics for several prediction columns."""
    y = oof["observed"].to_numpy(dtype=float)
    return pd.DataFrame(
        [
            {"model": name, **regression_metrics(y, oof[f"predicted_{name}"].to_numpy(dtype=float))}
            for name in model_names
        ]
    )


def bootstrap_mse_gain(
    oof: pd.DataFrame,
    baseline_model: str,
    candidate_model: str,
    *,
    n_bootstrap: int = 2000,
    seed: int = 12345,
) -> dict[str, float]:
    """Condition-stratified run bootstrap of fractional MSE removed."""
    base_error = (oof["observed"] - oof[f"predicted_{baseline_model}"]) ** 2
    candidate_error = (oof["observed"] - oof[f"predicted_{candidate_model}"]) ** 2
    losses = oof[["run_id", "condition_id"]].copy()
    losses["base_sse"] = base_error
    losses["candidate_sse"] = candidate_error
    run_losses = (
        losses.groupby(["condition_id", "run_id"], as_index=False)
        .agg(base_sse=("base_sse", "sum"), candidate_sse=("candidate_sse", "sum"), n=("base_sse", "size"))
    )
    base_mse = float(run_losses["base_sse"].sum() / run_losses["n"].sum())
    candidate_mse = float(run_losses["candidate_sse"].sum() / run_losses["n"].sum())
    observed_gain = fractional_mse_removed(base_mse, candidate_mse)

    rng = np.random.default_rng(seed)
    samples = np.empty(n_bootstrap, dtype=float)
    groups = [group.reset_index(drop=True) for _, group in run_losses.groupby("condition_id", sort=True)]
    for b in range(n_bootstrap):
        base_sse = candidate_sse = 0.0
        total_n = 0
        for group in groups:
            take = rng.integers(0, len(group), size=len(group))
            sampled = group.iloc[take]
            base_sse += float(sampled["base_sse"].sum())
            candidate_sse += float(sampled["candidate_sse"].sum())
            total_n += int(sampled["n"].sum())
        samples[b] = fractional_mse_removed(base_sse / total_n, candidate_sse / total_n)

    lower, upper = np.quantile(samples, [0.025, 0.975])
    return {
        "baseline_model": baseline_model,
        "candidate_model": candidate_model,
        "mse_baseline": base_mse,
        "mse_candidate": candidate_mse,
        "fraction_mse_removed": observed_gain,
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
        "bootstrap_fraction_positive": float(np.mean(samples > 0)),
    }


def center_within_state(frame: pd.DataFrame, target: str) -> pd.DataFrame:
    """Remove every between-state difference from response and local predictors."""
    if "state_id" not in frame:
        raise ValueError("within-state analysis requires state_id")
    centered = frame.copy()
    centered[target] = centered[target] - centered.groupby("state_id")[target].transform("mean")
    for column in LOCAL_FEATURES:
        centered[column] = centered[column] - centered.groupby("state_id")[column].transform("mean")
    return centered


def bootstrap_within_state_gain(
    oof: pd.DataFrame,
    *,
    n_bootstrap: int = 2000,
    seed: int = 12345,
) -> dict[str, float]:
    """Run/condition-stratified bootstrap for a within-state model.

    After centering within each state, the no-local-information baseline is
    identically zero.  This function therefore compares ``observed**2`` with
    the squared OOF residual of the fitted local model while resampling whole
    runs within condition.
    """
    required = {"run_id", "condition_id", "observed", "predicted"}
    missing = required.difference(oof.columns)
    if missing:
        raise ValueError(f"within-state OOF lacks columns: {sorted(missing)}")

    losses = oof[["run_id", "condition_id"]].copy()
    observed = oof["observed"].to_numpy(dtype=float)
    predicted = oof["predicted"].to_numpy(dtype=float)
    losses["base_sse"] = observed**2
    losses["candidate_sse"] = (observed - predicted) ** 2
    run_losses = (
        losses.groupby(["condition_id", "run_id"], as_index=False)
        .agg(
            base_sse=("base_sse", "sum"),
            candidate_sse=("candidate_sse", "sum"),
            n=("base_sse", "size"),
        )
    )
    base_mse = float(run_losses["base_sse"].sum() / run_losses["n"].sum())
    candidate_mse = float(run_losses["candidate_sse"].sum() / run_losses["n"].sum())
    observed_gain = fractional_mse_removed(base_mse, candidate_mse)

    rng = np.random.default_rng(seed)
    samples = np.empty(n_bootstrap, dtype=float)
    groups = [group.reset_index(drop=True) for _, group in run_losses.groupby("condition_id", sort=True)]
    for b in range(n_bootstrap):
        base_sse = 0.0
        candidate_sse = 0.0
        total_n = 0
        for group in groups:
            take = rng.integers(0, len(group), size=len(group))
            sampled = group.iloc[take]
            base_sse += float(sampled["base_sse"].sum())
            candidate_sse += float(sampled["candidate_sse"].sum())
            total_n += int(sampled["n"].sum())
        samples[b] = fractional_mse_removed(base_sse / total_n, candidate_sse / total_n)

    lower, upper = np.quantile(samples, [0.025, 0.975])
    return {
        "mse_baseline": base_mse,
        "mse_candidate": candidate_mse,
        "fraction_mse_removed": observed_gain,
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
        "bootstrap_fraction_positive": float(np.mean(samples > 0)),
    }


def run_within_state(
    frame: pd.DataFrame,
    target: str,
    *,
    algorithm: str = "ridge",
    inner_seed: int = 411650,
    ridge_alphas: np.ndarray | None = None,
) -> tuple[PredictionResult, dict[str, float]]:
    """Predict within-state response deviations from within-state local features."""
    centered = center_within_state(frame, target)
    result = run_nested_model(
        centered,
        target,
        "LOCAL_WITHIN",
        algorithm=algorithm,
        inner_seed=inner_seed,
        ridge_alphas=ridge_alphas,
    )
    y = result.oof["observed"].to_numpy(dtype=float)
    prediction = result.oof["predicted"].to_numpy(dtype=float)
    mse_baseline = float(np.mean(y**2))  # state-mean predictor -> zero after centering
    mse_candidate = float(mean_squared_error(y, prediction))
    summary = {
        "algorithm": algorithm,
        "mse_baseline": mse_baseline,
        "mse_candidate": mse_candidate,
        "fraction_mse_removed": fractional_mse_removed(mse_baseline, mse_candidate),
    }
    return result, summary
