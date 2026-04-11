"""
Resonance V2 — спектральный + семантический резонанс
Версия 2.0 — с эмбеддингами
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .embedder import Embedder


class SpectralResonatorV2:
    """Спектральный резонатор с гармониками и адаптацией"""
    
    def __init__(self):
        self.harmonics = {
            1.0: 1.0,
            2.0: 0.6,
            0.5: 0.5,
            3.0: 0.4,
            1/3: 0.3,
            4.0: 0.2,
            0.25: 0.15
        }
        self.hit_count = {h: 0 for h in self.harmonics}
        self.total_count = 0
    
    def resonate(self, tau1: float, tau2: float) -> float:
        """Вычисляет спектральный резонанс между двумя τ"""
        total = 0.0
        best_harmonic = None
        best_resonance = 0
        
        for harmonic, weight in self.harmonics.items():
            harmonic_tau = tau1 * harmonic
            diff = abs(harmonic_tau - tau2)
            resonance = 1.0 / (1.0 + diff)
            
            if resonance > best_resonance:
                best_resonance = resonance
                best_harmonic = harmonic
            
            total += resonance * weight
        
        if best_resonance > 0.7 and best_harmonic:
            self.hit_count[best_harmonic] += 1
            self.total_count += 1
        
        if self.total_count % 100 == 0:
            self._adapt_weights()
        
        return total
    
    def _adapt_weights(self):
        """Адаптирует веса гармоник под статистику"""
        total_hits = sum(self.hit_count.values())
        if total_hits == 0:
            return
        
        for h in self.harmonics:
            self.harmonics[h] = self.hit_count[h] / total_hits * len(self.harmonics)
        
        old_sum = sum(self.harmonics.values())
        if old_sum > 0:
            factor = len(self.harmonics) / old_sum
            for h in self.harmonics:
                self.harmonics[h] *= factor


class SemanticResonator:
    """Семантический резонатор на эмбеддингах"""
    
    def __init__(self, embedder: Embedder = None):
        self.embedder = embedder or Embedder()
    
    def resonate(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Семантический резонанс = косинусное сходство"""
        return self.embedder.similarity(emb1, emb2)
    
    def resonate_with_text(self, text: str, emb2: np.ndarray) -> float:
        """Семантический резонанс текста с эмбеддингом"""
        emb1 = self.embedder.encode(text)
        return self.resonate(emb1, emb2)


class CombinedResonator:
    """
    Комбинированный резонатор: спектральный + семантический
    """
    
    def __init__(self, spectral_weight: float = 0.5, semantic_weight: float = 0.5):
        self.spectral = SpectralResonatorV2()
        self.semantic = SemanticResonator()
        self.spectral_weight = spectral_weight
        self.semantic_weight = semantic_weight
    
    def resonate(self, tau1: float, tau2: float, 
                 emb1: Optional[np.ndarray] = None, 
                 emb2: Optional[np.ndarray] = None) -> float:
        """
        Вычисляет комбинированный резонанс.
        Если эмбеддинги не предоставлены — только спектральный.
        """
        spectral = self.spectral.resonate(tau1, tau2)
        
        if emb1 is not None and emb2 is not None:
            semantic = self.semantic.resonate(emb1, emb2)
            return spectral * self.spectral_weight + semantic * self.semantic_weight
        
        return spectral
    
    def resonate_with_text(self, tau1: float, tau2: float,
                           text: str, emb2: np.ndarray) -> float:
        """Резонанс с текстом (вычисляет эмбеддинг текста)"""
        emb1 = self.semantic.embedder.encode(text)
        return self.resonate(tau1, tau2, emb1, emb2)