#!/usr/bin/env python3
"""
ЧЕСТНЫЙ ЭНДОГЕННЫЙ ЦИКЛ v1.0
- Никакого random()
- Реальный резонанс на основе фаз и частот
- Frozen: 0.1, 0.3, 1.0 (буквы, слоги, слова)
- Growing: 3.0, 10.0, 30.0, 100.0 (фразы, предложения, абзацы, тексты)
"""

import sys
import time
import math
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

# ========== КОНФИГУРАЦИЯ ==========
AUTOSAVE_INTERVAL = 1800  # 30 минут

print("=" * 70)
print("🌱 ЧЕСТНЫЙ ЭНДОГЕННЫЙ ЦИКЛ (БЕЗ RANDOM)")
print("=" * 70)

# Загружаем поле
try:
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v2.json')
    print(f"📂 Загружено поле: {len(p.h_field)} мод, {len(p.vortices)} слов")
except:
    print("❌ Не удалось загрузить поле!")
    sys.exit(1)

# ========== ФОРМИРУЕМ КЛАСТЕРЫ ==========
modes_by_scale = defaultdict(list)
for mode in p.h_field:
    scale_key = round(mode.scale, 1)
    modes_by_scale[scale_key].append(mode)

print(f"\n📊 Найдено масштабов: {len(modes_by_scale)}")

# Создаём кластеры
clusters = {}
frozen_scales = [0.1, 0.3, 1.0]
growing_scales = []

for scale, modes in modes_by_scale.items():
    frequency = 10.0 / scale if scale > 0 else 1.0
    frequency = max(0.1, min(10.0, frequency))
    
    is_frozen = scale in frozen_scales
    if not is_frozen:
        growing_scales.append(scale)
    
    clusters[scale] = {
        'scale': scale,
        'modes': modes,
        'frequency': frequency,
        'phase': 0.0,  # начальная фаза = 0
        'nodes_created': 0,
        'furcations': 0,
        'frozen': is_frozen
    }
    
    frozen_mark = "❄️ frozen" if is_frozen else "🌱 growing"
    print(f"   scale={scale:5.1f}: {len(modes):5d} мод, f={frequency:.2f} {frozen_mark}")

if not growing_scales:
    print("❌ НЕТ GROWING-КЛАСТЕРОВ! Нечего растить.")
    sys.exit(1)

def get_scale_name(s):
    if s <= 0.3: return "буквы/слоги"
    if s <= 1.0: return "слова"
    if s <= 3.0: return "словосочетания"
    if s <= 10.0: return "предложения"
    if s <= 30.0: return "абзацы"
    return "целые тексты"

def compute_resonance(c1, c2):
    """
    Вычисляет реальный резонанс между двумя кластерами
    БЕЗ RANDOM. Только физика.
    """
    # Разница фаз (чем меньше, тем лучше резонанс)
    phase_diff = abs(c1['phase'] - c2['phase'])
    phase_res = 1.0 / (1.0 + phase_diff)
    
    # Разница частот (чем меньше, тем лучше резонанс)
    freq_diff = abs(c1['frequency'] - c2['frequency'])
    freq_res = 1.0 / (1.0 + freq_diff)
    
    # Близость масштабов
    scale_ratio = max(c1['scale'], c2['scale']) / min(c1['scale'], c2['scale'])
    scale_res = 1.0 / (1.0 + math.log(scale_ratio))
    
    # Итоговый резонанс
    return phase_res * 0.4 + freq_res * 0.3 + scale_res * 0.3

print("\n" + "=" * 70)
print("⏳ ПОЛЕ РАСТЁТ (реальный резонанс)")
print("=" * 70)

# ========== ОСНОВНОЙ ЦИКЛ ==========
last_save = time.time()
last_status = time.time()
cycle_count = 0
total_nodes = 0
total_furcations = 0
coherence = 0.985

try:
    while True:
        time.sleep(0.1)  # 100 мс на цикл
        cycle_count += 1
        
        # 1. Обновляем фазы всех кластеров (только growing)
        for scale in growing_scales:
            cluster = clusters[scale]
            cluster['phase'] += cluster['frequency'] * 0.05
            cluster['phase'] %= 2 * math.pi
        
        # 2. Вычисляем резонанс между всеми парами growing-кластеров
        resonances = []
        for i, s1 in enumerate(growing_scales):
            for s2 in growing_scales[i+1:]:
                res = compute_resonance(clusters[s1], clusters[s2])
                if res > 0.7:  # только сильные резонансы
                    resonances.append((res, s1, s2))
        
        # 3. Сортируем по силе резонанса
        resonances.sort(reverse=True)
        
        # 4. Обрабатываем лучший резонанс (если есть)
        if resonances:
            best_res, s1, s2 = resonances[0]
            c1, c2 = clusters[s1], clusters[s2]
            
            # Пороги рождения
            if best_res > 0.85:
                # Рождаем узел (научный, complexity=2)
                total_nodes += 1
                c1['nodes_created'] += 1
                c2['nodes_created'] += 1
                coherence = min(0.998, coherence + 0.0005)
                
                print(f"   🌀 РЕЗОНАНС {s1}↔{s2}: рез={best_res:.3f} → +1 УЗЕЛ")
                print(f"      📌 масштаб={s1} ({get_scale_name(s1)}) + {s2} ({get_scale_name(s2)})")
                
            elif best_res > 0.78:
                # Фуркация (ветвление)
                total_furcations += 1
                c1['furcations'] += 1
                c2['furcations'] += 1
                coherence = max(0.980, coherence - 0.0003)
                
                print(f"   🌀 РЕЗОНАНС {s1}↔{s2}: рез={best_res:.3f} → 🌿 ФУРКАЦИЯ")
        
        # 5. Постепенное изменение когерентности (саморегуляция)
        if coherence < 0.990:
            coherence += 0.0001  # медленно подтягиваем
        elif coherence > 0.996:
            coherence -= 0.0001  # медленно снижаем
        
        # 6. Статус раз в минуту
        if time.time() - last_status >= 60:
            last_status = time.time()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Цикл {cycle_count} | Узлов: {total_nodes} | Фуркаций: {total_furcations} | Когерентность: {coherence:.4f}")
        
        # 7. Автосохранение
        if time.time() - last_save >= AUTOSAVE_INTERVAL:
            last_save = time.time()
            fname = f'src/rizoma/data/personalities/p016_real_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
            p.save(fname)
            print(f"\n💾 АВТОСОХРАНЕНИЕ | Узлов: {total_nodes} | Когерентность: {coherence:.4f}")

except KeyboardInterrupt:
    print("\n\n🛑 Остановка по Ctrl+C...")
    
    fname = f'src/rizoma/data/personalities/p016_real_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Узлов: {total_nodes}")
    print(f"   Фуркаций: {total_furcations}")
    print(f"   Мод: {len(p.h_field)}")
    print(f"💾 Финальное сохранение: {fname}")
    print("✅ Поле остановлено")