"""
tau_resonance.py — настоящий резонанс через τ, scale, complexity
ерсия 1.0 — без random()
"""
import math

class TauResonance:
    def __init__(self, tau_min: int = 1, tau_max: int = 66):
        self.tau_min = tau_min
        self.tau_max = tau_max
        
    def compute_resonance(self, mode1, mode2) -> float:
        # 1. τ-резонанс (скорость мышления) — самый важный
        tau_res = self._tau_resonance(mode1.tau, mode2.tau)
        # 2. scale-резонанс
        scale_res = self._scale_resonance(mode1.scale, mode2.scale)
        # 3. complexity-резонанс
        comp_res = self._complexity_resonance(mode1.complexity, mode2.complexity)
        # тоговый резонанс
        resonance = tau_res * 0.5 + scale_res * 0.3 + comp_res * 0.2
        return min(1.0, max(0.0, resonance))
    
    def _tau_resonance(self, tau1: float, tau2: float) -> float:
        diff = abs(tau1 - tau2)
        return 1.0 / (1.0 + diff)
    
    def _scale_resonance(self, scale1: float, scale2: float) -> float:
        if scale1 <= 0 or scale2 <= 0:
            return 0.0
        log_ratio = abs(math.log(scale1 / scale2))
        return 1.0 / (1.0 + log_ratio)
    
    def _complexity_resonance(self, comp1: int, comp2: int) -> float:
        diff = abs(comp1 - comp2)
        return 1.0 / (1.0 + diff)
    
    def should_create_node(self, resonance: float, threshold: float = 0.85) -> bool:
        return resonance > threshold
    
    def should_create_furcation(self, resonance: float, low: float = 0.65, high: float = 0.85) -> bool:
        return low < resonance < high
    
    def get_coherence(self, resonances: list) -> float:
        if not resonances:
            return 0.5
        return sum(resonances) / len(resonances)
