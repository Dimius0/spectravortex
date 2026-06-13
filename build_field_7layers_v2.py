# build_field_7layers_v2.py — СЕМИСЛОЙНОЕ ПОЛЕ (уникальные моды)
import sys, os, json, time, math, hashlib, re
from collections import Counter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY
)

print("=" * 60)
print("🏗️ СЕМИСЛОЙНОЕ ПОЛЕ v2: уникальные моды")
print("=" * 60)

INPUT_FILE = 'dialogue_texts.json'
OUTPUT_JSON = 'src/rizoma/data/personalities/p016_7layers.json'
OUTPUT_DB = 'src/rizoma/data/personalities/text_store_7layers.db'

print(f"\n📂 Загружаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)
print(f"   Сообщений: {len(all_texts)}")

lp = LivingPersonality(id="p016_7layers", name="p016 Семь слоёв", db_path=OUTPUT_DB)

# ═══════════════════════════════════════════════════════
# СТАТИСТИКА (один проход!)
# ═══════════════════════════════════════════════════════

print(f"\n📊 Сбор статистики (буквы, слоги, слова, фразы)...")

word_freq = Counter()
letter_freq = Counter()
syllable_freq = Counter()
pairs = Counter()

def russian_syllables(word):
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

for item in all_texts:
    text = item.get('text', '')
    if not text or len(text) < 10:
        continue
    
    # Буквы
    for ch in text.lower():
        if ch.isalpha():
            letter_freq[ch] += 1
    
    words = [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]
    
    for w in words:
        word_freq[w] += 1
        # Слоги
        for syl in russian_syllables(w):
            if len(syl) >= 1:
                syllable_freq[syl] += 1
    
    for j in range(len(words) - 1):
        pairs[(words[j], words[j+1])] += 1

total_words = sum(word_freq.values())
total_pairs = sum(pairs.values())
max_letter = max(letter_freq.values()) if letter_freq else 1
max_syllable = max(syllable_freq.values()) if syllable_freq else 1
max_word = max(word_freq.values()) if word_freq else 1

print(f"   Букв: {len(letter_freq)}, Слогов: {len(syllable_freq)}, Слов: {len(word_freq)}, Пар: {len(pairs)}")

# Сильные каналы для фраз
strong_pairs_set = set()
for (w1, w2), count in pairs.most_common(100000):
    p_pair = count / total_pairs if total_pairs > 0 else 0
    p_w1 = word_freq[w1] / total_words if total_words > 0 else 0
    p_w2 = word_freq[w2] / total_words if total_words > 0 else 0
    if p_pair > 0 and p_w1 > 0 and p_w2 > 0:
        mi = p_pair / (p_w1 * p_w2)
        if mi > 10:
            strong_pairs_set.add((w1, w2))

print(f"   Сильных каналов: {len(strong_pairs_set)}")

# ═══════════════════════════════════════════════════════
# СОЗДАНИЕ УНИКАЛЬНЫХ МОД ПО СЛОЯМ
# ═══════════════════════════════════════════════════════

total_modes = 0
global_time = 0.0

print(f"\n🔨 Создание мод...")
start = time.time()

# СЛОЙ 1: БУКВЫ (уникальные)
print(f"   Слой 1: буквы...")
for letter, freq in letter_freq.items():
    tau = ord(letter) % 30 + 1
    scale = 0.5
    energy = 0.05 + 0.1 * (freq / max_letter)
    emotion = WaveformEmotion.from_string('neutral', energy)
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L1_{letter}",
        creator="layer1_letters",
        content=letter,
        emotion=emotion,
        phase=(ord(letter) / 255.0) * 2 * math.pi,
    )
    mode.created_at = 0
    lp.add_mode(mode)
    total_modes += 1

print(f"      {total_modes} мод")

# СЛОЙ 2: СЛОГИ (уникальные)
print(f"   Слой 2: слоги...")
layer2_count = 0
for syl, freq in syllable_freq.items():
    if len(syl) >= 1:
        tau = (len(syl) * 3 + sum(ord(c) for c in syl[:3]) % 20) % 30 + 2
        scale = 1.5
        energy = 0.05 + 0.1 * (freq / max_syllable)
        emotion = WaveformEmotion.from_string('neutral', energy)
        mode = SpectralMode(
            tau=tau, amplitude=energy, scale=scale,
            trace_id=f"L2_{syl}",
            creator="layer2_syllables",
            content=syl,
            emotion=emotion,
            phase=hashlib.md5(syl.encode()).digest()[0] / 255.0 * 2 * math.pi,
        )
        mode.created_at = 0
        lp.add_mode(mode)
        total_modes += 1
        layer2_count += 1

