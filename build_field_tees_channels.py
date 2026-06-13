# build_field_tees_channels.py — ПОЛЕ НА TEES-КАНАЛАХ (направленные связи)
import sys, os, json, time, math, hashlib
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧬 ПОЛЕ НА TEES-КАНАЛАХ: направленные связи как механизм")
print("=" * 60)

INPUT_FILE = 'dialogue_texts.json'
OUTPUT_JSON = 'src/rizoma/data/personalities/p016_tees_channels.json'
OUTPUT_DB = 'src/rizoma/data/personalities/text_store_tees_channels.db'

# Загружаем тексты
print(f"\n📂 Загружаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)

texts = all_texts  # все 43K
print(f"   Сообщений: {len(texts)}")

# Создаём поле
lp = LivingPersonality(id="p016_tees_channels", name="p016 TEES-каналы", db_path=OUTPUT_DB)

# ═══════════════════════════════════════════════════════
# СТРУКТУРА: МОДЫ + TEES-КАНАЛЫ
# ═══════════════════════════════════════════════════════

import re

def tokenize(text):
    return [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]

# Статистика
word_freq = Counter()
pairs = Counter()  # (A, B) → count (A слева от B)
word_to_mode = {}
total_modes = 0
global_time = 0.0

print(f"\n🔨 Сбор статистики...")
start = time.time()

for i, item in enumerate(texts):
    if i % 5000 == 0:
        print(f"   {i}/{len(texts)} ({i*100/len(texts):.0f}%)")
    
    text = item.get('text', '')
    if not text or len(text) < 10:
        global_time += 1.0
        continue
    
    words = tokenize(text)
    if len(words) < 2:
        global_time += 1.0
        continue
    
    for word in words:
        word_freq[word] += 1
    
    for j in range(len(words) - 1):
        pairs[(words[j], words[j+1])] += 1
    
    global_time += 1.0

print(f"   Готово: {len(word_freq)} уникальных слов, {len(pairs)} направленных пар за {time.time() - start:.0f}с")

# ═══════════════════════════════════════════════════════
# СОЗДАНИЕ МОД С ЭНЕРГИЕЙ ИЗ СТАТИСТИКИ
# ═══════════════════════════════════════════════════════

print(f"\n🔨 Создание мод с честной энергией из TEES-каналов...")
start = time.time()

# Энергия моды = нормированная частота слова
max_freq = max(word_freq.values()) if word_freq else 1

for word, freq in word_freq.items():
    # tau — из хеша слова (стабильно)
    word_hash = hashlib.md5(word.encode()).digest()
    tau = (word_hash[0] % 50) + 5.0
    
    # Энергия — из частоты (честно!)
    energy = 0.1 + 0.9 * (freq / max_freq)
    
    # Фаза — из хеша (уникальна для слова)
    phase = (word_hash[1] / 255.0) * 2 * math.pi
    
    # Scale — из частоты: частые слова — выше слой
    scale = 2.0 + 10.0 * (freq / max_freq)
    
    emotion = WaveformEmotion.from_string('neutral', energy)
    
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"word_{word}",
        creator="tees_channel_field",
        content=word,
        emotion=emotion,
        phase=phase,
    )
    mode.created_at = global_time
    lp.add_mode(mode)
    word_to_mode[word] = mode
    total_modes += 1

print(f"   Создано мод: {total_modes} за {time.time() - start:.0f}с")

# ═══════════════════════════════════════════════════════
# АНАЛИЗ TEES-КАНАЛОВ (КТО С КЕМ СВЯЗАН)
# ═══════════════════════════════════════════════════════

print(f"\n🔍 Анализ TEES-каналов:")

# Для каждого слова считаем входящие и исходящие связи
incoming = Counter()
outgoing = Counter()

for (w1, w2), count in pairs.items():
    outgoing[w1] += count
    incoming[w2] += count

# Определяем роли по соотношению входящих/исходящих
print(f"\n   Топ-20 слов по роли в TEES-каналах:")
print(f"   {'Слово':20s} {'Частота':8s} {'Исх':8s} {'Вх':8s} {'Роль':25s} {'Энергия':8s}")
print(f"   {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*25} {'-'*8}")

for word, freq in word_freq.most_common(30):
    out = outgoing.get(word, 0)
    inn = incoming.get(word, 0)
    total = out + inn
    
    if total == 0:
        role = "изолированное"
        ratio = 0.5
    else:
        ratio = out / total if total > 0 else 0.5
        
        if ratio > 0.7:
            role = "МОДИФИКАТОР (прил?)"
        elif ratio < 0.3:
            role = "ОБЪЕКТ (сущ?)"
        elif total > 50000:
            role = "ОПЕРАТОР (глагол?)"
        else:
            role = "смешанное"
    
    energy = word_to_mode[word].energy if word in word_to_mode else 0
    print(f"   {word:20s} {freq:8d} {out:8d} {inn:8d} {role:25s} {energy:8.4f}")

# ═══════════════════════════════════════════════════════
# ТЕСТ: ПЕРЕТОК ЭНЕРГИИ ПО TEES-КАНАЛАМ
# ═══════════════════════════════════════════════════════

print(f"\n🔄 Тест: переток энергии по TEES-каналам...")

# Берём топ-10 пар с самым сильным каналом
top_channels = pairs.most_common(10)

print(f"\n   Топ-10 TEES-каналов (поток энергии):")
for (w1, w2), count in top_channels:
    mode1 = word_to_mode.get(w1)
    mode2 = word_to_mode.get(w2)
    if mode1 and mode2:
        # Сила канала = частота пары / (частота_w1 * частота_w2) — взаимная информация
        p_pair = count / sum(pairs.values()) if sum(pairs.values()) > 0 else 0
        p_w1 = word_freq[w1] / sum(word_freq.values()) if sum(word_freq.values()) > 0 else 0
        p_w2 = word_freq[w2] / sum(word_freq.values()) if sum(word_freq.values()) > 0 else 0
        
        if p_pair > 0 and p_w1 > 0 and p_w2 > 0:
            mi = p_pair / (p_w1 * p_w2)  # взаимная информация
        else:
            mi = 0
        
        E1 = mode1.energy
        E2 = mode2.energy
        flow = mi * (E1 - E2) * 0.01  # модельный переток
        
        print(f"   {w1:15s} → {w2:15s}: канал={count:6d}, MI={mi:.2f}, "
              f"E1={E1:.3f}, E2={E2:.3f}, поток={flow:.4f}")

# Распределение по слоям
layer_counts = {i: 0 for i in range(1, 8)}
for mode in lp.get_all_modes():
    layer_counts[mode.layer] = layer_counts.get(mode.layer, 0) + 1

print(f"\n📊 Распределение по слоям:")
for layer_id in range(1, 8):
    count = layer_counts[layer_id]
    bar = '█' * min(50, count // 100) if count else ''
    print(f"   Слой {layer_id}: {count:6d} {bar}")

# Сохраняем
print(f"\n💾 Сохраняю...")
lp.save(OUTPUT_JSON)
print(f"   JSON: {OUTPUT_JSON}")
print(f"   DB:   {OUTPUT_DB}")
print(f"   Размер JSON: {os.path.getsize(OUTPUT_JSON) / 1024**2:.0f} МБ")
print(f"   Размер DB:   {os.path.getsize(OUTPUT_DB) / 1024**2:.0f} МБ")

print(f"\n✅ Поле на TEES-каналах собрано!")
print(f"   Моды = слова с энергией из частоты")
print(f"   TEES-каналы = направленные пары (уже работают)")
print(f"   Роли выведены из соотношения входящих/исходящих связей")