#!/usr/bin/env python3
"""
Тест ночного поля H (1247 узлов)
Загружает самое свежее автосохранение
"""
import sys
import os
import re
import time
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality

# Находим самое свежее автосохранение
auto_saves = glob.glob(os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v16_auto_*.json'))
if not auto_saves:
    print("❌ Нет автосохранений!")
    sys.exit(1)

# Берём самое свежее (по имени файла, где дата)
latest = max(auto_saves, key=lambda x: x)
print(f"📂 Загружаем: {os.path.basename(latest)}")

p = Personality.load(latest)
stats = p.get_endogenous_stats()

print("=" * 70)
print("🧪 ТЕСТ НОЧНОГО ПОЛЯ H")
print("=" * 70)
print(f" Слов: {len(p.vortices)}")
print(f" Мод: {len(p.h_field)}")
print(f" Узлов: {stats.get('knots_created', 0)}")
print(f" Фуркаций: {stats.get('furcations', 0)}")
print(f" Кросс-резонансов: {stats.get('cross_resonances', 0)}")
print()

# Научные вопросы
questions = [
    "Что такое вихрь?",
    "Что такое квантовая запутанность?",
    "Как работает память?",
    "Объясни теорию относительности",
    "Что такое фрактал?",
]

print("=" * 70)
print("🔬 НАУЧНЫЕ ВОПРОСЫ")
print("=" * 70)

for q in questions:
    print(f"\n❓ {q}")
    start = time.time()
    r = p.process(q)
    elapsed = (time.time() - start) * 1000
    print(f"   Режим: {r.get('mode_type', '?')}")
    print(f"   Резонанс: {r.get('resonance', 0):.3f}")
    print(f"   Время: {elapsed:.0f} мс")
    print(f"   Масштаб: {r.get('mode_scale', '?')}")
    print(f"   Ответ: {r.get('answer', '')[:400]}...")

# Бытовые вопросы
everyday = ["привет", "как дела", "спасибо", "пока"]

print("\n" + "=" * 70)
print("💬 БЫТОВЫЕ ВОПРОСЫ")
print("=" * 70)

for q in everyday:
    print(f"\n❓ {q}")
    r = p.process(q)
    print(f"   Режим: {r.get('mode_type', '?')}")
    print(f"   Ответ: {r.get('answer', '')}")

print("\n" + "=" * 70)
print("✅ ТЕСТ ЗАВЕРШЁН")
print("=" * 70)