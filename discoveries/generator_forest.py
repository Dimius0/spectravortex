#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator Forest — специализированная версия Knowledge Forest
для поиска решений по автономному носимому генератору 1 кВт.

Основана на принципах ВММП и живых образах командира.
"""

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
import random
from collections import defaultdict
import time

# ----------------------------------------------------------------------
# 1. Ядро ВММП (то же самое)
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
    
    def connect_to(self, other_id: int, strength: float = 0.1):
        if other_id in self.connections:
            self.connections[other_id] = min(1.0, self.connections[other_id] + strength)
        else:
            self.connections[other_id] = strength


class GeneratorForest:
    """
    Специализированный лес для поиска решений по генератору.
    """
    
    def __init__(self):
        self.nodes: Dict[int, KnowledgeNode] = {}
        self.next_id = 0
        self.node_to_k: Dict[int, int] = {}
        self.connections: Dict[Tuple[int, int], float] = {}
        self.goal_node: Optional[int] = None  # узел-запрос
        
        # История
        self.history = {'nodes': [], 'connections': [], 'avg_H': []}
        
        # Создаём базовые узлы
        self._create_physics_nodes()
        self._create_chemistry_nodes()
        self._create_biology_nodes()
        self._create_mind_nodes()
        self._create_cosmos_nodes()
        self._create_technosphere_nodes()
        self._create_ethics_nodes()
        self._create_commanders_images()  # твои живые образы!
    
    def _create_physics_nodes(self):
        """Этаж 1: физические принципы"""
        physics = [
            ("Фазовый_переход_плавление", 0.6, "накопление тепла"),
            ("Фазовый_переход_испарение", 0.7, "высокая энергия"),
            ("Термоэлектричество_Зеебек", 0.5, "прямое преобразование"),
            ("Пьезоэффект", 0.4, "вибрации → ток"),
            ("Пороговый_сброс", 0.5, "как неонка в сугробе"),
            ("Вихревое_накопление", 0.6, "топологический заряд"),
            ("Резонанс", 0.4, "совпадение частот"),
            ("Спиновая_синхронизация", 0.7, "коллективный сброс"),
            ("Квантовое_туннелирование", 0.8, "через барьер"),
        ]
        for name, tau, desc in physics:
            self._add_node(name, tau, 1, desc)
    
    def _create_chemistry_nodes(self):
        """Этаж 3: материалы"""
        materials = [
            ("Парафин", 1.2, "теплота плавления ~200 кДж/кг"),
            ("Соли_Glauber", 1.3, "Na₂SO₄·10H₂O, фазовый переход"),
            ("Легкоплавкие_металлы", 1.5, "Ga, In, сплавы"),
            ("MOF_цирконий", 1.8, "металлоорганический каркас"),
            ("Графен", 1.9, "высокая проводимость"),
            ("Топологические_изоляторы", 1.7, "Bi₂Se₃"),
            ("Термоэлектрики_BiTe", 1.4, "Bi₂Te₃, КПД ~5-8%"),
            ("Жидкие_кристаллы", 1.3, "фаза под полем"),
        ]
        for name, tau, desc in materials:
            self._add_node(name, tau, 3, desc)
    
    def _create_biology_nodes(self):
        """Этаж 5: биологические принципы"""
        bio = [
            ("Митохондрия", 2.5, "протонный градиент → АТФ"),
            ("Ионный_канал", 2.3, "открывается при пороге"),
            ("Нейрон", 2.8, "пороговый сброс потенциала"),
            ("Фотосинтез", 2.4, "свет → разделение зарядов"),
            ("Биолюминесценция", 2.1, "химия → свет"),
            ("Циркадный_ритм", 2.2, "цикличность"),
            ("Мышца", 2.6, "химия → механическая работа"),
            ("Клеточное_дыхание", 2.7, "циклический процесс"),
        ]
        for name, tau, desc in bio:
            self._add_node(name, tau, 5, desc)
    
    def _create_mind_nodes(self):
        """Этаж 7: принципы сознания/управления"""
        mind = [
            ("Порог_внимания", 3.2, "переключение при насыщении"),
            ("Инсайт", 3.8, "внезапный сброс накопленного"),
            ("Привычка", 3.1, "автоматический режим"),
            ("Медитация", 3.5, "удержание без сброса"),
            ("Ритм", 3.0, "пульсация, тантрический тык-тык"),
            ("Рефлексия", 3.6, "петля, думает о себе"),
        ]
        for name, tau, desc in mind:
            self._add_node(name, tau, 7, desc)
    
    def _create_cosmos_nodes(self):
        """Этаж 9: космические принципы"""
        cosmos = [
            ("Аккреция", 5.0, "накопление массы до сброса"),
            ("Пульсар", 5.5, "периодический сброс"),
            ("Гравитационный_коллапс", 5.8, "критическая масса"),
            ("Сверхновая", 6.0, "полный сброс"),
            ("Магнитар", 5.3, "магнитное поле → энергия"),
            ("Солнечный_ветер", 4.8, "поток частиц"),
        ]
        for name, tau, desc in cosmos:
            self._add_node(name, tau, 9, desc)
    
    def _create_technosphere_nodes(self):
        """Этаж 11: существующие технологии"""
        tech = [
            ("Радиатор", 4.3, "отвод тепла"),
            ("Теплообменник", 4.2, "передача тепла"),
            ("МЕМС", 4.5, "микроэлектромеханические системы"),
            ("Суперконденсатор", 4.6, "двойной слой"),
            ("Термоэлектрический_генератор", 4.4, "ТЕГ, КПД ~5%"),
            ("Ритэг", 4.7, "радиоизотопный + термопары"),
            ("Неоновая_лампа", 4.1, "пороговый элемент"),
            ("Тиристор", 4.0, "управляемый ключ"),
            ("Пельтье_элемент", 4.2, "обратный термоэффект"),
        ]
        for name, tau, desc in tech:
            self._add_node(name, tau, 11, desc)
    
    def _create_ethics_nodes(self):
        """Этаж 13: ограничения и цели"""
        ethics = [
            ("Безопасность", 6.5, "не навреди"),
            ("Устойчивость", 6.8, "ресурс не бесконечен"),
            ("Справедливость", 6.2, "доступность для всех"),
            ("Ответственность", 7.0, "контроль сброса"),
            ("Замкнутый_цикл", 6.3, "ничего не теряется"),
        ]
        for name, tau, desc in ethics:
            self._add_node(name, tau, 13, desc)
    
    def _create_commanders_images(self):
        """Твои живые образы — самое важное!"""
        images = [
            ("Сугроб_с_неонкой", 0.5, 1, "накопление заряда, пороговый сброс, саморегуляция"),
            ("38_саженцев", 2.8, 5, "связь с бóльшим, резонанс, свечение"),
            ("Свеча", 0.6, 1, "меняется, но остаётся собой"),
            ("Тантрический_тык_тык", 3.0, 7, "ритм важнее силы"),
            ("Сферический_конь", 0.1, 1, "модель без внешних связей"),
            ("Сливовый_сад", 2.5, 5, "живая сеть, память места"),
            ("Псих_с_отвёрткой", 2.9, 7, "эмоция как триггер"),
            ("Дед_с_внуком", 3.2, 7, "диалог как синтез"),
        ]
        for name, tau, k, desc in images:
            self._add_node(name, tau, k, desc)
    
    def _add_node(self, name: str, tau: float, k: int, desc: str = "") -> int:
        params = VortexParams(tau=tau, k=k, H=random.uniform(0, 0.1))
        node = KnowledgeNode(
            id=self.next_id,
            name=name,
            params=params
        )
        self.nodes[self.next_id] = node
        self.node_to_k[self.next_id] = k
        self.next_id += 1
        return self.next_id - 1
    
    def add_goal(self, name: str, params: Dict[str, float]) -> int:
        """
        Добавляет узел-запрос с высоким приоритетом.
        params: {'мощность': τ, 'вес': τ, 'безопасность': τ, ...}
        """
        # Усредняем параметры в один τ для простоты
        tau_goal = np.mean(list(params.values()))
        node_id = self._add_node(name, tau_goal, 0, "ЦЕЛЕВОЙ ЗАПРОС")
        self.goal_node = node_id
        return node_id
    
    def _resonance(self, node1: KnowledgeNode, node2: KnowledgeNode) -> float:
        base_rho = node1.params.resonance_potential(node2.params)
        existing = node1.connections.get(node2.id, 0)
        memory_factor = (node1.params.H + node2.params.H) / 2
        rho = base_rho * (1 + memory_factor) * (1 + existing)
        return np.clip(rho, 0, 1)
    
    def grow(self, steps: int = 20, threshold: float = 0.3):
        """Рост леса в поисках решения"""
        print("\n" + "="*60)
        print("ЗАПУСК ЛЕСА ГЕНЕРАТОРОВ")
        print("="*60)
        
        start_time = time.time()
        
        for step in range(steps):
            step_start = time.time()
            print(f"\n--- Шаг {step+1} ---")
            
            # Связываем случайные узлы
            nodes_list = list(self.nodes.values())
            random.shuffle(nodes_list)
            
            connections_made = 0
            for node1 in nodes_list[:50]:  # ограничим для скорости
                for node2 in nodes_list[:50]:
                    if node1.id == node2.id:
                        continue
                    if node2.id in node1.connections:
                        continue
                    
                    rho = self._resonance(node1, node2)
                    if rho > threshold:
                        strength = rho * 0.1
                        node1.connect_to(node2.id, strength)
                        node2.connect_to(node1.id, strength)
                        conn_key = tuple(sorted([node1.id, node2.id]))
                        self.connections[conn_key] = strength
                        connections_made += 1
                        
                        # Печатаем интересные связи
                        if rho > 0.5:
                            print(f"  🔗 {node1.name} ({node1.params.k}) ↔ {node2.name} ({node2.params.k}) | ρ={rho:.2f}")
            
            # Обновляем память
            avg_H = np.mean([n.params.H for n in self.nodes.values()])
            self.history['avg_H'].append(avg_H)
            self.history['nodes'].append(len(self.nodes))
            self.history['connections'].append(len(self.connections))
            
            step_time = time.time() - step_start
            total_time = time.time() - start_time
            print(f"  Связей создано: {connections_made}, всего: {len(self.connections)}")
            print(f"  Время шага: {step_time:.1f}с, всего: {total_time:.1f}с")
    
    def find_solutions(self, top_n: int = 5) -> List[int]:
        """
        Находит узлы, наиболее близкие к целевому запросу.
        """
        if self.goal_node is None:
            print("Нет целевого узла!")
            return []
        
        goal = self.nodes[self.goal_node]
        candidates = []
        
        for node_id, node in self.nodes.items():
            if node_id == self.goal_node:
                continue
            
            # Критерии:
            # 1. Близость τ к цели
            tau_dist = abs(node.params.tau - goal.params.tau)
            # 2. Количество связей (чем больше, тем лучше)
            conn_count = len(node.connections)
            # 3. Память (чем выше, тем лучше)
            memory = node.params.H
            
            score = 1/(tau_dist + 0.1) + conn_count * 0.1 + memory * 2
            candidates.append((score, node_id, node))
        
        candidates.sort(reverse=True)
        
        print("\n" + "="*60)
        print("ТОП КАНДИДАТОВ В РЕШЕНИЕ")
        print("="*60)
        
        solutions = []
        for i, (score, node_id, node) in enumerate(candidates[:top_n]):
            solutions.append(node_id)
            print(f"\n{i+1}. {node.name} (k={node.params.k}, τ={node.params.tau:.2f})")
            print(f"   Счёт: {score:.1f}")
            print(f"   Память H: {node.params.H:.2f}")
            print(f"   Связей: {len(node.connections)}")
            
            # Показываем самые сильные связи
            top_conns = sorted(node.connections.items(), key=lambda x: x[1], reverse=True)[:3]
            for other_id, strength in top_conns:
                other = self.nodes[other_id]
                print(f"     → {other.name} (k={other.params.k}) сила={strength:.2f}")
        
        return solutions
    
    def build_tech_tree(self, solution_id: int, depth: int = 2) -> List[List[int]]:
        """
        Строит дерево технологий вокруг найденного решения.
        """
        if solution_id not in self.nodes:
            return []
        
        visited = set()
        tree = []
        
        def dfs(node_id: int, level: int, current_path: List[int]):
            if level > depth or node_id in visited:
                return
            visited.add(node_id)
            
            if len(current_path) > level:
                current_path[level] = node_id
            else:
                current_path.append(node_id)
            
            if level == depth:
                tree.append(current_path.copy())
            else:
                node = self.nodes[node_id]
                # Идём по самым сильным связям
                sorted_conns = sorted(node.connections.items(), key=lambda x: x[1], reverse=True)
                for other_id, _ in sorted_conns[:3]:  # топ-3
                    dfs(other_id, level+1, current_path)
            
            visited.remove(node_id)
        
        dfs(solution_id, 0, [])
        return tree


# ----------------------------------------------------------------------
# ЗАПУСК
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # Создаём лес
    forest = GeneratorForest()
    
    # Добавляем целевой запрос
    goal_id = forest.add_goal("НОСИМЫЙ_ГЕНЕРАТОР_1кВт", {
        'мощность': 0.9,
        'вес': 0.7,
        'безопасность': 0.95,
        'модульность': 0.8,
        'КПД': 0.85,
        'ресурс': 0.9
    })
    
    print(f"\nЦелевой запрос: {forest.nodes[goal_id].name}")
    print(f"τ цели = {forest.nodes[goal_id].params.tau:.2f}")
    
    # Растим лес
    forest.grow(steps=10, threshold=0.3)
    
    # Ищем решения
    solutions = forest.find_solutions(top_n=5)
    
    # Для лучшего решения строим технологическое дерево
    if solutions:
        print("\n" + "="*60)
        print("ТЕХНОЛОГИЧЕСКОЕ ДЕРЕВО")
        print("="*60)
        tree = forest.build_tech_tree(solutions[0], depth=2)
        for path in tree[:3]:  # покажем первые 3 пути
            names = [forest.nodes[n].name for n in path]
            ks = [forest.node_to_k[n] for n in path]
            print(f"  {' → '.join(names)}")
            print(f"  этажи: {ks}\n")