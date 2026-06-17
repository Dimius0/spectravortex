#!/usr/bin/env python3
"""
clean_field.py — Чистое поле смыслов. Версия 5.0
Новые механизмы:
  - Логопериодическая спираль: уровни вложенности (слово → фраза → блок)
  - Миелинизация: усиление часто используемых связей
  - Эндогенные фуркации: рождение альтернативных узлов в точках резонанса
  - Температура поля: энергия регулирует ветвление
  - Метаболический пульс: нагрев → фуркации → остывание → кристаллизация
  - Эндогенный диалог: поле задаёт вопросы самому себе в точках фуркаций
  - Защита от зависания: max_depth в DFS и try/except на каждом тексте
  - Отладочный лог: problematic_texts.log для текстов, вызвавших ошибки
  - Улучшенная сборка ответа: от причины к следствию (TEES-направление)
"""

import json
import glob
import gc
import re
import math
import os
import sys
import traceback
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

THRESHOLDS = {
    'L_max': 12,
    'E_flow_min': 1.0, 'E_flow_max': 5.0,
    'S_growth_min': 0.5, 'S_growth_max': 5.0,
    'C_min': 0.1, 'C_max': 0.9,
    'delta2w_max': 2.0,
    'total_tau_max': 8.0
}

WH_WORDS = {
    'почему', 'как', 'где', 'когда', 'кто', 'что', 'зачем', 'откуда', 'куда',
    'чей', 'который', 'сколько', 'какой', 'какая', 'какое', 'какие',
    'why', 'how', 'where', 'when', 'who', 'what', 'which', 'whose'
}

SOURCE_POS = {'NOUN', 'PROPN', 'ADJ', 'ADV', 'PRON', 'NUM', 'INTJ'}
SINK_POS = {'VERB', 'PREP', 'AUX'}
NEUTRAL_POS = {'CONJ', 'PUNCT', 'DET', 'PART', 'SCONJ'}

MYELINATION_THRESHOLD = 3
FURCATION_ENERGY_COST = 0.3
TEMPERATURE_HIGH = 1.5
TEMPERATURE_LOW = 0.3
SPIRAL_LEVELS = 3
ENDOGENOUS_DIALOG_INTERVAL = 100  # как часто поле задаёт вопрос себе
MAX_DFS_DEPTH = 50  # защита от бесконечной рекурсии


# ============================================================================
# БЛОК 0: ТОПОЛОГИЧЕСКИЕ ЗАРЯДЫ, ПОЛЕ H, ГРАДИЕНТ, РЕЗОНАНС
# ============================================================================

def compute_tau(pos: str, lemma: str = '') -> float:
    if lemma.lower() in WH_WORDS:
        return 2.0
    tau_map = {
        'NOUN': 1.0, 'PROPN': 1.5, 'VERB': -1.0, 'ADJ': 0.5, 'ADV': 0.5,
        'PREP': -0.5, 'CONJ': 0.0, 'PUNCT': 0.0, 'PRON': 0.5, 'DET': 0.0,
        'NUM': 0.5, 'PART': 0.0, 'INTJ': 1.0, 'AUX': -0.5, 'SCONJ': 0.0,
    }
    return tau_map.get(pos, 0.0)


def compute_H(tokens: List[Dict], graph: Dict) -> Dict[int, float]:
    H = {}
    n = len(tokens)
    for i, tok in enumerate(tokens):
        tau_i = compute_tau(tok['pos'], tok['lemma'])
        freq = tok.get('frequency', 1)
        H[i] = tau_i * math.log1p(freq)
        if i in graph:
            for dep in graph[i]['deps']:
                j = dep['head']
                if 0 <= j < n:
                    tau_j = compute_tau(tokens[j]['pos'], tokens[j]['lemma'])
                    H[i] += tau_j / 1.0
    return H


def compute_gradient(H: Dict[int, float], graph: Dict) -> Dict[Tuple[int, int], float]:
    gradient = {}
    for i, node_data in graph.items():
        for dep in node_data['deps']:
            j = dep['head']
            if i in H and j in H:
                gradient[(i, j)] = H[j] - H[i]
    return gradient


