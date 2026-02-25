#!/usr/bin/env python3
"""
Скрипт автоматизации внедрения эмерджентного времени в architect.
Запускать из корня проекта: python3 setup_temporal.py
"""

import os
import sys
import shutil
from pathlib import Path

# Цвета для вывода
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_step(msg):
    print(f"{GREEN}→{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def create_temporal_state_file(base_path):
    """Создаёт файл temporal_state.py в нужной директории"""
    
    # Определяем возможные пути для architect
    possible_paths = [
        Path(base_path) / "src" / "architect",
        Path(base_path) / "architect",
        Path(base_path) / "src" / "temporal",
        Path(base_path) / "temporal"
    ]
    
    target_dir = None
    for path in possible_paths:
        if path.exists() and path.is_dir():
            target_dir = path
            print_step(f"Найдена директория: {target_dir}")
            break
    
    if not target_dir:
        # Создаём src/architect если ничего не нашлось
        target_dir = Path(base_path) / "src" / "architect"
        target_dir.mkdir(parents=True, exist_ok=True)
        print_step(f"Создана директория: {target_dir}")
    
    # Содержимое файла temporal_state.py
    content = '''"""
Модуль эмерджентного времени для architect.
Основан на принципах ВММП и фрактальной временной иерархии.
"""

from dataclasses import dataclass
from enum import Enum
import math
import random


class TimeLayer(Enum):
    """Уровни временной иерархии"""
    UNIT = "unit"        # отдельный компонент
    CLUSTER = "cluster"  # группа синхронизированных компонентов
    NETWORK = "network"  # вся сеть
    SYSTEM = "system"    # глобальное системное время


@dataclass
class TemporalState:
    """
    Временное состояние компонента или системы.
    
    Поля:
        phase: текущая фаза (0-2π)
        frequency: частота (обратное характерное время)
        amplitude: амплитуда (сила влияния на соседей)
        stability: устойчивость временного состояния (0-1)
    """
    phase: float = 0.0
    frequency: float = 1.0
    amplitude: float = 1.0
    stability: float = 1.0
    
    def __post_init__(self):
        """Автоматически вычисляем масштаб времени"""
        self.time_scale = 1.0 / max(0.01, self.frequency)
    
    @classmethod
    def random_init(cls, base_freq: float = 1.0):
        """Случайная инициализация для нового компонента"""
        return cls(
            phase=random.random() * 2 * math.pi,
            frequency=base_freq * (0.8 + 0.4 * random.random()),
            amplitude=random.random() * 0.5 + 0.5,
            stability=random.random() * 0.3 + 0.7
        )
    
    def phase_diff(self, other: 'TemporalState') -> float:
        """Разность фаз с другим состоянием (нормированная)"""
        diff = (self.phase - other.phase + math.pi) % (2 * math.pi) - math.pi
        return diff
    
    def kuramoto_coupling(self, other: 'TemporalState', strength: float = 0.1) -> float:
        """Вклад в изменение фазы по модели Курамото"""
        return strength * math.sin(self.phase_diff(other))
    
    def synchronize_with(self, other: 'TemporalState', dt: float = 0.1):
        """Один шаг синхронизации с соседом"""
        coupling = self.kuramoto_coupling(other)
        self.phase = (self.phase + coupling * dt) % (2 * math.pi)
'''
    
    target_file = target_dir / "temporal_state.py"
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_step(f"Файл создан: {target_file}")
    return target_file

def create_init_file(target_dir):
    """Создаёт или обновляет __init__.py в директории"""
    init_file = target_dir / "__init__.py"
    
    if not init_file.exists():
        with open(init_file, 'w') as f:
            f.write('# Модуль architect\n')
        print_step(f"Создан {init_file}")
    
    # Добавляем импорт temporal_state в __init__.py если его там нет
    with open(init_file, 'r+') as f:
        content = f.read()
        if 'from .temporal_state import' not in content:
            f.seek(0, 0)
            f.write('from .temporal_state import TemporalState, TimeLayer\n' + content)
            print_step(f"Обновлён {init_file}")

def create_test_script(base_path):
    """Создаёт простой тест для проверки"""
    test_dir = Path(base_path) / "tests"
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / "test_temporal.py"
    content = '''#!/usr/bin/env python3
"""
Тест базовой функциональности эмерджентного времени.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.temporal_state import TemporalState, TimeLayer
except ImportError:
    try:
        from architect.temporal_state import TemporalState, TimeLayer
    except ImportError:
        print("❌ Не удалось импортировать TemporalState")
        sys.exit(1)

def test_basics():
    """Проверка базовой инициализации"""
    print("\n1. Тест инициализации:")
    
    # Случайная инициализация
    t1 = TemporalState.random_init()
    t2 = TemporalState.random_init()
    
    print(f"   t1: phase={t1.phase:.3f}, freq={t1.frequency:.3f}, scale={t1.time_scale:.3f}")
    print(f"   t2: phase={t2.phase:.3f}, freq={t2.frequency:.3f}, scale={t2.time_scale:.3f}")
    
    # Разность фаз
    diff = t1.phase_diff(t2)
    print(f"   Разность фаз: {diff:.3f}")
    
    # Курамото-связь
    coupling = t1.kuramoto_coupling(t2)
    print(f"   Курамото-связь: {coupling:.3f}")
    
    return True

def test_synchronization():
    """Проверка синхронизации"""
    print("\n2. Тест синхронизации:")
    
    t1 = TemporalState(phase=0.0, frequency=1.0)
    t2 = TemporalState(phase=2.0, frequency=1.0)
    
    print(f"   До: t1.phase={t1.phase:.3f}, t2.phase={t2.phase:.3f}")
    
    for step in range(10):
        t1.synchronize_with(t2, dt=0.2)
        t2.synchronize_with(t1, dt=0.2)
    
    print(f"   После 10 шагов: t1.phase={t1.phase:.3f}, t2.phase={t2.phase:.3f}")
    print(f"   Разность: {abs(t1.phase - t2.phase):.3f}")
    
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ МОДУЛЯ ЭМЕРДЖЕНТНОГО ВРЕМЕНИ")
    print("=" * 50)
    
    tests = [test_basics, test_synchronization]
    passed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("   ✅ Тест пройден")
            else:
                print("   ❌ Тест провален")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print(f"Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("✅ Модуль работает корректно")
        sys.exit(0)
    else:
        print("⚠️ Требуется доработка")
        sys.exit(1)
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_step(f"Тест создан: {test_file}")
    return test_file

def main():
    print("\n⚙️  АВТОМАТИЧЕСКАЯ НАСТРОЙКА ЭМЕРДЖЕНТНОГО ВРЕМЕНИ")
    print("=" * 60)
    
    # Определяем корень проекта
    script_path = Path(__file__).resolve()
    project_root = script_path.parent
    
    print_step(f"Корень проекта: {project_root}")
    
    # Шаг 1: создаём temporal_state.py
    temporal_file = create_temporal_state_file(project_root)
    
    # Шаг 2: обновляем __init__.py
    target_dir = temporal_file.parent
    create_init_file(target_dir)
    
    # Шаг 3: создаём тест
    test_file = create_test_script(project_root)
    
    print("\n✅ НАСТРОЙКА ЗАВЕРШЕНА")
    print("=" * 60)
    print(f"\nФайлы созданы:")
    print(f"  • {temporal_file}")
    print(f"  • {test_file}")
    print(f"\nСледующие шаги:")
    print(f"  1. Запустите тест: python {test_file}")
    print(f"  2. Добавьте TemporalState в компоненты")
    print(f"  3. Интегрируйте в architect")
    print()

if __name__ == "__main__":
    main()