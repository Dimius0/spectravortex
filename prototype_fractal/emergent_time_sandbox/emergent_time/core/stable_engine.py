"""
СТЬ Я Т 
ерсия 2.0 - абочая и оптимизированная
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings

class StableNode:
    """Стабильная реализация узла сети"""
    __slots__ = ['id', 'health', 'phase', 'natural_freq', 'current_freq', 'confidence']
    
    def __init__(self, id: int, health: float = 0.85):
        self.id = id
        self.health = np.clip(health, 0.1, 1.0)
        self.phase = np.random.uniform(0, 2 * np.pi)
        self.natural_freq = 0.8 + 0.4 * self.health  # 0.9-1.2 для health=0.85
        self.current_freq = self.natural_freq
        self.confidence = self.health
    
    def __repr__(self):
        return f"Node(id={self.id}, health={self.health:.2f}, phase={self.phase:.3f})"

class StableEmergentEngine:
    """
    Стабильная и быстрая реализация эмерджентного времени
    """
    
    def __init__(self, 
                 nodes: List[StableNode],
                 connectivity: Optional[np.ndarray] = None,
                 dt: float = 0.01,
                 K: float = 3.0):
        
        self.nodes = nodes
        self.N = len(nodes)
        self.dt = dt
        self.K = K
        
        # атрица связности
        if connectivity is None:
            self.connectivity = self._create_default_connectivity()
        else:
            self.connectivity = connectivity
        
        # роверка размерности
        assert self.connectivity.shape == (self.N, self.N), \
            f"атрица связности {self.connectivity.shape} != ({self.N}, {self.N})"
        
        # стория для анализа
        self.order_history = []
        self.phase_history = []
        
        # нициализация
        self._initialize_system()
    
    def _create_default_connectivity(self) -> np.ndarray:
        """Создание малой мировой сети по умолчанию"""
        matrix = np.zeros((self.N, self.N))
        k = min(4, max(2, self.N // 5))  # 2-4 соседа
        
        for i in range(self.N):
            for j in range(1, k//2 + 1):
                matrix[i, (i+j) % self.N] = 1.0
                matrix[i, (i-j) % self.N] = 1.0
        
        # емного случайных дальних связей (10%)
        for i in range(self.N):
            for j in range(self.N):
                if i != j and matrix[i, j] == 0 and np.random.rand() < 0.1:
                    matrix[i, j] = 0.5
        
        # ормализация
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        return matrix / row_sums
    
    def _initialize_system(self):
        """нициализация системы"""
        # ачальный параметр порядка
        initial_order = self._calculate_order_parameter()
        self.order_history.append(initial_order)
        self.phase_history.append([node.phase for node in self.nodes])
        
        print(f"🔧 Система инициализирована: {self.N} узлов, начальный порядок: {initial_order:.3f}")
    
    def _calculate_order_parameter(self) -> float:
        """ычисление параметра порядка R"""
        phases = np.array([node.phase for node in self.nodes])
        complex_phases = np.exp(1j * phases)
        return np.abs(np.mean(complex_phases))
    
    def evolve(self, steps: int = 100):
        """
        волюция системы на заданное количество шагов
        """
        for step in range(steps):
            # Сохраняем старые фазы для вычисления производных
            old_phases = np.array([node.phase for node in self.nodes])
            
            # ычисляем новые фазы
            new_phases = self._compute_phase_update(old_phases)
            
            # бновляем узлы
            for i, node in enumerate(self.nodes):
                node.phase = new_phases[i] % (2 * np.pi)
                
                # даптация частоты (простая версия)
                self._adapt_frequency(node, i, old_phases[i], new_phases[i])
            
            # аписываем метрики каждые 10 шагов
            if step % 10 == 0:
                order = self._calculate_order_parameter()
                self.order_history.append(order)
                self.phase_history.append([node.phase for node in self.nodes])
    
    def _compute_phase_update(self, phases: np.ndarray) -> np.ndarray:
        """ычисление обновления фаз (уравнение урамото)"""
        N = self.N
        new_phases = np.zeros_like(phases)
        
        for i in range(N):
            # Собственная частота узла
            omega_i = self.nodes[i].current_freq
            
            # Сумма связей с соседями
            coupling_sum = 0.0
            for j in range(N):
                if self.connectivity[i, j] > 0:
                    phase_diff = phases[j] - phases[i]
                    coupling_sum += self.connectivity[i, j] * np.sin(phase_diff)
            
            # равнение урамото
            dphase = omega_i + (self.K / N) * coupling_sum
            
            # обавляем небольшой шум (1%)
            noise = 0.01 * self.nodes[i].confidence * np.random.randn()
            dphase += noise
            
            new_phases[i] = phases[i] + self.dt * dphase
        
        return new_phases
    
    def _adapt_frequency(self, node: StableNode, idx: int, 
                        old_phase: float, new_phase: float):
        """ростая адаптация частоты"""
        # ычисляем скорость изменения фазы
        phase_velocity = (new_phase - old_phase) / self.dt
        
        # сли фаза меняется слишком быстро/медленно, корректируем частоту
        if abs(phase_velocity) > 5.0:  # слишком быстро
            node.current_freq *= 0.95
        elif abs(phase_velocity) < 0.5:  # слишком медленно
            node.current_freq *= 1.05
        
        # граничиваем частоту разумными пределами
        node.current_freq = np.clip(node.current_freq, 0.5, 2.0)
    
    def get_synchronization_metrics(self) -> Dict[str, float]:
        """олучение метрик синхронизации"""
        phases = np.array([node.phase for node in self.nodes])
        freqs = np.array([node.current_freq for node in self.nodes])
        
        # араметр порядка
        complex_phases = np.exp(1j * phases)
        order_param = np.abs(np.mean(complex_phases))
        mean_phase = np.angle(np.mean(complex_phases))
        
        # исперсия
        phase_var = np.var(phases)
        freq_var = np.var(freqs)
        freq_cv = freq_var / np.mean(freqs) if np.mean(freqs) > 0 else 0
        
        # ластеризация
        clustering = np.abs(np.mean(complex_phases ** 2)) - order_param ** 2
        
        return {
            'order_parameter': float(order_param),
            'mean_phase': float(mean_phase),
            'phase_variance': float(phase_var),
            'frequency_mean': float(np.mean(freqs)),
            'frequency_cv': float(freq_cv),
            'clustering': float(clustering),
            'is_synchronized': order_param > 0.7 and phase_var < 2.0,
            'sync_strength': 'strong' if order_param > 0.85 else 
                            'medium' if order_param > 0.6 else 'weak',
            'health_mean': float(np.mean([n.health for n in self.nodes]))
        }
    
    def get_node_data(self) -> List[Dict]:
        """анные по узлам"""
        return [
            {
                'id': node.id,
                'health': node.health,
                'phase': node.phase,
                'natural_freq': node.natural_freq,
                'current_freq': node.current_freq,
                'confidence': node.confidence
            }
            for node in self.nodes
        ]
    
    def get_performance_stats(self) -> Dict:
        """Статистика производительности"""
        if len(self.order_history) < 2:
            return {}
        
        return {
            'initial_order': self.order_history[0],
            'final_order': self.order_history[-1],
            'max_order': max(self.order_history),
            'order_growth': self.order_history[-1] - self.order_history[0],
            'stability': np.std(self.order_history[-5:]) if len(self.order_history) >= 5 else 0,
            'steps_completed': len(self.order_history) * 10
        }
