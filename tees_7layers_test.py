import sys, os, time
sys.path.insert(0, 'src/architect')
from living_personality_v21_3_1 import LivingPersonality

print('=' * 60)
print('🌀 TEES НА 7 СЛОЯХ — 500 циклов')
print('=' * 60)

print('\n📂 Загружаю поле...')
start = time.time()
lp = LivingPersonality.load('src/rizoma/data/personalities/p016_7layers.json')
print(f'✅ Загрузка: {time.time() - start:.0f}с')

print(f'\n📊 Старт:')
print(f'   Мод: {len(lp.get_all_modes())}')
print(f'   Энергия поля: {lp.energy:.3f}')
print(f'   Порог резонанса: {lp.resonance_threshold:.4f}')

CYCLES = 500
print(f'\n🔄 TEES {CYCLES} циклов...')
start_tees = time.time()

for cycle in range(CYCLES):
    result = lp.grow_step(dt=0.1)
    
    if (cycle + 1) % 100 == 0:
        elapsed = time.time() - start_tees
        print(f'   [{cycle+1}/{CYCLES}] transfers={result["transfers"]}, flow={result["total_flow"]:.3f}, E={result["energy"]:.3f}, {elapsed:.0f}с')

print(f'\n⏱️  TEES: {time.time() - start_tees:.0f}с')

print(f'\n📊 После TEES:')
print(f'   Переносов: {lp.stats["cross_transfers"]}')
print(f'   Попыток: {lp.stats["tees_attempts"]}')
print(f'   Успехов: {lp.stats["tees_successes"]}')
print(f'   Эмерджентных: {lp.stats["emerged_modes"]}')

print(f'\n📊 Энергия по слоям после TEES:')
for layer_id in range(1, 8):
    layer_modes = [m for m in lp.get_all_modes() if m.layer == layer_id]
    if layer_modes:
        avg_e = sum(m.energy for m in layer_modes) / len(layer_modes)
        top3 = sorted(layer_modes, key=lambda m: -m.energy)[:3]
        top_words = [m.trace_id[:25] for m in top3]
        print(f'   Слой {layer_id}: avg E={avg_e:.4f} | топ: {top_words}')

print(f'\n✅ TEES на 7 слоях завершён!')