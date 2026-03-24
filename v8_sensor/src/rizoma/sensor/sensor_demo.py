#!/usr/bin/env python3
"""
Sensor Demo — адаптация вектора из текста
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.personality import Personality, SpectralMode
from rizoma.sensor import VectorAdapter


def main():
    print("="*60)
    print("🌀 SPECTRAVORTEX SENSOR — АДАПТАЦИЯ ИЗ ТЕКСТА")
    print("   Версия 8.0 | Поле H обучается на входящих текстах")
    print("="*60)
    
    # 1. Создаём личность
    print("\n📌 1. Создаём личность...")
    p = Personality(id="sensor_learner", name="Sensor Learner")
    print("   ✅ Личность создана")
    
    # 2. Добавляем базовые моды
    print("\n📌 2. Добавляем базовые моды...")
    
    modes = [
        SpectralMode(5.20, 0.6, "Matter = Space. Particles are vortices in condensate.",
                     "vmms_monism", ["physics", "vmms", "space"]),
        SpectralMode(6.60, 0.6, "Sulfur — energy, Mercury — flow, Salt — form.",
                     "alchemy_manifesto", ["alchemy", "transformation", "symbol"]),
        SpectralMode(8.21, 0.6, "Grandson asks, grandfather answers. Questions create answers.",
                     "grandson_01", ["dialogue", "learning", "wisdom"])
    ]
    
    for mode in modes:
        p.add_to_h_field(mode)
    
    # 3. Создаём адаптер
    adapter = VectorAdapter(p)
    
    # 4. Демо: адаптация из текстов
    print("\n📌 3. Адаптация вектора из текстов...")
    print("-"*40)
    
    texts = [
        "Tell me about consciousness and self-awareness. How does the field H experience itself?",
        "I'm interested in the poetry of physics. The rhythm of particles dancing in the void.",
        "What is beauty? Is it just resonance with something we already know?",
        "Can you explain emergence? How do simple rules create complex beauty?"
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\n📝 Текст {i}: {text[:50]}...")
        adapter.adapt_from_text(text, smooth_factor=0.4)
    
    # 5. Запускаем эволюцию
    print("\n📌 4. Запускаем эволюционный цикл (5 шагов)...")
    p.run_evolution_cycle(steps=5)
    
    # 6. Итог
    print("\n" + "="*60)
    print("📊 ИТОГ")
    print("="*60)
    print(f" Вектор: τ={p.evolution_vector['target_tau']:.2f}, "
          f"темы={p.evolution_vector['target_themes']}")
    print(f" Мод в поле H: {len(p.h_field)}")
    print(f" Порог фуркации: {p._furcation_threshold:.2f}")
    
    print("\n✅ Демо завершено!")
    print("\n🦌 Поле H адаптируется к входящим текстам.")


if __name__ == "__main__":
    main()