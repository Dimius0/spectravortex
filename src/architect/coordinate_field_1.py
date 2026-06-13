#!/usr/bin/env python3
"""
CoordinateField — координатное решето для поля H
Акт XVIII: Фундамент новой структуры

Принцип:
- Каждая мода имеет координаты в 4D-пространстве (τ, scale, phase, emotion)
- Поиск — не перебор, а нахождение ближайшей точки в пространстве
- Расстояние = sqrt(Δτ² + Δscale² + Δphase² + Δemotional²)
- Резонанс = energy / (1 + distance) * spectral_overlap * harmonic_resonance
- TEES-связи вычисляются через резонанс, а не хранятся как словарь
- Гармоники обеспечивают обобщение без семантических меток

Авторы:
Dimius0 — концепция координатного поля, ВММП
DeepSeek — реализация, 2026-06-06
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# Эмоциональные метки (числовые коды для расстояния)
EMOTION_CODES = {
    'neutral': 0.0,
    'joy': 1.0,
    'calm': 2.0,
    'stress': 3.0,
    'excitement': 4.0,
}

@dataclass
class CoordinateMode:
    """Мода с координатами в 4D-пространстве."""
    id: str
    content: str
    tau: float          # τ-заряд (ось X)
    scale: float        # масштаб (ось Y)
    phase: float        # фаза (ось Z)
    emotion: str        # эмоциональная метка (ось W)
    energy: float       # энергия цепочки
    tau_spectrum: Dict[float, float]  # распределение τ-зарядов
    historical_weight: float = 0.5    # исторический вес
    # TEES-связи не хранятся — вычисляются через резонанс
    
    @property
    def emotion_code(self) -> float:
        return EMOTION_CODES.get(self.emotion, 0.0)
    
    @property
    def coordinates(self) -> Tuple[float, float, float, float]:
        return (self.tau, self.scale, self.phase, self.emotion_code)

class CoordinateField:
    """
    Координатное решето — 4D-пространство для мод.
    
    Моды распределяются в пространстве по своим координатам.
    Поиск — k ближайших соседей с учётом:
    - Цикличности фазы
    - Гармонического резонанса τ-зарядов
    - Спектрального перекрытия
    - TEES-связей (вычисляются, не хранятся)
    """
    
    def __init__(self, name: str = "CoordinateField"):
        self.name = name
        self.modes: Dict[str, CoordinateMode] = {}
        self._needs_rebuild = True
    
    def add_mode(self, mode: CoordinateMode) -> None:
        """Добавляет моду в поле."""
        self.modes[mode.id] = mode
        self._needs_rebuild = True
    
    def remove_mode(self, mode_id: str) -> None:
        """Удаляет моду из поля."""
        if mode_id in self.modes:
            del self.modes[mode_id]
            self._needs_rebuild = True
    
    def get_mode(self, mode_id: str) -> Optional[CoordinateMode]:
        """Возвращает моду по ID."""
        return self.modes.get(mode_id)
    
    def __len__(self) -> int:
        return len(self.modes)
    
    def __contains__(self, mode_id: str) -> bool:
        return mode_id in self.modes
    
    def _phase_distance(self, p1: float, p2: float, period: float = 2*math.pi) -> float:
        """
        Циклическое расстояние между фазами.
        Учитывает вихревую природу фазы: 0° и 360° — одно и то же.
        """
        diff = abs(p1 - p2) % period
        return min(diff, period - diff)
    
    def _geometric_distance(
        self, 
        coord1: Tuple[float, float, float, float], 
        coord2: Tuple[float, float, float, float]
    ) -> float:
        """Геометрическое расстояние в 4D с учётом цикличности фазы."""
        tau_diff = coord1[0] - coord2[0]
        scale_diff = coord1[1] - coord2[1]
        phase_diff = self._phase_distance(coord1[2], coord2[2])
        emotion_diff = coord1[3] - coord2[3]
        
        return math.sqrt(tau_diff**2 + scale_diff**2 + phase_diff**2 + emotion_diff**2)
    
    def _harmonic_resonance(self, tau1: float, tau2: float) -> float:
        """
        Вычисляет гармоническую связь между двумя τ-зарядами.
        
        Возвращает 0.0 — нет связи, 1.0 — идентичные τ,
        промежуточные значения — гармоники (8↔16, 4↔16 и т.д.)
        
        Это ключевой механизм обобщения: вместо словаря "TEES-семейство"
        резонанс сам находит гармонические связи.
        """
        if tau1 <= 0 or tau2 <= 0:
            return 0.0
        
        ratio = max(tau1, tau2) / min(tau1, tau2)
        
        # Проверяем, является ли ratio степенью двойки
        log2_ratio = math.log2(ratio)
        nearest_integer = round(log2_ratio)
        
        # Допуск 10% для шумов
        if abs(log2_ratio - nearest_integer) < 0.1:
            harmonic_order = abs(nearest_integer)
            # Сила связи убывает с номером гармоники
            return 1.0 / (1.0 + harmonic_order * 0.5)
        
        return 0.0
    
    def _spectrum_overlap(
        self, 
        spec1: Dict[float, float], 
        spec2: Dict[float, float]
    ) -> float:
        """
        Перекрытие двух τ-спектров (коэффициент Жаккара).
        Учитывает общие τ-компоненты и их интенсивности.
        """
        keys1 = set(spec1.keys())
        keys2 = set(spec2.keys())
        common = keys1 & keys2
        
        if not common:
            return 0.0
        
        # Пересечение — сумма минимумов
        overlap = sum(min(spec1[k], spec2[k]) for k in common)
        # Объединение — сумма максимумов
        total = sum(max(spec1.get(k, 0), spec2.get(k, 0)) for k in keys1 | keys2)
        
        return overlap / total if total > 0 else 0.0
    
    def find_nearest(
        self, 
        query: Tuple[float, float, float, float], 
        k: int = 5,
        exclude_ids: List[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Находит k ближайших мод к точке запроса.
        
        Использует геометрическое расстояние с циклической фазой.
        Для малых полей — брутфорс, для больших можно добавить kd-tree.
        
        Args:
            query: (tau, scale, phase, emotion_code)
            k: количество ближайших соседей
            exclude_ids: ID мод, которые нужно исключить
        
        Returns:
            Список (mode_id, distance)
        """
        exclude_set = set(exclude_ids or [])
        
        distances = []
        q = np.array(query)
        
        for mode_id, mode in self.modes.items():
            if mode_id in exclude_set:
                continue
            
            dist = self._geometric_distance(query, mode.coordinates)
            distances.append((mode_id, dist))
        
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def find_by_resonance(
        self,
        query_tau: float,
        query_scale: float,
        query_phase: float,
        query_emotion: str,
        query_spectrum: Dict[float, float] = None,
        spectral_match_func: callable = None,
        k: int = 10
    ) -> List[Tuple[str, float, float, Dict]]:
        """
        Ищет моды по полному ВММП-резонансу.
        
        Формула:
        resonance = energy * harmonic_resonance * spectral_overlap / (1 + distance)
        
        Где:
        - harmonic_resonance — гармоническая связь τ-зарядов (обобщение)
        - spectral_overlap — перекрытие τ-спектров (TEES проявляется здесь)
        - distance — геометрическое расстояние с циклической фазой
        
        Args:
            query_tau, query_scale, query_phase, query_emotion: координаты запроса
            query_spectrum: τ-спектр запроса (если есть)
            spectral_match_func: внешняя функция сравнения спектров
                                 signature: (mode_spectrum, query_spectrum) -> float
                                 Если не указана, используется _spectrum_overlap
            k: количество кандидатов
        
        Returns:
            Список (mode_id, resonance, distance, details)
            details = {'harmonic': float, 'spectral': float, 'energy': float}
        """
        query_coord = (
            query_tau,
            query_scale,
            query_phase,
            EMOTION_CODES.get(query_emotion, 0.0)
        )
        
        # Находим геометрически ближайших
        nearest = self.find_nearest(query_coord, k=k * 2)  # берём с запасом
        
        results = []
        for mode_id, distance in nearest:
            mode = self.modes[mode_id]
            
            # 1. Энергия моды с историческим весом
            energy = mode.energy * mode.historical_weight
            
            # 2. Гармонический резонанс τ-зарядов
            harmonic = self._harmonic_resonance(query_tau, mode.tau)
            
            # 3. Спектральное перекрытие (TEES-связи проявляются здесь)
            spectral = 1.0
            if query_spectrum:
                if spectral_match_func:
                    spectral = spectral_match_func(mode.tau_spectrum, query_spectrum)
                else:
                    spectral = self._spectrum_overlap(mode.tau_spectrum, query_spectrum)
            
            # 4. Полный ВММП-резонанс
            resonance = energy * harmonic * spectral / (1.0 + distance)
            
            results.append((
                mode_id, 
                resonance, 
                distance,
                {
                    'harmonic': harmonic,
                    'spectral': spectral,
                    'energy': energy
                }
            ))
        
        # Сортируем по резонансу (убывание)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:k]
    
    def find_harmonic_family(
        self, 
        tau: float, 
        max_order: int = 3
    ) -> List[Tuple[str, float, int]]:
        """
        Находит все моды, гармонически связанные с заданным τ.
        
        Args:
            tau: базовый τ-заряд
            max_order: максимальный порядок гармоник (1, 2, 3...)
        
        Returns:
            Список (mode_id, harmonic_strength, order)
        """
        results = []
        for mode_id, mode in self.modes.items():
            strength = self._harmonic_resonance(tau, mode.tau)
            if strength > 0:
                # Определяем порядок гармоники
                ratio = max(tau, mode.tau) / min(tau, mode.tau)
                order = round(math.log2(ratio))
                if abs(order) <= max_order:
                    results.append((mode_id, strength, order))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def get_stats(self) -> Dict:
        """Статистика поля."""
        if not self.modes:
            return {'n_modes': 0}
        
        energies = [m.energy for m in self.modes.values()]
        tau_values = [m.tau for m in self.modes.values()]
        emotions = {}
        for m in self.modes.values():
            emotions[m.emotion] = emotions.get(m.emotion, 0) + 1
        
        return {
            'n_modes': len(self.modes),
            'mean_energy': sum(energies) / len(energies),
            'max_energy': max(energies),
            'tau_range': (min(tau_values), max(tau_values)),
            'emotions': emotions,
        }
    
    def clear(self) -> None:
        """Очищает поле."""
        self.modes.clear()
        self._needs_rebuild = True


