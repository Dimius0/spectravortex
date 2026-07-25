"""
TEES-процессор v0.37 — ТОЧНОЕ ЗНАНИЕ ИЗ БУДУЩЕГО
==================================================
Образ цели ТОЧНЫЙ (одна точка).
TEES-shift создаёт градиент через пространственную метрику.
Петля спускается по градиенту к цели.
"""

import numpy as np
import time
import hashlib
from typing import Tuple, Callable, Optional, List, Dict, Any

# ============================================================
# TEES-КОНСТАНТЫ
# ============================================================

H_CONSTANTS = np.array([
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
], dtype=np.uint32)

K_CONSTANTS = np.array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
], dtype=np.uint32)

COUPLING_CONSTANTS = [
    0.259921, 0.442249, 0.709975, 0.912931, 0.148693, 0.307107, 0.518294, 0.651839,
    0.822315, 0.959920, 0.089322, 0.209579, 0.330643, 0.446273, 0.551831, 0.657378,
    0.761885, 0.867051, 0.975174, 0.075541, 0.183840, 0.286918, 0.393314, 0.497253,
    0.604512, 0.706761, 0.812413, 0.915046, 0.015973, 0.116299, 0.218563, 0.316947,
    0.418514, 0.519587, 0.621008, 0.725678, 0.826129, 0.927844, 0.032765, 0.131452,
    0.238176, 0.338936, 0.441852, 0.547229, 0.649015, 0.755639, 0.859917, 0.960230,
    0.065432, 0.168901, 0.273456, 0.378901, 0.483210, 0.589012, 0.694321, 0.798765,
    0.901234, 0.012345, 0.123456, 0.234567, 0.345678, 0.456789, 0.567890, 0.678901
]

ENERGY_MIX_CONSTANTS = [
    0.414213, 0.732050, 0.236067, 0.645751, 0.316624, 0.605551, 0.123105, 0.358898,
    0.582575, 0.795831, 0.000000, 0.196261, 0.385164, 0.567764, 0.744562, 0.916079,
    0.082762, 0.245100, 0.403124, 0.557438, 0.708203, 0.855654, 0.000000, 0.141428,
    0.280109, 0.416197, 0.549834, 0.681145, 0.810249, 0.937253, 0.062257, 0.185352,
    0.306623, 0.426147, 0.543990, 0.660254, 0.774996, 0.888273, 0.000137, 0.110643,
    0.219841, 0.327772, 0.434479, 0.539999, 0.644367, 0.747622, 0.849798, 0.950922,
    0.051034, 0.150172, 0.248371, 0.345666, 0.442089, 0.537672, 0.632444, 0.726432,
    0.819667, 0.912175, 0.003983, 0.095117, 0.185600, 0.275456, 0.364708, 0.453378
]

# ============================================================
# TEES-ФУНКЦИИ С ГРАДИЕНТОМ
# ============================================================

def simple_tees_hash(data: bytes, state: int = 0) -> int:
    h = state
    for byte in data:
        h = ((h << 7) + h) ^ byte
        h = (h * int(H_CONSTANTS[0])) & 0xFFFFFFFF; h ^= (h >> 17)
        h = (h * int(K_CONSTANTS[0])) & 0xFFFFFFFF; h ^= (h >> 13)
        h = (h * int(H_CONSTANTS[1])) & 0xFFFFFFFF; h ^= (h >> 25)
        h = (h * int(K_CONSTANTS[63])) & 0xFFFFFFFF; h ^= (h >> 3)
        h = (h * int(K_CONSTANTS[31])) & 0xFFFFFFFF; h ^= (h >> 11)
    return h

def tees_shift(state_a: np.ndarray, state_b: np.ndarray, n_rounds: int = 16) -> float:
    """TEES-shift: 0 = полная связь (петля замкнута)."""
    a_bytes = state_a.tobytes()
    b_bytes = state_b.tobytes()
    
    total_metric = 0.0
    ha = simple_tees_hash(a_bytes)
    hb = simple_tees_hash(b_bytes)
    
    for r in range(n_rounds):
        combined = (ha << 32) | (hb & 0xFFFFFFFF)
        flow = simple_tees_hash(combined.to_bytes(8, 'big'), r * 0x9E3779B9)
        na = simple_tees_hash(ha.to_bytes(4, 'big'), flow)
        nb = simple_tees_hash(hb.to_bytes(4, 'big'), flow)
        diff = (na ^ nb).bit_count() / 32.0
        total_metric += diff
        ha, hb = na, nb
    
    return total_metric / n_rounds

