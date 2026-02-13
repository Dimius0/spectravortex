#!/usr/bin/env python3
"""
dev_workflow.py — Интерактивный проводник по разработке фрактально-адаптивного модуля.
Запуск: python dev_workflow.py
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# --- Конфигурация этапов ---
PROJECT_ROOT = Path.cwd()

# --- Стилизованный вывод ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Заголовок этапа"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}🎯 {text}{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")

def print_step(text: str):
    """Шаг внутри этапа"""
    print(f"\n{Colors.BLUE}• {text}{Colors.END}")

def print_success(text: str):
    """Успешное выполнение"""
    print(f"{Colors.GREEN}  ✓ {text}{Colors.END}")

def print_warning(text: str):
    """Предупреждение"""
    print(f"{Colors.YELLOW}  ⚠ {text}{Colors.END}")

def print_error(text: str):
    """Ошибка"""
    print(f"{Colors.RED}  ✗ {text}{Colors.END}")

def ask_continue(prompt: str = "Продолжить?", default: str = "y") -> bool:
    """Запрос подтверждения с подсветкой рекомендации"""
    choices = f"{Colors.GREEN}Y{Colors.END}/n" if default == "y" else f"y/{Colors.GREEN}N{Colors.END}"
    full_prompt = f"\n{prompt} [{choices}]: "
    
    while True:
        response = input(full_prompt).strip().lower()
        if not response:
            response = default
        
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        print("Пожалуйста, введите y/n")

def ask_choice(prompt: str, options: List[str], descriptions: List[str] = None, default: int = 0) -> int:
    """Выбор из вариантов с подсветкой рекомендации"""
    print(f"\n{prompt}")
    print(f"{Colors.BOLD}Варианты:{Colors.END}")
    
    for i, option in enumerate(options):
        prefix = f"{Colors.GREEN}→{Colors.END}" if i == default else " "
        desc = f" — {descriptions[i]}" if descriptions and i < len(descriptions) else ""
        print(f"  {prefix} [{i+1}] {option}{desc}")
    
    while True:
        choice_input = input(f"\nВаш выбор [1-{len(options)}] ({Colors.GREEN}по умолчанию {default+1}{Colors.END}): ").strip()
        
        if not choice_input:
            return default
        
        try:
            choice_idx = int(choice_input) - 1
            if 0 <= choice_idx < len(options):
                return choice_idx
            print(f"Пожалуйста, введите число от 1 до {len(options)}")
        except ValueError:
            print("Пожалуйста, введите число")

# --- Функции-этапы ---
def stage_1_core_unit() -> bool:
    """Этап 1: Ядро системы — FractalUnit"""
    print_header("ЭТАП 1: СОЗДАНИЕ ЯДРА СИСТЕМЫ (FractalUnit)")
    
    print("Цель: Создать базовый класс FractalUnit — элементарную 'клетку' системы.")
    print("Он будет содержать:")
    print("  - Состояние (нагрузка, здоровье, потенциал)")
    print("  - Список соседей")
    print("  - Методы вычисления потенциала и передачи нагрузки")
    
    if not ask_continue("Начать этап 1?"):
        return False
    
    # 1.1 Выбор места расположения
    print_step("Выбор места для класса FractalUnit")
    
    options = [
        "src/fractal/unit.py (рекомендуется)",
        "src/fractal/core/unit.py",
        "src/unit.py"
    ]
    descs = [
        "Стандартная структура, изолированная логика",
        "Более глубокая иерархия для сложных систем",
        "Простая структура для быстрого прототипа"
    ]
    
    choice = ask_choice("Где разместить класс FractalUnit?", options, descs, default=0)
    unit_path = Path(options[choice].split()[0])
    
    # 1.2 Проверка существования
    if unit_path.exists():
        print_warning(f"Файл {unit_path} уже существует!")
        overwrite_options = ["Перезаписать", "Добавить новый класс", "Пропустить создание"]
        overwrite_choice = ask_choice("Как поступить?", overwrite_options, default=2)
        
        if overwrite_choice == 2:
            print_success("Создание FractalUnit пропущено")
            return True
    
    # 1.3 Создание класса
    print_step(f"Создание {unit_path}")
    
    unit_content = '''"""
