#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_core_2.0.py — Единое ядро TEES-Института v21.0
======================================================
Объединяет:
- Математическое ядро (вихри, заряды, сдвиги, валидация)
- Живую личность v21.0 (ВММП-фильтр, эндогенный рост, черты)
- TEES-роутер v1.6 (усилитель, кэш, гомеостаз)
- Потоки (фуркации, резонанс, валидация, сохранение)
- Гомеостаз (температура, энтропия, память)
- Адаптивную точность с гистерезисом и буфером
- Перспективное планирование (теневое поле)
"""

import os
import sys
import time
import json
import queue
import threading
import logging
import gc
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# ══════════════════════════════════════
# 1. МАТЕМАТИЧЕСКОЕ ЯДРО (tees_core.py)
# ══════════════════════════════════════

try:
    from tees_core import (
        seed_to_vortex,
        compute_topological_charge,
        tees_shift,
        VortexConfig,
        simple_tees_hash,
        fast_16bit_hash,
        vmmp_entropy,
        TeesValidator,
        CoreConfig,
        get_validator,
        validate_triple,
        get_charge,
        get_shift,
        get_cache_stats,
        reset_validator,
    )
    HAS_TEES_CORE = True
    print("✅ tees_core загружен")
except ImportError:
    HAS_TEES_CORE = False
    print("⚠️ tees_core не найден. Будет использована заглушка.")

# ══════════════════════════════════════
# 2. ВНЕШНИЕ ЗАВИСИМОСТИ
# ══════════════════════════════════════

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil не установлен.")

try:
    from tees_router_v16 import TurboTEES
    HAS_ROUTER = True
    print("✅ TEESRouter v1.6 загружен")
except ImportError:
    HAS_ROUTER = False
    print("⚠️ TEESRouter не найден. Будет использована заглушка.")

try:
    from validators.vmmp_validator import VMMPValidator
    HAS_VALIDATOR = True
    print("✅ VMMPValidator загружен")
except ImportError:
    HAS_VALIDATOR = False
    print("⚠️ VMMPValidator не найден. Будет использована заглушка.")

# ══════════════════════════════════════
# ЗАГЛУШКИ
# ══════════════════════════════════════

class DummyRouter:
    def __init__(self, **kwargs):
        pass
    def generate_dual_topology(self, n_qubits=100):
        return {}, {}, [], [], []
    def route_cross_with_amplifier(self, *args, **kwargs):
        return []

class DummyValidator:
    def find_anomalies(self, modes):
        return []
    def check(self, cluster):
        return True

def validate_triple_stub(src, tees, dst):
    return True, 0.5, "stub"

def get_cache_stats_stub():
    return {'passed': 0, 'checked': 0}

def simple_tees_hash_stub(data):
    """Заглушка simple_tees_hash."""
    return hash(str(data)) & 0xFFFFFFFF

def seed_to_vortex_stub(seed, config=None):
    """Заглушка seed_to_vortex."""
    import numpy as np
    size = getattr(config, 'grid_size', 16) if config else 16
    return np.zeros((size, size))

def compute_topological_charge_stub(vortex):
    """Заглушка compute_topological_charge."""
    return 0.0

def tees_shift_stub(vortex1, vortex2):
    """Заглушка tees_shift."""
    return 0.0

# Подменяем функции, если tees_core не загружен
if not HAS_TEES_CORE:
    simple_tees_hash = simple_tees_hash_stub
    seed_to_vortex = seed_to_vortex_stub
    compute_topological_charge = compute_topological_charge_stub
    tees_shift = tees_shift_stub
    validate_triple = validate_triple_stub
    get_cache_stats = get_cache_stats_stub
    VortexConfig = type('VortexConfig', (), {'grid_size': 16, 'dtype': None})()

# ══════════════════════════════════════
# 3. АДАПТИВНЫЙ БУФЕР
# ══════════════════════════════════════

class AdaptiveBuffer:
    """Скользящее окно для сглаживания метрик."""
    
    def __init__(self, window_size: int = 5):
        self.window = []
        self.window_size = window_size
    
    def push(self, value: float) -> float:
        self.window.append(value)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        return sum(self.window) / len(self.window)
    
    def clear(self):
        self.window = []

# ══════════════════════════════════════
# 4. ЖИВАЯ ЛИЧНОСТЬ v21.0
# ══════════════════════════════════════

class LivingFieldV21:
    """
    Живая личность v21.0 — детерминированная турбулентность.
    
    Особенности:
    - ВММП-фильтр через validate_triple
    - Эндогенный рост без random (seed + топология поля)
    - Перспективное планирование (теневое поле на 5 шагов)
    - Адаптивная точность с гистерезисом и буфером
    - Гомеостаз с упреждающей реакцией
    """
    
    VMMP_TAU_MIN: float = 5.0
    VMMP_TAU_MAX: float = 11.0
    
    # Пороги гистерезиса
    ENTROPY_UP_THRESHOLD = 7.0
    ENTROPY_DOWN_THRESHOLD = 4.0
    TEMP_UP_THRESHOLD = 60.0
    TEMP_DOWN_THRESHOLD = 35.0
    COHERENCE_UP_THRESHOLD = 0.995
    COHERENCE_DOWN_THRESHOLD = 0.97
    BIFURCATION_RISK_THRESHOLD = 0.7
    
    def __init__(self, id: str = "living_v21", name: str = "Живая личность v21.0"):
        self.id = id
        self.name = name
        self.h_field: List[Any] = []
        self.vortices: Dict[str, Any] = {}
        
        # Черты характера
        self.traits = {
            'curiosity': 0.7,
            'creativity': 0.5,
            'empathy': 0.6,
            'stability': 0.8,
            'playfulness': 0.4
        }
        
        # Состояние
        self.mood = 0.0
        self.energy = 1.0
        self.experience = 0
        self.generation = 0
        self.coherence = 0.993
        self.nodes_created = 0
        self.furcation_count = 0
        
        # Адаптивная точность
        self.band_coefficients = 8
        self.max_band_coefficients = 16
        self.min_band_coefficients = 4
        
        self.convergence_epochs = 5
        self.max_convergence_epochs = 20
        self.min_convergence_epochs = 3
        
        self.furcation_depth = 1
        self.max_furcation_depth = 5
        
        self.validation_interval = 10
        
        # Буферы и контроль
        self.entropy_buffer = AdaptiveBuffer(window_size=5)
        self.temp_buffer = AdaptiveBuffer(window_size=5)
        self.coherence_buffer = AdaptiveBuffer(window_size=5)
        
        self._last_precision_change = 0.0
        self._precision_cooldown = 30
        
        # Перспективное планирование
        self.perspective_horizon = 5
        self.perspective_trajectory: List[Dict] = []
        self._shadow_field_cache = None
        
        # Эмоциональная память
        self.emotional_memory: List[Dict] = []
        self.dialog_history: Dict[str, List[Dict]] = {}
        self.mood_history: List[float] = []
        self.dialog_count = 0
        
        # Кластеры
        self.clusters: Dict[float, Dict] = {}
        
        # Валидатор
        if HAS_VALIDATOR:
            self.validator = VMMPValidator()
        else:
            self.validator = DummyValidator()
        
        # Счётчики
        self._seed_counter = 0
        self._field_state = 0
        
        # Потоки
        self._running = False
        self._bg_thread = None
        self._cycle = 0
        
        # Паттерн-лог для будущей грамматики
        self.grammar_enabled = False
        self.grammar_rules: List[Dict] = []
        self.pattern_log: List[Dict] = []
        
        self._init_clusters()
        
        # Логгер
        self.logger = logging.getLogger("LivingFieldV21")
        
        print(f"🌱 {name} инициализирована (v21.0 — детерминированная турбулентность)")
    
    # ══════════════════════════════════════
    # ИНИЦИАЛИЗАЦИЯ
    # ══════════════════════════════════════
    
    def _init_clusters(self):
        self.clusters = {
            1.0: {'scale': 1.0, 'modes': [], 'phase': 0.0, 'frozen': False},
            3.0: {'scale': 3.0, 'modes': [], 'phase': 0.5, 'frozen': False},
            6.0: {'scale': 6.0, 'modes': [], 'phase': 1.0, 'frozen': False},
            10.0: {'scale': 10.0, 'modes': [], 'phase': 1.5, 'frozen': True},
        }
    
    # ══════════════════════════════════════
    # ДЕТЕРМИНИРОВАННЫЕ ГЕНЕРАТОРЫ
    # ══════════════════════════════════════
    
    def _next_deterministic_seed(self) -> int:
        self._seed_counter += 1
        field_hash = 0
        for mode in self.h_field[-20:]:
            if hasattr(mode, 'source'):
                field_hash ^= hash(str(mode.source)[:10])
        combined = f"{field_hash}_{self._field_state}_{self._seed_counter}"
        return simple_tees_hash(combined.encode('utf-8'))
    
    def _seed_to_label(self, seed: int, prefix: str = "node") -> str:
        return f"{prefix}_{seed % 10000:04d}"
    
    def _compute_amplitude_from_charge(self, seed: int) -> float:
        try:
            vortex = seed_to_vortex(seed, VortexConfig())
            charge = abs(compute_topological_charge(vortex))
            amplitude = 0.3 + min(charge, 2.0) / 2.0 * 0.65
            return round(amplitude, 4)
        except Exception:
            return 0.5
    
    def _compute_tau_from_shift(self, source_seed: int, tees_seed: int) -> float:
        try:
            src_vortex = seed_to_vortex(source_seed, VortexConfig())
            tee_vortex = seed_to_vortex(tees_seed, VortexConfig())
            shift = abs(tees_shift(src_vortex, tee_vortex))
            tau = self.VMMP_TAU_MIN + shift * (self.VMMP_TAU_MAX - self.VMMP_TAU_MIN)
            return round(tau, 4)
        except Exception:
            return 8.0
    
    def _determine_scale(self, seed: int) -> float:
        base_scale = (seed % 4 + 1) * 2.5
        available_scales = [s for s, c in self.clusters.items() if not c['frozen']]
        if available_scales:
            closest = min(available_scales, key=lambda s: abs(s - base_scale))
            return closest
        return base_scale
    
    def _compute_quality(self, mode) -> float:
        try:
            src = getattr(mode, 'source', '')[:20]
            tees = getattr(mode, 'tees', '')[:20]
            dst = getattr(mode, 'receiver', '')[:20]
            ok, charge, reason = validate_triple(src, tees, dst)
            if ok:
                return 0.7 + min(charge, 1.0) * 0.3
            else:
                return 0.1 + min(charge, 0.5) * 0.4
        except Exception:
            return 0.5
    
    # ══════════════════════════════════════
    # ВММП-ФИЛЬТР
    # ══════════════════════════════════════
    
    def _passes_vmmp_filter(self, mode) -> bool:
        if hasattr(mode, 'source') and hasattr(mode, 'tees') and hasattr(mode, 'receiver'):
            ok, charge, reason = validate_triple(
                mode.source[:20],
                mode.tees[:20],
                mode.receiver[:20]
            )
            if ok:
                return True
        
        tau = getattr(mode, 'tau', 0)
        scale = getattr(mode, 'scale', 1.0)
        amplitude = getattr(mode, 'amplitude', 0.5)
        
        if scale >= 20.0:
            return True
        if amplitude >= 0.7:
            return True
        if self.VMMP_TAU_MIN <= tau <= self.VMMP_TAU_MAX:
            return True
        if (tau < self.VMMP_TAU_MIN or tau > self.VMMP_TAU_MAX) and scale >= 10.0 and amplitude >= 0.6:
            return True
        return False
    
    # ══════════════════════════════════════
    # ПЕРСПЕКТИВНОЕ ПЛАНИРОВАНИЕ
    # ══════════════════════════════════════
    
    def _snapshot_field(self) -> int:
        state_hash = self._field_state
        for mode in self.h_field[-10:]:
            if hasattr(mode, 'source'):
                state_hash ^= hash(str(mode.source)[:5])
        return state_hash
    
    def _compute_perspective(self) -> List[Dict]:
        trajectory = []
        shadow_state = self._snapshot_field()
        
        for step in range(1, self.perspective_horizon + 1):
            shadow_state = simple_tees_hash(str(shadow_state).encode('utf-8'))
            seed_sample = shadow_state % 1000
            
            predicted_coherence = self.coherence - step * 0.002 * (1 + (seed_sample % 3) / 10)
            predicted_coherence = max(0.9, min(0.999, predicted_coherence))
            
            predicted_entropy = 3.0 + (1.0 - predicted_coherence) * 50
            predicted_entropy = max(1.0, min(10.0, predicted_entropy))
            
            bifurcation_risk = 0.0
            if predicted_coherence < 0.97:
                bifurcation_risk = min(1.0, (0.97 - predicted_coherence) * 30)
            if predicted_entropy > 6:
                bifurcation_risk = max(bifurcation_risk, (predicted_entropy - 6) / 4)
            
            trajectory.append({
                'step': step,
                'predicted_coherence': round(predicted_coherence, 4),
                'predicted_entropy': round(predicted_entropy, 2),
                'bifurcation_risk': round(bifurcation_risk, 4),
                'shadow_state': shadow_state,
            })
        
        return trajectory
    
    # ══════════════════════════════════════
    # АДАПТИВНАЯ ТОЧНОСТЬ
    # ══════════════════════════════════════
    
    def _can_change_precision(self) -> bool:
        return time.time() - self._last_precision_change > self._precision_cooldown
    
    def _adapt_precision(self):
        if not self._can_change_precision():
            return
        
        metrics = self.get_metrics()
        entropy = self.entropy_buffer.push(metrics['entropy'])
        temp = self.temp_buffer.push(metrics['temperature'])
        coherence = self.coherence_buffer.push(self.coherence)
        
        self.perspective_trajectory = self._compute_perspective()
        next_crisis = None
        for point in self.perspective_trajectory:
            if point['bifurcation_risk'] > self.BIFURCATION_RISK_THRESHOLD:
                next_crisis = point
                break
        
        changed = False
        old_bands = self.band_coefficients
        old_epochs = self.convergence_epochs
        old_depth = self.furcation_depth
        
        # Перспективная мобилизация
        if next_crisis:
            steps_until = next_crisis['step']
            
            if steps_until <= 2:
                self.band_coefficients = self.max_band_coefficients
                self.convergence_epochs = self.max_convergence_epochs
                self.furcation_depth = self.max_furcation_depth
                self.validation_interval = 5
                changed = True
                self.logger.info(f"⚡ КРИЗИС через {steps_until} шагов! Полная мобилизация.")
            
            elif steps_until <= 4:
                self.band_coefficients = min(self.band_coefficients + 2, self.max_band_coefficients)
                self.convergence_epochs = min(self.convergence_epochs + 2, self.max_convergence_epochs)
                self.furcation_depth = min(self.furcation_depth + 1, self.max_furcation_depth)
                self.validation_interval = 8
                changed = True
                self.logger.info(f"🔍 Кризис через {steps_until} шагов. Повышаю точность.")
        
        # Гистерезис по текущим метрикам
        if not changed:
            if entropy > self.ENTROPY_UP_THRESHOLD and self.band_coefficients < self.max_band_coefficients:
                self.band_coefficients += 2
                changed = True
            elif entropy < self.ENTROPY_DOWN_THRESHOLD and self.band_coefficients > self.min_band_coefficients:
                self.band_coefficients -= 1
                changed = True
            
            if temp > self.TEMP_UP_THRESHOLD and self.convergence_epochs < self.max_convergence_epochs:
                self.convergence_epochs += 2
                changed = True
            elif temp < self.TEMP_DOWN_THRESHOLD and self.convergence_epochs > self.min_convergence_epochs:
                self.convergence_epochs -= 1
                changed = True
            
            if coherence < self.COHERENCE_DOWN_THRESHOLD:
                self.furcation_depth = min(self.furcation_depth + 1, self.max_furcation_depth)
                changed = True
            elif coherence > self.COHERENCE_UP_THRESHOLD:
                self.furcation_depth = max(self.furcation_depth - 1, 1)
                changed = True
            
            if entropy > 6:
                self.validation_interval = 5
            elif entropy < 3:
                self.validation_interval = 30
            else:
                self.validation_interval = 10
        
        if changed:
            self._last_precision_change = time.time()
            self.logger.info(
                f"🎯 Адаптация: полос={old_bands}→{self.band_coefficients}, "
                f"эпох={old_epochs}→{self.convergence_epochs}, "
                f"глубина={old_depth}→{self.furcation_depth} "
                f"(энтр={entropy:.1f}, когер={coherence:.4f}, темп={temp:.1f})"
            )
    
    # ══════════════════════════════════════
    # БИФУРКАЦИОННАЯ ЛОГИКА
    # ══════════════════════════════════════
    
    def _should_bifurcate(self) -> bool:
        if self.coherence < 0.97:
            return True
        
        accumulated_phase = self._seed_counter % 100 / 100.0
        phase_threshold = 0.8 + (1.0 - self.coherence) * 2
        
        if accumulated_phase > phase_threshold:
            return True
        
        if self.perspective_trajectory:
            immediate = self.perspective_trajectory[0]
            if immediate['bifurcation_risk'] > 0.5:
                return True
        
        return False
    
    # ══════════════════════════════════════
    # ФУРКАЦИИ
    # ══════════════════════════════════════
    
    def furcate(self) -> List[Any]:
        self.furcation_count += 1
        self.coherence = max(0.95, self.coherence - 0.0005)
        
        new_modes = []
        
        for i in range(self.furcation_depth):
            source_seed = self._next_deterministic_seed()
            tees_seed = simple_tees_hash(str(source_seed).encode('utf-8'))
            receiver_seed = simple_tees_hash(str(tees_seed).encode('utf-8'))
            
            mode = type('Mode', (), {
                'id': f"furc_{self.generation}_{self.furcation_count}_{i}",
                'trace_id': f"trace_{source_seed:08x}",
                'source': self._seed_to_label(source_seed),
                'tees': self._seed_to_label(tees_seed, "tees"),
                'receiver': self._seed_to_label(receiver_seed),
                'amplitude': self._compute_amplitude_from_charge(source_seed),
                'tau': self._compute_tau_from_shift(source_seed, tees_seed),
                'scale': self._determine_scale(source_seed),
                'phase': (self._seed_counter % 100) / 100.0,
                'generation': self.generation,
                'furcation_id': self.furcation_count,
                'quality': 0.0,
                'coherence': self.coherence,
                'entropy': 0.0,
            })()
            
            mode.quality = self._compute_quality(mode)
            
            if self._passes_vmmp_filter(mode):
                self.add_mode(mode)
                new_modes.append(mode)
                self._field_state ^= source_seed
        
        if new_modes:
            self.nodes_created += len(new_modes)
            self.generation += 1
        
        return new_modes
    
    # ══════════════════════════════════════
    # УПРАВЛЕНИЕ МОДАМИ
    # ══════════════════════════════════════
    
    def add_mode(self, mode):
        if self._passes_vmmp_filter(mode):
            self.h_field.append(mode)
            self._log_pattern(mode, 'added')
            return True
        else:
            self._log_pattern(mode, 'rejected')
            return False
    
    def add_clusters(self, clusters):
        for cluster in clusters:
            if isinstance(cluster, list):
                for mode in cluster:
                    self.add_mode(mode)
            else:
                self.add_mode(cluster)
    
    def cluster(self, data):
        clusters = []
        modes = data.get('modes', []) if isinstance(data, dict) else data
        
        if not modes:
            return clusters
        
        by_scale = {}
        for mode in modes:
            scale = getattr(mode, 'scale', 1.0)
            by_scale.setdefault(scale, []).append(mode)
        
        return list(by_scale.values())
    
    def get_all_modes(self) -> List[Any]:
        return self.h_field
    
    def remove_mode(self, mode_id: str):
        self.h_field = [m for m in self.h_field if getattr(m, 'id', '') != mode_id]
    
    def purge_weak_modes(self, threshold: float = 0.3):
        before = len(self.h_field)
        self.h_field = [m for m in self.h_field if getattr(m, 'quality', 0.5) >= threshold]
        after = len(self.h_field)
        if before > after:
            self.logger.info(f"🧹 purge_weak_modes: {before} → {after}")
    
    def mark_for_review(self, mode_id: str):
        for mode in self.h_field:
            if getattr(mode, 'id', '') == mode_id:
                mode._flagged = True
                break
    
    def clear_cache(self):
        self.vortices = {}
        self._shadow_field_cache = None
        self.entropy_buffer.clear()
        self.temp_buffer.clear()
        self.coherence_buffer.clear()
    
    # ══════════════════════════════════════
    # ПАТТЕРН-ЛОГ (ЗАДЕЛ ДЛЯ ГРАММАТИКИ)
    # ══════════════════════════════════════
    
    def _log_pattern(self, mode, event: str):
        if len(self.pattern_log) > 10000:
            self.pattern_log = self.pattern_log[-5000:]
        
        self.pattern_log.append({
            'event': event,
            'mode_id': getattr(mode, 'id', '?'),
            'source': getattr(mode, 'source', '')[:10],
            'tees': getattr(mode, 'tees', '')[:10],
            'receiver': getattr(mode, 'receiver', '')[:10],
            'amplitude': getattr(mode, 'amplitude', 0),
            'tau': getattr(mode, 'tau', 0),
            'scale': getattr(mode, 'scale', 0),
            'quality': getattr(mode, 'quality', 0),
            'coherence': self.coherence,
            'timestamp': time.time(),
        })
    
    def extract_rules(self):
        if not self.grammar_enabled:
            return []
        return []
    
    # ══════════════════════════════════════
    # МЕТРИКИ
    # ══════════════════════════════════════
    
    def get_metrics(self) -> Dict[str, float]:
        return {
            'temperature': 30.0 + len(self.h_field) * 0.01,
            'entropy': max(1.0, 5.0 - self.coherence * 5.0),
        }
    
    # ══════════════════════════════════════
    # ОБРАБОТКА СООБЩЕНИЙ
    # ══════════════════════════════════════
    
    def process(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        self.dialog_count += 1
        self.experience += 1
        
        sentiment = self._detect_sentiment(text)
        self.mood = self.mood * 0.9 + sentiment * 0.1
        self.mood_history.append(self.mood)
        
        best_mode, best_score, source = self._find_best_mode(text)
        
        if best_mode and best_score > 0.15:
            answer = best_mode.content[:500] if hasattr(best_mode, 'content') else str(best_mode)
            return {
                "answer": answer,
                "mode_used": best_mode.trace_id[:16] if hasattr(best_mode, 'trace_id') else '?',
                "mode_type": source,
                "resonance": best_score,
                "mood": self.mood,
                "dialog_count": self.dialog_count,
            }
        
        return {
            "answer": "Интересно... Расскажите подробнее?",
            "mode_type": "fallback",
            "resonance": 0.1,
            "mood": self.mood,
            "dialog_count": self.dialog_count,
        }
    
    def _detect_sentiment(self, text: str) -> float:
        positive = ["хорош", "отличн", "прекрасн", "класс", "супер", "люблю", "нравит"]
        negative = ["плох", "ужасн", "ненавиж", "грустн", "печальн", "зл", "обид"]
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        if pos + neg == 0:
            return 0.0
        return (pos - neg) / (pos + neg)
    
    def _find_best_mode(self, text: str) -> Tuple[Any, float, str]:
        if not self.h_field:
            return None, 0.0, "empty"
        best = max(self.h_field, key=lambda m: getattr(m, 'amplitude', 0.5))
        score = min(1.0, getattr(best, 'amplitude', 0.5) * 1.5)
        return best, score, "amplitude"
    
    # ══════════════════════════════════════
    # ЭНДОГЕННЫЙ ЦИКЛ
    # ══════════════════════════════════════
    
    def start_living(self, interval: float = 0.5):
        if self._running:
            return
        self._running = True
        self._bg_thread = threading.Thread(target=self._living_loop, args=(interval,), daemon=True)
        self._bg_thread.start()
        print("🌿 Эндогенный цикл v21.0 запущен (детерминированная турбулентность)")
    
    def stop_living(self):
        self._running = False
        print("🛑 Эндогенный цикл остановлен")
    
    def _living_loop(self, interval: float):
        while self._running:
            time.sleep(interval)
            self._cycle += 1
            
            if self._cycle % 10 == 0:
                self._adapt_precision()
            
            if self._should_bifurcate():
                new_modes = self.furcate()
                if new_modes:
                    self.logger.debug(f"🌀 Фуркация: {len(new_modes)} мод (глубина {self.furcation_depth})")
            
            if self._cycle % 30 == 0:
                self._update_clusters()
            
            if self._cycle % max(1, int(self.validation_interval / interval)) == 0:
                self._validate_field()
            
            if self._cycle % 10 == 0 and not self._should_bifurcate():
                self.coherence = min(0.998, self.coherence + 0.0001)
            
            if self._cycle % 120 == 0:
                self._print_status()
    
    def _update_clusters(self):
        for scale, cluster in self.clusters.items():
            if not cluster['frozen']:
                cluster['phase'] = (cluster['phase'] + 0.01 * scale) % 2.0
    
    def _validate_field(self):
        if not self.h_field:
            return
        stats = get_cache_stats()
        self.logger.debug(
            f"✅ Валидация: {stats['passed']}/{stats['checked']} прошло "
            f"(полос={self.band_coefficients}, эпох={self.convergence_epochs})"
        )
    
    def _print_status(self):
        print(f"\n🌱 {self.name} — статус (цикл {self._cycle}):")
        print(f"   Диалогов: {self.dialog_count} | Мод: {len(self.h_field)}")
        print(f"   Настроение: {self.mood:+.2f} | Когерентность: {self.coherence:.4f}")
        print(f"   Фуркаций: {self.furcation_count} | Глубина: {self.furcation_depth}")
        print(f"   Точность: полос={self.band_coefficients}, эпох={self.convergence_epochs}")
        if self.perspective_trajectory:
            risk = self.perspective_trajectory[0]['bifurcation_risk']
            print(f"   Перспектива: риск бифуркации {risk:.2%}")
    
    # ══════════════════════════════════════
    # СЕРИАЛИЗАЦИЯ
    # ══════════════════════════════════════
    
    def save(self, filepath: str):
        data = {
            "id": self.id,
            "name": self.name,
            "generation": self.generation,
            "coherence": self.coherence,
            "nodes_created": self.nodes_created,
            "furcation_count": self.furcation_count,
            "traits": self.traits,
            "mood": self.mood,
            "dialog_count": self.dialog_count,
            "h_field_size": len(self.h_field),
            "band_coefficients": self.band_coefficients,
            "convergence_epochs": self.convergence_epochs,
            "furcation_depth": self.furcation_depth,
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        instance = cls(data.get("id", "living_v21"), data.get("name", "Живая личность v21.0"))
        instance.generation = data.get("generation", 0)
        instance.coherence = data.get("coherence", 0.993)
        instance.nodes_created = data.get("nodes_created", 0)
        instance.furcation_count = data.get("furcation_count", 0)
        instance.mood = data.get("mood", 0.0)
        instance.dialog_count = data.get("dialog_count", 0)
        instance.band_coefficients = data.get("band_coefficients", 8)
        instance.convergence_epochs = data.get("convergence_epochs", 5)
        instance.furcation_depth = data.get("furcation_depth", 1)
        for k, v in data.get("traits", {}).items():
            if k in instance.traits:
                instance.traits[k] = v
        return instance


# ══════════════════════════════════════
# 5. ЯДРО TEES v2.0
# ══════════════════════════════════════

class TEESCoreV2:
    """Ядро TEES-Института v2.0."""
    
    DEFAULT_PERSONALITY_PATH = "personality_v21.json"
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.running = True
        
        # Личность
        self.personality = self._load_personality()
        
        # Роутер
        if HAS_ROUTER:
            self.router = TurboTEES(field_size=32, cache_size=500)
        else:
            self.router = DummyRouter()
        
        # Потоки
        self.threads = []
        self._init_threads()
        
        self.logger.info("✅ TEES Core v2.0 инициализирован")
    
    def _setup_logger(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)-7s] %(message)s',
            datefmt='%H:%M:%S'
        )
        return logging.getLogger("TEESCoreV2")
    
    def _load_personality(self):
        path = self.DEFAULT_PERSONALITY_PATH
        if os.path.exists(path):
            try:
                self.logger.info(f"📂 Загрузка личности из {path}")
                return LivingFieldV21.load(path)
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка загрузки: {e}")
        return LivingFieldV21()
    
    def _init_threads(self):
        self.threads = [
            threading.Thread(target=self._furcator_loop, name="Furcator", daemon=True),
            threading.Thread(target=self._resonator_loop, name="Resonator", daemon=True),
            threading.Thread(target=self._organizer_loop, name="Organizer", daemon=True),
            threading.Thread(target=self._validator_loop, name="Validator", daemon=True),
            threading.Thread(target=self._error_hunter_loop, name="ErrorHunter", daemon=True),
            threading.Thread(target=self._auto_save_loop, name="AutoSaver", daemon=True),
            threading.Thread(target=self._homeostasis_loop, name="Homeostasis", daemon=True),
        ]
    
    def _furcator_loop(self):
        self.logger.info("🌀 Furcator запущен")
        while self.running:
            time.sleep(30)
            try:
                new_modes = self.personality.furcate()
                if new_modes:
                    self.logger.debug(f"🌀 Сгенерировано {len(new_modes)} мод")
            except Exception as e:
                self.logger.error(f"❌ Furcator: {e}")
    
    def _resonator_loop(self):
        self.logger.info("🔮 Resonator запущен")
        while self.running:
            time.sleep(15)
            try:
                self.personality._update_clusters()
            except Exception as e:
                self.logger.error(f"❌ Resonator: {e}")
    
    def _organizer_loop(self):
        self.logger.info("🧩 Organizer запущен")
        while self.running:
            time.sleep(20)
    
    def _validator_loop(self):
        self.logger.info("✅ Validator запущен")
        while self.running:
            time.sleep(10)
            try:
                modes = self.personality.get_all_modes()
                if modes:
                    self.logger.debug(f"✅ Валидация: {len(modes)} мод в поле")
            except Exception as e:
                self.logger.error(f"❌ Validator: {e}")
    
    def _error_hunter_loop(self):
        self.logger.info("🔍 ErrorHunter запущен")
        while self.running:
            time.sleep(120)
            try:
                modes = self.personality.get_all_modes()
                anomalies = []
                for mode in modes:
                    if hasattr(mode, 'source') and hasattr(mode, 'tees') and hasattr(mode, 'receiver'):
                        ok, _, _ = validate_triple(mode.source[:20], mode.tees[:20], mode.receiver[:20])
                        if not ok:
                            anomalies.append(mode)
                if anomalies:
                    self.logger.warning(f"🔍 Найдено аномалий: {len(anomalies)}")
                    for anomaly in anomalies[:10]:
                        self.personality.mark_for_review(getattr(anomaly, 'id', ''))
            except Exception as e:
                self.logger.error(f"❌ ErrorHunter: {e}")
    
    def _auto_save_loop(self):
        self.logger.info("💾 AutoSaver запущен")
        while self.running:
            time.sleep(600)
            try:
                self.personality.save(self.DEFAULT_PERSONALITY_PATH)
                self.logger.info(f"💾 Сохранено: {self.DEFAULT_PERSONALITY_PATH}")
            except Exception as e:
                self.logger.error(f"❌ Ошибка сохранения: {e}")
    
    def _homeostasis_loop(self):
        self.logger.info("🌡️ Homeostasis Monitor запущен")
        while self.running:
            time.sleep(30)
            try:
                metrics = self.personality.get_metrics()
                temp = metrics.get('temperature', 30)
                entropy = metrics.get('entropy', 5)
                
                if HAS_PSUTIL:
                    mem = psutil.Process().memory_info().rss / 1e9
                    self.logger.debug(f"🌡️ t={temp:.1f} e={entropy:.2f} c={self.personality.coherence:.4f} mem={mem:.2f}GB")
                else:
                    self.logger.debug(f"🌡️ t={temp:.1f} e={entropy:.2f} c={self.personality.coherence:.4f}")
                
                if temp > 70:
                    self.logger.warning("🌡️ ПЕРЕГРЕВ! Охлаждение...")
                    self.personality.purge_weak_modes(0.5)
                    self.personality.clear_cache()
                
                if entropy > 8:
                    self.logger.warning("🌀 ВЫСОКАЯ ЭНТРОПИЯ! Очистка...")
                    self.personality.clear_cache()
                    
            except Exception as e:
                self.logger.error(f"❌ Homeostasis: {e}")
    
    def start(self):
        self.logger.info("🚀 Запуск TEES Core v2.0...")
        self.personality.start_living()
        for t in self.threads:
            t.start()
        self.logger.info(f"✅ Все {len(self.threads)} потоков запущены")
    
    def stop(self):
        self.logger.info("🛑 Остановка TEES Core v2.0...")
        self.running = False
        self.personality.stop_living()
        for t in self.threads:
            t.join(timeout=3)
        self.personality.save(self.DEFAULT_PERSONALITY_PATH)
        self.logger.info("✅ Остановлен")


# ══════════════════════════════════════
# 6. ТОЧКА ВХОДА
# ══════════════════════════════════════

if __name__ == "__main__":
    core = TEESCoreV2()
    try:
        core.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        core.stop()