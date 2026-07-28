"""
TEESRouter v1.3 — TRIPLE-LAYER HUB (Усилитель + Кэш + Гомеостаз)
====================================================================
Новое в v1.3:
  - Усилитель Хаба с динамическим gain (до 3× при хорошем резонансе)
  - Кэш маршрутов на 500+ записей (мгновенные повторы)
  - 7 эпох для наблюдения гомеостаза
  - Адаптивный порог успеха (растёт с эпохами)
  - Умное усиление поля вдоль успешных маршрутов
"""

import numpy as np
import time
import logging
import gc
import psutil
import os
from typing import Tuple, List, Dict, Optional, Any
from collections import OrderedDict
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

try:
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    prange = range

logger = logging.getLogger("TEES_Hub_Pro")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


# ===========================================================================
# JIT-функции (без изменений)
# ===========================================================================

@jit(nopython=True, cache=True, fastmath=True)
def generate_path_points_batch(starts: np.ndarray, ends: np.ndarray, 
                               max_points: int) -> np.ndarray:
    M = starts.shape[0]
    paths = np.zeros((M, max_points, 3), dtype=np.float64)
    
    for i in range(M):
        dist = np.sqrt(np.sum((ends[i] - starts[i]) ** 2))
        num_points = max(1, int(dist * 10))
        direction = ends[i] - starts[i]
        
        for j in range(min(num_points, max_points)):
            t = j / (num_points - 1) if num_points > 1 else 0.0
            paths[i, j] = starts[i] + t * direction
    
    return paths


@jit(nopython=True, parallel=True, cache=True, fastmath=True)
def interpolate_batch_paths(paths: np.ndarray, field: np.ndarray, 
                           field_size: int) -> np.ndarray:
    M = paths.shape[0]
    max_points = paths.shape[1]
    result = np.zeros((M, max_points), dtype=np.complex128)
    
    for i in prange(M):
        for j in range(max_points):
            x, y, z = paths[i, j, 0], paths[i, j, 1], paths[i, j, 2]
            
            if x == 0.0 and y == 0.0 and z == 0.0:
                continue
            
            x0 = int(np.floor(x))
            y0 = int(np.floor(y))
            z0 = int(np.floor(z))
            
            if (0 <= x0 < field_size - 1 and 
                0 <= y0 < field_size - 1 and 
                0 <= z0 < field_size - 1):
                
                fx, fy, fz = x - x0, y - y0, z - z0
                
                c000 = field[x0, y0, z0]
                c100 = field[x0 + 1, y0, z0]
                c010 = field[x0, y0 + 1, z0]
                c110 = field[x0 + 1, y0 + 1, z0]
                c001 = field[x0, y0, z0 + 1]
                c101 = field[x0 + 1, y0, z0 + 1]
                c011 = field[x0, y0 + 1, z0 + 1]
                c111 = field[x0 + 1, y0 + 1, z0 + 1]
                
                c00 = c000 * (1 - fx) + c100 * fx
                c01 = c001 * (1 - fx) + c101 * fx
                c10 = c010 * (1 - fx) + c110 * fx
                c11 = c011 * (1 - fx) + c111 * fx
                
                c0 = c00 * (1 - fy) + c10 * fy
                c1 = c01 * (1 - fy) + c11 * fy
                
                result[i, j] = c0 * (1 - fz) + c1 * fz
    
    return result


@jit(nopython=True, parallel=True, cache=True, fastmath=True)
def compute_qualities_batch(field_vals: np.ndarray, segments: np.ndarray) -> np.ndarray:
    M = field_vals.shape[0]
    qualities = np.zeros(M, dtype=np.float64)
    
    for i in prange(M):
        seg = segments[i]
        if seg == 0:
            continue
        
        total_phase = 0.0
        total_strength = 0.0
        
        for j in range(seg):
            val = field_vals[i, j]
            total_phase += np.angle(val)
            total_strength += np.abs(val)
        
        avg_phase = total_phase / seg
        avg_strength = total_strength / seg
        phase_quality = np.abs(np.cos(avg_phase))
        qualities[i] = min(1.0, phase_quality * avg_strength)
    
    return qualities


# ===========================================================================
class RouteCache:
    """Кэш маршрутов с учётом частоты использования."""
    
    def __init__(self, max_size: int = 500):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, start_key: tuple, end_key: tuple) -> Optional[float]:
        key = (start_key, end_key)
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, start_key: tuple, end_key: tuple, quality: float):
        key = (start_key, end_key)
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        self.cache[key] = quality
    
    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# ===========================================================================