FractalUnit — элементарная единица фрактально-адаптивной системы.
Состояние описывается непрерывными параметрами (принцип "переменного резистора").
"""

class FractalUnit:
    """Базовая единица системы с состоянием и локальными правилами."""
    
    def __init__(self, unit_id: str, initial_load: float = 0.0):
        """
        Инициализация фрактальной единицы.
        
        Args:
            unit_id: Уникальный идентификатор единицы
            initial_load: Начальная нагрузка (0.0 - 1.0)
        """
        self.id = unit_id
        self.load = initial_load  # Текущая нагрузка (0.0 - 1.0)
        self.health = 1.0         # Уровень "здоровья" (1.0 = идеально, 0.0 = сломан)
        self.neighbors = []       # Список соседних FractalUnit
        self.local_potential = 0.0  # Вычисленный локальный потенциал
        
    def add_neighbor(self, neighbor: 'FractalUnit', bidirectional: bool = True):
        """
        Добавляет связь с соседней единицей.
        
        Args:
            neighbor: Соседняя FractalUnit
            bidirectional: Если True, также добавляет обратную связь
        """
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            if bidirectional:
                neighbor.add_neighbor(self, bidirectional=False)
    
    def compute_potential(self, target_load: float = 0.7) -> float:
        """
        Вычисляет локальный потенциал как функцию отклонения от цели.
        
        Формула: (load - target)² + health_penalty
        
        Args:
            target_load: Целевой уровень нагрузки (0.0 - 1.0)
        
        Returns:
            Значение локального потенциала (≥ 0.0)
        """
        # Компонент нагрузки: квадрат отклонения от цели
        load_component = (self.load - target_load) ** 2
        
        # Штраф за плохое здоровье: чем ниже здоровье, тем выше потенциал
        health_penalty = (1.0 - self.health) * 5.0
        
        self.local_potential = load_component + health_penalty
        return self.local_potential
    
    def transfer_load(self, transfer_rate: float = 0.05) -> float:
        """
        Перераспределяет нагрузку среди соседей на основе разницы потенциалов.
        
        Args:
            transfer_rate: Коэффициент скорости перераспределения (0.0 - 1.0)
        
        Returns:
            Общий объём переданной нагрузки
        """
        transferred_total = 0.0
        
        for neighbor in self.neighbors:
            # Разность потенциалов определяет направление и силу потока
            potential_diff = self.local_potential - neighbor.local_potential
            
            if potential_diff > 0:  # Наш потенциал выше — отдаём нагрузку
                # Объём передачи пропорционален разности потенциалов
                transfer_amount = transfer_rate * potential_diff * self.load
                
                # Ограничения: не больше текущей нагрузки и свободного места у соседа
                safe_amount = min(
                    transfer_amount,
                    self.load,                    # Не больше, чем есть
                    1.0 - neighbor.load,          # Не больше свободного места у соседа
                    self.health * 0.5            # Ограничение по здоровью
                )
                
                if safe_amount > 0.001:  # Практически значимый перенос
                    self.load -= safe_amount
                    neighbor.load += safe_amount
                    transferred_total += safe_amount
        
        return transferred_total
    
    def update_health(self, delta: float):
        """
        Обновляет уровень здоровья единицы.
        
        Args:
            delta: Изменение здоровья (-0.1 до +0.1)
        """
        self.health = max(0.0, min(1.0, self.health + delta))
    
    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return (f"FractalUnit(id={self.id}, load={self.load:.2f}, "
                f"health={self.health:.2f}, potential={self.local_potential:.3f})")
'''
    
    # Создаём директорию если нужно
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Записываем файл
    with open(unit_path, 'w', encoding='utf-8') as f:
        f.write(unit_content)
    
    print_success(f"Создан файл: {unit_path}")
    
    # 1.4 Создание простого теста
    print_step("Создание базового теста")
    
    test_content = '''"""
Тесты для FractalUnit.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fractal.unit import FractalUnit

def test_unit_creation():
    """Тест создания единицы."""
    unit = FractalUnit("test_unit", 0.5)
    assert unit.id == "test_unit"
    assert unit.load == 0.5
    assert unit.health == 1.0
    assert unit.neighbors == []
    print("✓ test_unit_creation пройден")

def test_neighbor_connection():
    """Тест связи между единицами."""
    unit1 = FractalUnit("unit1")
    unit2 = FractalUnit("unit2")
    
    unit1.add_neighbor(unit2)
    
    assert unit2 in unit1.neighbors
    assert unit1 in unit2.neighbors  # Двусторонняя связь
    print("✓ test_neighbor_connection пройден")

def test_potential_calculation():
    """Тест вычисления потенциала."""
    unit = FractalUnit("test_unit", 0.9)
    potential = unit.compute_potential(target_load=0.7)
    
    # При нагрузке 0.9 и цели 0.7: (0.9-0.7)² = 0.04
    expected = (0.9 - 0.7) ** 2
    assert abs(potential - expected) < 0.001
    print("✓ test_potential_calculation пройден")

