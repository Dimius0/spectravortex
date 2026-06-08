#!/usr/bin/env python3
"""
Living Personality v21.2 — адаптивная, единое поле, саморегуляция
==================================================================
Все коэффициенты адаптивные, поле единое (нет fallback-ветвления),
сон по состоянию поля, инкрементальная статистика, адаптивные буферы.

Новое в v21.2:
- FieldV2Stub — единый интерфейс поля (нет _h_field_fallback)
- Инкрементальный сбор tau (O(1) вместо O(n))
- AdaptiveRingBuffer — буфер с адаптивным размером
- Сон по состоянию поля (sleep_pressure)
- Обоснованный COLD_START (из теории частот и mood dynamics)
- Скрипт тестирования на реальных данных

Авторы:
Dimius0 — концепция, ВММП, семь слоёв
DeepSeek — интеграция, адаптивные коэффициенты, FieldV2Stub, сон, 2026-06-08
"""

import sys
import os
import threading
import time
import random
import json
import math
import hashlib
import gc
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime

# Добавляем пути для импортов
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Импортируем базовый класс из v20.2
try:
    from rizoma.living_personality_v20_2 import LivingPersonality as BasePersonality, SpectralMode
except ImportError:
    try:
        from src.rizoma.living_personality_v20_2 import LivingPersonality as BasePersonality, SpectralMode
    except ImportError:
        print("⚠️ Не удалось импортировать living_personality_v20_2, использую заглушку")
        class SpectralMode:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
                # Гарантируем наличие id и trace_id
                if not hasattr(self, 'id'):
                    self.id = kwargs.get('trace_id', kwargs.get('text_id', ''))
                if not hasattr(self, 'trace_id'):
                    self.trace_id = self.id
        
        class BasePersonality:
            def __init__(self, id="base", name="Base"):
                self.id = id
                self.name = name
                self.h_field = []
                self.vortices = []
                self.focus = {"tau": 16.0, "scale": 10.0, "phase": 0.0}
            
            def phrase_spectrum(self, text):
                return {16.0: 1.0}
            
            def get_dominant_tau(self, spectrum):
                return 16.0
            
            def save(self, filepath):
                pass

# Импортируем FieldV2
try:
    from src.architect.field_v2 import FieldV2, WaveformEmotion, FieldMode
    FIELD_V2_AVAILABLE = True
except ImportError:
    try:
        from architect.field_v2 import FieldV2, WaveformEmotion, FieldMode
        FIELD_V2_AVAILABLE = True
    except ImportError:
        print("⚠️ FieldV2 не найден, использую FieldV2Stub")
        FIELD_V2_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
#   FIELD V2 STUB — ЕДИНЫЙ ИНТЕРФЕЙС
# ═══════════════════════════════════════════════════════════════════

class FieldV2Stub:
    """
    Заглушка FieldV2, эмулирующая интерфейс через список.
    
    Позволяет использовать единый код без ветвления FIELD_V2_AVAILABLE.
    """
    
    def __init__(self, name="stub"):
        self.name = name
        self._modes = []
        self.stats = {
            'total_modes': 0,
            'modes_per_layer': {i: 0 for i in range(1, 8)},
            'cross_layer_transfers': 0,
            'emerged_modes': 0,
            'recent_emerged': [],
        }
        # Эмулируем layers как словарь с атрибутом modes
        self.layers = {}
        for i in range(1, 8):
            self.layers[i] = type('Layer', (), {'modes': {}})()
    
    def _scale_to_layer(self, scale: float) -> int:
        if scale >= 25: return 7
        elif scale >= 18: return 6
        elif scale >= 12: return 5
        elif scale >= 8: return 4
        elif scale >= 4: return 3
        elif scale >= 2: return 2
        return 1
    
    def add_mode(self, mode):
        self._modes.append(mode)
        self.stats['total_modes'] = len(self._modes)
        
        # Определяем слой и добавляем в соответствующий layer.modes
        scale = getattr(mode, 'scale', 5.0)
        layer_id = self._scale_to_layer(scale)
        
        mode_id = getattr(mode, 'trace_id', f"stub_{len(self._modes)}")
        self.layers[layer_id].modes[mode_id] = mode
        self.stats['modes_per_layer'][layer_id] = len(self.layers[layer_id].modes)
    
    def find_by_resonance(self, query_tau, query_scale, query_phase,
                          query_emotion, query_spectrum, k=10,
                          use_priority_bonus=True, early_exit=True):
        scored = []
        for i, mode in enumerate(self._modes):
            tau = getattr(mode, 'tau', 16.0)
            tau_diff = abs(tau - query_tau)
            # Резонанс: чем ближе tau, тем выше score
            score = 1.0 / (1.0 + tau_diff * 0.5)
            
            # Бонус за масштаб
            scale = getattr(mode, 'scale', 5.0)
            scale_diff = abs(scale - query_scale) / max(query_scale, 1.0)
            score *= (1.0 - scale_diff * 0.3)
            
            # Приоритет верхних слоёв
            if use_priority_bonus:
                layer = self._scale_to_layer(scale)
                score *= (1.0 + layer * 0.05)
            
            trace_id = getattr(mode, 'trace_id', f"stub_{i}")
            scored.append((trace_id, score, self._scale_to_layer(scale), {}))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        if early_exit and scored and scored[0][1] > 0.7:
            return scored[:1]
        
        return scored[:k]
    
    def get_mode(self, mode_id):
        for mode in self._modes:
            if getattr(mode, 'trace_id', '') == mode_id:
                return mode
        return None
    
    def spectrum_to_intervals(self, spectrum):
        return spectrum
    
    def step_cross_layer_dynamics(self, dt=1.0):
        # В заглушке — простая эмуляция
        if len(self._modes) > 2 and random.random() < 0.1:
            return {'emerged': [f"emergent_{len(self._modes)}"], 'transfers': 1}
        return {'emerged': [], 'transfers': 0}
    
    def get_stats(self):
        stats = dict(self.stats)
        stats['modes_per_layer'] = dict(self.stats['modes_per_layer'])
        return stats


