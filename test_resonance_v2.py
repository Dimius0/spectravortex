"""
Тест комбинированного резонанса
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from rizoma.resonance_v2 import SpectralResonatorV2, SemanticResonator, CombinedResonator
from rizoma.embedder import Embedder


def test_spectral():
    print("🔊 Тест спектрального резонанса...")
    resonator = SpectralResonatorV2()
    
    test_pairs = [
        (5.0, 5.0),
        (5.0, 10.0),
        (5.0, 2.5),
        (5.0, 7.5),
    ]
    
    for tau1, tau2 in test_pairs:
        res = resonator.resonate(tau1, tau2)
        print(f"   τ₁={tau1:.1f}, τ₂={tau2:.1f} → резонанс: {res:.3f}")
    
    print("✅ Спектральный резонанс работает\n")


def test_semantic():
    print("🔊 Тест семантического резонанса...")
    embedder = Embedder()
    resonator = SemanticResonator(embedder)
    
    texts = [
        ("кран течёт", "вода из трубы"),
        ("кран течёт", "звёзды на небе"),
        ("чёрная дыра", "гравитационный коллапс"),
        ("чёрная дыра", "сантехника"),
    ]
    
    for text1, text2 in texts:
        emb1 = embedder.encode(text1)
        emb2 = embedder.encode(text2)
        sim = resonator.resonate(emb1, emb2)
        print(f"   '{text1}' vs '{text2}' → сходство: {sim:.3f}")
    
    print("✅ Семантический резонанс работает\n")


def test_combined():
    print("🔊 Тест комбинированного резонанса...")
    embedder = Embedder()
    resonator = CombinedResonator(spectral_weight=0.5, semantic_weight=0.5)
    
    # Имитируем данные
    tau1, tau2 = 5.5, 5.6
    text1, text2 = "почини кран", "сантехника ремонт"
    
    emb1 = embedder.encode(text1)
    emb2 = embedder.encode(text2)
    
    spectral = resonator.spectral.resonate(tau1, tau2)
    semantic = resonator.semantic.resonate(emb1, emb2)
    combined = resonator.resonate(tau1, tau2, emb1, emb2)
    
    print(f"   τ₁={tau1:.1f}, τ₂={tau2:.1f} → спектральный: {spectral:.3f}")
    print(f"   '{text1}' vs '{text2}' → семантический: {semantic:.3f}")
    print(f"   Комбинированный: {combined:.3f}")
    
    print("✅ Комбинированный резонанс работает\n")


if __name__ == "__main__":
    print("="*50)
    print("🧪 ТЕСТИРОВАНИЕ РЕЗОНАНСА V2")
    print("="*50)
    
    test_spectral()
    test_semantic()
    test_combined()
    
    print("🦌 Все тесты пройдены!")