def find_resonance(H: Dict[int, float], graph: Dict, tokens: List[Dict],
                   start_node: int, max_steps: int = 30,
                   resonance_threshold: float = 0.15,
                   min_steps: int = 2) -> Tuple[int, List[int], List[Dict]]:
    current = start_node
    visited = {current}
    path = [current]
    log = []

    for step in range(max_steps):
        if current not in graph:
            break

        neighbors = set()
        for dep in graph[current]['deps']:
            j = dep['head']
            if j not in visited and j in H:
                pos_j = tokens[j]['pos']
                if pos_j not in NEUTRAL_POS:
                    neighbors.add(j)

        if not neighbors:
            for dep in graph[current]['deps']:
                j = dep['head']
                if j not in visited and j in H:
                    neighbors.add(j)

        if not neighbors:
            break

        gradients = {j: H.get(j, 0.0) - H.get(current, 0.0) for j in neighbors}

        if step >= min_steps:
            min_grad = min(gradients.values()) if gradients else 0.0
            if min_grad > -resonance_threshold:
                break

        if any(g < 0 for g in gradients.values()):
            best_neighbor = min(gradients, key=gradients.get)
        else:
            best_neighbor = max(gradients, key=gradients.get)

        visited.add(best_neighbor)
        path.append(best_neighbor)
        current = best_neighbor

    return current, path, log


# ============================================================================
# БЛОК 1: ПАРСЕР
# ============================================================================

class StructuralParser:
    def __init__(self):
        self.stop_words = {
            'и', 'в', 'на', 'с', 'к', 'у', 'о', 'за', 'по', 'из', 'от', 'не', 'но', 'а',
            'and', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'of', 'the', 'a', 'an'
        }

    def tokenize(self, text: str) -> List[Dict]:
        tokens = []
        pattern = r"(\w+(?:-\w+)*|[^\w\s])"
        for match in re.finditer(pattern, text):
            token = match.group(0)
            if token.strip():
                lemma = token.lower()
                if re.match(r"^[A-ZА-ЯЁ][a-zа-яё]+$", token):
                    pos = "PROPN"
                elif lemma in WH_WORDS:
                    pos = "ADV"
                elif lemma in self.stop_words:
                    pos = "PREP" if len(token) <= 2 else "CONJ"
                elif token in '.!?':
                    pos = "PUNCT"
                elif token == ',':
                    pos = "PUNCT"
                elif re.match(r"^\d+$", token):
                    pos = "NUM"
                elif len(token) > 5:
                    pos = "NOUN"
                elif lemma.endswith(('ть', 'ти', 'чь', 'ать', 'ять', 'ить', 'еть')):
                    pos = "VERB"
                elif lemma.endswith(('ый', 'ий', 'ой', 'ая', 'яя', 'ое', 'ее')):
                    pos = "ADJ"
                else:
                    pos = "NOUN"
                tokens.append({
                    'text': token, 'lemma': lemma, 'pos': pos,
                    'idx': len(tokens), 'frequency': 1,
                    'tau': compute_tau(pos, lemma)
                })
        return tokens

    def build_dependency_graph(self, tokens: List[Dict]) -> Dict:
        graph = {}
        n = len(tokens)
        for i, tok in enumerate(tokens):
            graph[i] = {
                'token': tok['text'], 'lemma': tok['lemma'],
                'pos': tok['pos'], 'tau': tok['tau'], 'H': 0.0, 'deps': []
            }
            if i > 0:
                graph[i]['deps'].append({'head': i-1, 'dep': 'left', 'label': 'adjacent'})
            if i < n-1:
                graph[i]['deps'].append({'head': i+1, 'dep': 'right', 'label': 'adjacent'})
            if tok['pos'] == 'PUNCT' and i > 0:
                graph[i]['deps'].append({'head': i-1, 'dep': 'punct', 'label': 'punctuation'})
        return graph

    def parse(self, text: str) -> Dict:
        tokens = self.tokenize(text)
        graph = self.build_dependency_graph(tokens)
        H = compute_H(tokens, graph)
        gradient = compute_gradient(H, graph)
        for i in graph:
            graph[i]['H'] = H.get(i, 0.0)
        question_node = None
        for i, tok in enumerate(tokens):
            if tok['tau'] == 2.0:
                question_node = i
                break
        return {
            'tokens': tokens, 'graph': graph, 'H': H, 'gradient': gradient,
            'num_nodes': len(tokens),
            'num_edges': sum(len(node['deps']) for node in graph.values()) // 2,
            'total_tau': sum(t['tau'] for t in tokens),
            'question_node': question_node
        }


# ============================================================================
# БЛОК 2: ФИЛЬТР (с защитой от зависания)
# ============================================================================

