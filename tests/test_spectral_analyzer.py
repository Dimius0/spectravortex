#!/usr/bin/env python3
"""
Тест спектрального анализатора для состояния Хойла.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.spectral_analyzer import SpectralAnalyzer
    print("✅ Импорт модулей")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_spectral_analyzer_basics():
    """Проверка базовой работы спектрального анализатора"""
    print("\n1. Тест базовой функциональности:")
    
    # создаём простую систему из двух компонентов
    comps = [
        Component(id=0, charge=1.0),
        Component(id=1, charge=1.0)
    ]
    
    analyzer = SpectralAnalyzer(sampling_rate=1.0)
    result = analyzer.find_modes(comps, steps=50)
    
    print(f"   Доминирующая частота: {result['dominant_freq']:.4f}")
    print(f"   Спектр содержит {len(result['full_spectrum'])} точек")
    
    assert result['dominant_freq'] is not None, "Должна быть доминирующая частота"
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ СПЕКТРАЛЬНОГО АНАЛИЗАТОРА")
    print("=" * 60)
    
    tests = [test_spectral_analyzer_basics]
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
        print("✅ Спектральный анализатор работает")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)