class TEES_Layer:
    """TEES-слой с усилением поля."""
    
    BASE_COUPLING = np.array([
        0.259921, 0.442249, 0.709975, 0.912931, 0.148693, 0.307107, 0.518294, 0.651839,
        0.822315, 0.959920, 0.089322, 0.209579, 0.330643, 0.446273, 0.551831, 0.657378,
        0.761885, 0.867051, 0.975174, 0.075541, 0.183840, 0.286918, 0.393314, 0.497253,
        0.604512, 0.706761, 0.812413, 0.915046, 0.015973, 0.116299, 0.218563, 0.316947,
    ], dtype=np.float64)

    def __init__(self, name: str, field_size: int = 32, seed: int = 42):
        self.name = name
        self.field_size = field_size
        self.field = np.zeros((field_size, field_size, field_size), dtype=np.complex128)
        self._initialize_field(seed)
        
        self.micro_batch_size = 100
        self.field_reinforcements = 0
        
        logger.info(f"Слой '{self.name}': {self.field.size} ячеек")

    def _initialize_field(self, seed: int):
        rng = np.random.RandomState(seed)
        x = np.linspace(0, 4 * np.pi, self.field_size)
        y = np.linspace(0, 4 * np.pi, self.field_size)
        z = np.linspace(0, 4 * np.pi, self.field_size)
        X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
        
        base = (np.sin(X) * np.cos(Y) + np.sin(Y) * np.cos(Z) + np.sin(Z) * np.cos(X))
        
        k_vals = self._get_k_bands(0.5)
        for i, k in enumerate(k_vals[:8]):
            phase_shift = rng.uniform(0, 2 * np.pi)
            base += 0.1 * np.sin(X * k + phase_shift) * np.cos(Y * k) * np.sin(Z * k)
        
        noise = rng.normal(0, 0.1, (self.field_size, self.field_size, self.field_size))
        self.field = base + 1j * noise

    def _get_k_bands(self, complexity: float) -> np.ndarray:
        if complexity < 0.3:
            num = 4
        elif complexity < 0.6:
            num = 16
        else:
            num = 32
        x_orig = np.linspace(0, 1, 32)
        x_new = np.linspace(0, 1, num)
        return np.interp(x_new, x_orig, self.BASE_COUPLING)

    def reinforce_field(self, path: np.ndarray, boost_strength: float):
        """Усиление поля вдоль успешного маршрута."""
        if boost_strength <= 0:
            return
        
        for point in path:
            x0 = int(np.floor(point[0]))
            y0 = int(np.floor(point[1]))
            z0 = int(np.floor(point[2]))
            
            if (0 <= x0 < self.field_size - 1 and 
                0 <= y0 < self.field_size - 1 and 
                0 <= z0 < self.field_size - 1):
                
                # Когерентное усиление (сохраняем фазу)
                current_val = self.field[x0, y0, z0]
                phase = np.angle(current_val)
                boost = boost_strength * 0.1 * np.exp(1j * phase)
                self.field[x0, y0, z0] += boost
                self.field_reinforcements += 1

    def batch_resonance_quality_fast(self, starts: np.ndarray, ends: np.ndarray,
                                    sub_res: int = 10) -> np.ndarray:
        M = len(starts)
        if M == 0:
            return np.array([])
        
        qualities = np.zeros(M, dtype=np.float64)
        
        diffs = ends - starts
        dists = np.sqrt(np.sum(diffs ** 2, axis=1))
        max_segments = max(1, int(np.max(dists) * sub_res))
        
        for start_idx in range(0, M, self.micro_batch_size):
            end_idx = min(start_idx + self.micro_batch_size, M)
            mb_size = end_idx - start_idx
            
            mb_starts = starts[start_idx:end_idx]
            mb_ends = ends[start_idx:end_idx]
            
            paths = generate_path_points_batch(mb_starts, mb_ends, max_segments)
            field_vals = interpolate_batch_paths(paths, self.field, self.field_size)
            
            mb_segments = np.maximum(1, (dists[start_idx:end_idx] * sub_res).astype(np.int32))
            mb_qualities = compute_qualities_batch(field_vals, mb_segments)
            
            qualities[start_idx:end_idx] = mb_qualities
            
            if start_idx % (self.micro_batch_size * 100) == 0:
                gc.collect()
        
        return qualities


