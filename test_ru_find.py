import sys, os
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

p = LivingPersonality.load('src/rizoma/data/personalities/p016_grown_3h.json')

questions = [
    'Что такое ТЭЭС?',
    'Как работает эффект Юми?',
    'Расскажи про гравитацию',
    'Что такое ВММП?',
    'Кто такой Борис?',
]

for q in questions:
    mode, score, st = p._find_best_mode(q)
    content = getattr(mode, 'content', 'NO MODE') if mode else 'NO MODE'
    print(f'Q: {q}')
    print(f'  Score: {score:.3f} | Type: {st}')
    print(f'  Content: {content[:200]}')
    print()