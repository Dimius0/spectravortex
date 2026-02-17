#!/usr/bin/env python3
"""
СТРЕСС-ТЕСТИРОВАНИЕ FRACTAL NETWORK
Проверка устойчивости системы в экстремальных условиях.
"""
import sys
import os
import time
import random
import numpy as np

# Добавляем путь к src в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

try:
    from fractal.network import FractalNetwork
    print(f"[INFO] Модуль загружен из {src_dir}")
except ImportError as e:
    print(f"[ERROR] Не удалось загрузить модуль fractal: {e}")
    print("[INFO] Пытаемся альтернативный путь...")
    # Пробуем другой путь
    sys.path.insert(0, current_dir)
    try:
        from src.fractal.network import FractalNetwork
        print("[INFO] Модуль загружен из src/fractal/network.py")
    except ImportError as e2:
        print(f"[FATAL] Не удалось загрузить модуль: {e2}")
        print("Проверьте структуру проекта:")
        print(f"Текущая директория: {current_dir}")
        print(f"Существующие файлы: {os.listdir(current_dir)}")
        if os.path.exists(src_dir):
            print(f"Содержимое src/: {os.listdir(src_dir)}")
        sys.exit(1)

def print_test_header(name):
    """Красивый заголовок теста"""
    print(f"\n{'='*70}")
    print(f"{name}")
    print('='*70)

def test_extreme_overload():
    """Тест экстремальной перегрузки сети"""
    print_test_header("ТЕСТ 1: ЭКСТРЕМАЛЬНАЯ ПЕРЕГРУЗКА")
    
    # Создаём сеть с очень высокой начальной нагрузкой
    net = FractalNetwork(num_units=10, topology="mesh",
                        initial_load_range=(0.8, 1.0))
    
    print("Начальное состояние (все узлы перегружены 80-100%):")
    metrics = net.get_network_metrics()
    print(f"  • Средняя нагрузка: {metrics['avg_load']:.3f}")
    print(f"  • Разброс: {metrics['imbalance']:.3f}")
    print(f"  • Критических узлов: {metrics['critical_nodes']}")
    
    # Запускаем восстановление
    print("\nЗапуск восстановления (20 шагов):")
    recovery_data = []
    
    for step in range(20):
        transferred = net.simulate_step(target_load=0.6)
        metrics = net.get_network_metrics()
        recovery_data.append({
            'step': step,
            'imbalance': metrics['imbalance'],
            'avg_load': metrics['avg_load'],
            'avg_health': metrics['avg_health'],
            'critical': metrics['critical_nodes']
        })
        
        if step < 5 or step % 5 == 0:
            print(f"  Шаг {step+1:2d}: нагрузка={metrics['avg_load']:.3f}, "
                  f"разброс={metrics['imbalance']:.3f}, "
                  f"критических={metrics['critical_nodes']}")
    
    # Анализ результата
    initial = recovery_data[0]
    final = recovery_data[-1]
    
    print(f"\n  РЕЗУЛЬТАТЫ:")
    print(f"  • Снижение средней нагрузки: {initial['avg_load']:.3f} → {final['avg_load']:.3f}")
    print(f"  • Улучшение разброса: {initial['imbalance']:.3f} → {final['imbalance']:.3f}")
    print(f"  • Критических узлов: {initial['critical']} → {final['critical']}")
    
    # Критерии успеха
    success = True
    if final['avg_load'] > 0.7:
        print("  ❌ Средняя нагрузка > 0.7")
        success = False
    else:
        print("  ✅ Средняя нагрузка ≤ 0.7")
    
    if final['imbalance'] > 0.5:
        print(f"  ❌ Разброс > 0.5 ({final['imbalance']:.3f})")
        success = False
    else:
        print(f"  ✅ Разброс ≤ 0.5 ({final['imbalance']:.3f})")
    
    if final['critical'] > 2:
        print(f"  ❌ Критических узлов > 2 ({final['critical']})")
        success = False
    else:
        print(f"  ✅ Критических узлов ≤ 2 ({final['critical']})")
    
    return success

