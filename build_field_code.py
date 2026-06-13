# build_field_code.py — ПРОГРАММНОЕ ПОЛЕ на 7 слоях
import sys, os, json, time, math, hashlib, re, gc, random
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY
)

print("=" * 60)
print("💻 ПРОГРАММНОЕ ПОЛЕ на 7 слоях")
print("=" * 60)

INPUT_FILE = 'code_texts.json'
OUTPUT_JSON = 'src/rizoma/data/personalities/p016_code.json'
OUTPUT_DB = 'src/rizoma/data/personalities/text_store_code.db'

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
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════

print(f"\n📂 Загружаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)
print(f"   Сообщений: {len(all_texts)}")

print(f"\n📊 Сбор статистики...")
letter_freq = Counter()
syllable_freq = Counter()
word_freq = Counter()
pairs = Counter()

syllable_to_letters = defaultdict(set)
word_to_syllables = defaultdict(set)
phrase_to_words = defaultdict(set)
text_to_phrases = defaultdict(set)
phrase_to_texts = defaultdict(set)

text_hashes = []

for msg_idx, item in enumerate(all_texts):
    if msg_idx % 3000 == 0:
        print(f"   {msg_idx}/{len(all_texts)}...")
    
    text = item.get('text', '')
    if not text or len(text) < 10:
        text_hashes.append(None)
        continue
    
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    text_hashes.append(text_hash)
    
    for ch in text.lower():
        if ch.isalpha():
            letter_freq[ch] += 1
    
    # Токенизация кода: учитываем не только слова, но и спецсимволы
    words = re.findall(r'[а-яёa-z0-9_]+|[{}()\[\].,;:=+\-*/<>!&|^~@#\$%]+', text.lower())
    words = [w for w in words if len(w) > 0 and w not in [' ', '\n', '\t', '\r']]
    
    if len(words) < 2:
        continue
    
    for w in words:
        word_freq[w] += 1
        # Слоги — только для буквенных токенов
        if re.match(r'^[а-яёa-z_]+$', w):
            syllables = russian_syllables(w)
            for syl in syllables:
                if len(syl) >= 1:
                    syllable_freq[syl] += 1
                    word_to_syllables[w].add(syl)
                    for ch in syl:
                        if ch.isalpha():
                            syllable_to_letters[syl].add(ch)
    
    for j in range(len(words) - 1):
        w1, w2 = words[j], words[j+1]
        pairs[(w1, w2)] += 1
        phrase = f"{w1} {w2}"
        phrase_to_words[phrase].add(w1)
        phrase_to_words[phrase].add(w2)
        text_to_phrases[text_hash].add(phrase)
        phrase_to_texts[phrase].add(text_hash)

total_words = sum(word_freq.values())
total_pairs = sum(pairs.values())
max_letter = max(letter_freq.values()) if letter_freq else 1
max_syllable = max(syllable_freq.values()) if syllable_freq else 1
max_word = max(word_freq.values()) if word_freq else 1

print(f"   Готово: {len(letter_freq)} букв, {len(syllable_freq)} слогов, {len(word_freq)} токенов, {len(pairs)} пар")

# ═══════════════════════════════════════════════════════
# СОЗДАНИЕ ПОЛЯ
# ═══════════════════════════════════════════════════════

print(f"\n🔨 Создание программного поля...")
lp = LivingPersonality(id="p016_code", name="p016 Программное поле", db_path=OUTPUT_DB)

total_modes = 0
mode_index = {}
start = time.time()

# СЛОЙ 1: буквы
print(f"   Слой 1: буквы...")
for letter, freq in letter_freq.items():
    energy = 0.05 + 0.1 * (freq / max_letter)
    mode = SpectralMode(tau=ord(letter) % 30 + 1, amplitude=energy, scale=0.5,
        trace_id=f"L1_{letter}", creator="code_L1", content=letter,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(ord(letter) / 255.0) * 2 * math.pi)
    mode._mutation_allowed = False
    lp.add_mode(mode)
    mode_index[f"L1_{letter}"] = mode
    total_modes += 1
print(f"      {total_modes} мод")

# СЛОЙ 2: слоги
print(f"   Слой 2: слоги...")
for syl, freq in syllable_freq.items():
    if len(syl) < 1: continue
    parent_letters = syllable_to_letters.get(syl, set())
    inherited_energy = 0.0
    if parent_letters:
        energies = [mode_index[f"L1_{ch}"].energy for ch in parent_letters if f"L1_{ch}" in mode_index]
        if energies: inherited_energy = sum(energies) / len(energies)
    energy = (0.05 + 0.1 * (freq / max_syllable)) * 0.5 + inherited_energy * 0.5
    mode = SpectralMode(tau=(len(syl) * 3 + sum(ord(c) for c in syl[:3]) % 20) % 30 + 2,
        amplitude=energy, scale=1.5, trace_id=f"L2_{syl}", creator="code_L2", content=syl,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=hashlib.md5(syl.encode()).digest()[0] / 255.0 * 2 * math.pi)
    mode.parent_ids = [f"L1_{ch}" for ch in parent_letters]
    mode._mutation_allowed = False
    lp.add_mode(mode)
    mode_index[f"L2_{syl}"] = mode
    total_modes += 1
print(f"      +{len(syllable_freq)} = {total_modes} мод")

del syllable_to_letters; gc.collect()

# СЛОЙ 3-4: токены (слова + операторы)
print(f"   Слой 3-4: токены...")
for word, freq in word_freq.items():
    word_hash = hashlib.md5(word.encode()).digest()
    freq_ratio = freq / max_word
    # Для кода scale чуть выше — операторы важнее
    scale = min(8.0, 2.0 + 6.0 * freq_ratio + len(word) / 8)
    parent_syllables = word_to_syllables.get(word, set())
    inherited_energy = 0.0
    if parent_syllables:
        energies = [mode_index[f"L2_{syl}"].energy for syl in parent_syllables if f"L2_{syl}" in mode_index]
        if energies: inherited_energy = sum(energies) / len(energies)
    energy = (0.1 + 0.9 * freq_ratio) * 0.6 + inherited_energy * 0.4
    mode = SpectralMode(tau=(word_hash[0] % 50) + 5.0, amplitude=energy, scale=scale,
        trace_id=f"L3_{word}", creator="code_L3", content=word,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(word_hash[1] / 255.0) * 2 * math.pi)
    mode.parent_ids = [f"L2_{syl}" for syl in parent_syllables]
    mode._mutation_allowed = False
    lp.add_mode(mode)
    mode_index[f"L3_{word}"] = mode
    total_modes += 1
print(f"      +{len(word_freq)} = {total_modes} мод")

del word_to_syllables, word_freq; gc.collect()

# СЛОЙ 5-6: фразы (пары токенов — код более жёсткий)
print(f"   Слой 5-6: фразы...")
phrase_seen = set()
for (w1, w2), count in pairs.most_common(20000):  # меньше фраз — код компактнее
    phrase = f"{w1} {w2}"
    if phrase in phrase_seen: continue
    phrase_seen.add(phrase)
    p_pair = count / total_pairs if total_pairs > 0 else 0
    p_w1 = 1.0 / total_words if total_words > 0 else 0
    p_w2 = 1.0 / total_words if total_words > 0 else 0
    mi = p_pair / (p_w1 * p_w2) if (p_pair > 0 and p_w1 > 0 and p_w2 > 0) else 0
    if mi < 10: continue  # выше порог — код более структурирован
    parent_energies = [mode_index[f"L3_{pw}"].energy for pw in {w1, w2} if f"L3_{pw}" in mode_index]
    inherited_energy = sum(parent_energies) / len(parent_energies) if parent_energies else 0.1
    energy = min(1.0, mi / 500) * 0.4 + inherited_energy * 0.6
    mode = SpectralMode(tau=(len(w1) + len(w2)) % 40 + 8,
        amplitude=energy, scale=8.0 + min(24.0, mi / 50),
        trace_id=f"L5_{w1}_{w2}", creator="code_L5", content=phrase,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(hashlib.md5(w1.encode()).digest()[0] / 255.0) * 2 * math.pi)
    mode.parent_ids = [f"L3_{pw}" for pw in {w1, w2}]
    mode._mutation_allowed = True
    lp.add_mode(mode)
    mode_index[f"L5_{w1}_{w2}"] = mode
    total_modes += 1
print(f"      +{len(phrase_seen)} = {total_modes} мод")

# СЛОЙ 7: тексты
print(f"   Слой 7: тексты...")
for msg_idx, item in enumerate(all_texts):
    text = item.get('text', '')
    if not text or len(text) < 10: continue
    words = re.findall(r'[а-яёa-z0-9_]+|[{}()\[\].,;:=+\-*/<>!&|^~@#\$%]+', text.lower())
    words = [w for w in words if len(w) > 0]
    if len(words) < 2: continue
    
    text_hash = text_hashes[msg_idx]
    if not text_hash: continue
    
    unique_ratio = len(set(words)) / max(len(words), 1)
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
    
    mode = SpectralMode(tau=(len(text) / 20) % 40 + 32, amplitude=energy,
        scale=32.0 + min(32.0, len(text) / 100),
        trace_id=f"L7_{text_hash}", creator="code_L7", content=text[:300],
        emotion=WaveformEmotion.from_string('neutral', energy), phase=0.0)
    mode.text_id = ''
    mode._mutation_allowed = True
    mode._active_phrases = active_phrases
    lp.add_mode(mode)
    mode_index[f"L7_{text_hash}"] = mode
    total_modes += 1
print(f"      +{len(all_texts)} = {total_modes} мод")

del text_to_phrases, phrase_to_words, pairs, all_texts, text_hashes; gc.collect()

print(f"\n   Готово: {total_modes} мод за {time.time() - start:.0f}с")

# Вместо гигантского text_channels — передача энергии НА ЛЕТУ

# ═══════════════════════════════════════════════════════
# КАНАЛЬНЫЙ TEES (потоковый, без хранения текстовых каналов)
# ═══════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"🌀 КАНАЛЬНЫЙ TEES: программное поле (ПОТОКОВЫЙ)")
print(f"{'='*60}")

# Словесные каналы из фраз
word_channels = defaultdict(list)
for tid, mode in mode_index.items():
    if not tid.startswith('L5_'): continue
    parts = tid[3:].rsplit('_', 1)
    if len(parts) != 2: continue
    w1, w2 = parts
    if f"L3_{w1}" in mode_index and f"L3_{w2}" in mode_index:
        strength = mode.energy
        word_channels[w1].append((w2, strength))
        word_channels[w2].append((w1, strength))

print(f"   Словесных каналов: {sum(len(v) for v in word_channels.values())}")

# Подготавливаем индекс: фраза → тексты (для быстрого поиска)
print(f"   Построение индекса фраза→тексты...")
phrase_to_text_ids = {}
for tid, mode in mode_index.items():
    if not tid.startswith('L5_'): continue
    phrase = mode.content
    if not phrase: continue
    texts_with_phrase = phrase_to_texts.get(phrase, set())
    text_ids = [f"L7_{th}" for th in texts_with_phrase if f"L7_{th}" in mode_index]
    if len(text_ids) >= 2:
        phrase_to_text_ids[phrase] = text_ids

print(f"   Фраз с общими текстами: {len(phrase_to_text_ids)}")

# Запуск TEES — текстовые каналы строятся НА ЛЕТУ
CYCLES = 200
print(f"\n🔄 TEES ({CYCLES} циклов, потоковый)...")
total_transfers = 0
total_flow = 0.0
start_tees = time.time()

all_word_sources = list(word_channels.keys())
phrase_list = list(phrase_to_text_ids.keys())  # список фраз для потоковой передачи

for cycle in range(CYCLES):
    transfers = 0
    flow = 0.0
    
    # TEES между словами
    if all_word_sources:
        sources = random.sample(all_word_sources, min(2000, len(all_word_sources)))
        for word in sources:
            mode_from = mode_index.get(f"L3_{word}")
            if not mode_from: continue
            ch_list = word_channels.get(word, [])
            if not ch_list: continue
            w2, strength = random.choice(ch_list)
            mode_to = mode_index.get(f"L3_{w2}")
            if not mode_to: continue
            energy_diff = mode_from.energy - mode_to.energy
            if energy_diff > 0:
                f = strength * energy_diff * 0.1
                f = min(f, mode_from.energy * 0.1)
                mode_from.energy -= f
                mode_to.energy += f
                flow += abs(f)
                transfers += 1
    
    # TEES между текстами — НА ЛЕТУ через фразы
    # Берём случайную фразу и передаём энергию между её текстами
    if phrase_list:
        sample_phrases = random.sample(phrase_list, min(500, len(phrase_list)))
        for phrase in sample_phrases:
            text_ids = phrase_to_text_ids[phrase]
            if len(text_ids) < 2: continue
            
            # Случайная пара текстов с этой фразой
            i, j = random.sample(range(len(text_ids)), 2)
            tid1, tid2 = text_ids[i], text_ids[j]
            
            mode_from = mode_index.get(tid1)
            mode_to = mode_index.get(tid2)
            if not mode_from or not mode_to: continue
            
            # Сила канала — энергия фразы
            phrase_mode = mode_index.get(f"L5_{phrase.replace(' ', '_')}")
            strength = phrase_mode.energy if phrase_mode else 0.01
            
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
    
    if (cycle + 1) % 50 == 0:
        elapsed = time.time() - start_tees
        print(f"   [{cycle+1}/{CYCLES}] transfers={transfers}, flow={flow:.4f}, total={total_flow:.3f}, {elapsed:.0f}с")

print(f"\n📊 После TEES:")
print(f"   Всего переносов: {total_transfers}")
print(f"   Суммарный поток: {total_flow:.4f}")

# ═══════════════════════════════════════════════════════
# АГРЕССИВНАЯ ОЧИСТКА + СОХРАНЕНИЕ
# ═══════════════════════════════════════════════════════

print(f"\n🧹 Агрессивная очистка перед сохранением...")
del mode_index, word_channels, all_word_sources, phrase_to_texts, phrase_seen, phrase_to_text_ids, phrase_list
for mode in lp.get_all_modes():
    for attr in ['_active_phrases', '_mutation_allowed', '_layer', '_relaxation_period', 'parent_ids']:
        if hasattr(mode, attr):
            try: delattr(mode, attr)
            except: pass
for _ in range(3):
    gc.collect()
    time.sleep(0.1)
print(f"   Очистка завершена")

print(f"\n💾 Сохраняю...")
lp.save(OUTPUT_JSON)
print(f"   JSON: {OUTPUT_JSON}")
print(f"   Размер: {os.path.getsize(OUTPUT_JSON) / 1024**2:.0f} MB")
print(f"\n✅ Программное поле готово!")