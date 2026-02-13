#!/usr/bin/env python3
"""
БЫСТРЫЙ ТЕСТ ИСПРАВЛЕНИЙ
Проверяем восстановление здоровья и агрессивную передачу
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fractal.network import FractalNetwork

def test_health_recovery():
    """Тест восстановления здоровья"""
    print("\n" + "="*60)
    print("ТЕСТ ВОССТАНОВЛЕНИЯ ЗДОРОВЬЯ")
    print("="*60)
    
    # Создаём небольшую сеть
    net = FractalNetwork(num_units=5, topology="ring")
    
    # Сильно повреждаем один узел
    damaged_node = net.units[2]
    print(f"1. Повреждаем узел {damaged_node.id}")
    net.sabotage(unit_index=2, damage=0.8, extra_load=0.6)
    
    initial_health = damaged_node.health
    initial_load = damaged_node.load
    print(f"   Начальное состояние: здоровье={initial_health:.2f}, нагрузка={initial_load:.2f}")
    
    # Запускаем восстановление
    print("\n2. Запускаем восстановление (10 шагов)")
    
    health_history = []
    load_history = []
    
    for step in range(10):
        transferred = net.simulate_step(target_load=0.6)
        
        health_history.append(damaged_node.health)
        load_history.append(damaged_node.load)
        
        if step < 3 or step % 3 == 0:
            print(f"   Шаг {step+1}: здоровье={damaged_node.health:.3f}, нагрузка={damaged_node.load:.3f}")
    
    # Анализ результатов
    final_health = damaged_node.health
    final_load = damaged_node.load
    health_improvement = final_health - initial_health
    load_reduction = initial_load - final_load
    
    print(f"\n3. РЕЗУЛЬТАТЫ:")
    print(f"   Улучшение здоровья: {health_improvement:.3f} ({health_improvement/initial_health*100:.1f}%)")
    print(f"   Снижение нагрузки: {load_reduction:.3f} ({load_reduction/initial_load*100:.1f}%)")
    
    # Критерии успеха
    success = True
    if health_improvement < 0.1:
        print("   ❌ Восстановление здоровья недостаточное")
        success = False
    else:
        print("   ✅ Восстановление здоровья удовлетворительное")
    
    if load_reduction < 0.2:
        print("   ❌ Снижение нагрузки недостаточное")
        success = False
    else:
        print("   ✅ Снижение нагрузки удовлетворительное")
    
    if success:
        print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
    else:
        print("\n⚠️  ТЕСТ НЕ ПРОЙДЕН")
    
    return success

def test_network_recovery():
    """Тест восстановления всей сети"""
    print("\n" + "="*60)
    print("ТЕСТ ВОССТАНОВЛЕНИЯ СЕТИ")
    print("="*60)
    
    # Создаём сеть с повреждением нескольких узлов
    net = FractalNetwork(num_units=8, topology="mesh")
    
    # Повреждаем 3 узла
    damaged_indices = [1, 3, 6]
    print(f"1. Повреждаем узлы: {damaged_indices}")
    
    for idx in damaged_indices:
        net.sabotage(unit_index=idx, damage=0.7, extra_load=0.5)
        unit = net.units[idx]
        print(f"   • {unit.id}: здоровье={unit.health:.2f}, нагрузка={unit.load:.2f}")
    
    # Измеряем начальные метрики
    initial_metrics = net.get_network_metrics()
    print(f"\n2. Начальные метрики сети:")
    print(f"   • Среднее здоровье: {initial_metrics['avg_health']:.3f}")
    print(f"   • Разброс нагрузки: {initial_metrics['imbalance']:.3f}")
    print(f"   • Критических узлов: {initial_metrics['unhealthy_nodes']}")
    
    # Восстановление
    print("\n3. Запускаем восстановление (15 шагов)")
    
    for step in range(15):
        transferred = net.simulate_step(target_load=0.6)
        
        if step < 5 or step % 5 == 0:
            metrics = net.get_network_metrics()
            print(f"   Шаг {step+1}: здоровье={metrics['avg_health']:.3f}, разброс={metrics['imbalance']:.3f}")
    
    # Финальные метрики
    final_metrics = net.get_network_metrics()
    print(f"\n4. Финальные метрики сети:")
    print(f"   • Среднее здоровье: {final_metrics['avg_health']:.3f}")
    print(f"   • Разброс нагрузки: {final_metrics['imbalance']:.3f}")
    print(f"   • Критических узлов: {final_metrics['unhealthy_nodes']}")
    
    # Улучшение
    health_improvement = final_metrics['avg_health'] - initial_metrics['avg_health']
    imbalance_reduction = initial_metrics['imbalance'] - final_metrics['imbalance']
    
    print(f"\n5. УЛУЧШЕНИЕ:")
    print(f"   • Улучшение здоровья: {health_improvement:.3f}")
    print(f"   • Снижение разброса: {imbalance_reduction:.3f}")
    
    # Критерии успеха
    success = True
    if final_metrics['avg_health'] < 0.7:
        print("   ❌ Среднее здоровье сети < 0.7")
        success = False
    else:
        print("   ✅ Среднее здоровье сети ≥ 0.7")
    
    if final_metrics['imbalance'] > 0.4:
        print("   ❌ Разброс нагрузки > 0.4")
        success = False
    else:
        print("   ✅ Разброс нагрузки ≤ 0.4")
    
    if final_metrics['unhealthy_nodes'] > 1:
        print(f"   ❌ Критических узлов: {final_metrics['unhealthy_nodes']} (> 1)")
        success = False
    else:
        print(f"   ✅ Критических узлов: {final_metrics['unhealthy_nodes']} (≤ 1)")
    
    if success:
        print("\n🎉 СЕТЬ УСПЕШНО ВОССТАНОВИЛАСЬ!")
    else:
        print("\n⚠️  ВОССТАНОВЛЕНИЕ СЕТИ НЕДОСТАТОЧНО")
    
    return success

if __name__ == "__main__":
    print("🚀 БЫСТРЫЙ ТЕСТ ИСПРАВЛЕНИЙ")
    print("Проверка восстановления здоровья и агрессивной передачи")
    
    test1 = test_health_recovery()
    test2 = test_network_recovery()
    
    print("\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print("="*60)
    print(f"Тест восстановления здоровья: {'✅ ПРОЙДЕН' if test1 else '❌ ПРОВАЛЕН'}")
    print(f"Тест восстановления сети: {'✅ ПРОЙДЕН' if test2 else '❌ ПРОВАЛЕН'}")
    
    if test1 and test2:
        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
        sys.exit(0)
    else:
        print("\n⚠️  ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ОТЛАДКА")
        sys.exit(1)
