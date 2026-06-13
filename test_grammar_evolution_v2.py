# test_grammar_evolution_v2.py — ЭВОЛЮЦИЯ ГРАММАТИКИ через ПАРЫ связей
import sys, os, time, math, hashlib
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧪 ЭВОЛЮЦИЯ ГРАММАТИКИ v2: через ПАРЫ связей")
print("=" * 60)

# ═══════════════════════════════════════════════════════
# ФАЗА 1: Русский язык — строим пары
# ═══════════════════════════════════════════════════════

russian_sentences = [
    ["большой", "кот", "спит"],
    ["маленький", "пёс", "бежит"],
    ["старый", "дом", "стоит"],
    ["новый", "день", "настал"],
    ["холодный", "ветер", "дует"],
    ["тёплый", "чай", "греет"],
    ["зелёный", "лист", "падает"],
    ["быстрый", "конь", "скачет"],
    ["тихий", "сад", "цветёт"],
    ["яркий", "свет", "горит"],
    ["кот", "спит", "тихо"],
    ["пёс", "бежит", "быстро"],
    ["дом", "стоит", "крепко"],
    ["ветер", "дует", "сильно"],
    ["конь", "скачет", "резво"],
    ["кот", "бежит", "быстро"],
    ["пёс", "спит", "тихо"],
    ["свет", "горит", "ярко"],
    ["лист", "падает", "медленно"],
    ["чай", "греет", "приятно"],
    ["огромный", "кот", "спит"],
    ["маленький", "кот", "бежит"],
    ["старый", "кот", "спит"],
    ["холодный", "чай", "греет"],
    ["тёплый", "ветер", "дует"],
]

print(f"📝 Фаза 1: Русский язык ({len(russian_sentences)} предложений)")

lp = LivingPersonality(id="grammar_pairs", name="Грамматика пар", db_path=":memory:")

# Собираем направленные пары
# pair = (word_a, word_b, direction): direction = 'LR' (A слева от B) или 'RL'
pairs_russian = Counter()  # (A, B, direction) → count
word_to_mode = {}
global_time = 0.0

for sent_idx, words in enumerate(russian_sentences):
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        pairs_russian[(w1, w2, 'LR')] += 1  # w1 слева от w2
        pairs_russian[(w2, w1, 'RL')] += 1  # w2 справа от w1
    
    for word in words:
        if word not in word_to_mode:
            word_hash = hashlib.md5(word.encode()).digest()
            tau = (word_hash[0] % 50) + 5.0
            phase = (word_hash[1] / 255.0) * 2 * math.pi
            mode = SpectralMode(
                tau=tau, amplitude=0.5, scale=5.0,
                trace_id=f"word_{word}", creator="russian", content=word,
                emotion=WaveformEmotion(amplitude=0.5, base_emotion='neutral'),
                phase=phase,
            )
            mode.created_at = global_time
            mode.text_id = lp.text_store.store(word)
            lp.add_mode(mode)
            word_to_mode[word] = mode
    global_time += 1.0

# Топ пар в русском
print(f"\n🔍 Топ-15 направленных пар в русском:")
print(f"   {'Пара':30s} {'Направление':12s} {'Шт':5s}")
for (w1, w2, d), count in pairs_russian.most_common(15):
    dir_str = f"{w1} → {w2}" if d == 'LR' else f"{w2} ← {w1}"
    print(f"   {dir_str:30s} {d:12s} {count:5d}")

# Определяем доминирующее направление для каждой пары слов
pair_direction = {}  # (w1, w2) → 'LR' или 'RL' (доминирующее)
for (w1, w2, d), count in pairs_russian.items():
    key = (w1, w2) if w1 < w2 else (w2, w1)
    opposite_d = 'RL' if d == 'LR' else 'LR'
    opposite_count = pairs_russian.get((w2, w1, opposite_d), 0)
    if count >= opposite_count:
        pair_direction[key] = (d, count)

print(f"\n   Доминирующие направления пар:")
for (w1, w2), (d, count) in sorted(pair_direction.items(), key=lambda x: -x[1][1])[:10]:
    dir_str = f"{w1} → {w2}" if d == 'LR' else f"{w2} ← {w1}"
    print(f"   {dir_str:30s} ({count} раз)")

# ═══════════════════════════════════════════════════════
# ФАЗА 2: Испанский — сравниваем пары
# ═══════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"📝 Фаза 2: Испанский язык")

spanish_sentences = [
    ["gato", "grande", "duerme"],
    ["perro", "pequeño", "corre"],
    ["casa", "vieja", "permanece"],
    ["viento", "frío", "sopla"],
    ["té", "caliente", "calienta"],
    ["gato", "pequeño", "duerme"],
    ["perro", "grande", "corre"],
    ["casa", "grande", "permanece"],
    ["viento", "caliente", "sopla"],
    ["té", "frío", "calienta"],
]