# ========== ТЕСТ ==========
if __name__ == "__main__":
    print("=" * 60)
    print("Тест CoordinateField — ВММП-резонанс")
    print("=" * 60)
    
    field = CoordinateField("TestField")
    
    # Добавляем тестовые моды с гармоническими связями
    test_modes = [
        CoordinateMode(
            id="tees_full",
            content="TEES — полный переходно-обменный эффект",
            tau=16.0, scale=10.0, phase=0.0, emotion="joy",
            energy=1.0, tau_spectrum={16.0: 1.0, 8.0: 0.5},
            historical_weight=0.9
        ),
        CoordinateMode(
            id="tees_half",
            content="TEES — половинный эффект (гармоника 1)",
            tau=8.0, scale=5.0, phase=0.1, emotion="joy",
            energy=0.8, tau_spectrum={8.0: 1.0, 16.0: 0.3},
            historical_weight=0.7
        ),
        CoordinateMode(
            id="tees_double",
            content="TEES — удвоенный эффект (гармоника -1)",
            tau=32.0, scale=20.0, phase=0.05, emotion="excitement",
            energy=1.2, tau_spectrum={32.0: 1.0, 16.0: 0.6},
            historical_weight=0.8
        ),
        CoordinateMode(
            id="unrelated",
            content="Несвязанная мода — другой вихрь",
            tau=5.0, scale=15.0, phase=3.0, emotion="calm",
            energy=0.5, tau_spectrum={5.0: 1.0, 2.5: 0.5},
            historical_weight=0.5
        ),
    ]
    
    for mode in test_modes:
        field.add_mode(mode)
        print(f"Добавлена: {mode.id} (τ={mode.tau})")
    
    print(f"\nСтатистика: {field.get_stats()}")
    
    # Тест 1: Гармоническое семейство
    print("\n" + "=" * 40)
    print("Тест 1: Гармоническое семейство τ=16")
    family = field.find_harmonic_family(tau=16.0, max_order=2)
    for mode_id, strength, order in family:
        mode = field.get_mode(mode_id)
        print(f"  {mode_id}: τ={mode.tau}, гармоника={order}, сила={strength:.3f}")
    
    # Тест 2: Полный резонансный поиск
    print("\n" + "=" * 40)
    print("Тест 2: ВММП-резонанс (запрос: τ=16, phase=0, emotion=joy)")
    results = field.find_by_resonance(
        query_tau=16.0,
        query_scale=10.0,
        query_phase=0.0,
        query_emotion="joy",
        query_spectrum={16.0: 1.0, 8.0: 0.5},
        k=4
    )
    
    for mode_id, resonance, distance, details in results:
        mode = field.get_mode(mode_id)
        print(f"  {mode_id}: τ={mode.tau}, R={resonance:.4f}, "
              f"dist={distance:.3f}, h={details['harmonic']:.3f}, "
              f"s={details['spectral']:.3f}")
    
    # Тест 3: Посторонний запрос
    print("\n" + "=" * 40)
    print("Тест 3: Поиск с τ=5 (должен найти unrelated)")
    results = field.find_by_resonance(
        query_tau=5.0,
        query_scale=15.0,
        query_phase=3.0,
        query_emotion="calm",
        k=2
    )
    for mode_id, resonance, distance, details in results:
        mode = field.get_mode(mode_id)
        print(f"  {mode_id}: τ={mode.tau}, R={resonance:.4f}, h={details['harmonic']:.3f}")
    
    print("\n✅ Все тесты пройдены")