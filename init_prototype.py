#!/usr/bin/env python3
"""
init_prototype.py — Интерактивный мастер настройки прототипа фрактально-адаптивного модуля.
Запуск: python init_prototype.py
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

# --- Конфигурация проекта ---
PROJECT_NAME = "prototype_fractal"
PYTHON_VERSION = "3.10"

# --- Утилиты для вывода и взаимодействия ---
def print_step(step_num, title):
    """Красивый вывод шага"""
    print(f"\n{'='*60}")
    print(f"ШАГ {step_num}: {title}")
    print(f"{'='*60}")

def ask_yes_no(question, default="y"):
    """Запрашивает подтверждение y/n с подсветкой рекомендации"""
    choices = "Y/n" if default.lower() in ("y", "yes") else "y/N"
    prompt = f"{question} [{choices}]: "
    
    while True:
        response = input(prompt).strip().lower()
        if not response:
            response = default.lower()
        
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("Пожалуйста, введите 'y' или 'n'")

def ask_choice(question, options, default_index=0):
    """Запрашивает выбор из нескольких вариантов с подсветкой рекомендации"""
    print(f"\n{question}")
    for i, option in enumerate(options):
        prefix = "→ " if i == default_index else "  "
        print(f"  {prefix}[{i+1}] {option}")
    
    while True:
        response = input(f"\nВаш выбор [1-{len(options)}] (по умолчанию {default_index+1}): ").strip()
        
        if not response:
            return default_index
        
        try:
            choice_idx = int(response) - 1
            if 0 <= choice_idx < len(options):
                return choice_idx
            else:
                print(f"Пожалуйста, введите число от 1 до {len(options)}")
        except ValueError:
            print("Пожалуйста, введите число")

# --- Основные функции-шаги ---
def step_1_check_environment():
    """Шаг 1: Проверка Python и текущей директории"""
    print_step(1, "Проверка окружения")
    
    # Проверка версии Python
    print(f"Текущая версия Python: {sys.version}")
    if sys.version_info < (3, 10):
        print(f"⚠️  Внимание: Требуется Python {PYTHON_VERSION} или выше")
        if not ask_yes_no("Всё равно продолжить?", default="n"):
            print("Установите Python 3.10+ и запустите скрипт снова.")
            sys.exit(1)
    else:
        print("✓ Версия Python подходит")
    
    # Проверка текущей директории
    current_dir = Path.cwd()
    print(f"Текущая директория: {current_dir}")
    
    if current_dir.name == PROJECT_NAME:
        print("✓ Вы уже в папке проекта")
    else:
        print(f"Вы НЕ в папке '{PROJECT_NAME}'")
        
        if ask_yes_no(f"Создать папку '{PROJECT_NAME}' в текущей директории?", default="y"):
            project_path = current_dir / PROJECT_NAME
            project_path.mkdir(exist_ok=True)
            os.chdir(project_path)
            print(f"✓ Создана и открыта папка: {project_path}")
        else:
            print("Пожалуйста, создайте папку вручную и запустите скрипт внутри неё.")
            sys.exit(1)
    
    return ask_yes_no("\nПерейти к следующему шагу?", default="y")

def step_2_create_structure():
    """Шаг 2: Создание структуры каталогов"""
    print_step(2, "Создание структуры проекта")
    
    structure = {
        "src/fractal": "Исходный код фрактального модуля",
        "tests": "Модульные тесты",
        "data/output": "Графики и результаты симуляций",
        "docs": "Документация (опционально)",
    }
    
    print("Будет создана следующая структура:")
    for path, desc in structure.items():
        print(f"  {path}/ - {desc}")
    
    # Вариант с опциональной папкой docs
    if not ask_yes_no("\nСоздавать папку docs для документации?", default="n"):
        del structure["docs"]
        print("Папка docs не будет создана")
    
    if not ask_yes_no("\nСоздать структуру каталогов?", default="y"):
        return False
    
    # Создание каталогов
    for path in structure:
        Path(path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Создана папка: {path}")
    
    # Создание пустых __init__.py
    init_files = ["src/__init__.py", "src/fractal/__init__.py", "tests/__init__.py"]
    for init_file in init_files:
        if Path(init_file).parent.exists():
            Path(init_file).touch(exist_ok=True)
            print(f"✓ Создан файл: {init_file}")
    
    return ask_yes_no("\nПерейти к следующему шагу?", default="y")

def step_3_create_requirements():
    """Шаг 3: Создание файла зависимостей"""
    print_step(3, "Создание requirements.txt")
    
    requirements_content = """# Основные зависимости
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
networkx>=3.0

