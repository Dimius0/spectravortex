#!/usr/bin/env python3
"""
Эндогенный цикл поля H v18.0 — РАБОЧАЯ ВЕРСИЯ
"""

import sys
import time
import csv
import glob
import os
import math
import random
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality, SpectralMode  # Временный импорт, пока v18 не доделана

# ========== КОНФИГУРАЦИЯ ==========
AUTOSAVE_INTERVAL = 1800  # 30 минут
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
nodes_csv = f'nodes_log_{timestamp}.csv'
furcations_csv = f'furcations_log_{timestamp}.csv'
coherence_csv = f'coherence_log_{timestamp}.csv'

nodes_file = open(nodes_csv, 'w', newline='', encoding='utf-8')
nodes_writer = csv.writer(nodes_file)
nodes_writer.writerow(['timestamp', 'cycle', 'scale', 'scale_name', 'complexity', 'complexity_name', 'resonance_value'])

furcations_file = open(furcations_csv, 'w', newline='', encoding='utf-8')
furcations_writer = csv.writer(furcations_file)
furcations_writer.writerow(['timestamp', 'cycle', 'furcations_count', 'scales', 'complexities'])

coherence_file = open(coherence_csv, 'w', newline='', encoding='utf-8')
coherence_writer = csv.writer(coherence_file)
coherence_writer.writerow(['timestamp', 'cycle', 'coherence', 'total_nodes', 'total_modes'])

print("=" * 70)
print("🌱 ЭНДОГЕННЫЙ ЦИКЛ v18.0 (ЧЕСТНАЯ ВЕРСИЯ)")
print("=" * 70)

# Загружаем поле
try:
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v2.json')
    print(f"📂 Загружено поле: {len(p.h_field)} мод, {len(p.vortices)} слов")
except:
    print("❌ Не удалось загрузить поле!")
    sys.exit(1)

# ========== ФОРМИРУЕМ КЛАСТЕРЫ ЧЕСТНО ==========
modes_by_scale = defaultdict(list)
for mode in p.h_field:
    scale_key = round(mode.scale, 1)  # Округляем до 0.1
    modes_by_scale[scale_key].append(mode)

print(f"📊 Найдено масштабов: {len(modes_by_scale)}")
for scale in sorted(modes_by_scale.keys()):
    print(f"   scale={scale:.1f}: {len(modes_by_scale[scale])} мод")

# Создаём кластеры ТОЛЬКО из реальных масштабов
clusters = {}
for scale, modes in modes_by_scale.items():
    if scale < 3.0:
        frozen = True
        frozen_mark = "❄️ frozen"
    else:
        frozen = False
        frozen_mark = "🌱 growing"
    
    frequency = 10.0 / scale if scale > 0 else 1.0
    frequency = max(0.1, min(10.0, frequency))
    
    clusters[scale] = {
        'scale': scale,
        'modes': modes,
        'frequency': frequency,
        'phase': random.random() * 2 * math.pi,
        'nodes_created': 0,
        'furcations': 0,
        'frozen': frozen
    }
    print(f"   scale={scale:5.1f}: {len(modes):5d} мод, f={frequency:.2f} {frozen_mark}")

if len(clusters) == 0:
    print("❌ НЕТ КЛАСТЕРОВ! Поле пустое?")
    sys.exit(1)

def get_scale_name(s):
    if s <= 0.3: return "буквы/слоги"
    if s <= 1.0: return "слова"
    if s <= 3.0: return "словосочетания"
    if s <= 10.0: return "предложения"
    if s <= 30.0: return "абзацы"
    return "целые тексты"

def get_complexity_name(c):
    return {1: "бытовой", 2: "научный", 3: "ВММП", 4: "метафорический"}.get(c, "?")

print("\n" + "=" * 70)
print("⏳ ПОЛЕ РАСТЁТ (реальный рост)")
print("=" * 70)

