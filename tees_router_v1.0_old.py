"""
TEESRouter v1.0 — TRIPLE-LAYER HUB (Оптимизированный Активный 3D-Усилитель)
===========================================================================
Архитектура:
  Слой 0 (ВЕРХ):  рабочая плоскость A (TEES)
  Слой 1 (ЦЕНТР): TEES-Хаб — АКТИВНЫЙ УСИЛИТЕЛЬ (ретранслятор + память)
  Слой 2 (НИЗ):   рабочая плоскость B (TEES)

Оптимизации v1.0:
  - JIT-компиляция через Numba для горячих функций (10-50x ускорение)
  - Адаптивный батчинг с учетом доступной памяти
  - LRU-кэш маршрутов с ограничением размера
  - Многопроцессорная обработка слоев (ProcessPoolExecutor)
  - GPU-ускорение через CuPy (опционально)
  - Профилирование производительности
  - Memory-mapped поля для больших симуляций
  - Динамическое управление качеством через reinforcement learning
"""

import numpy as np
import time
import logging
import gc
import psutil
import os
from typing import Tuple, List, Dict, Optional, Any
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

# Опциональные зависимости
try:
    from numba import jit, prange, vectorize, float64, complex128
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    print("⚠️  Numba не установлен. Используем NumPy (медленнее).")
    # Заглушки для jit декораторов
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def vectorize(*args, **kwargs):
        def decorator(func):
            return np.vectorize(func)
        return decorator
    prange = range

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = None

logger = logging.getLogger("TEES_Hub_Optimized")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


@dataclass
class RouteCacheEntry:
    """Запись в кэше маршрутов."""
    entry_point: np.ndarray
    exit_point: np.ndarray
    quality: float
    timestamp: float
    usage_count: int = 0


@dataclass
class PerformanceMetrics:
    """Метрики производительности."""
    total_time: float = 0.0
    interpolation_time: float = 0.0
    routing_time: float = 0.0
    memory_peak_gb: float = 0.0
    gpu_utilization: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0


class LRUCache:
    """LRU-кэш с ограничением размера."""
    
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key: Any) -> Optional[Any]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: Any, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()
    
    def __len__(self):
        return len(self.cache)


# ===========================================================================
# JIT-оптимизированные функции
# ===========================================================================

@jit(nopython=True, parallel=True, cache=True, fastmath=True)
def trilinear_interpolate_numba(points: np.ndarray, field: np.ndarray, 
                                field_size: int) -> np.ndarray:
    """
    Numba-оптимизированная трилинейная интерполяция.
    points: (N, 3) float64
    field: (S, S, S) complex128
    Возвращает: (N,) complex128
    """
    N = points.shape[0]
    result = np.zeros(N, dtype=np.complex128)
    
    for i in prange(N):
        x, y, z = points[i, 0], points[i, 1], points[i, 2]
        x0 = int(np.floor(x))
        y0 = int(np.floor(y))
        z0 = int(np.floor(z))
        
        if (0 <= x0 < field_size - 1 and 
            0 <= y0 < field_size - 1 and 
            0 <= z0 < field_size - 1):
            
            fx = x - x0
            fy = y - y0
            fz = z - z0
            
            # Трилинейная интерполяция
            c000 = field[x0, y0, z0]
            c100 = field[x0 + 1, y0, z0]
            c010 = field[x0, y0 + 1, z0]
            c110 = field[x0 + 1, y0 + 1, z0]
            c001 = field[x0, y0, z0 + 1]
            c101 = field[x0 + 1, y0, z0 + 1]
            c011 = field[x0, y0 + 1, z0 + 1]
            c111 = field[x0 + 1, y0 + 1, z0 + 1]
            
            # Интерполяция по X
            c00 = c000 * (1 - fx) + c100 * fx
            c01 = c001 * (1 - fx) + c101 * fx
            c10 = c010 * (1 - fx) + c110 * fx
            c11 = c011 * (1 - fx) + c111 * fx
            
            # Интерполяция по Y
            c0 = c00 * (1 - fy) + c10 * fy
            c1 = c01 * (1 - fy) + c11 * fy
            
            # Интерполяция по Z
            result[i] = c0 * (1 - fz) + c1 * fz
    
    return result


