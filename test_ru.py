import sys, os
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

print('агружаю личность...')
p = LivingPersonality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v4.json')

print(f'од в H-поле: {len(p.h_field)}')
print(f'ихрей: {len(p.vortices)}')

# усские вопросы
questions = [
    'то такое сплав иридия?',
    'ак дела?',
    'асскажи что-нибудь интересное',
    'ривет!',
    'акая температура плавления иридия?',
]

for q in questions:
    print(f'\n{"="*50}')
    print(f'👤: {q}')
    r = p.process(q)
    answer = r.get('answer', '?')
    print(f'🤖: {answer[:300]}')
    print(f'   [настроение: {r.get("mood", 0):+.2f}]')
