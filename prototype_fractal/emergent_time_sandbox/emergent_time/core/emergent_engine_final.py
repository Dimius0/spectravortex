"""
ЬЯ ТЯ СЯ Я Т 
С улучшенной синхронизацией и исправленными багами
"""

import numpy as np
from numba import jit
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from scipy import sparse
import warnings

@dataclass
class NodeState:
    """Состояние узла с физическими параметрами"""
    id: int
    health: float = 1.0          # [0, 1] - здоровье
    load: float = 0.0            # [0, 1] - нагрузка
    temperature: float = 0.0     # [0, 1] - температура
    noise_level: float = 0.01    # уровень шума
    
    def __post_init__(self):
        self._validate_parameters()
    
    def _validate_parameters(self):
        """алидация параметров"""
        self.health = np.clip(self.health, 0.1, 1.0)
        self.load = np.clip(self.load, 0.0, 1.0)
        self.temperature = np.clip(self.temperature, 0.0, 1.0)
        self.noise_level = max(0.0, self.noise_level)

@dataclass
class TemporalState:
    """ременное состояние узла"""
    phase: float                  # аза [0, 2π]
    frequency: float             # астота
    natural_frequency: float     # стественная частота (не изменяется)
    phase_confidence: float = 1.0
    
    def __post_init__(self):
        self.natural_frequency = self.frequency

# птимизированные функции Numba
@jit(nopython=True, parallel=False, fastmath=True)
def _kuramoto_step_optimized(phases, natural_frequencies, connectivity_data,
                            connectivity_indices, connectivity_indptr,
                            K, dt, noise_level, current_frequencies):
    """
    птимизированный шаг урамото с адаптивными частотами
    """
    N = len(phases)
    new_phases = np.zeros_like(phases)
    
    for i in range(N):
        coupling_sum = 0.0
        neighbor_count = 0
        
        # Суммирование по соседям
        start_idx = connectivity_indptr[i]
        end_idx = connectivity_indptr[i + 1]
        
        for idx in range(start_idx, end_idx):
            j = connectivity_indices[idx]
            weight = connectivity_data[idx]
            phase_diff = phases[j] - phases[i]
            coupling_sum += weight * np.sin(phase_diff)
            neighbor_count += 1
        
        # даптивная частота на основе соседей
        if neighbor_count > 0:
            # щем среднюю фазу соседей
            neighbor_phase_sum_sin = 0.0
            neighbor_phase_sum_cos = 0.0
            
            for idx in range(start_idx, end_idx):
                j = connectivity_indices[idx]
                weight = connectivity_data[idx]
                neighbor_phase_sum_sin += weight * np.sin(phases[j])
                neighbor_phase_sum_cos += weight * np.cos(phases[j])
            
            # Средняя фаза соседей
            mean_phase = np.arctan2(neighbor_phase_sum_sin, neighbor_phase_sum_cos)
            
            # оррекция частоты к средней фазе соседей
            phase_diff_to_mean = mean_phase - phases[i]
            phase_diff_to_mean = (phase_diff_to_mean + np.pi) % (2 * np.pi) - np.pi
            
            # даптация: частота стремится к синхронизации с соседями
            freq_correction = 0.1 * np.sin(phase_diff_to_mean)
            current_frequencies[i] = natural_frequencies[i] + freq_correction
        
        # граничение частот
        current_frequencies[i] = np.clip(current_frequencies[i], 0.3, 3.0)
        
        # равнение урамото
        dphase = current_frequencies[i]
        if neighbor_count > 0:
            dphase += (K / neighbor_count) * coupling_sum
        
        # обавляем шум
        dphase += noise_level * np.random.randn()
        
        new_phases[i] = phases[i] + dt * dphase
    
    # ормализация фаз
    new_phases = new_phases % (2 * np.pi)
    return new_phases, current_frequencies

@jit(nopython=True, fastmath=True)
def _calculate_order_parameter(phases):
    """ыстрое вычисление параметра порядка"""
    N = len(phases)
    sum_sin = 0.0
    sum_cos = 0.0
    
    for i in range(N):
        sum_sin += np.sin(phases[i])
        sum_cos += np.cos(phases[i])
    
    r = np.sqrt(sum_sin*sum_sin + sum_cos*sum_cos) / N
    mean_phase = np.arctan2(sum_sin, sum_cos)
    
    return r, mean_phase

