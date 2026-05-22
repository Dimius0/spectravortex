#!/usr/bin/env python3
"""Прогон Майкла Джордана — сравнение двух времён рождения."""
import json, math, numpy as np
from datetime import datetime, timedelta
from family_vortex import VortexCluster, MultiClusterEvolution, ResonanceDetector, ExternalPulse, FactorX

def latlon_to_position(lat, lon, box_size=16.0):
    x = (lon + 180) / 360 * box_size
    y = (lat + 90) / 180 * box_size
    return (x, y, box_size/2)

def run_model(json_path, label):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ent = data['entities'][0]
    birth_utc = datetime.fromisoformat(ent['birth_utc'])
    position = latlon_to_position(ent['lat'], ent['lon'])
    cluster = VortexCluster(birth_time=birth_utc, birth_position=position,
                            tau_charges=ent.get('tau_charges', [1.0, -1.0, 1.0]),
                            name=ent['name'], fractal_level=ent.get('fractal_level', 1))
    
    print(f"\n{'='*60}")
    print(f"{label}: {birth_utc} UTC")
    print(f"{'='*60}")
    
    helio = ExternalPulse(period_steps=50, amplitude=0.05, phase=0.0, name="Helio")
    galactic = ExternalPulse(period_steps=3650, amplitude=0.5, phase=math.pi/4, name="Galactic")
    fx = FactorX(amplitude=0.1, threshold=0.15, name="FactorX")
    
    evolution = MultiClusterEvolution(clusters=[cluster], box_size=16.0,
                                      external_pulses=[helio, galactic], factor_x_list=[fx])
    
    total_steps = 22000
    for step in range(total_steps):
        evolution.evolve_step(base_dt=0.1, noise_level=0.01)
    
    detector = ResonanceDetector(cluster.gradient_history, cluster.energy_history,
                                 cluster.min_dist_history, window=30,
                                 threshold_factor=3.5, energy_factor=3.0)
    
    classified = detector.classify_peaks()
    jumps = detector.find_jumps()
    
    def step_to_date(step):
        return birth_utc + timedelta(days=step)
    
    # Ключевые даты для сравнения
    key_events = {
        "Смерть отца": "1993-08-03",
        "Первый уход из спорта": "1993-10-06",
        "Возвращение в Буллз": "1995-03-19",
        "Второй уход из спорта": "1999-01-13",
        "Подача на развод": "2002-01-04",
        "Брак с Иветт": "2013-04-27",
        "Рождение близнецов": "2014-02-11"
    }
    
    print(f"\nМакро-события: {len(classified['macro'])}")
    for p in classified['macro'][:10]:
        d = step_to_date(p['step'])
        print(f"  {d.date()}: |∇H|={p['gradient']:.4f}")
    
    print(f"\nСкачки энергии (топ-10):")
    for j in jumps[:10]:
        d = step_to_date(j['step'])
        print(f"  {d.date()}: ΔE={j['delta_energy']:.4f}")
    
    print(f"\n--- Проверка ключевых событий ---")
    for name, date_str in key_events.items():
        target = datetime.fromisoformat(date_str)
        target_step = (target - birth_utc).days
        
        # Ближайший скачок
        best_jump = None
        best_dist = float('inf')
        for j in jumps:
            dist = abs(j['step'] - target_step)
            if dist < best_dist:
                best_dist = dist
                best_jump = j
        
        # Ближайший пик
        best_peak = None
        best_peak_dist = float('inf')
        for p in classified['macro'] + classified['meso']:
            dist = abs(p['step'] - target_step)
            if dist < best_peak_dist:
                best_peak_dist = dist
                best_peak = p
        
        jump_str = f"скачок ΔE={best_jump['delta_energy']:.1f} на {best_jump['step']} ({step_to_date(best_jump['step']).date()}), откл {best_dist} дн" if best_jump else "—"
        peak_str = f"пик |∇H|={best_peak['gradient']:.3f} на {best_peak['step']} ({step_to_date(best_peak['step']).date()}), откл {best_peak_dist} дн" if best_peak else "—"
        
        print(f"  {name}: {date_str}")
        print(f"    Ближайший скачок: {jump_str}")
        print(f"    Ближайший пик: {peak_str}")
    
    return classified, jumps

# Запуск обоих вариантов
classified_1340, jumps_1340 = run_model('data/jordan_1340.json', '13:40 EST')
classified_0050, jumps_0050 = run_model('data/jordan_0050.json', '00:50 EST')

print(f"\n{'='*60}")
print("СРАВНЕНИЕ")
print(f"{'='*60}")
print(f"13:40 — макро: {len(classified_1340['macro'])}, скачков: {len(jumps_1340)}")
print(f"00:50 — макро: {len(classified_0050['macro'])}, скачков: {len(jumps_0050)}")
print("\nГОТОВО.")