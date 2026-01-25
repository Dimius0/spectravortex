#!/usr/bin/env python3
"""
🚀 Автопилот для SpectraVortex
Запускает: make all + дополнительные проверки
"""

import os
import sys
import subprocess
import time
from pathlib import Path


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_header(text):
    """Красивый заголовок"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🌀 {text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")


def run_command(command, description=None):
    """Запускает команду с выводом"""
    if description:
        print(f"\n{Colors.YELLOW}▶ {description}...{Colors.END}")
        print(f"{Colors.YELLOW}$ {command}{Colors.END}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ Успешно{Colors.END}")
            if result.stdout:
                print(result.stdout[:500])  # Первые 500 символов вывода
        else:
            print(f"{Colors.RED}✗ Ошибка (код: {result.returncode}){Colors.END}")
            if result.stderr:
                print(f"{Colors.RED}Ошибка:{Colors.END}")
                print(result.stderr[:1000])

        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.RED}✗ Исключение: {e}{Colors.END}")
        return False


def main():
    """Основная функция автопилота"""
    print_header("SPECTRAVORTEX АВТОПИЛОТ")
    print(f"{Colors.YELLOW}Время: {time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")

    successes = []
    failures = []

    # 1. Проверяем структуру проекта
    print_header("1. ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")

    required_files = [
        "main.py",
        "pyproject.toml",
        "simulator/field.py",
        "simulator/elements.py",
        "examples/hello_photon.svx",
    ]

    for file in required_files:
        if Path(file).exists():
            print(f"{Colors.GREEN}✓ {file}{Colors.END}")
            successes.append(f"Файл {file} найден")
        else:
            print(f"{Colors.RED}✗ {file} - ОТСУТСТВУЕТ{Colors.END}")
            failures.append(f"Файл {file} отсутствует")

    # 2. Запускаем make all
    print_header("2. ЗАПУСК ПОЛНОЙ ПРОВЕРКИ (make all)")

    commands = [
        ("make install", "Установка зависимостей"),
        ("make test-fast", "Быстрые тесты"),
        ("make lint", "Проверка стиля кода"),
    ]

    for cmd, desc in commands:
        if run_command(cmd, desc):
            successes.append(desc)
        else:
            failures.append(desc)

    # 3. Проверяем примеры
    print_header("3. ПРОВЕРКА ПРИМЕРОВ")

    if Path("examples/hello_photon.svx").exists():
        run_command(
            "python main.py --compile examples/hello_photon.svx",
            "Запуск примера hello_photon.svx",
        )

    # 4. Итоги
    print_header("ИТОГИ ПРОВЕРКИ")

    print(
        f"{Colors.GREEN}✅ УСПЕШНО: {len(successes)}/{len(successes)+len(failures)}{Colors.END}"
    )
    for success in successes[-5:]:  # Последние 5 успехов
        print(f"  {Colors.GREEN}✓ {success}{Colors.END}")

    if failures:
        print(f"\n{Colors.RED}❌ ПРОБЛЕМЫ: {len(failures)}{Colors.END}")
        for failure in failures:
            print(f"  {Colors.RED}✗ {failure}{Colors.END}")

        print(f"\n{Colors.YELLOW}🔧 РЕКОМЕНДАЦИИ:{Colors.END}")
        print("  1. Запустите: make format (исправит форматирование)")
        print("  2. Запустите: make clean (очистит кэш)")
        print("  3. Проверьте логи выше для деталей")

        return 1
    else:
        print(f"\n{Colors.GREEN}🎉 ВСЁ ОТЛИЧНО! Проект готов к работе.{Colors.END}")
        print(f"{Colors.BLUE}Следующие шаги:{Colors.END}")
        print("  1. Запустите: make run-example (проверит примеры)")
        print("  2. Запустите: make dev (полная установка для разработки)")
        print("  3. Начните реализацию compiler/ модулей")
        return 0


if __name__ == "__main__":
    sys.exit(main())
