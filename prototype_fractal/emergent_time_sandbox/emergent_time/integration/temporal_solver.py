"""
SOLVER Я Т С SPECTRAVORTEX
Совместим с SolverManager
"""

import numpy as np
from typing import Dict, Any, Tuple, List
import sys
import os

# обавляем путь к текущему модулю
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emergent_time.core.emergent_engine import EmergentTimeEngine, NodeState

class TemporalSynchronizationSolver:
    """
    ешатель для анализа и синхронизации временных полей
    олностью совместим с архитектурой SpectraVortex
    """
    
    name = "TemporalSynchronizationSolver"
    version = "1.0.0"
    description = "нализ эмерджентного времени и синхронизация сетей"
    
    def __init__(self, validation_mode: bool = False):
        self.validation_mode = validation_mode
        self.performance_stats = {
            'problems_solved': 0,
            'avg_sync_achieved': 0.0,
            'total_compute_time': 0.0
        }
    
    def can_solve(self, problem: Dict[str, Any]) -> Tuple[bool, float]:
        """
        пределение возможности решения проблемы
        
        Args:
            problem: писание проблемы в формате SpectraVortex
            
        Returns:
            Tuple[может_решить, уверенность]
        """
        problem_type = problem.get("type", "")
        
        # Типы проблем, которые мы можем решать
        temporal_problems = {
            "temporal_synchronization": 0.95,
            "network_health_analysis": 0.85,
            "resilience_temporal_analysis": 0.80,
            "topological_time_optimization": 0.75,
            "emergent_time_simulation": 0.99
        }
        
        if problem_type in temporal_problems:
            confidence = temporal_problems[problem_type]
            
            # ополнительные проверки
            if "network" in problem:
                confidence *= 1.1
            
            return True, min(1.0, confidence)
        
        return False, 0.0
    
    def solve(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        сновной метод решения
        
        Args:
            problem: писание проблемы
            
        Returns:
            ешение в стандартном формате
        """
        import time
        start_time = time.time()
        
        try:
            # 1. звлечение спецификации сети
            network_spec = problem.get("network", {})
            
            # 2. Создание узлов
            nodes = self._create_nodes_from_spec(network_spec)
            
            # 3. Создание движка
            engine = EmergentTimeEngine(
                nodes=nodes,
                connectivity_matrix=network_spec.get("connectivity_matrix"),
                dt=problem.get("dt", 0.01),
                validation_mode=self.validation_mode
            )
            
            # 4. волюция системы
            evolution_steps = problem.get("evolution_steps", 100)
            coupling_strength = problem.get("coupling_strength", 2.5)
            
            engine.evolve(steps=evolution_steps, K=coupling_strength)
            
            # 5. Сбор результатов
            results = self._collect_results(engine, problem)
            
            # 6. бновление статистики
            self._update_performance_stats(results, time.time() - start_time)
            
            return {
                "status": "solved",
                "data": results,
                "metadata": {
                    "solver": self.name,
                    "version": self.version,
                    "compute_time": time.time() - start_time,
                    "nodes_processed": len(nodes),
                    "steps_performed": evolution_steps
                }
            }
            
        except Exception as e:
            # озвращаем ошибку в стандартном формате
            return {
                "status": "error",
                "data": {"error": str(e)},
                "metadata": {
                    "solver": self.name,
                    "version": self.version,
                    "compute_time": time.time() - start_time
                }
            }
    
    def _create_nodes_from_spec(self, network_spec: Dict) -> List[NodeState]:
        """Создание узлов из спецификации сети"""
        nodes = []
        
        if "nodes" in network_spec:
            # ормат с явным описанием узлов
            for node_id, node_data in enumerate(network_spec["nodes"]):
                if isinstance(node_data, dict):
                    node = NodeState(
                        id=node_id,
                        health=node_data.get("health", 0.8),
                        load=node_data.get("load", 0.0),
                        temperature=node_data.get("temperature", 0.0),
                        noise_level=node_data.get("noise", 0.01)
                    )
                else:
                    # росто число - здоровье
                    node = NodeState(
                        id=node_id,
                        health=float(node_data)
                    )
                nodes.append(node)
        else:
            # Случайная сеть с параметрами
            num_nodes = network_spec.get("num_nodes", 10)
            health_mean = network_spec.get("health_mean", 0.8)
            health_std = network_spec.get("health_std", 0.1)
            
            for i in range(num_nodes):
                health = np.clip(
                    np.random.normal(health_mean, health_std),
                    0.1, 1.0
                )
                nodes.append(NodeState(id=i, health=health))
        
        return nodes
    
    def _collect_results(self, engine: EmergentTimeEngine, 
                        problem: Dict) -> Dict[str, Any]:
        """Сбор и структурирование результатов"""
        # етрики синхронизации
        sync_metrics = engine.get_synchronization_metrics()
        
        # одробные данные по узлам
        node_details = []
        for node_id, state in engine.temporal_states.items():
            node_details.append({
                "id": node_id,
                "phase": float(state.phase),
                "frequency": float(state.frequency),
                "phase_confidence": float(state.phase_confidence),
                "health": engine.nodes[node_id].health if node_id < len(engine.nodes) else 1.0
            })
        
        # Статистика производительности
        perf_stats = engine.get_performance_stats()
        
        # нализ рекомендаций
        recommendations = self._generate_recommendations(sync_metrics, node_details)
        
        return {
            "synchronization_metrics": sync_metrics,
            "node_details": node_details,
            "performance_stats": perf_stats,
            "recommendations": recommendations,
            "system_energy": float(engine.calculate_system_energy()),
            "connectivity_density": engine.connectivity.nnz / (engine.N * engine.N)
        }
    
    def _generate_recommendations(self, metrics: Dict, 
                                 nodes: List[Dict]) -> List[str]:
        """енерация рекомендаций на основе анализа"""
        recommendations = []
        
        # роверка синхронизации
        if not metrics.get('is_synchronized', False):
            recommendations.append(
                "величьте coupling_strength (рекомендуется 3.0-4.0) или evolution_steps (200+)"
            )
        
        # роверка здоровья узлов
        unhealthy_nodes = [n for n in nodes if n.get("health", 1.0) < 0.5]
        if unhealthy_nodes:
            recommendations.append(
                f"бнаружены {len(unhealthy_nodes)} нездоровых узлов (health < 0.5). "
                "екомендуется восстановить их здоровье."
            )
        
        # роверка разброса частот
        if metrics.get('frequency_cv', 0) > 0.3:
            recommendations.append(
                "ольшой разброс частот (CV > 0.3). "
                "ассмотрите возможность нормализации частот узлов."
            )
        
        # роверка плотности сети
        if len(nodes) > 0:
            avg_connections = sum(len(n.get('neighbors', [])) for n in nodes) / len(nodes)
            if avg_connections < 2:
                recommendations.append(
                    f"изкая связность сети (в среднем {avg_connections:.1f} связей на узел). "
                    "екомендуется увеличить плотность связей."
                )
        
        return recommendations
    
    def _update_performance_stats(self, results: Dict, compute_time: float):
        """бновление статистики производительности"""
        self.performance_stats['problems_solved'] += 1
        self.performance_stats['total_compute_time'] += compute_time
        
        sync_level = results.get("synchronization_metrics", {}).get("order_parameter", 0)
        prev_avg = self.performance_stats['avg_sync_achieved']
        prev_count = self.performance_stats['problems_solved'] - 1
        
        self.performance_stats['avg_sync_achieved'] = (
            (prev_avg * prev_count + sync_level) / 
            self.performance_stats['problems_solved']
        )
    
    def get_performance_report(self) -> Dict:
        """тчёт о производительности solver'а"""
        solved = max(1, self.performance_stats['problems_solved'])
        return {
            **self.performance_stats,
            "avg_compute_time": self.performance_stats['total_compute_time'] / solved,
            "solver_name": self.name,
            "version": self.version,
            "efficiency": self.performance_stats['avg_sync_achieved'] / 
                         (self.performance_stats['total_compute_time'] / solved + 0.001)
        }

# ласс решения для совместимости со SpectraVortex
class FieldSolution:
    """муляция класса FieldSolution из SpectraVortex"""
    def __init__(self, status: str, data: Dict, metadata: Dict = None):
        self.status = status
        self.data = data
        self.metadata = metadata or {}
