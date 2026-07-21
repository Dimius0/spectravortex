#!/usr/bin/env python3
"""
seed_resonator_v1441_intermediate_collisions.py — v14.41: ПРОМЕЖУТОЧНЫЕ КОЛЛИЗИИ
================================================================================
v14.41: 
    - Ищет коллизии в промежуточных раундах (до идеала)
    - Анализирует зарядовые конфигурации
    - Проверяет: могут ли разные фразы дать одинаковый отпечаток на раунде 2-3
"""

import sys, argparse, random, hashlib, struct, hmac, time, json
import numpy as np
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

try:
    from bip39_words import BIP39_WORDS, generate_valid_bip39_phrase
except ImportError:
    print("Ошибка импорта BIP39")
    sys.exit(1)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

@dataclass
class VortexConfig:
    grid_size: int = 32
    n_vortices: int = 12
    max_rounds: int = 5
    
    def __post_init__(self):
        gs = int(self.grid_size)
        self.x = np.linspace(-1, 1, gs)
        self.y = np.linspace(-1, 1, gs)
        self.X, self.Y = np.meshgrid(self.x, self.y)

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
# СОСТОЯНИЕ (упрощённое)
# ============================================================================

@dataclass
class SystemState:
    vortices: List[Vortex]
    round_number: int = 0
    
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
    
    def charge_fingerprint(self) -> str:
        """Отпечаток только по зарядам (самое грубое разрешение)"""
        return "|".join(str(c) for c in self.charges)
    
    def energy_fingerprint(self) -> str:
        """Отпечаток по энергиям с точностью 10^-3"""
        return "|".join(f"{e:.3f}" for e in self.energies)
    
    def phase_fingerprint(self) -> str:
        """Отпечаток по фазам с точностью 10^-3"""
        return "|".join(f"{p:.3f}" for p in self.phases)
    
    def full_fingerprint(self) -> str:
        """Полный отпечаток"""
        return f"{self.charge_fingerprint()}||{self.energy_fingerprint()}||{self.phase_fingerprint()}"

# ============================================================================
# ЭВОЛЮЦИЯ
# ============================================================================

def evolve_one_step(vortices: List[Vortex], coupling: float, energy_mix: float) -> List[Vortex]:
    n = len(vortices)
    phases = np.array([v.phase for v in vortices])
    mean_phase = np.angle(np.mean(np.exp(1j * phases)))
    r_sync = np.abs(np.mean(np.exp(1j * phases)))
    mean_energy = np.mean([v.energy for v in vortices])
    
    new_vortices = []
    for i in range(n):
        v = vortices[i]
        new_field = v.field.copy()
        
        phase_diff = mean_phase - v.phase
        k_eff = coupling * r_sync * 0.3
        fft = np.fft.fft2(new_field)
        fft *= np.exp(1j * phase_diff * k_eff)
        new_field = np.real(np.fft.ifft2(fft))
        
        if i > 0:
            new_field += 0.03 * coupling * vortices[i-1].field
        if i < n - 1:
            new_field += 0.03 * coupling * vortices[i+1].field
        
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

def converge_one_round(vortices: List[Vortex], round_num: int, 
                      max_iters: int = 200) -> Tuple[List[Vortex], List[SystemState]]:
    """
    Конвергенция в одном раунде с сохранением промежуточных состояний.
    """
    coupling = 0.2 + 0.8 * (round_num / 5.0)
    energy_mix = 0.3 + 0.7 * (round_num / 5.0)
    
    intermediate_states = []
    
    for iteration in range(1, max_iters + 1):
        vortices = evolve_one_step(vortices, coupling, energy_mix)
        
        # Сохраняем состояние каждые 50 итераций
        if iteration % 50 == 0:
            state = SystemState(vortices=vortices, round_number=round_num)
            intermediate_states.append(state)
            
            if state.is_converged:
                break
    
    return vortices, intermediate_states

# ============================================================================
# BIP32
# ============================================================================

def generate_keys(phrase: str, n: int = 5) -> List[bytes]:
    seed = hashlib.pbkdf2_hmac('sha512', phrase.encode(), b'mnemonic', 2048, 64)
    master = hmac.new(b'Bitcoin seed', seed, hashlib.sha512).digest()[:32]
    keys = [master]
    for i in range(n - 1):
        keys.append(hashlib.sha512(keys[-1] + struct.pack('>I', i)).digest()[:32])
    return keys

