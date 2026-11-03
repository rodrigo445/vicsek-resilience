import numpy as np

from vicsek.clusters import compute_mesoscopic_observables
from vicsek.neighbours import neighbour_pairs_kdtree
from vicsek.observables import polarization
from vicsek.perturbations import select_nearest_agents
from vicsek.resilience import integrated_absolute_response
from vicsek.simulation import vicsek_step


def test_periodic_neighbour_pair_across_boundary():
    positions = np.array([[0.05, 0.5], [9.95, 0.5], [5.0, 5.0]])
    pairs = neighbour_pairs_kdtree(positions, box_size=10.0, interaction_radius=0.2)
    assert pairs.tolist() == [[0, 1]]


def test_polarization_aligned_is_one():
    assert np.isclose(polarization(np.zeros(8)), 1.0)


def test_zero_noise_aligned_step_moves_with_new_orientation():
    positions = np.array([[0.0, 0.0], [0.5, 0.0]])
    angles = np.zeros(2)
    new_positions, new_angles = vicsek_step(
        positions,
        angles,
        box_size=10.0,
        interaction_radius=1.0,
        speed=0.1,
        time_step=1.0,
        noise_amplitude=0.0,
        random_generator=np.random.default_rng(7),
    )
    assert np.allclose(new_angles, 0.0)
    assert np.allclose(new_positions, positions + np.array([[0.1, 0.0], [0.1, 0.0]]))


def test_mesoscopic_degree_excludes_self_edges():
    positions = np.array([[0.0, 0.0], [0.5, 0.0], [5.0, 5.0]])
    angles = np.zeros(3)
    obs = compute_mesoscopic_observables(positions, angles, 10.0, interaction_radius=1.0)
    assert obs["degree"].tolist() == [1, 1, 0]
    assert np.isclose(obs["mean_degree"], 2 / 3)
    assert obs["number_of_components"] == 2


def test_nearest_target_uses_periodic_distance():
    positions = np.array([[0.1, 0.0], [9.9, 0.0], [5.0, 0.0]])
    selected = select_nearest_agents(positions, np.array([0.0, 0.0]), 10.0, m=2)
    assert set(selected.tolist()) == {0, 1}


def test_integrated_absolute_response():
    control = np.array([0.0, 0.0, 0.0])
    perturbed = np.array([0.0, 1.0, 0.0])
    assert np.isclose(integrated_absolute_response(control, perturbed), 1.0)
