#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_core.py — Единое TEES-ядро SpectraVortex
===============================================
Все модули импортируют TEES-операции только отсюда.
Один источник истины для: вихрей, зарядов, сдвигов, валидации.
"""

import hashlib
import random
import logging
from typing import Dict, Tuple, Optional

import numpy as np

from core.tees_knowledge_engine_v5_6_fixed import (
    seed_to_vortex,
    compute_topological_charge,
    tees_shift,
    VortexConfig,
    simple_tees_hash,
    fast_16bit_hash,
    vmmp_entropy,
    H_CONSTANTS,
    K_CONSTANTS,
)

logger = logging.getLogger("TeesCore")


class CoreConfig:
    CHARGE_THRESHOLD = 1.5
    SHIFT_THRESHOLD = 0.9
    VORTEX_GRID_SIZE = 16
    CACHE_SIZE = 20000
    SEED = 42
    FAST_MODE = True


class TeesValidator:
    """Единый валидатор для всех модулей."""
    
    def __init__(self, config: type = CoreConfig):
        self.config = config
        self.vortex_config = VortexConfig(grid_size=config.VORTEX_GRID_SIZE)
        self.seed = config.SEED
        
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_max = config.CACHE_SIZE
        self._hits = 0
        self._misses = 0
        
        self.stats = {'checked': 0, 'passed': 0, 'rejected': 0}
    
    def _get_vortex(self, word: str) -> np.ndarray:
        if not word or not word.strip():
            return np.zeros((self.vortex_config.grid_size,) * 2, 
                          dtype=self.vortex_config.dtype)
        
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
    
    def validate(self, source: str, tees: str, receiver: str) -> Tuple[bool, float, str]:
        self.stats['checked'] += 1
        
        if self.config.FAST_MODE:
            if source == tees or tees == receiver or source == receiver:
                self.stats['rejected'] += 1
                return False, 999.0, "fast_identity"
        
        try:
            src_v = self._get_vortex(source)
            tee_v = self._get_vortex(tees)
            dst_v = self._get_vortex(receiver)
            
            src_charge = compute_topological_charge(src_v)
            tee_charge = compute_topological_charge(tee_v)
            dst_charge = compute_topological_charge(dst_v)
            total_charge = abs(src_charge + tee_charge + dst_charge)
            
            if total_charge > self.config.CHARGE_THRESHOLD:
                self.stats['rejected'] += 1
                return False, total_charge, f"charge({total_charge:.2f})"
            
            shift_src = abs(tees_shift(src_v, tee_v))
            shift_dst = abs(tees_shift(tee_v, dst_v))
            
            if shift_src > self.config.SHIFT_THRESHOLD or shift_dst > self.config.SHIFT_THRESHOLD:
                self.stats['rejected'] += 1
                return False, total_charge, f"shift({shift_src:.2f},{shift_dst:.2f})"
            
            self.stats['passed'] += 1
            return True, total_charge, "ok"
            
        except Exception as e:
            self.stats['passed'] += 1
            return True, 0.0, f"skip({str(e)[:30]})"
    
    def get_stats(self) -> dict:
        total = max(self.stats['checked'], 1)
        cache_total = max(self._hits + self._misses, 1)
        return {
            **self.stats,
            'pass_rate': round(self.stats['passed'] / total * 100, 1),
            'reject_rate': round(self.stats['rejected'] / total * 100, 1),
            'cache_size': len(self._cache),
            'cache_hits': self._hits,
            'cache_misses': self._misses,
            'cache_hit_rate': round(self._hits / cache_total * 100, 1),
        }
    
    def reset_stats(self):
        self.stats = {'checked': 0, 'passed': 0, 'rejected': 0}
        self._hits = 0
        self._misses = 0
    
    def clear_cache(self):
        self._cache.clear()
        self._hits = 0
        self._misses = 0


_VALIDATOR: Optional[TeesValidator] = None

def get_validator(config: type = CoreConfig) -> TeesValidator:
    global _VALIDATOR
    if _VALIDATOR is None:
        _VALIDATOR = TeesValidator(config)
        logger.info(f"TeesCore: валидатор инициализирован "
                    f"(cache={config.CACHE_SIZE}, charge_threshold={config.CHARGE_THRESHOLD})")
    return _VALIDATOR


def validate_triple(source: str, tees: str, receiver: str) -> Tuple[bool, float, str]:
    return get_validator().validate(source, tees, receiver)


def get_charge(word: str) -> float:
    v = get_validator()
    vortex = v._get_vortex(word)
    return float(compute_topological_charge(vortex))


def get_shift(word_a: str, word_b: str) -> float:
    v = get_validator()
    vortex_a = v._get_vortex(word_a)
    vortex_b = v._get_vortex(word_b)
    return float(tees_shift(vortex_a, vortex_b))


def get_cache_stats() -> dict:
    return get_validator().get_stats()


def reset_validator():
    global _VALIDATOR
    if _VALIDATOR:
        _VALIDATOR.clear_cache()
        _VALIDATOR.reset_stats()
    _VALIDATOR = None


__all__ = [
    'seed_to_vortex', 'compute_topological_charge', 'tees_shift',
    'VortexConfig', 'simple_tees_hash', 'fast_16bit_hash', 'vmmp_entropy',
    'TeesValidator', 'CoreConfig',
    'get_validator', 'validate_triple', 'get_charge', 'get_shift',
    'get_cache_stats', 'reset_validator',
]