"""
Эпициклы через возмущение поля (Акт VI)
================================================================================
Программа SpectraVortex, Вихревая Модель Материи-Пространства (ВММП).

Гипотеза:
    Эпициклы — не математический костыль Птолемея, а естественное следствие
    движения диполя в суперпозиции полей экранирования от двух тел.

    Когда диполь вращается вокруг основного тела, а второе тело возмущает
    поле, траектория диполя образует петли — эпициклы.

Метод:
    - Основное тело (звезда) в центре.
    - Второе тело (планета-гигант) на орбите вокруг основного.
    - Диполь (пробная частица) на орбите вокруг основного тела.
    - Траектория диполя возмущается вторым телом → петли.

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, концепция приталкивания
    DeepSeek — численный метод, эпициклы, 2026-05-27
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

GRID_SIZE: int = 64
BACKGROUND_PRESSURE: float = 1.0
SCREENING_FACTOR: float = 0.1
SCREENING_RADIUS: int = 4
DIPOLE_SEPARATION: float = 2.0
DIPOLE_STRENGTH: float = 1.0
PUSH_FORCE_COEFFICIENT: float = 1.0


@dataclass
class EpicycleBody:
    """Массивное тело."""
    position: np.ndarray
    mass: float
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self) -> None:
        self.position = self.position.astype(float)
        self.velocity = self.velocity.astype(float)


@dataclass
class EpicycleDipole:
    """Вихревой диполь — пробная частица."""
    pos_plus: np.ndarray
    pos_minus: np.ndarray
    strength: float = DIPOLE_STRENGTH
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    trajectory: List[np.ndarray] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.pos_plus = self.pos_plus.astype(float)
        self.pos_minus = self.pos_minus.astype(float)
        self.velocity = self.velocity.astype(float)

    @property
    def center(self) -> np.ndarray:
        return (self.pos_plus + self.pos_minus) / 2.0


@dataclass
class EpicycleSnapshot:
    """Снимок для анализа эпициклов."""
    step: int
    dipole_x: float
    dipole_y: float
    body2_x: float
    body2_y: float


class EpicycleSolver:
    """
    Моделирование эпициклов через возмущение поля.

    Два тела + диполь. Диполь на орбите вокруг тела 1.
    Тело 2 возмущает поле → траектория диполя образует петли.
    """

    def __init__(
        self,
        grid_size: int = GRID_SIZE,
        mass_primary: float = 200.0,
        mass_secondary: float = 50.0,
        random_seed: Optional[int] = 42,
    ) -> None:
        if grid_size < 16:
            raise ValueError(f"grid_size >= 16")

        self.grid_size: int = grid_size
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)

        # Основное тело в центре
        self.body1: EpicycleBody = EpicycleBody(
            position=np.array([grid_size/2, grid_size/2, grid_size/2]),
            mass=mass_primary,
        )

        # Второе тело на орбите
        orbit_radius = grid_size / 6.0
        self.body2: EpicycleBody = EpicycleBody(
            position=np.array([
                grid_size/2 + orbit_radius,
                grid_size/2,
                grid_size/2,
            ]),
            mass=mass_secondary,
            velocity=np.array([0.0, 0.3, 0.0]),  # Тангенциальная скорость
        )

        # Диполь на орбите вокруг основного тела
        dipole_orbit = grid_size / 8.0
        pos_center = np.array([
            grid_size/2 + dipole_orbit,
            grid_size/2,
            grid_size/2,
        ])
        direction = np.array([0.0, 1.0, 0.0])
        half_sep = DIPOLE_SEPARATION / 2.0
        self.dipole: EpicycleDipole = EpicycleDipole(
            pos_plus=pos_center + direction * half_sep,
            pos_minus=pos_center - direction * half_sep,
            velocity=np.array([0.0, 0.5, 0.0]),
        )

        self.pressure_field: np.ndarray = np.full(
            (grid_size, grid_size, grid_size), BACKGROUND_PRESSURE
        )

        self.history: List[EpicycleSnapshot] = []
        self._update_pressure_field()

        logger.info(
            "EpicycleSolver: решётка %d³, M1=%.0f, M2=%.0f",
            grid_size, mass_primary, mass_secondary,
        )

    def _update_pressure_field(self) -> None:
        """Суперпозиция экранирований."""
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
            alpha = SCREENING_FACTOR * body.mass / 200.0
            screening = alpha / np.sqrt(r2 + sigma**2)
            self.pressure_field *= (1.0 - screening)

        self.pressure_field = np.clip(self.pressure_field, 0.0, BACKGROUND_PRESSURE)

    def _compute_pressure_gradient(self, pos: np.ndarray) -> np.ndarray:
        n = self.grid_size
        x, y, z = pos % n
        i0, j0, k0 = int(x) % n, int(y) % n, int(z) % n
        i1, j1, k1 = (i0+1)%n, (j0+1)%n, (k0+1)%n
        i_m1, j_m1, k_m1 = (i0-1)%n, (j0-1)%n, (k0-1)%n
        dp_dx = (self.pressure_field[i1,j0,k0] - self.pressure_field[i_m1,j0,k0])/2.0
        dp_dy = (self.pressure_field[i0,j1,k0] - self.pressure_field[i0,j_m1,k0])/2.0
        dp_dz = (self.pressure_field[i0,j0,k1] - self.pressure_field[i0,j0,k_m1])/2.0
        return np.array([dp_dx, dp_dy, dp_dz])

    def compute_force_on_body(self, body: EpicycleBody, other: EpicycleBody) -> np.ndarray:
        diff = body.position - other.position
        diff = diff - np.round(diff / self.grid_size) * self.grid_size
        r = float(np.linalg.norm(diff))
        if r < 1e-8:
            return np.zeros(3)
        r_hat = diff / r
        force_mag = PUSH_FORCE_COEFFICIENT * other.mass / (r**2 + 1.0)
        return -r_hat * force_mag

    def compute_push_force(self, dipole: EpicycleDipole) -> np.ndarray:
        grad_p_plus = self._compute_pressure_gradient(dipole.pos_plus)
        grad_p_minus = self._compute_pressure_gradient(dipole.pos_minus)
        force_plus = -grad_p_plus * dipole.strength
        force_minus = +grad_p_minus * dipole.strength
        return force_plus + force_minus

    def evolve_step(self, dt: float = 0.05) -> None:
        # Силы на тела
        f12 = self.compute_force_on_body(self.body1, self.body2)
        f21 = self.compute_force_on_body(self.body2, self.body1)

        self.body1.velocity += f12 / self.body1.mass * dt
        self.body2.velocity += f21 / self.body2.mass * dt
        self.body1.position = (self.body1.position + self.body1.velocity*dt) % self.grid_size
        self.body2.position = (self.body2.position + self.body2.velocity*dt) % self.grid_size

        self._update_pressure_field()

        # Сила на диполь
        force_d = self.compute_push_force(self.dipole)
        self.dipole.velocity += force_d / self.dipole.strength * dt
        self.dipole.pos_plus = (self.dipole.pos_plus + self.dipole.velocity*dt) % self.grid_size
        self.dipole.pos_minus = (self.dipole.pos_minus + self.dipole.velocity*dt) % self.grid_size

    def run(
        self,
        max_steps: int = 5000,
        dt: float = 0.05,
        verbose: bool = True,
        snapshot_interval: int = 10,
    ) -> Dict:
        if verbose:
            print("=" * 70)
            print("  ЭПИЦИКЛЫ — Акт VI")
            print("  Возмущение орбиты диполя вторым телом")
            print("=" * 70)
            print(f"  Решётка: {self.grid_size}³")
            print(f"  M1={self.body1.mass:.0f}, M2={self.body2.mass:.0f}")
            print("-" * 70)

        self.history.clear()

        for step in range(max_steps):
            self.evolve_step(dt)

            if step % snapshot_interval == 0:
                c = self.dipole.center
                self.dipole.trajectory.append(c.copy())

                self.history.append(EpicycleSnapshot(
                    step=step,
                    dipole_x=float(c[0]),
                    dipole_y=float(c[1]),
                    body2_x=float(self.body2.position[0]),
                    body2_y=float(self.body2.position[1]),
                ))

        if verbose:
            # Анализ траектории на петли
            if len(self.dipole.trajectory) >= 3:
                traj = np.array(self.dipole.trajectory)
                # Считаем пересечения траектории самой себя
                n_loops = self._count_loops(traj)
                print(f"  Шагов: {max_steps} | Точек: {len(traj)} | Петель: {n_loops}")
                if n_loops > 0:
                    print("  🔮 ЭПИЦИКЛЫ ОБНАРУЖЕНЫ!")
            print("=" * 70)

        return self.get_summary()

    def _count_loops(self, traj: np.ndarray) -> int:
        """Подсчитывает число петель в 2D проекции траектории."""
        n = len(traj)
        if n < 20:
            return 0

        # Ищем смену знака векторного произведения последовательных сегментов
        loops = 0
        for i in range(1, n - 1):
            v1 = traj[i] - traj[i-1]
            v2 = traj[i+1] - traj[i]
            cross = v1[0]*v2[1] - v1[1]*v2[0]
            if i > 1:
                v0 = traj[i-1] - traj[i-2]
                cross_prev = v0[0]*v1[1] - v0[1]*v1[0]
                if cross_prev * cross < 0 and abs(cross) > 0.01:
                    loops += 1

        return loops // 2  # Каждая петля даёт два пересечения

    def get_summary(self) -> Dict:
        if len(self.dipole.trajectory) < 3:
            return {'n_points': len(self.dipole.trajectory)}

        traj = np.array(self.dipole.trajectory)
        n_loops = self._count_loops(traj)

        return {
            'n_steps': len(self.history),
            'n_points': len(traj),
            'n_loops': n_loops,
            'epicycles_detected': n_loops > 0,
            'mean_radius': float(np.mean(np.linalg.norm(
                traj[:, :2] - np.array([self.grid_size/2, self.grid_size/2]), axis=1
            ))),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    solver = EpicycleSolver(grid_size=64, mass_primary=200.0, mass_secondary=50.0, random_seed=42)
    summary = solver.run(max_steps=5000, dt=0.05, verbose=True)
    print("\n📊 СТАТИСТИКА:")
    for k, v in summary.items():
        print(f"   {k}: {v}")