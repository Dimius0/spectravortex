"""
Топологический архитектор для SpectraVortex.
Синтез гибридных архитектур на основе ВММП.
Версия 3.0.0
"""

from .core.topological_api import (
    TopologicalArchitect,
    ArchitectureSolution,
    ComputationalDomain,
    TopologicalCharge
)

from .integration.vortex_integrator import (
    SpectraVortexTopologicalIntegrator,
    integrate_topological_architect
)

__version__ = "3.0.0"
__all__ = [
    'TopologicalArchitect',
    'ArchitectureSolution',
    'ComputationalDomain',
    'TopologicalCharge',
    'SpectraVortexTopologicalIntegrator',
    'integrate_topological_architect'
]

print(f"[ARCHITECT] Модуль v{__version__} загружен успешно.")