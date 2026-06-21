#!/usr/bin/env python3
"""
clean_field_v10.4.py — Чистое поле смыслов. Версия 10.4
Глаголический синтез: ответ как траектория по полю H через TEES-паттерны.
"""

import re
import glob
import os
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# ============================================================================
# TEES-ГРАММАТИКА v3.9 (ядро)
# ============================================================================

class ModeRole(Enum):
    SOURCE = "source"
    RECEIVER = "receiver"
    AFTER_ROUTER = "router"

@dataclass
class ExchangePattern:
    source_ending: str
    receiver_ending: str
    router: Optional[str]
    carriers: Counter
    examples: List[Tuple[str, str, str]]
    count: int

@dataclass
class TransformationRule:
    role: ModeRole
    router: Optional[str]
    old_ending: str
    new_ending: str
    examples: List[Tuple[str, str]]
    confidence: float

class TEESGrammar:
    def __init__(self):
        self.lemma_forms: Dict[str, List[Tuple[str, ModeRole, Optional[str]]]] = defaultdict(list)
        self.surface_to_lemma: Dict[str, str] = {}
        self.lemmas: set = set()
        self.exchange_records: List[Tuple[str, str, str, str, Optional[str]]] = []
        self.rules: List[TransformationRule] = []
        self.exchange_patterns: List[ExchangePattern] = []
        
        self.known_routers = {
            'в', 'во', 'на', 'с', 'со', 'к', 'ко', 'по', 'из', 'от', 'для', 'без',
            'над', 'под', 'об', 'обо', 'при', 'за', 'до', 'через', 'между', 'перед',
            'о', 'у', 'около', 'вокруг', 'после', 'про', 'ради', 'сквозь', 'вдоль',
        }
        
        self.non_verbs = {
            'и', 'или', 'либо', 'а', 'но', 'да', 'что', 'как', 'это', 'так', 'же',
            'бы', 'ли', 'то', 'всё', 'все', 'сам', 'если', 'когда', 'пока', 'чтобы',
            'хотя', 'ведь', 'раз', 'почти', 'более', 'менее', 'очень', 'весьма',
            'совсем', 'вполне', 'даже', 'именно', 'просто', 'ровно', 'примерно',
            'есть', 'нет', 'можно', 'нужно', 'надо', 'нельзя', 'возможно',
            'всегда', 'никогда', 'часто', 'редко', 'обычно', 'иногда', 'вдруг',
            'наконец', 'снова', 'опять', 'теперь', 'тогда', 'потом', 'уже', 'ещё',
            'только', 'лишь', 'вот', 'вон', 'там', 'здесь', 'тут', 'где', 'куда',
            'откуда', 'почему', 'зачем', 'сколько', 'насколько',
            'он', 'она', 'оно', 'они', 'я', 'ты', 'мы', 'вы', 'его', 'её', 'их',
            'мой', 'твой', 'наш', 'ваш', 'свой', 'весь', 'тот', 'этот', 'такой',
            'который', 'кто', 'чей', 'какой', 'каков', 'нибудь', 'либо',
            'сущность', 'плотность', 'поверхность', 'закономерность', 'интенсивность',
            'способность', 'точность', 'воспроизводимость', 'принадлежность',
            'эксперимент', 'обжим', 'статус', 'модель', 'узел', 'цикл',
        }
        
        self.MIN_STEM_LEN = 2
        self.MIN_EXCHANGE_COUNT = 3
        self.MIN_RULE_COUNT = 2

    def is_router(self, word: str) -> bool:
        return word.lower() in self.known_routers

    def is_verb(self, word: str) -> bool:
        w = word.lower()
        if w in self.non_verbs:
            return False
        if len(w) <= 2:
            return False
        if w.endswith('ться'):
            return True
        if w.endswith('ть') and len(w) >= 4:
            if w.endswith('ость') or w.endswith('есть') or w.endswith('асть'):
                return False
            return True
        if re.search(r'(л|ла|ло|ли|лся|лась|лось|лись)$', w):
            return True
        if re.search(r'(ет|ёт|ит|ют|ут|ят|ат)$', w) and len(w) >= 3:
            return True
        if w.endswith(('ется', 'ётся', 'ются', 'тся')):
            return True
        if len(w) >= 7:
            if re.search(r'(ющий|ющийся|вший|вшийся|енный|анный|имый|емый|омый|ащий|ящий|ущий)$', w):
                return True
        if re.search(r'(ен|ан|т|ят|ут)$', w) and len(w) >= 5:
            if w.endswith(('мент', 'тант', 'гент', 'кент')):
                return False
            return True
        return False

    def is_noun(self, word: str) -> bool:
        w = word.lower()
        if self.is_verb(w) or self.is_router(w) or w in self.non_verbs:
            return False
        if w.isupper() and len(w) <= 5:
            return False
        if re.search(r'\d', w):
            return False
        return len(w) > 2

    def _longest_common_prefix(self, a: str, b: str) -> str:
        min_len = min(len(a), len(b))
        for i in range(min_len, 0, -1):
            if a[:i] == b[:i]:
                return a[:i]
        return ""

    def _word_ending(self, word: str) -> str:
        if len(word) >= 2:
            return word[-2:]
        elif len(word) == 1:
            return word
        return '-'

    def analyze_sentence(self, text: str):
        words = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', text)
        if len(words) < 3:
            return

        for i in range(len(words) - 2):
            w1 = words[i].lower()
            w2 = words[i+1].lower()
            w3 = words[i+2].lower()

            if not self.is_verb(w2):
                continue
            if not self.is_noun(w1):
                continue

            router = None
            w3_idx = i + 2
            if self.is_router(w3):
                router = w3
                if w3_idx + 1 < len(words):
                    w3_idx += 1
                    w3 = words[w3_idx].lower()
                else:
                    continue

            if not self.is_noun(w3):
                continue

            self.lemmas.add(w1)
            receiver_role = ModeRole.AFTER_ROUTER if router else ModeRole.RECEIVER

            self.lemma_forms[w1].append((w1, ModeRole.SOURCE, None))
            self.lemma_forms[w1].append((w3, receiver_role, router))

            common = self._longest_common_prefix(w1, w3)
            if len(common) >= self.MIN_STEM_LEN and len(common) >= len(w3) * 0.4:
                self.surface_to_lemma[w3] = w1

            self.exchange_records.append((w1, w2, w3, w1, router))

    def process_corpus(self, texts: List[str]):
        for text in texts:
            sentences = re.split(r'[.!?]+', text)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 10:
                    self.analyze_sentence(sent)

    def discover_rules(self):
        raw = defaultdict(lambda: {'count': 0, 'examples': []})

        for lemma, forms in self.lemma_forms.items():
            source_form = None
            for surface, role, router in forms:
                if role == ModeRole.SOURCE:
                    source_form = surface
                    break
            if source_form is None:
                continue

            for surface, role, router in forms:
                if role == ModeRole.SOURCE or surface == source_form:
                    continue

                common = self._longest_common_prefix(source_form, surface)
                if len(common) < self.MIN_STEM_LEN:
                    continue
                if len(common) < len(surface) * 0.4:
                    continue

                old_end = source_form[len(common):]
                new_end = surface[len(common):]
                if old_end == new_end:
                    continue
                if len(old_end) > len(common) or len(new_end) > len(common):
                    continue

                key = (role, router, old_end, new_end)
                raw[key]['count'] += 1
                raw[key]['examples'].append((source_form, surface))

        self.rules = []
        for (role, router, old_end, new_end), data in raw.items():
            if data['count'] >= self.MIN_RULE_COUNT:
                unique_lemmas = set(src for src, _ in data['examples'])
                if len(unique_lemmas) >= 2:
                    self.rules.append(TransformationRule(
                        role=role, router=router,
                        old_ending=old_end, new_ending=new_end,
                        examples=data['examples'][:5],
                        confidence=data['count'] / max(1, len(self.lemmas)),
                    ))

        self.rules.sort(key=lambda r: (r.confidence, len(r.old_ending)), reverse=True)

        filtered = []
        for rule in self.rules:
            redundant = any(
                existing.role == rule.role and
                existing.router == rule.router and
                existing.old_ending.endswith(rule.old_ending) and
                existing.new_ending == rule.new_ending and
                existing.confidence >= rule.confidence
                for existing in filtered
            )
            if not redundant:
                filtered.append(rule)
        self.rules = filtered

    def discover_exchanges(self):
        raw_patterns = defaultdict(lambda: {'carriers': Counter(), 'examples': [], 'count': 0})

        for src_surface, carrier, recv_surface, src_lemma, router in self.exchange_records:
            src_end = self._word_ending(src_surface)
            recv_end = self._word_ending(recv_surface)

            key = (src_end, recv_end, router)
            raw_patterns[key]['carriers'][carrier] += 1
            raw_patterns[key]['examples'].append((src_surface, carrier, recv_surface))
            raw_patterns[key]['count'] += 1

        self.exchange_patterns = []
        for (src_end, recv_end, router), data in raw_patterns.items():
            if data['count'] >= self.MIN_EXCHANGE_COUNT:
                carriers = Counter({k: v for k, v in data['carriers'].items() if v >= 2})
                if len(carriers) >= 1:
                    self.exchange_patterns.append(ExchangePattern(
                        source_ending=src_end,
                        receiver_ending=recv_end,
                        router=router,
                        carriers=carriers,
                        examples=data['examples'][:5],
                        count=data['count'],
                    ))

        self.exchange_patterns.sort(key=lambda p: p.count, reverse=True)

    def apply_rules(self, lemma: str, role: ModeRole, router: Optional[str] = None) -> str:
        if role == ModeRole.SOURCE:
            return lemma

        best_rule = None
        best_old_len = 0

        for rule in self.rules:
            if rule.role != role:
                continue
            if rule.router != router and rule.router is not None and router is not None:
                continue
            if lemma.endswith(rule.old_ending):
                if len(rule.old_ending) > best_old_len:
                    best_old_len = len(rule.old_ending)
                    best_rule = rule

        if best_rule:
            return lemma[:-len(best_rule.old_ending)] + best_rule.new_ending

        for rule in self.rules:
            if rule.role == role and lemma.endswith(rule.old_ending):
                return lemma[:-len(rule.old_ending)] + rule.new_ending

        return lemma

    def find_carrier(self, lemma_a: str, lemma_b: str) -> Optional[Tuple[str, Optional[str]]]:
        end_a = self._word_ending(lemma_a)
        end_b = self._word_ending(lemma_b)

        for pattern in self.exchange_patterns:
            if pattern.source_ending == end_a and pattern.receiver_ending == end_b:
                carrier = pattern.carriers.most_common(1)[0][0]
                return (carrier, pattern.router)

        for pattern in self.exchange_patterns:
            if pattern.source_ending == end_a:
                carrier = pattern.carriers.most_common(1)[0][0]
                return (carrier, pattern.router)

        all_carriers = Counter()
        for pattern in self.exchange_patterns:
            all_carriers.update(pattern.carriers)

        if all_carriers:
            carrier = all_carriers.most_common(1)[0][0]
            return (carrier, None)

        return None

    def assemble(self, lemma_a: str, lemma_b: str) -> Optional[str]:
        found = self.find_carrier(lemma_a, lemma_b)
        if not found:
            return None

        carrier, router = found
        receiver_role = ModeRole.AFTER_ROUTER if router else ModeRole.RECEIVER

        source_form = self.apply_rules(lemma_a, ModeRole.SOURCE)
        receiver_form = self.apply_rules(lemma_b, receiver_role, router)

        parts = [source_form.capitalize(), carrier]
        if router:
            parts.append(router)
        parts.append(receiver_form)

        return ' '.join(parts) + '.'

