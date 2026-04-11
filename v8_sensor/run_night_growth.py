import sys
import time
from datetime import datetime
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

print("=" * 70)
print("🌱  СТ Я H v17.0")
print("=" * 70)

# агружаем поле
p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_20260403_173544.json')

print(f" Слов: {len(p.vortices)}")
print(f" од: {len(p.h_field)}")
print(f" злов (старт): {len(p.resonance_engine.topology.nodes) if hasattr(p.resonance_engine, 'topology') else 0}")
print("=" * 70)
print("⏳ оле растёт. втосохранение каждые 30 минут.")
print("   ажми Ctrl+C для остановки с сохранением")
print("=" * 70)

last_save = time.time()
last_status = time.time()

try:
    while True:
        time.sleep(30)
        
        now = time.time()
        stats = p.get_endogenous_stats()
        knots = len(p.resonance_engine.topology.nodes) if hasattr(p.resonance_engine, 'topology') else 0
        modes = len(p.h_field)
        
        if now - last_status >= 60:
            last_status = now
            print(f"[{datetime.now().strftime('%H:%M:%S')}] злов: {knots} | од: {modes}")
        
        if now - last_save >= 1800:
            last_save = now
            fname = f'src/rizoma/data/personalities/p016_fractal_v17_0_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
            p.save(fname)
            print(f"💾 ТСХ | злов: {knots} | од: {modes}")

except KeyboardInterrupt:
    print("\n\n🛑 становка...")
    fname = f'src/rizoma/data/personalities/p016_fractal_v17_0_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    knots = len(p.resonance_engine.topology.nodes) if hasattr(p.resonance_engine, 'topology') else 0
    print(f"💾 инальное сохранение: {fname}")
    print(f"   злов: {knots} | од: {len(p.h_field)}")
    print("✅ оле остановлено")
