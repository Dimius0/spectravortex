#!/usr/bin/env python3
"""
Voice Demo — голосовая адаптация поля H
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.personality import Personality, SpectralMode
from rizoma.sensor import VectorAdapter


def main():
    print("="*60)
    print("🌀 SPECTRAVORTEX — ГОЛОСОВАЯ АДАПТАЦИЯ")
    print("   Поле H слышит и реагирует")
    print("="*60)
    
    # 1. Создаём личность
    print("\n📌 1. Создаём личность...")
    p = Personality(id="voice_learner", name="Voice Learner")
    print("   ✅ Личность создана")
    
    # 2. Добавляем базовые моды
    print("\n📌 2. Добавляем базовые моды...")
    
    modes = [
        SpectralMode(5.20, 0.6, 
            "Matter = Space. Particles are vortices in quantum condensate.",
            "vmms_monism", ["physics", "vmms", "space"]),
        SpectralMode(6.60, 0.6,
            "Sulfur — energy, Mercury — flow, Salt — form. Alchemy is transformation.",
            "alchemy_manifesto", ["alchemy", "transformation", "symbol"]),
        SpectralMode(8.21, 0.6,
            "Grandson asks, grandfather answers. Questions create answers.",
            "grandson_01", ["dialogue", "learning", "wisdom"])
    ]
    
    for mode in modes:
        p.add_to_h_field(mode)
    
    # 3. Создаём адаптер с голосом
    print("\n📌 3. Создаём адаптер с голосом...")
    print("   (инициализация Whisper, может занять 5-10 сек)")
    adapter = VectorAdapter(p, whisper_model="base")
    print("   ✅ Адаптер готов")
    
    # 4. Меню
    print("\n" + "="*60)
    print("📋 МЕНЮ:")
    print("   1. Адаптация из текста")
    print("   2. Запись с микрофона (5 сек)")
    print("   3. Непрерывное прослушивание (скажите 'поле' для активации)")
    print("   4. Запустить эволюцию (5 шагов)")
    print("   5. Показать состояние поля H")
    print("   0. Выход")
    print("="*60)
    
    while True:
        try:
            choice = input("\n🔧 Выберите действие: ").strip()
            
            if choice == "1":
                text = input("📝 Введите текст: ")
                if text:
                    adapter.adapt_from_text(text)
            
            elif choice == "2":
                print("\n🎤 Запись 5 секунд...")
                adapter.adapt_from_microphone(duration=5.0, language="ru")
            
            elif choice == "3":
                print("\n🎤 Запуск непрерывного прослушивания...")
                print("   Скажите 'поле' для активации")
                print("   Нажмите Ctrl+C для возврата в меню")
                try:
                    adapter.continuous_listen(wake_word="поле", duration=3.0)
                except KeyboardInterrupt:
                    print("\n   Возврат в меню")
            
            elif choice == "4":
                print("\n🌀 Запуск эволюции (5 шагов)...")
                p.run_evolution_cycle(steps=5)
                print(f"\n📊 Поле H: {len(p.h_field)} мод")
            
            elif choice == "5":
                print(f"\n📊 СОСТОЯНИЕ ПОЛЯ H")
                print(f"   Мод: {len(p.h_field)}")
                print(f"   Вектор: τ={p.evolution_vector['target_tau']:.2f}, "
                      f"темы={p.evolution_vector['target_themes']}")
                print(f"   Порог фуркации: {p._furcation_threshold:.2f}")
                for mode in p.h_field[-3:]:
                    print(f"   - {mode.trace_id}: τ={mode.tau:.2f}, amp={mode.amplitude:.2f}")
            
            elif choice == "0":
                print("\n🦌 До свидания!")
                break
            
            else:
                print("   Неизвестная команда")
                
        except KeyboardInterrupt:
            print("\n🛑 Прервано")
            break
        except Exception as e:
            print(f"   ⚠️ Ошибка: {e}")


if __name__ == "__main__":
    main()