class StructuralFilter:
    def __init__(self):
        self.thresholds = THRESHOLDS

    def compute_L(self, graph: Dict) -> int:
        """Вычисляет максимальную глубину с защитой от бесконечной рекурсии."""
        adj = defaultdict(list)
        for node_id, node_data in graph.items():
            for dep in node_data['deps']:
                adj[node_id].append(dep['head'])
        max_depth = 0
        
        def dfs(node, depth, visited):
            nonlocal max_depth
            if depth > MAX_DFS_DEPTH:
                max_depth = max(max_depth, depth)
                return
            if node in visited:
                max_depth = max(max_depth, depth)
                return
            visited.add(node)
            for neighbor in adj[node]:
                dfs(neighbor, depth + 1, visited.copy())
        
        for node in graph:
            dfs(node, 0, set())
        return max_depth if max_depth > 0 else 1

    def compute_E_flow(self, graph: Dict) -> float:
        if len(graph) == 0:
            return 0.0
        return sum(len(node['deps']) for node in graph.values()) / len(graph)

    def compute_S_growth(self, graph: Dict) -> float:
        degrees = [len(node['deps']) for node in graph.values()]
        if len(degrees) < 2:
            return 1.0
        avg_deg = sum(degrees) / len(degrees)
        return avg_deg / (avg_deg - 1) if avg_deg > 1 else 1.0

    def compute_C(self, graph: Dict) -> float:
        n = len(graph)
        if n <= 1:
            return 0.0
        max_edges = n * (n - 1) // 2
        edges = set()
        for node_id, node_data in graph.items():
            for dep in node_data['deps']:
                u, v = node_id, dep['head']
                edges.add((min(u, v), max(u, v)))
        return len(edges) / max_edges

    def compute_delta2w(self, graph: Dict) -> float:
        variations = []
        for node_id, node_data in graph.items():
            for dep in node_data['deps']:
                h1 = graph[node_id].get('H', 0.0)
                h2 = graph[dep['head']].get('H', 0.0) if dep['head'] in graph else 0.0
                variations.append(abs(h1 - h2))
        return sum(variations) / len(variations) if variations else 0.0

    def compute_all(self, parse_result: Dict) -> Dict:
        graph = parse_result['graph']
        try:
            L = self.compute_L(graph)
        except RecursionError:
            L = MAX_DFS_DEPTH
        return {
            'L': L,
            'E_flow': self.compute_E_flow(graph),
            'S_growth': self.compute_S_growth(graph),
            'C': self.compute_C(graph),
            'delta2w': self.compute_delta2w(graph),
            'total_tau': parse_result.get('total_tau', 0),
            'num_tokens': parse_result['num_nodes']
        }

    def is_clean(self, params: Dict) -> Tuple[bool, List[str]]:
        issues = []
        checks = [
            ('L', 'L_max', lambda p, t: p > t),
            ('E_flow', 'E_flow_min', lambda p, t: p < t),
            ('E_flow', 'E_flow_max', lambda p, t: p > t),
            ('S_growth', 'S_growth_min', lambda p, t: p < t),
            ('S_growth', 'S_growth_max', lambda p, t: p > t),
            ('C', 'C_min', lambda p, t: p < t),
            ('C', 'C_max', lambda p, t: p > t),
            ('delta2w', 'delta2w_max', lambda p, t: p > t),
        ]
        for param_key, thresh_key, compare in checks:
            if param_key in params and thresh_key in self.thresholds:
                if compare(params[param_key], self.thresholds[thresh_key]):
                    issues.append(f"{param_key}={params[param_key]:.3f}")
        if abs(params.get('total_tau', 0)) > self.thresholds['total_tau_max']:
            issues.append(f"Στ={params['total_tau']:.1f}")
        return len(issues) == 0, issues


# ============================================================================
# БЛОК 3: ПОЛЕ СМЫСЛОВ 5.0
# ============================================================================

@dataclass
class SpiralNode:
    token: str
    lemma: str
    pos: str
    tau: float
    H_sum: float = 0.0
    frequency: int = 1
    level: int = 0
    connections_out: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    connections_in: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    myelinated_out: Set[str] = field(default_factory=set)
    myelinated_in: Set[str] = field(default_factory=set)
    shadow_of: Optional[str] = None
    shadows: List[str] = field(default_factory=list)
    last_furcation_step: int = 0