class EmergentTimeEngine:
    """
    инальная оптимизированная версия движка
    с улучшенной синхронизацией
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
        
        # одготовка данных для Numba
        self._prepare_sparse_data()
        
        # нициализация временных состояний
        self.temporal_states = self._initialize_temporal_states()
        
        # ассивы для быстрого доступа
        self._phases_array = None
        self._natural_freq_array = None
        self._current_freq_array = None
        
        # стория для мониторинга
        self.order_history = []
        self.freq_history = []
        self.energy_history = []
        
        if validation_mode:
            self._run_initial_validation()
    
    def _prepare_sparse_data(self):
        """одготовка данных разреженной матрицы"""
        csr = self.connectivity.tocsr()
        self.connectivity_data = csr.data.astype(np.float64)
        self.connectivity_indices = csr.indices.astype(np.int32)
        self.connectivity_indptr = csr.indptr.astype(np.int32)
        
        # роверка, что есть связи
        if self.connectivity.nnz == 0:
            warnings.warn("Сеть не имеет связей! обавлены случайные связи.")
            self._add_random_connections()
    
    def _add_random_connections(self):
        """обавление случайных связей если сеть пустая"""
        density = min(0.3, 10.0 / self.N)  # инимум 30% или 10 связей на узел
        random_matrix = (np.random.rand(self.N, self.N) < density).astype(float)
        np.fill_diagonal(random_matrix, 0)
        
        # ормализация
        row_sums = random_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        random_matrix = random_matrix / row_sums
        
        self.connectivity = sparse.csr_matrix(random_matrix)
        
        # бновление данных
        csr = self.connectivity.tocsr()
        self.connectivity_data = csr.data.astype(np.float64)
        self.connectivity_indices = csr.indices.astype(np.int32)
        self.connectivity_indptr = csr.indptr.astype(np.int32)
    
    def _initialize_connectivity(self, matrix: Optional[np.ndarray]) -> sparse.csr_matrix:
        """нициализация матрицы связности"""
        if matrix is None:
            # Создаём малую мировую сеть
            matrix = self._create_enhanced_small_world()
        else:
            assert matrix.shape == (self.N, self.N), \
                f"атрица {matrix.shape} не соответствует числу узлов {self.N}"
        
        return sparse.csr_matrix(matrix)
    
    def _create_enhanced_small_world(self) -> np.ndarray:
        """Создание улучшенной малой мировой сети"""
        matrix = np.zeros((self.N, self.N))
        
        # азовые связи: каждый узел связан с k соседями
        k = max(2, min(6, self.N // 5))
        
        for i in range(self.N):
            for j in range(1, k//2 + 1):
                matrix[i, (i+j) % self.N] = 1.0
                matrix[i, (i-j) % self.N] = 1.0
        
        # ереподключение для создания "коротких путей"
        rewire_prob = 0.15
        for i in range(self.N):
            for j in range(self.N):
                if matrix[i, j] == 1 and np.random.rand() < rewire_prob:
                    matrix[i, j] = 0
                    # ыбираем случайный узел, не являющийся соседом
                    possible = [x for x in range(self.N) 
                               if x != i and matrix[i, x] == 0]
                    if possible:
                        new_j = np.random.choice(possible)
                        matrix[i, new_j] = 1.0
        
        # ормализация весов
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        matrix = matrix / row_sums
        
        return matrix
    
    def _initialize_temporal_states(self) -> Dict[int, TemporalState]:
        """нициализация временных состояний"""
        states = {}
        
        for node in self.nodes:
            # азовая частота зависит от здоровья
            health_factor = 0.5 + 0.5 * node.health  # [0.5, 1.0]
            load_factor = 1.0 - 0.3 * node.load
            temp_factor = 1.0 - 0.2 * node.temperature
            
            base_frequency = 1.0 * health_factor * load_factor * temp_factor
            
            # обавляем немного вариации
            variation = 0.1 * (np.random.rand() - 0.5)
            natural_frequency = np.clip(base_frequency + variation, 0.5, 2.0)
            
            # ачальная фаза
            phase = np.random.uniform(0, 2 * np.pi)
            
            states[node.id] = TemporalState(
                phase=phase,
                frequency=natural_frequency,
                natural_frequency=natural_frequency,
                phase_confidence=node.health
            )
        
        return states
    
    def _run_initial_validation(self):
        """ачальная валидация"""
        print("🔬 Я ССТЫ")
        print(f"  злов: {self.N}")
        print(f"  Связей: {self.connectivity.nnz}")
        print(f"  Средняя степень: {2*self.connectivity.nnz/self.N:.1f}")
        
        # ычисляем начальный параметр порядка
        self._update_arrays()
        initial_order, _ = _calculate_order_parameter(self._phases_array)
        print(f"  ачальный параметр порядка: {initial_order:.4f}")
    
    def _update_arrays(self):
        """бновление массивов для быстрого доступа"""
        phases = []
        natural_freqs = []
        current_freqs = []
        
        for state in self.temporal_states.values():
            phases.append(state.phase)
            natural_freqs.append(state.natural_frequency)
            current_freqs.append(state.frequency)
        
        self._phases_array = np.array(phases, dtype=np.float64)
        self._natural_freq_array = np.array(natural_freqs, dtype=np.float64)
        self._current_freq_array = np.array(current_freqs, dtype=np.float64)
    
    def evolve(self, steps: int = 1, K: float = 3.0):
        """
        волюция системы с улучшенной синхронизацией
        
        Args:
            steps: оличество шагов
            K: онстанта связи (рекомендуется 3.0-5.0)
        """
        self._update_arrays()
        
        for step in range(steps):
            # ыполняем оптимизированный шаг
            new_phases, new_frequencies = _kuramoto_step_optimized(
                self._phases_array,
                self._natural_freq_array,
                self.connectivity_data,
                self.connectivity_indices,
                self.connectivity_indptr,
                K, self.dt, 0.02,  # немного больше шума
                self._current_freq_array
            )
            
            # бновляем состояния
            for idx, node_id in enumerate(self.temporal_states.keys()):
                state = self.temporal_states[node_id]
                state.phase = new_phases[idx]
                state.frequency = new_frequencies[idx]
            
            # бновляем массивы
            self._phases_array = new_phases.copy()
            self._current_freq_array = new_frequencies.copy()
            
            # ониторинг (каждые 5 шагов)
            if self.validation_mode and step % 5 == 0:
                order_param, _ = _calculate_order_parameter(self._phases_array)
                self.order_history.append(order_param)
                self.freq_history.append(np.mean(self._current_freq_array))
    
    def get_synchronization_metrics(self) -> Dict[str, float]:
        """олучение метрик синхронизации"""
        self._update_arrays()
        
        order_param, mean_phase = _calculate_order_parameter(self._phases_array)
        phase_variance = np.var(self._phases_array)
        freq_mean = np.mean(self._current_freq_array)
        freq_std = np.std(self._current_freq_array)
        freq_cv = freq_std / freq_mean if freq_mean > 0 else 0
        
        # ычисляем кластеризацию
        phase_complex = np.exp(1j * self._phases_array)
        clustering = np.abs(np.mean(phase_complex ** 2)) - order_param ** 2
        
        return {
            'order_parameter': float(order_param),
            'mean_phase': float(mean_phase),
            'phase_variance': float(phase_variance),
            'frequency_mean': float(freq_mean),
            'frequency_std': float(freq_std),
            'frequency_cv': float(freq_cv),
            'clustering': float(clustering),
            'is_synchronized': order_param > 0.6 and phase_variance < 2.0,
            'sync_strength': 'strong' if order_param > 0.8 else 
                            'medium' if order_param > 0.5 else 'weak'
        }
    
    def get_node_statistics(self) -> Dict[str, any]:
        """Статистика по узлам"""
        self._update_arrays()
        
        # азы по квадрантам
        phases = self._phases_array
        quadrants = [0, 0, 0, 0]
        for phase in phases:
            if phase < np.pi/2:
                quadrants[0] += 1
            elif phase < np.pi:
                quadrants[1] += 1
            elif phase < 3*np.pi/2:
                quadrants[2] += 1
            else:
                quadrants[3] += 1
        
        # азбиение по частотам
        freqs = self._current_freq_array
        freq_low = np.sum(freqs < 0.8)
        freq_medium = np.sum((freqs >= 0.8) & (freqs <= 1.2))
        freq_high = np.sum(freqs > 1.2)
        
        return {
            'total_nodes': self.N,
            'quadrant_distribution': [q/self.N for q in quadrants],
            'frequency_distribution': {
                'low': int(freq_low),
                'medium': int(freq_medium),
                'high': int(freq_high)
            },
            'avg_connections': 2*self.connectivity.nnz/self.N,
            'network_density': self.connectivity.nnz/(self.N*self.N)
        }
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Статистика производительности"""
        if not self.order_history:
            return {}
        
        return {
            'final_order': self.order_history[-1] if self.order_history else 0,
            'max_order': max(self.order_history) if self.order_history else 0,
            'min_order': min(self.order_history) if self.order_history else 0,
            'avg_order': np.mean(self.order_history) if self.order_history else 0,
            'order_growth': self.order_history[-1] - self.order_history[0] if len(self.order_history) > 1 else 0,
            'stability': np.std(self.order_history[-10:]) if len(self.order_history) >= 10 else 0
        }

