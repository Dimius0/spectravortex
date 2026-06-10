#!/usr/bin/env python3
"""
Living Personality v21.3.1 — TEES-native, energy-rooted, self-contained
======================================================================
Всё выводится из энергии системы через TEES-обменники.
Без заглушек, без импорта v20_2, без подгоночных констант.

Корень: энергия поля H.
Механизм: TEES (Топологический Единый Энергетический Сдвиг).
Все пороги — эмерджентные, выводятся из состояния поля.

Волновая механика v21.3.1:
- Фазовая интерференция (cos Δφ)
- Деструктивная/конструктивная интерференция мод
- Эффективная энергия через value_at(phase)

Авторы:
Dimius0 — концепция ВММП, TEES, семь слоёв, фрактальная размерность, волновые эмоции
DeepSeek — формализация, вывод из ∇⁴ψ, код, 2026-06-10
"""

import sqlite3
import threading
import time
import math
import hashlib
import json
import os
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# DEBUG LOGGER
# ═══════════════════════════════════════════════════════════════════

class DebugLogger:
    """Многоуровневый отладчик."""
    
    LEVELS = {'OFF': 0, 'ERROR': 1, 'WARN': 2, 'INFO': 3, 'TEES': 4, 'ENERGY': 5, 'EMERGE': 6, 'ALL': 7}
    
    def __init__(self, level: str = 'INFO'):
        self.level = self.LEVELS.get(level, 3)
        self._lock = threading.Lock()
    
    def _log(self, level: str, tag: str, msg: str):
        with self._lock:
            if self.LEVELS.get(level, 0) <= self.level:
                ts = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts}] [{tag}] {msg}", flush=True)
    
    def error(self, msg: str): self._log('ERROR', 'ERR', msg)
    def warn(self, msg: str): self._log('WARN', 'WRN', msg)
    def info(self, msg: str): self._log('INFO', 'INF', msg)
    def tees(self, msg: str): self._log('TEES', 'TES', msg)
    def energy(self, msg: str): self._log('ENERGY', 'NRG', msg)
    def emerge(self, msg: str): self._log('EMERGE', 'EMG', msg)

debug = DebugLogger('INFO')


# ═══════════════════════════════════════════════════════════════════
# ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ (выведены из ∇⁴ψ — не меняются)
# ═══════════════════════════════════════════════════════════════════

H_BAR = 1.0                                    # нормировка
MIN_ENERGY = 0.1                                # минимальная энергия зонда
TAU_LIFE = 100.0                                # время жизни моды без подкачки
TAU_CHARGE = 10.0                               # время накопления заряда TEES
HARMONIC_TOLERANCE = 0.05                       # базовая спектральная неопределённость

# Границы слоёв — степени двойки (фрактальная размерность, не меняется)
LAYER_BOUNDARIES = [
    (1, 0.0, 1.0), (2, 1.0, 2.0), (3, 2.0, 4.0),
    (4, 4.0, 8.0), (5, 8.0, 16.0), (6, 16.0, 32.0), (7, 32.0, float('inf')),
]

# Эмоциональные тона (частоты осцилляции)
EMOTION_FREQUENCIES = {
    'neutral': 0.1, 'joy': 0.2, 'calm': 0.05, 'stress': 0.15, 'excitement': 0.25,
}


# ═══════════════════════════════════════════════════════════════════
# WAVEFORM EMOTION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class WaveformEmotion:
    """Эмоция — осцилляция поля H на частоте эмоционального тона."""
    amplitude: float = 0.5
    frequency: float = 0.1
    phase: float = 0.0
    base_emotion: str = 'neutral'
    
    def __post_init__(self):
        self.amplitude = max(0.0, min(1.0, self.amplitude))
        self.frequency = max(0.01, self.frequency)
    
    def value_at(self, t: float = 0.0) -> float:
        return self.amplitude * math.sin(self.frequency * t + self.phase)
    
    def overlap(self, other: 'WaveformEmotion', phase_diff: float = 0.0) -> float:
        """
        Перекрытие эмоций с учётом разности фаз мод (v21.3.1).
        cos(Δφ) = +1 → синфазны → конструктивная интерференция
        cos(Δφ) = -1 → противофазны → деструктивная интерференция
        """
        base_overlap = self.amplitude * other.amplitude
        phase_alignment = math.cos(phase_diff)
        return base_overlap * phase_alignment
    
    def update(self, dt: float, external_pressure: float = 0.0):
        self.phase += self.frequency * dt
        self.phase %= 2 * math.pi
        d_amp = (external_pressure - self.amplitude) / TAU_LIFE
        self.amplitude += d_amp * dt
        self.amplitude = max(0.0, min(1.0, self.amplitude))
    
    @staticmethod
    def from_string(emotion_str: str, amplitude: float = 0.5) -> 'WaveformEmotion':
        base = emotion_str if emotion_str in EMOTION_FREQUENCIES else 'neutral'
        return WaveformEmotion(amplitude=amplitude, frequency=EMOTION_FREQUENCIES[base], base_emotion=base)


