"""
Навигационный модуль ВММП — Акт VII
================================================================================
Программа SpectraVortex, Вихревая Модель Материи-Пространства (ВММП).

Принцип:
    Корабль не движется механически. Он подстраивает свою массу (экранирование)
    под свойства поля в точке назначения. Поле само переносит корабль в целевую
    точку — потому что топология корабля становится идентичной топологии цели.

Метод:
    1. Датчики измеряют текущее поле (давление, градиент).
    2. Из таблицы известно целевое поле в точке назначения.
    3. Разность ΔP = P_target - P_current → коррекция массы.
    4. Новая масса меняет экранирование → возникает сила приталкивания.
    5. Корабль движется туда, где поле соответствует его массе.

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, концепция навигации
    DeepSeek — численный метод, реализация, 2026-05-27
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
DIPOLE_STRENGTH: float = 1.0
PUSH_FORCE_COEFFICIENT: float = 1.0

# Адаптивная навигация
MASS_ADAPTATION_RATE: float = 2.0  # Скорость подстройки массы
BASELINE: float = 6.0


@dataclass
class NavShip:
    """Корабль с адаптивной массой."""
    position: np.ndarray
    mass: float  # Адаптивная масса — меняется под поле
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self) -> None:
        self.position = self.position.astype(float)
        self.velocity = self.velocity.astype(float)


@dataclass
class FieldSample:
    """Измерение поля в точке."""
    position: np.ndarray
    pressure: float
    gradient: np.ndarray


class NavigationSolver:
    """
    Навигационный модуль: корабль подстраивает массу под целевое поле
    и движется за счёт приталкивания.
    """

    def __init__(
        self,
        grid_size: int = GRID_SIZE,
        source_mass: float = 100.0,
        target_position: Optional[np.ndarray] = None,
        random_seed: Optional[int] = 42,
    ) -> None:
        self.grid_size = grid_size
        self.rng = np.random.RandomState(random_seed)

        # Источник поля (звезда) в центре
        self.source_position = np.array([grid_size/2, grid_size/2, grid_size/2])
        self.source_mass = source_mass

        # Целевая точка — куда летим
        if target_position is None:
            target_position = np.array([grid_size*0.75, grid_size*0.5, grid_size*0.5])
        self.target_position = target_position.astype(float)

        # Корабль — создать ДО обновления поля
        ship_pos = np.array([grid_size*0.2, grid_size*0.3, grid_size*0.5])
        self.ship = NavShip(ship_pos, mass=10.0)

        # Поле давления
        self.pressure_field = np.full((grid_size, grid_size, grid_size), BACKGROUND_PRESSURE)
        self._update_pressure_field()

        # Целевое поле
        self.target_field = self._sample_field_at(self.target_position)

        # История
        self.trajectory: List[np.ndarray] = []
        self.mass_history: List[float] = []
        self.distance_history: List[float] = []

        logger.info(
            "NavigationSolver: источник m=%.0f, цель=%s, корабль m=%.1f",
            source_mass, target_position, self.ship.mass,
        )

    def _update_pressure_field(self) -> None:
        """Поле экранирования от источника И от корабля."""
        n = self.grid_size
        X, Y, Z = np.meshgrid(np.arange(n), np.arange(n), np.arange(n), indexing='ij')

        self.pressure_field.fill(BACKGROUND_PRESSURE)

        # Экранирование источником
        for body_pos, body_mass in [
            (self.source_position, self.source_mass),
            (self.ship.position, self.ship.mass),
        ]:
            dx = X - body_pos[0]
            dy = Y - body_pos[1]
            dz = Z - body_pos[2]
            dx = np.where(dx > n/2, dx - n, dx)
            dx = np.where(dx < -n/2, dx + n, dx)
            dy = np.where(dy > n/2, dy - n, dy)
            dy = np.where(dy < -n/2, dy + n, dy)
            dz = np.where(dz > n/2, dz - n, dz)
            dz = np.where(dz < -n/2, dz + n, dz)

            r2 = dx**2 + dy**2 + dz**2
            sigma = float(SCREENING_RADIUS)
            alpha = SCREENING_FACTOR * body_mass / 100.0
            screening = alpha / np.sqrt(r2 + sigma**2)
            self.pressure_field *= (1.0 - screening)

        self.pressure_field = np.clip(self.pressure_field, 0.0, BACKGROUND_PRESSURE)

    def _sample_field_at(self, pos: np.ndarray) -> FieldSample:
        """Измеряет давление и градиент в заданной точке."""
        n = self.grid_size
        x, y, z = pos % n
        i0, j0, k0 = int(x) % n, int(y) % n, int(z) % n
        i1, j1, k1 = (i0+1)%n, (j0+1)%n, (k0+1)%n
        im, jm, km = (i0-1)%n, (j0-1)%n, (k0-1)%n

        pressure = self._interpolate_pressure(pos)
        gradient = np.array([
            (self.pressure_field[i1,j0,k0] - self.pressure_field[im,j0,k0])/2.0,
            (self.pressure_field[i0,j1,k0] - self.pressure_field[i0,jm,k0])/2.0,
            (self.pressure_field[i0,j0,k1] - self.pressure_field[i0,j0,km])/2.0,
        ])

        return FieldSample(pos.copy(), pressure, gradient)

    def _interpolate_pressure(self, pos: np.ndarray) -> float:
        n = self.grid_size
        x, y, z = pos % n
        i0, j0, k0 = int(np.floor(x))%n, int(np.floor(y))%n, int(np.floor(z))%n
        i1, j1, k1 = (i0+1)%n, (j0+1)%n, (k0+1)%n
        dx, dy, dz = x - np.floor(x), y - np.floor(y), z - np.floor(z)
        c000 = self.pressure_field[i0,j0,k0]; c100 = self.pressure_field[i1,j0,k0]
        c010 = self.pressure_field[i0,j1,k0]; c110 = self.pressure_field[i1,j1,k0]
        c001 = self.pressure_field[i0,j0,k1]; c101 = self.pressure_field[i1,j0,k1]
        c011 = self.pressure_field[i0,j1,k1]; c111 = self.pressure_field[i1,j1,k1]
        return float((c000*(1-dx)+c100*dx)*(1-dy)*(1-dz) +
                     (c010*(1-dx)+c110*dx)*dy*(1-dz) +
                     (c001*(1-dx)+c101*dx)*(1-dy)*dz +
                     (c011*(1-dx)+c111*dx)*dy*dz)

    def _compute_force_on_ship(self) -> np.ndarray:
        """
        Сила приталкивания, действующая на корабль.

        Вычисляется как градиент давления в точке корабля,
        умноженный на массу корабля.
        """
        grad = self._sample_field_at(self.ship.position).gradient
        # Сила = -grad P * mass (приталкивание в сторону меньшего давления)
        # Усиление: корабль чувствует градиент острее
        return -grad * self.ship.mass * PUSH_FORCE_COEFFICIENT * 50.0

    def adapt_mass(self) -> float:
        """
        Подстраивает массу корабля под целевое поле.

        Δm = (P_target - P_current) * adaptation_rate
        """
        current = self._sample_field_at(self.ship.position)
        # dp < 0 если цель ближе к источнику (P_target < P_current)
        dp = self.target_field.pressure - current.pressure
        # Корабль увеличивает массу, чтобы двигаться к меньшему давлению
        delta_m = -dp * MASS_ADAPTATION_RATE * self.source_mass / 100.0
        self.ship.mass += delta_m
        self.ship.mass = max(1.0, min(self.ship.mass, self.source_mass))
        return delta_m

    def evolve_step(self, dt: float = 0.1) -> None:
        """Один шаг навигации."""
        # 1. Измерить текущее поле
        # 2. Подстроить массу
        self.adapt_mass()

        # 3. Обновить поле (масса корабля изменилась)
        self._update_pressure_field()

        # 4. Вычислить силу
        force = self._compute_force_on_ship()

        # 5. Движение под действием силы
        acceleration = force / self.ship.mass
        self.ship.velocity += acceleration * dt
        self.ship.position = (self.ship.position + self.ship.velocity * dt) % self.grid_size

    def run(
        self,
        max_steps: int = 500,
        dt: float = 0.1,
        verbose: bool = True,
        snapshot_interval: int = 50,
    ) -> Dict:
        if verbose:
            print("=" * 70)
            print("  НАВИГАЦИЯ ВММП — Акт VII")
            print("  Адаптивная масса + приталкивание")
            print("=" * 70)
            print(f"  Источник: {self.source_position}")
            print(f"  Цель: {self.target_position}")
            print(f"  Целевое P: {self.target_field.pressure:.4f}")
            print(f"  Старт корабля: {self.ship.position}, m={self.ship.mass:.1f}")
            print("-" * 70)

        self.trajectory.clear()
        self.mass_history.clear()
        self.distance_history.clear()

        for step in range(max_steps):
            self.evolve_step(dt)

            self.trajectory.append(self.ship.position.copy())
            self.mass_history.append(self.ship.mass)

            diff = self.ship.position - self.target_position
            diff = diff - np.round(diff / self.grid_size) * self.grid_size
            dist = float(np.linalg.norm(diff))
            self.distance_history.append(dist)

            if verbose and step % snapshot_interval == 0:
                current = self._sample_field_at(self.ship.position)
                print(
                    f"  Шаг {step:4d} | pos={self.ship.position} | "
                    f"m={self.ship.mass:.2f} | "
                    f"P={current.pressure:.4f} (цель={self.target_field.pressure:.4f}) | "
                    f"dist={dist:.2f}"
                )

        final_dist = self.distance_history[-1]
        orbit_stable = (
            np.std(self.distance_history[-100:]) < 2.0
            if len(self.distance_history) >= 100
            else False
        )

        if verbose:
            print("-" * 70)
            print(f"  Финиш: pos={self.ship.position}, dist={final_dist:.2f}")
            if orbit_stable:
                print("  🔮 НАВИГАЦИЯ УСПЕШНА! Корабль на стабильной орбите.")
            print("=" * 70)

        return {
            'initial_distance': self.distance_history[0],
            'final_distance': final_dist,
            'orbit_stable': orbit_stable,
            'mean_mass': float(np.mean(self.mass_history)),
            'final_mass': self.ship.mass,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    nav = NavigationSolver(
        grid_size=32,
        source_mass=100.0,
        random_seed=42,
    )
    summary = nav.run(max_steps=500, dt=0.1, verbose=True)

    print("\n📊 СТАТИСТИКА:")
    for k, v in summary.items():
        print(f"   {k}: {v}")

    if summary['orbit_stable']:
        print("\n🔮 НАВИГАЦИОННЫЙ МОДУЛЬ ГОТОВ К ПОЛЁТУ!")