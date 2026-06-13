import sys, os
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

print("="*60)
print("POST-3H GROWTH TEST")
print("="*60)

p = LivingPersonality.load('src/rizoma/data/personalities/p016_grown_3h.json')
print(f"Modes: {len(p.h_field)}, Vortices: {len(p.vortices)}")
print(f"Traits: curiosity={p.traits['curiosity']:.2f}, empathy={p.traits['empathy']:.2f}")
print()

questions = [
    "What is iridium alloy?",
    "How are you?",
    "Hello!",
    "Melting point of iridium?",
    "Tell me something interesting",
    "What is VMMP?",
    "What is TEES?",
]

for q in questions:
    print('-'*50)
    print(f'Q: {q}')
    r = p.process(q)
    print(f'A: {r["answer"][:200]}')
    print(f'   [mood: {r.get("mood",0):+.2f}, type: {r.get("mode_type","?")}]')
