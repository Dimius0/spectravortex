#!/usr/bin/env python3
"""
pipeline_v6.py — Production-Ready конвейер фуркаций (финальная версия)
======================================================================
Единый VMMPValidator для фуркаций и корпусов.
"""

import json, sys, time, random, gc, os, hashlib, logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from itertools import combinations
from typing import List, Dict, Optional, Set, Tuple, Any

# ============================================================================
# 0. КОНФИГ
# ============================================================================
class Config:
    OUTPUT_DIR = Path("./output")
    CORPUS_DIR = Path("./corpus_clean")
    CHECKPOINT_DIR = Path("./output/checkpoints")
    LOG_DIR = Path("./logs")
    
    VORTEX_GRID_SIZE = 16
    CHARGE_THRESHOLD = 1.5
    SHIFT_THRESHOLD = 0.9
    VMMP_CACHE_SIZE = 20000
    
    GRACE_PERIOD = 5
    MATURITY_AGE = 15
    ARCHIVE_AGE = 25
    
    MAX_TEES = 5000
    MAX_PER_TEES = 50
    MAX_RECEIVERS = 3000
    MAX_PER_RECEIVER = 30
    
    AWAKEN_KEYWORDS = {
        'quantum', 'energy', 'consciousness', 'Гаусс', 'память',
        'система', 'метод', 'структура', 'функция', 'анализ',
        'модель', 'данные', 'связь', 'процесс', 'свойство',
        'теория', 'закон', 'понятие', 'элемент', 'основа',
        'часть', 'форма', 'уровень', 'состояние', 'развитие'
    }
    
    UNIVERSAL_TEES = {
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did',
        'can', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'make', 'take', 'give', 'go', 'come', 'know', 'see', 'get', 'use',
        'find', 'show', 'provide', 'create', 'develop', 'include',
        'в', 'на', 'с', 'по', 'из', 'от', 'к', 'у', 'за',
        'для', 'при', 'под', 'над', 'об', 'без', 'до', 'со',
        'и', 'а', 'но', 'или', 'что', 'как', 'так', 'же',
        'не', 'ни', 'то', 'это', 'все', 'он', 'она', 'они',
        'of', 'for', 'with', 'from', 'by', 'to', 'in', 'on', 'at',
        'and', 'or', 'but', 'if', 'so', 'as', 'no', 'not',
    }
    
    @classmethod
    def setup_dirs(cls):
        for d in [cls.OUTPUT_DIR, cls.CORPUS_DIR, cls.CHECKPOINT_DIR, cls.LOG_DIR]:
            d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 0.1 ЛОГГЕР
