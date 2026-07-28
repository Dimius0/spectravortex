"""
TEESRouter v1.3.2 — "ТУРБО-НАБЛЮДАТЕЛЬ" (HOTFIX)
====================================================
Адаптивный Gain — раз за эпоху. Без дерганий!
"""

import numpy as np, time, logging, gc, psutil, os
from typing import Tuple, List, Dict, Optional, Any
from collections import OrderedDict
import warnings
warnings.filterwarnings('ignore')

try:
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def jit(*a,**k): return lambda f: f
    prange = range

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("TEES_Turbo")

# ===========================================================================
@jit(nopython=True, cache=True, fastmath=True)
def generate_path_points_batch(starts, ends, max_points):
    M = starts.shape[0]
    paths = np.zeros((M, max_points, 3), dtype=np.float64)
    for i in range(M):
        dist = np.sqrt(np.sum((ends[i] - starts[i]) ** 2))
        n_pts = max(1, int(dist * 10))
        d = ends[i] - starts[i]
        for j in range(min(n_pts, max_points)):
            t = j / (n_pts - 1) if n_pts > 1 else 0.0
            paths[i, j] = starts[i] + t * d
    return paths

@jit(nopython=True, parallel=True, cache=True, fastmath=True)
def interpolate_batch_paths(paths, field, fs):
    M, mp = paths.shape[0], paths.shape[1]
    result = np.zeros((M, mp), dtype=np.complex128)
    for i in prange(M):
        for j in range(mp):
            x, y, z = paths[i, j, 0], paths[i, j, 1], paths[i, j, 2]
            if x == 0.0 and y == 0.0 and z == 0.0: continue
            x0, y0, z0 = int(np.floor(x)), int(np.floor(y)), int(np.floor(z))
            if 0 <= x0 < fs-1 and 0 <= y0 < fs-1 and 0 <= z0 < fs-1:
                fx, fy, fz = x-x0, y-y0, z-z0
                c000, c100 = field[x0,y0,z0], field[x0+1,y0,z0]
                c010, c110 = field[x0,y0+1,z0], field[x0+1,y0+1,z0]
                c001, c101 = field[x0,y0,z0+1], field[x0+1,y0,z0+1]
                c011, c111 = field[x0,y0+1,z0+1], field[x0+1,y0+1,z0+1]
                c00 = c000*(1-fx) + c100*fx; c01 = c001*(1-fx) + c101*fx
                c10 = c010*(1-fx) + c110*fx; c11 = c011*(1-fx) + c111*fx
                c0 = c00*(1-fy) + c10*fy; c1 = c01*(1-fy) + c11*fy
                result[i, j] = c0*(1-fz) + c1*fz
    return result

@jit(nopython=True, parallel=True, cache=True, fastmath=True)
def compute_qualities_batch(fv, segs):
    M = fv.shape[0]
    qs = np.zeros(M, dtype=np.float64)
    for i in prange(M):
        s = segs[i]
        if s == 0: continue
        tp, ts = 0.0, 0.0
        for j in range(s):
            v = fv[i, j]; tp += np.angle(v); ts += np.abs(v)
        qs[i] = min(1.0, np.abs(np.cos(tp/s)) * (ts/s))
    return qs

# ===========================================================================
class RouteCache:
    def __init__(self, max_size=500):
        self.cache = OrderedDict(); self.max_size = max_size
        self.hits, self.misses = 0, 0
    def get(self, sk, ek, phase=0):
        key = (sk, ek, phase)
        if key in self.cache: self.cache.move_to_end(key); self.hits += 1; return self.cache[key]
        self.misses += 1; return None
    def put(self, sk, ek, quality, phase=0):
        key = (sk, ek, phase)
        if key in self.cache: self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size: self.cache.popitem(last=False)
        self.cache[key] = quality
    def clear(self): self.cache.clear(); self.hits = self.misses = 0
    def hit_rate(self):
        t = self.hits + self.misses; return self.hits / t if t > 0 else 0.0

