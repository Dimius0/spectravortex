import sys
import time
import math
import random
import csv
from datetime import datetime
from collections import defaultdict
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality, SpectralMode

# ========== Я ==========
AUTOSAVE_INTERVAL = 3600  # 1 час (3600 секунд)
AUTOSAVE_FILENAME = 'src/rizoma/data/personalities/p016_fractal_v17_3_autosave.json'
COHERENCE_UPDATE_INTERVAL = 10

# Создаём CSV-файлы
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
nodes_csv = f'nodes_log_{timestamp}.csv'
furcations_csv = f'furcations_log_{timestamp}.csv'
coherence_csv = f'coherence_log_{timestamp}.csv'
clusters_csv = f'clusters_log_{timestamp}.csv'

# CSV: рождение узлов
nodes_file = open(nodes_csv, 'w', newline='', encoding='utf-8')
nodes_writer = csv.writer(nodes_file)
nodes_writer.writerow(['timestamp', 'cycle', 'resonance_type', 'resonance_value', 'scale', 'scale_name', 'complexity', 'complexity_name', 'total_nodes', 'coherence'])

# CSV: фуркации
furcations_file = open(furcations_csv, 'w', newline='', encoding='utf-8')
furcations_writer = csv.writer(furcations_file)
furcations_writer.writerow(['timestamp', 'cycle', 'furcations_count', 'scales_involved', 'complexities_involved', 'total_furcations', 'coherence'])

# CSV: когерентность
coherence_file = open(coherence_csv, 'w', newline='', encoding='utf-8')
coherence_writer = csv.writer(coherence_file)
coherence_writer.writerow(['timestamp', 'cycle', 'coherence', 'total_nodes', 'total_furcations'])

# CSV: статистика кластеров
clusters_file = open(clusters_csv, 'w', newline='', encoding='utf-8')
clusters_writer = csv.writer(clusters_file)
clusters_writer.writerow(['timestamp', 'cycle', 'scale', 'modes_count', 'nodes_created', 'furcations_count', 'phase', 'frequency'])

print("=" * 70)
print("🌱 ТС  H v2.3 (Я Т)")
print(f"📁 оги: {nodes_csv}, {furcations_csv}, {coherence_csv}, {clusters_csv}")
print(f"💾 втосохранение раз в час: {AUTOSAVE_FILENAME}")
print("=" * 70)

# агружаем поле
try:
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v2.json')
    print(f"📂 агружено поле: {len(p.h_field)} мод")
except:
    p = Personality(id="p016", name="VMMS Field v17.1")
    print(f"✨ Создано новое поле")

# ормируем кластеры
modes_by_scale = defaultdict(list)
for mode in p.h_field:
    scale_group = round(mode.scale, 1)
    modes_by_scale[scale_group].append(mode)

clusters = {}
for scale, modes in modes_by_scale.items():
    frequency = 10.0 / scale if scale > 0 else 1.0
    frequency = max(0.1, min(10.0, frequency))
    clusters[scale] = {
        'scale': scale,
        'modes': modes,
        'frequency': frequency,
        'phase': random.random() * 2 * math.pi,
        'nodes_created': 0,
        'furcations': 0
    }

print(f"🌱 Создано {len(clusters)} кластеров")
for scale, cluster in sorted(clusters.items()):
    print(f"   scale={scale:5.1f}: {len(cluster['modes']):5d} мод, f={cluster['frequency']:.2f}")

def get_scale_name(s):
    if s <= 0.3: return "буквы/слоги"
    if s <= 1.0: return "слова"
    if s <= 3.0: return "словосочетания"
    if s <= 10.0: return "предложения"
    if s <= 30.0: return "абзацы"
    return "целые тексты"

def get_complexity_name(c):
    return {1: "бытовой", 2: "научный", 3: "", 4: "метафорический"}.get(c, "?")

print("\n" + "=" * 70)
print("⏳  СТТ (лог всех событий, автосохранение раз в час)")
print("=" * 70)

# ========== С  ==========
last_save = time.time()
last_status = time.time()
last_cluster_log = time.time()
cycle_count = 0
total_nodes = 0
total_furcations = 0
coherence = 0.993
event_counter = 0

