# test_fractal_search.py
# 🧪 Тест: поиск фракталов (Гровер + валидный процент)

from tees_fractal_search import FractalSearch


def main():
    print("=" * 60)
    print("🧪 ТЕСТ: ПОИСК ФРАКТАЛОВ (ГРОВЕР + ПРОЦЕНТ)")
    print("=" * 60)
    
    search = FractalSearch()
    
    # База
    texts = {
        'рыба': "рыба",
        'рыбу': "продаю рыбу",
        'рыбак': "старый рыбак на берегу",
        'рынок': "рынок свежей рыбы",
        'ии': "ИИ-помощь для анализа данных",
        'ии2': "Требуется анализ больших данных",
        'ии3': "Ищу ИИ для обработки текстов",
        'tsp': "Вычисления TSP для логистики",
        'tsp2': "Нужны вычисления для маршрутов",
    }
    
    for name, text in texts.items():
        search.add(name, text)
    
    print(f"\n📊 База: {len(texts)} фракталов")
    for item in search.list_all():
        print(f"  {item['name']}: {item['structure']}")
    
    # Тест 1: точный поиск
    print(f"\n🔍 Точный поиск:")
    for q in ["рыба", "продаю рыбу", "ИИ-помощь для анализа данных"]:
        result = search.find_exact(q)
        print(f"  '{q}' → {result}")
    
    # Тест 2: похожие
    print(f"\n🔍 Похожие (для 'ИИ-помощь для анализа данных'):")
    results = search.find_similar("ИИ-помощь для анализа данных")
    for r in results:
        print(f"  {r['name']}: {r['similarity']:.4f} — '{r['text']}'")
    
    print(f"\n🔍 Похожие (для 'продаю рыбу'):")
    results = search.find_similar("продаю рыбу")
    for r in results:
        print(f"  {r['name']}: {r['similarity']:.4f} — '{r['text']}'")
    
    print(f"\n🔍 Похожие (для 'несуществующий текст'):")
    results = search.find_similar("несуществующий текст")
    if results:
        for r in results:
            print(f"  {r['name']}: {r['similarity']:.4f}")
    else:
        print(f"  Ничего не найдено (>50% — валидных нет)")
    
    # Тест 3: полный поиск
    print(f"\n🔍 Полный поиск (для 'продаю рыбу'):")
    full = search.find_full("продаю рыбу")
    print(f"  Точное: {full['exact']}")
    print(f"  Похожих: {full['count']}")
    for r in full['similar']:
        print(f"    {r['name']}: {r['similarity']:.4f}")


if __name__ == "__main__":
    main()