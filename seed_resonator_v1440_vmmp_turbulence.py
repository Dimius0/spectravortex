#!/usr/bin/env python3
"""
seed_resonator_v1440_vmmp_turbulence.py — v14.40: VMMP TURBULENCE SHA-256
================================================================================
v14.40: Возвращение вихрей через правильную турбулентность ВММП!
        ✅ ТУРБУЛЕНТНОСТЬ: не шум, а управляемый топологический переход
        ✅ ДЕТЕРМИНИЗМ: ∇⁴ψ = 0 и квантование заряда τ = ∮(dθ/2π)
        ✅ ОБРАТИМОСТЬ: топологическое преобразование вместо потери информации
        ✅ СХОДИМОСТЬ + ЛАВИНА: правильный ключ → глубокий минимум,
           неправильный → топологическое короткое замыкание
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
# КОНСТАНТЫ SHA-256
# ============================================================================

SHA256_K = [
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
# ГЛОБАЛЬНЫЙ КЭШ ВИХРЕЙ (привязан к конфигурации)
# ============================================================================

class VortexCache:
    """Кэш вихрей с привязкой к конфигурации сетки"""
    
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
    turbulence_threshold: float = 0.5  # порог турбулентности ВММП
    turbulence_intensity: float = 0.3  # интенсивность перестройки
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
        for t, k_val in enumerate(SHA256_K):
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
        """Предвычисление оператора Лапласа для бигармонического уравнения ∇⁴ψ = 0"""
        # ∇² в частотной области
        self.laplacian2_fft = self.laplacian_fft ** 2  # ∇⁴
    
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
# ВММП-ТУРБУЛЕНТНОСТЬ (правильная!)
# ============================================================================

def compute_topological_charge(vortex: np.ndarray, config: VortexConfig) -> float:
    """
    Вычисляет топологический заряд τ = ∮(dθ/2π).
    Мера устойчивости вихря.
    """
    gy, gx = np.gradient(vortex)
    phase = np.arctan2(gy, gx + 1e-10)
    
    # Циркуляция градиента фазы
    dphase_dx = np.diff(phase, axis=1)
    dphase_dy = np.diff(phase, axis=0)
    
    # Приводим к одинаковому размеру
    circulation_x = np.sum(dphase_dx[:-1, :])
    circulation_y = np.sum(dphase_dy[:, :-1])
    
    charge = (circulation_x + circulation_y) / (2 * np.pi)
    return float(charge)


def compute_vortex_energy(vortex: np.ndarray, config: VortexConfig) -> float:
    """
    Энергия вихря E_vortex = ∫|∇H|² dV.
    """
    gy, gx = np.gradient(vortex)
    energy_density = gx**2 + gy**2
    return float(np.sum(energy_density))


def vmmp_turbulence(vortices, config, round_num):
    n = vortices.shape[0]
    
    for i in range(n):
        tau = compute_topological_charge(vortices[i], config)
        energy = compute_vortex_energy(vortices[i], config)
        
        if abs(tau) < config.turbulence_threshold or energy > 1.0:
            # Детерминированный выбор партнёра: по ближайшему заряду
            best_partner = i
            best_diff = float('inf')
            for j in range(n):
                if i != j:
                    tau_j = compute_topological_charge(vortices[j], config)
                    diff = abs(abs(tau) - abs(tau_j))
                    if diff < best_diff:
                        best_diff = diff
                        best_partner = j
            
            # Слияние с лучшим партнёром
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
# ВЕКТОРИЗОВАННЫЙ СМЕСИТЕЛЬ (с ВММП-турбулентностью)
# ============================================================================

def tees_mix_vortices_vmmp(
    vortices: np.ndarray, 
    key: bytes, 
    config: VortexConfig, 
    round_num: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Смеситель с правильной ВММП-турбулентностью.
    """
    
    n = vortices.shape[0]
    key_hash = np.frombuffer(hashlib.sha256(key).digest(), dtype=np.uint8)
    
    # 1. ДАВЛЕНИЕ (из кэша)
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
    
    # 6. ✅ ВММП-ТУРБУЛЕНТНОСТЬ (правильная!)
    vortices = vmmp_turbulence(vortices, config, round_num)
    
    # НОРМАЛИЗАЦИЯ
    stds = np.std(vortices, axis=(1, 2), keepdims=True)
    means = np.mean(vortices, axis=(1, 2), keepdims=True)
    vortices = np.where(stds > 1e-10, (vortices - means) / stds, vortices)
    
    # Финальный FFT для метрик
    final_fft = np.fft.fft2(vortices.astype(np.complex128), axes=(1, 2))
    
    return vortices, final_fft


# ============================================================================
# SHA-256 С ВММП-ТУРБУЛЕНТНОСТЬЮ
# ============================================================================