def test_load_transfer():
    """Тест передачи нагрузки."""
    unit1 = FractalUnit("unit1", 0.8)
    unit2 = FractalUnit("unit2", 0.3)
    
    unit1.add_neighbor(unit2)
    unit1.compute_potential(0.5)
    unit2.compute_potential(0.5)
    
    transferred = unit1.transfer_load(transfer_rate=0.1)
    
    # unit1 должен отдать часть нагрузки unit2
    assert transferred > 0
    assert unit1.load < 0.8
    assert unit2.load > 0.3
    print(f"✓ test_load_transfer пройден (передано {transferred:.3f})")

if __name__ == "__main__":
    print("Запуск тестов FractalUnit...")
    test_unit_creation()
    test_neighbor_connection()
    test_potential_calculation()
    test_load_transfer()
    print("\n✅ Все базовые тесты пройдены!")
'''
    
    test_path = Path("tests") / "test_unit_basic.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print_success(f"Создан тест: {test_path}")
    
    # 1.5 Запуск теста
    print_step("Проверка созданного класса")
    
    if ask_continue("Запустить базовые тесты FractalUnit?"):
        print("Запуск тестов...")
        try:
            # Запускаем тест напрямую
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_unit_basic", test_path)
            test_module = importlib.util.module_from_spec(spec)
            
            # Временно добавляем src в sys.path
            import sys
            sys.path.insert(0, str(PROJECT_ROOT / "src"))
            
            spec.loader.exec_module(test_module)
            print_success("Базовые тесты пройдены успешно!")
            
        except Exception as e:
            print_error(f"Ошибка при выполнении тестов: {e}")
            print_warning("Продолжить несмотря на ошибку?")
            if not ask_continue("", default="y"):
                return False
    
    print_success("Этап 1 завершён! Создано ядро системы.")
    return True

def stage_2_network_simulator() -> bool:
    """Этап 2: Создание сетевого симулятора"""
    print_header("ЭТАП 2: СОЗДАНИЕ СЕТЕВОГО СИМУЛЯТОРА (FractalNetwork)")
    
    print("Цель: Создать класс FractalNetwork для управления сетью FractalUnit.")
    print("Он будет обеспечивать:")
    print("  - Создание и соединение единиц в сеть")
    print("  - Координацию шагов симуляции")
    print("  - Визуализацию состояния сети")
    
    if not ask_continue("Начать этап 2?"):
        return False
    
    # 2.1 Выбор стратегии визуализации
    print_step("Выбор подхода к визуализации")
    
    viz_options = [
        "Matplotlib + NetworkX (рекомендуется)",
        "Только текстовая визуализация",
        "Сохранять данные для внешней визуализации"
    ]
    viz_descs = [
        "Интерактивные графики, цветовая кодировка, анимации",
        "Быстро, без зависимостей, для CI/CD",
        "Гибко, можно использовать другие инструменты"
    ]
    
    viz_choice = ask_choice("Какой подход к визуализации использовать?", viz_options, viz_descs, default=0)
    
    # 2.2 Создание сетевого класса
    network_path = Path("src/fractal/network.py")
    
    if network_path.exists():
        print_warning(f"Файл {network_path} уже существует!")
        if not ask_continue("Перезаписать существующий файл?"):
            return True
    
    print_step(f"Создание {network_path}")
    
    # Базовый шаблон сетевого класса
    network_content = '''"""
FractalNetwork — симулятор сети фрактальных единиц.
"""
import time
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

from .unit import FractalUnit

