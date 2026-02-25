#!/usr/bin/env python3
"""
Скрипт для добавления режима мухи (адаптивного ускорения времени).
"""

import re
from pathlib import Path

GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_step(msg):
    print(f"{GREEN}→{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def add_fly_mode_to_temporal_state(file_path):
    """Добавляет режим мухи в TemporalState"""
    
    print_step(f"Обновляем: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем метод fly_mode если его нет
    if 'def fly_mode' in content:
        print_info("Метод fly_mode уже есть")
    else:
        # Ищем место после других методов
        methods = re.finditer(r'^    def \w+', content, re.MULTILINE)
        last_method = None
        for m in methods:
            last_method = m
        
        if last_method:
            pos = last_method.start()
            
            fly_code = '''
    def fly_mode(self, factor: float = 2.0):
        """
        Активирует режим мухи — ускорение времени.
        
        Args:
            factor: коэффициент ускорения (1.0 = норма, >1.0 = быстрее)
        """
        self.frequency *= factor
        self.time_scale = 1.0 / max(0.01, self.frequency)
        # В режиме мухи амплитуда падает (энергия на ускорение)
        self.amplitude *= 0.9
        
    def turtle_mode(self, factor: float = 0.5):
        """
        Активирует режим черепахи — замедление времени.
        
        Args:
            factor: коэффициент замедления (<1.0 = медленнее)
        """
        self.frequency *= factor
        self.time_scale = 1.0 / max(0.01, self.frequency)
        # В режиме черепахи амплитуда растёт (накопление энергии)
        self.amplitude *= 1.1
        
    def emergency_level(self, threat: float) -> float:
        """
        Вычисляет уровень критичности на основе угрозы.
        
        Args:
            threat: уровень угрозы (0-1)
            
        Returns:
            float: коэффициент ускорения (1.0 + threat * 4)
        """
        # При угрозе 1.0 ускоряемся в 5 раз
        return 1.0 + threat * 4.0
'''
            content = content[:pos] + fly_code + content[pos:]
            print_info("Добавлены методы fly_mode, turtle_mode, emergency_level")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_step(f"✅ {file_path.name} обновлён")

def add_fly_mode_to_component(file_path):
    """Добавляет поддержку режима мухи в Component"""
    
    print_step(f"Обновляем: {file_path.name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем поле emergency если его нет
    if 'self.emergency' in content:
        print_info("Поле emergency уже есть")
    else:
        # Добавляем в __post_init__
        post_init_match = re.search(r'def __post_init__\(self\):', content)
        if post_init_match:
            # Находим конец метода
            lines = content.split('\n')
            post_init_end = None
            for i, line in enumerate(lines):
                if line.strip().startswith('def ') and i > 0:
                    post_init_end = i
                    break
            
            if post_init_end:
                # Вставляем инициализацию emergency
                indent = '        '
                lines.insert(post_init_end - 1, f'{indent}self.emergency = 0.0')
                content = '\n'.join(lines)
                print_info("Добавлена инициализация emergency")
    
    # Добавляем метод check_fly_mode если его нет
    if 'def check_fly_mode' in content:
        print_info("Метод check_fly_mode уже есть")
    else:
        # Вставляем перед __post_init__ или после него
        check_code = '''
    def check_fly_mode(self, threat_level: float = None):
        """
        Проверяет, нужно ли включить режим мухи.
        
        Args:
            threat_level: внешний уровень угрозы (если None, вычисляется из нагрузки)
        """
        if threat_level is None:
            # Вычисляем угрозу из состояния компонента
            threat = (1.0 - self.health) * 0.7 + self.load * 0.3
        else:
            threat = threat_level
        
        # Получаем коэффициент ускорения
        if hasattr(self.temporal, 'emergency_level'):
            factor = self.temporal.emergency_level(threat)
        else:
            factor = 1.0 + threat * 4.0
        
        # Применяем режим
        if factor > 1.5:
            self.temporal.fly_mode(factor)
            self.emergency = factor
            return True
        elif factor < 0.8:
            self.temporal.turtle_mode(factor)
            self.emergency = -factor
            return False
        else:
            # Нормальный режим
            if hasattr(self, 'emergency'):
                self.emergency = 0.0
            return False
'''
        # Ищем место после __post_init__
        post_init_end = re.search(r'def __post_init__\(self\):.*?\n\s*\n', content, re.DOTALL)
        if post_init_end:
            pos = post_init_end.end()
            content = content[:pos] + check_code + content[pos:]
            print_info("Добавлен метод check_fly_mode")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_step(f"✅ {file_path.name} обновлён")

def create_fly_mode_test(project_root):
    """Создаёт тест для режима мухи"""
    
    test_file = project_root / "tests" / "test_fly_mode.py"
    
    content = '''#!/usr/bin/env python3
"""
Тест режима мухи (адаптивного ускорения времени).
"""

import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.temporal_state import TemporalState
    print("✅ Импорт компонентов")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_fly_mode_acceleration():
    """Проверка ускорения времени в режиме мухи"""
    print("\n1. Тест ускорения:")
    
    comp = Component(id=0, charge=1.0, health=0.3, load=0.9)
    original_freq = comp.temporal.frequency
    
    print(f"   До: freq={original_freq:.3f}")
    
    # Включаем режим мухи
    comp.check_fly_mode(threat_level=0.8)
    
    print(f"   После: freq={comp.temporal.frequency:.3f}")
    print(f"   Ускорение: {comp.temporal.frequency/original_freq:.2f}x")
    
    assert comp.temporal.frequency > original_freq, "Частота должна вырасти"
    return True

def test_turtle_mode_deceleration():
    """Проверка замедления в режиме черепахи"""
    print("\n2. Тест замедления:")
    
    comp = Component(id=0, charge=1.0, health=0.9, load=0.1)
    original_freq = comp.temporal.frequency
    
    print(f"   До: freq={original_freq:.3f}")
    
    # Включаем режим черепахи
    comp.check_fly_mode(threat_level=0.1)
    
    print(f"   После: freq={comp.temporal.frequency:.3f}")
    print(f"   Замедление: {comp.temporal.frequency/original_freq:.2f}x")
    
    assert comp.temporal.frequency < original_freq, "Частота должна упасть"
    return True

def test_emergency_threshold():
    """Проверка порогов срабатывания"""
    print("\n3. Тест порогов:")
    
    comp = Component(id=0, charge=1.0)
    
    # Низкая угроза
    comp.check_fly_mode(threat_level=0.2)
    emergency = getattr(comp, 'emergency', 0.0)
    print(f"   Угроза 0.2 → emergency={emergency:.2f}")
    
    # Средняя угроза
    comp.check_fly_mode(threat_level=0.5)
    emergency = getattr(comp, 'emergency', 0.0)
    print(f"   Угроза 0.5 → emergency={emergency:.2f}")
    
    # Высокая угроза
    comp.check_fly_mode(threat_level=0.9)
    emergency = getattr(comp, 'emergency', 0.0)
    print(f"   Угроза 0.9 → emergency={emergency:.2f}")
    
    return True

if __name__ == "__main__":
    print("🧪 ТЕСТ РЕЖИМА МУХИ")
    print("=" * 50)
    
    tests = [test_fly_mode_acceleration, test_turtle_mode_deceleration, test_emergency_threshold]
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
        print("✅ Режим мухи работает корректно")
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
    print("\n⚙️  ДОБАВЛЕНИЕ РЕЖИМА МУХИ")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    
    # Обновляем temporal_state.py
    temporal_file = project_root / "src" / "architect" / "temporal_state.py"
    if temporal_file.exists():
        add_fly_mode_to_temporal_state(temporal_file)
    else:
        print_warning(f"Файл не найден: {temporal_file}")
    
    # Обновляем component.py
    component_file = project_root / "src" / "architect" / "component.py"
    if component_file.exists():
        add_fly_mode_to_component(component_file)
    else:
        print_warning(f"Файл не найден: {component_file}")
    
    # Создаём тест
    create_fly_mode_test(project_root)
    
    print("\n✅ ЭТАП 1.4 ЗАВЕРШЁН")
    print("=" * 60)
    print("\nЗапусти тест:")
    print("  python tests/test_fly_mode.py")
    print()

if __name__ == "__main__":
    main()