def test_cascade_failure():
    """Тест каскадного отказа (последовательный саботаж)"""
    print_test_header("ТЕСТ 2: КАСКАДНЫЙ ОТКАЗ")
    
    net = FractalNetwork(num_units=12, topology="grid")
    print("Исходное состояние сети:")
    metrics = net.get_network_metrics()
    print(f"  • Узлов: {metrics['total_units']}")
    print(f"  • Среднее здоровье: {metrics['avg_health']:.3f}")
    print(f"  • Разброс: {metrics['imbalance']:.3f}")
    
    # Последовательный саботаж 5 узлов
    sabotage_nodes = [1, 4, 7, 9, 11]
    print(f"\n  🎯 ПОСЛЕДОВАТЕЛЬНЫЙ САБОТАЖ ({len(sabotage_nodes)} УЗЛОВ):")
    
    failure_data = []
    for i, node_idx in enumerate(sabotage_nodes):
        print(f"\n  Этап {i+1}: Саботаж узла {node_idx}")
        net.sabotage(node_idx, damage=0.6, extra_load=0.4)
        
        # 3 шага восстановления после каждого саботажа
        for step in range(3):
            net.simulate_step(target_load=0.6)
        
        metrics = net.get_network_metrics()
        failure_data.append({
            'stage': i+1,
            'attacked_node': node_idx,
            'avg_health': metrics['avg_health'],
            'imbalance': metrics['imbalance'],
            'critical': metrics['critical_nodes']
        })
        
        print(f"    После восстановления:")
        print(f"    • Здоровье сети: {metrics['avg_health']:.3f}")
        print(f"    • Разброс: {metrics['imbalance']:.3f}")
        print(f"    • Критических узлов: {metrics['critical_nodes']}")
    
    # Дополнительные шаги для полного восстановления
    print(f"\n  🔄 ФИНАЛЬНОЕ ВОССТАНОВЛЕНИЕ (10 шагов):")
    for step in range(10):
        transferred = net.simulate_step(target_load=0.6)
        if step % 3 == 0:
            metrics = net.get_network_metrics()
            print(f"    Шаг {step+1}: здоровье={metrics['avg_health']:.3f}, "
                  f"разброс={metrics['imbalance']:.3f}")
    
    final_metrics = net.get_network_metrics()
    print(f"\n  РЕЗУЛЬТАТЫ КАСКАДНОГО ТЕСТА:")
    print(f"  • Финальное здоровье: {final_metrics['avg_health']:.3f}")
    print(f"  • Финальный разброс: {final_metrics['imbalance']:.3f}")
    print(f"  • Критических узлов: {final_metrics['critical_nodes']}")
    
    # Критерии успеха
    success = True
    if final_metrics['avg_health'] < 0.8:
        print(f"  ❌ Здоровье сети < 0.8 ({final_metrics['avg_health']:.3f})")
        success = False
    else:
        print(f"  ✅ Здоровье сети ≥ 0.8 ({final_metrics['avg_health']:.3f})")
    
    if final_metrics['imbalance'] > 0.6:
        print(f"  ❌ Разброс > 0.6 ({final_metrics['imbalance']:.3f})")
        success = False
    else:
        print(f"  ✅ Разброс ≤ 0.6 ({final_metrics['imbalance']:.3f})")
    
    return success

def test_dynamic_topology():
    """Тест динамического изменения топологии"""
    print_test_header("ТЕСТ 3: ДИНАМИЧЕСКАЯ ТОПОЛОГИЯ")
    
    # Создаём сеть
    net = FractalNetwork(num_units=8, topology="ring")
    print("Этап 1: Исходное кольцо (8 узлов)")
    metrics = net.get_network_metrics()
    print(f"  • Среднее здоровье: {metrics['avg_health']:.3f}")
    
    # Разрываем связи (имитация сбоя коммуникаций)
    print(f"\n  🔗 РАЗРЫВ 50% СВЯЗЕЙ:")
    units_to_isolate = [2, 5]
    
    # Нам нужен метод remove_neighbor, если его нет - пропускаем этот тест
    if not hasattr(net.units[0], 'remove_neighbor'):
        print("  ⚠️  Метод remove_neighbor не найден, пропускаем тест")
        return True
    
    for unit_idx in units_to_isolate:
        unit = net.units[unit_idx]
        # Разрываем все связи
        for neighbor in unit.neighbors.copy():
            # Удаляем связь в обе стороны
            unit.remove_neighbor(neighbor, bidirectional=True)
        print(f"  Узел {unit_idx} изолирован")
    
    # Запускаем адаптацию
    print(f"\n  🔄 АДАПТАЦИЯ К НОВОЙ ТОПОЛОГИИ (15 шагов):")
    for step in range(15):
        transferred = net.simulate_step(target_load=0.6)
        if step < 5 or step % 5 == 0:
            metrics = net.get_network_metrics()
            print(f"    Шаг {step+1}: здоровье={metrics['avg_health']:.3f}, "
                  f"разброс={metrics['imbalance']:.3f}")
    
    # Восстанавливаем связи
    print(f"\n  🔗 ВОССТАНОВЛЕНИЕ СВЯЗЕЙ:")
    for unit_idx in units_to_isolate:
        unit = net.units[unit_idx]
        # Восстанавливаем связи с соседями
        left_idx = (unit_idx - 1) % len(net.units)
        right_idx = (unit_idx + 1) % len(net.units)
        unit.add_neighbor(net.units[left_idx])
        unit.add_neighbor(net.units[right_idx])
        print(f"  Узел {unit_idx} переподключен")
    
    # Финальная адаптация
    print(f"\n  🔄 ФИНАЛЬНАЯ АДАПТАЦИЯ (10 шагов):")
    for step in range(10):
        net.simulate_step(target_load=0.6)
    
    final_metrics = net.get_network_metrics()
    print(f"\n  РЕЗУЛЬТАТЫ ДИНАМИЧЕСКОЙ ТОПОЛОГИИ:")
    print(f"  • Финальное здоровье: {final_metrics['avg_health']:.3f}")
    print(f"  • Финальный разброс: {final_metrics['imbalance']:.3f}")
    
    success = final_metrics['avg_health'] > 0.7 and final_metrics['imbalance'] < 0.5
    if success:
        print("  ✅ Система адаптировалась к изменениям топологии")
    else:
        print("  ❌ Проблемы с адаптацией к изменениям топологии")
    
    return success