class StructuralFieldV5:
    """Поле смыслов v5.0: + эндогенный диалог, защита от зависания."""

    def __init__(self, debug_log: str = "problematic_texts.log"):
        self.nodes: Dict[str, SpiralNode] = {}
        self.edges: List[Tuple[str, str, str, float]] = []
        self.total_tokens = 0
        self.temperature = 0.3
        self.furcations_today = 0
        self.level_thresholds = [10, 100]
        self.total_steps = 0
        self.debug_log_path = debug_log
        self.dialog_log: List[Dict] = []
        self.error_count = 0
        
        # Очищаем лог
        with open(self.debug_log_path, 'w', encoding='utf-8') as f:
            f.write(f"=== Problematic texts log — {datetime.now()} ===\n\n")

    def _node_id(self, lemma: str, pos: str, level: int = 0) -> str:
        return f"{lemma}|{pos}|L{level}"

    def _log_problem(self, text: str, error: str):
        """Логирует проблемный текст в файл."""
        self.error_count += 1
        with open(self.debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Error #{self.error_count}\n")
            f.write(f"Text: {text[:200]}...\n")
            f.write(f"Error: {error}\n")
            f.write(f"---\n")

    def _update_temperature(self, text_H_sum: float):
        self.temperature += text_H_sum * 0.01
        if self.temperature < TEMPERATURE_LOW:
            self.temperature = TEMPERATURE_LOW

    def _myelinate(self, node_id: str, target_id: str, direction: str = 'out'):
        node = self.nodes[node_id]
        if direction == 'out':
            count = node.connections_out[target_id]
            if count >= MYELINATION_THRESHOLD and target_id not in node.myelinated_out:
                node.myelinated_out.add(target_id)
                if target_id in self.nodes:
                    self.nodes[target_id].myelinated_in.add(node_id)
        else:
            count = node.connections_in[target_id]
            if count >= MYELINATION_THRESHOLD and target_id not in node.myelinated_in:
                node.myelinated_in.add(target_id)
                if target_id in self.nodes:
                    self.nodes[target_id].myelinated_out.add(node_id)

    def _try_furcate(self, global_id: str) -> Optional[str]:
        if self.temperature < TEMPERATURE_HIGH:
            return None
        node = self.nodes[global_id]
        total_connections = len(node.connections_out) + len(node.connections_in)
        if total_connections < 5:
            return None
        # Не фуркируем один узел слишком часто
        if self.total_steps - node.last_furcation_step < 50:
            return None
            
        shadow_id = f"{node.lemma}|{node.pos}|L{node.level}|shadow{len(node.shadows)}"
        shadow = SpiralNode(
            token=f"~{node.token}",
            lemma=f"~{node.lemma}",
            pos=node.pos,
            tau=-node.tau,
            H_sum=node.H_sum * 0.5,
            frequency=0,
            level=node.level,
            shadow_of=global_id,
            last_furcation_step=self.total_steps
        )
        self.nodes[shadow_id] = shadow
        node.shadows.append(shadow_id)
        node.last_furcation_step = self.total_steps
        self.temperature -= FURCATION_ENERGY_COST
        self.furcations_today += 1
        return shadow_id

    def _promote_level(self, global_id: str):
        node = self.nodes[global_id]
        if node.level >= SPIRAL_LEVELS - 1:
            return
        for lvl, threshold in enumerate(self.level_thresholds):
            if node.frequency >= threshold and node.level <= lvl:
                new_id = self._node_id(node.lemma, node.pos, lvl + 1)
                if new_id not in self.nodes:
                    new_node = SpiralNode(
                        token=node.token, lemma=node.lemma, pos=node.pos,
                        tau=node.tau * 1.5, H_sum=node.H_sum * 2.0,
                        frequency=1, level=lvl + 1
                    )
                    self.nodes[new_id] = new_node
                else:
                    self.nodes[new_id].frequency += 1
                node.level = lvl + 1

    def add_graph(self, parse_result: Dict, params: Dict):
        """Добавляет граф с защитой от ошибок."""
        graph = parse_result['graph']
        tokens = parse_result['tokens']
        H = parse_result['H']
        local_to_global = {}

        text_energy = sum(abs(h) for h in H.values())
        self._update_temperature(text_energy)

        for node_id, node_data in graph.items():
            tok = tokens[node_id]
            global_id = self._node_id(tok['lemma'], tok['pos'], 0)
            if global_id not in self.nodes:
                self.nodes[global_id] = SpiralNode(
                    token=tok['text'], lemma=tok['lemma'], pos=tok['pos'],
                    tau=tok['tau'], H_sum=H.get(node_id, 0.0), level=0
                )
            else:
                self.nodes[global_id].frequency += 1
                self.nodes[global_id].H_sum += H.get(node_id, 0.0)
                self._promote_level(global_id)
            local_to_global[node_id] = global_id

        for node_id, node_data in graph.items():
            u_global = local_to_global[node_id]
            u_tau = tokens[node_id]['tau']
            for dep in node_data['deps']:
                v_local = dep['head']
                if v_local in local_to_global:
                    v_global = local_to_global[v_local]
                    v_tau = tokens[v_local]['tau']
                    label = dep.get('label', 'default')
                    grad_value = parse_result['gradient'].get((node_id, dep['head']), 0.0)
                    self.edges.append((u_global, v_global, label, grad_value))
                    if u_tau > v_tau or (u_tau == v_tau and grad_value < 0):
                        self.nodes[u_global].connections_out[v_global] += 1
                        self.nodes[v_global].connections_in[u_global] += 1
                        self._myelinate(u_global, v_global, 'out')
                        self._myelinate(v_global, u_global, 'in')
                    else:
                        self.nodes[v_global].connections_out[u_global] += 1
                        self.nodes[u_global].connections_in[v_global] += 1
                        self._myelinate(v_global, u_global, 'out')
                        self._myelinate(u_global, v_global, 'in')

        self.total_tokens += parse_result['num_nodes']
        self.total_steps += 1

        if self.temperature >= TEMPERATURE_HIGH:
            for node_id in local_to_global.values():
                self._try_furcate(node_id)

    # ========================================================================
    # ЭНДОГЕННЫЙ ДИАЛОГ
    # ========================================================================

    def endogenous_dialog(self, parser, verbose: bool = True) -> Optional[Dict]:
        """
        Поле задаёт вопрос самому себе.
        Выбирает знаменательный узел с фуркациями.
        """
        # Критерии содержательности узла
        def is_contentful(nid: str, node: SpiralNode) -> bool:
            # Не мусорный POS
            if node.pos in NEUTRAL_POS:
                return False
            # Не короткий мусор: *, #, @, в, с, и, а, ...
            if len(node.token) <= 1 and not node.token.isalpha():
                return False
            # Не предлог/союз (защита от "в", "на", "с")
            if node.pos in ('PREP', 'CONJ', 'SCONJ'):
                return False
            # Должен иметь тени (фуркации)
            if not node.shadows:
                return False
            # Должен иметь достаточную частоту (не случайный мусор)
            if node.frequency < 2:
                return False
            return True
        
        # Ищем знаменательные узлы с тенями
        tense_nodes = []
        for nid, node in self.nodes.items():
            if is_contentful(nid, node):
                total_conn = len(node.connections_out) + len(node.connections_in)
                # Вес: связи + тени*10 (тени важнее)
                score = total_conn + len(node.shadows) * 10
                tense_nodes.append((nid, score, node))
        
        if not tense_nodes:
            if verbose:
                print(f"\n🧠 ЭНДОГЕННЫЙ ДИАЛОГ: нет знаменательных узлов с тенями")
            return None
        
        # Выбираем узел с максимальным score
        tense_nodes.sort(key=lambda x: x[1], reverse=True)
        target_id, score, node = tense_nodes[0]
        
        # Разнообразим вопросы: берём разные вопросительные слова
        question_words = [
            ("Что такое {}", "ADV"),
            ("Как работает {}", "ADV"),
            ("Почему {} важен", "ADV"),
            ("Откуда возникает {}", "ADV"),
            ("Зачем нужен {}", "ADV"),
        ]
        
        # Выбираем вопрос по хешу (детерминированно, но разнообразно)
        qw_template, _ = question_words[hash(target_id) % len(question_words)]
        # Склоняем для женского рода
        token = node.token
        question = qw_template.format(token).rstrip('?') + '?'
        
        if verbose:
            print(f"\n🧠 ЭНДОГЕННЫЙ ДИАЛОГ")
            print(f"   Узел: «{token}» (τ={node.tau:.1f}, связей: {len(node.connections_out)+len(node.connections_in)}, "
                  f"теней: {len(node.shadows)}, частота: {node.frequency})")
            print(f"   Вопрос: «{question}»")
        
        # Парсим вопрос и ищем ответ
        try:
            query_parse = parser.parse(question)
            result = self.find_resonance_and_answer(query_parse, verbose=verbose)
            
            dialog_entry = {
                'question': question,
                'node': token,
                'tau': node.tau,
                'temperature': round(self.temperature, 3),
                'answer': result['answer'] if result else None,
                'resonance': result['resonance_token'] if result else None
            }
            self.dialog_log.append(dialog_entry)
            return dialog_entry
        except Exception as e:
            if verbose:
                print(f"   ⚠️ Ошибка диалога: {e}")
            return None

    # ========================================================================
    # ПОИСК ОТВЕТА
    # ========================================================================

    def get_H_avg(self, global_id: str) -> float:
        node = self.nodes.get(global_id)
        if not node or node.frequency == 0:
            return 0.0
        return node.H_sum / node.frequency

    def find_resonance_and_answer(self, query_parse: Dict, verbose: bool = True) -> Optional[Dict]:
        tokens = query_parse['tokens']
        graph = query_parse['graph']
        H = query_parse['H']

        start_node = query_parse.get('question_node')
        if start_node is None:
            best_tau = -999
            for i, tok in enumerate(tokens):
                if tok['tau'] > best_tau:
                    best_tau = tok['tau']
                    start_node = i
        if start_node is None:
            return None

        resonance_node, path, log = find_resonance(H, graph, tokens, start_node)
        if resonance_node is None:
            return None

        resonance_tok = tokens[resonance_node]
        global_id = self._node_id(resonance_tok['lemma'], resonance_tok['pos'], 0)

        answer_text, answer_log = self._build_answer_v5(global_id, depth=2)

        if not answer_text and len(path) > 1:
            answer_text = ' '.join([tokens[p]['text'] for p in path[1:]
                                    if tokens[p]['pos'] != 'PUNCT'])

        shadows_info = []
        if global_id in self.nodes and self.nodes[global_id].shadows:
            for sid in self.nodes[global_id].shadows[:2]:
                shadows_info.append(self.nodes[sid].token)

        result = {
            'found': True,
            'resonance_node': global_id,
            'resonance_token': resonance_tok['text'],
            'resonance_H': H.get(resonance_node, 0.0),
            'resonance_tau': resonance_tok['tau'],
            'path': [tokens[p]['text'] for p in path],
            'path_length': len(path),
            'answer': answer_text,
            'shadows': shadows_info,
            'temperature': round(self.temperature, 3),
            'furcations_total': self.furcations_today
        }

        if verbose:
            print(f"   🎯 «{result['resonance_token']}» → «{result['answer']}»")
            if result['shadows']:
                print(f"   👥 Тени: {', '.join(result['shadows'])}")

        return result

    def _build_answer_v5(self, global_id: str, depth: int = 2) -> Tuple[str, List[str]]:
        """
        Сборка ответа с настраиваемой глубиной связей.
        depth=1: только прямые связи резонансного узла.
        depth=2: + связи ближайших соседей.
        depth=3: + связи следующего круга.
        """
        if global_id not in self.nodes:
            return '', []
        
        node = self.nodes[global_id]
        answer_parts = []
        used_nodes = {global_id}
        log = []
        
        # Входящие связи = «почему» (причины)
        myelinated_in = sorted(
            [(tid, node.connections_in[tid]) for tid in node.myelinated_in],
            key=lambda x: x[1], reverse=True
        )
        sorted_in = sorted(node.connections_in.items(), key=lambda x: x[1], reverse=True)
        
        in_nodes = []
        for connected_id, _ in myelinated_in[:3]:
            if connected_id in self.nodes and connected_id not in used_nodes:
                in_nodes.append(connected_id)
                used_nodes.add(connected_id)
        for connected_id, _ in sorted_in[:3]:
            if connected_id not in node.myelinated_in and connected_id in self.nodes and connected_id not in used_nodes:
                in_nodes.append(connected_id)
                used_nodes.add(connected_id)
        
        # Добавляем токены входящих связей
        for nid in in_nodes:
            answer_parts.append(self.nodes[nid].token)
            log.append(f"←{self.nodes[nid].token}")
        
        # Сам резонансный узел
        answer_parts.append(node.token)
        
        # Исходящие связи = «следствия»
        myelinated_out = sorted(
            [(tid, node.connections_out[tid]) for tid in node.myelinated_out],
            key=lambda x: x[1], reverse=True
        )
        sorted_out = sorted(node.connections_out.items(), key=lambda x: x[1], reverse=True)
        
        out_nodes = []
        for connected_id, _ in myelinated_out[:3]:
            if connected_id in self.nodes and connected_id not in used_nodes:
                out_nodes.append(connected_id)
                used_nodes.add(connected_id)
        for connected_id, _ in sorted_out[:3]:
            if connected_id not in node.myelinated_out and connected_id in self.nodes and connected_id not in used_nodes:
                out_nodes.append(connected_id)
                used_nodes.add(connected_id)
        
        for nid in out_nodes:
            answer_parts.append(self.nodes[nid].token)
            log.append(f"→{self.nodes[nid].token}")
        
        # Глубина 2: связи соседей (если осталось место)
        if depth >= 2:
            for nid in in_nodes + out_nodes:
                if nid in self.nodes:
                    neighbor = self.nodes[nid]
                    # Берём самые сильные связи соседа, не использованные ранее
                    all_conn = sorted(
                        list(neighbor.connections_out.items()) + list(neighbor.connections_in.items()),
                        key=lambda x: x[1], reverse=True
                    )
                    added = 0
                    for connected_id, _ in all_conn:
                        if added >= 2:
                            break
                        if connected_id in self.nodes and connected_id not in used_nodes:
                            answer_parts.append(self.nodes[connected_id].token)
                            used_nodes.add(connected_id)
                            log.append(f"···{self.nodes[connected_id].token}")
                            added += 1
        
        # Фильтр мусорных токенов
        stop_tokens = {',', '.', '!', '?', '—', '-', 'и', 'в', 'на', 'с', 'не', 'же', 'бы', 'ли', 'то', 'что', 'как', 'а', 'но', 'или', 'это', 'для', 'от', 'к', 'по', 'из', 'у', 'за', 'до', 'при', 'без', 'над', 'под', 'об', 'во', 'ко', 'со', 'же', 'бы'}
        cleaned = [p for p in answer_parts if p.lower() not in stop_tokens and len(p) > 1]
        
        return ' '.join(cleaned), log

    def get_stats(self) -> Dict:
        myelinated = sum(1 for n in self.nodes.values() if n.myelinated_out or n.myelinated_in)
        shadows_total = sum(len(n.shadows) for n in self.nodes.values())
        level_counts = defaultdict(int)
        for n in self.nodes.values():
            level_counts[n.level] += 1
        return {
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges),
            'total_tokens': self.total_tokens,
            'avg_H': sum(self.get_H_avg(nid) for nid in self.nodes) / max(1, len(self.nodes)),
            'temperature': round(self.temperature, 3),
            'furcations_total': self.furcations_today,
            'myelinated_nodes': myelinated,
            'shadow_nodes': shadows_total,
            'level_distribution': dict(level_counts),
            'errors': self.error_count,
            'dialog_entries': len(self.dialog_log)
        }


