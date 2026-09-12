# test_listing_variants.py
# 🧪 Тест: структура (без лемм)

from tees_listing import Listing
from tees_fractal_search import FractalSearch
import time


def main():
    print("=" * 60)
    print("🧪 ТЕСТ: СТРУКТУРА (БЕЗ ЛЕММ)")
    print("=" * 60)
    
    search = FractalSearch()
    
    listing_a = Listing("A", "ИИ-помощь", "Помогу с ИИ")
    listing_a.add_variant("Требуется ИИ для анализа данных")
    listing_a.add_variant("Ищу специалиста по ИИ")
    listing_a.add_variant("Нужна помощь с нейросетями")
    
    listing_b = Listing("B", "Ищу ИИ для обработки текстов")
    listing_c = Listing("C", "Продаю рыбу")
    listing_d = Listing("D", "Вычисления TSP для логистики")
    
    search.add_listing(listing_a)
    search.add_listing(listing_b)
    search.add_listing(listing_c)
    search.add_listing(listing_d)
    
    print(f"\n📊 Объявления:")
    for l in search.list_all():
        print(f"  {l['node_id']}: {l['variants']}")
    
    print(f"\n🔍 Точный поиск:")
    for q in ["ИИ-помощь", "Продаю рыбу"]:
        result = search.find_exact(q)
        if result:
            print(f"  '{q}' → {result['node_id']}")
    
    queries = [
        "ИИ-помощь для анализа",
        "ИИ для обработки текстов",
        "нейросети",
        "маршруты",
        "рыба",
    ]
    
    print(f"\n🔍 Похожие:")
    for q in queries:
        t0 = time.time()
        results = search.find_similar(q)
        elapsed = (time.time() - t0) * 1000
        
        print(f"\n  '{q}' ({elapsed:.1f} мс):")
        if results:
            for r in results:
                print(f"    {r['node_id']}: {r['similarity']:.4f} — '{r['best_variant']}'")
        else:
            print(f"    Ничего не найдено")


if __name__ == "__main__":
    main()