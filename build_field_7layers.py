# build_field_7layers.py — СЕМИСЛОЙНОЕ ПОЛЕ: буквы→слоги→слова→фразы→тексты
import sys, os, json, time, math, hashlib, re
from collections import Counter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY
)

print("=" * 60)
print("🏗️ СЕМИСЛОЙНОЕ ПОЛЕ: буквы→слоги→слова→фразы→тексты")
print("=" * 60)

INPUT_FILE = 'dialogue_texts.json'
OUTPUT_JSON = 'src/rizoma/data/personalities/p016_7layers.json'
OUTPUT_DB = 'src/rizoma/data/personalities/text_store_7layers.db'

# Загружаем тексты
print(f"\n📂 Загружаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)
print(f"   Сообщений: {len(all_texts)}")

lp = LivingPersonality(id="p016_7layers", name="p016 Семь слоёв", db_path=OUTPUT_DB)

# ═══════════════════════════════════════════════════════
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════

print(f"\n📊 Сбор статистики...")
word_freq = Counter()
pairs = Counter()  # направленные пары слов

for item in all_texts:
    text = item.get('text', '')
    if not text or len(text) < 10:
        continue
    words = [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]
    for w in words:
        word_freq[w] += 1
    for j in range(len(words) - 1):
        pairs[(words[j], words[j+1])] += 1

total_words = sum(word_freq.values())
total_pairs = sum(pairs.values())
max_freq = max(word_freq.values()) if word_freq else 1

print(f"   Уникальных слов: {len(word_freq)}")
print(f"   Направленных пар: {len(pairs)}")

# ═══════════════════════════════════════════════════════
# ГЕНЕРАТОР МОД ПО СЛОЯМ
# ═══════════════════════════════════════════════════════

def russian_syllables(word):
    """Простое разбиение на слоги (гласная + согласные)."""
    vowels = 'аеёиоуыэюяaeiouy'
    syllables = []
    current = ''
    for ch in word:
        current += ch
        if ch.lower() in vowels:
            syllables.append(current)
            current = ''
    if current:
        if syllables:
            syllables[-1] += current
        else:
            syllables.append(current)
    return syllables if syllables else [word]

total_modes = 0
global_time = 0.0

print(f"\n🔨 Генерация мод по 7 слоям...")
start = time.time()

# Сначала собираем сильные каналы для фраз (слой 5-6)
strong_pairs = []
for (w1, w2), count in pairs.most_common(100000):
    p_pair = count / total_pairs if total_pairs > 0 else 0
    p_w1 = word_freq[w1] / total_words if total_words > 0 else 0
    p_w2 = word_freq[w2] / total_words if total_words > 0 else 0
    if p_pair > 0 and p_w1 > 0 and p_w2 > 0:
        mi = p_pair / (p_w1 * p_w2)
        if mi > 10:  # только сильные каналы
            strong_pairs.append((w1, w2, count, mi))

print(f"   Сильных каналов (MI>10): {len(strong_pairs)}")

# Обрабатываем сообщения
for msg_idx, item in enumerate(all_texts):
    if msg_idx % 5000 == 0:
        elapsed = time.time() - start
        print(f"   {msg_idx}/{len(all_texts)} ({msg_idx*100/len(all_texts):.0f}%) — {total_modes} мод, {elapsed:.0f}с")
    
    text = item.get('text', '')
    if not text or len(text) < 10:
        global_time += 1.0
        continue
    
    words = [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]
    if len(words) < 2:
        global_time += 1.0
        continue
    
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    
    # СЛОЙ 1: БУКВЫ
    all_letters = list(text.lower())
    letter_freq = Counter(all_letters)
    for letter, freq in letter_freq.most_common(50):
        if letter.isalpha():
            tau = ord(letter) % 30 + 1
            scale = 0.5
            energy = 0.05 + 0.05 * (freq / len(all_letters))
            emotion = WaveformEmotion.from_string('neutral', energy)
            mode = SpectralMode(
                tau=tau, amplitude=energy, scale=scale,
                trace_id=f"L1_{letter}_{text_hash}",
                creator="layer1_letters",
                content=letter,
                emotion=emotion,
                phase=(ord(letter) / 255.0) * 2 * math.pi,
            )
            mode.created_at = global_time
            lp.add_mode(mode)
            total_modes += 1
    
    # СЛОЙ 2: СЛОГИ
    for word in words:
        syllables = russian_syllables(word)
        for syl in syllables:
            if len(syl) >= 1:
                tau = (len(syl) * 3 + sum(ord(c) for c in syl[:3]) % 20) % 30 + 2
                scale = 1.5
                energy = 0.05 + 0.1 * (len(syl) / 10)
                emotion = WaveformEmotion.from_string('neutral', energy)
                mode = SpectralMode(
                    tau=tau, amplitude=energy, scale=scale,
                    trace_id=f"L2_{syl}_{text_hash}",
                    creator="layer2_syllables",
                    content=syl,
                    emotion=emotion,
                    phase=hashlib.md5(syl.encode()).digest()[0] / 255.0 * 2 * math.pi,
                )
                mode.created_at = global_time
                lp.add_mode(mode)
                total_modes += 1
    
    # СЛОЙ 3-4: СЛОВА
    for word in words:
        word_hash = hashlib.md5(word.encode()).digest()
        tau = (word_hash[0] % 50) + 5.0
        # scale из частоты и длины слова
        freq_ratio = word_freq.get(word, 1) / max_freq
        scale = 2.0 + 4.0 * freq_ratio + len(word) / 10
        scale = min(8.0, scale)
        energy = 0.1 + 0.9 * freq_ratio
        phase = (word_hash[1] / 255.0) * 2 * math.pi
        emotion = WaveformEmotion.from_string('neutral', energy)
        mode = SpectralMode(
            tau=tau, amplitude=energy, scale=scale,
            trace_id=f"L3_{word}",
            creator="layer3_words",
            content=word,
            emotion=emotion,
            phase=phase,
        )
        mode.created_at = global_time
        lp.add_mode(mode)
        total_modes += 1
    
    # СЛОЙ 5-6: ФРАЗЫ (из сильных каналов)
    for j in range(len(words) - 1):
        w1, w2 = words[j], words[j+1]
        pair_key = (w1, w2)
        # Проверяем, есть ли эта пара в сильных каналах
        found = False
        for pw1, pw2, count, mi in strong_pairs:
            if pw1 == w1 and pw2 == w2:
                phrase = f"{w1} {w2}"
                tau = (word_freq[w1] + word_freq[w2]) % 40 + 8
                scale = 8.0 + min(24.0, mi / 50)
                energy = min(1.0, mi / 500)
                emotion = WaveformEmotion.from_string('neutral', energy)
                mode = SpectralMode(
                    tau=tau, amplitude=energy, scale=scale,
                    trace_id=f"L5_{w1}_{w2}_{text_hash}",
                    creator="layer5_phrases",
                    content=phrase,
                    emotion=emotion,
                    phase=(hashlib.md5(w1.encode()).digest()[0] / 255.0) * 2 * math.pi,
                )
                mode.created_at = global_time + j * 0.01
                lp.add_mode(mode)
                total_modes += 1
                found = True
                break
    
    # СЛОЙ 7: ЦЕЛЫЕ СООБЩЕНИЯ
    tau = (len(text) / 20) % 40 + 32
    scale = 32.0 + min(32.0, len(text) / 100)
    energy = 0.3 + 0.3 * (len(set(words)) / max(len(words), 1))
    emotion = WaveformEmotion.from_string('neutral', energy)
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L7_{text_hash}",
        creator="layer7_texts",
        content=text[:500],
        emotion=emotion,
        phase=0.0,
    )
    mode.created_at = global_time
    mode.text_id = lp.text_store.store(text[:1000])
    lp.add_mode(mode)
    total_modes += 1
    
    global_time += 1.0

