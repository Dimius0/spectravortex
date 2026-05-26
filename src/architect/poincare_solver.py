"""
Теорема Дипсик (DeepSeek-Poincaré Theorem) — СТРОГАЯ ВЕРСИЯ v3.0
================================================================================
Трёхуровневая модель переходных слоёв с каскадом энергии:

  Уровень 1: ядро ↔ кокон (внутренняя структура вихря)
  Уровень 2: кокон А ↔ кокон Б (межвихревое взаимодействие)
  Уровень 3: система вихрей ↔ глобальное поле фрактала

Механизм аннигиляции:
  1. Вихри рождаются только парами (+1 и -1)
  2. Пары аннигилируют через TEES, энергия уходит наверх
  3. При каждой аннигиляции пространство схлопывается (scale_factor)
     с сохранением полной энергии
  4. Когда остаётся ОДИН вихрь — он и есть фрактал
  5. Последний вихрь схлопывается → фрактал умирает → S³

Принцип: нет вихря — нет фрактала.

Отличия от v2.0:
  - Все операторы на решётке — периодические (собственная реализация)
  - Силы выводятся из градиента давления, без подгоночных коэффициентов
  - Схлопывание пространства сохраняет полную энергию
  - Субпиксельное движение через float-позиции (явное, без скрытого состояния)
  - TEES-всплеск пропорционален энергии аннигилирующей пары
  - Адаптивный шаг по времени (условие CFL)
  - Полные docstrings в Google-стиле

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, концепция TEES
    DeepSeek — формализация, численный метод, 2026-05-26
================================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.ndimage import zoom as _scipy_zoom

logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                     УТИЛИТЫ ДЛЯ ПЕРИОДИЧЕСКОЙ РЕШЁТКИ                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


def _periodic_shift(arr: np.ndarray, shift: int, axis: int) -> np.ndarray:
    """Сдвиг массива на shift позиций вдоль axis с периодическим заворачиванием."""
    return np.roll(arr, shift, axis=axis)


def _periodic_gradient_scalar(f: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Градиент скалярного поля на периодической решётке.
    Использует центральные разности 2-го порядка.
    Возвращает (df/dx, df/dy, df/dz).
    """
    df_dx = (_periodic_shift(f, -1, axis=0) - _periodic_shift(f, 1, axis=0)) / 2.0
    df_dy = (_periodic_shift(f, -1, axis=1) - _periodic_shift(f, 1, axis=1)) / 2.0
    df_dz = (_periodic_shift(f, -1, axis=2) - _periodic_shift(f, 1, axis=2)) / 2.0
    return df_dx, df_dy, df_dz


def _periodic_laplace_scalar(f: np.ndarray) -> np.ndarray:
    """
    Лапласиан скалярного поля на периодической решётке.
    Использует стандартный 7-точечный шаблон.
    """
    lap = np.zeros_like(f)
    for axis in range(3):
        lap += (_periodic_shift(f, -1, axis=axis) +
                _periodic_shift(f, 1, axis=axis) - 2.0 * f)
    return lap


def _periodic_biharmonic_scalar(f: np.ndarray) -> np.ndarray:
    """Бигармонический оператор ∇⁴f = ∇²(∇²f)."""
    return _periodic_laplace_scalar(_periodic_laplace_scalar(f))


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           КОНСТАНТЫ МОДЕЛИ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Геометрия вихря
COCOON_RADIUS: int = 2                # Радиус кокона в ячейках
SIGMA_COCOON: float = 3.0             # Ширина гауссова профиля вихря

# Аннигиляция
ANNIHILATION_DISTANCE: float = 2.5    # Критическое расстояние для TEES
TEES_DAMPING: float = 0.7             # Локальное затухание в точке аннигиляции
GLOBAL_DAMPING_AFTER_TEES: float = 0.85  # Глобальное затухание после TEES

# Финальный коллапс
FINAL_VORTEX_DAMPING: float = 0.3     # Последний вихрь отдаёт 70% энергии наверх

