#!/usr/bin/env python3
"""
tees_knowledge_engine_v5_5.py — ВММП с дормантным архивом
===========================================================
✅ ВММП-энтропия (без Гаусса!)
✅ Адаптивные пороги
✅ Глубина без лимита
✅ Раздельная статистика RU/EN
✅ Топ концептов (без стоп-слов и TEES)
✅ Истина вечна
✅ Память поколений:
   - 👶 0-5 текстов: юность, иммунитет
   - 🧑 5-15: зрелость, мягкое затухание
   - 👴 15-25: старость, усиленное затухание
   - 😴 25+: дормантный архив (НЕ удаляется!)
✅ Пробуждение из архива:
   - Прямое: try_awaken(source, tees, receiver)
   - Контекстное: awaken_by_context(words)
   - Массовое: awaken_all() — гипноз всего архива
✅ Омоложение ТОЛЬКО при ВММП-подтверждении
✅ Фуркации только на истине
"""

import json
import re
import hashlib
import time
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


def tees_shift_bytes(a_bytes: bytes, b_bytes: bytes) -> float:
    ha = simple_tees_hash(a_bytes)
    hb = simple_tees_hash(b_bytes)
    combined = (ha << 32) | (hb & 0xFFFFFFFF)
    flow = simple_tees_hash(combined.to_bytes(8, 'big'))
    na = simple_tees_hash(ha.to_bytes(4, 'big'), flow)
    nb = simple_tees_hash(hb.to_bytes(4, 'big'), flow)
    before = (ha ^ hb).bit_count() / 32.0
    after = (na ^ nb).bit_count() / 32.0
    return after - before


def tees_shift(state_a: np.ndarray, state_b: np.ndarray) -> float:
    return tees_shift_bytes(state_a.tobytes(), state_b.tobytes())


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
            'samples': len(data), 'mean': float(np.mean(data)), 'std': float(np.std(data)),
            'p50': float(np.percentile(data, 50)), 'p75': float(np.percentile(data, 75)),
            'p85': float(np.percentile(data, 85)), 'current_threshold': self._cached_threshold,
        }


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
    
    # Поколения памяти
    grace_period: int = 5
    maturity_age: int = 15
    archive_age: int = 25
    mature_decay: float = 0.8
    old_decay: float = 0.5
    archive_weight: float = 0.001
    
    # Пробуждение
    awakening_intensity: float = 1.0     # Сила прямого пробуждения
    context_awakening: float = 0.5        # Сила контекстного пробуждения
    awakening_age_reset: int = 20         # Возраст после пробуждения
    
    cache_size: int = 20000
    output_dir: Path = Path("./output")
    corpus_path: Path = Path("./corpus")
    
    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


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
        return results


# ============================================================================
# 7. ГРАФ С ДОРМАНТНЫМ АРХИВОМ
# ============================================================================

