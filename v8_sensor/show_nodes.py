import sys
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality
import glob
import os
from collections import defaultdict

# агружаем последнее финальное сохранение
files = glob.glob('src/rizoma/data/personalities/p016_fractal_v17_4_final_*.json')
if files:
    latest = max(files, key=os.path.getctime)
    p = Personality.load(latest)
    print(f'📂 агружено: {os.path.basename(latest)}')
else:
    files2 = glob.glob('src/rizoma/data/personalities/p016_fractal_v17_4_autosave.json')
    if files2:
        p = Personality.load(files2[0])
        print(f'📂 агружено: автосохранение')
    else:
        print('❌ е найдено сохранений!')
        exit(1)

print(f'📊 сего мод: {len(p.h_field)}')
print()

by_complexity = defaultdict(list)
for mode in p.h_field:
    by_complexity[mode.complexity].append(mode)

print('=' * 70)
print('📊 СТТСТ   COMPLEXITY')
print('=' * 70)
for c in sorted(by_complexity.keys()):
    name = {1: 'бытовой', 2: 'научный', 3: '', 4: 'метафорический'}.get(c, '?')
    print(f'   complexity={c} ({name:12}): {len(by_complexity[c]):6d} мод')

print()
print('=' * 70)
print('🔬 Ы Ы (complexity=2) — Ы 15')
print('=' * 70)

scientific = by_complexity.get(2, [])
print(f'сего научных мод: {len(scientific)}')
print()

for i, mode in enumerate(scientific[:15]):
    print(f'[{i+1}] scale={mode.scale:.1f}, tau={mode.tau:.2f}')
    print(f'    {mode.content[:300]}...')
    print()

print('=' * 70)
print('💡 ТС Ы (complexity=4) — Ы 15')
print('=' * 70)

metaphors = by_complexity.get(4, [])
print(f'сего метафорических мод: {len(metaphors)}')
print()

for i, mode in enumerate(metaphors[:15]):
    print(f'[{i+1}] scale={mode.scale:.1f}, tau={mode.tau:.2f}')
    print(f'    {mode.content[:300]}...')
    print()

print('=' * 70)
print('🧠 -Ы (complexity=3) — Ы 15')
print('=' * 70)

vmmp = by_complexity.get(3, [])
print(f'сего -мод: {len(vmmp)}')
print()

for i, mode in enumerate(vmmp[:15]):
    print(f'[{i+1}] scale={mode.scale:.1f}, tau={mode.tau:.2f}')
    print(f'    {mode.content[:300]}...')
    print()
