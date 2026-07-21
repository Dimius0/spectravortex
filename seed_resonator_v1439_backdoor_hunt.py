#!/usr/bin/env python3
"""
seed_resonator_v1439_backdoor_hunt.py — v14.39: ОХОТА НА БЕКДОР
================================================================================
v14.39: 
    - Ищет коллизии, вызванные фиксированными коэффициентами
    - Проверяет гипотезу бекдора через константы раундов
    - Варьирует сиды для поиска одинаковых финальных состояний
"""

import sys, argparse, random, hashlib, struct, hmac, time, json, os
import numpy as np
from typing import List, Tuple, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from bip39_words import BIP39_WORDS, generate_valid_bip39_phrase
except ImportError:
    logger.error("Не удалось импортировать bip39_words")
    sys.exit(1)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

@dataclass
class VortexConfig:
    grid_size: int = 32
    n_vortices: int = 12
    max_rounds: int = 12
    
    def __post_init__(self):
        gs = int(self.grid_size)
        self.x = np.linspace(-1, 1, gs)
        self.y = np.linspace(-1, 1, gs)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.R = np.sqrt(self.X**2 + self.Y**2)
        self.Theta = np.arctan2(self.Y, self.X)

# ============================================================================
# ВИХРЬ
# ============================================================================

@dataclass
class Vortex:
    field: np.ndarray
    charge: int
    natural_frequency: float
    energy: float = 1.0
    
    @property
    def phase(self) -> float:
        return np.angle(np.sum(self.field))

# ============================================================================
# СОЗДАНИЕ ВИХРЯ
# ============================================================================

