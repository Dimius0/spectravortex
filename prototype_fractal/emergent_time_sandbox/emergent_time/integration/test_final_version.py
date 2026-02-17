"""
ТСТ Ш С
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from temporal_solver_final import TemporalSynchronizationSolver

print("🧪 ТСТ Ш С SOLVER")
print("=" * 60)

solver = TemporalSynchronizationSolver(validation_mode=True)

# Тест 1: азовая синхронизация
print("\n1. Тест базовой синхронизации (30 узлов):")
problem1 = {
    "type": "temporal_synchronization",
    "network": {"num_nodes": 30},
    "evolution_steps": 250,
    "coupling_strength": 4.5
}

solution1 = solver.solve(problem1)
if solution1["status"] == "solved":
    data = solution1["data"]
    metrics = data["synchronization_metrics"]
    analysis = data["analysis"]
    
    print(f"   ремя: {solution1['metadata']['compute_time']:.2f} сек")
    print(f"   араметр порядка: {metrics['order_parameter']:.4f}")
    print(f"   ачество синхронизации: {metrics['sync_strength']}")
    print(f"   Синхронизирована: {'✅' if metrics['is_synchronized'] else '❌'}")
    
    if analysis.get("recommendations"):
        print(f"   екомендации: {analysis['recommendations'][0]}")

# Тест 2: азные топологии
print("\n2. Тест разных топологий (20 узлов):")
topologies = ["ring", "star", "small_world", "grid"]

for topology in topologies:
    problem2 = {
        "type": "temporal_synchronization",
        "network": {
            "num_nodes": 20,
            "topology": topology
        },
        "evolution_steps": 200,
        "coupling_strength": 4.0
    }
    
    solution2 = solver.solve(problem2)
    if solution2["status"] == "solved":
        metrics = solution2["data"]["synchronization_metrics"]
        print(f"   {topology:15}: порядок={metrics['order_parameter']:.4f}, "
              f"синхр={'✅' if metrics['is_synchronized'] else '❌'}")

# Тест 3: лияние здоровья
print("\n3. Тест влияния здоровья узлов:")
problem3 = {
    "type": "network_health_analysis",
    "network": {
        "nodes": [
            {"health": 0.95, "load": 0.1},
            {"health": 0.95, "load": 0.2},
            {"health": 0.30, "load": 0.8},  # больной узел
            {"health": 0.95, "load": 0.1},
            {"health": 0.95, "load": 0.2},
            {"health": 0.95, "load": 0.1},
            {"health": 0.20, "load": 0.9},  # очень больной
            {"health": 0.95, "load": 0.1}
        ]
    },
    "evolution_steps": 300,
    "coupling_strength": 5.0
}

solution3 = solver.solve(problem3)
if solution3["status"] == "solved":
    data = solution3["data"]
    print(f"   араметр порядка: {data['synchronization_metrics']['order_parameter']:.4f}")
    
    # оказываем частоты узлов
    print("   астоты узлов:")
    for node in data["node_details"]:
        health_status = "✅" if node["health"] > 0.7 else "⚠️" if node["health"] > 0.4 else "❌"
        print(f"     зел {node['id']}: частота={node['frequency']:.3f} "
              f"(естественная={node['natural_frequency']:.3f}) {health_status}")

# Тест 4: асштабируемость
print("\n4. Тест масштабируемости:")
sizes = [10, 30, 50, 100]

for size in sizes:
    problem4 = {
        "type": "temporal_synchronization",
        "network": {"num_nodes": size},
        "evolution_steps": min(200, 100 + size),  # адаптивное количество шагов
        "coupling_strength": 4.0
    }
    
    import time
    start = time.time()
    solution4 = solver.solve(problem4)
    elapsed = time.time() - start
    
    if solution4["status"] == "solved":
        metrics = solution4["data"]["synchronization_metrics"]
        print(f"   N={size:3d}: время={elapsed:.2f}с, "
              f"порядок={metrics['order_parameter']:.4f}, "
              f"синхр={'✅' if metrics['is_synchronized'] else '❌'}")

# инальный отчёт
print("\n" + "=" * 60)
print("📊 ЬЫ ТТ SOLVER:")
perf_report = solver.get_performance_report()
for key, value in perf_report.items():
    if isinstance(value, float):
        print(f"   {key}: {value:.4f}")
    else:
        print(f"   {key}: {value}")

print("\n" + "=" * 60)
print("✅ ТСТ Ш С Ш")
