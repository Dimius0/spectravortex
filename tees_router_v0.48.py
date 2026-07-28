"""
TEESRouter v0.48 — TRIPLE-LAYER HUB (Векторизованный)
======================================================
Архитектура:
  Слой 0 (ВЕРХ):  рабочая плоскость A (TEES)
  Слой 1 (ЦЕНТР): TEES-Хаб (маршрутизация + связь)
  Слой 2 (НИЗ):   рабочая плоскость B (TEES)

Исправления v0.48:
  - Векторизованный обсчёт слоёв (батчи вместо циклов)
  - Векторизованный ХАБ (все кросс-связи одной операцией)
  - Правильная модель ХАБ-резонанса (не "сам с собой")
  - Охлаждение и метрики для всех слоёв
"""

import numpy as np
import time
import logging
from typing import Tuple, List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("TEES_Hub")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


# ===========================================================================
class TEES_Layer:
    """Один TEES-слой: ВЕРХ, ЦЕНТР (ХАБ), или НИЗ."""
    
    BASE_COUPLING = np.array([
        0.259921, 0.442249, 0.709975, 0.912931, 0.148693, 0.307107, 0.518294, 0.651839,
        0.822315, 0.959920, 0.089322, 0.209579, 0.330643, 0.446273, 0.551831, 0.657378,
        0.761885, 0.867051, 0.975174, 0.075541, 0.183840, 0.286918, 0.393314, 0.497253,
        0.604512, 0.706761, 0.812413, 0.915046, 0.015973, 0.116299, 0.218563, 0.316947,
    ], dtype=np.float64)

    def __init__(self, name: str, field_size: int = 32, max_k: int = 256, seed: int = 42):
        self.name = name
        self.field_size = field_size
        self.max_k = max_k
        
        # 3D поле слоя
        self.field = np.zeros((field_size, field_size, field_size), dtype=np.complex128)
        
        # Уникальный шум для каждого слоя
        rng = np.random.RandomState(seed)
        
        x = np.linspace(0, 4 * np.pi, field_size)
        y = np.linspace(0, 4 * np.pi, field_size)
        z = np.linspace(0, 4 * np.pi, field_size)
        X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
        
        # Стоячие волны
        base = (
            np.sin(X) * np.cos(Y) 
            + np.sin(Y) * np.cos(Z) 
            + np.sin(Z) * np.cos(X)
        )
        
        # Уникальная К-модуляция для каждого слоя
        k_vals = self._get_k_bands(0.5)
        for i, k in enumerate(k_vals[:8]):
            phase_shift = rng.uniform(0, 2 * np.pi)
            base += 0.1 * np.sin(X * k + phase_shift) * np.cos(Y * k) * np.sin(Z * k)
        
        # Шум (уникальный для слоя)
        noise = rng.normal(0, 0.1, (field_size, field_size, field_size))
        self.field = base + 1j * noise
        
        # Метрики слоя
        self.temp = 30.0
        self.entropy = 0.0
        self.routing_count = 0
        
        logger.info(f"Слой '{self.name}' инициализирован: {self.field.size} ячеек")

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
        Векторизованная трилинейная интерполяция для пакета точек.
        points: (N, 3)
        Возвращает: (N,) комплексных значений
        """
        if len(points) == 0:
            return np.array([], dtype=np.complex128)
            
        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        x0 = np.int32(np.floor(x))
        y0 = np.int32(np.floor(y))
        z0 = np.int32(np.floor(z))
        
        # Маска валидности
        mask = (
            (x0 >= 0) & (x0 < self.field_size - 1) &
            (y0 >= 0) & (y0 < self.field_size - 1) &
            (z0 >= 0) & (z0 < self.field_size - 1)
        )
        
        fx, fy, fz = x - x0, y - y0, z - z0
        
        # Векторизованная выборка (только для валидных индексов)
        valid_x0 = x0[mask]
        valid_y0 = y0[mask]
        valid_z0 = z0[mask]
        
        result = np.zeros(len(points), dtype=np.complex128)
        
        if np.any(mask):
            c000 = self.field[(valid_x0, valid_y0, valid_z0)]
            c100 = self.field[(valid_x0 + 1, valid_y0, valid_z0)]
            c010 = self.field[(valid_x0, valid_y0 + 1, valid_z0)]
            c110 = self.field[(valid_x0 + 1, valid_y0 + 1, valid_z0)]
            c001 = self.field[(valid_x0, valid_y0, valid_z0 + 1)]
            c101 = self.field[(valid_x0 + 1, valid_y0, valid_z0 + 1)]
            c011 = self.field[(valid_x0, valid_y0 + 1, valid_z0 + 1)]
            c111 = self.field[(valid_x0 + 1, valid_y0 + 1, valid_z0 + 1)]
            
            fx_v = fx[mask]
            fy_v = fy[mask]
            fz_v = fz[mask]
            
            c00 = c000 * (1 - fx_v) + c100 * fx_v
            c01 = c001 * (1 - fx_v) + c101 * fx_v
            c10 = c010 * (1 - fx_v) + c110 * fx_v
            c11 = c011 * (1 - fx_v) + c111 * fx_v
            
            c0 = c00 * (1 - fy_v) + c10 * fy_v
            c1 = c01 * (1 - fy_v) + c11 * fy_v
            
            result[mask] = c0 * (1 - fz_v) + c1 * fz_v
        
        return result

    def batch_resonance_quality(
        self, 
        starts: np.ndarray, 
        ends: np.ndarray, 
        sub_res: int = 10
    ) -> np.ndarray:
        """
        Векторизованный расчёт качества резонанса для ПАКЕТА рёбер.
        starts: (M, 3) — начальные точки
        ends:   (M, 3) — конечные точки
        Возвращает: (M,) качество резонанса
        """
        M = len(starts)
        if M == 0:
            return np.array([])
        
        # Расстояния и количество сегментов
        diffs = ends - starts
        dists = np.linalg.norm(diffs, axis=1)
        segments = np.maximum(1, (dists * sub_res).astype(np.int32))
        
        # Максимальное количество сегментов для паддинга
        max_seg = np.max(segments)
        total_points = M * max_seg
        
        # Создаём ВСЕ точки пути одной операцией
        all_points = np.zeros((total_points, 3), dtype=np.float64)
        
        for i in range(M):
            seg = segments[i]
            t = np.linspace(0, 1, seg).reshape(-1, 1)
            path = starts[i].reshape(1, 3) + t * diffs[i].reshape(1, 3)
            # Паддинг нулями для выравнивания
            all_points[i * max_seg : i * max_seg + seg] = path
        
        # Одна гигантская интерполяция для ВСЕХ точек
        all_field_vals = self.interpolate_batch(all_points)
        
        # Считаем качество для каждого пути
        qualities = np.zeros(M, dtype=np.float64)
        for i in range(M):
            seg = segments[i]
            vals = all_field_vals[i * max_seg : i * max_seg + seg]
            if seg > 0:
                avg_phase = np.sum(np.angle(vals)) / seg
                avg_strength = np.sum(np.abs(vals)) / seg
                qualities[i] = np.clip(np.abs(np.cos(avg_phase)) * avg_strength, 0.0, 1.0)
        
        return qualities


# ===========================================================================
class TEES_TripleHub:
    """Трёхслойный TEES с Центральным Хабом."""
    
    def __init__(self, field_size: int = 32):
        # Три независимых слоя с разными seed для уникальности
        self.top = TEES_Layer("ВЕРХ", field_size, seed=42)
        self.hub = TEES_Layer("ЦЕНТР-ХАБ", field_size, seed=123)  # Отдельный seed
        self.bot = TEES_Layer("НИЗ", field_size, seed=789)        # Отдельный seed
        
        self.chip_temp = 30.0
        self.entropy_balance = 0.0
        self.total_routes = 0
    
    def generate_dual_topology(self, n_qubits: int) -> Tuple[Dict, Dict, List, List, List]:
        """Генерирует две топологии: для ВЕРХА и НИЗА + кросс-связи."""
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
            ])
            pos_bot[i] = np.array([
                rng.uniform(0, size),
                rng.uniform(0, size),
                rng.uniform(0, size)
            ])
        
        # Рёбра внутри слоёв
        edges_top = [(i, j) for i in range(half) for j in range(i+1, half) if rng.random() < 0.05]
        edges_bot = [(i, j) for i in range(half) for j in range(i+1, half) if rng.random() < 0.05]
        
        # Межслоевые связи (через ХАБ)
        edges_cross = [(i, j) for i in range(half) for j in range(half) if rng.random() < 0.02]
        
        logger.info(f"Топология: ВЕРХ={len(pos_top)}q/{len(edges_top)}e, НИЗ={len(pos_bot)}q/{len(edges_bot)}e, КРОСС={len(edges_cross)}")
        return pos_top, pos_bot, edges_top, edges_bot, edges_cross
    
    def route_cross_batch(
        self, 
        pos_top: Dict, 
        pos_bot: Dict, 
        edges_cross: List[Tuple[int, int]]
    ) -> np.ndarray:
        """
        Векторизованный маршрут через ХАБ для ВСЕХ кросс-связей.
        ВЕРХ → точка входа в ХАБ → резонанс ХАБА → точка выхода → НИЗ
        """
        M = len(edges_cross)
        if M == 0:
            return np.array([])
        
        # Точка входа в ХАБ (центр)
        center = np.array([16.0, 16.0, 16.0])
        
        # Собираем массивы точек
        top_starts = np.array([pos_top[i] for i, _ in edges_cross])
        bot_ends = np.array([pos_bot[j] for _, j in edges_cross])
        
        # Этап 1: ВЕРХ → ХАБ (центр)
        hub_entries = np.tile(center, (M, 1))
        q_top_to_hub = self.top.batch_resonance_quality(top_starts, hub_entries)
        
        # Этап 2: ХАБ-резонанс (не "сам с собой", а распространение через ХАБ)
        # Хаб "переизлучает" сигнал — учитываем это как проход через поле ХАБА
        # от точки входа до точки выхода с небольшим смещением
        hub_offsets = np.random.RandomState(42).uniform(-2, 2, (M, 3))
        hub_exits = center.reshape(1, 3) + hub_offsets
        q_hub_internal = self.hub.batch_resonance_quality(hub_entries, hub_exits)
        
        # Этап 3: ХАБ → НИЗ
        q_hub_to_bot = self.bot.batch_resonance_quality(hub_exits, bot_ends)
        
        # Сквозное качество (каскад резонансов)
        total_quality = q_top_to_hub * q_hub_internal * q_hub_to_bot
        
        return np.clip(total_quality, 0.0, 1.0)
    
    def run_parallel_test(self, n_qubits: int = 500):
        """Параллельный тест ВЕРХ + НИЗ с векторизованным ХАБ-связыванием."""
        logger.info(f"\n{'='*50}")
        logger.info(f"🚀 Трёхслойный TEES-Хаб: {n_qubits} кубитов")
        logger.info(f"{'='*50}")
        
        pos_top, pos_bot, edges_top, edges_bot, edges_cross = self.generate_dual_topology(n_qubits)
        
        start_time = time.time()
        
        # Векторизованный обсчёт слоёв
        top_starts = np.array([pos_top[u] for u, _ in edges_top])
        top_ends = np.array([pos_top[v] for _, v in edges_top])
        q_top = self.top.batch_resonance_quality(top_starts, top_ends)
        
        bot_starts = np.array([pos_bot[u] for u, _ in edges_bot])
        bot_ends = np.array([pos_bot[v] for _, v in edges_bot])
        q_bot = self.bot.batch_resonance_quality(bot_starts, bot_ends)
        
        # Векторизованный ХАБ
        q_cross = self.route_cross_batch(pos_top, pos_bot, edges_cross)
        
        elapsed = time.time() - start_time
        
        # Статистика
        top_success = np.sum(q_top > 0.7)
        bot_success = np.sum(q_bot > 0.7)
        cross_success = np.sum(q_cross > 0.7)
        
        total_edges = len(edges_top) + len(edges_bot) + len(edges_cross)
        total_success = top_success + bot_success + cross_success
        total_quality = (
            np.sum(q_top) + np.sum(q_bot) + np.sum(q_cross)
        ) / max(1, total_edges)
        
        # Охлаждение
        self._update_thermals(total_quality)
        
        logger.info(f"✅ ВЕРХ: {top_success}/{len(edges_top)} ({top_success/max(1,len(edges_top)):.2%}), качество {np.mean(q_top):.4f}")
        logger.info(f"✅ НИЗ:  {bot_success}/{len(edges_bot)} ({bot_success/max(1,len(edges_bot)):.2%}), качество {np.mean(q_bot):.4f}")
        logger.info(f"🌀 ХАБ:  {cross_success}/{len(edges_cross)} ({cross_success/max(1,len(edges_cross)):.2%}), качество {np.mean(q_cross):.4f}")
        logger.info(f"📊 ОБЩИЙ: {total_success}/{total_edges} ({total_success/max(1,total_edges):.2%}), качество {total_quality:.4f}")
        logger.info(f"⏱️  Время: {elapsed:.2f} сек")
        logger.info(f"🌡️  Темп-ра чипа: {self.chip_temp:.1f}°C")
        logger.info(f"🌀 Баланс энтропии: {self.entropy_balance:.2f}")
    
    def _update_thermals(self, avg_quality: float):
        """Обновление теплового баланса."""
        coherence = avg_quality ** 2
        heat = (1.0 - coherence) * 30.0  # Тепловыделение от трёх слоёв
        cooling = min(50.0, heat * 1.5)  # Пельтье
        self.chip_temp += (heat - cooling) * 0.1
        self.chip_temp = max(-273.15, self.chip_temp)
        self.entropy_balance += (1.0 - coherence)


# ===========================================================================
def flight_test():
    logger.info("=" * 50)
    logger.info("🚀 TEESRouter v0.48 — Triple-Layer Hub (Векторизованный)")
    logger.info("=" * 50)
    
    hub = TEES_TripleHub(field_size=32)
    
    for q in [100, 500, 1000, 2000]:
        hub.run_parallel_test(n_qubits=q)
    
    logger.info("\n" + "=" * 50)
    logger.info("ПОСАДКА ВЫПОЛНЕНА. ТРЁХСЛОЙНЫЙ ХАБ К ОХЛАЖДЕНИЮ ГОТОВ.")
    logger.info("=" * 50)


if __name__ == "__main__":
    flight_test()