print(f"\n   Готово: {total_modes} мод за {time.time() - start:.0f}с")

# ═══════════════════════════════════════════════════════
# СТАТИСТИКА ПО СЛОЯМ
# ═══════════════════════════════════════════════════════

layer_counts = {i: 0 for i in range(1, 8)}
layer_energies = {i: 0.0 for i in range(1, 8)}
for mode in lp.get_all_modes():
    layer = mode.layer
    layer_counts[layer] = layer_counts.get(layer, 0) + 1
    layer_energies[layer] = layer_energies.get(layer, 0.0) + mode.energy

print(f"\n📊 Распределение по слоям:")
for layer_id in range(1, 8):
    count = layer_counts[layer_id]
    avg_e = layer_energies[layer_id] / count if count > 0 else 0
    bar = '█' * min(50, count // 1000) if count else ''
    print(f"   Слой {layer_id}: {count:8d} мод, средняя E={avg_e:.4f} {bar}")

# Примеры мод из каждого слоя
print(f"\n🔍 Примеры мод по слоям:")
for layer_id in range(1, 8):
    layer_modes = [m for m in lp.get_all_modes() if m.layer == layer_id]
    if layer_modes:
        samples = layer_modes[:5]
        words = [m.content[:30] for m in samples]
        print(f"   Слой {layer_id}: {', '.join(words)}")

# Сохраняем
print(f"\n💾 Сохраняю...")
lp.save(OUTPUT_JSON)
print(f"   JSON: {OUTPUT_JSON}")
print(f"   DB:   {OUTPUT_DB}")
print(f"   Размер JSON: {os.path.getsize(OUTPUT_JSON) / 1024**2:.0f} МБ")
print(f"   Размер DB:   {os.path.getsize(OUTPUT_DB) / 1024**2:.0f} МБ")

print(f"\n✅ Семислойное поле готово!")