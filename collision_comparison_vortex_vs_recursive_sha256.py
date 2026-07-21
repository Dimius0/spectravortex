#!/usr/bin/env python3
"""
collision_comparison_vortex_vs_recursive_sha256.py — СРАВНЕНИЕ НА КОЛЛИЗИИ
=========================================================================
Сравнивает два подхода:
1. Вихревой движок (фиксированные константы)
2. Рекурсивный SHA-256 (переставленные константы)

Ожидаемый результат:
- Вихревой: коллизии найдены (бекдор)
- Рекурсивный SHA-256: 0 коллизий (бекдор устранён)
"""

import sys, argparse, random, hashlib, struct, hmac, time, json, os
import numpy as np
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

# ============================================================================
# BIP39
# ============================================================================

try:
    from bip39_words import BIP39_WORDS, generate_valid_bip39_phrase
except ImportError:
    # Минимальный BIP39 для теста
    BIP39_WORDS = [
        "abandon", "ability", "able", "about", "above", "absent",
        "absorb", "abstract", "absurd", "abuse", "access", "accident",
        "account", "accuse", "achieve", "acid", "acoustic", "acquire",
        "across", "act", "action", "actor", "actress", "actual",
        "adapt", "add", "addict", "address", "adjust", "admit",
        "adult", "advance", "advice", "aerobic", "affair", "afford",
        "afraid", "africa", "after", "again", "age", "agent",
        "agree", "ahead", "aim", "air", "airport", "aisle",
        "alarm", "album", "alcohol", "alert", "alien", "all",
        "alley", "allow", "almost", "alone", "alpha", "already",
        "also", "alter", "always", "amateur", "amazing", "among",
        "amount", "amused", "analyst", "anchor", "ancient", "anger",
        "angle", "angry", "animal", "ankle", "announce", "annual",
        "another", "answer", "antenna", "antique", "anxiety", "any",
        "apart", "apology", "appear", "apple", "approve", "april",
        "arch", "arctic", "area", "arena", "argue", "arm",
        "armed", "armor", "army", "around", "arrange", "arrest",
        "arrive", "arrow", "art", "artefact", "artist", "artwork",
        "ask", "aspect", "assault", "asset", "assist", "assume",
        "asthma", "athlete", "atom", "attack", "attend", "attitude",
        "attract", "auction", "audit", "august", "aunt", "author",
        "auto", "autumn", "average", "avocado", "avoid", "awake",
        "aware", "away", "awesome", "awful", "awkward", "axis",
    ]  # Только 132 слова для теста
    
    def generate_valid_bip39_phrase(n_words=12):
        """Генерация фразы из доступных слов"""
        return [random.choice(BIP39_WORDS) for _ in range(n_words)]

# ============================================================================
# SHA-256 КОНСТАНТЫ
# ============================================================================

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
# ЧАСТЬ 1: РЕКУРСИВНЫЙ SHA-256 (БЕЗ БЕКДОРА)
# ============================================================================

def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF

def sha256_permuted(message: bytes, h_order: List[int], k_order: List[int]) -> bytes:
    """SHA-256 с переставленными константами"""
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

def get_permutation(seed: bytes):
    """Генерирует уникальную перестановку констант из seed"""
    rng = random.Random(seed)
    h_order = rng.sample(range(8), 8)
    k_order = rng.sample(range(64), 64)
    return h_order, k_order

def recursive_sha256_hash(phrase: str, depth: int = 3) -> str:
    """
    Рекурсивный SHA-256 с seed-зависимыми константами.
    НЕТ ФИКСИРОВАННЫХ КОНСТАНТ → НЕТ БЕКДОРА!
    """
    message = phrase.encode('utf-8')
    seed = hashlib.sha256(message).digest()
    
    for _ in range(depth):
        h_order, k_order = get_permutation(seed)
        message = sha256_permuted(message, h_order, k_order)
        seed = message
    
    return message.hex()

# ============================================================================
# ЧАСТЬ 2: ВИХРЕВОЙ ДВИЖОК (С БЕКДОРОМ)
# ============================================================================

@dataclass
class VortexConfig:
    grid_size: int = 32
    n_vortices: int = 12

@dataclass
class Vortex:
    field: np.ndarray
    charge: int
    energy: float = 1.0
    
    @property
    def phase(self) -> float:
        return np.angle(np.sum(self.field))

def word_to_vortex(word: str, dictionary: List[str], config: VortexConfig) -> Vortex:
    try:
        word_idx = dictionary.index(word)
    except ValueError:
        word_idx = 0
    
    charge = (word_idx % 7) - 3
    energy = 0.5 + (word_idx % 1000) / 1000.0 * 1.5
    
    gs = int(config.grid_size)
    x = np.linspace(-1, 1, gs)
    y = np.linspace(-1, 1, gs)
    X, Y = np.meshgrid(x, y)
    r = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    
    core = 0.15 + energy * 0.15
    field = energy * r**abs(charge) * np.cos(charge * theta) * np.exp(-r**2 / (2 * core**2))
    
    current_energy = np.sum(np.gradient(field)[0]**2 + np.gradient(field)[1]**2)
    if current_energy > 1e-10:
        field *= np.sqrt(energy / current_energy)
    
    return Vortex(field=field, charge=charge, energy=energy)