# Инструменты разработки (опционально)
pytest>=7.3.0
pytest-cov>=4.1.0
flake8>=6.0.0
black>=23.3.0  # Автоформатирование кода
"""
    
    print("Содержимое requirements.txt:")
    print("-" * 40)
    print(requirements_content)
    print("-" * 40)
    
    # Проверка существующего файла
    req_file = Path("requirements.txt")
    if req_file.exists():
        print("⚠️  Файл requirements.txt уже существует!")
        
        options = [
            "Перезаписать существующий файл",
            "Добавить зависимости к существующему",
            "Пропустить этот шаг (оставить как есть)"
        ]
        choice = ask_choice("Как поступить с существующим файлом?", options, default_index=2)
        
        if choice == 0:  # Перезаписать
            with open(req_file, 'w') as f:
                f.write(requirements_content)
            print("✓ Файл перезаписан")
        elif choice == 1:  # Добавить
            with open(req_file, 'a') as f:
                f.write("\n# Дополнительные зависимости для фрактального модуля\n")
                f.write(requirements_content)
            print("✓ Зависимости добавлены в конец файла")
        else:  # Пропустить
            print("Файл оставлен без изменений")
    else:
        # Создание нового файла
        if ask_yes_no("Создать requirements.txt с этими зависимостями?", default="y"):
            with open(req_file, 'w') as f:
                f.write(requirements_content)
            print("✓ Файл requirements.txt создан")
    
    return ask_yes_no("\nПерейти к следующему шагу?", default="y")

def step_4_setup_venv():
    """Шаг 4: Настройка виртуального окружения"""
    print_step(4, "Настройка виртуального окружения")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("⚠️  Виртуальное окружение 'venv' уже существует!")
        
        options = [
            "Удалить и создать заново",
            "Использовать существующее",
            "Пропустить настройку venv"
        ]
        choice = ask_choice("Как поступить с виртуальным окружением?", options, default_index=1)
        
        if choice == 0:  # Пересоздать
            print("Удаляем старое окружение...")
            shutil.rmtree(venv_path)
            print("✓ Старое окружение удалено")
            create_new = True
        elif choice == 1:  # Использовать
            print("Будет использовано существующее окружение")
            create_new = False
        else:  # Пропустить
            print("Настройка venv пропущена")
            return ask_yes_no("\nПерейти к следующему шагу?", default="y")
    else:
        create_new = True
    
    if create_new:
        if ask_yes_no("Создать новое виртуальное окружение 'venv'?", default="y"):
            print("Создаю виртуальное окружение...")
            result = subprocess.run([sys.executable, "-m", "venv", "venv"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Виртуальное окружение создано")
                
                # Активация и установка pip
                print("Обновляю pip...")
                pip_cmd = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
                subprocess.run([pip_cmd, "install", "--upgrade", "pip"], 
                             capture_output=True)
                print("✓ Pip обновлён")
            else:
                print(f"✗ Ошибка при создании venv: {result.stderr}")
                if not ask_yes_no("Продолжить без виртуального окружения?", default="n"):
                    return False
    
    # Установка зависимостей
    if Path("requirements.txt").exists():
        if ask_yes_no("Установить зависимости из requirements.txt?", default="y"):
            print("Устанавливаю зависимости...")
            pip_cmd = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
            result = subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Все зависимости успешно установлены")
            else:
                print(f"⚠️  Были ошибки при установке: {result.stderr}")
                if not ask_yes_no("Продолжить несмотря на ошибки?", default="n"):
                    return False
    else:
        print("⚠️  Файл requirements.txt не найден, пропускаю установку зависимостей")
    
    return ask_yes_no("\nПерейти к следующему шагу?", default="y")

def step_5_create_configs():
    """Шаг 5: Создание конфигурационных файлов"""
    print_step(5, "Создание конфигурационных файлов")
    
    configs = {
        "pyproject.toml": """[project]
name = "fractal-adaptive-prototype"
version = "0.1.0"
description = "Прототип модуля фрактально-адаптивной динамики"
readme = "README.md"
requires-python = ">=3.10"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v"

