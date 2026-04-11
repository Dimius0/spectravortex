#!/usr/bin/env python3
"""
Тест ответов поля H (физический слой)
"""
import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality

print("="*60)
print("🧪 ТЕСТ ОТВЕТОВ ПОЛЯ H (физический слой)")
print("="*60)

p = Personality.load('src/rizoma/data/personalities/p016_physics_3d.json')
print(f"Вихрей: {len(p.vortices)}")
print(f"Мод: {len(p.h_field)}")
print()

questions = [
    'Что такое вихрь?',
    'Что такое квантовый конденсат?',
    'Что такое ∇⁴ψ = 0?',
    'Как работает фуркация?',
    'Что такое поле H?'
]

for q in questions:
    print(f"❓ {q}")
    result = p.process(q)
    print(f"   Мода: {result['mode_used']} (τ={result['tau']:.2f})")
    print(f"   Ответ: {result['answer'][:300]}...")
    print()

print("="*60)
print("✅ Тест завершён")