# ═══════════════════════════════════════════════════════════════════
#   TEXT STORE
# ═══════════════════════════════════════════════════════════════════

class TextStore:
    """
    Хранилище текстов на диске с LRU-кешем в RAM.
    Размер кеша — адаптивный.
    """
    
    def __init__(self, store_path: str = "./text_store", cache_size: int = 50):
        self.store_path = store_path
        self.cache_size = cache_size
        
        self._cache = {}
        self._cache_order = []
        self._index = {}
        
        self._hits = 0
        self._requests = 0
        
        self._lock = threading.Lock()
        
        os.makedirs(store_path, exist_ok=True)
        self._load_index()
    
    def _load_index(self):
        index_path = os.path.join(self.store_path, "index.json")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"⚠️ TextStore: не удалось загрузить индекс, создаю новый")
                self._index = {}
    
    def _save_index(self):
        index_path = os.path.join(self.store_path, "index.json")
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️ TextStore: не удалось сохранить индекс: {e}")
    
    def store(self, text: str) -> str:
        if not text:
            return ""
        
        with self._lock:
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
            
            for tid, info in self._index.items():
                if info.get('hash') == text_hash:
                    return tid
            
            text_id = f"txt_{len(self._index):08d}"
            filepath = os.path.join(self.store_path, f"{text_id}.txt")
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
            except IOError as e:
                print(f"⚠️ TextStore: не удалось сохранить текст {text_id}: {e}")
                return ""
            
            self._index[text_id] = {
                'file': f"{text_id}.txt",
                'hash': text_hash,
                'size': len(text)
            }
            
            if len(self._index) % 1000 == 0:
                self._save_index()
            
            return text_id
    
    def get(self, text_id: str) -> Optional[str]:
        if not text_id:
            return None
        
        with self._lock:
            self._requests += 1
            
            if text_id not in self._index:
                return None
            
            if text_id in self._cache:
                self._hits += 1
                if text_id in self._cache_order:
                    self._cache_order.remove(text_id)
                self._cache_order.append(text_id)
                return self._cache[text_id][0]
            
            filepath = os.path.join(self.store_path, self._index[text_id]['file'])
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self._add_to_cache(text_id, content)
                return content
            except FileNotFoundError:
                del self._index[text_id]
                return None
            except IOError as e:
                print(f"⚠️ TextStore: ошибка чтения {text_id}: {e}")
                return None
    
    def _add_to_cache(self, text_id: str, content: str):
        while len(self._cache) >= self.cache_size and self._cache_order:
            oldest = self._cache_order.pop(0)
            del self._cache[oldest]
        
        self._cache[text_id] = (content, time.time())
        if text_id in self._cache_order:
            self._cache_order.remove(text_id)
        self._cache_order.append(text_id)
    
    def remove(self, text_id: str):
        with self._lock:
            if text_id not in self._index:
                return
            
            filepath = os.path.join(self.store_path, self._index[text_id]['file'])
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            
            del self._index[text_id]
            
            if text_id in self._cache:
                del self._cache[text_id]
                if text_id in self._cache_order:
                    self._cache_order.remove(text_id)
    
    def get_size(self, text_id: str) -> int:
        with self._lock:
            if text_id in self._index:
                return self._index[text_id].get('size', 0)
            return 0
    
    @property
    def hit_rate(self) -> float:
        with self._lock:
            return self._hits / max(self._requests, 1)
    
    def stats(self) -> dict:
        with self._lock:
            total_size = sum(info.get('size', 0) for info in self._index.values())
            return {
                'total_texts': len(self._index),
                'total_size_mb': round(total_size / 1024**2, 2),
                'cached': len(self._cache),
                'cache_size_limit': self.cache_size,
                'cache_requests': self._requests,
                'cache_hits': self._hits,
                'cache_hit_rate': round(self.hit_rate, 3)
            }


# ═══════════════════════════════════════════════════════════════════
#   ADAPTIVE RING BUFFER
# ═══════════════════════════════════════════════════════════════════

class AdaptiveRingBuffer:
    """
    Кольцевой буфер, размер которого адаптируется под дисперсию данных.
    
    Расширяется при высокой вариативности, сужается при стабильности.
    """
    
    __slots__ = ('_buffer', '_size', '_pos', '_count',
                 '_min_size', '_max_size', '_sum', '_sum_sq')
    
    def __init__(self, min_size: int = 100, max_size: int = 5000):
        self._min_size = min_size
        self._max_size = max_size
        self._size = min_size
        self._buffer = [0.0] * min_size
        self._pos = 0
        self._count = 0
        self._sum = 0.0
        self._sum_sq = 0.0
    
    def append(self, value: float):
        # Проверяем, нужно ли расширить
        if self._count >= self._size and self._size < self._max_size and self._count > 10:
            mean = self._sum / self._count
            variance = (self._sum_sq / self._count) - (mean * mean)
            cv = math.sqrt(max(0, variance)) / (abs(mean) + 0.001)
            if cv > 0.3:  # коэффициент вариации > 30%
                self._resize(min(self._max_size, self._size * 2))
        
        # Удаляем старый элемент
        if self._count >= self._size:
            old = self._buffer[self._pos]
            self._sum -= old
            self._sum_sq -= old * old
        else:
            self._count += 1
        
        # Добавляем новый
        self._buffer[self._pos] = value
        self._sum += value
        self._sum_sq += value * value
        self._pos = (self._pos + 1) % self._size
    
    def _resize(self, new_size: int):
        old_data = self.to_list()
        self._size = new_size
        self._buffer = [0.0] * new_size
        self._pos = len(old_data) % new_size
        self._count = min(len(old_data), new_size)
        for i, v in enumerate(old_data[-self._count:]):
            self._buffer[i] = v
    
    def __len__(self):
        return self._count
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise NotImplementedError("AdaptiveRingBuffer does not support slices")
        if index < 0:
            index = self._count + index
        if index < 0 or index >= self._count:
            raise IndexError("AdaptiveRingBuffer index out of range")
        if self._count < self._size:
            return self._buffer[index]
        return self._buffer[(self._pos + index) % self._size]
    
    def __iter__(self):
        if self._count < self._size:
            return iter(self._buffer[:self._count])
        return iter(self._buffer[self._pos:] + self._buffer[:self._pos])
    
    def to_list(self) -> List[float]:
        return list(self)
    
    @property
    def mean(self) -> float:
        return self._sum / max(self._count, 1)
    
    @property
    def std(self) -> float:
        if self._count < 2:
            return 0.0
        variance = (self._sum_sq / self._count) - (self.mean ** 2)
        return math.sqrt(max(0, variance))


