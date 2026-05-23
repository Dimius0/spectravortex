#!/usr/bin/env python3
"""
run_family_v5_entropic.py — запуск ризоматической эволюции v5.0 с энтропийным стоком.
Сравнивает поведение с v4 (без стока) и v5 (со стоком).
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from family_vortex_v5_entropic import (
    VortexCluster, FamilyEvolutionV5, EventDetector,
    ExternalPulse, FactorX, KAPPA_0, kappa_effective
)

BOX_SIZE = 16.0

def latlon_to_position(lat, lon):
    return ((lon + 180) / 360 * BOX_SIZE, (lat + 90) / 180 * BOX_SIZE, BOX_SIZE / 2)


def run_simulation(enable_sink: bool, label: str, total_steps: int = 10000):
    """Запуск симуляции с/без энтропийного стока."""
    with open('family_7.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    clusters = []
    for ent in data['entities']:
        charges = ent.get('tau_charges', [1.0, -1.0, 1.0])
        level = ent.get('fractal_level', 1)
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
    
    pulses = [
        ExternalPulse(50, 0.05, 0.0),
        ExternalPulse(3650, 0.5, math.pi / 4),
        ExternalPulse(365, 0.3, 0.0),
    ]
    fx = FactorX(0.05, 0.15, 42)
    
    evo = FamilyEvolutionV5(
        clusters=clusters,
        box_size=BOX_SIZE,
        external_pulses=pulses,
        factor_x_list=[fx],
        enable_entropic_sink=enable_sink
    )
    
    # Статистика по шагам
    snapshots = []
    
    for step in range(total_steps):
        evo.evolve_step()
        
        if step % 2000 == 0:
            active = evo._active()
            sync = evo.clock.synchronization()
            
            total_entropic_flow = 0.0
            total_winding = 0.0
            for c in active:
                if c.entropic_flow_history:
                    total_entropic_flow += abs(c.entropic_flow_history[-1])
                total_winding += c.winding_number or 0.0
            
            snapshots.append({
                'step': step,
                'active_count': len(active),
                'sync': sync,
                'total_winding': total_winding,
                'total_entropic_flow': total_entropic_flow,
            })
            
            print(f"  [{label}] Шаг {step}: активно={len(active)}, "
                  f"sync={sync:.3f}, Σwinding={total_winding:.2f}, "
                  f"Σ|flow|={total_entropic_flow:.4f}")
    
    # Финальная статистика
    active = evo._active()
    dissolved = sum(1 for c in evo.clusters if c.dissolved)
    merged = sum(1 for c in evo.clusters if c.merged_into)
    
    return {
        'label': label,
        'enable_sink': enable_sink,
        'active_count': len(active),
        'dissolved_count': dissolved,
        'merged_count': merged,
        'total_clusters': len(evo.clusters),
        'exchanges': len(evo.global_exchanges),
        'bifurcations': len(evo.bifurcation_events),
        'checkpoints': len(evo.checkpoints),
        'final_sync': evo.clock.synchronization(),
        'snapshots': snapshots,
        'evolution': evo,
    }


def main():
    print("=" * 70)
    print("РИЗОМАТИЧЕСКАЯ ЭВОЛЮЦИЯ v5 — СРАВНЕНИЕ ЭНТРОПИЙНОГО СТОКА")
    print("=" * 70)
    print(f"Константы: ħ_eff=1.0, ω₀=2π, κ₀={KAPPA_0}")
    print(f"Энтропийный сток: {'ВКЛЮЧЁН' if True else 'ВЫКЛЮЧЕН'}")
    print()
    
    total_steps = 10000
    
    # Прогон БЕЗ энтропийного стока (v4)
    print("Прогон 1: БЕЗ энтропийного стока (v4)...")
    result_v4 = run_simulation(enable_sink=False, label="v4", total_steps=total_steps)
    
    # Прогон С энтропийным стоком (v5)
    print("\nПрогон 2: С энтропийным стоком (v5)...")
    result_v5 = run_simulation(enable_sink=True, label="v5", total_steps=total_steps)
    
    # Сравнение
    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ v4 vs v5")
    print("=" * 70)
    
    metrics = [
        ('Активных кластеров', 'active_count'),
        ('Растворено', 'dissolved_count'),
        ('Слито', 'merged_count'),
        ('Всего кластеров', 'total_clusters'),
        ('Обменов', 'exchanges'),
        ('Бифуркаций', 'bifurcations'),
        ('Чекпойнтов', 'checkpoints'),
        ('Финальная синхронизация', 'final_sync'),
    ]
    
    print(f"{'Метрика':<30} {'v4 (без стока)':<20} {'v5 (со стоком)':<20} {'Разница':<15}")
    print("-" * 85)
    
    for name, key in metrics:
        val_v4 = result_v4[key]
        val_v5 = result_v5[key]
        if isinstance(val_v4, float):
            diff = val_v5 - val_v4
            print(f"{name:<30} {val_v4:<20.4f} {val_v5:<20.4f} {diff:+.4f}")
        else:
            diff = val_v5 - val_v4
            print(f"{name:<30} {val_v4:<20} {val_v5:<20} {diff:+d}")
    
    # Сравнение по snapshots
    print(f"\n{'=' * 70}")
    print("ДИНАМИКА ВО ВРЕМЕНИ")
    print(f"{'=' * 70}")
    print(f"{'Шаг':<10} {'v4 active':<12} {'v5 active':<12} {'v4 sync':<10} {'v5 sync':<10} {'v5 |flow|':<12}")
    print("-" * 70)
    
    for s4, s5 in zip(result_v4['snapshots'], result_v5['snapshots']):
        print(f"{s4['step']:<10} {s4['active_count']:<12} {s5['active_count']:<12} "
              f"{s4['sync']:<10.3f} {s5['sync']:<10.3f} {s5['total_entropic_flow']:<12.6f}")
    
    # Анализ по кластерам (v5)
    print(f"\n{'=' * 70}")
    print("АНАЛИЗ ПО КЛАСТЕРАМ (v5)")
    print(f"{'=' * 70}")
    
    for c in result_v5['evolution'].clusters:
        if not c.born or c.merged_into:
            continue
        
        print(f"\n{c.name}:")
        if c.dissolved:
            print(f"  ☠ Растворён на шаге {c.dissolution_step}")
            continue
        
        print(f"  Winding: {c.winding_number:.2f}" if c.winding_number else "  Winding: n/a")
        print(f"  Strain: {c.strain:.4f}, Capacity: {c.capacity:.4f}")
        
        if c.entropic_flow_history:
            total_flow = sum(abs(f) for f in c.entropic_flow_history)
            avg_flow = float(np.mean(c.entropic_flow_history))
            print(f"  Энтропийный поток: всего={total_flow:.4f}, средний={avg_flow:.6f}")
            
            # Направление потока
            in_count = sum(1 for f in c.entropic_flow_history if f > 0)
            out_count = sum(1 for f in c.entropic_flow_history if f < 0)
            print(f"  Поглощал: {in_count} шагов, Терял: {out_count} шагов")
    
    print(f"\n{'=' * 70}")
    print("ГОТОВО.")
    print(f"v4 (без стока): {result_v4['active_count']} активно, "
          f"{result_v4['bifurcations']} бифуркаций")
    print(f"v5 (со стоком): {result_v5['active_count']} активно, "
          f"{result_v5['bifurcations']} бифуркаций")
    print(f"Энтропийный сток {'увеличил' if result_v5['active_count'] > result_v4['active_count'] else 'уменьшил'} "
          f"число выживших кластеров на {abs(result_v5['active_count'] - result_v4['active_count'])}")
    print(f"Энтропийный сток {'увеличил' if result_v5['bifurcations'] > result_v4['bifurcations'] else 'уменьшил'} "
          f"число бифуркаций на {abs(result_v5['bifurcations'] - result_v4['bifurcations'])}")


if __name__ == "__main__":
    main()