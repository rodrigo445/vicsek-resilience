"""Mesoscopic observables of the instantaneous interaction graph."""

from __future__ import annotations

import numpy as np

from .neighbours import neighbour_pairs_kdtree
from .observables import local_density_from_degree, polarization


def connected_components_from_pairs(
    number_of_agents: int,
    pairs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute connected components of an undirected edge list using union-find."""
    if number_of_agents <= 0:
        raise ValueError("number_of_agents must be positive")
    pairs = np.asarray(pairs, dtype=int).reshape(-1, 2)
    parent = np.arange(number_of_agents, dtype=int)
    size = np.ones(number_of_agents, dtype=int)

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for a, b in pairs:
        root_a, root_b = find(int(a)), find(int(b))
        if root_a == root_b:
            continue
        if size[root_a] < size[root_b]:
            root_a, root_b = root_b, root_a
        parent[root_b] = root_a
        size[root_a] += size[root_b]

    roots = np.array([find(i) for i in range(number_of_agents)], dtype=int)
    _, labels = np.unique(roots, return_inverse=True)
    return labels, np.bincount(labels)


def compute_mesoscopic_observables(
    positions: np.ndarray,
    angles: np.ndarray,
    box_size: float,
    interaction_radius: float = 1.0,
    density_ddof: int = 0,
) -> dict[str, object]:
    """Compute macro/mesoscopic observables for one microscopic state.

    The graph has one node per particle, no self-edges, and an undirected edge
    whenever periodic metric distance is <= ``interaction_radius``.
    """
    positions = np.asarray(positions, dtype=float)
    angles = np.asarray(angles, dtype=float)
    n = len(positions)
    if n == 0 or len(angles) != n:
        raise ValueError("positions and angles must describe the same non-empty system")

    pairs = neighbour_pairs_kdtree(positions, box_size, interaction_radius)
    degree = np.zeros(n, dtype=int)
    if len(pairs):
        np.add.at(degree, pairs[:, 0], 1)
        np.add.at(degree, pairs[:, 1], 1)

    labels, component_sizes = connected_components_from_pairs(n, pairs)
    sorted_sizes = np.sort(component_sizes)[::-1]
    largest = int(sorted_sizes[0])
    second = int(sorted_sizes[1]) if len(sorted_sizes) > 1 else 0
    local_density = local_density_from_degree(degree, interaction_radius)
    fractions = component_sizes / n
    n_components = len(component_sizes)
    degree_sum = np.bincount(labels, weights=degree, minlength=n_components)

    return {
        "polarization": polarization(angles),
        "number_of_components": int(n_components),
        "components_per_particle": float(n_components / n),
        "largest_component_size": largest,
        "f_lcc": float(largest / n),
        "second_component_size": second,
        "f_second_component": float(second / n),
        "component_entropy": float(-np.sum(fractions * np.log(fractions))),
        "components_ge_2": int(np.sum(component_sizes >= 2)),
        "components_ge_5": int(np.sum(component_sizes >= 5)),
        "components_ge_10": int(np.sum(component_sizes >= 10)),
        "mean_degree": float(np.mean(degree)),
        "mean_local_density": float(np.mean(local_density)),
        "sigma_local_density": float(np.std(local_density, ddof=density_ddof)),
        "fraction_isolated": float(np.mean(degree == 0)),
        "pairs": pairs,
        "degree": degree,
        "local_density": local_density,
        "component_labels": labels,
        "component_sizes": component_sizes,
        "sorted_component_sizes": sorted_sizes,
        "mean_degree_by_component": degree_sum / component_sizes,
    }
