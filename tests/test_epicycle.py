"""
Тесты для эпициклов.
============================================================================
Проверяют:
    1. Инициализация системы с двумя телами и диполем.
    2. Диполь движется по возмущённой орбите.
    3. Траектория содержит петли (эпициклы).
    4. Воспроизводимость.
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.epicycle_solver import EpicycleSolver


class TestEpicycleSolver:

    def test_initialization(self):
        s = EpicycleSolver(grid_size=64, mass_primary=200.0, mass_secondary=50.0, random_seed=42)
        assert s.body1.mass == 200.0
        assert s.body2.mass == 50.0
        assert s.dipole.strength == 1.0

    def test_dipole_moves(self):
        """Диполь должен двигаться по орбите."""
        s = EpicycleSolver(grid_size=64, mass_primary=200.0, mass_secondary=50.0, random_seed=123)
        initial_pos = s.dipole.center.copy()
        for _ in range(200):
            s.evolve_step(0.05)
        final_pos = s.dipole.center
        moved = np.linalg.norm(final_pos - initial_pos)
        assert moved > 0.1, f"Диполь не движется! Смещение: {moved:.4f}"

    def test_epicycles_detected(self):
        """За 5000 шагов должны обнаружиться петли."""
        s = EpicycleSolver(grid_size=64, mass_primary=200.0, mass_secondary=50.0, random_seed=456)
        s.run(max_steps=5000, dt=0.05, verbose=False)
        summary = s.get_summary()
        assert summary['epicycles_detected'], (
            f"Эпициклы не обнаружены! Петель: {summary.get('n_loops', 0)}"
        )

    def test_reproducibility(self):
        s1 = EpicycleSolver(grid_size=64, mass_primary=200.0, mass_secondary=50.0, random_seed=999)
        s1.run(max_steps=1000, dt=0.05, verbose=False)
        s2 = EpicycleSolver(grid_size=64, mass_primary=200.0, mass_secondary=50.0, random_seed=999)
        s2.run(max_steps=1000, dt=0.05, verbose=False)
        assert s1.get_summary()['n_loops'] == s2.get_summary()['n_loops']


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])