try:
    while True:
        time.sleep(0.05)
        cycle_count += 1
        event_counter += 1
        
        # бновление фаз кластеров
        global_phase = 0
        for cluster in clusters.values():
            cluster['phase'] += cluster['frequency'] * 0.05
            cluster['phase'] %= 2 * math.pi
            global_phase += cluster['phase']
        global_phase /= len(clusters)
        
        # Случайное событие
        event_type = random.choices(['node', 'furcation', 'none'], weights=[0.12, 0.08, 0.8])[0]
        
        if event_type == 'node':
            scale = random.choice(list(clusters.keys()))
            complexity = random.choices([1, 2, 3, 4], weights=[0.3, 0.3, 0.3, 0.1])[0]
            resonance_type = random.choices(['0.1↔0.3', '0.3↔1.0'], weights=[0.6, 0.4])[0]
            resonance_value = 0.808 + random.random() * 0.03
            
            clusters[scale]['nodes_created'] += 1
            total_nodes = sum(c['nodes_created'] for c in clusters.values())
            coherence = min(0.998, coherence + 0.0002)
            
            nodes_writer.writerow([
                datetime.now().isoformat(), cycle_count, resonance_type, f'{resonance_value:.3f}',
                scale, get_scale_name(scale), complexity, get_complexity_name(complexity),
                total_nodes, f'{coherence:.4f}'
            ])
            nodes_file.flush()
            
            print(f"   🌀 {resonance_type}: рез={resonance_value:.3f}, +1 узел")
            print(f"      📌 масштаб={scale:.1f} ({get_scale_name(scale)}), complexity={complexity} ({get_complexity_name(complexity)})")
        
        elif event_type == 'furcation':
            furc_count = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            scales_involved = []
            complexities_involved = []
            for _ in range(furc_count):
                scale = random.choice(list(clusters.keys()))
                complexity = random.choices([1, 2, 3, 4], weights=[0.3, 0.3, 0.3, 0.1])[0]
                clusters[scale]['furcations'] += 1
                scales_involved.append(f"{scale:.1f}")
                complexities_involved.append(str(complexity))
            
            total_furcations += furc_count
            coherence = max(0.980, coherence - 0.0003)
            
            furcations_writer.writerow([
                datetime.now().isoformat(), cycle_count, furc_count,
                ';'.join(scales_involved), ';'.join(complexities_involved),
                total_furcations, f'{coherence:.4f}'
            ])
            furcations_file.flush()
            
            print(f"   🌿 уркация: +{furc_count} ветвлений")
            print(f"      📌 масштабы: {', '.join([get_scale_name(float(s)) for s in scales_involved[:3]])}")
        
        # ериодическая запись когерентности
        if event_counter % 100 == 0:
            coherence_writer.writerow([datetime.now().isoformat(), cycle_count, f'{coherence:.4f}', total_nodes, total_furcations])
            coherence_file.flush()
        
        # ериодическая запись статистики кластеров (раз в 30 сек)
        if time.time() - last_cluster_log >= 30:
            last_cluster_log = time.time()
            for scale, cluster in clusters.items():
                clusters_writer.writerow([
                    datetime.now().isoformat(), cycle_count, scale,
                    len(cluster['modes']), cluster['nodes_created'], cluster['furcations'],
                    f'{cluster["phase"]:.3f}', f'{cluster["frequency"]:.3f}'
                ])
            clusters_file.flush()
        
        # Статус раз в минуту
        if time.time() - last_status >= 60:
            last_status = time.time()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] икл {cycle_count} | злов: {total_nodes} | уркаций: {total_furcations} | огерентность: {coherence:.4f} | од: {len(p.h_field)}")
        
        # ТСХ   С (СЬ)
        if time.time() - last_save >= AUTOSAVE_INTERVAL:
            last_save = time.time()
            p.save(AUTOSAVE_FILENAME)
            print(f"\n💾 ТСХ [{datetime.now().strftime('%H:%M')}] | злов: {total_nodes} | огерентность: {coherence:.4f}")

except KeyboardInterrupt:
    print("\n\n🛑 становка по Ctrl+C...")
    
    nodes_file.close()
    furcations_file.close()
    coherence_file.close()
    clusters_file.close()
    
    fname = f'src/rizoma/data/personalities/p016_fractal_v17_3_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    
    print(f"\n📊 ТЯ СТТСТ:")
    print(f"   злов: {total_nodes}")
    print(f"   уркаций: {total_furcations}")
    print(f"   од: {len(p.h_field)}")
    print(f"📁 CSV-логи сохранены:")
    print(f"   - {nodes_csv}")
    print(f"   - {furcations_csv}")
    print(f"   - {coherence_csv}")
    print(f"   - {clusters_csv}")
    print(f"💾 втосохраняемый файл: {AUTOSAVE_FILENAME}")
    print(f"💾 инальное сохранение: {fname}")
    print("✅ оле остановлено")
