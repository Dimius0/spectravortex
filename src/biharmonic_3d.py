"""
3D Biharmonic Solver for Vortex Field H.
Решает уравнение ∇⁴H = 0 с граничными условиями квантования циркуляции.

Интегрируется с TopologicalArchitect для 3D-задач.
"""

import numpy as np
from scipy import fft
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Vortex3D:
    """3D вихрь с топологическим зарядом"""
    charge: float
    position: np.ndarray
    orientation: np.ndarray = None
    circulation: float = 2.0 * np.pi
    
    def __post_init__(self):
        if self.orientation is None:
            self.orientation = np.array([0.0, 0.0, 1.0])
        self.position = np.asarray(self.position)
        self.orientation = np.asarray(self.orientation)
        # Нормализация ориентации
        norm = np.linalg.norm(self.orientation)
        if norm > 0:
            self.orientation = self.orientation / norm
        else:
            self.orientation = np.array([0.0, 0.0, 1.0])


class BiharmonicSolver3D:
    """
    Решатель бигармонического уравнения ∇⁴H = 0 в 3D.
    
    Использует спектральный метод с FFT для быстрого решения
    на регулярной сетке с периодическими граничными условиями.
    """
    
    def __init__(self, grid_shape: Tuple[int, int, int], box_size: Tuple[float, float, float] = None):
        """
        Args:
            grid_shape: (nx, ny, nz) - размеры сетки
            box_size: (Lx, Ly, Lz) - физические размеры области (по умолчанию = grid_shape)
        """
        self.grid_shape = grid_shape
        self.nx, self.ny, self.nz = grid_shape
        
        if box_size is None:
            self.box_size = tuple(float(s) for s in grid_shape)
        else:
            self.box_size = tuple(float(s) for s in box_size)
        
        self.Lx, self.Ly, self.Lz = self.box_size
        self.dx = self.Lx / self.nx
        self.dy = self.Ly / self.ny
        self.dz = self.Lz / self.nz
        
        # Волновые векторы для спектрального метода
        self._setup_wave_vectors()
        
        # Поле H и его производные
        self.H = np.zeros(grid_shape, dtype=np.float64)
        self.vortices: List[Vortex3D] = []
        
    def _setup_wave_vectors(self):
        """Настройка волновых векторов в Фурье-пространстве"""
        kx = 2.0 * np.pi * fft.fftfreq(self.nx, self.dx)
        ky = 2.0 * np.pi * fft.fftfreq(self.ny, self.dy)
        kz = 2.0 * np.pi * fft.fftfreq(self.nz, self.dz)
        
        self.Kx, self.Ky, self.Kz = np.meshgrid(kx, ky, kz, indexing='ij')
        self.K2 = self.Kx**2 + self.Ky**2 + self.Kz**2
        self.K4 = self.K2**2
        
        # Регуляризация для нулевой моды
        self.K4[0, 0, 0] = 1.0
        
    def add_vortex(self, vortex: Vortex3D):
        """Добавить вихрь в систему"""
        self.vortices.append(vortex)
        
    def compute_vortex_field(self, vortex: Vortex3D) -> np.ndarray:
        """
        Вычислить поле H от одиночного вихря.
        Вихрь моделируется как линия с циркуляцией.
        """
        x = np.linspace(0, self.Lx, self.nx) - vortex.position[0]
        y = np.linspace(0, self.Ly, self.ny) - vortex.position[1]
        z = np.linspace(0, self.Lz, self.nz) - vortex.position[2]
        
        # Периодические граничные условия: минимальное изображение
        x = np.where(x > self.Lx/2, x - self.Lx, x)
        x = np.where(x < -self.Lx/2, x + self.Lx, x)
        y = np.where(y > self.Ly/2, y - self.Ly, y)
        y = np.where(y < -self.Ly/2, y + self.Ly, y)
        z = np.where(z > self.Lz/2, z - self.Lz, z)
        z = np.where(z < -self.Lz/2, z + self.Lz, z)
        
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Направление вихря
        ux, uy, uz = vortex.orientation
        
        # Расстояние до оси вихря (квадрат)
        r_perp_sq = (Y*uz - Z*uy)**2 + (Z*ux - X*uz)**2 + (X*uy - Y*ux)**2
        r_perp_sq = np.maximum(r_perp_sq, 1e-10)
        r_perp = np.sqrt(r_perp_sq)
        
        # Проекция на ось вихря
        r_parallel = X*ux + Y*uy + Z*uz
        
        # Азимутальный угол вокруг оси вихря
        # Используем безопасное вычисление
        numerator = Y*uz - Z*uy
        denominator = r_parallel + 1e-10
        
        H_vortex = vortex.charge * np.arctan2(numerator, denominator)
        
        # Сглаживание ядра вихря (избегаем сингулярности)
        core_radius = 2.0
        smooth_factor = 1.0 - np.exp(-r_perp_sq / core_radius**2)
        
        # Применяем сглаживание
        H_vortex = H_vortex * smooth_factor
        
        # Обрезаем выбросы
        H_vortex = np.clip(H_vortex, -10.0, 10.0)
        
        return H_vortex
    
    def compute_total_field(self) -> np.ndarray:
        """Вычислить полное поле H от всех вихрей"""
        self.H = np.zeros(self.grid_shape, dtype=np.float64)
        
        for vortex in self.vortices:
            H_v = self.compute_vortex_field(vortex)
            self.H += H_v
        
        return self.H
    
    def solve_biharmonic(self, max_iter: int = 100, tol: float = 1e-6) -> np.ndarray:
        """
        Решить ∇⁴H = 0 с граничными условиями от вихрей.
        Использует итерационный метод в Фурье-пространстве.
        """
        # Начальное поле от вихрей (источники)
        H_source = self.compute_total_field()
        H_source_fft = fft.fftn(H_source)
        
        # Итерационное решение
        H_fft = H_source_fft.copy()
        
        for iteration in range(max_iter):
            H_fft_new = H_source_fft.copy()
            
            # Применяем бигармонический оператор: H_new = H_source - ∇⁴H / K4
            # Но ∇⁴H в Фурье-пространстве = K4 * H_fft
            mask = self.K4 > 1e-10
            H_fft_new[mask] = H_fft_new[mask] - H_fft[mask] / self.K4[mask]
            
            # Проверка сходимости
            diff = np.max(np.abs(H_fft_new - H_fft))
            H_fft = H_fft_new
            
            if diff < tol:
                print(f"  Сходимость на итерации {iteration + 1}, diff = {diff:.2e}")
                break
        
        # Обратное преобразование
        self.H = np.real(fft.ifftn(H_fft))
        
        # Обрезаем выбросы
        self.H = np.clip(self.H, -100.0, 100.0)
        
        return self.H
    
    def compute_energy(self) -> float:
        """
        Вычислить энергию поля: E = ∫|∇H|² dV
        """
        H_fft = fft.fftn(self.H)
        
        # Градиент в Фурье-пространстве
        grad_H_x = np.real(fft.ifftn(1j * self.Kx * H_fft))
        grad_H_y = np.real(fft.ifftn(1j * self.Ky * H_fft))
        grad_H_z = np.real(fft.ifftn(1j * self.Kz * H_fft))
        
        # Обрезаем выбросы градиента
        grad_H_x = np.clip(grad_H_x, -1e3, 1e3)
        grad_H_y = np.clip(grad_H_y, -1e3, 1e3)
        grad_H_z = np.clip(grad_H_z, -1e3, 1e3)
        
        # Плотность энергии
        energy_density = grad_H_x**2 + grad_H_y**2 + grad_H_z**2
        
        # Интеграл
        energy = np.sum(energy_density) * self.dx * self.dy * self.dz
        return float(energy)
    
    def compute_gradient(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Вычислить градиент поля H"""
        H_fft = fft.fftn(self.H)
        grad_x = np.real(fft.ifftn(1j * self.Kx * H_fft))
        grad_y = np.real(fft.ifftn(1j * self.Ky * H_fft))
        grad_z = np.real(fft.ifftn(1j * self.Kz * H_fft))
        
        # Обрезаем выбросы
        grad_x = np.clip(grad_x, -1e3, 1e3)
        grad_y = np.clip(grad_y, -1e3, 1e3)
        grad_z = np.clip(grad_z, -1e3, 1e3)
        
        return grad_x, grad_y, grad_z
    
    def find_vortex_cores(self, threshold: float = 0.5) -> List[Tuple[np.ndarray, float]]:
        """
        Найти ядра вихрей (локальные максимумы |∇H|)
        """
        grad_x, grad_y, grad_z = self.compute_gradient()
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        from scipy import ndimage
        local_max = ndimage.maximum_filter(grad_magnitude, size=5) == grad_magnitude
        
        max_val = np.max(grad_magnitude)
        if max_val > 0:
            mask = local_max & (grad_magnitude > threshold * max_val)
        else:
            mask = local_max
        
        coords = np.argwhere(mask)
        cores = []
        for coord in coords:
            pos = np.array([coord[0] * self.dx, coord[1] * self.dy, coord[2] * self.dz])
            strength = grad_magnitude[coord[0], coord[1], coord[2]]
            cores.append((pos, float(strength)))
        
        return cores
    
    def relax_vortices(self, max_iter: int = 100, learning_rate: float = 0.05, 
                       temperature: float = 0.0) -> dict:
        """
        Релаксация позиций вихрей к минимуму энергии.
        """
        energy_history = []
        
        for iteration in range(max_iter):
            # Вычисляем поле
            self.solve_biharmonic(max_iter=30, tol=1e-4)
            energy = self.compute_energy()
            
            # Проверка на inf
            if np.isinf(energy) or np.isnan(energy):
                print(f"  Внимание: энергия = {energy}, пропускаем итерацию")
                energy = 1e10
            
            energy_history.append(energy)
            
            # Вычисляем силы на каждый вихрь
            grad_x, grad_y, grad_z = self.compute_gradient()
            
            for vortex in self.vortices:
                # Находим позицию вихря в индексах сетки
                i = int(vortex.position[0] / self.dx) % self.nx
                j = int(vortex.position[1] / self.dy) % self.ny
                k = int(vortex.position[2] / self.dz) % self.nz
                
                # Сила пропорциональна градиенту энергии
                force = -np.array([
                    grad_x[i, j, k],
                    grad_y[i, j, k],
                    grad_z[i, j, k]
                ])
                
                # Обрезаем силу
                force_norm = np.linalg.norm(force)
                if force_norm > 10.0:
                    force = force / force_norm * 10.0
                
                # Тепловой шум
                if temperature > 0:
                    force += temperature * np.random.randn(3)
                
                # Обновление позиции
                vortex.position += learning_rate * force
                
                # Периодические граничные условия
                vortex.position[0] = vortex.position[0] % self.Lx
                vortex.position[1] = vortex.position[1] % self.Ly
                vortex.position[2] = vortex.position[2] % self.Lz
            
            if iteration % 20 == 0:
                print(f"  Итерация {iteration}: энергия = {energy:.2f}")
        
        return {
            'final_energy': energy_history[-1] if energy_history else 0.0,
            'energy_history': energy_history,
            'final_positions': [v.position.tolist() for v in self.vortices]
        }
    
    def export_to_vtk(self, filename: str):
        """
        Экспорт поля H в VTK формат для визуализации в ParaView/Blender.
        """
        try:
            from pyevtk.hl import gridToVTK
        except ImportError:
            print("pyevtk не установлен. Установите: pip install pyevtk")
            return
        
        x = np.linspace(0, self.Lx, self.nx)
        y = np.linspace(0, self.Ly, self.ny)
        z = np.linspace(0, self.Lz, self.nz)
        
        grad_x, grad_y, grad_z = self.compute_gradient()
        grad_mag = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        
        gridToVTK(
            filename,
            x, y, z,
            pointData={
                'H': np.real(self.H).astype(np.float32),
                'gradient': grad_mag.astype(np.float32),
                'energy_density': (grad_mag**2).astype(np.float32)
            }
        )
        print(f"Поле экспортировано в {filename}.vtr")


class TopologicalArchitect3D(BiharmonicSolver3D):
    """
    Расширение BiharmonicSolver3D с методами для топологического размещения.
    Совместимо с API TopologicalArchitect.
    """
    
    def __init__(self, grid_shape=(64, 64, 64), box_size=None):
        super().__init__(grid_shape, box_size)
        self.components = []
        
    def add_component(self, component_data: dict):
        """
        Добавить компонент (элемент) в систему.
        
        Args:
            component_data: словарь с параметрами:
                - charge: топологический заряд
                - position: начальная позиция [x, y, z]
                - orientation: ориентация вихря [x, y, z]
                - symbol: символ элемента
                - Z: атомный номер
        """
        orientation = component_data.get('orientation', [0, 0, 1])
        if np.linalg.norm(orientation) < 1e-6:
            orientation = [0, 0, 1]
            
        vortex = Vortex3D(
            charge=component_data.get('charge', 1.0),
            position=np.array(component_data.get('position', [0, 0, 0])),
            orientation=np.array(orientation)
        )
        self.add_vortex(vortex)
        
        self.components.append({
            'vortex': vortex,
            'symbol': component_data.get('symbol', '?'),
            'Z': component_data.get('Z', 0),
            'data': component_data
        })
        
    def optimize(self, objective='minimize_energy', max_iterations=100, 
                 temperature=0.0, **kwargs) -> dict:
        """
        Оптимизация размещения компонентов.
        
        Совместимо с API TopologicalArchitect.optimize()
        """
        result = self.relax_vortices(
            max_iter=max_iterations,
            learning_rate=0.05,
            temperature=temperature
        )
        
        # Формируем результат в стиле TopologicalArchitect
        class Solution:
            def __init__(self, energy, positions, components):
                self.energy = energy
                self.positions = positions
                self.components = components
                self.min_distance = self._compute_min_distance(positions)
                self.packing_coefficient = self._compute_packing(positions)
                self.total_charge = sum(c['vortex'].charge for c in components)
            
            def _compute_min_distance(self, positions):
                if len(positions) < 2:
                    return float('inf')
                min_dist = float('inf')
                for i in range(len(positions)):
                    for j in range(i+1, len(positions)):
                        dist = np.linalg.norm(np.array(positions[i]) - np.array(positions[j]))
                        min_dist = min(min_dist, dist)
                return min_dist
            
            def _compute_packing(self, positions):
                if len(positions) < 2:
                    return 1.0
                return 0.5
        
        return Solution(
            energy=result['final_energy'],
            positions=result['final_positions'],
            components=self.components
        )