def evolve_vortex(vortices: List[Vortex], round_num: int) -> List[Vortex]:
    """Эволюция с ФИКСИРОВАННЫМИ константами (бекдор!)"""
    n = len(vortices)
    # ФИКСИРОВАННЫЕ КОНСТАНТЫ — ИСТОЧНИК БЕКДОРА!
    coupling = 0.2 + 0.8 * (round_num / 5.0)
    energy_mix = 0.3 + 0.7 * (round_num / 5.0)
    phase_coeff = 0.3
    neighbor_coeff = 0.03
    
    phases = np.array([v.phase for v in vortices])
    mean_phase = np.angle(np.mean(np.exp(1j * phases)))
    r_sync = np.abs(np.mean(np.exp(1j * phases)))
    mean_energy = np.mean([v.energy for v in vortices])
    
    new_vortices = []
    for i in range(n):
        v = vortices[i]
        new_field = v.field.copy()
        
        phase_diff = mean_phase - v.phase
        k_eff = coupling * r_sync * phase_coeff
        fft = np.fft.fft2(new_field)
        fft *= np.exp(1j * phase_diff * k_eff)
        new_field = np.real(np.fft.ifft2(fft))
        
        if i > 0:
            new_field += neighbor_coeff * coupling * vortices[i-1].field
        if i < n - 1:
            new_field += neighbor_coeff * coupling * vortices[i+1].field
        
        current_energy = np.sum(np.gradient(new_field)[0]**2 + np.gradient(new_field)[1]**2)
        if current_energy > 1e-10:
            target = current_energy + energy_mix * (mean_energy - current_energy)
            new_field *= np.sqrt(target / current_energy)
        
        new_vortices.append(Vortex(field=new_field, charge=v.charge, energy=mean_energy))
    
    return new_vortices

def vortex_fingerprint(phrase: str, dictionary: List[str], config: VortexConfig, rounds: int = 5) -> str:
    """Вихревой отпечаток (с бекдором)"""
    words = phrase.split()
    vortices = [word_to_vortex(w, dictionary, config) for w in words]
    
    for round_num in range(1, rounds + 1):
        for _ in range(100):
            vortices = evolve_vortex(vortices, round_num)
    
    # Отпечаток из зарядов и энергий
    fp = "|".join(f"{v.charge}:{v.energy:.3f}" for v in vortices)
    return hashlib.sha256(fp.encode()).hexdigest()

# ============================================================================
# ЧАСТЬ 3: СРАВНИТЕЛЬНЫЙ ТЕСТ
# ============================================================================

