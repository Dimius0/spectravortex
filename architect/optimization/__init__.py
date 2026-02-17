"""
Модуль оптимизации для топологического архитектора.
"""

try:
    from .placement_optimizer import PlacementOptimizer
    from .genetic_optimizer import GeneticOptimizer
    
    __all__ = ['PlacementOptimizer', 'GeneticOptimizer']
except ImportError:
    # Заглушки если файлы не загружаются
    class PlacementOptimizer:
        def __init__(self, grid_shape):
            self.grid_shape = grid_shape
    
    class GeneticOptimizer:
        def __init__(self):
            pass
    
    __all__ = ['PlacementOptimizer', 'GeneticOptimizer']
