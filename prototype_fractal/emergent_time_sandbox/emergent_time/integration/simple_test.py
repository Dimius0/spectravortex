"""
СТ ТСТ SOLVER
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("🧪 СТ ТСТ SOLVER")
print("=" * 60)

try:
    from temporal_solver_final import TemporalSynchronizationSolver
    print("✅ Solver загружен успешно")
    
    # Создаём solver
    solver = TemporalSynchronizationSolver(validation_mode=True)
    print(f"мя: {solver.name}")
    print(f"ерсия: {solver.version}")
    print(f"писание: {solver.description}")
    
    # ростой тест
    print("\n📊 Тест простой проблемы:")
    problem = {
        "type": "temporal_synchronization",
        "network": {"num_nodes": 10},
        "evolution_steps": 50,
        "coupling_strength": 3.0
    }
    
    # роверка can_solve
    can_solve, confidence = solver.can_solve(problem)
    print(f"ожет решить: {'✅' if can_solve else '❌'}")
    print(f"веренность: {confidence:.2f}")
    
    # ешение
    import time
    start = time.time()
    solution = solver.solve(problem)
    elapsed = time.time() - start
    
    print(f"\nремя решения: {elapsed:.2f} сек")
    print(f"Статус: {solution['status']}")
    
    if solution['status'] == 'solved':
        data = solution['data']
        metrics = data['synchronization_metrics']
        
        print(f"\n📈 езультаты:")
        print(f"  араметр порядка: {metrics['order_parameter']:.4f}")
        print(f"  Синхронизирована: {'✅' if metrics['is_synchronized'] else '❌'}")
        print(f"  ачество: {metrics.get('sync_strength', 'unknown')}")
        
        # Статистика solver'а
        print(f"\n📊 Статистика solver'а:")
        report = solver.get_performance_report()
        print(f"  ешено проблем: {report['problems_solved']}")
        print(f"  Средняя синхронизация: {report['avg_sync_achieved']:.4f}")
        print(f"  спешность: {report['success_rate']:.1%}")
    
    # Тест разных типов проблем
    print("\n🎯 Тест разных типов проблем:")
    test_cases = [
        ("temporal_synchronization", "Синхронизация"),
        ("network_health_analysis", "нализ здоровья"),
        ("resilience_temporal_analysis", "нализ устойчивости"),
        ("unknown_type", "еизвестный тип")
    ]
    
    for ptype, pdesc in test_cases:
        test_prob = {"type": ptype, "network": {}}
        can_solve, conf = solver.can_solve(test_prob)
        print(f"  {pdesc}: {'✅' if can_solve else '❌'} (уверенность: {conf:.2f})")
    
    print("\n" + "=" * 60)
    print("✅ ТСТ Ш СШ")
    
except Exception as e:
    print(f"❌ шибка: {e}")
    import traceback
    traceback.print_exc()
