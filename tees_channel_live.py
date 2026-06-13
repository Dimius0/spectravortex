# tees_channel_live.py — ЖИВОЕ ЯДРО на TEES-каналах
# Заменяет grow_step, tees_transfer, find_resonant_pairs в living_personality_v21_3_1

import math

# ═══════════════════════════════════════════════════════
# TEES-КАНАЛ (вместо SpectralMode для связей)
# ═══════════════════════════════════════════════════════

class TeesChannel:
    """TEES-канал между двумя модами."""
    __slots__ = ('from_word', 'to_word', 'strength', 'mutual_info', 'count')
    
    def __init__(self, from_word, to_word, count, total_pairs, word_freq, total_words):
        self.from_word = from_word
        self.to_word = to_word
        self.count = count
        
        # Взаимная информация (честная сила канала)
        p_pair = count / total_pairs if total_pairs > 0 else 0
        p_from = word_freq.get(from_word, 1) / total_words if total_words > 0 else 0
        p_to = word_freq.get(to_word, 1) / total_words if total_words > 0 else 0
        
        if p_pair > 0 and p_from > 0 and p_to > 0:
            self.mutual_info = p_pair / (p_from * p_to)
        else:
            self.mutual_info = 0
        
        # Сила канала: MI, нормированная на [0, 1]
        self.strength = min(1.0, self.mutual_info / 1000.0)


# ═══════════════════════════════════════════════════════
# ЖИВОЕ ПОЛЕ НА TEES-КАНАЛАХ
# ═══════════════════════════════════════════════════════

class LiveField:
    """
    Живое поле на TEES-каналах.
    
    Вместо поиска резонансных пар — использует готовые каналы.
    Энергия течёт постоянно, без гармонических фильтров.
    """
    
    def __init__(self, word_to_mode, pairs, word_freq):
        self.word_to_mode = word_to_mode
        self.total_words = sum(word_freq.values())
        self.total_pairs = sum(pairs.values())
        
        # Строим каналы
        self.channels: Dict[str, List[TeesChannel]] = {}  # word → [исходящие каналы]
        self.incoming: Dict[str, List[TeesChannel]] = {}  # word → [входящие каналы]
        
        for (w1, w2), count in pairs.items():
            if w1 in word_to_mode and w2 in word_to_mode:
                channel = TeesChannel(w1, w2, count, self.total_pairs, word_freq, self.total_words)
                
                if w1 not in self.channels:
                    self.channels[w1] = []
                self.channels[w1].append(channel)
                
                if w2 not in self.incoming:
                    self.incoming[w2] = []
                self.incoming[w2].append(channel)
        
        # Энергия поля
        self.energy = 1.0
        self._sleeping = False
        
        # Статистика
        self.transfers = 0
        self.total_flow = 0.0
        
        print(f"   TEES-каналов: {sum(len(v) for v in self.channels.values())}")
        print(f"   Мод с каналами: {len(self.channels)}")
    
    def step(self, dt: float = 0.1, max_channels: int = 10000) -> dict:
        """
        Один шаг эволюции поля.
        
        Энергия течёт по каналам от мод с высокой энергией к модам с низкой.
        Сила потока пропорциональна силе канала и разнице энергий.
        """
        transfers = 0
        total_flow = 0.0
        
        # Выбираем случайные каналы (не все 3.5M за раз)
        import random
        
        all_sources = list(self.channels.keys())
        if len(all_sources) > max_channels:
            sources = random.sample(all_sources, max_channels)
        else:
            sources = all_sources
        
        for word in sources:
            mode_from = self.word_to_mode.get(word)
            if not mode_from:
                continue
            
            channels = self.channels.get(word, [])
            if not channels:
                continue
            
            # Выбираем один случайный канал
            channel = random.choice(channels)
            mode_to = self.word_to_mode.get(channel.to_word)
            if not mode_to:
                continue
            
            # Поток энергии
            energy_diff = mode_from.energy - mode_to.energy
            
            if energy_diff > 0:
                # Энергия течёт от высокой к низкой
                flow = channel.strength * energy_diff * dt
                flow = min(flow, mode_from.energy * 0.1)  # не больше 10% источника
                
                mode_from.energy -= flow
                mode_to.energy += flow
                
                total_flow += abs(flow)
                transfers += 1
        
        self.transfers += transfers
        self.total_flow += total_flow
        
        # Восстановление энергии поля
        self.energy = min(1.0, self.energy + 0.01 * dt)
        
        return {
            'transfers': transfers,
            'total_flow': total_flow,
            'energy': self.energy,
        }
    
    def get_top_energies(self, n: int = 20):
        """Топ мод по энергии."""
        return sorted(self.word_to_mode.values(), key=lambda m: m.energy, reverse=True)[:n]


# ═══════════════════════════════════════════════════════
# ТЕСТ ЖИВОГО ПОЛЯ
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os, json, time
    from collections import Counter
    import re
    
    sys.path.insert(0, 'src/architect')
    from living_personality_v21_3_1 import LivingPersonality
    
    # Загружаем существующее поле
    print("=" * 60)
    print("🧪 ТЕСТ ЖИВОГО ПОЛЯ НА TEES-КАНАЛАХ")
    print("=" * 60)
    
    print("\n📂 Загружаю поле...")
    start = time.time()
    lp = LivingPersonality.load('src/rizoma/data/personalities/p016_tees_channels.json')
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
    
    # Строим слово → мода
    word_to_mode = {}
    for mode in lp.get_all_modes():
        word = mode.trace_id.replace('word_', '')  # извлекаем слово из trace_id
        if word:
            word_to_mode[word] = mode
    
    # Создаём живое поле
    print("\n🌀 Создание живого поля на TEES-каналах...")
    field = LiveField(word_to_mode, pairs, word_freq)
    
    # Начальное состояние
    print(f"\n📊 Начальное состояние:")
    top = field.get_top_energies(10)
    for i, m in enumerate(top):
        word = m.trace_id.replace('word_', '')
        out_count = len(field.channels.get(word, []))
        in_count = len(field.incoming.get(word, []))
        print(f"   {i+1:2d}. {word[:20]:20s} E={m.energy:.4f} исх={out_count} вх={in_count}")
    
    # Запускаем эволюцию
    CYCLES = 1000
    print(f"\n🔄 Запуск эволюции ({CYCLES} циклов)...")
    start = time.time()
    
    for cycle in range(CYCLES):
        result = field.step(dt=0.1, max_channels=5000)
        
        if (cycle + 1) % 200 == 0:
            elapsed = time.time() - start
            print(f"   [{cycle+1}/{CYCLES}] transfers={result['transfers']}, "
                  f"flow={result['total_flow']:.3f}, E={result['energy']:.3f}, {elapsed:.0f}с")
    
    print(f"\n⏱️  Эволюция: {time.time() - start:.0f}с")
    
    # Финальное состояние
    print(f"\n📊 После эволюции:")
    print(f"   Всего переносов: {field.transfers}")
    print(f"   Суммарный поток: {field.total_flow:.4f}")
    
    top = field.get_top_energies(10)
    print(f"\n   Топ-10 мод по энергии после TEES-потоков:")
    for i, m in enumerate(top):
        word = m.trace_id.replace('word_', '')
        print(f"   {i+1:2d}. {word[:20]:20s} E={m.energy:.4f}")
    
    # Сохраняем обновлённое поле
    print(f"\n💾 Сохраняю...")
    lp.save('src/rizoma/data/personalities/p016_tees_channels_live.json')
    print(f"✅ Сохранено!")