# ============================================================================
# СТОП-СЛОВА
# ============================================================================

STOP_WORDS = {
    'что', 'как', 'почему', 'где', 'когда', 'кто', 'зачем', 'откуда', 'куда',
    'это', 'такое', 'так', 'же', 'бы', 'ли', 'то', 'в', 'на', 'с', 'к', 'у',
    'о', 'за', 'по', 'из', 'от', 'не', 'но', 'а', 'и', 'для', 'при', 'без',
    'над', 'под', 'об', 'во', 'ко', 'со', 'до', 'или', 'есть', 'быть',
    'какой', 'какая', 'какое', 'какие', 'чей', 'который', 'сколько',
}

# ============================================================================
# УЗЕЛ
# ============================================================================

@dataclass
class Node:
    token: str
    lemma: str
    frequency: int = 1
    charge: int = 0

# ============================================================================
# ПОЛЕ v10.4
# ============================================================================

class StructuralField:
    """Поле смыслов v10.4: Глаголический синтез — ответ как траектория по полю H."""
    
    def __init__(self, debug_log: str = "field_v10.log"):
        self.nodes: Dict[str, Node] = {}
        self.fragments: List[Dict] = []
        self.total_texts = 0
        self.links: Dict[Tuple[str, str], int] = defaultdict(int)
        self.clusters: List[Dict] = []
        self.MATCH_THRESHOLD = 0.6
        
        # TEES-грамматика
        self.grammar = TEESGrammar()
        self.grammar_loaded = False
        
        with open(debug_log, 'w', encoding='utf-8') as f:
            f.write(f"=== v10.4 log — {datetime.now()} ===\n\n")

    # ========================================================================
    # ОБЩИЕ МЕТОДЫ
    # ========================================================================

    def _node_id(self, lemma: str) -> str:
        return lemma

    def _get_or_create_node(self, word: str) -> Node:
        lemma = word.lower()
        node_id = self._node_id(lemma)
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(token=word, lemma=lemma)
        else:
            self.nodes[node_id].frequency += 1
        return self.nodes[node_id]

    def _word_charge(self, word: str) -> int:
        total = 0
        for ch in word.lower():
            if 'а' <= ch <= 'я':
                total += ord(ch) - ord('а') + 1
            elif 'a' <= ch <= 'z':
                total += ord(ch) - ord('a') + 1
        return total

    def _get_significant_words(self, text: str) -> List[str]:
        words = re.findall(r'[а-яёa-z]+', text.lower())
        return [w for w in words if w not in STOP_WORDS]

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'[»«→]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # ========================================================================
    # ЗАГРУЗКА ГРАММАТИКИ
    # ========================================================================

    def load_grammar(self, texts: List[str]):
        print("\n📚 Обучение TEES-грамматики (Глаголица)...")
        self.grammar.process_corpus(texts)
        self.grammar.discover_rules()
        self.grammar.discover_exchanges()
        self.grammar_loaded = True
        print(f"   Правил склонения: {len(self.grammar.rules)}")
        print(f"   Обменных паттернов: {len(self.grammar.exchange_patterns)}")

    # ========================================================================
    # ДОБАВЛЕНИЕ ТЕКСТА
    # ========================================================================

    def add_text(self, text: str) -> bool:
        words = re.findall(r'[а-яёa-z]+', text.lower())
        if len(words) < 3:
            return False

        fragment = {
            'id': self.total_texts,
            'words': [],
            'original': text,
        }
        for word in words:
            node = self._get_or_create_node(word)
            fragment['words'].append(node.lemma)
        self.fragments.append(fragment)

        for i in range(len(words) - 1):
            pair = (words[i], words[i+1])
            self.links[pair] += 1
            self.links[(words[i+1], words[i])] += 1

        cluster = {
            'id': self.total_texts,
            'words': words,
            'links': [(words[i], words[i+1]) for i in range(len(words)-1)],
            'original': text,
        }
        self.clusters.append(cluster)

        self.total_texts += 1
        return True

    # ========================================================================
    # ТОЧНЫЙ ПОИСК
    # ========================================================================

    def _exact_search(self, question: str) -> Optional[str]:
        question_words = self._get_significant_words(question)
        if not question_words:
            return None

        best_fragment = None
        best_score = 0.0

        for fragment in self.fragments:
            fragment_words = set(fragment['words'])
            matches = sum(1 for w in question_words if w in fragment_words)
            score = matches / len(question_words) if question_words else 0
            
            if score > best_score:
                best_score = score
                best_fragment = fragment

        if best_fragment and best_score >= self.MATCH_THRESHOLD:
            return self._clean_text(best_fragment['original'])
        
        return None

    # ========================================================================
    # ГЛАГОЛИЧЕСКИЙ СИНТЕЗ — ТРАЕКТОРИЯ ПО ПОЛЮ H
    # ========================================================================

    def _synthesize_glagolitic(self, question: str) -> Optional[str]:
        """
        Синтез как прокладка траектории по полю H через TEES-паттерны.
        """
        significant = self._get_significant_words(question)
        if not significant:
            return None

        # 1. Находим все кластеры, где есть слова вопроса
        first_word = significant[0]
        candidates = [c for c in self.clusters if first_word in c['words']]

        if not candidates:
            charge = self._word_charge(first_word)
            similar_words = []
            for word, node in self.nodes.items():
                if node.charge == charge and word != first_word:
                    similar_words.append(word)
            for sw in similar_words:
                candidates.extend([c for c in self.clusters if sw in c['words']])

        if not candidates:
            return None

        # 2. Сужаем по остальным словам
        for word in significant[1:]:
            if len(candidates) <= 1:
                break
            filtered = [c for c in candidates if word in c['words']]
            if filtered:
                candidates = filtered

        if not candidates:
            return None

        # 3. Выбираем кластер с наибольшей плотностью связей
        if len(candidates) > 1:
            candidates.sort(key=lambda c: self._cluster_link_density(c, significant), reverse=True)

        best_cluster = candidates[0]
        cluster_words = best_cluster['words']

        # 4. Строим траекторию: от первого значимого слова к последнему
        #    через TEES-паттерны (как маршруты)
        source = significant[0]
        target = significant[-1] if len(significant) > 1 else source

        # Проверяем, есть ли source и target в кластере
        if source not in cluster_words:
            # Ищем ближайшее по связям
            best_word = None
            best_strength = 0
            for word in cluster_words:
                strength = self.links.get((source, word), 0) + self.links.get((word, source), 0)
                if strength > best_strength:
                    best_strength = strength
                    best_word = word
            if best_word:
                source = best_word

        if target not in cluster_words:
            best_word = None
            best_strength = 0
            for word in cluster_words:
                strength = self.links.get((target, word), 0) + self.links.get((word, target), 0)
                if strength > best_strength:
                    best_strength = strength
                    best_word = word
            if best_word:
                target = best_word

        # 5. Пытаемся применить TEES-грамматику (Глаголица)
        if self.grammar_loaded:
            # Ищем carrier (глагол/связку) через паттерны обмена
            result = self.grammar.assemble(source, target)
            if result:
                return result

        # 6. Если грамматика не сработала — строим простую траекторию
        #    через самые сильные связи в кластере
        return self._reconstruct_trajectory(cluster_words, source, target)

    def _reconstruct_trajectory(self, cluster_words: List[str], source: str, target: str) -> str:
        """Строит траекторию от источника к приёмнику через сильные связи."""
        if source not in cluster_words or target not in cluster_words:
            return ' '.join(cluster_words[:5])

        visited = {source}
        trajectory = [source]
        current = source
        word_set = set(cluster_words)

        # Идём от источника к приёмнику
        while current != target and len(visited) < len(cluster_words):
            best_next = None
            best_strength = 0
            for word in word_set:
                if word not in visited:
                    strength = self.links.get((current, word), 0)
                    if strength > best_strength:
                        best_strength = strength
                        best_next = word

            if best_next is None:
                break

            visited.add(best_next)
            trajectory.append(best_next)
            current = best_next

        # Если дошли до цели — добавляем её
        if current != target and target not in visited:
            trajectory.append(target)

        return ' '.join(trajectory[:5])  # Ограничиваем длину

    def _cluster_link_density(self, cluster: Dict, question_words: List[str]) -> float:
        score = 0.0
        cluster_words = set(cluster['words'])
        for qw in question_words:
            if qw in cluster_words:
                for other in question_words:
                    if other != qw and other in cluster_words:
                        if self.links.get((qw, other), 0) > 0:
                            score += 1.0
        return score

    # ========================================================================
    # ЗАПРОС
    # ========================================================================

    def query(self, question: str) -> Optional[str]:
        print(f"\n❓ «{question}»")

        # 1. Точный поиск
        exact = self._exact_search(question)
        if exact:
            print(f"   📋 [ЦИТАТА] Найдено (порог {int(self.MATCH_THRESHOLD*100)}%)")
            print(f"   💬 {exact}")
            return f"[ЦИТАТА] {exact}"

        # 2. Глаголический синтез
        synthesized = self._synthesize_glagolitic(question)
        if synthesized:
            print(f"   📋 [СИНТЕЗ] Ответ как траектория по полю H (Глаголица)")
            print(f"   💬 {synthesized}")
            return f"[СИНТЕЗ] {synthesized}"

        print("   ✗ Нет ответа")
        return None

    # ========================================================================
    # СТАТИСТИКА
    # ========================================================================

    def get_stats(self) -> Dict:
        return {
            'num_nodes': len(self.nodes),
            'num_fragments': len(self.fragments),
            'num_clusters': len(self.clusters),
            'num_links': len(self.links),
            'total_texts': self.total_texts,
            'grammar_rules': len(self.grammar.rules) if self.grammar_loaded else 0,
            'grammar_patterns': len(self.grammar.exchange_patterns) if self.grammar_loaded else 0,
        }

