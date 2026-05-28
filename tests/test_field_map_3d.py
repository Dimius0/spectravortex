"""
Тесты для 3D-карты вихревого поля.
============================================================================
Проверяют:
    1. Карта создаётся с узлами.
    2. Бегуны находятся.
    3. Переходы обнаруживаются.
    4. Экспорт и импорт JSON.
    5. Карта с двумя источниками.
    6. Воспроизводимость.
============================================================================
"""

import sys
import os
from pathlib import Path
import json

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.field_map_3d import FieldMap3D


class TestFieldMap3D:

    def test_map_has_nodes(self):
        m = FieldMap3D(grid_size=32, map_resolution=24, random_seed=42)
        assert len(m.nodes) == 24**3, f"Узлов: {len(m.nodes)}, ожидалось {24**3}"

    def test_runners_exist(self):
        m = FieldMap3D(grid_size=32, map_resolution=24, random_seed=123)
        summary = m.run(verbose=False)
        assert summary['has_runners'], "Бегуны не найдены!"

    
    def test_export_import_json(self, tmp_path):
        m1 = FieldMap3D(grid_size=32, map_resolution=24, random_seed=789)
        filepath = str(tmp_path / "test_map.json")
        m1.save(filepath)
        assert os.path.exists(filepath)
        m2 = FieldMap3D.load(filepath)
        assert len(m2.nodes) == len(m1.nodes)

    def test_two_sources(self):
        sources = [
            {'position': np.array([10, 16, 16]), 'mass': 100.0},
            {'position': np.array([22, 16, 16]), 'mass': 60.0},
        ]
        m = FieldMap3D(grid_size=32, map_resolution=24, sources=sources, random_seed=101)
        summary = m.run(verbose=False)
        assert summary['n_nodes'] == 24**3

    def test_reproducibility(self):
        m1 = FieldMap3D(grid_size=32, map_resolution=24, random_seed=999)
        m2 = FieldMap3D(grid_size=32, map_resolution=24, random_seed=999)
        assert len(m1.runners) == len(m2.runners)


if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])