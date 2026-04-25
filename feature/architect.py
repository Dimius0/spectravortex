"""
Главный модуль architect для топологического синтеза.
Версия для тестов — только compute_energy.
"""

from typing import List
from .component import Component

class TopologicalArchitect:
    """Топологический архитектор (упрощённая версия для тестов)"""
    
    def __init__(self, grid_shape=(32, 32)):
        self.grid_shape = grid_shape
    
    def compute_energy(self, components: List[Component]) -> float:
        """
        Вычисляет энергию конфигурации на основе фаз и зарядов.
        Чем ближе по фазе и чем больше заряды, тем меньше энергия.
        """
        import math
        energy = 0.0
        n = len(components)
        
        for i in range(n):
            for j in range(i + 1, n):
                c1 = components[i]
                c2 = components[j]
                
                # разность фаз (нормированная)
                phase_diff = abs(c1.temporal.phase - c2.temporal.phase)
                phase_diff = min(phase_diff, 2 * math.pi - phase_diff)
                
                # вклад зарядов (если заряды разных знаков — связь сильнее)
                charge_product = c1.charge * c2.charge
                if charge_product < 0:
                    factor = 1.5  # притяжение
                elif charge_product > 0:
                    factor = 0.8  # отталкивание
                else:
                    factor = 1.0  # нейтральные
                
                energy += phase_diff * factor
        
        return energy / max(1, n)