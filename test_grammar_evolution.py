# test_grammar_evolution.py — ЭВОЛЮЦИЯ ГРАММАТИКИ: русский → другие языки
import sys, os, time, math, hashlib
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧪 ЭВОЛЮЦИЯ ГРАММАТИКИ: русский → европейские")
print("=" * 60)

# ═══════════════════════════════════════════════════════
# ФАЗА 1: Русский язык (древний)
# ═══════════════════════════════════════════════════════

russian_sentences = [
    # Прил+Сущ+Глаг
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
    # Сущ+Глаг+Нареч
    ["кот", "спит", "тихо"],
    ["пёс", "бежит", "быстро"],
    ["дом", "стоит", "крепко"],
    ["ветер", "дует", "сильно"],
    ["конь", "скачет", "резво"],
    # Больше связей
    ["кот", "бежит", "быстро"],
    ["пёс", "спит", "тихо"],
    ["свет", "горит", "ярко"],
    ["лист", "падает", "медленно"],
    ["чай", "греет", "приятно"],
]

print(f"📝 Фаза 1: Русский язык ({len(russian_sentences)} предложений)")
print(f"   Структура: прил+сущ+глаг, сущ+глаг+нар")

lp = LivingPersonality(id="grammar_evolution", name="Эволюция грамматики", db_path=":memory:")

# Генерация мод для русского
word_modes = {}  # слово → мода (единая для всех языков)
links = defaultdict(lambda: {'left': Counter(), 'right': Counter()})  # направленные связи!

global_time = 0.0

for sent_idx, words in enumerate(russian_sentences):
    for i, word in enumerate(words):
        if word not in word_modes:
            word_hash = hashlib.md5(word.encode()).digest()
            tau = (word_hash[0] % 50) + 5.0
            phase = (word_hash[1] / 255.0) * 2 * math.pi
            
            mode = SpectralMode(
                tau=tau, amplitude=0.5, scale=5.0,
                trace_id=f"word_{word}",
                creator="russian",
                content=word,
                emotion=WaveformEmotion(amplitude=0.5, base_emotion='neutral'),
                phase=phase,
            )
            mode.created_at = global_time
            text_id = lp.text_store.store(word)
            mode.text_id = text_id
            lp.add_mode(mode)
            word_modes[word] = mode
        
        # Направленные связи!
        if i > 0:
            links[word]['left'][words[i-1]] += 1
        if i < len(words) - 1:
            links[word]['right'][words[i+1]] += 1
    
    global_time += 1.0

# Определяем роли через направленные связи
def classify_word(word):
    """Классификация по асимметрии связей."""
    l = links[word]
    left_count = sum(l['left'].values())
    right_count = sum(l['right'].values())
    total = left_count + right_count
    
    if total == 0:
        return "неизвестно", 0
    
    # Асимметрия: -1 = только левые, +1 = только правые
    asymmetry = (right_count - left_count) / total if total > 0 else 0
    
    # Уникальность связей
    unique_neighbors = len(set(list(l['left'].keys()) + list(l['right'].keys())))
    
    if unique_neighbors >= 4:
        role = "ОПЕРАТОР (глагол?)"  # связывает многих
    elif asymmetry > 0.5:
        role = "МОДИФИКАТОР_ЛЕВЫЙ (прил?)"  # чаще справа от соседа → прилагательное в русском
    elif asymmetry < -0.5:
        role = "МОДИФИКАТОР_ПРАВЫЙ (нар?)"  # чаще слева от соседа → наречие в русском
    else:
        role = "ОБЪЕКТ (сущ?)"  # сбалансированные связи
    
    confidence = min(1.0, unique_neighbors / 5)
    return role, confidence

print(f"\n🔍 Роли слов в русском (по направленным связям):")
print(f"   {'Слово':15s} {'Роль':35s} {'Увер.':6s} {'Левые соседи':20s} {'Правые соседи':20s}")
print(f"   {'-'*15} {'-'*35} {'-'*6} {'-'*20} {'-'*20}")

russian_roles = {}
for word in sorted(word_modes.keys()):
    role, conf = classify_word(word)
    russian_roles[word] = (role, conf)
    left_str = ', '.join([w for w, _ in links[word]['left'].most_common(2)])
    right_str = ', '.join([w for w, _ in links[word]['right'].most_common(2)])
    conf_bar = '█' * int(conf * 5)
    print(f"   {word:15s} {role:35s} {conf_bar:6s} {left_str:20s} {right_str:20s}")

