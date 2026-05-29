"""
Тесты для NS-1 генератора — Акт XI
============================================================================
Проверяют:
    1. Чистый материал даёт разумный индекс
    2. Смесь материалов считается корректно
    3. Частота растёт с усложнением смеси
    4. Выход энергии положителен
    5. Воспроизводимость
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.ns1_generator import NS1Generator, Material, MATERIAL_DB


class TestNS1Generator:

    def test_pure_plastic(self):
        gen = NS1Generator([MATERIAL_DB['пластик_пэт']])
        d_idx = gen.calculate_debris_index()
        assert d_idx > 0, "Индекс должен быть положительным"
        print(f"\n  ПЭТ-пластик: D_idx={d_idx:.3f}, f_opt={gen.calculate_optimal_frequency():.1f} кГц")

    def test_mixed_waste(self):
        materials = [
            Material('Пластик', 1380, 350, 0.85, 0.4),
            Material('Древесина', 700, 450, 0.60, 0.3),
            Material('Органика', 1100, 500, 0.75, 0.3),
        ]
        gen = NS1Generator(materials)
        report = gen.get_report()
        assert report['debris_index'] > 0
        assert report['energy_yield_kwh_per_kg'] > 0
        print(f"\n  Смесь: D_idx={report['debris_index']:.3f}, "
              f"E={report['energy_yield_kwh_per_kg']:.3f} кВт·ч/кг")

    def test_complexity_increases_frequency(self):
        gen1 = NS1Generator([MATERIAL_DB['пластик_пэт']])
        f1 = gen1.calculate_optimal_frequency()
        
        materials = [
            MATERIAL_DB['пластик_пэт'],
            MATERIAL_DB['алюминий_банка'],
            MATERIAL_DB['электронный_лом'],
        ]
        for m in materials:
            m.mass_fraction = 1.0 / 3
        gen3 = NS1Generator(materials)
        f3 = gen3.calculate_optimal_frequency()
        
        assert f3 > f1, f"Частота смеси ({f3:.1f}) должна быть выше частоты чистого ({f1:.1f})"
        print(f"\n  f(1 комп)={f1:.1f} кГц, f(3 комп)={f3:.1f} кГц")

    def test_energy_yield_positive(self):
        for name, mat in MATERIAL_DB.items():
            gen = NS1Generator([mat])
            e_yield = gen.calculate_energy_yield()
            assert e_yield > 0, f"{name}: выход энергии = {e_yield:.4f}"
        print(f"\n  Все материалы дают положительный выход энергии")

    def test_reproducibility(self):
        gen1 = NS1Generator([MATERIAL_DB['древесина_сухая']])
        gen2 = NS1Generator([MATERIAL_DB['древесина_сухая']])
        assert gen1.calculate_debris_index() == gen2.calculate_debris_index()


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])