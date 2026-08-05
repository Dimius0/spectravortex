#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_core_4.1.py — TEES Core v4.1: Трассируемая отдача
========================================================
v4.1 — Ничто не исчезает. Энергия всегда переходит. Шум — нераспознанный сигнал.

Новое в v4.1 (на базе v4.0):
    - field_energy_pool: энергия «напрасных» смертей не теряется, а усиливает всё поле
    - ambient_amplification: каждая смерть без акцептора даёт микро-прирост всем модам
    - Трассировка: запись «эхо» в историю поля для каждой смерти без акцептора
    - Wasted заменён на «энергия в пути»
    - Аномалии — не ошибки, а нераспознанные сигналы
    - Эритроцитарный трансфер сохранён полностью
"""

import os, sys, time, json, queue, threading, logging, gc, random, math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter

# ══════════════════════════════════════
# КОНФИГУРАЦИЯ
# ══════════════════════════════════════
DATA_DIR = "E:/tees_data"
LOG_FILE = os.path.join(DATA_DIR, "tees_core_4.1.log")
PERSONALITY_FILE = os.path.join(DATA_DIR, "personality_v4.1.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════
# ЗАВИСИМОСТИ
# ══════════════════════════════════════
try:
    from tees_core import (seed_to_vortex, compute_topological_charge, tees_shift,
                           VortexConfig, simple_tees_hash, validate_triple, get_cache_stats)
    HAS_TEES_CORE = True
except ImportError:
    HAS_TEES_CORE = False
    print("⚠️ tees_core не найден. Заглушки активны.")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from tees_router_v16 import TurboTEES
    HAS_ROUTER = True
except ImportError:
    HAS_ROUTER = False

try:
    from validators.vmmp_validator import VMMPValidator
    HAS_VALIDATOR = True
except ImportError:
    HAS_VALIDATOR = False

# ══════════════════════════════════════
# ЗАГЛУШКИ
# ══════════════════════════════════════
class DummyRouter:
    def __init__(self, **kwargs): pass
    def route_cross_with_amplifier(self, *args, **kwargs): return []

class DummyValidator:
    def find_anomalies(self, modes): return []
    def check(self, cluster): return True

def validate_triple_stub(src, tees, dst): return True, 0.5, "stub"
def get_cache_stats_stub(): return {'passed': 0, 'checked': 0}
def simple_tees_hash_stub(data):
    if isinstance(data, str): data = data.encode('utf-8')
    return hash(data) & 0xFFFFFFFF
def seed_to_vortex_stub(seed, config=None):
    import numpy as np
    size = getattr(config, 'grid_size', 16) if config else 16
    return np.zeros((size, size))
def compute_topological_charge_stub(vortex): return 0.0
def tees_shift_stub(vortex1, vortex2): return 0.0

if not HAS_TEES_CORE:
    simple_tees_hash = simple_tees_hash_stub
    seed_to_vortex = seed_to_vortex_stub
    compute_topological_charge = compute_topological_charge_stub
    tees_shift = tees_shift_stub
    validate_triple = validate_triple_stub
    get_cache_stats = get_cache_stats_stub
    VortexConfig = type('VortexConfig', (), {'grid_size': 16, 'dtype': None})()

# ══════════════════════════════════════
# АДАПТИВНЫЙ БУФЕР
# ══════════════════════════════════════
class AdaptiveBuffer:
    def __init__(self, window_size: int = 5):
        self.window = []
        self.window_size = window_size
    
    def push(self, value: float) -> float:
        self.window.append(value)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        return sum(self.window) / len(self.window)
    
    def clear(self):
        self.window.clear()

# ══════════════════════════════════════
# LIVING FIELD v4.1 — ТРАССИРУЕМАЯ ОТДАЧА
# ══════════════════════════════════════
class LivingFieldV3:
    """
    Живая личность v4.1 — энергия не исчезает, шум = нераспознанный сигнал.
    """
    
    def __init__(self, id: str = "living_v4", name: str = "Живая личность v4.1"):
        self.id, self.name = id, name
        self.h_field: List[Any] = []
        self.vortices: Dict[str, Any] = {}
        
        # Черты и состояние
        self.traits = {
            'curiosity': 0.7, 'creativity': 0.5, 'empathy': 0.6,
            'stability': 0.8, 'playfulness': 0.4
        }
        self.mood, self.energy, self.experience = 0.0, 1.0, 0
        self.generation, self.coherence = 0, 0.993
        self.nodes_created, self.furcation_count = 0, 0
        self.temperature = 30.0
        
        # Адаптивная точность
        self.band_coefficients, self.max_bands, self.min_bands = 8, 16, 4
        self.convergence_epochs, self.max_epochs, self.min_epochs = 5, 20, 3
        self.furcation_depth, self.max_depth = 1, 5
        self.validation_interval = 10
        
        # Буферы
        self.entropy_buffer = AdaptiveBuffer(5)
        self.temp_buffer = AdaptiveBuffer(5)
        self.coherence_buffer = AdaptiveBuffer(5)
        self._last_precision_change, self._precision_cooldown = 0.0, 30
        
        # Гипоталамус и иммунитет (жёсткие пороги v3.1)
        self._last_thermal_action, self._thermal_cooldown = 0.0, 60
        self._thermal_mode = "normal"
        self._last_local_purge, self._local_purge_cooldown = 0.0, 120
        self._regeneration_active = False
        self.immune_memory: Dict[str, Dict] = {}
        self.active_dominants: Dict[str, Dict] = {}
        self.scar_index = 0.0
        
        # Эмоциональный контур
        self.hormones = {
            'dopamine': 0.5, 'cortisol': 0.3,
            'melatonin': 0.2, 'adrenaline': 0.1
        }
        self.emotional_tags: Dict[str, str] = {}
        
        # Перспектива
        self.perspective_horizon = 5
        self.perspective_trajectory: List[Dict] = []
        
        # Память
        self.emotional_memory, self.mood_history = [], []
        self.dialog_count = 0
        self.pattern_log: List[Dict] = []
        
        # Кластеры
        self.clusters: Dict[float, Dict] = {}
        
        # Валидатор
        self.validator = VMMPValidator() if HAS_VALIDATOR else DummyValidator()
        
        # Счётчики и потоки
        self._seed_counter, self._field_state = 0, 0
        self._running, self._bg_thread, self._cycle = False, None, 0
        
        # ВНЕШНИЙ СИГНАЛ
        self.external_signal_queue = queue.Queue(maxsize=200)
        self.signal_priority_queue: List[Dict] = []
        self.signal_history: List[Dict] = []
        
        # ═══ НОВОЕ В 4.1: ТРАССИРУЕМАЯ ОТДАЧА ═══
        self.erythro = {
            'total_deaths': 0,              # Всего смертей мод
            'donation_deaths': 0,           # Смертей через прямое дарение акцептору
            'field_deaths': 0,              # Смертей с отдачей в поле (бывш. wasted)
            'field_energy_pool': 0.0,       # Накопленная энергия в поле
            'donation_history': [],         # История последних дарений
            'field_echoes': [],             # Эхо смертей в поле (трассировка)
            'acceptor_bonuses': {},         # Сколько каждая мода получила через прямое дарение
        }
        
        self._init_clusters()
        self.logger = logging.getLogger("LivingFieldV3")
        self.logger.info(f"🌱 {name} инициализирована (v4.1 — Трассируемая отдача)")
    
    # ═══════════════════════ СВОЙСТВА ═══════════════════════
    @property
    def field_size(self) -> int:
        return len(self.h_field)
    
    @property
    def anomaly_rate(self) -> float:
        return self._count_recent_anomaly_rate(50)
    
    @property
    def active_dominant_count(self) -> int:
        return len(self.active_dominants)
    
    @property
    def erythro_index(self) -> float:
        """Доля отслеженных переходов (прямое дарение + поле) от общего числа смертей."""
        total = self.erythro['total_deaths']
        if total == 0:
            return 1.0
        tracked = self.erythro['donation_deaths'] + self.erythro['field_deaths']
        return tracked / total
    
    @property
    def donation_purity(self) -> float:
        """Доля прямых дарений среди всех отслеженных переходов."""
        tracked = self.erythro['donation_deaths'] + self.erythro['field_deaths']
        if tracked == 0:
            return 0.0
        return self.erythro['donation_deaths'] / tracked
    
    # ═══════════════════════ ЭРИТРОЦИТАРНЫЙ ТРАНСФЕР v4.1 ═══════════════════════
    
    def _compute_topological_distance(self, mode1, mode2) -> float:
        tau1 = getattr(mode1, 'tau', 8.0)
        tau2 = getattr(mode2, 'tau', 8.0)
        scale1 = getattr(mode1, 'scale', 1.0)
        scale2 = getattr(mode2, 'scale', 1.0)
        amp1 = getattr(mode1, 'amplitude', 0.5)
        amp2 = getattr(mode2, 'amplitude', 0.5)
        
        tau_dist = abs(tau1 - tau2) / 11.0
        scale_dist = abs(scale1 - scale2) / 10.0
        amp_dist = abs(amp1 - amp2)
        
        return tau_dist * 0.4 + scale_dist * 0.3 + amp_dist * 0.3
    
    def _find_acceptor(self, donor) -> Optional[Any]:
        candidates = [m for m in self.h_field 
                      if getattr(m, 'id', '') != getattr(donor, 'id', '')
                      and getattr(m, 'quality', 0) > 0.7]
        
        if not candidates:
            return None
        
        return min(candidates, key=lambda m: self._compute_topological_distance(donor, m))
    
    def _donate_to_acceptor(self, donor, acceptor) -> bool:
        """Прямое дарение: донор → конкретный акцептор."""
        donor_id = getattr(donor, 'id', 'unknown')
        acceptor_id = getattr(acceptor, 'id', 'unknown')
        
        donor_amp = getattr(donor, 'amplitude', 0.5)
        donor_tau = getattr(donor, 'tau', 8.0)
        donor_qual = getattr(donor, 'quality', 0.3)
        
        acceptor.amplitude = min(1.0, getattr(acceptor, 'amplitude', 0.5) + donor_amp * 0.3)
        acceptor.tau = (getattr(acceptor, 'tau', 8.0) + donor_tau) / 2
        acceptor.quality = min(1.0, getattr(acceptor, 'quality', 0.7) + donor_qual * 0.2)
        
        if not hasattr(acceptor, 'donations_received'):
            acceptor.donations_received = []
        acceptor.donations_received.append({
            'donor_id': donor_id,
            'donor_amp': donor_amp,
            'donor_tau': donor_tau,
            'timestamp': time.time(),
            'type': 'direct'
        })
        
        self.erythro['acceptor_bonuses'][acceptor_id] = (
            self.erythro['acceptor_bonuses'].get(acceptor_id, 0) + 1
        )
        
        self.h_field[:] = [m for m in self.h_field if getattr(m, 'id', '') != donor_id]
        
        self.erythro['total_deaths'] += 1
        self.erythro['donation_deaths'] += 1
        self.erythro['donation_history'].append({
            'donor': donor_id[:12],
            'acceptor': acceptor_id[:12],
            'type': 'direct',
            'cycle': self._cycle
        })
        if len(self.erythro['donation_history']) > 50:
            self.erythro['donation_history'] = self.erythro['donation_history'][-30:]
        
        return True
    
    def _donate_to_field(self, donor):
        """
        v4.1: Отдача в поле — энергия не теряется, а рассеивается по всем модам.
        """
        donor_id = getattr(donor, 'id', 'unknown')
        donor_amp = getattr(donor, 'amplitude', 0.5)
        donor_tau = getattr(donor, 'tau', 8.0)
        donor_qual = getattr(donor, 'quality', 0.3)
        
        # Энергия донора переходит в пул поля
        energy = donor_amp * 0.2 + donor_qual * 0.1
        self.erythro['field_energy_pool'] += energy
        
        # Микро-прирост всем оставшимся модам (ambient amplification)
        if self.h_field:
            per_mode_boost = energy / max(len(self.h_field), 1) * 0.5
            for mode in self.h_field:
                if getattr(mode, 'id', '') != donor_id:
                    mode.amplitude = min(1.0, getattr(mode, 'amplitude', 0.5) + per_mode_boost)
        
        # Запись эха в историю поля
        self.erythro['field_echoes'].append({
            'donor': donor_id[:12],
            'energy': round(energy, 4),
            'field_size': self.field_size,
            'cycle': self._cycle,
            'timestamp': time.time()
        })
        if len(self.erythro['field_echoes']) > 50:
            self.erythro['field_echoes'] = self.erythro['field_echoes'][-30:]
        
        # Удаление донора
        self.h_field[:] = [m for m in self.h_field if getattr(m, 'id', '') != donor_id]
        
        self.erythro['total_deaths'] += 1
        self.erythro['field_deaths'] += 1
        self.erythro['donation_history'].append({
            'donor': donor_id[:12],
            'acceptor': 'field',
            'type': 'field',
            'energy': round(energy, 4),
            'cycle': self._cycle
        })
        if len(self.erythro['donation_history']) > 50:
            self.erythro['donation_history'] = self.erythro['donation_history'][-30:]
    
    def _erythro_purge(self, weak_modes: List[Any]):
        """
        v4.1: Для каждой слабой моды — попытка найти акцептора.
        Если нет — отдача в поле (энергия не теряется).
        """
        donations = 0
        field_donations = 0
        
        for mode in weak_modes:
            acceptor = self._find_acceptor(mode)
            if acceptor:
                if self._donate_to_acceptor(mode, acceptor):
                    donations += 1
            else:
                self._donate_to_field(mode)
                field_donations += 1
        
        if donations > 0 or field_donations > 0:
            self.logger.info(
                f"🩸 ЭРИТРО-ТРАНСФЕР: {donations} прямых дарений, "
                f"{field_donations} в поле | "
                f"пул энергии: {self.erythro['field_energy_pool']:.2f} | "
                f"индекс: {self.erythro_index:.2%} | "
                f"чистота: {self.donation_purity:.2%}"
            )
    
    # ═══════════════════════ ИНИЦИАЛИЗАЦИЯ ═══════════════════════
    def _init_clusters(self):
        self.clusters = {
            1.0:  {'scale': 1.0,  'modes': [], 'phase': 0.0, 'frozen': False, 'scarred': False, 'inflamed': False, 'scar_count': 0},
            3.0:  {'scale': 3.0,  'modes': [], 'phase': 0.5, 'frozen': False, 'scarred': False, 'inflamed': False, 'scar_count': 0},
            6.0:  {'scale': 6.0,  'modes': [], 'phase': 1.0, 'frozen': False, 'scarred': False, 'inflamed': False, 'scar_count': 0},
            10.0: {'scale': 10.0, 'modes': [], 'phase': 1.5, 'frozen': True,  'scarred': False, 'inflamed': False, 'scar_count': 0},
        }
    
    # ═══════════════════════ ВНЕШНИЙ СИГНАЛ ═══════════════════════
    def ingest_external_signal(self, signal: Dict[str, Any]) -> bool:
        try:
            self.external_signal_queue.put(signal, timeout=0.1)
            return True
        except queue.Full:
            self.logger.warning("⚠️ Очередь сигналов переполнена")
            return False
    
    def _prioritize_signals(self):
        max_to_process = min(self.external_signal_queue.qsize(), 50)
        processed = 0
        
        while processed < max_to_process:
            try:
                sig = self.external_signal_queue.get_nowait()
            except queue.Empty:
                break
            
            content = sig.get('content', '')
            source = sig.get('source', 'unknown')
            
            immediate_stress = len(content) / 1000.0
            perspective_risk = (
                self.perspective_trajectory[0]['bifurcation_risk']
                if self.perspective_trajectory else 0.0
            )
            
            history_bonus = 0.0
            for h in self.signal_history[-20:]:
                if h.get('source') == source:
                    history_bonus += 0.1 if h.get('outcome') == 'beneficial' else -0.05
            
            priority = immediate_stress * 0.2 + perspective_risk * 0.6 + history_bonus * 0.2
            
            self.signal_priority_queue.append({
                'signal': sig,
                'priority': priority,
                'timestamp': time.time()
            })
            processed += 1
        
        if self.signal_priority_queue:
            self.signal_priority_queue.sort(key=lambda x: x['priority'], reverse=True)
            if len(self.signal_priority_queue) > 50:
                self.signal_priority_queue = self.signal_priority_queue[:50]
    
    def _process_signals(self):
        self._prioritize_signals()
        processed = 0
        
        while self.signal_priority_queue and processed < 5:
            item = self.signal_priority_queue.pop(0)
            sig = item['signal']
            
            result = self.process(
                sig.get('content', ''),
                sig.get('source', 'external')
            )
            
            outcome = 'beneficial' if result.get('coherence', 0) > 0.5 else 'stressful'
            self.signal_history.append({
                'source': sig.get('source', 'unknown'),
                'priority': item['priority'],
                'outcome': outcome,
                'timestamp': time.time()
            })
            processed += 1
        
        if len(self.signal_history) > 500:
            self.signal_history = self.signal_history[-300:]
    
    # ═══════════════════════ ЭМОЦИИ ═══════════════════════
    def _count_recent_anomaly_rate(self, lookback: int = 50) -> float:
        if not self.h_field:
            return 0.0
        
        actual_lookback = min(lookback, len(self.h_field))
        recent_modes = self.h_field[-actual_lookback:]
        mode_dicts = [
            {
                'source': getattr(m, 'source', ''),
                'tees': getattr(m, 'tees', ''),
                'receiver': getattr(m, 'receiver', '')
            }
            for m in recent_modes
        ]
        
        try:
            total_anomalies = len(self.validator.find_anomalies(mode_dicts))
            return total_anomalies / actual_lookback
        except Exception:
            return 0.0
    
    def _update_emotions(self):
        target_dopamine = self.coherence * 0.7
        self.hormones['dopamine'] += (target_dopamine - self.hormones['dopamine']) * 0.1
        
        target_cortisol = self.anomaly_rate + self.active_dominant_count * 0.1
        self.hormones['cortisol'] += (target_cortisol - self.hormones['cortisol']) * 0.15
        
        fatigue = min(self.dialog_count / 50, 0.8)
        self.hormones['melatonin'] += (1.0 - fatigue - self.hormones['melatonin']) * 0.05
        
        self.hormones['adrenaline'] *= 0.7
    
    def _experience_joy(self, reason: str):
        self.hormones['dopamine'] = min(1.0, self.hormones['dopamine'] + 0.15)
        self.logger.info(f"😊 КАЙФ: {reason} (дофамин={self.hormones['dopamine']:.2f})")
    
    def _use_comfort_resource(self):
        if self.hormones['dopamine'] < 0.65:
            return
        
        if self.furcation_depth < 3:
            self.furcation_depth = min(3, self.max_depth)
        
        for scale, cluster in self.clusters.items():
            if not cluster.get('inflamed') and not cluster.get('scarred') and not cluster.get('frozen'):
                modes = [m for m in self.h_field if getattr(m, 'scale', 1.0) == scale]
                if modes and self._calculate_cluster_coherence(modes) < 0.7:
                    self._regenerate_field()
                    break
    
    # ═══════════════════════ ГИПОТАЛАМУС (ЖЁСТКИЕ ПОРОГИ v3.1) ═══════════════════════
    def _thermal_regulation(self):
        if time.time() - self._last_thermal_action < self._thermal_cooldown:
            return
        
        temp = self.temp_buffer.push(self.temperature)
        modes = self.h_field
        
        anomaly_rate = 0.0
        anomaly_patterns = []
        seen_patterns = set()
        
        if modes:
            try:
                recent_modes = modes[-100:]
                mode_dicts = [
                    {
                        'source': getattr(m, 'source', ''),
                        'tees': getattr(m, 'tees', ''),
                        'receiver': getattr(m, 'receiver', '')
                    }
                    for m in recent_modes
                ]
                anomalies = self.validator.find_anomalies(mode_dicts)
                anomaly_rate = len(anomalies) / min(100, len(modes))
                
                for mode in recent_modes:
                    src = getattr(mode, 'source', '')[:10]
                    if src and src not in seen_patterns:
                        anomaly_patterns.append(src)
                        seen_patterns.add(src)
            except Exception:
                pass
        
        action_taken = False
        
        if temp < 45:
            if self._thermal_mode != "normal":
                self.logger.info(f"🌡️ Возврат к норме: t={temp:.1f}°")
            self._thermal_mode = "normal"
            self._regeneration_active = False
            return
        
        elif temp < 55:
            if anomaly_rate > 0.6:
                self._thermal_mode = "fever"
                self._local_inflammation()
                self.furcation_depth = 1
                self.validation_interval = 3
                self.band_coefficients = min(self.band_coefficients + 2, self.max_bands)
                
                for pattern in anomaly_patterns:
                    if pattern in self.immune_memory:
                        self.immune_memory[pattern]['count'] += 1
                        self.immune_memory[pattern]['last_seen'] = time.time()
                    else:
                        self.immune_memory[pattern] = {
                            'count': 1,
                            'last_seen': time.time(),
                            'severity': anomaly_rate
                        }
                
                action_taken = True
                self.logger.warning(
                    f"🦠 ЛИХОРАДКА: t={temp:.1f}°, память: {len(self.immune_memory)}"
                )
            
            elif anomaly_rate < 0.4 and self._thermal_mode == "fever":
                self._thermal_mode = "regeneration"
                self._regeneration_active = True
                self._regenerate_field()
                action_taken = True
        
        elif self._thermal_mode == "regeneration":
            if self.coherence > 0.98 and anomaly_rate < 0.3:
                self._thermal_mode = "normal"
                self._regeneration_active = False
                self.furcation_depth = 1
            else:
                self._regenerate_field()
                action_taken = True
        
        elif temp < 65:
            self._thermal_mode = "cooling"
            self.furcation_depth = 1
            self.purge_weak_modes(0.5)
            self.clear_cache()
            action_taken = True
        
        elif temp < 70:
            self._thermal_mode = "critical"
            self.furcation_depth = 0
            self.purge_weak_modes(0.7)
            action_taken = True
        
        else:
            self._thermal_mode = "critical"
            self.furcation_depth = 0
        
        if action_taken:
            self._last_thermal_action = time.time()
    
    def _local_inflammation(self):
        """Локальное воспаление с эритроцитарным трансфером v4.1."""
        if time.time() - self._last_local_purge < self._local_purge_cooldown:
            return
        if self.field_size < 50:
            return
        
        clusters = {}
        for mode in self.h_field:
            scale = getattr(mode, 'scale', 1.0)
            clusters.setdefault(scale, []).append(mode)
        
        total_purged = 0
        max_anomaly_ratio = 0.0
        all_weak_modes = []
        
        for scale, modes in clusters.items():
            if len(modes) < 10:
                continue
            
            try:
                mode_dicts = [
                    {
                        'source': getattr(m, 'source', ''),
                        'tees': getattr(m, 'tees', ''),
                        'receiver': getattr(m, 'receiver', '')
                    }
                    for m in modes
                ]
                anomalies = self.validator.find_anomalies(mode_dicts)
            except Exception:
                continue
            
            anomaly_ratio = len(anomalies) / len(modes)
            max_anomaly_ratio = max(max_anomaly_ratio, anomaly_ratio)
            
            if anomaly_ratio > 0.8:
                weak_modes = [m for m in modes if getattr(m, 'quality', 0) < 0.5]
                all_weak_modes.extend(weak_modes)
                
                if scale in self.clusters:
                    self.clusters[scale]['inflamed'] = True
                
                scale_key = f"scale_{scale}"
                if scale_key not in self.active_dominants:
                    self.active_dominants[scale_key] = {
                        'created_at': time.time(),
                        'severity': anomaly_ratio,
                        'scale': scale
                    }
        
        if all_weak_modes:
            total_purged = len(all_weak_modes)
            self._erythro_purge(all_weak_modes)
        
        if total_purged > 0:
            self.temperature = 30.0 + self.field_size * 0.01
            if max_anomaly_ratio > 0.9:
                self._local_purge_cooldown = 60
            elif max_anomaly_ratio > 0.8:
                self._local_purge_cooldown = 120
            else:
                self._local_purge_cooldown = 300
        else:
            self._local_purge_cooldown = min(self._local_purge_cooldown * 2, 600)
        
        self._last_local_purge = time.time()
    
    def _regenerate_field(self):
        if not self._regeneration_active:
            return
        
        healthy = [s for s, c in self.clusters.items() if not c.get('inflamed', False)]
        if healthy:
            self.furcation_depth = min(3, self.max_depth)
        
        if self.coherence > 0.98:
            self._regeneration_active = False
            self._thermal_mode = "normal"
            self.furcation_depth = 1
            self._experience_joy("регенерация завершена")
    
    def _resolve_dominants(self):
        if not self.active_dominants:
            return
        
        resolved = []
        for scale_key, dominant in self.active_dominants.items():
            scale = dominant['scale']
            c_modes = [m for m in self.h_field if getattr(m, 'scale', 1.0) == scale]
            
            if len(c_modes) < 5:
                resolved.append(scale_key)
                continue
            
            try:
                mode_dicts = [
                    {
                        'source': getattr(m, 'source', ''),
                        'tees': getattr(m, 'tees', ''),
                        'receiver': getattr(m, 'receiver', '')
                    }
                    for m in c_modes
                ]
                anomalies = self.validator.find_anomalies(mode_dicts)
            except Exception:
                continue
            
            ar = len(anomalies) / len(c_modes) if c_modes else 0
            
            if ar < 0.2 and time.time() - dominant['created_at'] > 300:
                resolved.append(scale_key)
                if scale in self.clusters:
                    self.clusters[scale]['scarred'] = False
                    self.clusters[scale]['inflamed'] = False
                self.furcation_depth = min(3, self.max_depth)
        
        for key in resolved:
            del self.active_dominants[key]
    
    def emdr_session(self, scale_key: str = None):
        if scale_key:
            self._emdr_single(scale_key)
        else:
            for key in list(self.active_dominants.keys()):
                self._emdr_single(key)
    
    def _emdr_single(self, scale_key: str):
        dominant = self.active_dominants.get(scale_key)
        if not dominant:
            return
        
        scale = dominant['scale']
        cluster_modes = [m for m in self.h_field if getattr(m, 'scale', 1.0) == scale]
        
        if len(cluster_modes) < 3:
            del self.active_dominants[scale_key]
            return
        
        for i in range(40):
            for mode in cluster_modes:
                mode.phase = (getattr(mode, 'phase', 0.0) + 0.3) % 2.0
                mode.amplitude = getattr(mode, 'amplitude', 0.5) * (1.1 if i % 2 == 0 else 0.9)
            time.sleep(0.05)
        
        available_scales = [
            s for s in self.clusters
            if s != scale and not self.clusters[s].get('frozen', False)
        ]
        if available_scales:
            for mode in cluster_modes:
                mode.scale = random.choice(available_scales)
        
        del self.active_dominants[scale_key]
        if scale in self.clusters:
            self.clusters[scale]['scarred'] = False
            self.clusters[scale]['inflamed'] = False
        
        self.temperature = 30.0 + self.field_size * 0.01
        self.logger.info(f"✅ EMDR: доминанта {scale_key} снята")
        self._experience_joy("EMDR снял доминанту")
    
    # ═══════════════════════ SCAR INDEX ═══════════════════════
    def _update_scar_index(self):
        scarred = inflamed = scar_count = 0
        
        for c in self.clusters.values():
            if c.get('scarred'):
                scarred += 1
            if c.get('inflamed'):
                inflamed += 1
            scar_count += c.get('scar_count', 0)
        
        total = len(self.clusters)
        self.scar_index = (
            scarred * 0.4 + inflamed * 0.4 + min(scar_count / 10, 1.0) * 0.2
        ) / max(total, 1)
        
        if self.scar_index > 0.5:
            self.logger.warning(
                f"🔴 Scar Index = {self.scar_index:.2f} → принудительная регенерация"
            )
            self._regeneration_active = True
            self._regenerate_field()
        elif self.scar_index > 0.2:
            self.logger.info(
                f"🟡 Scar Index = {self.scar_index:.2f} → профилактика"
            )
            for scale, cluster in self.clusters.items():
                if cluster.get('scarred') and not cluster.get('frozen'):
                    cluster['scarred'] = False
                    self._experience_joy(f"шрам {scale} исцелён")
    
    # ═══════════════════════ ДЕТЕРМИНИРОВАННЫЕ ГЕНЕРАТОРЫ ═══════════════════════
    def _next_deterministic_seed(self) -> int:
        self._seed_counter += 1
        field_hash = sum(
            hash(str(getattr(m, 'source', ''))[:10])
            for m in self.h_field[-20:]
        )
        return simple_tees_hash(
            f"{field_hash}_{self._field_state}_{self._seed_counter}".encode('utf-8')
        )
    
    def _seed_to_label(self, seed: int, prefix: str = "node") -> str:
        return f"{prefix}_{seed % 10000:04d}"
    
    def _compute_amplitude_from_charge(self, seed: int) -> float:
        try:
            vortex = seed_to_vortex(seed, VortexConfig())
            return round(
                0.3 + min(abs(compute_topological_charge(vortex)), 2.0) / 2.0 * 0.65,
                4
            )
        except Exception:
            return 0.5
    
    def _compute_tau_from_shift(self, s_seed: int, t_seed: int) -> float:
        try:
            s = seed_to_vortex(s_seed, VortexConfig())
            t = seed_to_vortex(t_seed, VortexConfig())
            return round(
                5.0 + abs(tees_shift(s, t)) * 6.0,
                4
            )
        except Exception:
            return 8.0
    
    def _determine_scale(self, seed: int) -> float:
        base = (seed % 4 + 1) * 2.5
        available = [s for s, c in self.clusters.items() if not c['frozen']]
        if available:
            return min(available, key=lambda s: abs(s - base))
        return base
    
    def _compute_quality(self, mode) -> float:
        try:
            src = mode.source[:20]
            tee = mode.tees[:20]
            dst = mode.receiver[:20]
            ok, charge, _ = validate_triple(src, tee, dst)
            return 0.7 + min(charge, 1.0) * 0.3 if ok else 0.1 + min(charge, 0.5) * 0.4
        except Exception:
            return 0.5
    
    def _passes_vmmp_filter(self, mode) -> bool:
        if hasattr(mode, 'source') and hasattr(mode, 'tees') and hasattr(mode, 'receiver'):
            ok, _, _ = validate_triple(
                mode.source[:20], mode.tees[:20], mode.receiver[:20]
            )
            if ok:
                return True
        
        tau = getattr(mode, 'tau', 0)
        scale = getattr(mode, 'scale', 1.0)
        amp = getattr(mode, 'amplitude', 0.5)
        
        if scale >= 20.0 or amp >= 0.7:
            return True
        if 5.0 <= tau <= 11.0:
            return True
        if (tau < 5.0 or tau > 11.0) and scale >= 10.0 and amp >= 0.6:
            return True
        
        return False
    
    # ═══════════════════════ ПЕРСПЕКТИВА И АДАПТАЦИЯ ═══════════════════════
    def _snapshot_field(self) -> int:
        state_hash = self._field_state
        for mode in self.h_field[-10:]:
            if hasattr(mode, 'source'):
                state_hash ^= hash(str(mode.source)[:5])
        return state_hash
    
    def _compute_perspective(self) -> List[Dict]:
        trajectory = []
        shadow = self._snapshot_field()
        
        for step in range(1, self.perspective_horizon + 1):
            shadow = simple_tees_hash(str(shadow).encode('utf-8'))
            sample = shadow % 1000
            pred_coherence = max(
                0.9,
                min(0.999, self.coherence - step * 0.002 * (1 + sample % 3 / 10))
            )
            pred_entropy = max(1.0, min(10.0, 3.0 + (1.0 - pred_coherence) * 50))
            
            risk = 0.0
            if pred_coherence < 0.97:
                risk = min(1.0, (0.97 - pred_coherence) * 30)
            if pred_entropy > 6:
                risk = max(risk, (pred_entropy - 6) / 4)
            
            trajectory.append({
                'step': step,
                'predicted_coherence': round(pred_coherence, 4),
                'predicted_entropy': round(pred_entropy, 2),
                'bifurcation_risk': round(risk, 4)
            })
        
        return trajectory
    
    def _can_change_precision(self) -> bool:
        return time.time() - self._last_precision_change > self._precision_cooldown
    
    def _adapt_precision(self):
        if not self._can_change_precision():
            return
        
        metrics = self.get_metrics()
        entropy = self.entropy_buffer.push(metrics['entropy'])
        temp = self.temp_buffer.push(self.temperature)
        coherence = self.coherence_buffer.push(self.coherence)
        
        self.perspective_trajectory = self._compute_perspective()
        next_crisis = next(
            (p for p in self.perspective_trajectory if p['bifurcation_risk'] > 0.7),
            None
        )
        
        changed = False
        old_bands = self.band_coefficients
        old_epochs = self.convergence_epochs
        old_depth = self.furcation_depth
        
        if next_crisis:
            steps = next_crisis['step']
            if steps <= 2:
                self.band_coefficients = self.max_bands
                self.convergence_epochs = self.max_epochs
                self.furcation_depth = self.max_depth
                self.validation_interval = 5
                changed = True
            elif steps <= 4:
                self.band_coefficients = min(self.band_coefficients + 2, self.max_bands)
                self.convergence_epochs = min(self.convergence_epochs + 2, self.max_epochs)
                self.furcation_depth = min(self.furcation_depth + 1, self.max_depth)
                self.validation_interval = 8
                changed = True
        
        if not changed:
            if entropy > 7.0 and self.band_coefficients < self.max_bands:
                self.band_coefficients += 2
                changed = True
            elif entropy < 4.0 and self.band_coefficients > self.min_bands:
                self.band_coefficients -= 1
                changed = True
            
            if temp > 60.0 and self.convergence_epochs < self.max_epochs:
                self.convergence_epochs += 2
                changed = True
            elif temp < 35.0 and self.convergence_epochs > self.min_epochs:
                self.convergence_epochs -= 1
                changed = True
            
            if coherence < 0.97:
                self.furcation_depth = min(self.furcation_depth + 1, self.max_depth)
                changed = True
            elif coherence > 0.995:
                self.furcation_depth = max(self.furcation_depth - 1, 1)
                changed = True
            
            self.validation_interval = 5 if entropy > 6 else (30 if entropy < 3 else 10)
        
        if changed:
            self._last_precision_change = time.time()
            self.logger.info(
                f"🎯 Адаптация: полос={old_bands}→{self.band_coefficients}, "
                f"эпох={old_epochs}→{self.convergence_epochs}, "
                f"глубина={old_depth}→{self.furcation_depth} "
                f"(t={temp:.1f}°, coh={coherence:.3f}, ent={entropy:.2f})"
            )
    
    def _should_bifurcate(self) -> bool:
        if self.coherence < 0.97:
            return True
        if (self._seed_counter % 100 / 100.0) > (0.8 + (1.0 - self.coherence) * 2):
            return True
        if self.perspective_trajectory and self.perspective_trajectory[0]['bifurcation_risk'] > 0.5:
            return True
        return False
    
    def furcate(self) -> List[Any]:
        self.furcation_count += 1
        self.coherence = max(0.95, self.coherence - 0.0005)
        new_modes = []
        
        for i in range(self.furcation_depth):
            src_s = self._next_deterministic_seed()
            tee_s = simple_tees_hash(str(src_s).encode('utf-8'))
            dst_s = simple_tees_hash(str(tee_s).encode('utf-8'))
            
            mode = type('Mode', (), {
                'id': f"furc_{self.generation}_{self.furcation_count}_{i}",
                'trace_id': f"trace_{src_s:08x}",
                'source': self._seed_to_label(src_s),
                'tees': self._seed_to_label(tee_s, "tees"),
                'receiver': self._seed_to_label(dst_s),
                'amplitude': self._compute_amplitude_from_charge(src_s),
                'tau': self._compute_tau_from_shift(src_s, tee_s),
                'scale': self._determine_scale(src_s),
                'phase': (self._seed_counter % 100) / 100.0,
                'generation': self.generation,
                'furcation_id': self.furcation_count,
                'quality': 0.0,
                'coherence': self.coherence,
                'entropy': 0.0,
                'donations_received': [],
            })()
            
            mode.quality = self._compute_quality(mode)
            
            if self._passes_vmmp_filter(mode):
                self.add_mode(mode)
                new_modes.append(mode)
                self._field_state ^= src_s
        
        if new_modes:
            self.nodes_created += len(new_modes)
            self.generation += 1
        
        return new_modes
    
    def add_mode(self, mode):
        if self._passes_vmmp_filter(mode):
            if not hasattr(mode, 'donations_received'):
                mode.donations_received = []
            self.h_field.append(mode)
            self.temperature = 30.0 + self.field_size * 0.01
            return True
        return False
    
    def add_clusters(self, clusters):
        for c in clusters:
            if isinstance(c, list):
                for m in c:
                    self.add_mode(m)
            else:
                self.add_mode(c)
    
    def get_all_modes(self) -> List[Any]:
        return self.h_field
    
    def remove_mode(self, mode_id: str):
        self.h_field[:] = [m for m in self.h_field if getattr(m, 'id', '') != mode_id]
        self.temperature = 30.0 + self.field_size * 0.01
    
    def purge_weak_modes(self, threshold: float = 0.3):
        before = self.field_size
        weak_modes = [m for m in self.h_field if getattr(m, 'quality', 0.5) < threshold]
        
        if weak_modes:
            self._erythro_purge(weak_modes)
        
        self.temperature = 30.0 + self.field_size * 0.01
        
        if before > self.field_size:
            self.logger.info(
                f"🧹 purge: {before} → {self.field_size} "
                f"(эритро-индекс={self.erythro_index:.2%}, "
                f"пул энергии={self.erythro['field_energy_pool']:.2f})"
            )
    
    def mark_for_review(self, mode_id: str):
        for mode in self.h_field:
            if getattr(mode, 'id', '') == mode_id:
                mode._flagged = True
                break
    
    def clear_cache(self):
        self.entropy_buffer.clear()
        self.temp_buffer.clear()
        self.coherence_buffer.clear()
    
    def _calculate_cluster_coherence(self, modes) -> float:
        if not modes:
            return 1.0
        return sum(getattr(m, 'quality', 0.5) for m in modes) / len(modes)
    
    def get_metrics(self) -> Dict[str, float]:
        return {
            'temperature': self.temperature,
            'entropy': max(1.0, 5.0 - self.coherence * 5.0)
        }
    
    # ═══════════════════════ ОБРАБОТКА ДИАЛОГА ═══════════════════════
    def process(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        self.dialog_count += 1
        self.experience += 1
        
        sentiment = self._detect_sentiment(text)
        self.mood = self.mood * 0.9 + sentiment * 0.1
        self.mood_history.append(self.mood)
        
        best_mode, best_score, source = self._find_best_mode(text)
        
        if best_mode and best_score > 0.15:
            answer = getattr(best_mode, 'content', str(best_mode))[:500]
            mode_used = getattr(best_mode, 'trace_id', '?')[:16]
        else:
            answer = "Интересно... Расскажите подробнее?"
            mode_used, source, best_score = '?', 'fallback', 0.1
        
        return {
            "answer": answer,
            "mode_used": mode_used,
            "mode_type": source,
            "resonance": best_score,
            "mood": self.mood,
            "dialog_count": self.dialog_count
        }
    
    def _detect_sentiment(self, text: str) -> float:
        pos_words = ["хорош", "отличн", "прекрасн", "класс", "супер", "люблю", "нравит"]
        neg_words = ["плох", "ужасн", "ненавиж", "грустн", "печальн", "зл", "обид"]
        
        text_lower = text.lower()
        pos = sum(1 for w in pos_words if w in text_lower)
        neg = sum(1 for w in neg_words if w in text_lower)
        
        if pos + neg == 0:
            return 0.0
        return (pos - neg) / (pos + neg)
    
    def _find_best_mode(self, text: str) -> Tuple[Any, float, str]:
        if not self.h_field:
            return None, 0.0, "empty"
        
        best = max(self.h_field, key=lambda m: getattr(m, 'amplitude', 0.5))
        return best, min(1.0, getattr(best, 'amplitude', 0.5) * 1.5), "amplitude"
    
    # ═══════════════════════ ЖИЗНЕННЫЙ ЦИКЛ ═══════════════════════
    def start_living(self, interval: float = 0.5):
        if self._running:
            return
        self._running = True
        self._bg_thread = threading.Thread(
            target=self._living_loop, args=(interval,), daemon=True
        )
        self._bg_thread.start()
        self.logger.info("🌿 Эндогенный цикл v4.1 запущен")
    
    def stop_living(self):
        self._running = False
        self.logger.info("🛑 Цикл остановлен")
    
    def _living_loop(self, interval: float):
        """Главный цикл v4.1."""
        while self._running:
            time.sleep(interval)
            self._cycle += 1
            
            cycle_mod10 = self._cycle % 10 == 0
            cycle_mod20 = self._cycle % 20 == 0
            cycle_mod30 = self._cycle % 30 == 0
            cycle_mod120 = self._cycle % 120 == 0
            cycle_mod300 = self._cycle % 300 == 0
            cycle_mod600 = self._cycle % 600 == 0
            
            self._process_signals()
            
            if cycle_mod10:
                self._adapt_precision()
                self._update_emotions()
                self._use_comfort_resource()
                if not self._should_bifurcate():
                    self.coherence = min(0.998, self.coherence + 0.0001)
            
            if cycle_mod20:
                self._thermal_regulation()
            
            if cycle_mod30:
                self._resolve_dominants()
                self._update_clusters()
            
            if cycle_mod120:
                self._print_status()
            
            if cycle_mod300:
                self._update_scar_index()
            
            if cycle_mod600:
                for key, dom in list(self.active_dominants.items()):
                    if time.time() - dom['created_at'] > 3600:
                        scale = dom['scale']
                        c_modes = [
                            m for m in self.h_field
                            if getattr(m, 'scale', 1.0) == scale
                        ]
                        if c_modes:
                            try:
                                mode_dicts = [
                                    {
                                        'source': getattr(m, 'source', ''),
                                        'tees': getattr(m, 'tees', ''),
                                        'receiver': getattr(m, 'receiver', '')
                                    }
                                    for m in c_modes
                                ]
                                anomalies = self.validator.find_anomalies(mode_dicts)
                                if len(anomalies) / len(c_modes) > 0.4:
                                    self.logger.warning(f"👁️ АВТО-EMDR: {key}")
                                    self.emdr_session(key)
                            except Exception:
                                pass
            
            if self._should_bifurcate():
                new_modes = self.furcate()
                if new_modes:
                    self.logger.debug(f"🌀 Фуркация: {len(new_modes)} мод")
            
            val_cycles = max(1, int(self.validation_interval / interval))
            if self._cycle % val_cycles == 0:
                self._validate_field()
    
    def _update_clusters(self):
        for scale, cluster in self.clusters.items():
            if not cluster['frozen']:
                cluster['phase'] = (cluster['phase'] + 0.01 * scale) % 2.0
    
    def _validate_field(self):
        if not self.h_field:
            return
        stats = get_cache_stats()
        self.logger.debug(f"✅ Валидация: {stats['passed']}/{stats['checked']}")
    
    def _print_status(self):
        d = self.hormones['dopamine']
        c = self.hormones['cortisol']
        emoji = "😊" if d > 0.6 else ("😐" if d > 0.4 else "😟")
        
        top_acceptors = sorted(
            self.erythro['acceptor_bonuses'].items(),
            key=lambda x: x[1], reverse=True
        )[:3]
        top_str = ", ".join(f"{aid[:8]}:{n}" for aid, n in top_acceptors) if top_acceptors else "нет"
        
        print(f"\n🌱 {self.name} — цикл {self._cycle}:")
        print(f"   Мод: {self.field_size} | "
              f"Когерентность: {self.coherence:.4f} | "
              f"t={self.temperature:.1f}° [{self._thermal_mode}]")
        print(f"   Фуркаций: {self.furcation_count} | "
              f"Глубина: {self.furcation_depth} | "
              f"Шрамы: {self.scar_index:.2f}")
        print(f"   Дофамин: {d:.2f} {emoji} | "
              f"Кортизол: {c:.2f} | "
              f"Доминант: {self.active_dominant_count}")
        print(f"   🩸 Эритро-индекс: {self.erythro_index:.2%} | "
              f"Чистота: {self.donation_purity:.2%} | "
              f"Пул энергии: {self.erythro['field_energy_pool']:.2f}")
        print(f"   📡 Прямых дарений: {self.erythro['donation_deaths']} | "
              f"В поле: {self.erythro['field_deaths']}")
        print(f"   🏆 Топ-акцепторы: {top_str}")
        
        if self.perspective_trajectory:
            print(f"   Перспектива: риск {self.perspective_trajectory[0]['bifurcation_risk']:.2%}")
    
    # ═══════════════════════ СОХРАНЕНИЕ / ЗАГРУЗКА ═══════════════════════
    def save(self, filepath: str):
        modes_data = [
            {
                'id': getattr(m, 'id', '?'),
                'source': getattr(m, 'source', ''),
                'tees': getattr(m, 'tees', ''),
                'receiver': getattr(m, 'receiver', ''),
                'amplitude': getattr(m, 'amplitude', 0),
                'tau': getattr(m, 'tau', 0),
                'scale': getattr(m, 'scale', 0),
                'quality': getattr(m, 'quality', 0),
                'generation': getattr(m, 'generation', 0),
                'donations_received': getattr(m, 'donations_received', [])[-10:],
            }
            for m in self.h_field[-1000:]
        ]
        
        data = {
            "id": self.id,
            "name": self.name,
            "version": "4.1",
            "generation": self.generation,
            "coherence": self.coherence,
            "nodes_created": self.nodes_created,
            "furcation_count": self.furcation_count,
            "traits": self.traits,
            "mood": self.mood,
            "dialog_count": self.dialog_count,
            "h_field_size": self.field_size,
            "temperature": self.temperature,
            "band_coefficients": self.band_coefficients,
            "convergence_epochs": self.convergence_epochs,
            "furcation_depth": self.furcation_depth,
            "thermal_mode": self._thermal_mode,
            "scar_index": self.scar_index,
            "hormones": self.hormones,
            "immune_memory_size": len(self.immune_memory),
            "active_dominants": self.active_dominant_count,
            "erythro": {
                'total_deaths': self.erythro['total_deaths'],
                'donation_deaths': self.erythro['donation_deaths'],
                'field_deaths': self.erythro['field_deaths'],
                'field_energy_pool': self.erythro['field_energy_pool'],
                'erythro_index': self.erythro_index,
                'donation_purity': self.donation_purity,
            },
            "modes": modes_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(
            f"💾 Сохранено: {len(modes_data)} мод, t={self.temperature:.1f}°, "
            f"эритро-индекс={self.erythro_index:.2%}, "
            f"пул энергии={self.erythro['field_energy_pool']:.2f}"
        )
    
    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        instance = cls(data.get("id", "living_v4"), data.get("name", "Живая личность v4.1"))
        instance.generation = data.get("generation", 0)
        instance.coherence = data.get("coherence", 0.993)
        instance.nodes_created = data.get("nodes_created", 0)
        instance.furcation_count = data.get("furcation_count", 0)
        instance.mood = data.get("mood", 0.0)
        instance.dialog_count = data.get("dialog_count", 0)
        instance.temperature = data.get("temperature", 30.0)
        instance.band_coefficients = data.get("band_coefficients", 8)
        instance.convergence_epochs = data.get("convergence_epochs", 5)
        instance.furcation_depth = data.get("furcation_depth", 1)
        instance._thermal_mode = data.get("thermal_mode", "normal")
        instance.scar_index = data.get("scar_index", 0.0)
        instance.hormones = data.get("hormones", instance.hormones)
        
        erythro_data = data.get("erythro", {})
        instance.erythro['total_deaths'] = erythro_data.get('total_deaths', 0)
        instance.erythro['donation_deaths'] = erythro_data.get('donation_deaths', 0)
        instance.erythro['field_deaths'] = erythro_data.get('field_deaths', 0)
        instance.erythro['field_energy_pool'] = erythro_data.get('field_energy_pool', 0.0)
        
        for k, v in data.get("traits", {}).items():
            if k in instance.traits:
                instance.traits[k] = v
        
        for m_data in data.get("modes", []):
            mode = type('Mode', (), {
                k: m_data.get(k, '')
                for k in ['id', 'source', 'tees', 'receiver', 'amplitude', 'tau', 'scale', 'quality']
            })()
            mode.donations_received = m_data.get('donations_received', [])
            instance.h_field.append(mode)
        
        instance.logger.info(
            f"📂 Загружено: {instance.field_size} мод (v4.1), "
            f"эритро-индекс={instance.erythro_index:.2%}"
        )
        return instance


# ══════════════════════════════════════
# ЯДРО TEES v4.1
# ══════════════════════════════════════
class TEESCoreV3:
    """Ядро системы v4.1 с трассируемой отдачей."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.running = True
        
        self.personality = (
            LivingFieldV3.load(PERSONALITY_FILE)
            if os.path.exists(PERSONALITY_FILE)
            else LivingFieldV3()
        )
        
        self.router = (
            TurboTEES(field_size=32, cache_size=500)
            if HAS_ROUTER
            else DummyRouter()
        )
        
        self.threads = [
            threading.Thread(target=self._furcator_loop, name="Furcator", daemon=True),
            threading.Thread(target=self._resonator_loop, name="Resonator", daemon=True),
            threading.Thread(target=self._signal_loop, name="SignalListener", daemon=True),
            threading.Thread(target=self._auto_save_loop, name="AutoSaver", daemon=True),
            threading.Thread(target=self._homeostasis_loop, name="Homeostasis", daemon=True),
        ]
        
        self.logger.info("✅ TEES Core v4.1 инициализирован")
    
    def _setup_logger(self):
        logger = logging.getLogger("TEESCoreV3")
        logger.setLevel(logging.INFO)
        
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)-7s] %(message)s', datefmt='%H:%M:%S'
        ))
        
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)-7s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        logger.addHandler(console)
        logger.addHandler(file_handler)
        return logger
    
    def _furcator_loop(self):
        self.logger.info("🌀 Furcator запущен")
        while self.running:
            time.sleep(30)
            try:
                self.personality.furcate()
            except Exception as e:
                self.logger.error(f"Furcator: {e}")
    
    def _resonator_loop(self):
        self.logger.info("🔮 Resonator запущен")
        while self.running:
            time.sleep(15)
            try:
                self.personality._update_clusters()
            except Exception as e:
                self.logger.error(f"Resonator: {e}")
    
    def _signal_loop(self):
        self.logger.info("📡 Signal Listener запущен")
        while self.running:
            time.sleep(15)
    
    def _auto_save_loop(self):
        self.logger.info("💾 AutoSaver запущен")
        while self.running:
            time.sleep(600)
            try:
                self.personality.save(PERSONALITY_FILE)
            except Exception as e:
                self.logger.error(f"Save: {e}")
    
    def _homeostasis_loop(self):
        self.logger.info("🌡️ Homeostasis запущен")
        while self.running:
            time.sleep(30)
            t = self.personality.temperature
            if t > 70:
                self.logger.error("💀 СТОПКРАН!")
                self.running = False
    
    def start(self):
        self.logger.info("🚀 Запуск TEES Core v4.1...")
        self.personality.start_living()
        for t in self.threads:
            t.start()
        self.logger.info(f"✅ {len(self.threads)} потоков запущено")
    
    def stop(self):
        self.running = False
        self.personality.stop_living()
        for t in self.threads:
            t.join(timeout=3)
        self.personality.save(PERSONALITY_FILE)
        self.logger.info("✅ Остановлен")


# ══════════════════════════════════════
# ТОЧКА ВХОДА
# ══════════════════════════════════════
if __name__ == "__main__":
    core = TEESCoreV3()
    try:
        core.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        core.stop()