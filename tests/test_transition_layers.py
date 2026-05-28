"""
Тесты для переходных слоёв.
============================================================================
Проверяют:
    1. Слой находится на всех трёх масштабах.
    2. Фрактальный коэффициент k примерно одинаков.
    3. Асимметрия растёт с потоком.
    4. Воспроизводимость.
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.transition_layers import TransitionLayerSolver, compare_scales


class TestTransitionLayers:

    def test_micro_layer_exists(self):
        s = TransitionLayerSolver(grid_size=32, scale='micro', random_seed=42)
        points = s.find_transition_layer()
        assert len(points) > 100, f"Слишком мало точек: {len(points)}"

    def test_meso_layer_exists(self):
        s = TransitionLayerSolver(grid_size=32, scale='meso', random_seed=123)
        points = s.find_transition_layer()
        assert len(points) > 100, f"Слишком мало точек: {len(points)}"

    def test_macro_layer_exists(self):
        s = TransitionLayerSolver(grid_size=32, scale='macro', random_seed=456)
        points = s.find_transition_layer()
        assert len(points) > 100, f"Слишком мало точек: {len(points)}"

    def test_asymmetry_increases_with_flow(self):
        """Чем сильнее поток, тем больше асимметрия."""
        asymms = []
        for scale in ['micro', 'meso', 'macro']:
            s = TransitionLayerSolver(grid_size=32, scale=scale, random_seed=789)
            s.find_transition_layer()
            profile = s.compute_radial_profile()
            asymms.append(profile.asymmetry)

        # Асимметрия должна расти с потоком
        assert asymms[2] > asymms[0], (
            f"Асимметрия не растёт: micro={asymms[0]:.2f}, macro={asymms[2]:.2f}"
        )

    def test_fractal_k_similar(self):
        """Фрактальный коэффициент k должен быть примерно одинаковым."""
        results = compare_scales(grid_size=32, verbose=False)
        k_values = [r['fractal_k'] for r in results.values()]
        k_mean = np.mean(k_values)
        k_std = np.std(k_values)

        # Относительная ошибка должна быть меньше 50%
        relative_error = k_std / k_mean if k_mean > 0 else 1.0
        assert relative_error < 0.5, (
            f"Слишком большой разброс k: {k_values}, ошибка={relative_error:.2f}"
        )

    def test_reproducibility(self):
        s1 = TransitionLayerSolver(grid_size=32, scale='meso', random_seed=999)
        profile1 = s1.compute_radial_profile()

        s2 = TransitionLayerSolver(grid_size=32, scale='meso', random_seed=999)
        profile2 = s2.compute_radial_profile()

        assert profile1.thickness == pytest.approx(profile2.thickness, rel=1e-10)


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])