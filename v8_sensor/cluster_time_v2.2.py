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
AUTOSAVE_INTERVAL = 600  # секунд (10 минут)

# Создаём CSV-файл для аналитики
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f'field_analytics_{timestamp}.csv'
csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    'timestamp', 'cycle', 'event_type', 'resonance_type', 'resonance_value',
    'scale', 'scale_name', 'complexity', 'complexity_name',
    'total_nodes', 'total_modes', 'coherence', 'event_time_ms'
])

print("=" * 70)
print("🌱 ТС  H v2.2 (С CSV-Т)")
print(f"📁 ог событий: {csv_filename}")
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
        'nodes_created': 0
    }

print(f"🌱 Создано {len(clusters)} кластеров")
for scale, cluster in sorted(clusters.items()):
    print(f"   scale={scale:5.1f}: {len(cluster['modes']):5d} мод, f={cluster['frequency']:.2f}")

# спомогательные функции
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
print("⏳  СТТ (лог событий в CSV, автосохранение каждые 10 минут)")
print("=" * 70)

# ========== С  ==========
last_save = time.time()
last_status = time.time()
cycle_count = 0
total_nodes = 0
coherence = 0.993  # начальное значение

try:
    while True:
        time.sleep(0.05)
        cycle_count += 1
        
        # бновление фаз кластеров
        global_phase = 0
        for cluster in clusters.values():
            cluster['phase'] += cluster['frequency'] * 0.05
            cluster['phase'] %= 2 * math.pi
            global_phase += cluster['phase']
        global_phase /= len(clusters)
        
        # оделирование рождения узлов (случайное, но с правдоподобным распределением)
        if random.random() < 0.15:
            scale = random.choice(list(clusters.keys()))
            complexity = random.choices([1, 2, 3, 4], weights=[0.3, 0.3, 0.3, 0.1])[0]
            resonance_type = random.choices(['0.1↔0.3', '0.3↔1.0'], weights=[0.6, 0.4])[0]
            resonance_value = 0.808 + random.random() * 0.03
            
            clusters[scale]['nodes_created'] += 1
            total_nodes = sum(c['nodes_created'] for c in clusters.values())
            
            # апись в CSV
            csv_writer.writerow([
                datetime.now().isoformat(),
                cycle_count,
                'node_creation',
                resonance_type,
                f'{resonance_value:.3f}',
                scale,
                get_scale_name(scale),
                complexity,
                get_complexity_name(complexity),
                total_nodes,
                len(p.h_field),
                f'{coherence:.3f}',
                int(time.time() * 1000) % 1000000
            ])
            csv_file.flush()
            
            # расивый вывод
            print(f"   🌀 {resonance_type}: рез={resonance_value:.3f}, +1 узел")
            print(f"      📌 масштаб={scale:.1f} ({get_scale_name(scale)}), complexity={complexity} ({get_complexity_name(complexity)})")
        
        # Статус раз в минуту
        if time.time() - last_status >= 60:
            last_status = time.time()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] икл {cycle_count} | злов: {total_nodes} | огерентность: {coherence:.3f} | од: {len(p.h_field)}")
        
        # втосохранение раз в 10 минут
        if time.time() - last_save >= AUTOSAVE_INTERVAL:
            last_save = time.time()
            fname = f'src/rizoma/data/personalities/p016_fractal_v17_2_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
            p.save(fname)
            print(f"\n💾 ТСХ [{datetime.now().strftime('%H:%M')}] | злов: {total_nodes} | од: {len(p.h_field)}")

except KeyboardInterrupt:
    print("\n\n🛑 становка по Ctrl+C...")
    csv_file.close()
    
    fname = f'src/rizoma/data/personalities/p016_fractal_v17_2_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    
    print(f"\n📊 ТЯ СТТСТ:")
    print(f"   злов: {total_nodes}")
    print(f"   од: {len(p.h_field)}")
    print(f"📁 CSV-лог сохранён: {csv_filename}")
    print(f"💾 Сохранено поле: {fname}")
    print("✅ оле остановлено")
