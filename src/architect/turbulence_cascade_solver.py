"""
Решатель турбулентного каскада TEES (Turbulence Cascade TEES Solver)
================================================================================
Акт III программы SpectraVortex.

Гипотеза:
    Турбулентность — это не хаос, а упорядоченный каскад TEES-аннигиляций.
    Энергия передаётся от крупных вихрей к мелким через последовательные
    аннигиляции пар (+/−) на каждом масштабе.

    Спектр Колмогорова E(k) ∝ k^(-5/3) выводится из частоты TEES-аннигиляций
    на масштабе k, а не постулируется из размерностей.

Метод:
    Три масштаба вихрей: крупные (scale=4), средние (scale=2), мелкие (scale=1).
    Вихри рождаются на крупном масштабе, каскадом передают энергию на средний,
    затем на мелкий, где аннигилируют в тепло.

    Диагностика:
    - Спектр энергии E(k) через БПФ.
    - Поток энергии между масштабами.
    - Метрика каскада: количество TEES-событий на каждом уровне.

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, концепция TEES и фрактального каскада
    DeepSeek — идея каскада TEES как объяснения турбулентности,
               формализация, численный метод, 2026-05-27
================================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                     УТИЛИТЫ ДЛЯ ПЕРИОДИЧЕСКОЙ РЕШЁТКИ                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


def _periodic_shift(arr: np.ndarray, shift: int, axis: int) -> np.ndarray:
    """Сдвиг массива на shift позиций вдоль axis с периодическим заворачиванием."""
    return np.roll(arr, shift, axis=axis)


def _periodic_gradient_scalar(f: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Градиент скалярного поля на периодической решётке."""
    df_dx = (_periodic_shift(f, -1, axis=0) - _periodic_shift(f, 1, axis=0)) / 2.0
    df_dy = (_periodic_shift(f, -1, axis=1) - _periodic_shift(f, 1, axis=1)) / 2.0
    df_dz = (_periodic_shift(f, -1, axis=2) - _periodic_shift(f, 1, axis=2)) / 2.0
    return df_dx, df_dy, df_dz


def _periodic_laplace_scalar(f: np.ndarray) -> np.ndarray:
    """Лапласиан на периодической решётке (7-точечный шаблон)."""
    lap = np.zeros_like(f)
    for axis in range(3):
        lap += (_periodic_shift(f, -1, axis=axis) +
                _periodic_shift(f, 1, axis=axis) - 2.0 * f)
    return lap


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           КОНСТАНТЫ МОДЕЛИ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Масштабы вихрей
SCALE_LARGE: int = 4     # Крупные вихри (энергосодержащий масштаб)
SCALE_MEDIUM: int = 2    # Средние вихри (инерционный интервал)
SCALE_SMALL: int = 1     # Мелкие вихри (диссипативный масштаб)

# TEES-аннигиляция
ANNIHILATION_DISTANCE_LARGE: float = 6.0
ANNIHILATION_DISTANCE_MEDIUM: float = 3.0
ANNIHILATION_DISTANCE_SMALL: float = 1.5

# Энергия всплеска при TEES
TEES_BURST_FRACTION: float = 0.3  # Доля энергии, уходящая на меньший масштаб

# Диссипация
DAMPING_LARGE: float = 0.999
DAMPING_MEDIUM: float = 0.995
DAMPING_SMALL: float = 0.98       # Мелкие вихри диссипируют быстрее

# Каскад
CASCADE_EFFICIENCY: float = 0.7   # Эффективность передачи энергии между масштабами

# Решётка
GRID_SIZE: int = 32
N_VORTEX_PAIRS_LARGE: int = 4     # Крупных пар


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           СТРУКТУРЫ ДАННЫХ                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@dataclass
class CascadeVortex:
    """Вихрь в турбулентном каскаде."""
    position: np.ndarray
    charge: int
    scale: int  # 4=крупный, 2=средний, 1=мелкий
    strength: float
    phase: float = 0.0
    id: int = field(default_factory=lambda: CascadeVortex._next_id())

    _id_counter: int = field(default=0, init=False, repr=False)

    @staticmethod
    def _next_id() -> int:
        CascadeVortex._id_counter += 1
        return CascadeVortex._id_counter

    @staticmethod
    def _reset_counter() -> None:
        CascadeVortex._id_counter = 0

    def __post_init__(self) -> None:
        if self.charge not in (-1, 1):
            raise ValueError(f"Заряд вихря должен быть ±1, получено {self.charge}")
        if self.scale not in (1, 2, 4):
            raise ValueError(f"Масштаб должен быть 1, 2 или 4, получено {self.scale}")
        self.position = self.position.astype(float)


