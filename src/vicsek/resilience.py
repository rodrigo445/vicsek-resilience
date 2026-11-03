"""Final scalar response observables used in the publication pipeline."""

from __future__ import annotations

import numpy as np


def integrated_absolute_response(
    phi_control: np.ndarray,
    phi_perturbed: np.ndarray,
    times: np.ndarray | None = None,
) -> float:
    """Return ``integral |Phi_pert - Phi_ctrl| dt``."""
    control = np.asarray(phi_control, dtype=float)
    perturbed = np.asarray(phi_perturbed, dtype=float)
    if control.shape != perturbed.shape or control.ndim != 1:
        raise ValueError("paired polarization series must be one-dimensional and equally sized")
    if times is None:
        times = np.arange(len(control), dtype=float)
    times = np.asarray(times, dtype=float)
    if times.shape != control.shape:
        raise ValueError("times must have the same shape as the polarization series")
    return float(np.trapezoid(np.abs(perturbed - control), times))


def response_summary(
    phi_control: np.ndarray,
    phi_perturbed: np.ndarray,
    times: np.ndarray | None = None,
    *,
    early_horizon: float | None = 100.0,
) -> dict[str, float]:
    """Return the small set of response diagnostics retained in final analyses."""
    control = np.asarray(phi_control, dtype=float)
    perturbed = np.asarray(phi_perturbed, dtype=float)
    if times is None:
        times = np.arange(len(control), dtype=float)
    times = np.asarray(times, dtype=float)
    delta = perturbed - control
    absolute = np.abs(delta)
    out = {
        "auc_abs_delta_phi": float(np.trapezoid(absolute, times)),
        "max_abs_delta_phi": float(np.max(absolute)),
        "mean_abs_delta_phi": float(np.mean(absolute)),
        "late_mean_abs_delta_phi": float(np.mean(absolute[max(0, int(0.8 * len(absolute))):])),
    }
    if early_horizon is not None:
        mask = times <= early_horizon
        out["early_auc_abs_delta_phi"] = float(np.trapezoid(absolute[mask], times[mask]))
    return out
