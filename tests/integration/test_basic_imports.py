import sys
sys.path.insert(0, '.')

print("=== инимальный тест работоспособности ===")

try:
    # робуем правильный импорт
    from simulator import FieldSolution
    print("✅ FieldSolution импортирован")
    
    # Создаем экземпляр
    sol = FieldSolution(status="test", data={"ok": True})
    print(f"✅ Создан экземпляр: status={sol.status}, data={sol.data}")
    
    # роверяем SolverManager
    from simulator.core.solver_manager import SolverManager
    mgr = SolverManager()
    print("✅ SolverManager создан")
    
    print("`n🎉 С ТТ! равильный импорт: from simulator import FieldSolution")
    
except Exception as e:
    print(f"❌ шибка: {e}")