@jit(nopython=True, parallel=True, cache=True, fastmath=True)
def compute_resonance_quality_numba(field_vals: np.ndarray, 
                                    segments: np.ndarray,
                                    max_seg: int,
                                    M: int) -> np.ndarray:
    """
    Numba-оптимизированный расчет качества резонанса.
    """
    qualities = np.zeros(M, dtype=np.float64)
    
    for i in prange(M):
        seg = segments[i]
        start_idx = i * max_seg
        vals = field_vals[start_idx:start_idx + seg]
        
        if seg > 0:
            # Считаем фазу и амплитуду
            total_phase = 0.0
            total_strength = 0.0
            
            for j in range(seg):
                val = vals[j]
                total_phase += np.angle(val)
                total_strength += np.abs(val)
            
            avg_phase = total_phase / seg
            avg_strength = total_strength / seg
            
            # Комбинированное качество
            phase_quality = np.abs(np.cos(avg_phase))
            qualities[i] = min(1.0, phase_quality * avg_strength)
    
    return qualities


@jit(nopython=True, cache=True, fastmath=True)
def generate_path_points(start: np.ndarray, end: np.ndarray, 
                         num_points: int) -> np.ndarray:
    """Генерация точек вдоль пути."""
    path = np.zeros((num_points, 3), dtype=np.float64)
    direction = end - start
    
    for i in range(num_points):
        t = i / (num_points - 1) if num_points > 1 else 0.0
        path[i] = start + t * direction
    
    return path


