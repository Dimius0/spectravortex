"""
ЬЫ SOLVER Я SPECTRAVORTEX
ерсия 2.0 - Стабильная и готовая к интеграции
"""

import numpy as np
from typing import Dict, Any, Tuple, List
import time
import sys
import os

# обавляем путь к ядру
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, "..", "core")
sys.path.insert(0, core_dir)

try:
    from stable_engine import StableEmergentEngine, StableNode
    ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  е удалось загрузить ядро: {e}")
    print("⚠️  спользуется режим эмуляции для тестирования")
    ENGINE_AVAILABLE = False

class EmergentTimeSolver:
    """
    инальный Solver для интеграции с SpectraVortex
    Совместим с SolverManager
    """
    
    name = "EmergentTimeSolver"
    version = "2.0.0"
    description = "мерджентное время и синхронизация сетей"
    
    # оддерживаемые типы проблем
    SUPPORTED_PROBLEMS = {
        "temporal_synchronization": {
            "confidence": 0.98,
            "description": "Синхронизация временных полей в сети"
        },
        "network_health_analysis": {
            "confidence": 0.90,
            "description": "нализ влияния здоровья узлов на синхронизацию"
        },
        "resilience_temporal_test": {
            "confidence": 0.85,
            "description": "Тест временной устойчивости сети"
        },
        "topology_optimization": {
            "confidence": 0.80,
            "description": "птимизация топологии для синхронизации"
        }
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.emergent_depth = self.config.get('emergent_depth', 0.7)
        self.validation_mode = self.config.get('validation', False)
        
        # Статистика
        self.stats = {
            'problems_solved': 0,
            'total_time': 0.0,
            'success_count': 0,
            'avg_sync_level': 0.0
        }
        
        print(f"⚡ {self.name} v{self.version} инициализирован")
        print(f"   лубина эмерджентности: {self.emergent_depth}")
        print(f"   оддерживаемых типов проблем: {len(self.SUPPORTED_PROBLEMS)}")
    
    def can_solve(self, problem: Dict) -> Tuple[bool, float]:
        """
        роверка возможности решения проблемы
        озвращает: (может_решить, уверенность)
        """
        problem_type = problem.get('type', '').lower()
        
        if problem_type in self.SUPPORTED_PROBLEMS:
            base_confidence = self.SUPPORTED_PROBLEMS[problem_type]['confidence']
            
            # овышаем уверенность для хорошо описанных проблем
            if 'network' in problem:
                network = problem['network']
                if isinstance(network, dict):
                    if 'nodes' in network or 'num_nodes' in network:
                        base_confidence = min(1.0, base_confidence * 1.1)
            
            return True, base_confidence
        
        return False, 0.0
    
    def solve(self, problem: Dict) -> Dict:
        """
        ешение проблемы эмерджентного времени
        """
        start_time = time.time()
        
        try:
            # огирование
            if self.validation_mode:
                print(f"\n🔍 ешение проблемы: {problem.get('type', 'unknown')}")
                print(f"   ID: {problem.get('id', 'N/A')}")
            
            # звлечение параметров
            problem_type = problem.get('type', 'temporal_synchronization')
            network_spec = problem.get('network', {})
            params = problem.get('parameters', {})
            
            # Создание сети
            nodes, connectivity = self._create_network(network_spec)
            
            # араметры эволюции
            evolution_steps = params.get('evolution_steps', 200)
            coupling_strength = params.get('coupling_strength', 3.5)
            dt = params.get('dt', 0.01)
            
            if self.validation_mode:
                print(f"   злов: {len(nodes)}")
                print(f"   Шагов эволюции: {evolution_steps}")
                print(f"   Сила связи: {coupling_strength}")
            
            # Создание и запуск движка
            if ENGINE_AVAILABLE:
                engine = StableEmergentEngine(
                    nodes=nodes,
                    connectivity=connectivity,
                    dt=dt,
                    K=coupling_strength
                )
                
                # волюция
                engine.evolve(steps=evolution_steps)
                
                # Сбор результатов
                results = self._collect_results(engine, problem)
            else:
                # ежим эмуляции
                results = self._emulate_results(nodes, problem)
            
            # етаданные
            compute_time = time.time() - start_time
            
            # бновление статистики
            self._update_stats(results, compute_time)
            
            # ормирование ответа
            solution = {
                'status': 'solved',
                'data': results,
                'metadata': {
                    'solver': self.name,
                    'version': self.version,
                    'compute_time': compute_time,
                    'nodes_processed': len(nodes),
                    'steps_performed': evolution_steps,
                    'emergent_depth_used': self.emergent_depth,
                    'problem_type': problem_type
                }
            }
            
            if self.validation_mode:
                sync_level = results.get('synchronization', {}).get('order_parameter', 0)
                print(f"   ✅ ешено за {compute_time:.2f} сек")
                print(f"   📊 Синхронизация: {sync_level:.3f}")
            
            return solution
            
        except Exception as e:
            # бработка ошибок
            compute_time = time.time() - start_time
            
            error_solution = {
                'status': 'error',
                'data': {
                    'error': str(e),
                    'error_type': type(e).__name__
                },
                'metadata': {
                    'solver': self.name,
                    'version': self.version,
                    'compute_time': compute_time
                }
            }
            
            if self.validation_mode:
                print(f"   ❌ шибка: {e}")
            
            return error_solution
    
    def _create_network(self, network_spec: Dict) -> Tuple[List, np.ndarray]:
        """Создание сети из спецификации"""
        nodes = []
        
        # Создание узлов
        if 'nodes' in network_spec:
            # етальная спецификация
            for i, node_data in enumerate(network_spec['nodes']):
                if isinstance(node_data, dict):
                    health = node_data.get('health', 0.85)
                else:
                    health = float(node_data)
                nodes.append(StableNode(id=i, health=health))
        else:
            # ростая спецификация
            num_nodes = network_spec.get('num_nodes', 20)
            health_mean = network_spec.get('health_mean', 0.85)
            health_std = network_spec.get('health_std', 0.1)
            
            for i in range(num_nodes):
                health = np.clip(np.random.normal(health_mean, health_std), 0.1, 1.0)
                nodes.append(StableNode(id=i, health=health))
        
        # Создание матрицы связности
        N = len(nodes)
        topology = network_spec.get('topology', 'small_world')
        
        if topology == 'ring':
            connectivity = np.zeros((N, N))
            for i in range(N):
                connectivity[i, (i-1) % N] = 1.0
                connectivity[i, (i+1) % N] = 1.0
        elif topology == 'fully_connected':
            connectivity = np.ones((N, N)) - np.eye(N)
        elif topology == 'star':
            connectivity = np.zeros((N, N))
            center = N // 2
            for i in range(N):
                if i != center:
                    connectivity[center, i] = 1.0
                    connectivity[i, center] = 1.0
        else:  # small_world по умолчанию
            connectivity = np.zeros((N, N))
            k = min(4, max(2, N // 5))
            for i in range(N):
                for j in range(1, k//2 + 1):
                    connectivity[i, (i+j) % N] = 1.0
                    connectivity[i, (i-j) % N] = 1.0
        
        # ормализация
        row_sums = connectivity.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        connectivity = connectivity / row_sums
        
        return nodes, connectivity
    
    def _collect_results(self, engine, problem: Dict) -> Dict:
        """Сбор результатов из движка"""
        # етрики синхронизации
        sync_metrics = engine.get_synchronization_metrics()
        
        # анные узлов
        node_data = engine.get_node_data()
        
        # Статистика производительности
        perf_stats = engine.get_performance_stats()
        
        # нализ и рекомендации
        analysis = self._analyze_system(sync_metrics, node_data, problem)
        
        # одготовка результата
        results = {
            'synchronization': sync_metrics,
            'nodes': node_data,
            'performance': perf_stats,
            'analysis': analysis,
            'network_info': {
                'total_nodes': len(node_data),
                'avg_health': np.mean([n['health'] for n in node_data]) if node_data else 0,
                'connectivity_density': engine.connectivity.sum() / (len(node_data) ** 2) if node_data else 0
            }
        }
        
        # обавляем эмерджентные коэффициенты если глубина > 0.5
        if self.emergent_depth > 0.5:
            results['emergent_coefficients'] = self._calculate_emergent_coeffs(sync_metrics, node_data)
        
        return results
    
    def _analyze_system(self, metrics: Dict, nodes: List[Dict], problem: Dict) -> Dict:
        """нализ системы и генерация выводов"""
        order_param = metrics.get('order_parameter', 0)
        is_sync = metrics.get('is_synchronized', False)
        
        analysis = {
            'summary': '',
            'recommendations': [],
            'warnings': [],
            'strengths': []
        }
        
        # ценка синхронизации
        if order_param > 0.8:
            analysis['summary'] = 'тличная синхронизация достигнута'
            analysis['strengths'].append('ысокий параметр порядка')
        elif order_param > 0.6:
            analysis['summary'] = 'Хорошая синхронизация'
            analysis['strengths'].append('Стабильная синхронизация')
        elif order_param > 0.4:
            analysis['summary'] = 'меренная синхронизация'
            analysis['warnings'].append('Синхронизация требует улучшения')
        else:
            analysis['summary'] = 'Слабая синхронизация'
            analysis['warnings'].append('еобходимо увеличить силу связи или время эволюции')
        
        # екомендации
        if not is_sync:
            analysis['recommendations'].extend([
                'величьте coupling_strength (рекомендуется 4.0-5.0)',
                'величьте evolution_steps (250-300 шагов)',
                'роверьте здоровье узлов (health > 0.7)'
            ])
        
        # нализ здоровья
        unhealthy = [n for n in nodes if n.get('health', 1) < 0.5]
        if unhealthy:
            analysis['warnings'].append(f'бнаружены {len(unhealthy)} нездоровых узлов')
            analysis['recommendations'].append('осстановите здоровье узлов для улучшения синхронизации')
        
        # ффект бабочки (если есть история)
        if 'performance' in metrics and 'order_growth' in metrics['performance']:
            growth = metrics['performance']['order_growth']
            if abs(growth) > 0.3:
                analysis['strengths'].append('Сильный эффект самоорганизации')
        
        return analysis
    
    def _calculate_emergent_coeffs(self, metrics: Dict, nodes: List[Dict]) -> Dict:
        """асчёт эмерджентных коэффициентов (заглушка для будущих версий)"""
        return {
            'temporal_coherence': metrics.get('order_parameter', 0) * self.emergent_depth,
            'adaptive_capacity': np.mean([n.get('health', 0) for n in nodes]) * self.emergent_depth,
            'sync_potential': min(1.0, metrics.get('order_parameter', 0) * 1.2),
            'emergent_depth_used': self.emergent_depth
        }
    
    def _emulate_results(self, nodes: List, problem: Dict) -> Dict:
        """муляция результатов для тестирования"""
        N = len(nodes)
        
        # мулируем синхронизацию
        base_sync = 0.3 + 0.5 * self.emergent_depth
        health_mean = np.mean([n.health for n in nodes]) if hasattr(nodes[0], 'health') else 0.85
        
        sync_level = min(0.95, base_sync * health_mean * (1 + np.random.rand() * 0.2))
        
        return {
            'synchronization': {
                'order_parameter': sync_level,
                'is_synchronized': sync_level > 0.6,
                'sync_strength': 'strong' if sync_level > 0.8 else 'medium' if sync_level > 0.6 else 'weak'
            },
            'nodes': [
                {
                    'id': i,
                    'health': n.health if hasattr(n, 'health') else 0.85,
                    'phase': np.random.uniform(0, 2*np.pi),
                    'frequency': 1.0 + np.random.rand() * 0.4
                }
                for i, n in enumerate(nodes[:10])  # Только первые 10 для краткости
            ],
            'analysis': {
                'summary': 'муляция результатов',
                'note': 'ежим эмуляции - установите стабильное ядро для реальных расчётов'
            }
        }
    
    def _update_stats(self, results: Dict, compute_time: float):
        """бновление статистики solver'а"""
        self.stats['problems_solved'] += 1
        self.stats['total_time'] += compute_time
        
        sync_level = results.get('synchronization', {}).get('order_parameter', 0)
        if sync_level > 0.4:
            self.stats['success_count'] += 1
        
        # бновление средней синхронизации
        prev_avg = self.stats['avg_sync_level']
        prev_count = self.stats['problems_solved'] - 1
        self.stats['avg_sync_level'] = (prev_avg * prev_count + sync_level) / self.stats['problems_solved']
    
    def get_stats(self) -> Dict:
        """олучение статистики solver'а"""
        solved = max(1, self.stats['problems_solved'])
        return {
            **self.stats,
            'avg_compute_time': self.stats['total_time'] / solved,
            'success_rate': self.stats['success_count'] / solved,
            'efficiency': self.stats['avg_sync_level'] / (self.stats['total_time'] / solved + 0.001),
            'solver_name': self.name,
            'version': self.version,
            'emergent_depth': self.emergent_depth
        }
    
    def reset_stats(self):
        """Сброс статистики"""
        self.stats = {
            'problems_solved': 0,
            'total_time': 0.0,
            'success_count': 0,
            'avg_sync_level': 0.0
        }

# ласс для совместимости со SpectraVortex
class FieldSolution:
    def __init__(self, status: str, data: Dict, metadata: Dict = None):
        self.status = status
        self.data = data
        self.metadata = metadata or {}
