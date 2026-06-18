#!/usr/bin/env python3
"""
clean_field.py — Чистое поле смыслов. Версия 6.1
Стековый парсер + изоморфный поиск по леммам: ответ = фрагмент скрипта с общими словами.
Термины: τ, H, ∇H, резонанс, бифуркация, TEES-канал, проводимость, пропускная способность.
"""

import json, glob, gc, re, math, os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

THRESHOLDS = {
    'L_max': 20, 'E_flow_min': 0.5, 'E_flow_max': 10.0,
    'S_growth_min': 0.3, 'S_growth_max': 10.0,
    'C_min': 0.05, 'C_max': 0.9, 'delta2w_max': 3.0, 'total_tau_max': 12.0
}

WH_WORDS = {
    'почему', 'как', 'где', 'когда', 'кто', 'что', 'зачем', 'откуда', 'куда',
    'чей', 'который', 'сколько', 'какой', 'какая', 'какое', 'какие',
    'why', 'how', 'where', 'when', 'who', 'what', 'which', 'whose'
}

SOURCE_POS = {'NOUN', 'PROPN', 'ADJ', 'ADV', 'PRON', 'NUM', 'INTJ'}
SINK_POS = {'VERB', 'PREP', 'AUX'}
NEUTRAL_POS = {'CONJ', 'PUNCT', 'DET', 'PART', 'SCONJ'}

CONDUCTIVITY_THRESHOLD = 3
BIFURCATION_ENERGY_COST = 0.3
TEMPERATURE_HIGH = 1.5
TEMPERATURE_LOW = 0.3
SPIRAL_LEVELS = 3
ENDOGENOUS_DIALOG_INTERVAL = 100
MAX_DFS_DEPTH = 50


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
    for step in range(max_steps):
        if current not in graph:
            break
        neighbors = set()
        for dep in graph[current]['deps']:
            j = dep['head']
            if j not in visited and j in H:
                if tokens[j]['pos'] not in NEUTRAL_POS:
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
            if min(gradients.values()) > -resonance_threshold:
                break
        if any(g < 0 for g in gradients.values()):
            best_neighbor = min(gradients, key=gradients.get)
        else:
            best_neighbor = max(gradients, key=gradients.get)
        visited.add(best_neighbor)
        path.append(best_neighbor)
        current = best_neighbor
    return current, path, []


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
        operand_stack = []
        operator_stack = []
        pending_prep = None
        question_node = None
        for i, tok in enumerate(tokens):
            tau = tok['tau']
            pos = tok['pos']
            if tau == 2.0:
                question_node = i
                if operator_stack:
                    graph[i]['deps'].append({'head': operator_stack[-1], 'dep': 'question', 'label': 'question_to_verb'})
                continue
            if pos == 'PUNCT' and tok['text'] in '.!?':
                if operator_stack:
                    graph[i]['deps'].append({'head': operator_stack[-1], 'dep': 'punct', 'label': 'end'})
                elif operand_stack:
                    graph[i]['deps'].append({'head': operand_stack[-1], 'dep': 'punct', 'label': 'end'})
                operand_stack.clear(); operator_stack.clear(); pending_prep = None
                continue
            if pos == 'PUNCT':
                if operator_stack:
                    graph[i]['deps'].append({'head': operator_stack[-1], 'dep': 'punct', 'label': 'comma'})
                continue
            if tau < 0 or pos == 'CONJ':
                if pos == 'PREP':
                    pending_prep = i
                if operand_stack:
                    graph[i]['deps'].append({'head': operand_stack[-1], 'dep': 'operand_to_operator', 'label': 'operand_to_operator'})
                    graph[operand_stack[-1]]['deps'].append({'head': i, 'dep': 'operator_to_operand', 'label': 'operator_to_operand'})
                if operator_stack and pos != 'PREP':
                    graph[i]['deps'].append({'head': operator_stack[-1], 'dep': 'operator_chain', 'label': 'operator_chain'})
                operator_stack.append(i)
                continue
            if tau > 0 or pos in SOURCE_POS:
                if pending_prep is not None:
                    graph[i]['deps'].append({'head': pending_prep, 'dep': 'prep_object', 'label': 'prepositional_object'})
                    graph[pending_prep]['deps'].append({'head': i, 'dep': 'prep_head', 'label': 'prepositional_head'})
                    pending_prep = None
                if operator_stack:
                    graph[i]['deps'].append({'head': operator_stack[-1], 'dep': 'verb_object', 'label': 'verb_object'})
                    graph[operator_stack[-1]]['deps'].append({'head': i, 'dep': 'verb_head', 'label': 'verb_head'})
                if operand_stack:
                    prev_op = operand_stack[-1]
                    prev_pos = tokens[prev_op]['pos']
                    if pos == 'ADJ' and prev_pos in ('NOUN', 'PROPN'):
                        graph[i]['deps'].append({'head': prev_op, 'dep': 'adj_to_noun', 'label': 'adjective_modifier'})
                    elif prev_pos == 'ADJ' and pos in ('NOUN', 'PROPN'):
                        graph[prev_op]['deps'].append({'head': i, 'dep': 'adj_to_noun', 'label': 'adjective_modifier'})
                    elif pos == prev_pos:
                        graph[i]['deps'].append({'head': prev_op, 'dep': 'enumeration', 'label': 'enumeration'})
                operand_stack.append(i)
                continue
        if question_node is not None and operand_stack:
            graph[question_node]['deps'].append({'head': operand_stack[-1], 'dep': 'question_to_object', 'label': 'question_to_object'})
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
# БЛОК 2: ФИЛЬТР
# ============================================================================

