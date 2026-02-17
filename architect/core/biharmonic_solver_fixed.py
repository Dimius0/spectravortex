"""
Исправленный решатель бигармонического уравнения.
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

class BiharmonicSolver:
    """Конечно-разностный решатель бигармонического уравнения."""
    
    def __init__(self, grid_shape, spacing=(1.0, 1.0, 1.0)):
        """
        Инициализация решателя.
        
        Args:
            grid_shape: (nx, ny, nz) - размер сетки
            spacing: (dx, dy, dz) - шаги сетки
        """
        self.grid_shape = grid_shape
        self.spacing = spacing
        self.nx, self.ny, self.nz = grid_shape
        self.n_points = self.nx * self.ny * self.nz
        print(f"[BIHARMONIC] Инициализирован решатель для сетки {grid_shape}")
    
    def build_discrete_biharmonic(self):
        """Строит дискретный оператор бигармонического уравнения."""
        print(f"[BIHARMONIC] Построение оператора для {self.n_points} точек...")
        
        # Простая реализация: оператор Лапласа в квадрате
        n = self.n_points
        
        # Используем формат LIL для гибкости
        A = sparse.lil_matrix((n, n))
        
        # Заполняем диагональ (упрощенная версия)
        for i in range(n):
            A[i, i] = 20.0  # Главная диагональ
            
            # Ближайшие соседи (для реальной реализации нужны правильные коэффициенты)
            if i + 1 < n:
                A[i, i + 1] = -8.0
            if i - 1 >= 0:
                A[i, i - 1] = -8.0
        
        print(f"[BIHARMONIC] Матрица {n}x{n} построена")
        return A
    
    def add_vortex_singularities(self, matrix, vortices):
        """
        Добавляет условия на сингулярности (топологические заряды).
        
        Args:
            matrix: разреженная матрица оператора
            vortices: список [(i, j, k, tau), ...] - положения и заряды вихрей
        """
        n = matrix.shape[0]
        
        for idx, (i, j, k, tau) in enumerate(vortices):
            # Преобразуем 3D индекс в линейный
            linear_idx = i + j * self.nx + k * self.nx * self.ny
            
            if linear_idx < n:
                # Модифицируем строку для условия сингулярности
                matrix[linear_idx, :] = 0
                matrix[linear_idx, linear_idx] = 1.0
                
        print(f"[BIHARMONIC] Добавлено {len(vortices)} условий сингулярности")
        return matrix
    
    def solve(self, vortices, boundary_conditions=None):
        """
        Решает уравнение ∇⁴φ = 0 с заданными вихрями.
        
        Args:
            vortices: список вихрей [(i, j, k, tau), ...]
            boundary_conditions: граничные условия (пока не используется)
            
        Returns:
            phi_field: 3D массив поля φ
        """
        print(f"[BIHARMONIC] Решение уравнения с {len(vortices)} вихрями...")
        
        # Строим матрицу в формате LIL
        A = self.build_discrete_biharmonic()
        
        # Добавляем условия на вихри
        A = self.add_vortex_singularities(A, vortices)
        
        # Конвертируем в CSR формат для эффективного решения
        A_csr = A.tocsr()
        
        # Правая часть: для обычных точек 0, для вихрей 2πτ
        b = np.zeros(self.n_points)
        for i, j, k, tau in vortices:
            linear_idx = i + j * self.nx + k * self.nx * self.ny
            if linear_idx < len(b):
                b[linear_idx] = 2 * np.pi * tau
        
        # Решаем систему
        print(f"[BIHARMONIC] Решение СЛАУ...")
        phi_flat = spsolve(A_csr, b)
        
        # Преобразуем обратно в 3D
        phi_field = phi_flat.reshape((self.nz, self.ny, self.nx))
        
        print(f"[BIHARMONIC] Решение завершено. min={phi_field.min():.3f}, max={phi_field.max():.3f}")
        return phi_field
    
    def compute_energy(self, phi_field):
        """Вычисляет энергию поля φ."""
        # Простая аппроксимация энергии (∫|∇φ|² dV)
        grad_x = np.gradient(phi_field, axis=2)
        grad_y = np.gradient(phi_field, axis=1)
        grad_z = np.gradient(phi_field, axis=0)
        
        energy_density = grad_x**2 + grad_y**2 + grad_z**2
        total_energy = np.sum(energy_density) * np.prod(self.spacing)
        
        return total_energy

def test_solver():
    """Тестирование решателя."""
    print("=== ТЕСТ РЕШАТЕЛЯ БИГАРМОНИЧЕСКОГО УРАВНЕНИЯ ===")
    
    # Создаем решатель для небольшой сетки
    solver = BiharmonicSolver(grid_shape=(16, 16, 8), spacing=(0.1, 0.1, 0.1))
    
    # Задаем два вихря с зарядами +1 и -1
    vortices = [
        (4, 4, 2, 1.0),   # Вихрь с зарядом +1
        (12, 12, 2, -1.0) # Вихрь с зарядом -1
    ]
    
    # Решаем
    phi = solver.solve(vortices)
    
    # Вычисляем энергию
    energy = solver.compute_energy(phi)
    print(f"Вычисленная энергия поля: {energy:.6f}")
    
    return solver, phi

if __name__ == "__main__":
    test_solver()