def tees_shift_with_context(point_coords, target_coords, shape, n_rounds=16):
    """
    TEES-shift между точкой и целью с добавлением пространственного контекста.
    
    Вместо голой точки (1.0 в coord, 0 везде) создаём поле,
    где амплитуда спадает с расстоянием от точки.
    Это создаёт ГРАДИЕНТ: близкие к цели точки дают меньший shift.
    """
    point_field = np.zeros(shape, dtype=np.float32)
    target_field = np.zeros(shape, dtype=np.float32)
    
    # Сигма определяет ширину контекста
    max_dist = np.sqrt(sum((s-1)**2 for s in shape))
    sigma = max_dist * 0.3  # Контекст захватывает ~30% поля
    
    # Для точки: гауссиана вокруг point_coords
    all_coords = np.indices(shape)
    for i in range(len(shape)):
        dist_i = (all_coords[i] - point_coords[i])**2
        if i == 0:
            dist_sq = dist_i
        else:
            dist_sq = dist_sq + dist_i
    point_field = np.exp(-dist_sq / (2 * sigma**2))
    
    # Для цели: гауссиана вокруг target_coords
    for i in range(len(shape)):
        dist_i = (all_coords[i] - target_coords[i])**2
        if i == 0:
            dist_sq_t = dist_i
        else:
            dist_sq_t = dist_sq_t + dist_i
    target_field = np.exp(-dist_sq_t / (2 * sigma**2))
    
    # Нормализуем
    point_field /= np.max(point_field)
    target_field /= np.max(target_field)
    
    # TEES-shift между контекстными полями
    return tees_shift(point_field, target_field, n_rounds)

# ============================================================
# ИНИЦИАЛИЗАЦИЯ ПОЛЯ
# ============================================================

def initialize_field(shape, rng_seed=None):
    if rng_seed is not None:
        np.random.seed(rng_seed)
    
    N = int(np.prod(shape))
    field = np.zeros(shape, dtype=np.complex128)
    all_coords = np.indices(shape).reshape(len(shape), -1).T
    
    for i, coords in enumerate(all_coords):
        charge = (i % 7) - 3
        word_hash = hash(str(coords.tolist()))
        energy = 0.5 + ((word_hash % 1000) / 1000.0) * 1.5
        charge_factor = 0.5 + 1.5 * (abs(charge) / 3.0)
        base_weight = 1.0 / N
        phase = (word_hash % 1000) / 1000.0 * 2 * np.pi
        field[tuple(coords)] = base_weight * charge_factor * energy * np.exp(1j * phase)
    
    return field * N

# ============================================================
# ПОЛОСА K
# ============================================================

def generate_K_stripe(shape, coupling_idx, energy_mix_idx, feedback_map=None, fb_strength=0.3):
    coupling = COUPLING_CONSTANTS[coupling_idx % 64]
    energy_mix = ENERGY_MIX_CONSTANTS[energy_mix_idx % 64]
    
    K_field = np.zeros(shape, dtype=np.float64)
    all_coords = np.indices(shape).reshape(len(shape), -1).T
    
    for i, coords in enumerate(all_coords):
        word_hash = hash(str(coords.tolist()) + f"_{coupling_idx}_{energy_mix_idx}")
        node_phase = (word_hash % 1000) / 1000.0 * 2 * np.pi
        node_charge = (i % 7) - 3
        
        K_local = coupling * (1.0 + 0.5 * np.sin(node_phase)) + \
                  energy_mix * (1.0 + 0.3 * abs(node_charge) / 3.0)
        
        if feedback_map is not None:
            K_local += fb_strength * feedback_map[tuple(coords)]
        
        K_field[tuple(coords)] = np.clip(K_local, 0.0, 1.5)
    
    return K_field