# ============================================================================
# СБОРКА КОРПУСА
# ============================================================================

def collect_corpus(base_path: str = ".") -> List[str]:
    texts = []
    patterns = [
        "discoveries/*.md",
        "brain_dump/**/*.md",
        "predictions/*.md",
        "*.md",
        "*.txt"
    ]
    
    EXCLUDE_MARKERS = [
        '❓', '💬', '📋', '⚡', '→', '»', '«',
        'Альтернативы:', 'Ответ:', 'Синтез', 'Цитата',
        '---', '##', '**', '|', '```',
        'pressure_force_', 'ЭКЗОРЦИЗМ', 'ПИД', 'Вселенная вечный двигатель'
    ]
    
    for pattern in patterns:
        for fpath in glob.glob(os.path.join(base_path, pattern), recursive=True):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    sentences = re.split(r'[.!?]+', content)
                    for s in sentences:
                        s = s.strip()
                        if len(s) < 15:
                            continue
                        if any(marker in s for marker in EXCLUDE_MARKERS):
                            continue
                        texts.append(s + '.')
            except Exception:
                pass
    
    return texts

# ============================================================================
# ЗАПУСК
# ============================================================================

def main():
    print("=" * 60)
    print("ЧИСТОЕ ПОЛЕ СМЫСЛОВ v10.4")
    print("Точный поиск + Глаголический синтез (траектория по полю H)")
    print("=" * 60)

    field = StructuralField()

    corpus = collect_corpus()
    print(f"\n📚 Корпус: {len(corpus)} текстов (после фильтрации)")

    # Обучаем грамматику
    field.load_grammar(corpus)

    print("\n🌀 Строим поле...")
    for i, text in enumerate(corpus):
        field.add_text(text)
        if i % 100 == 0 and i > 0:
            stats = field.get_stats()
            print(f"  [{i}] фрагментов:{stats['num_fragments']}")

    stats = field.get_stats()
    print(f"\n✅ Поле готово: {stats['num_nodes']} узлов, {stats['num_fragments']} фрагментов, {stats['num_links']} связей")
    print(f"   Глаголица: {stats['grammar_rules']} правил, {stats['grammar_patterns']} паттернов")

    questions = [
        "Почему трава зелёная?",
        "Что такое резонанс?",
        "Как работает двигатель?",
        "Почему вода кипит?",
        "Что измеряет температура?",
        "Почему лёд плавает?",
        "Что такое фотосинтез?",
        "Как устроен атом?",
        "Откуда берётся ветер?",
        "Что такое гравитация?",
    ]

    print("\n" + "=" * 60)
    print("🔍 ЗАПРОСЫ")
    print("=" * 60)

    for q in questions:
        field.query(q)

if __name__ == "__main__":
    main()