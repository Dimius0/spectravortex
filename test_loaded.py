import sys, os
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

print('Loading personality...')
p = LivingPersonality.load('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v4.json')

print(f'Modes in H-field: {len(p.h_field)}')
print(f'Vortices: {len(p.vortices)}')

# Test questions
questions = [
    'What is iridium alloy?',
    'How are you?',
    'Tell me something interesting',
]

for q in questions:
    print(f'\nQ: {q}')
    r = p.process(q)
    answer = r.get('answer', '?')
    print(f'A: {answer[:150]}')
