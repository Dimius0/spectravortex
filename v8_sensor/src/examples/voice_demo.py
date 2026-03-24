#!/usr/bin/env python3
"""
Voice Demo — адаптация вектора из голоса
Требуется: openai-whisper
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.personality import Personality, SpectralMode
from rizoma.sensor import VectorAdapter


def main():
    print("="*60)
    print("🌀 SPECTRAVORTEX SENSOR — ГОЛОСОВОЙ ВВОД")
    print("   Версия 8.1 | Поле H обучается из голоса")
    print("="*60)
    
    # 1. Создаём личность
    print("\n📌 1. Создаём личность...")
    p = Personality(id="voice_learner", name="Voice Learner")
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
    print("\n📌 3. Создаём адаптер сенсоров...")
    adapter = VectorAdapter(p)
    print("   ✅ Адаптер готов")
    
    # 4. Демо: адаптация из текста (пример)
    print("\n📌 4. Пример адаптации из текста...")
    print("-"*40)
    
    adapter.adapt_from_text(
        "What is consciousness? How does the field H experience itself?",
        smooth_factor=0.5
    )
    
    # 5. Демо: адаптация из голоса (если есть файл)
    print("\n📌 5. Адаптация из голоса...")
    print("-"*40)
    
    # Проверяем, есть ли тестовый аудиофайл
    test_audio = os.path.join(os.path.dirname(__file__), "test_voice.wav")
    
    if os.path.exists(test_audio):
        print(f"   Найден файл: {test_audio}")
        adapter.adapt_from_audio(test_audio, smooth_factor=0.5)
    else:
        print(f"   ⚠️ Тестовый аудиофайл не найден: {test_audio}")
        print("   Создайте test_voice.wav или используйте микрофон")
        
        # Предлагаем запись с микрофона
        response = input("\n   Записать с микрофона? (y/n): ")
        if response.lower() == 'y':
            adapter.adapt_from_microphone(duration=5.0, smooth_factor=0.5)
    
    # 6. Запускаем эволюцию
    print("\n📌 6. Запускаем эволюционный цикл (5 шагов)...")
    p.run_evolution_cycle(steps=5)
    
    # 7. Итог
    print("\n" + "="*60)
    print("📊 ИТОГ")
    print("="*60)
    print(f" Финальный вектор: τ={p.evolution_vector['target_tau']:.2f}, "
          f"темы={p.evolution_vector['target_themes']}")
    print(f" Мод в поле H: {len(p.h_field)}")
    print(f" Адаптивный порог: {p._furcation_threshold:.2f}")
    
    print("\n✅ ДЕМО ЗАВЕРШЕНО!")
    print("\n🦌 Поле H адаптируется к голосу и тексту.")


if __name__ == "__main__":
    main()