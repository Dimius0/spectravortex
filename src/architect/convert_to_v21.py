#!/usr/bin/env python3
"""
Конвертер старых JSON в формат v21.2
====================================
Читает плоский h_field из v20.2, создаёт 7-слойную структуру,
сохраняет тексты в TextStore.

Использование:
    python convert_to_v21.py ../rizoma/data/personalities/p016_grown_3h.json
    python convert_to_v21.py input.json --output output.json
    python convert_to_v21.py input.json --analyze
"""

import sys
import os
import json
import hashlib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from living_personality_v21 import LivingPersonality, SpectralMode


def convert_old_to_v21(input_path: str, output_path: str = None) -> str:
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_v21.json"
    
    print(f"📂 Читаю: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    old_modes = data.get('h_field', [])
    print(f"   Версия: {data.get('version', 'unknown')}")
    print(f"   Мод: {len(old_modes)}")
    
    lp = LivingPersonality(
        id=data.get('id', 'converted'),
        name=data.get('name', 'Конвертированная v21'),
        text_store_path=f"./text_store_{data.get('id', 'converted')}"
    )
    
    for attr in ['mood', 'energy', 'experience', 'generation', 'dialog_count']:
        if attr in data:
            setattr(lp, attr, data[attr])
    if 'traits' in data:
        lp.traits.update(data['traits'])
    if 'focus' in data:
        lp.focus = data['focus']
    if 'vortices' in data:
        lp.vortices = data['vortices']
    
    converted = 0
    skipped = 0
    
    for i, mode_data in enumerate(old_modes):
        try:
            content = mode_data.get('content', '')
            tau = mode_data.get('tau', 16.0)
            scale = mode_data.get('scale', None)
            
            if scale is None:
                content_len = len(content)
                if content_len > 500:
                    scale = 30.0
                elif content_len > 100:
                    scale = 15.0
                elif content_len > 20:
                    scale = 8.0
                else:
                    scale = 5.0
            
            trace_id = mode_data.get('trace_id', '') or hashlib.md5(
                f"{content}_{i}_{tau}".encode('utf-8')
            ).hexdigest()[:8]
            
            mode = SpectralMode(
                tau=tau,
                amplitude=mode_data.get('amplitude', 0.5),
                content=content,
                themes=mode_data.get('themes', []),
                trace_id=trace_id,
                creator=mode_data.get('creator', 'converted'),
                scale=scale,
                phase=mode_data.get('phase', 0.0),
            )
            
            lp.add_to_h_field(mode)
            converted += 1
            
            if converted % 1000 == 0:
                print(f"   Конвертировано: {converted}/{len(old_modes)}")
        
        except Exception as e:
            print(f"   ⚠️ Ошибка в моде {i}: {e}")
            skipped += 1
    
    print(f"\n✅ Конвертировано: {converted}")
    if skipped:
        print(f"⚠️ Пропущено: {skipped}")
    
    lp.save(output_path)
    
    stats = lp.get_field_stats()
    print(f"\n📊 Распределение по слоям:")
    for layer_id in range(1, 8):
        count = stats.get('modes_per_layer', {}).get(layer_id, 0)
        bar = '█' * min(50, count // 20) if count else ''
        print(f"   Слой {layer_id}: {count:5d} {bar}")
    
    print(f"\n💾 Сохранено: {output_path}")
    print(f"📦 TextStore: {lp.text_store.stats()['total_texts']} текстов")
    
    return output_path


def analyze_v21(filepath: str):
    print(f"\n=== Анализ {filepath} ===")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    modes = data.get('h_field', [])
    print(f"Всего мод: {len(modes)}")
    
    taus = [m['tau'] for m in modes if m.get('tau', 0) > 0]
    if taus:
        taus.sort()
        print(f"Tau: min={taus[0]:.1f}, 10%={taus[len(taus)//10]:.1f}, "
              f"50%={taus[len(taus)//2]:.1f}, 90%={taus[len(taus)*9//10]:.1f}, "
              f"max={taus[-1]:.1f}")
    
    scales = [m['scale'] for m in modes if m.get('scale', 0) > 0]
    if scales:
        scale_dist = {}
        for s in scales:
            if s >= 25: layer = 7
            elif s >= 18: layer = 6
            elif s >= 12: layer = 5
            elif s >= 8: layer = 4
            elif s >= 4: layer = 3
            elif s >= 2: layer = 2
            else: layer = 1
            scale_dist[layer] = scale_dist.get(layer, 0) + 1
        
        print("Распределение по слоям (scale):")
        for layer in sorted(scale_dist):
            print(f"  Слой {layer}: {scale_dist[layer]}")
    
    with_text_id = sum(1 for m in modes if m.get('text_id'))
    print(f"Мод с text_id: {with_text_id}/{len(modes)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python convert_to_v21.py input.json")
        print("  python convert_to_v21.py input.json --output output.json")
        print("  python convert_to_v21.py input.json --analyze")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if not os.path.exists(input_path):
        print(f"❌ Файл не найден: {input_path}")
        sys.exit(1)
    
    output_path = None
    analyze_only = False
    
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
        elif arg == '--analyze':
            analyze_only = True
    
    if analyze_only:
        analyze_v21(input_path)
    else:
        result_path = convert_old_to_v21(input_path, output_path)
        analyze_v21(result_path)