# build_field_7layers_v4.py — СЕМИСЛОЙНОЕ ПОЛЕ v4: ВММП-контроль + канальный TEES
import sys, os, json, time, math, hashlib, re, random
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY
)

print("=" * 60)
print("🏗️ СЕМИСЛОЙНОЕ ПОЛЕ v4: ВММП-контроль + канальный TEES")
print("=" * 60)

INPUT_FILE = 'dialogue_texts.json'
OUTPUT_JSON = 'src/rizoma/data/personalities/p016_7layers_v4.json'
OUTPUT_DB = 'src/rizoma/data/personalities/text_store_7layers_v4.db'

print(f"\n📂 Загружаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)
print(f"   Сообщений: {len(all_texts)}")

lp = LivingPersonality(id="p016_7layers_v4", name="p016 ВММП-контроль", db_path=OUTPUT_DB)

# ═══════════════════════════════════════════════════════
# ИЕРАРХИЯ СТАБИЛЬНОСТИ (ВММП-принцип)
# ═══════════════════════════════════════════════════════

MUTATION_RATES = {
    1: 0.0, 2: 0.001, 3: 0.01, 4: 0.02, 5: 0.05, 6: 0.1, 7: 0.5,
}

RELAXATION_PERIODS = {
    1: 100, 2: 50, 3: 20, 4: 15, 5: 10, 6: 5, 7: 2,
}

print(f"\n📊 ВММП-контроль активирован:")
print(f"   Мутации слоёв 1-2: ЗАПРЕЩЕНЫ")
print(f"   Связи: только соседние слои + канальный TEES")

# ═══════════════════════════════════════════════════════
# СТАТИСТИКА + ИНДЕКСЫ НАСЛЕДОВАНИЯ
# ═══════════════════════════════════════════════════════

print(f"\n📊 Сбор статистики...")

letter_freq = Counter()
syllable_freq = Counter()
word_freq = Counter()
pairs = Counter()

letter_to_syllables = defaultdict(set)
syllable_to_words = defaultdict(set)
word_to_phrases = defaultdict(set)
syllable_to_letters = defaultdict(set)
word_to_syllables = defaultdict(set)
phrase_to_words = defaultdict(set)
text_to_phrases = defaultdict(set)

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

for msg_idx, item in enumerate(all_texts):
    if msg_idx % 10000 == 0:
        print(f"   {msg_idx}/{len(all_texts)}...")
    
    text = item.get('text', '')
    if not text or len(text) < 10:
        continue
    
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    text_letters = [ch for ch in text.lower() if ch.isalpha()]
    
    for ch in text_letters:
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
        pairs[(words[j], words[j+1])] += 1
        phrase = f"{words[j]} {words[j+1]}"
        phrase_to_words[phrase].add(words[j])
        phrase_to_words[phrase].add(words[j+1])
        word_to_phrases[words[j]].add(phrase)
        word_to_phrases[words[j+1]].add(phrase)
        text_to_phrases[text_hash].add(phrase)

total_words = sum(word_freq.values())
total_pairs = sum(pairs.values())
max_letter = max(letter_freq.values()) if letter_freq else 1
max_syllable = max(syllable_freq.values()) if syllable_freq else 1
max_word = max(word_freq.values()) if word_freq else 1

print(f"   Готово: {len(letter_freq)} букв, {len(syllable_freq)} слогов, {len(word_freq)} слов, {len(pairs)} пар")

# ═══════════════════════════════════════════════════════
# СОЗДАНИЕ МОД С ВММП-КОНТРОЛЕМ
# ═══════════════════════════════════════════════════════

total_modes = 0
mode_index = {}

print(f"\n🔨 Создание мод с ВММП-контролем...")
start = time.time()

# СЛОЙ 1: БУКВЫ
print(f"   Слой 1: буквы (мутации ЗАПРЕЩЕНЫ)...")
for letter, freq in letter_freq.items():
    tau = ord(letter) % 30 + 1
    scale = 0.5
    energy = 0.05 + 0.1 * (freq / max_letter)
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L1_{letter}", creator="layer1", content=letter,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(ord(letter) / 255.0) * 2 * math.pi,
    )
    mode._mutation_allowed = False
    mode._layer = 1
    lp.add_mode(mode)
    mode_index[mode.trace_id] = mode
    total_modes += 1
print(f"      {total_modes} мод")

