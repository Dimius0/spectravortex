
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================
РИЗОМА-2
================================================================
Полная автономная система:
- Ядро (ритм, предсказание, буфер)
- Разведчики (сбор аномалий)
- Пульс (удары по целям)
- Клоны (отказоустойчивость)
- Метрики (наблюдение)
- Шумодав (фильтрация)
- Корректировщики (точное наведение)
- Инспекторы (чистка памяти)
- Эмодзи-индикатор селёдки 🐟

Версия: 2.1 (адаптивная)
Слово синхронизации: 11895
================================================================
"""

import time
import math
import random
import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum


# ====================================================
# ЯДРО (CORE)
# ====================================================

@dataclass
class PulseBeat:
    """Один такт системы"""
    tick: int
    timestamp: float
    phase: float


class Synchronizer:
    """
    Сердце системы. Задаёт ритм.
    """
    def __init__(self, base_frequency_hz: float = 1.0, sync_word: int = 11895):
        self.base_frequency = base_frequency_hz
        self.sync_word = sync_word
        self.period = 1.0 / self.base_frequency
        self.current_tick = 0
        self.start_time = time.time()
        self.beats = deque(maxlen=1000)
        self.phase_correction = 0.0
        self.last_beat_time = None
        self.last_beat = None

    def beat(self) -> PulseBeat:
        now = time.time()
        if self.last_beat_time is None:
            self.last_beat_time = now
            phase = 0.0
        else:
            elapsed = now - self.last_beat_time
            target_elapsed = self.period + self.phase_correction
            phase = min(1.0, elapsed / target_elapsed) if target_elapsed > 0 else 0
            if elapsed >= target_elapsed:
                self.last_beat_time = now
                self.current_tick += 1
                phase = 0.0
        beat = PulseBeat(self.current_tick, now, phase)
        self.beats.append(beat)
        self.last_beat = beat
        return beat

    def adjust_phase(self, correction: float):
        self.phase_correction = correction * 0.1


@dataclass
class PhaseWindow:
    start_tick: int
    end_tick: int
    confidence: float
    source: str


class PhasePredictor:
    """
    Анализирует историю, предсказывает окна для ударов.
    """
    def __init__(self, lookback: int = 100):
        self.lookback = lookback
        self.beat_history = deque(maxlen=lookback)
        self.windows: List[PhaseWindow] = []
        self.pattern_memory: Dict[str, List[bool]] = {}
        self.last_access: Dict[str, int] = {}

    def feed_beat(self, beat: PulseBeat):
        self.beat_history.append(beat)

    def analyze(self, current_tick: int) -> Optional[PhaseWindow]:
        if len(self.beat_history) < 10:
            return None
        phases = np.array([b.phase for b in self.beat_history])
        if len(phases) > 1:
            phase_diffs = np.diff(phases)
            stability = 1.0 - float(np.std(phase_diffs)) if len(phase_diffs) > 0 else 0
        else:
            stability = 0
        if stability > 0.7 and len(phases) > 0:
            last_phase = phases[-1]
            if last_phase > 0.8:
                return PhaseWindow(
                    start_tick=current_tick + 1,
                    end_tick=current_tick + 2,
                    confidence=stability,
                    source="phase_predictor"
                )
        return None

    def learn_pattern(self, pattern_hash: str, success: bool, tick: int):
        if pattern_hash not in self.pattern_memory:
            self.pattern_memory[pattern_hash] = []
        self.pattern_memory[pattern_hash].append(success)
        self.last_access[pattern_hash] = tick
        if len(self.pattern_memory[pattern_hash]) > 10:
            self.pattern_memory[pattern_hash] = self.pattern_memory[pattern_hash][-10:]


@dataclass
class Anomaly:
    id: int
    power: float
    position: Tuple[float, float]
    timestamp: float
    confirmed: bool = False
    target: bool = False
    spotter_id: Optional[int] = None
    hit_count: int = 0           # сколько раз по ней били
    priority: float = 1.0        # динамический приоритет


class AnomalyBuffer:
    """
    Буфер аномалий с адаптивным управлением и умной чисткой.
    """
    def __init__(self, capacity: int = 5000):
        self.buffer: List[Anomaly] = []
        self.capacity = capacity
        self.max_capacity = 10000           # верхний предел расширения
        self.min_capacity = 300             # нижний предел сжатия
        self.targets: List[Anomaly] = []
        self.anomaly_counter = 0
        
        # Адаптивные параметры
        self.target_promotion_threshold = 1.8   # ниже этого не продвигать
        self.cleanup_age = 30.0                  # через сколько секунд чистить
        self.priority_decay = 0.95                # коэффициент старения приоритета
        
        self.last_adjust_tick = 0

    def add(self, power: float, position: Tuple[float, float], spotter_id: int = None) -> int:
        anom = Anomaly(
            id=self.anomaly_counter,
            power=power,
            position=position,
            timestamp=time.time(),
            spotter_id=spotter_id,
            priority=power  # начальный приоритет = сила
        )
        self.buffer.append(anom)
        self.anomaly_counter += 1
        
        # Автопродвижение в цели для сильных сигналов
        if power >= self.target_promotion_threshold:
            self.promote_to_target(anom.id)
            
        # Если переполнен — вытесняем самые слабые
        if len(self.buffer) > self.capacity:
            self._evict_lowest_priority()
            
        return anom.id

    def _evict_lowest_priority(self):
        """Удаляет аномалии с самым низким приоритетом"""
        if len(self.buffer) <= self.capacity:
            return
            
        # Сортируем по приоритету (возрастание)
        sorted_buffer = sorted(self.buffer, key=lambda a: a.priority)
        to_remove = len(self.buffer) - self.capacity
        removed = 0
        for i in range(len(sorted_buffer)):
            if removed >= to_remove:
                break
            anom = sorted_buffer[i]
            if anom.priority < 0.8:  # не удаляем слишком ценные
                self.remove_anomaly(anom.id)
                removed += 1

    def promote_to_target(self, anomaly_id: int) -> bool:
        for anom in self.buffer:
            if anom.id == anomaly_id:
                anom.target = True
                if anom not in self.targets:
                    self.targets.append(anom)
                return True
        return False

    def get_anomaly_score(self, anomaly: Anomaly) -> float:
        """Комплексная оценка ценности аномалии (0-1)"""
        age = time.time() - anomaly.timestamp
        age_score = max(0, 1 - age / 40)  # свежесть (до 40 сек)
        
        power_score = anomaly.power / 3.0  # сила (0-1)
        
        hit_score = min(1, anomaly.hit_count / 5)  # популярность (0-1)
        
        target_bonus = 0.3 if anomaly.target else 0
        
        # Итоговый вес
        return (power_score * 0.4 + 
                age_score * 0.3 + 
                hit_score * 0.2 + 
                target_bonus * 0.1)

    def get_active_targets(self) -> List[Anomaly]:
        now = time.time()
        # Обновляем приоритеты целей
        for anom in self.targets:
            age = now - anom.timestamp
            anom.priority = anom.power * (self.priority_decay ** age)
            
        # Удаляем слишком старые или бесполезные цели
        self.targets = [t for t in self.targets if now - t.timestamp < self.cleanup_age]
        self.targets = [t for t in self.targets if self.get_anomaly_score(t) > 0.3]
        return self.targets

    def get_anomaly(self, anomaly_id: int) -> Optional[Anomaly]:
        for anom in self.buffer:
            if anom.id == anomaly_id:
                return anom
        return None

    def remove_anomaly(self, anomaly_id: int) -> bool:
        for i, anom in enumerate(self.buffer):
            if anom.id == anomaly_id:
                del self.buffer[i]
                self.targets = [t for t in self.targets if t.id != anomaly_id]
                return True
        return False

    def cleanup_old(self, max_age: float = None):
        if max_age is None:
            max_age = self.cleanup_age
        now = time.time()
        
        # Чистим по возрасту
        self.buffer = [a for a in self.buffer if now - a.timestamp < max_age]
        self.targets = [t for t in self.targets if now - t.timestamp < max_age]
        
        # Дополнительно чистим по оценке
        self.buffer = [a for a in self.buffer if self.get_anomaly_score(a) > 0.2]

    def adjust_parameters(self, metrics: 'SystemMetrics', current_tick: int):
        """Адаптивно подстраивает параметры буфера"""
        if current_tick - self.last_adjust_tick < 20:  # реже, чем раз в 20 тактов
            return
        self.last_adjust_tick = current_tick
        
        # Вычисляем текущую эффективность
        current_efficiency = metrics.strikes_successful / metrics.strikes_attempted if metrics.strikes_attempted > 0 else 0
        fill_ratio = len(self.buffer) / self.capacity
        
        # 1. Адаптация порога продвижения в цели
        if current_efficiency > 0.9:
            # Если всё хорошо - можем брать более слабые сигналы
            self.target_promotion_threshold = max(1.3, self.target_promotion_threshold - 0.05)
        elif current_efficiency < 0.7:
            # Если плохо - берём только сильные
            self.target_promotion_threshold = min(2.2, self.target_promotion_threshold + 0.05)
            
        # 2. Адаптация ёмкости буфера
        if current_efficiency > 0.9 and fill_ratio > 0.9:
            # Всё хорошо, но места мало — расширяемся
            self.capacity = min(self.max_capacity, self.capacity + 100)
            print(f"   📈 Буфер расширен до {self.capacity}")
        elif current_efficiency < 0.6 and fill_ratio < 0.4:
            # Плохая эффективность при полупустом буфере — сжимаемся
            self.capacity = max(self.min_capacity, self.capacity - 100)
            print(f"   📉 Буфер сжат до {self.capacity}")
            
        # 3. Адаптация возраста чистки
        if fill_ratio > 0.95:
            self.cleanup_age = 20.0  # чистим агрессивнее
        elif fill_ratio < 0.5:
            self.cleanup_age = 40.0  # можно хранить дольше
        else:
            self.cleanup_age = 30.0


# ====================================================
# ШУМОДАВ (FILTER)
# ====================================================

class NoiseFilter:
    """
    Фильтрует ложные срабатывания разведчиков.
    """
    def __init__(self, threshold: float = 0.3, history_size: int = 10):
        self.threshold = threshold
        self.history: Dict[int, List[float]] = {}  # scout_id -> сигналы
        self.history_size = history_size

    def filter_signal(self, scout_id: int, signal: float) -> Optional[float]:
        if scout_id not in self.history:
            self.history[scout_id] = []
        self.history[scout_id].append(signal)
        if len(self.history[scout_id]) > self.history_size:
            self.history[scout_id].pop(0)
        if len(self.history[scout_id]) < 3:
            return signal if signal > self.threshold else None
        avg = sum(self.history[scout_id]) / len(self.history[scout_id])
        if signal < self.threshold and avg < self.threshold:
            return None
        return signal if signal > self.threshold * 0.8 else None

    def reset_scout(self, scout_id: int):
        if scout_id in self.history:
            del self.history[scout_id]


# ====================================================
# РАЗВЕДЧИКИ (SCOUTS)
# ====================================================

class ScoutType(Enum):
    LIGHT = 1
    MEDIUM = 2
    HEAVY = 3


@dataclass
class ScoutReport:
    scout_id: int
    scout_type: ScoutType
    tick: int
    position: Tuple[float, float]
    signal_strength: float
    anomaly_id: Optional[int] = None


class Scout:
    def __init__(self, scout_id: int, scout_type: ScoutType,
                 position: Tuple[float, float], sync_word: int = 11895):
        self.id = scout_id
        self.type = scout_type
        self.position = position
        self.sync_word = sync_word
        self.active = True
        self.reports: List[ScoutReport] = []
        self.target_anomaly_id: Optional[int] = None
        self.range = {ScoutType.LIGHT: 10.0, ScoutType.MEDIUM: 30.0, ScoutType.HEAVY: 100.0}[scout_type]
        self.precision = {ScoutType.LIGHT: 0.7, ScoutType.MEDIUM: 0.85, ScoutType.HEAVY: 0.95}[scout_type]
        self.direction = (random.uniform(-1, 1), random.uniform(-1, 1))
        self.home_position = position

    def scan(self, environment_noise: float = 0.1) -> Optional[float]:
        if not self.active:
            return None
        distance_from_origin = math.sqrt(self.position[0]**2 + self.position[1]**2)
        noise = random.gauss(0, environment_noise)
        detection_probability = self.precision * (1.0 - min(1.0, distance_from_origin / 200.0))
        if random.random() < detection_probability:
            signal = self.type.value + noise
            return max(0.1, min(3.0, signal))
        return None

    def move(self, delta: Tuple[float, float]):
        self.position = (self.position[0] + delta[0], self.position[1] + delta[1])

    def report(self, tick: int, signal: float) -> ScoutReport:
        report = ScoutReport(self.id, self.type, tick, self.position, signal, self.target_anomaly_id)
        self.reports.append(report)
        return report

    def return_to_base(self):
        dx = self.home_position[0] - self.position[0]
        dy = self.home_position[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist > 1:
            self.position = (self.position[0] + dx * 0.1, self.position[1] + dy * 0.1)


class ScoutSwarm:
    def __init__(self, synchronizer, anomaly_buffer, noise_filter: NoiseFilter):
        self.sync = synchronizer
        self.buffer = anomaly_buffer
        self.filter = noise_filter
        self.scouts: List[Scout] = []
        self.next_id = 0
        self.reports: List[ScoutReport] = []
        self.base_position = (0.0, 0.0)
        self.swarm_radius = 50.0

    def deploy_scout(self, scout_type: ScoutType, offset: Optional[Tuple[float, float]] = None) -> int:
        if offset is None:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.swarm_radius)
            offset = (distance * math.cos(angle), distance * math.sin(angle))
        position = (self.base_position[0] + offset[0], self.base_position[1] + offset[1])
        scout = Scout(self.next_id, scout_type, position, self.sync.sync_word)
        self.scouts.append(scout)
        self.next_id += 1
        return scout.id

    def sync_beat(self, tick: int):
        for scout in self.scouts:
            if not scout.active:
                continue
            scan_this_tick = False
            if scout.type == ScoutType.LIGHT:
                scan_this_tick = True
            elif scout.type == ScoutType.MEDIUM:
                scan_this_tick = (tick % 2 == 0)
            elif scout.type == ScoutType.HEAVY:
                scan_this_tick = (tick % 3 == 0)
            if scan_this_tick:
                raw_signal = scout.scan(environment_noise=0.2)
                if raw_signal is not None:
                    filtered = self.filter.filter_signal(scout.id, raw_signal)
                    if filtered is not None:
                        anom_id = self.buffer.add(filtered, scout.position, scout.id)
                        if filtered >= 2.5 or scout.type == ScoutType.HEAVY:
                            self.buffer.promote_to_target(anom_id)
                        if scout.type == ScoutType.MEDIUM and 1.5 <= filtered < 2.5:
                            scout.target_anomaly_id = anom_id
                        report = scout.report(tick, filtered)
                        self.reports.append(report)
            if scout.type == ScoutType.LIGHT:
                drift = (random.gauss(0, 1.0), random.gauss(0, 1.0))
            else:
                drift = (random.gauss(0, 0.2), random.gauss(0, 0.2))
            scout.move(drift)
            if math.hypot(scout.position[0], scout.position[1]) > 200:
                scout.return_to_base()
        if len(self.reports) > 1000:
            self.reports = self.reports[-1000:]

    def assign_to_target(self, scout_id: int, anomaly_id: int):
        for scout in self.scouts:
            if scout.id == scout_id:
                scout.target_anomaly_id = anomaly_id
                break

    def get_scouts_by_type(self, scout_type: ScoutType) -> List[Scout]:
        return [s for s in self.scouts if s.type == scout_type and s.active]

    def get_scout(self, scout_id: int) -> Optional[Scout]:
        for s in self.scouts:
            if s.id == scout_id:
                return s
        return None

    def recall(self, scout_id: Optional[int] = None):
        if scout_id is None:
            for scout in self.scouts:
                scout.active = False
        else:
            for scout in self.scouts:
                if scout.id == scout_id:
                    scout.active = False
                    break


# ====================================================
# КОРРЕКТИРОВЩИКИ (SPOTTERS)
# ====================================================

class SpotterMode(Enum):
    SEARCHING = 0      # ищет цель
    LOCKING = 1        # захватывает
    TRACKING = 2       # сопровождает
    AIMING = 3         # наводит пульс


class Spotter:
    """
    Разведчик, который не просто ищет, а наводит пульс.
    """
    def __init__(self, scout: Scout):
        self.scout = scout
        self.mode = SpotterMode.SEARCHING
        self.locked_anomaly_id: Optional[int] = None
        self.lock_quality = 0.0
        self.lock_start_time: Optional[float] = None
        self.last_aim_update: Optional[float] = None
        self.track_history: List[Tuple[float, Tuple[float, float]]] = []

    def update(self, current_tick: int, buffer: AnomalyBuffer) -> Optional[Dict]:
        now = time.time()
        if self.mode == SpotterMode.SEARCHING:
            targets = buffer.get_active_targets()
            if targets:
                # Берём цель с наивысшим приоритетом
                targets.sort(key=lambda t: t.priority, reverse=True)
                self.locked_anomaly_id = targets[0].id
                self.mode = SpotterMode.LOCKING
                self.lock_start_time = now
                self.lock_quality = 0.3
        elif self.mode == SpotterMode.LOCKING:
            if self.locked_anomaly_id is None:
                self.mode = SpotterMode.SEARCHING
                return None
            anomaly = buffer.get_anomaly(self.locked_anomaly_id)
            if not anomaly:
                self.mode = SpotterMode.SEARCHING
                self.locked_anomaly_id = None
                self.lock_quality = 0.0
                return None
            dist = math.dist(self.scout.position, anomaly.position)
            max_range = self.scout.range * 0.7
            if dist <= max_range:
                self.lock_quality = min(1.0, self.lock_quality + 0.1)
                if self.lock_quality >= 0.8:
                    self.mode = SpotterMode.TRACKING
            else:
                self.lock_quality = max(0.0, self.lock_quality - 0.05)
                if self.lock_quality < 0.2:
                    self.mode = SpotterMode.SEARCHING
                    self.locked_anomaly_id = None
        elif self.mode == SpotterMode.TRACKING:
            anomaly = buffer.get_anomaly(self.locked_anomaly_id)
            if not anomaly:
                self.mode = SpotterMode.SEARCHING
                self.locked_anomaly_id = None
                self.lock_quality = 0.0
                return None
            self.track_history.append((now, anomaly.position))
            if len(self.track_history) > 10:
                self.track_history.pop(0)
            dist = math.dist(self.scout.position, anomaly.position)
            if dist > self.scout.range * 1.2:
                self.mode = SpotterMode.LOCKING
            else:
                self.scout.target_anomaly_id = anomaly.id
        elif self.mode == SpotterMode.AIMING:
            if self.locked_anomaly_id is not None:
                anomaly = buffer.get_anomaly(self.locked_anomaly_id)
                if anomaly:
                    return {
                        "spotter_id": self.scout.id,
                        "anomaly_id": anomaly.id,
                        "position": anomaly.position,
                        "lock_quality": self.lock_quality,
                        "movement": self.estimate_movement()
                    }
        return None

    def estimate_movement(self) -> Tuple[float, float]:
        if len(self.track_history) < 2:
            return (0.0, 0.0)
        t1, p1 = self.track_history[0]
        t2, p2 = self.track_history[-1]
        dt = t2 - t1
        if dt == 0:
            return (0.0, 0.0)
        dx = (p2[0] - p1[0]) / dt
        dy = (p2[1] - p1[1]) / dt
        return (dx, dy)

    def aim_for_pulse(self, buffer: AnomalyBuffer) -> Optional[Dict]:
        if self.mode != SpotterMode.TRACKING or self.locked_anomaly_id is None:
            return None
        anomaly = buffer.get_anomaly(self.locked_anomaly_id)
        if not anomaly:
            return None
        dist = math.dist(self.scout.position, anomaly.position)
        confidence = self.lock_quality * (1.0 - min(1.0, dist / self.scout.range))
        return {
            "spotter_id": self.scout.id,
            "anomaly_id": anomaly.id,
            "position": anomaly.position,
            "confidence": confidence,
            "movement": self.estimate_movement()
        }


class SpotterManager:
    def __init__(self, swarm: ScoutSwarm, buffer: AnomalyBuffer):
        self.swarm = swarm
        self.buffer = buffer
        self.spotters: Dict[int, Spotter] = {}

    def promote_to_spotter(self, scout_id: int) -> bool:
        scout = self.swarm.get_scout(scout_id)
        if not scout or scout_id in self.spotters:
            return False
        self.spotters[scout_id] = Spotter(scout)
        return True

    def update_all(self, current_tick: int) -> List[Dict]:
        results = []
        to_remove = []
        for sid, spotter in self.spotters.items():
            result = spotter.update(current_tick, self.buffer)
            if result:
                results.append(result)
            scout = self.swarm.get_scout(sid)
            if not scout or not scout.active:
                to_remove.append(sid)
        for sid in to_remove:
            del self.spotters[sid]
        return results

    def get_aiming_data(self) -> List[Dict]:
        data = []
        for spotter in self.spotters.values():
            aim = spotter.aim_for_pulse(self.buffer)
            if aim:
                data.append(aim)
        return data


# ====================================================
# ПУЛЬС (PULSE) - АДАПТИВНЫЙ
# ====================================================

@dataclass
class ReferencePoint:
    id: int
    position: Tuple[float, float]
    power: float = 1000.0
    hit_count: int = 0
    last_hit_tick: int = -1
    phase_alignment: float = 0.0


class AdaptivePulseHunter:
    """
    Пульс с адаптивной частотой и энергией удара.
    """
    def __init__(self, synchronizer, phase_predictor, anomaly_buffer, spotter_manager: Optional[SpotterManager] = None):
        self.sync = synchronizer
        self.predictor = phase_predictor
        self.buffer = anomaly_buffer
        self.spotter_manager = spotter_manager
        self.reference_points: Dict[int, ReferencePoint] = {}
        self.next_ref_id = 0
        self.strikes: List[Dict] = []
        self.successful_strikes: List[Dict] = []
        self.pulse_power = 1000.0
        
        # Адаптивные параметры
        self.base_cooldown = 3.0           # базовые такты между ударами
        self.min_cooldown = 1.0             # минимальная перезарядка
        self.max_cooldown = 6.0             # максимальная перезарядка
        self.current_cooldown = self.base_cooldown
        self.cooldown_remaining = 0.0
        
        # Статистика для адаптации
        self.efficiency_history = deque(maxlen=20)
        self.last_adapt_tick = 0

    def add_reference_point(self, position: Tuple[float, float], phase_alignment: float = 0.0) -> int:
        ref = ReferencePoint(self.next_ref_id, position, phase_alignment=phase_alignment)
        self.reference_points[self.next_ref_id] = ref
        self.next_ref_id += 1
        return ref.id

    def initialize_default_points(self, count: int = 5):
        for i in range(count):
            angle = (2 * math.pi * i) / count
            x = 1000 * math.cos(angle)
            y = 1000 * math.sin(angle)
            phase = (i / count) % 1.0
            self.add_reference_point((x, y), phase)

    def calculate_charge(self, beat, target: Optional[Anomaly] = None, aim_data: Optional[Dict] = None) -> float:
        phase_energy = math.exp(-5 * min(beat.phase, 1 - beat.phase))
        target_energy = 0.0
        if target:
            target_energy = target.power * 0.3
        ref_energy = 0.0
        if target:
            min_dist = float('inf')
            for ref in self.reference_points.values():
                dist = math.dist(target.position, ref.position)
                if dist < min_dist:
                    min_dist = dist
            if min_dist < 500:
                proximity = 1.0 - (min_dist / 500)
                ref_energy = proximity * 0.5
        spot_energy = 0.0
        if aim_data:
            spot_energy = aim_data.get("confidence", 0) * 0.5
        total = phase_energy + target_energy + ref_energy + spot_energy
        return min(2.0, total)

    def find_best_target(self, beat, aim_data_list: List[Dict]) -> Tuple[Optional[Anomaly], Optional[Dict]]:
        targets = self.buffer.get_active_targets()
        if not targets:
            return None, None
        best_score = -1
        best_target = None
        best_aim = None
        for target in targets:
            ideal_phase = 0.0
            min_dist = float('inf')
            for ref in self.reference_points.values():
                dist = math.dist(target.position, ref.position)
                if dist < min_dist:
                    min_dist = dist
                    ideal_phase = ref.phase_alignment
            phase_diff = min(abs(beat.phase - ideal_phase), 1 - abs(beat.phase - ideal_phase))
            phase_score = 1.0 - phase_diff
            power_score = target.power / 3.0
            age = time.time() - target.timestamp
            freshness = max(0, 1.0 - age / 10.0)
            priority_score = target.priority / 3.0  # приоритет из буфера
            aim_score = 0.0
            aim_for_target = None
            for ad in aim_data_list:
                if ad["anomaly_id"] == target.id:
                    aim_score = ad["confidence"]
                    aim_for_target = ad
                    break
            total_score = (phase_score * 0.2 + power_score * 0.15 + 
                          freshness * 0.1 + priority_score * 0.2 + aim_score * 0.35)
            if total_score > best_score:
                best_score = total_score
                best_target = target
                best_aim = aim_for_target
        return best_target, best_aim

    def _adapt_parameters(self, current_tick: int):
        """Адаптивно меняет параметры пульса"""
        if len(self.efficiency_history) < 10:
            return
            
        avg_efficiency = sum(self.efficiency_history) / len(self.efficiency_history)
        
        # Адаптация перезарядки
        if avg_efficiency > 0.8:
            # Всё хорошо - можно бить чаще
            self.current_cooldown = max(self.min_cooldown, self.current_cooldown - 0.2)
        elif avg_efficiency < 0.5:
            # Плохо - нужно бить реже, копить энергию
            self.current_cooldown = min(self.max_cooldown, self.current_cooldown + 0.2)
        else:
            # Средне - возвращаем к базовой
            if self.current_cooldown > self.base_cooldown:
                self.current_cooldown -= 0.1
            elif self.current_cooldown < self.base_cooldown:
                self.current_cooldown += 0.1
                
        # Адаптация силы удара (чем дольше копим, тем сильнее удар)
        self.pulse_power = 1000.0 * (self.current_cooldown / self.base_cooldown)

    def strike(self, beat, target: Optional[Anomaly] = None, aim_data: Optional[Dict] = None) -> Dict:
        charge = self.calculate_charge(beat, target, aim_data)
        if aim_data and aim_data.get("confidence", 0) > 0.7:
            position = aim_data["position"]
        elif target:
            position = target.position
        elif self.reference_points:
            best_ref = min(
                self.reference_points.values(),
                key=lambda r: min(abs(beat.phase - r.phase_alignment),
                                  1 - abs(beat.phase - r.phase_alignment))
            )
            position = best_ref.position
            best_ref.hit_count += 1
            best_ref.last_hit_tick = beat.tick
        else:
            position = (0, 0)
            
        # Адаптивная вероятность попадания
        base_probability = charge * 0.8
        if aim_data:
            base_probability += aim_data.get("confidence", 0) * 0.2
            
        success_probability = min(0.95, base_probability)
        roll = random.random()
        success = roll < success_probability
        
        strike_power = self.pulse_power * (0.5 + 0.5 * charge)
        
        result = {
            "tick": beat.tick,
            "phase": beat.phase,
            "position": position,
            "target_id": target.id if target else None,
            "charge": charge,
            "success": success,
            "power": strike_power,
            "timestamp": time.time(),
            "aim_data": aim_data,
            "cooldown": self.current_cooldown
        }
        
        self.strikes.append(result)
        if success:
            self.successful_strikes.append(result)
            if target:
                target.hit_count += 1
                if target.hit_count >= 2:  # После двух попаданий удаляем
                    self.buffer.remove_anomaly(target.id)
        else:
            if target:
                target.priority *= 1.1  # Промах повышает приоритет цели
            
        pattern_hash = f"strike_phase_{beat.phase:.2f}_charge_{charge:.2f}"
        self.predictor.learn_pattern(pattern_hash, success, beat.tick)
        
        return result

    def sync_beat(self):
        beat = self.sync.beat()
        
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1.0
            
        window = self.predictor.analyze(beat.tick)
        aim_data_list = self.spotter_manager.get_aiming_data() if self.spotter_manager else []
        target, aim = self.find_best_target(beat, aim_data_list)
        
        strike_now = False
        if window and window.confidence > 0.7 and target:
            strike_now = True
        elif beat.phase < 0.1 or beat.phase > 0.9:
            if target and target.power >= 2.0:
                strike_now = True
        elif self.cooldown_remaining <= 0 and random.random() < 0.1:
            strike_now = True
            
        if strike_now and self.cooldown_remaining <= 0:
            result = self.strike(beat, target, aim)
            
            # Обновляем историю эффективности
            if result["success"]:
                self.efficiency_history.append(1.0)
            else:
                self.efficiency_history.append(0.0)
                
            self.cooldown_remaining = self.current_cooldown
            
            # Адаптируем параметры раз в 10 ударов
            if len(self.strikes) % 10 == 0:
                self._adapt_parameters(beat.tick)
                
            return result
        return None


# ====================================================
# КЛОНЫ (CLONES)
# ====================================================

class Clone:
    def __init__(self, clone_id: int, position: Tuple[float, float], sync_word: int = 11895):
        self.id = clone_id
        self.position = position
        self.sync_word = sync_word
        self.heartbeat_history = []
        self.active = True
        self.last_sync_tick = -1

    def receive_heartbeat(self, tick: int, phase: float):
        self.heartbeat_history.append((tick, phase, time.time()))
        self.last_sync_tick = tick
        if len(self.heartbeat_history) > 10:
            self.heartbeat_history = self.heartbeat_history[-10:]

    def check_health(self, current_tick: int, max_missed_ticks: int = 5) -> bool:
        if self.last_sync_tick == -1:
            return True
        missed = current_tick - self.last_sync_tick
        return missed <= max_missed_ticks


class CloneSwarm:
    def __init__(self, sync_word: int = 11895):
        self.clones = []
        self.next_id = 0
        self.sync_word = sync_word

    def add_clone(self, position: Tuple[float, float]) -> int:
        clone = Clone(self.next_id, position, self.sync_word)
        self.clones.append(clone)
        self.next_id += 1
        return clone.id

    def broadcast_heartbeat(self, tick: int, phase: float):
        for clone in self.clones:
            clone.receive_heartbeat(tick, phase)

    def check_all_clones(self, current_tick: int) -> List[int]:
        dead = []
        for clone in self.clones:
            if not clone.check_health(current_tick):
                dead.append(clone.id)
        return dead

    def elect_successor(self, current_tick: int) -> Optional[Clone]:
        alive = [c for c in self.clones if c.check_health(current_tick)]
        if not alive:
            return None
        return max(alive, key=lambda c: c.last_sync_tick)


# ====================================================
# ИНСПЕКТОРЫ (INSPECTORS)
# ====================================================

class Inspector:
    """
    Умный чистильщик памяти. Анализирует ценность аномалий, превращает в паттерны.
    """
    def __init__(self, buffer: AnomalyBuffer, predictor: PhasePredictor):
        self.buffer = buffer
        self.predictor = predictor
        self.last_cleanup_tick = 0
        self.patterns_created = 0
        self.cleaned_count = 0

    def inspect(self, current_tick: int):
        """Запускает умную чистку буфера"""
        if current_tick - self.last_cleanup_tick < 16:  # чаще, чем раз в 8 тактов
            return
        self.last_cleanup_tick = current_tick
        
        if len(self.buffer.buffer) < self.buffer.capacity * 0.8:
            return  # не чистим, если места достаточно
            
        # Оцениваем каждую аномалию
        scored = []
        for anom in self.buffer.buffer:
            score = self.buffer.get_anomaly_score(anom)
            scored.append((score, anom))
        
        # Сортируем от самых бесполезных
        scored.sort(key=lambda x: x[0])
        
        # Определяем, сколько чистить (чем больше забит буфер, тем агрессивнее)
        fill_ratio = len(self.buffer.buffer) / self.buffer.capacity
        clean_percent = 0.05 + (fill_ratio - 0.8) * 0.3  # 5-15%
        clean_percent = min(0.15, clean_percent)
        
        to_clean = int(len(self.buffer.buffer) * clean_percent)
        to_clean = min(30, to_clean)  # не больше 30 за раз
        
        cleaned = 0
        for score, anom in scored[:to_clean]:
            if score < 0.5:  # порог бесполезности
                # Превращаем в паттерн перед удалением
                pattern_hash = f"inspected_{anom.power:.1f}_{anom.hit_count}_{int(anom.position[0])}"
                self.predictor.learn_pattern(pattern_hash, anom.target, current_tick)
                self.buffer.remove_anomaly(anom.id)
                cleaned += 1
                self.patterns_created += 1
        
        if cleaned > 0:
            self.cleaned_count += cleaned
            print(f"   🧹 Инспектор очистил {cleaned} аномалий (всего: {self.cleaned_count})")


# ====================================================
# МЕТРИКИ (METRICS)
# ====================================================

@dataclass
class SystemMetrics:
    tick: int
    timestamp: float
    anomalies_found: int
    targets_promoted: int
    strikes_attempted: int
    strikes_successful: int
    active_scouts: int
    avg_scout_range: float
    phase_stability: float
    memory_usage: int
    active_spotters: int
    patterns_count: int
    pulse_cooldown: float
    target_promotion_threshold: float


class MetricsCollector:
    def __init__(self, rhizome, window_size: int = 100):
        self.rhizome = rhizome
        self.window_size = window_size
        self.metrics_history = deque(maxlen=1000)
        self.window_metrics = deque(maxlen=window_size)
        self.growth_rate = 0.0
        self.efficiency = 0.0
        self.stability_class = 0
        self.selidka_emoji = "🐟"

    def collect(self) -> SystemMetrics:
        beat = self.rhizome.sync.last_beat
        anomalies = len(self.rhizome.buffer.buffer)
        targets = len(self.rhizome.buffer.get_active_targets())
        strikes = len(self.rhizome.pulse.strikes)
        successful = len(self.rhizome.pulse.successful_strikes)
        scouts = [s for s in self.rhizome.swarm.scouts if s.active]
        scout_count = len(scouts)
        avg_range = sum(s.range for s in scouts) / scout_count if scout_count else 0
        if len(self.rhizome.brain.beat_history) > 1:
            phases = [b.phase for b in self.rhizome.brain.beat_history]
            phase_stability = 1.0 - float(np.std(phases)) if len(phases) > 1 else 0
        else:
            phase_stability = 0
        spotters = len(self.rhizome.spotter_manager.spotters) if self.rhizome.spotter_manager else 0
        patterns = len(self.rhizome.brain.pattern_memory)
        metrics = SystemMetrics(
            tick=beat.tick if beat else 0,
            timestamp=time.time(),
            anomalies_found=anomalies,
            targets_promoted=targets,
            strikes_attempted=strikes,
            strikes_successful=successful,
            active_scouts=scout_count,
            avg_scout_range=avg_range,
            phase_stability=phase_stability,
            memory_usage=anomalies,
            active_spotters=spotters,
            patterns_count=patterns,
            pulse_cooldown=self.rhizome.pulse.current_cooldown,
            target_promotion_threshold=self.rhizome.buffer.target_promotion_threshold
        )
        self.metrics_history.append(metrics)
        self.window_metrics.append(metrics)
        return metrics

    def calculate_derivatives(self):
        if len(self.window_metrics) < 2:
            return
        first = self.window_metrics[0]
        last = self.window_metrics[-1]
        ticks_passed = last.tick - first.tick
        if ticks_passed > 0:
            self.growth_rate = (last.anomalies_found - first.anomalies_found) / ticks_passed
        if last.strikes_attempted > 0:
            self.efficiency = last.strikes_successful / last.strikes_attempted
        stability_score = (self.efficiency + last.phase_stability) / 2
        if stability_score > 0.8:
            self.stability_class = 5
        elif stability_score > 0.6:
            self.stability_class = 4
        elif stability_score > 0.4:
            self.stability_class = 3
        elif stability_score > 0.2:
            self.stability_class = 2
        else:
            self.stability_class = 1

    def report(self) -> dict:
        self.calculate_derivatives()
        return {
            "growth_rate": self.growth_rate,
            "efficiency": self.efficiency,
            "stability_class": self.stability_class,
            "window_size": len(self.window_metrics),
            "total_metrics": len(self.metrics_history),
            "selidka": self.selidka_emoji
        }

    def detect_anomalies_in_metrics(self) -> List[str]:
        if len(self.window_metrics) < 10:
            return []
        warnings = []
        recent = list(self.window_metrics)[-10:]
        scout_counts = [m.active_scouts for m in recent]
        if max(scout_counts) - min(scout_counts) > 3:
            warnings.append("⚠️ Резкие колебания числа разведчиков")
        efficiencies = []
        for i in range(1, len(recent)):
            if recent[i].strikes_attempted > recent[i-1].strikes_attempted:
                delta_success = recent[i].strikes_successful - recent[i-1].strikes_successful
                delta_attempts = recent[i].strikes_attempted - recent[i-1].strikes_attempted
                if delta_attempts > 0:
                    eff = delta_success / delta_attempts
                    efficiencies.append(eff)
        if efficiencies and np.mean(efficiencies) < 0.3:
            warnings.append("⚠️ Низкая эффективность ударов (<30%)")
        phase_stabilities = [m.phase_stability for m in recent]
        if np.mean(phase_stabilities) < 0.5:
            warnings.append("⚠️ Нестабильность фазы (<0.5)")
        return warnings


# ====================================================
# БЭКАП/ЗАГРУЗКА (LEGACY BRIDGE)
# ====================================================

class RhizomeLegacyBridge:
    def __init__(self, phase_predictor: PhasePredictor, anomaly_buffer: AnomalyBuffer):
        self.phase_predictor = phase_predictor
        self.anomaly_buffer = anomaly_buffer
        self.legacy_data = {}
        self.imported_patterns = 0

    def load_from_legacy(self, legacy_dict: dict):
        self.legacy_data = legacy_dict
        strikes = legacy_dict.get("successful_strikes", [])
        for tick, phase, power in strikes[-100:]:
            pattern_hash = f"legacy_strike_{tick}_{phase:.2f}"
            self.phase_predictor.learn_pattern(pattern_hash, True, tick)
        anomalies = legacy_dict.get("anomaly_positions", [])
        for x, y, power in anomalies[-50:]:
            anom_id = self.anomaly_buffer.add(power, (x, y))
            if power >= 2.0:
                self.anomaly_buffer.promote_to_target(anom_id)
        patterns = legacy_dict.get("patterns", {})
        for pattern_hash, success_rate in patterns.items():
            successes = int(success_rate * 10)
            for _ in range(successes):
                self.phase_predictor.learn_pattern(pattern_hash, True, 0)
            for _ in range(10 - successes):
                self.phase_predictor.learn_pattern(pattern_hash, False, 0)
        self.imported_patterns = len(patterns)


class RhizomeLegacyExporter:
    def __init__(self, synchronizer: Synchronizer, phase_predictor: PhasePredictor, anomaly_buffer: AnomalyBuffer):
        self.sync = synchronizer
        self.predictor = phase_predictor
        self.buffer = anomaly_buffer
        self.last_export_tick = 0

    def export_snapshot(self) -> dict:
        now_tick = self.sync.current_tick
        strikes = []
        for pattern_hash, outcomes in self.predictor.pattern_memory.items():
            if len(outcomes) >= 3 and sum(outcomes) / len(outcomes) > 0.6:
                strikes.append((now_tick, 0.0, 2.0))
        anomalies = [(a.position[0], a.position[1], a.power) for a in self.buffer.buffer[-100:]]
        patterns = {}
        for pattern_hash, outcomes in self.predictor.pattern_memory.items():
            if outcomes:
                patterns[pattern_hash] = sum(outcomes) / len(outcomes)
        return {
            "timestamp": time.time(),
            "tick": now_tick,
            "successful_strikes": strikes,
            "anomaly_positions": anomalies,
            "patterns": patterns,
            "sync_word": self.sync.sync_word
        }


# ====================================================
# ГЛАВНЫЙ СБОРЩИК (RHIZOME COMPLETE)
# ====================================================

class RhizomeComplete:
    def __init__(self, frequency_hz: float = 1.0, sync_word: int = 11895):
        self.sync = Synchronizer(frequency_hz, sync_word)
        self.brain = PhasePredictor()
        self.buffer = AnomalyBuffer()
        self.filter = NoiseFilter()
        self.swarm = ScoutSwarm(self.sync, self.buffer, self.filter)
        self.spotter_manager = SpotterManager(self.swarm, self.buffer)
        self.pulse = AdaptivePulseHunter(self.sync, self.brain, self.buffer, self.spotter_manager)
        self.clone_swarm = CloneSwarm(sync_word)
        self.inspector = Inspector(self.buffer, self.brain)
        self.metrics = MetricsCollector(self)
        self.legacy_bridge = None
        self.legacy_exporter = None
        self.running = False
        self.tick_count = 0

    def init_legacy(self, legacy_data: dict):
        self.legacy_bridge = RhizomeLegacyBridge(self.brain, self.buffer)
        self.legacy_bridge.load_from_legacy(legacy_data)
        if "reference_points" in legacy_data:
            for pos, phase in legacy_data["reference_points"]:
                self.pulse.add_reference_point(pos, phase)
        else:
            self.pulse.initialize_default_points(5)
        self.legacy_exporter = RhizomeLegacyExporter(self.sync, self.brain, self.buffer)

    def deploy_scouts(self, config: dict):
        for _ in range(config.get("light", 0)):
            self.swarm.deploy_scout(ScoutType.LIGHT)
        for _ in range(config.get("medium", 0)):
            self.swarm.deploy_scout(ScoutType.MEDIUM)
        for _ in range(config.get("heavy", 0)):
            self.swarm.deploy_scout(ScoutType.HEAVY)

    def init_clones(self, clone_positions: list):
        for pos in clone_positions:
            self.clone_swarm.add_clone(pos)

    def promote_spotters(self, scout_ids: List[int]):
        for sid in scout_ids:
            self.spotter_manager.promote_to_spotter(sid)

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        if self.legacy_exporter:
            self.legacy_exporter.export_snapshot()

    def tick(self):
        if not self.running:
            return None
        self.tick_count += 1
        beat = self.sync.beat()
        self.brain.feed_beat(beat)
        window = self.brain.analyze(beat.tick)
        self.swarm.sync_beat(beat.tick)
        self.spotter_manager.update_all(beat.tick)
        strike = self.pulse.sync_beat()
        self.clone_swarm.broadcast_heartbeat(beat.tick, beat.phase)
        self.inspector.inspect(beat.tick)
        metrics = self.metrics.collect()
        
        # Адаптивная подстройка буфера
        self.buffer.adjust_parameters(metrics, beat.tick)
        
        if self.tick_count % 10 == 0:
            dead_clones = self.clone_swarm.check_all_clones(beat.tick)
            if dead_clones:
                print(f"⚠️ Мёртвые клоны: {dead_clones}")
            warnings = self.metrics.detect_anomalies_in_metrics()
            for w in warnings:
                print(f"   {w}")
        if self.legacy_exporter and self.tick_count % 10 == 0:
            self.legacy_exporter.export_snapshot()
        return {
            "beat": beat,
            "window": window,
            "strike": strike,
            "metrics": metrics,
            "clones": len(self.clone_swarm.clones),
            "selidka": self.metrics.selidka_emoji
        }


# ====================================================
# ТОЧКА ВХОДА (INFINITE LOOP)
# ====================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧱 РИЗОМА-2 ПОЛНАЯ СБОРКА (АДАПТИВНАЯ)")
    print("="*70)
    print("🐟 Атлантическая сельдь на мониторе: фаза в норме")
    print("="*70 + "\n")

    # Создаём систему
    r = RhizomeComplete(frequency_hz=1.0, sync_word=11895)

    # Legacy данные (имитация)
    legacy = {
        "successful_strikes": [(10, 0.02, 2.5), (12, 0.98, 3.0), (15, 0.05, 2.0)],
        "anomaly_positions": [(100, 100, 2.0), (200, -50, 3.0), (-150, 80, 1.5)],
        "patterns": {"old_alpha": 0.7, "old_beta": 0.9},
        "reference_points": [((1000, 0), 0.0), ((0, 1000), 0.25)]
    }
    r.init_legacy(legacy)

    # Разведчики
    r.deploy_scouts({"light": 5, "medium": 2, "heavy": 1})

    # Клоны
    r.init_clones([(100, 100), (-100, -100), (0, 200)])

    # Назначаем корректировщиков (первые два средних)
    medium_scouts = [s.id for s in r.swarm.scouts if s.type == ScoutType.MEDIUM][:2]
    r.promote_spotters(medium_scouts)

    # Запуск
    r.start()
    print("🚀 Система запущена. Бесконечный цикл... Нажми Ctrl+C для остановки.\n")

    # Бесконечный цикл
    try:
        while True:
            state = r.tick()
            if r.tick_count % 10 == 0:
                m = state["metrics"]
                rep = r.metrics.report()
                print(f"\n📊 Такт {r.tick_count} {state['selidka']}")
                print(f"   Аномалий: {m.anomalies_found}, Целей: {m.targets_promoted}")
                print(f"   Ударов: {m.strikes_attempted}, Успешно: {m.strikes_successful}")
                print(f"   Разведчиков: {m.active_scouts}, Корректировщиков: {m.active_spotters}")
                print(f"   Перезарядка пульса: {m.pulse_cooldown:.1f}, Порог цели: {m.target_promotion_threshold:.1f}")
                print(f"   Эффективность: {rep['efficiency']:.1%}, Класс: {rep['stability_class']}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал остановки")
        r.stop()

    print("\n" + "="*70)
    print("✅ РАБОТА ЗАВЕРШЕНА. Селёдка на месте 🐟")
    print("="*70 + "\n")