# ═══════════════════════════════════════════════════════
# ФАЗА 2: Испанский язык (модификация)
# ═══════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"📝 Фаза 2: Испанский язык (сущ+прил+глаг)")
print(f"   Гипотеза: МОДИФИКАТОР_ЛЕВЫЙ → МОДИФИКАТОР_ПРАВЫЙ")

spanish_sentences = [
    ["gato", "grande", "duerme"],
    ["perro", "pequeño", "corre"],
    ["casa", "vieja", "permanece"],
    ["viento", "frío", "sopla"],
    ["té", "caliente", "calienta"],
]

spanish_new_words = []
for sent_idx, words in enumerate(spanish_sentences):
    for i, word in enumerate(words):
        if word not in word_modes:
            word_hash = hashlib.md5(word.encode()).digest()
            tau = (word_hash[0] % 50) + 5.0
            phase = (word_hash[1] / 255.0) * 2 * math.pi
            
            mode = SpectralMode(
                tau=tau, amplitude=0.5, scale=5.0,
                trace_id=f"word_{word}",
                creator="spanish",
                content=word,
                emotion=WaveformEmotion(amplitude=0.5, base_emotion='neutral'),
                phase=phase,
            )
            mode.created_at = global_time
            text_id = lp.text_store.store(word)
            mode.text_id = text_id
            lp.add_mode(mode)
            word_modes[word] = mode
            spanish_new_words.append(word)
        
        if i > 0:
            links[word]['left'][words[i-1]] += 1
        if i < len(words) - 1:
            links[word]['right'][words[i+1]] += 1
    
    global_time += 1.0

print(f"   Новых слов: {len(spanish_new_words)}")

# Смотрим, как изменились роли
print(f"\n🔍 Изменение ролей после испанского:")
print(f"   {'Русское слово':15s} {'Роль в русском':35s} → {'Исп. перевод':15s} {'Роль после исп.':35s}")
print(f"   {'-'*15} {'-'*35} {'-'*15} {'-'*35}")

translations = [
    ("кот", "gato"), ("большой", "grande"), ("спит", "duerme"),
    ("пёс", "perro"), ("маленький", "pequeño"), ("бежит", "corre"),
    ("дом", "casa"), ("старый", "vieja"), ("стоит", "permanece"),
    ("ветер", "viento"), ("холодный", "frío"), ("дует", "sopla"),
    ("чай", "té"), ("тёплый", "caliente"), ("греет", "calienta"),
]

role_changes = []
for ru_word, es_word in translations:
    ru_role, _ = russian_roles.get(ru_word, ("?", 0))
    es_role, _ = classify_word(es_word)
    
    changed = "✓" if ru_role == es_role else "⚠ ИЗМЕНИЛОСЬ"
    if "МОДИФИКАТОР_ЛЕВЫЙ" in ru_role and "МОДИФИКАТОР_ПРАВЫЙ" in es_role:
        changed = "🔀 ИНВЕРСИЯ (прил переползло)"
    if "МОДИФИКАТОР_ПРАВЫЙ" in ru_role and "МОДИФИКАТОР_ЛЕВЫЙ" in es_role:
        changed = "🔀 ИНВЕРСИЯ (нар переползло)"
    
    role_changes.append((ru_word, ru_role, es_word, es_role, changed))
    print(f"   {ru_word:15s} {ru_role:35s} → {es_word:15s} {es_role:35s} {changed}")

# Статистика изменений
inversions = sum(1 for _, _, _, _, c in role_changes if "ИНВЕРСИЯ" in c)
unchanged = sum(1 for _, _, _, _, c in role_changes if c == "✓")

print(f"\n📊 Статистика эволюции:")
print(f"   Не изменилось: {unchanged}")
print(f"   Инверсий (прил/нар переползли): {inversions}")
print(f"   Всего пар: {len(role_changes)}")

if inversions > 0:
    print(f"\n💡 Обнаружена эволюционная модификация!")
    print(f"   В испанском модификатор переполз с левой стороны на правую.")
    print(f"   Связь сохранилась, направление изменилось.")

print(f"\n✅ Эволюционный тест завершён.")