class VMMPGraph:
    """
    Граф с дормантным архивом.
    
    Активные связи: живут, затухают, участвуют в фуркациях.
    Дормантный архив: уснувшие связи, которые МОЖНО пробудить.
    
    Ни одна связь не удаляется навсегда — только засыпает.
    """
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []              # Активные связи
        self.dormant_edges: List[Dict] = []      # 😴 Архив уснувших
        self._edge_index: Dict[str, int] = {}    # Индекс активных
        self._dormant_index: Dict[str, int] = {} # Индекс дормантных
        self.furcation_count = 0
        self.total_hibernated = 0
        self.total_awakened = 0
        self.total_rejuvenated = 0
    
    def add_edge(self, source, tees, receiver, check_result, text_source=None):
        edge_id = f"{source}|{tees}|{receiver}"
        
        # Проверяем в дормантном архиве
        if edge_id in self._dormant_index:
            # Не пробуждаем автоматически — только если ВММП подтвердит
            if check_result['vmmp_compliant']:
                self._awaken_from_dormant(edge_id, check_result)
            return
        
        # Проверяем в активных
        if edge_id in self._edge_index:
            idx = self._edge_index[edge_id]
            self.edges[idx]['weight'] += check_result['score']
            
            # Омоложение ТОЛЬКО при ВММП-подтверждении
            if check_result['vmmp_compliant']:
                self.edges[idx]['age'] = 0
                self.edges[idx]['vmmp_compliant'] = True
                self.total_rejuvenated += 1
            
            if text_source:
                self.edges[idx]['sources'].append(text_source)
        else:
            # Новая связь
            self._edge_index[edge_id] = len(self.edges)
            self.edges.append({
                'id': edge_id,
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
            })
        
        for w in [source, tees, receiver]:
            if w and w.strip():
                if w not in self.nodes:
                    self.nodes[w] = {'degree': 0}
                self.nodes[w]['degree'] += 1
    
    def _awaken_from_dormant(self, edge_id: str, check_result: Dict):
        """Пробуждает связь из дормантного архива."""
        idx = self._dormant_index[edge_id]
        edge = self.dormant_edges.pop(idx)
        
        edge['weight'] = check_result['score']
        edge['age'] = 0
        edge['vmmp_compliant'] = True
        edge['awakened_at'] = datetime.now().isoformat()
        
        self._edge_index[edge_id] = len(self.edges)
        self.edges.append(edge)
        self.total_awakened += 1
        
        # Обновляем индекс дормантных
        self._dormant_index = {e['id']: j for j, e in enumerate(self.dormant_edges)}
    
    def decay_noise(self) -> int:
        """Затухание шума. Усыпление в архив вместо удаления."""
        to_hibernate = []
        
        for i, edge in enumerate(self.edges):
            if edge.get('vmmp_compliant', False):
                continue  # Истина вечна
            
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
        
        # Усыпляем (НЕ удаляем!)
        for i in reversed(to_hibernate):
            edge = self.edges.pop(i)
            edge['hibernated_at'] = datetime.now().isoformat()
            self.dormant_edges.append(edge)
            self.total_hibernated += 1
        
        # Обновляем индексы
        self._edge_index = {e['id']: j for j, e in enumerate(self.edges)}
        self._dormant_index = {e['id']: j for j, e in enumerate(self.dormant_edges)}
        
        return len(to_hibernate)
    
    def try_awaken(self, source: str, tees: str, receiver: str,
                   intensity: float = None) -> Optional[Dict]:
        """
        Прямое пробуждение конкретной связи.
        Как целенаправленное воспоминание.
        """
        if intensity is None:
            intensity = self.config.awakening_intensity
        
        edge_id = f"{source}|{tees}|{receiver}"
        
        if edge_id in self._dormant_index:
            idx = self._dormant_index[edge_id]
            edge = self.dormant_edges.pop(idx)
            
            edge['weight'] *= (1.0 + intensity)
            edge['age'] = self.config.awakening_age_reset
            edge['awakened_at'] = datetime.now().isoformat()
            edge['awakened_by'] = 'direct'
            
            self._edge_index[edge_id] = len(self.edges)
            self.edges.append(edge)
            self.total_awakened += 1
            
            self._dormant_index = {e['id']: j for j, e in enumerate(self.dormant_edges)}
            return edge
        
        return None
    
    def awaken_by_context(self, context_words: List[str],
                         intensity: float = None) -> List[str]:
        """
        Контекстное пробуждение: все дормантные связи с этими словами.
        Как запах или звук, пробуждающий воспоминания.
        """
        if intensity is None:
            intensity = self.config.context_awakening
        
        awakened = []
        to_awaken = []
        
        for i, edge in enumerate(self.dormant_edges):
            edge_text = f"{edge['source']} {edge['tees']} {edge['receiver']}"
            if any(w.lower() in edge_text.lower() for w in context_words):
                to_awaken.append(i)
        
        for i in reversed(to_awaken):
            edge = self.dormant_edges.pop(i)
            edge['weight'] *= (1.0 + intensity)
            edge['age'] = self.config.awakening_age_reset
            edge['awakened_at'] = datetime.now().isoformat()
            edge['awakened_by'] = f"context: {','.join(context_words[:3])}"
            
            self._edge_index[edge['id']] = len(self.edges)
            self.edges.append(edge)
            awakened.append(edge['id'])
            self.total_awakened += 1
        
        self._dormant_index = {e['id']: j for j, e in enumerate(self.dormant_edges)}
        return awakened
    
    def awaken_all(self, intensity: float = 0.3) -> int:
        """
        Массовое пробуждение ВСЕГО архива.
        Как гипноз — временно возвращает всё.
        """
        count = len(self.dormant_edges)
        
        for edge in self.dormant_edges:
            edge['weight'] *= (1.0 + intensity)
            edge['age'] = self.config.awakening_age_reset
            edge['awakened_at'] = datetime.now().isoformat()
            edge['awakened_by'] = 'mass_awakening'
            
            self._edge_index[edge['id']] = len(self.edges)
            self.edges.append(edge)
            self.total_awakened += 1
        
        self.dormant_edges.clear()
        self._dormant_index.clear()
        
        return count
    
    def get_edges_for_furcation(self, min_score=None):
        if min_score is None:
            min_score = self.config.min_edge_score
        return [
            e for e in self.edges
            if e.get('vmmp_compliant', False) and e.get('weight', 0) > min_score
        ]
    
    def get_statistics(self) -> Dict:
        if not self.nodes:
            return {'total_nodes': 0, 'active_edges': 0, 'dormant_edges': 0,
                    'compliant_edges': 0, 'noise_edges': 0, 'compliant_rate': 0}
        compliant = [e for e in self.edges if e.get('vmmp_compliant')]
        noise = [e for e in self.edges if not e.get('vmmp_compliant')]
        weights = [e['weight'] for e in self.edges]
        
        age_distribution = Counter()
        for e in noise:
            age = e.get('age', 0)
            if age < self.config.grace_period:
                age_distribution['👶 юность'] += 1
            elif age < self.config.maturity_age:
                age_distribution['🧑 зрелость'] += 1
            elif age < self.config.archive_age:
                age_distribution['👴 старость'] += 1
            else:
                age_distribution['😴 дормант'] += 1
        
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
            'age_distribution': dict(age_distribution),
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
            'meta': {'version': '5.5', 'created': datetime.now().isoformat()},
            'stats': stats,
            'active_edges': [
                {'source': e['source'], 'tees': e['tees'], 'receiver': e['receiver'],
                 'weight': float(e['weight']), 'age': e.get('age', 0),
                 'vmmp_compliant': e['vmmp_compliant']}
                for e in self.edges
            ],
            'dormant_edges': [
                {'source': e['source'], 'tees': e['tees'], 'receiver': e['receiver'],
                 'weight': float(e['weight']), 'age': e.get('age', 0),
                 'hibernated_at': e.get('hibernated_at')}
                for e in self.dormant_edges
            ]
        }
        data = convert(data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


# ============================================================================
# 8. ФУРКАТОР
# ============================================================================

class Furcator:
    def __init__(self, graph: VMMPGraph, config: PipelineConfig, checker: VMMPChecker):
        self.graph = graph
        self.config = config
        self.checker = checker
        self.furcations: List[Dict] = []
    
    def generate_and_apply(self) -> int:
        edges = self.graph.get_edges_for_furcation()
        if len(edges) < 2:
            return 0
        
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
        
        return added


# ============================================================================
# 9. КОНВЕЙЕР
# ============================================================================

def run_pipeline(config: PipelineConfig = None):
    if config is None:
        config = PipelineConfig()
    
    print("=" * 70)
    print("v5.5 — ДОРМАНТНЫЙ АРХИВ (ничто не удаляется навсегда)")
    print("=" * 70)
    
    if not config.corpus_path.exists():
        print(f"\n❌ Корпус не найден: {config.corpus_path}")
        return None, None

    with open(config.corpus_path, 'r', encoding='utf-8') as f:
        corpus = json.load(f)

    # ЗАМЕНИТЬ НА:
    corpus = {}

    # 1. Пробуем загрузить JSON если указан
    if config.corpus_path.suffix == '.json' and config.corpus_path.exists():
        with open(config.corpus_path, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        print(f"\n📚 Загружен JSON-корпус: {len(corpus)} текстов")

    # 2. Пробуем загрузить TXT из директории corpus/
    txt_dir = Path("./corpus")
    if txt_dir.exists():
        txt_files = list(txt_dir.glob("*.txt"))
        if txt_files:
            for txt_file in txt_files:
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        text = f.read()
                    if len(text.strip()) > 30:
                        name = txt_file.stem
                        corpus[name] = text
                except:
                    pass
            if txt_files:
                print(f"📚 Загружено TXT-файлов: {len(txt_files)}")

    # 3. Пробуем загрузить из директории (если указан путь к папке)
    if config.corpus_path.is_dir():
        for ext in ['*.txt', '*.json']:
            for f in config.corpus_path.glob(ext):
                try:
                    if ext == '*.json':
                        with open(f, 'r', encoding='utf-8') as fp:
                            data = json.load(fp)
                            if isinstance(data, dict):
                                corpus.update(data)
                    else:
                        with open(f, 'r', encoding='utf-8') as fp:
                            text = fp.read()
                        if len(text.strip()) > 30:
                            corpus[f.stem] = text
                except:
                    pass

    if not corpus:
        print(f"\n❌ Корпус не найден!")
        return None, None

    print(f"\n📚 Корпус загружен: {len(corpus)} текстов")
    
    graph = VMMPGraph(config)
    checker = VMMPChecker(config)
    
    total_triples = 0
    total_compliant = 0
    ru_texts = en_texts = 0
    ru_triples = en_triples = 0
    ru_compliant = en_compliant = 0
    
    for name, text in corpus.items():
        structure = TeesParser.parse(text)
        if not structure.get('valid'):
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
    
    stats = graph.get_statistics()
    
    print(f"\n  Извлечено троек:     {total_triples}")
    if total_triples > 0:
        print(f"  ВММП-согласованных:  {total_compliant} ({total_compliant/total_triples*100:.1f}%)")
    if ru_triples > 0:
        print(f"  🇷🇺 Русский:          {ru_compliant}/{ru_triples} ({ru_compliant/ru_triples*100:.1f}%)")
    if en_triples > 0:
        print(f"  🇬🇧 Английский:       {en_compliant}/{en_triples} ({en_compliant/en_triples*100:.1f}%)")
    print(f"  Активных связей:     {stats['active_edges']} (истина: {stats['compliant_edges']}, шум: {stats['noise_edges']})")
    print(f"  😴 В архиве:         {stats['dormant_edges']}")
    print(f"  Усыплено за всё время: {stats['total_hibernated']}")
    
    # Тест пробуждения
    print(f"\n  🧪 Тест пробуждения из архива...")
    
    # Контекстное пробуждение
    awakened = graph.awaken_by_context(['quantum', 'energy', 'consciousness'])
    print(f"  ⚡ Контекст ['quantum', 'energy', 'consciousness']: {len(awakened)} пробуждено")
    
    # Прямое пробуждение
    if graph.dormant_edges:
        first = graph.dormant_edges[0]
        graph.try_awaken(first['source'], first['tees'], first['receiver'])
        print(f"  ⚡ Прямое пробуждение '{first['source']} → {first['tees']} → {first['receiver']}': OK")
    
    # Статистика после пробуждений
    stats = graph.get_statistics()
    print(f"  После пробуждений: {stats['active_edges']} активно, {stats['dormant_edges']} в архиве")
    print(f"  Всего пробуждено: {stats['total_awakened']}")
    print(f"  Омоложено:        {stats['total_rejuvenated']}")
    
    # Пороги
    shift_stats = checker.shift_threshold.get_stats()
    charge_stats = checker.charge_threshold.get_stats()
    print(f"\n  📐 Пороги: сдвиг={shift_stats.get('current_threshold', 0.8):.3f}, "
          f"заряд={charge_stats.get('current_threshold', 1.0):.3f}")
    
    # Топ концептов
    NOISE_WORDS = (TeesParser.STOP_WORDS_RU | TeesParser.STOP_WORDS_EN |
                   TeesParser.EN_TEES_WORDS | TeesParser.EN_NOUN_TEES)
    meaningful = [(w, d) for w, d in graph.nodes.items()
                  if w not in NOISE_WORDS and len(w) > 3 and not w.isdigit()]
    top_concepts = sorted(meaningful, key=lambda x: x[1]['degree'], reverse=True)[:20]
    
    print(f"\n  🔝 Топ-20 концептов:")
    for word, data in top_concepts:
        print(f"    • {word}: {data['degree']}")
    
    # Фуркация
    furcator = Furcator(graph, config, checker)
    added_furcations = furcator.generate_and_apply()
    
    saved_path = graph.save()
    
    print(f"\n{'='*70}")
    print(f"✅ ГОТОВО")
    print(f"{'='*70}")
    print(f"  Текстов:        {ru_texts + en_texts} (RU:{ru_texts} EN:{en_texts})")
    print(f"  Троек:          {total_triples}")
    print(f"  Активно:        {stats['active_edges']} (истина: {stats['compliant_edges']})")
    print(f"  В архиве:       {stats['dormant_edges']}")
    print(f"  Усыплено:       {stats['total_hibernated']}")
    print(f"  Пробуждено:     {stats['total_awakened']}")
    print(f"  Омоложено:      {stats['total_rejuvenated']}")
    print(f"  Фуркаций:       {added_furcations}")
    print(f"  Граф:           {saved_path}")
    print(f"  Гаусс:          не использовался")
    print(f"  Архив:          ничто не удалено навсегда")
    print(f"{'='*70}\n")
    
    return graph, furcator.furcations


# ============================================================================
# 10. SMOKE-ТЕСТЫ
# ============================================================================

def run_smoke_tests():
    print("=" * 70)
    print("🧪 SMOKE-ТЕСТЫ")
    print("=" * 70)
    
    e1 = vmmp_entropy(42, 100)
    e2 = vmmp_entropy(42, 100)
    assert np.allclose(e1, e2)
    print("  ✅ Энтропия детерминирована")
    
    h1 = simple_tees_hash(b"test")
    h2 = simple_tees_hash(b"test")
    assert h1 == h2
    print("  ✅ Хэш воспроизводим")
    
    vconfig = VortexConfig()
    v = seed_to_vortex(12345, vconfig)
    tau_before = compute_topological_charge(v)
    pair = np.array([v, v.copy()])
    turb = vmmp_turbulence(pair, vconfig)
    tau_after = compute_topological_charge(turb[0])
    assert abs(tau_before - tau_after) < 0.5
    print(f"  ✅ Заряд сохраняется")
    
    assert TeesParser.detect_language("привет мир") == 'ru'
    print("  ✅ Определение языка работает")
    
    result = TeesParser.parse("Энергия является фундаментальной величиной.")
    assert result['valid']
    print(f"  ✅ Парсер извлёк {len(result['triples'])} троек")
    
    v1 = seed_to_vortex(111, vconfig)
    v2 = seed_to_vortex(222, vconfig)
    shift = tees_shift(v1, v2)
    assert not np.isnan(shift) and -1.0 <= shift <= 1.0
    print(f"  ✅ TEES-сдвиг корректен")
    
    ath = AdaptiveThreshold()
    for _ in range(100):
        ath.update(0.1)
    threshold = ath.get_threshold(85)
    assert 0.09 < threshold < 0.12
    print(f"  ✅ Адаптивный порог сходится")
    
    assert TeesParser.is_tees_en_auto('paper') == False
    print("  ✅ Английский парсер строже")
    
    # Тест дормантного архива
    graph = VMMPGraph(PipelineConfig(
        grace_period=2, maturity_age=4, archive_age=6,
        mature_decay=0.5, old_decay=0.3
    ))
    graph.add_edge('a', 'b', 'c', {
        'source': 'a', 'tees': 'b', 'receiver': 'c',
        'score': 1.0, 'vmmp_compliant': False,
        'src_charge': 1, 'tees_charge': 1, 'rec_charge': 1,
        'shift_src': 0.5, 'shift_rec': 0.5, 'is_balanced': False, 'is_connected': False
    })
    
    # Состарим до архива
    for _ in range(7):
        graph.decay_noise()
    
    assert len(graph.edges) == 0, "FAIL: связь не уснула!"
    assert len(graph.dormant_edges) == 1, "FAIL: связь не в архиве!"
    print("  ✅ Связь уснула в архиве (не удалена)")
    
    # Пробуждение
    awakened = graph.try_awaken('a', 'b', 'c')
    assert awakened is not None, "FAIL: не пробудилась!"
    assert len(graph.edges) == 1, "FAIL: не в активных!"
    assert len(graph.dormant_edges) == 0, "FAIL: не ушла из архива!"
    print("  ✅ Прямое пробуждение работает")
    
    # Омоложение только при compliant
    graph.edges[0]['age'] = 10
    graph.add_edge('a', 'b', 'c', {
        'source': 'a', 'tees': 'b', 'receiver': 'c',
        'score': 0.5, 'vmmp_compliant': False,
        'src_charge': 1, 'tees_charge': 1, 'rec_charge': 1,
        'shift_src': 0.5, 'shift_rec': 0.5, 'is_balanced': False, 'is_connected': False
    })
    assert graph.edges[0]['age'] == 10, "FAIL: омолодилась без compliant!"
    print("  ✅ Омоложение только при compliant")
    
    # Контекстное пробуждение
    graph.dormant_edges.append({
        'id': 'x|y|z', 'source': 'квантовая', 'tees': 'y', 'receiver': 'z',
        'weight': 0.5, 'age': 30, 'vmmp_compliant': False,
        'hibernated_at': '2024-01-01'
    })
    graph._dormant_index['x|y|z'] = 0
    awakened = graph.awaken_by_context(['квантовая', 'физика'])
    assert len(awakened) == 1
    assert len(graph.dormant_edges) == 0
    print("  ✅ Контекстное пробуждение работает")
    
    print(f"\n{'='*70}")
    print("✅ ВСЕ 12 ТЕСТОВ ПРОЙДЕНЫ")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_smoke_tests()
    else:
        config = PipelineConfig(
            seed=42,
            furcation_top_k=20,
            min_edge_score=0.25,
            min_furcation_score=0.3,
            grace_period=5,
            maturity_age=15,
            archive_age=25,
            mature_decay=0.8,
            old_decay=0.5,
            archive_weight=0.001,
            awakening_intensity=1.0,
            context_awakening=0.5,
            awakening_age_reset=20,
            output_dir=Path("./output"),
            corpus_path=Path("./corpus/corpus.json")
        )
        run_pipeline(config)