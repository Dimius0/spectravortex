# test_fractal_image_1.py
# 🧪 Тест 1: Резонанс фракталов

from tees_fractal_image import FractalImage
from tees_image_resonance import fractal_resonance


def print_details(title, img, res):
    print(f"\n📊 {title}:")
    print(f"  Структура: {img.structure_vector}")
    print(f"  Отношения: {img.ratio_vector}")
    print(f"  Резонанс (минимум): {res['resonance']:.4f}")
    print(f"  Структурный: {res['struct_resonance']:.4f}")
    print(f"  Отношений:   {res['ratio_resonance']:.4f}")
    for name, r in res['level_resonances'].items():
        print(f"    {name}: {r:.4f}")


def test_identical():
    t = "ИИ-помощь для анализа данных"
    img1 = FractalImage(t)
    img2 = FractalImage(t)
    res = fractal_resonance(img1, img2)
    print_details(f"Идентичные:\n  '{t}'", img1, res)
    return res['resonance']


def test_similar():
    t1 = "ИИ-помощь для анализа данных"
    t2 = "Требуется анализ больших данных"
    img1 = FractalImage(t1)
    img2 = FractalImage(t2)
    res = fractal_resonance(img1, img2)
    print_details(f"Похожие:\n  '{t1}'\n  '{t2}'", img1, res)
    print(f"  (У второго структура: {img2.structure_vector})")
    return res['resonance']


def test_different():
    t1 = "ИИ-помощь для анализа данных"
    t2 = "Продаю рыбу"
    img1 = FractalImage(t1)
    img2 = FractalImage(t2)
    res = fractal_resonance(img1, img2)
    print_details(f"Разные:\n  '{t1}'\n  '{t2}'", img1, res)
    print(f"  (У второго структура: {img2.structure_vector})")
    return res['resonance']


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ТЕСТ 1: Резонанс фракталов (структурный)")
    print("=" * 60)
    
    r_id = test_identical()
    r_sim = test_similar()
    r_diff = test_different()
    
    print("\n" + "=" * 60)
    print("🔬 ПРОВЕРКИ:")
    print("=" * 60)
    print(f"  Идентичные: {r_id:.4f}")
    print(f"  Похожие:    {r_sim:.4f}")
    print(f"  Разные:     {r_diff:.4f}")
    
    ok = True
    if r_id > 0.9:
        print("  ✅ Идентичные > 0.9")
    else:
        print(f"  ⚠️ Идентичные: {r_id:.4f}")
        ok = False
    
    if r_sim > r_diff:
        print(f"  ✅ Похожие > Разные ({r_sim:.4f} > {r_diff:.4f})")
    else:
        print(f"  ⚠️ Похожие ≤ Разные")
        ok = False
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТ ПРОЙДЕН" if ok else "⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН")
    print("=" * 60)