def word_to_vortex(word: str, dictionary: List[str], config: VortexConfig) -> Vortex:
    try:
        word_idx = dictionary.index(word)
    except ValueError:
        word_idx = 0
    
    charge = (word_idx % 7) - 3
    word_hash = hashlib.sha256(word.encode()).digest()
    natural_freq = 0.5 + (word_hash[0] / 255.0) * 2.0
    energy = 0.5 + (word_idx % 1000) / 1000.0 * 1.5
    
    X, Y = config.X, config.Y
    r = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    
    core = 0.15 + energy * 0.15
    field = energy * r**abs(charge) * np.cos(charge * theta + natural_freq) * np.exp(-r**2 / (2 * core**2))
    
    for i, char in enumerate(word[:4]):
        kx = 2 + ord(char) % 7
        ky = 2 + (ord(char) // 7) % 7
        field += 0.03 * np.sin(kx * X + i) * np.cos(ky * Y + i)
    
    current_energy = np.sum(np.gradient(field)[0]**2 + np.gradient(field)[1]**2)
    if current_energy > 1e-10:
        field *= np.sqrt(energy / current_energy)
    
    return Vortex(field=field, charge=charge, natural_frequency=natural_freq, energy=energy)

# ============================================================================
# СОСТОЯНИЕ
# ============================================================================

@dataclass
class SystemState:
    vortices: List[Vortex]
    round_number: int = 0
    iterations_to_converge: int = 0
    
    @property
    def energies(self) -> np.ndarray:
        return np.array([v.energy for v in self.vortices])
    
    @property
    def phases(self) -> np.ndarray:
        return np.array([v.phase for v in self.vortices])
    
    @property
    def charges(self) -> np.ndarray:
        return np.array([v.charge for v in self.vortices])
    
    @property
    def consistency(self) -> float:
        e = self.energies
        return max(0.0, 1.0 - np.std(e) / (np.mean(e) + 1e-10))
    
    @property
    def coherence(self) -> float:
        return float(np.abs(np.mean(np.exp(1j * self.phases))))
    
    @property
    def is_converged(self) -> bool:
        return self.consistency >= 0.95 and self.coherence >= 0.95
    
    def exact_fingerprint(self) -> str:
        """
        Точный отпечаток состояния (как хеш публичного ключа).
        Включает все параметры, которые могут совпасть при коллизии.
        """
        fp = ""
        # Заряды (дискретные,最容易 совпасть!)
        fp += "|".join(str(c) for c in self.charges)
        fp += "||"
        # Энергии с высокой точностью
        fp += "|".join(f"{e:.10f}" for e in self.energies)
        fp += "||"
        # Фазы с высокой точностью
        fp += "|".join(f"{p:.10f}" for p in self.phases)
        return hashlib.sha256(fp.encode()).hexdigest()

# ============================================================================
# ЭВОЛЮЦИЯ (с фиксированными коэффициентами — потенциальный бекдор!)
# ============================================================================

def evolve_one_step(vortices: List[Vortex], coupling: float, energy_mix: float) -> List[Vortex]:
    """
    Эволюция с ФИКСИРОВАННЫМИ коэффициентами.
    Именно здесь может быть бекдор — одинаковые коэффициенты для разных сидов.
    """
    n = len(vortices)
    phases = np.array([v.phase for v in vortices])
    mean_phase = np.angle(np.mean(np.exp(1j * phases)))
    r_sync = np.abs(np.mean(np.exp(1j * phases)))
    mean_energy = np.mean([v.energy for v in vortices])
    
    new_vortices = []
    for i in range(n):
        v = vortices[i]
        new_field = v.field.copy()
        
        # ФИКСИРОВАННЫЙ коэффициент 0.3
        phase_diff = mean_phase - v.phase
        k_eff = coupling * r_sync * 0.3  # ← КОНСТАНТА!
        fft = np.fft.fft2(new_field)
        fft *= np.exp(1j * phase_diff * k_eff)
        new_field = np.real(np.fft.ifft2(fft))
        
        # ФИКСИРОВАННЫЙ коэффициент 0.03
        if i > 0:
            new_field += 0.03 * coupling * vortices[i-1].field  # ← КОНСТАНТА!
        if i < n - 1:
            new_field += 0.03 * coupling * vortices[i+1].field  # ← КОНСТАНТА!
        
        current_energy = np.sum(np.gradient(new_field)[0]**2 + np.gradient(new_field)[1]**2)
        if current_energy > 1e-10:
            target = current_energy + energy_mix * (mean_energy - current_energy)
            new_field *= np.sqrt(target / current_energy)
        
        new_vortices.append(Vortex(
            field=new_field,
            charge=v.charge,
            natural_frequency=v.natural_frequency,
            energy=mean_energy
        ))
    
    return new_vortices

def converge_in_round(vortices: List[Vortex], key: bytes, 
                      round_num: int) -> Tuple[List[Vortex], int]:
    """
    Конвергенция с ФИКСИРОВАННЫМИ коэффициентами раундов.
    """
    # ФИКСИРОВАННЫЕ коэффициенты для раундов
    coupling = 0.2 + 0.8 * (round_num / 12.0)  # ← КОНСТАНТЫ 0.2, 0.8, 12.0
    energy_mix = 0.3 + 0.7 * (round_num / 12.0)  # ← КОНСТАНТЫ 0.3, 0.7, 12.0
    
    iteration = 0
    while True:
        iteration += 1
        vortices = evolve_one_step(vortices, coupling, energy_mix)
        
        if iteration % 100 == 0:
            state = SystemState(vortices=vortices, round_number=round_num)
            if state.is_converged:
                return vortices, iteration
        
        if iteration > 100_000:
            return vortices, iteration

# ============================================================================
# BIP32 (стандартные константы)
# ============================================================================

def generate_keys(phrase: str, n: int = 5) -> List[bytes]:
    """
    Генерация ключей со СТАНДАРТНЫМИ константами.
    Именно здесь может быть бекдор в SHA-256.
    """
    seed = hashlib.pbkdf2_hmac('sha512', phrase.encode(), b'mnemonic', 2048, 64)
    master = hmac.new(b'Bitcoin seed', seed, hashlib.sha512).digest()[:32]
    keys = [master]
    for i in range(n - 1):
        keys.append(hashlib.sha512(keys[-1] + struct.pack('>I', i)).digest()[:32])
    return keys

# ============================================================================
# ОХОТА НА БЕКДОР: ПОИСК КОЛЛИЗИЙ
# ============================================================================

def hunt_for_backdoor(dictionary: List[str], config: VortexConfig,
                     n_phrases: int = 100, rounds: int = 5) -> Dict[str, Any]:
    """
    Целенаправленный поиск коллизий, вызванных фиксированными константами.
    """
    print(f"\n{'='*80}")
    print(f"  🔍 ОХОТА НА БЕКДОР: ПОИСК КОЛЛИЗИЙ")
    print(f"{'='*80}")
    print(f"  Гипотеза: фиксированные константы создают коллизии")
    print(f"  Тест: {n_phrases} фраз × {rounds} раундов")
    
    # Хранилище всех отпечатков
    fingerprint_db = defaultdict(list)  # fingerprint → [список фраз]
    all_results = []
    
    # Для статистики по раундам
    round_collisions = defaultdict(int)
    
    for i in range(n_phrases):
        # Генерируем разные типы фраз
        if i % 3 == 0:
            words = generate_valid_bip39_phrase(12)
            label = f"ПРАВ_{i}"
        elif i % 3 == 1:
            correct = generate_valid_bip39_phrase(12)
            words = correct.copy()
            idx = BIP39_WORDS.index(words[5])
            words[5] = BIP39_WORDS[(idx + 1024) % 2048]
            label = f"ТОПОЛОГ_{i}"
        else:
            correct = generate_valid_bip39_phrase(12)
            words = correct.copy()
            words[3], words[4] = words[4], words[3]
            label = f"ПЕРЕСТ_{i}"
        
        if i % 10 == 0:
            print(f"\n  Прогресс: {i}/{n_phrases}...")
        
        # Тестируем фразу
        phrase = " ".join(words)
        keys = generate_keys(phrase, rounds)
        vortices = [word_to_vortex(w, dictionary, config) for w in words]
        
        for round_num in range(1, rounds + 1):
            key = keys[round_num - 1]
            vortices, iterations = converge_in_round(vortices, key, round_num)
            
            state = SystemState(vortices=vortices, round_number=round_num)
            fp = state.exact_fingerprint()
            
            # Проверяем коллизию
            if fp in fingerprint_db:
                collision_with = fingerprint_db[fp]
                round_collisions[round_num] += 1
                
                # Детальная информация о коллизии
                collision_info = {
                    "round": round_num,
                    "fingerprint": fp,
                    "phrase1": phrase,
                    "phrase2": collision_with[0]["phrase"],
                    "label1": label,
                    "label2": collision_with[0]["label"],
                    "charges": state.charges.tolist(),
                    "consistency": state.consistency,
                    "coherence": state.coherence
                }
                fingerprint_db[fp].append(collision_info)
            else:
                fingerprint_db[fp].append({
                    "phrase": phrase,
                    "label": label
                })
        
        all_results.append({
            "phrase": phrase,
            "label": label,
            "final_charges": state.charges.tolist(),
            "final_consistency": state.consistency,
            "final_coherence": state.coherence
        })
    
    # Анализ
    print(f"\n{'='*80}")
    print(f"  📊 РЕЗУЛЬТАТЫ ОХОТЫ НА БЕКДОР")
    print(f"{'='*80}")
    
    # Считаем коллизии
    total_fingerprints = len(fingerprint_db)
    collision_count = sum(1 for fp, phrases in fingerprint_db.items() if len(phrases) > 1)
    collision_rate = collision_count / total_fingerprints * 100 if total_fingerprints > 0 else 0
    
    print(f"\n  Всего фраз: {n_phrases}")
    print(f"  Уникальных отпечатков: {total_fingerprints}")
    print(f"  Отпечатков с коллизиями: {collision_count}")
    print(f"  Частота коллизий: {collision_rate:.2f}%")
    
    # Детали по раундам
    print(f"\n  Коллизии по раундам:")
    for r in range(1, rounds + 1):
        print(f"    Раунд {r}: {round_collisions[r]} коллизий")
    
    # Анализ коллизий
    if collision_count > 0:
        print(f"\n  ⚠️ НАЙДЕНЫ КОЛЛИЗИИ!")
        print(f"  Это подтверждает гипотезу бекдора через фиксированные константы.")
        
        # Показываем примеры
        print(f"\n  Примеры коллизий:")
        shown = 0
        for fp, phrases in fingerprint_db.items():
            if len(phrases) > 1 and shown < 3:
                print(f"\n  Отпечаток: {fp[:32]}...")
                for p in phrases[:3]:
                    if "phrase" in p:
                        print(f"    - {p['label']}: {p['phrase'][:50]}...")
                shown += 1
    else:
        print(f"\n  ✅ КОЛЛИЗИЙ НЕ НАЙДЕНО")
        print(f"  Фиксированные константы НЕ создают коллизий в данном диапазоне.")
        print(f"  Но теоретически они возможны при большем числе тестов.")
    
    # Статистика зарядовых конфигураций
    charge_configs = set()
    for r in all_results:
        charge_configs.add(str(r["final_charges"]))
    
    print(f"\n  Уникальных зарядовых конфигураций: {len(charge_configs)}")
    print(f"  Теоретический максимум: 7^12 = {7**12:,}")
    print(f"  Реализовано: {len(charge_configs) / 7**12 * 100:.6f}%")
    
    return {
        "total_phrases": n_phrases,
        "total_fingerprints": total_fingerprints,
        "collision_count": collision_count,
        "collision_rate": collision_rate,
        "round_collisions": dict(round_collisions),
        "unique_charge_configs": len(charge_configs),
        "conclusion": "BACKDOOR_FOUND" if collision_count > 0 else "NO_COLLISION_FOUND"
    }

# ============================================================================
# СОХРАНЕНИЕ ОТЧЁТА
# ============================================================================

def save_backdoor_report(results: Dict[str, Any], filename: str = None):
    """Сохраняет отчёт об охоте на бекдор"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backdoor_hunt_{timestamp}.json"
    
    report = {
        "version": "v14.39",
        "timestamp": datetime.now().isoformat(),
        "hypothesis": "Фиксированные константы в раундах создают коллизии (бекдор)",
        "results": results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  💾 Отчёт сохранён: {filename}")
    return filename

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="v14.39: Охота на бекдор")
    parser.add_argument("--n-phrases", type=int, default=100, help="Количество фраз")
    parser.add_argument("--rounds", type=int, default=5, help="Раундов на фразу")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    dictionary = BIP39_WORDS[:2048]
    config = VortexConfig(max_rounds=args.rounds)
    
    print(f"\n{'='*80}")
    print(f"  🔴 БЕКДОР-АНАЛИЗ: ФИКСИРОВАННЫЕ КОНСТАНТЫ")
    print(f"{'='*80}")
    print(f"  В SHA-256: 64 константы K и 8 начальных значений")
    print(f"  В вихрях: coupling, energy_mix, phase_coeff — тоже константы")
    print(f"  Если разные сиды дают одинаковый промежуточный результат → коллизия!")
    
    t0 = time.time()
    
    # Запускаем охоту
    results = hunt_for_backdoor(dictionary, config, args.n_phrases, args.rounds)
    
    # Сохраняем отчёт
    save_backdoor_report(results, args.output)
    
    elapsed = time.time() - t0
    print(f"\n  ⏱️ Время охоты: {elapsed:.1f}s")
    
    # Итоговый вердикт
    print(f"\n{'='*80}")
    if results["conclusion"] == "BACKDOOR_FOUND":
        print(f"  🔴 БЕКДОР ОБНАРУЖЕН!")
        print(f"  Фиксированные константы создают {results['collision_count']} коллизий")
        print(f"  Частота: {results['collision_rate']:.2f}%")
    else:
        print(f"  🟢 БЕКДОР НЕ ОБНАРУЖЕН")
        print(f"  Но теоретически возможен — нужно больше тестов")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()