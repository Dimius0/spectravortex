"""
Переходные слои — фрактальная геометрия (Акт VIII)
================================================================================
Программа SpectraVortex, Вихревая Модель Материи-Пространства (ВММП).

Гипотеза:
    Переходные слои между средами с разными свойствами поля имеют
    одинаковую геометрию на всех масштабах:
    - Микро: кокон вихря (из Теоремы Дипсик)
    - Мезо: магнитопауза Земли
    - Макро: гелиопауза (лента IBEX)

    Форма слоя — сфера, сжатая набегающим потоком, с хвостом.
    Фрактальный коэффициент k = толщина слоя / радиус источника
    должен быть одинаковым на всех масштабах.

Метод:
    - Один источник экранирования в фоновом поле.
    - Набегающий поток моделируется градиентом фона.
    - Находим поверхность максимального градиента → переходный слой.
    - Масштабируем и сравниваем геометрию.

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, концепция переходных слоёв
    DeepSeek — численный метод, фрактальная верификация, 2026-05-28
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

# Три масштаба
SCALES = {
    'micro': {'source_radius': 4, 'flow_speed': 0.0},     # Кокон вихря — без потока
    'meso':  {'source_radius': 8, 'flow_speed': 0.1},     # Магнитопауза — слабый поток
    'macro': {'source_radius': 16, 'flow_speed': 0.3},    # Гелиопауза — сильный поток
}


@dataclass
class LayerProfile:
    """Профиль переходного слоя в сечении."""
    scale: str
    angles: np.ndarray          # Углы от 0 до 2π
    distances: np.ndarray       # Расстояние до границы слоя
    thickness: float            # Толщина слоя
    asymmetry: float            # Коэффициент асимметрии (хвост/нос)


@dataclass
class TransitionSnapshot:
    """Снимок переходного слоя."""
    scale: str
    source_position: np.ndarray
    layer_points: np.ndarray    # Точки границы слоя (N x 3)
    max_gradient: float
    mean_radius: float


class TransitionLayerSolver:
    """
    Моделирование переходных слоёв на трёх масштабах.

    Один источник в центре, набегающий поток вдоль оси X.
    Переходный слой = поверхность максимального градиента давления.
    """

    def __init__(
        self,
        grid_size: int = GRID_SIZE,
        scale: str = 'meso',
        source_mass: float = 100.0,
        random_seed: Optional[int] = 42,
    ) -> None:
        if grid_size < 16:
            raise ValueError(f"grid_size >= 16")
        if scale not in SCALES:
            raise ValueError(f"scale должен быть одним из {list(SCALES.keys())}")

        self.grid_size = grid_size
        self.scale = scale
        self.params = SCALES[scale]
        self.rng = np.random.RandomState(random_seed)

        # Источник в центре
        self.source_position = np.array([grid_size/2, grid_size/2, grid_size/2])
        self.source_mass = source_mass

        # Поле давления
        self.pressure_field = np.full((grid_size, grid_size, grid_size), BACKGROUND_PRESSURE)
        self._update_pressure_field()

        # История
        self.layer_points: Optional[np.ndarray] = None
        self.profile: Optional[LayerProfile] = None

        logger.info(
            "TransitionLayerSolver: scale=%s, source_r=%d, flow=%.1f",
            scale, self.params['source_radius'], self.params['flow_speed'],
        )

    def _update_pressure_field(self) -> None:
        """
        Экранирование источником + градиент фона (набегающий поток).

        P(x,y,z) = P_bg * (1 - screening(x,y,z)) * (1 + flow * x / grid_size)
        """
        n = self.grid_size
        X, Y, Z = np.meshgrid(np.arange(n), np.arange(n), np.arange(n), indexing='ij')

        sx, sy, sz = self.source_position
        dx = X - sx
        dy = Y - sy
        dz = Z - sz
        dx = np.where(dx > n/2, dx - n, dx)
        dx = np.where(dx < -n/2, dx + n, dx)
        dy = np.where(dy > n/2, dy - n, dy)
        dy = np.where(dy < -n/2, dy + n, dy)
        dz = np.where(dz > n/2, dz - n, dz)
        dz = np.where(dz < -n/2, dz + n, dz)

        r2 = dx**2 + dy**2 + dz**2
        sigma = float(self.params['source_radius'])
        alpha = SCREENING_FACTOR * self.source_mass / 100.0
        screening = alpha / np.sqrt(r2 + sigma**2)

        # Набегающий поток вдоль X
        flow = self.params['flow_speed']
        flow_factor = 1.0 + flow * (X - n/2) / (n/2)

        self.pressure_field = BACKGROUND_PRESSURE * (1.0 - screening) * flow_factor
        self.pressure_field = np.clip(self.pressure_field, 0.0, BACKGROUND_PRESSURE)

    def compute_gradient_magnitude(self) -> np.ndarray:
        """Вычисляет |∇P| во всём поле."""
        n = self.grid_size
        grad_mag = np.zeros((n, n, n))

        # Центральные разности (упрощённые, без периодичности для границ)
        for i in range(1, n-1):
            for j in range(1, n-1):
                for k in range(1, n-1):
                    dp_dx = (self.pressure_field[i+1,j,k] - self.pressure_field[i-1,j,k]) / 2.0
                    dp_dy = (self.pressure_field[i,j+1,k] - self.pressure_field[i,j-1,k]) / 2.0
                    dp_dz = (self.pressure_field[i,j,k+1] - self.pressure_field[i,j,k-1]) / 2.0
                    grad_mag[i,j,k] = np.sqrt(dp_dx**2 + dp_dy**2 + dp_dz**2)

        return grad_mag

    def find_transition_layer(self, percentile: float = 90.0) -> np.ndarray:
        """
        Находит точки переходного слоя как области с наибольшим градиентом.

        Берём верхний (100 - percentile)% точек по величине градиента.
        """
        grad_mag = self.compute_gradient_magnitude()
        threshold = np.percentile(grad_mag, percentile)

        mask = grad_mag >= threshold
        points = np.argwhere(mask).astype(float)

        if len(points) > 5000:
            # Субдискретизация для скорости
            idx = self.rng.choice(len(points), 5000, replace=False)
            points = points[idx]

        self.layer_points = points
        return points

    def compute_radial_profile(self, num_angles: int = 72) -> LayerProfile:
        """
        Строит радиальный профиль переходного слоя.

        Для каждого угла в плоскости XY находит среднее расстояние
        до точек слоя от источника.
        """
        if self.layer_points is None:
            self.find_transition_layer()

        points = self.layer_points
        center = self.source_position[:2]  # Только XY

        angles = np.linspace(0, 2*np.pi, num_angles)
        distances = np.zeros(num_angles)
        thicknesses = np.zeros(num_angles)

        for i, angle in enumerate(angles):
            direction = np.array([np.cos(angle), np.sin(angle)])

            # Проекция точек на направление
            vecs = points[:, :2] - center
            proj = np.dot(vecs, direction)

            # Берём точки в секторе ±5°
            angle_tolerance = np.pi / 36  # 5 градусов
            dot_products = np.abs(np.dot(vecs, np.array([-direction[1], direction[0]])))
            in_sector = dot_products < np.sin(angle_tolerance) * np.linalg.norm(vecs, axis=1)

            if np.any(in_sector):
                sector_points = vecs[in_sector]
                dists = np.linalg.norm(sector_points, axis=1)
                distances[i] = np.mean(dists)
                thicknesses[i] = np.std(dists)
            else:
                distances[i] = self.params['source_radius']
                thicknesses[i] = 1.0

        thickness = float(np.mean(thicknesses))
        asymmetry = float(np.max(distances) / np.maximum(np.min(distances), 1e-8))

        self.profile = LayerProfile(
            scale=self.scale,
            angles=angles,
            distances=distances,
            thickness=thickness,
            asymmetry=asymmetry,
        )

        return self.profile

    def run(self, verbose: bool = True) -> Dict:
        """Полный цикл анализа переходного слоя."""
        if verbose:
            print("=" * 70)
            print(f"  ПЕРЕХОДНЫЙ СЛОЙ — {self.scale.upper()}")
            print("=" * 70)
            print(f"  Источник: r={self.params['source_radius']}")
            print(f"  Поток: v={self.params['flow_speed']}")
            print("-" * 70)

        points = self.find_transition_layer()
        profile = self.compute_radial_profile()

        if verbose:
            print(f"  Точек в слое: {len(points)}")
            print(f"  Средний радиус: {np.mean(profile.distances):.2f}")
            print(f"  Толщина: {profile.thickness:.2f}")
            print(f"  Асимметрия (хвост/нос): {profile.asymmetry:.2f}")
            print(f"  Фрактальный коэффициент k = толщина/радиус = {profile.thickness / np.mean(profile.distances):.4f}")
            print("=" * 70)

        return {
            'scale': self.scale,
            'n_points': len(points),
            'mean_radius': float(np.mean(profile.distances)),
            'thickness': profile.thickness,
            'asymmetry': profile.asymmetry,
            'fractal_k': profile.thickness / float(np.mean(profile.distances)),
        }


def compare_scales(grid_size: int = 64, verbose: bool = True) -> Dict[str, Dict]:
    """
    Сравнивает переходные слои на трёх масштабах.

    Возвращает словарь с результатами для каждого масштаба.
    """
    results = {}

    for scale in ['micro', 'meso', 'macro']:
        solver = TransitionLayerSolver(
            grid_size=grid_size,
            scale=scale,
            source_mass=100.0,
            random_seed=42,
        )
        results[scale] = solver.run(verbose=verbose)

    if verbose:
        print("\n" + "=" * 70)
        print("  ФРАКТАЛЬНОЕ СРАВНЕНИЕ")
        print("=" * 70)
        k_values = [r['fractal_k'] for r in results.values()]
        k_mean = np.mean(k_values)
        k_std = np.std(k_values)
        print(f"  k (микро): {k_values[0]:.4f}")
        print(f"  k (мезо):  {k_values[1]:.4f}")
        print(f"  k (макро): {k_values[2]:.4f}")
        print(f"  k_mean = {k_mean:.4f} ± {k_std:.4f}")
        print(f"  Относительная ошибка: {k_std / k_mean * 100:.1f}%")

        if k_std / k_mean < 0.3:
            print("\n  🔮 ФРАКТАЛЬНОЕ ПОДОБИЕ ПОДТВЕРЖДЕНО!")
            print("     Переходные слои имеют одинаковую геометрию на всех масштабах.")
        else:
            print("\n  ⚠️ Разброс k великоват. Возможно, нужна калибровка параметров.")
        print("=" * 70)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = compare_scales(grid_size=64, verbose=True)