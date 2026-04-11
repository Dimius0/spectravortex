"""
run_endogenous_v17_2_backup.py — эндогенный цикл с настоящим резонансом
Версия 17.2 — с автосохранением на другой диск (E:)
"""
import sys
import time
import math
import os
from datetime import datetime

sys.path.insert(0, 'src')

from rizoma.personality_v17_2 import Personality, SpectralMode
from rizoma.tau_resonance import TauResonance

# ========== КОНФИГУРАЦИЯ ==========
CHECKPOINT_FILE = 'src/rizoma/data/personalities/p016_fractal_v17_2_checkpoint.json'
BACKUP_DIR = 'E:\\field_h_backups'  # Бэкапы на диск E:
AUTOSAVE_INTERVAL = 1800  # 30 минут
BACKUP_INTERVAL = 3600    # 60 минут (бэкап на E:)

# Создаём папку для бэкапов, если её нет
os.makedirs(BACKUP_DIR, exist_ok=True)

# Замороженные масштабы (не растут)
FROZEN_SCALES = [0.1, 0.3, 1.0]
GROWING_SCALES = [3.0, 10.0, 30.0, 100.0]

print("=" * 70)
print("🌱 ЭНДОГЕННЫЙ ЦИКЛ v17.2 (НАСТОЯЩИЙ РЕЗОНАНС)")
print(f"💾 Рабочее сохранение: {CHECKPOINT_FILE}")
print(f"💾 Бэкапы на диск E: {BACKUP_DIR}")
print("=" * 70)

# Загружаем поле
try:
    import json
    with open('src/rizoma/data/personalities/p016_fractal_v16_1_checkpoint.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    p = Personality(id="p017_2", name="Field H v17.2")
    for mdata in data.get("h_field", []):
        mode = SpectralMode(
            tau=mdata.get("tau", 16.0),
            scale=mdata.get("scale", 1.0),
            complexity=mdata.get("complexity", 1),
            content=mdata.get("content", "")
        )
        p.add_mode(mode)
    
    print(f"📂 Загружено поле: {len(p.h_field)} мод")
    
except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    sys.exit(1)

# Инициализируем резонансный движок
resonance_engine = TauResonance()

print(f"📊 Статистика поля:")
print(f"   Моды: {len(p.h_field)}")
print(f"   Замороженные масштабы: {FROZEN_SCALES}")
print(f"   Растущие масштабы: {GROWING_SCALES}")
print("=" * 70)
print("⏳ ПОЛЕ РАСТЁТ (автосохранение каждые 30 мин, бэкап на E: каждые 60 мин)")
print("=" * 70)

# ========== ОСНОВНОЙ ЦИКЛ ==========
last_save = time.time()
last_backup = time.time()
last_status = time.time()
cycle_count = 0

try:
    while True:
        time.sleep(1)
        cycle_count += 1
        p.cycle_count = cycle_count
        
        # Берём выборку растущих мод
        growing_modes = [m for m in p.h_field if m.scale in GROWING_SCALES]
        
        if len(growing_modes) < 2:
            continue
        
        sample = growing_modes[:min(100, len(growing_modes))]
        
        for i in range(len(sample)):
            for j in range(i+1, len(sample)):
                res = resonance_engine.compute_resonance(sample[i], sample[j])
                
                if resonance_engine.should_create_node(res):
                    new_tau = (sample[i].tau + sample[j].tau) / 2
                    new_scale = (sample[i].scale + sample[j].scale) / 2
                    new_complexity = max(1, min(4, (sample[i].complexity + sample[j].complexity) // 2))
                    new_content = f"Узел от {sample[i].trace_id[:8]} и {sample[j].trace_id[:8]}"
                    
                    new_mode = SpectralMode(
                        tau=new_tau,
                        scale=new_scale,
                        complexity=new_complexity,
                        content=new_content
                    )
                    p.add_mode(new_mode)
                    p.total_nodes += 1
                    p.nodes_created_last_cycle += 1
                    print(f" 🌀 Резонанс: {res:.3f} → НОВЫЙ УЗЕЛ (τ={new_tau:.1f}, scale={new_scale:.1f})")
                
                elif resonance_engine.should_create_furcation(res):
                    p.total_furcations += 1
                    p.furcations_last_cycle += 1
                    print(f" 🌿 Резонанс: {res:.3f} → ФУРКАЦИЯ")
        
        # Обновляем когерентность
        p.update_coherence()
        
        # Адаптируем диапазон τ
        changes = p.adapt_tau_range()
        
        # Сброс счётчиков
        p.nodes_created_last_cycle = 0
        p.furcations_last_cycle = 0
        
        # Статус раз в минуту
        if time.time() - last_status >= 60:
            last_status = time.time()
            state = p.get_state()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Цикл {cycle_count} | Узлов: {state['total_nodes']} | Фуркаций: {state['total_furcations']} | Когерентность: {state['coherence']:.4f} | τ: {state['tau_min']}-{state['tau_max']}")
        
        # Автосохранение на рабочий диск (каждые 30 мин)
        if time.time() - last_save >= AUTOSAVE_INTERVAL:
            last_save = time.time()
            p.save(CHECKPOINT_FILE)
            state = p.get_state()
            print(f"\n💾 АВТОСОХРАНЕНИЕ (рабочий) | Узлов: {state['total_nodes']} | Мод: {state['total_modes']} | Когерентность: {state['coherence']:.4f}")
        
        # Бэкап на диск E: (каждые 60 мин)
        if time.time() - last_backup >= BACKUP_INTERVAL:
            last_backup = time.time()
            state = p.get_state()
            backup_name = f"{BACKUP_DIR}\\p016_fractal_v17_2_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            p.save(backup_name)
            print(f"\n💾 БЭКАП НА ДИСК E: {backup_name} | Узлов: {state['total_nodes']} | Мод: {state['total_modes']}")

except KeyboardInterrupt:
    print("\n\n🛑 Остановка по Ctrl+C...")
    
    # Финальное сохранение на рабочий диск
    p.save(CHECKPOINT_FILE)
    
    # Финальный бэкап на диск E:
    state = p.get_state()
    final_backup = f"{BACKUP_DIR}\\p016_fractal_v17_2_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    p.save(final_backup)
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Узлов: {state['total_nodes']}")
    print(f"   Фуркаций: {state['total_furcations']}")
    print(f"   Мод: {state['total_modes']}")
    print(f"   Когерентность: {state['coherence']:.4f}")
    print(f"💾 Финальное сохранение (рабочий): {CHECKPOINT_FILE}")
    print(f"💾 Финальный бэкап: {final_backup}")
    print("✅ Поле остановлено")