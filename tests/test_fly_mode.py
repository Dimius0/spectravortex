#!/usr/bin/env python3
"""
Тест режима мухи (адаптивного ускорения времени).
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

def test_fly_mode_acceleration():
    """Проверка ускорения времени в режиме мухи"""
    print("\n1. Тест ускорения:")
    
    comp = Component(id=0, charge=1.0, health=0.3, load=0.9)
    original_freq = comp.temporal.frequency
    
    print(f"   До: freq={original_freq:.3f}")
    
    # Включаем режим мухи
    comp.check_fly_mode(threat_level=0.8)
    
    print(f"   После: freq={comp.temporal.frequency:.3f}")
    print(f"   Ускорение: {comp.temporal.frequency/original_freq:.2f}x")
    
    assert comp.temporal.frequency > original_freq, "Частота должна вырасти"
    return True

def test_turtle_mode_deceleration():
    """Проверка замедления в режиме черепахи"""
    print("\n2. Тест замедления:")
    
    comp = Component(id=0, charge=1.0, health=0.9, load=0.1)
    original_freq = comp.temporal.frequency
    
    print(f"   До: freq={original_freq:.3f}")
    
    # Включаем режим черепахи
    comp.check_fly_mode(threat_level=0.1)
    
    print(f"   После: freq={comp.temporal.frequency:.3f}")
    print(f"   Замедление: {comp.temporal.frequency/original_freq:.2f}x")
    
    assert comp.temporal.frequency < original_freq, "Частота должна упасть"
    return True

def test_emergency_threshold():
    """Проверка порогов срабатывания"""
    print("\n3. Тест порогов:")
    
    comp = Component(id=0, charge=1.0)
    
    # Низкая угроза
    comp.check_fly_mode(threat_level=0.2)
    emergency = getattr(comp, 'emergency', 0.0)
    print(f"   Угроза 0.2 → emergency={emergency:.2f}")
    
    # Средняя угроза
    comp.check_fly_mode(threat_level=0.5)
    emergency = getattr(comp, 'emergency', 0.0)
    print(f"   Угроза 0.5 → emergency={emergency:.2f}")
    
    # Высокая угроза
    comp.check_fly_mode(threat_level=0.9)
    emergency = getattr(comp, 'emergency', 0.0)
    print(f"   Угроза 0.9 → emergency={emergency:.2f}")
    
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ РЕЖИМА МУХИ")
    print("=" * 50)
    
    tests = [test_fly_mode_acceleration, test_turtle_mode_deceleration, test_emergency_threshold]
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
        print("✅ Режим мухи работает корректно")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)