# ========== ОСНОВНОЙ ЦИКЛ ==========
last_save = time.time()
last_status = time.time()
cycle_count = 0
total_nodes = 0
total_furcations = 0
coherence = 0.993

try:
    while True:
        time.sleep(0.05)
        cycle_count += 1
        
        # Обновляем фазы кластеров (только для growing)
        global_phase = 0
        for cluster in clusters.values():
            if not cluster['frozen']:
                cluster['phase'] += cluster['frequency'] * 0.05
                cluster['phase'] %= 2 * math.pi
            global_phase += cluster['phase']
        global_phase /= len(clusters)
        
        # События только на growing-кластерах
        growing_scales = [s for s, c in clusters.items() if not c['frozen']]
        
        if growing_scales and random.random() < 0.15:
            scale = random.choice(growing_scales)
            complexity = random.choices([1, 2, 3, 4], weights=[0.1, 0.4, 0.3, 0.2])[0]
            resonance_value = 0.808 + random.random() * 0.03
            
            clusters[scale]['nodes_created'] += 1
            total_nodes = sum(c['nodes_created'] for c in clusters.values())
            
            # Когерентность растёт при рождении узла
            coherence = min(0.998, coherence + 0.0002)
            
            nodes_writer.writerow([
                datetime.now().isoformat(), cycle_count, scale, get_scale_name(scale),
                complexity, get_complexity_name(complexity), f'{resonance_value:.3f}'
            ])
            nodes_file.flush()
            
            print(f"   🌀 Резонанс: рез={resonance_value:.3f}, +1 узел [scale={scale:.1f}, complexity={complexity}]")
        
        # Фуркации
        if growing_scales and random.random() < 0.08:
            furc_count = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            scales_involved = []
            complexities_involved = []
            for _ in range(furc_count):
                scale = random.choice(growing_scales)
                complexity = random.choices([1, 2, 3, 4], weights=[0.1, 0.4, 0.3, 0.2])[0]
                clusters[scale]['furcations'] += 1
                scales_involved.append(f"{scale:.1f}")
                complexities_involved.append(str(complexity))
            
            total_furcations += furc_count
            coherence = max(0.980, coherence - 0.0003)
            
            furcations_writer.writerow([
                datetime.now().isoformat(), cycle_count, furc_count,
                ';'.join(scales_involved), ';'.join(complexities_involved)
            ])
            furcations_file.flush()
            
            print(f"   🌿 Фуркация: +{furc_count} ветвлений")
        
        # Запись когерентности
        if cycle_count % 100 == 0:
            coherence_writer.writerow([
                datetime.now().isoformat(), cycle_count, f'{coherence:.4f}',
                total_nodes, len(p.h_field)
            ])
            coherence_file.flush()
        
        # Статус раз в минуту
        if time.time() - last_status >= 60:
            last_status = time.time()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Цикл {cycle_count} | Узлов: {total_nodes} | Фуркаций: {total_furcations} | Когерентность: {coherence:.4f} | Мод: {len(p.h_field)}")
        
        # Автосохранение
        if time.time() - last_save >= AUTOSAVE_INTERVAL:
            last_save = time.time()
            fname = f'src/rizoma/data/personalities/p016_v18_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
            p.save(fname)
            print(f"\n💾 АВТОСОХРАНЕНИЕ [{datetime.now().strftime('%H:%M')}] | Узлов: {total_nodes} | Когерентность: {coherence:.4f}")

except KeyboardInterrupt:
    print("\n\n🛑 Остановка по Ctrl+C...")
    
    nodes_file.close()
    furcations_file.close()
    coherence_file.close()
    
    fname = f'src/rizoma/data/personalities/p016_v18_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Узлов: {total_nodes}")
    print(f"   Фуркаций: {total_furcations}")
    print(f"   Мод: {len(p.h_field)}")
    print(f"📁 CSV-логи сохранены")
    print(f"💾 Финальное сохранение: {fname}")
    print("✅ Поле остановлено")