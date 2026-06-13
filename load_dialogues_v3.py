#!/usr/bin/env python3
"""
Загрузчик диалогов в поле H — версия 3 (с полной цепочкой импортов)
"""

import json
import sys
import hashlib
import os
import importlib.util
from datetime import datetime

# Пути
REPO_ROOT = r'C:\Users\Dim\source\repos\spectravortex'
RIZOMA_DIR = os.path.join(REPO_ROOT, 'v8_sensor', 'src', 'rizoma')

# Функция для загрузки модуля из файла
def load_module(name, filepath, package=None):
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    if package:
        sys.modules[f'{package}.{name}'] = module
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Загружаем ВСЕ зависимости в правильном порядке
print("Загрузка зависимостей...")

# 1. Базовые модули (без зависимостей)
vortex_path = os.path.join(RIZOMA_DIR, 'vortex.py')
vortex = load_module('vortex', vortex_path)

quantum_path = os.path.join(RIZOMA_DIR, 'quantum_analogy.py')
if os.path.exists(quantum_path):
    quantum = load_module('quantum_analogy', quantum_path)

topology_path = os.path.join(RIZOMA_DIR, 'topology.py')
if os.path.exists(topology_path):
    topology = load_module('topology', topology_path)

endogenous_path = os.path.join(RIZOMA_DIR, 'endogenous.py')
if os.path.exists(endogenous_path):
    endogenous = load_module('endogenous', endogenous_path)

complexity_path = os.path.join(RIZOMA_DIR, 'complexity_utils.py')
if os.path.exists(complexity_path):
    complexity = load_module('complexity_utils', complexity_path)

# 2. resonance_v16_1 (зависит от vortex, quantum_analogy, topology)
resonance_path = os.path.join(RIZOMA_DIR, 'resonance_v16_1.py')
if os.path.exists(resonance_path):
    resonance = load_module('resonance_v16_1', resonance_path)

# 3. personality_v16_1.py (зависит от всех выше)
personality_path = os.path.join(RIZOMA_DIR, 'personality_v16_1.py')
personality = load_module('personality_v16_1', personality_path, 'v8_sensor.src.rizoma')

Personality = personality.Personality
SpectralMode = personality.SpectralMode

INPUT_FILE = os.path.join(REPO_ROOT, 'brain_dump', 'dialogues_json', 'conversations.json')
BASE_FIELD = os.path.join(REPO_ROOT, 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v16_1_auto_20260403_1159.json')
OUTPUT_FIELD = os.path.join(REPO_ROOT, 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v17_0_with_dialogues_v3.json')

print("=" * 60)
print("📂 ЗАГРУЗКА ДИАЛОГОВ В ПОЛЕ H (v3)")
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