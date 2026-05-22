#!/usr/bin/env python3
"""
run_family_8.py — запуск ризоматической эволюции v4.0.
Без подгоночных параметров: Пульс + Winding + Действие.
"""

import json, math
import numpy as np
from datetime import datetime, timedelta
from family_vortex_v4 import (
    VortexCluster, FamilyEvolutionV4, EventDetector,
    ExternalPulse, FactorX
)

BOX_SIZE = 16.0

def latlon_to_position(lat, lon):
    return ((lon+180)/360*BOX_SIZE, (lat+90)/180*BOX_SIZE, BOX_SIZE/2)


def main():
    with open('family_7.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # electroотрицательность = sqrt(|τ|) / fractal_level — выводится, не задаётся
    clusters = []
    for ent in data['entities']:
        charges = ent.get('tau_charges', [1.0, -1.0, 1.0])
        level = ent.get('fractal_level', 1)
        # χ из топологии
        chi = math.sqrt(sum(abs(t) for t in charges)) / level
        
        c = VortexCluster(
            birth_time=datetime.fromisoformat(ent['birth_utc']),
            birth_position=latlon_to_position(ent['lat'], ent['lon']),
            tau_charges=charges,
            name=ent['name'],
            fractal_level=level,
            exchange_potential=chi
        )
        clusters.append(c)
        print(f"{c.name}: {c.birth_time.date()} UTC, "
              f"уровень={c.fractal_level}, вихрей={c.n_vortices}, "
              f"χ={c.exchange_potential:.3f}")
    
    pulses = [
        ExternalPulse(50, 0.05, 0.0),
        ExternalPulse(3650, 0.5, math.pi/4),
        ExternalPulse(365, 0.3, 0.0),
    ]
    fx = FactorX(0.05, 0.15, 42)
    
    total_steps = 40000
    print(f"\nРизоматическая эволюция: {total_steps} шагов...")
    print(f"Константы: ħ_eff={1.0}, ω₀=2π, k_points=20, Δφ_threshold=π/4\n")
    
    evo = FamilyEvolutionV4(
        clusters=clusters,
        box_size=BOX_SIZE,
        external_pulses=pulses,
        factor_x_list=[fx]
    )
    
    for step in range(total_steps):
        evo.evolve_step()
        
        if step % 5000 == 0:
            sync = evo.clock.synchronization()
            print(f"\n  Шаг {step} [sync={sync:.3f} dt={evo.clock.compute_dt():.4f}]:")
            
            for c in evo.clusters:
                if not c.born:
                    continue
                pulse = evo.clock.get(c.name)
                phi = pulse.phase if pulse else 0
                w = c.winding_number
                
                if c.merged_into:
                    print(f"    {c.name}: 🔗 → {c.merged_into}")
                elif c.dissolved:
                    print(f"    {c.name}: ☠ растворён (шаг {c.dissolution_step})")
                else:
                    e = c.energy_history[-1] if c.energy_history else 0
                    print(f"    {c.name}: E={e:.4f} φ={phi:.2f} "
                          f"tension={c.tension:.4f} strain={c.strain:.4f} "
                          f"cap={c.capacity:.4f} W={w:.2f}" if w else f"    {c.name}: E={e:.4f} φ={phi:.2f} W=n/a")
    
    # Статистика обменов
    print(f"\n{'='*60}")
    print(f"СТАТИСТИКА ОБМЕНОВ")
    print(f"{'='*60}")
    print(f"Всего обменов: {len(evo.global_exchanges)}")
    if evo.global_exchanges:
        print(f"Суммарно передано τ: {sum(e['amount'] for e in evo.global_exchanges):.2f}")
        donors = set(e['donor'] for e in evo.global_exchanges)
        acceptors = set(e['acceptor'] for e in evo.global_exchanges)
        print(f"Доноры: {', '.join(sorted(donors))}")
        print(f"Акцепторы: {', '.join(sorted(acceptors))}")
    
    # Бифуркации
    print(f"\n{'='*60}")
    print(f"БИФУРКАЦИИ")
    print(f"{'='*60}")
    print(f"Всего событий: {len(evo.bifurcation_events)}")
    
    by_type = {}
    for ev in evo.bifurcation_events:
        t = ev['type']
        by_type[t] = by_type.get(t, 0) + 1
        d = evo.start_time + timedelta(days=ev['step'])
        
        if t == 'dissolution':
            print(f"  {d.date()} ☠ {ev['cluster']} ({ev.get('reason','?')})")
        elif t == 'child_created':
            print(f"  {d.date()} 🌱 {ev['parent']} → {ev['child']}")
        elif t == 'merged':
            print(f"  {d.date()} 🔗 {ev['cluster1']} + {ev['cluster2']} → {ev['merged_name']}")
    
    print(f"\n  По типам: {by_type}")
    
    # Чекпойнты
    print(f"\n{'='*60}")
    print(f"ЧЕКПОЙНТЫ (Память)")
    print(f"{'='*60}")
    print(f"Сохранено состояний: {len(evo.checkpoints)}")
    for cp in evo.checkpoints:
        d = evo.start_time + timedelta(days=cp['step'])
        print(f"  {d.date()} шаг {cp['step']}: {cp['reason']} (sync={cp['sync']:.3f})")
    
    # События по кластерам
    print(f"\n{'='*60}")
    print(f"АНАЛИЗ ПО КЛАСТЕРАМ")
    print(f"{'='*60}")
    
    for c in evo.clusters:
        if not c.born or c.merged_into:
            continue
        
        print(f"\n{c.name} ({c.birth_time.date()}):")
        
        if c.dissolved:
            d = c.birth_time + timedelta(days=c.dissolution_step) if c.dissolution_step else "?"
            print(f"  ☠ Растворён → {d}")
            print(f"  Winding: {c.winding_number:.2f}" if c.winding_number else "  Winding: n/a")
            continue
        
        pulse = evo.clock.get(c.name)
        if pulse:
            print(f"  Фаза: {pulse.phase:.2f}, частота: {pulse.frequency:.3f}")
        
        print(f"  Winding: {c.winding_number:.2f}" if c.winding_number else "  Winding: n/a")
        print(f"  Strain: {c.strain:.4f}, Capacity: {c.capacity:.4f}")
        print(f"  Бifurcation count: {c.bifurcation_count}")
        
        if len(c.tension_history) >= 60:
            det = EventDetector(c.tension_history, c.energy_history)
            peaks = det.classify_peaks()
            jumps = det.find_jumps()
            
            print(f"  Макро-событий: {len(peaks['macro'])}, "
                  f"Мезо: {len(peaks['meso'])}, "
                  f"Скачков энергии: {len(jumps)}")
            
            for p in peaks['macro'][:3]:
                d = evo.start_time + timedelta(days=p['step'])
                print(f"    ⋆ {d.date()}: tension={p['tension']:.4f}")
    
    # Итоги
    active_count = len(evo._active())
    dissolved_count = sum(1 for c in evo.clusters if c.dissolved)
    merged_count = sum(1 for c in evo.clusters if c.merged_into)
    
    print(f"\n{'='*60}")
    print(f"ИТОГИ")
    print(f"{'='*60}")
    print(f"Всего кластеров: {len(evo.clusters)}")
    print(f"Активных: {active_count}")
    print(f"Растворено: {dissolved_count}")
    print(f"Слито: {merged_count}")
    print(f"Обменов: {len(evo.global_exchanges)}")
    print(f"Бифуркаций: {len(evo.bifurcation_events)}")
    print(f"Чекпойнтов: {len(evo.checkpoints)}")
    print(f"Финальная синхронизация: {evo.clock.synchronization():.3f}")
    print("ГОТОВО.")


if __name__ == "__main__":
    main()