"""
resonance.py — модуль резонанса поля H
Версия 16.0 — с учётом фрактальных масштабов
"""
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from .vortex import Vortex3D, SpectralComponent
from .phase_dynamics import PhaseDynamics
from .nonlinear_dynamics import NonlinearDynamics
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
        if len(self.history) < 2:
            return 0.0
        return self.history[-1] - self.history[0]


class Fractal3DCoherentSpectralResonance:
    """
    Трёхмерный фрактальный когерентный спектральный резонанс
    Версия 16.0 — с учётом фрактальных масштабов
    """

    def __init__(self, field=None):
        self.field = field
        self.vortices: Dict[str, Vortex3D] = {}
        self._init_fractal_scales()

        self.buffers: Dict[float, ResonanceBuffer] = {}
        for scale in self.scales:
            self.buffers[scale] = ResonanceBuffer(size=5, decay=0.7)

        self.focus_buffer = ResonanceBuffer(size=3, decay=0.5)
        self.resonance_history: List[float] = []

        self.phase_dynamics = PhaseDynamics(field)
        self.nonlinear = NonlinearDynamics(field)
        self.quantum = QuantumAnalogy(field)
        self.topology = Topology(field)

        self.dt = 0.1

    def _init_fractal_scales(self):
        """Фрактальные масштабы: от буквы до смысла"""
        self.scales = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]

    # ========== МАСШТАБНЫЙ ФАКТОР ==========

    def scale_factor(self, scale1: float, scale2: float) -> float:
        """
        Коэффициент близости масштабов.
        Логарифмическая шкала: 1.0 и 0.3 — разница в ~1.2, а не в 0.7.
        Близкие масштабы дают коэффициент >0.5.
        """
        if scale1 <= 0 or scale2 <= 0:
            return 0.0
        log_ratio = abs(math.log(scale1 / scale2))
        return 1.0 / (1.0 + log_ratio)

    def scale_resonance(self, mode_scale: float, question_scale: float, base_resonance: float) -> float:
        """
        Применяет масштабный фактор к резонансу.
        Чем ближе масштабы, тем выше итоговый резонанс.
        """
        sf = self.scale_factor(mode_scale, question_scale)
        # Базовый резонанс (70%) + масштабный фактор (30%)
        return base_resonance * (0.7 + 0.3 * sf)

    # ========== БАЗОВЫЕ МЕТОДЫ РЕЗОНАНСА ==========

    def _spectral_coherence(self, spec1: Dict[float, SpectralComponent],
                            spec2: Dict[float, SpectralComponent]) -> float:
        if not spec1 or not spec2:
            return 0.0
        common = 0.0
        total = 0.0
        all_taus = set(spec1.keys()) | set(spec2.keys())
        for tau in all_taus:
            a1 = spec1.get(tau, SpectralComponent(0, 0)).amplitude
            a2 = spec2.get(tau, SpectralComponent(0, 0)).amplitude
            common += min(a1, a2)
            total += max(a1, a2)
        return common / total if total > 0 else 0.0

    def _phase_coherence(self, spec1: Dict[float, SpectralComponent],
                         spec2: Dict[float, SpectralComponent]) -> float:
        if not spec1 or not spec2:
            return 0.0
        total = 0.0
        weight = 0.0
        for tau in set(spec1.keys()) & set(spec2.keys()):
            comp1 = spec1[tau]
            comp2 = spec2[tau]
            phase_match = abs(math.cos(comp1.phase - comp2.phase))
            total += min(comp1.amplitude, comp2.amplitude) * phase_match
            weight += min(comp1.amplitude, comp2.amplitude)
        return total / weight if weight > 0 else 0.0

    def _spatial_coherence_3d(self, vortex) -> float:
        """3D пространственная когерентность вихря"""
        min_dist = float('inf')
        vortex_tau = vortex.get_dominant_tau() or 16.0
    
        for word, other in self.vortices.items():
            if word == vortex.word:
                continue
            other_tau = other.get_dominant_tau() or 16.0
            if abs(other_tau - vortex_tau) < 2.0:
                dist = math.sqrt((vortex.x - other.x)**2 + 
                                (vortex.y - other.y)**2 + 
                                (vortex.z - other.z)**2)
                if dist < min_dist:
                    min_dist = dist
    
        if min_dist < float('inf'):
            return 1.0 / (1.0 + min_dist)
        return 0.0

    def _fractal_coherence(self, mode, text: str) -> float:
        """Фрактальная когерентность"""
        scale = min(1.0, len(text) / 500)
        return scale * mode.amplitude

    # ========== ОСНОВНОЙ МЕТОД ==========

    def coherent_resonance(self, word: str, target_scale: float = 1.0) -> float:
        """Упрощённая версия — без нелинейной динамики"""
        vortex = self.vortices.get(word)
        if not vortex:
            return 0.0
    
        spectral = self._spectral_coherence(vortex.spectrum, vortex.spectrum)
        spatial_3d = self._spatial_coherence_3d(vortex)
    
        base = spectral * spatial_3d
    
        if hasattr(vortex, 'scale'):
            scale_res = self.scale_factor(vortex.scale, target_scale)
        else:
            scale_res = 1.0
    
        resonance = base * (0.7 + 0.3 * scale_res)
        return min(1.0, resonance)

    # ========== РЕЗОНАНС МЕЖДУ ДВУМЯ МОДАМИ ==========

    def resonance_between_modes(self, mode1, mode2) -> float:
        """
        Вычисляет резонанс между двумя модами с учётом масштабов.
        Используется для интерференции и фуркаций.
        """
        from .personality import SpectralMode
        
        # Спектральная когерентность
        spec1 = self.field.phrase_spectrum(mode1.content[:500]) if hasattr(self.field, 'phrase_spectrum') else {}
        spec2 = self.field.phrase_spectrum(mode2.content[:500]) if hasattr(self.field, 'phrase_spectrum') else {}
        spectral = self._spectral_coherence(spec1, spec2)
        
        # Фазовая когерентность
        phase = self._phase_coherence(spec1, spec2)
        
        # Масштабный фактор
        scale_sim = self.scale_factor(mode1.scale, mode2.scale)
        
        # Комбинированный резонанс
        return spectral * 0.4 + phase * 0.3 + scale_sim * 0.3

    # ========== ВЫСОКОУРОВНЕВЫЕ ОПЕРАЦИИ ==========

    def collapse_meaning(self, word: str, context: Optional[str] = None) -> str:
        return self.quantum.collapse(word, context)

    def entangle_meanings(self, word1: str, word2: str):
        self.quantum.entangle(word1, word2)

    def create_knot(self, words: List[str], knot_type: KnotType = KnotType.TREFOIL):
        return self.topology.create_knot(words, knot_type)

    def create_soliton(self, word: str, position: np.ndarray, amplitude: float = 1.0):
        return self.nonlinear.create_soliton(word, position, amplitude)

    def get_superposition(self, word: str) -> Optional[List[str]]:
        return self.quantum.get_superposition(word)

    def add_vortex(self, word: str, spectrum: Dict[float, SpectralComponent],
                   x: float = 0, y: float = 0, z: float = 0,
                   parent: Optional[str] = None, scale: float = 1.0):
        """Добавляет вихрь с указанием масштаба"""
        vortex = Vortex3D(word, x, y, z, spectrum, parent, scale=scale)
        self.vortices[word] = vortex

        if parent and parent in self.vortices:
            self.vortices[parent].children.append(word)

        meanings = [word]
        if parent:
            meanings.append(parent)
        self.quantum.create_superposition(word, meanings)

        dominant_tau = vortex.get_dominant_tau() or 16.0
        self.phase_dynamics.add_state(word, dominant_tau, 0.0)

    def get_state(self) -> Dict:
        return {
            "vortices": len(self.vortices),
            "scales": self.scales,
            "resonance_history": self.resonance_history[-20:],
            "phase": self.phase_dynamics.get_state(),
            "nonlinear": self.nonlinear.get_state(),
            "quantum": self.quantum.get_state(),
            "topology": self.topology.get_state()
        }