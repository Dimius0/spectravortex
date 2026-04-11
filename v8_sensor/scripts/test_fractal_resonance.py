# scripts/test_fractal_resonance.py
"""
Тест фрактального резонанса — проверка ответов с учётом масштабов
"""
import sys
import os
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rizoma.personality import Personality


def print_separator(title: str = None):
    print("\n" + "=" * 70)
    if title:
        print(f" {title}")
    print("=" * 70)


def test_resonance_by_scale(p):
    """Тест 1: Резонанс одного слова на разных масштабах"""
    print_separator("🎵 ТЕСТ 1: РЕЗОНАНС СЛОВА НА РАЗНЫХ МАСШТАБАХ")
    
    word = "вихрь"
    scales = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]
    
    print(f"\nСлово: {word}")
    print("-" * 50)
    print(f"{'Масштаб':>8} | {'Резонанс':>10} | {'Интерпретация'}")
    print("-" * 50)
    
    for scale in scales:
        res = p.resonance_engine.coherent_resonance(word, scale)
        
        if scale <= 0.3:
            interpret = "буквенный уровень"
        elif scale <= 1.0:
            interpret = "словесный уровень"
        elif scale <= 3.0:
            interpret = "словосочетания"
        elif scale <= 10.0:
            interpret = "предложения"
        elif scale <= 30.0:
            interpret = "абзацы"
        else:
            interpret = "весь текст"
        
        bar = "█" * int(res * 30)
        print(f"{scale:8.1f} | {res:10.3f} {bar:30} | {interpret}")


def test_fractal_question(p):
    """Тест 2: Один вопрос на всех масштабах"""
    print_separator("❓ ТЕСТ 2: ВОПРОС НА РАЗНЫХ МАСШТАБАХ")
    
    question = "Что такое вихрь?"
    
    print(f"\nВопрос: {question}")
    print("-" * 70)
    
    for scale in [1.0, 3.0, 10.0, 30.0]:
        print(f"\n📏 Масштаб = {scale}")
        
        # Временно меняем фокус
        old_focus = p.focus.copy()
        p.focus["tau"] = scale * 5  # эвристика
        
        result = p.process(question)
        print(f"   Режим: {result['mode_type']}")
        print(f"   Резонанс: {result.get('resonance', 0):.3f}")
        print(f"   Ответ: {result.get('answer', '')[:150]}...")
        
        # Восстанавливаем фокус
        p.focus = old_focus


def test_scale_factor(p):
    """Тест 3: Коэффициент близости масштабов"""
    print_separator("📊 ТЕСТ 3: КОЭФФИЦИЕНТ БЛИЗОСТИ МАСШТАБОВ")
    
    scales = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]
    
    print("\nМатрица близости масштабов (log-шкала):")
    print(" " * 10, end="")
    for s in scales:
        print(f"{s:6.1f}", end="")
    print()
    print("-" * 70)
    
    for s1 in scales:
        print(f"{s1:6.1f} | ", end="")
        for s2 in scales:
            sf = p.resonance_engine.scale_factor(s1, s2)
            print(f"{sf:6.3f}", end="")
        print()


def test_resonance_between_modes(p):
    """Тест 4: Резонанс между модами разных масштабов"""
    print_separator("🌀 ТЕСТ 4: РЕЗОНАНС МЕЖДУ МОДАМИ")
    
    # Находим по одной моде на каждом масштабе
    modes_by_scale = {}
    for mode in p.h_field:
        scale = mode.scale
        if scale not in modes_by_scale and scale in [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]:
            modes_by_scale[scale] = mode
    
    if not modes_by_scale:
        print("⚠️ Не найдены моды для теста")
        return
    
    print(f"\nНайдено мод: {len(modes_by_scale)}")
    print("-" * 70)
    
    scales = sorted(modes_by_scale.keys())
    
    for i, s1 in enumerate(scales):
        for s2 in scales[i+1:]:
            mode1 = modes_by_scale[s1]
            mode2 = modes_by_scale[s2]
            
            res = p.resonance_engine.resonance_between_modes(mode1, mode2)
            
            # Масштабный фактор отдельно
            sf = p.resonance_engine.scale_factor(s1, s2)
            
            print(f"\n scale {s1:.1f} ↔ scale {s2:.1f}")
            print(f"   Масштабный фактор: {sf:.3f}")
            print(f"   Общий резонанс: {res:.3f}")
            print(f"   Контент mode1: {mode1.content[:60]}...")
            print(f"   Контент mode2: {mode2.content[:60]}...")


def test_scientific_question(p):
    """Тест 5: Научный вопрос — должен искать в поле, а не штамповать"""
    print_separator("🔬 ТЕСТ 5: НАУЧНЫЙ ВОПРОС")
    
    questions = [
        "Что такое вихрь?",
        "Как работает квантовая запутанность?",
        "Объясни теорию относительности",
        "Что такое фрактал?",
        "Как устроена память?",
    ]
    
    for q in questions:
        print(f"\n❓ {q}")
        start = time.time()
        result = p.process(q)
        elapsed = (time.time() - start) * 1000
        
        print(f"   Режим: {result['mode_type']}")
        print(f"   Резонанс: {result.get('resonance', 0):.3f}")
        print(f"   Время: {elapsed:.0f} мс")
        
        if result['mode_type'] == 'stamp':
            print(f"   ⚠️ ШТАМП (не должно быть для научного вопроса!)")
        
        answer = result.get('answer', '')
        if answer:
            print(f"   Ответ: {answer[:200]}...")
        else:
            print(f"   Ответ: {result.get('answer', 'нет ответа')}")


def test_everyday_question(p):
    """Тест 6: Бытовой вопрос — должен штамповать"""
    print_separator("💬 ТЕСТ 6: БЫТОВОЙ ВОПРОС (ДОЛЖЕН БЫТЬ ШТАМП)")
    
    questions = [
        "привет",
        "как дела",
        "спасибо",
        "пока",
        "как жизнь",
    ]
    
    for q in questions:
        print(f"\n❓ {q}")
        result = p.process(q)
        
        print(f"   Режим: {result['mode_type']}")
        print(f"   Ответ: {result.get('answer', '')}")
        
        if result['mode_type'] == 'clarification':
            print(f"   ⚠️ УТОЧНЕНИЕ (должен быть штамп!)")


def main():
    print("=" * 70)
    print("🧪 ТЕСТ ФРАКТАЛЬНОГО РЕЗОНАНСА (ВЕРСИЯ 16.0)")
    print(" Учёт масштабов: 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0")
    print("=" * 70)
    
    # Загружаем поле
    print("\n📂 Загрузка поля...")
    start = time.time()
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16.json')
    elapsed = time.time() - start
    
    print(f" Загружено за {elapsed:.1f} сек")
    print(f" Слов: {len(p.vortices)}")
    print(f" Мод: {len(p.h_field)}")
    
    # Запускаем тесты
    test_resonance_by_scale(p)
    test_scale_factor(p)
    test_resonance_between_modes(p)
    test_scientific_question(p)
    test_everyday_question(p)
    
    print_separator("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")


if __name__ == "__main__":
    main()