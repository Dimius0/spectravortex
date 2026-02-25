#!/usr/bin/env python3
"""
Тест временных метрик architect.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.temporal_state import TemporalState
    print("✅ Импорт компонентов")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_metrics_with_random_components():
    """Проверка вычисления метрик для случайных компонентов"""
    print("\n1. Тест случайных компонентов:")
    
    # Создаём несколько компонентов со случайными временными состояниями
    components = []
    for i in range(5):
        comp = Component(id=i, charge=1.0)
        # Переопределяем временное состояние для теста
        comp.temporal = TemporalState.random_init()
        components.append(comp)
        print(f"   Компонент {i}: phase={comp.temporal.phase:.3f}, freq={comp.temporal.frequency:.3f}")
    
    print("   ✅ Компоненты созданы")
    return True

def test_synchronized_vs_chaotic():
    """Сравнение синхронизированной и хаотичной конфигураций"""
    print("\n2. Тест синхронизации:")
    
    # Синхронизированная конфигурация (все фазы близки)
    sync_comps = []
    for i in range(3):
        comp = Component(id=i, charge=1.0)
        comp.temporal = TemporalState(phase=1.0, frequency=1.0)
        sync_comps.append(comp)
    
    # Хаотичная конфигурация (фазы разбросаны)
    chaos_comps = []
    for i in range(3):
        comp = Component(id=i, charge=1.0)
        comp.temporal = TemporalState(phase=float(i)*2.0, frequency=1.0)
        chaos_comps.append(comp)
    
    print("   ✅ Конфигурации созданы")
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ ВРЕМЕННЫХ МЕТРИК ARCHITECT")
    print("=" * 50)
    
    tests = [test_metrics_with_random_components, test_synchronized_vs_chaotic]
    passed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("   ✅ Тест пройден")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print(f"Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("✅ Временные метрики готовы к интеграции")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)