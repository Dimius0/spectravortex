#!/usr/bin/env python3
"""
Тест для состояния Хойла в ¹²C.
Спектральный анализ с привязкой к энергии через E = ħω.
"""

import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.spectral_analyzer import SpectralAnalyzer
    from src.architect.temporal_state import TemporalState
    print("✅ Импорт модулей")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def create_tetrahedron(a_fm=2.5):
    """Создаёт 4 компонента в вершинах правильного тетраэдра"""
    a = a_fm * 1e-15  # в метры
    
    # Координаты вершин правильного тетраэдра
    vertices = [
        (0, 0, 0),
        (a, 0, 0),
        (a/2, a * math.sqrt(3)/2, 0),
        (a/2, a/3, a * math.sqrt(2/3))
    ]
    
    components = []
    for i, (x, y, z) in enumerate(vertices):
        comp = Component(id=i, charge=1.0, health=1.0)
        
        # Временное состояние с разными начальными фазами
        comp.temporal = TemporalState(
            phase=2 * math.pi * i / 4,  # 0, π/2, π, 3π/2
            frequency=0.005,  # базовая частота
            amplitude=1.0,
            stability=1.0
        )
        
        # Координаты
        comp.position = np.array([x, y, z])
        components.append(comp)
    
    return components

def test_hoyle_state():
    """Основной тест: спектральный анализ тетраэдра"""
    print("\n🧪 ТЕСТ СОСТОЯНИЯ ХОЙЛА")
    print("=" * 60)
    
    # Создаём тетраэдр
    print("Создаём тетраэдр из 4 компонентов...")
    components = create_tetrahedron(2.5)
    print(f"  Компонентов: {len(components)}")
    print(f"  Частота каждого: 0.005")
    
    # Добавляем небольшие возмущения, чтобы увидеть моды
    for i, comp in enumerate(components):
        if hasattr(comp, 'temporal') and comp.temporal:
            comp.temporal.phase += 0.01 * (i - 1.5)
    
    # Создаём анализатор
    analyzer = SpectralAnalyzer(sampling_rate=1.0)
    
    # Запускаем анализ с большим числом шагов для хорошего разрешения
    print("\nАнализируем колебательные моды (steps=4000, dt=0.05)...")
    result = analyzer.find_modes(components, steps=4000, dt=0.05)
    
    # Выводим результаты
    print("\n📊 Результаты:")
    print("-" * 40)
    
    if result['component_modes']:
        print("\nИндивидуальные моды компонентов:")
        freqs = []
        for mode in result['component_modes'][:4]:
            print(f"  Компонент {mode['component']}: "
                  f"f = {mode['frequency']:.6f}, "
                  f"E = {mode['energy_mev']:.2f} МэВ")
            freqs.append(mode['frequency'])
        
        print(f"\n  Средняя частота: {np.mean(freqs):.6f}")
    
    print("\n💨 Дыхательная мода (A₁):")
    breath = result['breathing_mode']
    print(f"  f = {breath['frequency']:.6f}")
    print(f"  E = {breath['energy_mev']:.2f} МэВ")
    print(f"  {breath['description']}")
    
    # Сравнение с экспериментом
    hoyle_energy = 7.65
    breath_energy = breath['energy_mev']
    
    print("\n🎯 Сравнение с состоянием Хойла:")
    print(f"  Эксперимент: {hoyle_energy:.2f} МэВ")
    print(f"  Дыхательная мода: {breath_energy:.2f} МэВ")
    print(f"  Отклонение: {abs(breath_energy - hoyle_energy):.2f} МэВ")
    
    # Проверка с разумным допуском
    if abs(breath_energy - hoyle_energy) < 1.0:
        print("\n✅ Дыхательная мода соответствует состоянию Хойла!")
        return True
    else:
        print("\n❌ Дыхательная мода не соответствует состоянию Хойла")
        return False

if __name__ == "__main__":
    success = test_hoyle_state()
    
    if success:
        print("\n" + "=" * 60)
        print("🔥 ПРЕДСКАЗАНИЕ ПОДТВЕРЖДЕНО:")
        print("   Состояние Хойла (0₂⁺ при 7.65 МэВ) в ¹²C")
        print("   интерпретируется как дыхательная мода")
        print("   тетраэдрического вихря (A₁ в группе T_d)")
        sys.exit(0)
    else:
        print("\n⚠️ Требуется доработка")
        sys.exit(1)