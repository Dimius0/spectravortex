import sys, os
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

p = LivingPersonality.load('src/rizoma/data/personalities/p016_grown_3h.json')

# Тестируем _find_best_mode
questions = [
    'What is TEES?',
    'How does the Yumi effect work?',
    'Tell me about gravity',
    'What is VMMP?',
]

for q in questions:
    mode, score, st = p._find_best_mode(q)
    content = getattr(mode, 'content', '?') if mode else 'NO MODE FOUND'
    print(f'Q: {q}')
    print(f'  Score: {score:.3f} | Type: {st}')
    print(f'  Content: {content[:150]}')
    print()
