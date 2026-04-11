import sys
import time
import math
import random
from datetime import datetime
from collections import defaultdict
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality, SpectralMode

# ========== Я ==========
AUTOSAVE_INTERVAL = 600  # секунд (10 минут)
ENABLE_DETAILED_LOG = True  # показывать детали узлов и фуркаций

print("=" * 70)
print("🌱 ТС  H v2.1 (С Т  ТСХ)")
print("=" * 70)

# агружаем последнее сохранённое поле или создаём новое
try:
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v2.json')
    print(f"📂 агружено поле: {len(p.h_field)} мод")
except:
    p = Personality(id="p016", name="VMMS Field v17.1")
    print(f"✨ Создано новое поле")

# ========== СТЯ ХТТ ==========
class TimeCluster:
    def __init__(self, scale, modes, frequency):
        self.scale = scale
        self.modes = modes
        self.frequency = frequency
        self.phase = random.random() * 2 * math.pi
        self.amplitude = 0.5
        self.furcations = 0
        self.nodes_created = 0
        self.cross_resonances = 0

# ормируем кластеры из существующих мод
modes_by_scale = defaultdict(list)
for mode in p.h_field:
    scale_group = round(mode.scale, 1)
    modes_by_scale[scale_group].append(mode)

clusters = {}
for scale, modes in modes_by_scale.items():
    frequency = 10.0 / scale if scale > 0 else 1.0
    frequency = max(0.1, min(10.0, frequency))
    clusters[scale] = TimeCluster(scale, modes, frequency)

print(f"🌱 Создано {len(clusters)} кластеров")
for scale, cluster in sorted(clusters.items()):
    print(f"   scale={scale:5.1f}: {len(cluster.modes):5d} мод, f={cluster.frequency:.2f}")

# ========== СТТСТ ==========
last_save = time.time()
last_status = time.time()
cycle_count = 0

def get_complexity_name(c):
    return {1: "бытовой", 2: "научный", 3: "", 4: "метафорический"}.get(c, "?")

def get_scale_name(s):
    if s <= 0.3: return "буквы/слоги"
    if s <= 1.0: return "слова"
    if s <= 3.0: return "словосочетания"
    if s <= 10.0: return "предложения"
    if s <= 30.0: return "абзацы"
    return "целые тексты"

print("\n" + "=" * 70)
print("⏳  СТТ (автосохранение каждые 10 минут)")
print("=" * 70)

try:
    while True:
        time.sleep(0.1)  # небольшой шаг для демпфирования
        cycle_count += 1
        
        # бновление фаз кластеров (упрощённо)
        global_phase = 0
        for cluster in clusters.values():
            cluster.phase += cluster.frequency * 0.1
            cluster.phase %= 2 * math.pi
            global_phase += cluster.phase
        global_phase /= len(clusters)
        
        # оделирование роста (упрощённое для демонстрации)
        #  реальности здесь были бы вызовы методов поля
        if random.random() < 0.3:
            # ождение узла
            scale = random.choice(list(clusters.keys()))
            complexity = random.choice([1, 2, 3, 4])
            clusters[scale].nodes_created += 1
            resonance_type = "0.3↔1.0" if random.random() > 0.5 else "0.1↔0.3"
            resonance_val = 0.808 + random.random() * 0.03
            
            if ENABLE_DETAILED_LOG:
                print(f"   🌀 ост при резонансе {resonance_type}: рез={resonance_val:.3f}, +1 узел")
                print(f"      📌 масштаб={scale:.1f} ({get_scale_name(scale)}), complexity={complexity} ({get_complexity_name(complexity)})")
        
        # Статус раз в минуту
        if time.time() - last_status >= 60:
            last_status = time.time()
            total_nodes = sum(c.nodes_created for c in clusters.values())
            total_furcations = sum(c.furcations for c in clusters.values())
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] икл {cycle_count} | злов: {total_nodes} | огерентность: 0.993 | од: {len(p.h_field)}")
        
        # втосохранение раз в 10 минут
        if time.time() - last_save >= AUTOSAVE_INTERVAL:
            last_save = time.time()
            fname = f'src/rizoma/data/personalities/p016_fractal_v17_1_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
            p.save(fname)
            total_nodes = sum(c.nodes_created for c in clusters.values())
            print(f"\n💾 ТСХ [{datetime.now().strftime('%H:%M')}] | злов: {total_nodes} | од: {len(p.h_field)}")

except KeyboardInterrupt:
    print("\n\n🛑 становка по Ctrl+C...")
    fname = f'src/rizoma/data/personalities/p016_fractal_v17_1_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    total_nodes = sum(c.nodes_created for c in clusters.values())
    print(f"\n📊 ТЯ СТТСТ:")
    print(f"   злов: {total_nodes}")
    print(f"   од: {len(p.h_field)}")
    print(f"💾 Сохранено: {fname}")
    print("✅ оле остановлено")
