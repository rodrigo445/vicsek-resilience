"""Validated metric Vicsek dynamics used in the project."""

from __future__ import annotations

import numpy as np

from .model import apply_periodic_boundaries, box_size_from_density, wrap_angles
from .neighbours import neighbour_pairs_kdtree
from .observables import polarization


def initialize_vicsek_state(
    number_of_agents: int,
    box_size: float,
    random_generator: np.random.Generator,
    initial_condition: str = "random",
    common_angle: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate random positions and random or aligned orientations."""
    if number_of_agents <= 0:
        raise ValueError("number_of_agents must be positive")
    if box_size <= 0:
        raise ValueError("box_size must be positive")

    positions = random_generator.uniform(0.0, box_size, size=(number_of_agents, 2))
    if initial_condition == "random":
        angles = random_generator.uniform(-np.pi, np.pi, size=number_of_agents)
    elif initial_condition == "aligned":
        angles = wrap_angles(np.full(number_of_agents, common_angle, dtype=float))
    else:
        raise ValueError("initial_condition must be 'random' or 'aligned'")
    return positions, angles


def vicsek_step(
    positions: np.ndarray,
    angles: np.ndarray,
    box_size: float,
    interaction_radius: float,
    speed: float,
    time_step: float,
    noise_amplitude: float,
    random_generator: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Perform one simultaneous Vicsek update.

    Scientific conventions preserved from the exploratory implementation:
    neighbours are computed at time ``t``; self-alignment is included; noise is
    ``U(-eta/2, eta/2)``; all particles move using their *new* orientation.
    """
    positions = np.asarray(positions, dtype=float)
    angles = np.asarray(angles, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 2 or len(positions) != len(angles):
        raise ValueError("positions must have shape (N,2) with one angle per particle")
    if speed < 0 or time_step <= 0 or noise_amplitude < 0:
        raise ValueError("invalid speed, time_step, or noise_amplitude")

    pairs = neighbour_pairs_kdtree(positions, box_size, interaction_radius)
    vectors = np.exp(1j * angles)
    local_sum = vectors.copy()  # self-interaction
    if len(pairs):
        i, j = pairs[:, 0], pairs[:, 1]
        np.add.at(local_sum, i, vectors[j])
        np.add.at(local_sum, j, vectors[i])

    mean_angle = np.angle(local_sum)
    ambiguous = np.abs(local_sum) < 1e-12
    mean_angle[ambiguous] = angles[ambiguous]
    noise = random_generator.uniform(-noise_amplitude / 2.0, noise_amplitude / 2.0, len(angles))
    new_angles = wrap_angles(mean_angle + noise)
    directions = np.column_stack((np.cos(new_angles), np.sin(new_angles)))
    new_positions = apply_periodic_boundaries(
        positions + speed * time_step * directions,
        box_size,
    )
    return new_positions, new_angles


def run_vicsek_simulation(
    number_of_agents: int,
    box_size: float,
    interaction_radius: float,
    speed: float,
    time_step: float,
    noise_amplitude: float,
    number_of_steps: int,
    seed: int,
    initial_condition: str = "random",
    common_angle: float = 0.0,
    store_every: int | None = None,
) -> dict[str, object]:
    """Run a complete simulation and optionally sample microscopic states."""
    if number_of_steps <= 0:
        raise ValueError("number_of_steps must be positive")
    if store_every is not None and store_every <= 0:
        raise ValueError("store_every must be positive or None")

    rng = np.random.default_rng(int(seed))
    positions, angles = initialize_vicsek_state(
        number_of_agents, box_size, rng, initial_condition, common_angle
    )
    phi = np.empty(number_of_steps + 1, dtype=float)
    phi[0] = polarization(angles)

    stored_positions: list[np.ndarray] = []
    stored_angles: list[np.ndarray] = []
    stored_steps: list[int] = []
    if store_every is not None:
        stored_positions.append(positions.copy())
        stored_angles.append(angles.copy())
        stored_steps.append(0)

    for step in range(1, number_of_steps + 1):
        positions, angles = vicsek_step(
            positions,
            angles,
            box_size,
            interaction_radius,
            speed,
            time_step,
            noise_amplitude,
            rng,
        )
        phi[step] = polarization(angles)
        if store_every is not None and step % store_every == 0:
            stored_positions.append(positions.copy())
            stored_angles.append(angles.copy())
            stored_steps.append(step)

    result: dict[str, object] = {
        "parameters": {
            "number_of_agents": int(number_of_agents),
            "box_size": float(box_size),
            "interaction_radius": float(interaction_radius),
            "speed": float(speed),
            "time_step": float(time_step),
            "noise_amplitude": float(noise_amplitude),
            "number_of_steps": int(number_of_steps),
            "seed": int(seed),
            "initial_condition": initial_condition,
        },
        "polarization": phi,
        "final_positions": positions,
        "final_angles": angles,
    }
    if store_every is not None:
        result.update(
            sample_steps=np.asarray(stored_steps, dtype=int),
            positions=np.asarray(stored_positions),
            angles=np.asarray(stored_angles),
        )
    return result


def run_density_simulation(
    number_of_agents: int,
    density: float,
    noise_amplitude: float,
    number_of_steps: int,
    seed: int,
    interaction_radius: float = 1.0,
    speed: float = 0.1,
    time_step: float = 1.0,
    initial_condition: str = "random",
    common_angle: float = 0.0,
    store_every: int | None = None,
) -> dict[str, object]:
    """Convenience wrapper parameterized by global density."""
    box_size = box_size_from_density(number_of_agents, density)
    result = run_vicsek_simulation(
        number_of_agents,
        box_size,
        interaction_radius,
        speed,
        time_step,
        noise_amplitude,
        number_of_steps,
        seed,
        initial_condition,
        common_angle,
        store_every,
    )
    result["parameters"]["density"] = float(density)  # type: ignore[index]
    return result