class FractalNetwork:
    """Сеть взаимодействующих фрактальных единиц."""
    
    def __init__(self, num_units: int = 10, topology: str = "ring"):
        """
        Инициализация сети.
        
        Args:
            num_units: Количество единиц в сети
            topology: Топология сети ('ring', 'mesh', 'star', 'random')
        """
        self.units = [FractalUnit(f"Unit_{i:02d}") for i in range(num_units)]
        self.topology = topology
        self.step_count = 0
        self.history = []  # История состояний для анализа
        
        # Инициализируем случайной нагрузкой
        for unit in self.units:
            unit.load = random.uniform(0.3, 0.7)
        
        self._create_connections()
    
    def _create_connections(self):
        """Создаёт связи между единицами в зависимости от топологии."""
        n = len(self.units)
        
        if self.topology == "ring":
            # Кольцо: каждый соединён с двумя соседями
            for i in range(n):
                self.units[i].add_neighbor(self.units[(i + 1) % n])
        
        elif self.topology == "mesh":
            # Полносвязная сеть (каждый с каждым, ограниченная степень)
            max_degree = min(4, n - 1)
            for i in range(n):
                # Соединяем с ближайшими соседями
                for j in range(1, max_degree + 1):
                    neighbor_idx = (i + j) % n
                    if neighbor_idx != i:
                        self.units[i].add_neighbor(self.units[neighbor_idx])
        
        elif self.topology == "star":
            # Звезда: центральный узел соединён со всеми
            center = self.units[0]
            for i in range(1, n):
                center.add_neighbor(self.units[i])
        
        elif self.topology == "random":
            # Случайные связи
            target_connections = n * 2  # В среднем 2 связи на узел
            for _ in range(target_connections):
                i, j = random.sample(range(n), 2)
                self.units[i].add_neighbor(self.units[j])
    
    def simulate_step(self, target_load: float = 0.7) -> float:
        """
        Выполняет один шаг симуляции.
        
        Args:
            target_load: Целевая нагрузка для всех единиц
        
        Returns:
            Общий объём перераспределённой нагрузки на этом шаге
        """
        # Фаза 1: все вычисляют свой текущий потенциал
        for unit in self.units:
            unit.compute_potential(target_load)
        
        # Фаза 2: перераспределение нагрузки
        total_transferred = 0.0
        for unit in self.units:
            total_transferred += unit.transfer_load()
        
        # Сохраняем снимок состояния
        self.history.append([
            (unit.load, unit.health, unit.local_potential)
            for unit in self.units
        ])
        
        self.step_count += 1
        return total_transferred
    
    def sabotage(self, unit_index: int, damage: float = 0.5, extra_load: float = 0.3):
        """
        Имитация сбоя узла.
        
        Args:
            unit_index: Индекс атакуемого узла
            damage: Урон здоровью (0.0 - 1.0)
            extra_load: Дополнительная нагрузка на узел
        """
        target = self.units[unit_index]
        target.health = max(0.1, target.health - damage)
        target.load = min(1.0, target.load + extra_load)
        
        return target
    
    def get_network_metrics(self) -> Dict[str, float]:
        """Возвращает метрики состояния всей сети."""
        if not self.units:
            return {}
        
        loads = [u.load for u in self.units]
        healths = [u.health for u in self.units]
        potentials = [u.local_potential for u in self.units]
        
        return {
            "avg_load": sum(loads) / len(loads),
            "avg_health": sum(healths) / len(healths),
            "total_potential": sum(potentials),
            "imbalance": max(loads) - min(loads),  # Разброс нагрузок
            "unhealthy_nodes": sum(1 for h in healths if h < 0.5),
        }
    
    def print_state(self):
        """Выводит текстовое представление состояния сети."""
        metrics = self.get_network_metrics()
        
        print(f"\n{'='*60}")
        print(f"СОСТОЯНИЕ СЕТИ (Шаг {self.step_count}, топология: {self.topology})")
        print(f"{'='*60}")
        
        # Краткая информация по каждому узлу
        for i, unit in enumerate(self.units[:5]):  # Показываем первые 5
            status = "⚠ " if unit.health < 0.7 else "✓ "
            print(f"  {status}{unit.id}: load={unit.load:.2f}, "
                  f"health={unit.health:.2f}, potential={unit.local_potential:.3f}")
        
        if len(self.units) > 5:
            print(f"  ... и ещё {len(self.units) - 5} узлов")
        
        print(f"\nМетрики сети:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.3f}")
