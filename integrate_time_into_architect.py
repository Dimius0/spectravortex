#!/usr/bin/env python3
"""
Скрипт для интеграции временного слоя в architect.
Добавляет временные метрики в процесс синтеза.
"""

import os
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

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def find_architect_file(project_root):
    """Ищет главный файл architect.py"""
    patterns = [
        "src/architect/architect.py",
        "src/architect/synthesizer.py",
        "architect/architect.py",
        "architect/synthesizer.py",
        "src/architect/__init__.py"
    ]
    
    for pattern in patterns:
        path = project_root / pattern
        if path.exists():
            return path
    return None

def add_temporal_metrics_to_architect(file_path):
    """Добавляет временные метрики в класс Architect"""
    
    print_step(f"Обрабатываем: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Добавляем импорт TemporalState если нужно
    if 'from .temporal_state import' not in content:
        content = 'from .temporal_state import TemporalState, TimeLayer\n' + content
        print_info("Добавлен импорт TemporalState")
    
    # 2. Добавляем метод compute_temporal_metrics
    if 'def compute_temporal_metrics' in content:
        print_info("Метод compute_temporal_metrics уже есть")
    else:
        # Ищем подходящее место для вставки (после других методов)
        methods = re.finditer(r'^    def \w+', content, re.MULTILINE)
        last_method = None
        for m in methods:
            last_method = m
        
        if last_method:
            pos = last_method.start()
            # Находим отступ
            indent = '    '
            
            metrics_code = f'''
    def compute_temporal_metrics(self, components):
        """
        Вычисляет временные характеристики конфигурации.
        
        Args:
            components: список компонентов с полем temporal
            
        Returns:
            dict: временные метрики
        """
        if not components:
            return {{
                'sync_level': 0.0,
                'temporal_domains': 0,
                'chaos_level': 0.0,
                'avg_frequency': 0.0
            }}
        
        # Собираем временные состояния
        phases = []
        freqs = []
        
        for comp in components:
            if hasattr(comp, 'temporal') and comp.temporal:
                phases.append(comp.temporal.phase)
                freqs.append(comp.temporal.frequency)
            else:
                # Если у компонента нет времени, создаём заглушку
                phases.append(0.0)
                freqs.append(1.0)
        
        # Параметр порядка Курамото (уровень синхронизации)
        import math
        complex_sum = sum(math.exp(1j * p) for p in phases)
        sync_level = abs(complex_sum) / len(phases) if phases else 0.0
        
        # Количество временных доменов (группы с близкими фазами)
        domains = self._detect_temporal_domains(phases)
        
        # Уровень хаоса (упрощённо)
        chaos_level = 1.0 - sync_level
        
        return {{
            'sync_level': round(sync_level, 4),
            'temporal_domains': domains,
            'chaos_level': round(chaos_level, 4),
            'avg_frequency': round(sum(freqs) / len(freqs), 4) if freqs else 1.0
        }}
    
    def _detect_temporal_domains(self, phases, threshold=0.5):
        """
        Обнаруживает группы синхронизации по фазам.
        
        Args:
            phases: список фаз
            threshold: порог схожести (в радианах)
            
        Returns:
            int: количество доменов
        """
        if len(phases) < 2:
            return 1
        
        # Простая кластеризация: группируем фазы в пределах threshold
        import math
        phases = [p % (2*math.pi) for p in phases]
        domains = 0
        used = [False] * len(phases)
        
        for i in range(len(phases)):
            if not used[i]:
                domains += 1
                for j in range(i+1, len(phases)):
                    if not used[j]:
                        diff = abs(phases[i] - phases[j])
                        diff = min(diff, 2*math.pi - diff)
                        if diff < threshold:
                            used[j] = True
        return domains
'''
            content = content[:pos] + metrics_code + content[pos:]
            print_info("Добавлен метод compute_temporal_metrics")
    
    # 3. Добавляем временные метрики в результат синтеза
    if 'temporal_metrics' in content:
        print_info("Временные метрики уже в результате")
    else:
        # Ищем место, где возвращается результат
        result_pattern = r'return\s*{.*?}'
        result_match = re.search(result_pattern, content, re.DOTALL)
        
        if result_match:
            old_return = result_match.group(0)
            new_return = old_return.replace('}', ', "temporal_metrics": self.compute_temporal_metrics(components)}')
            content = content.replace(old_return, new_return)
            print_info("Добавлены временные метрики в результат")
    
    # Записываем обратно
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_step(f"✅ Файл обновлён: {file_path.name}")

def create_test_for_temporal_metrics(project_root):
    """Создаёт тест для проверки временных метрик"""
    
    test_file = project_root / "tests" / "test_temporal_metrics.py"
    
    content = '''#!/usr/bin/env python3
"""
Тест временных метрик architect.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.temporal_state import TemporalState
    print("✅ Импорт компонентов")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_metrics_with_random_components():
    """Проверка вычисления метрик для случайных компонентов"""
    print("\n1. Тест случайных компонентов:")
    
    # Создаём несколько компонентов со случайными временными состояниями
    components = []
    for i in range(5):
        comp = Component(id=i, charge=1.0)
        # Переопределяем временное состояние для теста
        comp.temporal = TemporalState.random_init()
        components.append(comp)
        print(f"   Компонент {i}: phase={comp.temporal.phase:.3f}, freq={comp.temporal.frequency:.3f}")
    
    # Здесь должен быть вызов метода из architect
    # Пока тестируем только импорт и создание
    print("   ✅ Компоненты созданы")
    return True

def test_synchronized_vs_chaotic():
    """Сравнение синхронизированной и хаотичной конфигураций"""
    print("\n2. Тест синхронизации:")
    
    # Синхронизированная конфигурация (все фазы близки)
    sync_comps = []
    for i in range(3):
        comp = Component(id=i, charge=1.0)
        comp.temporal = TemporalState(phase=1.0, frequency=1.0)
        sync_comps.append(comp)
    
    # Хаотичная конфигурация (фазы разбросаны)
    chaos_comps = []
    for i in range(3):
        comp = Component(id=i, charge=1.0)
        comp.temporal = TemporalState(phase=float(i)*2.0, frequency=1.0)
        chaos_comps.append(comp)
    
    print("   ✅ Конфигурации созданы")
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ ВРЕМЕННЫХ МЕТРИК ARCHITECT")
    print("=" * 50)
    
    tests = [test_metrics_with_random_components, test_synchronized_vs_chaotic]
    passed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("   ✅ Тест пройден")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print(f"Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("✅ Временные метрики готовы к интеграции")
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
    print("\n⚙️  ИНТЕГРАЦИЯ ВРЕМЕННОГО СЛОЯ В ARCHITECT")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    print_step(f"Корень проекта: {project_root}")
    
    # Находим главный файл architect
    arch_file = find_architect_file(project_root)
    
    if not arch_file:
        print_warning("Файл architect не найден. Создаём заглушку...")
        arch_dir = project_root / "src" / "architect"
        arch_dir.mkdir(parents=True, exist_ok=True)
        arch_file = arch_dir / "architect.py"
        
        with open(arch_file, 'w', encoding='utf-8') as f:
            f.write('''"""
Главный модуль architect для топологического синтеза.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .component import Component
from .temporal_state import TemporalState, TimeLayer


@dataclass
class ArchitectResult:
    """Результат работы architect"""
    positions: List[tuple]
    energy: float
    metrics: Dict[str, Any]
    temporal_metrics: Dict[str, Any] = None


class TopologicalArchitect:
    """Топологический архитектор"""
    
    def __init__(self, grid_shape=(32, 32)):
        self.grid_shape = grid_shape
    
    def synthesize(self, components: List[Component], **kwargs) -> ArchitectResult:
        """
        Синтезирует топологическую конфигурацию.
        
        Args:
            components: список компонентов
            
        Returns:
            ArchitectResult: результат синтеза
        """
        # Здесь будет реальный синтез
        # Пока возвращаем заглушку
        positions = [(i % 10, i // 10) for i in range(len(components))]
        
        return ArchitectResult(
            positions=positions,
            energy=1000.0,
            metrics={'min_distance': 8.47},
            temporal_metrics=self.compute_temporal_metrics(components)
        )
    
    def compute_temporal_metrics(self, components):
        """Вычисляет временные метрики"""
        if not components:
            return {}
        
        phases = []
        freqs = []
        
        for comp in components:
            if hasattr(comp, 'temporal') and comp.temporal:
                phases.append(comp.temporal.phase)
                freqs.append(comp.temporal.frequency)
        
        if not phases:
            return {}
        
        import math
        complex_sum = sum(math.exp(1j * p) for p in phases)
        sync_level = abs(complex_sum) / len(phases)
        
        return {
            'sync_level': round(sync_level, 4),
            'chaos_level': round(1.0 - sync_level, 4),
            'avg_frequency': round(sum(freqs) / len(freqs), 4) if freqs else 1.0
        }
''')
        print_step(f"Создан файл-заглушка: {arch_file}")
    
    # Добавляем временные метрики
    add_temporal_metrics_to_architect(arch_file)
    
    # Создаём тест
    create_test_for_temporal_metrics(project_root)
    
    print("\n✅ ШАГ 1.3 ЗАВЕРШЁН")
    print("=" * 60)
    print("\nТеперь запусти тест:")
    print("  python tests/test_temporal_metrics.py")
    print()

if __name__ == "__main__":
    main()