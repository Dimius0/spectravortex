#!/usr/bin/env python3
"""
Скрипт для добавления TemporalState в компоненты architect.
Запускать из корня проекта: python3 add_temporal_to_components.py
"""

import os
import sys
import re
from pathlib import Path

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_step(msg):
    print(f"{GREEN}→{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def find_component_files(base_path):
    """Ищет все файлы, где может быть определён класс Component"""
    patterns = [
        "**/component.py",
        "**/components.py",
        "**/base.py",
        "**/library.py",
        "**/architect.py",
        "**/models.py"
    ]
    
    candidates = []
    base = Path(base_path)
    
    for pattern in patterns:
        for file in base.glob(pattern):
            if file.is_file():
                # Проверяем, есть ли внутри class Component
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if re.search(r'class\s+Component\b', content):
                        candidates.append(file)
                        print_step(f"Найден файл с Component: {file.relative_to(base)}")
    
    return candidates

def find_architect_init(base_path):
    """Находит __init__.py в папке architect"""
    base = Path(base_path)
    possible = [
        base / "src" / "architect" / "__init__.py",
        base / "architect" / "__init__.py"
    ]
    for p in possible:
        if p.exists():
            return p
    return None

def add_temporal_to_component(file_path):
    """Добавляет TemporalState в класс Component в указанном файле"""
    
    print_step(f"Обрабатываем: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Проверяем, есть ли уже импорт TemporalState
    if 'from .temporal_state import TemporalState' in content:
        print_info("   Импорт TemporalState уже есть")
    else:
        # Добавляем импорт после других импортов
        import_section = re.search(r'^(import .+$|from .+ import .+$)', content, re.MULTILINE)
        if import_section:
            # Вставляем после последнего импорта
            last_import = list(re.finditer(r'^(import .+$|from .+ import .+$)', content, re.MULTILINE))[-1]
            pos = last_import.end()
            content = content[:pos] + '\nfrom .temporal_state import TemporalState' + content[pos:]
            print_info("   Добавлен импорт TemporalState")
    
    # 2. Проверяем, есть ли поле temporal в классе Component
    if 'temporal:' in content or 'temporal =' in content:
        print_info("   Поле temporal уже есть")
    else:
        # Находим класс Component
        class_match = re.search(r'class\s+Component\b[^:]*:', content)
        if class_match:
            # Находим место после полей (обычно после __post_init__ или в конце класса)
            post_init_match = re.search(r'def\s+__post_init__\s*\(', content)
            
            if post_init_match:
                # Вставляем поле перед __post_init__
                insert_pos = post_init_match.start()
                field_line = '\n    temporal: TemporalState = None\n'
                content = content[:insert_pos] + field_line + content[insert_pos:]
                print_info("   Добавлено поле temporal перед __post_init__")
            else:
                # Вставляем в начало класса после объявления
                class_end_line = content.find(':', class_match.end())
                if class_end_line > 0:
                    insert_pos = class_end_line + 1
                    field_line = '\n    temporal: TemporalState = None'
                    content = content[:insert_pos] + field_line + content[insert_pos:]
                    print_info("   Добавлено поле temporal в начало класса")
    
    # 3. Добавляем инициализацию в __post_init__ если её нет
    if 'self.temporal is None' in content:
        print_info("   Инициализация temporal уже есть")
    else:
        # Ищем __post_init__
        post_init_match = re.search(r'def\s+__post_init__\s*\([^)]*\)\s*:', content)
        if post_init_match:
            # Находим тело метода
            method_start = post_init_match.end()
            # Находим отступ (пробелы или табуляция)
            indent_match = re.search(r'\n(\s+)', content[method_start:])
            if indent_match:
                indent = indent_match.group(1)
                
                # Код инициализации
                init_code = f'''
        # Инициализация временного состояния
        if self.temporal is None:
            # частота зависит от заряда (чем больше заряд, тем медленнее время)
            base_freq = 1.0 / (abs(self.charge) + 0.1) if hasattr(self, 'charge') else 1.0
            self.temporal = TemporalState.random_init(base_freq)
'''
                # Вставляем в начало тела метода
                insert_pos = method_start + len(indent)
                content = content[:insert_pos] + init_code + content[insert_pos:]
                print_info("   Добавлена инициализация temporal в __post_init__")
    
    # Записываем обратно
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_step(f"✅ Файл обновлён: {file_path.name}")
    return True

def update_architect_init(init_file):
    """Обновляет __init__.py в architect, если нужно"""
    
    if not init_file or not init_file.exists():
        print_warning("   __init__.py не найден, пропускаем")
        return
    
    print_step(f"Обновляем: {init_file.name}")
    
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли уже экспорт TemporalState
    if 'TemporalState' in content:
        print_info("   TemporalState уже экспортируется")
    else:
        # Добавляем в экспорт
        if 'from .temporal_state import' in content:
            # Уже есть, но возможно не все классы
            pass
        else:
            # Добавляем импорт
            content = 'from .temporal_state import TemporalState, TimeLayer\n' + content
            print_info("   Добавлен экспорт TemporalState")
        
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print_step(f"✅ {init_file.name} обновлён")

def main():
    print("\n⚙️  ДОБАВЛЕНИЕ TEMPORALSTATE В КОМПОНЕНТЫ")
    print("=" * 60)
    
    # Корень проекта
    script_path = Path(__file__).resolve()
    project_root = script_path.parent
    print_step(f"Корень проекта: {project_root}")
    
    # Ищем файлы с Component
    component_files = find_component_files(project_root)
    
    if not component_files:
        print_error("Не найдены файлы с классом Component!")
        print_info("Поищем вручную...")
        
        # Расширенный поиск
        all_py = list(project_root.glob("**/*.py"))
        for py_file in all_py:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'class Component' in content:
                        component_files.append(py_file)
                        print_step(f"Найден: {py_file.relative_to(project_root)}")
            except:
                continue
    
    if not component_files:
        print_error("Класс Component не найден. Нужно добавить вручную.")
        print_info("Создаём файл-заглушку для компонентов...")
        
        # Создаём базовый файл компонентов
        comp_dir = project_root / "src" / "architect"
        comp_dir.mkdir(parents=True, exist_ok=True)
        comp_file = comp_dir / "component.py"
        
        with open(comp_file, 'w', encoding='utf-8') as f:
            f.write('''"""
Базовый класс компонента для architect.
"""

from dataclasses import dataclass
from .temporal_state import TemporalState

@dataclass
class Component:
    """Базовый компонент системы"""
    id: int
    charge: float = 1.0
    health: float = 1.0
    load: float = 0.3
    temporal: TemporalState = None
    
    def __post_init__(self):
        if self.temporal is None:
            base_freq = 1.0 / (abs(self.charge) + 0.1)
            self.temporal = TemporalState.random_init(base_freq)
''')
        component_files = [comp_file]
        print_step(f"Создан файл компонентов: {comp_file.relative_to(project_root)}")
    
    # Обрабатываем каждый файл
    for comp_file in component_files:
        add_temporal_to_component(comp_file)
    
    # Обновляем __init__.py в architect
    init_file = find_architect_init(project_root)
    update_architect_init(init_file)
    
    print("\n✅ ШАГ 1.2 ЗАВЕРШЁН")
    print("=" * 60)
    print(f"\nОбработано файлов: {len(component_files)}")
    print("\nСледующие шаги:")
    print("  1. Проверьте изменения в файлах")
    print("  2. Запустите тесты: python tests/test_temporal.py")
    print("  3. Если тесты проходят — идём дальше")
    print()

if __name__ == "__main__":
    main()