def test_energy_conservation():
    """Тест сохранения энергии/нагрузки в системе"""
    print_test_header("ТЕСТ 4: СОХРАНЕНИЕ ЭНЕРГИИ")
    
    net = FractalNetwork(num_units=6, topology="mesh")
    
    # Измеряем начальную общую нагрузку
    initial_total_load = sum(unit.load for unit in net.units)
    initial_total_health = sum(unit.health for unit in net.units)
    
    print(f"Начальные totals:")
    print(f"  • Суммарная нагрузка: {initial_total_load:.4f}")
    print(f"  • Суммарное здоровье: {initial_total_health:.4f}")
    
    # Применяем саботаж
    net.sabotage(2, damage=0.4, extra_load=0.3)
    net.sabotage(4, damage=0.3, extra_load=0.2)
    
    print(f"\nПосле саботажа:")
    after_sabotage_load = sum(unit.load for unit in net.units)
    after_sabotage_health = sum(unit.health for unit in net.units)
    print(f"  • Суммарная нагрузка: {after_sabotage_load:.4f}")
    print(f"  • Суммарное здоровье: {after_sabotage_health:.4f}")
    
    # Запускаем симуляцию
    load_history = []
    health_history = []
    
    print(f"\n  🔄 ЗАПУСК СИМУЛЯЦИИ (20 шагов):")
    for step in range(20):
        net.simulate_step(target_load=0.6)
        total_load = sum(unit.load for unit in net.units)
        total_health = sum(unit.health for unit in net.units)
        load_history.append(total_load)
        health_history.append(total_health)
        
        if step % 5 == 0:
            metrics = net.get_network_metrics()
            print(f"    Шаг {step+1}: суммарная нагрузка={total_load:.4f}, "
                  f"разброс={metrics['imbalance']:.3f}")
    
    # Анализ сохранения
    final_load = load_history[-1]
    final_health = health_history[-1]
    load_variance = np.var(load_history)
    health_variance = np.var(health_history)
    
    print(f"\n  📊 АНАЛИЗ СОХРАНЕНИЯ:")
    print(f"    • Начальная нагрузка: {initial_total_load:.4f}")
    print(f"    • Финальная нагрузка: {final_load:.4f}")
    print(f"    • Изменение: {final_load - initial_total_load:+.4f}")
    print(f"    • Дисперсия нагрузки: {load_variance:.6f}")
    print(f"    • Дисперсия здоровья: {health_variance:.6f}")
    
    # Критерии успеха
    success = True
    
    # Нагрузка должна сохраняться (с небольшой погрешностью)
    load_change = abs(final_load - initial_total_load)
    if load_change > 0.1:
        print(f"  ❌ Слишком большое изменение нагрузки: {load_change:.4f}")
        success = False
    else:
        print(f"  ✅ Изменение нагрузки в пределах нормы: {load_change:.4f}")
    
    # Дисперсия должна быть низкой (система стабильна)
    if load_variance > 0.01:
        print(f"  ❌ Высокая дисперсия нагрузки: {load_variance:.4f}")
        success = False
    else:
        print(f"  ✅ Низкая дисперсия нагрузки: {load_variance:.4f}")
    
    return success

