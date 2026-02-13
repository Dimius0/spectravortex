#!/usr/bin/env python3
"""
ПРИМЕНЕНИЕ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ ДЛЯ УЛУЧШЕНИЯ АДАПТАЦИИ
"""

import sys
from pathlib import Path

# Путь к файлу unit.py
UNIT_FILE = Path("src/fractal/unit.py")

def apply_health_recovery_fix():
    """Добавляет механизм восстановления здоровья"""
    
    if not UNIT_FILE.exists():
        print(f"❌ Файл {UNIT_FILE} не найден")
        return False
    
    with open(UNIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем метод transfer_load
    if 'def transfer_load' not in content:
        print("❌ Метод transfer_load не найден")
        return False
    
    # Ищем место для вставки восстановления здоровья
    # (перед return transferred_total)
    marker = "return transferred_total"
    
    if marker not in content:
        print("❌ Маркер return transferred_total не найден")
        return False
    
    # Новый код для восстановления здоровья
    health_recovery_code = '''
        # 8. АВТОМАТИЧЕСКОЕ ВОССТАНОВЛЕНИЕ ЗДОРОВЬЯ
        # Если узел успешно передал нагрузку и здоровье < 1.0
        if transferred_total > 0 and self.health < 1.0:
            # Базовое восстановление
            health_recovery = 0.02  # 2% за успешную передачу
            
            # Усиленное восстановление в режиме ENERGY_CONSERVATION
            if self.state and self.state.behavioral_tendency == "ENERGY_CONSERVATION":
                health_recovery *= 3.0
            
            # Восстановление пропорционально успешной передаче
            recovery_multiplier = min(2.0, transferred_total * 10.0)
            health_recovery *= recovery_multiplier
            
            self.health = min(1.0, self.health + health_recovery)
        
        # 9. ШТРАФ ЗА ПЕРЕГРУЗКУ
        if self.load > 0.85 and self.health > 0.1:
            # Постепенное ухудшение здоровья при постоянной перегрузке
            overload_penalty = (self.load - 0.85) * 0.1  # 10% штраф за перегрузку
            self.health = max(0.1, self.health - overload_penalty)
        
        # 10. САМОЛЕЧЕНИЕ (очень медленное)
        if self.health < 0.5 and transferred_total == 0:
            # Пассивное восстановление для сильно повреждённых узлов
            self.health = min(0.5, self.health + 0.005)
    '''
    
    # Вставляем код перед return
    new_content = content.replace(
        marker,
        health_recovery_code + '\n\n        ' + marker
    )
    
    # Сохраняем изменения
    backup_file = UNIT_FILE.with_suffix('.unit.backup.py')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open(UNIT_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Механизм восстановления здоровья добавлен")
    print(f"   Резервная копия: {backup_file}")
    return True

def apply_aggressive_transfer_fix():
    """Увеличивает агрессивность передачи нагрузки"""
    
    with open(UNIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем блок расчёта safe_amount
    old_code = """safe_amount = min(
                    transfer_amount,
                    max_to_transfer,
                    neighbor_capacity
                )"""
    
    new_code = """# АГРЕССИВНАЯ ПЕРЕДАЧА ДЛЯ БЫСТРОГО ВОССТАНОВЛЕНИЯ
                    safe_amount = transfer_amount * 2.0  # Удваиваем объём передачи
                    
                    # ДИНАМИЧЕСКИЕ ОГРАНИЧЕНИЯ
                    # 1. Можно отдавать до 90% текущей нагрузки
                    max_transfer_percent = 0.9
                    if self.health < 0.4:
                        max_transfer_percent = 0.95  # Больные узлы могут отдавать больше
                    
                    # 2. Сосед может принять больше при низкой нагрузке
                    neighbor_capacity_boost = 1.0
                    if neighbor.load < 0.3:
                        neighbor_capacity_boost = 1.5
                    
                    # ФИНАЛЬНОЕ ОГРАНИЧЕНИЕ
                    safe_amount = min(
                        safe_amount,
                        self.load * max_transfer_percent,
                        (1.0 - neighbor.load) * neighbor_capacity_boost * 1.5,
                        self.health * 2.0  # Здоровые узлы могут передавать больше
                    )
                    
                    # БОНУС ДЛЯ ПОВРЕЖДЁННЫХ УЗЛОВ
                    if self.health < 0.5:
                        damage_bonus = 1.0 + (0.5 - self.health) * 2.0  # +0% до +100%
                        safe_amount *= damage_bonus"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open(UNIT_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Агрессивность передачи увеличена (x2)")
        return True
    else:
        print("⚠️  Код safe_amount не найден в ожидаемом формате")
        return False

def apply_intuition_boost():
    """Усиливает интуитивный контур"""
    
    INTUITION_FILE = Path("src/fractal/intuition.py")
    
    if not INTUITION_FILE.exists():
        print(f"❌ Файл {INTUITION_FILE} не найден")
        return False
    
    with open(INTUITION_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Увеличиваем порог уверенности для архетипов
    old_threshold = "self.min_confidence_threshold = 0.3"
    new_threshold = "self.min_confidence_threshold = 0.2"  # Более чувствительный
    
    if old_threshold in content:
        content = content.replace(old_threshold, new_threshold)
    
    # Увеличиваем скорость обучения
    old_learning = "self.learning_rate = 0.1"
    new_learning = "self.learning_rate = 0.15"
    
    if old_learning in content:
        content = content.replace(old_learning, new_learning)
    
    # Добавляем больше архетипов для повреждённых узлов
    archetype_marker = "# 1. АРХЕТИП КАСКАДНОГО ОТКАЗА"
    
    new_archetype = '''        # 0. АРХЕТИП КРИТИЧЕСКОГО ПОВРЕЖДЕНИЯ (новый)
        archetypes['critical_damage'] = Archetype(
            name="critical_damage",
            pattern={
                'gestalt': lambda g: 'CRITICAL' in g or 'VULNERABLE' in g,
                'health': lambda h: h < 0.4,
                'load': lambda l: l > 0.8,
                'urgency': lambda u: u > 0.6
            },
            typical_response={
                'action_bias': 'SELF_PRESERVATION',
                'transfer_multiplier': 3.0,
                'health_recovery_bonus': 2.0,
                'message': "🚨 КРИТИЧЕСКОЕ ПОВРЕЖДЕНИЕ! Максимальная разгрузка!"
            }
        )
        
        # 1. АРХЕТИП КАСКАДНОГО ОТКАЗА'''
    
    if archetype_marker in content:
        content = content.replace(archetype_marker, new_archetype)
    
    # Сохраняем изменения
    backup_file = INTUITION_FILE.with_suffix('.intuition.backup.py')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open(INTUITION_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Интуитивный контур усилен:")
    print("   - Порог уверенности снижен до 0.2")
    print("   - Скорость обучения увеличена до 0.15")
    print("   - Добавлен архетип 'critical_damage'")
    return True

def create_quick_test():
    """Создаёт быстрый тест для проверки исправлений"""
    
    test_code = '''#!/usr/bin/env python3
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
    print("\\n" + "="*60)
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
    print("\\n2. Запускаем восстановление (10 шагов)")
    
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
    
    print(f"\\n3. РЕЗУЛЬТАТЫ:")
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
        print("\\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
    else:
        print("\\n⚠️  ТЕСТ НЕ ПРОЙДЕН")
    
    return success

def test_network_recovery():
    """Тест восстановления всей сети"""
    print("\\n" + "="*60)
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
    print(f"\\n2. Начальные метрики сети:")
    print(f"   • Среднее здоровье: {initial_metrics['avg_health']:.3f}")
    print(f"   • Разброс нагрузки: {initial_metrics['imbalance']:.3f}")
    print(f"   • Критических узлов: {initial_metrics['unhealthy_nodes']}")
    
    # Восстановление
    print("\\n3. Запускаем восстановление (15 шагов)")
    
    for step in range(15):
        transferred = net.simulate_step(target_load=0.6)
        
        if step < 5 or step % 5 == 0:
            metrics = net.get_network_metrics()
            print(f"   Шаг {step+1}: здоровье={metrics['avg_health']:.3f}, разброс={metrics['imbalance']:.3f}")
    
    # Финальные метрики
    final_metrics = net.get_network_metrics()
    print(f"\\n4. Финальные метрики сети:")
    print(f"   • Среднее здоровье: {final_metrics['avg_health']:.3f}")
    print(f"   • Разброс нагрузки: {final_metrics['imbalance']:.3f}")
    print(f"   • Критических узлов: {final_metrics['unhealthy_nodes']}")
    
    # Улучшение
    health_improvement = final_metrics['avg_health'] - initial_metrics['avg_health']
    imbalance_reduction = initial_metrics['imbalance'] - final_metrics['imbalance']
    
    print(f"\\n5. УЛУЧШЕНИЕ:")
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
        print("\\n🎉 СЕТЬ УСПЕШНО ВОССТАНОВИЛАСЬ!")
    else:
        print("\\n⚠️  ВОССТАНОВЛЕНИЕ СЕТИ НЕДОСТАТОЧНО")
    
    return success

if __name__ == "__main__":
    print("🚀 БЫСТРЫЙ ТЕСТ ИСПРАВЛЕНИЙ")
    print("Проверка восстановления здоровья и агрессивной передачи")
    
    test1 = test_health_recovery()
    test2 = test_network_recovery()
    
    print("\\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print("="*60)
    print(f"Тест восстановления здоровья: {'✅ ПРОЙДЕН' if test1 else '❌ ПРОВАЛЕН'}")
    print(f"Тест восстановления сети: {'✅ ПРОЙДЕН' if test2 else '❌ ПРОВАЛЕН'}")
    
    if test1 and test2:
        print("\\n🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
        sys.exit(0)
    else:
        print("\\n⚠️  ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ОТЛАДКА")
        sys.exit(1)
'''
    
    test_file = Path("quick_test_fixes.py")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    test_file.chmod(0o755)  # Делаем исполняемым
    
    print(f"✅ Быстрый тест создан: {test_file}")
    return test_file

def main():
    """Основная функция применения исправлений"""
    print("\n" + "="*70)
    print("🛠️  ПРИМЕНЕНИЕ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ ДЛЯ УЛУЧШЕНИЯ АДАПТАЦИИ")
    print("="*70)
    
    fixes_applied = []
    
    # Применяем исправления
    print("\n1. Добавление механизма восстановления здоровья...")
    if apply_health_recovery_fix():
        fixes_applied.append("Восстановление здоровья")
    
    print("\n2. Увеличение агрессивности передачи нагрузки...")
    if apply_aggressive_transfer_fix():
        fixes_applied.append("Агрессивная передача")
    
    print("\n3. Усиление интуитивного контура...")
    if apply_intuition_boost():
        fixes_applied.append("Усиление интуиции")
    
    # Создаём тест
    print("\n4. Создание теста для проверки исправлений...")
    test_file = create_quick_test()
    
    # Итоги
    print("\n" + "="*70)
    print("📋 ИТОГИ ПРИМЕНЕНИЯ ИСПРАВЛЕНИЙ:")
    print("="*70)
    
    if fixes_applied:
        print(f"✅ Применено {len(fixes_applied)} исправлений:")
        for fix in fixes_applied:
            print(f"   • {fix}")
    else:
        print("❌ Исправления не применены")
    
    print(f"\n🔧 Тест для проверки: python {test_file}")
    print("\n🚀 Запустите тест для проверки работы исправлений:")
    print(f"   python {test_file}")
    
    return len(fixes_applied) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)