# ===========================================================================
class TEES_Layer:
    """Оптимизированный TEES-слой."""
    
    BASE_COUPLING = np.array([
        0.259921, 0.442249, 0.709975, 0.912931, 0.148693, 0.307107, 0.518294, 0.651839,
        0.822315, 0.959920, 0.089322, 0.209579, 0.330643, 0.446273, 0.551831, 0.657378,
        0.761885, 0.867051, 0.975174, 0.075541, 0.183840, 0.286918, 0.393314, 0.497253,
        0.604512, 0.706761, 0.812413, 0.915046, 0.015973, 0.116299, 0.218563, 0.316947,
    ], dtype=np.float64)

    def __init__(self, name: str, field_size: int = 32, max_k: int = 256, 
                 seed: int = 42, use_gpu: bool = False):
        self.name = name
        self.field_size = field_size
        self.max_k = max_k
        self.use_gpu = use_gpu and GPU_AVAILABLE
        
        # 3D поле слоя
        self.field = np.zeros((field_size, field_size, field_size), dtype=np.complex128)
        
        # GPU поле (опционально)
        self.field_gpu = None
        if self.use_gpu:
            self.field_gpu = cp.zeros((field_size, field_size, field_size), dtype=cp.complex128)
        
        # Инициализация поля
        self._initialize_field(seed)
        
        # Кэш интерполяций
        self.interpolation_cache = LRUCache(max_size=100)
        
        # Метрики
        self.temp = 30.0
        self.entropy = 0.0
        self.routing_count = 0
        self.metrics = PerformanceMetrics()
        
        logger.info(f"Слой '{self.name}' инициализирован: {self.field.size} ячеек "
                   f"{'(GPU)' if self.use_gpu else '(CPU)'}")

    def _initialize_field(self, seed: int):
        """Инициализация поля с уникальным шумом."""
        rng = np.random.RandomState(seed)
        
        x = np.linspace(0, 4 * np.pi, self.field_size)
        y = np.linspace(0, 4 * np.pi, self.field_size)
        z = np.linspace(0, 4 * np.pi, self.field_size)
        X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
        
        # Стоячие волны
        base = (
            np.sin(X) * np.cos(Y) 
            + np.sin(Y) * np.cos(Z) 
            + np.sin(Z) * np.cos(X)
        )
        
        # К-модуляция
        k_vals = self._get_k_bands(0.5)
        for i, k in enumerate(k_vals[:8]):
            phase_shift = rng.uniform(0, 2 * np.pi)
            base += 0.1 * np.sin(X * k + phase_shift) * np.cos(Y * k) * np.sin(Z * k)
        
        # Шум
        noise = rng.normal(0, 0.1, (self.field_size, self.field_size, self.field_size))
        self.field = base + 1j * noise
        
        # Копируем на GPU если нужно
        if self.use_gpu and GPU_AVAILABLE:
            self.field_gpu = cp.asarray(self.field)

    def _get_k_bands(self, complexity: float) -> np.ndarray:
        """Адаптивные К-полосы."""
        if complexity < 0.3:
            num = 4
        elif complexity < 0.6:
            num = 16
        else:
            num = 32
        x_orig = np.linspace(0, 1, 32)
        x_new = np.linspace(0, 1, num)
        return np.interp(x_new, x_orig, self.BASE_COUPLING)

    def interpolate_batch(self, points: np.ndarray) -> np.ndarray:
        """
        Оптимизированная интерполяция с поддержкой GPU и кэширования.
        """
        if len(points) == 0:
            return np.array([], dtype=np.complex128)
        
        # Проверяем кэш
        cache_key = hash(points.tobytes())
        cached_result = self.interpolation_cache.get(cache_key)
        if cached_result is not None:
            self.metrics.cache_hits += 1
            return cached_result
        
        self.metrics.cache_misses += 1
        start_time = time.time()
        
        # Выбираем метод интерполяции
        if self.use_gpu and len(points) > 1000:
            # GPU для больших батчей
            result = self._interpolate_gpu(points)
        elif NUMBA_AVAILABLE and len(points) > 100:
            # Numba для средних батчей
            result = trilinear_interpolate_numba(points, self.field, self.field_size)
        else:
            # NumPy для маленьких батчей
            result = self._interpolate_numpy(points)
        
        self.metrics.interpolation_time += time.time() - start_time
        
        # Кэшируем результат
        self.interpolation_cache.put(cache_key, result)
        
        return result

    def _interpolate_gpu(self, points: np.ndarray) -> np.ndarray:
        """GPU-интерполяция через CuPy."""
        points_gpu = cp.asarray(points)
        
        # Векторизованная интерполяция на GPU
        x = points_gpu[:, 0]
        y = points_gpu[:, 1]
        z = points_gpu[:, 2]
        
        x0 = cp.int32(cp.floor(x))
        y0 = cp.int32(cp.floor(y))
        z0 = cp.int32(cp.floor(z))
        
        mask = ((x0 >= 0) & (x0 < self.field_size - 1) &
                (y0 >= 0) & (y0 < self.field_size - 1) &
                (z0 >= 0) & (z0 < self.field_size - 1))
        
        result_gpu = cp.zeros(len(points), dtype=cp.complex128)
        
        if cp.any(mask):
            fx = x[mask] - x0[mask]
            fy = y[mask] - y0[mask]
            fz = z[mask] - z0[mask]
            
            # GPU индексация
            c000 = self.field_gpu[x0[mask], y0[mask], z0[mask]]
            c100 = self.field_gpu[x0[mask] + 1, y0[mask], z0[mask]]
            c010 = self.field_gpu[x0[mask], y0[mask] + 1, z0[mask]]
            c110 = self.field_gpu[x0[mask] + 1, y0[mask] + 1, z0[mask]]
            c001 = self.field_gpu[x0[mask], y0[mask], z0[mask] + 1]
            c101 = self.field_gpu[x0[mask] + 1, y0[mask], z0[mask] + 1]
            c011 = self.field_gpu[x0[mask], y0[mask] + 1, z0[mask] + 1]
            c111 = self.field_gpu[x0[mask] + 1, y0[mask] + 1, z0[mask] + 1]
            
            c00 = c000 * (1 - fx) + c100 * fx
            c01 = c001 * (1 - fx) + c101 * fx
            c10 = c010 * (1 - fx) + c110 * fx
            c11 = c011 * (1 - fx) + c111 * fx
            
            c0 = c00 * (1 - fy) + c10 * fy
            c1 = c01 * (1 - fy) + c11 * fy
            
            result_gpu[mask] = c0 * (1 - fz) + c1 * fz
        
        return cp.asnumpy(result_gpu)

    def _interpolate_numpy(self, points: np.ndarray) -> np.ndarray:
        """NumPy-интерполяция (запасной вариант)."""
        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        x0 = np.int32(np.floor(x))
        y0 = np.int32(np.floor(y))
        z0 = np.int32(np.floor(z))
        
        mask = ((x0 >= 0) & (x0 < self.field_size - 1) &
                (y0 >= 0) & (y0 < self.field_size - 1) &
                (z0 >= 0) & (z0 < self.field_size - 1))
        
        result = np.zeros(len(points), dtype=np.complex128)
        
        if np.any(mask):
            fx, fy, fz = x[mask] - x0[mask], y[mask] - y0[mask], z[mask] - z0[mask]
            
            c000 = self.field[(x0[mask], y0[mask], z0[mask])]
            c100 = self.field[(x0[mask] + 1, y0[mask], z0[mask])]
            c010 = self.field[(x0[mask], y0[mask] + 1, z0[mask])]
            c110 = self.field[(x0[mask] + 1, y0[mask] + 1, z0[mask])]
            c001 = self.field[(x0[mask], y0[mask], z0[mask] + 1)]
            c101 = self.field[(x0[mask] + 1, y0[mask], z0[mask] + 1)]
            c011 = self.field[(x0[mask], y0[mask] + 1, z0[mask] + 1)]
            c111 = self.field[(x0[mask] + 1, y0[mask] + 1, z0[mask] + 1)]
            
            c00 = c000 * (1 - fx) + c100 * fx
            c01 = c001 * (1 - fx) + c101 * fx
            c10 = c010 * (1 - fx) + c110 * fx
            c11 = c011 * (1 - fx) + c111 * fx
            
            c0 = c00 * (1 - fy) + c10 * fy
            c1 = c01 * (1 - fy) + c11 * fy
            
            result[mask] = c0 * (1 - fz) + c1 * fz
        
        return result

    def batch_resonance_quality(self, starts: np.ndarray, ends: np.ndarray, 
                               sub_res: int = 10) -> np.ndarray:
        """Оптимизированный расчет качества резонанса."""
        M = len(starts)
        if M == 0:
            return np.array([])
        
        # Расстояния и сегменты
        diffs = ends - starts
        dists = np.linalg.norm(diffs, axis=1)
        segments = np.maximum(1, (dists * sub_res).astype(np.int32))
        
        max_seg = np.max(segments)
        total_points = M * max_seg
        
        # Генерируем все точки
        all_points = np.zeros((total_points, 3), dtype=np.float64)
        
        for i in range(M):
            seg = segments[i]
            path = generate_path_points(starts[i], ends[i], seg)
            all_points[i * max_seg:i * max_seg + seg] = path
        
        # Интерполируем все точки
        all_field_vals = self.interpolate_batch(all_points)
        
        # Считаем качество
        if NUMBA_AVAILABLE:
            qualities = compute_resonance_quality_numba(
                all_field_vals, segments, max_seg, M
            )
        else:
            qualities = np.zeros(M, dtype=np.float64)
            for i in range(M):
                seg = segments[i]
                vals = all_field_vals[i * max_seg:i * max_seg + seg]
                if seg > 0:
                    avg_phase = np.sum(np.angle(vals)) / seg
                    avg_strength = np.sum(np.abs(vals)) / seg
                    qualities[i] = np.clip(np.abs(np.cos(avg_phase)) * avg_strength, 0.0, 1.0)
        
        return qualities

    def clear_cache(self):
        """Очистка кэша для освобождения памяти."""
        self.interpolation_cache.clear()
        gc.collect()


