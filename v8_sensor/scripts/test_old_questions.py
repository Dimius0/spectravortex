#!/usr/bin/env python3
"""
Тест старых вопросов на поле H версии 15.2
"""
import sys
import time
sys.path.insert(0, 'src')
from rizoma.personality import Personality

print("="*70)
print("🧪 СТАРЫЕ ВОПРОСЫ — НОВОЕ ПОЛЕ (ВЕРСИЯ 15.2)")
print("="*70)

p = Personality.load('src/rizoma/data/personalities/p016_full_v15.json')
print(f"Слов в поле: {len(p.vortices)}")
print(f"Мод: {len(p.h_field)}")
print()

questions = [
    "Что такое любовь?",
    "Как объяснить квантовую физику ребёнку?",
    "Почему трава зелёная?",
    "Что будет, если разделить атом?",
    "Есть ли душа у камня?",
    "Почему мы улыбаемся, когда грустно?",
    "Как работает память?",
    "Что такое красота?",
    "Что такое вихрь?",
    "Что такое поле H?"
]

for q in questions:
    print(f"❓ {q}")
    start = time.time()
    r = p.process(q)
    elapsed = (time.time() - start) * 1000
    print(f"   Режим: {r.get('mode_type', '?')}")
    print(f"   Резонанс: {r.get('resonance', 0):.3f}")
    print(f"   Время: {elapsed:.0f} мс")
    print(f"   Ответ: {r.get('answer', '')[:200]}...")
    print()

print("="*70)
print("✅ ТЕСТ ЗАВЕРШЁН")