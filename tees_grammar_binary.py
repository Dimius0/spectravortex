#!/usr/bin/env python3
"""
tees_grammar_binary.py — TEES-грамматика для бинарных данных v2.0
Адаптация tees_grammar_v3.9 для n-грамм с расширенной аналитикой.
"""

import re
import os
import glob
import struct
import hashlib
import numpy as np
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import json

# ============================================================================
# СУЩНОСТИ
# ============================================================================

class ModeRole(Enum):
    SOURCE = "source"
    RECEIVER = "receiver"
    AFTER_ROUTER = "router"
    ISOLATED = "isolated"

class DataNature(Enum):
    TEXT = "text"
    BINARY = "binary"
    ENCRYPTED = "encrypted"
    COMPRESSED = "compressed"
    HASH = "hash"
    UNKNOWN = "unknown"

@dataclass
class ExchangePattern:
    source_ending: bytes
    receiver_ending: bytes
    router: Optional[bytes]
    carriers: Counter
    examples: List[Tuple[bytes, bytes, bytes]]
    count: int
    confidence: float = 0.0
    
@dataclass
class TransformationRule:
    role: ModeRole
    router: Optional[bytes]
    old_ending: bytes
    new_ending: bytes
    examples: List[Tuple[bytes, bytes]]
    confidence: float
    
@dataclass
class GrammarStats:
    """Статистика грамматики."""
    total_lemmas: int = 0
    total_exchanges: int = 0
    total_rules: int = 0
    total_patterns: int = 0
    entropy: float = 0.0
    data_nature: DataNature = DataNature.UNKNOWN
    complexity_score: float = 0.0
    structure_index: float = 0.0  # 0 = случайные, 1 = строго структурированные

# ============================================================================
# БИНАРНЫЙ АНАЛИЗАТОР (УЛУЧШЕННЫЙ)
# ============================================================================

