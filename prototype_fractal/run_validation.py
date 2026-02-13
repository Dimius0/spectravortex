#!/usr/bin/env python3
"""
ЗАПУСК ПОЛНОЙ ВАЛИДАЦИИ ОПТИМИЗИРОВАННОЙ СИСТЕМЫ
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Импорт тестов
from test_integration import run_comprehensive_test
from config_optimizer import apply_optimized_config

def run_full_validation():
    """Запуск полного цикла валидации"""
    
    print("\n" + "="*80)
    print("🚀 ПОЛНЫЙ ЦИКЛ ВАЛИДАЦИИ ОПТИМИЗИРОВАННОЙ СИСТЕМЫ")
    print("="*80)
    
    start_time = time.time()
    
    # Шаг 1: Создание оптимизированной конфигурации
    print("\n🔧 ШАГ 1: СОЗДАНИЕ ОПТИМИЗИРОВАННОЙ КОНФИГУРАЦИИ")
    config_file = apply_optimized_config()
    
    # Шаг 2: Тестирование интеграции
    print("\n🔧 ШАГ 2: ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ")
    integration_success = run_comprehensive_test()
    
    # Шаг 3: Запуск демонстрации
    print("\n🔧 ШАГ 3: ДЕМОНСТРАЦИЯ РАБОТЫ")
    try:
        from demo_optimized import demo_optimized_system
        demo_results = demo_optimized_system()
        demo_success = demo_results['success_criteria_passed'] >= 3
    except Exception as e:
        print(f"❌ Ошибка демонстрации: {e}")
        demo_success = False
    
    # Итоги
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("📋 ИТОГИ ПОЛНОЙ ВАЛИДАЦИИ")
    print("="*80)
    
    print(f"\nВремя выполнения: {elapsed:.2f} секунд")
    print(f"\nРезультаты:")
    print(f"  ✅ Конфигурация создана: {config_file}")
    print(f"  {'✅' if integration_success else '❌'} Тестирование интеграции: {'ПРОЙДЕНО' if integration_success else 'ПРОВАЛЕНО'}")
    print(f"  {'✅' if demo_success else '❌'} Демонстрация работы: {'УСПЕШНА' if demo_success else 'НЕУДАЧНА'}")
    
    if integration_success and demo_success:
        print("\n🎉 ВАЛИДАЦИЯ ПРОЙДЕНА УСПЕШНО!")
        print("Система готова к использованию и интеграции с SpectraVortex.")
        return True
    else:
        print("\n⚠️  ВАЛИДАЦИЯ НЕ ПРОЙДЕНА")
        print("Требуется дополнительная отладка.")
        return False

if __name__ == "__main__":
    success = run_full_validation()
    
    # Выходной код для CI/CD
    sys.exit(0 if success else 1)