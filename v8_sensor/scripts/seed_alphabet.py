#!/usr/bin/env python3
"""
Инициализация базового алфавита
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')

print("="*70)
print("🎵 ИНИЦИАЛИЗАЦИЯ АЛФАВИТА")
print("="*70)

# Создаём поле
p = Personality(id="p016", name="VMMS Field")

print(f"\n✨ Создано поле")
print(f"   Базовый алфавит: {len(p.char_tau)} букв (τ=1..33)")

# Показываем алфавит
print("\n📖 Базовый алфавит:")
for ch, tau in sorted(p.char_tau.items(), key=lambda x: x[1])[:33]:
    print(f"   {ch} → τ={tau}")

# Сохраняем
p.save(OUTPUT_PATH)
print(f"\n💾 Сохранено в: {OUTPUT_PATH}")
print("\n✅ Готово. Можно загружать тексты.")