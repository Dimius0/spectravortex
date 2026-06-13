# grow_dialogues_field.py — TEES-рост на поле из диалогов
import sys, os, time, math, hashlib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, LAYER_BOUNDARIES, MIN_ENERGY, TAU_LIFE
)

print("=" * 60)
print("🌀 TEES-РОСТ: поле из 279K мод (наши диалоги)")
print("=" * 60)

INPUT_FILE = 'src/rizoma/data/personalities/p016_dialogues_full.json'
OUTPUT_FILE = INPUT_FILE.replace('.json', '_grown.json')

print(f"📂 Загружаю поле...")
start = time.time()
lp = LivingPersonality.load(INPUT_FILE)
print(f"✅ Загрузка: {time.time() - start:.0f}с")

print(f"\n📊 Старт:")
print(f"   Мод: {len(lp.get_all_modes())}")
print(f"   Энергия: {lp.energy:.3f}")
print(f"   Порог резонанса: {lp.resonance_threshold:.4f}")
print(f"   Порог фуркации: {lp.emerge_threshold:.4f}")
print(f"   Гарм. допуск: {lp.harmonic_tolerance:.4f}")
print(f"   Разведчиков: {lp.num_scouts}")
print(f"   Макс фуркаций: {lp.max_furcations}")

# Параметры роста
CYCLES = 5000
print(f"\n🔄 Запуск TEES ({CYCLES} циклов)...")
print(f"   Каждые 500 циклов — отчёт")

total_transfers = 0
start_tees = time.time()

for cycle in range(CYCLES):
    result = lp.grow_step(dt=0.1)
    total_transfers += result['transfers']
    
    if (cycle + 1) % 500 == 0:
        elapsed = time.time() - start_tees
        print(f"   [{cycle+1}/{CYCLES}] transfers={total_transfers}, E={lp.energy:.3f}, "
              f"scouts={result['scouts']}, pairs={result['pairs_found']}, {elapsed:.0f}с")

print(f"\n📊 После TEES ({CYCLES} циклов):")
print(f"   Всего переносов: {total_transfers}")
print(f"   TEES попыток: {lp.stats['tees_attempts']}")
print(f"   TEES успехов: {lp.stats['tees_successes']}")
print(f"   Эмерджентных мод: {lp.stats['emerged_modes']}")
print(f"   Энергия: {lp.energy:.3f}")
print(f"   Время: {time.time() - start_tees:.0f}с")

# Топ мод по энергии (после TEES)
print(f"\n🔍 Топ-20 мод по эффективной энергии (после TEES):")
sorted_modes = sorted(lp.get_all_modes(), key=lambda m: m.effective_energy, reverse=True)[:20]
for i, m in enumerate(sorted_modes):
    print(f"   {i+1:2d}. {m.content[:30]:30s} E={m.effective_energy:.4f} tau={m.tau:.1f} layer={m.layer}")

# Сохраняем
print(f"\n💾 Сохраняю...")
lp.save(OUTPUT_FILE)
print(f"✅ Сохранено: {OUTPUT_FILE}")
print(f"   Размер: {os.path.getsize(OUTPUT_FILE) / 1024**2:.0f} МБ")

print(f"\n✅ TEES-рост завершён!")