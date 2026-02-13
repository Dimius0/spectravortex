"""
Улучшенная интеграция архитектора с SpectraVortex.
Версия 2.0.0
"""

import json

try:
    from ..core.topological_api import TopologicalArchitect, ArchitectureSolution
    # Временный заглушки для избежания циклических импортов
    def create_component_from_library(name, component_id=None):
        return {"id": component_id or name, "type": "electronic", "tau": 1.0}
    
    class PlacementOptimizer:
        def __init__(self, grid_shape):
            self.grid_shape = grid_shape
        def random_positions(self, n):
            return [[1,1,1]] * n
        def optimize_energy(self, pos, charges, iterations=1):
            return pos
except ImportError:
    from architect.core.topological_api import TopologicalArchitect, ArchitectureSolution
    def create_component_from_library(name, component_id=None):
        return {"id": component_id or name, "type": "electronic", "tau": 1.0}
    class PlacementOptimizer:
        def __init__(self, grid_shape):
            self.grid_shape = grid_shape

class EnhancedSpectraVortexIntegrator:
    """Улучшенный интегратор."""
    
    def __init__(self, config=None):
        self.architect = TopologicalArchitect()
        self.config = config or {
            "auto_optimize": True,
            "use_component_library": True,
            "min_component_distance": 2,
            "default_grid_shape": [48, 48, 24]
        }
        print("[ENHANCED_INTEGRATOR] Создан улучшенный интегратор")
    
    def enhance_problem_spec(self, problem_spec):
        """Улучшает спецификацию проблемы."""
        enhanced = problem_spec.copy()
        
        if "grid_shape" not in enhanced:
            enhanced["grid_shape"] = self.config["default_grid_shape"]
        
        if self.config["use_component_library"] and "components" in enhanced:
            new_components = []
            for comp in enhanced["components"]:
                if "library_name" in comp:
                    lib_comp = create_component_from_library(
                        comp["library_name"], 
                        comp.get("id")
                    )
                    new_components.append(lib_comp)
                else:
                    new_components.append(comp)
            enhanced["components"] = new_components
        
        return enhanced
    
    def synthesize_architecture(self, problem_spec):
        """Улучшенный синтез архитектуры."""
        enhanced_spec = self.enhance_problem_spec(problem_spec)
        solution = self.architect.synthesize(enhanced_spec)
        
        if solution.metadata:
            solution.metadata["integrator_version"] = "2.0.0"
        
        return solution
    
    def integrate_with_solver_manager(self, solver_manager, priority=7):
        """Интеграция с SolverManager."""
        try:
            solver_id = solver_manager.register_solver(self.architect, priority=priority)
            print(f"[ENHANCED_INTEGRATOR] Архитектор зарегистрирован: {solver_id}")
            return solver_id
        except Exception as e:
            print(f"[ENHANCED_INTEGRATOR] Ошибка: {e}")
            return None

def register_architect_solver(solver_manager):
    """Регистрация архитектора в SolverManager."""
    integrator = EnhancedSpectraVortexIntegrator()
    return integrator.integrate_with_solver_manager(solver_manager)

def integrate_topological_architect():
    """Основная функция интеграции."""
    return EnhancedSpectraVortexIntegrator()

SpectraVortexTopologicalIntegrator = EnhancedSpectraVortexIntegrator
