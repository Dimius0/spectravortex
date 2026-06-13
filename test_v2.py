import sys, os
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

print('='*60)
print('TEST WITH CORRECT TRAITS')
print('='*60)

p = LivingPersonality.load('src/rizoma/data/personalities/p016_grown_1h_v2.json')
print(f'Modes: {len(p.h_field)}, Vortices: {len(p.vortices)}')
print(f'Curiosity: {p.traits["curiosity"]:.2f}, Empathy: {p.traits["empathy"]:.2f}')
print()

questions = [
    'What is iridium alloy?',
    'How are you?',
    'Hello!',
    'Melting point of iridium?',
    'Tell me something interesting',
]

for q in questions:
    print('-'*50)
    print(f'Q: {q}')
    r = p.process(q)
    print(f'A: {r["answer"][:300]}')
    print(f'   [mood: {r.get("mood",0):+.2f}, type: {r.get("mode_type","?")}]')
