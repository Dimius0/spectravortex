import sys
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality
from collections import defaultdict

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_3_final_20260405_041917.json')
print(f'📂 агружено: {len(p.h_field)} мод')
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
print('🔬 Ы Ы (complexity=2) — Ы 10')
print('=' * 70)

scientific = by_complexity.get(2, [])
for i, mode in enumerate(scientific[:10]):
    print(f'[{i+1}] scale={mode.scale:.1f}, tau={mode.tau:.2f}')
    print(f'    {mode.content[:200]}...')
    print()

print('=' * 70)
print('💡 ТС Ы (complexity=4) — Ы 10')
print('=' * 70)

metaphors = by_complexity.get(4, [])
for i, mode in enumerate(metaphors[:10]):
    print(f'[{i+1}] scale={mode.scale:.1f}, tau={mode.tau:.2f}')
    print(f'    {mode.content[:200]}...')
    print()

print('=' * 70)
print('🧠 -Ы (complexity=3) — Ы 10')
print('=' * 70)

vmmp = by_complexity.get(3, [])
for i, mode in enumerate(vmmp[:10]):
    print(f'[{i+1}] scale={mode.scale:.1f}, tau={mode.tau:.2f}')
    print(f'    {mode.content[:200]}...')
    print()
