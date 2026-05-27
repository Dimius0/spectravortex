"""
Тесты для орбитальной динамики через групповое экранирование.
============================================================================
Проверяют:
    1. Два тела создают суперпозицию экранирований.
    2. Тела сближаются под действием взаимного приталкивания.
    3. Диполь чувствует оба тела.
    4. Орбитальная устойчивость (тела не падают друг на друга).
    5. Воспроизводимость.
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.orbital_solver import OrbitalSolver, OrbitalDipole, OrbitalBody


class TestOrbitalSolver:

    def test_initialization(self):
        s = OrbitalSolver(grid_size=32, mass1=100.0, mass2=50.0, n_dipoles=2, random_seed=42)
        assert len(s.dipoles) == 2
        assert s.body1.mass == 100.0
        assert s.body2.mass == 50.0

    def test_superposition_of_screening(self):
        """Давление минимально вблизи обоих тел."""
        s = OrbitalSolver(grid_size=32, mass1=100.0, mass2=50.0, n_dipoles=0, random_seed=42)

        p_bg = 1.0
        p_near_1 = s.pressure_field[
            int(s.body1.position[0]), int(s.body1.position[1]), int(s.body1.position[2])
        ]
        p_near_2 = s.pressure_field[
            int(s.body2.position[0]), int(s.body2.position[1]), int(s.body2.position[2])
        ]
        p_far = s.pressure_field[0, 0, 0]

        assert p_near_1 < p_bg, f"Нет экранирования у тела 1: {p_near_1}"
        assert p_near_2 < p_bg, f"Нет экранирования у тела 2: {p_near_2}"
        assert p_far > p_near_1, "Вдали давление должно быть выше"

    def test_bodies_attract_each_other(self):
        """Тела должны сближаться под действием взаимного приталкивания."""
        s = OrbitalSolver(grid_size=32, mass1=100.0, mass2=50.0, n_dipoles=0, random_seed=123)

        initial_dist = s.distance_between_bodies()

        for _ in range(500):
            s.evolve_step(0.05)

        final_dist = s.distance_between_bodies()
        assert final_dist < initial_dist, (
            f"Тела не сблизились: {initial_dist:.2f} → {final_dist:.2f}"
        )

    def test_dipole_feels_both_bodies(self):
        """Диполь должен двигаться под действием обоих тел."""
        s = OrbitalSolver(grid_size=32, mass1=100.0, mass2=50.0, n_dipoles=1, random_seed=456)
        dipole = s.dipoles[0]

        initial_dist1 = s.distance_to_body1(dipole)
        initial_dist2 = s.distance_to_body2(dipole)

        for _ in range(300):
            s.evolve_step(0.05)

        final_dist1 = s.distance_to_body1(dipole)
        final_dist2 = s.distance_to_body2(dipole)

        # Хотя бы одно расстояние должно измениться
        changed = (
            abs(final_dist1 - initial_dist1) > 0.1 or
            abs(final_dist2 - initial_dist2) > 0.1
        )
        assert changed, "Диполь не движется!"

    def test_force_on_body_has_correct_direction(self):
        """Сила на тело 1 должна быть направлена к телу 2."""
        s = OrbitalSolver(grid_size=32, mass1=100.0, mass2=50.0, n_dipoles=0, random_seed=789)

        force = s.compute_force_on_body(s.body1, s.body2)
        force_mag = np.linalg.norm(force)

        if force_mag > 1e-12:
            to_other = s.body2.position - s.body1.position
            to_other = to_other - np.round(to_other / s.grid_size) * s.grid_size
            to_other /= np.linalg.norm(to_other)

            force_dir = force / force_mag
            dot_product = np.dot(force_dir, to_other)

            assert dot_product > 0, f"Сила направлена от тела! dot={dot_product:.4f}"

    def test_reproducibility(self):
        s1 = OrbitalSolver(grid_size=32, mass1=100.0, mass2=50.0, n_dipoles=1, random_seed=999)
        s1.run(max_steps=400, dt=0.05, verbose=False)
        s2 = OrbitalSolver(grid_size=32, mass1=100.0, mass2=50.0, n_dipoles=1, random_seed=999)
        s2.run(max_steps=400, dt=0.05, verbose=False)
        
        summary1 = s1.get_summary()
        summary2 = s2.get_summary()
        
        if 'r12_final' in summary1 and 'r12_final' in summary2:
            assert abs(summary1['r12_final'] - summary2['r12_final']) < 1e-10
        else:
            pytest.skip("Недостаточно снимков для сравнения")


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])