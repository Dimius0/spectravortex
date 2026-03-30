#!/usr/bin/env python3
"""
check_field.py — проверка состояния поля H после загрузки
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rizoma.personality import Personality

print("=" * 60)
print("📊 СОСТОЯНИЕ ПОЛЯ H")
print("=" * 60)

# Загружаем поле
p = Personality.load('src/rizoma/data/personalities/p016_full.json')

print(f"   Слов в поле: {len(p.vortices)}")
print(f"   Мод: {len(p.h_field)}")
print(f"   Символов в алфавите: {len(p.char_tau)}")
print(f"   Фокус: τ={p.focus['tau']:.2f}")
print()

# Распределение τ
tau_dist = {}
for word, vortex in p.vortices.items():
    tau = vortex.get_dominant_tau()
    if tau:
        tau_key = round(tau, 0)
        tau_dist[tau_key] = tau_dist.get(tau_key, 0) + 1

print("📈 Распределение τ (топ-10):")
for tau, count in sorted(tau_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
    bar = "█" * min(40, count // 200)
    print(f"   τ≈{tau:3.0f}: {count:6d} слов {bar}")

# Временные метки
print()
print("⏰ Временные метки (пример):")
sample_word = list(p.vortices.keys())[0]
sample_vortex = p.vortices[sample_word]
print(f"   Слово: {sample_word}")
if sample_vortex.created:
    print(f"   Создано: {sample_vortex.created.strftime('%Y-%m-%d %H:%M:%S')}")
if sample_vortex.last_updated:
    print(f"   Обновлено: {sample_vortex.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Использовано: {sample_vortex.usage_count} раз")
print(f"   Амплитуда: {sample_vortex.amplitude:.2f}")

# Адаптивный порог
print()
print("🔧 Адаптивный порог:")
print(f"   Текущий порог штампа: {p.threshold_stamp:.3f}")
print(f"   Мин: {p.threshold_stamp_min:.3f}")
print(f"   Макс: {p.threshold_stamp_max:.3f}")
if p.resonance_history:
    avg = sum(p.resonance_history) / len(p.resonance_history)
    print(f"   Средний резонанс: {avg:.3f}")
    print(f"   История резонансов: {len(p.resonance_history)} записей")

print()
print("✅ Проверка завершена")