pairs_spanish = Counter()
for sent_idx, words in enumerate(spanish_sentences):
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        pairs_spanish[(w1, w2, 'LR')] += 1
        pairs_spanish[(w2, w1, 'RL')] += 1
    
    for word in words:
        if word not in word_to_mode:
            word_hash = hashlib.md5(word.encode()).digest()
            tau = (word_hash[0] % 50) + 5.0
            phase = (word_hash[1] / 255.0) * 2 * math.pi
            mode = SpectralMode(
                tau=tau, amplitude=0.5, scale=5.0,
                trace_id=f"word_{word}", creator="spanish", content=word,
                emotion=WaveformEmotion(amplitude=0.5, base_emotion='neutral'),
                phase=phase,
            )
            mode.created_at = global_time
            mode.text_id = lp.text_store.store(word)
            lp.add_mode(mode)
            word_to_mode[word] = mode
    global_time += 1.0

# ═══════════════════════════════════════════════════════
# СРАВНЕНИЕ ПАР: русский vs испанский
# ═══════════════════════════════════════════════════════

translations = [
    ("кот", "gato"), ("большой", "grande"), ("спит", "duerme"),
    ("пёс", "perro"), ("маленький", "pequeño"), ("бежит", "corre"),
    ("дом", "casa"), ("старый", "vieja"), ("стоит", "permanece"),
    ("ветер", "viento"), ("холодный", "frío"), ("дует", "sopla"),
    ("чай", "té"), ("тёплый", "caliente"), ("греет", "calienta"),
]

print(f"\n🔍 СРАВНЕНИЕ ПАР: русский → испанский")
print(f"   {'Русская пара':25s} {'Напр':4s} {'Испанская пара':25s} {'Напр':4s} {'Результат'}")
print(f"   {'-'*25} {'-'*4} {'-'*25} {'-'*4} {'-'*20}")

inversions = 0
preserved = 0
different = 0

# Сравниваем пары (прил, сущ) и (сущ, глаг)
# Русские пары
ru_pairs_to_check = [
    ("большой", "кот"), ("маленький", "пёс"), ("старый", "дом"),
    ("холодный", "ветер"), ("тёплый", "чай"), ("кот", "спит"),
    ("пёс", "бежит"), ("дом", "стоит"), ("ветер", "дует"), ("чай", "греет"),
]

for ru_w1, ru_w2 in ru_pairs_to_check:
    # Находим испанские эквиваленты
    es_w1 = dict(translations).get(ru_w1)
    es_w2 = dict(translations).get(ru_w2)
    if not es_w1 or not es_w2:
        continue
    
    # Доминирующее направление в русском
    ru_key = (ru_w1, ru_w2) if ru_w1 < ru_w2 else (ru_w2, ru_w1)
    ru_dir, ru_count = pair_direction.get(ru_key, ('?', 0))
    ru_str = f"{ru_w1}→{ru_w2}" if ru_dir == 'LR' else f"{ru_w1}←{ru_w2}"
    
    # Доминирующее направление в испанском
    es_lr = pairs_spanish.get((es_w1, es_w2, 'LR'), 0)
    es_rl = pairs_spanish.get((es_w2, es_w1, 'RL'), 0)
    es_dir = 'LR' if es_lr >= es_rl else 'RL'
    es_str = f"{es_w1}→{es_w2}" if es_dir == 'LR' else f"{es_w1}←{es_w2}"
    
    # Сравниваем
    if ru_dir == es_dir:
        result = "✓ СОХРАНИЛОСЬ"
        preserved += 1
    elif ru_dir == 'LR' and es_dir == 'RL':
        result = "🔀 ИНВЕРСИЯ (L→R стало R→L)"
        inversions += 1
    elif ru_dir == 'RL' and es_dir == 'LR':
        result = "🔀 ИНВЕРСИЯ (R→L стало L→R)"
        inversions += 1
    else:
        result = "⚠ РАЗНОЕ"
        different += 1
    
    print(f"   {ru_str:25s} {ru_dir:4s} {es_str:25s} {es_dir:4s} {result}")

print(f"\n📊 Статистика эволюции пар:")
print(f"   Сохранилось: {preserved}")
print(f"   Инверсий: {inversions}")
print(f"   Разное: {different}")

if inversions > 0:
    print(f"\n💡 ОБНАРУЖЕНА ЭВОЛЮЦИОННАЯ ИНВЕРСИЯ!")
    print(f"   В испанском направление связи изменилось на противоположное.")
    print(f"   Прилагательное и существительное поменялись местами,")
    print(f"   но СВЯЗЬ между ними сохранилась.")
    print(f"   Это и есть универсальная грамматика — инвариант относительно инверсии.")

print(f"\n✅ Эволюционный тест v2 завершён.")