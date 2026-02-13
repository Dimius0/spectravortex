import sys
sys.path.insert(0, '.')

print("=== равильное использование FieldSolution ===")

try:
    from simulator import FieldSolution
    
    print("✅ FieldSolution импортирован")
    
    # осмотрим что принимает конструктор
    print(f"онструктор FieldSolution: {FieldSolution.__init__}")
    
    # Создадим пустой экземпляр и посмотрим атрибуты
    sol = FieldSolution()
    print(f"✅ Создан экземпляр: {sol}")
    
    # осмотрим какие атрибуты есть по умолчанию
    print(f"трибуты по умолчанию: {[attr for attr in dir(sol) if not attr.startswith('_')][:10]}")
    
    # опробуем установить атрибуты
    sol.status = "solved"
    sol.data = {"result": "test_ok"}
    
    print(f"✅ становлены атрибуты: status={sol.status}, data={sol.data}")
    
    # Теперь проверим SolverManager
    from simulator.core.solver_manager import SolverManager
    
    class TestSolver:
        name = "TestSolver"
        def can_solve(self, problem):
            return True, 1.0
        def solve(self, problem):
            solution = FieldSolution()
            solution.status = "solved"
            solution.data = {"problem": problem.get('id'), "result": 42}
            return solution
    
    manager = SolverManager()
    solver = TestSolver()
    manager.register_solver(solver)
    
    problem = {"id": "test_1", "type": "test"}
    solution = manager.solve(problem)
    
    print(f"✅ SolverManager работает!")
    print(f"   ешение: status={solution.status}")
    print(f"   анные: {solution.data}")
    
    print("`n🎉 С ТТ! равильное использование FieldSolution:")
    print("   1. Создаем: sol = FieldSolution()")
    print("   2. станавливаем: sol.status = '...'; sol.data = {...}")
    
except Exception as e:
    print(f"❌ шибка: {e}")
    import traceback
    traceback.print_exc()
