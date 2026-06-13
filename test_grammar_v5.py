# test_grammar_v5.py — УНИВЕРСАЛЬНАЯ ГРАММАТИКА: связи, а не позиции
import sys, os, time, math, hashlib
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧪 УНИВЕРСАЛЬНАЯ ГРАММАТИКА: связи вместо позиций")
print("=" * 60)

# Предложения на РАЗНЫХ языках с одинаковым смыслом
test_sentences = [
    # Русский: прил+сущ+глаг
    ["большой", "кот", "спит"],
    ["маленький", "пёс", "бежит"],
    ["старый", "дом", "стоит"],
    ["холодный", "ветер", "дует"],
    ["тёплый", "чай", "греет"],
    
    # Испанский: сущ+прил+глаг (порядок другой!)
    ["gato", "grande", "duerme"],     # кот большой спит
    ["perro", "pequeño", "corre"],    # пёс маленький бежит
    ["casa", "vieja", "permanece"],   # дом старый стоит
    ["viento", "frío", "sopla"],      # ветер холодный дует
    ["té", "caliente", "calienta"],   # чай тёплый греет
    
    # Английский: прил+сущ+глаг (как русский)
    ["big", "cat", "sleeps"],
    ["small", "dog", "runs"],
    ["old", "house", "stands"],
    ["cold", "wind", "blows"],
    ["warm", "tea", "warms"],
    
    # Японский (упрощённо): сущ+прил+глаг (как испанский, но глагол в конце)
    ["neko", "ookii", "nemuru"],      # кот большой спит
    ["inu", "chiisai", "hashiru"],    # пёс маленький бежит
    ["ie", "furui", "tatsu"],         # дом старый стоит
]

CYCLES = 2000

print(f"📝 Предложений: {len(test_sentences)}")
print(f"   Русский: 5, Испанский: 5, Английский: 5, Японский: 5")
print(f"   Порядок слов разный, но СВЯЗИ одинаковые!")
print(f"🔄 Циклов TEES: {CYCLES}")

lp = LivingPersonality(id="universal_grammar", name="Универсальная грамматика", db_path=":memory:")

# ═══════════════════════════════════════════════════════
# ГЕНЕРАЦИЯ МОД: каждая уникальная словоформа — одна мода
# Фаза = хеш слова (универсально, не зависит от позиции)
# ═══════════════════════════════════════════════════════

word_to_mode = {}  # слово → его мода (дедупликация)
cooccurrence = defaultdict(Counter)  # word → {neighbor: count}
position_stats = defaultdict(list)   # word → [positions]

global_time = 0.0

for sent_idx, words in enumerate(test_sentences):
    for i, word in enumerate(words):
        # Создаём моду для слова (только один раз)
        if word not in word_to_mode:
            # tau = хеш слова (детерминировано, не зависит от языка)
            word_hash = hashlib.md5(word.encode()).digest()
            tau = (word_hash[0] % 50) + 5.0
            
            # scale — из типичной позиции (будет уточняться)
            scale = 5.0  # начальное, нейтральное
            
            # amplitude — из частоты (будет расти)
            amplitude = 0.3
            
            # Фаза = хеш слова (каждое слово — своя волна)
            phase = (word_hash[1] / 255.0) * 2 * math.pi
            
            emotion = WaveformEmotion(amplitude=amplitude, base_emotion='neutral')
            
            mode = SpectralMode(
                tau=tau, amplitude=amplitude, scale=scale,
                trace_id=f"word_{word}",
                creator="universal",
                content=word,
                emotion=emotion,
                phase=phase,
            )
            mode.created_at = global_time
            
            text_id = lp.text_store.store(word)
            mode.text_id = text_id
            lp.add_mode(mode)
            word_to_mode[word] = mode
        
        # Обновляем статистику
        position_stats[word].append(i)
        
        # Собираем соседей
        if i > 0:
            cooccurrence[word][words[i-1]] += 1
        if i < len(words) - 1:
            cooccurrence[word][words[i+1]] += 1
    
    global_time += 1.0

print(f"✅ Уникальных слов: {len(word_to_mode)}")
print(f"   (русских, испанских, английских, японских — все в одном поле)")

# ═══════════════════════════════════════════════════════
# TEES
# ═══════════════════════════════════════════════════════

