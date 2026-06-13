#!/usr/bin/env python3
"""
Загрузчик диалогов в поле H — версия для conversations.json (OpenAI формат)
"""

import json
import sys
import hashlib
from datetime import datetime

sys.path.insert(0, 'src')
from personality_v16_1 import Personality, SpectralMode

INPUT_FILE = 'brain_dump/dialogues_json/conversations.json'
BASE_FIELD = 'src/rizoma/data/personalities/p016_fractal_v17_0.json'
OUTPUT_FIELD = 'src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v3.json'

print("=" * 60)
print("📂 ЗАГРУЗКА ДИАЛОГОВ В ПОЛЕ H")
print("=" * 60)

# 1. Загружаем базовое поле
print("\n1. Загружаю базовое поле...")
try:
    p = Personality.load(BASE_FIELD)
    print(f"   Загружено: {len(p.h_field)} мод, {len(p.vortices)} слов")
except FileNotFoundError:
    print("   Базовое поле не найдено, создаю новое...")
    p = Personality(id="p016", name="VMMS Field v17.3")

# 2. Загружаем conversations.json
print(f"\n2. Читаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"   Загружено диалогов: {len(data)}")

# 3. Обрабатываем каждый диалог
total_messages = 0
total_loaded = 0

for conv in data:
    mapping = conv.get('mapping', {})
    title = conv.get('title', 'Без названия')
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        content = message.get('content')
        role = message.get('author', {}).get('role', 'unknown')
        
        if not content or not isinstance(content, str):
            continue
        
        total_messages += 1
        
        # Создаём спектральную моду
        # τ зависит от длины сообщения (фрактальная модель)
        msg_len = len(content)
        if msg_len < 50:
            tau = 8.0 + (msg_len % 10)
        elif msg_len < 200:
            tau = 16.0 + (msg_len % 5)
        elif msg_len < 1000:
            tau = 22.0 + (msg_len % 3)
        else:
            tau = 31.0 + (msg_len % 5)
        
        # Масштаб по 7-уровневой фрактальной модели:
        # 1: буквы/знаки (scale 0.1-0.5)
        # 2: слоги (scale 0.5-1.0)
        # 3: слова (scale 1.0-3.0)
        # 4: словосочетания (scale 3.0-5.0)   ← пропустил
        # 5: предложения (scale 5.0-15.0)
        # 6: абзацы (scale 15.0-40.0)
        # 7: тексты (scale 40.0+)
        
        if msg_len < 10:
            scale = 0.5          # буквы/знаки
        elif msg_len < 30:
            scale = 1.0          # слоги
        elif msg_len < 80:
            scale = 3.0          # слова
        elif msg_len < 200:
            scale = 5.0          # словосочетания ← вот он
        elif msg_len < 600:
            scale = 10.0         # предложения
        elif msg_len < 2000:
            scale = 30.0         # абзацы
        else:
            scale = 100.0        # тексты
        
        mode = SpectralMode(
            tau=tau,
            amplitude=0.5,
            content=content[:1000],
            themes=['dialogue', role, title[:50]],
            trace_id=f"dialogue_{hashlib.md5(content[:100].encode()).hexdigest()[:8]}",
            creator=role,
            scale=scale,
        )
        p.add_to_h_field(mode)
        total_loaded += 1
        
        if total_loaded % 10000 == 0:
            print(f"   Загружено {total_loaded} сообщений...")

print(f"\n3. Статистика загрузки:")
print(f"   Всего сообщений в диалогах: {total_messages}")
print(f"   Загружено в поле H: {total_loaded}")
print(f"   Мод в поле после загрузки: {len(p.h_field)}")

# 4. Сохраняем
print(f"\n4. Сохраняю поле...")
p.save(OUTPUT_FIELD)
print(f"💾 Сохранено: {OUTPUT_FIELD}")
print("=" * 60)