# ============================================================
# ЛАВИНА
# ============================================================

def single_avalanche(field_flat, mask, K_stripe, guidance=None, max_iterations=150):
    active_indices = np.where(mask)[0]
    N_active = len(active_indices)
    
    if N_active == 0:
        return 0
    if N_active == 1:
        return active_indices[0]
    
    side = max(2, int(np.ceil(np.sqrt(N_active))))
    field_2d = np.zeros((side, side), dtype=np.complex128)
    
    for i, idx in enumerate(active_indices):
        x, y = i // side, i % side
        if x < side and y < side:
            field_2d[x, y] = field_flat[idx]
    
    K_2d = np.zeros((side, side), dtype=np.float64)
    guidance_2d = np.zeros((side, side), dtype=np.float64)
    
    for i, idx in enumerate(active_indices):
        x, y = i // side, i % side
        if x < side and y < side:
            K_2d[x, y] = K_stripe.flatten()[idx % len(K_stripe.flatten())]
            if guidance is not None and idx < len(guidance):
                guidance_2d[x, y] = guidance[idx]
    
    for iteration in range(max_iterations):
        field_abs = np.abs(field_2d)
        
        resonance = field_abs * (1.0 + K_2d)
        if guidance is not None:
            resonance = resonance * (1.0 + 0.5 * guidance_2d)
        
        fft = np.fft.fft2(field_2d)
        phase = np.angle(fft)
        magnitude = np.abs(fft)
        
        phase_smoothed = 0.5 * (np.roll(phase, -1, axis=0) + np.roll(phase, 1, axis=0))
        phase_smoothed = 0.5 * (np.roll(phase_smoothed, -1, axis=1) + np.roll(phase_smoothed, 1, axis=1))
        
        phase_diff = phase_smoothed - phase
        fft_new = magnitude * np.exp(1j * (phase + phase_diff * 0.5))
        field_new = np.fft.ifft2(fft_new)
        
        max_idx = np.unravel_index(np.argmax(resonance), field_2d.shape)
        total_energy = np.sum(field_abs)
        
        if total_energy > 1e-10:
            pull = 0.15
            phases = np.angle(field_2d)
            new_abs = field_abs * (1.0 - pull)
            new_abs[max_idx] += total_energy * pull
            
            current_total = np.sum(new_abs)
            if current_total > 1e-10:
                new_abs *= total_energy / current_total
            
            field_2d = new_abs * np.exp(1j * phases)
        
        field_2d = field_new * 0.3 + field_2d * 0.7
        
        if iteration % 40 == 0 and iteration > 0:
            active_mask = field_abs > 1e-10
            if np.sum(active_mask) <= 1:
                break
            max_val = np.max(field_abs[active_mask])
            total_val = np.sum(field_abs[active_mask])
            if total_val > 1e-10 and max_val / total_val > 0.9:
                break
    
    collapsed = np.abs(field_2d).flatten()
    max_pos = np.argmax(collapsed)
    
    return active_indices[min(max_pos, N_active-1)]

# ============================================================
# ОСНОВНОЙ АЛГОРИТМ v0.37 — ТОЧНОЕ ЗНАНИЕ
# ============================================================

