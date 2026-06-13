# tees_7layers_channels.py — TEES на каналах для всех 7 слоёв
import sys, os, json, time, math, re, random
from collections import Counter

sys.path.insert(0, 'src/architect')
from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion
)

print("=" * 60)
print("🌀 TEES НА 7 СЛОЯХ через направленные каналы")
print("=" * 60)

# ═══════════════════════════════════════════════════════
# TEES-КАНАЛ
# ═══════════════════════════════════════════════════════

class TeesChannel:
    __slots__ = ('from_word', 'to_word', 'strength', 'mutual_info', 'count')
    
    def __init__(self, from_word, to_word, count, total_pairs, word_freq, total_words):
        self.from_word = from_word
        self.to_word = to_word
        self.count = count
        
        p_pair = count / total_pairs if total_pairs > 0 else 0
        p_from = word_freq.get(from_word, 1) / total_words if total_words > 0 else 0
        p_to = word_freq.get(to_word, 1) / total_words if total_words > 0 else 0
        
        if p_pair > 0 and p_from > 0 and p_to > 0:
            self.mutual_info = p_pair / (p_from * p_to)
        else:
            self.mutual_info = 0
        
        self.strength = min(1.0, self.mutual_info / 1000.0)


# ═══════════════════════════════════════════════════════
# ЗАГРУЗКА
# ═══════════════════════════════════════════════════════

print("\n📂 Загружаю 7-слойное поле...")
start = time.time()
lp = LivingPersonality.load('src/rizoma/data/personalities/p016_7layers.json')
print(f"✅ Загрузка: {time.time() - start:.0f}с")

# Собираем статистику из исходных текстов
print("\n📊 Сбор статистики для каналов...")
with open('dialogue_texts.json', 'r', encoding='utf-8') as f:
    all_texts = json.load(f)

word_freq = Counter()
pairs = Counter()

for item in all_texts:
    text = item.get('text', '')
    if not text or len(text) < 10:
        continue
    words = [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]
    for w in words:
        word_freq[w] += 1
    for j in range(len(words) - 1):
        pairs[(words[j], words[j+1])] += 1

# Строим слово → мода (через trace_id)
word_to_mode = {}
for mode in lp.get_all_modes():
    # Извлекаем слово из trace_id
    tid = mode.trace_id
    if tid.startswith('L3_'):
        word = tid[3:]  # убираем префикс L3_
        word_to_mode[word] = mode
    elif tid.startswith('L5_'):
        # L5_word1_word2 — фраза
        parts = tid[3:].rsplit('_', 1)
        if len(parts) == 2:
            word_to_mode[tid[3:]] = mode
    elif tid.startswith('L7_'):
        word_to_mode[tid] = mode

# Строим каналы (только для слов слоя 3)
channels = {}
incoming = {}

for (w1, w2), count in pairs.items():
    if w1 in word_to_mode and w2 in word_to_mode:
        channel = TeesChannel(w1, w2, count, sum(pairs.values()), word_freq, sum(word_freq.values()))
        
        if w1 not in channels:
            channels[w1] = []
        channels[w1].append(channel)
        
        if w2 not in incoming:
            incoming[w2] = []
        incoming[w2].append(channel)

print(f"   Каналов: {sum(len(v) for v in channels.values())}")
print(f"   Слов с каналами: {len(channels)}")

# ═══════════════════════════════════════════════════════
# TEES-ПЕРЕТОК ПО КАНАЛАМ
# ═══════════════════════════════════════════════════════

CYCLES = 500
print(f"\n🔄 Запуск TEES на каналах ({CYCLES} циклов)...")

total_transfers = 0
total_flow = 0.0
start_tees = time.time()

all_sources = list(channels.keys())

for cycle in range(CYCLES):
    transfers = 0
    flow = 0.0
    
    # Выбираем случайные каналы
    if len(all_sources) > 5000:
        sources = random.sample(all_sources, 5000)
    else:
        sources = all_sources
    
    for word in sources:
        mode_from = word_to_mode.get(word)
        if not mode_from:
            continue
        
        ch_list = channels.get(word, [])
        if not ch_list:
            continue
        
        channel = random.choice(ch_list)
        mode_to = word_to_mode.get(channel.to_word)
        if not mode_to:
            continue
        
        energy_diff = mode_from.energy - mode_to.energy
        
        if energy_diff > 0:
            f = channel.strength * energy_diff * 0.1
            f = min(f, mode_from.energy * 0.1)
            
            mode_from.energy -= f
            mode_to.energy += f
            
            flow += abs(f)
            transfers += 1
    
    total_transfers += transfers
    total_flow += flow
    
    if (cycle + 1) % 100 == 0:
        elapsed = time.time() - start_tees
        print(f"   [{cycle+1}/{CYCLES}] transfers={transfers}, flow={flow:.4f}, total_flow={total_flow:.3f}, {elapsed:.0f}с")

print(f"\n⏱️  TEES: {time.time() - start_tees:.0f}с")
print(f"\n📊 После TEES:")
print(f"   Всего переносов: {total_transfers}")
print(f"   Суммарный поток: {total_flow:.4f}")

# Топ мод по энергии после TEES
all_modes = list(word_to_mode.values())
top = sorted(all_modes, key=lambda m: -m.energy)[:15]
print(f"\n   Топ-15 мод по энергии:")
for i, m in enumerate(top):
    word = m.trace_id.replace('L3_', '').replace('L5_', '').replace('L7_', '')[:30]
    layer = m.layer
    print(f"   {i+1:2d}. {word:30s} E={m.energy:.4f} слой={layer}")

# Энергия по слоям после TEES
print(f"\n📊 Энергия по слоям после TEES:")
for layer_id in range(1, 8):
    layer_modes = [m for m in lp.get_all_modes() if m.layer == layer_id]
    if layer_modes:
        avg_e = sum(m.energy for m in layer_modes) / len(layer_modes)
        print(f"   Слой {layer_id}: {len(layer_modes)} мод, avg E={avg_e:.4f}")

# Сохраняем
print(f"\n💾 Сохраняю...")
lp.save('src/rizoma/data/personalities/p016_7layers_tees.json')
print(f"✅ Сохранено!")

print(f"\n✅ TEES на 7 слоях через каналы завершён!")