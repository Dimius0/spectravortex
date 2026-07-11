#!/usr/bin/env python3
"""
tees_knowledge_engine_v4_2_vmpp.py — Финальный TEES-движок без Гаусса
======================================================================
✅ ВММП-энтропия вместо np.random.RandomState
✅ ВММП-турбулентность в Furcator
✅ Интегрированный парсер (ВСЕ тройки, без лимита)
✅ Адаптивные пороги (самонастройка под корпус)
✅ Nothing-up-my-sleeve константы
✅ Единый файл без дублирования

ИСПРАВЛЕНИЯ v4.2:
- Убран лимит троек на текст (глубина без ограничений)
- Адаптивные пороги для TEES-сдвига и топологического заряда
- Статистика порогов в выводе
"""

import json
import re
import hashlib
import numpy as np
from pathlib import Path
from collections import defaultdict, deque, Counter
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from functools import lru_cache
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 0. МАНИФЕСТ
# ============================================================================

MANIFEST = """
🧬 VMMP MANIFEST v4.2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Гаусс был неправ — нормальное распределение не работает для турбулентности
2. Случайности нет — только ВММП-энтропия через хэш-цепочки
3. Топология первична — τ = ∮(dθ/2π) определяет структуру
4. Nothing-up-my-sleeve — все константы из SHA-256
5. ∇⁴ψ = 0 — бигармоническое уравнение как фильтр реальности
6. Адаптивность — пороги самонастраиваются под корпус
7. Глубина без лимита — все связи важны
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# 1. КОНСТАНТЫ (nothing-up-my-sleeve — из SHA-256)
# ============================================================================

H_CONSTANTS = np.array([
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
], dtype=np.uint32)

K_CONSTANTS = np.array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
], dtype=np.uint32)

# ============================================================================
# 2. ВММП-ЯДРО (БЕЗ ГАУССА)
# ============================================================================

@dataclass
class VortexConfig:
    grid_size: int = 16
    turbulence_threshold: float = 0.5
    turbulence_intensity: float = 0.3
    dtype: type = np.float32
    
    def __post_init__(self):
        gs = int(self.grid_size)
        self.x = np.linspace(-1, 1, gs)
        self.y = np.linspace(-1, 1, gs)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.R = np.sqrt(self.X**2 + self.Y**2)
        self.Theta = np.arctan2(self.Y, self.X)
        
        kx = np.fft.fftfreq(gs)
        ky = np.fft.fftfreq(gs)
        KX, KY = np.meshgrid(kx, ky, indexing='ij')
        laplacian_fft = (-4 * np.pi**2 * (KX**2 + KY**2)).astype(self.dtype)
        self.laplacian2_fft = (laplacian_fft ** 2).astype(self.dtype)
        self.smoothing_kernel = 1.0 / (1.0 + self.laplacian2_fft)


def simple_tees_hash(data: bytes, state: int = 0) -> int:
    h = state
    for byte in data:
        h = ((h << 5) + h) ^ byte
        h = (h * int(H_CONSTANTS[0])) & 0xFFFFFFFF; h ^= (h >> 17)
        h = (h * int(K_CONSTANTS[0])) & 0xFFFFFFFF; h ^= (h >> 13)
        h = (h * int(H_CONSTANTS[1])) & 0xFFFFFFFF; h ^= (h >> 25)
        h = (h * int(K_CONSTANTS[63])) & 0xFFFFFFFF; h ^= (h >> 3)
    return h


def vmmp_entropy(seed: int, size: int) -> np.ndarray:
    state = seed & 0xFFFFFFFF
    result = np.zeros(size, dtype=np.float32)
    for i in range(size):
        state = simple_tees_hash(state.to_bytes(4, 'big'))
        result[i] = (float(state) / float(0xFFFFFFFF)) * 2.0 - 1.0
    std = result.std()
    if std > 1e-10:
        result = (result - result.mean()) / std
    return result


def seed_to_vortex(seed: int, config: VortexConfig) -> np.ndarray:
    gs = config.grid_size
    flat = vmmp_entropy(seed, gs * gs)
    vortex = flat.reshape(gs, gs).astype(config.dtype)
    fft_vortex = np.fft.fft2(vortex.astype(np.complex128))
    smooth_fft = fft_vortex * config.smoothing_kernel
    smooth_vortex = np.real(np.fft.ifft2(smooth_fft)).astype(config.dtype)
    std = smooth_vortex.std()
    if std > 1e-10:
        smooth_vortex = (smooth_vortex - smooth_vortex.mean()) / std
    return smooth_vortex


def compute_topological_charge(vortex: np.ndarray) -> float:
    gy, gx = np.gradient(vortex)
    phase = np.arctan2(gy, gx + 1e-10)
    dphase_dx = np.diff(phase, axis=1)
    dphase_dy = np.diff(phase, axis=0)
    circulation_x = np.sum(dphase_dx[:-1, :])
    circulation_y = np.sum(dphase_dy[:, :-1])
    return float((circulation_x + circulation_y) / (2 * np.pi))


def tees_shift(state_a: np.ndarray, state_b: np.ndarray) -> float:
    a_bytes = state_a.tobytes()
    b_bytes = state_b.tobytes()
    ha = simple_tees_hash(a_bytes)
    hb = simple_tees_hash(b_bytes)
    combined = (ha << 32) | (hb & 0xFFFFFFFF)
    flow = simple_tees_hash(combined.to_bytes(8, 'big'))
    na = simple_tees_hash(ha.to_bytes(4, 'big'), flow)
    nb = simple_tees_hash(hb.to_bytes(4, 'big'), flow)
    before = (ha ^ hb).bit_count() / 32.0
    after = (na ^ nb).bit_count() / 32.0
    return after - before


def vmmp_turbulence(vortices: np.ndarray, config: VortexConfig) -> np.ndarray:
    n = vortices.shape[0]
    result = vortices.copy()
    charges = np.array([compute_topological_charge(vortices[i]) for i in range(n)])
    for i in range(n):
        tau_i = charges[i]
        if abs(tau_i) < config.turbulence_threshold:
            diff_array = np.abs(np.abs(charges) - np.abs(tau_i))
            diff_array[i] = float('inf')
            best_partner = np.argmin(diff_array)
            fft_i = np.fft.fft2(vortices[i].astype(np.complex128))
            fft_partner = np.fft.fft2(vortices[best_partner].astype(np.complex128))
            biharm_i = fft_i * config.laplacian2_fft
            biharm_partner = fft_partner * config.laplacian2_fft
            merged_fft = (biharm_i + biharm_partner) * 0.5
            merged = np.real(np.fft.ifft2(merged_fft)).astype(config.dtype)
            turbulence_energy = config.turbulence_intensity * (1.0 - abs(tau_i))
            result[i] = vortices[i] * (1.0 - turbulence_energy) + merged * turbulence_energy
    return result


# ============================================================================
# 3. АДАПТИВНЫЕ ПОРОГИ
# ============================================================================

class AdaptiveThreshold:
    """
    Самонастраивающийся порог на основе статистики.
    Чем больше данных — тем точнее порог.
    """
    
    def __init__(self, window_size: int = 5000):
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        self._cached_threshold = 0.8
        self._cache_valid = False
    
    def update(self, value: float):
        self.values.append(abs(value))
        self._cache_valid = False
    
    def get_threshold(self, percentile: float = 85) -> float:
        if len(self.values) < 10:
            return 0.8
        
        if not self._cache_valid or len(self.values) % 100 == 0:
            data = list(self.values)
            self._cached_threshold = float(np.percentile(data, percentile))
            self._cache_valid = True
        
        return self._cached_threshold
    
    def get_stats(self) -> Dict:
        if len(self.values) < 10:
            return {'samples': len(self.values), 'default': 0.8}
        
        data = list(self.values)
        return {
            'samples': len(data),
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'p50': float(np.percentile(data, 50)),
            'p75': float(np.percentile(data, 75)),
            'p85': float(np.percentile(data, 85)),
            'p90': float(np.percentile(data, 90)),
            'p95': float(np.percentile(data, 95)),
            'current_threshold': self._cached_threshold,
        }


# ============================================================================
# 4. ИНТЕГРИРОВАННЫЙ TEES-ПАРСЕР
# ============================================================================

class TeesParser:
    """
    Встроенный TEES-парсер.
    Извлекает ВСЕ тройки без ограничений.
    """
    
    RU_VERB_ENDINGS = (
        'ть', 'тся', 'ться',
        'л', 'ла', 'ло', 'ли',
        'ет', 'ит', 'ют', 'ут', 'ат', 'ят',
        'ает', 'еет', 'иет', 'оет', 'ует',
        'ывает', 'ивает', 'овал', 'евал',
        'лся', 'лась', 'лось', 'лись',
    )
    
    RU_NOUN_TEES = frozenset({
        'связь', 'связи', 'система', 'структура', 'основа',
        'часть', 'элемент', 'функция', 'процесс', 'метод',
        'закон', 'теория', 'модель', 'понятие', 'свойство',
    })
    
    EN_TEES_WORDS = frozenset({
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing',
        'can', 'could', 'will', 'would', 'shall', 'should',
        'may', 'might', 'must',
        'make', 'makes', 'made', 'take', 'takes', 'took',
        'give', 'gives', 'gave', 'go', 'goes', 'went',
        'come', 'comes', 'came', 'know', 'knows', 'knew',
        'see', 'sees', 'saw', 'get', 'gets', 'got',
        'use', 'uses', 'used', 'find', 'finds', 'found',
        'show', 'shows', 'showed', 'provide', 'provides',
        'create', 'creates', 'created', 'develop', 'develops',
        'include', 'includes', 'included', 'describe', 'describes',
        'demonstrate', 'demonstrates', 'represent', 'represents',
        'define', 'defines', 'explain', 'explains',
        'present', 'presents', 'study', 'studies',
        'propose', 'proposes', 'introduce', 'introduces',
        'produce', 'produces', 'generate', 'generates',
        'form', 'forms', 'establish', 'establishes',
    })
    
    STOP_WORDS_RU = frozenset({
        'в', 'на', 'с', 'по', 'из', 'от', 'к', 'у', 'за',
        'и', 'а', 'но', 'или', 'что', 'как', 'так', 'же', 'бы', 'ли',
        'не', 'ни', 'то', 'это', 'все', 'всё',
        'он', 'она', 'оно', 'они', 'я', 'ты', 'мы', 'вы',
        'для', 'при', 'под', 'над', 'об', 'без', 'до', 'со',
        'его', 'ее', 'её', 'их', 'свой', 'своя', 'своё', 'свои',
    })
    
    STOP_WORDS_EN = frozenset({
        'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'from',
        'and', 'or', 'but', 'if', 'so', 'as', 'by', 'with', 'about',
        'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'this', 'that', 'these', 'those',
        'not', 'no', 'yes', 'very', 'just', 'only', 'also',
        'all', 'some', 'any', 'each', 'every',
        'who', 'which', 'what', 'when', 'where', 'why', 'how',
        'his', 'her', 'its', 'their', 'our', 'my', 'your',
    })
    
    @classmethod
    def detect_language(cls, text: str) -> str:
        text_lower = text.lower()
        cyrillic_chars = sum(1 for c in text_lower if 'а' <= c <= 'я' or c == 'ё')
        return 'ru' if cyrillic_chars > len(text_lower) * 0.1 else 'en'
    
    @classmethod
    def is_tees_ru(cls, word: str) -> bool:
        word_clean = re.sub(r'[^а-яё]', '', word.lower())
        if len(word_clean) < 3:
            return False
        return (
            any(word_clean.endswith(end) for end in cls.RU_VERB_ENDINGS) or
            word_clean in cls.RU_NOUN_TEES
        )
    
    @classmethod
    def is_tees_en(cls, word: str) -> bool:
        return word.lower() in cls.EN_TEES_WORDS
    
    @classmethod
    def parse(cls, text: str) -> dict:
        """
        Извлекает ВСЕ TEES-структуры из текста.
        БЕЗ ЛИМИТА — глубина без ограничений.
        """
        if not text or len(text.strip()) < 30:
            return {'valid': False, 'error': 'Текст слишком короткий'}
        
        language = cls.detect_language(text)
        is_russian = (language == 'ru')
        stop_words = cls.STOP_WORDS_RU if is_russian else cls.STOP_WORDS_EN
        
        text_clean = text.lower()
        text_clean = re.sub(r'[^а-яёa-z\s]', ' ', text_clean)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        
        sentences = re.split(r'[.!?]+', text_clean)
        
        all_triples = []
        seen_triples = set()
        
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            
            words = sent.split()
            if len(words) < 3:
                continue
            
            # Ищем ВСЕ TEES — без break и без лимита!
            for i in range(1, len(words) - 1):
                word = words[i]
                
                is_explicit = cls.is_tees_ru(word) if is_russian else cls.is_tees_en(word)
                
                is_auto = False
                if not is_explicit:
                    left_word = words[i - 1]
                    right_word = words[i + 1]
                    left_ok = left_word not in stop_words and len(left_word) > 2
                    right_ok = right_word not in stop_words and len(right_word) > 2
                    if left_ok and right_ok:
                        is_auto = True
                
                if not (is_explicit or is_auto):
                    continue
                
                source_idx = i - 1
                skipped = 0
                while source_idx >= 0 and words[source_idx] in stop_words:
                    source_idx -= 1
                    skipped += 1
                if skipped > 2:
                    continue
                
                receiver_idx = i + 1
                skipped = 0
                while receiver_idx < len(words) and words[receiver_idx] in stop_words:
                    receiver_idx += 1
                    skipped += 1
                if skipped > 2:
                    continue
                
                if source_idx < 0 or receiver_idx >= len(words):
                    continue
                
                if words[source_idx] in stop_words or words[receiver_idx] in stop_words:
                    continue
                
                triple_key = f"{words[source_idx]}|{word}|{words[receiver_idx]}"
                if triple_key in seen_triples:
                    continue
                seen_triples.add(triple_key)
                
                triple = {
                    'source': words[source_idx],
                    'tees': word,
                    'receiver': words[receiver_idx],
                    'type': 'explicit' if is_explicit else 'auto',
                    'sentence': sent[:100]
                }
                
                all_triples.append(triple)
                # БЕЗ BREAK — собираем все тройки!
        
        if not all_triples:
            return {'valid': False, 'error': 'TEES не найдены'}
        
        return {
            'valid': True,
            'language': language,
            'triples': all_triples,
            'total_triples': len(all_triples)
        }


# ============================================================================
# 5. КОНФИГУРАЦИЯ
# ============================================================================

@dataclass
class PipelineConfig:
    vortex: VortexConfig = field(default_factory=VortexConfig)
    seed: int = 42
    furcation_top_k: int = 20
    min_edge_score: float = 0.25
    min_furcation_score: float = 0.3
    cache_size: int = 20000
    output_dir: Path = Path("./output")
    corpus_path: Path = Path("./corpus/corpus.json")
    
    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 6. ВММП-ПРОВЕРКА С АДАПТИВНЫМИ ПОРОГАМИ
# ============================================================================

class VMMPChecker:
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.vortex_config = self.config.vortex
        self.seed = self.config.seed
        self._stats = defaultdict(int)
        
        # Адаптивные пороги
        self.shift_threshold = AdaptiveThreshold()
        self.charge_threshold = AdaptiveThreshold()
    
    def _compute_vortex_raw(self, word_hash: str) -> np.ndarray:
        if not word_hash:
            return np.zeros((self.vortex_config.grid_size,) * 2, dtype=self.vortex_config.dtype)
        seed = int(word_hash, 16) ^ self.seed
        return seed_to_vortex(seed, self.vortex_config)
    
    def get_vortex(self, word: str) -> np.ndarray:
        if not word or not word.strip():
            return np.zeros((self.vortex_config.grid_size,) * 2, dtype=self.vortex_config.dtype)
        word_hash = hashlib.md5(word.encode('utf-8')).hexdigest()
        if not hasattr(self, '_cached_compute'):
            self._cached_compute = lru_cache(maxsize=self.config.cache_size)(
                self._compute_vortex_raw
            )
        return self._cached_compute(word_hash)
    
    def check_triples_batch(self, triples: List[Tuple[str, str, str]], lang: str = None) -> List[Dict]:
        if not triples:
            return []
        
        words = set()
        for s, t, r in triples:
            words.update([s, t, r])
        
        vortices = {w: self.get_vortex(w) for w in words}
        charges = {w: compute_topological_charge(vortices[w]) for w in words}
        
        results = []
        for source, tees, receiver in triples:
            src_v = vortices[source]
            tee_v = vortices[tees]
            rec_v = vortices[receiver]
            src_c = charges[source]
            tee_c = charges[tees]
            rec_c = charges[receiver]
            
            shift_src = tees_shift(src_v, tee_v)
            shift_rec = tees_shift(tee_v, rec_v)
            total_charge = src_c + tee_c + rec_c
            
            # Адаптивные пороги
            charge_limit = self.charge_threshold.get_threshold(85)
            shift_limit = self.shift_threshold.get_threshold(85)
            
            is_balanced = abs(total_charge) < charge_limit
            is_connected = abs(shift_src) < shift_limit and abs(shift_rec) < shift_limit
            
            score = 1.0 - (abs(shift_src) + abs(shift_rec)) / 2.0
            if not is_balanced:
                score *= 0.7
            score = max(0.0, min(1.0, score))
            
            # Обновляем статистику порогов
            self.shift_threshold.update(abs(shift_src))
            self.shift_threshold.update(abs(shift_rec))
            self.charge_threshold.update(abs(total_charge))
            
            result = {
                'source': source, 'tees': tees, 'receiver': receiver,
                'score': score,
                'vmmp_compliant': is_balanced and is_connected and score > self.config.min_edge_score,
                'is_balanced': is_balanced, 'is_connected': is_connected,
                'src_charge': src_c, 'tees_charge': tee_c, 'rec_charge': rec_c,
                'shift_src': shift_src, 'shift_rec': shift_rec,
            }
            results.append(result)
            self._stats['total'] += 1
            if result['vmmp_compliant']:
                self._stats['compliant'] += 1
        
        return results


# ============================================================================
# 7. ГРАФ ЗНАНИЙ
# ============================================================================

class KnowledgeGraph:
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        self._edge_index: Dict[str, int] = {}
        self.furcation_count = 0
    
    def add_edge(self, source, tees, receiver, check_result, text_source=None):
        edge_id = f"{source}|{tees}|{receiver}"
        if edge_id in self._edge_index:
            idx = self._edge_index[edge_id]
            self.edges[idx]['weight'] += check_result['score']
            if text_source:
                self.edges[idx]['sources'].append(text_source)
        else:
            self._edge_index[edge_id] = len(self.edges)
            self.edges.append({
                'id': edge_id,
                'source': source, 'tees': tees, 'receiver': receiver,
                'weight': check_result['score'],
                'vmmp_compliant': check_result['vmmp_compliant'],
                'sources': [text_source] if text_source else [],
                'charges': {
                    'src': check_result['src_charge'],
                    'tees': check_result['tees_charge'],
                    'rec': check_result['rec_charge']
                }
            })
        for w in [source, tees, receiver]:
            if w and w.strip():
                if w not in self.nodes:
                    self.nodes[w] = {'degree': 0}
                self.nodes[w]['degree'] += 1
    
    def get_statistics(self) -> Dict:
        if not self.nodes:
            return {'total_nodes': 0, 'total_edges': 0, 'avg_weight': 0,
                    'compliant_edges': 0, 'compliant_rate': 0}
        weights = [e['weight'] for e in self.edges]
        compliant = sum(1 for e in self.edges if e.get('vmmp_compliant'))
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'avg_weight': float(np.mean(weights)) if weights else 0,
            'compliant_edges': compliant,
            'compliant_rate': compliant / len(self.edges) if self.edges else 0
        }
    
    def get_edges_by_quality(self, min_score=None):
        if min_score is None:
            min_score = self.config.min_edge_score
        return [e for e in self.edges if e.get('weight', 0) > min_score]
    
    def save(self, path=None):
        if path is None:
            path = self.config.output_dir / f"graph_vmmp_{datetime.now():%Y%m%d_%H%M%S}.json"
        
        def convert(obj):
            if isinstance(obj, (np.integer,)): return int(obj)
            elif isinstance(obj, (np.floating,)): return float(obj)
            elif isinstance(obj, np.ndarray): return obj.tolist()
            elif isinstance(obj, dict): return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list): return [convert(i) for i in obj]
            return obj
        
        data = {
            'meta': {
                'version': '4.2',
                'engine': 'VMMP (адаптивная, без Гаусса)',
                'created': datetime.now().isoformat(),
                'nodes': len(self.nodes),
                'edges': len(self.edges),
                'furcations': self.furcation_count
            },
            'nodes': {w: {'degree': n['degree']} for w, n in self.nodes.items()},
            'edges': [
                {'source': e['source'], 'tees': e['tees'],
                 'receiver': e['receiver'], 'weight': float(e['weight']),
                 'vmmp_compliant': e['vmmp_compliant']}
                for e in self.edges
            ]
        }
        
        data = convert(data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 Граф сохранён: {path}")
        return path


# ============================================================================
# 8. ФУРКАТОР С ВММП-ТУРБУЛЕНТНОСТЬЮ
# ============================================================================

class Furcator:
    def __init__(self, graph: KnowledgeGraph, config: PipelineConfig, checker: VMMPChecker):
        self.graph = graph
        self.config = config
        self.checker = checker
        self.furcations: List[Dict] = []
    
    def generate_and_apply(self) -> int:
        edges = self.graph.get_edges_by_quality()
        if len(edges) < 2:
            print("  ⚠️ Недостаточно качественных связей для фуркации")
            return 0
        
        print(f"  🔄 ВММП-фуркация из {len(edges)} связей...")
        
        source_index = defaultdict(list)
        for e in edges:
            source_index[e['source']].append(e)
        
        seen = set()
        for e1 in edges:
            if e1['receiver'] not in source_index:
                continue
            for e2 in source_index[e1['receiver']]:
                new_src = e1['source']
                new_dst = e2['receiver']
                new_tees = f"{e1['tees']}⥅{e2['tees']}"
                fur_id = f"{new_src}|{new_tees}|{new_dst}"
                if fur_id in seen or new_src == new_dst:
                    continue
                seen.add(fur_id)
                
                v_src = self.checker.get_vortex(new_src)
                v_dst = self.checker.get_vortex(new_dst)
                pair = np.array([v_src, v_dst])
                turb_pair = vmmp_turbulence(pair, self.config.vortex)
                shift = tees_shift(turb_pair[0], turb_pair[1])
                score = 1.0 - abs(shift)
                
                charge_bonus = 1.0 - abs(
                    e1['charges']['src'] + e1['charges']['tees'] + e1['charges']['rec']
                ) / 3.0
                score = (score + charge_bonus) / 2.0
                
                self.furcations.append({
                    'source': new_src, 'tees': new_tees, 'receiver': new_dst,
                    'score': score, 'type': 'vmmp_turbulence',
                    'parents': [e1['id'], e2['id']]
                })
        
        self.furcations.sort(key=lambda x: x['score'], reverse=True)
        self.furcations = self.furcations[:self.config.furcation_top_k]
        
        triples = [(f['source'], f['tees'], f['receiver']) 
                   for f in self.furcations 
                   if f['score'] >= self.config.min_furcation_score]
        
        if not triples:
            print("  ⚠️ Нет фуркаций, прошедших порог качества")
            return 0
        
        results = self.checker.check_triples_batch(triples)
        
        added = 0
        applicable = [f for f in self.furcations if f['score'] >= self.config.min_furcation_score]
        for fur, result in zip(applicable, results):
            if result['vmmp_compliant']:
                self.graph.add_edge(fur['source'], fur['tees'], fur['receiver'], result,
                                   text_source=f"furcation:{fur['type']}")
                added += 1
                self.graph.furcation_count += 1
        
        if self.furcations:
            print(f"\n  ✨ Топ-5 ВММП-фуркаций:")
            for i, fur in enumerate(self.furcations[:5]):
                status = "✅" if fur['score'] >= self.config.min_furcation_score else "⏳"
                print(f"    {status} {fur['source']} → {fur['tees']} → {fur['receiver']} "
                      f"(τ-score: {fur['score']:.3f})")
        
        print(f"\n  ✅ Применено фуркаций: {added}/{len(triples)}")
        return added


# ============================================================================
# 9. КОНВЕЙЕР
# ============================================================================

def run_pipeline(config: PipelineConfig = None):
    if config is None:
        config = PipelineConfig()
    
    print(MANIFEST)
    print("=" * 70)
    print("🚀 ЗАПУСК КОНВЕЙЕРА (v4.2 — без лимита, адаптивные пороги)")
    print("=" * 70)
    
    if not config.corpus_path.exists():
        print(f"\n❌ Корпус не найден: {config.corpus_path}")
        return None, None
    
    with open(config.corpus_path, 'r', encoding='utf-8') as f:
        corpus = json.load(f)
    
    print(f"\n📚 Корпус загружен: {len(corpus)} текстов")
    
    graph = KnowledgeGraph(config)
    checker = VMMPChecker(config)
    
    print(f"\n{'='*70}")
    print("📝 ИЗВЛЕЧЕНИЕ И ПРОВЕРКА TEES-СТРУКТУР")
    print(f"{'='*70}")
    
    total_triples = 0
    total_compliant = 0
    ru_texts = 0
    en_texts = 0
    
    for name, text in corpus.items():
        structure = TeesParser.parse(text)
        if not structure.get('valid'):
            continue
        
        lang = structure['language']
        if lang == 'ru':
            ru_texts += 1
        else:
            en_texts += 1
        
        triples = structure['triples']
        triple_tuples = [(t['source'], t['tees'], t['receiver']) for t in triples]
        results = checker.check_triples_batch(triple_tuples, lang=lang)
        
        compliant_in_text = 0
        for triple, result in zip(triples, results):
            graph.add_edge(triple['source'], triple['tees'], triple['receiver'], result, name)
            if result['vmmp_compliant']:
                compliant_in_text += 1
        
        total_triples += len(triples)
        total_compliant += compliant_in_text
        
        print(f"  ✅ {name}: {len(triples)} связей (ВММП: {compliant_in_text}) [{lang}]")
    
    # Статистика
    print(f"\n{'='*70}")
    print("📊 СТАТИСТИКА ГРАФА ЗНАНИЙ")
    print(f"{'='*70}")
    
    stats = graph.get_statistics()
    print(f"  Текстов:             {ru_texts + en_texts}")
    print(f"    • Русских (RU):    {ru_texts}")
    print(f"    • Английских (EN): {en_texts}")
    print(f"  Троек извлечено:     {total_triples}")
    print(f"  Узлов:               {stats['total_nodes']}")
    print(f"  Связей (уникальных): {stats['total_edges']}")
    print(f"  Средний вес связи:   {stats['avg_weight']:.3f}")
    if total_triples > 0:
        print(f"  ВММП-согласованных:  {total_compliant} ({total_compliant/total_triples*100:.1f}%)")
    
    # Топ-15 узлов (фильтруем стоп-слова для красоты)
    all_stop_words = TeesParser.STOP_WORDS_RU | TeesParser.STOP_WORDS_EN
    meaningful_nodes = [
        (w, d) for w, d in graph.nodes.items() 
        if w not in all_stop_words and len(w) > 2
    ]
    top_nodes = sorted(meaningful_nodes, key=lambda x: x[1]['degree'], reverse=True)[:15]
    
    print(f"\n  🔝 Топ-15 значимых слов по связям:")
    for word, data in top_nodes:
        print(f"    • {word}: {data['degree']}")
    
    # Адаптивные пороги
    print(f"\n{'='*70}")
    print("📐 АДАПТИВНЫЕ ПОРОГИ (самонастройка)")
    print(f"{'='*70}")
    
    shift_stats = checker.shift_threshold.get_stats()
    charge_stats = checker.charge_threshold.get_stats()
    
    print(f"  TEES-сдвиг:")
    print(f"    • Текущий порог (p85): {shift_stats.get('current_threshold', 0.8):.3f}")
    print(f"    • Медиана (p50):       {shift_stats.get('p50', 0):.3f}")
    print(f"    • Разброс (std):       {shift_stats.get('std', 0):.3f}")
    print(f"    • Всего образцов:      {shift_stats.get('samples', 0)}")
    
    print(f"  Топологический заряд:")
    print(f"    • Текущий порог (p85): {charge_stats.get('current_threshold', 1.0):.3f}")
    print(f"    • Медиана (p50):       {charge_stats.get('p50', 0):.3f}")
    print(f"    • Разброс (std):       {charge_stats.get('std', 0):.3f}")
    print(f"    • Всего образцов:      {charge_stats.get('samples', 0)}")
    
    # Фуркация
    print(f"\n{'='*70}")
    print("🔄 ВММП-ФУРКАЦИЯ (ТОПОЛОГИЧЕСКИЕ ПЕРЕХОДЫ)")
    print(f"{'='*70}")
    
    furcator = Furcator(graph, config, checker)
    added_furcations = furcator.generate_and_apply()
    
    # Сохранение
    print(f"\n{'='*70}")
    print("💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print(f"{'='*70}")
    
    saved_path = graph.save()
    
    # Итоги
    print(f"\n{'='*70}")
    print("✅ КОНВЕЙЕР ЗАВЕРШЁН")
    print(f"{'='*70}")
    print(f"  Обработано текстов:     {ru_texts + en_texts}")
    print(f"  Извлечено троек:        {total_triples}")
    print(f"  ВММП-согласованных:     {total_compliant}")
    print(f"  Фуркаций создано:       {added_furcations}")
    print(f"  Итоговый граф:          {saved_path}")
    print()
    print("  🎯 Гаусс не использовался ни разу.")
    print("  🎯 Пороги самонастроились под корпус.")
    print(f"{'='*70}\n")
    
    return graph, furcator.furcations


# ============================================================================
# 10. ТОЧКА ВХОДА
# ============================================================================

if __name__ == "__main__":
    config = PipelineConfig(
        seed=42,
        furcation_top_k=20,
        min_edge_score=0.25,
        min_furcation_score=0.3,
        cache_size=20000,
        output_dir=Path("./output"),
        corpus_path=Path("./corpus/corpus.json")
    )
    
    graph, furcations = run_pipeline(config)