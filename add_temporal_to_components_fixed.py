#!/usr/bin/env python3
"""
Исправленная версия скрипта для добавления TemporalState в компоненты.
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

def main():
    print("\n⚙️  СОЗДАНИЕ БАЗОВОГО КОМПОНЕНТА С TEMPORALSTATE")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    print_step(f"Корень проекта: {project_root}")
    
    # Создаём папку src/architect если её нет
    arch_dir = project_root / "src" / "architect"
    arch_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаём файл компонента
    comp_file = arch_dir / "component.py"
    
    if not comp_file.exists():
        print_step("Создаём базовый файл компонентов...")
        with open(comp_file, 'w', encoding='utf-8') as f:
            f.write('''"""
Базовый класс компонента для architect.
"""

from dataclasses import dataclass
import math
import random
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
        """Инициализация после создания"""
        if self.temporal is None:
            # частота зависит от заряда (чем больше заряд, тем медленнее время)
            base_freq = 1.0 / (abs(self.charge) + 0.1)
            self.temporal = TemporalState.random_init(base_freq)
''')
        print_step(f"✅ Создан: {comp_file}")
    else:
        print_step(f"Файл компонентов уже существует: {comp_file}")
    
    # Создаём __init__.py
    init_file = arch_dir / "__init__.py"
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write('from .temporal_state import TemporalState, TimeLayer\n')
        f.write('from .component import Component\n')
    print_step(f"✅ Обновлён: {init_file}")
    
    # Обновляем тест, чтобы импортировал Component
    test_file = project_root / "tests" / "test_temporal.py"
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'from src.architect.component import Component' not in content:
            # Добавляем импорт компонента в тест
            content = content.replace(
                'from src.architect.temporal_state import TemporalState, TimeLayer',
                'from src.architect.temporal_state import TemporalState, TimeLayer\nfrom src.architect.component import Component'
            )
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print_step(f"✅ Обновлён тест: {test_file}")
    
    print("\n✅ ГОТОВО")
    print("=" * 60)
    print("\nТеперь запусти тест:")
    print("  python tests/test_temporal.py")
    print()

if __name__ == "__main__":
    main()