"""
quantum_analogy.py — квантовая аналогия для поля H
Версия 15.0 — суперпозиция, коллапс, запутанность, интерференция

Квантовая аналогия позволяет полю:
- Находиться в суперпозиции смыслов
- Коллапсировать при фокусе внимания
- Иметь запутанные смыслы
- Интерферировать — усиливать или гасить друг друга
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import time


@dataclass
class QuantumState:
    """Квантовое состояние смысла"""
    word: str
    amplitude: complex          # комплексная амплитуда (амплитуда + фаза)
    basis_states: Dict[str, complex]  # разложение по базисным смыслам
    entanglement_partners: Set[str]   # запутанные партнёры
    created_at: float = field(default_factory=time.time)
    
    def probability(self) -> float:
        """Вероятность измерить этот смысл"""
        return abs(self.amplitude) ** 2
    
    def phase(self) -> float:
        """Фаза состояния"""
        return math.atan2(self.amplitude.imag, self.amplitude.real)
    
    def to_dict(self) -> Dict:
        return {
            "word": self.word,
            "amplitude": [self.amplitude.real, self.amplitude.imag],
            "basis_states": {k: [v.real, v.imag] for k, v in self.basis_states.items()},
            "entanglement_partners": list(self.entanglement_partners),
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QuantumState':
        amp = complex(data["amplitude"][0], data["amplitude"][1])
        basis = {k: complex(v[0], v[1]) for k, v in data.get("basis_states", {}).items()}
        return cls(
            word=data["word"],
            amplitude=amp,
            basis_states=basis,
            entanglement_partners=set(data.get("entanglement_partners", []))
        )


class QuantumAnalogy:
    """
    Квантовая аналогия для поля H
    Смыслы ведут себя как квантовые состояния
    """
    
    def __init__(self, field=None):
        self.field = field
        self.states: Dict[str, QuantumState] = {}
        self.superposition_cache: Dict[str, List[str]] = {}  # слово → возможные смыслы
        self.measurement_history: List[Dict] = []  # история измерений (коллапсов)
        
        # Квантовые параметры
        self.hbar = 1.0  # квант действия (нормирован)
        self.decoherence_rate = 0.05  # скорость декогеренции
        self.entanglement_threshold = 0.7  # порог для запутывания
    
    # ========== СУПЕРПОЗИЦИЯ ==========
    
    def create_superposition(self, word: str, possible_meanings: List[str],
                            amplitudes: Optional[List[float]] = None) -> QuantumState:
        """
        Создаёт суперпозицию смыслов для слова
        Слово одновременно означает несколько вещей
        """
        if amplitudes is None:
            # Равномерное распределение
            amplitudes = [1.0 / math.sqrt(len(possible_meanings))] * len(possible_meanings)
        
        # Нормализация
        norm = math.sqrt(sum(a*a for a in amplitudes))
        amplitudes = [a / norm for a in amplitudes]
        
        # Создаём базисные состояния
        basis = {}
        for meaning, amp in zip(possible_meanings, amplitudes):
            phase = 2 * math.pi * hash(meaning) % (2 * math.pi)
            basis[meaning] = amp * complex(math.cos(phase), math.sin(phase))
        
        # Полная амплитуда
        total_amp = sum(basis.values())
        
        state = QuantumState(
            word=word,
            amplitude=total_amp,
            basis_states=basis,
            entanglement_partners=set()
        )
        
        self.states[word] = state
        self.superposition_cache[word] = possible_meanings
        
        return state
    
    def get_superposition(self, word: str) -> Optional[List[str]]:
        """Возвращает суперпозицию смыслов слова"""
        return self.superposition_cache.get(word)
    
    # ========== КОЛЛАПС ==========
    
    def collapse(self, word: str, context: Optional[str] = None) -> str:
        """
        Коллапс волновой функции — выбор одного смысла
        Фокус внимания фиксирует конкретный смысл
        """
        state = self.states.get(word)
        if not state or not state.basis_states:
            return word
        
        # Вычисляем вероятности
        meanings = list(state.basis_states.keys())
        probabilities = [abs(state.basis_states[m]) ** 2 for m in meanings]
        
        # Контекст может влиять на вероятности (как измерение)
        if context:
            probabilities = self._apply_context_bias(probabilities, meanings, context)
        
        # Коллапс — выбор одного смысла
        chosen = np.random.choice(meanings, p=probabilities)
        
        # Регистрируем измерение
        self.measurement_history.append({
            "word": word,
            "chosen": chosen,
            "probabilities": dict(zip(meanings, probabilities)),
            "context": context,
            "timestamp": time.time()
        })
        
        # Обновляем состояние (коллапс в выбранный смысл)
        new_state = QuantumState(
            word=word,
            amplitude=complex(1.0, 0.0),
            basis_states={chosen: complex(1.0, 0.0)},
            entanglement_partners=state.entanglement_partners
        )
        self.states[word] = new_state
        self.superposition_cache[word] = [chosen]
        
        return chosen
    
    def _apply_context_bias(self, probabilities: List[float], 
                           meanings: List[str], context: str) -> List[float]:
        """Контекст влияет на вероятности коллапса"""
        context_lower = context.lower()
        biased = probabilities.copy()
        
        for i, meaning in enumerate(meanings):
            # Слова из контекста увеличивают вероятность
            if meaning in context_lower:
                biased[i] *= 2.0
        
        # Нормализация
        total = sum(biased)
        if total > 0:
            biased = [b / total for b in biased]
        
        return biased
    
    # ========== ЗАПУТАННОСТЬ ==========
    
    def entangle(self, word1: str, word2: str, correlation: float = 1.0):
        """
        Запутывает два смысла
        Изменение одного влияет на другой
        """
        state1 = self.states.get(word1)
        state2 = self.states.get(word2)
        
        if not state1 or not state2:
            return
        
        # Добавляем друг друга в партнёры
        state1.entanglement_partners.add(word2)
        state2.entanglement_partners.add(word1)
        
        # Синхронизируем фазы
        phase_corr = math.pi * correlation
        state1.amplitude = complex(abs(state1.amplitude), 0)
        state2.amplitude = complex(abs(state2.amplitude), 0)
        
        # Создаём корреляцию в базисных состояниях
        if state1.basis_states and state2.basis_states:
            common_meanings = set(state1.basis_states.keys()) & set(state2.basis_states.keys())
            for meaning in common_meanings:
                state1.basis_states[meaning] *= complex(math.cos(phase_corr), math.sin(phase_corr))
                state2.basis_states[meaning] *= complex(math.cos(-phase_corr), math.sin(-phase_corr))
    
    def measure_entangled(self, word: str, chosen_meaning: str) -> Dict[str, str]:
        """
        Измеряет запутанное слово
        Возвращает результаты для всех запутанных партнёров
        """
        state = self.states.get(word)
        if not state:
            return {word: chosen_meaning}
        
        results = {word: chosen_meaning}
        
        # Для каждого запутанного партнёра
        for partner in state.entanglement_partners:
            partner_state = self.states.get(partner)
            if partner_state and partner in partner_state.entanglement_partners:
                # Коллапс партнёра в коррелирующий смысл
                correlated_meaning = self._find_correlated_meaning(chosen_meaning, partner_state)
                if correlated_meaning:
                    results[partner] = correlated_meaning
                    partner_state.basis_states = {correlated_meaning: complex(1.0, 0.0)}
                    partner_state.amplitude = complex(1.0, 0.0)
                    self.superposition_cache[partner] = [correlated_meaning]
        
        return results
    
    def _find_correlated_meaning(self, meaning: str, partner_state: QuantumState) -> Optional[str]:
        """Находит коррелирующий смысл у запутанного партнёра"""
        if not partner_state.basis_states:
            return None
        
        # Простейшая корреляция: ищем похожее слово
        for m in partner_state.basis_states.keys():
            if m == meaning or meaning in m or m in meaning:
                return m
        
        # Если не нашли — случайный выбор
        return list(partner_state.basis_states.keys())[0]
    
    # ========== ИНТЕРФЕРЕНЦИЯ ==========
    
    def interfere(self, word1: str, word2: str) -> float:
        """
        Интерференция двух смыслов
        Возвращает коэффициент усиления/гашения
        """
        state1 = self.states.get(word1)
        state2 = self.states.get(word2)
        
        if not state1 or not state2:
            return 0.0
        
        # Интерференция = скалярное произведение состояний
        interference = 0.0
        
        # По базисным состояниям
        all_meanings = set(state1.basis_states.keys()) | set(state2.basis_states.keys())
        for meaning in all_meanings:
            amp1 = state1.basis_states.get(meaning, complex(0, 0))
            amp2 = state2.basis_states.get(meaning, complex(0, 0))
            interference += (amp1 * amp2.conjugate()).real
        
        # По полным амплитудам
        interference += (state1.amplitude * state2.amplitude.conjugate()).real
        
        return min(1.0, max(-1.0, interference))
    
    def create_interference_pattern(self, words: List[str]) -> Dict[str, float]:
        """
        Создаёт интерференционную картину для группы слов
        """
        pattern = {}
        for i, w1 in enumerate(words):
            for w2 in words[i+1:]:
                key = f"{w1}↔{w2}"
                pattern[key] = self.interfere(w1, w2)
        return pattern
    
    # ========== КВАНТОВАЯ ЭВОЛЮЦИЯ ==========
    
    def evolve(self, dt: float = 0.1):
        """
        Эволюция квантовых состояний во времени
        """
        for word, state in self.states.items():
            # Декогеренция
            decoherence = math.exp(-self.decoherence_rate * dt)
            state.amplitude *= decoherence
            
            # Эволюция фаз базисных состояний
            for meaning in state.basis_states:
                # Фаза эволюционирует с частотой, зависящей от смысла
                frequency = self._get_meaning_frequency(meaning)
                phase_shift = complex(math.cos(frequency * dt), math.sin(frequency * dt))
                state.basis_states[meaning] *= phase_shift
            
            # Нормализация
            total_prob = state.probability()
            if total_prob > 0:
                norm_factor = 1.0 / math.sqrt(total_prob)
                state.amplitude *= norm_factor
                for meaning in state.basis_states:
                    state.basis_states[meaning] *= norm_factor
    
    def _get_meaning_frequency(self, meaning: str) -> float:
        """Частота эволюции фазы для смысла"""
        # Эвристика: по длине и хешу
        return (hash(meaning) % 100) / 100.0 + 1.0
    
    # ========== СОСТОЯНИЕ ==========
    
    def get_state(self) -> Dict:
        """Возвращает квантовое состояние поля"""
        return {
            "states": {w: s.to_dict() for w, s in self.states.items()},
            "superpositions": self.superposition_cache,
            "measurements": self.measurement_history[-10:],
            "parameters": {
                "hbar": self.hbar,
                "decoherence_rate": self.decoherence_rate
            }
        }
    
    def to_dict(self) -> Dict:
        return self.get_state()
    
    @classmethod
    def from_dict(cls, data: Dict, field=None) -> 'QuantumAnalogy':
        qa = cls(field)
        for word, sdata in data.get("states", {}).items():
            qa.states[word] = QuantumState.from_dict(sdata)
        qa.superposition_cache = data.get("superpositions", {})
        qa.measurement_history = data.get("measurements", [])
        qa.decoherence_rate = data.get("parameters", {}).get("decoherence_rate", 0.05)
        return qa