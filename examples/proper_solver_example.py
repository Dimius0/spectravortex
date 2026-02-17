"""
Ь С FieldSolution Я SOLVER
"""
import sys
sys.path.insert(0, '.')
import numpy as np
from simulator.core.data_interface import FieldSolution
from simulator.core.solver_manager import SolverManager

print("=== ример правильного солвера ===")

class SimpleTestSolver:
    name = "SimpleTestSolver"
    
    def can_solve(self, problem):
        # ожем решать задачи типа "test"
        return problem.get("type") == "test", 0.9
    
    def solve(self, problem):
        # Создаем простое 1D поле для демонстрации
        n_points = 10
        amplitude = np.ones(n_points)  # диничная амплитуда
        phase = np.linspace(0, 2*np.pi, n_points)  # инейная фаза
        
        # С FieldSolution с правильными параметрами
        solution = FieldSolution(
            amplitude=amplitude,
            phase=phase,
            spatial_dim=1
        )
        
        # обавляем дополнительные данные
        solution.status = "solved"
        solution.data = {
            "problem_id": problem.get("id"),
            "points": n_points,
            "description": "ростое тестовое решение"
        }
        
        return solution

# Тестируем
try:
    manager = SolverManager()
    solver = SimpleTestSolver()
    solver_id = manager.register_solver(solver)
    
    problem = {"id": "demo_1", "type": "test", "complexity": "low"}
    result = manager.solve(problem)
    
    print(f"✅ Солвер зарегистрирован: {solver_id}")
    print(f"✅ ешение получено: {result.status}")
    print(f"✅ анные: {result.data}")
    print(f"✅ оле: shape={result.amplitude.shape}, spatial_dim={result.spatial_dim}")
    
except Exception as e:
    print(f"❌ шибка: {e}")
