#!/usr/bin/env python3
"""
Запуск всех тестов фрактальной системы
"""
import sys
import os
import subprocess

def run_test(test_name, command):
    """Запускает тест и возвращает результат"""
    print(f"\n{'='*60}")
    print(f"🚀 ЗАПУСК: {test_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 минут таймаут
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        return success, result.stdout
        
    except subprocess.TimeoutExpired:
        print(f"❌ ТЕСТ ПРЕРВАН: {test_name} превысил лимит времени")
        return False, ""
    except Exception as e:
        print(f"❌ ОШИБКА В ТЕСТЕ {test_name}: {e}")
        return False, ""

def main():
    """Основная функция запуска тестов"""
    print("🧪 ПОЛНОЕ ТЕСТИРОВАНИЕ FRACTAL NETWORK")
    print("="*60)
    
    # Проверяем наличие файлов
    tests = [
        ("Быстрый тест", ["python", "quick_test_fixes.py"]),
        ("Стресс-тест", ["python", "stress_test.py"]),
        ("Случайные сценарии", ["python", "random_scenarios.py"])
    ]
    
    # Проверка существования файлов
    for test_name, cmd in tests:
        script_file = cmd[1]
        if not os.path.exists(script_file):
            print(f"❌ Файл {script_file} не найден!")
            return False
    
    results = []
    
    # Запускаем все тесты
    for test_name, cmd in tests:
        success, output = run_test(test_name, cmd)
        results.append((test_name, success))
        
        # Проверяем ключевые индикаторы в выводе
        if success and "ПРОЙДЕН" in output.upper():
            print(f"✅ {test_name}: ПРОЙДЕН")
        elif not success:
            print(f"❌ {test_name}: ПРОВАЛЕН")
        else:
            print(f"⚠️  {test_name}: НЕОПРЕДЕЛЕННЫЙ РЕЗУЛЬТАТ")
    
    # Итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {'ПРОЙДЕН' if success else 'ПРОВАЛЕН'}")
    
    print(f"\n📈 Успешно пройдено: {passed}/{total} ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система стабильна и готова к работе.")
        return True
    elif passed >= total * 0.7:
        print("\n⚠️  СИСТЕМА РАБОТАЕТ, но требуются некоторые доработки.")
        return True
    else:
        print("\n❌ ТРЕБУЕТСЯ СЕРЬЕЗНАЯ ДОРАБОТКА СИСТЕМЫ.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)