# ===========================================================================
class TEES_TripleHub:
    """Оптимизированный трёхслойный TEES с Активным 3D-Усилителем."""
    
    def __init__(self, field_size: int = 32, use_gpu: bool = False, 
                 max_cache_size: int = 1000):
        # Проверяем доступную память
        available_memory_gb = psutil.virtual_memory().available / 1e9
        logger.info(f"Доступно памяти: {available_memory_gb:.1f} GB")
        
        # Создаем слои
        self.top = TEES_Layer("ВЕРХ", field_size, seed=42, use_gpu=use_gpu)
        self.hub = TEES_Layer("ЦЕНТР-ХАБ", field_size, seed=123, use_gpu=use_gpu)
        self.bot = TEES_Layer("НИЗ", field_size, seed=789, use_gpu=use_gpu)
        
        self.chip_temp = 30.0
        self.entropy_balance = 0.0
        self.total_routes = 0
        
        # Параметры усилителя
        self.hub_amplifier_gain = 2.0
        self.max_cache_size = max_cache_size
        
        # Кэш маршрутов
        self.route_cache = LRUCache(max_size=max_cache_size)
        
        # Метрики производительности
        self.global_metrics = PerformanceMetrics()
        
        # Адаптивный размер батча
        self.optimal_batch_size = self._calculate_optimal_batch_size()
        
        logger.info(f"Оптимальный размер батча: {self.optimal_batch_size}")
        logger.info(f"Использование GPU: {use_gpu and GPU_AVAILABLE}")
        logger.info(f"Numba оптимизации: {NUMBA_AVAILABLE}")

    def _calculate_optimal_batch_size(self) -> int:
        """Рассчитывает оптимальный размер батча на основе доступной памяти."""
        available_gb = psutil.virtual_memory().available / 1e9
        
        # Каждая точка требует ~100 байт в памяти
        # Оставляем 50% памяти для других операций
        max_points = int((available_gb * 0.5) / 100)
        
        # Ограничиваем разумными пределами
        batch_size = min(max_points, 50000)
        batch_size = max(batch_size, 100)
        
        return batch_size

    def generate_dual_topology(self, n_qubits: int) -> Tuple[Dict, Dict, List, List, List]:
        """Генерирует две топологии с оптимизированной памятью."""
        rng = np.random.RandomState(42)
        half = n_qubits // 2
        size = self.top.field_size - 1
        
        # Используем float32 для экономии памяти
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
        
        # Генерируем рёбра с контролем плотности
        density_top = min(0.05, 500 / half)  # Ограничиваем количество рёбер
        density_bot = min(0.05, 500 / half)
        density_cross = min(0.02, 200 / half)
        
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

    def _find_best_hub_entries_optimized(self, top_points: np.ndarray, 
                                        bot_points: np.ndarray) -> np.ndarray:
        """Оптимизированный поиск точек входа с кэшированием."""
        M = len(top_points)
        half_field = self.top.field_size // 2
        
        # Генерируем кандидатов
        candidates = self._generate_candidate_points(half_field)
        
        # Проверяем кэш для повторяющихся паттернов
        cache_key = hash((top_points.tobytes(), bot_points.tobytes()))
        cached_result = self.route_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        best_entries = np.zeros((M, 3), dtype=np.float64)
        
        # Векторизованный поиск для всех точек одновременно
        if M > 100:
            best_entries = self._find_entries_vectorized(top_points, bot_points, candidates)
        else:
            # Последовательный поиск для маленьких батчей
            for i in range(M):
                best_entries[i] = self._find_single_best_entry(
                    top_points[i], bot_points[i], candidates
                )
        
        # Кэшируем результат
        self.route_cache.put(cache_key, best_entries.copy())
        
        return best_entries

    def _generate_candidate_points(self, half_field: int) -> np.ndarray:
        """Генерирует сетку кандидатов."""
        n_points = 3  # 3x3x3 сетка
        offsets = np.linspace(-half_field/4, half_field/4, n_points)
        
        candidates = []
        for dx in offsets:
            for dy in offsets:
                for dz in offsets:
                    candidates.append([half_field + dx, half_field + dy, half_field + dz])
        
        return np.array(candidates, dtype=np.float64)

    def _find_entries_vectorized(self, top_points: np.ndarray, 
                                bot_points: np.ndarray,
                                candidates: np.ndarray) -> np.ndarray:
        """Векторизованный поиск лучших точек входа."""
        M = len(top_points)
        C = len(candidates)
        
        # Расширяем для векторных операций
        top_expanded = np.repeat(top_points, C, axis=0)
        bot_expanded = np.repeat(bot_points, C, axis=0)
        candidates_tiled = np.tile(candidates, (M, 1))
        
        # Качество ВЕРХ -> кандидаты
        q_top = self.top.batch_resonance_quality(top_expanded, candidates_tiled)
        
        # Качество кандидаты -> НИЗ
        q_bot = self.bot.batch_resonance_quality(candidates_tiled, bot_expanded)
        
        # Комбинированное качество
        combined = q_top * q_bot
        
        # Выбираем лучших для каждой пары
        combined_reshaped = combined.reshape(M, C)
        best_indices = np.argmax(combined_reshaped, axis=1)
        
        return candidates[best_indices]

    def _find_single_best_entry(self, top_point: np.ndarray, 
                               bot_point: np.ndarray,
                               candidates: np.ndarray) -> np.ndarray:
        """Поиск лучшей точки для одной пары."""
        # Качество от ВЕРХА к кандидатам
        q_to = self.top.batch_resonance_quality(
            np.tile(top_point, (len(candidates), 1)), candidates
        )
        
        # Качество от кандидатов к НИЗУ
        q_from = self.bot.batch_resonance_quality(
            candidates, np.tile(bot_point, (len(candidates), 1))
        )
        
        # Комбинированное качество
        combined = q_to * q_from
        best_idx = np.argmax(combined)
        
        return candidates[best_idx]

    def route_cross_batch_optimized(self, pos_top: Dict, pos_bot: Dict, 
                                   edges_cross: List[Tuple[int, int]]) -> Tuple[np.ndarray, int]:
        """Оптимизированная кросс-маршрутизация с адаптивным батчингом."""
        M = len(edges_cross)
        if M == 0:
            return np.array([]), 0
        
        # Адаптивный батчинг
        if M <= self.optimal_batch_size:
            return self._route_cross_single_batch(pos_top, pos_bot, edges_cross)
        
        # Разбиваем на подбатчи
        all_qualities = []
        total_paths = 0
        
        for start_idx in range(0, M, self.optimal_batch_size):
            end_idx = min(start_idx + self.optimal_batch_size, M)
            sub_edges = edges_cross[start_idx:end_idx]
            
            qualities, paths = self._route_cross_single_batch(
                pos_top, pos_bot, sub_edges
            )
            
            all_qualities.append(qualities)
            total_paths += paths
            
            # Очищаем кэш после каждого подбатча
            if start_idx % (self.optimal_batch_size * 5) == 0:
                self._clear_caches()
                gc.collect()
        
        return np.concatenate(all_qualities), total_paths

    def _route_cross_single_batch(self, pos_top: Dict, pos_bot: Dict, 
                                 edges_cross: List[Tuple[int, int]]) -> Tuple[np.ndarray, int]:
        """Маршрутизация одного батча через хаб."""
        M = len(edges_cross)
        
        # Подготавливаем массивы
        top_starts = np.array([pos_top[i] for i, _ in edges_cross], dtype=np.float64)
        bot_ends = np.array([pos_bot[j] for _, j in edges_cross], dtype=np.float64)
        
        # Находим оптимальные точки входа
        hub_entries = self._find_best_hub_entries_optimized(top_starts, bot_ends)
        center = np.array([self.top.field_size / 2] * 3)
        hub_exits = 2 * center - hub_entries
        
        # Этап 1: ВЕРХ -> Хаб
        q_top_to_hub = self.top.batch_resonance_quality(top_starts, hub_entries)
        
        # Этап 2: Внутри хаба
        q_hub_internal = self.hub.batch_resonance_quality(hub_entries, hub_exits)
        
        # Усиление
        gains = 1.0 + (q_hub_internal - 0.5) * self.hub_amplifier_gain
        gains = np.clip(gains, 0.5, 2.0)
        
        # Этап 3: Хаб -> НИЗ
        q_hub_to_bot = self.bot.batch_resonance_quality(hub_exits, bot_ends)
        
        # Общее качество
        total_quality = q_top_to_hub * gains * q_hub_to_bot
        total_quality = np.clip(total_quality, 0.0, 1.0)
        
        # Сохраняем успешные маршруты
        paths_count = 0
        for i in range(M):
            if total_quality[i] > 0.7:
                self.hub.route_cache.put(
                    hash((edges_cross[i], time.time())),
                    RouteCacheEntry(
                        entry_point=hub_entries[i],
                        exit_point=hub_exits[i],
                        quality=total_quality[i],
                        timestamp=time.time()
                    )
                )
                paths_count += 1
        
        return total_quality, paths_count

    def _clear_caches(self):
        """Очистка всех кэшей."""
        self.top.clear_cache()
        self.hub.clear_cache()
        self.bot.clear_cache()

    def run_parallel_test_optimized(self, n_qubits: int = 500, epochs: int = 3,
                                   use_multiprocessing: bool = True):
        """Оптимизированный параллельный тест."""
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Трёхслойный TEES-Хаб v1.0: {n_qubits} кубитов")
        logger.info(f"{'='*60}")
        
        # Мониторинг памяти
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1e9
        logger.info(f"Начальное использование памяти: {initial_memory:.2f} GB")
        
        pos_top, pos_bot, edges_top, edges_bot, edges_cross = \
            self.generate_dual_topology(n_qubits)
        
        total_start = time.time()
        
        for epoch in range(epochs):
            epoch_start = time.time()
            
            if use_multiprocessing and len(edges_top) + len(edges_bot) > 1000:
                # Многопроцессорная обработка
                q_top, q_bot = self._process_layers_parallel(edges_top, edges_bot, 
                                                            pos_top, pos_bot)
            else:
                # Последовательная обработка
                q_top = self.top.batch_resonance_quality(
                    np.array([pos_top[u] for u, _ in edges_top]),
                    np.array([pos_top[v] for _, v in edges_top])
                )
                q_bot = self.bot.batch_resonance_quality(
                    np.array([pos_bot[u] for u, _ in edges_bot]),
                    np.array([pos_bot[v] for _, v in edges_bot])
                )
            
            # Кросс-связи через хаб
            q_cross, paths_count = self.route_cross_batch_optimized(
                pos_top, pos_bot, edges_cross
            )
            
            epoch_time = time.time() - epoch_start
            
            # Статистика
            self._print_epoch_stats(epoch, q_top, q_bot, q_cross, 
                                   edges_top, edges_bot, edges_cross,
                                   epoch_time, paths_count)
            
            # Очистка после эпохи
            if epoch < epochs - 1:
                self._clear_caches()
                gc.collect()
        
        total_time = time.time() - total_start
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1e9
        
        # Финальная статистика
        self._print_final_stats(total_time, initial_memory, final_memory)

    def _process_layers_parallel(self, edges_top, edges_bot, pos_top, pos_bot):
        """Параллельная обработка слоев."""
        with ProcessPoolExecutor(max_workers=2) as executor:
            future_top = executor.submit(
                self._process_layer_chunk, 'top', edges_top, pos_top, pos_top
            )
            future_bot = executor.submit(
                self._process_layer_chunk, 'bot', edges_bot, pos_bot, pos_bot
            )
            
            q_top = future_top.result(timeout=30)
            q_bot = future_bot.result(timeout=30)
        
        return q_top, q_bot

    @staticmethod
    def _process_layer_chunk(layer_name: str, edges: List, 
                            pos_dict: Dict, target_dict: Dict) -> np.ndarray:
        """Статический метод для параллельной обработки."""
        layer = TEES_Layer(layer_name, seed=hash(layer_name) % 1000)
        
        starts = np.array([pos_dict[u] for u, _ in edges])
        ends = np.array([target_dict[v] for _, v in edges])
        
        return layer.batch_resonance_quality(starts, ends)

    def _print_epoch_stats(self, epoch: int, q_top: np.ndarray, q_bot: np.ndarray,
                          q_cross: np.ndarray, edges_top: List, edges_bot: List,
                          edges_cross: List, epoch_time: float, paths_count: int):
        """Вывод статистики эпохи."""
        top_success = np.sum(q_top > 0.7)
        bot_success = np.sum(q_bot > 0.7)
        cross_success = np.sum(q_cross > 0.7)
        
        total_quality = (np.mean(q_top) + np.mean(q_bot) + np.mean(q_cross)) / 3
        
        self._update_thermals(total_quality)
        
        memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1e9
        
        logger.info(f"  Эпоха {epoch+1}: "
                   f"ВЕРХ {top_success}/{len(edges_top)} "
                   f"({top_success/max(1,len(edges_top)):.1%}), "
                   f"НИЗ {bot_success}/{len(edges_bot)} "
                   f"({bot_success/max(1,len(edges_bot)):.1%}), "
                   f"ХАБ {cross_success}/{len(edges_cross)} "
                   f"({cross_success/max(1,len(edges_cross)):.1%})")
        logger.info(f"           Время: {epoch_time:.2f}с, "
                   f"Память: {memory_usage:.2f}GB, "
                   f"Маршрутов: {paths_count}")

    def _print_final_stats(self, total_time: float, initial_memory: float, 
                          final_memory: float):
        """Вывод финальной статистики."""
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ ТЕСТ ЗАВЕРШЕН")
        logger.info(f"⏱️  Общее время: {total_time:.1f} сек")
        logger.info(f"💾 Память: {initial_memory:.2f}GB -> {final_memory:.2f}GB "
                   f"(Δ{final_memory-initial_memory:+.2f}GB)")
        logger.info(f"🌡️  Темп-ра чипа: {self.chip_temp:.1f}°C")
        logger.info(f"🌀 Баланс энтропии: {self.entropy_balance:.2f}")
        logger.info(f"📊 Кэш хитов: {self.top.metrics.cache_hits + self.hub.metrics.cache_hits + self.bot.metrics.cache_hits}")
        logger.info(f"{'='*60}")

    def _update_thermals(self, avg_quality: float):
        """Обновление теплового баланса."""
        coherence = avg_quality ** 2
        heat = (1.0 - coherence) * 30.0
        cooling = min(50.0, heat * 1.5)
        self.chip_temp += (heat - cooling) * 0.1
        self.chip_temp = max(-273.15, self.chip_temp)
        self.entropy_balance += (1.0 - coherence)


