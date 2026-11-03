"""Small mathematical utilities shared by the Vicsek implementation."""

from __future__ import annotations

import numpy as np


def wrap_angles(angles: np.ndarray) -> np.ndarray:
    """Wrap angles to ``[-pi, pi)``."""
    values = np.asarray(angles, dtype=float)
    return (values + np.pi) % (2.0 * np.pi) - np.pi


def apply_periodic_boundaries(positions: np.ndarray, box_size: float) -> np.ndarray:
    """Wrap positions to the periodic square ``[0, L) x [0, L)``."""
    if box_size <= 0:
        raise ValueError("box_size must be positive")
    return np.asarray(positions, dtype=float) % float(box_size)


def box_size_from_density(number_of_agents: int, density: float) -> float:
    """Return ``L`` from ``rho = N / L**2``."""
    if number_of_agents <= 0:
        raise ValueError("number_of_agents must be positive")
    if density <= 0:
        raise ValueError("density must be positive")
    return float(np.sqrt(number_of_agents / density))
