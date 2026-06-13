#!/usr/bin/env python3
"""
Загрузчик диалогов в поле H — версия 4 (исправленная структура fragments)
"""

import sys
import os
import json
import hashlib
import time

sys.path.insert(0, os.path.join('v8_sensor', 'src'))
from rizoma.living_personality_v20 import LivingPersonality, SpectralMode

REPO_ROOT = r'C:\Users\Dim\source\repos\spectravortex'
INPUT_FILE = os.path.join(REPO_ROOT, 'brain_dump', 'dialogues_json', 'conversations.json')
BASE_FIELD = os.path.join(REPO_ROOT, 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v16_1_auto_20260403_1159.json')
OUTPUT_FIELD = os.path.join(REPO_ROOT, 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v17_0_with_dialogues_v4.json')

print("=" * 60)
print("📂 ЗАГРУЗКА ДИАЛОГОВ В ПОЛЕ H (v4 — fragments)")
print("=" * 60)

# 1. Загружаем или создаём личность
print("\n1. Загружаю базовое поле...")
try:
    p = LivingPersonality.load(BASE_FIELD)
    print(f"   ✅ Загружено: {len(p.h_field)} мод")
except:
    print("   ⚠️ Создаю новую личность...")
    p = LivingPersonality(id="p016", name="VMMS Field v17.4")

# 2. Загружаем conversations.json
print(f"\n2. Читаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

conversations = data if isinstance(data, list) else [data]
print(f"   Диалогов: {len(conversations)}")

# 3. Обрабатываем
total_messages = 0
total_loaded = 0
total_skipped = 0
start_time = time.time()

print("\n3. Обработка сообщений...")

for conv_idx, conv in enumerate(conversations):
    if conv_idx % 100 == 0 and conv_idx > 0:
        elapsed = time.time() - start_time
        speed = total_loaded / elapsed if elapsed > 0 else 0
        print(f"   Диалог {conv_idx}/{len(conversations)} | "
              f"Загружено: {total_loaded} | "
              f"Скорость: {speed:.0f} msg/s")
    
    mapping = conv.get('mapping', {})
    title = conv.get('title', 'Без названия')[:100]
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        # ИЗВЛЕКАЕМ КОНТЕНТ ИЗ FRAGMENTS
        content = ""
        role = "unknown"
        msg_type = "unknown"
        
        fragments = message.get('fragments', [])
        for frag in fragments:
            if isinstance(frag, dict):
                content = frag.get('content', '')
                msg_type = frag.get('type', 'unknown')
                if content:
                    break  # берём первый фрагмент с контентом
        
        # Определяем роль
        author = message.get('author', {})
        if isinstance(author, dict):
            role = author.get('role', 'unknown')
        
        # Пропускаем пустые
        if not content or not isinstance(content, str) or len(content.strip()) < 10:
            total_skipped += 1
            continue
        
        total_messages += 1
        msg_len = len(content)
        
        # Вычисляем tau
        if msg_len < 50:
            tau = 8.0 + (msg_len % 10)
        elif msg_len < 200:
            tau = 16.0 + (msg_len % 5)
        elif msg_len < 1000:
            tau = 22.0 + (msg_len % 3)
        else:
            tau = 31.0 + (msg_len % 5)
        
        # Вычисляем scale
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
        
        # Создаём моду
        try:
            mode = SpectralMode(
                tau=tau,
                amplitude=0.5,
                content=content[:1000],
                themes=['dialogue', role, msg_type, title[:50]],
                trace_id=f"dial_{hashlib.md5(content[:100].encode()).hexdigest()[:8]}",
                creator=role,
                scale=scale,
            )
            p.h_field.append(mode)
            total_loaded += 1
        except Exception as e:
            continue

elapsed = time.time() - start_time

print(f"\n📊 Статистика:")
print(f"   Диалогов: {len(conversations)}")
print(f"   Сообщений всего: {total_messages}")
print(f"   Загружено: {total_loaded}")
print(f"   Пропущено: {total_skipped}")
print(f"   Мод в поле: {len(p.h_field)}")
print(f"   Время: {elapsed:.1f} сек")
if elapsed > 0:
    print(f"   Скорость: {total_loaded/elapsed:.0f} msg/s")

# 4. Сохраняем
print(f"\n4. Сохраняю...")
os.makedirs(os.path.dirname(OUTPUT_FIELD), exist_ok=True)

try:
    p.save(OUTPUT_FIELD)
    print(f"   💾 Сохранено: {OUTPUT_FIELD}")
except:
    # Ручное сохранение
    data_out = {
        "id": p.id,
        "name": getattr(p, 'name', 'Unknown'),
        "h_field": [{
            "tau": m.tau, "amplitude": m.amplitude,
            "content": m.content[:200] if hasattr(m, 'content') else "",
            "themes": getattr(m, 'themes', []),
            "trace_id": getattr(m, 'trace_id', ""),
            "scale": getattr(m, 'scale', 1.0)
        } for m in p.h_field]
    }
    with open(OUTPUT_FIELD, 'w', encoding='utf-8') as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)
    print(f"   💾 Сохранено вручную: {OUTPUT_FIELD}")

print("=" * 60)
print("✅ Готово!")
print("=" * 60)