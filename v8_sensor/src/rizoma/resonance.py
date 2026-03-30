"""
resonance.py — модуль резонанса поля H
Версия 15.0 — полная интеграция всех подсистем

Объединяет:
- 3D вихри (vortex.py)
- Фазовую динамику (phase_dynamics.py)
- Нелинейную динамику (nonlinear_dynamics.py)
- Квантовую аналогию (quantum_analogy.py)
- Топологию (topology.py)
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from .vortex import Vortex3D, SpectralComponent
from .phase_dynamics import PhaseDynamics
from .nonlinear_dynamics import NonlinearDynamics, BifurcationType
from .quantum_analogy import QuantumAnalogy
from .topology import Topology, KnotType


@dataclass
class ResonanceBuffer:
    """Буфер резонанса — плавное нарастание и затухание"""
    size: int = 5
    history: List[float] = field(default_factory=list)
    decay: float = 0.7
    
    def push(self, value: float) -> float:
        self.history.append(value)
        if len(self.history) > self.size:
            self.history.pop(0)
        return self.get_smoothed()
    
    def get_smoothed(self) -> float:
        if not self.history:
            return 0.0
        weight = 1.0
        total = 0.0
        weight_sum = 0.0
        for val in reversed(self.history):
            total += val * weight
            weight_sum += weight
            weight *= self.decay
        return total / weight_sum if weight_sum > 0 else 0.0
    
    def clear(self):
        self.history.clear()
    
    def trend(self) -> float:
        """Тренд: положительный = рост, отрицательный = спад"""
        if len(self.history) < 2:
            return 0.0
        return self.history[-1] - self.history[0]


class Fractal3DCoherentSpectralResonance:
    """
    Трёхмерный фрактальный когерентный спектральный резонанс
    Версия 15.0 — полная интеграция
    
    Это главный двигатель поля H. Собирает всё воедино.
    """
    
    def __init__(self, field=None):
        self.field = field
        self.vortices: Dict[str, Vortex3D] = {}
        self._init_fractal_scales()
        
        # Буферы для каждого масштаба
        self.buffers: Dict[float, ResonanceBuffer] = {}
        for scale in self.scales:
            self.buffers[scale] = ResonanceBuffer(size=5, decay=0.7)
        
        self.focus_buffer = ResonanceBuffer(size=3, decay=0.5)
        self.resonance_history: List[float] = []
        
        # Подсистемы
        self.phase_dynamics = PhaseDynamics(field)
        self.nonlinear = NonlinearDynamics(field)
        self.quantum = QuantumAnalogy(field)
        self.topology = Topology(field)
        
        self.dt = 0.1  # шаг времени для эволюции
    
    def _init_fractal_scales(self):
        """Фрактальные масштабы: от буквы до смысла"""
        self.scales = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]
    
    # ========== УПРАВЛЕНИЕ ВИХРЯМИ ==========
    
    def add_vortex(self, word: str, spectrum: Dict[float, SpectralComponent],
                   x: float = 0, y: float = 0, z: float = 0,
                   parent: Optional[str] = None, scale: float = 1.0):
        """Добавляет 3D вихрь в поле"""
        vortex = Vortex3D(word, x, y, z, spectrum, parent, scale=scale)
        self.vortices[word] = vortex
        
        if parent and parent in self.vortices:
            self.vortices[parent].children.append(word)
        
        # Создаём квантовое состояние (суперпозиция)
        meanings = [word]
        if parent:
            meanings.append(parent)
        self.quantum.create_superposition(word, meanings)
        
        # Создаём фазовое состояние
        dominant_tau = vortex.get_dominant_tau() or 16.0
        self.phase_dynamics.add_state(word, dominant_tau, 0.0)
    
    # ========== ГЛАВНЫЙ МЕТОД — РЕЗОНАНС ==========
    
    def coherent_resonance(self, word: str, target_scale: float = 1.0) -> float:
        """
        Полный резонанс слова с полем.
        Интегрирует все подсистемы.
        """
        vortex = self.vortices.get(word)
        if not vortex:
            return 0.0
        
        # ========== 1. БАЗОВЫЕ КОМПОНЕНТЫ ==========
        
        # Спектральная когерентность (амплитуды + фазы)
        spectral = self._spectral_coherence(vortex)
        
        # 3D пространственная когерентность
        spatial_3d = self._spatial_coherence_3d(vortex)
        
        # Фрактальная когерентность (самоподобие)
        fractal = self._fractal_coherence(vortex, target_scale)
        
        base = spectral * spatial_3d * fractal
        
        # ========== 2. ФАЗОВАЯ КОГЕРЕНТНОСТЬ ==========
        
        # Находим ближайший вихрь для фазового сравнения
        nearest = self._find_nearest_vortex(vortex)
        phase_factor = 1.0
        if nearest:
            phase_factor = self.phase_dynamics.phase_coherence(word, nearest)
        
        # ========== 3. КВАНТОВАЯ КОГЕРЕНТНОСТЬ ==========
        
        quantum_factor = 1.0
        quantum_state = self.quantum.states.get(word)
        if quantum_state:
            quantum_factor = quantum_state.probability()
            # Запутанность усиливает
            if quantum_state.entanglement_partners:
                quantum_factor *= 1.2
        
        # ========== 4. ТОПОЛОГИЧЕСКИЙ ФАКТОР ==========
        
        topology_factor = 1.0
        for node in self.topology.nodes.values():
            if word in node.words:
                topology_factor *= 1.5
                if node.is_linked:
                    topology_factor *= 1.3
        
        # ========== 5. НЕЛИНЕЙНОЕ УСИЛЕНИЕ ==========
        
        nonlinear_factor = 1 + self.nonlinear.nonlinear_gain * base
        
        # ========== 6. ИТОГОВЫЙ РЕЗОНАНС ==========
        
        resonance = base * phase_factor * quantum_factor * topology_factor * nonlinear_factor
        resonance = min(1.0, resonance)
        
        # ========== 7. ДЕТЕКЦИЯ БИФУРКАЦИИ ==========
        
        location = np.array([vortex.x, vortex.y, vortex.z])
        bifurcation = self.nonlinear.detect_bifurcation(resonance, word, location)
        if bifurcation and self.field:
            self.field.last_bifurcation = bifurcation
        
        # ========== 8. ЭВОЛЮЦИЯ ПОДСИСТЕМ ==========
        
        # Обновляем фазу
        self.phase_dynamics.update_phase(word, resonance, self.dt)
        
        # Обновляем солитоны
        self.nonlinear.update_solitons(self.dt)
        
        # Квантовая эволюция
        self.quantum.evolve(self.dt)
        
        # Топологическая эволюция
        self.topology.evolve(self.dt)
        
        # Самоорганизация (периодически)
        if np.random.random() < 0.1:
            self.nonlinear.self_organize(self.dt)
        
        # ========== 9. БУФЕРИЗАЦИЯ ==========
        
        buffer = self.buffers.get(target_scale)
        if buffer:
            smoothed = buffer.push(resonance)
        else:
            smoothed = resonance
        
        self.resonance_history.append(smoothed)
        if len(self.resonance_history) > 100:
            self.resonance_history = self.resonance_history[-100:]
        
        return smoothed
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def _spectral_coherence(self, vortex: Vortex3D) -> float:
        """Спектральная когерентность с учётом фаз"""
        if not vortex.spectrum:
            return 0.0
        
        total = 0.0
        weight = 0.0
        
        for freq, comp in vortex.spectrum.items():
            # Получаем фазу поля в точке вихря
            field_phase = self.phase_dynamics.get_phase_at(vortex.x, vortex.y, vortex.z, freq)
            phase_match = abs(math.cos(comp.phase - field_phase))
            total += comp.amplitude * phase_match
            weight += comp.amplitude
        
        return total / weight if weight > 0 else 0.0
    
    def _spatial_coherence_3d(self, vortex: Vortex3D) -> float:
        """3D пространственная когерентность"""
        grad = self.phase_dynamics.get_gradient(vortex.x, vortex.y, vortex.z)
        vortex_vec = np.array([vortex.x, vortex.y, vortex.z])
        norm_v = np.linalg.norm(vortex_vec)
        norm_g = np.linalg.norm(grad)
        if norm_v == 0 or norm_g == 0:
            return 0.5
        return abs(np.dot(vortex_vec, grad)) / (norm_v * norm_g + 1e-8)
    
    def _fractal_coherence(self, vortex: Vortex3D, target_scale: float) -> float:
        """Фрактальная когерентность — самоподобие на всех масштабах"""
        if not vortex.children and not vortex.parent:
            return 1.0
        
        child_coherence = 0.0
        for child_word in vortex.children:
            child = self.vortices.get(child_word)
            if child:
                child_coherence += self._parent_child_coherence(vortex, child)
        if vortex.children:
            child_coherence /= len(vortex.children)
        
        parent_coherence = 1.0
        if vortex.parent and vortex.parent in self.vortices:
            parent = self.vortices[vortex.parent]
            parent_coherence = self._parent_child_coherence(parent, vortex)
        
        return (child_coherence + parent_coherence) / 2
    
    def _parent_child_coherence(self, parent: Vortex3D, child: Vortex3D) -> float:
        """Когерентность между родителем и ребёнком"""
        scale_ratio = child.scale / parent.scale if parent.scale != 0 else 1.0
        
        spectral = 0.0
        weight = 0.0
        for freq, pcomp in parent.spectrum.items():
            ccomp = child.spectrum.get(freq * scale_ratio)
            if ccomp:
                phase_match = abs(math.cos(pcomp.phase - ccomp.phase))
                spectral += pcomp.amplitude * ccomp.amplitude * phase_match
                weight += pcomp.amplitude * ccomp.amplitude
        spectral = spectral / weight if weight > 0 else 0.0
        
        parent_pos = np.array([parent.x, parent.y, parent.z])
        child_pos = np.array([child.x, child.y, child.z])
        distance = np.linalg.norm(child_pos - parent_pos)
        max_distance = 1.0 / child.scale if child.scale > 0 else 1.0
        geometric = 1.0 - min(1.0, distance / max_distance)
        
        return spectral * geometric
    
    def _find_nearest_vortex(self, vortex: Vortex3D) -> Optional[str]:
        """Находит ближайший вихрь для фазового сравнения"""
        min_dist = float('inf')
        nearest = None
        
        for word, other in self.vortices.items():
            if word == vortex.word:
                continue
            dist = vortex.distance_to(other)
            if dist < min_dist:
                min_dist = dist
                nearest = word
        
        return nearest
    
    # ========== ВЫСОКОУРОВНЕВЫЕ ОПЕРАЦИИ ==========
    
    def collapse_meaning(self, word: str, context: Optional[str] = None) -> str:
        """Коллапс суперпозиции — выбор смысла"""
        return self.quantum.collapse(word, context)
    
    def entangle_meanings(self, word1: str, word2: str):
        """Запутывает два смысла"""
        self.quantum.entangle(word1, word2)
    
    def create_knot(self, words: List[str], knot_type: KnotType = KnotType.TREFOIL):
        """Создаёт топологический узел"""
        return self.topology.create_knot(words, knot_type)
    
    def create_soliton(self, word: str, position: np.ndarray, amplitude: float = 1.0):
        """Создаёт солитон"""
        return self.nonlinear.create_soliton(word, position, amplitude)
    
    def get_superposition(self, word: str) -> Optional[List[str]]:
        """Возвращает суперпозицию смыслов"""
        return self.quantum.get_superposition(word)
    
    # ========== СОСТОЯНИЕ ==========
    
    def get_state(self) -> Dict:
        """Возвращает полное состояние поля"""
        return {
            "vortices": len(self.vortices),
            "scales": self.scales,
            "resonance_history": self.resonance_history[-20:],
            "phase": self.phase_dynamics.get_state(),
            "nonlinear": self.nonlinear.get_state(),
            "quantum": self.quantum.get_state(),
            "topology": self.topology.get_state()
        }