#!/usr/bin/env python3
"""
Living Personality v21.2 — чистая версия (без заглушек)
========================================================
Работает с оригинальным living_personality_v20_2.py.
Не заменяет SpectralMode, не мокает BasePersonality.
Все оптимизации внутри класса, без внешних заглушек.

Путь: src/architect/living_personality_v21_clean.py
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
from datetime import datetime

# Добавляем пути для импортов
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Импортируем оригинальный v20.2 (без заглушек!)
from rizoma.living_personality_v20_2 import LivingPersonality as BasePersonality, SpectralMode

# Импортируем FieldV2
try:
    from architect.field_v2 import FieldV2, WaveformEmotion
    FIELD_V2_AVAILABLE = True
except ImportError:
    print("❌ FieldV2 не найден. v21.2 требует FieldV2.")
    print("   Убедитесь, что src/architect/field_v2.py существует.")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
#   TEXT STORE
# ═══════════════════════════════════════════════════════════════════

class TextStore:
    """Хранилище текстов на диске с LRU-кешем в RAM."""
    
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
                self._index = {}
    
    def _save_index(self):
        index_path = os.path.join(self.store_path, "index.json")
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False)
        except IOError:
            pass
    
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
            except IOError:
                return ""
            self._index[text_id] = {'file': f"{text_id}.txt", 'hash': text_hash, 'size': len(text)}
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
            except (FileNotFoundError, IOError):
                if text_id in self._index:
                    del self._index[text_id]
                return None
    
    def _add_to_cache(self, text_id: str, content: str):
        while len(self._cache) >= self.cache_size and self._cache_order:
            oldest = self._cache_order.pop(0)
            del self._cache[oldest]
        self._cache[text_id] = (content, time.time())
        if text_id in self._cache_order:
            self._cache_order.remove(text_id)
        self._cache_order.append(text_id)
    
    def get_size(self, text_id: str) -> int:
        with self._lock:
            return self._index.get(text_id, {}).get('size', 0)
    
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
    """Кольцевой буфер с адаптивным размером."""
    
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
        if self._count >= self._size and self._size < self._max_size and self._count > 10:
            mean = self._sum / self._count
            variance = (self._sum_sq / self._count) - (mean * mean)
            cv = math.sqrt(max(0, variance)) / (abs(mean) + 0.001)
            if cv > 0.3:
                self._resize(min(self._max_size, self._size * 2))
        if self._count >= self._size:
            old = self._buffer[self._pos]
            self._sum -= old
            self._sum_sq -= old * old
        else:
            self._count += 1
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
            raise NotImplementedError
        if index < 0:
            index = self._count + index
        if index < 0 or index >= self._count:
            raise IndexError
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
#   LIVING PERSONALITY V21.2 — ЧИСТАЯ ВЕРСИЯ
# ═══════════════════════════════════════════════════════════════════

class LivingPersonality(BasePersonality):
    """
    Живая личность v21.2 — адаптивная, 7-слойное поле, авто-сон.
    
    Наследует LivingPersonality из living_personality_v20_2.py.
    Не использует заглушек.
    """
    
    def __init__(self, id: str = "living_v21", name: str = "Живая личность v21",
                 text_store_path: str = None):
        
        # Вызываем оригинальный конструктор v20.2
        super().__init__(id=id, name=name)
        
        # Хранилище текстов
        store_path = text_store_path or f"./text_store_{id}"
        self.text_store = TextStore(store_path=store_path, cache_size=50)
        
        # ЕДИНОЕ ПОЛЕ
        self.field = FieldV2(name=f"{name}_field")
        self._field_lock = threading.Lock()
        
        # Состояние
        self.mood = getattr(self, 'mood', 0.0)
        self.energy = getattr(self, 'energy', 1.0)
        self.experience = getattr(self, 'experience', 0)
        self.generation = getattr(self, 'generation', 0)
        
        # Черты (сохраняем из v20.2 если есть, иначе дефолт)
        default_traits = {'curiosity': 0.7, 'creativity': 0.5, 'empathy': 0.6, 'stability': 0.5}
        if hasattr(self, 'traits'):
            for k, v in default_traits.items():
                if k not in self.traits:
                    self.traits[k] = v
        else:
            self.traits = default_traits
        
        # Инкрементальная статистика tau
        self._tau_sum = 0.0
        self._tau_sum_sq = 0.0
        self._tau_count = 0
        self._tau_recent = AdaptiveRingBuffer(min_size=100, max_size=2000)
        
        # Адаптивные буферы
        self.mood_history = AdaptiveRingBuffer(min_size=100, max_size=2000)
        self._resonance_history = AdaptiveRingBuffer(min_size=50, max_size=1000)
        
        # Счётчики
        self.dialog_count = getattr(self, 'dialog_count', 0)
        self._cache_hit_window = []
        
        # Волновые эмоции
        self._current_emotion = WaveformEmotion()
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
        print(f"   Поле: FieldV2 (7 слоёв)")
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
            self.field = FieldV2(name=old_name)
            for mode in value:
                self.add_to_h_field(mode)
            if value:
                print(f"⚠️ h_field перезаписан: {len(value)} мод")
    
    # ═══════════════════════════════════════════════════
    #   ИНКРЕМЕНТАЛЬНАЯ СТАТИСТИКА TAU (O(1))
    # ═══════════════════════════════════════════════════
    
    def _collect_tau_incremental(self, tau: float):
        if tau <= 0:
            return
        self._tau_count += 1
        self._tau_sum += tau
        self._tau_sum_sq += tau * tau
        self._tau_recent.append(tau)
    
    @property
    def tau_mean(self) -> float:
        return self._tau_sum / max(self._tau_count, 1) if self._tau_count > 0 else 16.0
    
    @property
    def tau_std(self) -> float:
        if self._tau_count < 2:
            return 5.0
        mean = self.tau_mean
        variance = (self._tau_sum_sq / self._tau_count) - (mean * mean)
        return math.sqrt(max(0, variance))
    
    @property
    def vmmp_tau_min(self) -> float:
        recent = self._tau_recent.to_list()
        if len(recent) < 20:
            return self._COLD_START['tau_min']
        recent.sort()
        idx = max(0, int(len(recent) * 0.1))
        return recent[idx]
    
    @property
    def vmmp_tau_max(self) -> float:
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
        return 0.7 + self.traits.get('stability', 0.5) * 0.25
    
    @property
    def hormone_rate(self) -> float:
        energy = max(0.1, self.energy)
        experience_factor = 1.0 / (1.0 + self.experience * 0.001)
        return (0.01 + energy * 0.09) * experience_factor
    
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
        return max(0.03, min(0.5, base * energy_factor * experience_factor * history_factor))
    
    @property
    def adrenaline_decay(self) -> float:
        return 0.9 + self.traits.get('stability', 0.5) * 0.08
    
    @property
    def sleep_pressure(self) -> float:
        pressure = 0.0
        pressure += (1.0 - self.energy) * 0.4
        pressure += self._hormones.get('melatonin', 0.2) * 0.3
        unprocessed = min(1.0, self.experience / max(self.dialog_count, 1))
        pressure += unprocessed * 0.2
        if self.tau_std > 0:
            pressure += min(1.0, self.tau_std / 20.0) * 0.1
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
            dispersion_scale = 30.0 if dispersion > 20 else 20.0 if dispersion > 10 else 10.0
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
        return base_cost * scale_factor * (1.0 + fatigue * 0.5)
    
    # ═══════════════════════════════════════════════════
    #   ВММП-ФИЛЬТР
    # ═══════════════════════════════════════════════════
    
    def _passes_vmmp_filter(self, mode) -> bool:
        tau = getattr(mode, 'tau', 0)
        scale = getattr(mode, 'scale', 1.0)
        amplitude = getattr(mode, 'amplitude', 0.5)
        
        if scale >= 20.0 or amplitude >= 0.7:
            return True
        if self.vmmp_tau_min <= tau <= self.vmmp_tau_max:
            return True
        if (tau < self.vmmp_tau_min or tau > self.vmmp_tau_max) and scale >= 10.0 and amplitude >= 0.6:
            return True
        return False
    
    # ═══════════════════════════════════════════════════
    #   РАБОТА С ПОЛЕМ
    # ═══════════════════════════════════════════════════
    
    def add_to_h_field(self, mode) -> None:
        with self._field_lock:
            # Сохраняем текст в TextStore
            content = getattr(mode, 'content', '') or getattr(mode, '_content', '')
            if content and not getattr(mode, 'text_id', None):
                mode.text_id = self.text_store.store(content)
                if hasattr(mode, '_content'):
                    mode._content = None
            
            # Создаём спектр
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
            
            # Устанавливаем scale
            if not hasattr(mode, 'scale') or mode.scale is None:
                content_len = self.text_store.get_size(getattr(mode, 'text_id', '')) if getattr(mode, 'text_id', None) else len(content)
                if content_len > 500:
                    mode.scale = 30.0
                elif content_len > 100:
                    mode.scale = 15.0
                else:
                    mode.scale = 5.0
            
            # Адаптируем mode для FieldV2 (нужен .id)
            if not hasattr(mode, 'id'):
                mode.id = getattr(mode, 'trace_id', None) or getattr(mode, 'text_id', None) or hashlib.md5(
                    str(getattr(mode, 'tau', 0)).encode()
                ).hexdigest()[:8]
            
            # Добавляем в поле
            self.field.add_mode(mode)
            
            # Очищаем спектр из RAM
            if hasattr(mode, 'tau_spectrum') and mode.tau_spectrum is not None:
                mode.tau_spectrum = None
            
            # Инкрементальная статистика
            self._collect_tau_incremental(getattr(mode, 'tau', 0))
            
            self._prune_field()
    
    def _prune_field(self):
        max_modes_per_layer = 500
        for layer_id in range(1, 5):
            layer = self.field.layers.get(layer_id)
            if not layer or not hasattr(layer, 'modes'):
                continue
            excess = len(layer.modes) - max_modes_per_layer
            if excess > 0:
                for _ in range(excess):
                    if layer.modes:
                        first_key = next(iter(layer.modes))
                        del layer.modes[first_key]
                if hasattr(self.field, 'stats'):
                    self.field.stats['total_modes'] = max(0, self.field.stats.get('total_modes', 0) - excess)
    
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
        return 'joy' if self.mood > 0.3 else 'stress' if self.mood < -0.3 else 'neutral'
    
    def _update_hormones(self, sentiment: float):
        rate = self.hormone_rate
        self._hormones['dopamine'] += (max(0, sentiment) - self._hormones['dopamine']) * rate
        self._hormones['cortisol'] += (max(0, -sentiment) * 1.5 - self._hormones['cortisol']) * rate
        hour_angle = (self.dialog_count % 24) / 24.0 * 2 * math.pi
        target_m = 0.3 + 0.4 * math.sin(hour_angle)
        self._hormones['melatonin'] += (target_m - self._hormones['melatonin']) * rate * 0.3
        surprise = abs(sentiment - self.mood)
        if surprise > 0.5:
            self._hormones['adrenaline'] = min(1.0, surprise * 1.5)
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
            amplitude=0.5, frequency=0.1, phase=0.0,
            base_emotion=self._get_emotional_tag()
        )
        
        with self._field_lock:
            try:
                results = self.field.find_by_resonance(
                    query_tau=question_tau, query_scale=preferred_scale,
                    query_phase=0.0, query_emotion=query_emotion,
                    query_spectrum=question_spectrum, k=10,
                    use_priority_bonus=True, early_exit=True
                )
            except TypeError:
                results = self.field.find_by_resonance(
                    query_tau=question_tau, query_scale=preferred_scale,
                    query_phase=0.0, query_emotion=query_emotion,
                    query_spectrum=question_spectrum, k=10,
                    use_priority_bonus=True
                )
        
        if not results:
            return None, 0.0, "no_resonance"
        
        mode_id, resonance, layer, details = results[0]
        
        with self._field_lock:
            best_mode = self.field.get_mode(mode_id)
        
        if not best_mode or not self._passes_vmmp_filter(best_mode):
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
        return (pos - neg) / (pos + neg) if pos + neg > 0 else 0.0
    
    def _update_mood(self, sentiment: float):
        inertia = self.mood_inertia
        self.mood = self.mood * inertia + sentiment * (1.0 - inertia)
        self.mood = max(-1.0, min(1.0, self.mood))
        self.mood_history.append(self.mood)
        self._update_hormones(sentiment)
        if hasattr(self._current_emotion, 'update'):
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
            full_content = self.text_store.get(text_id) if text_id else getattr(best_mode, 'content', '')
            answer = full_content[:800] if full_content else ''
            
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
                "mode_type": source,
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
            answer = "zzz... *поле видит сон* ...zzz" if self._sleeping else "Интересно... Расскажи подробнее."
            response = {
                "answer": answer,
                "mode_type": "fallback",
                "resonance": 0.0,
                "energy_cost": energy_cost,
                "mood": self.mood,
                "dialog_count": self.dialog_count,
                "sleeping": self._sleeping,
            }
        
        self.energy = min(1.0, self.energy + (0.002 if self._sleeping else 0.001))
        
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
        if len(user_history) >= 50:
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
            users_with_ts = sorted(
                [(u, h[-1].get('timestamp', 0) if h else 0) for u, h in self.dialog_history.items()],
                key=lambda x: x[1]
            )
            for u, _ in users_with_ts[:len(users_with_ts)//2]:
                del self.dialog_history[u]
        
        return response
    
    def _adapt_cache_size(self):
        if len(self._cache_hit_window) < 50:
            return
        hit_rate = sum(self._cache_hit_window[-100:]) / 100
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
        self._background_thread = threading.Thread(target=self._living_loop, args=(interval,), daemon=True)
        self._background_thread.start()
        print("🌿 Фоновый рост запущен (с авто-сном)")
    
    def stop_living(self):
        self._background_running = False
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=2.0)
        print("🛑 Фоновый рост остановлен")
    
    def force_sleep(self):
        self._sleeping = True
        self._hormones['melatonin'] = 0.9
        print("😴 Поле принудительно усыплено")
    
    def force_wake(self):
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
                
                pressure = self.sleep_pressure
                
                if pressure > 0.7 and not self._sleeping:
                    self._sleeping = True
                    print(f"😴 Поле засыпает (давление сна: {pressure:.2f})")
                
                if self._sleeping:
                    self.energy = min(1.0, self.energy + 0.005)
                    self._hormones['melatonin'] *= 0.995
                    self._hormones['cortisol'] *= 0.99
                    
                    if cycle % 120 == 0:
                        with self._field_lock:
                            dynamics = self.field.step_cross_layer_dynamics(dt=interval * 120)
                        if dynamics.get('emerged'):
                            print(f"💤 Сон: эмерджентные моды {dynamics['emerged']}")
                    
                    if self.energy > 0.85 and self._hormones['melatonin'] < 0.15:
                        self._sleeping = False
                        self.experience = 0
                        print(f"☀️ Поле проснулось (энергия: {self.energy:.2f})")
                    
                    if cycle % 600 == 0:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💤 Сон: E={self.energy:.2f} M={self._hormones['melatonin']:.2f}")
                else:
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
            self.traits[trait] = max(0.2, min(0.9, self.traits[trait] + random.uniform(-0.002, 0.002)))
    
    def _print_status(self):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🌱 Статус v21.2:")
        print(f"   Диалогов: {self.dialog_count} | Опыт: {self.experience}")
        print(f"   Мод: {self.field.stats.get('total_modes', '?')}")
        print(f"   Настроение: {self.mood:+.2f} | Энергия: {self.energy:.2f}")
        print(f"   VMMP tau: [{self.vmmp_tau_min:.1f}, {self.vmmp_tau_max:.1f}]")
        print(f"   Порог резонанса: {self.resonance_threshold:.3f}")
        print(f"   Давление сна: {self.sleep_pressure:.2f}")
    
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
Состояние: {'💤 Сон' if self._sleeping else '🌱 Бодрствование'}

Настроение: {self.mood:+.2f} | Энергия: {self.energy:.2f}
Давление сна: {self.sleep_pressure:.2f}
Гормоны: Д={self._hormones['dopamine']:.2f} К={self._hormones['cortisol']:.2f} М={self._hormones['melatonin']:.2f} А={self._hormones['adrenaline']:.2f}

Черты: {', '.join(f'{k}={v:.2f}' for k, v in self.traits.items())}

Адаптивные коэффициенты:
  VMMP tau: [{self.vmmp_tau_min:.1f}, {self.vmmp_tau_max:.1f}] (μ={self.tau_mean:.1f}, σ={self.tau_std:.1f})
  Инерция настроения: {self.mood_inertia:.3f}
  Порог резонанса: {self.resonance_threshold:.3f}

Поле: {self.field.stats.get('total_modes', '?')} мод
TextStore: {ts_stats['total_texts']} текстов, {ts_stats['total_size_mb']} МБ
"""
    
    # ═══════════════════════════════════════════════════
    #   СОХРАНЕНИЕ И ЗАГРУЗКА
    # ═══════════════════════════════════════════════════
    
    def save(self, filepath: str):
        with self._field_lock:
            all_modes = self.get_all_modes()
        
        data = {
            'id': self.id, 'name': self.name, 'h_field': [],
            'vortices': getattr(self, 'vortices', []),
            'focus': self.focus,
            'mood': self.mood, 'energy': self.energy,
            'experience': self.experience, 'generation': self.generation,
            'traits': self.traits, 'dialog_count': self.dialog_count,
            'version': 'v21.2',
            'text_store_path': self.text_store.store_path,
            'sleeping': self._sleeping,
        }
        
        for mode in all_modes:
            text_id = getattr(mode, 'text_id', None)
            content = self.text_store.get(text_id) if text_id else getattr(mode, 'content', '')
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
        
        instance = cls(
            id=data.get('id', 'loaded'),
            name=data.get('name', 'Загруженная v21'),
            text_store_path=data.get('text_store_path')
        )
        
        for attr in ['focus', 'mood', 'energy', 'experience', 'generation', 'dialog_count']:
            if attr in data:
                setattr(instance, attr, data[attr])
        
        if 'traits' in data:
            instance.traits.update(data['traits'])
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
                trace_id=mode_data.get('trace_id', hashlib.md5(content.encode() if content else b'').hexdigest()[:8]),
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
    print("Тестирование Living Personality v21.2 (чистая)")
    print("=" * 60)
    
    lp = LivingPersonality(id="test_v21_clean", name="Тест v21.2 clean")
    
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
        lp.add_to_h_field(mode)
    
    print(f"\n📊 Адаптивные коэффициенты:")
    print(f"   VMMP tau: [{lp.vmmp_tau_min:.1f}, {lp.vmmp_tau_max:.1f}]")
    print(f"   Средний tau: {lp.tau_mean:.1f} ± {lp.tau_std:.1f}")
    print(f"   Порог резонанса: {lp.resonance_threshold:.3f}")
    print(f"   Давление сна: {lp.sleep_pressure:.2f}")
    
    for q in ["Что такое TEES?", "Расскажи про гравитацию"]:
        result = lp.process(q)
        print(f"\nQ: {q}")
        print(f"A: {result['answer'][:100]}...")
        print(f"   Резонанс: {result['resonance']:.2f} | Спит: {result['sleeping']}")
    
    # Тест сохранения
    lp.save("/tmp/test_v21_clean.json")
    loaded = LivingPersonality.load("/tmp/test_v21_clean.json")
    print(f"\n✅ Загружено мод: {len(loaded.h_field)}")
    
    print("\n" + "=" * 60)
    print("✅ Тест v21.2 clean пройден")
    print("=" * 60)