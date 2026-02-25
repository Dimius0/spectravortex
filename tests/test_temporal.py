#!/usr/bin/env python3
"""
Тест базовой функциональности эмерджентного времени.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.temporal_state import TemporalState, TimeLayer
    print("✅ Импорт из src.architect")
except ImportError:
    try:
        from architect.temporal_state import TemporalState, TimeLayer
        print("✅ Импорт из architect")
    except ImportError as e:
        print(f"❌ Не удалось импортировать TemporalState: {e}")
        sys.exit(1)

def test_basics():
    """Проверка базовой инициализации"""
    print("\n1. Тест инициализации:")
    
    # Случайная инициализация
    t1 = TemporalState.random_init()
    t2 = TemporalState.random_init()
    
    print(f"   t1: phase={t1.phase:.3f}, freq={t1.frequency:.3f}, scale={t1.time_scale:.3f}")
    print(f"   t2: phase={t2.phase:.3f}, freq={t2.frequency:.3f}, scale={t2.time_scale:.3f}")
    
    # Разность фаз
    diff = t1.phase_diff(t2)
    print(f"   Разность фаз: {diff:.3f}")
    
    # Курамото-связь
    coupling = t1.kuramoto_coupling(t2)
    print(f"   Курамото-связь: {coupling:.3f}")
    
    return True

def test_synchronization():
    """Проверка синхронизации"""
    print("\n2. Тест синхронизации:")
    
    t1 = TemporalState(phase=0.0, frequency=1.0)
    t2 = TemporalState(phase=2.0, frequency=1.0)
    
    print(f"   До: t1.phase={t1.phase:.3f}, t2.phase={t2.phase:.3f}")
    
    for step in range(10):
        t1.synchronize_with(t2, dt=0.2)
        t2.synchronize_with(t1, dt=0.2)
    
    print(f"   После 10 шагов: t1.phase={t1.phase:.3f}, t2.phase={t2.phase:.3f}")
    print(f"   Разность: {abs(t1.phase - t2.phase):.3f}")
    
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ МОДУЛЯ ЭМЕРДЖЕНТНОГО ВРЕМЕНИ")
    print("=" * 50)
    
    tests = [test_basics, test_synchronization]
    passed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("   ✅ Тест пройден")
            else:
                print("   ❌ Тест провален")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print(f"Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("✅ Модуль работает корректно")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)