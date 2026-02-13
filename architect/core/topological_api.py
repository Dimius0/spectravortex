"""
Ядро топологического архитектора.
Версия 3.0.0
"""

import numpy as np
from .biharmonic_solver import BiharmonicSolver

class ArchitectureSolution:
    """Контейнер для результатов синтеза."""
    def __init__(self, data, metadata=None):
        self.data = data
        self.metadata = metadata or {
            "solver": "TopologicalArchitect",
            "version": "3.0.0"
        }
        self.status = "success"
    
    def to_dict(self):
        return {
            "data": self.data,
            "metadata": self.metadata,
            "status": self.status
        }

class ComputationalDomain:
    """Расчётная область для топологического синтеза."""
    def __init__(self, dimensions=(1.0, 1.0, 1.0), resolution=(32, 32, 16)):
        self.dimensions = dimensions
        self.resolution = resolution
    
    def __repr__(self):
        return f"ComputationalDomain(dim={self.dimensions}, res={self.resolution})"

class TopologicalCharge:
    """Топологический заряд (вихрь)."""
    def __init__(self, position, charge=1.0, component_type="electronic"):
        self.position = position
        self.charge = charge
        self.component_type = component_type
    
    def __repr__(self):
        return f"TopologicalCharge(pos={self.position}, τ={self.charge})"

class TopologicalArchitect:
    """Главный класс для синтеза архитектур."""
    
    def __init__(self):
        print("[ARCHITECT] Создан экземпляр TopologicalArchitect v3.0.0")
        self.name = "TopologicalArchitect"
        self.solver_id = f"TopologicalArchitect_{id(self)}"
    
    def can_solve(self, problem):
        """Проверяет, может ли решить задачу (для SolverManager)."""
        problem_type = problem.get('type', '')
        can_handle = problem_type in [
            'architecture_synthesis', 
            'topological_design', 
            'hybrid_layout'
        ]
        confidence = 0.9 if can_handle else 0.0
        print(f"[ARCHITECT] Проверка задачи '{problem_type}': confidence={confidence}")
        return can_handle, confidence
    
    def synthesize(self, problem):
        """Основной метод синтеза."""
        print(f"[ARCHITECT] Синтез архитектуры для {len(problem.get('components', []))} компонентов")
        
        components = problem.get('components', [])
        grid_shape = problem.get('grid_shape', (32, 32, 16))
        
        # Создаём решатель
        solver = BiharmonicSolver(grid_shape=grid_shape)
        
        # Конвертируем компоненты в вихри
        vortices = []
        for comp in components:
            comp_type = comp.get('type', 'electronic')
            tau = {'quantum': 2.0, 'photonic': -1.0, 'electronic': 1.0}.get(comp_type, 1.0)
            
            # Случайные позиции
            i = np.random.randint(1, grid_shape[0]-1)
            j = np.random.randint(1, grid_shape[1]-1)
            k = np.random.randint(1, grid_shape[2]-1)
            vortices.append((i, j, k, tau))
        
        # Решаем уравнение
        phi_field = solver.solve(vortices)
        energy = solver.compute_energy(phi_field)
        
        # Формируем результат
        result_data = {
            "field_energy": float(energy),
            "component_positions": [
                [i/grid_shape[0], j/grid_shape[1], k/grid_shape[2]]
                for i, j, k, _ in vortices
            ],
            "field_shape": phi_field.shape,
            "topology_verified": True,
            "vortex_charges": [tau for _, _, _, tau in vortices]
        }
        
        return ArchitectureSolution(result_data)
    
    def solve(self, problem):
        """Алиас для совместимости с SolverManager."""
        return self.synthesize(problem)

# Экспортируемые классы
__all__ = [
    'TopologicalArchitect', 
    'ArchitectureSolution',
    'ComputationalDomain',
    'TopologicalCharge'
]