# ===========================================================================
class TEES_TripleHub:
    """Трёхслойный TEES с УСИЛИТЕЛЕМ, КЭШЕМ и ГОМЕОСТАЗОМ."""
    
    def __init__(self, field_size: int = 32, cache_size: int = 500):
        available_memory_gb = psutil.virtual_memory().available / 1e9
        logger.info(f"Доступно памяти: {available_memory_gb:.1f} GB")
        
        self.top = TEES_Layer("ВЕРХ", field_size, seed=42)
        self.hub = TEES_Layer("ЦЕНТР-ХАБ", field_size, seed=123)
        self.bot = TEES_Layer("НИЗ", field_size, seed=789)
        
        # Термальный гомеостаз
        self.chip_temp = 30.0
        self.entropy_balance = 0.0
        self.homeostasis_quality = 0.0
        
        # УСИЛИТЕЛЬ ХАБА
        self.base_gain = 1.5        # Базовое усиление
        self.max_gain = 3.0         # Максимальное усиление при идеальном резонансе
        self.gain_boost_rate = 0.1  # Скорость роста усиления с эпохами
        
        # КЭШ МАРШРУТОВ
        self.route_cache = RouteCache(max_size=cache_size)
        
        # Адаптивный порог успеха
        self.success_threshold = 0.6  # Начальный порог (будет расти)
        self.threshold_growth = 0.02  # Рост порога за эпоху
        
        # Параметры микробатчей
        self.cross_micro_batch = 200
        
        # История для анализа гомеостаза
        self.history = {
            'top_quality': [],
            'bot_quality': [],
            'cross_quality': [],
            'temperature': [],
            'cache_hit_rate': [],
            'gain_used': []
        }
        
        logger.info(f"🚀 УСИЛИТЕЛЬ ХАБА: gain {self.base_gain:.1f}× → {self.max_gain:.1f}×")
        logger.info(f"💾 КЭШ МАРШРУТОВ: {cache_size} записей")
        logger.info(f"🎯 ПОРОГ УСПЕХА: {self.success_threshold:.0%} → растёт с эпохами")

    def _calculate_dynamic_gain(self, hub_quality: float, epoch: int) -> float:
        """
        Динамический усилитель Хаба.
        Чем лучше резонанс в хабе и чем старше эпоха — тем сильнее усиление.
        """
        # Базовое усиление растёт с эпохами
        epoch_bonus = min(1.0, epoch * self.gain_boost_rate)
        current_max_gain = self.base_gain + (self.max_gain - self.base_gain) * epoch_bonus
        
        # Качество хаба модулирует усиление
        quality_factor = (hub_quality - 0.3) / 0.7  # Нормализация от 0.3 до 1.0
        quality_factor = np.clip(quality_factor, 0.0, 1.0)
        
        # Итоговый gain
        gain = 1.0 + (current_max_gain - 1.0) * quality_factor
        
        return np.clip(gain, 1.0, self.max_gain)

    def _check_memory(self, threshold_gb: float = 0.3):
        available_gb = psutil.virtual_memory().available / 1e9
        if available_gb < threshold_gb:
            logger.warning(f"⚠️  Мало памяти: {available_gb:.2f} GB. Очистка...")
            self.route_cache.clear()
            gc.collect()
            return True
        return False

    def generate_dual_topology(self, n_qubits: int) -> Tuple[Dict, Dict, List, List, List]:
        rng = np.random.RandomState(42)
        half = n_qubits // 2
        size = self.top.field_size - 1
        
        pos_top = {}
        pos_bot = {}
        
        for i in range(half):
            pos_top[i] = np.array([
                rng.uniform(0, size),
                rng.uniform(0, size),
                rng.uniform(0, size)
            ], dtype=np.float32)
            pos_bot[i] = np.array([
                rng.uniform(0, size),
                rng.uniform(0, size),
                rng.uniform(0, size)
            ], dtype=np.float32)
        
        density_top = min(0.05, 500 / max(1, half))
        density_bot = min(0.05, 500 / max(1, half))
        density_cross = min(0.02, 200 / max(1, half))
        
        edges_top = [(i, j) for i in range(half) for j in range(i+1, half) 
                    if rng.random() < density_top]
        edges_bot = [(i, j) for i in range(half) for j in range(i+1, half) 
                    if rng.random() < density_bot]
        edges_cross = [(i, j) for i in range(half) for j in range(half) 
                      if rng.random() < density_cross]
        
        logger.info(f"Топология: ВЕРХ={len(pos_top)}q/{len(edges_top)}e, "
                   f"НИЗ={len(pos_bot)}q/{len(edges_bot)}e, "
                   f"КРОСС={len(edges_cross)}e")
        
        return pos_top, pos_bot, edges_top, edges_bot, edges_cross

    def route_cross_with_amplifier(self, pos_top: Dict, pos_bot: Dict,
                                   edges_cross: List[Tuple[int, int]], 
                                   epoch: int) -> np.ndarray:
        """
        Кросс-маршрутизация с УСИЛИТЕЛЕМ ХАБА и КЭШЕМ.
        """
        M = len(edges_cross)
        if M == 0:
            return np.array([])
        
        qualities = np.zeros(M, dtype=np.float64)
        center = np.array([self.top.field_size / 2] * 3, dtype=np.float64)
        
        total_gain_used = 0.0
        cache_hits_this_epoch = 0
        
        for start_idx in range(0, M, self.cross_micro_batch):
            end_idx = min(start_idx + self.cross_micro_batch, M)
            mb_size = end_idx - start_idx
            
            # Подготовка микробатча
            mb_top_starts = np.zeros((mb_size, 3), dtype=np.float64)
            mb_bot_ends = np.zeros((mb_size, 3), dtype=np.float64)
            
            for i, idx in enumerate(range(start_idx, end_idx)):
                top_idx, bot_idx = edges_cross[idx]
                mb_top_starts[i] = pos_top[top_idx]
                mb_bot_ends[i] = pos_bot[bot_idx]
            
            # Проверяем КЭШ для каждой пары
            cached_mask = np.zeros(mb_size, dtype=bool)
            for i in range(mb_size):
                start_key = tuple(mb_top_starts[i].round(4))
                end_key = tuple(mb_bot_ends[i].round(4))
                cached_quality = self.route_cache.get(start_key, end_key)
                
                if cached_quality is not None:
                    qualities[start_idx + i] = cached_quality
                    cached_mask[i] = True
                    cache_hits_this_epoch += 1
            
            # Точки входа/выхода для НЕкэшированных
            hub_entries = center + np.random.uniform(-2, 2, (mb_size, 3))
            hub_exits = 2 * center - hub_entries
            
            # Этап 1: ВЕРХ -> Хаб
            q1 = self.top.batch_resonance_quality_fast(mb_top_starts, hub_entries, sub_res=8)
            
            # Этап 2: Внутри ХАБА (ключевой этап для усиления!)
            q2 = self.hub.batch_resonance_quality_fast(hub_entries, hub_exits, sub_res=10)
            
            # ДИНАМИЧЕСКИЙ УСИЛИТЕЛЬ
            gains = np.array([self._calculate_dynamic_gain(q2[i], epoch) 
                            for i in range(mb_size)])
            total_gain_used += np.mean(gains)
            
            # УСИЛЕНИЕ поля хаба для успешных путей
            for i in range(mb_size):
                if q2[i] > 0.5:  # Хороший резонанс в хабе
                    path_in_hub = np.vstack([
                        hub_entries[i],
                        (hub_entries[i] + hub_exits[i]) / 2,
                        hub_exits[i]
                    ])
                    self.hub.reinforce_field(path_in_hub, q2[i] * 0.05)
            
            # Этап 3: Хаб -> НИЗ
            q3 = self.bot.batch_resonance_quality_fast(hub_exits, mb_bot_ends, sub_res=8)
            
            # Итоговое качество с УСИЛЕНИЕМ
            for i in range(mb_size):
                if not cached_mask[i]:
                    q = np.clip(q1[i] * gains[i] * q3[i], 0.0, 1.0)
                    qualities[start_idx + i] = q
                    
                    # Кэшируем успешные маршруты
                    if q > self.success_threshold:
                        start_key = tuple(mb_top_starts[i].round(4))
                        end_key = tuple(mb_bot_ends[i].round(4))
                        self.route_cache.put(start_key, end_key, q)
                        
                        # Усиливаем поле вдоль всего пути
                        full_path = np.vstack([
                            mb_top_starts[i],
                            hub_entries[i],
                            hub_exits[i],
                            mb_bot_ends[i]
                        ])
                        for layer in [self.top, self.hub, self.bot]:
                            layer.reinforce_field(full_path, q * 0.03)
            
            if start_idx % (self.cross_micro_batch * 50) == 0:
                self._check_memory()
        
        return qualities

    def run_homeostasis_test(self, n_qubits: int = 5000, epochs: int = 7):
        """Тест с наблюдением гомеостаза (7 эпох)."""
        logger.info(f"\n{'='*70}")
        logger.info(f"🧬 ТЕСТ ГОМЕОСТАЗА v1.3: {n_qubits} КУБИТОВ, {epochs} ЭПОХ")
        logger.info(f"{'='*70}")
        
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1e9
        logger.info(f"Начальная память: {initial_memory:.2f} GB")
        
        pos_top, pos_bot, edges_top, edges_bot, edges_cross = \
            self.generate_dual_topology(n_qubits)
        
        total_start = time.time()
        
        for epoch in range(epochs):
            epoch_start = time.time()
            
            # РАСТУЩИЙ ПОРОГ УСПЕХА
            self.success_threshold = min(0.85, 0.6 + epoch * self.threshold_growth)
            
            # Подготовка массивов
            top_starts = np.array([pos_top[u] for u, _ in edges_top], dtype=np.float64)
            top_ends = np.array([pos_top[v] for _, v in edges_top], dtype=np.float64)
            bot_starts = np.array([pos_bot[u] for u, _ in edges_bot], dtype=np.float64)
            bot_ends = np.array([pos_bot[v] for _, v in edges_bot], dtype=np.float64)
            
            # Обработка слоёв
            q_top = self.top.batch_resonance_quality_fast(top_starts, top_ends)
            del top_starts, top_ends
            gc.collect()
            
            q_bot = self.bot.batch_resonance_quality_fast(bot_starts, bot_ends)
            del bot_starts, bot_ends
            gc.collect()
            
            # Кросс-связи с УСИЛИТЕЛЕМ и КЭШЕМ
            q_cross = self.route_cross_with_amplifier(pos_top, pos_bot, edges_cross, epoch)
            gc.collect()
            
            epoch_time = time.time() - epoch_start
            
            # Статистика
            top_success = np.sum(q_top > self.success_threshold)
            bot_success = np.sum(q_bot > self.success_threshold)
            cross_success = np.sum(q_cross > self.success_threshold)
            
            top_avg = np.mean(q_top) if len(q_top) > 0 else 0
            bot_avg = np.mean(q_bot) if len(q_bot) > 0 else 0
            cross_avg = np.mean(q_cross) if len(q_cross) > 0 else 0
            
            # Сохраняем историю
            self.history['top_quality'].append(top_avg)
            self.history['bot_quality'].append(bot_avg)
            self.history['cross_quality'].append(cross_avg)
            self.history['temperature'].append(self.chip_temp)
            self.history['cache_hit_rate'].append(self.route_cache.hit_rate())
            
            memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1e9
            
            # Обновление гомеостаза
            self._update_homeostasis(top_avg, bot_avg, cross_avg)
            
            logger.info(f"  Эпоха {epoch+1}/{epochs} [порог {self.success_threshold:.0%}]:")
            logger.info(f"    ВЕРХ: {top_success}/{len(edges_top)} ({top_success/max(1,len(edges_top)):.1%}) avg={top_avg:.3f}")
            logger.info(f"    НИЗ:  {bot_success}/{len(edges_bot)} ({bot_success/max(1,len(edges_bot)):.1%}) avg={bot_avg:.3f}")
            logger.info(f"    ХАБ:  {cross_success}/{len(edges_cross)} ({cross_success/max(1,len(edges_cross)):.1%}) avg={cross_avg:.3f} ⚡")
            logger.info(f"    Кэш: {self.route_cache.hit_rate():.0%} хитов | Память: {memory_usage:.2f}GB | Время: {epoch_time:.1f}с")
        
        total_time = time.time() - total_start
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1e9
        
        # АНАЛИЗ ГОМЕОСТАЗА
        self._print_homeostasis_report(total_time, initial_memory, final_memory, epochs)

    def _update_homeostasis(self, top_q: float, bot_q: float, cross_q: float):
        """Обновление гомеостаза системы."""
        avg_quality = (top_q + bot_q + cross_q) / 3
        
        # Термальный баланс
        coherence = avg_quality ** 2
        heat = (1.0 - coherence) * 30.0
        cooling = min(50.0, heat * 1.5)
        self.chip_temp += (heat - cooling) * 0.1
        self.chip_temp = np.clip(self.chip_temp, 20.0, 80.0)
        
        # Энтропийный баланс
        self.entropy_balance += (1.0 - coherence) * 0.1
        self.entropy_balance = np.clip(self.entropy_balance, 0.0, 10.0)
        
        # Качество гомеостаза (стабильность)
        self.homeostasis_quality = coherence * (1.0 - abs(50.0 - self.chip_temp) / 50.0)

    def _print_homeostasis_report(self, total_time: float, initial_mem: float, 
                                  final_mem: float, epochs: int):
        """Отчёт о гомеостазе."""
        logger.info(f"\n{'='*70}")
        logger.info(f"🧬 ОТЧЁТ ГОМЕОСТАЗА v1.3")
        logger.info(f"{'='*70}")
        logger.info(f"⏱️  Общее время: {total_time:.1f} сек ({total_time/epochs:.1f} сек/эпоха)")
        logger.info(f"💾 Память: {initial_mem:.2f}GB → {final_mem:.2f}GB (Δ{final_mem-initial_mem:+.2f}GB)")
        logger.info(f"🌡️  Температура чипа: {self.chip_temp:.1f}°C")
        logger.info(f"🌀 Энтропийный баланс: {self.entropy_balance:.2f}")
        logger.info(f"✨ Качество гомеостаза: {self.homeostasis_quality:.3f}")
        
        # Тренды качества
        if len(self.history['cross_quality']) >= 2:
            cross_trend = self.history['cross_quality'][-1] - self.history['cross_quality'][0]
            logger.info(f"📈 Тренд ХАБ: {cross_trend:+.3f} (эпоха 1 → {epochs})")
        
        logger.info(f"💾 Кэш хитов всего: {self.route_cache.hits}")
        logger.info(f"🔧 Усилений поля: TOP={self.top.field_reinforcements}, "
                   f"HUB={self.hub.field_reinforcements}, BOT={self.bot.field_reinforcements}")
        
        # График гомеостаза (ASCII)
        logger.info(f"\n📊 ДИНАМИКА ГОМЕОСТАЗА:")
        logger.info(f"{'Эпоха':<8} {'Темп-ра':<10} {'ХАБ кач-во':<12} {'Кэш хиты':<12}")
        logger.info(f"{'-'*42}")
        for e in range(epochs):
            temp = self.history['temperature'][e]
            cross_q = self.history['cross_quality'][e]
            cache_hr = self.history['cache_hit_rate'][e]
            
            temp_bar = '🔥' * int(temp / 10) + '❄️' * (5 - int(temp / 10))
            logger.info(f"{e+1:<8} {temp:.1f}°C {temp_bar:<12} {cross_q:.3f}        {cache_hr:.0%}")
        
        logger.info(f"{'='*70}")
        logger.info(f"✅ ГОМЕОСТАЗ ДОСТИГНУТ" if self.homeostasis_quality > 0.7 
                   else f"⚠️  ГОМЕОСТАЗ НЕСТАБИЛЕН (качество {self.homeostasis_quality:.3f})")


def battle_test_5000_pro():
    """Боевой тест v1.3 на 5000 кубитов с 7 эпохами."""
    logger.info("\n" + "=" * 70)
    logger.info("🧬 БОЕВОЙ ТЕСТ v1.3: 5000 КУБИТОВ × 7 ЭПОХ")
    logger.info("=" * 70)
    
    hub = TEES_TripleHub(field_size=32, cache_size=500)
    hub.run_homeostasis_test(n_qubits=5000, epochs=7)


if __name__ == "__main__":
    os.environ['OMP_NUM_THREADS'] = str(os.cpu_count())
    if NUMBA_AVAILABLE:
        os.environ['NUMBA_NUM_THREADS'] = str(os.cpu_count())
    
    # Быстрый тест на 1000
    logger.info("🧪 ПРОВЕРОЧНЫЙ ПУСК v1.3: 1000 кубитов × 3 эпохи")
    hub = TEES_TripleHub(field_size=32, cache_size=300)
    hub.run_homeostasis_test(n_qubits=1000, epochs=3)
    
    # Основной тест
    battle_test_5000_pro()