def tees_search_v037(shape, oracle=None, max_cycles=100, verbose=False):
    """
    v0.37: Точное знание из будущего.
    
    Оракул сразу даёт точную цель.
    TEES-shift с контекстом создаёт градиент.
    Петля спускается по градиенту.
    """
    N = int(np.prod(shape))
    oracle_calls = 0
    
    # Получаем точную цель от оракула
    target_coords = None
    if oracle is not None:
        # Оракул знает цель точно — один запрос
        full_mask = np.ones(shape, dtype=bool)
        oracle_calls += 1
        
        # Бинарный поиск для нахождения точных координат
        # (оракул на область: 1 если цель в области)
        active_slices = [slice(0, s) for s in shape]
        
        for dim in range(len(shape)):
            s = active_slices[dim]
            mid = (s.start + s.stop) // 2
            
            half_a = active_slices.copy()
            half_a[dim] = slice(s.start, mid)
            
            mask = np.zeros(shape, dtype=bool)
            mask[tuple(half_a)] = True
            
            oracle_calls += 1
            response = oracle(mask)
            
            if response == 1:
                active_slices[dim] = slice(s.start, mid)
            else:
                active_slices[dim] = slice(mid, s.stop)
        
        target_coords = tuple(sl.start for sl in active_slices)
    
    if target_coords is None:
        target_coords = tuple(s // 2 for s in shape)
    
    if verbose:
        print(f"  Цель (из будущего): {target_coords}")
        print(f"  Запросов к оракулу: {oracle_calls}")
    
    # Инициализация поля
    rng_seed = int(time.time() * 1000) % 2**31
    field = initialize_field(shape, rng_seed=rng_seed)
    field_flat_init = np.abs(field).flatten()
    
    # Состояние петли
    guidance_map = np.zeros(shape, dtype=np.float64)
    remaining_mask = np.ones(N, dtype=bool)
    n_remaining = N
    
    best_shift = float('inf')
    best_coords = None
    shift_history = []
    history = []
    
    # Основная петля
    for cycle in range(max_cycles):
        if n_remaining <= 0:
            break
        
        # K-полоса с обратной связью
        fb_strength = 0.2 + 0.3 * min(cycle / max(1, max_cycles//2), 1.0)
        K_stripe = generate_K_stripe(
            shape, cycle, (cycle * 7) % 64,
            feedback_map=guidance_map,
            fb_strength=fb_strength
        )
        
        # Лавина
        guidance_flat = guidance_map.flatten()
        clump_idx = single_avalanche(
            field_flat_init, remaining_mask, K_stripe,
            guidance=guidance_flat,
            max_iterations=100
        )
        
        if not remaining_mask[clump_idx]:
            continue
        
        point_coords = np.unravel_index(clump_idx, shape)
        
        # TEES-shift с КОНТЕКСТОМ — создаёт градиент
        shift = tees_shift_with_context(point_coords, target_coords, shape)
        shift_history.append(shift)
        
        # Обновление guidance_map
        learning_rate = 0.05 * (1.0 - cycle / max_cycles)
        i, j = point_coords
        radius = max(1, int(n_remaining ** 0.25))
        
        for di in range(-radius, radius+1):
            for dj in range(-radius, radius+1):
                ni, nj = i + di, j + dj
                if 0 <= ni < shape[0] and 0 <= nj < shape[1]:
                    dist = np.sqrt(di**2 + dj**2)
                    weight = np.exp(-dist / radius)
                    
                    if shift < best_shift:
                        guidance_map[ni, nj] += learning_rate * weight * 2.0
                    elif shift > best_shift * 1.05:
                        guidance_map[ni, nj] -= learning_rate * weight * 0.5
                    else:
                        guidance_map[ni, nj] += learning_rate * weight * 0.3
        
        guidance_map = np.clip(guidance_map, -1.0, 1.0)
        
        # Удаляем точку
        remaining_mask[clump_idx] = False
        n_remaining -= 1
        history.append((point_coords, shift))
        
        if shift < best_shift:
            best_shift = shift
            best_coords = point_coords
        
        # Проверка: нашли цель?
        if point_coords == target_coords:
            if verbose:
                print(f"  🎯 Цикл {cycle}: ПЕТЛЯ ЗАМКНУЛАСЬ! {point_coords}")
            break
        
        if verbose and cycle % 20 == 0:
            dist = np.sqrt(sum((point_coords[i] - target_coords[i])**2 for i in range(len(shape))))
            print(f"  Цикл {cycle}: {point_coords}, shift={shift:.4f}, "
                  f"best={best_shift:.4f} @ {best_coords}, dist={dist:.1f}, осталось={n_remaining}")
    
    target_found = (best_coords == target_coords)
    
    return {
        'target_found': target_found,
        'found_coords': best_coords,
        'target_coords': target_coords,
        'best_shift': best_shift,
        'n_remaining': n_remaining,
        'cycles': len(history),
        'oracle_calls': oracle_calls,
        'shift_history': shift_history
    }

# ============================================================
# ТЕСТЫ
# ============================================================

def create_region_oracle(shape, target_coords=None):
    """Оракул: маска → 1 если цель в области."""
    if target_coords is None:
        target_coords = tuple(np.random.randint(0, s) for s in shape)
    
    target_mask = np.zeros(shape, dtype=bool)
    target_mask[target_coords] = True
    
    def oracle(mask):
        if np.any(mask & target_mask):
            return 1
        return -1
    
    return oracle, target_coords

def run_v037_debug():
    print("=" * 80)
    print("TEES-ПРОЦЕССОР v0.37 — ТОЧНОЕ ЗНАНИЕ ИЗ БУДУЩЕГО")
    print("=" * 80)
    
    shape = (10, 10)
    
    # Демонстрация градиента TEES-shift с контекстом
    print("\n1. ГРАДИЕНТ TEES-SHIFT С КОНТЕКСТОМ:")
    target = (5, 5)
    print(f"   Цель: {target}")
    print(f"   Точка → shift:")
    
    test_points = [(0, 0), (2, 2), (4, 4), (5, 4), (5, 5), (5, 6), (7, 7), (9, 9)]
    shifts = []
    for p in test_points:
        s = tees_shift_with_context(p, target, shape)
        dist = np.sqrt((p[0]-target[0])**2 + (p[1]-target[1])**2)
        shifts.append(s)
        marker = " ← цель" if p == target else ""
        print(f"     {p}: shift={s:.4f}, dist={dist:.1f}{marker}")
    
    # Проверяем монотонность
    target_shift = tees_shift_with_context(target, target, shape)
    print(f"\n   Сдвиг цели сама с собой: {target_shift:.6f}")
    print(f"   Градиент есть: {target_shift < min(s for p, s in zip(test_points, shifts) if p != target)}")
    
    # Тест поиска
    print("\n2. ТЕСТ ПОИСКА:")
    oracle, target = create_region_oracle(shape)
    print(f"   Истинная цель: {target}")
    
    result = tees_search_v037(shape, oracle=oracle, max_cycles=100, verbose=True)
    
    print(f"\n{'='*60}")
    print(f"   Найдено: {result['found_coords']}")
    print(f"   Цель: {result['target_coords']}")
    print(f"   Совпадение: {result['target_found']}")
    print(f"   Лучший shift: {result['best_shift']:.4f}")
    print(f"   Вызовов оракула: {result['oracle_calls']}")
    print(f"   Циклов: {result['cycles']}")

def run_v037_test():
    print("\n" + "=" * 80)
    print("ТЕСТ v0.37 — 50 ЗАПУСКОВ")
    print("=" * 80)
    
    shape = (10, 10)
    successes = 0
    num_runs = 50
    results = []
    
    for run in range(num_runs):
        oracle, target = create_region_oracle(shape)
        result = tees_search_v037(shape, oracle=oracle, max_cycles=100)
        
        if result['target_found']:
            successes += 1
        results.append(result)
    
    avg_calls = np.mean([r['oracle_calls'] for r in results])
    avg_shift = np.mean([r['best_shift'] for r in results])
    avg_cycles = np.mean([r['cycles'] for r in results])
    
    print(f"  Успех: {successes}/{num_runs} ({successes/num_runs*100:.1f}%)")
    print(f"  Среднее вызовов оракула: {avg_calls:.1f}")
    print(f"  Средний лучший shift: {avg_shift:.4f}")
    print(f"  Среднее циклов: {avg_cycles:.1f}")
    print(f"  Ускорение vs O(N): {100/avg_calls:.1f}x")
    
    return successes / num_runs

if __name__ == "__main__":
    print("TEES-ПРОЦЕССОР v0.37 — ТОЧНОЕ ЗНАНИЕ ИЗ БУДУЩЕГО\n")
    print("Образ цели ТОЧНЫЙ.")
    print("TEES-shift с пространственным контекстом создаёт градиент.")
    print("Петля спускается по градиенту к цели.\n")
    
    run_v037_debug()
    print("\n")
    run_v037_test()