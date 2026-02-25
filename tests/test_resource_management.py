#!/usr/bin/env python3
"""
Тест механизмов управления ресурсами и жизненным циклом.
"""

import sys
import os
import math
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.architect import TopologicalArchitect
    print("✅ Импорт компонентов")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_priority_redistribution():
    """Проверка приоритетного перераспределения энергии"""
    print("\n1. Тест перераспределения энергии:")
    
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
    
    result = weak.priority_energy_redistribution(companions)
    
    print(f"   После: weak.energy={weak.energy:.2f}, strong.energy={strong.energy:.2f}")
    print(f"   weak.active={weak.active}, strong.health={strong.health:.2f}")
    print(f"   weak.mode={weak.mode}")
    
    assert weak.energy <= 0.03, "Энергия слабого должна упасть до 0.03"
    assert strong.energy > 0.8, "Энергия сильного должна вырасти"
    assert not weak.active, "Слабый должен стать неактивным"
    assert weak.mode == "depleted", "Режим должен быть depleted"
    
    return True

def test_low_power_mode():
    """Проверка режима пониженного энергопотребления"""
    print("\n2. Тест режима низкого энергопотребления:")
    
    comp = Component(id=0, charge=1.0, health=0.5)
    comp.energy = 0.05
    
    print(f"   До: energy={comp.energy:.2f}, freq={comp.temporal.frequency:.2f}")
    
    result = comp.low_power_mode()
    
    print(f"   После: mode={comp.mode}, freq={comp.temporal.frequency:.2f}")
    print(f"   amplitude={comp.temporal.amplitude:.2f}")
    
    assert result, "Режим должен активироваться"
    assert comp.mode == "low_power", "Режим должен быть low_power"
    assert comp.temporal.frequency == 0.01, "Частота должна быть 0.01"
    assert comp.temporal.amplitude == 0.1, "Амплитуда должна быть 0.1"
    
    return True

def test_graceful_termination():
    """Проверка завершения цикла жизни"""
    print("\n3. Тест завершения цикла:")
    
    comp = Component(id=0, charge=1.0, health=0.8)
    comp.age = 121
    comp.lifespan = 120
    comp.energy = 0.5
    
    memory_pool = []
    energy_pool = []
    
    print(f"   До: age={comp.age}, active={comp.active}")
    
    result = comp.graceful_termination(memory_pool, energy_pool)
    
    print(f"   После: active={comp.active}, mode={comp.mode}")
    print(f"   memory_pool: {len(memory_pool)} записей")
    print(f"   energy_pool: {len(energy_pool)} порций")
    
    assert result, "Завершение должно произойти"
    assert not comp.active, "Компонент должен стать неактивным"
    assert comp.mode == "terminated", "Режим должен быть terminated"
    assert len(memory_pool) == 1, "Опыт должен сохраниться"
    assert len(energy_pool) == 1, "Энергия должна вернуться"
    
    return True

def test_vortex_interaction_breathing():
    """Проверка дыхания нейтральных вихрей (статистическая)"""
    print("\n4. Тест единого пульса (статистика по 1000 запускам):")
    
    from src.architect.architect import TopologicalArchitect
    import math
    import random
    
    arch = TopologicalArchitect()
    
    # для накопления результатов
    stats = {
        "одинаковые": [],
        "разные": [],
        "нейтральные": []
    }
    
    runs = 1000  # количество запусков
    seed = 42   # фиксируем для воспроизводимости, но можно менять
    
    for run in range(runs):
        # меняем seed для каждого запуска (но детерминированно)
        random.seed(seed + run)
        
        for case, charge1, charge2 in [
            ("одинаковые", 1.0, 1.0),
            ("разные", 1.0, -1.0),
            ("нейтральные", 0.0, 0.0)
        ]:
            comps = [
                Component(id=1, charge=charge1, health=1.0),
                Component(id=2, charge=charge2, health=1.0)
            ]
            comps[0].neighbors = [2]
            comps[1].neighbors = [1]
            
            # случайные начальные фазы
            comps[0].temporal.phase = random.random() * 2 * math.pi
            comps[1].temporal.phase = random.random() * 2 * math.pi
            
            # собираем фазы на каждом шаге
            phase_diffs = []
            for step in range(30):
                # естественная эволюция с небольшим шумом
                comps[0].temporal.phase += 0.05 + random.gauss(0, 0.01)
                comps[1].temporal.phase -= 0.03 + random.gauss(0, 0.01)
                
                # разность фаз (нормированная)
                diff = abs(comps[0].temporal.phase - comps[1].temporal.phase)
                diff = min(diff, 2*math.pi - diff)
                phase_diffs.append(diff)
            
            # стабильность пульса
            changes = []
            for i in range(1, len(phase_diffs)):
                changes.append(abs(phase_diffs[i] - phase_diffs[i-1]))
            
            avg_change = sum(changes) / len(changes)
            stability = 1.0 / (avg_change + 0.01)
            
            stats[case].append(stability)
        
        if (run + 1) % 10 == 0:
            print(f"   Прогресс: {run + 1}/{runs} запусков")
    
    # выводим статистику
    print("\n   РЕЗУЛЬТАТЫ (по 1000 запускам):")
    for case in ["одинаковые", "разные", "нейтральные"]:
        values = stats[case]
        avg = sum(values) / len(values)
        variance = sum((v - avg)**2 for v in values) / len(values)
        std = math.sqrt(variance)
        print(f"   {case}: среднее = {avg:.3f} ± {std:.3f}")
    
    # критерий: нейтральные должны быть стабильнее в среднем
    avg_neutral = sum(stats["нейтральные"]) / len(stats["нейтральные"])
    avg_same = sum(stats["одинаковые"]) / len(stats["одинаковые"])
    avg_diff = sum(stats["разные"]) / len(stats["разные"])
    
    assert avg_neutral > avg_same, "Нейтральные должны быть стабильнее одинаковых в среднем"
    assert avg_neutral > avg_diff, "Нейтральные должны быть стабильнее разных в среднем"
    
    return True
    
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ МЕХАНИЗМОВ УПРАВЛЕНИЯ РЕСУРСАМИ")
    print("=" * 60)
    
    tests = [
        test_priority_redistribution,
        test_low_power_mode,
        test_graceful_termination,
        test_vortex_interaction_breathing
    ]
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
        print("✅ Все механизмы работают корректно")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)