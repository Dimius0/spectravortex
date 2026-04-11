#!/usr/bin/env python3
"""
Тест поля H версии 15.2
- Природные штампы (резонансные)
- Накопление уточнений
- Энергетическая экономия
- Квантовая аналогия
- Топология
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality


def print_separator(title: str = None):
    print("\n" + "="*70)
    if title:
        print(f" {title}")
        print("="*70)


def test_stamps(p):
    """Тест 1: Природные штампы"""
    print_separator("📦 ТЕСТ 1: ПРИРОДНЫЕ ШТАМПЫ")
    
    questions = [
        "привет",
        "как дела",
        "как твои дела",
        "что нового",
        "спасибо",
        "извини",
        "пока"
    ]
    
    for q in questions:
        print(f"\n❓ {q}")
        start = time.time()
        r = p.process(q, "test_user")
        elapsed = (time.time() - start) * 1000
        print(f"   Режим: {r['mode_type']}")
        print(f"   Энергия: {r.get('energy_cost', 0):.2f}")
        print(f"   Время: {elapsed:.0f} мс")
        print(f"   Ответ: {r['answer']}")


def test_dialog_memory(p):
    """Тест 2: Накопление уточнений"""
    print_separator("💬 ТЕСТ 2: НАКОПЛЕНИЕ УТОЧНЕНИЙ")
    
    dialog = [
        ("test_user", "Что такое ризома?"),
        ("test_user", "Это как корневая система, где нет главного корня, всё связано со всем"),
        ("test_user", "А как это связано с философией?"),
        ("test_user", "А в биологии?"),
    ]
    
    for user, q in dialog:
        print(f"\n❓ {q}")
        r = p.process(q, user)
        print(f"   Режим: {r['mode_type']}")
        print(f"   Ответ: {r['answer'][:200]}...")


def test_resonance(p):
    """Тест 3: Резонанс с разными словами"""
    print_separator("🎵 ТЕСТ 3: РЕЗОНАНС")
    
    words = ["вихрь", "поле", "война", "мир", "любовь", "ризома", "голограмма"]
    
    print("\n   Слово            Резонанс")
    print("   " + "-"*35)
    
    for w in words:
        res = p.resonate(w)
        bar = "█" * int(res * 30)
        print(f"   {w:15} {res:.3f}  {bar}")


def test_quantum(p):
    """Тест 4: Квантовая аналогия"""
    print_separator("🌀 ТЕСТ 4: КВАНТОВАЯ АНАЛОГИЯ")
    
    # Создаём суперпозицию
    meanings = ["волна", "колебание", "резонанс", "ритм"]
    p.create_superposition("вибрация", meanings)
    
    print(f"\n   Создана суперпозиция для 'вибрация'")
    print(f"   Возможные смыслы: {meanings}")
    
    # Коллапс в разных контекстах
    contexts = ["музыка", "физика", "повседневность"]
    for ctx in contexts:
        chosen = p.collapse("вибрация", ctx)
        print(f"   Коллапс в контексте '{ctx}' → '{chosen}'")
    
    # Запутанность
    p.entangle("вихрь", "поле")
    print(f"\n   Запутаны 'вихрь' и 'поле'")
    
    state1 = p.resonance_engine.quantum.states.get("вихрь")
    state2 = p.resonance_engine.quantum.states.get("поле")
    if state1 and state2:
        print(f"   'вихрь' запутан с: {list(state1.entanglement_partners)}")
        print(f"   'поле' запутан с: {list(state2.entanglement_partners)}")


def test_topology(p):
    """Тест 5: Топология"""
    print_separator("🧬 ТЕСТ 5: ТОПОЛОГИЯ")
    
    # Создаём узел
    knot = p.create_knot(["вихрь", "поле", "резонанс"])
    print(f"\n   Создан топологический узел:")
    print(f"   ID: {knot.id[:20]}...")
    print(f"   Тип: {knot.knot_type.value}")
    print(f"   Слова: {knot.words}")
    print(f"   Число пересечений: {knot.crossing_number}")
    
    # Создаём петлю
    loop = p.resonance_engine.topology.create_loop("вихрь")
    print(f"\n   Создана топологическая петля для 'вихрь'")
    print(f"   Длина пути: {loop.length:.2f}")


def test_energy(p):
    """Тест 6: Энергетический бюджет"""
    print_separator("⚡ ТЕСТ 6: ЭНЕРГЕТИЧЕСКИЙ БЮДЖЕТ")
    
    print(f"\n   Начальная энергия: {p.energy_budget:.2f}")
    
    # Быстрые вопросы (штампы)
    stamps = ["привет", "как дела", "спасибо", "пока"]
    for q in stamps:
        r = p.process(q, "energy_user")
        print(f"   '{q}' → затрачено: {r.get('energy_cost', 0):.2f}")
    
    print(f"\n   Энергия после штампов: {p.energy_budget:.2f}")
    
    # Восстановление
    p._regen_energy(0.5)
    print(f"   После восстановления: {p.energy_budget:.2f}")


def test_state(p):
    """Тест 7: Состояние поля"""
    print_separator("📊 ТЕСТ 7: СОСТОЯНИЕ ПОЛЯ")
    
    print(f"\n   Слов в поле: {len(p.vortices)}")
    print(f"   Квантовых состояний: {len(p.resonance_engine.quantum.states)}")
    print(f"   Топологических узлов: {len(p.resonance_engine.topology.nodes)}")
    print(f"   Топологических петель: {len(p.resonance_engine.topology.loops)}")
    print(f"   Солитонов: {len(p.resonance_engine.nonlinear.solitons)}")
    print(f"   Мод: {len(p.h_field)}")
    print(f"   Энергия: {p.energy_budget:.2f}")
    
    # Первые 10 слов
    print("\n   Первые 10 слов в поле:")
    for i, (word, vortex) in enumerate(list(p.vortices.items())[:10]):
        tau = vortex.get_dominant_tau()
        print(f"      {i+1}. {word} (τ={tau:.2f})")


def main():
    print("="*70)
    print("🧪 ТЕСТ ПОЛЯ H (ВЕРСИЯ 15.2)")
    print("   Природные штампы | Накопление уточнений | Энергетическая экономия")
    print("="*70)
    
    # Загружаем поле
    print("\n📂 Загрузка поля...")
    start = time.time()
    p = Personality.load('src/rizoma/data/personalities/p016_full_v15.json')
    elapsed = time.time() - start
    print(f"   Загружено за {elapsed:.1f} сек")
    print(f"   Слов: {len(p.vortices)}")
    
    # Запускаем тесты
    test_stamps(p)
    test_dialog_memory(p)
    test_resonance(p)
    test_quantum(p)
    test_topology(p)
    test_energy(p)
    test_state(p)
    
    print_separator("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("\n🦌 Поле H версии 15.2 готово к работе!")


if __name__ == "__main__":
    main()