# test_grammar.py — тест на выведение грамматики через градиенты и TEES
import sys, os, time, math, hashlib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧪 ТЕСТ: ВЫВЕДЕНИЕ ГРАММАТИКИ")
print("=" * 60)

# Тестовые предложения — простые русские фразы с повторяющимися паттернами
test_sentences = [
    # Паттерн: прилагательное + существительное + глагол
    "большой кот спит",
    "маленький пёс бежит",
    "старый дом стоит",
    "новый день настал",
    "холодный ветер дует",
    "тёплый чай греет",
    "зелёный лист падает",
    "быстрый конь скачет",
    "тихий сад цветёт",
    "яркий свет горит",
    
    # Паттерн: существительное + глагол + наречие
    "кот спит тихо",
    "пёс бежит быстро",
    "дом стоит крепко",
    "день настал внезапно",
    "ветер дует сильно",
    "чай греет приятно",
    "лист падает медленно",
    "конь скачет резво",
    "сад цветёт пышно",
    "свет горит ярко",
    
    # Смешанные (для проверки)
    "кот большой спит",
    "пёс маленький бежит",
    "дом старый стоит",
]

print(f"📝 Тестовых предложений: {len(test_sentences)}")

# Создаём поле
lp = LivingPersonality(id="grammar_test", name="Тест грамматики", db_path=":memory:")

# Генератор мод через градиенты (упрощённая версия)
from collections import Counter

def compute_gradient(words1, words2):
    """Косинусное расстояние между наборами слов."""
    vec1 = Counter(words1)
    vec2 = Counter(words2)
    all_w = set(vec1.keys()) | set(vec2.keys())
    dot = sum(vec1.get(w, 0) * vec2.get(w, 0) for w in all_w)
    n1 = math.sqrt(sum(v**2 for v in vec1.values()))
    n2 = math.sqrt(sum(v**2 for v in vec2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return 1.0 - max(-1.0, min(1.0, dot / (n1 * n2)))

total_modes = 0
global_time = 0.0

for sent_idx, sentence in enumerate(test_sentences):
    words = sentence.lower().split()
    
    # Моды для каждого слова (слой 3-4)
    for i, word in enumerate(words):
        if i > 0:
            gradient = compute_gradient([words[i-1]], [word])
        else:
            gradient = 0.5
        
        tau = (len(word) * 2 + sum(ord(c) for c in word) % 20) % 40 + 2
        tau = tau * (1.0 + gradient)
        scale = 2.0 + gradient * 6.0
        amplitude = 0.3 + gradient * 0.4
        
        mode = SpectralMode(
            tau=tau, amplitude=amplitude, scale=scale,
            trace_id=f"word_{word}_{sent_idx}_{i}",
            creator="grammar_test",
            content=word,
            emotion=WaveformEmotion(amplitude=amplitude, base_emotion='neutral'),
            phase=math.pi * gradient,
        )
        mode.created_at = global_time + i * 0.1
        text_id = lp.text_store.store(word)
        mode.text_id = text_id
        lp.add_mode(mode)
        total_modes += 1
    
    # Мода для всего предложения (слой 6-7)
    gradient_full = compute_gradient(words[:1], words[-1:])
    tau = 30.0 + gradient_full * 20.0
    scale = 16.0 + gradient_full * 24.0
    
    mode = SpectralMode(
        tau=tau, amplitude=0.7, scale=scale,
        trace_id=f"sent_{sent_idx}",
        creator="grammar_test",
        content=sentence,
        emotion=WaveformEmotion(amplitude=0.7, base_emotion='neutral'),
        phase=0.0,
    )
    mode.created_at = global_time + 0.5
    text_id = lp.text_store.store(sentence)
    mode.text_id = text_id
    lp.add_mode(mode)
    total_modes += 1
    
    global_time += 1.0

print(f"✅ Создано мод: {total_modes}")
print(f"   Из них слов: {total_modes - len(test_sentences)}")
print(f"   Предложений: {len(test_sentences)}")

# Запускаем TEES на 20 циклов
print(f"\n🔄 Запуск TEES-обмена (20 циклов)...")
print(f"   Порог резонанса: {lp.resonance_threshold:.4f}")
print(f"   Гарм. допуск: {lp.harmonic_tolerance:.4f}")

total_transfers = 0
for cycle in range(20):
    result = lp.grow_step(dt=1.0)
    total_transfers += result['transfers']
    if result['transfers'] > 0:
        print(f"   Цикл {cycle+1}: {result['transfers']} переносов")

print(f"\n📊 После TEES:")
print(f"   Всего переносов: {total_transfers}")
print(f"   TEES попыток: {lp.stats['tees_attempts']}")
print(f"   TEES успехов: {lp.stats['tees_successes']}")

# Анализ: какие моды резонировали?
print(f"\n🔍 АНАЛИЗ СВЯЗЕЙ:")
print(f"   Ищем паттерны: прилагательное+существительное, существительное+глагол...")

# Сгруппируем моды по tau
from collections import defaultdict
tau_groups = defaultdict(list)
for mode in lp.get_all_modes():
    tau_rounded = round(mode.tau / 5) * 5  # группировка по 5
    tau_groups[tau_rounded].append(mode)

print(f"\n   Группы мод по tau (гармонические семьи):")
for tau, modes in sorted(tau_groups.items()):
    words = [m.content[:20] for m in modes[:5]]
    print(f"   tau≈{tau:5.0f}: {len(modes):2d} мод — {', '.join(words)}")

# Проверим эффективную энергию (должна быть выше у частых паттернов)
print(f"\n   Эффективная энергия мод (топ-10):")
sorted_modes = sorted(lp.get_all_modes(), key=lambda m: m.effective_energy, reverse=True)[:10]
for m in sorted_modes:
    print(f"   {m.content[:30]:30s} E={m.effective_energy:.3f} tau={m.tau:.1f} t={getattr(m,'created_at',0):.1f}")

print(f"\n✅ Тест грамматики завершён.")
print(f"   Если поле нашло паттерны — моды 'прилагательное' и 'существительное'")
print(f"   должны иметь близкие tau и высокую эффективную энергию.")