# СЛОЙ 2: СЛОГИ
print(f"   Слой 2: слоги...")
layer2_count = 0
for syl, freq in syllable_freq.items():
    if len(syl) >= 1:
        tau = (len(syl) * 3 + sum(ord(c) for c in syl[:3]) % 20) % 30 + 2
        scale = 1.5
        base_energy = 0.05 + 0.1 * (freq / max_syllable)
        parent_letters = syllable_to_letters.get(syl, set())
        inherited_energy = 0.0
        if parent_letters:
            parent_energies = [mode_index[f"L1_{ch}"].energy for ch in parent_letters if f"L1_{ch}" in mode_index]
            if parent_energies:
                inherited_energy = sum(parent_energies) / len(parent_energies)
        energy = base_energy * 0.5 + inherited_energy * 0.5
        mode = SpectralMode(
            tau=tau, amplitude=energy, scale=scale,
            trace_id=f"L2_{syl}", creator="layer2", content=syl,
            emotion=WaveformEmotion.from_string('neutral', energy),
            phase=hashlib.md5(syl.encode()).digest()[0] / 255.0 * 2 * math.pi,
        )
        mode.parent_ids = [f"L1_{ch}" for ch in parent_letters]
        mode._mutation_allowed = False
        mode._layer = 2
        mode._relaxation_period = RELAXATION_PERIODS[2]
        lp.add_mode(mode)
        mode_index[mode.trace_id] = mode
        total_modes += 1
        layer2_count += 1
print(f"      +{layer2_count} = {total_modes} мод")

# СЛОЙ 3-4: СЛОВА
print(f"   Слой 3-4: слова...")
layer34_count = 0
for word, freq in word_freq.items():
    word_hash = hashlib.md5(word.encode()).digest()
    tau = (word_hash[0] % 50) + 5.0
    freq_ratio = freq / max_word
    scale = 2.0 + 4.0 * freq_ratio + len(word) / 10
    scale = min(8.0, scale)
    base_energy = 0.1 + 0.9 * freq_ratio
    parent_syllables = word_to_syllables.get(word, set())
    inherited_energy = 0.0
    if parent_syllables:
        parent_energies = [mode_index[f"L2_{syl}"].energy for syl in parent_syllables if f"L2_{syl}" in mode_index]
        if parent_energies:
            inherited_energy = sum(parent_energies) / len(parent_energies)
    energy = base_energy * 0.6 + inherited_energy * 0.4
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L3_{word}", creator="layer3", content=word,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(word_hash[1] / 255.0) * 2 * math.pi,
    )
    mode.parent_ids = [f"L2_{syl}" for syl in parent_syllables]
    mode._mutation_allowed = True
    mode._layer = 3
    mode._relaxation_period = RELAXATION_PERIODS[3]
    lp.add_mode(mode)
    mode_index[mode.trace_id] = mode
    total_modes += 1
    layer34_count += 1
print(f"      +{layer34_count} = {total_modes} мод")

# СЛОЙ 5-6: ФРАЗЫ
print(f"   Слой 5-6: фразы...")
layer56_count = 0
phrase_seen = set()
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
    tau = (word_freq.get(w1, 0) + word_freq.get(w2, 0)) % 40 + 8
    scale = 8.0 + min(24.0, mi / 50)
    base_energy = min(1.0, mi / 500)
    parent_words = {w1, w2}
    parent_energies = [mode_index[f"L3_{pw}"].energy for pw in parent_words if f"L3_{pw}" in mode_index]
    inherited_energy = sum(parent_energies) / len(parent_energies) if parent_energies else base_energy
    energy = base_energy * 0.4 + inherited_energy * 0.6
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L5_{w1}_{w2}", creator="layer5", content=phrase,
        emotion=WaveformEmotion.from_string('neutral', energy),
        phase=(hashlib.md5(w1.encode()).digest()[0] / 255.0) * 2 * math.pi,
    )
    mode.parent_ids = [f"L3_{pw}" for pw in parent_words]
    mode._mutation_allowed = True
    mode._layer = 5
    mode._relaxation_period = RELAXATION_PERIODS[5]
    lp.add_mode(mode)
    mode_index[mode.trace_id] = mode
    total_modes += 1
    layer56_count += 1
print(f"      +{layer56_count} = {total_modes} мод")

# СЛОЙ 7: ТЕКСТЫ
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
    base_energy = 0.3 + 0.3 * unique_ratio
    text_phrases = text_to_phrases.get(text_hash, set())
    inherited_energy = 0.0
    if text_phrases:
        phrase_energies = []
        for ph in text_phrases:
            ph_key = f"L5_{ph.replace(' ', '_')}"
            if ph_key in mode_index:
                phrase_energies.append(mode_index[ph_key].energy)
        if phrase_energies:
            inherited_energy = sum(phrase_energies) / len(phrase_energies)
    energy = base_energy * 0.5 + inherited_energy * 0.5 if text_phrases else base_energy
    mode = SpectralMode(
        tau=tau, amplitude=energy, scale=scale,
        trace_id=f"L7_{text_hash}", creator="layer7", content=text[:300],
        emotion=WaveformEmotion.from_string('neutral', energy), phase=0.0,
    )
    mode.text_id = lp.text_store.store(text[:1000])
    mode._mutation_allowed = True
    mode._layer = 7
    mode._relaxation_period = RELAXATION_PERIODS[7]
    lp.add_mode(mode)
    mode_index[mode.trace_id] = mode
    total_modes += 1
    layer7_count += 1
print(f"      +{layer7_count} = {total_modes} мод")

print(f"\n   Готово: {total_modes} мод за {time.time() - start:.0f}с")

