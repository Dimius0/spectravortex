# tees_channel_live_v2.py — ЖИВОЕ ПОЛЕ С ФУРКАЦИЯМИ
import sys, os, json, time, math, re, hashlib
from collections import Counter
import random

sys.path.insert(0, 'src/architect')
from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, MIN_ENERGY
)

print("=" * 60)
print("🧪 ЖИВОЕ ПОЛЕ С ФУРКАЦИЯМИ (рождение новых смыслов)")
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
# ЖИВОЕ ПОЛЕ С ФУРКАЦИЯМИ
# ═══════════════════════════════════════════════════════

class LiveFieldFurcations:
    """
    Живое поле на TEES-каналах с рождением новых мод.
    Фуркация = новый канал из сильного потока энергии.
    """
    
    def __init__(self, word_to_mode, pairs, word_freq, lp):
        self.word_to_mode = word_to_mode
        self.lp = lp  # ссылка на LivingPersonality для add_mode()
        self.total_words = sum(word_freq.values())
        self.total_pairs = sum(pairs.values())
        self.word_freq = word_freq
        
        # Строим каналы
        self.channels = {}
        self.incoming = {}
        
        for (w1, w2), count in pairs.items():
            if w1 in word_to_mode and w2 in word_to_mode:
                channel = TeesChannel(w1, w2, count, self.total_pairs, word_freq, self.total_words)
                
                if w1 not in self.channels:
                    self.channels[w1] = []
                self.channels[w1].append(channel)
                
                if w2 not in self.incoming:
                    self.incoming[w2] = []
                self.incoming[w2].append(channel)
        
        self.energy = 1.0
        self.transfers = 0
        self.total_flow = 0.0
        self.furcations = 0
        
        # Порог фуркации: эмерджентный (средний поток по каналам)
        self.furcation_threshold = 0.0
        
        print(f"   TEES-каналов: {sum(len(v) for v in self.channels.values())}")
        print(f"   Мод с каналами: {len(self.channels)}")
    
    def step(self, dt: float = 0.1, max_channels: int = 5000) -> dict:
        """Один шаг: переток энергии + фуркации."""
        transfers = 0
        total_flow = 0.0
        new_furcations = 0
        
        all_sources = list(self.channels.keys())
        if len(all_sources) > max_channels:
            sources = random.sample(all_sources, max_channels)
        else:
            sources = all_sources
        
        flows_this_step = []
        
        for word in sources:
            mode_from = self.word_to_mode.get(word)
            if not mode_from:
                continue
            
            channels = self.channels.get(word, [])
            if not channels:
                continue
            
            channel = random.choice(channels)
            mode_to = self.word_to_mode.get(channel.to_word)
            if not mode_to:
                continue
            
            energy_diff = mode_from.energy - mode_to.energy
            
            if energy_diff > 0:
                flow = channel.strength * energy_diff * dt
                flow = min(flow, mode_from.energy * 0.1)
                
                mode_from.energy -= flow
                mode_to.energy += flow
                
                total_flow += abs(flow)
                transfers += 1
                flows_this_step.append((word, channel.to_word, flow, channel))
        
        # Обновляем порог фуркации (средний поток)
        if flows_this_step:
            avg_flow = sum(f[2] for f in flows_this_step) / len(flows_this_step)
            self.furcation_threshold = avg_flow * 3  # в 3 раза выше среднего
        else:
            self.furcation_threshold = 0.001
        
        # Фуркации: рождение новых мод из сильных потоков
        for from_word, to_word, flow, channel in flows_this_step:
            if flow > self.furcation_threshold and flow > 0.001:
                new_word = f"{from_word}_{to_word}"
                
                if new_word not in self.word_to_mode:
                    # Создаём новую моду-посредник
                    energy_new = flow * 0.5
                    
                    new_mode = SpectralMode(
                        tau=(self.word_to_mode[from_word].tau + self.word_to_mode[to_word].tau) / 2,
                        amplitude=energy_new,
                        scale=min(30, self.word_to_mode[from_word].scale + 1),
                        trace_id=f"furcated_{new_word}",
                        creator="furcation",
                        content='',
                        emotion=WaveformEmotion(amplitude=energy_new, base_emotion='neutral'),
                        phase=(self.word_to_mode[from_word].phase + self.word_to_mode[to_word].phase) / 2,
                    )
                    
                    self.lp.add_mode(new_mode)
                    self.word_to_mode[new_word] = new_mode
                    
                    # Создаём новый канал: from → new
                    new_channel = TeesChannel(from_word, new_word, 1, self.total_pairs, 
                                             self.word_freq, self.total_words)
                    new_channel.strength = channel.strength * 0.8
                    
                    if from_word not in self.channels:
                        self.channels[from_word] = []
                    self.channels[from_word].append(new_channel)
                    
                    if new_word not in self.incoming:
                        self.incoming[new_word] = []
                    self.incoming[new_word].append(new_channel)
                    
                    new_furcations += 1
                    
                    if new_furcations <= 3:  # покажем первые три
                        print(f"   🌱 Фуркация: {from_word} + {to_word} → {new_word} (E={energy_new:.4f})")
        
        self.transfers += transfers
        self.total_flow += total_flow
        self.furcations += new_furcations
        
        self.energy = min(1.0, self.energy + 0.01 * dt)
        
        return {
            'transfers': transfers,
            'total_flow': total_flow,
            'energy': self.energy,
            'furcations': new_furcations,
        }
    
    def get_top_energies(self, n: int = 20):
        return sorted(self.word_to_mode.values(), key=lambda m: m.energy, reverse=True)[:n]
    
    def get_new_modes(self):
        return [m for m in self.word_to_mode.values() if m.creator == "furcation"]


