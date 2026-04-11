import sys
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_20260404_210354.json')

print("=" * 70)
print("📊 СТТ Я H v17.0")
print("=" * 70)
print(f"Слов (вихрей): {len(p.vortices)}")
print(f"од (блоков текста): {len(p.h_field)}")
if hasattr(p.resonance_engine, "topology"):
    print(f"злов (топологических связей): {len(p.resonance_engine.topology.nodes)}")
print()

scale_stats = {}
for mode in p.h_field:
    s = mode.scale
    scale_stats[s] = scale_stats.get(s, 0) + 1

print("📐 С  СШТ:")
for s in sorted(scale_stats.keys()):
    print(f"  scale={s:5.1f}: {scale_stats[s]:6d} мод")

comp_stats = {}
for mode in p.h_field:
    c = mode.complexity
    comp_stats[c] = comp_stats.get(c, 0) + 1

print()
print("📚 С  COMPLEXITY:")
names = {1: "бытовой", 2: "научный", 3: "", 4: "метафорический"}
for c in sorted(comp_stats.keys()):
    print(f"  complexity={c} ({names.get(c, '?'):12}): {comp_stats[c]:6d} мод")

print()
print("🔍 Ы  (первые 5):")
for i, mode in enumerate(p.h_field[:5]):
    print(f"  [{i+1}] scale={mode.scale}, complexity={mode.complexity}, tau={mode.tau:.2f}")
    print(f"      content: {mode.content[:100]}...")
