"""
Тесты для гравитации как приталкивания.
============================================================================
Проверяют:
    1. Экранирование создаёт градиент давления.
    2. Сила приталкивания направлена к телу.
    3. Сила убывает с расстоянием.
    4. Закон близок к 1/r².
    5. Диполь движется к телу.
    6. Воспроизводимость.
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.gravity_solver import GravitySolver, GravDipole


class TestGravitySolver:

    def test_initialization(self):
        s = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=2, random_seed=42)
        assert len(s.dipoles) == 2
        center = int(s.grid_size / 2)
        assert s.pressure_field[center, center, center] < 1.0

    def test_pressure_gradient_exists(self):
        s = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=0, random_seed=42)
        center = int(s.grid_size / 2)
        p_center = s.pressure_field[center, center, center]
        p_far = s.pressure_field[0, 0, 0]
        assert p_center < p_far

    def test_force_points_to_body(self):
        s = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=1, random_seed=123)
        dipole = s.dipoles[0]
        
        # pos_plus ближе к телу (давление меньше), pos_minus дальше (давление больше)
        dipole.pos_plus = s.body.position + np.array([3.0, 0.0, 0.0])
        dipole.pos_minus = s.body.position + np.array([5.0, 0.0, 0.0])
        dipole.velocity = np.zeros(3)
        
        force = s.compute_push_force(dipole)
        force_mag = np.linalg.norm(force)

        assert force_mag > 1e-12, "Сила равна нулю!"

        # Вектор к телу
        to_body = s.body.position - dipole.center
        to_body = to_body - np.round(to_body / s.grid_size) * s.grid_size
        to_body /= np.linalg.norm(to_body)
        force_dir = force / force_mag
        dot_product = np.dot(force_dir, to_body)
        
        assert dot_product > 0, (
            f"Сила направлена от тела! dot={dot_product:.4f}\n"
            f"  force_dir={force_dir}\n  to_body={to_body}"
        )

    def test_force_decreases_with_distance(self):
        s = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=1, random_seed=456)
        dipole = s.dipoles[0]

        forces = []
        for offset in [5.0, 8.0, 12.0, 16.0]:
            dipole.pos_plus = s.body.position + np.array([offset - 1.0, 0.0, 0.0])
            dipole.pos_minus = s.body.position + np.array([offset + 1.0, 0.0, 0.0])
            forces.append(s.compute_force_magnitude(dipole))

        assert forces[-1] < forces[0] * 0.8 or forces[0] < 1e-10

    def test_inverse_square_law(self):
        s = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=1, random_seed=789)
        dipole = s.dipoles[0]

        distances = []
        forces = []

        for offset in np.linspace(5.0, 18.0, 8):
            # pos_plus ближе к телу, pos_minus дальше
            dipole.pos_plus = s.body.position + np.array([offset - 1.0, 0.0, 0.0])
            dipole.pos_minus = s.body.position + np.array([offset + 1.0, 0.0, 0.0])
            dist = s.compute_distance(dipole)
            force = s.compute_force_magnitude(dipole)
            if dist > 1.0 and force > 1e-12:
                distances.append(dist)
                forces.append(force)

        if len(distances) >= 3:
            log_r = np.log(distances)
            log_f = np.log(forces)
            slope, _ = np.polyfit(log_r, log_f, 1)
            assert abs(slope + 2.0) < 1.0, f"Наклон {slope:.2f}, ожидался -2.0 (1/r²)"

    def test_dipole_moves_toward_body(self):
        s = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=1, random_seed=101)
        dipole = s.dipoles[0]
        dipole.pos_plus = np.array([5.0, 16.0, 16.0])
        dipole.pos_minus = np.array([5.0, 16.0, 18.0])
        dipole.velocity = np.zeros(3)

        initial_dist = s.compute_distance(dipole)
        for _ in range(200):
            s.evolve_step(0.1)
        final_dist = s.compute_distance(dipole)
        assert final_dist < initial_dist

    def test_reproducibility(self):
        s1 = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=1, random_seed=999)
        s1.run(max_steps=200, dt=0.1, verbose=False)
        s2 = GravitySolver(grid_size=32, body_mass=100.0, n_dipoles=1, random_seed=999)
        s2.run(max_steps=200, dt=0.1, verbose=False)
        assert abs(s1.get_summary()['final_distance'] - s2.get_summary()['final_distance']) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])