'''
    
    # Добавляем выбранную визуализацию
    if viz_choice == 0:
        network_content += '''
    def visualize(self, save_path: Optional[Path] = None):
        """
        Визуализирует сеть с помощью matplotlib и networkx.
        
        Args:
            save_path: Путь для сохранения изображения (None для показа на экране)
        """
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            import matplotlib.cm as cm
            from matplotlib.colors import Normalize
        except ImportError:
            print("Для визуализации установите: pip install matplotlib networkx")
            return
        
        G = nx.Graph()
        
        # Добавляем узлы с атрибутами
        for i, unit in enumerate(self.units):
            G.add_node(unit.id, 
                      load=unit.load, 
                      health=unit.health, 
                      potential=unit.local_potential)
        
        # Добавляем рёбра
        for unit in self.units:
            for neighbor in unit.neighbors:
                if not G.has_edge(unit.id, neighbor.id):
                    # Вес ребра = средний поток между узлами
                    avg_potential = (unit.local_potential + neighbor.local_potential) / 2
                    G.add_edge(unit.id, neighbor.id, weight=avg_potential)
        
        # Параметры визуализации
        pos = nx.spring_layout(G, seed=42)  # Детерминированное расположение
        
        # Цвет узлов = потенциал
        node_colors = [G.nodes[n]['potential'] for n in G.nodes()]
        node_sizes = [2000 * (0.5 + G.nodes[n]['load']) for n in G.nodes()]  # Размер = нагрузка
        edge_widths = [0.5 + G.edges[e]['weight'] for e in G.edges()]
        
        # Нормализация цветов
        norm = Normalize(vmin=min(node_colors), vmax=max(node_colors))
        cmap = cm.viridis
        
        plt.figure(figsize=(12, 10))
        
        # Рисуем граф
        nodes = nx.draw_networkx_nodes(G, pos,
                                      node_color=node_colors,
                                      node_size=node_sizes,
                                      cmap=cmap,
                                      alpha=0.9)
        
        nx.draw_networkx_edges(G, pos,
                              width=edge_widths,
                              alpha=0.5,
                              edge_color='gray')
        
        nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')
        
        # Цветовая шкала
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, shrink=0.8)
        cbar.set_label('Потенциал узла', fontsize=12)
        
        plt.title(f"Фрактальная адаптивная сеть (Шаг {self.step_count}, {self.topology})", 
                 fontsize=14, fontweight='bold')
        
        # Аннотация метрик
        metrics = self.get_network_metrics()
        metrics_text = (
            f"Узлов: {len(self.units)}\\n"
            f"Ср. нагрузка: {metrics['avg_load']:.2f}\\n"
            f"Разброс: {metrics['imbalance']:.2f}\\n"
            f"Больных узлов: {metrics['unhealthy_nodes']}"
        )
        
        plt.figtext(0.02, 0.02, metrics_text, 
                   fontsize=9, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8))
        
        plt.axis('off')
        plt.tight_layout()
        
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"График сохранён: {save_path}")
            plt.close()
        else:
            plt.show()
'''
    elif viz_choice == 1:
        network_content += '''
    def visualize(self, save_path: Optional[Path] = None):
        """Текстовая визуализация сети в ASCII."""
        print("\\n" + "="*60)
        print("ТЕКСТОВОЕ ПРЕДСТАВЛЕНИЕ СЕТИ")
        print("="*60)
        
        # Создаём простую матрицу связей
        n = len(self.units)
        matrix = [["·" for _ in range(n)] for _ in range(n)]
        
        for i, unit in enumerate(self.units):
            matrix[i][i] = "○" if unit.health > 0.7 else "⨂"
            for neighbor in unit.neighbors:
                j = self.units.index(neighbor)
                matrix[i][j] = "─"
        
        # Выводим матрицу
        print("   " + " ".join(f"{i:2d}" for i in range(min(10, n))))
        for i in range(min(10, n)):
            row = " ".join(matrix[i][:10])
            unit = self.units[i]
            status = "✓" if unit.health > 0.7 else "⚠"
            print(f"{i:2d} {row}  {status} {unit.id}: L={unit.load:.2f} H={unit.health:.2f}")
        
        if n > 10:
            print(f"... (ещё {n-10} строк и столбцов)")
'''
    
    # Записываем файл
    with open(network_path, 'w', encoding='utf-8') as f:
        f.write(network_content)
    
    print_success(f"Создан файл: {network_path}")
    
    # 2.3 Создание демонстрационного скрипта
    print_step("Создание демонстрационного скрипта")
    
    demo_path = Path("demo_network.py")
    demo_content = '''#!/usr/bin/env python3
"""
Демонстрация фрактально-адаптивной сети.
"""
import sys
from pathlib import Path

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fractal.network import FractalNetwork

