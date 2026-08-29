#!/usr/bin/env python3
"""
tees_knowledge_engine_v5_6_fixed.py — БОЕВАЯ ВЕРСИЯ С ИСПРАВЛЕНИЯМИ
===========================================================================
Исправлено:
- fast_16bit_hash: обрезание только в конце
- check_triples_batch: очистка словаря vortices
- load_checkpoint: обработка битых файлов
- Добавлен gc.collect() после каждого файла
- Проверка импорта numpy
- Улучшена загрузка корпуса
"""

import json
import re
import hashlib
import time
import pickle
import sys
import warnings
import gc

# Проверка numpy
try:
    import numpy as np
except ImportError:
    print("❌ Требуется numpy. Установите: pip install numpy scipy")
    sys.exit(1)

try:
    from scipy.ndimage import maximum_filter, minimum_filter, label
except ImportError:
    print("❌ Требуется scipy. Установите: pip install scipy")
    sys.exit(1)

from pathlib import Path
from collections import defaultdict, deque, Counter
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from functools import lru_cache
from datetime import datetime

warnings.filterwarnings('ignore')

# ============================================================================
# 1. КОНСТАНТЫ
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

IDX_SIZE = 65536
IDX_MASK = 0xFFFF

def fast_16bit_hash(s: str) -> int:
    """Быстрый 16-битный хеш — обрезание только в конце."""
    h = 0
    for ch in s:
        h = ((h << 5) + h) ^ ord(ch)
        h = h & 0xFFFFFFFF  # Держим 32 бита внутри цикла
    return h & IDX_MASK  # Обрезаем до 16 бит только в конце

# ============================================================================
# 2. ВММП-ЯДРО
# ============================================================================

@dataclass
class VortexConfig:
    grid_size: int = 16
    turbulence_threshold: float = 0.5
    turbulence_intensity: float = 0.3
    dtype: type = np.float32
    
    def __post_init__(self):
        gs = int(self.grid_size)
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
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        self._cached_threshold = 0.8
        self._sample_count = 0
    
    def update(self, value: float):
        self.values.append(abs(value))
        self._sample_count += 1
    
    def get_threshold(self, percentile: float = 85) -> float:
        if len(self.values) < 10:
            return 0.8
        if self._sample_count % 100 == 0 or self._sample_count < 10:
            data = np.array(list(self.values))
            self._cached_threshold = float(np.percentile(data, percentile))
        return self._cached_threshold

# ============================================================================
# 4. TEES-ПАРСЕР
# ============================================================================

