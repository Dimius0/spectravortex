#!/usr/bin/env python3
"""
Тест ответов поля H на нестандартные вопросы
"""
import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality

p = Personality.load('src/rizoma/data/personalities/p016_full.json')
print(f'Поле H: {len(p.h_field)} мод, {len(p.word_tau)} слов\n')

questions = [
    'Что такое любовь?',
    'Как объяснить квантовую физику ребёнку?',
    'Почему трава зелёная?',
    'Что будет, если разделить атом?',
    'Есть ли душа у камня?',
    'Почему мы улыбаемся, когда грустно?',
    'Как работает память?',
    'Что такое красота?'
]

for q in questions:
    print(f'❓ {q}')
    result = p.process(q)
    print(f'   Мода: {result["mode_used"]} (τ={result["tau"]:.2f})')
    print(f'   Ответ: {result["answer"][:300]}...')
    print()