#!/usr/bin/env python3
"""
Тест принципа кислородной маски.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    print("✅ Импорт компонентов")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_oxygen_mask_transfer():
    """Проверка передачи ресурса от слабого к сильному"""
    print("\n1. Тест передачи ресурса:")
    
    # Создаём компоненты
    weak = Component(id=0, charge=0.5, health=0.2)
    weak.energy = 0.15
    weak.neighbors = [1, 2]
    
    strong = Component(id=1, charge=2.0, health=0.9)
    strong.energy = 0.8
    strong.neighbors = [0, 2, 3]
    
    medium = Component(id=2, charge=1.0, health=0.6)
    medium.energy = 0.5
    medium.neighbors = [0, 1]
    
    companions = [weak, strong, medium]
    
    print(f"   До: weak.energy={weak.energy:.2f}, strong.energy={strong.energy:.2f}")
    
    # Слабый ищет, кому отдать
    result = weak.oxygen_mask(companions)
    
    print(f"   После: weak.energy={weak.energy:.2f}, strong.energy={strong.energy:.2f}")
    print(f"   weak.active={weak.active}, strong.health={strong.health:.2f}")
    
    assert weak.energy <= 0.03, "Энергия слабого должна упасть"
    assert strong.energy > 0.8, "Энергия сильного должна вырасти"
    assert not weak.active, "Слабый должен стать неактивным"
    
    return True

def test_viability_property():
    """Проверка расчёта жизнестойкости"""
    print("\n2. Тест жизнестойкости:")
    
    comp = Component(id=0, charge=2.0, health=0.8)
    comp.neighbors = [1, 2, 3]
    
    v = comp.viability
    print(f"   viability = {v:.2f} (ожидается ~ 2.0*0.8*3 = 4.8)")
    
    assert v > 4.5, "Жизнестойкость должна быть около 4.8"
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ КИСЛОРОДНОЙ МАСКИ")
    print("=" * 50)
    
    tests = [test_oxygen_mask_transfer, test_viability_property]
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
        print("✅ Кислородная маска работает")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)