# ═══════════════════════════════════════════════════════
# ТЕСТ
# ═══════════════════════════════════════════════════════

print("\n📂 Загружаю поле...")
start = time.time()
lp = LivingPersonality.load('src/rizoma/data/personalities/p016_tees_channels.json')
print(f"✅ Загрузка: {time.time() - start:.0f}с")

print("\n📊 Сбор статистики...")
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

word_to_mode = {}
for mode in lp.get_all_modes():
    word = mode.trace_id.replace('word_', '')
    if word:
        word_to_mode[word] = mode

print("\n🌀 Создание живого поля с фуркациями...")
field = LiveFieldFurcations(word_to_mode, pairs, word_freq, lp)

print(f"\n📊 Начальное состояние:")
top = field.get_top_energies(10)
for i, m in enumerate(top):
    word = m.trace_id.replace('word_', '').replace('furcated_', '')
    out_count = len(field.channels.get(word, []))
    in_count = len(field.incoming.get(word, []))
    print(f"   {i+1:2d}. {word[:25]:25s} E={m.energy:.4f} исх={out_count} вх={in_count}")

CYCLES = 1000
print(f"\n🔄 Запуск эволюции с фуркациями ({CYCLES} циклов)...")
print(f"   Порог фуркации: адаптивный (3× средний поток)")
start = time.time()

for cycle in range(CYCLES):
    result = field.step(dt=0.1, max_channels=5000)
    
    if (cycle + 1) % 200 == 0:
        elapsed = time.time() - start
        print(f"   [{cycle+1}/{CYCLES}] transfers={result['transfers']}, "
              f"flow={result['total_flow']:.3f}, furcations={result['furcations']}, "
              f"E={result['energy']:.3f}, {elapsed:.0f}с")

print(f"\n⏱️  Эволюция: {time.time() - start:.0f}с")

print(f"\n📊 После эволюции:")
print(f"   Всего переносов: {field.transfers}")
print(f"   Суммарный поток: {field.total_flow:.4f}")
print(f"   Фуркаций: {field.furcations}")
print(f"   Новых мод: {len(field.get_new_modes())}")

top = field.get_top_energies(10)
print(f"\n   Топ-10 мод по энергии:")
for i, m in enumerate(top):
    word = m.trace_id.replace('word_', '').replace('furcated_', '')
    marker = " 🆕" if m.creator == "furcation" else ""
    print(f"   {i+1:2d}. {word[:30]:30s} E={m.energy:.4f}{marker}")

# Покажем новорождённые моды
new_modes = field.get_new_modes()
if new_modes:
    print(f"\n🌱 Новорождённые моды (фуркации):")
    for m in sorted(new_modes, key=lambda x: -x.energy)[:15]:
        word = m.trace_id.replace('furcated_', '')
        print(f"   {word[:40]:40s} E={m.energy:.4f}")

print(f"\n💾 Сохраняю...")
lp.save('src/rizoma/data/personalities/p016_tees_furcations.json')
print(f"✅ Сохранено!")
print(f"   Мод: {len(lp.get_all_modes())}")