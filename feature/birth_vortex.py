#!/usr/bin/env python3
"""
birth_vortex.py — эволюция вихревого кластера в поле H и детектирование событий.
Вход: начальные параметры кластера (время, место, τ-заряды).
Выход: последовательность узлов резонанса (предсказанных событий).
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import Counter


class VortexCluster:
    """Вихревой кластер — модель человека в поле H."""
    
    def __init__(self, birth_time: datetime, birth_position: Tuple[float, float, float],
                 tau_charges: List[float], initial_positions: List[Tuple[float, float, float]] = None):
        self.birth_time = birth_time
        self.birth_position = np.array(birth_position, dtype=np.float64)
        self.tau_charges = tau_charges
        self.n_vortices = len(tau_charges)
        self.initial_phase = self._time_to_phase(birth_time)
        
        if initial_positions is None:
            np.random.seed(int(birth_time.timestamp()))
            self.initial_positions = [
                tuple(np.random.randn(3) * 0.5) for _ in range(self.n_vortices)
            ]
        else:
            self.initial_positions = initial_positions
        
        self.energy_history: List[float] = []
        self.gradient_history: List[float] = []
        self.position_history: List[np.ndarray] = []
        
    def _time_to_phase(self, dt: datetime) -> float:
        epoch = datetime(2000, 1, 1, 12, 0, 0)
        seconds = (dt - epoch).total_seconds()
        period = 86164.0
        phase = (seconds % period) / period * 2 * math.pi
        return phase


class FieldHEvolution:
    """Эволюция кластера в поле H под действием градиента."""
    
    def __init__(self, cluster: VortexCluster, grid_size: int = 16, box_size: float = 16.0):
        self.cluster = cluster
        self.grid_size = grid_size
        self.box_size = box_size
        
        self.positions = np.array([
            cluster.birth_position + np.array(pos)
            for pos in cluster.initial_positions
        ], dtype=np.float64)
        
        self.phase = cluster.initial_phase
        self.step_counter = 0
        
        self.energy_history: List[float] = []
        self.gradient_history: List[float] = []
        self.min_dist_history: List[float] = []
        
    def compute_total_energy(self) -> float:
        energy = 0.0
        for i in range(self.cluster.n_vortices):
            for j in range(i + 1, self.cluster.n_vortices):
                dist = np.linalg.norm(self.positions[i] - self.positions[j])
                if dist > 1e-6:
                    tau_product = self.cluster.tau_charges[i] * self.cluster.tau_charges[j]
                    energy += tau_product / dist
        return energy
    
    def compute_gradient_magnitude(self) -> float:
        center = np.mean(self.positions, axis=0)
        gradient = np.zeros(3, dtype=np.float64)
        for i in range(self.cluster.n_vortices):
            diff = self.positions[i] - center
            dist = np.linalg.norm(diff)
            if dist > 1e-6:
                gradient += self.cluster.tau_charges[i] * diff / (dist ** 3)
        return float(np.linalg.norm(gradient))
    
    def compute_min_distance(self) -> float:
        min_dist = float('inf')
        for i in range(self.cluster.n_vortices):
            for j in range(i + 1, self.cluster.n_vortices):
                dist = np.linalg.norm(self.positions[i] - self.positions[j])
                if dist < min_dist:
                    min_dist = dist
        return min_dist
    
    def evolve_step(self, dt: float = 0.1, noise_level: float = 0.01):
        for i in range(self.cluster.n_vortices):
            force = np.zeros(3, dtype=np.float64)
            for j in range(self.cluster.n_vortices):
                if i != j:
                    diff = self.positions[i] - self.positions[j]
                    dist = np.linalg.norm(diff)
                    if dist > 1e-6:
                        tau_product = self.cluster.tau_charges[i] * self.cluster.tau_charges[j]
                        force += tau_product * diff / (dist ** 3)
            
            noise = np.random.randn(3) * noise_level
            self.positions[i] += force * dt + noise
            self.positions[i] = self.positions[i] % self.box_size
        
        self.phase = (self.phase + dt * 0.1) % (2 * math.pi)
        self.step_counter += 1
        
        energy = self.compute_total_energy()
        gradient = self.compute_gradient_magnitude()
        min_dist = self.compute_min_distance()
        
        self.energy_history.append(energy)
        self.gradient_history.append(gradient)
        self.min_dist_history.append(min_dist)
        
        return energy, gradient, min_dist


class ResonanceDetector:
    """Детектор узлов резонанса (событий) по истории эволюции."""
    
    def __init__(self, gradient_history: List[float], energy_history: List[float],
                 min_dist_history: List[float], window: int = 20, 
                 threshold_factor: float = 3.5, energy_factor: float = 3.0):
        self.gradient_history = gradient_history
        self.energy_history = energy_history
        self.min_dist_history = min_dist_history
        self.window = window
        self.threshold_factor = threshold_factor
        self.energy_factor = energy_factor
    
    def find_peaks(self) -> List[Dict]:
        if len(self.gradient_history) < self.window * 2:
            return []
        
        # Сглаживаем |∇H| скользящим средним
        smoothed = np.convolve(self.gradient_history, np.ones(self.window)/self.window, mode='same')
        
        mean_val = np.mean(smoothed[-self.window:])
        std_val = np.std(smoothed[-self.window:])
        threshold = mean_val + self.threshold_factor * std_val
        
        peaks = []
        for i in range(self.window, len(smoothed) - self.window):
            if (smoothed[i] > threshold and
                smoothed[i] > smoothed[i-1] and
                smoothed[i] > smoothed[i+1]):
                
                peaks.append({
                    'step': i,
                    'gradient': self.gradient_history[i],
                    'smoothed_gradient': smoothed[i],
                    'energy': self.energy_history[i] if i < len(self.energy_history) else None,
                    'min_dist': self.min_dist_history[i] if i < len(self.min_dist_history) else None,
                })
        
        return peaks
    
    def find_jumps(self) -> List[Dict]:
        if len(self.energy_history) < 2:
            return []
        
        jumps = []
        for i in range(1, len(self.energy_history)):
            delta = abs(self.energy_history[i] - self.energy_history[i-1])
            jumps.append({
                'step': i,
                'delta_energy': delta,
                'gradient': self.gradient_history[i] if i < len(self.gradient_history) else None,
            })
        
        if not jumps:
            return []
        
        mean_delta = np.mean([j['delta_energy'] for j in jumps])
        std_delta = np.std([j['delta_energy'] for j in jumps])
        threshold = mean_delta + self.energy_factor * std_delta
        
        significant = [j for j in jumps if j['delta_energy'] > threshold]
        return sorted(significant, key=lambda x: x['delta_energy'], reverse=True)
    
    def classify_peaks(self) -> Dict[str, List[Dict]]:
        """Разделяет пики на макро-, мезо- и микро-события."""
        all_peaks = self.find_peaks()
        
        if not all_peaks:
            return {'macro': [], 'meso': [], 'micro': []}
        
        mean_val = np.mean(self.gradient_history)
        std_val = np.std(self.gradient_history)
        
        macro = [p for p in all_peaks if p['gradient'] > mean_val + 4.0 * std_val]
        meso = [p for p in all_peaks if mean_val + 2.0 * std_val < p['gradient'] <= mean_val + 4.0 * std_val]
        micro = [p for p in all_peaks if p['gradient'] <= mean_val + 2.0 * std_val]
        
        return {'macro': macro, 'meso': meso, 'micro': micro}
    
    def find_weak_periodicities(self, low_threshold: float = 1.0, min_repetitions: int = 5) -> List[Dict]:
        """
        Ищет слабые периодические сигналы, которые не превышают стандартный порог,
        но повторяются регулярно. Это могут быть влияния внешних кластеров (семья, работа).
        """
        mean_val = np.mean(self.gradient_history)
        std_val = np.std(self.gradient_history)
        threshold = mean_val + low_threshold * std_val
        
        weak_peaks = []
        for i in range(self.window, len(self.gradient_history) - self.window):
            if (self.gradient_history[i] > threshold and
                self.gradient_history[i] < mean_val + 2.0 * std_val and
                self.gradient_history[i] > self.gradient_history[i-1] and
                self.gradient_history[i] > self.gradient_history[i+1]):
                weak_peaks.append({'step': i, 'gradient': self.gradient_history[i]})
        
        if len(weak_peaks) < min_repetitions:
            return []
        
        steps = [p['step'] for p in weak_peaks]
        diffs = [steps[i+1] - steps[i] for i in range(len(steps)-1)]
        
        counter = Counter(diffs)
        
        periodicities = []
        for period, count in counter.most_common(10):
            if count >= min_repetitions:
                matching = [weak_peaks[i] for i in range(len(diffs)) if diffs[i] == period]
                avg_gradient = np.mean([p['gradient'] for p in matching]) if matching else 0
                periodicities.append({
                    'period': period,
                    'repetitions': count,
                    'avg_intensity': avg_gradient,
                    'steps': [p['step'] for p in matching]
                })
        
        return periodicities


# ========== ДЕМО-ПРОГОН ==========

def main():
    print("=" * 60)
    print("BIRTH VORTEX — эволюция вихревого кластера")
    print("=" * 60)
    
    birth_time = datetime(2000, 1, 1, 12, 0, 0)
    birth_position = (8.0, 8.0, 8.0)
    tau_charges = [1.0, -1.0, 1.0]
    
    cluster = VortexCluster(birth_time, birth_position, tau_charges)
    
    print(f"Время рождения: {birth_time}")
    print(f"Начальная фаза: {cluster.initial_phase:.3f} рад")
    print(f"Количество вихрей: {cluster.n_vortices}")
    print(f"τ-заряды: {tau_charges}")
    
    evolution = FieldHEvolution(cluster, grid_size=16, box_size=16.0)
    
    print(f"\nЭволюция: 1000 шагов...")
    total_steps = 1000
    
    for step in range(total_steps):
        energy, gradient, min_dist = evolution.evolve_step(dt=0.1, noise_level=0.01)
        
        if step % 200 == 0:
            print(f"  Шаг {step}: E={energy:.4f} |∇H|={gradient:.4f} d_min={min_dist:.4f}")
    
    print(f"  Шаг {total_steps}: E={evolution.energy_history[-1]:.4f} |∇H|={evolution.gradient_history[-1]:.4f} d_min={evolution.min_dist_history[-1]:.4f}")
    
    detector = ResonanceDetector(
        evolution.gradient_history,
        evolution.energy_history,
        evolution.min_dist_history,
        window=20,
        threshold_factor=3.5,
        energy_factor=3.0
    )
    
    # Классификация пиков
    classified = detector.classify_peaks()
    jumps = detector.find_jumps()
    
    print(f"\n=== КЛАССИФИКАЦИЯ СОБЫТИЙ ===")
    print(f"Макро-события (выше 4σ): {len(classified['macro'])}")
    for p in classified['macro'][:5]:
        print(f"  Шаг {p['step']}: |∇H|={p['gradient']:.4f} E={p['energy']:.4f} d_min={p['min_dist']:.4f}")
    
    print(f"\nМезо-события (2σ-4σ): {len(classified['meso'])}")
    for p in classified['meso'][:5]:
        print(f"  Шаг {p['step']}: |∇H|={p['gradient']:.4f} E={p['energy']:.4f}")
    
    print(f"\nМикро-события (ниже 2σ): {len(classified['micro'])} (первые 5 показаны)")
    for p in classified['micro'][:5]:
        print(f"  Шаг {p['step']}: |∇H|={p['gradient']:.4f}")
    
    print(f"\nЗначимых скачков энергии (выше 3.0σ): {len(jumps)}")
    for j in jumps[:5]:
        print(f"  Шаг {j['step']}: ΔE={j['delta_energy']:.4f} |∇H|={j['gradient']:.4f}")
    
    # Слабые периодичности
    weak_periods = detector.find_weak_periodicities(low_threshold=1.0, min_repetitions=5)
    print(f"\nСлабых периодичностей (ниже 2σ, но регулярных): {len(weak_periods)}")
    for wp in weak_periods[:5]:
        print(f"  Период {wp['period']} шагов, повторений: {wp['repetitions']}, средняя интенсивность: {wp['avg_intensity']:.4f}")
    
    print("\nГОТОВО.")


if __name__ == "__main__":
    main()