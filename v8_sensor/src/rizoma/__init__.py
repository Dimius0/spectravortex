# Rizoma package
# елаем все основные классы доступными при импорте пакета

from .vortex import Vortex3D, SpectralComponent
from .resonance_v16_1 import Fractal3DCoherentSpectralResonance
from .quantum_analogy import QuantumState
from .topology import TopologicalNode, KnotType
from .endogenous import EndogenousCycle, EndogenousConfig
from .complexity_utils import detect_complexity, get_complexity_name

__all__ = [
    'Vortex3D', 'SpectralComponent',
    'Fractal3DCoherentSpectralResonance',
    'QuantumState',
    'TopologicalNode', 'KnotType',
    'EndogenousCycle', 'EndogenousConfig',
    'detect_complexity', 'get_complexity_name'
]