class TeesParser:
    RU_VERB_ENDINGS = (
        'ть', 'тся', 'ться', 'л', 'ла', 'ло', 'ли',
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
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
        'can', 'could', 'will', 'would', 'shall', 'should',
        'may', 'might', 'must', 'make', 'makes', 'made',
        'take', 'takes', 'took', 'give', 'gives', 'gave',
        'go', 'goes', 'went', 'come', 'comes', 'came',
        'know', 'knows', 'knew', 'see', 'sees', 'saw',
        'get', 'gets', 'got', 'use', 'uses', 'used',
        'find', 'finds', 'found', 'show', 'shows', 'showed',
        'provide', 'provides', 'create', 'creates', 'created',
        'develop', 'develops', 'include', 'includes', 'included',
        'describe', 'describes', 'demonstrate', 'demonstrates',
        'represent', 'represents', 'define', 'defines',
        'explain', 'explains', 'present', 'presents',
        'study', 'studies', 'propose', 'proposes',
        'introduce', 'introduces', 'produce', 'produces',
        'generate', 'generates', 'form', 'forms', 'establish', 'establishes',
    })
    
    EN_NOUN_TEES = frozenset({
        'part', 'form', 'type', 'kind', 'use', 'result',
        'effect', 'cause', 'basis', 'method', 'process',
        'model', 'system', 'structure', 'function',
        'analysis', 'research', 'theory',
        'application', 'approach', 'component', 'example',
        'case', 'set', 'group', 'class', 'level', 'state',
    })
    
    EN_VERB_SUFFIXES = ('s', 'es', 'ed', 'ing')
    
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
        'this', 'that', 'these', 'those', 'not', 'no', 'yes',
        'very', 'just', 'only', 'also', 'all', 'some', 'any',
        'each', 'every', 'who', 'which', 'what', 'when',
        'where', 'why', 'how', 'his', 'her', 'its', 'their', 'our', 'my', 'your',
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
        return (any(word_clean.endswith(end) for end in cls.RU_VERB_ENDINGS) or
                word_clean in cls.RU_NOUN_TEES)
    
    @classmethod
    def is_tees_en_auto(cls, word: str) -> bool:
        w = word.lower()
        if w in cls.EN_TEES_WORDS:
            return True
        if w in cls.EN_NOUN_TEES:
            return True
        if len(w) > 3 and any(w.endswith(suf) for suf in cls.EN_VERB_SUFFIXES):
            return True
        return False
    
    @classmethod
    def parse(cls, text: str) -> dict:
        if not text or len(text.strip()) < 30:
            return {'valid': False}
        
        # Валидация: проверяем, что текст не бинарный мусор
        try:
            text.encode('utf-8')
        except UnicodeEncodeError:
            return {'valid': False}
        
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
            for i in range(1, len(words) - 1):
                word = words[i]
                if is_russian:
                    is_explicit = cls.is_tees_ru(word)
                else:
                    is_explicit = cls.is_tees_en_auto(word)
                is_auto = False
                if not is_explicit:
                    left_word = words[i - 1]
                    right_word = words[i + 1]
                    if (left_word not in stop_words and len(left_word) > 2 and
                        right_word not in stop_words and len(right_word) > 2):
                        if not is_russian:
                            if cls.is_tees_en_auto(word):
                                is_auto = True
                        else:
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
                all_triples.append({
                    'source': words[source_idx],
                    'tees': word,
                    'receiver': words[receiver_idx],
                })
        if not all_triples:
            return {'valid': False}
        return {'valid': True, 'language': language, 'triples': all_triples}

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
    grace_period: int = 5
    maturity_age: int = 15
    archive_age: int = 25
    mature_decay: float = 0.8
    old_decay: float = 0.5
    archive_weight: float = 0.001
    cache_size: int = 20000
    output_dir: Path = Path("./output")
    checkpoint_dir: Path = Path("./output/checkpoints")
    corpus_path: Path = Path("./corpus")
    
    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 6. ВММП-ПРОВЕРКА
# ============================================================================

class VMMPChecker:
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.vortex_config = self.config.vortex
        self.seed = self.config.seed
        self._stats = defaultdict(int)
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
            self._cached_compute = lru_cache(maxsize=self.config.cache_size)(self._compute_vortex_raw)
        return self._cached_compute(word_hash)
    
    def check_triples_batch(self, triples: List[Tuple[str, str, str]], lang: str = None) -> List[Dict]:
        if not triples:
            return []
        words = set()
        for s, t, r in triples:
            words.update([s, t, r])
        
        # Создаем словарь вихрей
        vortices = {w: self.get_vortex(w) for w in words}
        charges = {w: compute_topological_charge(vortices[w]) for w in words}
        
        results = []
        for source, tees, receiver in triples:
            src_v = vortices[source]; tee_v = vortices[tees]; rec_v = vortices[receiver]
            src_c = charges[source]; tee_c = charges[tees]; rec_c = charges[receiver]
            shift_src = tees_shift(src_v, tee_v)
            shift_rec = tees_shift(tee_v, rec_v)
            total_charge = src_c + tee_c + rec_c
            charge_limit = self.charge_threshold.get_threshold(85)
            shift_limit = self.shift_threshold.get_threshold(85)
            is_balanced = abs(total_charge) < charge_limit
            is_connected = abs(shift_src) < shift_limit and abs(shift_rec) < shift_limit
            score = 1.0 - (abs(shift_src) + abs(shift_rec)) / 2.0
            if not is_balanced:
                score *= 0.7
            score = max(0.0, min(1.0, score))
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
        
        # Явно очищаем словарь вихрей
        del vortices
        del charges
        
        return results

# ============================================================================
# 7. ГРАФ С 16-БИТНЫМ ИНДЕКСОМ И ЧЕКПОЙНТАМИ
# ============================================================================

