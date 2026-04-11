#!/usr/bin/env python3
"""
Тест 3D-поля H (физический слой)
"""
import sys
import json
sys.path.insert(0, 'src')
from rizoma.personality import FieldH, Vortex

print("="*60)
print("🌀 ТЕСТ 3D-ПОЛЯ H (физический слой)")
print("="*60)

# Загружаем поле напрямую
with open('src/rizoma/data/personalities/p016_physics_3d.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

p = FieldH()
for word, vdata in data.get("vortices", {}).items():
    p.vortices[word] = Vortex.from_dict(vdata)

print(f"Вихрей в поле: {len(p.vortices)}")
print(f"Средняя τ: {sum(v.tau for v in p.vortices.values())/len(p.vortices):.2f}")
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
    print(f"   Вихрь: {result.get('word_used', '?')}")
    print(f"   τ={result.get('tau', 0):.2f}, δ={result.get('delta', 0):.2f}, θ={result.get('theta', 0):.2f}")
    print(f"   Ответ: {result['answer'][:200]}...")
    print()

print("="*60)
print("✅ Тест завершён")