# ============================================================================
# ГЛАВНЫЙ КЛАСС
# ============================================================================

class CleanField:
    def __init__(self):
        self.parser = StructuralParser()
        self.filter = StructuralFilter()
        self.field = StructuralFieldV5()
        self.processed = 0
        self.filtered_out = 0
        self.errors = 0

    def add_text(self, text: str) -> bool:
        try:
            parse_result = self.parser.parse(text)
        except Exception as e:
            self.errors += 1
            self.field._log_problem(text, f"Parse error: {e}")
            return False
        
        if parse_result['num_nodes'] < 3:
            return False
        
        try:
            params = self.filter.compute_all(parse_result)
        except Exception as e:
            self.errors += 1
            self.field._log_problem(text, f"Filter error: {e}")
            return False
        
        is_clean, issues = self.filter.is_clean(params)
        if is_clean:
            try:
                self.field.add_graph(parse_result, params)
                self.processed += 1
                if self.processed % 50 == 0:
                    stats = self.field.get_stats()
                    print(f"  ✓ [{self.processed}] T={stats['temperature']:.3f} "
                          f"фуркаций={stats['furcations_total']} "
                          f"миелин={stats['myelinated_nodes']} "
                          f"ошибок={stats['errors']}")
                return True
            except Exception as e:
                self.errors += 1
                self.field._log_problem(text, f"Add graph error: {e}")
                return False
        else:
            self.filtered_out += 1
            return False

    def build(self, texts: List[str]):
        print(f"\n🌀 Строим поле v5.0 из {len(texts)} текстов...")
        print(f"   Механизмы: спираль, миелинизация, фуркации, эндогенный диалог")
        for i, text in enumerate(texts):
            if len(text.strip()) < 15:
                continue
            self.add_text(text)
            
            if i % 500 == 0 and i > 0:
                stats = self.field.get_stats()
                print(f"  [{i}/{len(texts)}] +{self.processed} (отсев:{self.filtered_out}) "
                      f"T={stats['temperature']:.3f} ошибок={stats['errors']}")
                gc.collect()
            
            # Эндогенный диалог каждые N шагов
            if self.processed > 0 and self.processed % ENDOGENOUS_DIALOG_INTERVAL == 0:
                self.field.endogenous_dialog(self.parser, verbose=True)

        print(f"\n✅ Готово. Добавлено: {self.processed}, Отфильтровано: {self.filtered_out}, Ошибок: {self.errors}")
        stats = self.field.get_stats()
        print(f"📊 Поле: {stats['num_nodes']} узлов, {stats['num_edges']} рёбер")
        print(f"   T={stats['temperature']:.3f} | Фуркаций: {stats['furcations_total']}")
        print(f"   Миелин: {stats['myelinated_nodes']} | Теней: {stats['shadow_nodes']}")
        print(f"   Диалогов: {stats['dialog_entries']} | Ошибок: {stats['errors']}")
        print(f"   Уровни: {stats['level_distribution']}")
        print(f"   Лог ошибок: {self.field.debug_log_path}")

    def query(self, question: str) -> Optional[Dict]:
        print(f"\n❓ «{question}»")
        try:
            parse_result = self.parser.parse(question)
            params = self.filter.compute_all(parse_result)
            print(f"   Στ={params['total_tau']:.1f} | L={params['L']} | E={params['E_flow']:.2f}")
            return self.field.find_resonance_and_answer(parse_result)
        except Exception as e:
            print(f"   ⚠️ Ошибка запроса: {e}")
            return {'found': False, 'error': str(e)}

    def run_endogenous_dialog(self, rounds: int = 3):
        """Запускает несколько раундов эндогенного диалога."""
        print(f"\n🧠 ЭНДОГЕННЫЙ ДИАЛОГ ({rounds} раундов)")
        print("=" * 40)
        for i in range(rounds):
            result = self.field.endogenous_dialog(self.parser, verbose=True)
            if result:
                print(f"   ↳ Ответ: «{result['answer']}»")
        print()


