# build_field_from_dialogues_v3.py — ПОЛНАЯ СБОРКА: 43K сообщений с эволюционной грамматикой
import sys, os, json, time, math, hashlib
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧬 ПОЛНАЯ СБОРКА ПОЛЯ: 43K диалогов + эволюционная грамматика")
print("=" * 60)

# Параметры
INPUT_FILE = 'dialogue_texts.json'
OUTPUT_JSON = 'src/rizoma/data/personalities/p016_dialogues_full.json'
OUTPUT_DB = 'src/rizoma/data/personalities/text_store_dialogues_full.db'
MAX_TEXTS = None  # Все 43K

# Загружаем тексты
print(f"\n📂 Загружаю {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)

if MAX_TEXTS:
    texts = all_texts[:MAX_TEXTS]
else:
    texts = all_texts

print(f"   Сообщений: {len(texts)}")

# Создаём поле
lp = LivingPersonality(id="p016_dialogues_full", name="p016 полное поле диалогов", db_path=OUTPUT_DB)

# ═══════════════════════════════════════════════════════
# ГЕНЕРАТОР МОД С ЭВОЛЮЦИОННОЙ ГРАММАТИКОЙ
# ═══════════════════════════════════════════════════════

def tokenize(text):
    """Простая токенизация: слова из букв и цифр."""
    import re
    return [w.lower() for w in re.findall(r'[а-яёa-z0-9]+', text) if len(w) > 1]

# Глобальные структуры
word_to_mode = {}  # слово → мода (единая для всего поля)
pairs = Counter()  # направленные пары (A, B, direction)
word_freq = Counter()  # частота слов
total_modes = 0
global_time = 0.0

print(f"\n🔨 Генерация мод...")
start = time.time()

for i, item in enumerate(texts):
    if i % 5000 == 0:
        elapsed = time.time() - start
        print(f"   {i}/{len(texts)} ({i*100/len(texts):.0f}%) — {total_modes} мод, {len(word_to_mode)} слов, {elapsed:.0f}с")
    
    text = item.get('text', '')
    role = item.get('role', 'user')
    
    if not text or len(text) < 10:
        global_time += 1.0
        continue
    
    words = tokenize(text)
    if len(words) < 2:
        global_time += 1.0
        continue
    
    # Сохраняем полный текст в SQLite
    lp.text_store.store(text)
    
    # Обновляем частоты слов
    for word in words:
        word_freq[word] += 1
    
    # Собираем направленные пары
    for j in range(len(words) - 1):
        w1, w2 = words[j], words[j+1]
        pairs[(w1, w2, 'LR')] += 1
        pairs[(w2, w1, 'RL')] += 1
    
    # Создаём моды для новых слов
    for j, word in enumerate(words):
        if word not in word_to_mode:
            word_hash = hashlib.md5(word.encode()).digest()
            tau = (word_hash[0] % 50) + 5.0
            phase = (word_hash[1] / 255.0) * 2 * math.pi
            scale = 2.0 + (len(word) / 10)
            amplitude = 0.3
            
            emotion = WaveformEmotion.from_string('neutral', amplitude)
            
            mode = SpectralMode(
                tau=tau, amplitude=amplitude, scale=scale,
                trace_id=f"word_{word}",
                creator="dialogue_field",
                content=word,
                emotion=emotion,
                phase=phase,
            )
            mode.created_at = global_time
            mode.text_id = lp.text_store.store(word)
            lp.add_mode(mode)
            word_to_mode[word] = mode
            total_modes += 1
        
        # Обновляем позиционную статистику для моды
        mode = word_to_mode[word]
        if not hasattr(mode, 'positions'):
            mode.positions = []
        mode.positions.append(j)
    
    global_time += 1.0

print(f"\n   Готово: {total_modes} мод, {len(word_to_mode)} уникальных слов за {time.time() - start:.0f}с")

# ═══════════════════════════════════════════════════════
# АНАЛИЗ ГРАММАТИКИ НА 43K СООБЩЕНИЙ
# ═══════════════════════════════════════════════════════

print(f"\n📊 Статистика:")
print(f"   Всего мод: {len(lp.get_all_modes())}")
print(f"   Уникальных слов: {len(word_to_mode)}")
print(f"   Направленных пар: {len(pairs)}")
print(f"   Всего вхождений пар: {sum(pairs.values())}")

# Доминирующее направление для частых пар
print(f"\n🔍 Топ-20 доминирующих пар:")
pair_dominance = {}
for (w1, w2, d), count in pairs.most_common(200000):
    key = (w1, w2) if w1 < w2 else (w2, w1)
    opposite_d = 'RL' if d == 'LR' else 'LR'
    opposite_count = pairs.get((w2, w1, opposite_d), 0)
    if count >= opposite_count:
        pair_dominance[key] = (w1, w2, d, count)

for (w1, w2), (a, b, d, count) in sorted(pair_dominance.items(), key=lambda x: -x[1][3])[:20]:
    dir_str = f"{a} → {b}" if d == 'LR' else f"{b} ← {a}"
    print(f"   {dir_str:40s} ({count} раз)")

# Роли слов через асимметрию связей
print(f"\n🔍 Роли частых слов (по асимметрии связей):")
links = defaultdict(lambda: {'left': Counter(), 'right': Counter()})

for (w1, w2, d), count in pairs.items():
    if d == 'LR':
        links[w1]['right'][w2] += count
        links[w2]['left'][w1] += count
    else:
        links[w2]['right'][w1] += count
        links[w1]['left'][w2] += count

top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:30]

print(f"   {'Слово':20s} {'Частота':8s} {'Роль':30s} {'Левые':20s} {'Правые':20s}")
print(f"   {'-'*20} {'-'*8} {'-'*30} {'-'*20} {'-'*20}")

for word, freq in top_words:
    l = links[word]
    left_count = sum(l['left'].values())
    right_count = sum(l['right'].values())
    total = left_count + right_count
    
    if total == 0:
        role = "изолированное"
    else:
        asymmetry = (right_count - left_count) / total
        unique_neighbors = len(set(list(l['left'].keys()) + list(l['right'].keys())))
        
        if unique_neighbors >= 30:
            role = "ОПЕРАТОР (связующее)"
        elif asymmetry > 0.6:
            role = "МОДИФИКАТОР ЛЕВЫЙ"
        elif asymmetry < -0.6:
            role = "МОДИФИКАТОР ПРАВЫЙ"
        else:
            role = "ОБЪЕКТ"
    
    left_str = ', '.join([w for w, _ in l['left'].most_common(2)])
    right_str = ', '.join([w for w, _ in l['right'].most_common(2)])
    print(f"   {word:20s} {freq:8d} {role:30s} {left_str:20s} {right_str:20s}")

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
save_start = time.time()
lp.save(OUTPUT_JSON)
print(f"   Сохранение: {time.time() - save_start:.0f}с")
print(f"   JSON: {OUTPUT_JSON}")
print(f"   DB:   {OUTPUT_DB}")
print(f"   Размер JSON: {os.path.getsize(OUTPUT_JSON) / 1024**2:.0f} МБ")
print(f"   Размер DB:   {os.path.getsize(OUTPUT_DB) / 1024**2:.0f} МБ")

print(f"\n✅ Полная сборка завершена!")