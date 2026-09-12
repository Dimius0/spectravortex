# test_fractal_genome.py
# 🧪 Тест: конвейер геномов

from tees_fractal_image import FractalImage
from tees_image_resonance import fractal_resonance, fractal_diff


def print_genome(title, img):
    print(f"\n📊 {title}:")
    print(f"  Структура: ", end="")
    for level_num in sorted(img.levels.keys()):
        print(f"{img.levels[level_num]['count']} ", end="")
    print()
    print(f"  Геномы уровней:")
    for level_num in sorted(img.levels.keys()):
        l = img.levels[level_num]
        print(f"    {l['name']}: {l['vortex'].hex()[:16]}...")


def test_identical():
    t = "продаю рыбу"
    img1 = FractalImage(t)
    img2 = FractalImage(t)
    res = fractal_resonance(img1, img2)
    diff = fractal_diff(img1, img2)
    
    print(f"\n🔬 ИДЕНТИЧНЫЕ: '{t}'")
    print(f"  Резонанс: {res['resonance']:.4f}")
    print(f"  Идентичны: {diff['identical']}")
    for name, r in res['level_resonances'].items():
        print(f"    {name}: {r:.4f}")
    return res['resonance'], diff['identical']


def test_different_lengths():
    """Разные длины, но общий корень."""
    t1 = "рыба"
    t2 = "продаю рыбу"
    t3 = "продаю свежую рыбу сегодня утром на рынке"
    
    img1 = FractalImage(t1)
    img2 = FractalImage(t2)
    img3 = FractalImage(t3)
    
    print(f"\n🔬 РАЗНЫЕ ДЛИНЫ:")
    print_genome(f"'{t1}'", img1)
    print_genome(f"'{t2}'", img2)
    print_genome(f"'{t3}'", img3)
    
    # Сравнения
    print(f"\n  Сравнения:")
    
    res_12 = fractal_resonance(img1, img2)
    print(f"    '{t1}' vs '{t2}':")
    print(f"      общий: {res_12['resonance']:.4f}")
    for name, r in res_12['level_resonances'].items():
        print(f"        {name}: {r:.4f}")
    
    res_23 = fractal_resonance(img2, img3)
    print(f"    '{t2}' vs '{t3}':")
    print(f"      общий: {res_23['resonance']:.4f}")
    for name, r in res_23['level_resonances'].items():
        print(f"        {name}: {r:.4f}")
    
    res_13 = fractal_resonance(img1, img3)
    print(f"    '{t1}' vs '{t3}':")
    print(f"      общий: {res_13['resonance']:.4f}")
    for name, r in res_13['level_resonances'].items():
        print(f"        {name}: {r:.4f}")
    
    return res_12['resonance'], res_23['resonance'], res_13['resonance']


def test_fish_family():
    """Семья рыб."""
    texts = {
        'рыба': "рыба",
        'рыбу': "продаю рыбу",
        'рыбак': "старый рыбак на берегу",
        'рынок': "рынок свежей рыбы",
        'ии': "ИИ-помощь для анализа данных",
    }
    
    images = {name: FractalImage(t) for name, t in texts.items()}
    
    print(f"\n🔬 СЕМЬЯ РЫБ И НЕ ТОЛЬКО:")
    for name, img in images.items():
        print_genome(name, img)
    
    print(f"\n  Сравнения (с 'рыба'):")
    for name, img in images.items():
        if name == 'рыба':
            continue
        res = fractal_resonance(images['рыба'], img)
        print(f"    'рыба' vs '{name}': {res['resonance']:.4f}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ТЕСТ: КОНВЕЙЕР ГЕНОМОВ")
    print("=" * 60)
    
    r_id, ident = test_identical()
    
    print("\n" + "=" * 60)
    print("РАЗНЫЕ ДЛИНЫ")
    print("=" * 60)
    test_different_lengths()
    
    print("\n" + "=" * 60)
    print("СЕМЬЯ РЫБ")
    print("=" * 60)
    test_fish_family()
    
    print("\n" + "=" * 60)
    print("🔬 ПРОВЕРКИ:")
    print("=" * 60)
    
    print(f"  Идентичные:")
    print(f"    резонанс: {r_id:.4f}")
    print(f"    identical: {ident}")
    
    ok = True
    if r_id > 0.9:
        print("  ✅ Идентичные > 0.9")
    else:
        print(f"  ⚠️ Идентичные: {r_id:.4f}")
        ok = False
    
    if ident:
        print("  ✅ Идентичные — идентичны")
    else:
        print("  ❌ Идентичные — не идентичны")
        ok = False
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТ ПРОЙДЕН" if ok else "⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН")
    print("=" * 60)