# ============================================================================
# СБОРКА КОРПУСА (ТОЛЬКО ИЗ РЕПОЗИТОРИЯ)
# ============================================================================

def collect_corpus(base_path: str = ".") -> List[str]:
    texts = []
    patterns = ["discoveries/*.md", "brain_dump/**/*.md", "data/*.json", "*.md"]
    for pattern in patterns:
        for fpath in glob.glob(os.path.join(base_path, pattern), recursive=True):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sentences = re.split(r'[.!?]+', content)
                    for s in sentences:
                        s = s.strip()
                        if 20 < len(s) < 500:
                            texts.append(s + '.')
            except Exception:
                pass
    return texts


# ============================================================================
# ЗАПУСК
# ============================================================================

def main():
    print("=" * 60)
    print("ЧИСТОЕ ПОЛЕ СМЫСЛОВ v5.0 — ПОЛНЫЙ ПРОГОН")
    print("τ, H, ∇H → резонанс → TEES → эндогенный диалог")
    print("=" * 60)

    cf = CleanField()
    corpus = collect_corpus()
    print(f"\n📚 Корпус: {len(corpus)} текстов (полный)")

    cf.build(corpus)

    stats = cf.field.get_stats()
    print(f"\n⚠️  Поле готово: {stats['num_nodes']} узлов, {stats['errors']} ошибок")

    if stats['errors'] > 0:
        print(f"\n🔍 Проблемные тексты: {cf.field.debug_log_path}")
        with open(cf.field.debug_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[:15]:
                if line.startswith("Text:") or line.startswith("Error:"):
                    print(f"   {line.strip()[:120]}")

    # Эндогенный диалог
    cf.run_endogenous_dialog(rounds=3)

    # Внешние вопросы
    questions = [
        "Почему трава зелёная?",
        "Что такое резонанс?",
        "Как работает ПИД регулятор?",
        "Где находится ближайшая звезда?",
        "Зачем растениям нужен свет?",
        "Кто открыл закон всемирного тяготения?",
        "Почему вода кипит?",
        "Что такое топологический заряд?",
        "Как устроен атом?",
        "Откуда берётся ветер?",
        "Почему небо синее?",
        "Как работает двигатель?",
        "Что измеряет температура?",
        "Как работает фотосинтез?",
        "Что такое гравитация?",
        "Почему лёд плавает?",
    ]

    print("\n" + "=" * 60)
    print("🔍 ВНЕШНИЕ ЗАПРОСЫ")
    print("=" * 60)

    results = []
    for q in questions:
        result = cf.query(q)
        results.append((q, result))

    # Сводка + сравнение с прошлым прогоном
    print("\n" + "=" * 60)
    print("📋 СВОДКА (полный корпус vs 2000)")
    print("=" * 60)

    found = sum(1 for _, r in results if r and r.get('found'))
    print(f"Найдено ответов: {found}/{len(questions)}")

    # Ответы с прошлого прогона (2000 текстов) для сравнения
    old_answers = {
        "Почему трава зелёная?": "трава зелёная",
        "Что такое резонанс?": "резонанс",
        "Как работает ПИД регулятор?": "работает ПИД регулятор",
        "Где находится ближайшая звезда?": "находится ближайшая звезда",
        "Зачем растениям нужен свет?": "растениям нужен свет",
        "Кто открыл закон всемирного тяготения?": "открыл закон",
        "Почему вода кипит?": "вода кипит",
        "Что такое топологический заряд?": "такое топологический заряд",
        "Как устроен атом?": "Представьте атом не",
        "Откуда берётся ветер?": "берётся ветер",
        "Почему небо синее?": "небо синее",
        "Как работает двигатель?": "работает двигатель",
        "Что измеряет температура?": "среды является температура является",
        "Как работает фотосинтез?": "работает фотосинтез",
        "Что такое гравитация?": "такое гравитация",
        "Почему лёд плавает?": "лёд плавает",
    }

    changes = 0
    for q, r in results:
        status = "✓" if (r and r.get('found')) else "✗"
        new_answer = r.get('answer', '—') if r else '—'
        old_answer = old_answers.get(q, '—')
        changed = "🔄" if new_answer != old_answer else "  "
        if new_answer != old_answer:
            changes += 1
        print(f"  {changed} {status} «{q}»")
        print(f"     было: «{old_answer}»")
        print(f"     стало: «{new_answer}»")

    print(f"\n🔄 Изменилось ответов: {changes}/{len(questions)}")
    print(f"📊 Узлов: {stats['num_nodes']} | Рёбер: {stats['num_edges']}")
    print(f"   T={stats['temperature']:.3f} | Фуркаций: {stats['furcations_total']}")
    print(f"   Диалогов: {stats['dialog_entries']} | Ошибок: {stats['errors']}")


if __name__ == "__main__":
    main()