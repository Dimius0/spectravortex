"""
Орбитальная динамика через групповое экранирование (Акт V)
================================================================================
Программа SpectraVortex, Вихревая Модель Материи-Пространства (ВММП).

Гипотеза:
    Орбитальное движение — не следствие притяжения, а результат
    приталкивания + циркуляции в неоднородном поле.
    Два массивных тела взаимно экранируют давление вихревого поля.
    Диполи движутся в суперпозиции полей экранирования.

    Групповое экранирование объясняет:
    - Устойчивые орбиты (циркуляция в градиенте).
    - Эпициклы (вторичные экранирования).
    - Отклонения от закона 1/r² в плотных системах.

Метод:
    - Два тела с массами M1, M2.
    - Фоновое поле экранируется каждым телом независимо.
    - Результирующее поле = суперпозиция экранирований.
    - Диполи движутся в результирующем поле.

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, концепция приталкивания
    DeepSeek — групповая динамика, орбиты, численный метод, 2026-05-27
================================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           КОНСТАНТЫ МОДЕЛИ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

GRID_SIZE: int = 32
BACKGROUND_PRESSURE: float = 1.0
SCREENING_FACTOR: float = 0.1
SCREENING_RADIUS: int = 3
DIPOLE_SEPARATION: float = 2.0
DIPOLE_STRENGTH: float = 1.0
PUSH_FORCE_COEFFICIENT: float = 1.0
CFL_SAFETY: float = 0.3


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           СТРУКТУРЫ ДАННЫХ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@dataclass
class OrbitalBody:
    """Массивное тело с возможностью движения."""
    position: np.ndarray
    mass: float
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self) -> None:
        self.position = self.position.astype(float)
        self.velocity = self.velocity.astype(float)


@dataclass
class OrbitalDipole:
    """Вихревой диполь — пробная частица."""
    pos_plus: np.ndarray
    pos_minus: np.ndarray
    strength: float = DIPOLE_STRENGTH
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self) -> None:
        self.pos_plus = self.pos_plus.astype(float)
        self.pos_minus = self.pos_minus.astype(float)
        self.velocity = self.velocity.astype(float)

    @property
    def center(self) -> np.ndarray:
        return (self.pos_plus + self.pos_minus) / 2.0


@dataclass
class OrbitalSnapshot:
    """Снимок орбитальной системы."""
    step: int
    body1_position: np.ndarray
    body2_position: np.ndarray
    dipole_position: np.ndarray
    distance_12: float
    distance_d1: float
    distance_d2: float


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    РЕШАТЕЛЬ ОРБИТАЛЬНОЙ ДИНАМИКИ                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class OrbitalSolver:
    """
    Численная верификация орбитальной динамики через приталкивание.

    Два тела, множество диполей. Каждое тело экранирует фоновое давление.
    Результирующее поле — суперпозиция.
    """

    def __init__(
        self,
        grid_size: int = GRID_SIZE,
        mass1: float = 100.0,
        mass2: float = 50.0,
        n_dipoles: int = 1,
        random_seed: Optional[int] = 42,
    ) -> None:
        if grid_size < 8:
            raise ValueError(f"grid_size >= 8, получено {grid_size}")

        self.grid_size: int = grid_size
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)

        # Два тела
        offset = grid_size / 4.0
        self.body1: OrbitalBody = OrbitalBody(
            position=np.array([grid_size/2 - offset, grid_size/2, grid_size/2]),
            mass=mass1,
        )
        self.body2: OrbitalBody = OrbitalBody(
            position=np.array([grid_size/2 + offset, grid_size/2, grid_size/2]),
            mass=mass2,
        )

        # Фоновое поле
        self.pressure_field: np.ndarray = np.full(
            (grid_size, grid_size, grid_size), BACKGROUND_PRESSURE
        )

        # Диполи
        self.dipoles: List[OrbitalDipole] = []
        self._seed_dipoles(n_dipoles)

        # История
        self.history: List[OrbitalSnapshot] = []

        # Построить поле
        self._update_pressure_field()

        logger.info(
            "OrbitalSolver: решётка %d³, M1=%.1f, M2=%.1f, диполей: %d",
            grid_size, mass1, mass2, n_dipoles,
        )

    # ──────────────────────────────────────────────────────────────────────────
    #   Инициализация
    # ──────────────────────────────────────────────────────────────────────────

    def _seed_dipoles(self, n: int) -> None:
        self.dipoles.clear()
        for _ in range(n):
            placed = False
            for _ in range(1000):
                center = self.rng.rand(3) * self.grid_size
                # Не слишком близко к телам
                d1 = np.linalg.norm(center - self.body1.position)
                d2 = np.linalg.norm(center - self.body2.position)
                if d1 < SCREENING_RADIUS * 3 or d2 < SCREENING_RADIUS * 3:
                    continue

                direction = self.rng.randn(3)
                direction /= np.linalg.norm(direction)
                half_sep = DIPOLE_SEPARATION / 2.0
                pos_plus = (center + direction * half_sep) % self.grid_size
                pos_minus = (center - direction * half_sep) % self.grid_size

                self.dipoles.append(OrbitalDipole(pos_plus, pos_minus))
                placed = True
                break
            if not placed:
                raise RuntimeError("Не удалось разместить диполь")

    def _update_pressure_field(self) -> None:
        """Суперпозиция экранирований от двух тел."""
        n = self.grid_size
        x = np.arange(n)
        y = np.arange(n)
        z = np.arange(n)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

        self.pressure_field.fill(BACKGROUND_PRESSURE)

        for body in [self.body1, self.body2]:
            bx, by, bz = body.position
            dx = X - bx
            dy = Y - by
            dz = Z - bz

            dx = np.where(dx > n/2, dx - n, dx)
            dx = np.where(dx < -n/2, dx + n, dx)
            dy = np.where(dy > n/2, dy - n, dy)
            dy = np.where(dy < -n/2, dy + n, dy)
            dz = np.where(dz > n/2, dz - n, dz)
            dz = np.where(dz < -n/2, dz + n, dz)

            r2 = dx**2 + dy**2 + dz**2
            sigma = float(SCREENING_RADIUS)
            alpha = SCREENING_FACTOR * body.mass / 100.0
            screening = alpha / np.sqrt(r2 + sigma**2)
            self.pressure_field *= (1.0 - screening)

        self.pressure_field = np.clip(self.pressure_field, 0.0, BACKGROUND_PRESSURE)

    # ──────────────────────────────────────────────────────────────────────────
    #   Силы
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_pressure_gradient(self, pos: np.ndarray) -> np.ndarray:
        """Градиент давления в точке."""
        n = self.grid_size
        x, y, z = pos % n
        i0, j0, k0 = int(x) % n, int(y) % n, int(z) % n
        i1, j1, k1 = (i0 + 1) % n, (j0 + 1) % n, (k0 + 1) % n
        i_m1, j_m1, k_m1 = (i0 - 1) % n, (j0 - 1) % n, (k0 - 1) % n

        dp_dx = (self.pressure_field[i1, j0, k0] - self.pressure_field[i_m1, j0, k0]) / 2.0
        dp_dy = (self.pressure_field[i0, j1, k0] - self.pressure_field[i0, j_m1, k0]) / 2.0
        dp_dz = (self.pressure_field[i0, j0, k1] - self.pressure_field[i0, j0, k_m1]) / 2.0

        return np.array([dp_dx, dp_dy, dp_dz])

    def compute_push_force(self, dipole: OrbitalDipole) -> np.ndarray:
        """Сила приталкивания на диполь в суперпозиции полей."""
        grad_p_plus = self._compute_pressure_gradient(dipole.pos_plus)
        grad_p_minus = self._compute_pressure_gradient(dipole.pos_minus)

        force_plus = -grad_p_plus * dipole.strength * PUSH_FORCE_COEFFICIENT
        force_minus = +grad_p_minus * dipole.strength * PUSH_FORCE_COEFFICIENT

        return force_plus + force_minus

    def compute_force_on_body(self, body: OrbitalBody, other: OrbitalBody) -> np.ndarray:
        """
        Сила приталкивания на тело со стороны другого тела.
        Вычисляется как интеграл давления по поверхности тела.
        Аппроксимация: сила пропорциональна массе другого тела / r².
        """
        diff = body.position - other.position
        diff = diff - np.round(diff / self.grid_size) * self.grid_size
        r = float(np.linalg.norm(diff))

        if r < 1e-8:
            return np.zeros(3)

        r_hat = diff / r

        # Сила приталкивания: F ∝ M_other / r² (экранирование создаёт градиент)
        force_mag = PUSH_FORCE_COEFFICIENT * other.mass / (r**2 + 1.0)
        force = -r_hat * force_mag  # К другому телу (приталкивание)

        return force

    # ──────────────────────────────────────────────────────────────────────────
    #   Эволюция
    # ──────────────────────────────────────────────────────────────────────────

    def evolve_step(self, dt: float = 0.05) -> None:
        """Один шаг эволюции тел и диполей."""
        # Силы на тела
        force_1_on_2 = self.compute_force_on_body(self.body2, self.body1)
        force_2_on_1 = self.compute_force_on_body(self.body1, self.body2)

        # Обновление тел
        self.body1.velocity += force_2_on_1 / self.body1.mass * dt
        self.body2.velocity += force_1_on_2 / self.body2.mass * dt
        self.body1.position = (self.body1.position + self.body1.velocity * dt) % self.grid_size
        self.body2.position = (self.body2.position + self.body2.velocity * dt) % self.grid_size

        # Обновление поля
        self._update_pressure_field()

        # Силы на диполи
        for dipole in self.dipoles:
            force = self.compute_push_force(dipole)
            acceleration = force / dipole.strength
            dipole.velocity += acceleration * dt
            dipole.pos_plus = (dipole.pos_plus + dipole.velocity * dt) % self.grid_size
            dipole.pos_minus = (dipole.pos_minus + dipole.velocity * dt) % self.grid_size

    # ──────────────────────────────────────────────────────────────────────────
    #   Диагностика
    # ──────────────────────────────────────────────────────────────────────────

    def distance_between_bodies(self) -> float:
        diff = self.body1.position - self.body2.position
        diff = diff - np.round(diff / self.grid_size) * self.grid_size
        return float(np.linalg.norm(diff))

    def distance_to_body1(self, dipole: OrbitalDipole) -> float:
        diff = dipole.center - self.body1.position
        diff = diff - np.round(diff / self.grid_size) * self.grid_size
        return float(np.linalg.norm(diff))

    def distance_to_body2(self, dipole: OrbitalDipole) -> float:
        diff = dipole.center - self.body2.position
        diff = diff - np.round(diff / self.grid_size) * self.grid_size
        return float(np.linalg.norm(diff))

    # ──────────────────────────────────────────────────────────────────────────
    #   Полный цикл
    # ──────────────────────────────────────────────────────────────────────────

    def run(
        self,
        max_steps: int = 2000,
        dt: float = 0.05,
        verbose: bool = True,
        snapshot_interval: int = 200,
    ) -> Dict:
        if verbose:
            print("=" * 70)
            print("  ОРБИТАЛЬНАЯ ДИНАМИКА — Акт V")
            print("  Групповое экранирование")
            print("=" * 70)
            print(f"  Решётка: {self.grid_size}³")
            print(f"  M1={self.body1.mass:.0f}, M2={self.body2.mass:.0f}")
            print(f"  Диполей: {len(self.dipoles)}")
            print("-" * 70)

        self.history.clear()

        for step in range(max_steps):
            self.evolve_step(dt)

            if step % snapshot_interval == 0:
                d12 = self.distance_between_bodies()
                d_d1 = self.distance_to_body1(self.dipoles[0]) if self.dipoles else 0.0
                d_d2 = self.distance_to_body2(self.dipoles[0]) if self.dipoles else 0.0

                self.history.append(OrbitalSnapshot(
                    step=step,
                    body1_position=self.body1.position.copy(),
                    body2_position=self.body2.position.copy(),
                    dipole_position=self.dipoles[0].center.copy() if self.dipoles else np.zeros(3),
                    distance_12=d12,
                    distance_d1=d_d1,
                    distance_d2=d_d2,
                ))

                if verbose:
                    print(
                        f"  Шаг {step:5d} | r12={d12:.2f} | "
                        f"rd1={d_d1:.2f} | rd2={d_d2:.2f}"
                    )

        if verbose:
            print("-" * 70)
            if len(self.history) >= 2:
                r12_initial = self.history[0].distance_12
                r12_final = self.history[-1].distance_12
                print(f"  r12: {r12_initial:.2f} → {r12_final:.2f}")
                print(f"  Орбита {'устойчива' if abs(r12_final - r12_initial) < 2.0 else 'эволюционирует'}")
            print("=" * 70)

        return self.get_summary()

    def get_summary(self) -> Dict:
        if len(self.history) < 2:
            return {'n_snapshots': len(self.history)}

        r12_initial = self.history[0].distance_12
        r12_final = self.history[-1].distance_12
        r12_values = np.array([s.distance_12 for s in self.history])

        return {
            'n_snapshots': len(self.history),
            'r12_initial': r12_initial,
            'r12_final': r12_final,
            'r12_mean': float(np.mean(r12_values)),
            'r12_std': float(np.std(r12_values)),
            'bodies_converged': r12_final < r12_initial,
            'orbit_stable': abs(r12_final - r12_initial) < 2.0,
            'n_dipoles': len(self.dipoles),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    solver = OrbitalSolver(
        grid_size=32,
        mass1=100.0,
        mass2=50.0,
        n_dipoles=3,
        random_seed=42,
    )
    summary = solver.run(max_steps=2000, dt=0.05, verbose=True)

    print("\n📊 СТАТИСТИКА:")
    for k, v in summary.items():
        print(f"   {k}: {v}")