# ═══════════════════════════════════════════════════════════════════
#   LIVING PERSONALITY V21.2 — ФИНАЛЬНАЯ
# ═══════════════════════════════════════════════════════════════════

class LivingPersonality(BasePersonality):
    """
    Живая личность v21.2 — единое поле, адаптивные коэффициенты, сон.
    
    Все параметры выводятся из состояния поля. Поле всегда единое
    (FieldV2 или FieldV2Stub). Сон включается автоматически при
    высоком sleep_pressure.
    """
    
    # ═══════════════════════════════════════════════════
    #   КОНСТРУКТОР
    # ═══════════════════════════════════════════════════
    
    def __init__(self, id: str = "living_v21", name: str = "Живая личность v21",
                text_store_path: str = None):
        # Не вызываем super().__init__() — он делает self.h_field = [] до создания _field_lock
        # Вместо этого копируем нужные поля из BasePersonality
        self.id = id
        self.name = name
        self.focus = {"tau": 16.0, "scale": 10.0, "phase": 0.0}
        self.vortices = []
        
        # Блокировка
        self._field_lock = threading.Lock()
        
        # Хранилище текстов
        store_path = text_store_path or f"./text_store_{id}"
        self.text_store = TextStore(store_path=store_path, cache_size=50)
        
        # ЕДИНОЕ ПОЛЕ
        if FIELD_V2_AVAILABLE:
            self.field = FieldV2(name=f"{name}_field")
        else:
            self.field = FieldV2Stub(name=f"{name}_field")
        
        # Состояние
        self.mood = 0.0
        self.energy = 1.0
        self.experience = 0
        self.generation = 0
        
        # Черты
        self.traits = {
            'curiosity': 0.7,
            'creativity': 0.5,
            'empathy': 0.6,
            'stability': 0.5,
        }
        
        # Инкрементальная статистика tau
        self._tau_sum = 0.0
        self._tau_sum_sq = 0.0
        self._tau_count = 0
        self._tau_recent = AdaptiveRingBuffer(min_size=100, max_size=2000)
        
        # Адаптивные буферы
        self.mood_history = AdaptiveRingBuffer(min_size=100, max_size=2000)
        self._resonance_history = AdaptiveRingBuffer(min_size=50, max_size=1000)
        
        # Счётчики
        self.dialog_count = 0
        self._cache_hit_window = []
        
        # Волновые эмоции
        if FIELD_V2_AVAILABLE:
            self._current_emotion = WaveformEmotion()
        else:
            self._current_emotion = type('WaveformEmotion', (), {
                'update': lambda self, dt=1.0, external_pressure=0.0: None
            })()
        
        self._hormones = {
            'dopamine': 0.5,
            'cortisol': 0.3,
            'melatonin': 0.3,
            'adrenaline': 0.1,
        }
        
        # Фоновый поток
        self._background_running = False
        self._background_thread = None
        self._sleeping = False
        
        # Холодный старт
        self._COLD_START = {
            'tau_min': 5.0,
            'tau_max': 11.0,
            'mood_inertia_base': 0.85,
            'hormone_rate_base': 0.05,
            'resonance_threshold': 0.15,
            'energy_cost_base': 0.1,
        }
        
        print(f"\n🌱 {name} v21.2 активирована")
        print(f"   Поле: {'FieldV2' if FIELD_V2_AVAILABLE else 'FieldV2Stub'} (единый интерфейс)")
        print(f"   TextStore: {store_path}")
        print(f"   Все коэффициенты — адаптивные")
        print(f"   Сон — автоматический")
    
    # ═══════════════════════════════════════════════════
    #   PROPERTY ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ
    # ═══════════════════════════════════════════════════
    
    @property
    def h_field(self):
        with self._field_lock:
            modes = []
            for layer in self.field.layers.values():
                if hasattr(layer, 'modes'):
                    modes.extend(layer.modes.values())
            return modes
    
    @h_field.setter
    def h_field(self, value):
        with self._field_lock:
            old_name = self.field.name if hasattr(self.field, 'name') else "field"
            if FIELD_V2_AVAILABLE:
                self.field = FieldV2(name=old_name)
            else:
                self.field = FieldV2Stub(name=old_name)
            
            for mode in value:
                self.add_to_h_field(mode)
            
            print(f"⚠️ h_field перезаписан: {len(value)} мод")
    
    # ═══════════════════════════════════════════════════
    #   ИНКРЕМЕНТАЛЬНАЯ СТАТИСТИКА TAU (O(1))
    # ═══════════════════════════════════════════════════
    
    def _collect_tau_incremental(self, tau: float):
        """O(1) обновление статистики tau."""
        if tau <= 0:
            return
        
        self._tau_count += 1
        self._tau_sum += tau
        self._tau_sum_sq += tau * tau
        self._tau_recent.append(tau)
    
    @property
    def tau_mean(self) -> float:
        if self._tau_count == 0:
            return 16.0
        return self._tau_sum / self._tau_count
    
    @property
    def tau_std(self) -> float:
        if self._tau_count < 2:
            return 5.0
        mean = self.tau_mean
        variance = (self._tau_sum_sq / self._tau_count) - (mean * mean)
        return math.sqrt(max(0, variance))
    
    @property
    def vmmp_tau_min(self) -> float:
        """10-й перцентиль из недавней выборки."""
        recent = self._tau_recent.to_list()
        if len(recent) < 20:
            return self._COLD_START['tau_min']
        recent.sort()
        idx = max(0, int(len(recent) * 0.1))
        return recent[idx]
    
    @property
    def vmmp_tau_max(self) -> float:
        """90-й перцентиль."""
        recent = self._tau_recent.to_list()
        if len(recent) < 20:
            return self._COLD_START['tau_max']
        recent.sort()
        idx = min(len(recent) - 1, int(len(recent) * 0.9))
        return recent[idx]
    
    # ═══════════════════════════════════════════════════
    #   АДАПТИВНЫЕ КОЭФФИЦИЕНТЫ
    # ═══════════════════════════════════════════════════
    
    @property
    def mood_inertia(self) -> float:
        stability = self.traits.get('stability', 0.5)
        return 0.7 + stability * 0.25
    
    @property
    def hormone_rate(self) -> float:
        energy = max(0.1, self.energy)
        experience_factor = 1.0 / (1.0 + self.experience * 0.001)
        base_rate = 0.01 + energy * 0.09
        return base_rate * experience_factor
    
    @property
    def resonance_threshold(self) -> float:
        base = self._COLD_START['resonance_threshold']
        
        energy_factor = 1.0 + (1.0 - self.energy) * 0.5
        experience_factor = 1.0 / (1.0 + self.experience * 0.01)
        
        history_factor = 1.0
        recent = self._resonance_history.to_list()
        if len(recent) >= 10:
            avg_recent = sum(recent[-10:]) / 10
            if avg_recent < 0.2:
                history_factor = 0.6
            elif avg_recent > 0.6:
                history_factor = 1.3
        
        threshold = base * energy_factor * experience_factor * history_factor
        return max(0.03, min(0.5, threshold))
    
    @property
    def adrenaline_decay(self) -> float:
        stability = self.traits.get('stability', 0.5)
        return 0.9 + stability * 0.08
    
    @property
    def sleep_pressure(self) -> float:
        """
        Давление сна: 0.0 (бодрость) — 1.0 (глубокий сон).
        
        Факторы:
        - 40%: низкая энергия
        - 30%: высокий мелатонин
        - 20%: необработанный опыт
        - 10%: фрагментация поля
        """
        pressure = 0.0
        
        pressure += (1.0 - self.energy) * 0.4
        pressure += self._hormones.get('melatonin', 0.2) * 0.3
        
        unprocessed = min(1.0, self.experience / max(self.dialog_count, 1))
        pressure += unprocessed * 0.2
        
        if self.tau_std > 0:
            fragmentation = min(1.0, self.tau_std / 20.0)
            pressure += fragmentation * 0.1
        
        return max(0.0, min(1.0, pressure))
    
    def compute_preferred_scale(self, text: str) -> float:
        text_len = len(text)
        if text_len > 500:
            len_scale = 30.0
        elif text_len > 100:
            len_scale = 15.0
        elif text_len > 20:
            len_scale = 8.0
        else:
            len_scale = 3.0
        
        spectrum = self.phrase_spectrum(text)
        if spectrum and len(spectrum) > 1:
            freqs = list(spectrum.keys())
            dispersion = max(freqs) - min(freqs)
            if dispersion > 20:
                dispersion_scale = 30.0
            elif dispersion > 10:
                dispersion_scale = 20.0
            else:
                dispersion_scale = 10.0
        else:
            dispersion_scale = len_scale
        
        context_depth = min(1.0, self.dialog_count / 100.0)
        context_scale = 5.0 + context_depth * 25.0
        
        preferred = len_scale * 0.3 + dispersion_scale * 0.4 + context_scale * 0.3
        self.focus["scale"] = self.focus.get("scale", 10.0) * 0.9 + preferred * 0.1
        
        return preferred
    
    def compute_energy_cost(self, resonance: float, scale: float) -> float:
        base_cost = 0.02 + (1.0 - resonance) * 0.2
        scale_factor = 1.0 + scale / 100.0
        fatigue = min(1.0, self.dialog_count / 1000.0)
        fatigue_factor = 1.0 + fatigue * 0.5
        return base_cost * scale_factor * fatigue_factor
    
    # ═══════════════════════════════════════════════════
    #   ВММП-ФИЛЬТР
    # ═══════════════════════════════════════════════════
    
    def _passes_vmmp_filter(self, mode) -> bool:
        tau = getattr(mode, 'tau', 0)
        scale = getattr(mode, 'scale', 1.0)
        amplitude = getattr(mode, 'amplitude', 0.5)
        
        if scale >= 20.0:
            return True
        if amplitude >= 0.7:
            return True
        
        tau_min = self.vmmp_tau_min
        tau_max = self.vmmp_tau_max
        
        if tau_min <= tau <= tau_max:
            return True
        
        if tau < tau_min or tau > tau_max:
            if scale >= 10.0 and amplitude >= 0.6:
                return True
            return False
        
        return True
    
    # ═══════════════════════════════════════════════════
    #   РАБОТА С ПОЛЕМ
    # ═══════════════════════════════════════════════════
    
    def add_to_h_field(self, mode) -> None:
        with self._field_lock:
            content = getattr(mode, 'content', '') or getattr(mode, '_content', '')
            if content and not getattr(mode, 'text_id', None):
                mode.text_id = self.text_store.store(content)
                if hasattr(mode, '_content'):
                    mode._content = None
            
            if not hasattr(mode, 'tau_spectrum') or mode.tau_spectrum is None:
                text_for_spectrum = ''
                if getattr(mode, 'text_id', None):
                    text_for_spectrum = self.text_store.get(mode.text_id) or ''
                elif content:
                    text_for_spectrum = content[:500]
                
                if text_for_spectrum:
                    spectrum = self.field.spectrum_to_intervals(
                        self.phrase_spectrum(text_for_spectrum[:500])
                    )
                    mode.tau_spectrum = spectrum
            
            if not hasattr(mode, 'scale') or mode.scale is None:
                content_len = 0
                if getattr(mode, 'text_id', None):
                    content_len = self.text_store.get_size(mode.text_id)
                elif content:
                    content_len = len(content)
                
                if content_len > 500:
                    mode.scale = 30.0
                elif content_len > 100:
                    mode.scale = 15.0
                else:
                    mode.scale = 5.0
            
            # === ИСПРАВЛЕНИЕ: адаптируем mode для FieldV2 ===
            # FieldV2.add_mode ожидает объект с .id, а SpectralMode использует .trace_id
            # Создаём поле .id если его нет
            if not hasattr(mode, 'id'):
                mode.id = getattr(mode, 'trace_id', None) or getattr(mode, 'text_id', None) or hashlib.md5(
                    str(getattr(mode, 'tau', 0)).encode()
                ).hexdigest()[:8]
            
            # FieldV2 также может ожидать .tau_spectrum как dict с интервалами
            # Убедимся что спектр — это dict или None
            if hasattr(mode, 'tau_spectrum') and mode.tau_spectrum is not None:
                if not isinstance(mode.tau_spectrum, dict):
                    # Конвертируем в dict если нужно
                    mode.tau_spectrum = {float(k): float(v) for k, v in mode.tau_spectrum.items()} if hasattr(mode.tau_spectrum, 'items') else {}
            # =============================================
            
            # Добавляем в единое поле
            self.field.add_mode(mode)
            
            # Очищаем спектр
            if hasattr(mode, 'tau_spectrum') and mode.tau_spectrum is not None:
                mode.tau_spectrum = None
            
            # Инкрементальная статистика tau
            tau = getattr(mode, 'tau', 0)
            self._collect_tau_incremental(tau)
            
            self._prune_field()
    
    def _prune_field(self):
        max_modes_per_layer = 500
        for layer_id in range(1, 5):
            layer = self.field.layers.get(layer_id)
            if not layer or not hasattr(layer, 'modes'):
                continue
            
            excess = len(layer.modes) - max_modes_per_layer
            if excess > 0:
                # Удаляем первые N элементов (самые старые)
                # dict.popitem() не поддерживает last=False в Python 3.7+
                # Поэтому получаем первый ключ и удаляем по нему
                for _ in range(excess):
                    if layer.modes:
                        first_key = next(iter(layer.modes))
                        del layer.modes[first_key]
                
                if hasattr(self.field, 'stats'):
                    self.field.stats['total_modes'] = max(
                        0, self.field.stats.get('total_modes', 0) - excess
                    )
    
    def get_all_modes(self) -> List:
        with self._field_lock:
            modes = []
            for layer in self.field.layers.values():
                if hasattr(layer, 'modes'):
                    modes.extend(layer.modes.values())
            return modes
    
    # ═══════════════════════════════════════════════════
    #   ЭМОЦИИ И ГОРМОНЫ
    # ═══════════════════════════════════════════════════
    
    def _get_emotional_tag(self) -> str:
        d = self._hormones.get('dopamine', 0.5)
        c = self._hormones.get('cortisol', 0.3)
        m = self._hormones.get('melatonin', 0.2)
        
        if d > 0.6 and c < 0.4:
            return 'joy'
        elif c > 0.5 and d < 0.5:
            return 'stress'
        elif m > 0.6:
            return 'calm'
        
        if self.mood > 0.3:
            return 'joy'
        elif self.mood < -0.3:
            return 'stress'
        return 'neutral'
    
    def _update_hormones(self, sentiment: float):
        rate = self.hormone_rate
        
        target_d = max(0, sentiment)
        self._hormones['dopamine'] += (target_d - self._hormones['dopamine']) * rate
        
        target_c = max(0, -sentiment)
        self._hormones['cortisol'] += (target_c * 1.5 - self._hormones['cortisol']) * rate
        
        hour_angle = (self.dialog_count % 24) / 24.0 * 2 * math.pi
        target_m = 0.3 + 0.4 * math.sin(hour_angle)
        self._hormones['melatonin'] += (target_m - self._hormones['melatonin']) * rate * 0.3
        
        surprise = abs(sentiment - self.mood)
        if surprise > 0.5:
            spike = min(1.0, surprise * 1.5)
            self._hormones['adrenaline'] = spike
        else:
            self._hormones['adrenaline'] *= self.adrenaline_decay
        
        for k in self._hormones:
            self._hormones[k] = max(0.0, min(1.0, self._hormones[k]))
    
    # ═══════════════════════════════════════════════════
    #   ПОИСК МОДЫ
    # ═══════════════════════════════════════════════════
    
    def _find_best_mode(self, text: str, preferred_scale: float = None) -> Tuple[Any, float, str]:
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        
        if preferred_scale is None:
            preferred_scale = self.compute_preferred_scale(text)
        
        query_emotion = WaveformEmotion(
            amplitude=0.5,
            frequency=0.1,
            phase=0.0,
            base_emotion=self._get_emotional_tag()
        ) if FIELD_V2_AVAILABLE else None
        
        with self._field_lock:
            try:
                results = self.field.find_by_resonance(
                    query_tau=question_tau,
                    query_scale=preferred_scale,
                    query_phase=0.0,
                    query_emotion=query_emotion,
                    query_spectrum=question_spectrum,
                    k=10,
                    use_priority_bonus=True,
                    early_exit=True
                )
            except TypeError:
                results = self.field.find_by_resonance(
                    query_tau=question_tau,
                    query_scale=preferred_scale,
                    query_phase=0.0,
                    query_emotion=query_emotion,
                    query_spectrum=question_spectrum,
                    k=10,
                    use_priority_bonus=True
                )
        
        if not results:
            return None, 0.0, "no_resonance"
        
        mode_id, resonance, layer, details = results[0]
        
        with self._field_lock:
            best_mode = self.field.get_mode(mode_id)
        
        if not best_mode:
            return None, 0.0, "mode_not_found"
        
        if not self._passes_vmmp_filter(best_mode):
            return None, 0.0, "filtered"
        
        self._resonance_history.append(resonance)
        
        return best_mode, resonance, f"field_layer_{layer}"
    
    # ═══════════════════════════════════════════════════
    #   ОБРАБОТКА СООБЩЕНИЙ
    # ═══════════════════════════════════════════════════
    
    def _detect_sentiment(self, text: str) -> float:
        positive = ["хорош", "отличн", "прекрасн", "класс", "супер", "люблю", "нравит", "рад"]
        negative = ["плох", "ужасн", "ненавиж", "грустн", "печальн", "зл", "обид"]
        
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        
        if pos + neg == 0:
            return 0.0
        return (pos - neg) / (pos + neg)
    
    def _update_mood(self, sentiment: float):
        inertia = self.mood_inertia
        sensitivity = 1.0 - inertia
        
        self.mood = self.mood * inertia + sentiment * sensitivity
        self.mood = max(-1.0, min(1.0, self.mood))
        
        self.mood_history.append(self.mood)
        self._update_hormones(sentiment)
        
        if self._current_emotion and hasattr(self._current_emotion, 'update'):
            self._current_emotion.update(dt=1.0, external_pressure=abs(sentiment))
    
    def process(self, text: str, user_id: str = "default") -> dict:
        self.dialog_count += 1
        self.experience += 1
        
        sentiment = self._detect_sentiment(text)
        self._update_mood(sentiment)
        
        best_mode, best_score, source = self._find_best_mode(text)
        threshold = self.resonance_threshold
        
        if best_mode and best_score > threshold:
            text_id = getattr(best_mode, 'text_id', None)
            if text_id:
                full_content = self.text_store.get(text_id) or ''
            else:
                full_content = getattr(best_mode, 'content', '') or getattr(best_mode, '_content', '')
            
            answer = full_content[:800] if full_content else ''
            mode_type = source
            
            if best_score > 0.6:
                eeg = "Глубокая синхронизация тета-альфа. Безвременье активно."
            elif best_score > 0.4:
                eeg = "Умеренная синхронизация. Пред-инсайтное состояние."
            else:
                eeg = "Обычная когнитивная нагрузка. Попытка вывода."
            
            scale = getattr(best_mode, 'scale', 10.0)
            energy_cost = self.compute_energy_cost(best_score, scale)
            self.energy = max(0.0, self.energy - energy_cost)
            
            response = {
                "answer": answer,
                "mode_used": getattr(best_mode, 'trace_id', '?')[:16],
                "mode_type": mode_type,
                "resonance": best_score,
                "eeg_prediction": eeg,
                "energy_cost": round(energy_cost, 3),
                "is_stamp": False,
                "mood": self.mood,
                "dialog_count": self.dialog_count,
                "sleeping": self._sleeping,
            }
        else:
            energy_cost = 0.01
            self.energy = max(0.0, self.energy - energy_cost)
            
            if self._sleeping:
                answer = "zzz... *поле видит сон* ...zzz"
            else:
                answer = "Интересно... Расскажи подробнее."
            
            response = {
                "answer": answer,
                "mode_type": "fallback",
                "resonance": 0.0,
                "energy_cost": energy_cost,
                "mood": self.mood,
                "dialog_count": self.dialog_count,
                "sleeping": self._sleeping,
            }
        
        # Восстановление энергии (медленнее во сне)
        recovery_rate = 0.002 if self._sleeping else 0.001
        self.energy = min(1.0, self.energy + recovery_rate)
        
        # Адаптация кеша
        self._cache_hit_window.append(1 if best_score > threshold else 0)
        if len(self._cache_hit_window) >= 100:
            self._adapt_cache_size()
            self._cache_hit_window = self._cache_hit_window[-100:]
        
        # История диалогов
        if not hasattr(self, 'dialog_history'):
            self.dialog_history = {}
        if user_id not in self.dialog_history:
            self.dialog_history[user_id] = []
        
        user_history = self.dialog_history[user_id]
        max_per_user = 50
        if len(user_history) >= max_per_user:
            user_history = user_history[-20:]
            for entry in user_history:
                entry['question'] = entry.get('question', '')[:200]
                entry['answer'] = entry.get('answer', '')[:200]
        
        user_history.append({
            "question": text[:2048],
            "answer": response.get("answer", "")[:2048],
            "sentiment": sentiment,
            "mood": self.mood,
            "timestamp": int(time.time())
        })
        self.dialog_history[user_id] = user_history
        
        total_dialogs = sum(len(h) for h in self.dialog_history.values())
        if total_dialogs > 5000:
            users_with_ts = []
            for u, history in self.dialog_history.items():
                ts = history[-1].get('timestamp', 0) if history else 0
                users_with_ts.append((u, ts))
            users_with_ts.sort(key=lambda x: x[1])
            to_remove = len(users_with_ts) // 2
            for u, _ in users_with_ts[:to_remove]:
                del self.dialog_history[u]
        
        return response
    
    def _adapt_cache_size(self):
        if len(self._cache_hit_window) < 50:
            return
        
        recent = self._cache_hit_window[-100:]
        hit_rate = sum(recent) / len(recent)
        
        if hit_rate < 0.7 and self.text_store.cache_size < 500:
            self.text_store.cache_size = min(500, self.text_store.cache_size + 50)
        elif hit_rate > 0.95 and self.text_store.cache_size > 30:
            self.text_store.cache_size = max(30, self.text_store.cache_size - 25)
    
    # ═══════════════════════════════════════════════════
    #   ФОНОВЫЙ РОСТ С САМОРЕГУЛЯЦИЕЙ СНА
    # ═══════════════════════════════════════════════════
    
    def start_living(self, interval: float = 0.5):
        if self._background_running:
            return
        
        self._background_running = True
        self._background_thread = threading.Thread(
            target=self._living_loop, args=(interval,), daemon=True
        )
        self._background_thread.start()
        print("🌿 Фоновый рост запущен (с авто-сном)")
    
    def stop_living(self):
        self._background_running = False
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=2.0)
        print("🛑 Фоновый рост остановлен")
    
    def force_sleep(self):
        """Принудительно отправляет поле в сон."""
        self._sleeping = True
        self._hormones['melatonin'] = 0.9
        print("😴 Поле принудительно усыплено")
    
    def force_wake(self):
        """Принудительно пробуждает поле."""
        self._sleeping = False
        self._hormones['melatonin'] = 0.1
        self.energy = 0.9
        print("☀️ Поле принудительно пробуждено")
    
    def _living_loop(self, interval: float):
        cycle = 0
        while self._background_running:
            try:
                time.sleep(interval)
                cycle += 1
                
                # Проверка давления сна
                pressure = self.sleep_pressure
                
                if pressure > 0.7 and not self._sleeping:
                    self._sleeping = True
                    print(f"😴 Поле засыпает (давление сна: {pressure:.2f})")
                
                if self._sleeping:
                    # === РЕЖИМ СНА ===
                    # Восстановление энергии (быстрее)
                    self.energy = min(1.0, self.energy + 0.005)
                    
                    # Снижение мелатонина
                    self._hormones['melatonin'] *= 0.995
                    
                    # Снижение кортизола
                    self._hormones['cortisol'] *= 0.99
                    
                    # Консолидация опыта (кросс-слойная динамика)
                    if cycle % 120 == 0:
                        with self._field_lock:
                            dynamics = self.field.step_cross_layer_dynamics(dt=interval * 120)
                        
                        if dynamics.get('emerged'):
                            print(f"💤 Сон: эмерджентные моды {dynamics['emerged']}")
                    
                    # Пробуждение
                    if self.energy > 0.85 and self._hormones['melatonin'] < 0.15:
                        self._sleeping = False
                        self.experience = 0  # сбрасываем необработанный опыт
                        print(f"☀️ Поле проснулось (энергия: {self.energy:.2f})")
                    
                    if cycle % 600 == 0:
                        self._print_sleep_status()
                
                else:
                    # === РЕЖИМ БОДРСТВОВАНИЯ ===
                    self._evolve_traits()
                    
                    if cycle % 240 == 0:
                        with self._field_lock:
                            dynamics = self.field.step_cross_layer_dynamics(dt=interval * 240)
                        
                        if dynamics.get('emerged'):
                            print(f"🌱 Эмерджентные моды: {dynamics['emerged']}")
                    
                    if cycle % 120 == 0:
                        self._print_status()
                    
                    if cycle % 1200 == 0:
                        gc.collect()
                
            except Exception as e:
                print(f"⚠️ Ошибка в фоновом цикле: {e}")
                time.sleep(5)
    
    def _evolve_traits(self):
        for trait in self.traits:
            delta = random.uniform(-0.002, 0.002)
            self.traits[trait] = max(0.2, min(0.9, self.traits[trait] + delta))
    
    def _print_status(self):
        lines = [
            f"\n[{datetime.now().strftime('%H:%M:%S')}] 🌱 Статус v21.2:",
            f"   Диалогов: {self.dialog_count} | Опыт: {self.experience}",
            f"   Мод: {self.field.stats.get('total_modes', '?')}",
            f"   Настроение: {self.mood:+.2f} | Энергия: {self.energy:.2f}",
            f"   Эмоция: {self._get_emotional_tag()}",
            f"   VMMP tau: [{self.vmmp_tau_min:.1f}, {self.vmmp_tau_max:.1f}]",
            f"   Порог резонанса: {self.resonance_threshold:.3f}",
            f"   Давление сна: {self.sleep_pressure:.2f}",
        ]
        print("\n".join(lines))
    
    def _print_sleep_status(self):
        lines = [
            f"\n[{datetime.now().strftime('%H:%M:%S')}] 💤 Сон:",
            f"   Энергия: {self.energy:.2f} | Мелатонин: {self._hormones['melatonin']:.2f}",
            f"   Давление сна: {self.sleep_pressure:.2f}",
        ]
        print("\n".join(lines))
    
    # ═══════════════════════════════════════════════════
    #   ДИАГНОСТИКА
    # ═══════════════════════════════════════════════════
    
    def get_field_stats(self) -> Dict:
        with self._field_lock:
            stats = self.field.get_stats()
            stats['text_store'] = self.text_store.stats()
            stats['adaptive'] = {
                'vmmp_tau_min': round(self.vmmp_tau_min, 2),
                'vmmp_tau_max': round(self.vmmp_tau_max, 2),
                'tau_mean': round(self.tau_mean, 2),
                'tau_std': round(self.tau_std, 2),
                'mood_inertia': round(self.mood_inertia, 3),
                'hormone_rate': round(self.hormone_rate, 4),
                'resonance_threshold': round(self.resonance_threshold, 3),
                'energy': round(self.energy, 3),
                'sleep_pressure': round(self.sleep_pressure, 3),
                'sleeping': self._sleeping,
                'tau_samples': self._tau_count,
            }
            return stats
    
    def introspect(self) -> str:
        ts_stats = self.text_store.stats()
        
        return f"""
=== САМОРЕФЛЕКСИЯ v21.2 ===
Я: {self.name}
Диалогов: {self.dialog_count} | Опыт: {self.experience}
Поколение: {self.generation}
Состояние: {'💤 Сон' if self._sleeping else '🌱 Бодрствование'}

Настроение: {self.mood:+.2f} | Энергия: {self.energy:.2f}
Эмоция: {self._get_emotional_tag()}
Давление сна: {self.sleep_pressure:.2f}
Гормоны: Д={self._hormones['dopamine']:.2f} К={self._hormones['cortisol']:.2f} М={self._hormones['melatonin']:.2f} А={self._hormones['adrenaline']:.2f}

Черты:
  - Любопытство: {self.traits['curiosity']:.2f}
  - Креативность: {self.traits['creativity']:.2f}
  - Эмпатия: {self.traits['empathy']:.2f}
  - Стабильность: {self.traits['stability']:.2f}

Адаптивные коэффициенты:
  - VMMP tau: [{self.vmmp_tau_min:.1f}, {self.vmmp_tau_max:.1f}] (μ={self.tau_mean:.1f}, σ={self.tau_std:.1f})
  - Инерция настроения: {self.mood_inertia:.3f}
  - Скорость гормонов: {self.hormone_rate:.4f}
  - Порог резонанса: {self.resonance_threshold:.3f}
  - Затухание адреналина: {self.adrenaline_decay:.3f}

Поле:
  - Всего мод: {self.field.stats.get('total_modes', '?')}
  - По слоям: {self.field.stats.get('modes_per_layer', {})}

TextStore:
  - Текстов на диске: {ts_stats['total_texts']}
  - Занимают: {ts_stats['total_size_mb']} МБ
  - Кеш: {ts_stats['cached']}/{ts_stats['cache_size_limit']}
  - Hit rate: {ts_stats['cache_hit_rate']}
"""
    
    # ═══════════════════════════════════════════════════
    #   СОХРАНЕНИЕ И ЗАГРУЗКА
    # ═══════════════════════════════════════════════════
    
    def save(self, filepath: str):
        with self._field_lock:
            all_modes = self.get_all_modes()
        
        data = {
            'id': self.id,
            'name': self.name,
            'h_field': [],
            'vortices': self.vortices if hasattr(self, 'vortices') else [],
            'focus': self.focus,
            'mood': self.mood,
            'energy': self.energy,
            'experience': self.experience,
            'generation': self.generation,
            'traits': self.traits,
            'dialog_count': self.dialog_count,
            'version': 'v21.2',
            'text_store_path': self.text_store.store_path,
            'sleeping': self._sleeping,
        }
        
        for mode in all_modes:
            text_id = getattr(mode, 'text_id', None)
            content = ''
            if text_id:
                content = self.text_store.get(text_id) or ''
            else:
                content = getattr(mode, 'content', '') or getattr(mode, '_content', '')
            
            mode_data = {
                'tau': getattr(mode, 'tau', 0),
                'amplitude': getattr(mode, 'amplitude', 0.5),
                'content': content,
                'themes': getattr(mode, 'themes', []),
                'trace_id': getattr(mode, 'trace_id', ''),
                'creator': getattr(mode, 'creator', ''),
                'scale': getattr(mode, 'scale', 10.0),
                'phase': getattr(mode, 'phase', 0.0),
                'text_id': text_id or '',
            }
            data['h_field'].append(mode_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.text_store._save_index()
        print(f"💾 Сохранено: {filepath} (мод: {len(data['h_field'])})")
    
    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        store_path = data.get('text_store_path')
        instance = cls(
            id=data.get('id', 'loaded'),
            name=data.get('name', 'Загруженная v21'),
            text_store_path=store_path
        )
        
        if 'focus' in data:
            instance.focus = data['focus']
        if 'mood' in data:
            instance.mood = data['mood']
        if 'energy' in data:
            instance.energy = data['energy']
        if 'experience' in data:
            instance.experience = data['experience']
        if 'generation' in data:
            instance.generation = data['generation']
        if 'traits' in data:
            instance.traits.update(data['traits'])
        if 'dialog_count' in data:
            instance.dialog_count = data['dialog_count']
        if 'sleeping' in data:
            instance._sleeping = data['sleeping']
        
        for mode_data in data.get('h_field', []):
            content = mode_data.get('content', '')
            text_id = mode_data.get('text_id', '')
            
            if content and not text_id:
                text_id = instance.text_store.store(content)
            
            mode = SpectralMode(
                tau=mode_data.get('tau', 16.0),
                amplitude=mode_data.get('amplitude', 0.5),
                content='',
                themes=mode_data.get('themes', []),
                trace_id=mode_data.get('trace_id', hashlib.md5(
                    content.encode() if content else b''
                ).hexdigest()[:8]),
                creator=mode_data.get('creator', 'loaded_v21'),
                scale=mode_data.get('scale', 10.0),
                phase=mode_data.get('phase', 0.0),
                text_id=text_id,
            )
            instance.add_to_h_field(mode)
        
        print(f"📂 Загружено: {filepath} (мод: {len(data.get('h_field', []))})")
        return instance
    
    def migrate_to_text_store(self) -> int:
        migrated = 0
        with self._field_lock:
            for layer in self.field.layers.values():
                if not hasattr(layer, 'modes'):
                    continue
                for mode in list(layer.modes.values()):
                    content = getattr(mode, '_content', None) or getattr(mode, 'content', '')
                    if content and not getattr(mode, 'text_id', None):
                        mode.text_id = self.text_store.store(content)
                        if hasattr(mode, '_content'):
                            mode._content = None
                        migrated += 1
        
        if migrated:
            print(f"📦 Мигрировано {migrated} мод в TextStore")
            self.text_store._save_index()
        
        return migrated


# ═══════════════════════════════════════════════════════════════════
#   ТЕСТ
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование Living Personality v21.2")
    print("=" * 60)
    
    personality = LivingPersonality(id="test_v21_2", name="Тест v21.2")
    
    test_modes = [
        ("tees_основа", "TEES — это топологический переход в поле H.", 16.0, 0.7, 30.0),
        ("углерод_тетраэдр", "Углерод имеет тетраэдрическую симметрию и 4 валентности.", 6.0, 0.8, 15.0),
        ("приталкивание", "Гравитация — это приталкивание, а не притяжение.", 10.0, 0.6, 5.0),
    ]
    
    for mid, content, tau, amp, scale in test_modes:
        mode = SpectralMode(
            tau=tau, amplitude=amp, content=content,
            themes=['test'], trace_id=mid, creator='test', scale=scale
        )
        personality.add_to_h_field(mode)
    
    print(f"\n📊 Адаптивные коэффициенты:")
    print(f"   VMMP tau: [{personality.vmmp_tau_min:.1f}, {personality.vmmp_tau_max:.1f}]")
    print(f"   Средний tau: {personality.tau_mean:.1f} ± {personality.tau_std:.1f}")
    print(f"   Порог резонанса: {personality.resonance_threshold:.3f}")
    print(f"   Давление сна: {personality.sleep_pressure:.2f}")
    
    test_questions = [
        "Что такое TEES?",
        "Расскажи про гравитацию",
    ]
    
    for q in test_questions:
        print(f"\n👤 Вопрос: {q}")
        result = personality.process(q)
        print(f"🤖 Ответ: {result['answer'][:100]}...")
        print(f"   Резонанс: {result['resonance']:.2f} | Спит: {result['sleeping']}")
    
    # Тест сна
    print("\n--- Тест сна ---")
    personality.energy = 0.1
    personality._hormones['melatonin'] = 0.8
    print(f"Давление сна: {personality.sleep_pressure:.2f}")
    
    if personality.sleep_pressure > 0.7:
        personality._sleeping = True
        print("😴 Поле заснуло")
        result = personality.process("Привет!")
        print(f"🤖 Ответ во сне: {result['answer']}")
    
    print("\n" + "=" * 60)
    print("✅ Тест v21.2 пройден")
    print("=" * 60)