# ============================================================================
# ТЕСТ: ПРОМЕЖУТОЧНЫЕ КОЛЛИЗИИ
# ============================================================================

def test_intermediate_collisions(dictionary: List[str], config: VortexConfig,
                                n_phrases: int = 50, rounds: int = 5):
    """
    Ищет коллизии в промежуточных состояниях (до достижения идеала).
    """
    print(f"\n{'='*80}")
    print(f"  🔍 ПОИСК ПРОМЕЖУТОЧНЫХ КОЛЛИЗИЙ: {n_phrases} ФРАЗ")
    print(f"{'='*80}")
    print(f"  Гипотеза: коллизии возникают до конвергенции к идеалу")
    
    # Хранилища для каждого раунда
    round_databases = defaultdict(lambda: {
        "charges": defaultdict(list),      # заряд → список фраз
        "energies": defaultdict(list),     # энергия → список фраз
        "phases": defaultdict(list),       # фаза → список фраз
        "full": defaultdict(list)          # полный отпечаток → список фраз
    })
    
    charge_collisions = defaultdict(int)  # раунд → число коллизий по зарядам
    energy_collisions = defaultdict(int)  # раунд → число коллизий по энергиям
    phase_collisions = defaultdict(int)   # раунд → число коллизий по фазам
    full_collisions = defaultdict(int)    # раунд → число полных коллизий
    
    for i in range(n_phrases):
        if i % 10 == 0:
            print(f"\n  Прогресс: {i}/{n_phrases}...")
        
        # Генерируем фразу
        if i < n_phrases // 2:
            words = generate_valid_bip39_phrase(12)
            label = f"ПРАВ_{i}"
        else:
            correct = generate_valid_bip39_phrase(12)
            words = correct.copy()
            # Разные дефекты
            defect_type = (i - n_phrases // 2) % 4
            if defect_type == 0:
                idx = BIP39_WORDS.index(words[5])
                words[5] = BIP39_WORDS[(idx + 1024) % 2048]
                label = f"ТОПОЛОГ_{i}"
            elif defect_type == 1:
                words[3], words[4] = words[4], words[3]
                label = f"ПЕРЕСТ_{i}"
            elif defect_type == 2:
                words[8] = random.choice(BIP39_WORDS)
                label = f"СЛУЧ_{i}"
            else:
                words[2] = random.choice(BIP39_WORDS)
                words[9] = random.choice(BIP39_WORDS)
                label = f"ДВОЙН_{i}"
        
        phrase = " ".join(words)
        keys = generate_keys(phrase, rounds)
        vortices = [word_to_vortex(w, dictionary, config) for w in words]
        
        for round_num in range(1, rounds + 1):
            key = keys[round_num - 1]
            vortices, intermediate_states = converge_one_round(vortices, round_num)
            
            # Проверяем промежуточные состояния
            for state in intermediate_states:
                db = round_databases[state.round_number]
                
                # Зарядовый отпечаток
                cfp = state.charge_fingerprint()
                if cfp in db["charges"]:
                    charge_collisions[state.round_number] += 1
                db["charges"][cfp].append(label)
                
                # Энергетический отпечаток
                efp = state.energy_fingerprint()
                if efp in db["energies"]:
                    energy_collisions[state.round_number] += 1
                db["energies"][efp].append(label)
                
                # Фазовый отпечаток
                pfp = state.phase_fingerprint()
                if pfp in db["phases"]:
                    phase_collisions[state.round_number] += 1
                db["phases"][pfp].append(label)
                
                # Полный отпечаток
                ffp = state.full_fingerprint()
                if ffp in db["full"]:
                    full_collisions[state.round_number] += 1
                db["full"][ffp].append(label)
    
    # Анализ
    print(f"\n{'='*80}")
    print(f"  📊 РЕЗУЛЬТАТЫ: ПРОМЕЖУТОЧНЫЕ КОЛЛИЗИИ")
    print(f"{'='*80}")
    
    print(f"\n  Коллизии по раундам:")
    print(f"  {'Раунд':<8} {'По зарядам':<12} {'По энергиям':<12} {'По фазам':<12} {'Полные':<12}")
    print(f"  {'─'*8} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")
    
    total_charge = 0
    total_energy = 0
    total_phase = 0
    total_full = 0
    
    for r in range(1, rounds + 1):
        cc = charge_collisions[r]
        ec = energy_collisions[r]
        pc = phase_collisions[r]
        fc = full_collisions[r]
        
        total_charge += cc
        total_energy += ec
        total_phase += pc
        total_full += fc
        
        print(f"  {r:<8} {cc:<12} {ec:<12} {pc:<12} {fc:<12}")
    
    print(f"  {'─'*8} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")
    print(f"  {'ВСЕГО':<8} {total_charge:<12} {total_energy:<12} {total_phase:<12} {total_full:<12}")
    
    # Анализ уникальности
    print(f"\n  {'─'*70}")
    print(f"  🔬 АНАЛИЗ УНИКАЛЬНОСТИ:")
    
    # Считаем общее число состояний
    total_states = n_phrases * (rounds * 4)  # примерно 4 состояния на раунд
    
    print(f"  Всего промежуточных состояний: ~{total_states}")
    print(f"  Коллизий по зарядам: {total_charge} ({total_charge/total_states*100:.2f}%)")
    print(f"  Коллизий по энергиям: {total_energy} ({total_energy/total_states*100:.2f}%)")
    print(f"  Коллизий по фазам: {total_phase} ({total_phase/total_states*100:.2f}%)")
    print(f"  Полных коллизий: {total_full} ({total_full/total_states*100:.2f}%)")
    
    # Выводы
    print(f"\n  {'─'*70}")
    print(f"  💡 ВЫВОДЫ:")
    
    if total_charge > 0:
        print(f"  ⚠️ Зарядовые коллизии: {total_charge}")
        print(f"     Причина: только 7 возможных зарядов (от -3 до +3)")
        print(f"     Вероятность совпадения: 1/7^12 ≈ 10^-10 на конфигурацию")
        print(f"     Но при {total_states} состояний коллизии ВОЗМОЖНЫ!")
    else:
        print(f"  ✅ Зарядовых коллизий нет — все конфигурации уникальны")
    
    if total_full > 0:
        print(f"  🔴 ПОЛНЫЕ КОЛЛИЗИИ НАЙДЕНЫ!")
        print(f"     Это БЕКДОР — разные фразы дают одинаковое состояние!")
    else:
        print(f"  ✅ Полных коллизий нет")
    
    # Сравнение с SHA-256
    print(f"\n  Для сравнения:")
    print(f"  SHA-256: 2^256 возможных состояний")
    print(f"  Наш движок: 7^12 × (диапазон энергий) × (диапазон фаз)")
    print(f"  Теоретически: ~7^12 × 10^3 × 10^3 ≈ 10^16 состояний")
    
    return {
        "charge_collisions": dict(charge_collisions),
        "energy_collisions": dict(energy_collisions),
        "phase_collisions": dict(phase_collisions),
        "full_collisions": dict(full_collisions),
        "total_charge": total_charge,
        "total_full": total_full
    }

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="v14.41: Промежуточные коллизии")
    parser.add_argument("--n-phrases", type=int, default=50)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    dictionary = BIP39_WORDS[:2048]
    config = VortexConfig(max_rounds=args.rounds)
    
    print(f"\n{'='*80}")
    print(f"  🔴 ПОИСК БЕКДОРА: ПРОМЕЖУТОЧНЫЕ КОЛЛИЗИИ")
    print(f"{'='*80}")
    print(f"  Ищем коллизии ДО того, как система сошлась к идеалу")
    print(f"  Именно здесь могут быть скрытые уязвимости!")
    
    t0 = time.time()
    
    results = test_intermediate_collisions(dictionary, config, args.n_phrases, args.rounds)
    
    elapsed = time.time() - t0
    print(f"\n  ⏱️ Время: {elapsed:.1f}s")
    
    # Сохраняем результаты
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"intermediate_collisions_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  💾 Результаты сохранены: {filename}")

if __name__ == "__main__":
    main()