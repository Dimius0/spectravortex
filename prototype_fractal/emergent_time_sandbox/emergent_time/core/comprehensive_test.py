import sys
sys.path.insert(0, '.')
from emergent_engine import EmergentTimeEngine, NodeState
import numpy as np
import time

print('🧪 С ТСТ Я')
print('=' * 50)

# Тест 1: азовая синхронизация
print('\n1. ТСТ: азовая синхронизация (20 узлов, 100 шагов)')
nodes = [NodeState(id=i, health=0.9) for i in range(20)]
engine = EmergentTimeEngine(nodes, validation_mode=False)

start_time = time.time()
engine.evolve(steps=100, K=2.5)
compute_time = time.time() - start_time

metrics = engine.get_synchronization_metrics()
print(f'   ремя вычисления: {compute_time:.3f} сек')
print(f'   араметр порядка: {metrics["order_parameter"]:.4f}')
print(f'   Синхронизирована: {"" if metrics["is_synchronized"] else "Т"}')

# Тест 2: лияние здоровья на синхронизацию
print('\n2. ТСТ: лияние здоровья узлов')
healthy_nodes = [NodeState(id=i, health=0.95) for i in range(10)]
damaged_nodes = [NodeState(id=i+10, health=0.4) for i in range(10)]
mixed_nodes = healthy_nodes + damaged_nodes

engine_mixed = EmergentTimeEngine(mixed_nodes, validation_mode=False)
engine_mixed.evolve(steps=150, K=3.0)

metrics_mixed = engine_mixed.get_synchronization_metrics()
print(f'   араметр порядка (смешанная сеть): {metrics_mixed["order_parameter"]:.4f}')

# Тест 3: азные топологии
print('\n3. ТСТ: азные топологии сети')
# ольцевая топология
ring_matrix = np.zeros((15, 15))
for i in range(15):
    ring_matrix[i, (i-1) % 15] = 1.0
    ring_matrix[i, (i+1) % 15] = 1.0

nodes_ring = [NodeState(id=i, health=0.85) for i in range(15)]
engine_ring = EmergentTimeEngine(nodes_ring, connectivity_matrix=ring_matrix, validation_mode=False)
engine_ring.evolve(steps=100, K=2.0)

metrics_ring = engine_ring.get_synchronization_metrics()
print(f'   ольцевая топология: {metrics_ring["order_parameter"]:.4f}')

# олносвязная топология
full_matrix = np.ones((15, 15)) - np.eye(15)
engine_full = EmergentTimeEngine(nodes_ring, connectivity_matrix=full_matrix, validation_mode=False)
engine_full.evolve(steps=100, K=2.0)

metrics_full = engine_full.get_synchronization_metrics()
print(f'   олносвязная топология: {metrics_full["order_parameter"]:.4f}')

# Тест 4: асштабируемость
print('\n4. ТСТ: асштабируемость')
for N in [10, 30, 50]:
    nodes_scaling = [NodeState(id=i, health=0.9) for i in range(N)]
    engine_scaling = EmergentTimeEngine(nodes_scaling, validation_mode=False)
    
    start = time.time()
    engine_scaling.evolve(steps=50, K=2.0)
    elapsed = time.time() - start
    
    metrics_scaling = engine_scaling.get_synchronization_metrics()
    print(f'   N={N:3d}: время={elapsed:.3f} сек, синхронизация={metrics_scaling["order_parameter"]:.4f}')

# Тест 5: ффект бабочки
print('\n5. ТСТ: ффект бабочки')
nodes_butterfly = [NodeState(id=i, health=0.9) for i in range(25)]
engine1 = EmergentTimeEngine(nodes_butterfly, validation_mode=False)
engine2 = EmergentTimeEngine(nodes_butterfly, validation_mode=False)

# дентичная эволюция
engine1.evolve(steps=30, K=2.0)
engine2.evolve(steps=30, K=2.0)

# аленькое воздействие на один узел
state = engine2.temporal_states[10]
state.phase += 0.001  # инимальное изменение

# родолжаем эволюцию
engine1.evolve(steps=50, K=2.0)
engine2.evolve(steps=50, K=2.0)

metrics1 = engine1.get_synchronization_metrics()
metrics2 = engine2.get_synchronization_metrics()
phase_diff = abs(metrics1["order_parameter"] - metrics2["order_parameter"])

print(f'   азница параметров порядка: {phase_diff:.6f}')
print(f'   силение: {phase_diff / 0.001:.1f}x')
print(f'   ффект бабочки: {"" if phase_diff > 0.01 else "не обнаружен"}')

print('\n' + '=' * 50)
print('✅ С ТСТЫ ШЫ')
