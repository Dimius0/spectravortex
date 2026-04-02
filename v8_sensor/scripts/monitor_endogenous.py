# scripts/monitor_endogenous.py
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality

print("=" * 70)
print("🌱 МОНИТОРИНГ ЭНДОГЕННОГО ЦИКЛА")
print("=" * 70)

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16.json')

print(f"\n📊 Поле загружено:")
print(f"   Слов: {len(p.vortices)}")
print(f"   Мод: {len(p.h_field)}")

print("\n🌱 Текущая статистика эндогенного цикла:")
stats = p.get_endogenous_stats()
for key, value in stats.items():
    print(f"   {key}: {value}")

print("\n" + "=" * 70)
print("⏳ Наблюдение... (обновление каждые 60 сек, Ctrl+C для выхода)")
print("=" * 70)

try:
    last_cycle = stats.get('cycle_count', 0)
    while True:
        time.sleep(60)
        stats = p.get_endogenous_stats()
        new_cycle = stats.get('cycle_count', 0)
        
        print(f"\n[{time.strftime('%H:%M:%S')}] Циклов: {new_cycle} (+{new_cycle - last_cycle})")
        print(f"   Фуркаций: {stats.get('furcations', 0)}")
        print(f"   Кросс-резонансов: {stats.get('cross_resonances', 0)}")
        print(f"   Узлов: {stats.get('knots_created', 0)}")
        print(f"   Забыто: {stats.get('decayed', 0)}")
        print(f"   Перегрев: {stats.get('overheated', False)}")
        print(f"   Демпфирований: {stats.get('damping_applied', 0)}")
        print(f"   Всего мод: {stats.get('total_modes', 0)}")
        
        last_cycle = new_cycle
except KeyboardInterrupt:
    print("\n\n✅ Мониторинг остановлен")