import sys
sys.path.insert(0, '../../src')
sys.path.insert(0, '../../src/architect')

import numpy as np
from biharmonic_3d import TopologicalArchitect3D
from thermodynamics import ThermodynamicState

# Создаём архитектора с несколькими вихрями
arch = TopologicalArchitect3D(grid_shape=(64, 64, 64), box_size=(100, 100, 100))

# Добавляем несколько тестовых вихрей
for z in [1, 2, 6, 8, 26]:  # H, He, C, O, Fe
    arch.add_component({
        'charge': z,
        'symbol': f'Z{z}',
        'Z': z,
        'position': [50 + np.random.randn()*10, 50 + np.random.randn()*10, 50 + np.random.randn()*10]
    })

# Тест 1: P=0.1, T=300
state1 = ThermodynamicState(300.0, 0.1)
print("\n=== ТЕСТ 1: P=0.1 GPa, T=300 K ===")
result1 = arch.relax_vortices(max_iter=50, learning_rate=0.05, state=state1, thermal_scale=0.3)

# Тест 2: P=50, T=5000
state2 = ThermodynamicState(5000.0, 50.0)
print("\n=== ТЕСТ 2: P=50 GPa, T=5000 K ===")
result2 = arch.relax_vortices(max_iter=50, learning_rate=0.05, state=state2, thermal_scale=0.3)

# Сравнение позиций
print("\n=== СРАВНЕНИЕ ПОЗИЦИЙ ===")
for i, (v1, v2) in enumerate(zip(result1['final_positions'], result2['final_positions'])):
    diff = np.linalg.norm(np.array(v1) - np.array(v2))
    print(f"  Вихрь {i}: diff = {diff:.3f}")

if any(np.linalg.norm(np.array(v1) - np.array(v2)) > 1.0 for v1, v2 in zip(result1['final_positions'], result2['final_positions'])):
    print("\n✅ УСПЕХ: Позиции различаются! Давление и температура влияют.")
else:
    print("\n❌ ОШИБКА: Позиции одинаковы. Давление и температура не влияют.")