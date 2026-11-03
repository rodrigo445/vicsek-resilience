"""Macroscopic observables."""

from __future__ import annotations

import numpy as np


def compute_global_polarization(angles: np.ndarray) -> tuple[float, float]:
    """Return polarization magnitude and collective direction."""
    angles = np.asarray(angles, dtype=float)
    if angles.ndim != 1 or angles.size == 0:
        raise ValueError("angles must be a non-empty one-dimensional array")
    mean_vector = np.mean(np.exp(1j * angles))
    return float(np.abs(mean_vector)), float(np.angle(mean_vector))


def polarization(angles: np.ndarray) -> float:
    """Return global polarization ``Phi``."""
    return compute_global_polarization(angles)[0]


def local_density_from_degree(degree: np.ndarray, interaction_radius: float) -> np.ndarray:
    """Return ``rho_i = k_i / (pi R**2)`` using external graph degree."""
    if interaction_radius <= 0:
        raise ValueError("interaction_radius must be positive")
    return np.asarray(degree, dtype=float) / (np.pi * interaction_radius**2)
