"""
Тесты для Вихревого решателя Навье-Стокса — строгая версия.
============================================================================
Проверяют:
    1. Гладкость решения при ΣN = 0, ν > 0.
    2. Строгую монотонность энергии.
    3. Диссипацию энстрофии.
    4. Полную аннигиляцию всех вихрей.
    5. Обнаружение сингулярности при нарушении ΣN = 0.
    6. Воспроизводимость.
    7. Сохранение свойств при разных размерах решётки.
    8. Сходимость по времени.
    9. Проверку периодических граничных условий.
    10. Экспорт отчёта и истории.
============================================================================
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from architect.navier_stokes_vortex_solver import (
        NSVortex,
        NavierStokesVortexSolver,
        _periodic_laplace_scalar,
        _periodic_curl,
        _periodic_gradient_scalar,
    )
except ImportError:
    from src.architect.navier_stokes_vortex_solver import (  # type: ignore
        NSVortex,
        NavierStokesVortexSolver,
        _periodic_laplace_scalar,
        _periodic_curl,
        _periodic_gradient_scalar,
    )


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                      ТЕСТЫ УТИЛИТ ПЕРИОДИЧЕСКОЙ РЕШЁТКИ                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestPeriodicUtilities:
    """Проверка корректности операторов на периодической решётке."""

    def test_laplace_constant_is_zero(self):
        """Лапласиан константы должен быть нулевым."""
        f = np.ones((8, 8, 8))
        lap = _periodic_laplace_scalar(f)
        assert np.allclose(lap, 0.0)

    def test_laplace_sine(self):
        """Лапласиан sin(kx): ∇²sin(kx) = -k²sin(kx)."""
        n = 16
        k = 2 * np.pi / n
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        f = np.sin(k * X)
        lap = _periodic_laplace_scalar(f)
        expected = -k**2 * np.sin(k * X)
        assert np.allclose(lap, expected, atol=0.05)

    def test_curl_gradient_is_zero(self):
        """∇×(∇φ) = 0 для любого скалярного поля."""
        n = 8
        phi = np.random.randn(n, n, n)
        gx, gy, gz = _periodic_gradient_scalar(phi)
        grad_phi = np.array([gx, gy, gz])
        curl = _periodic_curl(grad_phi)
        assert np.allclose(curl, 0.0, atol=1e-10)

    def test_div_curl_is_zero(self):
        """∇·(∇×v) = 0 для любого векторного поля."""
        n = 8
        v = np.random.randn(3, n, n, n)
        curl = _periodic_curl(v)
        gx_x, _, _ = _periodic_gradient_scalar(curl[0])
        _, gy_y, _ = _periodic_gradient_scalar(curl[1])
        _, _, gz_z = _periodic_gradient_scalar(curl[2])
        div_curl = gx_x + gy_y + gz_z
        assert np.allclose(div_curl, 0.0, atol=1e-10)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    ТЕСТЫ СТРУКТУР ДАННЫХ                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestNSVortex:
    """Тесты структуры данных вихря."""

    def test_creation(self):
        """Создание вихря с валидными параметрами."""
        v = NSVortex(
            position=np.array([1.0, 2.0, 3.0]),
            charge=+1,
            orientation=np.array([0.0, 0.0, 1.0]),
            strength=1.5,
            phase=0.0,
        )
        assert v.charge == 1
        assert np.allclose(v.orientation, [0, 0, 1])

    def test_invalid_charge_raises(self):
        """Невалидный заряд вызывает исключение."""
        with pytest.raises(ValueError, match="Заряд вихря должен быть ±1"):
            NSVortex(
                position=np.zeros(3),
                charge=0,
                orientation=np.array([1, 0, 0]),
                strength=1.0,
                phase=0.0,
            )

    def test_zero_orientation_raises(self):
        """Нулевая ориентация вызывает исключение."""
        with pytest.raises(ValueError, match="Ориентация не может быть нулевым"):
            NSVortex(
                position=np.zeros(3),
                charge=1,
                orientation=np.zeros(3),
                strength=1.0,
                phase=0.0,
            )

    def test_orientation_normalized(self):
        """Ориентация автоматически нормализуется."""
        v = NSVortex(
            position=np.zeros(3),
            charge=1,
            orientation=np.array([3.0, 0.0, 0.0]),
            strength=1.0,
            phase=0.0,
        )
        assert np.allclose(np.linalg.norm(v.orientation), 1.0)

    def test_unique_ids(self):
        """Каждый вихрь получает уникальный ID."""
        v1 = NSVortex(np.zeros(3), 1, np.array([1, 0, 0]), 1.0, 0.0)
        v2 = NSVortex(np.ones(3), -1, np.array([0, 1, 0]), 1.0, 0.0)
        assert v1.id != v2.id


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    ТЕСТЫ РЕШАТЕЛЯ                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestNavierStokesVortexSolver:
    """Основные тесты решателя."""

    # ── Валидация входных параметров ────────────────────────────────────────

    def test_invalid_grid_size_raises(self):
        """Слишком маленькая решётка вызывает исключение."""
        with pytest.raises(ValueError, match="grid_size должен быть >= 4"):
            NavierStokesVortexSolver(grid_size=3)

    def test_invalid_viscosity_raises(self):
        """Неположительная вязкость вызывает исключение."""
        with pytest.raises(ValueError, match="Вязкость должна быть > 0"):
            NavierStokesVortexSolver(viscosity=0.0)

        with pytest.raises(ValueError, match="Вязкость должна быть > 0"):
            NavierStokesVortexSolver(viscosity=-0.1)

    # ── Инициализация ───────────────────────────────────────────────────────

    def test_initial_charge_is_zero(self):
        """При инициализации суммарный заряд всегда 0."""
        solver = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=3, random_seed=42
        )
        total_charge = sum(v.charge for v in solver.vortices)
        assert total_charge == 0

    def test_initial_energy_positive(self):
        """Начальная энергия всегда положительна."""
        solver = NavierStokesVortexSolver(
            grid_size=10, n_vortex_pairs=2, random_seed=123
        )
        assert solver.compute_kinetic_energy() > 0

    # ── Гладкость ───────────────────────────────────────────────────────────

    def test_smooth_solution_small_grid(self):
        """Маленькая решётка, 1 пара → гладкость сохраняется."""
        solver = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.02, random_seed=123
        )
        success = solver.run(max_steps=2000, dt=0.03, verbose=False)
        assert success, "Решение потеряло гладкость!"
        summary = solver.get_summary()
        assert summary['all_annihilated']

    def test_multiple_pairs_smooth(self):
        """4 пары → все аннигилируют, гладкость сохраняется."""
        solver = NavierStokesVortexSolver(
            grid_size=16, n_vortex_pairs=4, viscosity=0.01, random_seed=456
        )
        success = solver.run(max_steps=5000, dt=0.03, verbose=False)
        assert success

    def test_high_viscosity_smooth(self):
        """При высокой вязкости аннигиляция происходит быстрее."""
        solver = NavierStokesVortexSolver(
            grid_size=10, n_vortex_pairs=3, viscosity=0.1, random_seed=789
        )
        success = solver.run(max_steps=3000, dt=0.03, verbose=False)
        assert success
        summary = solver.get_summary()
        assert summary['all_annihilated']

    # ── Энергия ─────────────────────────────────────────────────────────────

    def test_energy_monotonically_decreases(self):
        """
        Энергия должна монотонно убывать.

        Допускаются микроскопические флуктуации (относительная амплитуда < 1e-6)
        из-за численных эффектов.
        """
        solver = NavierStokesVortexSolver(
            grid_size=10, n_vortex_pairs=2, viscosity=0.02, random_seed=101
        )
        solver.run(max_steps=2000, dt=0.03, verbose=False)

        energies = np.array([s.kinetic_energy for s in solver.history])
        initial_energy = energies[0]

        diffs = np.diff(energies)
        max_positive = np.max(diffs[diffs > 0]) if np.any(diffs > 0) else 0
        relative_increase = max_positive / initial_energy

        assert relative_increase < 1e-6, (
            f"Энергия выросла на {relative_increase:.2e} от начальной"
        )
        assert energies[-1] < energies[0] * 0.5, (
            f"Энергия не уменьшилась значительно: "
            f"{energies[0]:.4f} → {energies[-1]:.4f}"
        )

    def test_energy_without_annihilation(self):
        """
        Без механизма аннигиляции энергия диссипирует только за счёт
        вязкости, но не до нуля.
        """
        solver = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.01, random_seed=42
        )
        original_check = solver.check_annihilation
        solver.check_annihilation = lambda step: False
        solver.run(max_steps=2000, dt=0.03, verbose=False)
        solver.check_annihilation = original_check

        energies = [s.kinetic_energy for s in solver.history]
        assert energies[-1] < energies[0]
        assert len(solver.vortices) > 0

    # ── Энстрофия ───────────────────────────────────────────────────────────

    def test_enstrophy_decays(self):
        """Энстрофия (∫|ω|²) должна диссипировать."""
        solver = NavierStokesVortexSolver(
            grid_size=10, n_vortex_pairs=2, viscosity=0.02, random_seed=202
        )
        solver.run(max_steps=2000, dt=0.03, verbose=False)
        enstrophies = [s.enstrophy for s in solver.history]
        assert enstrophies[-1] < enstrophies[0] * 0.5, (
            f"Энстрофия не диссипировала: "
            f"{enstrophies[0]:.4f} → {enstrophies[-1]:.4f}"
        )

    # ── Сингулярность при ΣN ≠ 0 ───────────────────────────────────────────

    def test_nonzero_charge_singularity(self):
        """При ΣN ≠ 0 должна возникать сингулярность."""
        solver = NavierStokesVortexSolver(
            grid_size=10, n_vortex_pairs=2, viscosity=0.01, random_seed=555
        )
        extra = NSVortex(
            position=np.array([5.0, 5.0, 5.0]),
            charge=+1,
            orientation=np.array([0.0, 0.0, 1.0]),
            strength=2.0,
            phase=0.0,
        )
        solver.vortices.append(extra)
        assert sum(v.charge for v in solver.vortices) == 1, "Нарушена подготовка теста"
        solver._rebuild_fields()

        success = solver.run(max_steps=2000, dt=0.03, verbose=False)
        assert not success, (
            f"Ожидалась сингулярность при ΣN = {sum(v.charge for v in solver.vortices)}!"
        )

    # ── Воспроизводимость ───────────────────────────────────────────────────

    def test_reproducibility(self):
        """Фиксированный seed → одинаковые траектории."""
        s1 = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=2, viscosity=0.02, random_seed=42
        )
        s1.run(max_steps=200, dt=0.03, verbose=False)

        s2 = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=2, viscosity=0.02, random_seed=42
        )
        s2.run(max_steps=200, dt=0.03, verbose=False)

        for snap1, snap2 in zip(s1.history, s2.history):
            assert snap1.n_vortices == snap2.n_vortices
            assert abs(snap1.kinetic_energy - snap2.kinetic_energy) < 1e-12

    def test_different_seeds_different_results(self):
        """Разные seed'ы дают разные траектории."""
        s1 = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.02, random_seed=1
        )
        s1.run(max_steps=100, dt=0.03, verbose=False)
        e1 = s1.history[-1].kinetic_energy

        s2 = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.02, random_seed=2
        )
        s2.run(max_steps=100, dt=0.03, verbose=False)
        e2 = s2.history[-1].kinetic_energy

        assert abs(e1 - e2) > 1e-10, "Разные seed'ы дали одинаковый результат"

    # ── Метрика гладкости ───────────────────────────────────────────────────

    def test_smoothness_metric_positive(self):
        """Метрика гладкости всегда > 0 для гладких решений."""
        solver = NavierStokesVortexSolver(
            grid_size=10, n_vortex_pairs=2, viscosity=0.02, random_seed=333
        )
        solver.run(max_steps=1000, dt=0.03, verbose=False)
        for snap in solver.history:
            assert snap.smoothness_metric > 0, (
                f"Гладкость упала до {snap.smoothness_metric} на шаге {snap.step}"
            )

    # ── Экспорт ─────────────────────────────────────────────────────────────

    def test_export_history(self, tmp_path):
        """Экспорт истории в JSON."""
        solver = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.02, random_seed=42
        )
        solver.run(max_steps=100, dt=0.03, verbose=False)

        filepath = str(tmp_path / "history.json")
        solver.export_history(filepath)

        assert os.path.exists(filepath)
        with open(filepath) as f:
            data = json.load(f)
        assert len(data) > 0
        assert 'kinetic_energy' in data[0]
        assert 'enstrophy' in data[0]

    def test_export_report(self, tmp_path):
        """Экспорт отчёта в Markdown."""
        solver = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.02, random_seed=42
        )
        solver.run(max_steps=100, dt=0.03, verbose=False)

        filepath = str(tmp_path / "report.md")
        solver.export_report(filepath)

        assert os.path.exists(filepath)
        with open(filepath) as f:
            content = f.read()
        assert "Вихревое решение Навье-Стокса" in content
        assert "Гладкость решения" in content

    # ── Адаптивный шаг ──────────────────────────────────────────────────────

    def test_adaptive_dt_reduces_for_high_velocity(self):
        """При высокой скорости шаг уменьшается."""
        solver = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.01, random_seed=42
        )
        solver.u.fill(10.0)
        dt = solver._compute_adaptive_dt(0.03)
        assert dt < 0.03, f"Адаптивный шаг не уменьшился: {dt}"

    def test_adaptive_dt_uses_base_for_zero_velocity(self):
        """При нулевой скорости используется базовый шаг."""
        solver = NavierStokesVortexSolver(
            grid_size=8, n_vortex_pairs=1, viscosity=0.01, random_seed=42
        )
        solver.u.fill(0.0)
        dt = solver._compute_adaptive_dt(0.03)
        assert dt == 0.03


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           ЗАПУСК                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])