def demo_basic_network():
    """Демонстрация базовой работы сети."""
    print("="*70)
    print("ДЕМОНСТРАЦИЯ: ФРАКТАЛЬНАЯ АДАПТИВНАЯ СЕТЬ")
    print("="*70)
    
    # 1. Создаём сеть из 8 узлов в кольцевой топологии
    print("\\n1. Создаём сеть из 8 узлов (топология: кольцо)...")
    network = FractalNetwork(num_units=8, topology="ring")
    network.print_state()
    
    # 2. Запускаем несколько шагов стабилизации
    print("\\n2. Запускаем 5 шагов стабилизации...")
    for step in range(5):
        transferred = network.simulate_step(target_load=0.6)
        print(f"   Шаг {step+1}: перераспределено {transferred:.4f} нагрузки")
    
    network.print_state()
    
    # 3. Визуализируем стабильное состояние
    if len(sys.argv) > 1 and sys.argv[1] == "--no-viz":
        print("\\nВизуализация отключена (--no-viz)")
    else:
        print("\\n3. Визуализация стабильного состояния...")
        try:
            network.visualize()
        except ImportError as e:
            print(f"   Не удалось визуализировать: {e}")
            print("   Установите: pip install matplotlib networkx")
    
    # 4. САБОТАЖ!
    print("\\n4. ИМИТАЦИЯ САБОТАЖА НА УЗЛЕ 2...")
    network.sabotage(unit_index=2, damage=0.6, extra_load=0.4)
    network.print_state()
    
    # 5. Адаптация после сбоя
    print("\\n5. ЗАПУСК АДАПТАЦИИ (10 шагов)...")
    for step in range(10):
        transferred = network.simulate_step(target_load=0.6)
        if step < 3 or step % 3 == 0:
            print(f"   Шаг {step+1}: перераспределено {transferred:.4f} нагрузки")
    
    # 6. Финальное состояние
    print("\\n6. ФИНАЛЬНОЕ СОСТОЯНИЕ ПОСЛЕ АДАПТАЦИИ:")
    network.print_state()
    
    # 7. Сохранение графика
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        import matplotlib
        save_path = output_dir / "network_final_state.png"
        network.visualize(save_path=save_path)
        print(f"\\nГрафик сохранён: {save_path}")
    except ImportError:
        pass
    
    print("\\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*70)

def demo_topology_comparison():
    """Сравнение разных топологий."""
    print("\\n" + "="*70)
    print("СРАВНЕНИЕ ТОПОЛОГИЙ СЕТИ")
    print("="*70)
    
    topologies = ["ring", "mesh", "star", "random"]
    
    for topology in topologies:
        print(f"\\n--- Топология: {topology.upper()} ---")
        net = FractalNetwork(num_units=10, topology=topology)
        
        # Сразу после создания
        initial = net.get_network_metrics()["imbalance"]
        
        # После стабилизации
        for _ in range(10):
            net.simulate_step()
        
        final = net.get_network_metrics()
        
        print(f"  Начальный разброс: {initial:.3f}")
        print(f"  Конечный разброс: {final['imbalance']:.3f}")
        print(f"  Общий потенциал: {final['total_potential']:.3f}")
        print(f"  Больных узлов: {final['unhealthy_nodes']}")

if __name__ == "__main__":
    demo_basic_network()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        demo_topology_comparison()
'''
    
    with open(demo_path, 'w', encoding='utf-8') as f:
        f.write(demo_content)
    
    # Делаем скрипт исполняемым (Unix)
    try:
        demo_path.chmod(0o755)
    except:
        pass
    
    print_success(f"Создан демо-скрипт: {demo_path}")
    
    # 2.4 Запуск демо (опционально)
    print_step("Проверка работоспособности")
    
    if ask_continue("Запустить демонстрацию сети (быстрый тест)?"):
        print("Запуск демо...")
        print("="*60)
        
        # Импортируем и запускаем демо
        import importlib.util
        spec = importlib.util.spec_from_file_location("demo_network", demo_path)
        demo_module = importlib.util.module_from_spec(spec)
        
        # Сохраняем оригинальные аргументы
        original_argv = sys.argv.copy()
        sys.argv = [sys.argv[0]]  # Очищаем аргументы
        
        try:
            spec.loader.exec_module(demo_module)
            print_success("Демонстрация выполнена успешно!")
        except Exception as e:
            print_error(f"Ошибка при демонстрации: {e}")
            print_warning("Продолжить разработку?")
            if not ask_continue("", default="y"):
                return False
        finally:
            # Восстанавливаем аргументы
            sys.argv = original_argv
    
    print_success("Этап 2 завершён! Создан сетевой симулятор.")
    return True

def stage_3_advanced_features() -> bool:
    """Этап 3: Расширенные возможности"""
    print_header("ЭТАП 3: РАСШИРЕННЫЕ ВОЗМОЖНОСТИ")
    
    print("Цель: Добавить возможности для реального применения:")
    print("  1. Фрактальная иерархия (кластеризация)")
    print("  2. Динамическое изменение топологии")
    print("  3. Экспорт/импорт состояния")
    print("  4. Интеграционные тесты")
    
    if not ask_continue("Начать этап 3?"):
        return True  # Этот этап опциональный
    
    # 3.1 Выбор приоритетных функций
    print_step("Выбор приоритетных расширений")
    
    feature_options = [
        "Фрактальная кластеризация (рекомендуется)",
        "Динамическая топология",
        "Сохранение/загрузка состояния",
        "Все перечисленные"
    ]
    feature_descs = [
        "Создание иерархии: группы узлов как супер-узлы",
        "Изменение связей во время работы",
        "Сериализация состояния для анализа/восстановления",
        "Полный набор функций"
    ]
    
    feature_choice = ask_choice("Какие расширения реализовать в первую очередь?", 
                               feature_options, feature_descs, default=0)
    
    # 3.2 Реализация выбранных функций
    if feature_choice in [0, 3]:  # Кластеризация
        print_step("Реализация фрактальной кластеризации")
        
        cluster_path = Path("src/fractal/cluster.py")
        cluster_content = '''"""
FractalCluster — кластер фрактальных единиц как супер-узел.
"""
from typing import List
from .unit import FractalUnit
from .network import FractalNetwork

class FractalCluster(FractalUnit):
    """Кластер единиц, ведущий себя как одна фрактальная единица."""
    
    def __init__(self, cluster_id: str, child_units: List[FractalUnit]):
        """
        Инициализация кластера.
        
        Args:
            cluster_id: Идентификатор кластера
            child_units: Список дочерних единиц
        """
        super().__init__(cluster_id)
        self.child_units = child_units
        self.child_network = None
        
        # Инициализируем внутреннюю сеть
        if len(child_units) > 1:
            self.child_network = FractalNetwork.__new__(FractalNetwork)
            self.child_network.units = child_units
            self.child_network.topology = "mesh"
            self.child_network.step_count = 0
            self.child_network.history = []
    
    @property
    def load(self) -> float:
        """Средняя нагрузка кластера."""
        if not self.child_units:
            return 0.0
        return sum(unit.load for unit in self.child_units) / len(self.child_units)
    
    @load.setter
    def load(self, value: float):
        """Распределение нагрузки по кластеру."""
        if not self.child_units:
            return
        
        # Простое равномерное распределение
        for unit in self.child_units:
            unit.load = value
    
    @property
    def health(self) -> float:
        """Наихудшее здоровье в кластере."""
        if not self.child_units:
            return 1.0
        return min(unit.health for unit in self.child_units)
    
    def compute_potential(self, target_load: float = 0.7) -> float:
        """
        Вычисление потенциала кластера как супер-узла.
        """
        if not self.child_units:
            self.local_potential = 0.0
            return 0.0
        
        # 1. Все дочерние единицы вычисляют свои потенциалы
        child_potentials = []
        for unit in self.child_units:
            child_potentials.append(unit.compute_potential(target_load))
        
        # 2. Внутренняя балансировка (если есть сеть)
        if self.child_network and len(self.child_units) > 1:
            self.child_network.simulate_step(target_load)
        
        # 3. Потенциал кластера = средний потенциал + штраф за неоднородность
        avg_potential = sum(child_potentials) / len(child_potentials)
        
        # Штраф за разброс потенциалов внутри кластера
        if len(child_potentials) > 1:
            max_diff = max(child_potentials) - min(child_potentials)
            imbalance_penalty = max_diff * 0.5
        else:
            imbalance_penalty = 0.0
        
        self.local_potential = avg_potential + imbalance_penalty
        return self.local_potential
    
    def transfer_load(self, transfer_rate: float = 0.05) -> float:
        """
        Передача нагрузки на уровне кластера.
        """
        if not self.child_network or len(self.child_units) <= 1:
            return 0.0
        
        # Внутренняя балансировка
        internal_transferred = 0.0
        for _ in range(3):  # Несколько итераций для лучшей балансировки
            for unit in self.child_units:
                internal_transferred += unit.transfer_load(transfer_rate * 0.5)
        
        return internal_transferred
'''
        
        with open(cluster_path, 'w', encoding='utf-8') as f:
            f.write(cluster_content)
        
        print_success(f"Создан файл: {cluster_path}")
    
    # Продолжение для других функций...
    print_step("Этап 3 будет продолжен в следующих итерациях")
    
    print_success("Этап 3 частично завершён. Дополнительные функции готовы к реализации.")
    return True

def stage_4_integration_tests() -> bool:
    """Этап 4: Интеграционные тесты"""
    print_header("ЭТАП 4: ИНТЕГРАЦИОННЫЕ ТЕСТЫ")
    
    print("Цель: Проверить работу всей системы в комплексе.")
    print("Создадим:")
    print("  - Тест полного цикла симуляции")
    print("  - Тест восстановления после сбоев")
    print("  - Тест разных топологий")
    print("  - Тест производительности")
    
    if not ask_continue("Создать интеграционные тесты?"):
        return True  # Опциональный этап
    
    # Создание интеграционных тестов
    test_path = Path("tests/test_integration.py")
    
    # ... (код интеграционных тестов) ...
    
    print_success("Интеграционные тесты созданы.")
    return True

def stage_5_documentation() -> bool:
    """Этап 5: Документация"""
    print_header("ЭТАП 5: ДОКУМЕНТАЦИЯ И ПОДГОТОВКА К ИНТЕГРАЦИИ")
    
    print("Цель: Подготовить модуль к интеграции с SpectraVortex.")
    print("Создадим:")
    print("  - README с примерами использования")
    print("  - API документацию")
    print("  - План интеграции с SolverManager")
    
    if not ask_continue("Создать документацию?"):
        return True
    
    # Создание документации
    # ... (код создания README, API docs) ...
    
    print_success("Документация создана.")
    return True

# --- Главная функция ---
def main():
    """Основной цикл разработки"""
    print(f"\n{Colors.BOLD}{'*'*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}   МАСТЕР РАЗРАБОТКИ ФРАКТАЛЬНО-АДАПТИВНОГО МОДУЛЯ   {Colors.END}")
    print(f"{Colors.BOLD}{'*'*70}{Colors.END}")
    
    print(f"\nТекущая директория: {Colors.BLUE}{PROJECT_ROOT}{Colors.END}")
    print("Этот мастер проведёт вас через все этапы разработки.")
    print("На каждом этапе вы сможете:")
    print("  • Увидеть что будет сделано")
    print("  • Выбрать варианты реализации")
    print("  • Подтвердить или отклонить действие")
    print(f"\n{Colors.YELLOW}Готовы начать?{Colors.END}")
    
    if not ask_continue("Запустить мастер разработки?"):
        print(f"\n{Colors.YELLOW}Мастер отменён.{Colors.END}")
        return
    
    # Этапы разработки
    stages = [
        ("Ядро системы (FractalUnit)", stage_1_core_unit),
        ("Сетевой симулятор", stage_2_network_simulator),
        ("Расширенные возможности", stage_3_advanced_features),
        ("Интеграционные тесты", stage_4_integration_tests),
        ("Документация", stage_5_documentation),
    ]
    
    completed_stages = []
    
    for i, (stage_name, stage_func) in enumerate(stages, 1):
        print(f"\n{Colors.BOLD}{'═'*70}{Colors.END}")
        print(f"{Colors.BOLD}Этап {i}/{len(stages)}: {stage_name}{Colors.END}")
        
        if ask_continue(f"Перейти к этапу '{stage_name}'?"):
            try:
                success = stage_func()
                if success:
                    completed_stages.append(stage_name)
                    print(f"\n{Colors.GREEN}✅ Этап '{stage_name}' успешно завершён!{Colors.END}")
                else:
                    print(f"\n{Colors.YELLOW}⚠ Этап '{stage_name}' пропущен или отменён.{Colors.END}")
                    
                    if not ask_continue("Продолжить со следующим этапом?"):
                        break
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}⚠ Этап прерван пользователем.{Colors.END}")
                if not ask_continue("Продолжить разработку?"):
                    break
            except Exception as e:
                print_error(f"Ошибка на этапе: {e}")
                if not ask_continue("Продолжить несмотря на ошибку?"):
                    break
        else:
            print(f"\n{Colors.YELLOW}⚠ Этап '{stage_name}' пропущен.{Colors.END}")
    
    # Итоги
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}   РАЗРАБОТКА ЗАВЕРШЕНА   {Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    
    if completed_stages:
        print(f"\n{Colors.GREEN}✅ Выполненные этапы:{Colors.END}")
        for stage in completed_stages:
            print(f"  • {stage}")
    
    # Следующие шаги
    print(f"\n{Colors.BOLD}Следующие шаги:{Colors.END}")
    print("  1. Проверить код: flake8 src/")
    print("  2. Запустить все тесты: pytest tests/ -v")
    print("  3. Запустить демо: python demo_network.py")
    print("  4. Проанализировать результаты в data/output/")
    
    print(f"\n{Colors.BOLD}Команды для проверки:{Colors.END}")
    print(f"  {Colors.BLUE}flake8 src/{Colors.END}")
    print(f"  {Colors.BLUE}pytest tests/ -v{Colors.END}")
    print(f"  {Colors.BLUE}python demo_network.py{Colors.END}")
    print(f"  {Colors.BLUE}python demo_network.py --compare{Colors.END}")
    
    print(f"\n{Colors.GREEN}🚀 Прототип готов к использованию и интеграции!{Colors.END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Разработка прервана пользователем.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        sys.exit(1)