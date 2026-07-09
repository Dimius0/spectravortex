#!/usr/bin/env python3
"""
seed_resonator_v1441_vmmp_permuted_sha256.py — v14.41: VMMP TURBULENCE + PERMUTED SHA-256
========================================================================================
v14.41: Полный комбайн!
        ✅ Вихри ВММП из BIP39 слов
        ✅ Турбулентность ВММП: ∇⁴ψ = 0, τ = ∮(dθ/2π)
        ✅ Рекурсивный SHA-256 с ПЕРЕСТАВЛЕННЫМИ nothing-up-my-sleeve константами
        ✅ Детерминизм: всё вычислимо, всё воспроизводимо
        ✅ Защита от бэкдора: порядок K и H уникален для каждого кошелька
        
        🔧 Можно заменить H_CONSTANTS и K_CONSTANTS на другие nothing-up-my-sleeve
           числа (например, √11, √13... или кубические корни других простых).
           Это сделает систему ещё более непредсказуемой для атакующего.
"""

import sys, argparse, random, hashlib, struct, hmac, time, os
import numpy as np
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from bip39_words import BIP39_WORDS, generate_valid_bip39_phrase
except ImportError:
    logger.error("Не удалось импортировать bip39_words")
    sys.exit(1)

# ============================================================================
# NOTHING-UP-MY-SLEEVE КОНСТАНТЫ SHA-256
# ============================================================================
# 🔧 Можно заменить на другие nothing-up-my-sleeve числа:
#    H: √2, √3, √5, √7, √11, √13, √17, √19 (первые 8 простых)
#    K: кубические корни первых 64 простых чисел
#    Альтернативы:
#    - Использовать √p для других простых (√23, √29, √31...)
#    - Использовать кубические корни других последовательностей
#    - Смешать H и K: использовать √p для H и ∛p для K других простых
#    Чем неожиданнее набор — тем сложнее атакующему предсказать TEES-профиль.

H_CONSTANTS = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
]

K_CONSTANTS = [
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
]

# ============================================================================
# ГЛОБАЛЬНЫЙ КЭШ ВИХРЕЙ
# ============================================================================