# ===========================================================================
class TEES_Layer:
    BASE_COUPLING = np.array([
        0.259921,0.442249,0.709975,0.912931,0.148693,0.307107,0.518294,0.651839,
        0.822315,0.959920,0.089322,0.209579,0.330643,0.446273,0.551831,0.657378,
        0.761885,0.867051,0.975174,0.075541,0.183840,0.286918,0.393314,0.497253,
        0.604512,0.706761,0.812413,0.915046,0.015973,0.116299,0.218563,0.316947
    ], dtype=np.float64)

    def __init__(self, name, field_size=32, seed=42):
        self.name = name; self.field_size = field_size
        self.field = np.zeros((field_size,)*3, dtype=np.complex128)
        self._init_field(seed)
        self.micro_batch_size = 100; self.field_reinforcements = 0

    def _init_field(self, seed):
        rng = np.random.RandomState(seed)
        x = np.linspace(0, 4*np.pi, self.field_size)
        X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
        base = np.sin(X)*np.cos(Y) + np.sin(Y)*np.cos(Z) + np.sin(Z)*np.cos(X)
        k_vals = self._get_k_bands(0.5)
        for i, k in enumerate(k_vals[:8]):
            base += 0.1 * np.sin(X*k + rng.uniform(0, 2*np.pi)) * np.cos(Y*k) * np.sin(Z*k)
        self.field = base + 1j * rng.normal(0, 0.1, (self.field_size,)*3)

    def _get_k_bands(self, complexity):
        n = 4 if complexity < 0.3 else (16 if complexity < 0.6 else 32)
        return np.interp(np.linspace(0, 1, n), np.linspace(0, 1, 32), self.BASE_COUPLING)

    def reinforce_field(self, path, boost):
        if boost <= 0: return
        for p in path:
            x0, y0, z0 = int(np.floor(p[0])), int(np.floor(p[1])), int(np.floor(p[2]))
            if 0 <= x0 < self.field_size-1 and 0 <= y0 < self.field_size-1 and 0 <= z0 < self.field_size-1:
                self.field[x0, y0, z0] += boost * 0.1 * np.exp(1j * np.angle(self.field[x0, y0, z0]))
                self.field_reinforcements += 1

    def get_health(self):
        amp = np.abs(self.field)
        return {
            'name': self.name,
            'mean_amp': float(np.mean(amp)),
            'dead_zone_pct': float(np.mean(amp < 0.1) * 100),
            'hot_zone_pct': float(np.mean(amp > 1.5) * 100),
            'reinforcements': self.field_reinforcements
        }

    def detect_dead_zones(self, threshold=0.1):
        return np.abs(self.field) < threshold

    def inject_chaos(self, intensity=0.3, target_zones=None):
        if target_zones is None: target_zones = self.detect_dead_zones()
        if not np.any(target_zones): return 0
        self.field[target_zones] += 1j * np.random.normal(0, intensity, self.field.shape)[target_zones]
        return np.sum(target_zones)

    def batch_resonance_quality_fast(self, starts, ends, sub_res=10):
        M = len(starts)
        if M == 0: return np.array([])
        qualities = np.zeros(M, dtype=np.float64)
        diffs = ends - starts
        dists = np.sqrt(np.sum(diffs**2, axis=1))
        max_seg = max(1, int(np.max(dists) * sub_res))
        for start_idx in range(0, M, self.micro_batch_size):
            end_idx = min(start_idx + self.micro_batch_size, M)
            paths = generate_path_points_batch(starts[start_idx:end_idx], ends[start_idx:end_idx], max_seg)
            fv = interpolate_batch_paths(paths, self.field, self.field_size)
            segs = np.maximum(1, (dists[start_idx:end_idx] * sub_res).astype(np.int32))
            qualities[start_idx:end_idx] = compute_qualities_batch(fv, segs)
            if start_idx % (self.micro_batch_size * 100) == 0: gc.collect()
        return qualities