def compare_collisions(n_phrases: int = 50, rounds: int = 5, depth: int = 3):
    """
    Сравнивает два подхода на одном наборе фраз.
    """
    print(f"\n{'='*80}")
    print(f"  🔬 СРАВНЕНИЕ: ВИХРИ vs РЕКУРСИВНЫЙ SHA-256")
    print(f"{'='*80}")
    print(f"  Тест: {n_phrases} фраз")
    print(f"  Вихри: {rounds} раундов с ФИКСИРОВАННЫМИ константами")
    print(f"  SHA-256: {depth} рекурсий с ПЕРЕСТАВЛЕННЫМИ константами")
    
    dictionary = BIP39_WORDS
    config = VortexConfig()
    
    # Генерируем фразы
    phrases = []
    for i in range(n_phrases):
        words = generate_valid_bip39_phrase(12)
        phrases.append(" ".join(words))
    
    # Тест 1: Вихревой движок
    print(f"\n  {'─'*70}")
    print(f"  🌪️ ТЕСТ 1: ВИХРЕВОЙ ДВИЖОК (фиксированные константы)")
    print(f"  {'─'*70}")
    
    vortex_fingerprints = {}
    vortex_collisions = 0
    vortex_time_start = time.time()
    
    for i, phrase in enumerate(phrases):
        if i % 10 == 0:
            print(f"  Прогресс: {i}/{n_phrases}...")
        
        fp = vortex_fingerprint(phrase, dictionary, config, rounds)
        
        if fp in vortex_fingerprints:
            vortex_collisions += 1
            if vortex_collisions <= 3:
                print(f"  ⚠️ Коллизия! {phrase[:40]}... == {vortex_fingerprints[fp][:40]}...")
        else:
            vortex_fingerprints[fp] = phrase
    
    vortex_time = time.time() - vortex_time_start
    vortex_unique = len(vortex_fingerprints)
    vortex_collision_rate = vortex_collisions / n_phrases * 100
    
    # Тест 2: Рекурсивный SHA-256
    print(f"\n  {'─'*70}")
    print(f"  🔐 ТЕСТ 2: РЕКУРСИВНЫЙ SHA-256 (переставленные константы)")
    print(f"  {'─'*70}")
    
    sha256_fingerprints = {}
    sha256_collisions = 0
    sha256_time_start = time.time()
    
    for i, phrase in enumerate(phrases):
        if i % 10 == 0:
            print(f"  Прогресс: {i}/{n_phrases}...")
        
        fp = recursive_sha256_hash(phrase, depth)
        
        if fp in sha256_fingerprints:
            sha256_collisions += 1
            if sha256_collisions <= 3:
                print(f"  ⚠️ Коллизия! {phrase[:40]}... == {sha256_fingerprints[fp][:40]}...")
        else:
            sha256_fingerprints[fp] = phrase
    
    sha256_time = time.time() - sha256_time_start
    sha256_unique = len(sha256_fingerprints)
    sha256_collision_rate = sha256_collisions / n_phrases * 100
    
    # Сравнительный анализ
    print(f"\n{'='*80}")
    print(f"  📊 РЕЗУЛЬТАТЫ СРАВНЕНИЯ")
    print(f"{'='*80}")
    
    print(f"\n  {'Параметр':<30} {'Вихревой движок':<20} {'Рекурсивный SHA-256':<20}")
    print(f"  {'─'*30} {'─'*20} {'─'*20}")
    print(f"  {'Фраз протестировано':<30} {n_phrases:<20} {n_phrases:<20}")
    print(f"  {'Уникальных отпечатков':<30} {vortex_unique:<20} {sha256_unique:<20}")
    print(f"  {'Коллизий':<30} {vortex_collisions:<20} {sha256_collisions:<20}")
    print(f"  {'Частота коллизий':<30} {vortex_collision_rate:<19.1f}% {sha256_collision_rate:<19.1f}%")
    print(f"  {'Время выполнения':<30} {vortex_time:<19.1f}s {sha256_time:<19.1f}s")
    
    # Константы
    print(f"\n  {'─'*70}")
    print(f"  🔍 АНАЛИЗ КОНСТАНТ:")
    print(f"  Вихри:    coupling=0.2+0.8*(r/5) — ФИКСИРОВАНЫ")
    print(f"            energy_mix=0.3+0.7*(r/5) — ФИКСИРОВАНЫ")
    print(f"            phase_coeff=0.3 — ФИКСИРОВАН")
    print(f"  SHA-256:  K[0..63] переставлены seed-ом — УНИКАЛЬНЫ ДЛЯ КАЖДОЙ ФРАЗЫ")
    print(f"            H[0..7] переставлены seed-ом — УНИКАЛЬНЫ ДЛЯ КАЖДОЙ ФРАЗЫ")
    print(f"            Вариантов: 8! × 64! ≈ 10^89 на рекурсию")
    
    # Вердикт
    print(f"\n  {'─'*70}")
    print(f"  ⚖️ ВЕРДИКТ:")
    
    if vortex_collisions > 0 and sha256_collisions == 0:
        print(f"  🔴 Вихревой движок: БЕКДОР ОБНАРУЖЕН ({vortex_collisions} коллизий)")
        print(f"  🟢 Рекурсивный SHA-256: БЕКДОР ОТСУТСТВУЕТ (0 коллизий)")
        print(f"  ✅ Рекомендация: использовать рекурсивный SHA-256")
    elif vortex_collisions == 0 and sha256_collisions == 0:
        print(f"  🟡 Оба подхода без коллизий на {n_phrases} фразах")
        print(f"  Но вихри ТЕОРЕТИЧЕСКИ уязвимы из-за фиксированных констант")
    else:
        print(f"  🔴 Оба подхода имеют коллизии — требуется улучшение")
    
    # Сохраняем отчёт
    report = {
        "timestamp": datetime.now().isoformat(),
        "n_phrases": n_phrases,
        "vortex": {
            "unique": vortex_unique,
            "collisions": vortex_collisions,
            "collision_rate": vortex_collision_rate,
            "time": vortex_time,
            "constants": "FIXED",
            "backdoor": vortex_collisions > 0
        },
        "sha256": {
            "unique": sha256_unique,
            "collisions": sha256_collisions,
            "collision_rate": sha256_collision_rate,
            "time": sha256_time,
            "constants": "PERMUTED_BY_SEED",
            "backdoor": sha256_collisions > 0
        }
    }
    
    filename = f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n  💾 Отчёт сохранён: {filename}")
    
    return report

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Сравнение вихрей vs рекурсивного SHA-256")
    parser.add_argument("--n-phrases", type=int, default=50, help="Количество фраз")
    parser.add_argument("--rounds", type=int, default=5, help="Раундов вихрей")
    parser.add_argument("--depth", type=int, default=3, help="Глубина рекурсии SHA-256")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    print(f"\n{'='*80}")
    print(f"  🔬 СРАВНИТЕЛЬНЫЙ АНАЛИЗ НА КОЛЛИЗИИ")
    print(f"{'='*80}")
    print(f"  Гипотеза: фиксированные константы → бекдор")
    print(f"  Решение: seed-зависимые перестановки констант")
    
    t0 = time.time()
    
    report = compare_collisions(args.n_phrases, args.rounds, args.depth)
    
    elapsed = time.time() - t0
    print(f"\n  ⏱️ Общее время: {elapsed:.1f}s")

if __name__ == "__main__":
    main()