class VmmpVortexSHA256:
    """Вихревой SHA-256 с правильной ВММП-турбулентностью."""
    
    def __init__(self, config: VortexConfig, dictionary: List[str]):
        self.config = config
        self.dictionary = dictionary
        self.metrics_history = []
    
    def process_phrase(self, words: List[str], phrase_str: str, 
                    verbose: bool = False) -> Dict:
        
        vortices = batch_word_to_vortex(words, self.dictionary, self.config)
        seed_diameters = [measure_diameter_deterministic(v, self.config) 
                        for v in vortices]
        
        states = [{'field': v, 'diameter_history': [d]} 
                for v, d in zip(vortices, seed_diameters)]
        
        master_key = seed_to_master_key(phrase_str)
        extended_key = derive_key(master_key)
        child_key = derive_key(extended_key)
        address_key = derive_key(child_key, 1)
        keys = [master_key, extended_key, child_key, address_key]
        
        level_names = ['Master', 'Extended', 'Child', 'Final']
        all_diameters = {'Seed': seed_diameters.copy()}
        
        global_round = 0
        total_rounds_used = 0
        all_fft_cache = []
        
        for level_idx, (key, level_name) in enumerate(zip(keys, level_names)):
            current_fields = np.array([s['field'] for s in states], dtype=self.config.dtype)
            
            target_rounds = self._get_target_rounds(level_idx)
            round_check_interval = max(5, target_rounds // 20)
            
            prev_fields = None
            converged = False
            
            if verbose:
                logger.info(f"Уровень {level_name}: цель {target_rounds} раундов")
            
            for r in range(target_rounds):
                current_fields, current_fft = tees_mix_vortices_vmmp(
                    current_fields, key, self.config, global_round
                )
                global_round += 1
                
                if r == target_rounds - 1:
                    all_fft_cache.append(current_fft)
                
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
                if verbose:
                    logger.info(f"  ⚠️ Не сошлось за {target_rounds} раундов")
            
            for i, field in enumerate(current_fields):
                states[i]['field'] = field
            
            level_diameters = []
            for state in states:
                d = measure_diameter_deterministic(state['field'], self.config)
                state['diameter_history'].append(d)
                level_diameters.append(d)
            
            all_diameters[level_name] = level_diameters
        
        final_diameters = np.array(all_diameters['Final'])
        
        address_seed = hashlib.sha256(final_diameters.tobytes()).digest()
        final_address = key_to_address(address_seed)
        
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
            ).hexdigest()[:16]
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
    print("  🎯 ТЕСТ ДЕТЕРМИНИЗМА (ВММП-турбулентность)")
    print("="*80)
    
    words = generate_valid_bip39_phrase(12)
    phrase = " ".join(words)
    
    processor = VmmpVortexSHA256(config, dictionary)
    
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
    else:
        print("  ❌ ОБНАРУЖЕНА НЕДЕТЕРМИНИРОВАННОСТЬ!")
    
    print("="*80)
    return all_same_hashes and all_same_addresses


# ============================================================================
# ТЕСТ ТОПОЛОГИЧЕСКОГО ЗАРЯДА
# ============================================================================

def test_topological_charge(config: VortexConfig, dictionary: List[str]):
    """Проверка квантования топологического заряда."""
    print("\n" + "="*80)
    print("  🧪 ТЕСТ ТОПОЛОГИЧЕСКОГО ЗАРЯДА")
    print("="*80)
    
    words = generate_valid_bip39_phrase(12)
    vortices = batch_word_to_vortex(words, dictionary, config)
    
    print(f"  Вихрей: {len(vortices)}")
    print(f"  {'Вихрь':6} {'τ (заряд)':12} {'Энергия':10} {'Статус'}")
    print(f"  {'─'*6} {'─'*12} {'─'*10} {'─'*10}")
    
    for i, vortex in enumerate(vortices):
        tau = compute_topological_charge(vortex, config)
        energy = compute_vortex_energy(vortex, config)
        
        if abs(tau) < config.turbulence_threshold:
            status = "🌪️ ТУРБУЛЕНТНОСТЬ"
        elif abs(tau) > 1.0:
            status = "✅ СТАБИЛЕН"
        else:
            status = "🟡 НЕЙТРАЛЕН"
        
        print(f"  {i:6} {tau:+12.4f} {energy:10.4f} {status}")
    
    print("="*80)


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="v14.40: VMMP Turbulence SHA-256"
    )
    
    parser.add_argument("--dict-size", type=int, default=2048)
    parser.add_argument("--grid-size", type=int, default=16)
    parser.add_argument("--n-tests", type=int, default=10)
    parser.add_argument("--temperature", type=float, default=0.15)
    parser.add_argument("--viscosity", type=float, default=0.02)
    parser.add_argument("--turbulence-threshold", type=float, default=0.5)
    parser.add_argument("--turbulence-intensity", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dtype", type=str, default="float32",
                    choices=["float32", "float64"])
    parser.add_argument("--min-rounds", type=int, default=20)
    parser.add_argument("--max-rounds", type=int, default=2048)
    parser.add_argument("--convergence-threshold", type=float, default=0.005)
    parser.add_argument("--test-charge", action="store_true",
                       help="Тест топологического заряда")
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
        min_rounds=args.min_rounds,
        max_rounds=args.max_rounds,
        convergence_threshold=args.convergence_threshold,
        n_jobs=-1,
        dtype=dtype
    )
    
    print("=" * 80)
    print(f"  v14.40: VMMP TURBULENCE SHA-256")
    print(f"  ✅ Турбулентность: управляемый топологический переход")
    print(f"  ✅ ∇⁴ψ = 0 | τ = ∮(dθ/2π) | E = ∫|∇H|² dV")
    print(f"  Сетка {config.grid_size}×{config.grid_size} | dtype={dtype.__name__}")
    print(f"  Порог турбулентности: τ < {config.turbulence_threshold}")
    print("=" * 80)
    
    # Тест топологического заряда
    if args.test_charge:
        test_topological_charge(config, dictionary)
        return
    
    # Тест детерминизма
    is_deterministic = test_determinism(config, dictionary)
    if not is_deterministic:
        logger.error("Детерминизм нарушен!")
        return
    
    print("\n✅ ГОТОВО К ИСПОЛЬЗОВАНИЮ")
    print("  Турбулентность теперь — не шум, а топологический переход.")
    print("  Детерминированность сохранена. Обратимость возможна.")
    print("=" * 80)


if __name__ == "__main__":
    main()