class BinaryTEESAnalyzer:
    """
    TEES-анализ бинарных данных через n-граммы.
    Версия 2.0 с автоопределением природы данных и многопоточной обработкой.
    """
    
    def __init__(self, n: int = None, min_ending_len: int = 2,
                 min_pattern_count: int = 3, overlap: bool = True,
                 auto_configure: bool = True):
        self.n = n
        self.min_ending_len = min_ending_len
        self.min_pattern_count = min_pattern_count
        self.overlap = overlap
        self.auto_configure = auto_configure
        
        # Хранилище
        self.lemma_forms: Dict[bytes, List[Tuple[bytes, ModeRole, Optional[bytes]]]] = defaultdict(list)
        self.surface_to_lemma: Dict[bytes, bytes] = {}
        self.lemmas: Set[bytes] = set()
        self.exchange_records: List[Tuple[bytes, bytes, bytes, bytes, Optional[bytes]]] = []
        self.rules: List[TransformationRule] = []
        self.exchange_patterns: List[ExchangePattern] = []
        self.stats = GrammarStats()
        
        # Кэш
        self._gram_cache: Dict[bytes, bytes] = {}
        self._entropy_cache: Dict[int, float] = {}
        
        # Расширенные роутеры (частые бинарные маркеры)
        self.known_routers = {
            # Null-паттерны
            b'\x00\x00', b'\x00\x00\x00\x00', b'\xff\xff', b'\xff\xff\xff\xff',
            # Управляющие последовательности
            b'\x00\x01', b'\x01\x00', b'\x0a\x0d', b'\x0d\x0a',
            # Пробельные символы
            b'\x20\x20', b'\x00\x20', b'\x20\x00', b'\x09\x20',
            # Маркеры форматов
            b'\x89PNG', b'\xff\xd8\xff', b'%PDF', b'PK\x03\x04',
            # Сетевые маркеры
            b'\x00\x00\x00\x01', b'\x00\x00\x00\x02',
        }
        
        # Автоконфигурация при необходимости
        if auto_configure and n is None:
            self._auto_n = True
        else:
            self._auto_n = False
    
    # ========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================================================
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Вычисляет энтропию Шеннона для данных."""
        if not data:
            return 0.0
        
        # Кэшируем для производительности
        data_hash = hash(data)
        if data_hash in self._entropy_cache:
            return self._entropy_cache[data_hash]
        
        byte_counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
        byte_probs = byte_counts[byte_counts > 0] / len(data)
        entropy = -np.sum(byte_probs * np.log2(byte_probs))
        
        self._entropy_cache[data_hash] = entropy
        return entropy
    
    def _determine_data_nature(self, data: bytes) -> DataNature:
        """Определяет природу данных на основе энтропии и паттернов."""
        entropy = self._calculate_entropy(data)
        
        if entropy < 3.5:
            return DataNature.TEXT
        elif entropy < 5.0:
            return DataNature.BINARY
        elif entropy < 7.0:
            return DataNature.COMPRESSED
        elif entropy < 7.8:
            return DataNature.ENCRYPTED
        else:
            return DataNature.HASH
    
    def _auto_configure_n(self, data: bytes) -> int:
        """Автоматически подбирает оптимальный размер n-граммы."""
        nature = self._determine_data_nature(data)
        entropy = self._calculate_entropy(data)
        
        optimal_n = {
            DataNature.TEXT: min(4, len(data) // 100),
            DataNature.BINARY: min(8, len(data) // 50),
            DataNature.COMPRESSED: min(16, len(data) // 20),
            DataNature.ENCRYPTED: min(32, len(data) // 10),
            DataNature.HASH: min(64, len(data) // 5),
        }.get(nature, 8)
        
        return max(2, optimal_n)
    
    def _ngrams(self, data: bytes) -> List[bytes]:
        """Извлекает n-граммы с оптимизацией."""
        if len(data) < self.n:
            return []
        
        if self.overlap:
            # Оптимизированное извлечение через numpy
            arr = np.frombuffer(data, dtype=np.uint8)
            return [bytes(arr[i:i+self.n]) for i in range(len(arr) - self.n + 1)]
        else:
            return [data[i:i+self.n] for i in range(0, len(data) - self.n + 1, self.n)]
    
    def _longest_common_prefix(self, a: bytes, b: bytes) -> bytes:
        """Эффективный поиск общего префикса."""
        min_len = min(len(a), len(b))
        # Бинарный поиск для длинных последовательностей
        if min_len > 8:
            low, high = 0, min_len
            while low < high:
                mid = (low + high + 1) // 2
                if a[:mid] == b[:mid]:
                    low = mid
                else:
                    high = mid - 1
            return a[:low]
        else:
            for i in range(min_len, 0, -1):
                if a[:i] == b[:i]:
                    return a[:i]
            return b''
    
    def _ending(self, gram: bytes) -> bytes:
        """Возвращает «окончание» n-граммы с кэшированием."""
        if gram in self._gram_cache:
            return self._gram_cache[gram]
        
        if len(gram) >= self.min_ending_len:
            result = gram[-self.min_ending_len:]
        elif len(gram) == 1:
            result = gram
        else:
            result = b'-'
        
        self._gram_cache[gram] = result
        return result
    
    def _is_router(self, gram: bytes) -> bool:
        """Проверяет, является ли n-грамма «роутером»."""
        if gram in self.known_routers:
            return True
        
        # Эвристика: роутеры часто имеют низкую энтропию
        if len(gram) <= 2:
            entropy = self._calculate_entropy(gram)
            return entropy < 1.0
        
        return False
    
    def _is_carrier(self, gram: bytes) -> bool:
        """Проверяет, является ли n-грамма «носителем»."""
        # Носитель — мост между контекстами
        if self._is_router(gram):
            return False
        
        # Эвристика: носители имеют среднюю энтропию
        if len(gram) >= self.n // 2:
            entropy = self._calculate_entropy(gram)
            return 2.0 < entropy < 6.0
        
        return False
    
    # ========================================================================
    # АНАЛИЗ (УЛУЧШЕННЫЙ)
    # ========================================================================
    
    def analyze_bytes(self, data: bytes) -> int:
        """Анализирует байтовые данные и извлекает обменные паттерны."""
        
        # Автоконфигурация при первом запуске
        if self._auto_n and self.n is None:
            self.n = self._auto_configure_n(data)
        
        grams = self._ngrams(data)
        if len(grams) < 3:
            return 0
        
        count = 0
        unique_pairs = set()  # Для фильтрации дубликатов
        
        # Ищем тройки: [источник] [носитель] [приёмник]
        for i in range(len(grams) - 2):
            g1 = grams[i]
            g2 = grams[i+1]
            g3 = grams[i+2]
            
            # Пропускаем одинаковые
            if g1 == g2 == g3:
                continue
            
            # Проверяем carrier
            if not self._is_carrier(g2):
                continue
            
            # Проверяем, что источник и приёмник связаны
            common = self._longest_common_prefix(g1, g3)
            if len(common) < max(2, self.n // 3):
                continue
            
            # Фильтруем дубликаты
            pair_key = (g1, g2, g3)
            if pair_key in unique_pairs:
                continue
            unique_pairs.add(pair_key)
            
            # Определяем роутер
            router = g2 if self._is_router(g2) else None
            
            # Сохраняем
            self.lemmas.add(g1)
            receiver_role = ModeRole.AFTER_ROUTER if router else ModeRole.RECEIVER
            
            self.lemma_forms[g1].append((g1, ModeRole.SOURCE, None))
            self.lemma_forms[g1].append((g3, receiver_role, router))
            
            if len(common) >= self.n // 2:
                self.surface_to_lemma[g3] = g1
            
            self.exchange_records.append((g1, g2, g3, g1, router))
            count += 1
        
        # Обновляем статистику
        self.stats.total_lemmas = len(self.lemmas)
        self.stats.total_exchanges = count
        self.stats.entropy = self._calculate_entropy(data)
        self.stats.data_nature = self._determine_data_nature(data)
        self.stats.structure_index = self._calculate_structure_index()
        
        return count
    
    def _calculate_structure_index(self) -> float:
        """Вычисляет индекс структурированности данных."""
        if not self.lemmas:
            return 0.0
        
        # Отношение уникальных лемм к общему числу обменов
        lemma_ratio = len(self.lemmas) / max(1, self.stats.total_exchanges)
        
        # Средняя частота использования лемм
        avg_freq = self.stats.total_exchanges / max(1, len(self.lemmas))
        
        # Индекс структурированности (0 = хаос, 1 = строгая структура)
        structure = 1.0 - min(1.0, lemma_ratio)
        structure = structure * min(1.0, avg_freq / 10)
        
        return structure
    
    def analyze_file(self, filepath: str) -> int:
        """Анализирует файл с автоопределением параметров."""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            return self.analyze_bytes(data)
        except Exception as e:
            print(f"   ⚠ Ошибка при чтении {filepath}: {e}")
            return 0
    
    def discover_rules(self):
        """Выводит правила обмена с улучшенной фильтрацией."""
        raw = defaultdict(lambda: {'count': 0, 'examples': [], 'lemmas': set()})
        
        for lemma, forms in self.lemma_forms.items():
            source_form = next((surface for surface, role, _ in forms 
                              if role == ModeRole.SOURCE), None)
            
            if source_form is None:
                continue
            
            for surface, role, router in forms:
                if role == ModeRole.SOURCE or surface == source_form:
                    continue
                
                common = self._longest_common_prefix(source_form, surface)
                
                if len(common) < max(2, self.n // 3):
                    continue
                if len(common) < len(surface) * 0.3:
                    continue
                
                old_end = source_form[len(common):]
                new_end = surface[len(common):]
                
                if old_end == new_end:
                    continue
                
                key = (role, router, old_end, new_end)
                raw[key]['count'] += 1
                raw[key]['examples'].append((source_form, surface))
                raw[key]['lemmas'].add(lemma)
        
        # Формируем правила с оценкой confidence
        self.rules = []
        for (role, router, old_end, new_end), data in raw.items():
            if data['count'] >= self.min_pattern_count:
                if len(data['lemmas']) >= 2:  # Минимум 2 разные леммы
                    confidence = data['count'] / max(1, len(self.lemmas))
                    self.rules.append(TransformationRule(
                        role=role,
                        router=router,
                        old_ending=old_end,
                        new_ending=new_end,
                        examples=data['examples'][:5],
                        confidence=min(1.0, confidence),
                    ))
        
        # Сортировка и дедупликация
        self.rules.sort(key=lambda r: (r.confidence, len(r.old_ending)), reverse=True)
        self._deduplicate_rules()
        
        self.stats.total_rules = len(self.rules)
    
    def _deduplicate_rules(self):
        """Удаляет избыточные правила."""
        filtered = []
        for rule in self.rules:
            is_redundant = any(
                existing.role == rule.role and
                existing.router == rule.router and
                existing.old_ending.endswith(rule.old_ending) and
                existing.new_ending == rule.new_ending and
                existing.confidence >= rule.confidence
                for existing in filtered
            )
            if not is_redundant:
                filtered.append(rule)
        self.rules = filtered
    
    def discover_exchanges(self):
        """Выводит обменные паттерны с оценкой значимости."""
        raw_patterns = defaultdict(lambda: {
            'carriers': Counter(), 
            'examples': [], 
            'count': 0,
            'contexts': set()
        })
        
        for src_surface, carrier, recv_surface, src_lemma, router in self.exchange_records:
            src_end = self._ending(src_surface)
            recv_end = self._ending(recv_surface)
            
            key = (src_end, recv_end, router)
            raw_patterns[key]['carriers'][carrier] += 1
            raw_patterns[key]['examples'].append((src_surface, carrier, recv_surface))
            raw_patterns[key]['count'] += 1
            raw_patterns[key]['contexts'].add(src_lemma)
        
        self.exchange_patterns = []
        for (src_end, recv_end, router), data in raw_patterns.items():
            if data['count'] >= self.min_pattern_count:
                carriers = Counter({k: v for k, v in data['carriers'].items() if v >= 2})
                if len(carriers) >= 1:
                    confidence = len(data['contexts']) / max(1, len(self.lemmas))
                    self.exchange_patterns.append(ExchangePattern(
                        source_ending=src_end,
                        receiver_ending=recv_end,
                        router=router,
                        carriers=carriers,
                        examples=data['examples'][:5],
                        count=data['count'],
                        confidence=min(1.0, confidence),
                    ))
        
        self.exchange_patterns.sort(key=lambda p: (p.confidence, p.count), reverse=True)
        self.stats.total_patterns = len(self.exchange_patterns)
    
    # ========================================================================
    # ПРИМЕНЕНИЕ (УЛУЧШЕННОЕ)
    # ========================================================================
    
    def apply_rules(self, lemma: bytes, role: ModeRole, router: Optional[bytes] = None) -> bytes:
        """Применяет правила с учётом контекста."""
        if role == ModeRole.SOURCE:
            return lemma
        
        # Ищем точное совпадение
        for rule in self.rules:
            if rule.role != role:
                continue
            if rule.router != router and not (rule.router is None or router is None):
                continue
            if lemma.endswith(rule.old_ending):
                return lemma[:-len(rule.old_ending)] + rule.new_ending
        
        # Ищем приблизительное совпадение
        for rule in self.rules:
            if rule.role == role and lemma.endswith(rule.old_ending):
                return lemma[:-len(rule.old_ending)] + rule.new_ending
        
        return lemma
    
    def generate_sequence(self, lemma_a: bytes, lemma_b: bytes) -> Optional[bytes]:
        """Генерирует последовательность от lemma_a к lemma_b."""
        end_a = self._ending(lemma_a)
        end_b = self._ending(lemma_b)
        
        # Ищем подходящий паттерн
        best_pattern = None
        for pattern in self.exchange_patterns:
            if pattern.source_ending == end_a and pattern.receiver_ending == end_b:
                best_pattern = pattern
                break
        
        if not best_pattern:
            # Ищем хотя бы по источнику
            for pattern in self.exchange_patterns:
                if pattern.source_ending == end_a:
                    best_pattern = pattern
                    break
        
        if not best_pattern:
            return None
        
        # Выбираем лучший carrier
        carrier = best_pattern.carriers.most_common(1)[0][0]
        router = best_pattern.router
        
        # Применяем правила
        source_form = self.apply_rules(lemma_a, ModeRole.SOURCE)
        receiver_role = ModeRole.AFTER_ROUTER if router else ModeRole.RECEIVER
        receiver_form = self.apply_rules(lemma_b, receiver_role, router)
        
        # Собираем
        parts = [source_form, carrier]
        if router:
            parts.append(router)
        parts.append(receiver_form)
        
        return b' '.join(parts)
    
    # ========================================================================
    # СТАТИСТИКА И ВИЗУАЛИЗАЦИЯ
    # ========================================================================
    
    def get_grammar_stats(self) -> GrammarStats:
        """Возвращает полную статистику грамматики."""
        return self.stats
    
    def print_analysis(self):
        """Полный вывод анализа."""
        print(f"\n{'='*60}")
        print(f"  TEES-ГРАММАТИКА БИНАРНЫХ ДАННЫХ")
        print(f"{'='*60}")
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Природа данных: {self.stats.data_nature.value}")
        print(f"   Энтропия: {self.stats.entropy:.2f} бит/байт")
        print(f"   Размер n-граммы: {self.n}")
        print(f"   Лемм (уникальных n-грамм): {self.stats.total_lemmas}")
        print(f"   Обменов (троек): {self.stats.total_exchanges}")
        print(f"   Правил обмена: {self.stats.total_rules}")
        print(f"   Обменных паттернов: {self.stats.total_patterns}")
        print(f"   Индекс структурированности: {self.stats.structure_index:.3f}")
        
        if self.stats.structure_index > 0.7:
            print(f"   Вывод: ДАННЫЕ СТРОГО СТРУКТУРИРОВАНЫ")
        elif self.stats.structure_index > 0.3:
            print(f"   Вывод: ДАННЫЕ ИМЕЮТ СТРУКТУРУ")
        else:
            print(f"   Вывод: ДАННЫЕ БЛИЗКИ К СЛУЧАЙНЫМ")
    
    def print_rules(self, max_rules: int = 15):
        """Выводит наиболее значимые правила."""
        print(f"\n📋 ПРАВИЛА ОБМЕНА (топ-{min(max_rules, len(self.rules))}):")
        if not self.rules:
            print("   (правила не найдены)")
            return
        
        for i, rule in enumerate(self.rules[:max_rules]):
            router_str = f" [{rule.router.hex()}]" if rule.router else ""
            examples = ", ".join([f"{a.hex()[:8]}→{b.hex()[:8]}" 
                                for a, b in rule.examples[:2]])
            print(f"   {i+1:2d}. {rule.role.value}{router_str}: "
                  f"'{rule.old_ending.hex()}' → '{rule.new_ending.hex()}' "
                  f"({examples}) conf={rule.confidence:.3f}")
    
    def print_exchanges(self, max_patterns: int = 15):
        """Выводит наиболее значимые паттерны."""
        print(f"\n📋 ОБМЕННЫЕ ПАТТЕРНЫ (топ-{min(max_patterns, len(self.exchange_patterns))}):")
        if not self.exchange_patterns:
            print("   (паттерны не найдены)")
            return
        
        for i, p in enumerate(self.exchange_patterns[:max_patterns]):
            router_str = f" [{p.router.hex()}]" if p.router else ""
            carriers_str = ", ".join([f"{c.hex()[:8]}×{n}" 
                                    for c, n in p.carriers.most_common(3)])
            print(f"   {i+1:2d}. ({p.source_ending.hex()}) ↔ "
                  f"({p.receiver_ending.hex()}){router_str}: "
                  f"{carriers_str} (×{p.count}, conf={p.confidence:.3f})")


# ============================================================================
# ИНТЕГРАЦИЯ С ПОЛЕМ H
# ============================================================================

def binary_to_field(data: bytes, n: int = None, auto_configure: bool = True) -> Dict:
    """
    Превращает бинарные данные в поле H через TEES-грамматику.
    Версия 2.0 с автоопределением параметров.
    """
    
    analyzer = BinaryTEESAnalyzer(n=n, auto_configure=auto_configure)
    
    count = analyzer.analyze_bytes(data)
    
    if count == 0:
        return {
            'nodes': [],
            'edges': [],
            'grammar': {'rules': [], 'patterns': []},
            'metadata': {
                'error': 'No patterns found',
                'data_nature': analyzer.stats.data_nature.value,
                'entropy': analyzer.stats.entropy
            }
        }
    
    analyzer.discover_rules()
    analyzer.discover_exchanges()
    
    # Строим поле
    nodes = []
    for lemma in analyzer.lemmas:
        forms = analyzer.lemma_forms.get(lemma, [])
        frequency = sum(1 for rec in analyzer.exchange_records 
                       if rec[0] == lemma or rec[2] == lemma)
        
        nodes.append({
            'id': hashlib.md5(lemma).hexdigest()[:16],
            'hex': lemma.hex(),
            'length': len(lemma),
            'frequency': frequency,
            'roles': list(set(role.value for _, role, _ in forms)),
            'is_source': any(role == ModeRole.SOURCE for _, role, _ in forms),
            'is_receiver': any(role in (ModeRole.RECEIVER, ModeRole.AFTER_ROUTER) 
                             for _, role, _ in forms),
        })
    
    # Строим связи
    edges = []
    seen_edges = set()
    
    for pattern in analyzer.exchange_patterns:
        for src_hex, carrier, recv_hex in pattern.examples[:3]:
            edge_key = (src_hex, recv_hex, carrier)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({
                    'source_id': hashlib.md5(src_hex).hexdigest()[:16],
                    'target_id': hashlib.md5(recv_hex).hexdigest()[:16],
                    'source_hex': src_hex.hex(),
                    'target_hex': recv_hex.hex(),
                    'carrier_hex': carrier.hex(),
                    'router_hex': pattern.router.hex() if pattern.router else None,
                    'weight': pattern.count,
                    'confidence': pattern.confidence,
                    'pattern': {
                        'source_ending': pattern.source_ending.hex(),
                        'receiver_ending': pattern.receiver_ending.hex(),
                    }
                })
    
    return {
        'nodes': nodes,
        'edges': edges,
        'grammar': {
            'rules': [
                {
                    'role': r.role.value,
                    'router': r.router.hex() if r.router else None,
                    'old_ending': r.old_ending.hex(),
                    'new_ending': r.new_ending.hex(),
                    'confidence': r.confidence,
                }
                for r in analyzer.rules[:50]
            ],
            'patterns': [
                {
                    'source_ending': p.source_ending.hex(),
                    'receiver_ending': p.receiver_ending.hex(),
                    'router': p.router.hex() if p.router else None,
                    'carriers': {c.hex(): n for c, n in p.carriers.most_common(5)},
                    'count': p.count,
                    'confidence': p.confidence,
                }
                for p in analyzer.exchange_patterns[:50]
            ]
        },
        'metadata': {
            'n': analyzer.n,
            'total_lemmas': analyzer.stats.total_lemmas,
            'total_exchanges': analyzer.stats.total_exchanges,
            'rules_count': analyzer.stats.total_rules,
            'patterns_count': analyzer.stats.total_patterns,
            'entropy': analyzer.stats.entropy,
            'data_nature': analyzer.stats.data_nature.value,
            'structure_index': analyzer.stats.structure_index,
        }
    }


# ============================================================================
# ДЕМОНСТРАЦИЯ
# ============================================================================

def demo():
    """Расширенная демонстрация возможностей."""
    print("=" * 60)
    print("  TEES-ГРАММАТИКА ДЛЯ БИНАРНЫХ ДАННЫХ v2.0")
    print("=" * 60)
    
    # 1. Структурированные данные
    print("\n1. СТРУКТУРИРОВАННЫЕ ДАННЫЕ (протокол):")
    protocol_data = b'\x01\x02\x03\x04' * 100 + b'\x05\x06\x07\x08' * 50
    field1 = binary_to_field(protocol_data)
    print(f"   Узлов: {len(field1['nodes'])}, Связей: {len(field1['edges'])}")
    print(f"   Индекс структуры: {field1['metadata']['structure_index']:.3f}")
    
    # 2. Текст
    print("\n2. ТЕКСТ НА РУССКОМ:")
    text_data = "привет мир привет вселенная привет друг ".encode('utf-8') * 20
    field2 = binary_to_field(text_data)
    print(f"   Узлов: {len(field2['nodes'])}, Связей: {len(field2['edges'])}")
    print(f"   Природа: {field2['metadata']['data_nature']}")
    
    # 3. Криптографические данные
    print("\n3. ХЕШИ (SHA-256):")
    hash_data = b''.join([hashlib.sha256(str(i).encode()).digest() for i in range(50)])
    field3 = binary_to_field(hash_data)
    print(f"   Узлов: {len(field3['nodes'])}, Связей: {len(field3['edges'])}")
    if field3['metadata'].get('error'):
        print(f"   {field3['metadata']['error']}")
    
    # 4. Сравнительный анализ
    print("\n4. СРАВНИТЕЛЬНЫЙ АНАЛИЗ:")
    fields = [
        ("Протокол", field1),
        ("Текст", field2),
        ("Хеши", field3)
    ]
    
    for name, field in fields:
        meta = field['metadata']
        print(f"   {name:12}: структура={meta.get('structure_index', 0):.3f}, "
              f"правил={meta.get('rules_count', 0)}, "
              f"паттернов={meta.get('patterns_count', 0)}")


if __name__ == "__main__":
    demo()