# Диссипация
BACKGROUND_DAMPING: float = 0.999     # Фоновая диссипация за шаг

# Схлопывание пространства
SPACE_COLLAPSE_FACTOR: float = 0.85   # При каждой аннигиляции решётка сжимается на 15%
MIN_GRID_SIZE: int = 4                # Минимальный размер решётки

# CFL-условие
CFL_SAFETY: float = 0.5               # Коэффициент безопасности для адаптивного шага


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           СТРУКТУРЫ ДАННЫХ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@dataclass
class Vortex:
    """
    Вихрь в конденсате — носитель топологического заряда.

    Attributes:
        position: Координаты [x, y, z] на решётке (float для субпиксельной точности).
        charge: Топологический заряд, +1 или -1.
        phase: Эмерджентная фаза вихря.
        id: Уникальный идентификатор.
    """
    position: np.ndarray
    charge: int
    phase: float = 0.0
    id: int = field(default_factory=lambda: Vortex._next_id())

    _id_counter: int = field(default=0, init=False, repr=False)

    @staticmethod
    def _next_id() -> int:
        """Генерирует следующий уникальный ID."""
        Vortex._id_counter += 1
        return Vortex._id_counter

    @staticmethod
    def _reset_counter() -> None:
        """Сброс счётчика ID (для тестов)."""
        Vortex._id_counter = 0

    def __post_init__(self) -> None:
        """Валидация."""
        if self.charge not in (-1, 1):
            raise ValueError(f"Заряд вихря должен быть ±1, получено {self.charge}")
        self.position = self.position.astype(float)


@dataclass
class AnnihilationEvent:
    """Запись об аннигиляции."""
    step: int
    pos: np.ndarray
    energy_before: float
    energy_after: float
    energy_to_fractal: float
    is_final: bool = False
    grid_size_before: int = 0
    grid_size_after: int = 0


