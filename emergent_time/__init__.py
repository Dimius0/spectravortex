"""
Ь Т  Я SPECTRAVORTEX
ерсия 2.0.0 - Стабильная и готовая к интеграции

мерджентное время — это не часы на стене, 
а живой процесс общения элементов системы.
"""

__version__ = "2.0.0"
__author__ = "SpectraVortex Team"
__description__ = "Emergent Time Module for SpectraVortex"

# сновные компоненты
from .core.emergent_engine import StableEmergentEngine, StableNode
from .integration.spectravortex_solver import EmergentTimeSolver, FieldSolution

__all__ = [
    "StableEmergentEngine",
    "StableNode", 
    "EmergentTimeSolver",
    "FieldSolution"
]

print(f"🌀 одуль эмерджентного времени v{__version__} загружен")
print(f"📚 {__description__}")
