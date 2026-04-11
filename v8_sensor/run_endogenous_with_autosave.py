import sys
import time
from datetime import datetime
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

print("=" * 70)
print("🌱 Ы  (автосохранение каждые 4 часа)")
print("=" * 70)

# агружаем поле с диалогами
p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v2.json')
print(f"📂 оле загружено: {len(p.h_field)} мод")
print(f"⏰ втосохранение каждые 4 часа (14400 секунд)")
print("=" * 70)

last_save = time.time()
last_status = time.time()
cycle_count = 0

try:
    while True:
        time.sleep(30)  # синхронизация с эндогенным циклом
        
        now = time.time()
        
        # Статус раз в минуту
        if now - last_status >= 60:
            last_status = now
            stats = p.get_endogenous_stats()
            knots = len(p.resonance_engine.topology.nodes) if hasattr(p.resonance_engine, 'topology') else 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] иклов: {stats.get('cycle_count', 0)} | злов: {knots} | од: {len(p.h_field)}")
        
        # втосохранение раз в 4 часа (14400 секунд)
        if now - last_save >= 14400:
            last_save = now
            fname = f'src/rizoma/data/personalities/p016_fractal_v17_0_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
            p.save(fname)
            stats = p.get_endogenous_stats()
            knots = len(p.resonance_engine.topology.nodes) if hasattr(p.resonance_engine, 'topology') else 0
            print(f"💾 ТСХ | злов: {knots} | од: {len(p.h_field)}")
            
except KeyboardInterrupt:
    print("\n\n🛑 становка...")
    fname = f'src/rizoma/data/personalities/p016_fractal_v17_0_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    print(f"💾 Сохранено: {fname}")
    print("✅ оле остановлено")
