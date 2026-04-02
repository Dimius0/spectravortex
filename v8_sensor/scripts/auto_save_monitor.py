#!/usr/bin/env python3
"""
Автоматическое сохранение поля H без остановки эндогенного цикла
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality

print("=" * 70)
print("🌱 АВТОСОХРАНЕНИЕ ПОЛЯ H")
print("=" * 70)

# Загружаем поле
p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16.json')
print(f"\n📊 Поле загружено:")
print(f"   Слов: {len(p.vortices)}")
print(f"   Мод: {len(p.h_field)}")

print("\n⏳ Мониторинг и автосохранение каждые 30 минут...")
print("   (Ctrl+C для остановки)")
print("=" * 70)

last_cycle = 0
save_counter = 0
last_stats_time = time.time()

try:
    while True:
        time.sleep(60)  # проверяем раз в минуту
        
        stats = p.get_endogenous_stats()
        cycle = stats.get('cycle_count', 0)
        
        # Показываем статистику раз в 5 минут
        if time.time() - last_stats_time >= 300:
            last_stats_time = time.time()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]")
            print(f"   Циклов: {cycle}")
            print(f"   Фуркаций: {stats.get('furcations', 0)}")
            print(f"   Кросс-резонансов: {stats.get('cross_resonances', 0)}")
            print(f"   Узлов: {stats.get('knots_created', 0)}")
            print(f"   Всего мод: {stats.get('total_modes', 0)}")
        
        # Сохраняем каждые 30 минут (при cycle кратно 60)
        if cycle >= save_counter + 60:
            save_counter = cycle
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            save_path = f"src/rizoma/data/personalities/p016_fractal_v16_auto_{timestamp}.json"
            
            print(f"\n💾 АВТОСОХРАНЕНИЕ [{timestamp}]")
            p.save(save_path)
            print(f"   Сохранено: {save_path}")
            print(f"   Моды: {stats.get('total_modes', 0)} | Узлы: {stats.get('knots_created', 0)}")
            
except KeyboardInterrupt:
    print("\n\n✅ Мониторинг остановлен")
    # Финальное сохранение
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"src/rizoma/data/personalities/p016_fractal_v16_final_{timestamp}.json"
    p.save(save_path)
    print(f"💾 Финальное сохранение: {save_path}")