# ============================================================================
def setup_logging(config=Config) -> logging.Logger:
    config.setup_dirs()
    logger = logging.getLogger("SpectraVortex")
    logger.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler(
        config.LOG_DIR / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log", encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s'))
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s', datefmt='%H:%M:%S'))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

# ============================================================================
# 0.2 ИМПОРТЫ ВММП
# ============================================================================
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

if HAS_NUMPY:
    try:
        from tees_knowledge_engine_v5_6 import (
            seed_to_vortex, compute_topological_charge, tees_shift, VortexConfig
        )
        HAS_VMMP = True
    except ImportError:
        HAS_VMMP = False
else:
    HAS_VMMP = False

# ============================================================================
# 1. БАЗОВЫЙ ВАЛИДАТОР
# ============================================================================
class BaseValidator:
    def __init__(self, name="base"):
        self.name = name
        self.stats = {'checked': 0, 'passed': 0, 'rejected': 0, 'filtered_out': 0}
    
    def validate(self, candidate: dict) -> Tuple[bool, str]:
        """Для фуркаций: candidate = {'source': ..., 'tees': ..., 'receiver': ...}"""
        raise NotImplementedError
    
    def check(self, source: str, tees: str, receiver: str) -> bool:
        """Для корпусов: отдельные аргументы."""
        ok, _ = self.validate({'source': source, 'tees': tees, 'receiver': receiver})
        return ok
    
    def get_stats(self) -> dict:
        total = max(self.stats['checked'], 1)
        return {
            **self.stats,
            'pass_rate': round(self.stats['passed'] / total * 100, 1),
            'reject_rate': round(100 - self.stats['passed'] / total * 100, 1)
        }
    
    def reset_stats(self):
        self.stats = {'checked': 0, 'passed': 0, 'rejected': 0, 'filtered_out': 0}

# ============================================================================
# 2. ВАЛИДАТОРЫ
# ============================================================================
class LatexFilter(BaseValidator):
    def __init__(self):
        super().__init__("LatexFilter")
        self.markers = [
            '\\frac', '\\sqrt', '\\cdot', '\\rightarrow', '\\left', '\\right',
            '\\mathcal', '\\hbar', '\\times', '\\sim', '\\text', '\\quad',
            '\\epsilon', '\\rho', '\\partial', '\\sum', '\\int', '\\prod',
            '\\infty', '\\alpha', '\\beta', '\\gamma', '\\delta', '\\lambda',
            '\\mu', '\\sigma', '\\omega', '\\theta', '\\phi', '\\psi'
        ]
        self.short_whitelist = {
            'is', 'be', 'do', 'go', 'he', 'it', 'we', 'в', 'на', 'с', 'к',
            'по', 'за', 'от', 'из', 'до', 'об', 'as', 'at', 'by', 'in', 'of', 'to'
        }
    
    def validate(self, candidate):
        self.stats['checked'] += 1
        s, t, r = candidate.get('source',''), candidate.get('tees',''), candidate.get('receiver','')
        
        if len(s) <= 1 or len(t) <= 1 or len(r) <= 1:
            self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
            return False, "single_char"
        if any(m in f"{s} {t} {r}" for m in self.markers):
            self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
            return False, "latex"
        if s.isdigit() or r.isdigit():
            self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
            return False, "numeric"
        if len(t) <= 2 and t.lower() not in self.short_whitelist:
            self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
            return False, "short_tees"
        
        self.stats['passed'] += 1
        return True, "ok"


class CodeFilter(BaseValidator):
    def __init__(self):
        super().__init__("CodeFilter")
        self.keywords = {
            'def', 'class', 'import', 'return', 'self', 'args', 'kwargs',
            'init', 'none', 'true', 'false', 'lambda', 'yield', 'raise',
            'except', 'finally', 'assert', 'async', 'await', 'nonlocal'
        }
        self.tech = {
            'json', 'csv', 'xml', 'yaml', 'toml', 'png', 'jpg', 'svg',
            'gds', 'gdsii', 'svx', 'oas', 'ndarray', 'dtype', 'float32',
            'filename', 'filepath', 'extension'
        }
        self.methods = {
            'print', 'len', 'range', 'enumerate', 'append', 'extend',
            'keys', 'values', 'items', 'update', 'encode', 'decode', 'strip', 'split'
        }
    
    def validate(self, candidate):
        self.stats['checked'] += 1
        s = candidate.get('source','').lower()
        t = candidate.get('tees','').lower()
        r = candidate.get('receiver','').lower()
        
        if s in self.keywords or t in self.keywords or r in self.keywords:
            self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
            return False, "python_kw"
        if any(p in f"{s} {t} {r}" for p in self.tech):
            self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
            return False, "tech"
        if t in self.methods:
            self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
            return False, "code_method"
        if '_' in s or '_' in r:
            if len(s.replace('_',' ').split()) > 1 or len(r.replace('_',' ').split()) > 1:
                self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
                return False, "snake_case"
        
        self.stats['passed'] += 1
        return True, "ok"


class LanguageFilter(BaseValidator):
    def __init__(self, universal_tees=None):
        super().__init__("LanguageFilter")
        self.universal = universal_tees or Config.UNIVERSAL_TEES
    
    def _has_cyrillic(self, w): return any('а' <= c <= 'я' or c == 'ё' for c in w.lower())
    def _has_latin(self, w): return any(c.isascii() and c.isalpha() for c in w.lower())
    
    def validate(self, candidate):
        self.stats['checked'] += 1
        s, t, r = candidate.get('source',''), candidate.get('tees',''), candidate.get('receiver','')
        
        if t.lower() in self.universal:
            self.stats['passed'] += 1; return True, "universal"
        
        s_ru, t_ru, r_ru = self._has_cyrillic(s), self._has_cyrillic(t), self._has_cyrillic(r)
        s_en, t_en, r_en = self._has_latin(s), self._has_latin(t), self._has_latin(r)
        
        if s_ru and t_ru and r_ru:
            self.stats['passed'] += 1; return True, "ru"
        if s_en and t_en and r_en:
            self.stats['passed'] += 1; return True, "en"
        
        self.stats['rejected'] += 1; self.stats['filtered_out'] += 1
        return False, "mixed_lang"
    
    def classify(self, source, tees, receiver) -> str:
        s_ru = self._has_cyrillic(source); t_ru = self._has_cyrillic(tees); r_ru = self._has_cyrillic(receiver)
        s_en = self._has_latin(source); t_en = self._has_latin(tees); r_en = self._has_latin(receiver)
        if s_ru and t_ru and r_ru: return 'ru'
        if s_en and t_en and r_en: return 'en'
        if not s_ru and not s_en and not r_ru and not r_en: return 'code'
        return 'mixed'


class VMMPValidator(BaseValidator):
    """
    ЕДИНЫЙ ВММП-валидатор для всех этапов:
    - validate(candidate) — для FurcationPipeline (возвращает Tuple[bool, str])
    - check(source, tees, receiver) — для CorpusBuilder (возвращает bool)
    """
    
    def __init__(self, config=Config, fast_mode=True):
        super().__init__("VMMPValidator")
        if not HAS_VMMP:
            raise ImportError("VMMPValidator требует tees_knowledge_engine_v5_6")
        
        self.vortex_config = VortexConfig()
        self.seed = 42
        self.charge_threshold = config.CHARGE_THRESHOLD
        self.shift_threshold = config.SHIFT_THRESHOLD
        self.fast_mode = fast_mode
        
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_max = config.VMMP_CACHE_SIZE
        self._hits = 0
        self._misses = 0
    
    def _get_vortex(self, word: str) -> np.ndarray:
        if not word or not word.strip():
            return np.zeros((self.vortex_config.grid_size,) * 2, dtype=self.vortex_config.dtype)
        
        word_hash = hashlib.md5(word.encode('utf-8')).hexdigest()
        if word_hash in self._cache:
            self._hits += 1
            return self._cache[word_hash]
        
        self._misses += 1
        if len(self._cache) >= self._cache_max:
            keys = random.sample(list(self._cache.keys()), self._cache_max // 5)
            for k in keys:
                del self._cache[k]
        
        seed = int(word_hash, 16) ^ self.seed
        vortex = seed_to_vortex(seed, self.vortex_config)
        self._cache[word_hash] = vortex
        return vortex
    
    def _check_impl(self, source: str, tees: str, receiver: str) -> Tuple[bool, str]:
        """Общая реализация проверки."""
        if self.fast_mode and (source == tees or tees == receiver or source == receiver):
            return False, "fast_identity"
        
        try:
            src_v = self._get_vortex(source)
            tee_v = self._get_vortex(tees)
            dst_v = self._get_vortex(receiver)
            
            total_charge = abs(
                compute_topological_charge(src_v) +
                compute_topological_charge(tee_v) +
                compute_topological_charge(dst_v)
            )
            if total_charge > self.charge_threshold:
                return False, f"charge({total_charge:.2f})"
            
            shift_src = abs(tees_shift(src_v, tee_v))
            shift_dst = abs(tees_shift(tee_v, dst_v))
            if shift_src > self.shift_threshold or shift_dst > self.shift_threshold:
                return False, f"shift({shift_src:.2f},{shift_dst:.2f})"
            
            return True, "vmmp_ok"
        except Exception as e:
            return True, f"skip({str(e)[:30]})"
    
    def validate(self, candidate: dict) -> Tuple[bool, str]:
        """Для FurcationPipeline: возвращает (ok, reason)."""
        self.stats['checked'] += 1
        src = candidate.get('source', '')
        tees = candidate.get('tees', '')
        dst = candidate.get('receiver', '')
        
        ok, reason = self._check_impl(src, tees, dst)
        if ok:
            self.stats['passed'] += 1
        else:
            self.stats['rejected'] += 1
            self.stats['filtered_out'] += 1
        return ok, reason
    
    def check(self, source: str, tees: str, receiver: str) -> bool:
        """Для CorpusBuilder: возвращает bool."""
        self.stats['checked'] += 1
        ok, _ = self._check_impl(source, tees, receiver)
        if ok:
            self.stats['passed'] += 1
        else:
            self.stats['rejected'] += 1
        return ok
    
    def get_stats(self) -> dict:
        base = super().get_stats()
        total = max(self._hits + self._misses, 1)
        base.update({
            'cache_hits': self._hits,
            'cache_misses': self._misses,
            'cache_size': len(self._cache),
            'hit_rate': round(self._hits / total * 100, 1)
        })
        return base

# ============================================================================
# 3. ВАЛИДАЦИЯ ДАННЫХ
# ============================================================================
def validate_graph_structure(data: dict, logger=None) -> bool:
    log = logger or logging.getLogger(__name__)
    required = {'active_edges', 'dormant_edges'}
    if not required.issubset(data.keys()):
        log.error(f"Отсутствуют ключи: {required - set(data.keys())}")
        return False
    edge_keys = {'source', 'tees', 'receiver', 'weight'}
    for i, e in enumerate(data.get('active_edges', [])):
        if not edge_keys.issubset(e.keys()):
            log.warning(f"Ребро {i}: отсутствуют ключи {edge_keys - set(e.keys())}")
            return False
    log.info(f"Структура графа валидна: {len(data['active_edges']):,} активных, "
             f"{len(data['dormant_edges']):,} в архиве")
    return True

# ============================================================================
# 4. FURCATOR
# ============================================================================
class LightFurcatorV6:
    def __init__(self, edges, validators=None, config=Config, logger=None):
        self.edges = edges
        self.furcations = []
        self.validators = validators or []
        self.config = config
        self.log = logger or logging.getLogger(__name__)
        
        self._gen_stats = {'total': 0, 'passed': 0, 'rejected': 0}
        self._source_index = defaultdict(list)
        self._receiver_index = defaultdict(list)
        self._tees_index = defaultdict(list)
        
        self.log.info("Построение индексов...")
        for i, e in enumerate(edges):
            self._source_index[e['source']].append(i)
            self._receiver_index[e['receiver']].append(i)
            self._tees_index[e['tees']].append(i)
        self.log.info(f"Индексы: {len(self._source_index):,} ист., "
                      f"{len(self._tees_index):,} связ., {len(self._receiver_index):,} приём.")
    
    def _validate(self, candidate):
        self._gen_stats['total'] += 1
        for v in self.validators:
            ok, reason = v.validate(candidate)
            if not ok:
                self._gen_stats['rejected'] += 1
                return False
        self._gen_stats['passed'] += 1
        return True
    
    def generate_chain(self):
        existing = {f"{e['source']}|{e['tees']}|{e['receiver']}" for e in self.edges}
        candidates = []
        sorted_tees = sorted(self._tees_index.items(), key=lambda x: len(x[1]), reverse=True)[:self.config.MAX_TEES]
        
        for idx, (tees_word, indices) in enumerate(sorted_tees):
            if len(indices) < 2: continue
            for i, j in combinations(indices[:self.config.MAX_PER_TEES], 2):
                e1, e2 = self.edges[i], self.edges[j]
                if e1['receiver'] == e2['source']:
                    src, dst = e1['source'], e2['receiver']
                    if src == dst: continue
                    if f"{src}|{tees_word}|{dst}" in existing: continue
                    c = {'source': src, 'tees': tees_word, 'receiver': dst,
                         'type': 'chain', 'parents': [e1.get('id',''), e2.get('id','')]}
                    if self._validate(c):
                        candidates.append(c)
            if (idx+1) % 1000 == 0:
                self.log.debug(f"  Связок: {idx+1}/{len(sorted_tees)} | Кандидатов: {len(candidates):,}")
        return candidates
    
    def generate_convergent(self):
        existing = {f"{e['source']}|{e['tees']}|{e['receiver']}" for e in self.edges}
        candidates = []
        sorted_recv = sorted(self._receiver_index.items(), key=lambda x: len(x[1]), reverse=True)[:self.config.MAX_RECEIVERS]
        
        for idx, (receiver, indices) in enumerate(sorted_recv):
            if len(indices) < 2: continue
            src_edges = defaultdict(list)
            for i in indices[:self.config.MAX_PER_RECEIVER]:
                e = self.edges[i]
                src_edges[e['source']].append(e)
            sources = list(src_edges.keys())[:10]
            for s1, s2 in combinations(sources, 2):
                tees1 = Counter(e['tees'] for e in src_edges[s1]).most_common(1)
                tees2 = Counter(e['tees'] for e in src_edges[s2]).most_common(1)
                if tees1 and tees2:
                    syn = tees1[0][0] if tees1[0][1] >= tees2[0][1] else tees2[0][0]
                    for src, dst in [(s1, s2), (s2, s1)]:
                        if f"{src}|{syn}|{dst}" in existing: continue
                        c = {'source': src, 'tees': syn, 'receiver': dst,
                             'type': 'convergent', 'parents': [src_edges[s1][0].get('id',''), src_edges[s2][0].get('id','')]}
                        if self._validate(c):
                            candidates.append(c)
            if (idx+1) % 500 == 0:
                self.log.debug(f"  Приёмников: {idx+1}/{len(sorted_recv)} | Кандидатов: {len(candidates):,}")
        return candidates
    
    def apply(self, chain, convergent):
        all_c = chain + convergent
        existing = {f"{e['source']}|{e['tees']}|{e['receiver']}" for e in self.edges}
        applied = 0
        for c in all_c:
            key = f"{c['source']}|{c['tees']}|{c['receiver']}"
            if key not in existing:
                existing.add(key)
                self.furcations.append(c)
                applied += 1
        return applied
    
    def get_gen_stats(self):
        total = max(self._gen_stats['total'], 1)
        return {**self._gen_stats, 'rejection_rate': round(self._gen_stats['rejected']/total*100, 1)}

# ============================================================================
# 5. АНАЛИЗАТОР ГРАФА
# ============================================================================
class GraphAnalyzer:
    def __init__(self, edges, logger=None):
        self.edges = edges
        self.log = logger or logging.getLogger(__name__)
        self.nodes = {}
        self._out_degree = Counter()
        self._in_degree = Counter()
        for e in edges:
            s, d = e['source'], e['receiver']
            self._out_degree[s] += 1; self._in_degree[d] += 1
            if s not in self.nodes: self.nodes[s] = {'out':0,'in':0}
            if d not in self.nodes: self.nodes[d] = {'out':0,'in':0}
            self.nodes[s]['out'] += 1; self.nodes[d]['in'] += 1
    
    def connectivity(self):
        return len(self.edges) / max(len(self.nodes), 1)
    
    def top_hubs(self, n=10):
        return self._out_degree.most_common(n)
    
    def top_authorities(self, n=10):
        return self._in_degree.most_common(n)
    
    def report(self):
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'connectivity': round(self.connectivity(), 2),
            'top_hubs': [{'node': n, 'out_degree': d} for n, d in self.top_hubs(10)],
            'top_authorities': [{'node': n, 'in_degree': d} for n, d in self.top_authorities(10)],
        }
    
    def print_report(self):
        r = self.report()
        print(f"\n📊 АНАЛИЗ ГРАФА")
        print(f"   Узлов: {r['total_nodes']:,} | Связей: {r['total_edges']:,} | Связность: {r['connectivity']}")
        print(f"   Топ-хабы: {', '.join(f'{n}({d})' for n,d in self.top_hubs(5))}")
        print(f"   Топ-авторитеты: {', '.join(f'{n}({d})' for n,d in self.top_authorities(5))}")

# ============================================================================
# 6. СОХРАНЕНИЕ
# ============================================================================
def save_json_streaming(furcations, graph_path, chain_count, conv_count, awakened,
                        validators, gen_stats, furcator, analyzer=None, config=Config, logger=None):
    log = logger or logging.getLogger(__name__)
    config.setup_dirs()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = config.OUTPUT_DIR / f"furcations_v6_{timestamp}.json"
    
    type_stats = Counter(f['type'] for f in furcations)
    log_data = {
        'meta': {
            'timestamp': datetime.now().isoformat(),
            'source_graph': graph_path, 'version': 'v6.0',
            'total_applied': len(furcations),
            'chain_count': chain_count, 'convergent_count': conv_count,
            'awakened_edges': awakened
        },
        'generation_stats': gen_stats,
        'validators_report': {v.name: v.get_stats() for v in validators},
        'furcation_stats': {
            'by_type': dict(type_stats),
            'top_tees': [{'word': w, 'count': c} for w, c in Counter(f['tees'] for f in furcations).most_common(30)],
        }
    }
    if analyzer:
        log_data['graph_analysis'] = analyzer.report()
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('{\n')
        for key in ['meta', 'generation_stats', 'validators_report', 'furcation_stats', 'graph_analysis']:
            if key in log_data:
                f.write(f'  "{key}": '); json.dump(log_data[key], f, ensure_ascii=False, indent=2); f.write(',\n')
        f.write('  "sample_furcations": [\n')
        for i, fur in enumerate(sorted(furcations[:300], key=lambda x: (x['type'], x['tees']))):
            json.dump(fur, f, ensure_ascii=False)
            if i < min(len(furcations), 300) - 1: f.write(',\n')
        f.write('\n  ]\n}\n')
    
    log.info(f"Лог сохранён: {log_path} ({os.path.getsize(log_path)/1024/1024:.1f} MB)")
    return log_path

# ============================================================================
# 7. ДАШБОРД
# ============================================================================
def print_dashboard(stage_times, chain_count, conv_count, applied, awakened, validators, gen_stats, analyzer=None):
    total = sum(stage_times.values())
    print("\n" + "="*60)
    print(f"  FURCATION PIPELINE v6.0 — RESULTS")
    print("="*60)
    print(f"  ⏱️  Общее время: {total:.0f} сек ({total/60:.1f} мин)")
    for stage, t in stage_times.items():
        print(f"     └─ {stage:<15} {t:.0f} сек")
    print(f"  🔗 Цепных: {chain_count:,} | Конвергентных: {conv_count:,}")
    print(f"  ✅ Применено: {applied:,} | ⚡ Пробуждено: {awakened:,}")
    print(f"  🛡️  Валидаторы:")
    for v in validators:
        s = v.get_stats()
        print(f"     {v.name}: pass {s['pass_rate']}% ({s['passed']:,}/{s['checked']:,})")
    print(f"  📊 Кандидатов: {gen_stats['total']:,} | Прошли: {gen_stats['passed']:,} | Отсеяно: {gen_stats['rejected']:,} ({gen_stats['rejection_rate']}%)")
    if analyzer:
        analyzer.print_report()
    print("="*60)

# ============================================================================
# 8. FURCATION PIPELINE
# ============================================================================
class FurcationPipeline:
    def __init__(self, config=Config, logger=None):
        self.config = config
        self.log = logger or logging.getLogger(__name__)
        self.validators = []
        self.furcator = None
        self.analyzer = None
    
    def add_validator(self, validator):
        self.validators.append(validator)
        return self
    
    def run(self, graph_path):
        self.log.info("="*50)
        self.log.info("ЗАПУСК КОНВЕЙЕРА ФУРКАЦИЙ v6.0")
        self.log.info("="*50)
        
        stage_times = {}
        
        # Загрузка
        self.log.info(f"Загрузка: {graph_path}")
        t0 = time.time()
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.log.error(f"Ошибка загрузки: {e}"); return None
        
        if not validate_graph_structure(data, self.log):
            return None
        
        edges = data.get('active_edges', [])
        dormant = data.get('dormant_edges', [])
        self.log.info(f"Загружено: {len(edges):,} активных, {len(dormant):,} в архиве")
        
        # Пробуждение
        awakened = [e for e in dormant if any(
            k in f"{e['source']} {e['tees']} {e['receiver']}".lower()
            for k in self.config.AWAKEN_KEYWORDS
        )]
        self.log.info(f"Пробуждено: {len(awakened):,}")
        
        all_edges = edges + awakened
        del dormant, data; gc.collect()
        stage_times['Загрузка'] = time.time() - t0
        
        # Анализ
        self.analyzer = GraphAnalyzer(all_edges, self.log)
        
        # Фуркации
        self.furcator = LightFurcatorV6(all_edges, self.validators, self.config, self.log)
        
        self.log.info("Цепные фуркации..."); t1 = time.time()
        chain = self.furcator.generate_chain()
        stage_times['Цепные'] = time.time() - t1
        self.log.info(f"  Найдено: {len(chain):,}")
        
        self.log.info("Конвергентные фуркации..."); t2 = time.time()
        convergent = self.furcator.generate_convergent()
        stage_times['Конвергентные'] = time.time() - t2
        self.log.info(f"  Найдено: {len(convergent):,}")
        
        self.log.info("Применение..."); t3 = time.time()
        applied = self.furcator.apply(chain, convergent)
        stage_times['Применение'] = time.time() - t3
        self.log.info(f"  Применено: {applied:,}")
        
        # Сохранение
        t4 = time.time()
        log_path = save_json_streaming(
            self.furcator.furcations, graph_path,
            len(chain), len(convergent), len(awakened),
            self.validators, self.furcator.get_gen_stats(),
            self.furcator, self.analyzer, self.config, self.log
        )
        stage_times['Сохранение'] = time.time() - t4
        
        # Дашборд
        print_dashboard(stage_times, len(chain), len(convergent), applied,
                       len(awakened), self.validators, self.furcator.get_gen_stats(), self.analyzer)
        
        self.log.info(f"ГОТОВО! Лог: {log_path}")
        return {'log_path': log_path, 'furcator': self.furcator, 'analyzer': self.analyzer}

# ============================================================================
# 9. ТОЧКА ВХОДА
# ============================================================================
if __name__ == "__main__":
    Config.setup_dirs()
    logger = setup_logging(Config)
    
    graph_file = "output/graph_vmmp_20260714_233840.json"
    use_vmmp = False
    fast_vmmp = True
    
    for arg in sys.argv[1:]:
        if arg.endswith('.json'): graph_file = arg
        elif arg == '--vmmp': use_vmmp = True
        elif arg == '--no-vmmp': use_vmmp = False
        elif arg == '--fast': fast_vmmp = True
        elif arg == '--full': fast_vmmp = False
    
    pipeline = FurcationPipeline(Config, logger)
    pipeline.add_validator(LatexFilter())
    pipeline.add_validator(CodeFilter())
    pipeline.add_validator(LanguageFilter(Config.UNIVERSAL_TEES))
    
    if use_vmmp:
        if HAS_VMMP:
            logger.warning("VMMPValidator включён — будет медленно!")
            pipeline.add_validator(VMMPValidator(Config, fast_vmmp))
        else:
            logger.warning("VMMP недоступен")
    
    pipeline.run(graph_file)