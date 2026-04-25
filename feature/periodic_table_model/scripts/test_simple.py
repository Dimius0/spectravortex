import sys
sys.path.insert(0, '../../src')
sys.path.insert(0, '../../src/architect')

import numpy as np
from biharmonic_3d import TopologicalArchitect3D

# Простой класс для состояния (если thermodynamics не загрузится)
class SimpleState:
    def __init__(self, T, P):
        self.temperature = T
        self.pressure = P

print("=" * 60)
print("ТЕСТ РЕЛАКСАЦИИ С УЧЁТОМ P И T")
print("=" * 60)

# Создаём архитектора с маленькой сеткой для быстрого теста
arch = TopologicalArchitect3D(grid_shape=(32, 32, 32), box_size=(50, 50, 50))

# Добавляем несколько вихрей
print("\n[1] Добавляем вихри...")
for z, sym in [(1, 'H'), (6, 'C'), (8, 'O'), (26, 'Fe')]:
    arch.add_component({
        'charge': z,
        'symbol': sym,
        'Z': z,
        'position': [25 + np.random.randn()*10, 25 + np.random.randn()*10, 25 + np.random.randn()*10]
    })
print(f"    Добавлено {len(arch.vortices)} вихрей")

# Тест 1: нормальные условия
state1 = SimpleState(300.0, 0.1)
print("\n[2] ТЕСТ 1: T=300K, P=0.1 GPa (нормальные условия)")
result1 = arch.relax_vortices(max_iter=30, learning_rate=0.05, state=state1, thermal_scale=0.3)
print(f"    Финальная энергия: {result1['final_energy']:.2f}")
print(f"    d_min(P): {result1['d_min_equilibrium']:.3f}")

# Тест 2: высокое давление и температура
state2 = SimpleState(5000.0, 50.0)
print("\n[3] ТЕСТ 2: T=5000K, P=50 GPa (экстремальные условия)")
result2 = arch.relax_vortices(max_iter=30, learning_rate=0.05, state=state2, thermal_scale=0.3)
print(f"    Финальная энергия: {result2['final_energy']:.2f}")
print(f"    d_min(P): {result2['d_min_equilibrium']:.3f}")

# Сравнение позиций
print("\n[4] СРАВНЕНИЕ ПОЗИЦИЙ")
positions1 = result1['final_positions']
positions2 = result2['final_positions']

differences = []
for i, (p1, p2) in enumerate(zip(positions1, positions2)):
    diff = np.linalg.norm(np.array(p1) - np.array(p2))
    differences.append(diff)
    print(f"    Вихрь {i}: diff = {diff:.3f}")

avg_diff = np.mean(differences)
print(f"\n    Среднее отклонение: {avg_diff:.3f}")

if avg_diff > 1.0:
    print("\n" + "=" * 60)
    print("✅ УСПЕХ: Позиции существенно различаются!")
    print("   Давление и температура влияют на релаксацию вихрей.")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("❌ ОШИБКА: Позиции почти не изменились.")
    print("   Давление и температура НЕ влияют на релаксацию.")
    print("=" * 60)

# Вывод итоговых позиций для визуального контроля
print("\n[5] ФИНАЛЬНЫЕ ПОЗИЦИИ (нормальные условия):")
for i, pos in enumerate(positions1[:4]):
    print(f"    {['H','C','O','Fe'][i]}: [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}]")

print("\n[6] ФИНАЛЬНЫЕ ПОЗИЦИИ (экстремальные условия):")
for i, pos in enumerate(positions2[:4]):
    print(f"    {['H','C','O','Fe'][i]}: [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}]")