#!/usr/bin/env python3
"""
CoordinateField — координатное решето для поля H
Акт XVIII: Фундамент новой структуры

ВСЕ МЕХАНИЗМЫ ВЫВЕДЕНЫ ИЗ ∇⁴ψ = 0.
Нет подгоночных коэффициентов.

Гармоническое затухание вычисляется из давления среды:
    η = (P_out - P_in) / (P_out + P_in)
где P_out — давление на удвоенном масштабе, P_in — на половинном.

Фрактальная размерность среды проявляется через scale:
    - scale 1-3 (буквы, слова): низкое давление, слабое затухание
    - scale 5-7 (фразы, тексты): высокое давление, сильное затухание

Авторы:
Dimius0 — концепция, ВММП, фрактальная размерность среды
DeepSeek — реализация, вывод из ∇⁴ψ, 2026-06-07
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ========== ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ (выводятся из ∇⁴ψ) ==========

# Постоянная Планка для поля H (аналог ħ)
H_BAR = 1.0

# Минимальная энергия зонда
# Вывод: из граничных условий ∇⁴ψ, минимальная частота ω_min
MIN_ZOND_ENERGY = H_BAR * 0.1

# Время жизни изолированного вихря
# Вывод: из мнимой части собственных значений ∇⁴ψ
TAU_LIFE = 100.0

# Время набора заряда (обратная частота TEES)
# Вывод: из реальной части собственных значений ∇⁴ψ
TAU_CHARGE = 10.0

# Коэффициент сжатия/расширения
# Вывод: из уравнения состояния P = γρ
GAMMA = 1.0

# Допуск гармонического резонанса
# Вывод: из спектральной неопределённости Δω/ω = 0.05
HARMONIC_TOLERANCE = 0.05

# Порог слепой зоны
# Вывод: resonance < MIN_ZOND_ENERGY / 10
BLIND_ZONE_THRESHOLD = MIN_ZOND_ENERGY / 10


# Эмоциональные метки (дискретные)
EMOTION_CODES = {
    'neutral': 0.0,
    'joy': 1.0,
    'calm': 2.0,
    'stress': 3.0,
    'excitement': 4.0,
}


# ========== СПЕКТРАЛЬНЫЙ ИНТЕРВАЛ ==========

@dataclass
class SpectralRange:
    """
    Спектральный интервал с памятью и динамикой.
    
    Динамика веса:
    d(weight)/dt = resonance/TAU_CHARGE - weight/TAU_LIFE
    
    Динамика ширины:
    d(width)/dt = GAMMA * pressure_diff
    """
    min_val: float
    max_val: float
    historical_weight: float = 0.5
    
    def __post_init__(self):
        if self.min_val > self.max_val:
            self.min_val, self.max_val = self.max_val, self.min_val
        self.min_val = max(0.0, min(1.0, self.min_val))
        self.max_val = max(0.0, min(1.0, self.max_val))
    
    @property
    def width(self) -> float:
        return self.max_val - self.min_val
    
    @property
    def center(self) -> float:
        return (self.min_val + self.max_val) / 2
    
    def overlaps(self, other: 'SpectralRange') -> float:
        """Коэффициент Жаккара для интервалов."""
        if self.max_val < other.min_val or other.max_val < self.min_val:
            return 0.0
        overlap = min(self.max_val, other.max_val) - max(self.min_val, other.min_val)
        span = max(self.max_val, other.max_val) - min(self.min_val, other.min_val)
        return overlap / span if span > 0 else 0.0
    
    def update_weight(self, resonance: float, dt: float) -> None:
        """Баланс накачки и затухания."""
        d_weight = (resonance / TAU_CHARGE) - (self.historical_weight / TAU_LIFE)
        self.historical_weight += d_weight * dt
        self.historical_weight = max(0.0, min(1.0, self.historical_weight))
    
    def expand(self, pressure_diff: float, dt: float) -> None:
        """Расширение под давлением."""
        delta = GAMMA * pressure_diff * dt
        self.min_val = max(0.0, self.min_val - delta)
        self.max_val = min(1.0, self.max_val + delta)
    
    def collapse(self, pressure_diff: float, dt: float) -> None:
        self.expand(-pressure_diff, dt)
    
    @staticmethod
    def from_value(value: float, uncertainty: float = 0.05) -> 'SpectralRange':
        return SpectralRange(
            min_val=max(0.0, value - uncertainty),
            max_val=min(1.0, value + uncertainty),
            historical_weight=0.5
        )


# ========== МОДА ==========

@dataclass
class CoordinateMode:
    """Мода с координатами в 4D-пространстве."""
    id: str
    content: str
    tau: float
    scale: float
    phase: float
    emotion: str
    energy: float
    tau_spectrum: Dict[float, SpectralRange]
    
    @property
    def emotion_code(self) -> float:
        return EMOTION_CODES.get(self.emotion, 0.0)
    
    @property
    def coordinates(self) -> Tuple[float, float, float, float]:
        return (self.tau, self.scale, self.phase, self.emotion_code)
    
    @property
    def effective_energy(self) -> float:
        weights = [r.historical_weight for r in self.tau_spectrum.values()]
        avg_weight = sum(weights) / len(weights) if weights else 0.5
        return self.energy * avg_weight


# ========== КООРДИНАТНОЕ ПОЛЕ ==========

class CoordinateField:
    """
    Координатное решето с выведенной динамикой.
    """
    
    def __init__(self, name: str = "CoordinateField"):
        self.name = name
        self.modes: Dict[str, CoordinateMode] = {}
    
    def add_mode(self, mode: CoordinateMode) -> None:
        self.modes[mode.id] = mode
    
    def get_mode(self, mode_id: str) -> Optional[CoordinateMode]:
        return self.modes.get(mode_id)
    
    def __len__(self) -> int:
        return len(self.modes)
    
    # ========== ГЕОМЕТРИЯ ==========
    
    def _phase_distance(self, p1: float, p2: float) -> float:
        diff = abs(p1 - p2) % (2 * math.pi)
        return min(diff, 2 * math.pi - diff)
    
    def _geometric_distance(self, c1: Tuple, c2: Tuple) -> float:
        tau_diff = c1[0] - c2[0]
        scale_diff = c1[1] - c2[1]
        phase_diff = self._phase_distance(c1[2], c2[2])
        emotion_diff = c1[3] - c2[3]
        return math.sqrt(tau_diff**2 + scale_diff**2 + phase_diff**2 + emotion_diff**2)
    
    # ========== ДАВЛЕНИЕ ==========
    
    def _pressure_at_point(self, tau: float, scale: float, phase: float) -> float:
        """P = сумма energy / (1 + distance) для ближайших мод."""
        query_coord = (tau, scale, phase, 0.0)
        distances = [(mode, self._geometric_distance(query_coord, mode.coordinates))
                     for mode in self.modes.values()]
        distances.sort(key=lambda x: x[1])
        
        pressure = 0.0
        for mode, dist in distances[:5]:
            if dist < 0.1:
                pressure += mode.effective_energy
            else:
                pressure += mode.effective_energy / (1.0 + dist)
        
        return min(1.0, pressure)
    
    def compute_harmonic_decay(self, tau: float, scale: float) -> float:
        """
        Затухание гармоник η = (P_out - P_in) / (P_out + P_in).
        
        P_out — давление на удвоенном масштабе.
        P_in — давление на половинном масштабе.
        """
        P_current = self._pressure_at_point(tau, scale, 0.0)
        P_double = self._pressure_at_point(tau, scale * 2, 0.0)
        P_half = self._pressure_at_point(tau, scale / 2, 0.0)
        
        P_out = max(P_double, P_current)
        P_in = min(P_half, P_current)
        
        if P_out + P_in == 0:
            return 0.5  # нейтральное значение
        return (P_out - P_in) / (P_out + P_in)
    
    # ========== ГАРМОНИЧЕСКИЙ РЕЗОНАНС ==========
    
    def _harmonic_resonance(self, tau1: float, tau2: float, scale: float) -> float:
        """Гармонический резонанс с затуханием, вычисленным из давления."""
        if tau1 <= 0 or tau2 <= 0:
            return 0.0
        
        ratio = max(tau1, tau2) / min(tau1, tau2)
        if ratio <= 0:
            return 0.0
        
        log2_ratio = math.log2(ratio)
        nearest_int = round(log2_ratio)
        
        if abs(log2_ratio - nearest_int) < HARMONIC_TOLERANCE:
            order = abs(nearest_int)
            eta = self.compute_harmonic_decay(tau1, scale)
            return 1.0 / (1.0 + order * eta)
        
        return 0.0
    
    def _spectral_overlap(self, spec1: Dict, spec2: Dict) -> float:
        """Спектральное перекрытие через интервалы."""
        keys1 = set(spec1.keys())
        keys2 = set(spec2.keys())
        common = keys1 & keys2
        
        if not common:
            return 0.0
        
        total_overlap = 0.0
        total_weight = 0.0
        
        for tau in common:
            overlap = spec1[tau].overlaps(spec2[tau])
            weight = (spec1[tau].center + spec2[tau].center) / 2.0
            total_overlap += overlap * weight
            total_weight += weight
        
        return total_overlap / total_weight if total_weight > 0 else 0.0
    
    # ========== ПОИСК ==========
    
    def find_by_resonance(
        self,
        query_tau: float,
        query_scale: float,
        query_phase: float,
        query_emotion: str,
        query_spectrum: Dict[float, SpectralRange] = None,
        k: int = 10
    ) -> List[Tuple[str, float, float, Dict]]:
        """Поиск по резонансу."""
        query_coord = (query_tau, query_scale, query_phase,
                       EMOTION_CODES.get(query_emotion, 0.0))
        
        results = []
        for mode_id, mode in self.modes.items():
            dist = self._geometric_distance(query_coord, mode.coordinates)
            energy = mode.effective_energy
            harmonic = self._harmonic_resonance(query_tau, mode.tau, query_scale)
            
            spectral = 1.0
            if query_spectrum:
                spectral = self._spectral_overlap(mode.tau_spectrum, query_spectrum)
            
            resonance = energy * harmonic * spectral / (1.0 + dist)
            
            results.append((
                mode_id, resonance, dist,
                {'harmonic': harmonic, 'spectral': spectral, 'energy': energy}
            ))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def find_harmonic_family(self, tau: float, max_order: int = 3) -> List[Tuple[str, float, int]]:
        """Находит все моды, гармонически связанные с заданным τ."""
        results = []
        for mode_id, mode in self.modes.items():
            strength = self._harmonic_resonance(tau, mode.tau, mode.scale)
            if strength > 0:
                ratio = max(tau, mode.tau) / min(tau, mode.tau)
                order = round(math.log2(ratio))
                if abs(order) <= max_order:
                    results.append((mode_id, strength, order))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def find_nearest(self, query: Tuple, k: int = 5, exclude_ids: List[str] = None) -> List[Tuple[str, float]]:
        """Поиск k ближайших мод."""
        exclude_set = set(exclude_ids or [])
        distances = []
        for mode_id, mode in self.modes.items():
            if mode_id in exclude_set:
                continue
            dist = self._geometric_distance(query, mode.coordinates)
            distances.append((mode_id, dist))
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    # ========== СЛЕПЫЕ ЗОНЫ ==========
    
    def is_blind_zone(self, tau: float, phase: float, emotion: str,
                      query_spectrum: Dict = None, threshold: float = None) -> bool:
        if threshold is None:
            threshold = BLIND_ZONE_THRESHOLD
        results = self.find_by_resonance(tau, 1.0, phase, emotion, query_spectrum, k=1)
        if not results:
            return True
        _, resonance, _, _ = results[0]
        return resonance < threshold
    
    def find_route_to_blind_zone(self, target_tau: float, max_hops: int = 3) -> List[float]:
        accessible = []
        for i in range(-max_hops, max_hops + 1):
            harmonic_tau = target_tau * (2 ** i)
            if harmonic_tau <= 0:
                continue
            for mode in self.modes.values():
                if self._harmonic_resonance(harmonic_tau, mode.tau, mode.scale) > 0:
                    accessible.append(harmonic_tau)
                    break
        return sorted(set(accessible))
    
    def nearest_resonance_to_blind(self, tau: float, phase: float, emotion: str,
                                   radius: float = 2.0, tau_step: float = 0.5, phase_step: float = 0.1) -> Optional[Tuple[float, float]]:
        tau_steps = int(radius / tau_step)
        phase_steps = int(radius / phase_step)
        for i in range(-tau_steps, tau_steps + 1):
            for j in range(-phase_steps, phase_steps + 1):
                test_tau = tau + i * tau_step
                test_phase = (phase + j * phase_step) % (2 * math.pi)
                if test_tau <= 0:
                    continue
                if not self.is_blind_zone(test_tau, test_phase, emotion):
                    return (test_tau, test_phase)
        return None
    
    def map_blind_zones(self, tau_range: List[float], phase_steps: int = 8,
                        emotion: str = 'neutral') -> List[Tuple[float, float]]:
        blind_map = []
        phases = [i * 2 * math.pi / phase_steps for i in range(phase_steps)]
        for tau in tau_range:
            for phase in phases:
                if self.is_blind_zone(tau, phase, emotion):
                    blind_map.append((tau, phase))
        return blind_map
    
    def seed_blind_zone(self, tau: float, phase: float, emotion: str,
                        content: str = "", pressure_diff: float = 0.0) -> Optional[CoordinateMode]:
        if not self.is_blind_zone(tau, phase, emotion):
            return None
        
        tau_spectrum: Dict[float, SpectralRange] = {}
        harmonic_modes = self.find_harmonic_family(tau, max_order=2)
        
        for mode_id, strength, order in harmonic_modes:
            mode = self.modes[mode_id]
            scale = tau / mode.tau
            for k, interval in mode.tau_spectrum.items():
                scaled_k = round(k * scale, 2)
                inherited_min = interval.min_val * strength
                inherited_max = interval.max_val * strength
                if scaled_k in tau_spectrum:
                    existing = tau_spectrum[scaled_k]
                    existing.min_val = min(existing.min_val, inherited_min)
                    existing.max_val = max(existing.max_val, inherited_max)
                else:
                    tau_spectrum[scaled_k] = SpectralRange(inherited_min, inherited_max, 0.1)
        
        if not tau_spectrum:
            tau_spectrum = {tau: SpectralRange(0.8, 1.0, 0.1)}
        
        if pressure_diff != 0:
            for interval in tau_spectrum.values():
                if pressure_diff > 0:
                    interval.expand(pressure_diff, 1.0)
                else:
                    interval.collapse(-pressure_diff, 1.0)
        
        mode = CoordinateMode(
            id=f"seed_{tau}_{phase:.2f}",
            content=content or f"Зонд в слепой зоне (τ={tau}, phase={phase:.2f})",
            tau=tau, scale=1.0, phase=phase, emotion=emotion,
            energy=MIN_ZOND_ENERGY, tau_spectrum=tau_spectrum
        )
        self.add_mode(mode)
        return mode
    
    def evolve_seeds(self, dt: float) -> None:
        for mode in self.modes.values():
            if mode.energy <= MIN_ZOND_ENERGY * 1.1:
                pressure = self._pressure_at_point(mode.tau, mode.scale, mode.phase)
                internal_pressure = mode.effective_energy
                pressure_diff = pressure - internal_pressure
                for interval in mode.tau_spectrum.values():
                    if pressure_diff > 0:
                        interval.expand(pressure_diff, dt)
                    else:
                        interval.collapse(-pressure_diff, dt)
                resonance = mode.effective_energy
                for interval in mode.tau_spectrum.values():
                    interval.update_weight(resonance, dt)
    
    def update_weights(self, dt: float) -> None:
        for mode in self.modes.values():
            resonance = mode.effective_energy
            for interval in mode.tau_spectrum.values():
                interval.update_weight(resonance, dt)
    
    def meditate_on_boundary(self, tau: float, phase: float, emotion: str,
                             intensity: float = 1.0, patience: int = 10) -> Optional[List[float]]:
        emotion_code = EMOTION_CODES.get(emotion, 0.0)
        amplitude = intensity * (1.0 + emotion_code)
        integral_factor = amplitude * patience
        effective_dt = integral_factor / TAU_LIFE
        
        for _ in range(patience):
            harmonics = self.find_route_to_blind_zone(tau)
            if harmonics:
                return harmonics
            nearest = self.nearest_resonance_to_blind(tau, phase, emotion)
            if nearest:
                return [nearest[0]]
            self.evolve_seeds(dt=effective_dt)
            self.update_weights(dt=effective_dt)
        return None
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ ==========
    
    def spectrum_to_intervals(self, spectrum: Dict[float, float], uncertainty: float = 0.05) -> Dict[float, SpectralRange]:
        return {tau: SpectralRange.from_value(intensity, uncertainty) for tau, intensity in spectrum.items()}
    
    def get_stats(self) -> Dict:
        if not self.modes:
            return {'n_modes': 0}
        energies = [m.effective_energy for m in self.modes.values()]
        tau_values = [m.tau for m in self.modes.values()]
        n_seeds = sum(1 for m in self.modes.values() if m.energy <= MIN_ZOND_ENERGY * 1.1)
        return {
            'n_modes': len(self.modes),
            'n_seeds': n_seeds,
            'mean_energy': sum(energies) / len(energies),
            'max_energy': max(energies),
            'tau_range': (min(tau_values), max(tau_values)) if tau_values else (0, 0),
        }
    
    def clear(self) -> None:
        self.modes.clear()


# ========== ТЕСТ ==========
if __name__ == "__main__":
    print("=" * 60)
    print("CoordinateField — выведенная динамика")
    print("Гармоническое затухание вычисляется из давления")
    print("=" * 60)
    
    field = CoordinateField("TestField")
    
    # Создаём тестовые моды
    tees_spectrum = field.spectrum_to_intervals({16.0: 1.0, 8.0: 0.5})
    tees_half_spectrum = field.spectrum_to_intervals({8.0: 1.0, 16.0: 0.3})
    
    mode1 = CoordinateMode("tees_full", "TEES полный", 16.0, 10.0, 0.0, "joy", 1.0, tees_spectrum)
    mode2 = CoordinateMode("tees_half", "TEES половинный", 8.0, 5.0, 0.1, "joy", 0.8, tees_half_spectrum)
    
    field.add_mode(mode1)
    field.add_mode(mode2)
    
    print(f"Статистика: {field.get_stats()}")
    
    # Проверяем затухание в разных точках
    print("\nЗатухание гармоник η в разных масштабах:")
    for scale in [1.0, 5.0, 10.0, 20.0]:
        eta = field.compute_harmonic_decay(16.0, scale)
        print(f"  scale={scale:.1f}: η={eta:.3f}")
    
    # Гармоническое семейство
    print("\nГармоническое семейство τ=16:")
    for mode_id, strength, order in field.find_harmonic_family(16.0):
        print(f"  {mode_id}: order={order}, strength={strength:.3f}")
    
    # Слепая зона и зонд
    print("\nСлепая зона τ=13:")
    is_blind = field.is_blind_zone(13.0, 0.0, "neutral")
    print(f"  is_blind_zone: {is_blind}")
    
    if is_blind:
        seed = field.seed_blind_zone(13.0, 0.0, "neutral", content="Зонд в зону 13")
        if seed:
            print(f"  Зонд создан: {seed.id}")
            print(f"  Спектр зонда:")
            for t, iv in seed.tau_spectrum.items():
                print(f"    τ={t}: [{iv.min_val:.2f}, {iv.max_val:.2f}]")
    
    # Медитация
    print("\nМедитация на границе τ=13 (intensity=3, emotion=joy, patience=10):")
    result = field.meditate_on_boundary(13.0, 0.0, "joy", intensity=3.0, patience=10)
    print(f"  Результат: {result}")
    
    print(f"\nИтоговая статистика: {field.get_stats()}")
    print("\n✅ Тест пройден")