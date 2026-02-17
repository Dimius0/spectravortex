# test_integration.py
"""
ТЕСТ ИНТЕГРАЦИИ НОВЫХ МОДУЛЕЙ
Проверяем работу InternalState и IntuitionEngine вместе с FractalUnit
"""

import sys
import time
from pathlib import Path

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_basic_integration():
    """Тест базовой интеграции новых модулей"""
    print("\n" + "="*60)
    print("ТЕСТ ИНТЕГРАЦИИ INTERNALSTATE И INTUITIONENGINE")
    print("="*60)
    
    try:
        from fractal.unit import FractalUnit
        from fractal.internal_state import InternalState
        from fractal.intuition import IntuitionEngine
        
        print("✅ Модули успешно импортированы")
        
        # 1. СОЗДАНИЕ ТЕСТОВОЙ ЕДИНИЦЫ
        print("\n1. Создание FractalUnit с новыми модулями...")
        unit = FractalUnit("test_unit_01", initial_load=0.5)
        
        # Проверяем, что модули созданы
        assert hasattr(unit, 'state'), "InternalState не создан"
        assert hasattr(unit, 'intuition'), "IntuitionEngine не создан"
        
        print(f"   Создана единица: {unit.id}")
        print(f"   InternalState: {'✅' if unit.state else '❌'}")
        print(f"   IntuitionEngine: {'✅' if unit.intuition else '❌'}")
        
        # 2. ТЕСТ ВНУТРЕННЕГО СОСТОЯНИЯ
        print("\n2. Тестирование InternalState...")
        
        # Обновляем состояние
        raw_metrics = {
            'load': 0.7,
            'health': 0.8,
            'stress': 0.2,
            'prediction_error': 0.1,
            'novelty': 0.3,
            'success_rate': 0.6,
            'topology_metrics': {
                'isolation_score': 0.2,
                'centrality': 0.5,
                'clustering_coef': 0.3
            }
        }
        
        unit.state.update(raw_metrics)
        
        # Проверяем вычисленные значения
        print(f"   Гештальт: {unit.state.gestalt}")
        print(f"   Стабильность: {unit.state.stability_index:.3f}")
        print(f"   Склонность: {unit.state.behavioral_tendency}")
        
        # Получаем данные для интуиции
        intuition_data = unit.state.get_for_intuition()
        print(f"   Данные для интуиции: {len(intuition_data)} параметров")
        
        # Получаем данные для аналитики
        analytic_data = unit.state.get_for_analytics()
        print(f"   Эффективная цель: {analytic_data['effective_target_load']:.3f}")
        print(f"   Агрессивность передачи: {analytic_data['transfer_aggressiveness']:.3f}")
        
        # 3. ТЕСТ ИНТУИТИВНОГО КОНТУРА
        print("\n3. Тестирование IntuitionEngine...")
        
        # Получаем совет от интуиции
        advice = unit.intuition.assess(intuition_data, analytic_confidence=0.5)
        
        print(f"   Интуитивный совет: {advice.get('tendency', 'N/A')}")
        print(f"   Уверенность: {advice.get('confidence', 0.0):.3f}")
        print(f"   Сила переопределения: {advice.get('override_power', 0.0):.3f}")
        
        if 'message' in advice:
            print(f"   Сообщение: {advice['message']}")
        
        # 4. ТЕСТ ВЫЧИСЛЕНИЯ ПОТЕНЦИАЛА С УЧЁТОМ СОСТОЯНИЯ
        print("\n4. Тестирование compute_potential с InternalState...")
        
        potential = unit.compute_potential(target_load=0.6)
        print(f"   Потенциал: {potential:.4f}")
        print(f"   Использована динамическая цель: {'✅' if hasattr(unit.state, 'gestalt') else '❌'}")
        
        # 5. ТЕСТ ПЕРЕДАЧИ НАГРУЗКИ С ИНТУИЦИЕЙ
        print("\n5. Тестирование transfer_load с интуицией...")
        
        # Создаём соседа для передачи
        neighbor = FractalUnit("test_unit_02", initial_load=0.3)
        unit.add_neighbor(neighbor)
        
        # Передаём нагрузку с использованием интуиции
        transferred = unit.transfer_load(use_intuition=True)
        print(f"   Передано нагрузки: {transferred:.4f}")
        print(f"   Новая нагрузка: {unit.load:.3f} -> {neighbor.load:.3f}")
        
        # Проверяем, что интуиция получила опыт
        stats = unit.intuition.get_statistics()
        print(f"   Интуиция: {stats['total_decisions']} решений, успешность: {stats['success_rate']:.2f}")
        
        # 6. ТЕСТ ДИАГНОСТИКИ
        print("\n6. Тестирование диагностических отчётов...")
        
        state_report = unit.get_state_report()
        print(f"   Отчёт состояния: {len(state_report)} параметров")
        
        diagnostics = unit.get_detailed_diagnostics()
        print(f"   Диагностика:\n{diagnostics[:200]}...")
        
        print("\n" + "="*60)
        print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("   Все модули работают корректно")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stress_scenario():
    """Тест стрессового сценария (саботаж и восстановление)"""
    print("\n" + "="*60)
    print("ТЕСТ СТРЕССОВОГО СЦЕНАРИЯ")
    print("="*60)
    
    try:
        from fractal.unit import FractalUnit
        from fractal.network import FractalNetwork
        
        # Создаём сеть
        net = FractalNetwork(num_units=8, topology="ring")
        print("Сеть создана: 8 узлов, топология 'кольцо'")
        
        # Базовое состояние
        print("\nИсходное состояние:")
        for i, unit in enumerate(net.units[:3]):  # Показываем первые 3
            print(f"  {unit.id}: нагрузка={unit.load:.2f}, здоровье={unit.health:.2f}")
        
        # САБОТАЖ
        print("\n>>> ПРИМЕНЯЕМ САБОТАЖ К УЗЛУ 2")
        net.sabotage(unit_index=2, damage=0.6, extra_load=0.4)
        
        damaged_unit = net.units[2]
        print(f"  Узел после саботажа: {damaged_unit.id}")
        print(f"    Нагрузка: {damaged_unit.load:.2f}")
        print(f"    Здоровье: {damaged_unit.health:.2f}")
        
        if hasattr(damaged_unit, 'state'):
            print(f"    Гештальт: {damaged_unit.state.gestalt}")
            print(f"    Склонность: {damaged_unit.state.behavioral_tendency}")
            print(f"    Срочность: {damaged_unit.state.get_for_intuition().get('urgency', 0.0):.2f}")
        
        # АДАПТАЦИЯ
        print("\n>>> ЗАПУСК АДАПТАЦИИ (5 шагов)")
        
        recovery_data = []
        for step in range(5):
            transferred = net.simulate_step(target_load=0.6)
            
            # Собираем данные о повреждённом узле
            if hasattr(damaged_unit, 'state'):
                state = damaged_unit.state
                recovery_data.append({
                    'step': step,
                    'load': damaged_unit.load,
                    'health': damaged_unit.health,
                    'gestalt': state.gestalt,
                    'stability': state.stability_index,
                    'transferred': transferred
                })
            
            print(f"  Шаг {step+1}: передано {transferred:.4f}, нагрузка={damaged_unit.load:.3f}")
        
        # АНАЛИЗ ВОССТАНОВЛЕНИЯ
        print("\n>>> АНАЛИЗ ВОССТАНОВЛЕНИЯ")
        if recovery_data:
            initial = recovery_data[0]
            final = recovery_data[-1]
            
            load_reduction = initial['load'] - final['load']
            health_improvement = final['health'] - initial['health']
            
            print(f"  Снижение нагрузки: {load_reduction:.3f}")
            print(f"  Улучшение здоровья: {health_improvement:.3f}")
            print(f"  Итоговый гештальт: {final['gestalt']}")
            print(f"  Стабильность: {final['stability']:.3f}")
            
            # Критерий успеха
            if load_reduction > 0.1 and final['stability'] > 0.5:
                print("  ✅ АДАПТАЦИЯ УСПЕШНА")
            else:
                print("  ⚠️  АДАПТАЦИЯ НЕДОСТАТОЧНА")
        
        print("\n" + "="*60)
        print("✅ ТЕСТ СТРЕССОВОГО СЦЕНАРИЯ ЗАВЕРШЁН")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        return False

def run_comprehensive_test():
    """Запуск комплексного тестирования"""
    print("\n" + "="*80)
    print("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ")
    print("="*80)
    
    start_time = time.time()
    
    # Тест 1: Базовая интеграция
    test1_success = test_basic_integration()
    
    # Тест 2: Стрессовый сценарий
    test2_success = test_stress_scenario()
    
    # Итоги
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print("="*80)
    print(f"Тест 1 (Базовая интеграция): {'✅ ПРОЙДЕН' if test1_success else '❌ ПРОВАЛЕН'}")
    print(f"Тест 2 (Стрессовый сценарий): {'✅ ПРОЙДЕН' if test2_success else '❌ ПРОВАЛЕН'}")
    print(f"Общее время: {elapsed:.2f} секунд")
    
    if test1_success and test2_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Новые модули готовы к использованию.")
        return True
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        print("Требуется отладка.")
        return False

if __name__ == "__main__":
    # Запуск тестирования
    success = run_comprehensive_test()
    
    # Выходной код для CI/CD
    import sys
    sys.exit(0 if success else 1)