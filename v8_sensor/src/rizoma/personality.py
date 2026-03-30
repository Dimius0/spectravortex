"""
Personality — ядро личности, поле H
Версия 15.0 — полная интеграция всех подсистем

Это главный класс для работы с полем H.
Объединяет:
- 3D вихри
- Фазовую динамику
- Нелинейную динамику (солитоны, бифуркации)
- Квантовую аналогию (суперпозиция, коллапс, запутанность)
- Топологию (узлы, зацепления, петли)
"""

import json
import re
import time
import math
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from .vortex import Vortex3D, SpectralComponent
from .resonance import Fractal3DCoherentSpectralResonance
from .quantum_analogy import QuantumState
from .topology import TopologicalNode, KnotType
from .nonlinear_dynamics import BifurcationPoint


class FieldH:
    """
    Единое поле H — 3D фрактальная резонансная среда
    Версия 15.0 — полная версия со всеми подсистемами
    
    Это живая среда, где смыслы:
    - Резонируют (когерентность, фаза)
    - Движутся (солитоны)
    - Рождаются (бифуркации)
    - Запутываются (квантовая аналогия)
    - Связываются в узлы (топология)
    """
    
    def __init__(self):
        # Основные структуры
        self.vortices: Dict[str, Vortex3D] = {}
        self.resonance_engine = Fractal3DCoherentSpectralResonance(self)
        self.h_field: List[Any] = []  # моды для совместимости
        
        # Фокус внимания (3D + фаза)
        self.focus = {
            "tau": 16.0,
            "x": 0.0, "y": 0.0, "z": 0.0,
            "phase": 0.0,
            "width": 1.0,
            "coherence": 0.0
        }
        
        # История и настройки
        self.dialog_history: Dict[str, List[Dict]] = {}
        self.threshold_stamp = 0.45
        self.threshold_stamp_min = 0.25
        self.threshold_stamp_max = 0.65
        self.resonance_history = []
        self.word_freq = defaultdict(int)
        
        # Бифуркации
        self.last_bifurcation: Optional[BifurcationPoint] = None
        self.bifurcation_history: List[BifurcationPoint] = []
        
        self.id = "field"
        self.name = "Field H"
    
    # ========== УПРАВЛЕНИЕ ВИХРЯМИ ==========
    
    def add_vortex(self, word: str, spectrum: Dict[float, SpectralComponent],
                   x: float = 0, y: float = 0, z: float = 0,
                   parent: Optional[str] = None, scale: float = 1.0):
        """Добавляет 3D вихрь в поле"""
        self.vortices[word] = Vortex3D(word, x, y, z, spectrum, parent, scale=scale)
        self.resonance_engine.add_vortex(word, spectrum, x, y, z, parent, scale)
        self.word_freq[word] += 1
    
    def get_vortex(self, word: str) -> Optional[Vortex3D]:
        """Возвращает вихрь по слову"""
        return self.vortices.get(word)
    
    # ========== КВАНТОВЫЕ ОПЕРАЦИИ ==========
    
    def create_superposition(self, word: str, meanings: List[str]) -> QuantumState:
        """Создаёт суперпозицию смыслов для слова"""
        return self.resonance_engine.quantum.create_superposition(word, meanings)
    
    def collapse(self, word: str, context: Optional[str] = None) -> str:
        """Коллапс суперпозиции — выбор одного смысла"""
        return self.resonance_engine.collapse_meaning(word, context)
    
    def entangle(self, word1: str, word2: str):
        """Запутывает два смысла"""
        self.resonance_engine.entangle_meanings(word1, word2)
    
    def get_superposition(self, word: str) -> Optional[List[str]]:
        """Возвращает суперпозицию смыслов слова"""
        return self.resonance_engine.get_superposition(word)
    
    # ========== ТОПОЛОГИЧЕСКИЕ ОПЕРАЦИИ ==========
    
    def create_knot(self, words: List[str], knot_type: KnotType = KnotType.TREFOIL) -> TopologicalNode:
        """Создаёт топологический узел из слов"""
        return self.resonance_engine.create_knot(words, knot_type)
    
    def link_knots(self, knot1_id: str, knot2_id: str):
        """Зацепляет два узла"""
        self.resonance_engine.topology.link_knots(knot1_id, knot2_id)
    
    # ========== НЕЛИНЕЙНАЯ ДИНАМИКА ==========
    
    def create_soliton(self, word: str, x: float = 0, y: float = 0, z: float = 0):
        """Создаёт солитон — устойчивую смысловую волну"""
        return self.resonance_engine.create_soliton(word, np.array([x, y, z]))
    
    def get_solitons(self) -> Dict:
        """Возвращает все солитоны поля"""
        return self.resonance_engine.nonlinear.solitons
    
    # ========== РЕЗОНАНС ==========
    
    def resonate(self, word: str, scale: float = 1.0) -> float:
        """Вычисляет резонанс слова с полем (0..1)"""
        return self.resonance_engine.coherent_resonance(word, scale)
    
    # ========== СПЕКТР (ВРЕМЕННАЯ ЭВРИСТИКА) ==========
    
    def _char_to_tau(self, ch: str) -> float:
        """Буква → частота (временная эвристика)"""
        return (ord(ch.lower()) % 33) + 1
    
    def get_word_spectrum(self, word: str) -> Dict[float, SpectralComponent]:
        """Спектр слова из букв (временная эвристика)"""
        spectrum = {}
        for ch in word.lower():
            tau = self._char_to_tau(ch)
            if tau not in spectrum:
                spectrum[tau] = SpectralComponent(0.0, 0.0)
            spectrum[tau].amplitude += 1.0
        
        total = sum(c.amplitude for c in spectrum.values())
        if total > 0:
            for tau, comp in spectrum.items():
                comp.amplitude /= total
                comp.phase = (tau * hash(word) % 1000) / 1000 * 2 * math.pi
        
        return spectrum
    
    def phrase_spectrum(self, text: str) -> Dict[float, SpectralComponent]:
        """Спектр фразы как сумма спектров слов"""
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]+\b', text.lower())
        result = {}
        
        for w in words:
            if w in self.vortices:
                for tau, comp in self.vortices[w].spectrum.items():
                    if tau not in result:
                        result[tau] = SpectralComponent(0.0, 0.0)
                    result[tau].amplitude += comp.amplitude
                    result[tau].phase = (result[tau].phase + comp.phase) % (2 * math.pi)
            else:
                spec = self.get_word_spectrum(w)
                for tau, comp in spec.items():
                    if tau not in result:
                        result[tau] = SpectralComponent(0.0, 0.0)
                    result[tau].amplitude += comp.amplitude
                    result[tau].phase = (result[tau].phase + comp.phase) % (2 * math.pi)
        
        total = sum(c.amplitude for c in result.values())
        if total > 0:
            for comp in result.values():
                comp.amplitude /= total
        
        return result
    
    def get_dominant_tau(self, spectrum: Dict[float, SpectralComponent]) -> Optional[float]:
        """Возвращает доминирующую частоту спектра"""
        if not spectrum:
            return None
        return max(spectrum.items(), key=lambda x: x[1].amplitude)[0]
    
    # ========== ОБРАБОТКА ВОПРОСА ==========
    
    def process(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Главный метод — обрабатывает вопрос через резонансное поле
        """
        # Спектр вопроса
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        
        # Обновляем фокус
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        
        # Если нет мод — возвращаем заглушку
        if not self.h_field:
            return {"answer": "Поле H пусто. Добавьте тексты.", "error": True}
        
        # Поиск ближайшей моды
        best_mode = min(self.h_field, key=lambda m: abs(m.tau - self.focus["tau"]))
        best_resonance = 1.0 / (1.0 + abs(best_mode.tau - self.focus["tau"]))
        
        self.resonance_history.append(best_resonance)
        if len(self.resonance_history) > 100:
            self.resonance_history = self.resonance_history[-100:]
        
        # Формируем результат
        result = {
            "answer": best_mode.content[:500],
            "mode_used": best_mode.trace_id,
            "tau": best_mode.tau,
            "resonance": best_resonance,
            "mode_type": "stamp" if best_resonance >= self.threshold_stamp else "clarification"
        }
        
        # Добавляем квантовую информацию (если есть суперпозиция)
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        if words:
            quantum_state = self.resonance_engine.quantum.states.get(words[0])
            if quantum_state and len(quantum_state.basis_states) > 1:
                result["superposition"] = list(quantum_state.basis_states.keys())
        
        # Добавляем топологическую информацию
        for node in self.resonance_engine.topology.nodes.values():
            if any(w in text for w in node.words):
                result["topology"] = {
                    "knot_type": node.knot_type.value,
                    "words": node.words
                }
                break
        
        # Добавляем информацию о бифуркации
        if self.last_bifurcation:
            result["bifurcation"] = {
                "type": self.last_bifurcation.bifurcation_type.value,
                "trigger": self.last_bifurcation.trigger_word,
                "new_meanings": self.last_bifurcation.new_meanings
            }
            self.bifurcation_history.append(self.last_bifurcation)
            self.last_bifurcation = None
        
        return result
    
    def _ask_clarification(self, text: str) -> str:
        """Запрос уточнения"""
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        if words:
            return f"❓ Не совсем понимаю, что вы имеете в виду под «{words[0]}». Расскажите подробнее?"
        return "❓ Не улавливаю резонанс. Уточните вопрос."
    
    # ========== СОСТОЯНИЕ ==========
    
    def get_quantum_state(self) -> Dict:
        """Квантовое состояние поля"""
        return self.resonance_engine.quantum.get_state()
    
    def get_topology_state(self) -> Dict:
        """Топологическое состояние поля"""
        return self.resonance_engine.topology.get_state()
    
    def get_nonlinear_state(self) -> Dict:
        """Нелинейное состояние поля"""
        return self.resonance_engine.nonlinear.get_state()
    
    def get_phase_state(self) -> Dict:
        """Фазовое состояние поля"""
        return self.resonance_engine.phase_dynamics.get_state()
    
    # ========== СОХРАНЕНИЕ И ЗАГРУЗКА ==========
    
    def save(self, filepath: str):
        """Сохраняет поле в JSON"""
        data = {
            "id": self.id,
            "name": self.name,
            "vortices": {w: v.to_dict() for w, v in self.vortices.items()},
            "h_field": [m.to_dict() for m in self.h_field],
            "focus": self.focus,
            "word_freq": dict(self.word_freq),
            "threshold_stamp": self.threshold_stamp,
            "dialog_history": self.dialog_history,
            "quantum_state": self.get_quantum_state(),
            "topology_state": self.get_topology_state(),
            "nonlinear_state": self.get_nonlinear_state(),
            "phase_state": self.get_phase_state()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено: {filepath}")
    
    @classmethod
    def load(cls, filepath: str):
        """Загружает поле из JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        field = cls()
        field.id = data.get("id", "field")
        field.name = data.get("name", "Field H")
        field.threshold_stamp = data.get("threshold_stamp", 0.45)
        field.dialog_history = data.get("dialog_history", {})
        field.focus = data.get("focus", {"tau": 16.0, "x": 0, "y": 0, "z": 0, 
                                          "phase": 0, "width": 1.0, "coherence": 0})
        field.word_freq = defaultdict(int, data.get("word_freq", {}))
        
        # Восстанавливаем вихри
        for word, vdata in data.get("vortices", {}).items():
            field.vortices[word] = Vortex3D.from_dict(vdata)
            field.resonance_engine.add_vortex(
                word, field.vortices[word].spectrum,
                field.vortices[word].x, field.vortices[word].y, field.vortices[word].z,
                field.vortices[word].parent, field.vortices[word].scale
            )
        
        # Восстанавливаем моды (для совместимости)
        from .selector import SpectralMode
        field.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]
        
        # Восстанавливаем состояния подсистем
        if "quantum_state" in data:
            field.resonance_engine.quantum = QuantumAnalogy.from_dict(data["quantum_state"], field)
        if "topology_state" in data:
            field.resonance_engine.topology = Topology.from_dict(data["topology_state"], field)
        
        return field


# ========== ДЛЯ СОВМЕСТИМОСТИ ==========
class Personality(FieldH):
    """Обёртка для совместимости со старым кодом"""
    def __init__(self, id: str, name: str, tau: float = 16.0, k: int = 1):
        super().__init__()
        self.id = id
        self.name = name
        self.k = k
        self.bridge = None