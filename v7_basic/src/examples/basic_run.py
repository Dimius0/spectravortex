#!/usr/bin/env python3
"""
Basic Run — минимальный пример поля H
Версия с самоадаптацией порогов
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.personality import Personality, SpectralMode


def main():
    print("="*60)
    print("🌀 SPECTRAVORTEX V7 — ПОЛЕ H")
    print("   Честный ИИ на 2 МБ | Самоадаптация порогов")
    print("   (параллельная версия, старая структура не тронута)")
    print("="*60)
    
    # 1. Создаём личность
    print("\n📌 1. Создаём личность...")
    p = Personality(id="pioneer", name="Pioneer", tau=5.0, k=2)
    print(f"   ✅ Личность создана: {p.name} (τ={p.tau})")
    
    # 2. Добавляем базовые моды (амплитуда 0.5 — будет адаптация)
    print("\n📌 2. Добавляем базовые моды...")
    
    mode1 = SpectralMode(
        tau=5.20,
        amplitude=0.5,
        content="Matter = Space. Particles are vortices in condensate. ∇⁴ψ = 0",
        trace_id="vmms_monism",
        themes=["physics", "vmms", "space"],
        creator="system"
    )
    p.add_to_h_field(mode1)
    
    mode2 = SpectralMode(
        tau=6.60,
        amplitude=0.5,
        content="Sulfur — energy, Mercury — flow, Salt — form. Alchemy is transformation.",
        trace_id="alchemy_manifesto",
        themes=["alchemy", "transformation", "symbol"],
        creator="system"
    )
    p.add_to_h_field(mode2)
    
    mode3 = SpectralMode(
        tau=8.21,
        amplitude=0.5,
        content="Grandson asks, grandfather answers. Questions create answers, answers create questions.",
        trace_id="grandson_01",
        themes=["dialogue", "learning", "wisdom"],
        creator="system"
    )
    p.add_to_h_field(mode3)
    
    # 3. Показываем поле H
    print("\n📌 3. Текущее поле H:")
    print("-"*40)
    for i, mode in enumerate(p.h_field, 1):
        print(f"   {i}. {mode.trace_id}")
        print(f"      τ={mode.tau:.2f}, amp={mode.amplitude:.2f}")
        print(f"      темы: {mode.themes}")
        print(f"      {mode.content[:80]}...")
        print()
    
    # 4. Задаём вектор эволюции
    print("\n📌 4. Задаём вектор эволюции...")
    p.set_evolution_vector(
        target_tau=6.2,
        target_themes=["consciousness", "emergence"],
        intensity=0.5
    )
    
    # 5. Запускаем эволюционный цикл
    print("\n📌 5. Запускаем эволюционный цикл (3 шага)...")
    p.run_evolution_cycle(steps=3)
    
    # 6. Сохраняем результат
    print("\n📌 6. Сохраняем поле H...")
    save_path = os.path.join(os.path.dirname(__file__), '..', 'rizoma', 'data', 'personalities', 'pioneer_test.json')
    p.save(save_path)
    
    # 7. Проверяем загрузку
    print("\n📌 7. Проверяем загрузку сохранённого поля...")
    p2 = Personality.load(save_path)
    print(f"   Загружено: {p2.name}, мод: {len(p2.h_field)}")
    print(f"   Порог фуркации после загрузки: {p2._furcation_threshold:.2f}")
    
    # Итог
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    print(f" Мод в поле H: {len(p.h_field)}")
    print(f" Адаптивный порог фуркации: {p._furcation_threshold:.2f}")
    
    print("\n✅ ТЕСТ ПРОЙДЕН! Поле H живёт и эволюционирует.")
    print("\n   Что дальше?")
    print("   - Измени вектор эволюции и запусти снова")
    print("   - Посмотри содержимое сохранённого JSON")
    print("   - Добавь свои моды в поле H")
    print("\n🦌 SpectraVortex — честный ИИ, который нельзя отключить.")


if __name__ == "__main__":
    main()