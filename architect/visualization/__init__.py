"""
Модуль визуализации для топологического архитектора.
"""

try:
    from .architecture_visualizer import (
        plot_3d_architecture,
        plot_field_slices,
        plot_energy_density
    )
    
    __all__ = [
        'plot_3d_architecture',
        'plot_field_slices', 
        'plot_energy_density'
    ]
except ImportError:
    # Заглушки
    def plot_3d_architecture(*args, **kwargs):
        print("Визуализация недоступна (требуется matplotlib)")
        return None
    
    def plot_field_slices(*args, **kwargs):
        print("Визуализация недоступна (требуется matplotlib)")
        return None
    
    def plot_energy_density(*args, **kwargs):
        print("Визуализация недоступна (требуется matplotlib)")
        return None
    
    __all__ = [
        'plot_3d_architecture',
        'plot_field_slices', 
        'plot_energy_density'
    ]
