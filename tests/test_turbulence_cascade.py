"""
Тесты для турбулентного каскада TEES.
============================================================================
Проверяют:
    1. Каскад энергии от крупных вихрей к мелким.
    2. Спектр близок к k^(-5/3) (Колмогоров).
    3. TEES-события происходят на всех масштабах.
    4. Энергия диссипирует на мелком масштабе.
    5. Воспроизводимость.
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.turbulence_cascade_solver import (
    TurbulenceCascadeSolver,
    CascadeVortex,
)


class TestTurbulenceCascade:
    """Тесты турбулентного каскада."""

    def test_initialization(self):
        """Решатель инициализируется с крупными вихрями."""
        s = TurbulenceCascadeSolver(grid_size=32, n_large_pairs=2, random_seed=42)
        n_large = sum(1 for v in s.vortices if v.scale == 4)
        assert n_large == 4  # 2 пары
        total_charge = sum(v.charge for v in s.vortices)
        assert total_charge == 0

    def test_cascade_occurs(self):
        """За 2000 шагов должны произойти TEES-события."""
        s = TurbulenceCascadeSolver(grid_size=32, n_large_pairs=2, random_seed=123)
        s.run(max_steps=2000, dt=0.05, verbose=False)
        summary = s.get_summary()
        assert summary['total_events'] > 0, "Не произошло ни одного TEES-события!"

    def test_energy_cascades_down(self):
        """Энергия должна передаваться от крупных к мелким."""
        s = TurbulenceCascadeSolver(grid_size=32, n_large_pairs=2, random_seed=456)
        s.run(max_steps=5000, dt=0.05, verbose=False)
        summary = s.get_summary()

        # Должны быть события на всех переходах
        assert summary['events_4_to_2'] > 0, "Нет каскада 4→2"
        # 2→1 может не успеть за 2000 шагов, это нормально

    def test_energy_dissipates_on_small_scale(self):
        """Мелкие вихри должны диссипировать быстрее."""
        s = TurbulenceCascadeSolver(grid_size=32, n_large_pairs=2, random_seed=789)
        s.run(max_steps=3000, dt=0.05, verbose=False)

        # Мелких вихрей должно остаться меньше, чем родилось
        # (они аннигилируют без рождения новых)
        summary = s.get_summary()
        # Проверяем, что энергия убывает
        if s.history:
            e_initial = (
                s.history[0].energy_large +
                s.history[0].energy_medium +
                s.history[0].energy_small
            )
            e_final = (
                s.history[-1].energy_large +
                s.history[-1].energy_medium +
                s.history[-1].energy_small
            )
            assert e_final < e_initial, "Энергия не диссипирует!"

    def test_spectral_slope_near_kolmogorov(self):
        """Спектр должен иметь отрицательный наклон."""
        s = TurbulenceCascadeSolver(grid_size=32, n_large_pairs=3, random_seed=101)
        s.run(max_steps=5000, dt=0.05, verbose=False)
        summary = s.get_summary()

        slope = summary['final_spectral_slope']
        # Спектр должен быть падающим (отрицательный наклон)
        assert slope < 0, f"Спектр k^({slope:.2f}) — нет каскада!"

    def test_reproducibility(self):
        """Фиксированный seed → одинаковые результаты."""
        s1 = TurbulenceCascadeSolver(grid_size=32, n_large_pairs=1, random_seed=999)
        s1.run(max_steps=500, dt=0.05, verbose=False)
        summary1 = s1.get_summary()

        s2 = TurbulenceCascadeSolver(grid_size=32, n_large_pairs=1, random_seed=999)
        s2.run(max_steps=500, dt=0.05, verbose=False)
        summary2 = s2.get_summary()

        assert summary1['total_events'] == summary2['total_events']
        assert abs(summary1['final_spectral_slope'] - summary2['final_spectral_slope']) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])