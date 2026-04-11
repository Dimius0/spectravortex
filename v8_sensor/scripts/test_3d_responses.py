# scripts/test_3d_responses.py
import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality

p = Personality.load('src/rizoma/data/personalities/p016_full.json')

print("="*60)
print("🧪 ТЕСТ 3D-ПОЛЯ H (первая версия)")
print("="*60)
print(f"Мод: {len(p.h_field)}")
print(f"Слов: {len(p.word_spectrum)}")
print(f"Иерархия: {len(p.word_parent)} связей")
print()

questions = [
    "Что такое война?",
    "Что такое мир?",
    "Кто такой Наполеон?",
    "Что такое любовь?",
    "Почему Андрей Болконский пошёл на войну?",
]

for q in questions:
    print(f"❓ {q}")
    result = p.process(q)
    print(f"   Мода: {result['mode_used']} (τ={result['tau']:.2f}, δ={result['delta']:.2f}, θ={result['theta']:.2f})")
    print(f"   Ответ: {result['answer'][:300]}...")
    print()