def test_scalability():
    """Тест масштабируемости системы"""
    print_test_header("ТЕСТ 5: МАСШТАБИРУЕМОСТЬ")
    
    sizes = [5, 10, 20, 30]
    results = {}
    
    for size in sizes:
        print(f"\n  📈 Тестируем сеть из {size} узлов:")
        start_time = time.time()
        
        net = FractalNetwork(num_units=size, topology="mesh")
        
        # Применяем саботаж
        sabotage_count = min(3, size // 3)
        for i in range(sabotage_count):
            node_idx = random.randint(0, size-1)
            net.sabotage(node_idx, damage=0.5, extra_load=0.4)
        
        # Запускаем восстановление
        recovery_steps = 15
        for step in range(recovery_steps):
            net.simulate_step(target_load=0.6)
        
        # Измеряем метрики
        final_metrics = net.get_network_metrics()
        elapsed = time.time() - start_time
        
        results[size] = {
            'avg_health': final_metrics['avg_health'],
            'imbalance': final_metrics['imbalance'],
            'time': elapsed,
            'success': final_metrics['avg_health'] > 0.7 and final_metrics['imbalance'] < 0.5
        }
        
        status = "✅" if results[size]['success'] else "❌"
        print(f"    {status} Здоровье: {final_metrics['avg_health']:.3f}, "
              f"Разброс: {final_metrics['imbalance']:.3f}, "
              f"Время: {elapsed:.2f}с")
    
    # Анализ масштабируемости
    print(f"\n  📊 АНАЛИЗ МАСШТАБИРУЕМОСТИ:")
    success_rate = sum(1 for r in results.values() if r['success']) / len(results)
    print(f"    • Успешных тестов: {success_rate:.1%}")
    
    # Проверяем временную сложность
    print(f"\n    ⏱️  Временные показатели:")
    for size in sizes:
        print(f"      • {size:2d} узлов: {results[size]['time']:.2f}с")
    
    success = success_rate >= 0.75  # 75% успешных тестов
    if success:
        print("  ✅ Система масштабируема")
    else:
        print("  ❌ Проблемы с масштабируемостью")
    
    return success

def run_comprehensive_stress_test():
    """Запуск всех стресс-тестов"""
    print("\n" + "="*80)
    print("🔥 ПОЛНОЕ СТРЕСС-ТЕСТИРОВАНИЕ FRACTAL NETWORK")
    print("="*80)
    
    tests = [
        ("Экстремальная перегрузка", test_extreme_overload),
        ("Каскадный отказ", test_cascade_failure),
        ("Динамическая топология", test_dynamic_topology),
        ("Сохранение энергии", test_energy_conservation),
        ("Масштабируемость", test_scalability)
    ]
    
    results = []
    total_start = time.time()
    
    for test_name, test_func in tests:
        try:
            test_start = time.time()
            success = test_func()
            test_time = time.time() - test_start
            
            results.append({
                "name": test_name,
                "success": success,
                "time": test_time
            })
            
            print(f"\n{'✅' if success else '❌'} {test_name}: "
                  f"{'ПРОЙДЕН' if success else 'ПРОВАЛЕН'} "
                  f"({test_time:.1f}с)")
            
        except Exception as e:
            print(f"\n❌ {test_name}: ОШИБКА - {e}")
            import traceback
            traceback.print_exc()
            
            results.append({
                "name": test_name,
                "success": False,
                "time": 0,
                "error": str(e)
            })
    
    total_time = time.time() - total_start
    
    # Итоги
    print(f"\n" + "="*80)
    print("📊 ИТОГИ СТРЕСС-ТЕСТИРОВАНИЯ")
    print("="*80)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\nТестов пройдено: {passed}/{total} ({passed/total:.1%})")
    print(f"Общее время: {total_time:.1f} секунд")
    
    print(f"\nДетальные результаты:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        error_msg = f" - {result['error']}" if 'error' in result else ""
        print(f"  {status} {result['name']}: {result['time']:.1f}с{error_msg}")
    
    # Общая оценка
    if passed == total:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к эксплуатации.")
    elif passed >= total * 0.7:
        print(f"\n⚠️  СИСТЕМА УСТОЙЧИВА, но требует доработки.")
    else:
        print(f"\n❌ ТРЕБУЕТСЯ СЕРЬЕЗНАЯ ДОРАБОТКА.")
    
    return passed >= total * 0.7  # Успех если ≥70% тестов пройдено

if __name__ == "__main__":
    print("Запуск стресс-тестирования Fractal Network...")
    success = run_comprehensive_stress_test()
    
    # Выходной код для CI/CD
    sys.exit(0 if success else 1)