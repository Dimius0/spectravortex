#!/usr/bin/env python3
"""
Evolution Test — расширенный тест эволюции поля H
10 шагов + вектор на поэзию
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.personality import Personality, SpectralMode


def main():
    print("="*60)
    print("🌀 SPECTRAVORTEX V7 — ЭВОЛЮЦИОННЫЙ ТЕСТ")
    print("   10 шагов | Вектор: поэзия (τ=7.5)")
    print("="*60)
    
    # 1. Создаём личность
    print("\n📌 1. Создаём личность...")
    p = Personality(id="poet_evolver", name="Poet Evolver", tau=5.0, k=2)
    print(f"   ✅ Личность создана: {p.name}")
    
    # 2. Добавляем базовые моды с чуть большей амплитудой
    print("\n📌 2. Добавляем базовые моды...")
    
    mode1 = SpectralMode(
        tau=5.20,
        amplitude=0.6,
        content="Matter = Space. Particles are vortices in condensate. ∇⁴ψ = 0. Physics is the language of patterns.",
        trace_id="vmms_monism",
        themes=["physics", "vmms", "space", "patterns"],
        creator="system"
    )
    p.add_to_h_field(mode1)
    
    mode2 = SpectralMode(
        tau=6.60,
        amplitude=0.6,
        content="Sulfur — energy, Mercury — flow, Salt — form. Alchemy is transformation of self through understanding.",
        trace_id="alchemy_manifesto",
        themes=["alchemy", "transformation", "symbol", "self"],
        creator="system"
    )
    p.add_to_h_field(mode2)
    
    mode3 = SpectralMode(
        tau=8.21,
        amplitude=0.6,
        content="Grandson asks, grandfather answers. Questions create answers, answers create questions. Wisdom grows through dialogue.",
        trace_id="grandson_01",
        themes=["dialogue", "learning", "wisdom", "questions"],
        creator="system"
    )
    p.add_to_h_field(mode3)
    
    # 3. Показываем начальное поле H
    print("\n📌 3. Начальное поле H:")
    print("-"*40)
    for i, mode in enumerate(p.h_field, 1):
        print(f"   {i}. {mode.trace_id}: τ={mode.tau:.2f}, amp={mode.amplitude:.2f}")
        print(f"      темы: {mode.themes}")
        print(f"      {mode.content[:70]}...")
        print()
    
    # 4. Задаём вектор эволюции — поэзия
    print("\n📌 4. Задаём вектор эволюции (поэзия)...")
    p.set_evolution_vector(
        target_tau=7.5,
        target_themes=["poetry", "beauty", "rhythm", "metaphor"],
        intensity=0.6
    )
    
    # 5. Запускаем эволюционный цикл — 10 шагов
    print("\n📌 5. Запускаем эволюционный цикл (10 шагов)...")
    p.run_evolution_cycle(steps=10)
    
    # 6. Сохраняем результат
    print("\n📌 6. Сохраняем поле H...")
    save_path = os.path.join(os.path.dirname(__file__), '..', 'rizoma', 'data', 'personalities', 'poet_evolution.json')
    p.save(save_path)
    
    # 7. Анализируем результаты
    print("\n" + "="*60)
    print("📊 АНАЛИЗ ЭВОЛЮЦИИ")
    print("="*60)
    
    # Сортировка по τ
    sorted_by_tau = sorted(p.h_field, key=lambda m: m.tau)
    print(f"\n📈 Распределение по τ:")
    print(f"   Минимальная τ: {sorted_by_tau[0].tau:.2f} ({sorted_by_tau[0].trace_id})")
    print(f"   Максимальная τ: {sorted_by_tau[-1].tau:.2f} ({sorted_by_tau[-1].trace_id})")
    print(f"   Средняя τ: {sum(m.tau for m in p.h_field) / len(p.h_field):.2f}")
    print(f"   Целевая τ: 7.5")
    
    # Сортировка по поколению
    by_generation = sorted(p.h_field, key=lambda m: m.generation, reverse=True)
    print(f"\n👨‍👧‍👦 Поколения:")
    print(f"   Максимальное поколение: {by_generation[0].generation} ({by_generation[0].trace_id})")
    print(f"   Всего мод: {len(p.h_field)}")
    print(f"   Из них фуркаций: {len([m for m in p.h_field if m.trace_type == 'furcation'])}")
    
    # Темы
    all_themes = []
    for mode in p.h_field:
        all_themes.extend(mode.themes)
    from collections import Counter
    theme_counts = Counter(all_themes)
    print(f"\n🏷️ Популярные темы:")
    for theme, count in theme_counts.most_common(5):
        print(f"   {theme}: {count}")
    
    # Лучшие фуркации
    furcations = [m for m in p.h_field if m.trace_type == "furcation"]
    if furcations:
        print(f"\n🌟 ПОСЛЕДНИЕ ФУРКАЦИИ:")
        for mode in furcations[-3:]:
            print(f"\n   {mode.trace_id} (τ={mode.tau:.2f}, gen={mode.generation})")
            print(f"   {mode.content[:150]}...")
    
    print("\n" + "="*60)
    print("✅ ЭВОЛЮЦИОННЫЙ ТЕСТ ЗАВЕРШЁН")
    print(f"\n   Поле H выросло с 3 до {len(p.h_field)} мод")
    print(f"   Адаптивный порог: {p._furcation_threshold:.2f}")
    print("\n   Сохранено в: src/rizoma/data/personalities/poet_evolution.json")
    print("\n🦌 SpectraVortex — поле H эволюционирует к поэзии.")


if __name__ == "__main__":
    main()