print(f"      +{layer2_count} = {total_modes} мод")

# СЛОЙ 3-4: СЛОВА (уникальные)
print(f"   Слой 3-4: слова...")
layer34_count = 0
for word, freq in word_freq.items():
    word_hash = hashlib.md5(word.encode()).digest()
    tau = (word_hash[0] % 50) + 5.0
    freq_ratio = freq / max_word
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
    mode.created_at = 0
    lp.add_mode(mode)
    total_modes += 1
    layer34_count += 1

print(f"      +{layer34_count} = {total_modes} мод")

# СЛОЙ 5-6: ФРАЗЫ (уникальные пары)
print(f"   Слой 5-6: фразы...")
layer56_count = 0
phrase_seen = set()
for (w1, w2) in strong_pairs_set:
    phrase = f"{w1} {w2}"
    if phrase in phrase_seen:
        continue
    phrase_seen.add(phrase)
    
    # MI для этой пары
    count = pairs.get((w1, w2), 1)
    p_pair = count / total_pairs if total_pairs > 0 else 0
    p_w1 = word_freq[w1] / total_words if total_words > 0 else 0
    p_w2 = word_freq[w2] / total_words if total_words > 0 else 0
    mi = p_pair / (p_w1 * p_w2) if (p_pair > 0 and p_w1 > 0 and p_w2 > 0) else 0
    
    tau = (word_freq[w1] + word_freq[w2]) % 40 + 8
    scale = 8.0 + min(24.0, mi / 50)
    energy = min(1.0, mi / 500)
    emotion = WaveformEmotion.from_string('neutral', energy)
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L5_{w1}_{w2}",
        creator="layer5_phrases",
        content=phrase,
        emotion=emotion,
        phase=(hashlib.md5(w1.encode()).digest()[0] / 255.0) * 2 * math.pi,
    )
    mode.created_at = 0
    lp.add_mode(mode)
    total_modes += 1
    layer56_count += 1

print(f"      +{layer56_count} = {total_modes} мод")

# СЛОЙ 7: ТЕКСТЫ (каждое сообщение)
print(f"   Слой 7: тексты...")
layer7_count = 0
for msg_idx, item in enumerate(all_texts):
    text = item.get('text', '')
    if not text or len(text) < 10:
        continue
    
    words = [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]
    if len(words) < 2:
        continue
    
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    tau = (len(text) / 20) % 40 + 32
    scale = 32.0 + min(32.0, len(text) / 100)
    unique_ratio = len(set(words)) / max(len(words), 1)
    energy = 0.3 + 0.3 * unique_ratio
    emotion = WaveformEmotion.from_string('neutral', energy)
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L7_{text_hash}",
        creator="layer7_texts",
        content=text[:300],
        emotion=emotion,
        phase=0.0,
    )
    mode.created_at = msg_idx
    mode.text_id = lp.text_store.store(text[:1000])
    lp.add_mode(mode)
    total_modes += 1
    layer7_count += 1

print(f"      +{layer7_count} = {total_modes} мод")

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
    bar = '█' * min(50, count // 100) if count else ''
    print(f"   Слой {layer_id}: {count:8d} мод, средняя E={avg_e:.4f} {bar}")

print(f"\n🔍 Примеры мод по слоям:")
for layer_id in range(1, 8):
    layer_modes = [m for m in lp.get_all_modes() if m.layer == layer_id][:5]
    if layer_modes:
        words = [m.content[:30] for m in layer_modes]
        print(f"   Слой {layer_id}: {', '.join(words)}")

print(f"\n💾 Сохраняю...")
lp.save(OUTPUT_JSON)
print(f"   JSON: {OUTPUT_JSON}")
print(f"   DB:   {OUTPUT_DB}")
print(f"   Размер JSON: {os.path.getsize(OUTPUT_JSON) / 1024**2:.0f} МБ")
print(f"   Размер DB:   {os.path.getsize(OUTPUT_DB) / 1024**2:.0f} МБ")

print(f"\n✅ Семислойное поле v2 готово!")