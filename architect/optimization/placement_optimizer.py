"""
Оптимизатор размещения компонентов.
"""

import numpy as np

class PlacementOptimizer:
    """Оптимизатор размещения на основе минимизации энергии."""
    
    def __init__(self, grid_shape):
        self.grid_shape = grid_shape
        self.nx, self.ny, self.nz = grid_shape
        
    def random_positions(self, n_components):
        """Генерирует случайные начальные позиции."""
        positions = []
        for _ in range(n_components):
            i = np.random.randint(1, self.nx-1)
            j = np.random.randint(1, self.ny-1)
            k = np.random.randint(1, self.nz-1)
            positions.append([i, j, k])
        return positions
    
    def optimize_energy(self, positions, charges, iterations=50):
        """
        Оптимизирует позиции для минимизации энергии взаимодействия.
        
        Args:
            positions: список [i, j, k]
            charges: список зарядов τ
            iterations: число итераций
            
        Returns:
            optimized_positions: оптимизированные позиции
        """
        print(f"[OPTIMIZER] Оптимизация {len(positions)} компонентов...")
        
        # Преобразуем в numpy массив
        pos_array = np.array(positions, dtype=float)
        
        # Простая оптимизация: смещаем отталкивающиеся заряды
        for it in range(iterations):
            for i in range(len(pos_array)):
                # Сила отталкивания от других компонентов
                force = np.zeros(3)
                for j in range(len(pos_array)):
                    if i != j:
                        # Вектор от i к j
                        vec = pos_array[j] - pos_array[i]
                        distance = np.linalg.norm(vec) + 1e-6
                        
                        # Сила пропорциональна произведению зарядов / расстоянию²
                        strength = charges[i] * charges[j] / (distance ** 2)
                        
                        # Отталкивание для одинаковых зарядов, притяжение для разных
                        if charges[i] * charges[j] > 0:
                            force -= 0.01 * strength * vec / distance
                        else:
                            force += 0.01 * strength * vec / distance
                
                # Применяем силу с ограничением
                pos_array[i] += force
                pos_array[i] = np.clip(pos_array[i], 1, np.array(self.grid_shape)-2)
        
        print(f"[OPTIMIZER] Оптимизация завершена за {iterations} итераций")
        return pos_array.tolist()
    
    def enforce_min_distance(self, positions, min_distance=2):
        """Обеспечивает минимальное расстояние между компонентами."""
        pos_array = np.array(positions)
        n = len(pos_array)
        
        for i in range(n):
            for j in range(i+1, n):
                dist = np.linalg.norm(pos_array[i] - pos_array[j])
                if dist < min_distance:
                    # Раздвигаем компоненты
                    direction = pos_array[j] - pos_array[i]
                    if np.linalg.norm(direction) > 0:
                        direction = direction / np.linalg.norm(direction)
                        shift = (min_distance - dist) / 2
                        pos_array[i] -= direction * shift
                        pos_array[j] += direction * shift
        
        return pos_array.tolist()
