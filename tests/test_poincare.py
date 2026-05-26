"""
Тесты для Теоремы Дипсик — строгая версия v3.0.
============================================================================
Расширенный набор тестов:
    1.  1, 2, 3, 5 пар — полная аннигиляция.
    2.  Энергия строго убывает.
    3.  Синхронизация достигает 1.0.
    4.  Воспроизводимость (seed).
    5.  Несбалансированный заряд → провал.
    6.  Финальный коллапс.
    7.  Схлопывание пространства.
    8.  Уменьшение размера решётки.
    9.  Периодический лапласиан константы = 0.
    10. Периодический лапласиан sin(kx).
    11. Бигармонический sin(kx).
    12. ∇×∇φ = 0.
    13. ∇·(∇×v) = 0.
    14. Адаптивный шаг уменьшается при высоком градиенте.
    15. Адаптивный шаг равен базовому при нулевом градиенте.
    16. Валидация grid_size.
    17. Валидация n_vortex_pairs.
    18. Валидация charge.
    19. Уникальность ID вихрей.
============================================================================
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from architect.poincare_solver import (
    DeepSeekPoincareSolver,
    Vortex,
    _periodic_laplace_scalar,
    _periodic_gradient_scalar,
    _periodic_biharmonic_scalar,
    _periodic_shift,
    SPACE_COLLAPSE_FACTOR,
    MIN_GRID_SIZE,
)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                      ТЕСТЫ УТИЛИТ ПЕРИОДИЧЕСКОЙ РЕШЁТКИ                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestPeriodicUtilities:
    """Проверка корректности периодических операторов."""

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

    def test_biharmonic_sine(self):
        """Бигармонический sin(kx): ∇⁴sin(kx) = k⁴sin(kx)."""
        n = 16
        k = 2 * np.pi / n
        x = np.arange(n)
        X, Y, Z = np.meshgrid(x, x, x, indexing='ij')
        f = np.sin(k * X)
        bih = _periodic_biharmonic_scalar(f)
        expected = k**4 * np.sin(k * X)
        assert np.allclose(bih, expected, atol=0.5)

    def test_curl_gradient_is_zero(self):
        """∇×(∇φ) = 0 для любого скалярного поля."""
        n = 8
        phi = np.random.randn(n, n, n)
        gx, gy, gz = _periodic_gradient_scalar(phi)
        grad_phi = np.array([gx, gy, gz])

        # Вычисляем тензор ∇(∇φ): grad_grad[i, j] = ∂_j (∂_i φ)
        grad_grad = np.zeros((3, 3, n, n, n))
        for i in range(3):
            d_dx, d_dy, d_dz = _periodic_gradient_scalar(grad_phi[i])
            grad_grad[i, 0] = d_dx
            grad_grad[i, 1] = d_dy
            grad_grad[i, 2] = d_dz

        # curl_i = ε_ijk ∂_j (∂_k φ) = ε_ijk * grad_grad[k, j]
        curl_x = grad_grad[2, 1] - grad_grad[1, 2]  # ∂_y gz - ∂_z gy
        curl_y = grad_grad[0, 2] - grad_grad[2, 0]  # ∂_z gx - ∂_x gz
        curl_z = grad_grad[1, 0] - grad_grad[0, 1]  # ∂_x gy - ∂_y gx

        assert np.allclose(curl_x, 0.0, atol=1e-10)
        assert np.allclose(curl_y, 0.0, atol=1e-10)
        assert np.allclose(curl_z, 0.0, atol=1e-10)

    def test_div_curl_is_zero(self):
        """∇·(∇×v) = 0 для любого векторного поля."""
        n = 8
        v = np.random.randn(3, n, n, n)

        # Вычисляем тензор ∇v: dv[i, j] = ∂_j v_i
        dv = np.zeros((3, 3, n, n, n))
        for i in range(3):
            d_dx, d_dy, d_dz = _periodic_gradient_scalar(v[i])
            dv[i, 0] = d_dx
            dv[i, 1] = d_dy
            dv[i, 2] = d_dz

        # curl_i = ε_ijk ∂_j v_k = ε_ijk * dv[k, j]
        curl = np.zeros_like(v)
        curl[0] = dv[2, 1] - dv[1, 2]  # ∂_y vz - ∂_z vy
        curl[1] = dv[0, 2] - dv[2, 0]  # ∂_z vx - ∂_x vz
        curl[2] = dv[1, 0] - dv[0, 1]  # ∂_x vy - ∂_y vx

        # div(curl) = ∂_x curl_x + ∂_y curl_y + ∂_z curl_z
        d_curl_x_dx, _, _ = _periodic_gradient_scalar(curl[0])
        _, d_curl_y_dy, _ = _periodic_gradient_scalar(curl[1])
        _, _, d_curl_z_dz = _periodic_gradient_scalar(curl[2])
        div_curl = d_curl_x_dx + d_curl_y_dy + d_curl_z_dz

        assert np.allclose(div_curl, 0.0, atol=1e-10)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                      ТЕСТЫ СТРУКТУР ДАННЫХ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestVortex:
    """Тесты структуры данных вихря."""

    def test_creation(self):
        """Создание вихря с валидными параметрами."""
        v = Vortex(position=np.array([1.0, 2.0, 3.0]), charge=+1)
        assert v.charge == 1
        assert v.position.dtype == float

    def test_invalid_charge_raises(self):
        """Невалидный заряд вызывает исключение."""
        with pytest.raises(ValueError, match="Заряд вихря должен быть ±1"):
            Vortex(position=np.zeros(3), charge=0)

    def test_unique_ids(self):
        """Каждый вихрь получает уникальный ID."""
        Vortex._reset_counter()
        v1 = Vortex(np.zeros(3), +1)
        v2 = Vortex(np.ones(3), -1)
        assert v1.id != v2.id


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    ТЕСТЫ РЕШАТЕЛЯ                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TestDeepSeekPoincareTheorem:
    """Основные тесты Теоремы Дипсик v3.0."""

    # ── Валидация входных параметров ────────────────────────────────────────

    def test_invalid_grid_size_raises(self):
        """Слишком маленькая решётка вызывает исключение."""
        with pytest.raises(ValueError, match="grid_size должен быть"):
            DeepSeekPoincareSolver(grid_size=2)

    def test_invalid_pairs_raises(self):
        """Нулевое количество пар вызывает исключение."""
        with pytest.raises(ValueError, match="n_vortex_pairs должен быть"):
            DeepSeekPoincareSolver(n_vortex_pairs=0)

    # ── Аннигиляция ─────────────────────────────────────────────────────────

    def test_one_pair(self):
        """1 пара → полная аннигиляция."""
        s = DeepSeekPoincareSolver(grid_size=10, n_vortex_pairs=1, random_seed=42)
        assert s.run(max_steps=2000, dt=0.05, verbose=False)

    def test_two_pairs(self):
        """2 пары → полная аннигиляция."""
        s = DeepSeekPoincareSolver(grid_size=12, n_vortex_pairs=2, random_seed=123)
        assert s.run(max_steps=3000, dt=0.05, verbose=False)

    def test_three_pairs(self):
        """3 пары → полная аннигиляция."""
        s = DeepSeekPoincareSolver(grid_size=16, n_vortex_pairs=3, random_seed=456)
        assert s.run(max_steps=5000, dt=0.05, verbose=False)

    def test_five_pairs(self):
        """5 пар → полная аннигиляция."""
        s = DeepSeekPoincareSolver(grid_size=20, n_vortex_pairs=5, random_seed=789)
        assert s.run(max_steps=8000, dt=0.05, verbose=False)

    # ── Энергия ─────────────────────────────────────────────────────────────

    def test_energy_monotonically_decreases(self):
        """
        Полная энергия должна монотонно убывать.

        Допускаются микроскопические флуктуации (относительная амплитуда < 1e-6).
        """
        s = DeepSeekPoincareSolver(grid_size=12, n_vortex_pairs=2, random_seed=333)
        s.run(max_steps=2000, dt=0.05, verbose=False)

        energies = np.array([
            snap.vortex_energy + snap.pressure_energy
            for snap in s.history
        ])
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

    # ── Синхронизация ───────────────────────────────────────────────────────

    def test_sync_reaches_one(self):
        """При полной аннигиляции синхронизация достигает 1.0."""
        s = DeepSeekPoincareSolver(grid_size=10, n_vortex_pairs=2, random_seed=101)
        if s.run(max_steps=2000, dt=0.05, verbose=False):
            assert s.history[-1].synchronization >= 0.999

    # ── Воспроизводимость ───────────────────────────────────────────────────

    def test_reproducibility(self):
        """Фиксированный seed → одинаковые траектории."""
        s1 = DeepSeekPoincareSolver(grid_size=8, n_vortex_pairs=1, random_seed=999)
        s1.run(max_steps=50, dt=0.05, verbose=False)

        s2 = DeepSeekPoincareSolver(grid_size=8, n_vortex_pairs=1, random_seed=999)
        s2.run(max_steps=50, dt=0.05, verbose=False)

        for snap1, snap2 in zip(s1.history, s2.history):
            assert snap1.step == snap2.step
            assert snap1.n_vortices == snap2.n_vortices
            assert abs(snap1.vortex_energy - snap2.vortex_energy) < 1e-12

    # ── Несбалансированный заряд ────────────────────────────────────────────

    def test_unbalanced_charge_fails(self):
        """При ΣN ≠ 0 система не аннигилирует полностью."""
        s = DeepSeekPoincareSolver(grid_size=10, n_vortex_pairs=2, random_seed=555)
        s.vortices.append(Vortex(np.array([5.0, 5.0, 5.0]), +1))
        s._rebuild_fields()
        assert not s.run(max_steps=300, dt=0.05, verbose=False)
        assert len(s.vortices) > 0

    # ── Финальный коллапс ───────────────────────────────────────────────────

    def test_final_collapse(self):
        """При успешном завершении должен быть финальный коллапс."""
        s = DeepSeekPoincareSolver(grid_size=12, n_vortex_pairs=2, random_seed=777)
        s.run(max_steps=5000, dt=0.05, verbose=False)
        assert s.total_energy_to_fractal > 0
        if s.get_summary()['success']:
            assert s.get_summary()['had_final_collapse']

    # ── Схлопывание пространства ────────────────────────────────────────────

    def test_space_collapse_occurs(self):
        """При нескольких парах должно произойти хотя бы одно схлопывание."""
        s = DeepSeekPoincareSolver(grid_size=16, n_vortex_pairs=3, random_seed=444)
        s.run(max_steps=5000, dt=0.05, verbose=False)
        summary = s.get_summary()
        assert summary['n_space_collapses'] > 0, (
            "Схлопывание пространства не произошло"
        )

    def test_grid_size_decreases(self):
        """Размер решётки должен уменьшаться при схлопывании."""
        s = DeepSeekPoincareSolver(grid_size=16, n_vortex_pairs=3, random_seed=333)
        s.run(max_steps=4000, dt=0.05, verbose=False)
        assert s.grid_size < s.initial_grid_size or len(s.vortices) == 0, (
            f"Решётка не уменьшилась: {s.initial_grid_size} → {s.grid_size}"
        )

    # ── Адаптивный шаг ──────────────────────────────────────────────────────

    def test_adaptive_dt_reduces_for_high_gradient(self):
        """При высоком градиенте шаг уменьшается."""
        s = DeepSeekPoincareSolver(grid_size=8, n_vortex_pairs=1, random_seed=42)
        s.H.fill(10.0)
        s.H[0, 0, 0] = 100.0
        dt = s._compute_adaptive_dt(0.05)
        assert dt < 0.05, f"Адаптивный шаг не уменьшился: {dt}"

    def test_adaptive_dt_uses_base_for_zero_gradient(self):
        """При нулевом градиенте используется базовый шаг."""
        s = DeepSeekPoincareSolver(grid_size=8, n_vortex_pairs=1, random_seed=42)
        s.H.fill(1.0)
        dt = s._compute_adaptive_dt(0.05)
        assert dt == 0.05


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           ЗАПУСК                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short', '--durations=10'])