# ═══════════════════════════════════════════════════════
# СТАТИСТИКА ПОСЛЕ СБОРКИ
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
    bar = '█' * min(50, count // 1000) if count else ''
    print(f"   Слой {layer_id}: {count:8d} мод, средняя E={avg_e:.4f} {bar}")

# ═══════════════════════════════════════════════════════
# КАНАЛЬНЫЙ TEES С ВЕРТИКАЛЬНЫМ НАСЛЕДОВАНИЕМ
# ═══════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"🌀 КАНАЛЬНЫЙ TEES с вертикальным наследованием")
print(f"{'='*60}")

class TeesChannel:
    __slots__ = ('from_word', 'to_word', 'strength', 'mutual_info', 'count')
    def __init__(self, from_word, to_word, count, total_pairs, word_freq, total_words):
        self.from_word = from_word
        self.to_word = to_word
        self.count = count
        p_pair = count / total_pairs if total_pairs > 0 else 0
        p_from = word_freq.get(from_word, 1) / total_words if total_words > 0 else 0
        p_to = word_freq.get(to_word, 1) / total_words if total_words > 0 else 0
        self.mutual_info = p_pair / (p_from * p_to) if (p_pair > 0 and p_from > 0 and p_to > 0) else 0
        self.strength = min(1.0, self.mutual_info / 1000.0)

# Строим каналы
channels = defaultdict(list)
incoming = defaultdict(list)

for (w1, w2), count in pairs.items():
    if f"L3_{w1}" in mode_index and f"L3_{w2}" in mode_index:
        channel = TeesChannel(w1, w2, count, total_pairs, word_freq, total_words)
        channels[w1].append(channel)
        incoming[w2].append(channel)

print(f"   Каналов: {sum(len(v) for v in channels.values())}")

CYCLES = 500
print(f"\n🔄 Канальный TEES ({CYCLES} циклов)...")
total_transfers = 0
total_flow = 0.0
start_tees = time.time()
all_sources = list(channels.keys())

for cycle in range(CYCLES):
    transfers = 0
    flow = 0.0
    
    if len(all_sources) > 5000:
        sources = random.sample(all_sources, 5000)
    else:
        sources = all_sources
    
    for word in sources:
        mode_from = mode_index.get(f"L3_{word}")
        if not mode_from:
            continue
        ch_list = channels.get(word, [])
        if not ch_list:
            continue
        channel = random.choice(ch_list)
        mode_to = mode_index.get(f"L3_{channel.to_word}")
        if not mode_to:
            continue
        
        energy_diff = mode_from.energy - mode_to.energy
        if energy_diff > 0:
            f = channel.strength * energy_diff * 0.1
            f = min(f, mode_from.energy * 0.1)
            mode_from.energy -= f
            mode_to.energy += f
            
            # Вертикальное наследование: 1% родителям
            if hasattr(mode_from, 'parent_ids'):
                for pid in mode_from.parent_ids:
                    parent = mode_index.get(pid)
                    if parent:
                        parent.energy += f * 0.01
            if hasattr(mode_to, 'parent_ids'):
                for pid in mode_to.parent_ids:
                    parent = mode_index.get(pid)
                    if parent:
                        parent.energy += f * 0.01
            
            flow += abs(f)
            transfers += 1
    
    total_transfers += transfers
    total_flow += flow
    
    if (cycle + 1) % 100 == 0:
        elapsed = time.time() - start_tees
        print(f"   [{cycle+1}/{CYCLES}] transfers={transfers}, flow={flow:.4f}, total={total_flow:.3f}, {elapsed:.0f}с")

print(f"\n📊 После канального TEES:")
print(f"   Всего переносов: {total_transfers}")
print(f"   Суммарный поток: {total_flow:.4f}")

# Энергия по слоям
layer_energies_after = {i: 0.0 for i in range(1, 8)}
for mode in lp.get_all_modes():
    layer = mode.layer
    layer_energies_after[layer] = layer_energies_after.get(layer, 0.0) + mode.energy

print(f"\n📊 Энергия по слоям после TEES:")
for layer_id in range(1, 8):
    count = layer_counts.get(layer_id, 0)
    avg_e = layer_energies_after[layer_id] / count if count > 0 else 0
    print(f"   Слой {layer_id}: avg E={avg_e:.4f}")

# Топ мод
top = sorted(lp.get_all_modes(), key=lambda m: -m.energy)[:15]
print(f"\n   Топ-15 мод по энергии:")
for i, m in enumerate(top):
    word = m.trace_id.replace('L3_', '').replace('L5_', '').replace('L7_', '')[:35]
    print(f"   {i+1:2d}. {word:35s} E={m.energy:.4f} слой={m.layer}")

# ═══════════════════════════════════════════════════════
# СОХРАНЕНИЕ
# ═══════════════════════════════════════════════════════

print(f"\n💾 Сохраняю...")
lp.save(OUTPUT_JSON)
print(f"   JSON: {OUTPUT_JSON}")
print(f"   DB:   {OUTPUT_DB}")
print(f"   Размер JSON: {os.path.getsize(OUTPUT_JSON) / 1024**2:.0f} МБ")

print(f"\n✅ Семислойное поле v4 с канальным TEES готово!")