class StructuralFilter:
    def __init__(self):
        self.thresholds = THRESHOLDS

    def compute_L(self, graph: Dict) -> int:
        if not graph:
            return 0
        n = len(graph)
        if n > 50:
            max_degree = max((len(node['deps']) for node in graph.values()), default=0)
            return min(max_degree * 2, MAX_DFS_DEPTH)
        adj = defaultdict(set)
        for node_id, node_data in graph.items():
            for dep in node_data['deps']:
                adj[node_id].add(dep['head'])
        max_depth = 0
        nodes = list(graph.keys())
        sample_nodes = nodes if n <= 20 else nodes[:20]
        for start_node in sample_nodes:
            visited = {start_node}
            queue = [(start_node, 0)]
            while queue:
                current, depth = queue.pop(0)
                max_depth = max(max_depth, depth)
                if depth >= MAX_DFS_DEPTH:
                    continue
                for neighbor in adj[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))
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
            'L': L, 'E_flow': self.compute_E_flow(graph),
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
# БЛОК 3: ПОЛЕ СМЫСЛОВ
# ============================================================================

@dataclass
class Node:
    token: str; lemma: str; pos: str; tau: float
    H_sum: float = 0.0; frequency: int = 1; level: int = 0
    throughput_out: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    throughput_in: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    conductive_out: Set[str] = field(default_factory=set)
    conductive_in: Set[str] = field(default_factory=set)
    alternate_of: Optional[str] = None
    alternants: List[str] = field(default_factory=list)
    last_bifurcation_step: int = 0


