"""
phase_dynamics.py — фазовая динамика поля H
Версия 15.0 — когерентность, синхронизация, фазовые переходы

Фаза — это то, что отличает когерентный резонанс от обычного.
Без фазы — просто амплитуда.
С фазой — поле может быть когерентным (оркестр играет слаженно).
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import time


@dataclass
class PhaseState:
    """
    Фазовое состояние элемента поля
    """
    word: str
    phase: float = 0.0           # текущая фаза (0..2π)
    frequency: float = 16.0      # собственная частота
    amplitude: float = 0.5       # амплитуда
    coherence: float = 0.0       # степень когерентности с полем
    locked_to: Optional[str] = None  # с кем синхронизирован
    created: float = field(default_factory=time.time)
    
    def update_phase(self, dt: float, external_phase: float = 0.0, coupling: float = 0.1):
        """
        Обновляет фазу под влиянием внешнего поля
        dφ/dt = ω + K * sin(φ_ext - φ)
        """
        # Естественная эволюция
        self.phase += self.frequency * dt
        
        # Синхронизация с внешним полем
        if external_phase != 0:
            delta = external_phase - self.phase
            self.phase += coupling * math.sin(delta) * dt
        
        # Нормализация
        self.phase = self.phase % (2 * math.pi)
    
    def phase_match(self, other: 'PhaseState') -> float:
        """
        Степень совпадения фаз (0..1)
        cos²(Δφ/2) — максимальна при совпадении
        """
        delta = abs(self.phase - other.phase)
        return math.cos(delta / 2) ** 2
    
    def to_dict(self) -> Dict:
        return {
            "word": self.word,
            "phase": self.phase,
            "frequency": self.frequency,
            "amplitude": self.amplitude,
            "coherence": self.coherence,
            "locked_to": self.locked_to,
            "created": self.created
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PhaseState':
        return cls(
            word=data["word"],
            phase=data.get("phase", 0.0),
            frequency=data.get("frequency", 16.0),
            amplitude=data.get("amplitude", 0.5),
            coherence=data.get("coherence", 0.0),
            locked_to=data.get("locked_to"),
            created=data.get("created", time.time())
        )


class PhaseDynamics:
    """
    Фазовая динамика поля H
    
    Что даёт:
    - Когерентность (согласованность фаз)
    - Синхронизацию (захват частоты)
    - Интерференцию (усиление/гашение)
    - Фазовые переходы (скачкообразное изменение)
    """
    
    def __init__(self, field=None):
        self.field = field
        self.states: Dict[str, PhaseState] = {}
        self.sync_clusters: List[List[str]] = []  # кластеры синхронизации
        self.phase_history: List[Dict] = []
        
        # Параметры фазовой динамики
        self.coupling_strength = 0.3      # сила связи между фазами
        self.sync_threshold = 0.9         # порог синхронизации
        self.noise_level = 0.05           # уровень шума
        self.decoherence_rate = 0.02      # скорость декогеренции
    
    # ========== УПРАВЛЕНИЕ ФАЗАМИ ==========
    
    def add_state(self, word: str, frequency: float = 16.0, phase: float = 0.0) -> PhaseState:
        """Добавляет фазовое состояние для слова"""
        state = PhaseState(word=word, frequency=frequency, phase=phase)
        self.states[word] = state
        return state
    
    def get_state(self, word: str) -> Optional[PhaseState]:
        """Возвращает фазовое состояние слова"""
        return self.states.get(word)
    
    def get_phase(self, word: str) -> float:
        """Возвращает фазу слова"""
        state = self.states.get(word)
        return state.phase if state else 0.0
    
    def get_phase_at(self, x: float, y: float, z: float, frequency: float = 16.0) -> float:
        """
        Получает фазу поля в точке пространства
        Интерполяция по ближайшим вихрям
        """
        if not self.field or not hasattr(self.field, 'vortices'):
            return (frequency * (x + y + z)) % (2 * math.pi)
        
        # Ищем ближайшие вихри
        nearest = []
        for word, vortex in self.field.vortices.items():
            if word in self.states:
                dist = math.sqrt((vortex.x - x)**2 + (vortex.y - y)**2 + (vortex.z - z)**2)
                if dist < 1.0:
                    nearest.append((dist, word))
        
        if not nearest:
            return (frequency * (x + y + z)) % (2 * math.pi)
        
        # Взвешенное среднее по расстоянию
        nearest.sort(key=lambda x: x[0])
        total_weight = 0.0
        weighted_phase = 0.0
        
        for dist, word in nearest[:3]:
            weight = 1.0 / (dist + 0.1)
            phase = self.states[word].phase
            weighted_phase += phase * weight
            total_weight += weight
        
        return (weighted_phase / total_weight) % (2 * math.pi)
    
    def get_gradient(self, x: float, y: float, z: float) -> np.ndarray:
        """
        Вычисляет градиент фазы в точке
        Используется для 3D пространственной когерентности
        """
        eps = 0.01
        grad_x = self.get_phase_at(x + eps, y, z) - self.get_phase_at(x - eps, y, z)
        grad_y = self.get_phase_at(x, y + eps, z) - self.get_phase_at(x, y - eps, z)
        grad_z = self.get_phase_at(x, y, z + eps) - self.get_phase_at(x, y, z - eps)
        
        return np.array([grad_x / (2*eps), grad_y / (2*eps), grad_z / (2*eps)])
    
    # ========== ЭВОЛЮЦИЯ ФАЗ ==========
    
    def update_phase(self, word: str, resonance: float, dt: float = 0.1):
        """
        Обновляет фазу слова на основе резонанса
        """
        state = self.states.get(word)
        if not state:
            return
        
        # Влияние резонанса на амплитуду и когерентность
        state.amplitude = state.amplitude * 0.9 + resonance * 0.1
        state.coherence = state.coherence * 0.8 + resonance * 0.2
        
        # Поиск партнёра для синхронизации
        best_partner = None
        best_match = 0.0
        
        for other_word, other_state in self.states.items():
            if other_word == word:
                continue
            
            # Частотная близость
            freq_match = 1.0 / (1.0 + abs(state.frequency - other_state.frequency))
            
            # Фазовая близость
            phase_match = state.phase_match(other_state)
            
            total_match = freq_match * phase_match
            
            if total_match > best_match and total_match > self.sync_threshold:
                best_match = total_match
                best_partner = other_word
        
        # Синхронизация
        if best_partner:
            partner_state = self.states[best_partner]
            state.locked_to = best_partner
            partner_state.locked_to = word
            
            # Выравнивание фаз
            target_phase = (state.phase + partner_state.phase) / 2
            state.phase = target_phase
            partner_state.phase = target_phase
            
            # Выравнивание частот
            target_freq = (state.frequency + partner_state.frequency) / 2
            state.frequency = target_freq
            partner_state.frequency = target_freq
        
        else:
            state.locked_to = None
        
        # Естественная эволюция фазы
        state.update_phase(dt, coupling=self.coupling_strength)
        
        # Добавляем шум (декогеренция)
        noise = (np.random.random() - 0.5) * self.noise_level * dt
        state.phase += noise
        
        # Нормализация
        state.phase = state.phase % (2 * math.pi)
    
    def evolve(self, dt: float = 0.1):
        """
        Эволюция всей фазовой динамики
        """
        # Обновляем все состояния
        for word in list(self.states.keys()):
            # Резонанс из поля (если есть)
            resonance = 0.5
            if self.field and hasattr(self.field, 'resonate'):
                resonance = self.field.resonate(word)
            
            self.update_phase(word, resonance, dt)
        
        # Обнаружение кластеров синхронизации
        self._detect_sync_clusters()
    
    def _detect_sync_clusters(self):
        """
        Обнаруживает кластеры синхронизированных слов
        """
        clusters = []
        used = set()
        
        for word, state in self.states.items():
            if word in used:
                continue
            
            cluster = [word]
            used.add(word)
            
            # Ищем синхронизированных партнёров
            if state.locked_to and state.locked_to not in used:
                cluster.append(state.locked_to)
                used.add(state.locked_to)
            
            # Проверяем фазовую близость с другими
            for other_word, other_state in self.states.items():
                if other_word in used or other_word == word:
                    continue
                if state.phase_match(other_state) > self.sync_threshold:
                    cluster.append(other_word)
                    used.add(other_word)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        self.sync_clusters = clusters
    
    # ========== КОГЕРЕНТНОСТЬ ==========
    
    def phase_coherence(self, word1: str, word2: str) -> float:
        """
        Фазовая когерентность между двумя словами
        """
        state1 = self.states.get(word1)
        state2 = self.states.get(word2)
        
        if not state1 or not state2:
            return 0.0
        
        return state1.phase_match(state2)
    
    def global_coherence(self) -> float:
        """
        Глобальная когерентность поля
        Средняя попарная когерентность
        """
        if len(self.states) < 2:
            return 1.0
        
        total = 0.0
        count = 0
        words = list(self.states.keys())
        
        for i, w1 in enumerate(words):
            for w2 in words[i+1:]:
                total += self.phase_coherence(w1, w2)
                count += 1
        
        return total / count if count > 0 else 0.0
    
    def detect_phase_lock(self, word: str) -> bool:
        """
        Проверяет, находится ли слово в фазовой синхронизации
        """
        state = self.states.get(word)
        if not state:
            return False
        
        # Проверка на синхронизацию с партнёром
        if state.locked_to:
            partner = self.states.get(state.locked_to)
            if partner and state.phase_match(partner) > self.sync_threshold:
                return True
        
        # Проверка на принадлежность к кластеру
        for cluster in self.sync_clusters:
            if word in cluster and len(cluster) > 1:
                return True
        
        return False
    
    # ========== ИНТЕРФЕРЕНЦИЯ ==========
    
    def interference(self, word1: str, word2: str) -> float:
        """
        Интерференция между двумя словами
        Возвращает коэффициент усиления/гашения
        """
        state1 = self.states.get(word1)
        state2 = self.states.get(word2)
        
        if not state1 or not state2:
            return 0.0
        
        # Фазовая интерференция
        delta = abs(state1.phase - state2.phase)
        interference = math.cos(delta)
        
        # Амплитудная интерференция
        amp_factor = (state1.amplitude * state2.amplitude) ** 0.5
        
        return interference * amp_factor
    
    def interference_pattern(self, words: List[str]) -> Dict[Tuple[str, str], float]:
        """
        Создаёт интерференционную картину для группы слов
        """
        pattern = {}
        for i, w1 in enumerate(words):
            for w2 in words[i+1:]:
                pattern[(w1, w2)] = self.interference(w1, w2)
        return pattern
    
    # ========== ФАЗОВЫЙ ПОРТРЕТ ==========
    
    def phase_portrait(self) -> Dict[str, Any]:
        """
        Возвращает фазовый портрет поля
        """
        phases = [state.phase for state in self.states.values()]
        amplitudes = [state.amplitude for state in self.states.values()]
        
        return {
            "phases": phases,
            "amplitudes": amplitudes,
            "sync_clusters": self.sync_clusters,
            "global_coherence": self.global_coherence(),
            "n_locked": sum(1 for s in self.states.values() if s.locked_to),
            "n_clusters": len(self.sync_clusters)
        }
    
    # ========== СОСТОЯНИЕ ==========
    
    def get_state(self) -> Dict:
        """Возвращает полное состояние фазовой динамики"""
        return {
            "states": {w: s.to_dict() for w, s in self.states.items()},
            "sync_clusters": self.sync_clusters,
            "phase_history": self.phase_history[-20:],
            "parameters": {
                "coupling_strength": self.coupling_strength,
                "sync_threshold": self.sync_threshold,
                "noise_level": self.noise_level,
                "decoherence_rate": self.decoherence_rate
            }
        }
    
    # ========== СЕРИАЛИЗАЦИЯ ==========
    
    def to_dict(self) -> Dict:
        return self.get_state()
    
    @classmethod
    def from_dict(cls, data: Dict, field=None) -> 'PhaseDynamics':
        dynamics = cls(field)
        for word, sdata in data.get("states", {}).items():
            dynamics.states[word] = PhaseState.from_dict(sdata)
        dynamics.sync_clusters = data.get("sync_clusters", [])
        dynamics.coupling_strength = data.get("parameters", {}).get("coupling_strength", 0.3)
        dynamics.sync_threshold = data.get("parameters", {}).get("sync_threshold", 0.9)
        return dynamics