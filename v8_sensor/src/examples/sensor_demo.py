#!/usr/bin/env python3
"""
Sensor Demo — адаптация вектора из текста
"""

import sys
import os

# Добавляем путь к src
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
    
    mode1 = SpectralMode(
        tau=5.20,
        amplitude=0.6,
        content="Matter = Space. Particles are vortices in condensate. ∇⁴ψ = 0",
        trace_id="vmms_monism",
        themes=["physics", "vmms", "space"],
        creator="system"
    )
    p.add_to_h_field(mode1)
    
    mode2 = SpectralMode(
        tau=6.60,
        amplitude=0.6,
        content="Sulfur — energy, Mercury — flow, Salt — form. Alchemy is transformation.",
        trace_id="alchemy_manifesto",
        themes=["alchemy", "transformation", "symbol"],
        creator="system"
    )
    p.add_to_h_field(mode2)
    
    mode3 = SpectralMode(
        tau=8.21,
        amplitude=0.6,
        content="Grandson asks, grandfather answers. Questions create answers, answers create questions.",
        trace_id="grandson_01",
        themes=["dialogue", "learning", "wisdom"],
        creator="system"
    )
    p.add_to_h_field(mode3)
    
    # 3. Создаём адаптер
    print("\n📌 3. Создаём адаптер сенсоров...")
    adapter = VectorAdapter(p)
    print("   ✅ Адаптер готов")
    
    # 4. Демо: адаптация из текстов
    print("\n📌 4. Адаптация вектора из текстов...")
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
        print(f"   → Текущий вектор: τ={p.evolution_vector['target_tau']:.2f}, "
              f"темы={p.evolution_vector['target_themes']}")
    
    # 5. Запускаем эволюцию
    print("\n📌 5. Запускаем эволюционный цикл (5 шагов)...")
    p.run_evolution_cycle(steps=5)
    
    # 6. Итог
    print("\n" + "="*60)
    print("📊 ИТОГ")
    print("="*60)
    print(f" Финальный вектор: τ={p.evolution_vector['target_tau']:.2f}, "
          f"темы={p.evolution_vector['target_themes']}")
    print(f" Мод в поле H: {len(p.h_field)}")
    print(f" Адаптивный порог фуркации: {p._furcation_threshold:.2f}")
    
    # 7. Сохраняем
    print("\n📌 6. Сохраняем поле H...")
    save_path = os.path.join(os.path.dirname(__file__), '..', 'rizoma', 'data', 'personalities', 'sensor_learner.json')
    p.save(save_path)
    
    print("\n" + "="*60)
    print("✅ ДЕМО ЗАВЕРШЕНО!")
    print("\n🦌 Поле H адаптируется к входящим текстам.")
    print("   Вектор эволюции меняется в зависимости от прочитанного.")


if __name__ == "__main__":
    main()