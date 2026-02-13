import numpy as np
from numba import jit
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from scipy import sparse
import warnings

@dataclass
class NodeState:
    """аучно обоснованное состояние узла"""
    id: int
    health: float = 1.0          # [0, 1] - интегральный показатель здоровья
    load: float = 0.0            # [0, 1] - текущая нагрузка
    temperature: float = 0.0     # ормализованная температура [0, 1]
    noise_level: float = 0.01    # ровень внутреннего шума
    
    def __post_init__(self):
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Строгая валидация физических параметров"""
        assert 0 <= self.health <= 1.0, f"health={self.health} вне диапазона [0,1]"
        assert 0 <= self.load <= 1.0, f"load={self.load} вне диапазона [0,1]"
        assert 0 <= self.temperature <= 1.0, f"temp={self.temperature} вне [0,1]"
        assert self.noise_level >= 0, f"noise={self.noise_level} должно быть ≥0"

@dataclass
class TemporalState:
    """олное временное состояние с ковариационной матрицей"""
    phase: float                  # Текущая фаза [0, 2π]
    frequency: float             # гновенная частота
    frequency_std: float = 0.0   # Стандартное отклонение частоты
    phase_confidence: float = 1.0 # остоверность оценки фазы [0,1]
    
    # овариация для фильтра алмана
    covariance: np.ndarray = None
    
    def __post_init__(self):
        if self.covariance is None:
            self.covariance = np.eye(2) * 0.01

# птимизированные функции для Numba
@jit(nopython=True)
def _kuramoto_step_fast(phases, frequencies, connectivity_data, 
                        connectivity_indices, connectivity_indptr, 
                        K, dt, noise_level):
    """ыстрый шаг урамото с использованием разреженных матриц"""
    N = len(phases)
    new_phases = np.zeros_like(phases)
    
    for i in range(N):
        coupling_sum = 0.0
        
        # спользуем разреженную структуру для эффективности
        start_idx = connectivity_indptr[i]
        end_idx = connectivity_indptr[i + 1]
        
        for idx in range(start_idx, end_idx):
            j = connectivity_indices[idx]
            weight = connectivity_data[idx]
            phase_diff = phases[j] - phases[i]
            coupling_sum += weight * np.sin(phase_diff)
        
        dphase = frequencies[i] + (K / N) * coupling_sum
        dphase += noise_level * np.random.randn()
        new_phases[i] = phases[i] + dt * dphase
    
    new_phases = new_phases % (2 * np.pi)
    return new_phases

@jit(nopython=True)
def _calculate_energy_fast(phases, frequencies, connectivity_data,
                          connectivity_indices, connectivity_indptr):
    """ыстрое вычисление энергии"""
    N = len(phases)
    kinetic = -np.sum(frequencies * phases)
    potential = 0.0
    
    for i in range(N):
        start_idx = connectivity_indptr[i]
        end_idx = connectivity_indptr[i + 1]
        
        for idx in range(start_idx, end_idx):
            j = connectivity_indices[idx]
            weight = connectivity_data[idx]
            potential += weight * np.cos(phases[j] - phases[i])
    
    potential = -potential / (2 * N)
    return kinetic + potential

class EmergentTimeEngine:
    """
    птимизированный движок эмерджентного времени
    """
    
    def __init__(self, 
                 nodes: List[NodeState],
                 connectivity_matrix: Optional[np.ndarray] = None,
                 dt: float = 0.01,
                 validation_mode: bool = True):
        
        self.nodes = nodes
        self.N = len(nodes)
        self.dt = dt
        self.validation_mode = validation_mode
        
        # нициализация матрицы связности
        self.connectivity = self._initialize_connectivity(connectivity_matrix)
        
        # одготовка данных для быстрых функций
        self._prepare_sparse_data()
        
        # нициализация временных состояний
        self.temporal_states = self._initialize_temporal_states()
        
        # ониторинг
        self.energy_history = []
        self.order_history = []
        
        if validation_mode:
            self.run_initial_validation()
    
    def _prepare_sparse_data(self):
        """одготовка данных разреженной матрицы для Numba"""
        csr = self.connectivity.tocsr()
        self.connectivity_data = csr.data
        self.connectivity_indices = csr.indices
        self.connectivity_indptr = csr.indptr
    
    def _initialize_connectivity(self, matrix: Optional[np.ndarray]) -> sparse.csr_matrix:
        """нициализация матрицы связности"""
        if matrix is None:
            # алая мировая сеть по умолчанию (более реалистичная)
            matrix = self._create_small_world_network()
        else:
            assert matrix.shape == (self.N, self.N), \
                f"атрица {matrix.shape} не соответствует числу узлов {self.N}"
            assert np.all(matrix >= 0), "атрица связности должна быть неотрицательной"
        
        return sparse.csr_matrix(matrix)
    
    def _create_small_world_network(self) -> np.ndarray:
        """Создание малой мировой сети (оттс-Строгац)"""
        matrix = np.zeros((self.N, self.N))
        k = min(4, self.N // 4)  # оличество соседей с каждой стороны
        
        for i in range(self.N):
            for j in range(1, k//2 + 1):
                matrix[i, (i+j) % self.N] = 1.0
                matrix[i, (i-j) % self.N] = 1.0
        
        # ереподключение с вероятностью 0.1
        for i in range(self.N):
            for j in range(self.N):
                if matrix[i, j] == 1 and np.random.rand() < 0.1:
                    matrix[i, j] = 0
                    available = [x for x in range(self.N) if x != i and matrix[i, x] == 0]
                    if available:
                        new_j = np.random.choice(available)
                        matrix[i, new_j] = 1.0
        
        return matrix
    
    def _initialize_temporal_states(self) -> Dict[int, TemporalState]:
        """нициализация временных состояний"""
        states = {}
        
        for node in self.nodes:
            # астота зависит от здоровья
            health_factor = np.exp(-1.5 * (1 - node.health))
            load_factor = 1.0 - 0.2 * node.load
            frequency = 1.0 * health_factor * load_factor
            frequency = np.clip(frequency, 0.3, 3.0)  # олее узкий диапазон
            
            phase = np.random.uniform(0, 2 * np.pi)
            
            states[node.id] = TemporalState(
                phase=phase,
                frequency=frequency,
                frequency_std=0.1 * frequency,
                phase_confidence=node.health
            )
        
        return states
    
    def run_initial_validation(self):
        """ачальная валидация"""
        print("🔬 Я ССТЫ")
        print(f"  злов: {self.N}")
        print(f"  Связей: {self.connectivity.nnz}")
        print(f"  лотность сети: {self.connectivity.nnz/(self.N*self.N):.1%}")
    
    def evolve(self, steps: int = 1, K: float = 2.0):
        """
        ффективная эволюция системы
        """
        for step in range(steps):
            phases = np.array([s.phase for s in self.temporal_states.values()])
            frequencies = np.array([s.frequency for s in self.temporal_states.values()])
            
            new_phases = _kuramoto_step_fast(
                phases, frequencies,
                self.connectivity_data,
                self.connectivity_indices,
                self.connectivity_indptr,
                K, self.dt, 0.01
            )
            
            # бновление фаз и адаптация частот
            for idx, node_id in enumerate(self.temporal_states.keys()):
                state = self.temporal_states[node_id]
                old_phase = state.phase
                state.phase = new_phases[idx]
                
                # ростая адаптация частоты
                self._adapt_frequency_simple(state, old_phase, new_phases[idx])
            
            # ониторинг (только каждые 10 шагов для производительности)
            if self.validation_mode and step % 10 == 0:
                self.energy_history.append(
                    _calculate_energy_fast(
                        phases, frequencies,
                        self.connectivity_data,
                        self.connectivity_indices,
                        self.connectivity_indptr
                    )
                )
                
                order_param = np.abs(np.mean(np.exp(1j * phases)))
                self.order_history.append(order_param)
    
    def _adapt_frequency_simple(self, state: TemporalState, old_phase: float, new_phase: float):
        """ростая и эффективная адаптация частоты"""
        # даптация на основе скорости изменения фазы
        phase_velocity = (new_phase - old_phase) / self.dt
        
        # лавная коррекция к средней частоте (1.0)
        target_frequency = 1.0
        correction = 0.02 * (target_frequency - state.frequency)
        
        # чёт скорости для динамической адаптации
        if abs(phase_velocity) > 5.0:  # ыстрое изменение
            correction *= 1.5
        elif abs(phase_velocity) < 0.5:  # едленное изменение
            correction *= 0.5
        
        state.frequency += correction
        state.frequency = np.clip(state.frequency, 0.3, 3.0)
    
    def calculate_system_energy(self) -> float:
        """ычисление энергии системы"""
        phases = np.array([s.phase for s in self.temporal_states.values()])
        frequencies = np.array([s.frequency for s in self.temporal_states.values()])
        
        return _calculate_energy_fast(
            phases, frequencies,
            self.connectivity_data,
            self.connectivity_indices,
            self.connectivity_indptr
        )
    
    def get_synchronization_metrics(self) -> Dict[str, float]:
        """нализ синхронизации"""
        phases = np.array([s.phase for s in self.temporal_states.values()])
        frequencies = np.array([s.frequency for s in self.temporal_states.values()])
        
        order_param = np.abs(np.mean(np.exp(1j * phases)))
        phase_variance = np.var(phases)
        freq_mean = np.mean(frequencies)
        freq_cv = np.std(frequencies) / freq_mean if freq_mean != 0 else 0
        
        # ыстрый расчёт энтропии
        bins = np.linspace(0, 2*np.pi, 21)
        hist, _ = np.histogram(phases, bins=bins)
        hist_norm = hist / np.sum(hist) if np.sum(hist) > 0 else np.ones_like(hist)/20
        phase_entropy = -np.sum(hist_norm * np.log(hist_norm + 1e-10))
        
        return {
            'order_parameter': order_param,
            'phase_variance': phase_variance,
            'frequency_cv': freq_cv,
            'phase_entropy': phase_entropy,
            'is_synchronized': order_param > 0.7 and phase_variance < 1.0,
            'frequency_mean': freq_mean
        }
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Статистика производительности"""
        if not self.order_history:
            return {}
        
        return {
            'final_order': self.order_history[-1] if self.order_history else 0,
            'max_order': max(self.order_history) if self.order_history else 0,
            'min_order': min(self.order_history) if self.order_history else 0,
            'energy_change': abs(self.energy_history[-1] - self.energy_history[0]) if len(self.energy_history) > 1 else 0
        }