class VortexCache:
    def __init__(self):
        self._caches: Dict[str, Dict] = {}
    
    def _get_cache_key(self, config: 'VortexConfig') -> str:
        return f"gs{config.grid_size}_dtype{config.dtype.__name__}"
    
    def get_or_create(self, word: str, dictionary: List[str], 
                      config: 'VortexConfig') -> np.ndarray:
        cache_key = self._get_cache_key(config)
        
        if cache_key not in self._caches:
            self._caches[cache_key] = {}
        
        cache = self._caches[cache_key]
        
        if word not in cache:
            try:
                word_idx = dictionary.index(word)
            except ValueError:
                word_idx = 0
            cache[word] = self._create_vortex(word, word_idx, config)
        
        return cache[word].copy()
    
    def _create_vortex(self, word: str, word_idx: int, 
                       config: 'VortexConfig') -> np.ndarray:
        X, Y = config.X, config.Y
        
        diameter = 0.15 + (word_idx / 2047.0) * 0.6
        prefix = word[:4]
        phase_seed = sum(ord(c) * (i+1) for i, c in enumerate(prefix))
        freq = 3.0 + (phase_seed % 100) / 100.0 * 5.0
        phase = (phase_seed % 1000) / 1000.0 * 2 * np.pi
        intensity = 0.3 + (word_idx % 200) / 200.0 * 0.7
        
        vortex = (intensity * np.sin(freq * config.Theta + phase) * 
                 np.exp(-config.R**2 / (2 * diameter**2)))
        
        for i, char in enumerate(prefix):
            kx = 2 + ord(char) % 7
            ky = 2 + (ord(char) // 7) % 7
            vortex += 0.05 * np.sin(kx * X + ky * Y + i)
        
        std = vortex.std()
        if std > 1e-10:
            vortex = (vortex - vortex.mean()) / std
        
        return vortex.astype(config.dtype)
    
    def clear(self, config: Optional['VortexConfig'] = None):
        if config is None:
            self._caches.clear()
        else:
            self._caches.pop(self._get_cache_key(config), None)


VORTEX_CACHE = VortexCache()


# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

@dataclass
class VortexConfig:
    grid_size: int = 16
    temperature: float = 0.15
    viscosity: float = 0.02
    turbulence_threshold: float = 0.5
    turbulence_intensity: float = 0.3
    recursion_depth: int = 3  # глубина рекурсии для перестановки констант
    min_rounds: int = 20
    max_rounds: int = 2048
    convergence_threshold: float = 0.005
    n_jobs: int = -1
    dtype: type = np.float32
    
    def __post_init__(self):
        gs = int(self.grid_size)
        self.x = np.linspace(-1, 1, gs)
        self.y = np.linspace(-1, 1, gs)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.R = np.sqrt(self.X**2 + self.Y**2)
        self.R_safe = np.maximum(self.R, 1e-8)
        self.Theta = np.arctan2(self.Y, self.X)
        
        self._precompute_pressure_fields()
        self._precompute_fft_operators()
        self._precompute_laplacian()
        
        self.boundary_mask = np.exp(-self.R**2 / 0.1).astype(self.dtype)
    
    def _precompute_pressure_fields(self):
        self.cached_pressure = {}
        for t, k_val in enumerate(K_CONSTANTS):
            pressure_val = (k_val % 1000) / 1000.0 * 0.1
            freq = k_val % 10 + 1
            self.cached_pressure[t] = (
                pressure_val * 
                np.sin(self.Theta * freq) * 
                np.exp(-self.R**2 / 0.1)
            ).astype(self.dtype)
    
    def _precompute_fft_operators(self):
        kx = np.fft.fftfreq(self.grid_size)
        ky = np.fft.fftfreq(self.grid_size)
        KX, KY = np.meshgrid(kx, ky, indexing='ij')
        
        self.laplacian_fft = (-4 * np.pi**2 * (KX**2 + KY**2)).astype(self.dtype)
        self.viscosity_fft = (1 + self.viscosity * self.laplacian_fft).astype(self.dtype)
    
    def _precompute_laplacian(self):
        self.laplacian2_fft = self.laplacian_fft ** 2
    
    def get_pressure(self, round_num: int) -> np.ndarray:
        return self.cached_pressure[round_num % 64]


# ============================================================================
# ДЕТЕРМИНИРОВАННЫЕ ОПЕРАЦИИ
# ============================================================================

def word_to_vortex_deterministic(word: str, dictionary: List[str], 
                                  config: VortexConfig) -> np.ndarray:
    return VORTEX_CACHE.get_or_create(word, dictionary, config)


def batch_word_to_vortex(words: List[str], dictionary: List[str], 
                         config: VortexConfig) -> np.ndarray:
    vortices = [word_to_vortex_deterministic(w, dictionary, config) for w in words]
    return np.array(vortices, dtype=config.dtype)


def measure_diameter_deterministic(vortex: np.ndarray, config: VortexConfig) -> float:
    gy, gx = np.gradient(vortex)
    gmag = np.sqrt(gx**2 + gy**2)
    r_weighted = config.R * gmag
    return float(np.sum(r_weighted) / (np.sum(gmag) + 1e-10)) * 2


# ============================================================================
# ВММП-ТУРБУЛЕНТНОСТЬ
# ============================================================================

def compute_topological_charge(vortex: np.ndarray, config: VortexConfig) -> float:
    gy, gx = np.gradient(vortex)
    phase = np.arctan2(gy, gx + 1e-10)
    dphase_dx = np.diff(phase, axis=1)
    dphase_dy = np.diff(phase, axis=0)
    circulation_x = np.sum(dphase_dx[:-1, :])
    circulation_y = np.sum(dphase_dy[:, :-1])
    return float((circulation_x + circulation_y) / (2 * np.pi))


def compute_vortex_energy(vortex: np.ndarray, config: VortexConfig) -> float:
    gy, gx = np.gradient(vortex)
    energy_density = gx**2 + gy**2
    return float(np.sum(energy_density))


def vmmp_turbulence(vortices: np.ndarray, config: VortexConfig) -> np.ndarray:
    n = vortices.shape[0]
    
    for i in range(n):
        tau = compute_topological_charge(vortices[i], config)
        energy = compute_vortex_energy(vortices[i], config)
        
        if abs(tau) < config.turbulence_threshold or energy > 1.0:
            # Детерминированный выбор партнёра по ближайшему заряду
            best_partner = i
            best_diff = float('inf')
            for j in range(n):
                if i != j:
                    tau_j = compute_topological_charge(vortices[j], config)
                    diff = abs(abs(tau) - abs(tau_j))
                    if diff < best_diff:
                        best_diff = diff
                        best_partner = j
            
            # Слияние через бигармонический оператор
            fft_i = np.fft.fft2(vortices[i].astype(np.complex128))
            fft_partner = np.fft.fft2(vortices[best_partner].astype(np.complex128))
            
            biharm_i = fft_i * config.laplacian2_fft
            biharm_partner = fft_partner * config.laplacian2_fft
            
            merged_fft = (biharm_i + biharm_partner) * 0.5
            merged = np.real(np.fft.ifft2(merged_fft)).astype(config.dtype)
            
            turbulence_energy = config.turbulence_intensity * (1.0 - abs(tau))
            
            vortices[i] = vortices[i] * (1.0 - turbulence_energy) + merged * turbulence_energy
            vortices[best_partner] = vortices[best_partner] * (1.0 - turbulence_energy * 0.5)
    
    return vortices


# ============================================================================
# SHA-256 С ПЕРЕСТАВЛЕННЫМИ КОНСТАНТАМИ
# ============================================================================

def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def sha256_permuted(message: bytes, h_order: List[int], k_order: List[int]) -> bytes:
    """
    SHA-256 с переставленными nothing-up-my-sleeve константами.
    """
    H = [H_CONSTANTS[i] for i in h_order]
    K = [K_CONSTANTS[i] for i in k_order]
    
    msg_bytes = bytearray(message)
    msg_len_bits = len(msg_bytes) * 8
    msg_bytes.append(0x80)
    while (len(msg_bytes) + 8) % 64 != 0:
        msg_bytes.append(0x00)
    msg_bytes.extend(struct.pack('>Q', msg_len_bits))
    
    blocks = [msg_bytes[i:i+64] for i in range(0, len(msg_bytes), 64)]
    
    for block in blocks:
        w = list(struct.unpack('>16I', bytes(block)))
        
        for i in range(16, 64):
            s0 = _rotr(w[i-15], 7) ^ _rotr(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = _rotr(w[i-2], 17) ^ _rotr(w[i-2], 19) ^ (w[i-2] >> 10)
            w.append((w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF)
        
        a, b, c, d, e, f, g, h = [int(x) for x in H]
        
        for i in range(64):
            S1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ (~e & g)
            temp1 = (h + S1 + ch + K[i] + w[i]) & 0xFFFFFFFF
            S0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xFFFFFFFF
            
            h = g; g = f; f = e; e = (d + temp1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (temp1 + temp2) & 0xFFFFFFFF
        
        H = [(H[i] + x) & 0xFFFFFFFF for i, x in enumerate([a, b, c, d, e, f, g, h])]
    
    return struct.pack('>8I', *[int(x) for x in H])


def recursive_sha256_permuted(message: bytes, initial_seed: bytes, depth: int = 3) -> bytes:
    """
    Рекурсивный SHA-256 с переставленными константами.
    Каждый уровень: Random(seed) → порядок H и K → SHA-256.
    """
    seed = initial_seed
    data = message
    
    for _ in range(depth):
        rng = random.Random(seed)
        h_order = rng.sample(range(8), 8)
        k_order = rng.sample(range(64), 64)
        data = sha256_permuted(data, h_order, k_order)
        seed = data
    
    return data


# ============================================================================
# СМЕСИТЕЛЬ С ВММП-ТУРБУЛЕНТНОСТЬЮ
# ============================================================================

def tees_mix_vortices_vmmp_permuted(
    vortices: np.ndarray, 
    key: bytes, 
    config: VortexConfig, 
    round_num: int
) -> Tuple[np.ndarray, np.ndarray]:
    
    n = vortices.shape[0]
    key_hash = np.frombuffer(hashlib.sha256(key).digest(), dtype=np.uint8)
    
    # 1. ДАВЛЕНИЕ
    pressure = config.get_pressure(round_num)
    vortices = vortices + pressure[np.newaxis, :, :]
    
    # 2. ВЗАИМОДЕЙСТВИЕ
    if n > 1:
        mix_coeffs = key_hash[:n].astype(config.dtype) / 255.0 * 0.3
        left_shifted = np.roll(vortices, 1, axis=0)
        right_shifted = np.roll(vortices, -1, axis=0)
        vortices[1:] += mix_coeffs[1:, np.newaxis, np.newaxis] * left_shifted[1:]
        vortices[:-1] += mix_coeffs[:-1, np.newaxis, np.newaxis] * right_shifted[:-1]
    
    # 3. ФАЗОВАЯ МОДУЛЯЦИЯ
    phases = key_hash[:n*2:2].astype(np.float64) / 255.0 * np.pi * 1.5
    fft_batch = np.fft.fft2(vortices.astype(np.complex128), axes=(1, 2))
    fft_batch *= np.exp(1j * phases[:, np.newaxis, np.newaxis])
    vortices = np.real(np.fft.ifft2(fft_batch, axes=(1, 2))).astype(config.dtype)
    
    # 4. ТЕМПЕРАТУРНАЯ НЕЛИНЕЙНОСТЬ
    vortices = np.tanh(vortices / config.temperature) * config.temperature
    
    # 5. ВЯЗКОСТЬ ЧЕРЕЗ FFT
    F_vortices = np.fft.fft2(vortices.astype(np.complex128), axes=(1, 2))
    F_vortices = F_vortices * config.viscosity_fft[np.newaxis, :, :]
    vortices = np.real(np.fft.ifft2(F_vortices, axes=(1, 2))).astype(config.dtype)
    
    # 6. ВММП-ТУРБУЛЕНТНОСТЬ
    vortices = vmmp_turbulence(vortices, config)
    
    # НОРМАЛИЗАЦИЯ
    stds = np.std(vortices, axis=(1, 2), keepdims=True)
    means = np.mean(vortices, axis=(1, 2), keepdims=True)
    vortices = np.where(stds > 1e-10, (vortices - means) / stds, vortices)
    
    final_fft = np.fft.fft2(vortices.astype(np.complex128), axes=(1, 2))
    
    return vortices, final_fft


# ============================================================================
# VMMP VORTEX SHA-256 С ПЕРЕСТАВЛЕННЫМИ КОНСТАНТАМИ
# ============================================================================

class VmmpPermutedVortexSHA256:
    """Вихревой SHA-256 с ВММП-турбулентностью и переставленными константами."""
    
    def __init__(self, config: VortexConfig, dictionary: List[str]):
        self.config = config
        self.dictionary = dictionary
    
    def process_phrase(self, words: List[str], phrase_str: str, 
                    verbose: bool = False) -> Dict:
        
        # 1. Вихри из BIP39 слов
        vortices = batch_word_to_vortex(words, self.dictionary, self.config)
        seed_diameters = [measure_diameter_deterministic(v, self.config) 
                        for v in vortices]
        
        states = [{'field': v, 'diameter_history': [d]} 
                for v, d in zip(vortices, seed_diameters)]
        
        # 2. BIP32 ключи
        master_key = seed_to_master_key(phrase_str)
        extended_key = derive_key(master_key)
        child_key = derive_key(extended_key)
        address_key = derive_key(child_key, 1)
        keys = [master_key, extended_key, child_key, address_key]
        
        level_names = ['Master', 'Extended', 'Child', 'Final']
        all_diameters = {'Seed': seed_diameters.copy()}
        
        # 3. Вихревая динамика с ВММП-турбулентностью
        global_round = 0
        total_rounds_used = 0
        
        for level_idx, (key, level_name) in enumerate(zip(keys, level_names)):
            current_fields = np.array([s['field'] for s in states], dtype=self.config.dtype)
            
            target_rounds = self._get_target_rounds(level_idx)
            round_check_interval = max(5, target_rounds // 20)
            
            prev_fields = None
            converged = False
            
            if verbose:
                logger.info(f"Уровень {level_name}: цель {target_rounds} раундов")
            
            for r in range(target_rounds):
                current_fields, _ = tees_mix_vortices_vmmp_permuted(
                    current_fields, key, self.config, global_round
                )
                global_round += 1
                
                if (r >= self.config.min_rounds and 
                    r % round_check_interval == 0):
                    
                    if prev_fields is not None:
                        diff = np.mean(np.abs(current_fields - prev_fields))
                        if diff < self.config.convergence_threshold:
                            if verbose:
                                logger.info(f"  ✅ Сходимость на раунде {r+1} (diff={diff:.6f})")
                            total_rounds_used += r + 1
                            converged = True
                            break
                    
                    prev_fields = current_fields.copy()
            
            if not converged:
                total_rounds_used += target_rounds
            
            for i, field in enumerate(current_fields):
                states[i]['field'] = field
            
            level_diameters = []
            for state in states:
                d = measure_diameter_deterministic(state['field'], self.config)
                state['diameter_history'].append(d)
                level_diameters.append(d)
            
            all_diameters[level_name] = level_diameters
        
        # 4. Финальные диаметры → байты
        final_diameters = np.array(all_diameters['Final'], dtype=np.float32)
        vortex_state_bytes = final_diameters.tobytes()
        
        # 5. Рекурсивный SHA-256 с переставленными константами
        # Seed для перестановки = хэш от финальных диаметров
        permutation_seed = hashlib.sha256(vortex_state_bytes).digest()
        message = phrase_str.encode('utf-8')
        
        final_hash = recursive_sha256_permuted(
            message, permutation_seed, self.config.recursion_depth
        )
        
        # 6. Адрес
        final_address = key_to_address(final_hash)
        
        all_diameters['Address'] = final_address
        
        return {
            'diameters': all_diameters,
            'address': final_address,
            'total_rounds': total_rounds_used,
            'convergence_achieved': total_rounds_used < sum(
                self._get_target_rounds(i) for i in range(4)
            ),
            'hash_deterministic': hashlib.sha256(
                json.dumps({k: v for k, v in all_diameters.items() if k != 'Address'}, 
                        sort_keys=True).encode()
            ).hexdigest()[:16],
            'recursion_depth': self.config.recursion_depth
        }
    
    def _get_target_rounds(self, level_idx: int) -> int:
        targets = [2048, 80, 80, 64]
        return min(targets[level_idx], self.config.max_rounds)


# ============================================================================
# BIP32
# ============================================================================

@lru_cache(maxsize=128)
def seed_to_master_key(seed_phrase: str) -> bytes:
    seed_bytes = hashlib.pbkdf2_hmac('sha512', seed_phrase.encode('utf-8'), 
                                    b'mnemonic', 2048, 64)
    return hmac.new(b'Bitcoin seed', seed_bytes, hashlib.sha512).digest()[:32]

@lru_cache(maxsize=256)
def derive_key(key: bytes, index: int = 0) -> bytes:
    return hashlib.sha512(key + struct.pack('>I', index)).digest()[:32]

def key_to_address(key: bytes) -> str:
    sha = hashlib.sha256(key).digest()
    ripe = hashlib.new('ripemd160', sha).digest()
    prefix = b'\x00' + ripe
    checksum = hashlib.sha256(hashlib.sha256(prefix).digest()).digest()[:4]
    address_bytes = prefix + checksum
    
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    num = int.from_bytes(address_bytes, 'big')
    
    if num == 0:
        return '1'
    
    result = []
    while num > 0:
        num, rem = divmod(num, 58)
        result.append(alphabet[rem])
    
    return '1' + ''.join(reversed(result))


# ============================================================================
# ТЕСТ ДЕТЕРМИНИЗМА
# ============================================================================

def test_determinism(config: VortexConfig, dictionary: List[str]) -> bool:
    print("\n" + "="*80)
    print("  🎯 ТЕСТ ДЕТЕРМИНИЗМА (ВММП + Переставленные константы)")
    print("="*80)
    
    words = generate_valid_bip39_phrase(12)
    phrase = " ".join(words)
    
    processor = VmmpPermutedVortexSHA256(config, dictionary)
    
    results = []
    for i in range(5):
        result = processor.process_phrase(words, phrase)
        results.append(result)
    
    hashes = [r['hash_deterministic'] for r in results]
    addresses = [r['address'] for r in results]
    
    all_same_hashes = len(set(hashes)) == 1
    all_same_addresses = len(set(addresses)) == 1
    
    print(f"  Хэши идентичны: {'✅' if all_same_hashes else '❌'}")
    print(f"  Адреса идентичны: {'✅' if all_same_addresses else '❌'}")
    
    if all_same_hashes and all_same_addresses:
        print("  ✅ ПОЛНЫЙ ДЕТЕРМИНИЗМ ПОДТВЕРЖДЁН!")
        print(f"  Хэш: {hashes[0]}")
        print(f"  Адрес: {addresses[0]}")
        print(f"  Глубина рекурсии: {results[0]['recursion_depth']}")
    else:
        print("  ❌ ОБНАРУЖЕНА НЕДЕТЕРМИНИРОВАННОСТЬ!")
    
    print("="*80)
    return all_same_hashes and all_same_addresses


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="v14.41: VMMP Turbulence + Permuted SHA-256"
    )
    
    parser.add_argument("--dict-size", type=int, default=2048)
    parser.add_argument("--grid-size", type=int, default=16)
    parser.add_argument("--temperature", type=float, default=0.15)
    parser.add_argument("--viscosity", type=float, default=0.02)
    parser.add_argument("--turbulence-threshold", type=float, default=0.5)
    parser.add_argument("--turbulence-intensity", type=float, default=0.3)
    parser.add_argument("--recursion-depth", type=int, default=3,
                       help="Глубина рекурсии для перестановки констант")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dtype", type=str, default="float32",
                    choices=["float32", "float64"])
    parser.add_argument("--min-rounds", type=int, default=20)
    parser.add_argument("--max-rounds", type=int, default=2048)
    parser.add_argument("--convergence-threshold", type=float, default=0.005)
    parser.add_argument("--verbose", action="store_true")
    
    args = parser.parse_args()
    
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    dictionary = BIP39_WORDS[:args.dict_size]
    
    dtype = np.float32 if args.dtype == "float32" else np.float64
    config = VortexConfig(
        grid_size=args.grid_size,
        temperature=args.temperature,
        viscosity=args.viscosity,
        turbulence_threshold=args.turbulence_threshold,
        turbulence_intensity=args.turbulence_intensity,
        recursion_depth=args.recursion_depth,
        min_rounds=args.min_rounds,
        max_rounds=args.max_rounds,
        convergence_threshold=args.convergence_threshold,
        n_jobs=-1,
        dtype=dtype
    )
    
    print("=" * 80)
    print(f"  v14.41: VMMP TURBULENCE + PERMUTED SHA-256")
    print(f"  ✅ Вихри ВММП: ∇⁴ψ = 0, τ = ∮(dθ/2π)")
    print(f"  ✅ Турбулентность: управляемый топологический переход")
    print(f"  ✅ SHA-256: переставленные nothing-up-my-sleeve константы")
    print(f"  ✅ Глубина рекурсии: {config.recursion_depth}")
    print(f"  Сетка {config.grid_size}×{config.grid_size} | dtype={dtype.__name__}")
    print("=" * 80)
    
    # Тест детерминизма
    is_deterministic = test_determinism(config, dictionary)
    if not is_deterministic:
        logger.error("Детерминизм нарушен!")
        return
    
    print("\n✅ ГОТОВО К ИСПОЛЬЗОВАНИЮ")
    print("  🔧 Можно заменить H_CONSTANTS и K_CONSTANTS на другие nothing-up-my-sleeve числа.")
    print("     Например: √11, √13... или кубические корни других простых.")
    print("     Это сделает TEES-профиль ещё более непредсказуемым для атакующего.")
    print("=" * 80)


if __name__ == "__main__":
    main()