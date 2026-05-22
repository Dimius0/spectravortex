#!/usr/bin/env python3
"""
run_family_7.py v3.3.2 — запуск фрактально-эмерджентной модели с бифуркациями.
Исправлено: вызовы методов total_charge(), ключи бифуркаций, _get_active_clusters.
"""

import json, math
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from family_vortex import (
    VortexCluster, FamilyEvolution, EventDetector,
    ExternalPulse, FactorX
)

BOX_SIZE = 16.0

def latlon_to_position(lat, lon):
    return ((lon+180)/360*BOX_SIZE, (lat+90)/180*BOX_SIZE, BOX_SIZE/2)


def main():
    with open('family_7.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    exchange_potentials = {"Л":0.3,"Д":0.5,"Р":0.7,"В":0.6,"Д1":0.8,"С":0.4,"М":0.3}
    clusters = []
    
    for ent in data['entities']:
        c = VortexCluster(
            birth_time=datetime.fromisoformat(ent['birth_utc']),
            birth_position=latlon_to_position(ent['lat'], ent['lon']),
            tau_charges=ent.get('tau_charges', [1.0,-1.0,1.0]),
            name=ent['name'],
            fractal_level=ent.get('fractal_level',1),
            exchange_potential=exchange_potentials.get(ent['name'],0.5)
        )
        clusters.append(c)
        print(f"{c.name}: {c.birth_time.date()} UTC, уровень={c.fractal_level}, "
              f"вихрей={c.n_vortices}, ex_pot={c.exchange_potential}")
    
    pulses = [
        ExternalPulse(50, 0.05, 0.0),
        ExternalPulse(3650, 0.5, math.pi/4),
        ExternalPulse(365, 0.3, 0.0),
    ]
    fx = FactorX(0.05, 0.15, 42)
    
    total_steps = 40000
    print(f"\nЭволюция: {total_steps} шагов...")
    
    evo = FamilyEvolution(
        clusters=clusters,
        box_size=BOX_SIZE,
        external_pulses=pulses,
        factor_x_list=[fx],
        noise_seed=42
    )
    
    for step in range(total_steps):
        evo.evolve_step()
        
        if step % 5000 == 0:
            print(f"\n  Шаг {step}:")
            for c in evo.clusters:
                if not c.born:
                    continue
                if c.merged_into:
                    print(f"    {c.name}: 🔗 слит в {c.merged_into}")
                elif c.dissolved:
                    print(f"    {c.name}: ☠ РАСТВОРЁН (шаг {c.dissolution_step})")
                else:
                    e = c.energy_history[-1] if c.energy_history else 0
                    print(f"    {c.name}: E={e:.4f} tension={c.tension:.4f} "
                          f"strain={c.strain:.4f} cap={c.capacity:.4f} "
                          f"заряд={c.total_charge():.2f}/{c.total_original_charge():.2f}")
    
    # Статистика обменов
    print(f"\n{'='*60}\nСТАТИСТИКА ОБМЕНОВ\n{'='*60}")
    print(f"Всего: {len(evo.global_exchanges)}")
    print(f"Передано τ: {sum(e['amount'] for e in evo.global_exchanges):.2f}")
    
    # Бифуркации
    print(f"\n{'='*60}\nБИФУРКАЦИИ\n{'='*60}")
    print(f"Всего: {len(evo.bifurcation_events)}")
    for ev in evo.bifurcation_events:
        d = evo.start_time + timedelta(days=ev['step'])
        if ev['type'] == 'dissolution':
            print(f"  {d.date()}: ☠ {ev['cluster']} растворён")
        elif ev['type'] == 'child_created':
            print(f"  {d.date()}: 🌱 {ev['parent']} → {ev['child']}")
        elif ev['type'] == 'merged':
            print(f"  {d.date()}: 🔗 {ev['cluster1']} + {ev['cluster2']} → {ev['merged_name']}")
    
    # События
    print(f"\n{'='*60}\nПРЕДСКАЗАННЫЕ СОБЫТИЯ\n{'='*60}")
    for c in evo.clusters:
        if not c.born or c.merged_into or not c.energy_history:
            continue
        print(f"\n{c.name} ({c.birth_time.date()}):")
        if c.dissolved:
            if c.dissolution_step is not None:
                print(f"  ☠ Растворён → {(c.birth_time+timedelta(days=c.dissolution_step)).date()}")
            else:
                print(f"  ☠ Растворён")
            continue
        if len(c.tension_history) < 60:
            continue
        det = EventDetector(c.tension_history, c.energy_history)
        cl = det.classify_peaks()
        jm = det.find_jumps()
        print(f"  Макро: {len(cl['macro'])}")
        for p in cl['macro'][:3]:
            d = evo.start_time + timedelta(days=p['step'])
            print(f"    {d.date()}: tension={p['tension']:.4f}")
        print(f"  Мезо: {len(cl['meso'])}")
        for p in cl['meso'][:3]:
            d = evo.start_time + timedelta(days=p['step'])
            print(f"    {d.date()}: tension={p['tension']:.4f}")
    
    active_count = sum(1 for c in evo.clusters if c.born and not c.dissolved and not c.merged_into)
    print(f"\nВсего кластеров: {len(evo.clusters)}")
    print(f"Активных: {active_count}")
    print("ГОТОВО.")


if __name__ == "__main__":
    main()