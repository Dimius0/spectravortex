#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Forest — фрактальная модель растущего знания.
Упрощённая версия для генератора ошибок.
"""

import numpy as np
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict

# ----------------------------------------------------------------------
# 1. Ядро ВММП
# ----------------------------------------------------------------------
@dataclass
class VortexParams:
    tau: float
    k: int
    H: float = 0.0
    n: float = None
    
    def __post_init__(self):
        if self.n is None:
            self.n = abs(self.tau) * self.k
    
    def distance_to(self, other: 'VortexParams') -> float:
        return abs(self.n - other.n)
    
    def resonance_potential(self, other: 'VortexParams') -> float:
        d = self.distance_to(other)
        return np.exp(-d / 10.0)


@dataclass
class KnowledgeNode:
    id: int
    name: str
    params: VortexParams
    parent_id: Optional[int] = None
    children_ids: List[int] = field(default_factory=list)
    connections: Dict[int, float] = field(default_factory=dict)
    
    def add_child(self, child_id: int):
        """Добавляет потомка"""
        self.children_ids.append(child_id)
    
    def connect_to(self, other_id: int, strength: float = 0.1):
        """Создаёт или укрепляет связь"""
        if other_id in self.connections:
            self.connections[other_id] = min(1.0, self.connections[other_id] + strength)
        else:
            self.connections[other_id] = strength
    
    def get_connection_strength(self, other_id: int) -> float:
        """Возвращает силу связи с другим узлом (0 если связи нет)"""
        return self.connections.get(other_id, 0.0)


class KnowledgeTree:
    def __init__(self, k: int, name: str, base_tau_range: Tuple[float, float]):
        self.k = k
        self.name = name
        self.base_tau_range = base_tau_range
        self.nodes: Dict[int, KnowledgeNode] = {}
        self.next_id = 0
        self.root_id: Optional[int] = None
        self._create_root()
    
    def _create_root(self):
        tau = random.uniform(*self.base_tau_range)
        params = VortexParams(tau=tau, k=self.k, H=0.0)
        self.root_id = self.next_id
        self.nodes[self.root_id] = KnowledgeNode(
            id=self.root_id,
            name=f"{self.name}_root",
            params=params
        )
        self.next_id += 1
    
    def add_node(self, parent_id: int, name: str, tau_shift: float = 0.0) -> int:
        if parent_id not in self.nodes:
            raise ValueError(f"Parent node {parent_id} not found")
        
        parent = self.nodes[parent_id]
        new_tau = parent.params.tau + tau_shift
        new_tau = np.clip(new_tau, self.base_tau_range[0], self.base_tau_range[1])
        new_H = parent.params.H * 0.9 + random.uniform(0, 0.1)
        params = VortexParams(tau=new_tau, k=self.k, H=new_H)
        
        node_id = self.next_id
        self.nodes[node_id] = KnowledgeNode(
            id=node_id,
            name=name,
            params=params,
            parent_id=parent_id
        )
        parent.add_child(node_id)
        self.next_id += 1
        return node_id
    
    def furcate(self, parent_id: int, n_branches: int = 1) -> List[int]:
        new_ids = []
        for _ in range(n_branches):
            tau_shift = random.gauss(0, 0.2)
            name = f"{self.name}_node_{self.next_id}"
            node_id = self.add_node(parent_id, name, tau_shift)
            new_ids.append(node_id)
        return new_ids
    
    def get_node(self, node_id: int) -> KnowledgeNode:
        return self.nodes[node_id]
    
    def size(self) -> int:
        return len(self.nodes)


class KnowledgeForest:
    def __init__(self):
        self.trees: Dict[int, KnowledgeTree] = {}
        self.node_to_tree: Dict[int, int] = {}
        self.history = {'nodes': [], 'connections': [], 'avg_H': []}
    
    def add_tree(self, tree: KnowledgeTree):
        self.trees[tree.k] = tree
        for node_id in tree.nodes:
            self.node_to_tree[node_id] = tree.k
    
    def _resonance(self, node1: KnowledgeNode, node2: KnowledgeNode) -> float:
        """Вычисляет резонанс между двумя узлами"""
        base_rho = node1.params.resonance_potential(node2.params)
        existing = node1.get_connection_strength(node2.id)
        memory_factor = (node1.params.H + node2.params.H) / 2
        rho = base_rho * (1 + memory_factor) * (1 + existing)
        return np.clip(rho, 0, 1)
    
    def grow_towards(self, tree1_k: int, tree2_k: int, threshold: float = 0.5) -> List[Tuple[int, int]]:
        """Проращивает связи между двумя деревьями"""
        if tree1_k not in self.trees or tree2_k not in self.trees:
            return []
        
        tree1 = self.trees[tree1_k]
        tree2 = self.trees[tree2_k]
        new_connections = []
        
        for node1 in tree1.nodes.values():
            for node2 in tree2.nodes.values():
                if node2.id in node1.connections:
                    continue
                try:
                    rho = self._resonance(node1, node2)
                    if rho > threshold:
                        strength = rho * 0.1
                        node1.connect_to(node2.id, strength)
                        node2.connect_to(node1.id, strength)
                        new_connections.append((node1.id, node2.id))
                except Exception as e:
                    # Игнорируем ошибки резонанса
                    continue
        
        return new_connections
    
    def grow_all(self, threshold: float = 0.5) -> int:
        """Проращивает связи между всеми деревьями"""
        total = 0
        ks = list(self.trees.keys())
        for i in range(len(ks)):
            for j in range(i+1, len(ks)):
                try:
                    conns = self.grow_towards(ks[i], ks[j], threshold)
                    total += len(conns)
                except Exception as e:
                    continue
        return total
    
    def total_nodes(self) -> int:
        return sum(tree.size() for tree in self.trees.values())
    
    def total_connections(self) -> int:
        total = 0
        for tree in self.trees.values():
            for node in tree.nodes.values():
                total += len(node.connections)
        return total // 2
    
    def analyze_distribution(self, sigma_threshold: float = 1.0, quiet: bool = False) -> List[int]:
        """Находит узлы с отклонением > sigma_threshold, возвращает их ID"""
        outliers = []
        
        for k, tree in self.trees.items():
            nodes = list(tree.nodes.values())
            if len(nodes) < 2:
                continue
            
            tau_values = [n.params.tau for n in nodes]
            if len(tau_values) == 0:
                continue
                
            mean_tau = np.mean(tau_values)
            std_tau = np.std(tau_values)
            
            if std_tau == 0:
                continue
                
            for node in nodes:
                if abs(node.params.tau - mean_tau) > sigma_threshold * std_tau:
                    if node.connections:
                        outliers.append(node.id)
        
        return outliers


# ----------------------------------------------------------------------
# Генератор ошибок (надстройка над лесом)
# ----------------------------------------------------------------------
class ErrorGenerator:
    def __init__(self, forest: KnowledgeForest):
        self.forest = forest
        self.history = []
    
    def experiment(self, node_id: int, violations: List[float]) -> Tuple[float, str]:
        """
        Проводит эксперимент над узлом.
        violations — список сил нарушений (0.1-1.0)
        Возвращает (новый потенциал, статус)
        """
        if node_id not in self.forest.node_to_tree:
            return 0, "узел не найден"
        
        k = self.forest.node_to_tree[node_id]
        node = self.forest.trees[k].nodes[node_id]
        
        # Исходный потенциал
        P0 = node.params.n * (1 + node.params.H)
        if P0 == 0:
            P0 = 1.0
        
        # Применяем нарушения
        delta_sum = sum(violations)
        N = len(violations)
        
        # Новый потенциал (теорема Липсика)
        P = P0 * (1 + delta_sum) * math.exp(N)
        
        # Классификация
        ratio = P / P0
        if ratio < 2:
            status = "обычный"
        elif ratio < 5:
            status = "аномальный"
        elif ratio < 20:
            status = "прорывной"
        else:
            status = "НЕИЗВЕСТНОЕ"
        
        self.history.append({
            'node': node_id,
            'name': node.name,
            'violations': N,
            'P0': P0,
            'P': P,
            'status': status
        })
        
        return P, status
    
    def suggest_experiment(self) -> Tuple[int, str, int]:
        """Возвращает (id узла, имя, рекомендуемое число нарушений)"""
        try:
            outliers = self.forest.analyze_distribution(sigma_threshold=1.0, quiet=True)
            
            if outliers:
                node_id = random.choice(outliers)
                k = self.forest.node_to_tree[node_id]
                node = self.forest.trees[k].nodes[node_id]
                N = random.randint(1, 3)
                return node_id, node.name, N
        except Exception as e:
            pass
        
        # Берём случайный узел
        k = random.choice(list(self.forest.trees.keys()))
        node_id = random.choice(list(self.forest.trees[k].nodes.keys()))
        node = self.forest.trees[k].nodes[node_id]
        return node_id, node.name, 1


# ----------------------------------------------------------------------
# Для тестирования
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("🌳 KNOWLEDGE FOREST (упрощённая версия)")
    print("=" * 60)
    
    # Создаём лес
    forest = KnowledgeForest()
    
    # Добавляем деревья
    trees_data = [
        (3, "materials", (0.5, 3.0)),
        (1, "physics", (0.1, 1.0)),
    ]
    
    for k, name, tau_range in trees_data:
        tree = KnowledgeTree(k, name, tau_range)
        # Добавляем несколько узлов
        if k == 3:
            tree.add_node(tree.root_id, "графен чистый", 0)
            tree.add_node(tree.root_id, "графен дефектный", 0.3)
            tree.add_node(tree.root_id, "MOF цирконий", 0.5)
            tree.add_node(tree.root_id, "Bi2Se3", 0.7)
            tree.add_node(tree.root_id, "осадок со свалки", 1.2)
        else:
            tree.add_node(tree.root_id, "туннелирование", 0)
            tree.add_node(tree.root_id, "синхронизация", 0.2)
            tree.add_node(tree.root_id, "фазовый переход", 0.1)
        forest.add_tree(tree)
    
    # Проращиваем связи
    print("🌱 Проращиваем начальные связи...")
    forest.grow_all(threshold=0.3)
    print(f"   Создано связей: {forest.total_connections()}")
    
    # Тестируем генератор
    gen = ErrorGenerator(forest)
    
    print("\n🧪 ТЕСТ ГЕНЕРАТОРА ОШИБОК")
    for i in range(3):
        node_id, name, N = gen.suggest_experiment()
        violations = [random.uniform(0.2, 0.8) for _ in range(N)]
        P, status = gen.experiment(node_id, violations)
        print(f"\nЭксперимент {i+1}: {name}")
        print(f"   нарушений: {N}")
        print(f"   потенциал: {P:.1f}")
        print(f"   статус: {status}")