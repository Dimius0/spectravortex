import sys
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_1.json')

questions = [
    'то такое вихрь?',
    'ак работает квантовая запутанность?',
    'ак устроена память?',
    'бъясни теорию относительности',
]

for q in questions:
    print(f'\n❓ {q}')
    r = p.process(q)
    print(f'   ежим: {r.get("mode_type", "?")}')
    print(f'   езонанс: {r.get("resonance", 0):.3f}')
    print(f'   Complexity: {r.get("mode_complexity", "?")}')
    print(f'   твет: {r.get("answer", "")[:300]}...')
