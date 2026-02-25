#!/usr/bin/env python3
"""
do_everything.py — универсальный скрипт для проверки всего проекта.
Запускает тесты, проверяет структуру, генерирует отчёт.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Цвета для вывода
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_step(msg):
    print(f"{GREEN}→{RESET} {msg}")

def print_ok(msg):
    print(f" {GREEN}✅{RESET} {msg}")

def print_warn(msg):
    print(f" {YELLOW}⚠️{RESET} {msg}")

def print_error(msg):
    print(f" {RED}❌{RESET} {msg}")

def run_tests():
    """Запускает все тесты и возвращает результат"""
    print_step("Запуск тестов...")
    
    test_files = [
        "tests/test_hoyle_state.py",
        "tests/test_temperature_decay.py",
        "tests/test_nuclear_modes.py",
        "tests/test_resource_management.py"
    ]
    
    results = {}
    all_passed = True
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print_warn(f"Файл {test_file} не найден, пропускаем")
            continue
        
        print(f"  {test_file}...")
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            results[test_file] = {
                "passed": passed,
                "output": result.stdout,
                "error": result.stderr
            }
            
            if passed:
                print_ok(f"{test_file} пройден")
            else:
                print_error(f"{test_file} упал")
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print_error(f"{test_file} превысил таймаут")
            results[test_file] = {"passed": False, "error": "Timeout"}
            all_passed = False
        except Exception as e:
            print_error(f"{test_file} ошибка: {e}")
            results[test_file] = {"passed": False, "error": str(e)}
            all_passed = False
    
    return results, all_passed

def check_structure():
    """Проверяет наличие всех необходимых папок и файлов"""
    print_step("Проверка структуры проекта...")
    
    required_dirs = [
        "src/architect",
        "tests",
        "predictions",
        "discoveries"
    ]
    
    required_files = [
        "src/architect/spectral_analyzer.py",
        "src/architect/component.py",
        "src/architect/temporal_state.py",
        "README.md",
        "README.en.md"
    ]
    
    discoveries_files = [
        "butterfly_effect_chi.md",
        "fractal_truth.md",
        "accumulation_trampoline.md",
        "ca48_chi.md",
        "emergent_time_and_consciousness.md",
        "paradox_of_the_seer.md"
    ]
    
    structure_ok = True
    
    # Проверяем папки
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_ok(f"Папка {dir_path} существует")
        else:
            print_warn(f"Папка {dir_path} не найдена")
            structure_ok = False
    
    # Проверяем файлы
    for file_path in required_files:
        if Path(file_path).exists():
            print_ok(f"Файл {file_path} существует")
        else:
            print_warn(f"Файл {file_path} не найден")
            structure_ok = False
    
    # Проверяем discoveries
    print_step("Проверка discoveries/...")
    discoveries_ok = True
    for file_name in discoveries_files:
        file_path = f"discoveries/{file_name}"
        if Path(file_path).exists():
            print_ok(f"  {file_name}")
        else:
            print_warn(f"  {file_name} отсутствует")
            discoveries_ok = False
    
    return structure_ok, discoveries_ok

def generate_report(test_results, structure_ok, discoveries_ok, all_passed):
    """Генерирует итоговый отчёт"""
    print_step("Генерация отчёта summary.md...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Итоговый отчёт SpectraVortex

**Дата:** {timestamp}
**Версия:** 1.0.0

---

## 1. Структура проекта

| Компонент | Статус |
|-----------|--------|
| Основные папки | {"✅" if structure_ok else "⚠️"} |
| discoveries/ | {"✅" if discoveries_ok else "⚠️"} |

---

## 2. Результаты тестов

| Тест | Статус |
|------|--------|
"""
    
    for test_file, result in test_results.items():
        status = "✅" if result["passed"] else "❌"
        report += f"| {test_file} | {status} |\n"
    
    report += f"""
---

## 3. Общий итог

**Все тесты:** {"✅ ПРОЙДЕНЫ" if all_passed else "❌ ЕСТЬ ПАДЕНИЯ"}

**Структура:** {"✅ в порядке" if structure_ok else "⚠️ требует внимания"}

**discoveries/:** {"✅ заполнена" if discoveries_ok else "⚠️ неполная"}

---

## 4. Следующие шаги

"""
    if not all_passed:
        report += "- [ ] Исправить упавшие тесты\n"
    if not discoveries_ok:
        report += "- [ ] Дополнить папку discoveries/\n"
    if not structure_ok:
        report += "- [ ] Восстановить структуру проекта\n"
    
    report += "- [ ] Залить на GitHub\n"
    report += "- [ ] Шаг к `noise_analyzer`\n"
    
    # Записываем отчёт
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print_ok("Отчёт сохранён в summary.md")
    return report

def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("🚀 DO EVERYTHING — универсальная проверка проекта")
    print("="*60)
    
    # Проверяем структуру
    structure_ok, discoveries_ok = check_structure()
    
    # Запускаем тесты
    test_results, all_passed = run_tests()
    
    # Генерируем отчёт
    report = generate_report(test_results, structure_ok, discoveries_ok, all_passed)
    
    # Финальный вердикт
    print("\n" + "="*60)
    if all_passed and structure_ok and discoveries_ok:
        print(f"{GREEN}✅ ВСЁ ОТЛИЧНО! Можно заливать на GitHub.{RESET}")
    elif all_passed:
        print(f"{YELLOW}⚠️ Тесты проходят, но структура требует внимания.{RESET}")
    else:
        print(f"{RED}❌ Есть проблемы. Смотри отчёт summary.md{RESET}")
    print("="*60)

if __name__ == "__main__":
    main()