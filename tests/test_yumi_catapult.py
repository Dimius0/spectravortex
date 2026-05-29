"""
Тесты для Резонансной Катапульты Юми — Акт X
============================================================================
Проверяют:
    1. Инициализация с двумя фундаментальными слоями и эмерджентным
    2. Инертность вычисляется правильно
    3. Резонансная масса с учётом инертности
    4. TEES-синхронизация
    5. Катапультная последовательность
    6. Врата создают резонанс
    7. Воспроизводимость
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.yumi_catapult import (
    YumiCatapult,
    FUNDAMENTAL_SCALES,
    EMERGENT_SCALE,
    COCOON_RADIUS,
    YUMI_RATIO,
)


class TestYumiCatapult:

    def test_initialization(self):
        """Проверка: два фундаментальных слоя + эмерджентный"""
        yumi = YumiCatapult(grid_size=32, random_seed=42)
        
        assert 16 in yumi.fundamental_layers
        assert 32 in yumi.fundamental_layers
        assert yumi.emergent_layer.resolution == 24
        assert len(yumi.fundamental_layers) + 1 == 3  # + эмерджентный

    def test_inertia_calculation(self):
        """Проверка: инертность = mean_k * R²"""
        yumi = YumiCatapult(grid_size=32, random_seed=42)
        
        for res, layer in yumi.fundamental_layers.items():
            expected_inertia = layer.mean_k * COCOON_RADIUS**2
            assert abs(layer.inertia - expected_inertia) < 0.01, (
                f"Инертность {res}³: {layer.inertia:.3f} != {expected_inertia:.3f}"
            )
        
        print(f"\n  Инертность: 16³={yumi.fundamental_layers[16].inertia:.3f}, "
              f"32³={yumi.fundamental_layers[32].inertia:.3f}")

    def test_fractal_time_scaling(self):
        """Проверка: фрактальное время масштабируется как 2:1"""
        yumi = YumiCatapult(grid_size=32, random_seed=42)
        
        t16 = yumi.fundamental_layers[16].local_time
        t32 = yumi.fundamental_layers[32].local_time
        
        assert abs(t32 / t16 - YUMI_RATIO) < 0.01, (
            f"Отношение времён: {t32/t16:.2f} != {YUMI_RATIO}"
        )
        print(f"\n  Фрактальное время: t16={t16:.2f}, t32={t32:.2f}")

    def test_resonant_mass_with_inertia(self):
        """Проверка: резонансная масса с учётом инертности"""
        yumi = YumiCatapult(grid_size=32, random_seed=456)
        
        mass_32 = yumi.calculate_resonant_mass(target_resolution=32)
        
        assert 10.0 < mass_32 < 1000.0, f"Масса {mass_32:.2f} вне пределов!"
        print(f"\n  Резонансная масса (32³): {mass_32:.2f}")

    def test_gate_creates_resonance(self):
        """Проверка: Врата с резонансной массой создают катапульту"""
        sources = [
            {'position': np.array([8, 16, 16]), 'mass': 100.0},
            {'position': np.array([16, 16, 16]), 'mass': 60.0},
            {'position': np.array([24, 16, 16]), 'mass': 30.0},
        ]
        yumi = YumiCatapult(sources=sources, grid_size=32, random_seed=456)
        
        mass_16 = yumi.calculate_resonant_mass(target_resolution=16)
        mass_32 = yumi.calculate_resonant_mass(target_resolution=32)
        
        yumi.add_gate(np.array([16, 8, 16]), mass=mass_16)
        yumi.add_gate(np.array([16, 32, 16]), mass=mass_32)
        
        summary = yumi.run(steps=3000, dt=0.01, verbose=False)
        
        # Проверяем, что были TEES-события или катапульты
        assert summary['tees_events'] > 0 or summary['catapult_events'] > 0, (
            "Ни одного события синхронизации!"
        )
        
        print(f"\n  TEES: {summary['tees_events']}, Катапульт: {summary['catapult_events']}")

    def test_reproducibility(self):
        """Проверка: воспроизводимость"""
        yumi1 = YumiCatapult(grid_size=32, random_seed=999)
        yumi2 = YumiCatapult(grid_size=32, random_seed=999)
        
        assert yumi1.fundamental_layers[16].phase == yumi2.fundamental_layers[16].phase
        assert yumi1.fundamental_layers[32].phase == yumi2.fundamental_layers[32].phase


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])