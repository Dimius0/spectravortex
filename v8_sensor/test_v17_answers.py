import sys
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

print("=" * 70)
print("🧪 ТСТ ТТ (копия поля v17.0)")
print("=" * 70)

# агружаем копию поля
p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_test.json')

stats = p.get_endogenous_stats()
print(f" злов: {stats.get('knots_created', 0)}")
print(f" од: {len(p.h_field)}")
print("=" * 70)

questions = [
    "то такое вихрь?",
    "ак работает память?",
]

for q in questions:
    print(f"\n❓ {q}")
    r = p.process(q)
    print(f"   ежим: {r.get('mode_type', '?')}")
    print(f"   езонанс: {r.get('resonance', 0):.3f}")
    print(f"   твет: {r.get('answer', '')[:400]}...")
    print("-" * 50)

print("\n✅ Тест завершён")
