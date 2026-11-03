"""Spatially local angular perturbations with common-random-number controls."""

from __future__ import annotations

import math

import numpy as np

from .clusters import compute_mesoscopic_observables
from .model import wrap_angles
from .observables import polarization
from .simulation import vicsek_step


def minimum_image_displacements(
    positions: np.ndarray,
    centre: np.ndarray,
    box_size: float,
) -> np.ndarray:
    """Return minimum-image vectors from ``centre`` to each particle."""
    positions = np.asarray(positions, dtype=float)
    centre = np.asarray(centre, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 2:
        raise ValueError("positions must have shape (N, 2)")
    if centre.shape != (2,):
        raise ValueError("centre must have shape (2,)")
    displacement = positions - centre
    displacement -= box_size * np.round(displacement / box_size)
    return displacement


def periodic_distances_from_point(
    positions: np.ndarray,
    centre: np.ndarray,
    box_size: float,
) -> np.ndarray:
    """Periodic Euclidean distance from one point to every particle."""
    return np.linalg.norm(minimum_image_displacements(positions, centre, box_size), axis=1)


def select_nearest_agents(
    positions: np.ndarray,
    centre: np.ndarray,
    box_size: float,
    *,
    fraction: float | None = None,
    m: int | None = None,
) -> np.ndarray:
    """Select the nearest particles to a random centre.

    Exactly one of ``fraction`` or ``m`` must be supplied. Fractional targets
    use ``ceil(fraction * N)``. Distance ties are broken by particle index,
    which makes selection deterministic.
    """
    positions = np.asarray(positions, dtype=float)
    n = len(positions)
    if n == 0:
        raise ValueError("at least one particle is required")
    if (fraction is None) == (m is None):
        raise ValueError("specify exactly one of fraction or m")

    if fraction is not None:
        fraction = float(fraction)
        if not np.isfinite(fraction) or not 0 < fraction <= 1:
            raise ValueError("fraction must lie in (0, 1]")
        number_selected = math.ceil(fraction * n)
    else:
        if isinstance(m, bool) or not isinstance(m, (int, np.integer)):
            raise ValueError("m must be an integer")
        number_selected = int(m)
        if not 1 <= number_selected <= n:
            raise ValueError("m must lie between 1 and N")

    distances = periodic_distances_from_point(positions, centre, box_size)
    order = np.lexsort((np.arange(n), distances))
    return order[:number_selected]


def rotate_selected_agents(
    angles: np.ndarray,
    selected_indices: np.ndarray,
    delta_theta: float,
) -> np.ndarray:
    """Rotate selected orientations and wrap them to ``[-pi, pi)``."""
    angles = np.asarray(angles, dtype=float)
    selected = np.asarray(selected_indices, dtype=int)
    if angles.ndim != 1 or selected.ndim != 1:
        raise ValueError("angles and selected_indices must be one-dimensional")
    if len(np.unique(selected)) != len(selected):
        raise ValueError("selected_indices contains duplicates")
    if np.any((selected < 0) | (selected >= len(angles))):
        raise ValueError("selected_indices contains an out-of-range value")

    perturbed = angles.copy()
    perturbed[selected] = wrap_angles(perturbed[selected] + float(delta_theta))
    return perturbed


def describe_local_target(
    positions: np.ndarray,
    angles: np.ndarray,
    centre: np.ndarray,
    selected_indices: np.ndarray,
    box_size: float,
    interaction_radius: float = 1.0,
    density_ddof: int = 0,
    *,
    precomputed_mesoscopic: dict[str, object] | None = None,
) -> dict[str, float | int]:
    """Describe the unperturbed region selected for a local intervention.

    ``precomputed_mesoscopic`` can be supplied when many perturbations are
    applied to the same microstate so that the interaction graph is computed
    only once.
    """
    positions = np.asarray(positions, dtype=float)
    angles = np.asarray(angles, dtype=float)
    selected = np.asarray(selected_indices, dtype=int)
    if len(positions) != len(angles) or len(selected) == 0:
        raise ValueError("invalid state or empty target")

    observables = precomputed_mesoscopic or compute_mesoscopic_observables(
        positions,
        angles,
        box_size,
        interaction_radius=interaction_radius,
        density_ddof=density_ddof,
    )
    distances = periodic_distances_from_point(positions, centre, box_size)
    labels = np.asarray(observables["component_labels"], dtype=int)
    sizes = np.asarray(observables["component_sizes"], dtype=int)
    largest_label = int(np.argmax(sizes))
    degree = np.asarray(observables["degree"], dtype=float)

    return {
        "number_selected": int(len(selected)),
        "fraction_selected": float(len(selected) / len(positions)),
        "effective_target_radius": float(np.max(distances[selected])),
        "mean_distance_from_centre": float(np.mean(distances[selected])),
        "selected_polarization": float(polarization(angles[selected])),
        "selected_mean_degree": float(np.mean(degree[selected])),
        "selected_fraction_in_lcc": float(np.mean(labels[selected] == largest_label)),
    }


def construct_local_angular_perturbation(
    positions: np.ndarray,
    angles: np.ndarray,
    centre: np.ndarray,
    box_size: float,
    delta_theta: float,
    *,
    fraction: float | None = None,
    m: int | None = None,
    interaction_radius: float = 1.0,
    density_ddof: int = 0,
    precomputed_mesoscopic: dict[str, object] | None = None,
) -> dict[str, object]:
    """Select, describe and rotate one local target."""
    selected = select_nearest_agents(
        positions,
        centre,
        box_size,
        fraction=fraction,
        m=m,
    )
    return {
        "centre": np.asarray(centre, dtype=float).copy(),
        "selected_indices": selected,
        "delta_theta": float(delta_theta),
        "angles": rotate_selected_agents(angles, selected, delta_theta),
        "target": describe_local_target(
            positions,
            angles,
            centre,
            selected,
            box_size,
            interaction_radius,
            density_ddof,
            precomputed_mesoscopic=precomputed_mesoscopic,
        ),
    }


def evolve_paired_polarization(
    positions: np.ndarray,
    control_angles: np.ndarray,
    perturbed_angles: np.ndarray,
    *,
    box_size: float,
    interaction_radius: float,
    speed: float,
    time_step: float,
    noise_amplitude: float,
    number_of_steps: int,
    future_seed: int,
) -> dict[str, np.ndarray]:
    """Evolve control and perturbed branches with identical future noise."""
    control_positions = np.asarray(positions, dtype=float).copy()
    perturbed_positions = np.asarray(positions, dtype=float).copy()
    control_angles = np.asarray(control_angles, dtype=float).copy()
    perturbed_angles = np.asarray(perturbed_angles, dtype=float).copy()
    rng_control = np.random.default_rng(int(future_seed))
    rng_perturbed = np.random.default_rng(int(future_seed))

    phi_control = np.empty(number_of_steps + 1, dtype=float)
    phi_perturbed = np.empty(number_of_steps + 1, dtype=float)
    phi_control[0] = polarization(control_angles)
    phi_perturbed[0] = polarization(perturbed_angles)

    for step in range(1, number_of_steps + 1):
        control_positions, control_angles = vicsek_step(
            control_positions,
            control_angles,
            box_size,
            interaction_radius,
            speed,
            time_step,
            noise_amplitude,
            rng_control,
        )
        perturbed_positions, perturbed_angles = vicsek_step(
            perturbed_positions,
            perturbed_angles,
            box_size,
            interaction_radius,
            speed,
            time_step,
            noise_amplitude,
            rng_perturbed,
        )
        phi_control[step] = polarization(control_angles)
        phi_perturbed[step] = polarization(perturbed_angles)

    times = np.arange(number_of_steps + 1, dtype=float) * time_step
    return {
        "time": times,
        "phi_control": phi_control,
        "phi_perturbed": phi_perturbed,
        "delta_phi": phi_perturbed - phi_control,
    }
