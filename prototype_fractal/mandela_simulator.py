#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mandela Effect Simulator
Дискретно-временная симуляция фуркаций и эффекта Манделы в рамках ВММП.

Основана на:
- Теореме о фуркации в дискретном времени
- Памяти H как носителе следов ветвления
- Резонансной активации скрытых воспоминаний
"""

import numpy as np
import random
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import networkx as nx
from enum import Enum

# ======================================================================
# 1. БАЗОВЫЕ ПАРАМЕТРЫ
# ======================================================================

class NodeType(Enum):
    ORDINARY = 0      # обычный узел
    BRANCH_POINT = 1  # точка бифуркации
    MANDELA = 2       # узел с эффектом Манделы

@dataclass
class VortexParams:
    """Параметры вихря (ВММП)"""
    tau: float        # топологический заряд
    k: int            # этаж сборки
    H: float = 0.0    # память (накопленная история)
    n: float = None   # вихревое число = |tau| * k
    
    def __post_init__(self):
        if self.n is None:
            self.n = abs(self.tau) * self.k
    
    def distance_to(self, other: 'VortexParams') -> float:
        """Вихревое расстояние"""
        return abs(self.n - other.n)
    
    def resonance_potential(self, other: 'VortexParams') -> float:
        """Потенциальный резонанс (0-1)"""
        d = self.distance_to(other)
        return np.exp(-d / 10.0)

@dataclass
class QuantumNode:
    """Узел с поддержкой мультиветвленности"""
    id: int
    name: str
    params: VortexParams
    parent_id: Optional[int] = None
    children_ids: List[int] = field(default_factory=list)
    connections: Dict[int, float] = field(default_factory=dict)
    
    # Квантовые свойства
    alt_state: Optional['QuantumNode'] = None  # альтернативная ветка
    H_shadow: float = 0.0                       # память о другой ветке
    node_type: NodeType = NodeType.ORDINARY
    branch_time: Optional[int] = None            # время фуркации
    mandela_count: int = 0                       # сколько раз активировалась чужая память
    
    def connect_to(self, other_id: int, strength: float = 0.1):
        """Создаёт или укрепляет связь"""
        if other_id in self.connections:
            self.connections[other_id] = min(1.0, self.connections[other_id] + strength)
        else:
            self.connections[other_id] = strength
    
    def get_connection_strength(self, other_id: int) -> float:
        return self.connections.get(other_id, 0.0)
    
    def copy(self) -> 'QuantumNode':
        """Создаёт копию узла (для ветвления)"""
        new_node = QuantumNode(
            id=self.id,
            name=self.name,
            params=VortexParams(self.params.tau, self.params.k, self.params.H),
            parent_id=self.parent_id,
            children_ids=self.children_ids.copy(),
            connections=self.connections.copy()
        )
        return new_node
    
    @property
    def n(self) -> float:
        return self.params.n
    
    @property
    def tau(self) -> float:
        return self.params.tau
    
    @property
    def k(self) -> int:
        return self.params.k
    
    @property
    def H(self) -> float:
        return self.params.H
    
    @H.setter
    def H(self, value: float):
        self.params.H = value
        self.params.n = abs(self.params.tau) * self.params.k

# ======================================================================
# 2. ЛЕС ЗНАНИЙ С ПОДДЕРЖКОЙ КВАНТОВЫХ СОСТОЯНИЙ
# ======================================================================

class QuantumForest:
    """Лес знаний с дискретным временем и фуркациями"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        
        self.nodes: Dict[int, QuantumNode] = {}
        self.next_id = 0
        self.time = 0
        
        # Статистика
        self.branch_points: List[Tuple[int, int, float, float]] = []  # (time, node_id, H1, H2)
        self.mandela_events: List[Tuple[int, int, float]] = []        # (time, node_id, strength)
        self.branch_history: Dict[int, List[int]] = defaultdict(list)  # node_id -> [times]
        self.node_count_history: List[int] = []  # история количества узлов
        
        # Параметры
        self.F_crit = 5.0           # критическое значение для бифуркации
        self.resonance_threshold = 2.0  # порог резонанса
        self.H_decay = 0.99          # затухание скрытой памяти со временем
        self.activation_prob = 0.3    # вероятность активации при резонансе
        
    def add_node(self, tau: float, k: int, H: float = 0.0, name: str = "") -> int:
        """Добавляет новый узел в лес"""
        params = VortexParams(tau=tau, k=k, H=H)
        node = QuantumNode(
            id=self.next_id,
            name=name or f"node_{self.next_id}",
            params=params
        )
        self.nodes[node.id] = node
        self.next_id += 1
        return node.id
    
    def create_connection(self, id1: int, id2: int, strength: float = 0.1):
        """Создаёт связь между узлами"""
        if id1 in self.nodes and id2 in self.nodes:
            self.nodes[id1].connect_to(id2, strength)
            self.nodes[id2].connect_to(id1, strength)
    
    def F_stability(self, node: QuantumNode) -> float:
        """
        Функционал устойчивости (упрощённая формула Липсика)
        Чем выше F, тем стабильнее система
        """
        E = node.n * 0.5  # энергия
        S = len(node.connections) * 0.2  # энтропия (связность)
        L = 1.0  # время жизни
        H = node.H * 0.3
        U = 0.1 * len(node.children_ids)  # дефекты (потомки)
        B = 1.0  # буфер
        
        return E + S + L + H - U + B
    
    def is_bifurcation_point(self, node: QuantumNode) -> bool:
        """
        Проверяет, находится ли узел в точке бифуркации
        """
        F = self.F_stability(node)
        # Случайный элемент для большей реалистичности
        return abs(F - self.F_crit) < 0.5 and random.random() < 0.3
    
    def create_furcation(self, node: QuantumNode) -> Tuple[QuantumNode, QuantumNode]:
        """
        Создаёт фуркацию узла
        Возвращает две ветки
        """
        # Создаём копии
        node1 = node.copy()
        node2 = node.copy()
        
        # Расщепляем память
        delta_H = random.uniform(0.2, 0.8)
        node1.H += delta_H
        node2.H -= delta_H
        
        # Каждая ветка помнит о другой
        node1.H_shadow = abs(node2.H) * 0.5
        node2.H_shadow = abs(node1.H) * 0.5
        
        # Меняем топологический заряд
        node1.params.tau += random.uniform(-0.1, 0.1)
        node2.params.tau += random.uniform(-0.1, 0.1)
        
        # Обновляем вихревые числа
        node1.params.n = abs(node1.params.tau) * node1.k
        node2.params.n = abs(node2.params.tau) * node2.k
        
        # Маркируем как точки ветвления
        node1.node_type = NodeType.BRANCH_POINT
        node2.node_type = NodeType.BRANCH_POINT
        node1.branch_time = self.time
        node2.branch_time = self.time
        
        # Запоминаем событие
        self.branch_points.append((self.time, node.id, node1.H, node2.H))
        self.branch_history[node.id].append(self.time)
        
        return node1, node2
    
    def evolve_network(self):
        """
        Эволюция сети: создание связей между близкими узлами
        """
        nodes_list = list(self.nodes.values())
        for i, node1 in enumerate(nodes_list):
            for node2 in nodes_list[i+1:]:
                # Проверяем, нет ли уже связи
                if node2.id in node1.connections:
                    continue
                
                # Резонансный потенциал
                rho = node1.params.resonance_potential(node2.params)
                
                # Создаём связь, если потенциал высок
                if rho > 0.3:
                    strength = rho * 0.2
                    self.create_connection(node1.id, node2.id, strength)
    
    def check_resonance_activation(self, node: QuantumNode):
        """
        Проверяет, не активируется ли скрытая память через резонанс
        """
        if node.H_shadow < 0.01:
            return
        
        # Поиск резонансных партнёров
        for other in self.nodes.values():
            if other.id == node.id:
                continue
            
            # Резонанс по вихревому числу
            if abs(node.n - other.n) < self.resonance_threshold:
                # Вероятностная активация
                if random.random() < self.activation_prob:
                    # Активируем скрытую память
                    activation = other.H_shadow * random.uniform(0.1, 0.3)
                    node.H += activation
                    node.mandela_count += 1
                    
                    # Запоминаем событие
                    self.mandela_events.append((self.time, node.id, activation))
                    
                    # Маркируем узел
                    node.node_type = NodeType.MANDELA
                    
                    print(f"  ✨ Эффект Манделы: узел {node.id} получил "
                          f"чужую память {activation:.3f} от узла {other.id}")
                    return
    
    def step(self):
        """
        Один шаг симуляции (дискретное время)
        """
        # Фаза 1: безвременье — поиск точек бифуркации
        bifurcation_nodes = []
        for node in self.nodes.values():
            if self.is_bifurcation_point(node):
                bifurcation_nodes.append(node)
        
        # Создаём фуркации (не более 10% узлов за шаг)
        new_nodes = {}
        max_branches = max(1, len(self.nodes) // 10)
        
        for node in bifurcation_nodes[:max_branches]:
            node1, node2 = self.create_furcation(node)
            
            # Назначаем новые ID
            node1.id = self.next_id
            self.next_id += 1
            node2.id = self.next_id
            self.next_id += 1
            
            new_nodes[node1.id] = node1
            new_nodes[node2.id] = node2
            
            # Удаляем старый узел
            del self.nodes[node.id]
        
        # Добавляем новые узлы
        self.nodes.update(new_nodes)
        
        # Фаза 2: время — эволюция сети
        self.evolve_network()
        
        # Фаза 3: резонансная активация
        for node in self.nodes.values():
            self.check_resonance_activation(node)
        
        # Затухание скрытой памяти
        for node in self.nodes.values():
            node.H_shadow *= self.H_decay
        
        self.time += 1
        self.node_count_history.append(len(self.nodes))
        
    def run(self, steps: int = 100, verbose: bool = True):
        """
        Запуск симуляции на несколько шагов
        """
        print(f"\n{'='*60}")
        print(f"🧪 ЗАПУСК СИМУЛЯЦИИ ЭФФЕКТА МАНДЕЛЫ")
        print(f"{'='*60}")
        print(f"Шагов: {steps}")
        print(f"Начальное количество узлов: {len(self.nodes)}")
        print(f"{'='*60}\n")
        
        for step in range(steps):
            old_count = len(self.nodes)
            self.step()
            new_count = len(self.nodes)
            
            if verbose and (step % 10 == 0 or new_count != old_count):
                print(f"\n--- Шаг {step+1} ---")
                print(f"  Узлов: {new_count} (Δ = {new_count - old_count})")
                print(f"  Фуркаций всего: {len(self.branch_points)}")
                print(f"  Эффектов Манделы: {len(self.mandela_events)}")
        
        print(f"\n{'='*60}")
        print(f"✅ СИМУЛЯЦИЯ ЗАВЕРШЕНА")
        print(f"{'='*60}")
        print(f"Итоговое количество узлов: {len(self.nodes)}")
        print(f"Всего фуркаций: {len(self.branch_points)}")
        print(f"Всего эффектов Манделы: {len(self.mandela_events)}")
        print(f"{'='*60}")
    
    def get_stats(self) -> dict:
        """Возвращает статистику симуляции"""
        mandela_nodes = [n for n in self.nodes.values() if n.mandela_count > 0]
        
        return {
            'nodes': len(self.nodes),
            'branches': len(self.branch_points),
            'mandela_events': len(self.mandela_events),
            'mandela_nodes': len(mandela_nodes),
            'avg_mandela': np.mean([n.mandela_count for n in mandela_nodes]) if mandela_nodes else 0,
            'total_H': sum(n.H for n in self.nodes.values()),
            'total_H_shadow': sum(n.H_shadow for n in self.nodes.values())
        }
    
    def plot_results(self):
        """Визуализация результатов"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Рост количества узлов
        axes[0,0].plot(self.node_count_history, 'b-', linewidth=2)
        axes[0,0].set_title('Рост количества узлов')
        axes[0,0].set_xlabel('Время')
        axes[0,0].set_ylabel('Количество узлов')
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Фуркации по времени
        if self.branch_points:
            times = [b[0] for b in self.branch_points]
            axes[0,1].hist(times, bins=min(20, len(set(times))), color='purple', alpha=0.7)
            axes[0,1].set_title('Распределение фуркаций по времени')
            axes[0,1].set_xlabel('Время')
            axes[0,1].set_ylabel('Количество')
            axes[0,1].grid(True, alpha=0.3)
        
        # 3. Эффекты Манделы
        if self.mandela_events:
            times = [e[0] for e in self.mandela_events]
            strengths = [e[2] for e in self.mandela_events]
            axes[1,0].scatter(times, strengths, alpha=0.6, color='red', s=30)
            axes[1,0].set_title('Эффекты Манделы (сила активации)')
            axes[1,0].set_xlabel('Время')
            axes[1,0].set_ylabel('Сила')
            axes[1,0].grid(True, alpha=0.3)
        
        # 4. Распределение памяти
        H_values = [n.H for n in self.nodes.values()]
        H_shadow_values = [n.H_shadow for n in self.nodes.values() if n.H_shadow > 0.01]
        
        axes[1,1].hist(H_values, bins=30, alpha=0.5, label='H (память)', density=True)
        if H_shadow_values:
            axes[1,1].hist(H_shadow_values, bins=30, alpha=0.5, color='orange', 
                          label='H_shadow', density=True)
        axes[1,1].set_title('Распределение памяти')
        axes[1,1].set_xlabel('H')
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


# ======================================================================
# 3. СОЗДАНИЕ ТЕСТОВОГО ЛЕСА
# ======================================================================

def create_test_forest(seed: int = 42, size: int = 30) -> QuantumForest:
    """
    Создаёт тестовый лес для симуляции
    """
    forest = QuantumForest(seed=seed)
    
    # Создаём базовые узлы на разных этажах
    for i in range(size):
        k = random.choice([1, 3, 5, 7, 9, 11, 13])  # все этажи
        tau = random.uniform(0.5, 5.0)
        H = random.uniform(0, 0.5)
        name = f"node_{i}_k{k}"
        forest.add_node(tau, k, H, name)
    
    # Создаём начальные связи
    nodes = list(forest.nodes.values())
    for i, node1 in enumerate(nodes):
        for node2 in nodes[i+1:]:
            if random.random() < 0.2:  # 20% начальных связей
                strength = random.uniform(0.05, 0.15)
                forest.create_connection(node1.id, node2.id, strength)
    
    return forest


# ======================================================================
# 4. ЗАПУСК
# ======================================================================

if __name__ == "__main__":
    # Создаём лес
    print("🌳 Создание тестового леса...")
    forest = create_test_forest(seed=42, size=30)
    
    # Запускаем симуляцию
    forest.run(steps=100, verbose=True)
    
    # Статистика
    stats = forest.get_stats()
    print(f"\n📊 Статистика:")
    for key, value in stats.items():
        print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")
    
    # Визуализация
    print("\n📈 Построение графиков...")
    forest.plot_results()
    
    print("\n🎯 Вывод:")
    if stats['mandela_events'] > 0:
        print(f"  ✅ Эффект Манделы обнаружен!")
        print(f"  Затронуто узлов: {stats['mandela_nodes']} из {stats['nodes']}")
        print(f"  Средняя сила: {stats['avg_mandela']:.3f}")
        print(f"  Фуркаций: {stats['branches']}")
    else:
        print("  ❌ Эффект Манделы не обнаружен.")
        print("  Попробуйте изменить параметры:")
        print("    - Уменьшить F_crit")
        print("    - Увеличить activation_prob")
        print("    - Увеличить количество шагов")