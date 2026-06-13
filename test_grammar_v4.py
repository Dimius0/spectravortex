# test_grammar_v4.py — ФИЗИКА СМЫСЛА: моды-объекты + TEES-операторы
# Без семантики. Слова сами становятся модами или связями через TEES.
import sys, os, time, math, hashlib
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧪 ФИЗИКА СМЫСЛА: моды-объекты + TEES-операторы (без семантики)")
print("=" * 60)

# Предложения — просто последовательности слов
test_sentences = [
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
    ["большой", "кот", "бежит"],
    ["маленький", "пёс", "спит"],
    ["старый", "дом", "цветёт"],
    ["холодный", "чай", "греет"],
    ["яркий", "свет", "падает"],
]

CYCLES = 3000

print(f"📝 Предложений: {len(test_sentences)}")
print(f"🔄 Циклов TEES: {CYCLES}")
print(f"   Гипотеза: слова сами станут модами (объектами) или операторами (связями)")
print(f"   через то, как они взаимодействуют в TEES.")

# Создаём поле
lp = LivingPersonality(id="physics_of_meaning", name="Физика смысла", db_path=":memory:")

# ═══════════════════════════════════════════════════════
# ГЕНЕРАЦИЯ МОД: каждое слово — потенциальная мода
# НИКАКОЙ семантики! Только позиция и соседство.
# ═══════════════════════════════════════════════════════

total_modes = 0
global_time = 0.0
all_words_flat = []  # все слова для статистики

for sent_idx, words in enumerate(test_sentences):
    all_words_flat.extend(words)
    
    for i, word in enumerate(words):
        # tau — из самого слова
        base_tau = (len(word) * 4 + sum(ord(c) for c in word[:5]) % 50) % 50 + 5
        tau = base_tau
        
        # scale — из позиции: начало предложения = ниже, конец = выше
        scale = 2.0 + (i / max(len(words) - 1, 1)) * 15.0
        
        # amplitude — все равны на старте (поле само решит)
        amplitude = 0.5
        
        # phase — из позиции (чтобы соседние слова были в разных фазах)
        phase = (i / len(words)) * 2 * math.pi
        
        emotion = WaveformEmotion(amplitude=amplitude, base_emotion='neutral')
        
        mode = SpectralMode(
            tau=tau, amplitude=amplitude, scale=scale,
            trace_id=f"w_{word}_{sent_idx}_{i}",
            creator="unknown",  # роль НЕ задана!
            content=word,
            emotion=emotion,
            phase=phase,
        )
        mode.created_at = global_time + i * 0.1
        # Сохраняем позицию для анализа
        mode.position = i
        mode.sentence_idx = sent_idx
        
        text_id = lp.text_store.store(word)
        mode.text_id = text_id
        lp.add_mode(mode)
        total_modes += 1
    
    global_time += 1.0

print(f"✅ Создано мод: {total_modes}")
print(f"   Все моды имеют creator='unknown' — роль не задана")

# Частоты слов (для анализа потом)
word_freq = Counter(all_words_flat)

# ═══════════════════════════════════════════════════════
# TEES-РЕЛАКСАЦИЯ
# ═══════════════════════════════════════════════════════

print(f"\n🔄 Запуск TEES ({CYCLES} циклов)...")
print(f"   Порог резонанса: {lp.resonance_threshold:.4f}")
print(f"   Гарм. допуск: {lp.harmonic_tolerance:.4f}")

total_transfers = 0
start = time.time()

for cycle in range(CYCLES):
    result = lp.grow_step(dt=0.1)
    total_transfers += result['transfers']
    
    if (cycle + 1) % 500 == 0:
        elapsed = time.time() - start
        print(f"   [{cycle+1}/{CYCLES}] transfers={total_transfers}, E={lp.energy:.3f}, {elapsed:.0f}с")

print(f"\n📊 После TEES:")
print(f"   Переносов: {total_transfers}")
print(f"   Попыток: {lp.stats['tees_attempts']}")
print(f"   Успехов: {lp.stats['tees_successes']}")

# ═══════════════════════════════════════════════════════
# АНАЛИЗ: КТО СТАЛ ОБЪЕКТОМ, КТО — ОПЕРАТОРОМ?
# ═══════════════════════════════════════════════════════

print(f"\n🔍 АНАЛИЗ: КЕМ СТАЛИ СЛОВА?")

# Если TEES молчит — анализируем через позиции и tau
# Гипотеза: слова-объекты (сущ) должны иметь стабильный tau
# Слова-операторы (глаг) должны быть между объектами
# Слова-градиенты (прил) должны быть перед объектами

# Сгруппируем одинаковые слова
word_stats = defaultdict(lambda: {
    'count': 0, 'positions': [], 'taus': [], 'energies': [], 
    'left_neighbors': [], 'right_neighbors': []
})

for mode in lp.get_all_modes():
    word = mode.content
    ws = word_stats[word]
    ws['count'] += 1
    ws['positions'].append(getattr(mode, 'position', -1))
    ws['taus'].append(mode.tau)
    ws['energies'].append(mode.effective_energy)

# Соберём соседей из исходных предложений
for sent_idx, words in enumerate(test_sentences):
    for i, word in enumerate(words):
        ws = word_stats[word]
        if i > 0:
            ws['left_neighbors'].append(words[i-1])
        if i < len(words) - 1:
            ws['right_neighbors'].append(words[i+1])

print(f"\n   Статистика слов (роль определяется позицией и соседями):")
print(f"   {'Слово':15s} {'Шт':4s} {'AvgPos':7s} {'AvgTau':7s} {'AvgE':7s} {'Левый сосед':15s} {'Правый сосед':15s} {'Вероятная роль'}")
print(f"   {'-'*15} {'-'*4} {'-'*7} {'-'*7} {'-'*7} {'-'*15} {'-'*15} {'-'*20}")

for word, ws in sorted(word_stats.items(), key=lambda x: -x[1]['count']):
    avg_pos = sum(ws['positions']) / len(ws['positions']) if ws['positions'] else 0
    avg_tau = sum(ws['taus']) / len(ws['taus']) if ws['taus'] else 0
    avg_e = sum(ws['energies']) / len(ws['energies']) if ws['energies'] else 0
    
    left = Counter(ws['left_neighbors']).most_common(1)
    right = Counter(ws['right_neighbors']).most_common(1)
    left_str = left[0][0] if left else '-'
    right_str = right[0][0] if right else '-'
    
    # Эвристика роли (без семантики!)
    if avg_pos < 1.0 and right_str:
        role = "ГРАДИЕНТ (прил?)"
    elif avg_pos > 1.0 and left_str:
        role = "ОПЕРАТОР (глаг?)"
    else:
        role = "ОБЪЕКТ (сущ?)"
    
    print(f"   {word:15s} {ws['count']:4d} {avg_pos:7.2f} {avg_tau:7.1f} {avg_e:7.3f} {left_str:15s} {right_str:15s} {role}")

print(f"\n✅ Тест физики смысла завершён.")
print(f"   Если поле само выделило роли — слова на позиции 0 (первые)")
print(f"   должны быть ГРАДИЕНТАМИ, на позиции 1 — ОБЪЕКТАМИ, на позиции 2 — ОПЕРАТОРАМИ.")