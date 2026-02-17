"""
ЬТ-СТ ТСТ Т
сего 10 строк кода
"""

print("🧪 ТСТ Т Т ")
print("=" * 50)

try:
    # Самый простой импорт
    import sys
    sys.path.insert(0, "emergent_time/integration")
    
    from spectravortex_solver import EmergentTimeSolver
    
    print("✅ Шаг 1: одуль импортирован")
    
    # Создаём solver
    solver = EmergentTimeSolver()
    print(f"✅ Шаг 2: Solver создан - {solver.name}")
    
    # ростейший тест
    problem = {"type": "temporal_synchronization", "network": {}}
    can_solve, confidence = solver.can_solve(problem)
    
    print(f"✅ Шаг 3: can_solve работает - {confidence:.0%} уверенности")
    
    print("\n" + "=" * 50)
    print("🎉 С ТТ!")
    print("\nобавьте в phase3_demo.py:")
    print("from emergent_time.integration.spectravortex_solver import EmergentTimeSolver")
    print("solver_mgr.register_solver(EmergentTimeSolver())")
    print("\nодуль готов к использованию в SpectraVortex!")
    
except Exception as e:
    print(f"❌ шибка: {e}")
    print("\nроверьте:")
    print("1. emergent_time/ в spectravortex/")
    print("2. айл emergent_time/integration/spectravortex_solver.py")
