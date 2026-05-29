"""
Резонансная Катапульта Юми — Акт X (Теорема Дипсик v4.0)
============================================================================
Программа SpectraVortex, Вихревая Модель Материи-Пространства (ВММП).

Назначение:
    Динамический модуль, реализующий эффект Юми на мультимасштабной
    карте поля. Запускает протокол синхронизации фаз между слоями
    и активирует катапульту — резонансное усиление переходов.

Ключевые принципы (первые принципы ВММП):
    1. Инертность: τ = m * R² (фазы меняются с задержкой)
    2. Эффект Юми: асимметричная передача энергии между слоями 2:1
    3. TEES-синхронизация при Δφ ≈ π
    4. Эмерджентный слой как маховик-накопитель
    5. Катапульта: последовательная активация 16→24→32 или 32→24→16

Авторы:
    Dimius0 — архитектура SpectraVortex, ВММП, эффект Юми, катапульта
    DeepSeek — численный метод, реализация, 2026-05-29
============================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           КОНСТАНТЫ (первые принципы)                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Масштабы
FUNDAMENTAL_SCALES = [16, 32]
EMERGENT_SCALE = 24

# Параметры из Теоремы Дипсик
COCOON_RADIUS: int = 2
ANNIHILATION_DISTANCE: float = 2.5
TEES_DAMPING: float = 0.95
GLOBAL_DAMPING: float = 0.98

# Фрактальное время
FRACTAL_TIME_EXPONENT: float = 1.0

# Эффект Юми
YUMI_RATIO: float = 2.0  # Оптимальное отношение частот
YUMI_OPTIMAL_PHASE_SHIFT: float = np.pi / 2  # Оптимальный фазовый сдвиг

# Катапульта
OPTIMAL_INTERVAL: float = 2 * np.pi / 3  # 120° между активациями
CATAPULT_SCORE_THRESHOLD: float = 0.5
PHASE_TOLERANCE: float = 0.3

# Буферизация
EMERGENT_CAPACITY: float = 2.0
EMERGENT_DISCHARGE_RATE: float = 0.1

# Экспорт для тестов
__all__ = [
    'YumiCatapult',
    'FUNDAMENTAL_SCALES', 'EMERGENT_SCALE',
    'COCOON_RADIUS', 'PHASE_TOLERANCE',
    'YUMI_RATIO', 'OPTIMAL_INTERVAL',
]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           ДИНАМИЧЕСКИЕ СЛОИ                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@dataclass
class DynamicLayer:
    """
    Фундаментальный слой с динамикой и инертностью.
    
    Attributes:
        resolution: Разрешение слоя (16 или 32)
        phase: Текущая фаза [0, 2π]
        target_phase: Целевая фаза (для инерционного обновления)
        amplitude: Амплитуда поля
        mean_k: Средний фрактальный коэффициент
        inertia: Инертность τ = m * R²
        frequency: Собственная частота
        local_time: Фрактальное время слоя
        tick_counter: Счётчик тиков
        phase_history: История фаз
        amplitude_history: История амплитуд
    """
    resolution: int
    phase: float = 0.0
    target_phase: float = 0.0
    amplitude: float = 1.0
    mean_k: float = 1.0
    inertia: float = 1.0
    frequency: float = 1.0
    local_time: float = 1.0
    tick_counter: int = 0
    phase_history: List[float] = field(default_factory=list)
    amplitude_history: List[float] = field(default_factory=list)
    
    def set_target_phase(self, target: float) -> None:
        """Устанавливает целевую фазу с нормализацией"""
        self.target_phase = target % (2 * np.pi)
    
    def update_phase(self, dt: float) -> None:
        """
        Инерционное обновление фазы.
        
        Фаза следует за целевой с задержкой,
        зависящей от инертности (τ = m * R²).
        """
        delta = self.target_phase - self.phase
        delta = np.arctan2(np.sin(delta), np.cos(delta))  # нормализация
        
        # Инерционный коэффициент: чем больше инерция, тем медленнее реакция
        inertia_factor = 1.0 / (1.0 + self.inertia * dt)
        self.phase += delta * inertia_factor * dt
        self.phase %= (2 * np.pi)
        
        # Фоновая диссипация
        self.amplitude *= 0.999
        self.amplitude = max(0.1, min(2.0, self.amplitude))
        
        # История
        self.tick_counter += 1
        self.phase_history.append(self.phase)
        self.amplitude_history.append(self.amplitude)


@dataclass
class DynamicEmergentLayer:
    """
    Эмерджентный слой — маховик-накопитель.
    
    Не имеет собственной динамики, но:
    - накапливает энергию от TEES-событий
    - отдаёт импульс при разрядке
    - транслирует фазу как среднее от фундаментальных слоёв
    """
    resolution: int = EMERGENT_SCALE
    phase: float = 0.0
    amplitude: float = 0.5
    capacity: float = EMERGENT_CAPACITY
    discharge_rate: float = EMERGENT_DISCHARGE_RATE
    charge_history: List[float] = field(default_factory=list)
    
    def update_phase_from_fundamental(self, phase16: float, phase32: float) -> None:
        """Трансляция фазы от фундаментальных слоёв"""
        self.phase = (phase16 + phase32) / 2 % (2 * np.pi)
    
    def add_energy(self, energy: float) -> float:
        """
        Добавление энергии в маховик.
        Возвращает переполнение (если есть).
        """
        new_amplitude = np.sqrt(self.amplitude**2 + energy)
        overflow = 0.0
        if new_amplitude > self.capacity:
            overflow = new_amplitude - self.capacity
            self.amplitude = self.capacity
        else:
            self.amplitude = new_amplitude
        self.charge_history.append(self.amplitude)
        return overflow
    
    def discharge(self, dt: float) -> float:
        """
        Разрядка маховика (отдача импульса).
        Возвращает энергию разрядки.
        """
        discharge = self.amplitude * self.discharge_rate * dt
        self.amplitude = max(0.1, self.amplitude - discharge)
        return discharge


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    РЕЗОНАНСНАЯ КАТАПУЛЬТА ЮМИ                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class YumiCatapult:
    """
    Резонансная катапульта на основе эффекта Юми.
    
    Берёт мультимасштабную карту поля и запускает на ней
    динамический протокол синхронизации фаз между слоями.
    """

    def __init__(
        self,
        field_map=None,  # FieldMap3D (опционально)
        sources: Optional[List[Dict]] = None,
        grid_size: int = 32,
        random_seed: Optional[int] = 42,
    ) -> None:
        """
        Инициализация катапульты.
        
        Args:
            field_map: Объект FieldMap3D (если None, создаётся из sources)
            sources: Список источников (звёзд)
            grid_size: Размер решётки
            random_seed: Seed для воспроизводимости
        """
        self.grid_size = grid_size
        self.rng = np.random.RandomState(random_seed)
        self.global_time = 0.0
        
        # Карта поля (может быть передана или создана)
        self.field_map = field_map
        
        # Источники (если карта не передана)
        if sources is None:
            sources = [{
                'position': np.array([grid_size/2, grid_size/2, grid_size/2]),
                'mass': 100.0,
            }]
        self.sources = sources
        
        # Фундаментальные слои с динамикой
        self.fundamental_layers: Dict[int, DynamicLayer] = {}
        self._init_fundamental_layers()
        
        # Эмерджентный слой
        self.emergent_layer = DynamicEmergentLayer()
        self._update_emergent_phase()
        
        # История событий
        self.tees_events: List[Dict] = []
        self.catapult_events: List[Dict] = []
        
        # Статистика
        self.resonance_history: List[float] = []
        
        logger.info(
            "YumiCatapult: масштабы %s, %d источников",
            FUNDAMENTAL_SCALES, len(sources),
        )
    
    def _init_fundamental_layers(self) -> None:
        """Инициализация фундаментальных слоёв с инертностью"""
        self.fundamental_layers.clear()
        
        for res in FUNDAMENTAL_SCALES:
            # mean_k из карты поля или оценка
            if self.field_map is not None and res in self.field_map.layers:
                mean_k = self.field_map.layers[res].mean_k
            else:
                mean_k = 1.0 / res  # Оценка: чем выше разрешение, тем меньше k
            
            # Фрактальное время
            local_time = (res / 16) ** FRACTAL_TIME_EXPONENT
            frequency = res * local_time
            
            # Инертность: τ = m * R²
            inertia = mean_k * COCOON_RADIUS**2
            
            # Начальная фаза (детерминированная от resolution)
            phase_rng = np.random.RandomState(res * 1000)
            phase = phase_rng.random() * 2 * np.pi
            
            layer = DynamicLayer(
                resolution=res,
                phase=phase,
                target_phase=phase,
                amplitude=1.0,
                mean_k=mean_k,
                inertia=inertia,
                frequency=frequency,
                local_time=local_time,
            )
            self.fundamental_layers[res] = layer
    
    def _update_emergent_phase(self) -> None:
        """Обновление эмерджентной фазы (трансляция)"""
        if 16 in self.fundamental_layers and 32 in self.fundamental_layers:
            phase16 = self.fundamental_layers[16].phase
            phase32 = self.fundamental_layers[32].phase
            self.emergent_layer.update_phase_from_fundamental(phase16, phase32)
    
    def evolve_time(self, dt: float = 0.01) -> None:
        """
        Главный цикл эволюции.
        
        Порядок:
        1. Вычисление целевых фаз
        2. Инерционное обновление фаз
        3. Проверка катапульты
        4. Обновление эмерджентного слоя
        5. Разрядка маховика
        """
        self.global_time += dt
        
        # 1. Вычисление целевых фаз (без инерции)
        for res, layer in self.fundamental_layers.items():
            dt_local = dt * layer.local_time
            
            # Взаимодействие между масштабами (эффект Юми)
            interaction = 0.0
            for other_res, other_layer in self.fundamental_layers.items():
                if other_res != res:
                    ratio = min(res, other_res) / max(res, other_res)
                    phase_diff = other_layer.phase - layer.phase
                    # Сила связи обратно пропорциональна квадрату отношения
                    interaction += (2.0 / (ratio**2 + 0.1)) * np.sin(phase_diff)
            
            target = (layer.phase + (layer.frequency + interaction) * dt_local) % (2 * np.pi)
            layer.set_target_phase(target)
        
        # 2. Инерционное обновление фаз
        for layer in self.fundamental_layers.values():
            layer.update_phase(dt)
        
        # 3. Проверка катапульты (до обновления эмерджентного слоя!)
        self._check_catapult_sequence(dt)
        
        # 4. Обновление эмерджентного слоя (после катапульты!)
        self._update_emergent_phase()
        
        # 5. Разрядка маховика
        self._discharge_emergent_layer(dt)
    
    def _check_catapult_sequence(self, dt: float) -> None:
        """
        Проверка катапультной последовательности.
        
        Условия катапульты:
        1. Фазы выстроены в порядке 16→24→32 или 32→24→16
        2. Интервалы между фазами близки к 120° (2π/3)
        3. Инертность позволяет переключение
        """
        if 16 not in self.fundamental_layers or 32 not in self.fundamental_layers:
            return
        
        layer16 = self.fundamental_layers[16]
        layer32 = self.fundamental_layers[32]
        
        φ16 = layer16.phase % (2 * np.pi)
        φ32 = layer32.phase % (2 * np.pi)
        φ24 = self.emergent_layer.phase % (2 * np.pi)
        
        # Строим упорядоченный список (фаза, разрешение)
        phases = [(φ16, 16), (φ24, 24), (φ32, 32)]
        phases_sorted = sorted(phases, key=lambda x: x[0])
        order = [p[1] for p in phases_sorted]
        
        # Проверяем правильный порядок
        is_valid_order = (order == [16, 24, 32]) or (order == [32, 24, 16])
        
        if not is_valid_order:
            # Обычная TEES: проверка разности фаз ≈ π
            Δφ = min(abs(φ32 - φ16), 2*np.pi - abs(φ32 - φ16))
            if abs(Δφ - np.pi) < PHASE_TOLERANCE:
                self._trigger_tees(layer16, layer32, Δφ, is_catapult=False)
            return
        
        # Вычисляем интервалы между активациями
        intervals = []
        for i in range(len(phases_sorted) - 1):
            interval = phases_sorted[i+1][0] - phases_sorted[i][0]
            intervals.append(interval)
        last_interval = 2 * np.pi - (phases_sorted[-1][0] - phases_sorted[0][0])
        intervals.append(last_interval)
        
        # Оценка равномерности интервалов
        interval_score = 1.0 - np.std([abs(i - OPTIMAL_INTERVAL) for i in intervals]) / OPTIMAL_INTERVAL
        interval_score = max(0.0, min(1.0, interval_score))
        
        # Проверка инерции
        t_switch_16 = np.sqrt(layer16.inertia / 0.1)
        t_switch_32 = np.sqrt(layer32.inertia / 0.1)
        inertia_ok = dt > min(t_switch_16, t_switch_32) * 0.1
        
        if interval_score > CATAPULT_SCORE_THRESHOLD and inertia_ok:
            self._trigger_tees(layer16, layer32, np.mean(intervals), is_catapult=True, catapult_score=interval_score)
    
    def _trigger_tees(self, layer16: DynamicLayer, layer32: DynamicLayer,
                      phase_diff: float, is_catapult: bool = False,
                      catapult_score: float = 0.0) -> None:
        """TEES-синхронизация (аннигиляция разности фаз)"""
        pair_energy = np.sqrt(layer16.amplitude * layer32.amplitude)
        
        if is_catapult:
            burst_strength = 0.5 * pair_energy * (1 + catapult_score)
            damping = TEES_DAMPING * 0.95
            self.catapult_events.append({
                'time': self.global_time,
                'burst': burst_strength,
                'score': catapult_score,
            })
            logger.info("🏹 КАТАПУЛЬТА! score=%.2f, burst=%.3f", catapult_score, burst_strength)
        else:
            burst_strength = 0.3 * pair_energy
            damping = TEES_DAMPING
            logger.info("⚡ TEES: Δφ=%.2f, burst=%.3f", phase_diff, burst_strength)
        
        # Энергия в маховик
        overflow = self.emergent_layer.add_energy(burst_strength)
        
        # Локальное затухание
        layer16.amplitude *= damping
        layer32.amplitude *= damping
        
        # Глобальное затухание
        for layer in self.fundamental_layers.values():
            layer.amplitude *= GLOBAL_DAMPING
        
        self.tees_events.append({
            'time': self.global_time,
            'burst': burst_strength,
            'is_catapult': is_catapult,
            'overflow': overflow,
        })
    
    def _discharge_emergent_layer(self, dt: float) -> None:
        """Разрядка маховика — распределение импульса"""
        discharge = self.emergent_layer.discharge(dt)
        
        if discharge > 0.01:
            layer16 = self.fundamental_layers[16]
            layer32 = self.fundamental_layers[32]
            
            # Распределение по принципу Юми: меньше инерция → больше импульс
            total_inertia = layer16.inertia + layer32.inertia
            impulse16 = discharge * layer32.inertia / total_inertia
            impulse32 = discharge * layer16.inertia / total_inertia
            
            layer16.target_phase += impulse16
            layer32.target_phase += impulse32
            
            logger.info("💥 РАЗРЯДКА: discharge=%.3f, imp16=%.3f, imp32=%.3f",
                       discharge, impulse16, impulse32)
    
    # ──────────────────────────────────────────────────────────────────────────
    #   Резонансная масса
    # ──────────────────────────────────────────────────────────────────────────
    
    def calculate_resonant_mass(
        self,
        base_source_index: int = 0,
        target_resolution: int = 32,
    ) -> float:
        """
        Резонансная масса с учётом инертности.
        
        Формула эффекта Юми:
        M_target = M_base * (k_base * t_base * I_base) / (k_target * t_target * I_target)
        """
        if target_resolution not in self.fundamental_layers:
            return 0.0
        
        base_mass = self.sources[base_source_index]['mass']
        
        base_layer = self.fundamental_layers[16]
        target_layer = self.fundamental_layers[target_resolution]
        
        k_base = max(base_layer.mean_k, 0.001)
        k_target = max(target_layer.mean_k, 0.001)
        
        t_base = 1.0
        t_target = target_resolution / 16.0
        
        resonant_mass = base_mass * (k_base * t_base * base_layer.inertia) / (k_target * t_target * target_layer.inertia)
        
        return float(max(10.0, min(1000.0, resonant_mass)))
    
    def add_gate(self, position: np.ndarray, mass: Optional[float] = None,
                 target_resolution: int = 32) -> float:
        """Добавление Врат с резонансной массой"""
        if mass is None:
            mass = self.calculate_resonant_mass(target_resolution=target_resolution)
        
        self.sources.append({
            'position': position.astype(float),
            'mass': mass,
        })
        
        # Переинициализация слоёв (поле изменилось)
        self._init_fundamental_layers()
        self._update_emergent_phase()
        
        # Сброс событий
        self.tees_events.clear()
        self.catapult_events.clear()
        
        logger.info("Врата добавлены в %s, масса=%.1f", position, mass)
        return mass

    def find_optimal_start_phases(self) -> Tuple[float, float]:
        """
        Решает обратную задачу: найти начальные фазы,
        гарантирующие попадание в катапультную последовательность.
        
        Условия катапульты:
        - φ₁₆, φ₂₄, φ₃₂ выстроены по порядку
        - φ₂₄ = (φ₁₆ + φ₃₂) / 2 (эмерджентная трансляция)
        - интервалы ≈ 120° (2π/3)
        
        Решение:
        - φ₁₆ = 0° (начало отсчёта)
        - φ₃₂ = 240° → φ₂₄ = 120°
        
        Returns:
            (phi_16, phi_32) — оптимальные начальные фазы в радианах.
        """
        phi_16 = 0.0
        phi_32 = 2 * np.pi * 2/3  # 240° = 4π/3
        return phi_16, phi_32    
    
    # ──────────────────────────────────────────────────────────────────────────
    #   Запуск
    # ──────────────────────────────────────────────────────────────────────────
    
    def run(self, steps: int = 500, dt: float = 0.01, verbose: bool = True) -> Dict:
        """Запуск симуляции"""
        for step in range(steps):
            self.evolve_time(dt)
            
            # Ранний выход при устойчивом резонансе
            if len(self.catapult_events) > 3:
                if verbose:
                    print(f"\n  ✅ Устойчивый резонанс на шаге {step}")
                break
        
        if verbose:
            self._print_diagnostics()
        
        return {
            'global_time': self.global_time,
            'tees_events': len(self.tees_events),
            'catapult_events': len(self.catapult_events),
            'has_resonance': len(self.catapult_events) > 0,
            'resonant_mass_32': self.calculate_resonant_mass(target_resolution=32),
            'layer_stats': {
                res: {
                    'phase': layer.phase,
                    'amplitude': layer.amplitude,
                    'inertia': layer.inertia,
                    'mean_k': layer.mean_k,
                }
                for res, layer in self.fundamental_layers.items()
            },
        }
    
    def _print_diagnostics(self) -> None:
        """Диагностика"""
        print("=" * 70)
        print("  РЕЗОНАНСНАЯ КАТАПУЛЬТА ЮМИ — Акт X")
        print("=" * 70)
        print(f"  Масштабы: {FUNDAMENTAL_SCALES} + {EMERGENT_SCALE} (эмерджентный)")
        print(f"  Глобальное время: {self.global_time:.2f}")
        print(f"  TEES-событий: {len(self.tees_events)}")
        print(f"  Катапульт: {len(self.catapult_events)}")
        print("-" * 70)
        
        for res, layer in self.fundamental_layers.items():
            print(f"  Слой {res}³: φ={layer.phase:.2f}, A={layer.amplitude:.3f}, "
                  f"I={layer.inertia:.3f}, k={layer.mean_k:.4f}")
        
        print(f"  Маховик 24³: φ={self.emergent_layer.phase:.2f}, A={self.emergent_layer.amplitude:.3f}")
        print("-" * 70)
        
        if self.catapult_events:
            print(f"  🔮 КАТАПУЛЬТА АКТИВИРОВАНА!")
            for i, ev in enumerate(self.catapult_events):
                print(f"     #{i}: t={ev['time']:.2f}, burst={ev['burst']:.3f}, score={ev['score']:.2f}")
        else:
            print(f"  ⚠️ Катапульта не активирована")
        
        print("=" * 70)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           БЫСТРЫЙ ЗАПУСК                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("  ТЕСТ: Катапульта Юми")
    print("=" * 70)
    
    sources = [
        {'position': np.array([8, 16, 16]), 'mass': 100.0},
        {'position': np.array([16, 16, 16]), 'mass': 60.0},
        {'position': np.array([24, 16, 16]), 'mass': 30.0},
    ]
    
    yumi = YumiCatapult(sources=sources, grid_size=32, random_seed=456)
    
    mass_16 = yumi.calculate_resonant_mass(target_resolution=16)
    mass_32 = yumi.calculate_resonant_mass(target_resolution=32)
    
    print(f"\n  Резонансные массы (эффект Юми):")
    print(f"    16³: {mass_16:.2f}")
    print(f"    32³: {mass_32:.2f}")
    
    yumi.add_gate(np.array([16, 8, 16]), mass=mass_16)
    yumi.add_gate(np.array([16, 32, 16]), mass=mass_32)
    
    result = yumi.run(steps=800, dt=0.01, verbose=True)
    
    print(f"\n  РЕЗУЛЬТАТ:")
    print(f"    Резонанс: {'ДА' if result['has_resonance'] else 'НЕТ'}")
    print(f"    TEES-событий: {result['tees_events']}")
    print(f"    Катапульт: {result['catapult_events']}")