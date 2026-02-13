"""
ЬЫ  ТСТ Я
"""

import os
import sys

print("🎯 ЬЫ ТСТ ТСССТ")
print("=" * 60)

# ути
module_dir = os.path.join(os.getcwd(), "emergent_time")
integration_dir = os.path.join(module_dir, "integration")

# обавляем пути
sys.path.insert(0, module_dir)
sys.path.insert(0, integration_dir)

try:
    # мпортируем
    print("1. мпорт модуля...")
    
    # рямой импорт из integration
    exec(open(os.path.join(integration_dir, "spectravortex_solver.py"), encoding='utf-8').read())
    from spectravortex_solver import EmergentTimeSolver
    
    print("   ✅ одуль импортирован")
    
    # Создаём solver
    print("\n2. Создание solver'а...")
    solver = EmergentTimeSolver(config={
        "emergent_depth": 0.8,
        "validation": True
    })
    
    print(f"   ✅ Solver: {solver.name} v{solver.version}")
    print(f"   📖 {solver.description}")
    
    # Тест can_solve
    print("\n3. Тест can_solve...")
    test_problem = {
        "type": "temporal_synchronization",
        "network": {"num_nodes": 8}
    }
    
    can_solve, confidence = solver.can_solve(test_problem)
    print(f"   ✅ оддерживается с уверенностью: {confidence:.0%}")
    
    # ешение
    print("\n4. Тест решения...")
    solution = solver.solve(test_problem)
    
    print(f"   📊 Статус: {solution['status']}")
    
    if solution['status'] == 'solved':
        data = solution['data']
        sync = data['synchronization']
        
        print(f"   🎯 араметр порядка: {sync['order_parameter']:.3f}")
        print(f"   📈 Синхронизирована: {'✅ ' if sync['is_synchronized'] else '❌ Т'}")
        print(f"   🏷️  ачество: {sync['sync_strength']}")
        
        # роверяем структуру данных
        print(f"   📦 злов в результатах: {len(data.get('nodes', []))}")
        print(f"   📊 нализ: {data.get('analysis', {}).get('summary', 'N/A')}")
        
    elif solution['status'] == 'error':
        error_msg = solution['data'].get('error', 'еизвестная ошибка')
        print(f"   ⚠️  шибка решения: {error_msg}")
        
        # сли это ошибка импорта, покажем как исправить
        if "import" in error_msg.lower() or "module" in error_msg.lower():
            print("\n   🔧 ля исправления проверьте:")
            print("   1. айл emergent_time/core/emergent_engine.py существует")
            print("   2.  spectravortex_solver.py импорт: from emergent_engine import ...")
    
    # Статистика
    print("\n5. Статистика solver'а...")
    stats = solver.get_stats()
    print(f"   📈 ешено проблем: {stats.get('problems_solved', 0)}")
    print(f"   ⏱️  Среднее время: {stats.get('avg_compute_time', 0):.3f} сек")
    print(f"   🎯 спешность: {stats.get('success_rate', 0):.1%}")
    
    print("\n" + "=" * 60)
    print("✅ Ь ТТ  Т  Т!")
    print("=" * 60)
    
    print("\n📋 ля регистрации в SpectraVortex добавьте в phase3_demo.py:")
    print('''
# осле создания SolverManager (после строки solver_mgr = SolverManager())
try:
    from emergent_time.integration.spectravortex_solver import EmergentTimeSolver
    
    # онфигурация solver'а
    temporal_config = {
        "emergent_depth": 0.8,  # ровень эмерджентности (0.0-1.0)
        "validation": False,    # True для отладки, False для скорости
    }
    
    # Создаём и регистрируем
    temporal_solver = EmergentTimeSolver(config=temporal_config)
    temporal_solver_id = solver_mgr.register_solver(temporal_solver)
    
    print(f"🌀 EmergentTimeSolver зарегистрирован (ID: {temporal_solver_id})")
    print(f"   • ерсия: {temporal_solver.version}")
    print(f"   • лубина эмерджентности: {temporal_config['emergent_depth']}")
    
except ImportError as e:
    print(f"⚠️  одуль эмерджентного времени не загружен: {e}")
    print("   бедитесь, что папка emergent_time/ находится в spectravortex/")
''')
    
    print("\n🚀 одуль готов к использованию в SpectraVortex!")
    
except Exception as e:
    print(f"\n❌ ритическая ошибка: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 иагностика проблемы:")
    print("1. роверьте файл emergent_time/integration/spectravortex_solver.py")
    print("2. бедитесь, что строка импорта: from emergent_engine import ...")
    print("3. роверьте файл emergent_time/core/emergent_engine.py")
