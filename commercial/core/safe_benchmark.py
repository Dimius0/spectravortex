#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resonance_gravitsapa.py — НОВАЯ ГРАВИЦАПА
- Карта проходов между островами
- Резонансный поиск частот
- Временные окна коллапсов
- Память на всех уровнях
- Для товарищей из Китая — с любовью
"""

import os
import sys
import time
import csv
import json
import random
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from collections import Counter

# ========== ПУТИ ==========
BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"
COMMERCIAL_DIR = BASE_DIR / "commercial"
RESULTS_DIR.mkdir(exist_ok=True)

# ========== ИМПОРТ ЯДРА ==========
sys.path.insert(0, str(BASE_DIR))
from architect import TopologicalArchitect
from architect.components import create_component_from_library

# ========== КОНСТАНТЫ ==========
SEED = 7777
random.seed(SEED)
np.random.seed(SEED)
RAM_MIN_FREE_GB = 0.8
SSD_MIN_FREE_GB = 5.0

# ========== КЛАСС: КАРТА ПРОХОДОВ ==========
class PassageMap:
    """Знает, откуда и куда можно пройти"""
    
    def __init__(self):
        self.passages = {}  # (from_N, to_N) -> статистика
        self.load()
    
    def record(self, from_N: int, jump: int, success: bool, energy: float):
        to_N = from_N + jump
        key = (from_N, to_N)
        
        if key not in self.passages:
            self.passages[key] = {
                'attempts': 0,
                'successes': 0,
                'collapses': 0,
                'energies': [],
                'last_attempt': None
            }
        
        self.passages[key]['attempts'] += 1
        if success:
            self.passages[key]['successes'] += 1
        else:
            self.passages[key]['collapses'] += 1
        
        self.passages[key]['energies'].append(energy)
        self.passages[key]['last_attempt'] = datetime.now().isoformat()
        self.save()
    
    def is_open(self, from_N: int, to_N: int) -> bool:
        key = (from_N, to_N)
        if key not in self.passages:
            return None  # неизвестно
        stats = self.passages[key]
        return stats['successes'] > 0
    
    def success_rate(self, from_N: int, to_N: int) -> float:
        key = (from_N, to_N)
        if key not in self.passages:
            return 0.0
        stats = self.passages[key]
        if stats['attempts'] == 0:
            return 0.0
        return stats['successes'] / stats['attempts']
    
    def get_working_jumps(self, from_N: int) -> List[int]:
        """Все прыжки, которые хоть раз работали с этого острова"""
        working = []
        for (f, t), stats in self.passages.items():
            if f == from_N and stats['successes'] > 0:
                working.append(t - f)
        return sorted(working)
    
    def save(self):
        path = RESULTS_DIR / "passage_map.json"
        to_save = {str(k): v for k, v in self.passages.items()}
        with open(path, 'w') as f:
            json.dump(to_save, f, indent=2, default=str)
    
    def load(self):
        path = RESULTS_DIR / "passage_map.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    self.passages = json.load(f)
                # конвертируем ключи обратно в tuple
                self.passages = {eval(k): v for k, v in self.passages.items()}
            except:
                pass

# ========== КЛАСС: РЕЗОНАНСНЫЙ ДЕТЕКТОР ==========
class ResonanceDetector:
    """Ищет любимые частоты островов"""
    
    def __init__(self, passage_map: PassageMap):
        self.passage_map = passage_map
        self.resonances = {}  # N -> любимый прыжок
        self.load()
    
    def analyze(self, N: int) -> Optional[int]:
        """Возвращает резонансный прыжок для N, если есть"""
        working = self.passage_map.get_working_jumps(N)
        if not working:
            return None
        
        # Строим спектр — какие прыжки чаще работали
        spectrum = Counter()
        for jump in working:
            to_N = N + jump
            rate = self.passage_map.success_rate(N, to_N)
            spectrum[jump] = rate
        
        if not spectrum:
            return None
        
        # Берём прыжок с самой высокой частотой успеха
        resonance = spectrum.most_common(1)[0][0]
        self.resonances[N] = resonance
        self.save()
        return resonance
    
    def save(self):
        path = RESULTS_DIR / "resonances.json"
        with open(path, 'w') as f:
            json.dump(self.resonances, f, indent=2)
    
    def load(self):
        path = RESULTS_DIR / "resonances.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    self.resonances = json.load(f)
                self.resonances = {int(k): v for k, v in self.resonances.items()}
            except:
                pass

# ========== КЛАСС: ВРЕМЕННЫЕ ОКНА ==========
class TemporalGate:
    """Знает, какие проходы сейчас закрыты"""
    
    def __init__(self):
        self.closed_until = {}  # (from_N, to_N) -> время открытия
        self.load()
    
    def close(self, from_N: int, to_N: int, duration: int = 3600):
        """Закрыть проход на duration секунд"""
        key = (from_N, to_N)
        self.closed_until[key] = datetime.now() + timedelta(seconds=duration)
        self.save()
    
    def is_open(self, from_N: int, to_N: int) -> bool:
        key = (from_N, to_N)
        if key not in self.closed_until:
            return True
        return datetime.now() > self.closed_until[key]
    
    def save(self):
        path = RESULTS_DIR / "temporal_gates.json"
        with open(path, 'w') as f:
            data = {str(k): v.isoformat() for k, v in self.closed_until.items()}
            json.dump(data, f, indent=2)
    
    def load(self):
        path = RESULTS_DIR / "temporal_gates.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                self.closed_until = {eval(k): datetime.fromisoformat(v) 
                                     for k, v in data.items()}
            except:
                pass

# ========== КЛАСС: РАСШИРЕННЫЙ АВТОНОМНЫЙ ЦИКЛ ==========
@dataclass
class TestSession:
    timestamp: str
    seed: int
    N: int
    grid: int
    energy: float
    min_distance: float
    time: float
    iterations: int
    jump_from: int
    jump_used: int
    resonance_used: Optional[int] = None

class ResonanceCycle:
    """Новая гравицапа — с резонансом, картой и окнами"""
    
    def __init__(self, start_N: int = 75):
        self.current_N = start_N
        self.last_stable_N = start_N
        self.jump_attempt = 1
        self.collapse_streak = 0
        self.stabilization_counter = 0
        
        self.passage_map = PassageMap()
        self.resonance_detector = ResonanceDetector(self.passage_map)
        self.temporal_gate = TemporalGate()
        
        self.border_06 = None
        self.border_confirmed = False
        
        self.load_state()
    
    def get_iterations(self, N: int) -> int:
        return 100 + max(0, N - 60) * 10
    
    def next_N(self) -> int:
        """Выбирает следующую цель с учётом резонанса и временных окон"""
        
        if self.border_confirmed:
            return self.border_06
        
        # Если только что коллапс — возвращаемся на базу
        if hasattr(self, '_just_collapsed') and self._just_collapsed:
            self._just_collapsed = False
            return self.last_stable_N
        
        # Пробуем резонансный прыжок
        resonance = self.resonance_detector.analyze(self.last_stable_N)
        if resonance:
            target = self.last_stable_N + resonance
            # Проверяем, открыт ли проход
            if self.temporal_gate.is_open(self.last_stable_N, target):
                print(f"   🎵 Резонанс! Прыжок +{resonance}")
                return target
        
        # Если резонанса нет или проход закрыт — обычный прыжок
        target = self.last_stable_N + self.jump_attempt
        return min(target, 200)  # расширили до 200
    
    def record(self, session: TestSession):
        """Анализ теста с записью в карту"""
        
        # Записываем в карту проходов
        self.passage_map.record(
            from_N=session.jump_from,
            jump=session.jump_used,
            success=(session.min_distance >= 0.06),
            energy=session.energy
        )
        
        # Если коллапс — закрываем проход на время
        if session.min_distance < 0.01:
            self.temporal_gate.close(session.jump_from, session.N, duration=3600)
            self.collapse_streak += 1
            self.stabilization_counter = 0
            self.jump_attempt = self.collapse_streak + 1
            self._just_collapsed = True
            
            print(f"\n   📊 АВТОНОМНАЯ СВЯЗЬ:")
            print(f"   ├─ N={session.N}, dist={session.min_distance:.2f}, энергия={session.energy:.0f}")
            print(f"   ├─ Прыжок: +{session.jump_used} от {session.jump_from}")
            print(f"   ☢️ КОЛЛАПС! Попытка #{self.collapse_streak}")
            print(f"   🎯 Прыжок увеличен до +{self.jump_attempt}")
            print(f"   🚪 Проход закрыт на 1 час")
            print(f"   ↩️ Откат до N={self.last_stable_N}")
        
        # Если успех
        elif session.min_distance >= 0.06:
            self.stabilization_counter += 1
            self.last_stable_N = session.N
            self.collapse_streak = 0
            self._just_collapsed = False
            
            # Проверяем, не рекорд ли это
            if session.N > estimate_capacity(session.grid):
                print(f"   🧬 НОВЫЙ РЕКОРД! Ёмкость {session.grid}³ = {session.N}")
                self.border_06 = session.N
            
            # Разгон
            if self.stabilization_counter >= 3:
                self.jump_attempt += 1
                print(f"   ⚡ РАЗГОН! Прыжок увеличен до +{self.jump_attempt}")
                self.stabilization_counter = 0
            
            print(f"\n   📊 АВТОНОМНАЯ СВЯЗЬ:")
            print(f"   ├─ N={session.N}, dist={session.min_distance:.2f}, энергия={session.energy:.0f}")
            print(f"   ├─ Прыжок: +{session.jump_used} от {session.jump_from}")
            print(f"   └─ Успехов подряд: {self.stabilization_counter}")
        
        self.save_state()
    
    def save_state(self):
        state = {
            'current_N': self.current_N,
            'last_stable_N': self.last_stable_N,
            'jump_attempt': self.jump_attempt,
            'collapse_streak': self.collapse_streak,
            'stabilization_counter': self.stabilization_counter,
            'border_06': self.border_06,
            'border_confirmed': self.border_confirmed,
            'last_updated': datetime.now().isoformat()
        }
        path = RESULTS_DIR / "resonance_state.json"
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        path = RESULTS_DIR / "resonance_state.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    state = json.load(f)
                    self.current_N = state.get('current_N', 75)
                    self.last_stable_N = state.get('last_stable_N', 75)
                    self.jump_attempt = state.get('jump_attempt', 1)
                    self.collapse_streak = state.get('collapse_streak', 0)
                    self.stabilization_counter = state.get('stabilization_counter', 0)
                    self.border_06 = state.get('border_06')
                    self.border_confirmed = state.get('border_confirmed', False)
            except:
                pass

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def estimate_capacity(grid_size):
    return int(grid_size**3 * 0.005)

def create_components(N):
    components = []
    type_names = ['transmon_qubit', 'si_photonic_modulator', 'finfet_processor']
    charges = [1, -1, 0]
    
    for i in range(N):
        comp_type = type_names[i % len(type_names)]
        comp_id = f"{comp_type}_{i}_{SEED}"
        
        comp_dict = create_component_from_library(comp_type, comp_id)
        comp_dict['charge'] = charges[i % len(charges)]
        components.append(comp_dict)
    
    return components

def check_resources():
    import psutil
    ram = psutil.virtual_memory()
    ram_free = ram.available / (1024**3)
    disk = psutil.disk_usage('C:\\')
    ssd_free = disk.free / (1024**3)
    
    issues = []
    if ram_free < RAM_MIN_FREE_GB:
        issues.append(f"RAM {ram_free:.2f} ГБ < {RAM_MIN_FREE_GB}")
    if ssd_free < SSD_MIN_FREE_GB:
        issues.append(f"SSD {ssd_free:.2f} ГБ < {SSD_MIN_FREE_GB}")
    
    return len(issues) == 0, issues, ram_free, ssd_free

def calculate_pause(session: TestSession, cycle: ResonanceCycle) -> int:
    pause = session.N * 0.5 + session.energy / 800 + session.iterations / 20
    
    if session.min_distance < 0.01:
        pause = 120
    elif session.min_distance < 0.06:
        pause += 30
    elif session.min_distance < 0.08:
        pause += 15
    
    if cycle.stabilization_counter >= 2:
        pause *= 0.9
    if cycle.stabilization_counter >= 4:
        pause *= 0.9
    
    return max(20, min(int(pause), 120))

# ========== ОСНОВНОЙ ТЕСТ ==========
def run_test(N, from_N, jump_used, grid_size=16):
    iterations = CYCLE.get_iterations(N)
    
    print(f"\n🚀 ТЕСТ N={N} [с {from_N} +{jump_used}, seed={SEED}, итерации={iterations}]")
    
    components = create_components(N)
    architect = TopologicalArchitect()
    
    start = time.time()
    try:
        problem = {
            "name": f"resonance_test_N{N}_from{from_N}",
            "components": components,
            "grid_shape": [grid_size, grid_size, grid_size],
            "optimization_iters": iterations,
            "convergence_tolerance": 1e-3
        }
        
        solution = architect.synthesize(problem)
        elapsed = time.time() - start
        
        result_data = solution.data if hasattr(solution, 'data') else {}
        energy = result_data.get('field_energy', -1)
        
        positions = result_data.get('component_positions', [])
        min_dist = -1.0
        if positions and len(positions) > 1:
            distances = []
            for i in range(len(positions)):
                for j in range(i+1, len(positions)):
                    d = np.linalg.norm(np.array(positions[i]) - np.array(positions[j]))
                    distances.append(d)
            min_dist = min(distances) if distances else -1.0
        
        print(f"   ✅ Энергия: {energy:.2f}")
        print(f"   📏 Min dist: {min_dist:.2f}")
        print(f"   ⏱️  Время: {elapsed:.3f} с")
        
        # Сохраняем в CSV
        csv_path = RESULTS_DIR / "resonance_results.csv"
        row = {
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'seed': SEED,
            'N': N,
            'from_N': from_N,
            'jump': jump_used,
            'grid': f"{grid_size}³",
            'energy': round(energy, 2),
            'min_distance': round(min_dist, 2),
            'time': round(elapsed, 3),
            'iterations': iterations
        }
        
        file_exists = csv_path.exists()
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        
        session = TestSession(
            timestamp=row['timestamp'],
            seed=SEED,
            N=N,
            grid=grid_size,
            energy=energy,
            min_distance=min_dist,
            time=elapsed,
            iterations=iterations,
            jump_from=from_N,
            jump_used=jump_used
        )
        
        CYCLE.record(session)
        return session, None
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)[:200]}")
        return None, str(e)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔬 НОВАЯ ГРАВИЦАПА — РЕЗОНАНСНАЯ")
    print("="*70)
    print("🏅 Чемпион: seed=7777")
    print("🧠 Режим: карта проходов + резонанс + временные окна")
    print("🙏 С благодарностью китайским товарищам")
    print("="*70)
    
    ok, issues, ram_free, ssd_free = check_resources()
    print(f"\n🖥️  RAM: {ram_free:.2f} ГБ свободно")
    print(f"💾 SSD: {ssd_free:.2f} ГБ свободно")
    
    if not ok:
        print(f"\n❌ Ресурсы: {', '.join(issues)}")
        sys.exit(1)
    
    CYCLE = ResonanceCycle(start_N=90)  # стартуем с 90
    
    try:
        while not CYCLE.border_confirmed and CYCLE.last_stable_N < 200:
            next_n = CYCLE.next_N()
            from_n = CYCLE.last_stable_N
            jump = next_n - from_n
            
            session, error = run_test(next_n, from_n, jump)
            
            if error:
                print(f"❌ Ошибка: {error}")
                break
            
            if session and session.min_distance >= 0.06:
                pause = calculate_pause(session, CYCLE)
                print(f"\n⏸️  Восстановление: {pause} с")
                print(f"   ├─ N={session.N}, dist={session.min_distance:.2f}")
                print(f"   ├─ энергия={session.energy:.0f}")
                print(f"   └─ итерации={session.iterations}")
                time.sleep(pause)
            
            print("-"*70)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Прервано пользователем")
        print("📊 Состояние сохранено")
        sys.exit(0)