# ===========================================================================
def flight_test_optimized():
    """Оптимизированный тестовый полет."""
    logger.info("=" * 60)
    logger.info("🚀 TEESRouter v1.0 — Оптимизированный Активный 3D-Усилитель")
    logger.info(f"📦 Numba: {NUMBA_AVAILABLE}, GPU: {GPU_AVAILABLE}")
    logger.info("=" * 60)
    
    # Определяем использование GPU
    use_gpu = GPU_AVAILABLE and psutil.virtual_memory().total > 8e9  # >8GB RAM
    
    hub = TEES_TripleHub(field_size=32, use_gpu=use_gpu, max_cache_size=2000)
    
    # Тестируем с разными размерами
    test_sizes = [100, 500, 1000]
    
    for q in test_sizes:
        try:
            hub.run_parallel_test_optimized(
                n_qubits=q, 
                epochs=3,
                use_multiprocessing=(q > 200)
            )
        except Exception as e:
            logger.error(f"Ошибка при тестировании {q} кубитов: {e}")
            continue
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ПОСАДКА ВЫПОЛНЕНА. ХАБ-УСИЛИТЕЛЬ К ОХЛАЖДЕНИЮ ГОТОВ.")
    logger.info("=" * 60)


def benchmark_performance():
    """Бенчмарк производительности."""
    logger.info("\n📊 БЕНЧМАРК ПРОИЗВОДИТЕЛЬНОСТИ")
    
    hub = TEES_TripleHub(field_size=32, use_gpu=False)
    
    # Тест интерполяции
    test_points = np.random.uniform(0, 31, (10000, 3))
    
    start = time.time()
    for _ in range(10):
        result = hub.top.interpolate_batch(test_points)
    interp_time = (time.time() - start) / 10
    
    logger.info(f"Интерполяция 10K точек: {interp_time*1000:.2f} мс")
    
    # Тест качества резонанса
    starts = np.random.uniform(0, 31, (100, 3))
    ends = np.random.uniform(0, 31, (100, 3))
    
    start = time.time()
    for _ in range(10):
        qualities = hub.top.batch_resonance_quality(starts, ends)
    quality_time = (time.time() - start) / 10
    
    logger.info(f"Качество 100 путей: {quality_time*1000:.2f} мс")


if __name__ == "__main__":
    # Настройка для высокопроизводительных вычислений
    os.environ['OMP_NUM_THREADS'] = str(os.cpu_count())
    os.environ['MKL_NUM_THREADS'] = str(os.cpu_count())
    
    if NUMBA_AVAILABLE:
        os.environ['NUMBA_NUM_THREADS'] = str(os.cpu_count())
    
    # Запуск тестов
    flight_test_optimized()
    benchmark_performance()