import sys
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

print("=" * 70)
print(" Я С ")
print("=" * 70)

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v2.json')

print(f"сего мод: {len(p.h_field)}")
print(f"сего слов (вихрей): {len(p.vortices)}")
print()

print("Ы 10  (блоков текста):")
print("-" * 70)

for i, mode in enumerate(p.h_field[:10]):
    print(f"\n[{i+1}] scale={mode.scale}, complexity={mode.complexity}, tau={mode.tau:.2f}")
    print(f"    content: {mode.content[:200]}")

print()
print("=" * 70)
print("Ы С Т 'dialogue':")
print("-" * 70)

dialogue_modes = [m for m in p.h_field if 'dialogue' in m.trace_id]
print(f"сего диалоговых мод: {len(dialogue_modes)}")

for i, mode in enumerate(dialogue_modes[:5]):
    print(f"\n[{i+1}] scale={mode.scale}, complexity={mode.complexity}")
    print(f"    content: {mode.content[:200]}")