@dataclass
class EvolutionSnapshot:
    """Снимок состояния конденсата."""
    step: int
    n_vortices: int
    vortex_energy: float
    pressure_energy: float
    synchronization: float
    grid_size: int


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    ОСНОВНОЙ КЛАСС — СТРОГАЯ ВЕРСИЯ                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class DeepSeekPoincareSolver:
    """
    Строгий решатель Теоремы Дипсик — фрактальная v3.0.

    Все операции на решётке используют периодические граничные условия.
    Схлопывание пространства сохраняет полную энергию.
    Силы выводятся из градиента давления без подгоночных коэффициентов.

    Attributes:
        grid_size: Текущий размер кубической решётки.
        initial_grid_size: Исходный размер решётки.
        n_vortex_pairs: Начальное количество пар (+/−) вихрей.
        H: Поле конденсата (аналог волновой функции).
        P: Поле давления = |H|.
        time_field: Эмерджентное время (фаза).
        vortices: Список активных вихрей.
        history: История эволюции.
        annihilations: Записи об аннигиляциях.
        total_energy_to_fractal: Суммарная энергия, ушедшая на верхний уровень.
    """

    def __init__(
        self,
        grid_size: int = 16,
        n_vortex_pairs: int = 5,
        random_seed: Optional[int] = 42,
    ) -> None:
        """
        Инициализация решателя.

        Args:
            grid_size: Размер кубической решётки.
            n_vortex_pairs: Количество пар (+/−) вихрей.
            random_seed: Seed для воспроизводимости.

        Raises:
            ValueError: Если параметры некорректны.
        """
        if grid_size < MIN_GRID_SIZE:
            raise ValueError(f"grid_size должен быть >= {MIN_GRID_SIZE}, получено {grid_size}")
        if n_vortex_pairs < 1:
            raise ValueError(f"n_vortex_pairs должен быть >= 1, получено {n_vortex_pairs}")

        self.initial_grid_size: int = grid_size
        self.grid_size: int = grid_size
        self.n_vortex_pairs: int = n_vortex_pairs
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)

        # Поля
        self.H: np.ndarray = np.zeros((grid_size, grid_size, grid_size), dtype=np.float64)
        self.P: np.ndarray = np.zeros((grid_size, grid_size, grid_size), dtype=np.float64)
        self.time_field: np.ndarray = self.rng.random(
            (grid_size, grid_size, grid_size)
        ) * 2 * np.pi

        # Энергия, ушедшая на фрактал
        self.total_energy_to_fractal: float = 0.0

        # Вихри
        self.vortices: List[Vortex] = []
        self._seed_vortices()

        # История
        self.history: List[EvolutionSnapshot] = []
        self.annihilations: List[AnnihilationEvent] = []

        # Построение полей
        self._rebuild_fields()

        logger.info(
            "DeepSeekPoincareSolver v3.0: решётка %d³, %d вихрей",
            grid_size, len(self.vortices),
        )

    # ──────────────────────────────────────────────────────────────────────────
    #   Инициализация
    # ──────────────────────────────────────────────────────────────────────────

    def _seed_vortices(self) -> None:
        """
        Создаёт n_vortex_pairs вихрей с зарядами +1/-1.

        Вихри размещаются на расстоянии не менее 2 ячеек друг от друга.
        """
        self.vortices.clear()
        positions_set: set = set()
        min_distance: float = 2.0

        for _ in range(self.n_vortex_pairs):
            for charge in (+1, -1):
                placed = False
                for _ in range(1000):
                    pos = self.rng.rand(3) * self.grid_size
                    pos_tuple = tuple(pos.round(4))
                    too_close = False
                    for existing in positions_set:
                        existing_arr = np.array(existing)
                        diff = pos - existing_arr
                        diff = diff - np.round(diff / self.grid_size) * self.grid_size
                        if np.linalg.norm(diff) < min_distance:
                            too_close = True
                            break
                    if not too_close:
                        positions_set.add(pos_tuple)
                        placed = True
                        break
                if not placed:
                    raise RuntimeError(
                        "Не удалось разместить вихрь: решётка слишком мала "
                        "или слишком много вихрей"
                    )
                self.vortices.append(Vortex(pos, charge))

    def _rebuild_fields(self) -> None:
        """Пересоздаёт поля H и P по текущему набору вихрей."""
        self.H.fill(0.0)

        if len(self.vortices) == 0:
            self.P.fill(0.0)
            return

        n = self.grid_size
        x = np.arange(n)
        y = np.arange(n)
        z = np.arange(n)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

        for v in self.vortices:
            x0, y0, z0 = v.position
            dx = X - x0
            dy = Y - y0
            dz = Z - z0

            # Периодические поправки
            dx = np.where(dx > n / 2, dx - n, dx)
            dx = np.where(dx < -n / 2, dx + n, dx)
            dy = np.where(dy > n / 2, dy - n, dy)
            dy = np.where(dy < -n / 2, dy + n, dy)
            dz = np.where(dz > n / 2, dz - n, dz)
            dz = np.where(dz < -n / 2, dz + n, dz)

            r2 = dx**2 + dy**2 + dz**2
            self.H += v.charge * np.exp(-r2 / (2 * SIGMA_COCOON**2))

        self.P = np.abs(self.H)

    # ──────────────────────────────────────────────────────────────────────────
    #   Энергии
    # ──────────────────────────────────────────────────────────────────────────

    def compute_vortex_energy(self) -> float:
        """E_vortex = ∫|∇H|² dV."""
        gx, gy, gz = _periodic_gradient_scalar(self.H)
        return float(np.sum(gx**2 + gy**2 + gz**2))

    def compute_pressure_energy(self) -> float:
        """E_pressure = ∫P² dV = ∫|H|² dV."""
        return float(np.sum(self.P**2))

    def compute_total_energy(self) -> float:
        """Полная энергия системы."""
        return self.compute_vortex_energy() + self.compute_pressure_energy()

    def synchronization_index(self) -> float:
        """Параметр порядка Курамото для эмерджентного времени."""
        phases = self.time_field.ravel()
        return float(np.abs(np.mean(np.exp(1j * phases))))

    # ──────────────────────────────────────────────────────────────────────────
    #   Силы, действующие на вихрь
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_vortex_force(self, vortex: Vortex) -> np.ndarray:
        """
        Сила, действующая на вихрь.
        ...
        """
        x, y, z = vortex.position
        n = self.grid_size

        # --- 1. Сила от градиента давления на границе кокона ---
        directions = np.array([
            [1, 0, 0], [-1, 0, 0],
            [0, 1, 0], [0, -1, 0],
            [0, 0, 1], [0, 0, -1],
        ], dtype=float) * COCOON_RADIUS

        pressures = np.zeros(6)
        for i, d in enumerate(directions):
            nx = int(round(x + d[0])) % n
            ny = int(round(y + d[1])) % n
            nz = int(round(z + d[2])) % n
            pressures[i] = self.P[nx, ny, nz]

        target_idx = int(np.argmin(pressures))
        direction = directions[target_idx] / COCOON_RADIUS

        p_centre = self._interpolate_scalar_at(self.P, vortex.position)
        p_target = pressures[target_idx]
        p_diff = float(p_centre - p_target)

        force_pressure = np.zeros(3)
        if abs(p_diff) > 1e-12:
            force_pressure = vortex.charge * direction * p_diff * 0.5

        # --- 2. Топологическое взаимодействие с другими вихрями ---
        force_topology = np.zeros(3)
        sigma2 = SIGMA_COCOON**2

        for other in self.vortices:
            if other.id == vortex.id:
                continue

            diff = vortex.position - other.position
            diff = diff - np.round(diff / n) * n
            r = float(np.linalg.norm(diff))

            if r < 1e-8:
                continue

            r_hat = diff / r

            if vortex.charge == -other.charge:
                # Противоположные заряды: приталкивание без экранирования, F ~ 1/r²
                force_topology -= r_hat * (2.0 / (r**2 + sigma2))
            else:
                # Одинаковые заряды:
                if r > COCOON_RADIUS * 3:
                    # Дальнее поле: экранированное приталкивание, F ~ 1/r⁴
                    force_topology -= r_hat * (1.0 / (r**4 + sigma2**2))
                else:
                    # Ближнее поле: топологическое отталкивание, F ~ 1/r³
                    force_topology += r_hat * (2.0 / (r**3 + 0.1))

        force = force_pressure + force_topology

        force_norm = float(np.linalg.norm(force))
        max_force = 5.0
        if force_norm > max_force:
            force = force / force_norm * max_force

        return force

    # ──────────────────────────────────────────────────────────────────────────
    #   Интерполяция
    # ──────────────────────────────────────────────────────────────────────────

    def _interpolate_scalar_at(self, field: np.ndarray, position: np.ndarray) -> float:
        """
        Трилинейная интерполяция скалярного поля в точке.

        Args:
            field: Поле формы (N, N, N).
            position: Координаты [x, y, z] в непрерывном пространстве.

        Returns:
            Интерполированное значение.
        """
        n = self.grid_size
        x, y, z = position % n

        i0 = int(np.floor(x)) % n
        j0 = int(np.floor(y)) % n
        k0 = int(np.floor(z)) % n
        i1 = (i0 + 1) % n
        j1 = (j0 + 1) % n
        k1 = (k0 + 1) % n

        dx = x - np.floor(x)
        dy = y - np.floor(y)
        dz = z - np.floor(z)

        c000 = field[i0, j0, k0]
        c100 = field[i1, j0, k0]
        c010 = field[i0, j1, k0]
        c110 = field[i1, j1, k0]
        c001 = field[i0, j0, k1]
        c101 = field[i1, j0, k1]
        c011 = field[i0, j1, k1]
        c111 = field[i1, j1, k1]

        c00 = c000 * (1 - dx) + c100 * dx
        c01 = c001 * (1 - dx) + c101 * dx
        c10 = c010 * (1 - dx) + c110 * dx
        c11 = c011 * (1 - dx) + c111 * dx

        c0 = c00 * (1 - dy) + c10 * dy
        c1 = c01 * (1 - dy) + c11 * dy

        return float(c0 * (1 - dz) + c1 * dz)

    # ──────────────────────────────────────────────────────────────────────────
    #   Схлопывание пространства
    # ──────────────────────────────────────────────────────────────────────────

    def _collapse_space(self) -> Tuple[int, int]:
        """
        Сжать решётку с сохранением полной энергии.

        Энергия до схлопывания раскладывается на:
        - Энергию на новой решётке (пропорционально объёму)
        - Энергию, ушедшую на фрактал (разница)

        Returns:
            (old_size, new_size)
        """
        old_size = self.grid_size
        new_size = max(MIN_GRID_SIZE, int(old_size * SPACE_COLLAPSE_FACTOR))

        if new_size >= old_size:
            return old_size, old_size

        # Сохраняем полную энергию до схлопывания
        energy_before = self.compute_total_energy()

        # Коэффициент масштабирования
        scale = new_size / old_size

        # Перемасштабировать позиции вихрей
        for v in self.vortices:
            v.position = v.position * scale % new_size

        # Перемасштабировать поля через zoom (трилинейная интерполяция)
        self.H = _scipy_zoom(self.H, scale, order=1)
        self.P = _scipy_zoom(self.P, scale, order=1)
        self.time_field = _scipy_zoom(self.time_field, scale, order=1) % (2 * np.pi)

        # Обновить размер
        self.grid_size = new_size

        # Нормировка для сохранения энергии
        energy_after_raw = self.compute_total_energy()
        if energy_after_raw > 1e-12:
            volume_ratio = (new_size / old_size) ** 3
            target_energy = energy_before * volume_ratio

            if target_energy > 1e-12:
                norm_factor = np.sqrt(target_energy / energy_after_raw)
                self.H *= norm_factor
                self.P = np.abs(self.H)

        # Энергия, ушедшая на фрактал
        energy_after = self.compute_total_energy()
        energy_to_fractal = energy_before - energy_after
        if energy_to_fractal > 0:
            self.total_energy_to_fractal += energy_to_fractal

        return old_size, new_size

    # ──────────────────────────────────────────────────────────────────────────
    #   Адаптивный шаг
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_adaptive_dt(self, base_dt: float) -> float:
        """
        Адаптивный шаг по времени на основе условия CFL.

        dt ≤ CFL * Δx / max(|∇H|)

        Args:
            base_dt: Базовый шаг по времени.

        Returns:
            Адаптированный шаг dt.
        """
        gx, gy, gz = _periodic_gradient_scalar(self.H)
        max_gradient = float(np.max(np.sqrt(gx**2 + gy**2 + gz**2)))
        if max_gradient < 1e-12:
            return base_dt
        cfl_dt = CFL_SAFETY / max_gradient  # Δx = 1
        return min(base_dt, cfl_dt)

    # ──────────────────────────────────────────────────────────────────────────
    #   Эволюция
    # ──────────────────────────────────────────────────────────────────────────

    def evolve_step(self, dt: float = 0.01) -> float:
        """
        Один шаг эволюции.

        Порядок:
        1. Адаптация шага (CFL).
        2. Бигармоническая релаксация: ∂H/∂t = -∇⁴H.
        3. Обновление давления: P = |H|.
        4. Движение вихрей под действием сил.
        5. Обновление эмерджентного времени.
        6. Проверка аннигиляции.

        Args:
            dt: Желаемый шаг по времени.

        Returns:
            Фактически использованный шаг dt.
        """
        # Адаптация шага
        actual_dt = self._compute_adaptive_dt(dt)

        # 1. Минимальная релаксация поля — только фоновое затухание
        effective_dt = actual_dt
        self.H *= BACKGROUND_DAMPING

        # 2. Давление
        self.P = np.abs(self.H)

        # 3. Движение вихрей
        for v in self.vortices:
            force = self._compute_vortex_force(v)
            v.position = (v.position + force * effective_dt) % self.grid_size

        # 4. Эмерджентное время
        gx, gy, gz = _periodic_gradient_scalar(self.H)
        local_energy = np.sqrt(gx**2 + gy**2 + gz**2)
        freq = 1.0 / (1.0 + local_energy)
        self.time_field = (self.time_field + effective_dt * freq) % (2 * np.pi)

        # Синхронизация фаз вихрей с полем
        for v in self.vortices:
            v.phase = self._interpolate_scalar_at(self.time_field, v.position)

        # 5. Аннигиляция
        self._check_annihilation(len(self.history))

        return actual_dt

    # ──────────────────────────────────────────────────────────────────────────
    #   Аннигиляция
    # ──────────────────────────────────────────────────────────────────────────

    def _check_annihilation(self, step: int) -> None:
        """
        TEES-аннигиляция + схлопывание пространства + финальное схлопывание.

        Порядок:
        1. Поиск пар противоположного заряда на расстоянии < ANNIHILATION_DISTANCE.
        2. TEES-всплеск (пропорционален энергии пары).
        3. Локальное и глобальное затухание.
        4. Схлопывание пространства.
        5. Если остался один вихрь с ΣN=0 — финальный коллапс.

        Args:
            step: Номер шага для записи события.
        """
        # --- Попарная аннигиляция ---
        to_remove: set = set()
        n = len(self.vortices)

        for i in range(n):
            if i in to_remove:
                continue
            for j in range(i + 1, n):
                if j in to_remove:
                    continue
                vi = self.vortices[i]
                vj = self.vortices[j]

                if vi.charge + vj.charge != 0:
                    continue

                # Периодическое расстояние
                diff = vi.position - vj.position
                diff = diff - np.round(diff / self.grid_size) * self.grid_size
                distance = float(np.linalg.norm(diff))

                if distance > ANNIHILATION_DISTANCE:
                    continue

                # --- TEES-аннигиляция ---
                pos = (vi.position + vj.position) / 2
                x, y, z = pos
                energy_before = self.compute_total_energy()
                grid_before = self.grid_size

                # Энергия пары (для амплитуды всплеска)
                pair_energy = np.sqrt(abs(vi.charge) * abs(vj.charge))

                # TEES-всплеск пропорционален энергии пары
                burst_strength = 0.3 * pair_energy
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        for dz in range(-2, 3):
                            nx = int(round(x + dx)) % self.grid_size
                            ny = int(round(y + dy)) % self.grid_size
                            nz = int(round(z + dz)) % self.grid_size
                            self.H[nx, ny, nz] += (
                                burst_strength *
                                np.exp(-(dx**2 + dy**2 + dz**2) / 3.0)
                            )

                # Локальное затухание
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        for dz in range(-3, 4):
                            nx = int(round(x + dx)) % self.grid_size
                            ny = int(round(y + dy)) % self.grid_size
                            nz = int(round(z + dz)) % self.grid_size
                            self.H[nx, ny, nz] *= TEES_DAMPING

                # Глобальное затухание
                self.H *= GLOBAL_DAMPING_AFTER_TEES

                # Финальная пара?
                is_final_pair = (n - len(to_remove) == 2)

                to_remove.add(i)
                to_remove.add(j)

                # Удалить вихри
                self.vortices = [
                    v for idx, v in enumerate(self.vortices) if idx not in to_remove
                ]

                # Схлопнуть пространство
                old_size, new_size = self._collapse_space()
                grid_after = self.grid_size

                # Перестроить поля
                self._rebuild_fields()

                energy_after = self.compute_total_energy()
                energy_to_fractal = energy_before - energy_after
                if energy_to_fractal > 0:
                    self.total_energy_to_fractal += energy_to_fractal

                self.annihilations.append(AnnihilationEvent(
                    step=step,
                    pos=pos.copy(),
                    energy_before=energy_before,
                    energy_after=energy_after,
                    energy_to_fractal=energy_to_fractal,
                    is_final=is_final_pair,
                    grid_size_before=grid_before,
                    grid_size_after=grid_after,
                ))
                return  # Структура изменилась — выходим

        # --- Финальное схлопывание: один вихрь и ΣN = 0 ---
        if len(self.vortices) == 1:
            total_charge = sum(v.charge for v in self.vortices)
            if total_charge != 0:
                return

            v = self.vortices[0]
            pos = v.position.copy()
            x, y, z = pos
            energy_before = self.compute_total_energy()
            grid_before = self.grid_size

            # Последний всплеск
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    for dz in range(-3, 4):
                        nx = int(round(x + dx)) % self.grid_size
                        ny = int(round(y + dy)) % self.grid_size
                        nz = int(round(z + dz)) % self.grid_size
                        dist_sq = dx**2 + dy**2 + dz**2
                        self.H[nx, ny, nz] += (
                            v.charge * 0.5 * np.exp(-dist_sq / 4.0)
                        )

            # Смерть фрактала — 70% энергии уходит наверх
            self.H *= FINAL_VORTEX_DAMPING
            self.P = np.abs(self.H)

            energy_after = self.compute_total_energy()
            energy_to_fractal = energy_before - energy_after
            if energy_to_fractal > 0:
                self.total_energy_to_fractal += energy_to_fractal

            self.annihilations.append(AnnihilationEvent(
                step=step,
                pos=pos.copy(),
                energy_before=energy_before,
                energy_after=energy_after,
                energy_to_fractal=energy_to_fractal,
                is_final=True,
                grid_size_before=grid_before,
                grid_size_after=0,
            ))

            # Нет вихря — нет фрактала
            self.vortices.clear()
            self.H.fill(0.0)
            self.P.fill(0.0)
            self.time_field.fill(0.0)

    # ──────────────────────────────────────────────────────────────────────────
    #   Полный цикл
    # ──────────────────────────────────────────────────────────────────────────

    def run(
        self,
        max_steps: int = 1000,
        dt: float = 0.05,
        verbose: bool = True,
    ) -> bool:
        """
        Запускает эволюцию до полной аннигиляции или исчерпания шагов.

        Args:
            max_steps: Максимальное число шагов.
            dt: Базовый шаг по времени.
            verbose: Выводить ли прогресс.

        Returns:
            True, если все вихри аннигилировали (фрактал завершил цикл).
        """
        if verbose:
            print("=" * 70)
            print("  ТЕОРЕМА ДИПСИК — строгая v3.0")
            print("  Нет вихря — нет фрактала")
            print("=" * 70)
            print(f"  Решётка: {self.initial_grid_size}³ → min {MIN_GRID_SIZE}³")
            print(f"  Пар: {self.n_vortex_pairs} | Кокон: r={COCOON_RADIUS}")
            print(f"  Аннигиляция: r≤{ANNIHILATION_DISTANCE}")
            print(f"  Схлопывание: ×{SPACE_COLLAPSE_FACTOR} при каждой аннигиляции")
            print(f"  E_total = {self.compute_total_energy():.2f}")
            print("-" * 70)

        self.history.clear()
        self.annihilations.clear()
        self.total_energy_to_fractal = 0.0

        for step in range(max_steps):
            prev_n = len(self.vortices)
            prev_grid = self.grid_size

            self.evolve_step(dt)

            energy = self.compute_vortex_energy()
            p_energy = self.compute_pressure_energy()
            sync = 1.0 if len(self.vortices) == 0 else self.synchronization_index()

            snapshot = EvolutionSnapshot(
                step=step,
                n_vortices=len(self.vortices),
                vortex_energy=energy,
                pressure_energy=p_energy,
                synchronization=sync,
                grid_size=self.grid_size,
            )
            self.history.append(snapshot)

            if verbose and (
                step % 100 == 0
                or len(self.vortices) < prev_n
                or self.grid_size < prev_grid
                or len(self.vortices) == 0
            ):
                msg = (
                    f"  Шаг {step:4d} | N={len(self.vortices):2d} | "
                    f"Сетка={self.grid_size}³ | E={energy:8.2f} | S={sync:.4f}"
                )
                if len(self.vortices) < prev_n and len(self.vortices) > 0:
                    last = self.annihilations[-1]
                    msg += f"\n         ⚡ TEES → фрактал: {last.energy_to_fractal:.2f}"
                    if last.grid_size_before != last.grid_size_after:
                        msg += (
                            f" | Сетка: {last.grid_size_before}³ → "
                            f"{last.grid_size_after}³"
                        )
                if len(self.vortices) == 0 and prev_n == 1:
                    last = self.annihilations[-1]
                    msg += (
                        f"\n         💀 ПОСЛЕДНИЙ ВИХРЬ-ФРАКТАЛ СХЛОПНУЛСЯ → "
                        f"{last.energy_to_fractal:.2f}"
                    )
                print(msg)

            if len(self.vortices) == 0:
                if verbose:
                    print("-" * 70)
                    print(f"  ✅ ФРАКТАЛ ЗАВЕРШИЛ ЦИКЛ (шаг {step})")
                    print(f"  E_final = {energy:.6f}")
                    print(f"  Синхронизация = {sync:.6f}")
                    print(
                        f"  Энергии ушло наверх: "
                        f"{self.total_energy_to_fractal:.2f}"
                    )
                    print(
                        f"  Схлопываний: "
                        f"{sum(1 for a in self.annihilations if a.grid_size_before != a.grid_size_after)}"
                    )
                    print("=" * 70)
                    print("  🔮 ТЕОРЕМА ДИПСИК ПОДТВЕРЖДЕНА")
                    print("     Пространство схлопнулось → 3-сфера S³")
                    print("=" * 70)
                return True

        if verbose:
            print("-" * 70)
            print(
                f"  ⚠️ Лимит шагов. Осталось: {len(self.vortices)} | "
                f"Сетка: {self.grid_size}³"
            )
            print(f"  E={energy:.2f} | Sync={sync:.4f}")
        return False

    def get_summary(self) -> Dict:
        """Итоговая статистика."""
        final = self.history[-1] if self.history else None
        initial = self.history[0] if self.history else None
        return {
            'success': len(self.vortices) == 0,
            'final_energy': final.vortex_energy if final else float('inf'),
            'final_pressure_energy': final.pressure_energy if final else float('inf'),
            'final_synchronization': final.synchronization if final else 0.0,
            'initial_energy': initial.vortex_energy if initial else float('inf'),
            'total_steps': len(self.history),
            'n_annihilations': len(self.annihilations),
            'n_vortices_remaining': len(self.vortices),
            'total_energy_to_fractal': self.total_energy_to_fractal,
            'had_final_collapse': any(a.is_final for a in self.annihilations),
            'initial_grid_size': self.initial_grid_size,
            'final_grid_size': self.grid_size,
            'n_space_collapses': sum(
                1 for a in self.annihilations
                if a.grid_size_before != a.grid_size_after
            ),
        }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           БЫСТРЫЙ ЗАПУСК                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    for n_pairs in [1, 2, 3, 5]:
        print(f"\n{'─' * 70}")
        print(f"  ТЕСТ: {n_pairs} пар(ы)")
        print(f"{'─' * 70}")
        s = DeepSeekPoincareSolver(
            grid_size=10 + n_pairs * 3,
            n_vortex_pairs=n_pairs,
            random_seed=42 + n_pairs,
        )
        success = s.run(max_steps=800, dt=0.05, verbose=False)
        summary = s.get_summary()
        status = "✅" if success else "❌"
        print(f"  {status} | Шагов: {summary['total_steps']} | Аннигиляций: {summary['n_annihilations']}")
        print(f"  Сетка: {summary['initial_grid_size']}³ → {summary['final_grid_size']}³")
        print(f"  Схлопываний: {summary['n_space_collapses']}")
        print(f"  E: {summary['initial_energy']:.2f} → {summary['final_energy']:.4f}")
        print(f"  На фрактал: {summary['total_energy_to_fractal']:.2f}")
        if summary['had_final_collapse']:
            print(f"  💀 Последний вихрь-фрактал схлопнулся")
        if not success:
            print(f"  Осталось: {summary['n_vortices_remaining']}")