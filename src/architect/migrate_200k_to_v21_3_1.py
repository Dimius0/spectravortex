# migrate_200k_to_v21_3_1.py
import sys, os, time, json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

import importlib.util
spec = importlib.util.spec_from_file_location("v21_3_1", os.path.join(CURRENT_DIR, "living_personality_v21_3_1.py"))
v21 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v21)
LivingPersonality = v21.LivingPersonality
SpectralMode = v21.SpectralMode
WaveformEmotion = v21.WaveformEmotion

# Пути
INPUT_JSON = os.path.join(os.path.dirname(CURRENT_DIR), "rizoma", "data", "personalities", "p016_grown_3h.json")
OUTPUT_JSON = os.path.join(os.path.dirname(CURRENT_DIR), "rizoma", "data", "personalities", "p016_v21_3_1.json")
OUTPUT_DB = os.path.join(os.path.dirname(CURRENT_DIR), "rizoma", "data", "personalities", "text_store_p016.db")

print("=" * 60)
print("Миграция p016_grown_3h.json (302 МБ) → v21.3.1 + SQLite")
print("=" * 60)

# Загружаем старый JSON
print(f"\n📂 Загружаю: {INPUT_JSON}")
print(f"   Размер: {os.path.getsize(INPUT_JSON) / 1024**2:.0f} МБ")

start = time.time()
with open(INPUT_JSON, 'r', encoding='utf-8') as f:
    old_data = json.load(f)
print(f"   Загрузка JSON: {time.time() - start:.0f}с")

old_modes = old_data.get('h_field', old_data.get('modes', old_data.get('data', [])))
print(f"   Найдено мод: {len(old_modes)}")

# Создаём новую личность
print(f"\n🌱 Создаю v21.3.1...")
lp = LivingPersonality(id="p016_v21_3_1", name="p016 v21.3.1", db_path=OUTPUT_DB)

# Конвертируем моды
print(f"\n🔄 Конвертация мод...")
converted = 0
batch_start = time.time()

for i, old_mode in enumerate(old_modes):
    if i % 5000 == 0 and i > 0:
        elapsed = time.time() - batch_start
        rate = 5000 / elapsed
        remaining = (len(old_modes) - i) / rate
        print(f"   {i}/{len(old_modes)} ({i*100/len(old_modes):.1f}%) — {rate:.0f} мод/с, осталось {remaining:.0f}с")
        batch_start = time.time()
    
    # Извлекаем данные
    tau = old_mode.get('tau', 16.0)
    amplitude = old_mode.get('amplitude', 0.5)
    content = old_mode.get('content', '')
    trace_id = old_mode.get('trace_id', f"mode_{i:08d}")
    scale = old_mode.get('scale', 10.0)
    phase = old_mode.get('phase', 0.0)
    themes = old_mode.get('themes', [])
    creator = old_mode.get('creator', 'migrated')
    
    # Эмоция по контенту
    emotion_str = 'neutral'
    if content:
        cl = content.lower()
        if any(w in cl for w in ['радост', 'joy', 'отличн', 'прекрасн']):
            emotion_str = 'joy'
        elif any(w in cl for w in ['спокой', 'calm', 'тишин']):
            emotion_str = 'calm'
        elif any(w in cl for w in ['стресс', 'stress', 'напряж']):
            emotion_str = 'stress'
    
    emotion = WaveformEmotion.from_string(emotion_str, amplitude)
    
    # Сохраняем текст в SQLite (с проверкой уникальности)
    text_id = ''
    if content:
        try:
            text_id = lp.text_store.store(content)
        except:
            # Если такой текст уже есть — ищем существующий ID по хешу
            import hashlib
            text_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
            cursor = lp.text_store._conn.execute("SELECT id FROM texts WHERE hash = ?", (text_hash,))
            row = cursor.fetchone()
            if row:
                text_id = row[0]
    
    # Создаём моду
    mode = SpectralMode(
        tau=tau, amplitude=amplitude, content=content,
        text_id=text_id, scale=scale, phase=phase,
        trace_id=trace_id, themes=themes, creator=creator,
        emotion=emotion,
    )
    
    lp.add_mode(mode)
    converted += 1

total_elapsed = time.time() - start
print(f"\n   Готово: {converted} мод за {total_elapsed:.0f}с ({converted/total_elapsed:.0f} мод/с)")

# Статистика
print(f"\n📊 Статистика после миграции:")
print(f"   Мод: {len(lp.get_all_modes())}")
print(f"   Энергия: {lp.energy:.3f}")

layer_counts = {i: 0 for i in range(1, 8)}
for mode in lp.get_all_modes():
    layer_counts[mode.layer] = layer_counts.get(mode.layer, 0) + 1

print(f"   По слоям:")
for layer_id in range(1, 8):
    count = layer_counts[layer_id]
    bar = '█' * min(50, count // 100) if count else ''
    print(f"     Слой {layer_id}: {count:6d} {bar}")

# Сохраняем
print(f"\n💾 Сохраняю...")
save_start = time.time()
lp.save(OUTPUT_JSON)
print(f"   Сохранение: {time.time() - save_start:.0f}с")
print(f"   JSON: {OUTPUT_JSON}")
print(f"   DB:   {OUTPUT_DB}")

size_json = os.path.getsize(OUTPUT_JSON) / 1024**2
size_db = os.path.getsize(OUTPUT_DB) / 1024**2 if os.path.exists(OUTPUT_DB) else 0
print(f"   Размер JSON: {size_json:.0f} МБ")
print(f"   Размер DB:   {size_db:.0f} МБ")

# Проверка загрузки
print(f"\n🔄 Проверка загрузки...")
check_start = time.time()
lp2 = LivingPersonality.load(OUTPUT_JSON)
print(f"   Загрузка: {time.time() - check_start:.0f}с")
print(f"   Мод: {len(lp2.get_all_modes())}")

ts_stats = lp2.text_store.stats()
print(f"   TextStore: {ts_stats['total_texts']} текстов, {ts_stats['total_size_mb']} МБ")

print(f"\n✅ Миграция завершена за {time.time() - start:.0f}с")
print(f"   Исходный: {INPUT_JSON}")
print(f"   Новый JSON: {OUTPUT_JSON}")
print(f"   Новый DB:   {OUTPUT_DB}")