[tool.flake8]
max-line-length = 120
exclude = [".git", "__pycache__", ".venv", "venv"]
""",
        ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
.venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
data/output/*
!data/output/.gitkeep
""",
        "README.md": """# Прототип фрактально-адаптивного модуля

Прототип модуля для проекта SpectraVortex, реализующий принципы фрактальной адаптивной динамики.

## Структура проекта

- `src/fractal/` — исходный код модуля
- `tests/` — модульные тесты
- `data/output/` — результаты симуляций и графики
- `docs/` — документация

## Быстрый старт

1. Установите зависимости: `pip install -r requirements.txt`
2. Запустите демо: `python demo_fractal_network.py`

## Основные компоненты

- `FractalUnit` — базовая единица системы
- `FractalNetwork` — сеть взаимодействующих единиц
- Адаптивные алгоритмы перераспределения нагрузки
"""
    }
    
    files_to_create = []
    for filename, content in configs.items():
        if Path(filename).exists():
            print(f"⚠️  Файл {filename} уже существует")
            if ask_yes_no(f"  Перезаписать {filename}?", default="n"):
                files_to_create.append((filename, content))
        else:
            files_to_create.append((filename, content))
    
    if files_to_create:
        print("\nБудут созданы/перезаписаны файлы:")
        for filename, _ in files_to_create:
            print(f"  • {filename}")
        
        if ask_yes_no("\nСоздать эти конфигурационные файлы?", default="y"):
            for filename, content in files_to_create:
                with open(filename, 'w') as f:
                    f.write(content)
                print(f"✓ Создан файл: {filename}")
    else:
        print("Все конфигурационные файлы уже существуют, пропускаю...")
    
    return ask_yes_no("\nПерейти к следующему шагу?", default="y")

def step_6_initial_commit():
    """Шаг 6: Инициализация git (опционально)"""
    print_step(6, "Настройка Git")
    
    if not ask_yes_no("Инициализировать Git репозиторий для прототипа?", default="n"):
        return True
    
    # Проверяем, есть ли git
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Git не установлен или не найден в PATH")
        if ask_yes_no("Пропустить настройку Git?", default="y"):
            return True
        else:
            return False
    
    # Инициализация
    if Path(".git").exists():
        print("✓ Репозиторий Git уже инициализирован")
    else:
        subprocess.run(["git", "init"], capture_output=True)
        print("✓ Репозиторий Git инициализирован")
    
    # Добавление .gitignore
    if Path(".gitignore").exists():
        subprocess.run(["git", "add", ".gitignore"])
        print("✓ .gitignore добавлен в индекс")
    
    # Первый коммит
    if ask_yes_no("Сделать первый коммит?", default="y"):
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Initial commit: fractal adaptive module prototype"])
        print("✓ Первый коммит создан")
    
    return True

def step_7_summary():
    """Финальный шаг: сводка"""
    print_step(7, "Сводка выполненных действий")
    
    print("✅ Проект успешно настроен!")
    print("\nСоздана структура для прототипа фрактально-адаптивного модуля.")
    
    # Показываем дерево проекта
    print("\nСтруктура проекта:")
    for root, dirs, files in os.walk("."):
        level = root.count(os.sep) - 1
        indent = "  " * level
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        if "venv" in root:
            continue
        print(f"{indent}📁 {os.path.basename(root) or '.'}/")
        subindent = "  " * (level + 1)
        for file in files[:5]:  # Показываем первые 5 файлов в каждой папке
            if not file.startswith(".") and file != "__pycache__":
                print(f"{subindent}📄 {file}")
        if len(files) > 5:
            print(f"{subindent}... и ещё {len(files) - 5} файлов")
    
    print("\n🎯 Следующие шаги:")
    print("  1. Активируйте виртуальное окружение:")
    print("     source venv/bin/activate  # Linux/Mac")
    print("     venv\\Scripts\\activate   # Windows")
    print("  2. Начните разработку в папке src/fractal/")
    print("  3. Запускайте тесты: pytest tests/")
    print("  4. Проверяйте стиль кода: flake8 src/")
    
    print("\n" + "="*60)
    print("Прототип готов к разработке! Удачи! 🚀")
    print("="*60)

# --- Главная функция ---
def main():
    """Основной цикл выполнения шагов"""
    print("="*60)
    print("МАСТЕР НАСТРОЙКИ ПРОТОТИПА ФРАКТАЛЬНО-АДАПТИВНОГО МОДУЛЯ")
    print("="*60)
    print("\nЭтот мастер поможет настроить среду разработки для прототипа.")
    print("На каждом шаге вы сможете подтвердить или отклонить действие.\n")
    
    # Последовательность шагов
    steps = [
        ("Проверка окружения", step_1_check_environment),
        ("Создание структуры каталогов", step_2_create_structure),
        ("Создание файла зависимостей", step_3_create_requirements),
        ("Настройка виртуального окружения", step_4_setup_venv),
        ("Создание конфигурационных файлов", step_5_create_configs),
        ("Настройка Git (опционально)", step_6_initial_commit),
    ]
    
    # Выполнение шагов
    for i, (step_name, step_func) in enumerate(steps, 1):
        if not step_func():
            print(f"\n⚠️  Шаг {i} ('{step_name}') был пропущен или отменён.")
            if not ask_yes_no("Продолжить выполнение следующих шагов?", default="y"):
                print("\nНастройка прервана пользователем.")
                return
    
    # Финальная сводка
    step_7_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Настройка прервана пользователем (Ctrl+C).")
        sys.exit(1)