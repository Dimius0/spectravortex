#!/usr/bin/env python3
"""
Тест поиска моды Хойла в тетраэдрической конфигурации.
"""

import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.spectral_analyzer import SpectralAnalyzer
    print("✅ Импорт модулей")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def create_tetrahedron():
    """Создаёт 4 компонента в тетраэдрической конфигурации"""
    comps = []
    # вершины тетраэдра (условные координаты не важны, только фазы)
    for i in range(4):
        comp = Component(id=i, charge=1.0, health=1.0)
        # начальные фазы, близкие к симметричным
        comp.temporal.phase = (i * 2 * math.pi / 4) + 0.1
        comps.append(comp)
    
    # задаём связи (каждый с каждым)
    for i in range(4):
        comps[i].neighbors = [j for j in range(4) if j != i]
    
    return comps

def test_tetrahedron_modes():
    """Поиск коллективных колебательных мод тетраэдра"""
    print("\n1. Поиск мод тетраэдрической конфигурации:")
    
    comps = create_tetrahedron()
    analyzer = SpectralAnalyzer(sampling_rate=1.0)
    
    # собираем историю СИСТЕМЫ в целом
    history = []
    for step in range(200):
        # естественная эволюция с малыми возмущениями
        for c in comps:
            c.temporal.phase += 0.01
            # небольшое случайное отклонение
            c.temporal.phase += np.random.normal(0, 0.001)
        # параметр порядка (средняя фаза)
        phases = [c.temporal.phase for c in comps]
        mean_phase = sum(phases) / len(phases)
        history.append(mean_phase)
    
    # Фурье-анализ
    fft = np.fft.fft(history)
    freqs = np.fft.fftfreq(len(history), d=analyzer.sampling_rate)
    
    # ищем доминирующую частоту (кроме нулевой)
    positive = freqs[:len(freqs)//2]
    magnitudes = np.abs(fft[:len(freqs)//2])
    dominant_idx = np.argmax(magnitudes[1:]) + 1
    dominant_freq = positive[dominant_idx]
    
    print(f"   Доминирующая частота системы: {dominant_freq:.4f}")
    
    # ожидаем частоту в диапазоне 0.01-0.03
    assert 0.01 < dominant_freq < 0.03, f"Частота {dominant_freq} вне ожидаемого диапазона"
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ МОДЫ ХОЙЛА")
    print("=" * 60)
    
    tests = [test_tetrahedron_modes]
    passed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("   ✅ Тест пройден")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print(f"Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("✅ Тетраэдр дышит")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)