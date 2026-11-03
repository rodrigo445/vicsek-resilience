import numpy as np
import pandas as pd

from vicsek.prediction import build_design_matrix, center_within_state, fractional_mse_removed
from vicsek.validation import attach_outer_folds, make_balanced_run_assignment, make_inner_splits


def toy_frame():
    rows = []
    for condition in ["a", "b"]:
        for run in range(6):
            for state in range(2):
                rows.append(
                    {
                        "run_id": f"{condition}_{run}",
                        "state_id": f"{condition}_{run}_{state}",
                        "condition_id": condition,
                        "rho": 1.0,
                        "eta": 2.0,
                        "phi_0": 0.1 + 0.01 * state,
                        "mean_degree_0": 2.0,
                        "f_lcc_0": 0.5,
                        "sigma_local_density_0": 0.2,
                        "components_per_particle_0": 0.1,
                        "component_entropy_0": 0.4,
                    }
                )
    return pd.DataFrame(rows)


def test_balanced_outer_folds_have_no_run_leakage():
    frame = toy_frame()
    assignment = make_balanced_run_assignment(frame, 3, seed=1)
    attached = attach_outer_folds(frame, assignment)
    counts = (
        attached[["run_id", "condition_id", "outer_fold"]]
        .drop_duplicates()
        .groupby(["condition_id", "outer_fold"])
        .size()
    )
    assert (counts == 2).all()


def test_inner_splits_are_run_disjoint():
    frame = toy_frame()
    splits = make_inner_splits(frame, n_splits=3, seed=2)
    for train_idx, validation_idx in splits:
        train_runs = set(frame.iloc[train_idx].run_id)
        validation_runs = set(frame.iloc[validation_idx].run_id)
        assert train_runs.isdisjoint(validation_runs)


def test_p0_contains_condition_specific_cubic_terms():
    design = build_design_matrix(toy_frame(), "P0")
    assert "phi_0" in design
    assert "phi_0_sq" in design
    assert "phi_0_cu" in design
    assert any(column.endswith(":phi3") for column in design.columns)


def test_within_state_centering_removes_state_means():
    frame = pd.DataFrame(
        {
            "state_id": ["a", "a", "b", "b"],
            "y": [1.0, 3.0, 10.0, 14.0],
            "selected_polarization": [1.0, 2.0, 4.0, 8.0],
            "selected_mean_degree": [1.0, 3.0, 5.0, 7.0],
            "selected_fraction_in_lcc": [0.2, 0.4, 0.6, 0.8],
            "effective_target_radius": [1.0, 2.0, 3.0, 4.0],
            "mean_distance_from_centre": [2.0, 4.0, 6.0, 8.0],
        }
    )
    centered = center_within_state(frame, "y")
    assert np.allclose(centered.groupby("state_id").y.mean(), 0.0)


def test_fractional_mse_removed():
    assert np.isclose(fractional_mse_removed(10.0, 8.0), 0.2)


def test_nested_ridge_produces_prediction_for_every_row():
    from vicsek.prediction import run_nested_model

    frame = toy_frame()
    assignment = make_balanced_run_assignment(frame, 3, seed=3)
    frame = attach_outer_folds(frame, assignment)
    frame["target"] = 2.0 * frame["phi_0"] + 0.1 * frame["mean_degree_0"]
    result = run_nested_model(frame, "target", "M0", algorithm="ridge", inner_seed=4)
    assert len(result.oof) == len(frame)
    assert np.isfinite(result.oof["predicted"]).all()
    assert result.oof["outer_fold"].nunique() == 3
