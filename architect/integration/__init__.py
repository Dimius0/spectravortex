"""
Интеграция с SpectraVortex.
"""

from .vortex_integrator import (
    SpectraVortexTopologicalIntegrator,
    register_architect_solver,
    integrate_topological_architect
)

__all__ = [
    'SpectraVortexTopologicalIntegrator',
    'register_architect_solver',
    'integrate_topological_architect'
]
