import sys
sys.path.insert(0, '.')
from emergent_engine import EmergentTimeEngine, NodeState
import numpy as np

print('🧪 ТСТ Я ССТЫ')
print('=' * 40)

# 1. Создание тестовой сети
nodes = [NodeState(id=i, health=0.8 + 0.2*np.random.rand()) for i in range(10)]
print(f'1. Создано узлов: {len(nodes)}')

# 2. нициализация движка
engine = EmergentTimeEngine(nodes, validation_mode=True)
print('2. вижок инициализирован')

# 3. роверка начальной синхронизации
initial_metrics = engine.get_synchronization_metrics()
print(f'3. ачальный параметр порядка: {initial_metrics["order_parameter"]:.4f}')

# 4. волюция системы
print('4. апуск эволюции (50 шагов)...')
engine.evolve(steps=50, K=2.0)

# 5. роверка конечной синхронизации
final_metrics = engine.get_synchronization_metrics()
print(f'5. онечный параметр порядка: {final_metrics["order_parameter"]:.4f}')
print(f'   Синхронизирована: {"" if final_metrics["is_synchronized"] else "Т"}')

# 6. роверка энергии
energy = engine.calculate_system_energy()
print(f'6. нергия системы: {energy:.6f}')

print('=' * 40)
print('✅ ТСТ Ш СШ')
