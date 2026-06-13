# test_grammar_v3.py — ЧЕСТНЫЙ тест: только слова, без разметки, много циклов
import sys, os, time, math, hashlib
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🧪 ТЕСТ ГРАММАТИКИ v3: ЧЕСТНЫЙ (без разметки, много циклов)")
print("=" * 60)

# Только предложения — без ролей!
test_sentences = [
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
    "кот спит тихо",
    "пёс бежит быстро",
    "дом стоит крепко",
    "ветер дует сильно",
    "конь скачет резво",
    "большой кот бежит",
    "маленький пёс спит",
    "старый дом цветёт",
    "новый день горит",
    "холодный чай греет",
]

CYCLES = 5000  # много циклов для релаксации

print(f"📝 Предложений: {len(test_sentences)}")
print(f"🔄 Циклов TEES: {CYCLES}")

# Создаём поле
lp = LivingPersonality(id="grammar_honest", name="Честная грамматика", db_path=":memory:")

def compute_gradient(w1, w2):
    """Градиент между двумя словами (упрощённый)."""
    if w1 == w2:
        return 0.0
    # Разные слова → градиент зависит от длины
    return abs(len(w1) - len(w2)) / max(len(w1), len(w2)) + 0.3

total_modes = 0
global_time = 0.0

for sent_idx, sentence in enumerate(test_sentences):
    words = sentence.lower().split()
    
    for i, word in enumerate(words):
        # Градиент относительно соседа
        if i > 0:
            gradient = compute_gradient(words[i-1], word)
        else:
            gradient = 0.5
        
        # tau — ТОЛЬКО из слова и его позиции, без ролей
        base_tau = (len(word) * 3 + sum(ord(c) for c in word[:3]) % 30) % 40 + 5
        tau = base_tau * (1.0 + gradient * 0.5)
        
        # scale — из позиции в предложении (первое слово = пониже, последнее = повыше)
        position_ratio = i / max(len(words) - 1, 1)
        scale = 2.0 + position_ratio * 10.0
        
        # amplitude — из длины слова и позиции
        amplitude = 0.2 + (len(word) / 15) + position_ratio * 0.3
        amplitude = max(0.1, min(0.8, amplitude))
        
        # Фаза — ТОЛЬКО из позиции в предложении
        phase = position_ratio * 2 * math.pi
        
        # Эмоция — нейтральная
        emotion = WaveformEmotion(amplitude=amplitude, base_emotion='neutral')
        
        mode = SpectralMode(
            tau=tau, amplitude=amplitude, scale=scale,
            trace_id=f"word_{word}_{sent_idx}_{i}",
            creator="honest_test",
            content=word,
            emotion=emotion,
            phase=phase,
        )
        mode.created_at = global_time + i * 0.1
        text_id = lp.text_store.store(word)
        mode.text_id = text_id
        lp.add_mode(mode)
        total_modes += 1
    
    global_time += 1.0

print(f"✅ Создано мод: {total_modes}")

# Запускаем МНОГО циклов TEES
print(f"\n🔄 Запуск TEES-обмена ({CYCLES} циклов)...")
print(f"   Порог резонанса: {lp.resonance_threshold:.4f}")
print(f"   Гарм. допуск: {lp.harmonic_tolerance:.4f}")

total_transfers = 0
last_report = 0
start = time.time()

for cycle in range(CYCLES):
    result = lp.grow_step(dt=0.1)
    total_transfers += result['transfers']
    
    # Отчёт каждые 500 циклов
    if (cycle + 1) % 500 == 0:
        elapsed = time.time() - start
        new_transfers = total_transfers - last_report
        print(f"   [{cycle+1}/{CYCLES}] transfers={total_transfers} (+{new_transfers}), "
              f"E={lp.energy:.3f}, emerged={lp.stats['emerged_modes']}, {elapsed:.0f}с")
        last_report = total_transfers

print(f"\n📊 После {CYCLES} циклов:")
print(f"   Всего переносов: {total_transfers}")
print(f"   TEES попыток: {lp.stats['tees_attempts']}")
print(f"   TEES успехов: {lp.stats['tees_successes']}")
print(f"   Эмерджентных мод: {lp.stats['emerged_modes']}")
print(f"   Время: {time.time() - start:.0f}с")

# АНАЛИЗ: кластеризация по tau
print(f"\n🔍 КЛАСТЕРИЗАЦИЯ ПО TAU (что поле само выделило):")

# Группируем моды по близким tau (окна по 5)
tau_groups = defaultdict(list)
for mode in lp.get_all_modes():
    if mode.creator == "honest_test":  # только слова
        tau_rounded = round(mode.tau / 5) * 5
        tau_groups[tau_rounded].append(mode)

print(f"\n   Группы мод по tau (гармонические семьи):")
for tau in sorted(tau_groups.keys()):
    modes = tau_groups[tau]
    words = list(set(m.content[:15] for m in modes))
    # Смотрим позиции этих слов
    positions = []
    for m in modes:
        # Извлекаем позицию из trace_id
        parts = m.trace_id.split('_')
        if len(parts) >= 3:
            positions.append(int(parts[-1]))
    avg_pos = sum(positions) / len(positions) if positions else 0
    print(f"   tau≈{tau:5.0f}: {len(modes):2d} мод, avg_pos={avg_pos:.1f} — {', '.join(sorted(words)[:5])}")

# Проверим: если прилагательные кластеризовались — они должны быть в одной группе tau
# и иметь близкие позиции (0 = первое слово)

print(f"\n   Анализ позиций:")
print(f"   Если прилагательные выделились — они должны быть в группах с avg_pos≈0")
print(f"   Если существительные выделились — они должны быть в группах с avg_pos≈1")
print(f"   Если глаголы выделились — они должны быть в группах с avg_pos≈2")

# Топ мод по эффективной энергии
print(f"\n   Топ-10 мод по энергии (после TEES):")
sorted_modes = sorted(
    [m for m in lp.get_all_modes() if m.creator == "honest_test"],
    key=lambda m: m.effective_energy, reverse=True
)[:10]
for m in sorted_modes:
    parts = m.trace_id.split('_')
    pos = int(parts[-1]) if len(parts) >= 3 else -1
    print(f"   {m.content[:15]:15s} E={m.effective_energy:.3f} tau={m.tau:.1f} pos={pos}")

print(f"\n✅ Честный тест завершён.")
print(f"   Если поле само выделило категории — слова одной роли")
print(f"   должны собраться в близкие группы tau и позиций.")