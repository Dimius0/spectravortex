#!/usr/bin/env python3
"""
run_family_7.py v3.1 — запуск фрактально-эмерджентной модели семьи.
Бигармоническое поле, обменные сущности в зазорах, фрактальное время.
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from family_vortex import (
    VortexCluster, FamilyEvolution, EventDetector,
    ExternalPulse, FactorX
)


def latlon_to_position(lat: float, lon: float, box_size: float = 16.0):
    x = (lon + 180) / 360 * box_size
    y = (lat + 90) / 180 * box_size
    z = box_size / 2
    return (x, y, z)


def main():
    with open('family_7.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = data['entities']
    
    exchange_potentials = {
        "Л": 0.3,
        "Д": 0.5,
        "Р": 0.7,
        "В": 0.6,
        "Д1": 0.8,
        "С": 0.4,
        "М": 0.3,
    }
    
    clusters = []
    for ent in entities:
        birth_utc = datetime.fromisoformat(ent['birth_utc'])
        position = latlon_to_position(ent['lat'], ent['lon'])
        tau_charges = ent.get('tau_charges', [1.0, -1.0, 1.0])
        fractal_level = ent.get('fractal_level', 1)
        exchange_pot = exchange_potentials.get(ent['name'], 0.5)
        
        cluster = VortexCluster(
            birth_time=birth_utc,
            birth_position=position,
            tau_charges=tau_charges,
            name=ent['name'],
            fractal_level=fractal_level,
            exchange_potential=exchange_pot
        )
        clusters.append(cluster)
        
        print(f"{ent['name']} ({ent['role']}): {birth_utc.date()} UTC, "
              f"уровень={fractal_level}, вихрей={len(tau_charges)}, "
              f"exchange_potential={exchange_pot}")
    
    # Внешние импульсы
    helio_noise = ExternalPulse(period_steps=50, amplitude=0.05, phase=0.0)
    galactic_signal = ExternalPulse(period_steps=3650, amplitude=0.5, phase=math.pi/4)
    annual_cycle = ExternalPulse(period_steps=365, amplitude=0.3, phase=0.0)
    factor_x = FactorX(amplitude=0.05, threshold=0.15, seed=42)
    
    total_steps = 40000
    print(f"\nЭволюция: {total_steps} глобальных шагов...")
    print(f"Фрактальное время: уровень 1 — каждый шаг, уровень 2 — каждый 2-й шаг")
    print(f"Обменные сущности рождаются в зазорах при резонансе tension\n")
    
    evolution = FamilyEvolution(
        clusters=clusters,
        box_size=16.0,
        external_pulses=[helio_noise, galactic_signal, annual_cycle],
        factor_x_list=[factor_x],
        noise_seed=42
    )
    
    # Заполняем начальные значения для шага 0
    for cluster in clusters:
        pos = cluster.positions
        energies = [evolution.field.get_energy_density_at(p) for p in pos]
        energy = float(np.mean(energies)) if energies else 0.0
        cluster.energy_history.append(energy)
        cluster.tension_history.append(0.0)
        cluster.strain_history.append(0.0)
        cluster.capacity_history.append(1.0)
    
    def print_status(step):
        print(f"  Глобальный шаг {step}:")
        active_count = 0
        for cluster in clusters:
            if cluster.dissolved:
                print(f"    {cluster.name}: ☠ РАСТВОРЁН (шаг {cluster.dissolution_step}) "
                      f"| strain={cluster.strain:.2f}")
            else:
                active_count += 1
                e = cluster.energy_history[-1] if cluster.energy_history else 0.0
                print(f"    {cluster.name}: E={e:.4f} "
                      f"tension={cluster.tension:.4f} "
                      f"strain={cluster.strain:.4f} "
                      f"capacity={cluster.capacity:.4f} "
                      f"заряд={cluster.total_charge():.2f}/{cluster.total_original_charge():.2f}")
        if active_count <= 1:
            print(f"    ⚠ Остался только {active_count} активный кластер")
        print()
    
    print_status(0)
    
    for step in range(1, total_steps + 1):
        evolution.evolve_step(noise_level=0.005)
        
        if step % 5000 == 0:
            print_status(step)
    
    # ============================================================
    # СТАТИСТИКА ОБМЕНОВ
    # ============================================================
    print(f"{'='*60}")
    print("СТАТИСТИКА ОБМЕНОВ (ОБМЕННЫЕ СУЩНОСТИ В ЗАЗОРАХ)")
    print(f"{'='*60}")
    print(f"Всего обменов: {len(evolution.global_exchanges)}")
    
    total_transferred = sum(e['amount'] for e in evolution.global_exchanges)
    print(f"Всего передано τ: {total_transferred:.4f}")
    
    for cluster in clusters:
        print(f"\n{cluster.name}:")
        print(f"  Заряд: {cluster.total_charge():.4f} / {cluster.total_original_charge():.4f}")
        print(f"  Tension: {cluster.tension:.4f}")
        print(f"  Strain: {cluster.strain:.4f}")
        print(f"  Capacity: {cluster.capacity:.4f}")
        print(f"  Отдано: {cluster.total_given:.4f} τ")
        print(f"  Получено: {cluster.total_received:.4f} τ")
        print(f"  Баланс: {cluster.total_received - cluster.total_given:+.4f}")
        
        if cluster.dissolved:
            print(f"  ☠ РАСТВОРЁН на шаге {cluster.dissolution_step}")
    
    # ============================================================
    # ПРЕДСКАЗАННЫЕ СОБЫТИЯ
    # ============================================================
    print(f"\n{'='*60}")
    print("ПРЕДСКАЗАННЫЕ СОБЫТИЯ")
    print(f"{'='*60}")
    
    for cluster in clusters:
        print(f"\n{cluster.name} ({cluster.birth_time.date()}):")
        
        if cluster.dissolved:
            diss_date = cluster.birth_time + timedelta(days=cluster.dissolution_step)
            age_at_diss = (diss_date - cluster.birth_time).days // 365
            print(f"  ☠ РАСТВОРЁН → {diss_date.date()} (возраст: {age_at_diss} лет)")
            print(f"  Strain: {cluster.strain:.4f}")
            continue
        
        if len(cluster.tension_history) < 60:
            print(f"  Недостаточно данных для детектирования событий")
            continue
        
        detector = EventDetector(
            cluster.tension_history,
            cluster.energy_history,
            window=30,
            threshold_factor=3.5,
            energy_factor=3.0
        )
        
        classified = detector.classify_peaks()
        jumps = detector.find_jumps()
        
        def step_to_date(step):
            return cluster.birth_time + timedelta(days=step)
        
        def age_at_step(step):
            return (step_to_date(step) - cluster.birth_time).days // 365
        
        print(f"  Tension: {cluster.tension:.4f}")
        print(f"  Strain: {cluster.strain:.4f}")
        print(f"  Capacity: {cluster.capacity:.4f}")
        print(f"  Заряд: {cluster.total_charge():.4f} / {cluster.total_original_charge():.4f}")
        
        print(f"  Макро-события: {len(classified['macro'])}")
        for p in classified['macro'][:5]:
            d = step_to_date(p['step'])
            age = age_at_step(p['step'])
            print(f"    Шаг {p['step']} → {d.date()} (возраст {age}): tension={p['tension']:.4f}")
        
        print(f"  Мезо-события: {len(classified['meso'])}")
        for p in classified['meso'][:5]:
            d = step_to_date(p['step'])
            age = age_at_step(p['step'])
            print(f"    Шаг {p['step']} → {d.date()} (возраст {age}): tension={p['tension']:.4f}")
        
        print(f"  Скачки энергии: {len(jumps)}")
        for j in jumps[:5]:
            d = step_to_date(j['step'])
            age = age_at_step(j['step'])
            print(f"    Шаг {j['step']} → {d.date()} (возраст {age}): ΔE={j['delta_energy']:.4f}")
    
    # ============================================================
    # ХРОНОЛОГИЯ ОБМЕНОВ
    # ============================================================
    print(f"\n{'='*60}")
    print("ХРОНОЛОГИЯ ОБМЕНОВ (первые 15)")
    print(f"{'='*60}")
    
    if evolution.global_exchanges:
        for ex in evolution.global_exchanges[:15]:
            acceptor = next(c for c in clusters if c.name == ex['acceptor'])
            exchange_date = acceptor.birth_time + timedelta(days=ex['step'])
            print(f"  Шаг {ex['step']} → {exchange_date.date()}: "
                  f"{ex['donor']} → {ex['acceptor']} "
                  f"({ex['amount']:.4f} τ)")
    else:
        print("  Обменов не было.")
    
    print(f"\n{'='*60}")
    print("ГОТОВО.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()