# build_field_v5.py — ПОЛНОЕ ПОЛЕ v5.0: все индексы, все связи, все контенты
import sys, os, json, time, math, hashlib, re, gc, random, sqlite3
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY
)

print("=" * 60)
print("🏗️ ПОЛНОЕ ПОЛЕ v5.0: все индексы, все связи, все контенты")
print("=" * 60)

INPUT_FILE = 'dialogue_texts.json'
OUTPUT_JSON = 'src/rizoma/data/personalities/p016_v5.json'
OUTPUT_DB = 'src/rizoma/data/personalities/text_store_v5.db'

# ═══════════════════════════════════════════════════════
# ВММП-ДЕМОКРАТИЯ
# ═══════════════════════════════════════════════════════

MUTATION_RATES = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.05, 6: 0.1, 7: 0.5}

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

# ═══════════════════════════════════════════════════════
# ШАГ 1: СТАТИСТИКА + ВСЕ ИНДЕКСЫ
# ═══════════════════════════════════════════════════════

print(f"\n📂 Загружаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)
print(f"   Сообщений: {len(all_texts)}")

print(f"\n📊 Сбор полной статистики...")

letter_freq = Counter()
syllable_freq = Counter()
word_freq = Counter()
pairs = Counter()

# Все индексы наследования
letter_to_syllables = defaultdict(set)
syllable_to_words = defaultdict(set)
word_to_phrases = defaultdict(set)
phrase_to_texts = defaultdict(set)
text_to_phrases = defaultdict(set)
syllable_to_letters = defaultdict(set)
word_to_syllables = defaultdict(set)
phrase_to_words = defaultdict(set)

# Хеши текстов для быстрого поиска
text_hashes = []

for msg_idx, item in enumerate(all_texts):
    if msg_idx % 10000 == 0:
        print(f"   {msg_idx}/{len(all_texts)}...")
    
    text = item.get('text', '')
    if not text or len(text) < 10:
        text_hashes.append(None)
        continue
    
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    text_hashes.append(text_hash)
    
    # Буквы
    for ch in text.lower():
        if ch.isalpha():
            letter_freq[ch] += 1
    
    words = [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]
    if len(words) < 2:
        continue
    
    for w in words:
        word_freq[w] += 1
        syllables = russian_syllables(w)
        for syl in syllables:
            if len(syl) >= 1:
                syllable_freq[syl] += 1
                syllable_to_words[syl].add(w)
                word_to_syllables[w].add(syl)
                for ch in syl:
                    if ch.isalpha():
                        letter_to_syllables[ch].add(syl)
                        syllable_to_letters[syl].add(ch)
    
    for j in range(len(words) - 1):
        w1, w2 = words[j], words[j+1]
        pairs[(w1, w2)] += 1
        phrase = f"{w1} {w2}"
        phrase_to_words[phrase].add(w1)
        phrase_to_words[phrase].add(w2)
        word_to_phrases[w1].add(phrase)
        word_to_phrases[w2].add(phrase)
        text_to_phrases[text_hash].add(phrase)
        phrase_to_texts[phrase].add(text_hash)

total_words = sum(word_freq.values())
total_pairs = sum(pairs.values())
max_letter = max(letter_freq.values()) if letter_freq else 1
max_syllable = max(syllable_freq.values()) if syllable_freq else 1
max_word = max(word_freq.values()) if word_freq else 1

print(f"   Готово: {len(letter_freq)} букв, {len(syllable_freq)} слогов, {len(word_freq)} слов, {len(pairs)} пар")
print(f"   Индексы: {len(text_to_phrases)} текстов с фразами, {len(phrase_to_texts)} фраз в текстах")

# ═══════════════════════════════════════════════════════
# ШАГ 2: СОЗДАНИЕ ПОЛЯ
# ═══════════════════════════════════════════════════════

print(f"\n🔨 Создание полного поля...")
lp = LivingPersonality(id="p016_v5", name="p016 Полное поле v5.0", db_path=OUTPUT_DB)

total_modes = 0
mode_index = {}
start = time.time()

# СЛОЙ 1: БУКВЫ
print(f"   Слой 1: буквы...")
for letter, freq in letter_freq.items():
    energy = 0.05 + 0.1 * (freq / max_letter)
    mode = SpectralMode(
        tau=ord(letter) % 30 + 1, amplitude=energy, scale=0.5,
        trace_id=f"L1_{letter}", creator="layer1", content=letter,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(ord(letter) / 255.0) * 2 * math.pi,
    )
    mode._mutation_allowed = False
    lp.add_mode(mode)
    mode_index[f"L1_{letter}"] = mode
    total_modes += 1
print(f"      {total_modes} мод")

# СЛОЙ 2: СЛОГИ
print(f"   Слой 2: слоги...")
for syl, freq in syllable_freq.items():
    if len(syl) < 1:
        continue
    parent_letters = syllable_to_letters.get(syl, set())
    inherited_energy = 0.0
    if parent_letters:
        energies = [mode_index[f"L1_{ch}"].energy for ch in parent_letters if f"L1_{ch}" in mode_index]
        if energies:
            inherited_energy = sum(energies) / len(energies)
    energy = (0.05 + 0.1 * (freq / max_syllable)) * 0.5 + inherited_energy * 0.5
    mode = SpectralMode(
        tau=(len(syl) * 3 + sum(ord(c) for c in syl[:3]) % 20) % 30 + 2,
        amplitude=energy, scale=1.5,
        trace_id=f"L2_{syl}", creator="layer2", content=syl,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=hashlib.md5(syl.encode()).digest()[0] / 255.0 * 2 * math.pi,
    )
    mode.parent_ids = [f"L1_{ch}" for ch in parent_letters]
    mode._mutation_allowed = False
    lp.add_mode(mode)
    mode_index[f"L2_{syl}"] = mode
    total_modes += 1
print(f"      +{len(syllable_freq)} = {total_modes} мод")

# Очистка
del syllable_to_letters, letter_to_syllables
gc.collect()

# СЛОЙ 3-4: СЛОВА
print(f"   Слой 3-4: слова...")
for word, freq in word_freq.items():
    word_hash = hashlib.md5(word.encode()).digest()
    freq_ratio = freq / max_word
    scale = min(8.0, 2.0 + 4.0 * freq_ratio + len(word) / 10)
    parent_syllables = word_to_syllables.get(word, set())
    inherited_energy = 0.0
    if parent_syllables:
        energies = [mode_index[f"L2_{syl}"].energy for syl in parent_syllables if f"L2_{syl}" in mode_index]
        if energies:
            inherited_energy = sum(energies) / len(energies)
    energy = (0.1 + 0.9 * freq_ratio) * 0.6 + inherited_energy * 0.4
    mode = SpectralMode(
        tau=(word_hash[0] % 50) + 5.0, amplitude=energy, scale=scale,
        trace_id=f"L3_{word}", creator="layer3", content=word,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(word_hash[1] / 255.0) * 2 * math.pi,
    )
    mode.parent_ids = [f"L2_{syl}" for syl in parent_syllables]
    mode._mutation_allowed = False
    lp.add_mode(mode)
    mode_index[f"L3_{word}"] = mode
    total_modes += 1
print(f"      +{len(word_freq)} = {total_modes} мод")

del word_to_syllables
gc.collect()

# СЛОЙ 5-6: ФРАЗЫ (с сохранением phrase_to_texts!)
print(f"   Слой 5-6: фразы...")
phrase_seen = set()
strong_phrases = {}
for (w1, w2), count in pairs.most_common(100000):
    phrase = f"{w1} {w2}"
    if phrase in phrase_seen:
        continue
    p_pair = count / total_pairs if total_pairs > 0 else 0
    p_w1 = word_freq[w1] / total_words if total_words > 0 else 0
    p_w2 = word_freq[w2] / total_words if total_words > 0 else 0
    mi = p_pair / (p_w1 * p_w2) if (p_pair > 0 and p_w1 > 0 and p_w2 > 0) else 0
    if mi < 10:
        continue
    phrase_seen.add(phrase)
    strong_phrases[phrase] = mi
    
    parent_energies = [mode_index[f"L3_{pw}"].energy for pw in {w1, w2} if f"L3_{pw}" in mode_index]
    inherited_energy = sum(parent_energies) / len(parent_energies) if parent_energies else 0.1
    energy = min(1.0, mi / 500) * 0.4 + inherited_energy * 0.6
    
    mode = SpectralMode(
        tau=(word_freq.get(w1, 0) + word_freq.get(w2, 0)) % 40 + 8,
        amplitude=energy, scale=8.0 + min(24.0, mi / 50),
        trace_id=f"L5_{w1}_{w2}", creator="layer5", content=phrase,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(hashlib.md5(w1.encode()).digest()[0] / 255.0) * 2 * math.pi,
    )
    mode.parent_ids = [f"L3_{pw}" for pw in {w1, w2}]
    mode._mutation_allowed = True
    lp.add_mode(mode)
    mode_index[f"L5_{w1}_{w2}"] = mode
    total_modes += 1
print(f"      +{len(phrase_seen)} = {total_modes} мод")

# СЛОЙ 7: ТЕКСТЫ (с контентом и связями!)
print(f"   Слой 7: тексты...")
layer7_count = 0
text_modes = []

for msg_idx, item in enumerate(all_texts):
    text = item.get('text', '')
    if not text or len(text) < 10:
        continue
    words = [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]
    if len(words) < 2:
        continue
    
    text_hash = text_hashes[msg_idx]
    if not text_hash:
        continue
    
    unique_ratio = len(set(words)) / max(len(words), 1)
    
    # Наследование от фраз: средняя энергия фраз в этом тексте
    text_phrases = text_to_phrases.get(text_hash, set())
    inherited_energy = 0.0
    active_phrases = []
    if text_phrases:
        phrase_energies = []
        for ph in text_phrases:
            ph_key = f"L5_{ph.replace(' ', '_')}"
            if ph_key in mode_index:
                phrase_energies.append(mode_index[ph_key].energy)
                active_phrases.append(ph_key)
        if phrase_energies:
            inherited_energy = sum(phrase_energies) / len(phrase_energies)
    
    energy = (0.3 + 0.3 * unique_ratio) * 0.5 + inherited_energy * 0.5 if text_phrases else 0.3
    
    mode = SpectralMode(
        tau=(len(text) / 20) % 40 + 32, amplitude=energy,
        scale=32.0 + min(32.0, len(text) / 100),
        trace_id=f"L7_{text_hash}", creator="layer7", content=text[:500],
        emotion=WaveformEmotion.from_string('neutral', energy), phase=0.0,
    )
    mode.text_id = ''
    mode._mutation_allowed = True
    mode._active_phrases = active_phrases  # СВЯЗИ С ФРАЗАМИ!
    lp.add_mode(mode)
    mode_index[f"L7_{text_hash}"] = mode
    text_modes.append(mode)
    total_modes += 1
    layer7_count += 1
print(f"      +{layer7_count} = {total_modes} мод")

print(f"\n   Готово: {total_modes} мод за {time.time() - start:.0f}с")

# ═══════════════════════════════════════════════════════
# ШАГ 3: СТАТИСТИКА ДО TEES
# ═══════════════════════════════════════════════════════

layer_counts = {i: 0 for i in range(1, 8)}
layer_energies = {i: 0.0 for i in range(1, 8)}
for mode in lp.get_all_modes():
    layer = mode.layer
    layer_counts[layer] = layer_counts.get(layer, 0) + 1
    layer_energies[layer] = layer_energies.get(layer, 0.0) + mode.energy

print(f"\n📊 Распределение по слоям (до TEES):")
for layer_id in range(1, 8):
    count = layer_counts[layer_id]
    avg_e = layer_energies[layer_id] / count if count > 0 else 0
    print(f"   Слой {layer_id}: {count:8d} мод, средняя E={avg_e:.4f}")

# ═══════════════════════════════════════════════════════
# ШАГ 4: КАНАЛЬНЫЙ TEES (слова + тексты)
# ═══════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"🌀 КАНАЛЬНЫЙ TEES: слова + тексты через фразы")
print(f"{'='*60}")

# Каналы между словами (из фраз)
word_channels = defaultdict(list)
for (w1, w2), count in pairs.most_common(200000):
    if f"L3_{w1}" in mode_index and f"L3_{w2}" in mode_index:
        p_pair = count / total_pairs if total_pairs > 0 else 0
        p_w1 = word_freq[w1] / total_words if total_words > 0 else 0
        p_w2 = word_freq[w2] / total_words if total_words > 0 else 0
        mi = p_pair / (p_w1 * p_w2) if (p_pair > 0 and p_w1 > 0 and p_w2 > 0) else 0
        strength = min(1.0, mi / 1000.0)
        word_channels[w1].append((w2, strength))

# Каналы между текстами (через общие фразы)
text_channels = defaultdict(list)
text_ids = list(mode_index.keys())
text_ids = [tid for tid in text_ids if tid.startswith('L7_')]
print(f"   Построение каналов между {len(text_ids)} текстами...")

for i, tid1 in enumerate(text_ids):
    if i % 5000 == 0:
        print(f"   {i}/{len(text_ids)}...")
    mode1 = mode_index.get(tid1)
    if not mode1 or not hasattr(mode1, '_active_phrases'):
        continue
    phrases1 = set(mode1._active_phrases)
    if not phrases1:
        continue
    
    for tid2 in text_ids[i+1:]:
        mode2 = mode_index.get(tid2)
        if not mode2 or not hasattr(mode2, '_active_phrases'):
            continue
        phrases2 = set(mode2._active_phrases)
        common = phrases1 & phrases2
        if common:
            # Сила канала = количество общих фраз × средняя энергия этих фраз
            common_energy = sum(mode_index[ph].energy for ph in common if ph in mode_index) / max(len(common), 1)
            strength = min(1.0, len(common) * common_energy / 100)
            text_channels[tid1].append((tid2, strength))
            text_channels[tid2].append((tid1, strength))

print(f"   Текстовых каналов: {sum(len(v) for v in text_channels.values())}")

# Запуск TEES
CYCLES = 300
print(f"\n🔄 Канальный TEES ({CYCLES} циклов)...")
total_transfers = 0
total_flow = 0.0
start_tees = time.time()

all_word_sources = list(word_channels.keys())
all_text_sources = list(text_channels.keys())

for cycle in range(CYCLES):
    transfers = 0
    flow = 0.0
    
    # TEES между словами
    if all_word_sources:
        sources = random.sample(all_word_sources, min(3000, len(all_word_sources)))
        for word in sources:
            mode_from = mode_index.get(f"L3_{word}")
            if not mode_from:
                continue
            ch_list = word_channels.get(word, [])
            if not ch_list:
                continue
            w2, strength = random.choice(ch_list)
            mode_to = mode_index.get(f"L3_{w2}")
            if not mode_to:
                continue
            
            energy_diff = mode_from.energy - mode_to.energy
            if energy_diff > 0:
                f = strength * energy_diff * 0.1
                f = min(f, mode_from.energy * 0.1)
                mode_from.energy -= f
                mode_to.energy += f
                flow += abs(f)
                transfers += 1
    
    # TEES между текстами (через общие фразы)
    if all_text_sources:
        sources = random.sample(all_text_sources, min(1000, len(all_text_sources)))
        for tid in sources:
            mode_from = mode_index.get(tid)
            if not mode_from:
                continue
            ch_list = text_channels.get(tid, [])
            if not ch_list:
                continue
            tid2, strength = random.choice(ch_list)
            mode_to = mode_index.get(tid2)
            if not mode_to:
                continue
            
            energy_diff = mode_from.energy - mode_to.energy
            if energy_diff > 0:
                f = strength * energy_diff * 0.1
                f = min(f, mode_from.energy * 0.1)
                mode_from.energy -= f
                mode_to.energy += f
                flow += abs(f)
                transfers += 1
    
    total_transfers += transfers
    total_flow += flow
    
    if (cycle + 1) % 60 == 0:
        elapsed = time.time() - start_tees
        print(f"   [{cycle+1}/{CYCLES}] transfers={transfers}, flow={flow:.4f}, total={total_flow:.3f}, {elapsed:.0f}с")

print(f"\n📊 После TEES:")
print(f"   Всего переносов: {total_transfers}")
print(f"   Суммарный поток: {total_flow:.4f}")

# Энергия по слоям
for layer_id in range(1, 8):
    layer_modes = [m for m in lp.get_all_modes() if m.layer == layer_id]
    if layer_modes:
        avg_e = sum(m.energy for m in layer_modes) / len(layer_modes)
        print(f"   Слой {layer_id}: avg E={avg_e:.4f}")

# Топ текстов
top_texts = sorted([m for m in lp.get_all_modes() if m.layer == 7], key=lambda m: -m.energy)[:10]
print(f"\n   Топ-10 текстов по энергии:")
for i, m in enumerate(top_texts):
    content = m.content[:100] if m.content else '(пусто)'
    print(f"   {i+1:2d}. E={m.energy:.4f} | {content}...")

# Топ слов
top_words = sorted([m for m in lp.get_all_modes() if m.layer == 3], key=lambda m: -m.energy)[:10]
print(f"\n   Топ-10 слов по энергии:")
for i, m in enumerate(top_words):
    print(f"   {i+1:2d}. {m.content:20s} E={m.energy:.4f}")

# ═══════════════════════════════════════════════════════
# ШАГ 5: СОХРАНЕНИЕ
# ═══════════════════════════════════════════════════════

print(f"\n💾 Сохраняю...")
lp.save(OUTPUT_JSON)
print(f"   JSON: {OUTPUT_JSON}")
print(f"   DB:   {OUTPUT_DB}")
print(f"   Размер JSON: {os.path.getsize(OUTPUT_JSON) / 1024**2:.0f} MB")

print(f"\n✅ Полное поле v5.0 готово!")
print(f"   Связи: буквы→слоги→слова→фразы→тексты")
print(f"   Каналы: слова↔слова, тексты↔тексты (через общие фразы)")