print(f"\n🔄 Запуск TEES ({CYCLES} циклов)...")
print(f"   Порог резонанса: {lp.resonance_threshold:.4f}")

total_transfers = 0
start = time.time()

for cycle in range(CYCLES):
    result = lp.grow_step(dt=0.1)
    total_transfers += result['transfers']
    if (cycle + 1) % 500 == 0:
        print(f"   [{cycle+1}/{CYCLES}] transfers={total_transfers}, E={lp.energy:.3f}, {time.time()-start:.0f}с")

print(f"\n📊 После TEES:")
print(f"   Переносов: {total_transfers}")

# ═══════════════════════════════════════════════════════
# АНАЛИЗ: КТО С КЕМ СВЯЗАН?
# ═══════════════════════════════════════════════════════

print(f"\n🔍 АНАЛИЗ СВЯЗЕЙ (универсальная грамматика):")

# Для каждого слова смотрим его соседей
# Если слово A всегда рядом со словом B — они образуют пару
# Слово, которое связывает две пары — оператор

# Найдём слова по их связям
linkers = []  # слова, которые связывают другие пары
modifiers = []  # слова, которые всегда с одним партнёром
objects = []   # слова, с которыми связываются модификаторы

for word, mode in word_to_mode.items():
    neighbors = cooccurrence[word]
    if not neighbors:
        continue
    
    total_cooc = sum(neighbors.values())
    top_neighbor, top_count = neighbors.most_common(1)[0]
    exclusivity = top_count / total_cooc if total_cooc > 0 else 0
    
    # Если слово имеет много разных соседей → оно связующее (оператор)
    if len(neighbors) >= 3 and exclusivity < 0.5:
        linkers.append((word, len(neighbors), exclusivity))
    # Если слово всегда с одним соседом → оно модификатор (прилагательное)
    elif exclusivity > 0.6 and len(neighbors) <= 2:
        modifiers.append((word, top_neighbor, exclusivity))
    # Остальные — объекты (существительные)
    else:
        objects.append((word, top_neighbor, exclusivity))

print(f"\n   МОДИФИКАТОРЫ (прилагательные? всегда с одним соседом):")
for word, neighbor, exc in sorted(modifiers, key=lambda x: -x[2])[:10]:
    print(f"   {word:15s} → {neighbor:15s} (исключительность: {exc:.2f})")

print(f"\n   ОБЪЕКТЫ (существительные? с ними связываются модификаторы):")
for word, neighbor, exc in sorted(objects, key=lambda x: -x[2])[:10]:
    print(f"   {word:15s} ← {neighbor:15s} (связь: {exc:.2f})")

print(f"\n   ОПЕРАТОРЫ (глаголы? связывают много слов):")
for word, n_neighbors, exc in sorted(linkers, key=lambda x: -x[1])[:10]:
    neighbors_str = ', '.join([w for w, _ in cooccurrence[word].most_common(3)])
    print(f"   {word:15s} связывает {n_neighbors} слов: {neighbors_str} (разброс: {1-exc:.2f})")

# Проверим: на разных языках роли должны совпадать
print(f"\n   ПРОВЕРКА МЕЖЪЯЗЫКОВОЙ УНИВЕРСАЛЬНОСТИ:")
# Кот = gato = cat = neko — все должны быть ОБЪЕКТАМИ
# Большой = grande = big = ookii — все должны быть МОДИФИКАТОРАМИ
# Спит = duerme = sleeps = nemuru — все должны быть ОПЕРАТОРАМИ

pairs_to_check = [
    ("кот", "gato", "cat", "neko"),
    ("большой", "grande", "big", "ookii"),
    ("спит", "duerme", "sleeps", "nemuru"),
]

for words in pairs_to_check:
    roles = []
    for w in words:
        if w in word_to_mode:
            if w in [m[0] for m in modifiers]:
                roles.append("МОДИФИКАТОР")
            elif w in [l[0] for l in linkers]:
                roles.append("ОПЕРАТОР")
            else:
                roles.append("ОБЪЕКТ")
        else:
            roles.append("—")
    print(f"   {' ↔ '.join(words)}: {' | '.join(roles)}")

print(f"\n✅ Тест универсальной грамматики завершён.")
print(f"   Если роли СОВПАДАЮТ для переводов — грамматика выведена честно.")