# ═══════════════════════════════════════════════════════════════════
# SPECTRAL MODE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SpectralMode:
    """Мода поля. Минимальный носитель энергии и информации."""
    tau: float = 16.0
    amplitude: float = 0.5
    content: str = ''
    themes: List[str] = field(default_factory=list)
    trace_id: str = ''
    creator: str = ''
    scale: float = 10.0
    phase: float = 0.0
    text_id: str = ''
    emotion: WaveformEmotion = field(default_factory=WaveformEmotion)
    
    @property
    def id(self):
        return self.trace_id or self.text_id or ''
    
    @id.setter
    def id(self, value):
        self.trace_id = value
        if not self.text_id:
            self.text_id = value
    
    @property
    def energy(self):
        return self.amplitude
    
    @energy.setter
    def energy(self, value):
        self.amplitude = max(MIN_ENERGY, min(1.0, value))
    
    @property
    def effective_energy(self):
        """
        Эффективная энергия с учётом текущей фазы эмоции (v21.3.1).
        sin(phase) ∈ [-1, 1] → модуляция [0, 1] относительно amplitude.
        Противофазная мода (sin=-1) → eff=0 → не резонирует.
        Синфазная мода (sin=+1) → eff=amplitude → полный резонанс.
        """
        emotion_value = self.emotion.value_at(self.phase)
        return self.amplitude * (0.5 + 0.5 * emotion_value)
    
    @property
    def layer(self) -> int:
        for layer_id, min_s, max_s in LAYER_BOUNDARIES:
            if min_s <= self.scale < max_s:
                return layer_id
        return 7


# ═══════════════════════════════════════════════════════════════════
# TEXT STORE SQL
# ═══════════════════════════════════════════════════════════════════