class StructuralField:
    def __init__(self, debug_log: str = "problematic_texts.log"):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Tuple[str, str, str, float]] = []
        self.total_tokens = 0
        self.temperature = 0.3
        self.bifurcations_total = 0
        self.level_thresholds = [10, 100]
        self.total_steps = 0
        self.debug_log_path = debug_log
        self.dialog_log: List[Dict] = []
        self.error_count = 0
        self._asked_nodes: Set[str] = set()
        self.script_fragments: Dict[str, Dict] = {}
        with open(self.debug_log_path, 'w', encoding='utf-8') as f:
            f.write(f"=== Problematic texts log — {datetime.now()} ===\n\n")

    def _node_id(self, lemma: str, pos: str, level: int = 0) -> str:
        return f"{lemma}|{pos}|L{level}"

    def _log_problem(self, text: str, error: str):
        self.error_count += 1
        with open(self.debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Error #{self.error_count}\n")
            f.write(f"Text: {text[:200]}...\nError: {error}\n---\n")

    def _update_temperature(self, text_H_sum: float):
        self.temperature += text_H_sum * 0.01
        if self.temperature < TEMPERATURE_LOW:
            self.temperature = TEMPERATURE_LOW

    def _update_conductivity(self, node_id: str, target_id: str, direction: str = 'out'):
        node = self.nodes[node_id]
        if direction == 'out':
            if node.throughput_out[target_id] >= CONDUCTIVITY_THRESHOLD and target_id not in node.conductive_out:
                node.conductive_out.add(target_id)
                if target_id in self.nodes:
                    self.nodes[target_id].conductive_in.add(node_id)
        else:
            if node.throughput_in[target_id] >= CONDUCTIVITY_THRESHOLD and target_id not in node.conductive_in:
                node.conductive_in.add(target_id)
                if target_id in self.nodes:
                    self.nodes[target_id].conductive_out.add(node_id)

    def _try_bifurcate(self, global_id: str) -> Optional[str]:
        if self.temperature < TEMPERATURE_HIGH:
            return None
        node = self.nodes[global_id]
        if len(node.throughput_out) + len(node.throughput_in) < 5:
            return None
        if self.total_steps - node.last_bifurcation_step < 50:
            return None
        alt_id = f"{node.lemma}|{node.pos}|L{node.level}|alt{len(node.alternants)}"
        alternant = Node(
            token=f"¬{node.token}", lemma=f"¬{node.lemma}", pos=node.pos,
            tau=-node.tau, H_sum=node.H_sum * 0.5, frequency=0,
            level=node.level, alternate_of=global_id,
            last_bifurcation_step=self.total_steps
        )
        self.nodes[alt_id] = alternant
        node.alternants.append(alt_id)
        node.last_bifurcation_step = self.total_steps
        self.temperature -= BIFURCATION_ENERGY_COST
        self.bifurcations_total += 1
        return alt_id

    def _promote_level(self, global_id: str):
        node = self.nodes[global_id]
        if node.level >= SPIRAL_LEVELS - 1:
            return
        for lvl, threshold in enumerate(self.level_thresholds):
            if node.frequency >= threshold and node.level <= lvl:
                new_id = self._node_id(node.lemma, node.pos, lvl + 1)
                if new_id not in self.nodes:
                    self.nodes[new_id] = Node(
                        token=node.token, lemma=node.lemma, pos=node.pos,
                        tau=node.tau * 1.5, H_sum=node.H_sum * 2.0,
                        frequency=1, level=lvl + 1
                    )
                else:
                    self.nodes[new_id].frequency += 1
                node.level = lvl + 1

    def add_graph(self, parse_result: Dict, params: Dict):
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
                self.nodes[global_id] = Node(
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
                        self.nodes[u_global].throughput_out[v_global] += 1
                        self.nodes[v_global].throughput_in[u_global] += 1
                        self._update_conductivity(u_global, v_global, 'out')
                        self._update_conductivity(v_global, u_global, 'in')
                    else:
                        self.nodes[v_global].throughput_out[u_global] += 1
                        self.nodes[u_global].throughput_in[v_global] += 1
                        self._update_conductivity(v_global, u_global, 'out')
                        self._update_conductivity(u_global, v_global, 'in')
        self.total_tokens += parse_result['num_nodes']
        self.total_steps += 1
        fragment_id = f"script_{self.total_steps}"
        self.script_fragments[fragment_id] = {'tokens': tokens, 'graph': {k: v for k, v in graph.items()}}
        if len(self.script_fragments) > 10000:
            del self.script_fragments[min(self.script_fragments.keys())]
        if self.temperature >= TEMPERATURE_HIGH:
            for node_id in local_to_global.values():
                self._try_bifurcate(node_id)

    # ========================================================================
    # ЭНДОГЕННЫЙ ДИАЛОГ
    # ========================================================================

    def endogenous_dialog(self, parser, verbose: bool = True) -> Optional[Dict]:
        def is_contentful(node: Node) -> bool:
            if node.pos in NEUTRAL_POS: return False
            if len(node.token) <= 1 and not node.token.isalpha(): return False
            if node.pos in ('PREP', 'CONJ', 'SCONJ'): return False
            if not node.alternants: return False
            if node.frequency < 2: return False
            return True
        tense_nodes = []
        for nid, node in self.nodes.items():
            if is_contentful(node) and nid not in self._asked_nodes:
                score = len(node.throughput_out) + len(node.throughput_in) + len(node.alternants) * 10
                tense_nodes.append((nid, score, node))
        if not tense_nodes:
            self._asked_nodes.clear()
            for nid, node in self.nodes.items():
                if is_contentful(node):
                    score = len(node.throughput_out) + len(node.throughput_in) + len(node.alternants) * 10
                    tense_nodes.append((nid, score, node))
        if not tense_nodes:
            if verbose: print(f"\n🧠 ЭНДОГЕННЫЙ ДИАЛОГ: нет узлов с альтернантами")
            return None
        tense_nodes.sort(key=lambda x: x[1], reverse=True)
        target_id, score, node = tense_nodes[0]
        self._asked_nodes.add(target_id)
        q_words = ["Что такое {}", "Как работает {}", "Почему {} важен", "Откуда возникает {}", "Зачем нужен {}"]
        q_template = q_words[hash(target_id) % len(q_words)]
        question = q_template.format(node.token).rstrip('?') + '?'
        if verbose:
            print(f"\n🧠 ЭНДОГЕННЫЙ ДИАЛОГ")
            print(f"   Узел: «{node.token}» (τ={node.tau:.1f}, пропускная: {len(node.throughput_out)+len(node.throughput_in)}, "
                  f"альтернантов: {len(node.alternants)})")
            print(f"   Вопрос: «{question}»")
        try:
            query_parse = parser.parse(question)
            result = self.find_resonance_and_answer(query_parse, verbose=verbose)
            entry = {'question': question, 'node': node.token, 'tau': node.tau,
                     'temperature': round(self.temperature, 3),
                     'answer': result['answer'] if result else None}
            self.dialog_log.append(entry)
            return entry
        except Exception as e:
            if verbose: print(f"   ⚠️ Ошибка диалога: {e}")
            return None

    # ========================================================================
    # ПОИСК ОТВЕТА
    # ========================================================================

    def get_H_avg(self, global_id: str) -> float:
        node = self.nodes.get(global_id)
        if not node or node.frequency == 0: return 0.0
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
                    best_tau = tok['tau']; start_node = i
        if start_node is None:
            return None
        resonance_node, path, _ = find_resonance(H, graph, tokens, start_node)
        if resonance_node is None:
            return None
        resonance_tok = tokens[resonance_node]
        global_id = self._node_id(resonance_tok['lemma'], resonance_tok['pos'], 0)
        answer_text = self._find_script_fragment(query_parse)
        if not answer_text and len(path) > 1:
            answer_text = ' '.join([tokens[p]['text'] for p in path[1:] if tokens[p]['pos'] != 'PUNCT'])
        alternants_info = []
        if global_id in self.nodes and self.nodes[global_id].alternants:
            for aid in self.nodes[global_id].alternants[:2]:
                alternants_info.append(self.nodes[aid].token)
        result = {
            'found': True, 'resonance_node': global_id,
            'resonance_token': resonance_tok['text'],
            'resonance_H': H.get(resonance_node, 0.0),
            'resonance_tau': resonance_tok['tau'],
            'path': [tokens[p]['text'] for p in path], 'path_length': len(path),
            'answer': answer_text, 'alternants': alternants_info,
            'temperature': round(self.temperature, 3),
            'bifurcations_total': self.bifurcations_total
        }
        if verbose:
            print(f"   🎯 «{result['resonance_token']}» → «{result['answer']}»")
            if result['alternants']:
                print(f"   ¬ Альтернанты: {', '.join(result['alternants'])}")
        return result

    def _find_script_fragment(self, query_parse: Dict) -> str:
        tokens = query_parse['tokens']
        graph = query_parse['graph']
        question_lemmas = set()
        for node_id, node_data in graph.items():
            tok = tokens[node_id]
            if tok['pos'] not in NEUTRAL_POS and tok['pos'] not in ('PREP', 'CONJ', 'SCONJ', 'PUNCT'):
                question_lemmas.add(tok['lemma'])
        candidates = []
        for fragment_id, fragment in self.script_fragments.items():
            frag_tokens = fragment['tokens']
            frag_lemmas = set()
            for tok in frag_tokens:
                if tok['pos'] not in NEUTRAL_POS and tok['pos'] not in ('PREP', 'CONJ', 'SCONJ', 'PUNCT'):
                    frag_lemmas.add(tok['lemma'])
            overlap = question_lemmas & frag_lemmas
            if overlap:
                score = self._fragment_score(graph, tokens, fragment['graph'], frag_tokens, overlap)
                if score > 0:
                    candidates.append((fragment, score, len(overlap)))
        if not candidates:
            return ''
        candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        best_fragment = candidates[0][0]
        frag_tokens = best_fragment['tokens']
        frag_graph = best_fragment['graph']
        sorted_ids = sorted(frag_graph.keys())
        answer_tokens = [frag_tokens[sid]['text'] for sid in sorted_ids
                         if frag_tokens[sid]['pos'] != 'PUNCT' or frag_tokens[sid]['text'] in '.!?']
        result = ' '.join(answer_tokens)
        stop_tokens = {',', '.', '!', '?', '—', '-', 'и', 'в', 'на', 'с', 'не', 'же', 'бы', 'ли',
                      'то', 'что', 'как', 'а', 'но', 'или', 'это', 'для', 'от', 'к', 'по', 'из',
                      'у', 'за', 'до', 'при', 'без', 'над', 'под', 'об', 'во', 'ко', 'со'}
        cleaned = [t for t in result.split() if t.lower() not in stop_tokens and len(t) > 1]
        return ' '.join(cleaned)

    def _fragment_score(self, query_graph: Dict, query_tokens: List[Dict],
                        frag_graph: Dict, frag_tokens: List[Dict],
                        common_lemmas: Set[str]) -> float:
        total_score = 0.0; pairs = 0
        for lemma in common_lemmas:
            q_nodes = [nid for nid in query_graph if query_tokens[nid]['lemma'] == lemma]
            f_nodes = [nid for nid in frag_graph if frag_tokens[nid]['lemma'] == lemma]
            for qn in q_nodes:
                q_labels = set(dep['label'] for dep in query_graph[qn]['deps'])
                for fn in f_nodes:
                    f_labels = set(dep['label'] for dep in frag_graph[fn]['deps'])
                    if q_labels:
                        total_score += len(q_labels & f_labels) / len(q_labels)
                        pairs += 1
        return total_score / pairs if pairs > 0 else 0.0

    def get_stats(self) -> Dict:
        conductive_count = sum(1 for n in self.nodes.values() if n.conductive_out or n.conductive_in)
        alternants_total = sum(len(n.alternants) for n in self.nodes.values())
        level_counts = defaultdict(int)
        for n in self.nodes.values():
            level_counts[n.level] += 1
        return {
            'num_nodes': len(self.nodes), 'num_edges': len(self.edges),
            'total_tokens': self.total_tokens,
            'avg_H': sum(self.get_H_avg(nid) for nid in self.nodes) / max(1, len(self.nodes)),
            'temperature': round(self.temperature, 3),
            'bifurcations_total': self.bifurcations_total,
            'conductive_nodes': conductive_count,
            'alternants_total': alternants_total,
            'level_distribution': dict(level_counts),
            'errors': self.error_count,
            'dialog_entries': len(self.dialog_log),
            'script_fragments': len(self.script_fragments)
        }


# ============================================================================
# ГЛАВНЫЙ КЛАСС
# ============================================================================

class CleanField:
    def __init__(self):
        self.parser = StructuralParser()
        self.filter = StructuralFilter()
        self.field = StructuralField()
        self.processed = 0; self.filtered_out = 0; self.errors = 0

    def add_text(self, text: str) -> bool:
        try:
            parse_result = self.parser.parse(text)
        except Exception as e:
            self.errors += 1; self.field._log_problem(text, f"Parse: {e}"); return False
        if parse_result['num_nodes'] < 3:
            return False
        try:
            params = self.filter.compute_all(parse_result)
        except Exception as e:
            self.errors += 1; self.field._log_problem(text, f"Filter: {e}"); return False
        is_clean, _ = self.filter.is_clean(params)
        if is_clean:
            try:
                self.field.add_graph(parse_result, params)
                self.processed += 1
                if self.processed % 50 == 0:
                    stats = self.field.get_stats()
                    print(f"  ✓ [{self.processed}] T={stats['temperature']:.3f} "
                          f"бифуркаций={stats['bifurcations_total']} "
                          f"проводящих={stats['conductive_nodes']} "
                          f"фрагментов={stats['script_fragments']}")
                return True
            except Exception as e:
                self.errors += 1; self.field._log_problem(text, f"Add graph: {e}"); return False
        else:
            self.filtered_out += 1; return False

    def build(self, texts: List[str]):
        print(f"\n🌀 Строим поле v6.1 из {len(texts)} текстов...")
        print(f"   Стековый парсер + изоморфный поиск по леммам")
        for i, text in enumerate(texts):
            if len(text.strip()) < 15:
                continue
            self.add_text(text)
            if i % 500 == 0 and i > 0:
                stats = self.field.get_stats()
                print(f"  [{i}/{len(texts)}] +{self.processed} (отсев:{self.filtered_out}) "
                      f"T={stats['temperature']:.3f}")
                gc.collect()
            if self.processed > 0 and self.processed % ENDOGENOUS_DIALOG_INTERVAL == 0:
                self.field.endogenous_dialog(self.parser, verbose=True)
        print(f"\n✅ Готово. +{self.processed} -{self.filtered_out} ошибок:{self.errors}")
        stats = self.field.get_stats()
        print(f"📊 Поле: {stats['num_nodes']} узлов, {stats['num_edges']} рёбер, {stats['script_fragments']} фрагментов")
        print(f"   T={stats['temperature']:.3f} | Бифуркаций: {stats['bifurcations_total']}")

    def query(self, question: str) -> Optional[Dict]:
        print(f"\n❓ «{question}»")
        try:
            parse_result = self.parser.parse(question)
            params = self.filter.compute_all(parse_result)
            print(f"   Στ={params['total_tau']:.1f} | L={params['L']} | E={params['E_flow']:.2f}")
            return self.field.find_resonance_and_answer(parse_result)
        except Exception as e:
            print(f"   ⚠️ Ошибка: {e}")
            return {'found': False, 'error': str(e)}

    def run_endogenous_dialog(self, rounds: int = 3):
        print(f"\n🧠 ЭНДОГЕННЫЙ ДИАЛОГ ({rounds} раундов)")
        print("=" * 40)
        for _ in range(rounds):
            result = self.field.endogenous_dialog(self.parser, verbose=True)
            if result:
                print(f"   ↳ Ответ: «{result['answer']}»")
        print()


# ============================================================================
# СБОРКА КОРПУСА И ЗАПУСК
# ============================================================================

def collect_corpus(base_path: str = ".") -> List[str]:
    texts = []
    for pattern in ["discoveries/*.md", "brain_dump/**/*.md", "data/*.json", "*.md"]:
        for fpath in glob.glob(os.path.join(base_path, pattern), recursive=True):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    for s in re.split(r'[.!?]+', f.read()):
                        s = s.strip()
                        if 20 < len(s) < 500:
                            texts.append(s + '.')
            except Exception:
                pass
    return texts


def main():
    print("=" * 60)
    print("ЧИСТОЕ ПОЛЕ СМЫСЛОВ v6.1 — изоморфный поиск по леммам")
    print("Стековый парсер → фрагменты скриптов → ответ с общими словами")
    print("=" * 60)
    cf = CleanField()
    corpus = collect_corpus()
    print(f"\n📚 Корпус: {len(corpus)} текстов")
    cf.build(corpus)
    stats = cf.field.get_stats()
    print(f"\n⚠️  Поле готово: {stats['num_nodes']} узлов, {stats['script_fragments']} фрагментов")
    cf.run_endogenous_dialog(rounds=3)
    questions = [
        "Почему трава зелёная?", "Что такое резонанс?", "Как работает ПИД регулятор?",
        "Где находится ближайшая звезда?", "Зачем растениям нужен свет?",
        "Кто открыл закон всемирного тяготения?", "Почему вода кипит?",
        "Что такое топологический заряд?", "Как устроен атом?", "Откуда берётся ветер?",
        "Почему небо синее?", "Как работает двигатель?", "Что измеряет температура?",
        "Как работает фотосинтез?", "Что такое гравитация?", "Почему лёд плавает?",
    ]
    print("\n" + "=" * 60 + "\n🔍 ВНЕШНИЕ ЗАПРОСЫ\n" + "=" * 60)
    results = [(q, cf.query(q)) for q in questions]
    print("\n" + "=" * 60 + "\n📋 СВОДКА\n" + "=" * 60)
    found = sum(1 for _, r in results if r and r.get('found'))
    print(f"Найдено ответов: {found}/{len(questions)}")
    for q, r in results:
        print(f"  {'✓' if (r and r.get('found')) else '✗'} «{q}» → «{r.get('answer', '—') if r else '—'}»")


if __name__ == "__main__":
    main()