class VMMPGraph:
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.nodes: Dict[str, Dict] = {}
        self._buckets: List[List[Dict]] = [[] for _ in range(IDX_SIZE)]
        self.edges: List[Dict] = []
        self.dormant_edges: List[Dict] = []
        self.furcation_count = 0
        self.total_hibernated = 0
        self.total_awakened = 0
        self.total_rejuvenated = 0
        self.processed_files: Set[str] = set()
    
    def _bucket_key(self, source: str, tees: str, receiver: str) -> int:
        return fast_16bit_hash(f"{source}|{tees}|{receiver}") % IDX_SIZE
    
    def _find_in_bucket(self, bucket_idx: int, source: str, tees: str, receiver: str) -> Optional[Dict]:
        for edge in self._buckets[bucket_idx]:
            if edge['source'] == source and edge['tees'] == tees and edge['receiver'] == receiver:
                return edge
        return None
    
    def add_edge(self, source, tees, receiver, check_result, text_source=None):
        bucket_idx = self._bucket_key(source, tees, receiver)
        existing = self._find_in_bucket(bucket_idx, source, tees, receiver)
        
        if existing:
            existing['weight'] += check_result['score']
            if check_result['vmmp_compliant']:
                existing['age'] = 0
                existing['vmmp_compliant'] = True
                self.total_rejuvenated += 1
            if text_source:
                existing['sources'].append(text_source)
        else:
            edge = {
                'id': f"{source}|{tees}|{receiver}",
                'source': source, 'tees': tees, 'receiver': receiver,
                'weight': check_result['score'],
                'age': 0,
                'vmmp_compliant': check_result['vmmp_compliant'],
                'sources': [text_source] if text_source else [],
                'charges': {
                    'src': check_result['src_charge'],
                    'tees': check_result['tees_charge'],
                    'rec': check_result['rec_charge']
                }
            }
            self._buckets[bucket_idx].append(edge)
            self.edges.append(edge)
        
        for w in [source, tees, receiver]:
            if w and w.strip():
                if w not in self.nodes:
                    self.nodes[w] = {'degree': 0}
                self.nodes[w]['degree'] += 1
    
    def decay_noise(self) -> int:
        to_hibernate = []
        for i, edge in enumerate(self.edges):
            if edge.get('vmmp_compliant', False):
                continue
            age = edge.get('age', 0)
            edge['age'] = age + 1
            if age < self.config.grace_period:
                continue
            elif age < self.config.maturity_age:
                edge['weight'] *= self.config.mature_decay
            elif age < self.config.archive_age:
                edge['weight'] *= self.config.old_decay
            else:
                if edge['weight'] < self.config.archive_weight:
                    to_hibernate.append(i)
        
        for i in reversed(to_hibernate):
            edge = self.edges.pop(i)
            bucket_idx = self._bucket_key(edge['source'], edge['tees'], edge['receiver'])
            self._buckets[bucket_idx] = [e for e in self._buckets[bucket_idx] if e['id'] != edge['id']]
            edge['hibernated_at'] = datetime.now().isoformat()
            self.dormant_edges.append(edge)
            self.total_hibernated += 1
        
        return len(to_hibernate)
    
    def save_checkpoint(self, filepath: Path):
        """Сохраняет чекпойнт с атомарной записью."""
        tmp_path = filepath.with_suffix('.tmp')
        try:
            with open(tmp_path, 'wb') as f:
                pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
            tmp_path.replace(filepath)  # Атомарная замена
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise IOError(f"Ошибка сохранения чекпойнта: {e}")
    
    @classmethod
    def load_checkpoint(cls, filepath: Path) -> Optional['VMMPGraph']:
        """Загружает чекпойнт с обработкой битых файлов."""
        if not filepath.exists():
            print(f"⚠️  Чекпойнт не найден: {filepath}")
            return None
        
        try:
            with open(filepath, 'rb') as f:
                graph = pickle.load(f)
            
            # Проверяем, что загрузился именно VMMPGraph
            if not isinstance(graph, cls):
                print(f"⚠️  Файл {filepath} содержит объект другого типа: {type(graph)}")
                return None
            
            print(f"✅ Чекпойнт загружен: {filepath.name}")
            return graph
        
        except (pickle.UnpicklingError, EOFError, ValueError) as e:
            print(f"❌ Чекпойнт повреждён ({filepath.name}): {e}")
            # Пробуем загрузить предыдущий чекпойнт
            backup = filepath.with_name(filepath.stem + "_backup.pkl")
            if backup.exists():
                print(f"🔄 Пробую резервную копию: {backup.name}")
                return cls.load_checkpoint(backup)
            return None
        
        except Exception as e:
            print(f"❌ Неизвестная ошибка при загрузке чекпойнта: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        compliant = [e for e in self.edges if e.get('vmmp_compliant')]
        noise = [e for e in self.edges if not e.get('vmmp_compliant')]
        weights = [e['weight'] for e in self.edges]
        return {
            'total_nodes': len(self.nodes),
            'active_edges': len(self.edges),
            'dormant_edges': len(self.dormant_edges),
            'compliant_edges': len(compliant),
            'noise_edges': len(noise),
            'compliant_rate': len(compliant) / len(self.edges) if self.edges else 0,
            'avg_weight': float(np.mean(weights)) if weights else 0,
            'total_hibernated': self.total_hibernated,
            'total_awakened': self.total_awakened,
            'total_rejuvenated': self.total_rejuvenated,
        }
    
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
        
        stats = self.get_statistics()
        data = {
            'meta': {'version': '5.6-fixed', 'created': datetime.now().isoformat()},
            'stats': stats,
            'active_edges': [
                {'source': e['source'], 'tees': e['tees'], 'receiver': e['receiver'],
                 'weight': float(e['weight']), 'age': e.get('age', 0),
                 'vmmp_compliant': e['vmmp_compliant']}
                for e in self.edges
            ],
            'dormant_edges': [
                {'source': e['source'], 'tees': e['tees'], 'receiver': e['receiver'],
                 'weight': float(e['weight']), 'age': e.get('age', 0)}
                for e in self.dormant_edges
            ]
        }
        data = convert(data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

# ============================================================================
# 8. КОНВЕЙЕР С ЧЕКПОЙНТАМИ
# ============================================================================

def run_pipeline(config: PipelineConfig = None):
    if config is None:
        config = PipelineConfig()
    
    print("=" * 70)
    print("v5.6-fixed — БОЕВАЯ ВЕРСИЯ С ИСПРАВЛЕНИЯМИ")
    print("=" * 70)
    
    # Загрузка корпуса
    corpus = {}
    
    # Приоритет: JSON-корпус
    if config.corpus_path.suffix == '.json' and config.corpus_path.exists():
        try:
            with open(config.corpus_path, 'r', encoding='utf-8') as f:
                corpus = json.load(f)
            print(f"\n📚 Загружен JSON-корпус: {len(corpus)} текстов")
        except Exception as e:
            print(f"⚠️  Ошибка загрузки JSON-корпуса: {e}")
    
    # Если JSON не загрузился или это директория, ищем TXT
    if not corpus and config.corpus_path.is_dir():
        txt_files = list(config.corpus_path.glob("*.txt"))
        if not txt_files:
            # Пробуем ./corpus как запасной вариант
            fallback = Path("./corpus")
            if fallback.is_dir():
                txt_files = list(fallback.glob("*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                if len(text.strip()) > 30:
                    corpus[txt_file.stem] = text
            except Exception as e:
                print(f"⚠️  Ошибка чтения {txt_file.name}: {e}")
        
        if txt_files:
            print(f"📚 Загружено TXT-файлов: {len(corpus)}")
    
    if not corpus:
        print("❌ Корпус не найден! Поместите тексты в ./corpus/ или укажите JSON-файл.")
        return
    
    print(f"📚 Всего текстов: {len(corpus)}")
    
    # Проверка чекпойнта
    last_checkpoint = None
    checkpoints = sorted(config.checkpoint_dir.glob("checkpoint_*.pkl"))
    
    # Фильтруем битые чекпойнты
    valid_checkpoints = [cp for cp in checkpoints if cp.stat().st_size > 0]
    
    if valid_checkpoints:
        last_checkpoint = valid_checkpoints[-1]
        print(f"💾 Найден чекпойнт: {last_checkpoint.name}")
        graph = VMMPGraph.load_checkpoint(last_checkpoint)
        
        if graph is None:
            # Пробуем предпоследний
            if len(valid_checkpoints) > 1:
                last_checkpoint = valid_checkpoints[-2]
                print(f"🔄 Пробую предыдущий: {last_checkpoint.name}")
                graph = VMMPGraph.load_checkpoint(last_checkpoint)
        
        if graph is None:
            print("⚠️  Все чекпойнты повреждены, начинаю с чистого графа")
            graph = VMMPGraph(config)
        else:
            print(f"   Восстановлено: {len(graph.edges)} связей, {graph.total_hibernated} в архиве")
    else:
        graph = VMMPGraph(config)
    
    checker = VMMPChecker(config)
    
    total_triples = 0
    total_compliant = 0
    ru_texts = en_texts = 0
    ru_triples = en_triples = 0
    ru_compliant = en_compliant = 0
    
    items = list(corpus.items())
    start_time = time.time()
    
    for idx, (name, text) in enumerate(items):
        # Пропускаем уже обработанные
        if name in graph.processed_files:
            continue
        
        # Валидация текста
        if not isinstance(text, str) or len(text.strip()) < 30:
            graph.processed_files.add(name)
            continue
        
        structure = TeesParser.parse(text)
        if not structure.get('valid'):
            graph.processed_files.add(name)
            continue
        
        lang = structure['language']
        is_ru = (lang == 'ru')
        if is_ru: ru_texts += 1
        else: en_texts += 1
        
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
        if is_ru:
            ru_triples += len(triples)
            ru_compliant += compliant_in_text
        else:
            en_triples += len(triples)
            en_compliant += compliant_in_text
        
        graph.decay_noise()
        graph.processed_files.add(name)
        
        # Принудительная сборка мусора после каждого файла
        gc.collect()
        
        # Прогресс-бар
        pct = (idx + 1) / len(items) * 100
        bar_len = 20
        filled = int(bar_len * (idx + 1) / len(items))
        bar = '█' * filled + '░' * (bar_len - filled)
        
        elapsed = time.time() - start_time
        if idx > 0:
            eta = elapsed / (idx + 1) * (len(items) - idx - 1)
            eta_str = f" | ETA: {eta/60:.1f} мин"
        else:
            eta_str = ""
        
        print(f"\r  Прогресс: [{bar}] {idx+1}/{len(items)} ({pct:.1f}%) | "
              f"RAM: {graph.get_statistics()['active_edges']} связей{eta_str}", end='')
        
        # Чекпойнт каждые 10 файлов
        if (idx + 1) % 10 == 0:
            checkpoint_path = config.checkpoint_dir / f"checkpoint_{idx+1:04d}.pkl"
            try:
                graph.save_checkpoint(checkpoint_path)
                print(f"\n  💾 Чекпойнт сохранён: {checkpoint_path.name}")
            except Exception as e:
                print(f"\n  ⚠️  Ошибка сохранения чекпойнта: {e}")
            
            # Дополнительная очистка
            gc.collect()
    
    print("\n")
    
    # Финальная статистика
    elapsed_total = time.time() - start_time
    stats = graph.get_statistics()
    
    print(f"  ⏱️  Общее время:       {elapsed_total/60:.1f} мин")
    print(f"  Извлечено троек:     {total_triples}")
    if total_triples > 0:
        print(f"  ВММП-согласованных:  {total_compliant} ({total_compliant/total_triples*100:.1f}%)")
    if ru_triples > 0:
        print(f"  🇷🇺 Русский:          {ru_compliant}/{ru_triples} ({ru_compliant/ru_triples*100:.1f}%)")
    if en_triples > 0:
        print(f"  🇬🇧 Английский:       {en_compliant}/{en_triples} ({en_compliant/en_triples*100:.1f}%)")
    print(f"  Активных связей:     {stats['active_edges']} (истина: {stats['compliant_edges']}, шум: {stats['noise_edges']})")
    print(f"  😴 В архиве:         {stats['dormant_edges']}")
    
    # Сохранение графа
    try:
        saved_path = graph.save()
        print(f"  💾 Граф сохранён:    {saved_path}")
    except Exception as e:
        print(f"  ⚠️  Ошибка сохранения графа: {e}")
    
    # Финальный чекпойнт
    final_checkpoint = config.checkpoint_dir / f"checkpoint_final.pkl"
    try:
        graph.save_checkpoint(final_checkpoint)
        print(f"  💾 Финальный чекпойнт: {final_checkpoint.name}")
    except Exception as e:
        print(f"  ⚠️  Ошибка сохранения финального чекпойнта: {e}")
    
    print(f"\n{'='*70}")
    print(f"✅ ГОТОВО (v5.6-fixed)")
    print(f"{'='*70}")
    
    return graph

if __name__ == "__main__":
    config = PipelineConfig(
        seed=42,
        output_dir=Path("./output"),
        checkpoint_dir=Path("./output/checkpoints"),
        corpus_path=Path("./corpus")
    )
    run_pipeline(config)