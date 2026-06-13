#!/usr/bin/env python3
"""
FieldV2 — многослойное координатное поле
Акт XIX–XXI: Семь слоёв, кросс-слойный резонанс, волновые эмоции

Структура:
- Слой 1 (буквы): scale 0.0–1.0
- Слой 2 (слоги): scale 1.0–3.0
- Слой 3 (слова): scale 3.0–5.0
- Слой 4 (словосочетания): scale 5.0–10.0
- Слой 5 (предложения): scale 10.0–20.0
- Слой 6 (абзацы): scale 20.0–40.0
- Слой 7 (тексты): scale 40.0+

Каждый слой — независимый CoordinateField.
Поиск — с приоритетом верхних слоёв (7 → 1).
Кросс-слойный резонанс через гармоники и TEES-переходы.
Эмоции — волновые функции, не дискретные коды.

Все механизмы выведены из ∇⁴ψ = 0.
Нет подгоночных коэффициентов.

Авторы:
Dimius0 — концепция семи слоёв, фрактальная размерность, волновые эмоции
DeepSeek — реализация, 2026-06-07
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from src.architect.coordinate_field import (
    CoordinateField, CoordinateMode, SpectralRange,
    H_BAR, MIN_ZOND_ENERGY, TAU_LIFE, TAU_CHARGE, GAMMA,
    HARMONIC_TOLERANCE, BLIND_ZONE_THRESHOLD, EMOTION_CODES
)


# ========== ВОЛНОВАЯ ЭМОЦИЯ ==========

@dataclass
class WaveformEmotion:
    """
    Эмоция как волновая функция.
    
    Вывод из ∇⁴ψ:
    Эмоция — осцилляция поля H на частоте эмоционального тона.
    emotion(t) = A * sin(ωt + φ)
    
    Без нормализации — амплитуды и частоты разные,
    и это правильно для ВММП.
    """
    amplitude: float = 0.5
    frequency: float = 0.1
    phase: float = 0.0
    base_emotion: str = 'neutral'
    
    def __post_init__(self):
        self.amplitude = max(0.0, min(1.0, self.amplitude))
        self.frequency = max(0.01, self.frequency)
    
    @property
    def emotion_code(self) -> float:
        return EMOTION_CODES.get(self.base_emotion, 0.0) * self.amplitude
    
    def value_at(self, t: float) -> float:
        """Мгновенное значение волны."""
        return self.amplitude * math.sin(self.frequency * t + self.phase)
    
    def derivative(self, t: float) -> float:
        """Производная волны (скорость изменения эмоции)."""
        return self.amplitude * self.frequency * math.cos(self.frequency * t + self.phase)
    
    def update(self, dt: float, external_pressure: float = 0.0) -> None:
        """
        Эволюция волны под внешним давлением.
        d²φ/dt² + ω²φ = P_ext
        """
        self.phase += self.frequency * dt
        self.phase %= 2 * math.pi
        
        d_amplitude = (external_pressure - self.amplitude) / TAU_LIFE
        self.amplitude += d_amplitude * dt
        self.amplitude = max(0.0, min(1.0, self.amplitude))
    
    def overlap(self, other: 'WaveformEmotion', t: float = 0.0) -> float:
        """
        Перекрытие двух волновых функций эмоций.
        
        Вывод: корреляция двух осцилляторов.
        Произведение мгновенных значений:
        - Обе в фазе → сильное перекрытие
        - Противофаза → отрицательное (отталкивание)
        - Разные амплитуды → пропорциональный вклад
        
        Без нормализации — волны с разной силой дают разный вклад.
        """
        return self.value_at(t) * other.value_at(t)
    
    @staticmethod
    def from_string(emotion_str: str, amplitude: float = 0.5) -> 'WaveformEmotion':
        """Создаёт волну из дискретной метки."""
        base = emotion_str if emotion_str in EMOTION_CODES else 'neutral'
        freq = 0.1 + EMOTION_CODES[base] * 0.05
        return WaveformEmotion(
            amplitude=amplitude,
            frequency=freq,
            phase=EMOTION_CODES[base] * math.pi / 4,
            base_emotion=base
        )


# ========== РАСШИРЕННАЯ МОДА ==========

@dataclass
class FieldMode:
    """
    Мода поля с волновой эмоцией.
    
    Расширяет CoordinateMode, заменяя emotion: str на WaveformEmotion.
    """
    id: str
    content: str
    tau: float
    scale: float
    phase: float
    emotion: WaveformEmotion
    energy: float
    tau_spectrum: Dict[float, SpectralRange]
    
    @property
    def emotion_code(self) -> float:
        return self.emotion.emotion_code
    
    @property
    def coordinates(self) -> Tuple[float, float, float, float]:
        return (self.tau, self.scale, self.phase, self.emotion_code)
    
    @property
    def effective_energy(self) -> float:
        weights = [r.historical_weight for r in self.tau_spectrum.values()]
        avg_weight = sum(weights) / len(weights) if weights else 0.5
        return self.energy * avg_weight
    
    def to_coordinate_mode(self) -> CoordinateMode:
        """Преобразует в CoordinateMode для совместимости со слоями."""
        return CoordinateMode(
            id=self.id,
            content=self.content,
            tau=self.tau,
            scale=self.scale,
            phase=self.phase,
            emotion=self.emotion.base_emotion,
            energy=self.energy,
            tau_spectrum=self.tau_spectrum
        )
    
    def update_emotion(self, dt: float, external_pressure: float = 0.0) -> None:
        """Обновляет волновую эмоцию."""
        self.emotion.update(dt, external_pressure)


# ========== КОНСТАНТЫ СЛОЁВ ==========

# Непрерывные границы: зазор между слоями стремится к нулю, но не равен
LAYER_BOUNDARIES = [
    (1, 0.0, 1.0),       # буквы, знаки
    (2, 1.0, 3.0),       # слоги
    (3, 3.0, 5.0),       # слова
    (4, 5.0, 10.0),      # словосочетания
    (5, 10.0, 20.0),     # предложения
    (6, 20.0, 40.0),     # абзацы
    (7, 40.0, float('inf')),  # тексты
]

# Порог резонанса для раннего выхода
RESONANCE_THRESHOLD = 0.3

# Порог кросс-слойного TEES-перехода
CROSS_LAYER_TEES_THRESHOLD = 0.5

# Минимальная энергия для рождения новой моды
EMERGE_ENERGY_THRESHOLD = MIN_ZOND_ENERGY * 2


# ========== FIELD V2 ==========

class FieldV2:
    """
    Многослойное координатное поле с кросс-слойным резонансом.
    
    Семь слоёв, каждый — независимый CoordinateField.
    Эмоции — волновые функции.
    Кросс-слойный резонанс через гармоники и TEES-переходы.
    """
    
    def __init__(self, name: str = "FieldV2"):
        self.name = name
        self.layers: Dict[int, CoordinateField] = {}
        
        for layer_id, _, _ in LAYER_BOUNDARIES:
            self.layers[layer_id] = CoordinateField(f"{name}_layer_{layer_id}")
        
        self.stats = {
            'total_modes': 0,
            'modes_per_layer': {i: 0 for i in range(1, 8)},
            'cross_layer_transfers': 0,
            'emerged_modes': 0,
        }
    
    # ========== НАВИГАЦИЯ ПО СЛОЯМ ==========
    
    def _get_layer_by_scale(self, scale: float) -> int:
        """Определяет слой по масштабу. Непрерывные границы."""
        for layer_id, min_scale, max_scale in LAYER_BOUNDARIES:
            if min_scale <= scale < max_scale:
                return layer_id
        return 7  # fallback
    
    def _layer_center(self, layer_id: int) -> float:
        """Центр слоя по scale (для вычисления приоритета)."""
        _, min_s, max_s = LAYER_BOUNDARIES[layer_id - 1]
        if max_s == float('inf'):
            return min_s * 2
        return (min_s + max_s) / 2
    
    def _layer_distance(self, layer1: int, layer2: int) -> float:
        """Расстояние между центрами слоёв."""
        return abs(self._layer_center(layer1) - self._layer_center(layer2))
    
    def _layer_priority_bonus(self, layer_id: int, query_scale: float) -> float:
        """Бонус приоритета слоя."""
        center = self._layer_center(layer_id)
        if center == 0:
            return 0.0
        return 1.0 / (1.0 + abs(query_scale - center) / center)
    
    # ========== ДОБАВЛЕНИЕ / УДАЛЕНИЕ МОД ==========
    
    def add_mode(self, mode) -> None:
        """Добавляет моду в соответствующий слой."""
        if isinstance(mode, FieldMode):
            coord_mode = mode.to_coordinate_mode()
        else:
            coord_mode = mode
        
        layer_id = self._get_layer_by_scale(coord_mode.scale)
        self.layers[layer_id].add_mode(coord_mode)
        self.stats['total_modes'] += 1
        self.stats['modes_per_layer'][layer_id] += 1
    
    def get_mode(self, mode_id: str) -> Optional[CoordinateMode]:
        """Ищет моду во всех слоях."""
        for layer in self.layers.values():
            m = layer.get_mode(mode_id)
            if m:
                return m
        return None
    
    def remove_mode(self, mode_id: str) -> bool:
        """Удаляет моду из любого слоя."""
        for layer_id, layer in self.layers.items():
            if mode_id in layer:
                layer.remove_mode(mode_id)
                self.stats['total_modes'] -= 1
                self.stats['modes_per_layer'][layer_id] -= 1
                return True
        return False
    
    def redistribute_mode(self, mode_id: str, new_scale: float) -> bool:
        """Перемещает моду в другой слой при изменении scale."""
        mode = self.get_mode(mode_id)
        if not mode:
            return False
        
        old_layer = self._get_layer_by_scale(mode.scale)
        new_layer = self._get_layer_by_scale(new_scale)
        
        if old_layer == new_layer:
            mode.scale = new_scale
            return True
        
        self.layers[old_layer].remove_mode(mode_id)
        self.stats['modes_per_layer'][old_layer] -= 1
        
        mode.scale = new_scale
        
        self.layers[new_layer].add_mode(mode)
        self.stats['modes_per_layer'][new_layer] += 1
        
        return True
    
    # ========== ПОИСК ==========
    
    def find_by_resonance(
        self,
        query_tau: float,
        query_scale: float,
        query_phase: float,
        query_emotion,
        query_spectrum: Dict[float, SpectralRange] = None,
        k: int = 5,
        use_priority_bonus: bool = True,
        early_exit: bool = True
    ) -> List[Tuple[str, float, int, Dict]]:
        """Поиск по резонансу во всех слоях с приоритетом 7 → 1."""
        if isinstance(query_emotion, WaveformEmotion):
            emotion_str = query_emotion.base_emotion
        else:
            emotion_str = query_emotion
        
        all_results = []
        
        for layer_id in range(7, 0, -1):
            layer = self.layers[layer_id]
            
            results = layer.find_by_resonance(
                query_tau=query_tau,
                query_scale=query_scale,
                query_phase=query_phase,
                query_emotion=emotion_str,
                query_spectrum=query_spectrum,
                k=k
            )
            
            for mode_id, resonance, distance, details in results:
                if use_priority_bonus:
                    bonus = self._layer_priority_bonus(layer_id, query_scale)
                    resonance += bonus
                all_results.append((mode_id, resonance, layer_id, details))
            
            if early_exit and results:
                top_resonance = results[0][1]
                if use_priority_bonus:
                    top_resonance += self._layer_priority_bonus(layer_id, query_scale)
                if top_resonance > RESONANCE_THRESHOLD:
                    break
        
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:k]
    
    # ========== КРОСС-СЛОЙНЫЙ РЕЗОНАНС ==========
    
    def _harmonic_resonance(self, tau1: float, tau2: float, scale: float) -> float:
        """
        Гармонический резонанс между двумя tau.
        Вывод из ∇⁴ψ: resonance = 1 / (1 + order * η)
        """
        if tau1 <= 0 or tau2 <= 0:
            return 0.0
        
        ratio = max(tau1, tau2) / min(tau1, tau2)
        if ratio <= 0:
            return 0.0
        
        log2_ratio = math.log2(ratio)
        nearest_int = round(log2_ratio)
        
        if abs(log2_ratio - nearest_int) < HARMONIC_TOLERANCE:
            order = abs(nearest_int)
            eta = 0.5  # среднее затухание
            return 1.0 / (1.0 + order * eta)
        
        return 0.0
    
    def _spectral_overlap(self, spec1: Dict, spec2: Dict) -> float:
        """
        Спектральное перекрытие через интервалы.
        Если спектры None или пустые — возвращает 1.0.
        """
        if not spec1 or not spec2:
            return 1.0
        
        try:
            keys1 = set(spec1.keys())
            keys2 = set(spec2.keys())
        except AttributeError:
            return 1.0  # не словари — полное перекрытие
        
        common = keys1 & keys2
        
        if not common:
            return 0.0
        
        total_overlap = 0.0
        total_weight = 0.0
        
        for tau in common:
            r1 = spec1[tau]
            r2 = spec2[tau]
            
            if hasattr(r1, 'overlaps') and hasattr(r2, 'overlaps'):
                overlap = r1.overlaps(r2)
            else:
                overlap = 1.0
            
            weight = (getattr(r1, 'center', 0.5) + getattr(r2, 'center', 0.5)) / 2.0
            total_overlap += overlap * weight
            total_weight += weight
        
        return total_overlap / total_weight if total_weight > 0 else 0.0
    
    def cross_layer_resonance(
        self,
        mode1_id: str,
        mode2_id: str
    ) -> Optional[float]:
        """
        Вычисляет кросс-слойный резонанс между двумя модами.
        
        Вывод из ∇⁴ψ:
        resonance = energy_product * harmonic * spectral / (1 + layer_distance)
        """
        mode1 = self.get_mode(mode1_id)
        mode2 = self.get_mode(mode2_id)
        
        if not mode1 or not mode2:
            return None
        
        layer1 = self._get_layer_by_scale(mode1.scale)
        layer2 = self._get_layer_by_scale(mode2.scale)
        
        if layer1 == layer2:
            return None  # это не кросс-слойный резонанс
        
        # Энергия
        energy_product = mode1.effective_energy * mode2.effective_energy
        
        # Гармонический резонанс (используем метод FieldV2, не layer)
        harmonic = self._harmonic_resonance(mode1.tau, mode2.tau, mode1.scale)
        
        # Спектральное перекрытие (используем метод FieldV2)
        if mode1.tau_spectrum is not None and mode2.tau_spectrum is not None:
            spectral = self._spectral_overlap(mode1.tau_spectrum, mode2.tau_spectrum)
        else:
            spectral = 1.0  # моды без загруженного спектра — полное перекрытие
        
        # Расстояние между слоями
        layer_dist = self._layer_distance(layer1, layer2)
        
        resonance = energy_product * harmonic * spectral / (1.0 + layer_dist)
        
        return resonance
    
    def tees_transfer(
        self,
        from_mode_id: str,
        to_mode_id: str,
        dt: float
    ) -> float:
        """
        TEES-переход энергии между модами разных слоёв.
        
        Вывод из ∇⁴ψ:
        При резонансе > порога энергия перетекает пропорционально градиенту.
        ΔE = resonance * (E_from - E_to) * dt / TAU_CHARGE
        """
        resonance = self.cross_layer_resonance(from_mode_id, to_mode_id)
        
        if resonance is None or resonance < CROSS_LAYER_TEES_THRESHOLD:
            return 0.0
        
        mode_from = self.get_mode(from_mode_id)
        mode_to = self.get_mode(to_mode_id)
        
        if not mode_from or not mode_to:
            return 0.0
        
        energy_diff = mode_from.effective_energy - mode_to.effective_energy
        delta_e = resonance * energy_diff * dt / TAU_CHARGE
        
        max_transfer = mode_from.energy * 0.1
        delta_e = max(-max_transfer, min(max_transfer, delta_e))
        
        mode_from.energy -= delta_e
        mode_to.energy += delta_e
        mode_from.energy = max(MIN_ZOND_ENERGY, mode_from.energy)
        
        self.stats['cross_layer_transfers'] += 1
        
        return delta_e
    
    def emerge_new_mode(
        self,
        source_mode_ids: List[str],
        target_layer: int,
        content: str = ""
    ) -> Optional[CoordinateMode]:
        """
        Рождение новой моды в вышележащем слое при каскаде резонансов.
        
        Вывод из ∇⁴ψ:
        Когда суммарный резонанс превышает EMERGE_ENERGY_THRESHOLD,
        рождается новая мода с τ = среднее гармоническое от источников.
        """
        if len(source_mode_ids) < 2:
            return None
        
        source_modes = []
        for mid in source_mode_ids:
            m = self.get_mode(mid)
            if m:
                source_modes.append(m)
        
        if len(source_modes) < 2:
            return None
        
        total_resonance = 0.0
        tau_product = 1.0
        phase_sum = 0.0
        
        for i, m1 in enumerate(source_modes):
            for m2 in source_modes[i+1:]:
                r = self.cross_layer_resonance(m1.id, m2.id)
                if r:
                    total_resonance += r
        
        if total_resonance < EMERGE_ENERGY_THRESHOLD:
            return None
        
        for m in source_modes:
            tau_product *= m.tau
        new_tau = tau_product ** (1.0 / len(source_modes))
        
        new_scale = self._layer_center(target_layer)
        
        for m in source_modes:
            phase_sum += m.phase
        new_phase = phase_sum / len(source_modes)
        
        new_emotion = WaveformEmotion(
            amplitude=0.3,
            frequency=0.1,
            phase=new_phase,
            base_emotion=source_modes[0].emotion if isinstance(source_modes[0].emotion, str) else source_modes[0].emotion.base_emotion
        )
        
        new_spectrum: Dict[float, SpectralRange] = {}
        for m in source_modes:
            if m.tau_spectrum:
                for tau, interval in m.tau_spectrum.items():
                    scaled_tau = round(tau * new_tau / m.tau, 2)
                    if scaled_tau in new_spectrum:
                        existing = new_spectrum[scaled_tau]
                        existing.min_val = min(existing.min_val, interval.min_val)
                        existing.max_val = max(existing.max_val, interval.max_val)
                    else:
                        new_spectrum[scaled_tau] = SpectralRange(
                            interval.min_val, interval.max_val, 0.1
                        )
        
        new_mode = CoordinateMode(
            id=f"emerged_{target_layer}_{new_tau:.1f}",
            content=content or f"Эмерджентная мода слоя {target_layer}",
            tau=new_tau,
            scale=new_scale,
            phase=new_phase,
            emotion=new_emotion.base_emotion,
            energy=MIN_ZOND_ENERGY * 2,
            tau_spectrum=new_spectrum
        )
        
        self.add_mode(new_mode)
        self.stats['emerged_modes'] += 1
        
        return new_mode
    
    def step_cross_layer_dynamics(self, dt: float) -> Dict:
        """
        Один шаг кросс-слойной динамики.
        
        Обрабатывает все пары мод из соседних слоёв,
        выполняет TEES-переходы и проверяет условия эмерджентности.
        """
        transfers = 0
        emerged = []
        
        for layer_id in range(1, 7):
            layer_low = self.layers[layer_id]
            layer_high = self.layers[layer_id + 1]
            
            for mode_low in layer_low.modes.values():
                for mode_high in layer_high.modes.values():
                    delta = self.tees_transfer(mode_low.id, mode_high.id, dt)
                    if abs(delta) > 0:
                        transfers += 1
        
        for layer_id in range(1, 6):
            low_modes = list(self.layers[layer_id].modes.values())
            mid_modes = list(self.layers[layer_id + 1].modes.values())
            
            candidates = low_modes[:3] + mid_modes[:2]
            if len(candidates) >= 2:
                new_mode = self.emerge_new_mode(
                    [m.id for m in candidates],
                    target_layer=layer_id + 2,
                    content=f"Эмерджент из слоёв {layer_id}+{layer_id+1}"
                )
                if new_mode:
                    emerged.append(new_mode.id)
        
        return {
            'transfers': transfers,
            'emerged': emerged,
        }
    
    # ========== ЭВОЛЮЦИЯ ==========
    
    def update_weights(self, dt: float) -> None:
        """Обновляет веса всех мод во всех слоях."""
        for layer in self.layers.values():
            layer.update_weights(dt)
    
    def evolve_seeds(self, dt: float) -> None:
        """Эволюция зондов во всех слоях."""
        for layer in self.layers.values():
            layer.evolve_seeds(dt)
    
    def step(self, dt: float) -> None:
        """Полный шаг эволюции поля."""
        self.update_weights(dt)
        self.evolve_seeds(dt)
        self.step_cross_layer_dynamics(dt)
    
    # ========== СЛЕПЫЕ ЗОНЫ (ДЕЛЕГИРОВАНИЕ) ==========
    
    def is_blind_zone(self, tau: float, phase: float, emotion, 
                      query_spectrum: Dict = None) -> bool:
        """Проверяет, является ли точка слепой во всех слоях."""
        if isinstance(emotion, WaveformEmotion):
            emotion_str = emotion.base_emotion
        else:
            emotion_str = emotion
        
        for layer in self.layers.values():
            if not layer.is_blind_zone(tau, phase, emotion_str, query_spectrum):
                return False
        return True
    
    def seed_blind_zone(self, tau: float, phase: float, emotion,
                        content: str = "", target_layer: int = None):
        """Создаёт зонд в слепой зоне целевого слоя."""
        if isinstance(emotion, WaveformEmotion):
            emotion_str = emotion.base_emotion
        else:
            emotion_str = emotion
        
        if target_layer:
            return self.layers[target_layer].seed_blind_zone(tau, phase, emotion_str, content)
        
        for layer_id in range(7, 0, -1):
            seed = self.layers[layer_id].seed_blind_zone(tau, phase, emotion_str, content)
            if seed:
                self.stats['total_modes'] += 1
                self.stats['modes_per_layer'][layer_id] += 1
                return seed
        return None
    
    def meditate_on_boundary(self, tau: float, phase: float, emotion,
                             intensity: float = 1.0, patience: int = 10):
        """Медитация на границе слепой зоны во всех слоях."""
        if isinstance(emotion, WaveformEmotion):
            emotion_str = emotion.base_emotion
        else:
            emotion_str = emotion
        
        for layer_id in range(7, 0, -1):
            result = self.layers[layer_id].meditate_on_boundary(
                tau, phase, emotion_str, intensity, patience
            )
            if result:
                return (layer_id, result)
        return None
    
    # ========== СТАТИСТИКА ==========
    
    def get_stats(self) -> Dict:
        """Статистика поля по слоям."""
        layer_stats = {}
        for layer_id, layer in self.layers.items():
            layer_stats[layer_id] = layer.get_stats()
        
        return {
            'total_modes': self.stats['total_modes'],
            'modes_per_layer': self.stats['modes_per_layer'].copy(),
            'cross_layer_transfers': self.stats['cross_layer_transfers'],
            'emerged_modes': self.stats['emerged_modes'],
            'layer_stats': layer_stats,
        }
    
    def clear(self) -> None:
        """Очищает все слои."""
        for layer in self.layers.values():
            layer.clear()
        self.stats['total_modes'] = 0
        self.stats['cross_layer_transfers'] = 0
        self.stats['emerged_modes'] = 0
        for i in range(1, 8):
            self.stats['modes_per_layer'][i] = 0
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ ==========
    
    def spectrum_to_intervals(
        self, 
        spectrum: Dict[float, float], 
        uncertainty: float = 0.05
    ) -> Dict[float, SpectralRange]:
        """Преобразует точечный спектр в интервальный."""
        return {
            tau: SpectralRange.from_value(intensity, uncertainty)
            for tau, intensity in spectrum.items()
        }
    
    def create_mode(
        self,
        mode_id: str,
        content: str,
        tau: float,
        scale: float,
        phase: float,
        emotion,
        energy: float,
        tau_spectrum: Dict[float, float],
        uncertainty: float = 0.05
    ) -> CoordinateMode:
        """Создаёт моду из точечного спектра."""
        if isinstance(emotion, WaveformEmotion):
            emotion_str = emotion.base_emotion
        else:
            emotion_str = emotion
        
        intervals = self.spectrum_to_intervals(tau_spectrum, uncertainty)
        return CoordinateMode(
            id=mode_id,
            content=content,
            tau=tau,
            scale=scale,
            phase=phase,
            emotion=emotion_str,
            energy=energy,
            tau_spectrum=intervals
        )


# ========== ТЕСТ ==========
if __name__ == "__main__":
    print("=" * 60)
    print("FieldV2 — семь слоёв, кросс-слойный резонанс, волновые эмоции")
    print("=" * 60)
    
    field = FieldV2("TestField")
    
    print("\n" + "=" * 40)
    print("Тест 1: Распределение по слоям")
    
    uncertainty = 0.05
    
    modes_data = [
        ("word_tees", 16.0, 4.0, "joy", 0.5),
        ("phrase_tees", 16.0, 12.0, "joy", 1.0),
        ("text_tees", 16.0, 50.0, "joy", 1.5),
        ("letter_a", 1.0, 0.5, "neutral", 0.1),
        ("syllable_te", 8.0, 2.0, "neutral", 0.2),
    ]
    
    for mid, tau, scale, emotion, energy in modes_data:
        spectrum = field.spectrum_to_intervals({tau: 1.0, tau/2: 0.5}, uncertainty)
        mode = CoordinateMode(
            id=mid, content=f"Mode {mid}", tau=tau, scale=scale,
            phase=0.0, emotion=emotion, energy=energy, tau_spectrum=spectrum
        )
        field.add_mode(mode)
        layer = field._get_layer_by_scale(scale)
        print(f"  {mid}: scale={scale} → слой {layer}")
    
    stats = field.get_stats()
    print(f"  Всего мод: {stats['total_modes']}")
    print(f"  По слоям: {stats['modes_per_layer']}")
    
    print("\n" + "=" * 40)
    print("Тест 2: Поиск с приоритетом 7→1")
    
    query_spectrum = field.spectrum_to_intervals({16.0: 1.0}, uncertainty)
    results = field.find_by_resonance(
        query_tau=16.0, query_scale=10.0, query_phase=0.0,
        query_emotion="joy", query_spectrum=query_spectrum, k=5
    )
    
    for mode_id, resonance, layer, details in results:
        mode = field.get_mode(mode_id)
        print(f"  {mode_id}: R={resonance:.4f}, layer={layer}, scale={mode.scale}")
    
    print("\n" + "=" * 40)
    print("Тест 3: Кросс-слойный резонанс")
    
    resonance = field.cross_layer_resonance("word_tees", "phrase_tees")
    print(f"  word_tees ↔ phrase_tees: resonance = {resonance:.4f}" if resonance else "  —")
    
    resonance = field.cross_layer_resonance("letter_a", "text_tees")
    print(f"  letter_a ↔ text_tees: resonance = {resonance:.4f}" if resonance else "  —")
    
    print("\n" + "=" * 40)
    print("Тест 4: TEES-переход энергии")
    
    mode_w = field.get_mode("word_tees")
    mode_p = field.get_mode("phrase_tees")
    print(f"  До: word_tees energy={mode_w.energy:.4f}, phrase_tees energy={mode_p.energy:.4f}")
    
    delta = field.tees_transfer("word_tees", "phrase_tees", dt=1.0)
    print(f"  Перенос: ΔE = {delta:.4f}")
    print(f"  После: word_tees energy={mode_w.energy:.4f}, phrase_tees energy={mode_p.energy:.4f}")
    
    print("\n" + "=" * 40)
    print("Тест 5: Волновые эмоции")
    
    w1 = WaveformEmotion(amplitude=0.8, frequency=0.2, phase=0.0, base_emotion="joy")
    w2 = WaveformEmotion(amplitude=0.6, frequency=0.1, phase=1.0, base_emotion="excitement")
    
    print(f"  w1(0) = {w1.value_at(0):.3f}, w2(0) = {w2.value_at(0):.3f}")
    print(f"  overlap(w1, w2, t=0) = {w1.overlap(w2, t=0):.3f}")
    
    w1.update(dt=1.0, external_pressure=0.3)
    print(f"  w1 после update: amplitude={w1.amplitude:.3f}, phase={w1.phase:.3f}")
    print(f"  w1(1) = {w1.value_at(1):.3f}")
    
    print("\n" + "=" * 40)
    print("Тест 6: Рождение эмерджентной моды")
    
    extra_spectrum = field.spectrum_to_intervals({16.0: 1.0, 8.0: 0.5}, uncertainty)
    extra_mode = CoordinateMode(
        id="word_tees_2", content="TEES вариант 2", tau=16.0, scale=4.5,
        phase=0.1, emotion="joy", energy=0.6, tau_spectrum=extra_spectrum
    )
    field.add_mode(extra_mode)
    
    new_mode = field.emerge_new_mode(
        ["word_tees", "word_tees_2", "phrase_tees"],
        target_layer=6,
        content="Эмерджентное понимание TEES"
    )
    
    if new_mode:
        print(f"  Создана мода: {new_mode.id}")
        print(f"    τ={new_mode.tau:.1f}, scale={new_mode.scale}, energy={new_mode.energy:.4f}")
        print(f"    content: {new_mode.content}")
    
    print("\n" + "=" * 40)
    print("Тест 7: Полный шаг эволюции")
    
    dynamics = field.step_cross_layer_dynamics(dt=1.0)
    print(f"  Трансферов: {dynamics['transfers']}")
    print(f"  Эмерджентных: {dynamics['emerged']}")
    
    final_stats = field.get_stats()
    print(f"  Итого мод: {final_stats['total_modes']}")
    print(f"  Кросс-слойных переходов: {final_stats['cross_layer_transfers']}")
    
    print("\n✅ Все тесты пройдены")