# ===========================================================================
class TurboTEES:
    """v1.3.2 HOTFIX — Адаптивный Gain раз за эпоху!"""

    def __init__(self, field_size=32, cache_size=500):
        available_gb = psutil.virtual_memory().available / 1e9
        logger.info(f"💾 Память: {available_gb:.1f} GB")

        self.top = TEES_Layer("ВЕРХ", field_size, 42)
        self.hub = TEES_Layer("ХАБ", field_size, 123)
        self.bot = TEES_Layer("НИЗ", field_size, 789)

        self.chip_temp = 30.0; self.entropy_balance = 0.0; self.homeostasis_quality = 0.0
        self.current_gain = 1.5  # Стартовый gain
        self.max_gain = 3.0
        self.route_cache = RouteCache(cache_size)
        self.success_threshold = 0.6; self.threshold_growth = 0.02
        self.cross_micro_batch = 200

        # 🚀 Турбо-Хаб
        self.turbo_mode = False
        self.turbo_epochs = 0

        # 🧯 Умный хаос
        self.chaos_applied = 0
        self.chaos_cooldown = 0

        self.history = {
            'epoch': [], 'top_quality': [], 'bot_quality': [], 'cross_quality': [],
            'temperature': [], 'cache_hit_rate': [], 'gain_used': [],
            'top_success_rate': [], 'bot_success_rate': [], 'cross_success_rate': [],
            'anomalies': [], 'turbo': [], 'chaos': []
        }

        logger.info(f"🚀 УСИЛИТЕЛЬ: {self.current_gain}× → {self.max_gain}× (адаптивный: 1 раз/эпоху)")
        logger.info(f"💾 КЭШ: {cache_size}")
        logger.info(f"🎯 ПОРОГ: {self.success_threshold:.0%}")
        logger.info(f"🧯 УМНЫЙ ХАОС: да | 🚀 ТУРБО-ХАБ: готов")

    def _update_adaptive_gain(self, epoch):
        """📈 Адаптивный Gain — раз за эпоху! Сравниваем среднее качество ХАБ."""
        if epoch < 1: return  # Нет истории
        
        prev_cross = self.history['cross_quality'][-2]  # Предыдущая эпоха
        current_cross = self.history['cross_quality'][-1]  # Текущая
        
        if prev_cross == 0: return
        
        delta = current_cross - prev_cross
        
        if delta > 0.02:  # Растёт — ускоряемся
            self.current_gain = min(self.max_gain, self.current_gain * 1.2)
            logger.info(f"  📈 GAIN РАСТЁТ: {self.current_gain:.1f}× (Δ качества: {delta:+.3f})")
        elif delta < -0.02:  # Падает — сбрасываем
            self.current_gain = max(1.0, self.current_gain * 0.8)
            logger.info(f"  📉 GAIN ПАДАЕТ: {self.current_gain:.1f}× (Δ качества: {delta:+.3f})")
        # Иначе — стабильно, держим

    def _smart_chaos_trigger(self, epoch):
        """🧠 Умный триггер: хаос только при dead_zones > 30% И mean_amp < 0.4"""
        if self.chaos_cooldown > 0:
            self.chaos_cooldown -= 1
            return

        for layer in [self.top, self.hub, self.bot]:
            health = layer.get_health()
            if health['dead_zone_pct'] > 30 and health['mean_amp'] < 0.4:
                affected = layer.inject_chaos(intensity=0.2)
                if affected > 0:
                    self.chaos_applied += 1
                    self.chaos_cooldown = 2
                    logger.info(f"  🧯 УМНЫЙ ХАОС: {layer.name} — {health['dead_zone_pct']:.0f}% мёртвых, амплитуда {health['mean_amp']:.3f}")
                    self.history['chaos'].append(epoch+1)
                    return

    def _turbo_hub_check(self, top_q, bot_q):
        """🚀 Турбо-Хаб: если края слабеют — Хаб берёт на себя их маршруты"""
        if top_q < 0.5 and bot_q < 0.5 and not self.turbo_mode:
            self.turbo_mode = True
            self.turbo_epochs = 2
            logger.info(f"  🚀 ТУРБО-ХАБ АКТИВИРОВАН! ВЕРХ={top_q:.3f}, НИЗ={bot_q:.3f}")
        elif (top_q > 0.6 or bot_q > 0.6) and self.turbo_mode:
            self.turbo_mode = False
            logger.info(f"  ✅ ТУРБО-ХАБ ОТКЛЮЧЁН — края восстановились")
        
        if self.turbo_mode:
            self.turbo_epochs -= 1
            if self.turbo_epochs <= 0:
                self.turbo_mode = False
        
        self.history['turbo'].append(1 if self.turbo_mode else 0)

    def generate_dual_topology(self, n_qubits):
        rng = np.random.RandomState(42)
        half = n_qubits // 2
        size = self.top.field_size - 1
        
        pos_top, pos_bot = {}, {}
        for i in range(half):
            pos_top[i] = np.array([rng.uniform(0, size) for _ in range(3)], dtype=np.float32)
            pos_bot[i] = np.array([rng.uniform(0, size) for _ in range(3)], dtype=np.float32)
        
        density = min(0.05, 500 / max(1, half))
        density_cross = min(0.02, 200 / max(1, half))
        
        et = [(i, j) for i in range(half) for j in range(i+1, half) if rng.random() < density]
        eb = [(i, j) for i in range(half) for j in range(i+1, half) if rng.random() < density]
        ec = [(i, j) for i in range(half) for j in range(half) if rng.random() < density_cross]
        
        logger.info(f"📐 Топология: ВЕРХ={len(pos_top)}q/{len(et)}e, НИЗ={len(pos_bot)}q/{len(eb)}e, КРОСС={len(ec)}e")
        return pos_top, pos_bot, et, eb, ec

    def route_cross_with_amplifier(self, pos_top, pos_bot, edges_cross, epoch):
        M = len(edges_cross)
        if M == 0: return np.array([])
        
        qualities = np.zeros(M, dtype=np.float64)
        center = np.array([self.top.field_size/2]*3, dtype=np.float64)
        
        # Используем ТЕКУЩИЙ gain (не дёргаем!)
        gain = self.current_gain
        if self.turbo_mode:
            gain = min(self.max_gain, gain * 1.5)  # Турбо +50%
        
        for start_idx in range(0, M, self.cross_micro_batch):
            end_idx = min(start_idx + self.cross_micro_batch, M)
            mb_size = end_idx - start_idx
            
            mb_top = np.zeros((mb_size, 3), dtype=np.float64)
            mb_bot = np.zeros((mb_size, 3), dtype=np.float64)
            for i, idx in enumerate(range(start_idx, end_idx)):
                ti, bi = edges_cross[idx]; mb_top[i] = pos_top[ti]; mb_bot[i] = pos_bot[bi]
            
            cached_mask = np.zeros(mb_size, dtype=bool)
            for i in range(mb_size):
                sk = tuple(mb_top[i].round(2)); ek = tuple(mb_bot[i].round(2))
                q = self.route_cache.get(sk, ek)
                if q is not None: qualities[start_idx+i] = q; cached_mask[i] = True
            
            hub_entries = center + np.random.uniform(-1, 1, (mb_size, 3))
            hub_exits = 2*center - hub_entries
            
            q1 = self.top.batch_resonance_quality_fast(mb_top, hub_entries, sub_res=8)
            q2 = self.hub.batch_resonance_quality_fast(hub_entries, hub_exits, sub_res=10)
            
            for i in range(mb_size):
                if q2[i] > 0.5:
                    path = np.vstack([hub_entries[i], (hub_entries[i]+hub_exits[i])/2, hub_exits[i]])
                    self.hub.reinforce_field(path, q2[i]*0.05)
            
            q3 = self.bot.batch_resonance_quality_fast(hub_exits, mb_bot, sub_res=8)
            
            for i in range(mb_size):
                if not cached_mask[i]:
                    q = np.clip(q1[i]*gain*q3[i], 0.0, 1.0)
                    qualities[start_idx+i] = q
                    if q > self.success_threshold:
                        self.route_cache.put(tuple(mb_top[i].round(2)), tuple(mb_bot[i].round(2)), q)
                        full_path = np.vstack([mb_top[i], hub_entries[i], hub_exits[i], mb_bot[i]])
                        for layer in [self.top, self.hub, self.bot]: layer.reinforce_field(full_path, q*0.03)
            
            if start_idx % (self.cross_micro_batch * 50) == 0:
                if psutil.virtual_memory().available / 1e9 < 0.3:
                    self.route_cache.clear(); gc.collect()
        
        return qualities

    def run_turbo_test(self, n_qubits=5000, epochs=5):
        """🚀 Турбо-тест: разумные параметры!"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 ТУРБО-ТЕСТ v1.3.2: {n_qubits}q × {epochs} эпох")
        logger.info(f"{'='*70}")
        
        initial_mem = psutil.Process(os.getpid()).memory_info().rss / 1e9
        pos_top, pos_bot, et, eb, ec = self.generate_dual_topology(n_qubits)
        
        total_start = time.time()
        
        for epoch in range(epochs):
            epoch_start = time.time()
            self.success_threshold = min(0.85, 0.6 + epoch * self.threshold_growth)
            
            # 🧠 УМНЫЙ ХАОС
            self._smart_chaos_trigger(epoch)
            
            # Подготовка
            ts = np.array([pos_top[u] for u,_ in et], dtype=np.float64)
            te = np.array([pos_top[v] for _,v in et], dtype=np.float64)
            bs = np.array([pos_bot[u] for u,_ in eb], dtype=np.float64)
            be = np.array([pos_bot[v] for _,v in eb], dtype=np.float64)
            
            q_top = self.top.batch_resonance_quality_fast(ts, te)
            del ts, te; gc.collect()
            
            q_bot = self.bot.batch_resonance_quality_fast(bs, be)
            del bs, be; gc.collect()
            
            # 🚀 ТУРБО-ХАБ ПРОВЕРКА
            tq_avg = np.mean(q_top) if len(q_top) else 0
            bq_avg = np.mean(q_bot) if len(q_bot) else 0
            self._turbo_hub_check(tq_avg, bq_avg)
            
            q_cross = self.route_cross_with_amplifier(pos_top, pos_bot, ec, epoch)
            gc.collect()
            
            epoch_time = time.time() - epoch_start
            
            tsr = np.sum(q_top > self.success_threshold) / max(1, len(et))
            bsr = np.sum(q_bot > self.success_threshold) / max(1, len(eb))
            csr = np.sum(q_cross > self.success_threshold) / max(1, len(ec))
            
            cq = np.mean(q_cross) if len(q_cross) else 0
            
            anomaly = "НОРМА"
            if cq < 0.1: anomaly = "КРИТИЧЕСКИ"
            if epoch > 0 and cq < self.history['cross_quality'][-1]*0.8: anomaly = "ДЕГРАДАЦИЯ"
            if self.turbo_mode: anomaly = "🚀 ТУРБО"
            
            for h, v in [
                ('epoch', epoch+1), ('top_quality', tq_avg), ('bot_quality', bq_avg),
                ('cross_quality', cq), ('temperature', self.chip_temp),
                ('cache_hit_rate', self.route_cache.hit_rate()), ('gain_used', self.current_gain),
                ('top_success_rate', tsr), ('bot_success_rate', bsr),
                ('cross_success_rate', csr), ('anomalies', anomaly)
            ]: self.history[h].append(v)
            
            # 📈 АДАПТИВНЫЙ GAIN — РАЗ ЗА ЭПОХУ!
            self._update_adaptive_gain(epoch)
            
            # Гомеостаз
            avg_q = (tq_avg + bq_avg + cq) / 3
            coherence = avg_q**2
            self.chip_temp += ((1-coherence)*30 - min(50, (1-coherence)*45)) * 0.1
            self.chip_temp = np.clip(self.chip_temp, 20, 80)
            self.entropy_balance = np.clip(self.entropy_balance + (1-coherence)*0.1, 0, 10)
            self.homeostasis_quality = coherence * (1 - abs(50-self.chip_temp)/50)
            
            mem = psutil.Process(os.getpid()).memory_info().rss / 1e9
            turbo_icon = "🚀" if self.turbo_mode else "✅"
            
            logger.info(f"  {turbo_icon} Эпоха {epoch+1}/{epochs} [порог {self.success_threshold:.0%}]: "
                       f"ВЕРХ {tsr:.1%} | НИЗ {bsr:.1%} | ХАБ {csr:.1%} avg={cq:.3f}")
            logger.info(f"    Gain: {self.current_gain:.1f}× | Кэш: {self.route_cache.hit_rate():.0%} | "
                       f"Память: {mem:.2f}GB | {epoch_time:.1f}с")
        
        total_time = time.time() - total_start
        final_mem = psutil.Process(os.getpid()).memory_info().rss / 1e9
        
        # Быстрый отчёт
        cs = self.history['cross_success_rate']
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 ИТОГИ v1.3.2:")
        logger.info(f"⏱️  Время: {total_time:.1f} сек ({total_time/epochs:.1f} сек/эпоха)")
        logger.info(f"💾 Память: {initial_mem:.2f}GB → {final_mem:.2f}GB (Δ{final_mem-initial_mem:+.2f}GB)")
        logger.info(f"🌡️  Темп-ра: {self.chip_temp:.0f}°C | 🌀 Энтропия: {self.entropy_balance:.2f}")
        logger.info(f"📈 ХАБ: {cs[0]:.1%} → {cs[-1]:.1%} (Δ{cs[-1]-cs[0]:+.1%})")
        logger.info(f"📈 Gain: {self.history['gain_used'][0]:.1f}× → {self.history['gain_used'][-1]:.1f}×")
        logger.info(f"🧯 Хаос: {self.chaos_applied} раз | 🚀 Турбо: {'ДА' if any(self.history['turbo']) else 'НЕТ'}")
        logger.info(f"{'='*70}")


def turbo_test():
    """🚀 Быстрый тест 1000q, затем основной 5000q × 5 эпох."""
    logger.info("\n" + "="*70)
    logger.info("🚀 ТУРБО-НАБЛЮДАТЕЛЬ v1.3.2 HOTFIX")
    logger.info("="*70)
    
    logger.info("\n🧪 БЫСТРЫЙ ТЕСТ: 1000q × 3 эпохи")
    hub = TurboTEES(field_size=32, cache_size=300)
    hub.run_turbo_test(n_qubits=1000, epochs=3)
    
    logger.info("\n\n🚀 ОСНОВНОЙ ТЕСТ: 5000q × 5 эпох")
    hub = TurboTEES(field_size=32, cache_size=500)
    hub.run_turbo_test(n_qubits=5000, epochs=5)


if __name__ == "__main__":
    os.environ['OMP_NUM_THREADS'] = str(os.cpu_count())
    if NUMBA_AVAILABLE: os.environ['NUMBA_NUM_THREADS'] = str(os.cpu_count())
    turbo_test()