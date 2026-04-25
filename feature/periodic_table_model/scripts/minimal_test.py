# инимальный тест без импорта thermodynamics
import sys
import os
import numpy as np

# обавляем путь
sys.path.insert(0, os.path.abspath('../../src'))

# ростой класс состояния
class TestState:
    def __init__(self, T, P):
        self.temperature = T
        self.pressure = P

# ытаемся импортировать
from biharmonic_3d import TopologicalArchitect3D

print("=" * 60)
print("ЬЫ ТСТ")
print("=" * 60)

# Создаём архитектора
arch = TopologicalArchitect3D(grid_shape=(32, 32, 32), box_size=(50, 50, 50))

# обавляем компоненты
for z, sym in [(1, 'H'), (6, 'C')]:
    arch.add_component({
        'charge': z,
        'symbol': sym,
        'Z': z,
        'position': [25, 25, 25]
    })

print(f"Создано {len(arch.vortices)} вихрей")

# Тест 1
state1 = TestState(300, 0.1)
print("\n[1] ызов relax_vortices с state...")
try:
    result1 = arch.relax_vortices(max_iter=5, learning_rate=0.05, state=state1)
    print(f"    ✅ спешно! final_energy = {result1.get('final_energy', 'N/A')}")
except TypeError as e:
    print(f"    ❌ шибка: {e}")
    print("    Сигнатура метода не поддерживает параметр 'state'")

# Тест 2 без state
print("\n[2] ызов relax_vortices без state...")
try:
    result2 = arch.relax_vortices(max_iter=5, learning_rate=0.05)
    print(f"    ✅ спешно! final_energy = {result2.get('final_energy', 'N/A')}")
except Exception as e:
    print(f"    ❌ шибка: {e}")

print("\n" + "=" * 60)
