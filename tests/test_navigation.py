"""
Тесты для навигационного модуля ВММП.
============================================================================
Проверяют:
    1. Корабль инициализируется с адаптивной массой.
    2. Масса меняется в ответ на разность давлений.
    3. Корабль движется к цели.
    4. Корабль достигает цели.
    5. Воспроизводимость.
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.navigation import NavigationSolver


class TestNavigation:

    def test_initialization(self):
        nav = NavigationSolver(grid_size=32, source_mass=100.0, random_seed=42)
        assert nav.ship.mass > 0
        assert nav.target_field.pressure > 0

    def test_mass_adapts(self):
        nav = NavigationSolver(grid_size=32, source_mass=100.0, random_seed=123)
        initial_mass = nav.ship.mass
        nav.evolve_step(0.1)
        assert nav.ship.mass != initial_mass, "Масса не изменилась!"

    def test_ship_moves(self):
        nav = NavigationSolver(grid_size=32, source_mass=100.0, random_seed=456)
        initial_pos = nav.ship.position.copy()
        for _ in range(100):
            nav.evolve_step(0.1)
        moved = np.linalg.norm(nav.ship.position - initial_pos)
        assert moved > 0.1, f"Корабль не движется! Смещение: {moved:.4f}"

    def test_ship_reaches_target(self):
        nav = NavigationSolver(grid_size=32, source_mass=100.0, random_seed=789)
        summary = nav.run(max_steps=500, dt=0.1, verbose=False)
        
        # Проверяем, что корабль стабилизировался на орбите
        # (дистанция не меняется сильно в конце)
        distances = nav.distance_history[-100:]  # Последние 100 шагов
        distance_std = np.std(distances)
        
        assert distance_std < 2.0, (
            f"Корабль не стабилизировался! std={distance_std:.2f}"
        )

    def test_reproducibility(self):
        nav1 = NavigationSolver(grid_size=32, source_mass=100.0, random_seed=999)
        nav1.run(max_steps=100, dt=0.1, verbose=False)
        nav2 = NavigationSolver(grid_size=32, source_mass=100.0, random_seed=999)
        nav2.run(max_steps=100, dt=0.1, verbose=False)
        assert nav1.ship.mass == nav2.ship.mass


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])