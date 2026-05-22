#!/usr/bin/env python3
"""Прогон Стива Джобса."""
import json, math, numpy as np
from datetime import datetime, timedelta
from family_vortex import VortexCluster, MultiClusterEvolution, ResonanceDetector, ExternalPulse, FactorX

def latlon_to_position(lat, lon, box_size=16.0):
    x = (lon + 180) / 360 * box_size
    y = (lat + 90) / 180 * box_size
    return (x, y, box_size/2)

with open('data/jobs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

ent = data['entities'][0]
birth_utc = datetime.fromisoformat(ent['birth_utc'])
position = latlon_to_position(ent['lat'], ent['lon'])
cluster = VortexCluster(birth_time=birth_utc, birth_position=position,
                        tau_charges=ent.get('tau_charges', [1.0, -1.0, 1.0]),
                        name=ent['name'], fractal_level=ent.get('fractal_level', 1))

print(f"{ent['name']}: {birth_utc} UTC, позиция=({position[0]:.2f}, {position[1]:.2f})")

helio = ExternalPulse(period_steps=50, amplitude=0.05, phase=0.0, name="Гелиосферный шум")
galactic = ExternalPulse(period_steps=3650, amplitude=0.5, phase=math.pi/4, name="Галактический сигнал")
fx = FactorX(amplitude=0.1, threshold=0.15, name="Крыло бабочки")

evolution = MultiClusterEvolution(clusters=[cluster], box_size=16.0,
                                  external_pulses=[helio, galactic], factor_x_list=[fx])

# Стив Джобс прожил 56 лет = ~20680 дней. Прогон с запасом 22000 шагов
total_steps = 22000
print(f"\nЭволюция: {total_steps} шагов (~60 лет)...")

for step in range(total_steps):
    evolution.evolve_step(base_dt=0.1, noise_level=0.01)
    if step % 5000 == 0:
        print(f"  Шаг {step}: E={cluster.energy_history[-1]:.4f} |∇H|={cluster.gradient_history[-1]:.4f} d_min={cluster.min_dist_history[-1]:.4f}")

# Детектор
detector = ResonanceDetector(cluster.gradient_history, cluster.energy_history,
                             cluster.min_dist_history, window=30,
                             threshold_factor=3.5, energy_factor=3.0)

classified = detector.classify_peaks()
jumps = detector.find_jumps()

def step_to_date(step):
    return birth_utc + timedelta(days=step)

print(f"\nМакро-события: {len(classified['macro'])}")
for p in classified['macro'][:10]:
    d = step_to_date(p['step'])
    print(f"  {d.date()}: |∇H|={p['gradient']:.4f}")

print(f"\nМезо-события: {len(classified['meso'])}")
for p in classified['meso'][:10]:
    d = step_to_date(p['step'])
    print(f"  {d.date()}: |∇H|={p['gradient']:.4f}")

print(f"\nСкачки энергии (топ-10):")
for j in jumps[:10]:
    d = step_to_date(j['step'])
    print(f"  {d.date()}: ΔE={j['delta_energy']:.4f}")

print("\nГОТОВО.")