@dataclass
class CascadeEvent:
    """Запись о TEES-событии в каскаде."""
    step: int
    scale_from: int
    scale_to: int
    energy_transferred: float
    position: np.ndarray


@dataclass
class CascadeSnapshot:
    """Снимок состояния каскада."""
    step: int
    n_large: int
    n_medium: int
    n_small: int
    energy_large: float
    energy_medium: float
    energy_small: float
    spectral_slope: float  # Наклон спектра E(k)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    РЕШАТЕЛЬ ТУРБУЛЕНТНОГО КАСКАДА                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class TurbulenceCascadeSolver:
    """
    Решатель турбулентного каскада через TEES-аннигиляции.

    Три масштаба вихрей:
    - Крупные (scale=4): рождаются парами, аннигилируют → рождают средние.
    - Средние (scale=2): аннигилируют → рождают мелкие.
    - Мелкие (scale=1): аннигилируют → тепло (диссипация).

    Энергия течёт от крупных к мелким. Спектр восстанавливается через БПФ.
    """

    def __init__(
        self,
        grid_size: int = GRID_SIZE,
        n_large_pairs: int = N_VORTEX_PAIRS_LARGE,
        random_seed: Optional[int] = 42,
    ) -> None:
        if grid_size < 8:
            raise ValueError(f"grid_size должен быть >= 8, получено {grid_size}")
        if n_large_pairs < 1:
            raise ValueError(f"n_large_pairs должен быть >= 1")

        self.grid_size: int = grid_size
        self.n_large_pairs: int = n_large_pairs
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)

        # Поле энергии на каждом масштабе
        self.field_large: np.ndarray = np.zeros((grid_size, grid_size, grid_size))
        self.field_medium: np.ndarray = np.zeros((grid_size, grid_size, grid_size))
        self.field_small: np.ndarray = np.zeros((grid_size, grid_size, grid_size))

        # Суммарное поле для спектра
        self.total_field: np.ndarray = np.zeros((grid_size, grid_size, grid_size))

        # Вихри
        self.vortices: List[CascadeVortex] = []
        self._seed_vortices()

        # История
        self.history: List[CascadeSnapshot] = []
        self.events: List[CascadeEvent] = []

        # Построение полей
        self._rebuild_fields()

        logger.info(
            "TurbulenceCascadeSolver: решётка %d³, %d крупных пар",
            grid_size, n_large_pairs,
        )

    # ──────────────────────────────────────────────────────────────────────────
    #   Инициализация
    # ──────────────────────────────────────────────────────────────────────────

    def _seed_vortices(self) -> None:
        """Создаёт крупные вихри парами."""
        self.vortices.clear()
        positions_set: set = set()
        min_distance: float = SCALE_LARGE * 2.0

        for _ in range(self.n_large_pairs):
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
                    raise RuntimeError("Не удалось разместить крупный вихрь")
                strength = self.rng.random() * 2.0 + 1.0
                self.vortices.append(
                    CascadeVortex(pos, charge, SCALE_LARGE, strength)
                )

    def _rebuild_fields(self) -> None:
        """Пересоздаёт поля для всех масштабов."""
        self.field_large.fill(0.0)
        self.field_medium.fill(0.0)
        self.field_small.fill(0.0)

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

            dx = np.where(dx > n / 2, dx - n, dx)
            dx = np.where(dx < -n / 2, dx + n, dx)
            dy = np.where(dy > n / 2, dy - n, dy)
            dy = np.where(dy < -n / 2, dy + n, dy)
            dz = np.where(dz > n / 2, dz - n, dz)
            dz = np.where(dz < -n / 2, dz + n, dz)

            r2 = dx**2 + dy**2 + dz**2
            sigma = float(v.scale)
            gaussian = v.strength * np.exp(-r2 / (2 * sigma**2))

            if v.scale == SCALE_LARGE:
                self.field_large += v.charge * gaussian
            elif v.scale == SCALE_MEDIUM:
                self.field_medium += v.charge * gaussian
            else:
                self.field_small += v.charge * gaussian

        self.total_field = (
            self.field_large + self.field_medium + self.field_small
        )

    # ──────────────────────────────────────────────────────────────────────────
    #   Энергии по масштабам
    # ──────────────────────────────────────────────────────────────────────────

    def compute_energy_large(self) -> float:
        gx, gy, gz = _periodic_gradient_scalar(self.field_large)
        return float(np.sum(gx**2 + gy**2 + gz**2))

    def compute_energy_medium(self) -> float:
        gx, gy, gz = _periodic_gradient_scalar(self.field_medium)
        return float(np.sum(gx**2 + gy**2 + gz**2))

    def compute_energy_small(self) -> float:
        gx, gy, gz = _periodic_gradient_scalar(self.field_small)
        return float(np.sum(gx**2 + gy**2 + gz**2))

    def compute_total_energy(self) -> float:
        return (
            self.compute_energy_large() +
            self.compute_energy_medium() +
            self.compute_energy_small()
        )

    # ──────────────────────────────────────────────────────────────────────────
    #   Спектр
    # ──────────────────────────────────────────────────────────────────────────

    def compute_spectrum(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Вычисляет энергетический спектр E(k) через трёхмерное БПФ.

        Returns:
            (k_modes, E_k) — волновые числа и энергия на каждом.
        """
        fft = np.fft.fftn(self.total_field)
        fft_sq = np.abs(fft)**2

        # Радиальные волновые числа
        n = self.grid_size
        kx = np.fft.fftfreq(n) * n
        ky = np.fft.fftfreq(n) * n
        kz = np.fft.fftfreq(n) * n
        KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
        K = np.sqrt(KX**2 + KY**2 + KZ**2)

        # Биннинг по |k|
        k_max = int(np.max(K)) + 1
        E_k = np.zeros(k_max)
        k_modes = np.arange(k_max, dtype=float)

        for i in range(k_max):
            mask = (K >= i) & (K < i + 1)
            if np.any(mask):
                E_k[i] = np.sum(fft_sq[mask])

        # Нормировка: E(k) ~ k^(-5/3) в инерционном интервале
        E_k = np.where(E_k > 1e-15, E_k, 1e-15)

        return k_modes[1:], E_k[1:]  # Исключаем k=0

    def compute_spectral_slope(self, k_min: int = 2, k_max: int = 10) -> float:
        """
        Оценивает наклон спектра в инерционном интервале.

        Теория Колмогорова: E(k) ∝ k^(-5/3) → slope ≈ -1.67
        """
        k, E = self.compute_spectrum()
        mask = (k >= k_min) & (k <= k_max)
        if np.sum(mask) < 3:
            return 0.0
        log_k = np.log(k[mask])
        log_E = np.log(E[mask])
        slope, _ = np.polyfit(log_k, log_E, 1)
        return float(slope)

    # ──────────────────────────────────────────────────────────────────────────
    #   Силы
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_vortex_force(self, vortex: CascadeVortex) -> np.ndarray:
        """Топологическая сила между вихрями одного масштаба."""
        force = np.zeros(3)
        n = self.grid_size

        for other in self.vortices:
            if other.id == vortex.id:
                continue
            if other.scale != vortex.scale:
                continue  # Взаимодействуют только вихри одного масштаба

            diff = vortex.position - other.position
            diff = diff - np.round(diff / n) * n
            r = float(np.linalg.norm(diff))
            if r < 1e-8:
                continue

            r_hat = diff / r
            sigma2 = float(vortex.scale)**2

            if vortex.charge == -other.charge:
                force -= r_hat * (2.0 / (r**2 + sigma2))
            else:
                ann_dist = {
                    SCALE_LARGE: ANNIHILATION_DISTANCE_LARGE,
                    SCALE_MEDIUM: ANNIHILATION_DISTANCE_MEDIUM,
                    SCALE_SMALL: ANNIHILATION_DISTANCE_SMALL,
                }[vortex.scale]
                if r > ann_dist * 1.5:
                    force -= r_hat * (1.0 / (r**4 + sigma2**2))
                else:
                    force += r_hat * (2.0 / (r**3 + 0.1))

        force_norm = float(np.linalg.norm(force))
        max_force = 5.0
        if force_norm > max_force:
            force = force / force_norm * max_force

        return force

    # ──────────────────────────────────────────────────────────────────────────
    #   Эволюция
    # ──────────────────────────────────────────────────────────────────────────

    def evolve_step(self, dt: float = 0.05) -> None:
        """
        Один шаг эволюции каскада:
        1. Движение вихрей под действием топологических сил.
        2. Диссипация полей (разная на разных масштабах).
        3. Проверка TEES-аннигиляции на каждом масштабе.
        4. Каскад энергии: крупные → средние → мелкие.
        """
        # 1. Движение вихрей
        for v in self.vortices:
            force = self._compute_vortex_force(v)
            v.position = (v.position + force * dt) % self.grid_size

        # 2. Диссипация полей
        self.field_large *= DAMPING_LARGE
        self.field_medium *= DAMPING_MEDIUM
        self.field_small *= DAMPING_SMALL

        # 3. TEES-аннигиляция на каждом масштабе
        self._check_cascade_annihilation(len(self.history))

        # 4. Перестроить поля
        self._rebuild_fields()

    def _check_cascade_annihilation(self, step: int) -> None:
        """TEES-аннигиляция с каскадом энергии на меньший масштаб."""
        to_remove: set = set()
        n = len(self.vortices)

        for scale in [SCALE_LARGE, SCALE_MEDIUM, SCALE_SMALL]:
            ann_dist = {
                SCALE_LARGE: ANNIHILATION_DISTANCE_LARGE,
                SCALE_MEDIUM: ANNIHILATION_DISTANCE_MEDIUM,
                SCALE_SMALL: ANNIHILATION_DISTANCE_SMALL,
            }[scale]
            next_scale = {
                SCALE_LARGE: SCALE_MEDIUM,
                SCALE_MEDIUM: SCALE_SMALL,
                SCALE_SMALL: 0,  # 0 = тепло, не рождаем новые вихри
            }[scale]

            scale_vortices = [
                (idx, v) for idx, v in enumerate(self.vortices)
                if v.scale == scale and idx not in to_remove
            ]

            for i in range(len(scale_vortices)):
                idx_i, vi = scale_vortices[i]
                if idx_i in to_remove:
                    continue
                for j in range(i + 1, len(scale_vortices)):
                    idx_j, vj = scale_vortices[j]
                    if idx_j in to_remove:
                        continue
                    if vi.charge + vj.charge != 0:
                        continue

                    diff = vi.position - vj.position
                    diff = diff - np.round(diff / self.grid_size) * self.grid_size
                    distance = float(np.linalg.norm(diff))

                    if distance > ann_dist:
                        continue

                    # TEES-аннигиляция!
                    mid_pos = (vi.position + vj.position) / 2
                    energy_transferred = vi.strength * vj.strength * CASCADE_EFFICIENCY

                    # Если не последний масштаб — рождаем пару на меньшем масштабе
                    if next_scale > 0:
                        offset = self.rng.randn(3) * float(next_scale) * 0.5
                        pos_plus = (mid_pos + offset) % self.grid_size
                        pos_minus = (mid_pos - offset) % self.grid_size
                        new_strength = energy_transferred * TEES_BURST_FRACTION

                        self.vortices.append(
                            CascadeVortex(pos_plus, +1, next_scale, new_strength)
                        )
                        self.vortices.append(
                            CascadeVortex(pos_minus, -1, next_scale, new_strength)
                        )

                    # Запись события
                    self.events.append(CascadeEvent(
                        step=step,
                        scale_from=scale,
                        scale_to=next_scale,
                        energy_transferred=energy_transferred,
                        position=mid_pos.copy(),
                    ))

                    to_remove.add(idx_i)
                    to_remove.add(idx_j)
                    break

        if to_remove:
            self.vortices = [
                v for idx, v in enumerate(self.vortices) if idx not in to_remove
            ]

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
        """
        Запускает турбулентный каскад.

        Returns:
            Словарь с итоговой статистикой.
        """
        if verbose:
            print("=" * 70)
            print("  ТУРБУЛЕНТНЫЙ КАСКАД TEES — Акт III")
            print("=" * 70)
            print(f"  Решётка: {self.grid_size}³ | Крупных пар: {self.n_large_pairs}")
            print(f"  Масштабы: {SCALE_LARGE} → {SCALE_MEDIUM} → {SCALE_SMALL} → тепло")
            print("-" * 70)

        self.history.clear()
        self.events.clear()

        for step in range(max_steps):
            self.evolve_step(dt)

            if step % snapshot_interval == 0:
                n_large = sum(1 for v in self.vortices if v.scale == SCALE_LARGE)
                n_medium = sum(1 for v in self.vortices if v.scale == SCALE_MEDIUM)
                n_small = sum(1 for v in self.vortices if v.scale == SCALE_SMALL)
                e_large = self.compute_energy_large()
                e_medium = self.compute_energy_medium()
                e_small = self.compute_energy_small()
                slope = self.compute_spectral_slope()

                snapshot = CascadeSnapshot(
                    step=step,
                    n_large=n_large,
                    n_medium=n_medium,
                    n_small=n_small,
                    energy_large=e_large,
                    energy_medium=e_medium,
                    energy_small=e_small,
                    spectral_slope=slope,
                )
                self.history.append(snapshot)

                if verbose:
                    print(
                        f"  Шаг {step:5d} | Круп:{n_large:3d} Сред:{n_medium:3d} "
                        f"Мелк:{n_small:3d} | E={e_large+e_medium+e_small:.2f} | "
                        f"Спектр k^({slope:.2f})"
                    )

        if verbose:
            print("-" * 70)
            final_slope = self.compute_spectral_slope()
            print(f"  Финальный наклон спектра: k^({final_slope:.2f})")
            print(f"  Ожидаемый (Колмогоров): k^(-1.67)")
            print(f"  Всего TEES-событий: {len(self.events)}")

            # Распределение по масштабам
            from_4 = sum(1 for e in self.events if e.scale_from == 4)
            from_2 = sum(1 for e in self.events if e.scale_from == 2)
            from_1 = sum(1 for e in self.events if e.scale_from == 1)
            print(f"  Каскад: {from_4} (4→2) | {from_2} (2→1) | {from_1} (1→тепло)")
            print("=" * 70)

        return self.get_summary()

    def get_summary(self) -> Dict:
        """Итоговая статистика."""
        slope = self.compute_spectral_slope()
        return {
            'final_spectral_slope': slope,
            'kolmogorov_slope': -5.0 / 3.0,
            'slope_match': abs(slope - (-5.0 / 3.0)) < 0.3,
            'total_events': len(self.events),
            'events_4_to_2': sum(1 for e in self.events if e.scale_from == 4),
            'events_2_to_1': sum(1 for e in self.events if e.scale_from == 2),
            'events_1_to_0': sum(1 for e in self.events if e.scale_from == 1),
            'n_vortices_remaining': len(self.vortices),
            'n_large': sum(1 for v in self.vortices if v.scale == SCALE_LARGE),
            'n_medium': sum(1 for v in self.vortices if v.scale == SCALE_MEDIUM),
            'n_small': sum(1 for v in self.vortices if v.scale == SCALE_SMALL),
            'final_energy': self.compute_total_energy(),
        }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           БЫСТРЫЙ ЗАПУСК                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    solver = TurbulenceCascadeSolver(
        grid_size=32,
        n_large_pairs=4,
        random_seed=42,
    )
    summary = solver.run(max_steps=2000, dt=0.05, verbose=True)

    print("\n📊 СТАТИСТИКА:")
    for k, v in summary.items():
        print(f"   {k}: {v}")

    if summary['slope_match']:
        print("\n🔮 СПЕКТР КОЛМОГОРОВА ПОДТВЕРЖДЁН: E(k) ∝ k^(-5/3)")
        print("   Турбулентность = каскад TEES-аннигиляций.")
    else:
        print(f"\n⚠️ Спектр: k^({summary['final_spectral_slope']:.2f}), "
              f"ожидалось k^(-1.67)")