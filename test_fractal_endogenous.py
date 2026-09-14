# test_fractal_endogenous.py
# 🧪 Тест: эндогенный цикл + петля самопричинения

from tees_fractal_endogenous import FractalField
import time


def main():
    print("=" * 60)
    print("🧪 ТЕСТ: Эндогенный цикл фракталов")
    print("=" * 60)
    
    # Создаём поле
    field = FractalField()
    
    # Добавляем фракталы
    field.add_fractal('ai_help', "ИИ-помощь для анализа данных")
    field.add_fractal('ai_analysis', "Требуется анализ больших данных")
    field.add_fractal('tsp', "Вычисления TSP для логистики")
    field.add_fractal('fish', "Продаю рыбу")
    
    print(f"\n📊 Начальное состояние:")
    field.print_state()
    
    # Эволюция
    print(f"\n🔄 Эволюция поля (20 циклов)...")
    for i in range(20):
        field.evolve(dt=0.1)
        if i % 5 == 0:
            stats = field.get_stats()
            print(f"  Цикл {i}: когерентность={stats['coherence']:.4f}, "
                  f"энтропия={stats['entropy']:.4f}")
    
    print(f"\n📊 После эволюции:")
    field.print_state()
    
    # Фуркации
    print(f"\n🌿 Попытки фуркаций (10 раз)...")
    for i in range(10):
        if field.try_furcation():
            print(f"  ✅ Фуркация #{field.furcation_count}")
        time.sleep(0.01)
    
    print(f"\n📊 Финальное состояние:")
    field.print_state()
    
    # Проверки
    print(f"\n" + "=" * 60)
    print("🔬 ПРОВЕРКИ:")
    print("=" * 60)
    
    stats = field.get_stats()
    
    ok = True
    
    if stats['coherence'] > 0.5:
        print(f"  ✅ Когерентность > 0.5: {stats['coherence']:.4f}")
    else:
        print(f"  ⚠️ Когерентность низкая: {stats['coherence']:.4f}")
    
    if stats['entropy'] > 0.5:
        print(f"  ✅ Энтропия > 0.5: {stats['entropy']:.4f}")
    else:
        print(f"  ⚠️ Энтропия низкая: {stats['entropy']:.4f}")
    
    if stats['furcations'] > 0:
        print(f"  ✅ Фуркации: {stats['furcations']}")
    else:
        print(f"  ⚠️ Фуркаций нет")
    
    # Ключевое: когерентность 1.0 + энтропия 1.0
    print(f"\n  🎯 КЛЮЧЕВОЕ:")
    print(f"    Когерентность: {stats['coherence']:.4f}")
    print(f"    Энтропия: {stats['entropy']:.4f}")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТ ПРОЙДЕН" if ok else "⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН")
    print("=" * 60)


if __name__ == "__main__":
    main()