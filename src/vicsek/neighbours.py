"""Periodic metric-neighbour search for the Vicsek model."""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def neighbour_pairs_kdtree(
    positions: np.ndarray,
    box_size: float,
    interaction_radius: float,
) -> np.ndarray:
    """Return all undirected pairs ``(i, j)``, ``i < j``, with periodic distance <= R."""
    positions = np.asarray(positions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 2:
        raise ValueError("positions must have shape (N, 2)")
    if box_size <= 0:
        raise ValueError("box_size must be positive")
    if interaction_radius < 0:
        raise ValueError("interaction_radius cannot be negative")

    tree = cKDTree(positions, boxsize=float(box_size))
    pairs = tree.query_pairs(
        r=float(interaction_radius) * (1.0 + 1e-12),
        output_type="ndarray",
    )
    return np.asarray(pairs, dtype=int).reshape(-1, 2)