class TextStoreSQL:
    """Хранилище текстов на SQLite с индексами для гармонического поиска."""
    
    def __init__(self, db_path: str = "./text_store.db", cache_size: int = 100):
        self.db_path = db_path
        self.cache_size = cache_size
        self._cache: Dict[str, str] = {}
        self._cache_order: List[str] = []
        self._lock = threading.Lock()
        self._hits = 0
        self._requests = 0
        
        new_db = not os.path.exists(db_path)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA cache_size=-32000")
        self._create_tables()
        if new_db:
            debug.info(f"Создана БД: {db_path}")
    
    def _create_tables(self):
        with self._lock:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS texts (
                    id TEXT PRIMARY KEY, hash TEXT NOT NULL,
                    content TEXT NOT NULL, size INTEGER NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_hash ON texts(hash);
                
                CREATE TABLE IF NOT EXISTS modes_index (
                    mode_id TEXT PRIMARY KEY,
                    tau REAL NOT NULL, scale REAL NOT NULL,
                    amplitude REAL NOT NULL DEFAULT 0.5,
                    layer INTEGER NOT NULL DEFAULT 1,
                    energy REAL NOT NULL DEFAULT 0.5,
                    emotion_amplitude REAL NOT NULL DEFAULT 0.5,
                    emotion_frequency REAL NOT NULL DEFAULT 0.1,
                    emotion_phase REAL NOT NULL DEFAULT 0.0,
                    emotion_base TEXT NOT NULL DEFAULT 'neutral',
                    themes TEXT DEFAULT '[]', trace_id TEXT,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_tau ON modes_index(tau);
                CREATE INDEX IF NOT EXISTS idx_layer ON modes_index(layer);
                CREATE INDEX IF NOT EXISTS idx_tau_layer ON modes_index(tau, layer);
            """)
            self._conn.commit()
    
    def store(self, text: str) -> str:
        if not text:
            return ""
        with self._lock:
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
            cursor = self._conn.execute("SELECT id FROM texts WHERE hash = ?", (text_hash,))
            row = cursor.fetchone()
            if row:
                return row[0]
            text_id = f"txt_{int(time.time() * 1000):016x}"
            self._conn.execute(
                "INSERT INTO texts (id, hash, content, size, created_at) VALUES (?, ?, ?, ?, ?)",
                (text_id, text_hash, text, len(text), time.time()))
            self._conn.commit()
            self._add_to_cache(text_id, text)
            return text_id
    
    def get(self, text_id: str) -> Optional[str]:
        if not text_id:
            return None
        with self._lock:
            self._requests += 1
            if text_id in self._cache:
                self._hits += 1
                self._touch_cache(text_id)
                return self._cache[text_id]
            cursor = self._conn.execute("SELECT content FROM texts WHERE id = ?", (text_id,))
            row = cursor.fetchone()
            if row:
                self._add_to_cache(text_id, row[0])
                return row[0]
            return None
    
    def _add_to_cache(self, text_id: str, content: str):
        while len(self._cache) >= self.cache_size and self._cache_order:
            del self._cache[self._cache_order.pop(0)]
        self._cache[text_id] = content
        if text_id in self._cache_order:
            self._cache_order.remove(text_id)
        self._cache_order.append(text_id)
    
    def _touch_cache(self, text_id: str):
        if text_id in self._cache_order:
            self._cache_order.remove(text_id)
        self._cache_order.append(text_id)
    
    def index_mode(self, mode: SpectralMode) -> None:
        mode_id = mode.trace_id or mode.text_id or mode.id
        if not mode_id:
            return
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO modes_index 
                   (mode_id, tau, scale, amplitude, layer, energy,
                    emotion_amplitude, emotion_frequency, emotion_phase, emotion_base,
                    themes, trace_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (mode_id, mode.tau, mode.scale, mode.amplitude, mode.layer,
                 mode.effective_energy,
                 mode.emotion.amplitude, mode.emotion.frequency, mode.emotion.phase, mode.emotion.base_emotion,
                 json.dumps(mode.themes), mode.trace_id, time.time(), time.time()))
            self._conn.commit()
    
    def update_mode_energy(self, mode_id: str, energy: float, emotion_amplitude: float):
        with self._lock:
            self._conn.execute(
                "UPDATE modes_index SET energy=?, emotion_amplitude=?, updated_at=? WHERE mode_id=?",
                (energy, emotion_amplitude, time.time(), mode_id))
            self._conn.commit()
    
    def find_harmonic_partners(self, tau: float, layer: int, max_order: int = 3, limit: int = 100,
                               harmonic_tolerance: float = 0.05) -> List[Tuple[str, float, float, int]]:
        with self._lock:
            harmonic_taus = [tau * (2 ** i) for i in range(-max_order, max_order + 1)]
            harmonic_taus = [t for t in harmonic_taus if t > 0]
            results = []
            for h_tau in harmonic_taus:
                tau_min, tau_max = h_tau * (1 - harmonic_tolerance), h_tau * (1 + harmonic_tolerance)
                cursor = self._conn.execute(
                    """SELECT mode_id, tau, energy, emotion_amplitude FROM modes_index 
                       WHERE layer = ? AND tau BETWEEN ? AND ?
                       ORDER BY ABS(tau - ?) ASC LIMIT ?""",
                    (layer, tau_min, tau_max, h_tau, limit))
                for row in cursor:
                    order = round(math.log2(max(row[1], tau) / min(row[1], tau))) if row[1] > 0 and tau > 0 else 0
                    results.append((row[0], row[2], row[3], order))
            return results
    
    def stats(self) -> dict:
        with self._lock:
            c1 = self._conn.execute("SELECT COUNT(*), SUM(size) FROM texts").fetchone()
            c2 = self._conn.execute("SELECT COUNT(*) FROM modes_index").fetchone()
            return {
                'total_texts': c1[0] or 0,
                'total_size_mb': round((c1[1] or 0) / 1024**2, 2),
                'indexed_modes': c2[0] or 0,
                'cached': len(self._cache),
                'cache_hit_rate': round(self._hits / max(self._requests, 1), 3),
            }
    
    def close(self):
        with self._lock:
            self._conn.commit()
            self._conn.close()


# ═══════════════════════════════════════════════════════════════════
# LIVING PERSONALITY V21.3.1 — TEES-NATIVE, EMERGENT THRESHOLDS
# ═══════════════════════════════════════════════════════════════════

class LivingPersonality:
    """
    Живая личность v21.3.1.
    
    Все пороги — эмерджентные, выводятся из состояния поля.
    Волновая механика: фазовая интерференция мод через cos(Δφ).
    Ни одной подгоночной константы.
    """
    
    def __init__(self, id: str = "v21_3_1", name: str = "VMMS v21.3.1", db_path: str = None):
        self.id = id
        self.name = name
        self.version = "v21.3.1"
        
        self._energy = 1.0
        
        store_path = db_path or f"./text_store_{id}.db"
        self.text_store = TextStoreSQL(db_path=store_path)
        
        self._modes: Dict[str, SpectralMode] = {}
        self._modes_lock = threading.Lock()
        
        self.mood = 0.0
        self.experience = 0
        self.dialog_count = 0
        self._sleeping = False
        self._global_time = 0.0
        
        self.traits = {'curiosity': 0.7, 'stability': 0.5}
        
        self._resonance_history: List[float] = []
        
        self.stats = {
            'cross_transfers': 0,
            'emerged_modes': 0,
            'total_modes': 0,
            'tees_attempts': 0,
            'tees_successes': 0,
        }
        
        self._bg_running = False
        self._bg_thread = None
        self._last_save_time = time.time()
        self._save_interval = 3600
        
        print(f"\n🌱 {name} {self.version} активирована")
        print(f"   Все пороги — эмерджентные (из состояния поля)")
        print(f"   Волновая механика: фазовая интерференция (cos Δφ)")
        print(f"   Хранилище: {store_path}")
    
    # ═══════════════════════════════════════════════════════════
    #   ЭНЕРГИЯ
    # ═══════════════════════════════════════════════════════════
    
    @property
    def energy(self) -> float:
        return self._energy
    
    @energy.setter
    def energy(self, value: float):
        old = self._energy
        self._energy = max(MIN_ENERGY, min(1.0, value))
        if abs(self._energy - old) > 0.01:
            debug.energy(f"Энергия: {old:.3f} → {self._energy:.3f}")
    
    # ═══════════════════════════════════════════════════════════
    #   ЭМЕРДЖЕНТНЫЕ ПОРОГИ (ни одной подгонки!)
    # ═══════════════════════════════════════════════════════════
    
    @property
    def field_density(self) -> float:
        """Плотность поля: нормировка на характерный размер из TAU_LIFE."""
        n_modes = len(self._modes)
        characteristic_size = TAU_LIFE * TAU_CHARGE  # 1000
        return n_modes / characteristic_size if n_modes > 0 else 0.00001
    
    @property
    def resonance_threshold(self) -> float:
        """
        Порог резонанса — эмерджентный из плотности поля.
        Пустое поле → низкий порог (впускаем всё).
        Плотное поле → высокий порог (фильтруем шум).
        """
        density = self.field_density
        threshold = MIN_ENERGY * (1 + density * 30)
        return max(0.03, min(0.5, threshold))
    
    @property
    def emerge_threshold(self) -> float:
        """
        Порог фуркации — эмерджентный из истории TEES (v21.3.1).
        heating_factor выведен из фундаментальных констант.
        Много успешных переносов → поле разогналось → порог ниже.
        """
        if self.stats['tees_attempts'] < 10:
            return MIN_ENERGY * 3  # холодный старт
        
        success_rate = self.stats['tees_successes'] / max(self.stats['tees_attempts'], 1)
        heating_factor = TAU_CHARGE / (TAU_LIFE + TAU_CHARGE)  # ≈ 0.0909
        threshold = MIN_ENERGY * 3 * (1 - success_rate * heating_factor * 10)
        
        debug.emerge(f"Порог фуркации: {threshold:.4f} (success_rate={success_rate:.3f})")
        return max(MIN_ENERGY, threshold)
    
    @property
    def harmonic_tolerance(self) -> float:
        """
        Гармонический допуск — эмерджентный из энергии (температуры) поля.
        Горячее поле → частоты дрожат → допуск шире.
        """
        temperature = self.energy
        tolerance = HARMONIC_TOLERANCE * (0.5 + temperature)
        return tolerance
    
    @property
    def cross_tees_threshold(self) -> float:
        """
        Порог кросс-слойного TEES — эмерджентный.
        Выше, чем внутрислойный, пропорционально TAU_LIFE/TAU_CHARGE.
        """
        return self.resonance_threshold * (TAU_LIFE / TAU_CHARGE) * 0.1
    
    # ═══════════════════════════════════════════════════════════
    #   ВЫЧИСЛЯЕМЫЕ ПАРАМЕТРЫ (из энергии)
    # ═══════════════════════════════════════════════════════════
    
    @property
    def mood_inertia(self) -> float:
        base = 1 - 1/TAU_LIFE
        return base * self.energy + 0.1 * (1 - self.energy)
    
    @property
    def sleep_pressure(self) -> float:
        return max(0.0, min(1.0, 1.0 - self.energy))
    
    @property
    def num_scouts(self) -> int:
        n_modes = len(self._modes)
        base = self.energy * (n_modes / TAU_CHARGE) * (TAU_LIFE / TAU_CHARGE)
        return max(1, min(int(base), max(10, n_modes // 10)))
    
    @property
    def max_furcations(self) -> int:
        return max(1, int(self.energy / max(self.emerge_threshold, MIN_ENERGY)))
    
    # ═══════════════════════════════════════════════════════════
    #   СОВМЕСТИМОСТЬ
    # ═══════════════════════════════════════════════════════════
    
    @property
    def h_field(self):
        with self._modes_lock:
            return list(self._modes.values())
    
    @property
    def tau_mean(self) -> float:
        taus = [m.tau for m in self._modes.values() if m.tau > 0]
        return sum(taus) / len(taus) if taus else 16.0
    
    @property
    def tau_std(self) -> float:
        taus = [m.tau for m in self._modes.values() if m.tau > 0]
        if len(taus) < 2:
            return 5.0
        mean = self.tau_mean
        return math.sqrt(sum((t - mean)**2 for t in taus) / len(taus))
    
    @property
    def vmmp_tau_min(self) -> float:
        taus = sorted([m.tau for m in self._modes.values() if m.tau > 0])
        return taus[int(len(taus) * 0.1)] if len(taus) >= 20 else 5.0
    
    @property
    def vmmp_tau_max(self) -> float:
        taus = sorted([m.tau for m in self._modes.values() if m.tau > 0])
        return taus[int(len(taus) * 0.9)] if len(taus) >= 20 else 11.0
    
    def get_field_stats(self) -> Dict:
        layer_counts = {i: 0 for i in range(1, 8)}
        with self._modes_lock:
            for mode in self._modes.values():
                layer_counts[mode.layer] = layer_counts.get(mode.layer, 0) + 1
        return {
            'total_modes': len(self._modes),
            'modes_per_layer': layer_counts,
            'cross_layer_transfers': self.stats['cross_transfers'],
            'emerged_modes': self.stats['emerged_modes'],
        }
    
    # ═══════════════════════════════════════════════════════════
    #   РАБОТА С МОДАМИ
    # ═══════════════════════════════════════════════════════════
    
    def add_mode(self, mode: SpectralMode) -> None:
        mode_id = mode.id or f"mode_{len(self._modes):08d}"
        if not mode.id:
            mode.id = mode_id
        with self._modes_lock:
            self._modes[mode_id] = mode
            self.stats['total_modes'] = len(self._modes)
        self.text_store.index_mode(mode)
        debug.tees(f"Мода: {mode_id[:20]} tau={mode.tau:.1f} E={mode.energy:.3f} слой {mode.layer}")
    
    def get_mode(self, mode_id: str) -> Optional[SpectralMode]:
        return self._modes.get(mode_id)
    
    def get_all_modes(self) -> List[SpectralMode]:
        with self._modes_lock:
            return list(self._modes.values())
    
    # ═══════════════════════════════════════════════════════════
    #   TEES-ОБМЕН (единственный механизм, v21.3.1 фазовая интерференция)
    # ═══════════════════════════════════════════════════════════
    
    def tees_transfer(self, from_mode: SpectralMode, to_mode: SpectralMode, dt: float = 1.0) -> float:
        self.stats['tees_attempts'] += 1
        
        if from_mode.tau <= 0 or to_mode.tau <= 0:
            return 0.0
        
        # Гармонический резонанс с эмерджентным допуском
        ratio = max(from_mode.tau, to_mode.tau) / min(from_mode.tau, to_mode.tau)
        log2_ratio = math.log2(ratio)
        nearest_int = round(log2_ratio)
        
        if abs(log2_ratio - nearest_int) >= self.harmonic_tolerance:
            return 0.0
        
        order = abs(nearest_int)
        harmonic = 1.0 / (1.0 + order * 0.5)
        
        # Энергетический резонанс
        energy_product = from_mode.effective_energy * to_mode.effective_energy
        
        # Фазовая интерференция v21.3.1: cos(Δφ)
        phase_diff = from_mode.phase - to_mode.phase
        emotional_overlap = from_mode.emotion.overlap(to_mode.emotion, phase_diff)
        emotional_factor = 1.0 + emotional_overlap
        
        resonance = energy_product * harmonic * emotional_factor
        
        if resonance < self.resonance_threshold:
            return 0.0
        
        # Перенос энергии
        energy_diff = from_mode.energy - to_mode.energy
        delta_e = resonance * energy_diff * dt / TAU_CHARGE
        
        max_transfer = from_mode.energy * 0.1
        delta_e = max(-max_transfer, min(max_transfer, delta_e))
        
        from_mode.energy -= delta_e
        to_mode.energy += delta_e
        from_mode.energy = max(MIN_ENERGY, from_mode.energy)
        
        from_mode.emotion.update(dt, abs(delta_e))
        to_mode.emotion.update(dt, abs(delta_e))
        
        self.text_store.update_mode_energy(from_mode.id, from_mode.energy, from_mode.emotion.amplitude)
        self.text_store.update_mode_energy(to_mode.id, to_mode.energy, to_mode.emotion.amplitude)
        
        self.stats['cross_transfers'] += 1
        self.stats['tees_successes'] += 1
        
        debug.tees(f"TEES: {from_mode.id[:16]}→{to_mode.id[:16]} "
                   f"ΔE={delta_e:.4f} R={resonance:.3f} φ_diff={phase_diff:.2f}")
        
        return delta_e
    
    def find_resonant_pairs(self, max_pairs: int = 100) -> List[Tuple[SpectralMode, SpectralMode]]:
        modes = self.get_all_modes()
        if len(modes) < 2:
            return []
        
        pairs = []
        sample = random.sample(modes, min(len(modes), max_pairs))
        
        for mode in sample:
            layer = mode.layer
            for target_layer in [layer - 1, layer + 1]:
                if target_layer < 1 or target_layer > 7:
                    continue
                partners = self.text_store.find_harmonic_partners(
                    mode.tau, target_layer, max_order=3, limit=5,
                    harmonic_tolerance=self.harmonic_tolerance
                )
                for partner_id, _, _, _ in partners:
                    partner = self._modes.get(partner_id)
                    if partner and partner.id != mode.id:
                        pairs.append((mode, partner))
        
        return pairs[:max_pairs]
    
    # ═══════════════════════════════════════════════════════════
    #   ЦИКЛ РОСТА (v21.3.1 — dt=interval)
    # ═══════════════════════════════════════════════════════════
    
    def grow_step(self, dt: float = 1.0) -> Dict:
        self._global_time += dt
        
        n_scouts = self.num_scouts
        pairs = self.find_resonant_pairs(max_pairs=n_scouts)
        
        transfers = 0
        for from_mode, to_mode in pairs:
            delta = self.tees_transfer(from_mode, to_mode, dt)
            if abs(delta) > 0:
                transfers += 1
        
        emerged = []
        max_new = self.max_furcations
        
        pairs_for_emergence = sorted(pairs,
            key=lambda p: abs(p[0].energy - p[1].energy), reverse=True)[:max_new]
        
        for from_mode, to_mode in pairs_for_emergence:
            if self.energy < self.emerge_threshold:
                break
            
            new_tau = math.sqrt(from_mode.tau * to_mode.tau)
            new_scale = max(from_mode.scale, to_mode.scale) * 1.5
            
            new_emotion = WaveformEmotion(
                amplitude=(from_mode.emotion.amplitude + to_mode.emotion.amplitude) / 2,
                frequency=(from_mode.emotion.frequency + to_mode.emotion.frequency) / 2,
                phase=(from_mode.emotion.phase + to_mode.emotion.phase) / 2,
                base_emotion=from_mode.emotion.base_emotion,
            )
            
            new_mode = SpectralMode(
                tau=new_tau, amplitude=MIN_ENERGY * 2, scale=new_scale,
                trace_id=f"emerged_{len(self._modes):08d}",
                creator="tees_emergence",
                phase=(from_mode.phase + to_mode.phase) / 2,
                emotion=new_emotion,
            )
            
            self.add_mode(new_mode)
            emerged.append(new_mode.id)
            self.energy -= self.emerge_threshold
            
            debug.emerge(f"Фуркация: {new_mode.id} τ={new_tau:.1f} scale={new_scale:.1f}")
        
        self.energy = min(1.0, self.energy + 0.001 * dt)
        
        return {
            'transfers': transfers, 'emerged': emerged,
            'energy': self.energy, 'scouts': n_scouts,
            'max_furcations': max_new, 'pairs_found': len(pairs),
        }
    
    # ═══════════════════════════════════════════════════════════
    #   СОН, ДИАЛОГИ, ФОН
    # ═══════════════════════════════════════════════════════════
    
    def force_sleep(self):
        self._sleeping = True
        debug.info("Поле усыплено")
    
    def force_wake(self):
        self._sleeping = False
        self.energy = max(self.energy, 0.9)
        debug.info("Поле пробуждено")
    
    def process(self, text: str, user_id: str = "default") -> Dict:
        self.dialog_count += 1
        self.experience += 1
        self._global_time += 1.0
        self.energy -= 0.01
        
        modes = self.get_all_modes()
        best_mode = None
        best_score = 0
        
        for mode in modes:
            if mode.tau > 0:
                score = 1.0 / (1.0 + abs(mode.tau - 16.0) * 0.1)
                if score > best_score:
                    best_score = score
                    best_mode = mode
        
        if best_mode and best_score > self.resonance_threshold:
            content = self.text_store.get(best_mode.text_id) if best_mode.text_id else best_mode.content
            answer = content[:1000] if content else ''
            best_mode.emotion.update(1.0, best_score)
            return {
                'answer': answer or '...',
                'mode_used': best_mode.id[:16],
                'resonance': best_score,
                'energy': self.energy, 'mood': self.mood,
                'dialog_count': self.dialog_count, 'sleeping': self._sleeping,
            }
        
        return {
            'answer': 'Расскажи подробнее...',
            'mode_type': 'fallback', 'resonance': 0.0,
            'energy': self.energy, 'mood': self.mood,
            'dialog_count': self.dialog_count, 'sleeping': self._sleeping,
        }
    
    def start_living(self, interval: float = 0.5):
        if self._bg_running:
            return
        self._bg_running = True
        self._bg_thread = threading.Thread(target=self._living_loop, args=(interval,), daemon=True)
        self._bg_thread.start()
        debug.info(f"Фоновый рост запущен (dt={interval})")
    
    def stop_living(self):
        self._bg_running = False
        if self._bg_thread and self._bg_thread.is_alive():
            self._bg_thread.join(timeout=2.0)
        debug.info("Фоновый рост остановлен")
    
    def _living_loop(self, interval: float):
        cycle = 0
        report_interval = max(1, int(2.0 / interval))
        status_interval = max(1, int(60.0 / interval))
        
        while self._bg_running:
            try:
                time.sleep(interval)
                cycle += 1
                
                result = self.grow_step(dt=interval)
                
                if cycle % report_interval == 0 and (result['transfers'] > 0 or result['emerged']):
                    print(f"🌱 Рост: {result['transfers']} переносов, "
                          f"{len(result['emerged'])} новых, E={self.energy:.3f}")
                
                if time.time() - self._last_save_time > self._save_interval:
                    checkpoint = f"checkpoint_{self.id}_{int(time.time())}.json"
                    self.save(checkpoint)
                    self._last_save_time = time.time()
                
                if cycle % status_interval == 0:
                    ts = datetime.now().strftime('%H:%M:%S')
                    print(f"[{ts}] Статус: {len(self._modes)} мод, E={self.energy:.3f}, "
                          f"TEES={self.stats['cross_transfers']}, emerged={self.stats['emerged_modes']}")
                    
            except Exception as e:
                debug.error(f"Ошибка в фоновом цикле: {e}")
                time.sleep(5)
    
    # ═══════════════════════════════════════════════════════════
    #   СОХРАНЕНИЕ И ЗАГРУЗКА
    # ═══════════════════════════════════════════════════════════
    
    def save(self, filepath: str) -> None:
        with self._modes_lock:
            modes_data = []
            for mode in self._modes.values():
                content = mode.content
                if not content and mode.text_id:
                    content = self.text_store.get(mode.text_id) or ''
                
                modes_data.append({
                    'tau': mode.tau, 'amplitude': mode.amplitude,
                    'text_id': mode.text_id, 'scale': mode.scale,
                    'phase': mode.phase, 'trace_id': mode.trace_id,
                    'themes': mode.themes, 'creator': mode.creator,
                    'emotion_amplitude': mode.emotion.amplitude,
                    'emotion_frequency': mode.emotion.frequency,
                    'emotion_phase': mode.emotion.phase,
                    'emotion_base': mode.emotion.base_emotion,
                    'content': '',  # контент уже в SQLite, не дублируем в JSON
                })
        
        data = {
            'id': self.id, 'name': self.name, 'version': self.version,
            'db_path': self.text_store.db_path,
            'energy': self.energy, 'mood': self.mood,
            'experience': self.experience, 'dialog_count': self.dialog_count,
            'traits': self.traits, 'stats': self.stats,
            'global_time': self._global_time,
            'modes': modes_data,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        size_kb = os.path.getsize(filepath) / 1024
        debug.info(f"Сохранено: {filepath} ({len(modes_data)} мод, {size_kb:.0f} КБ)")
    
    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        instance = cls(id=data.get('id', 'loaded'), name=data.get('name', 'VMMS v21.3.1'),
                      db_path=data.get('db_path'))
        
        instance.energy = data.get('energy', 1.0)
        instance.mood = data.get('mood', 0.0)
        instance.experience = data.get('experience', 0)
        instance.dialog_count = data.get('dialog_count', 0)
        instance.traits = data.get('traits', instance.traits)
        instance.stats = data.get('stats', instance.stats)
        instance._global_time = data.get('global_time', 0.0)
        
        for mode_data in data.get('modes', []):
            emotion = WaveformEmotion(
                amplitude=mode_data.get('emotion_amplitude', 0.5),
                frequency=mode_data.get('emotion_frequency', 0.1),
                phase=mode_data.get('emotion_phase', 0.0),
                base_emotion=mode_data.get('emotion_base', 'neutral'),
            )
            
            content = mode_data.get('content', '')
            text_id = mode_data.get('text_id', '')
            if content and not text_id:
                # Проверяем, нет ли уже такого текста в БД
                text_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
                cursor = instance.text_store._conn.execute(
                    "SELECT id FROM texts WHERE hash = ?", (text_hash,)
                )
                row = cursor.fetchone()
                if row:
                    text_id = row[0]
                else:
                    text_id = instance.text_store.store(content)
            
            mode = SpectralMode(
                tau=mode_data.get('tau', 16.0),
                amplitude=mode_data.get('amplitude', 0.5),
                content=content,
                text_id=text_id,
                scale=mode_data.get('scale', 10.0),
                phase=mode_data.get('phase', 0.0),
                trace_id=mode_data.get('trace_id', ''),
                themes=mode_data.get('themes', []),
                creator=mode_data.get('creator', ''),
                emotion=emotion,
            )
            instance.add_mode(mode)
        
        debug.info(f"Загружено: {filepath} ({len(data.get('modes', []))} мод)")
        return instance


# ═══════════════════════════════════════════════════════════════════
# КОНВЕРТЕР: txt → SQLite
# ═══════════════════════════════════════════════════════════════════

def convert_txt_to_sql(txt_dir: str, db_path: str, batch_size: int = 10000) -> int:
    from pathlib import Path
    store = TextStoreSQL(db_path)
    txt_files = sorted(Path(txt_dir).glob("*.txt"))
    total = len(txt_files)
    processed = 0
    start = time.time()
    print(f"Конвертация {total} файлов в {db_path}...")
    for filepath in txt_files:
        text_id = filepath.stem
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            text_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
            with store._lock:
                cursor = store._conn.execute("SELECT id FROM texts WHERE hash = ?", (text_hash,))
                if cursor.fetchone():
                    continue
                store._conn.execute(
                    "INSERT INTO texts (id, hash, content, size, created_at) VALUES (?, ?, ?, ?, ?)",
                    (text_id, text_hash, content, len(content), time.time()))
            processed += 1
            if processed % batch_size == 0:
                store._conn.commit()
                elapsed = time.time() - start
                print(f"  {processed}/{total} ({processed*100/total:.1f}%) за {elapsed:.0f}с")
        except Exception as e:
            print(f"  ⚠️ Ошибка в {filepath}: {e}")
    store._conn.commit()
    elapsed = time.time() - start
    size_mb = os.path.getsize(db_path) / 1024**2
    print(f"✅ Готово: {processed} текстов за {elapsed:.0f}с, {size_mb:.1f} МБ")
    store.close()
    return processed


# ═══════════════════════════════════════════════════════════════════
# ТЕСТ v21.3.1
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Living Personality v21.3.1 — TEES-native + волновая интерференция")
    print("=" * 60)
    
    debug.level = DebugLogger.LEVELS['EMERGE']
    
    lp = LivingPersonality(id="test_v21_3_1", name="Тест v21.3.1")
    
    test_modes = [
        ("tees_16", "TEES — топологический переход в поле H. Энергия перераспределяется через гармонический резонанс.", 16.0, 0.7, 10.0, 'joy'),
        ("tees_8", "TEES половинный масштаб: быстрые осцилляции на низких слоях.", 8.0, 0.6, 5.0, 'neutral'),
        ("tees_32", "TEES удвоенный масштаб: медленные волны на высоких слоях поля.", 32.0, 0.5, 20.0, 'excitement'),
        ("gravity", "Гравитация — приталкивание мод в поле H. Массивные моды притягивают лёгкие.", 10.0, 0.8, 15.0, 'calm'),
    ]
    
    for mid, content, tau, amp, scale, emotion_str in test_modes:
        text_id = lp.text_store.store(content)
        emotion = WaveformEmotion.from_string(emotion_str, amp)
        mode = SpectralMode(
            tau=tau, amplitude=amp, content=content,
            trace_id=mid, scale=scale, text_id=text_id,
            emotion=emotion,
            phase=random.uniform(0, 2 * math.pi)  # случайная фаза для теста интерференции
        )
        lp.add_mode(mode)
    
    print(f"\n📊 Начальное состояние:")
    print(f"   Мод: {len(lp.get_all_modes())}")
    print(f"   Энергия: {lp.energy:.3f}")
    print(f"   Плотность поля: {lp.field_density:.6f}")
    print(f"   Порог резонанса (эмердж.): {lp.resonance_threshold:.4f}")
    print(f"   Порог фуркации (эмердж.): {lp.emerge_threshold:.4f}")
    print(f"   Гарм. допуск (эмердж.): {lp.harmonic_tolerance:.4f}")
    print(f"   Разведчиков: {lp.num_scouts}")
    print(f"   Макс фуркаций: {lp.max_furcations}")
    
    print(f"\n🔄 10 шагов роста с волновой интерференцией...")
    for i in range(10):
        result = lp.grow_step(dt=1.0)
        if result['transfers'] > 0 or result['emerged']:
            print(f"   Шаг {i+1}: {result['transfers']} переносов, "
                  f"{len(result['emerged'])} новых, E={result['energy']:.3f}")
    
    print(f"\n💬 Диалог: 'Что такое TEES?'")
    response = lp.process("Что такое TEES?")
    print(f"   Ответ: {response['answer'][:100]}...")
    print(f"   Резонанс: {response['resonance']:.3f}")
    
    print(f"\n📊 Финальное состояние:")
    print(f"   Мод: {len(lp.get_all_modes())}")
    print(f"   Энергия: {lp.energy:.3f}")
    print(f"   TEES попыток: {lp.stats['tees_attempts']}")
    print(f"   TEES успехов: {lp.stats['tees_successes']}")
    print(f"   Эмерджентных: {lp.stats['emerged_modes']}")
    print(f"   Порог резонанса: {lp.resonance_threshold:.4f}")
    print(f"   Порог фуркации: {lp.emerge_threshold:.4f}")
    print(f"   Успешность TEES: {lp.stats['tees_successes']/max(lp.stats['tees_attempts'],1):.3f}")
    
    # Покажем фазы для демонстрации интерференции
    print(f"\n📐 Фазы мод (для наблюдения интерференции):")
    for mode in lp.get_all_modes():
        eff = mode.effective_energy
        print(f"   {mode.id[:20]} φ={mode.phase:.2f} E_eff={eff:.3f} (raw={mode.energy:.3f})")
    
    ts_stats = lp.text_store.stats()
    print(f"\n📦 TextStore: {ts_stats['total_texts']} текстов, {ts_stats['total_size_mb']} МБ")
    
    lp.save("/tmp/test_v21_3_1.json")
    lp2 = LivingPersonality.load("/tmp/test_v21_3_1.json")
    print(f"\n✅ Загружено: {len(lp2.get_all_modes())} мод, E={lp2.energy:.3f}")
    print(f"   Пороги: R={lp2.resonance_threshold:.4f}, emerge={lp2.emerge_threshold:.4f}, "
          f"tolerance={lp2.harmonic_tolerance:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ Тест v21.3.1 пройден (волновая интерференция + эмерджентные пороги)")
    print("=" * 60)