#!/usr/bin/env python3
"""
Загрузчик диалогов в поле H — версия 2 (без относительных импортов)
"""

import json
import sys
import hashlib
import os
import importlib.util
from datetime import datetime

# Пути
REPO_ROOT = r'C:\Users\Dim\source\repos\spectravortex'
MODULE_PATH = os.path.join(REPO_ROOT, 'v8_sensor', 'src', 'rizoma', 'personality_v16_1.py')

# Загружаем модуль напрямую
spec = importlib.util.spec_from_file_location('personality_v16_1', MODULE_PATH)
personality = importlib.util.module_from_spec(spec)
sys.modules['personality_v16_1'] = personality
spec.loader.exec_module(personality)

Personality = personality.Personality
SpectralMode = personality.SpectralMode

INPUT_FILE = os.path.join(REPO_ROOT, 'brain_dump', 'dialogues_json', 'conversations.json')
BASE_FIELD = os.path.join(REPO_ROOT, 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v16_1_auto_20260403_1159.json')
OUTPUT_FIELD = os.path.join(REPO_ROOT, 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v17_0_with_dialogues_v3.json')

print("=" * 60)
print("📂 ЗАГРУЗКА ДИАЛОГОВ В ПОЛЕ H (v2)")
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
        
        msg_len = len(content)
        if msg_len < 50:
            tau = 8.0 + (msg_len % 10)
        elif msg_len < 200:
            tau = 16.0 + (msg_len % 5)
        elif msg_len < 1000:
            tau = 22.0 + (msg_len % 3)
        else:
            tau = 31.0 + (msg_len % 5)
        
        if msg_len < 10:
            scale = 0.5
        elif msg_len < 30:
            scale = 1.0
        elif msg_len < 80:
            scale = 3.0
        elif msg_len < 200:
            scale = 5.0
        elif msg_len < 600:
            scale = 10.0
        elif msg_len < 2000:
            scale = 30.0
        else:
            scale = 100.0
        
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