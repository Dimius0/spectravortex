"""
auto_checkpoint.py — автосохранение поля каждые 30 минут (ПЕРЕЗАПИСЬ)
"""
import sys
import time
import os
from datetime import datetime

sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

CHECKPOINT_FILE = 'src/rizoma/data/personalities/p016_fractal_v16_1_checkpoint.json'
INTERVAL = 1800  # 30 минут

print("=" * 60)
print("🔄 АВТОСОХРАНЕНИЕ ПОЛЯ H (перезапись)")
print(f"📁 Файл: {CHECKPOINT_FILE}")
print(f"⏱️ Интервал: {INTERVAL // 60} минут")
print("=" * 60)
print("Нажми Ctrl+C для остановки")
print()

last_mb = 0

try:
    while True:
        time.sleep(INTERVAL)
        
        try:
            # Загружаем текущее поле
            p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_1.json')
            
            # Сохраняем ПЕРЕЗАПИСЬЮ (заменяет старый файл)
            p.save(CHECKPOINT_FILE)
            
            # Проверяем размер файла
            size_mb = os.path.getsize(CHECKPOINT_FILE) / 1024 / 1024
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 ПЕРЕЗАПИСАНО: {len(p.h_field)} мод, {len(p.vortices)} слов")
            print(f"    📦 Размер: {size_mb:.1f} МБ")
            
            # Темп роста
            if last_mb > 0:
                delta = len(p.h_field) - last_mb
                print(f"    📈 Рост: +{delta} мод (≈{delta/30:.1f} мод/мин)")
            last_mb = len(p.h_field)
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            
except KeyboardInterrupt:
    print("\n🛑 Автосохранение остановлено")