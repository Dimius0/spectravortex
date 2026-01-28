"""
Solver Manager for Hybrid Architecture.
The "brain" that coordinates multiple solvers and enables automatic solver selection.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import numpy as np
import time
from scipy import ndimage  # Для продвинутого анализа полей

logger = logging.getLogger(__name__)

# Импорты с защитой на случай отсутствия гибридных модулей
try:
    from .solver import Solver
    from .data_interface import FieldSolution
    HYBRID_CORE_AVAILABLE = True
except ImportError:
    HYBRID_CORE_AVAILABLE = False
    # Заглушки для обратной совместимости
    class Solver:
        def __init__(self, *args, **kwargs):
            raise ImportError("Solver requires core.solver module")
    
    class FieldSolution:
        def __init__(self, *args, **kwargs):
            raise ImportError("FieldSolution requires core.data_interface module")

@dataclass
class SolverSelection:
    """Result of solver selection process."""
    solver: Solver
    confidence: float  # 0.0 to 1.0
    reason: str
    estimated_cost: Dict[str, float]

@dataclass
class HybridProblemPart:
    """Part of a problem assigned to a specific solver."""
    domain_id: str
    problem_description: Dict[str, Any]
    assigned_solver: Optional[Solver] = None
    boundary_conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TopologicalFeature:
    """Data class for topological features found in solutions."""
    feature_type: str  # 'vortex', 'saddle', 'node', 'boundary'
    position: Tuple[float, float]  # (x, y) coordinates
    strength: float  # Strength or topological charge
    stability_index: float  # 0.0 to 1.0, higher = more stable
    metadata: Dict[str, Any] = field(default_factory=dict)

class SolverManager:
    """
    Manages multiple solvers and coordinates hybrid computations.
    
    Features:
    - Automatic solver selection based on problem characteristics
    - Solver registry and discovery
    - Hybrid problem decomposition
    - Performance monitoring and logging
    - Topological analysis of solutions (NEW)
    """
    
    def __init__(self, enable_auto_selection: bool = True):
        """
        Initialize the solver manager.
        
        Args:
            enable_auto_selection: Whether to enable automatic solver selection
        """
        if not HYBRID_CORE_AVAILABLE:
            raise ImportError(
                "SolverManager requires hybrid architecture. "
                "Install core.solver and core.data_interface modules."
            )
        
        self.solvers: Dict[str, Solver] = {}
        self.enable_auto_selection = enable_auto_selection
        self.performance_log: List[Dict[str, Any]] = []
        self.solver_stats: Dict[str, Dict[str, Any]] = {}
        self.topology_cache: Dict[str, List[TopologicalFeature]] = {}
        
        logger.info(f"SolverManager initialized (auto-selection: {enable_auto_selection})")
    
    def register_solver(self, solver: Solver, priority: int = 0) -> None:
        """
        Register a solver in the manager.
        
        Args:
            solver: Solver instance to register
            priority: Priority for automatic selection (higher = more preferred)
        """
        if not isinstance(solver, Solver):
            raise TypeError(f"Expected Solver instance, got {type(solver)}")
        
        # Используем имя класса для ID вместо solver.name (которого может не быть)
        solver_id = f"{solver.__class__.__name__}_{id(solver)}"
        self.solvers[solver_id] = solver
        
        # Initialize statistics
        self.solver_stats[solver_id] = {
            'name': solver.__class__.__name__,
            'version': getattr(solver, 'version', 'unknown'),
            'priority': priority,
            'usage_count': 0,
            'success_count': 0,
            'total_time': 0.0,
            'last_used': None,
            'topology_analysis_count': 0,  # NEW: track topology analyses
        }
        
        logger.info(f"Registered solver: {solver.__class__.__name__} "
                   f"v{self.solver_stats[solver_id]['version']} (ID: {solver_id})")
    
    def register_default_solvers(self) -> None:
        """Register default solvers if available."""
        try:
            from ..solvers.linear_wave_solver import LinearWaveSolver
            linear_solver = LinearWaveSolver()
            self.register_solver(linear_solver, priority=10)
            logger.info("Registered default LinearWaveSolver")
        except ImportError:
            logger.warning("LinearWaveSolver not available for registration")
        except Exception as e:
            logger.error(f"Error registering LinearWaveSolver: {e}")
    
    def get_available_solvers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available solvers.
        
        Returns:
            Dictionary with solver information
        """
        result = {}
        
        for solver_id, solver in self.solvers.items():
            stats = self.solver_stats.get(solver_id, {})
            solver_info = {
                'name': stats.get('name', 'unknown'),
                'version': stats.get('version', 'unknown'),
                'priority': stats.get('priority', 0),
                'usage_count': stats.get('usage_count', 0),
                'success_rate': self._calculate_success_rate(solver_id),
                'last_used': stats.get('last_used'),
                'topology_analyses': stats.get('topology_analysis_count', 0),  # NEW
            }
            
            # Get solver requirements if the method exists
            if hasattr(solver, 'get_requirements'):
                try:
                    requirements = solver.get_requirements()
                    solver_info.update({
                        'capabilities': requirements.get('physical_models', []),
                        'max_dimensions': requirements.get('max_dimensions', 1),
                    })
                except Exception as e:
                    logger.warning(f"Error getting requirements for {solver_id}: {e}")
            else:
                # Default values if method doesn't exist
                solver_info.update({
                    'capabilities': ['unknown'],
                    'max_dimensions': 1,
                })
            
            result[solver_id] = solver_info
        
        return result
    
    def _calculate_success_rate(self, solver_id: str) -> float:
        """Calculate success rate for a solver."""
        stats = self.solver_stats.get(solver_id, {})
        usage = stats.get('usage_count', 0)
        success = stats.get('success_count', 0)
        
        return success / usage if usage > 0 else 0.0
    
    def select_solver(self, problem: Dict[str, Any]) -> SolverSelection:
        """
        Select the best solver for a given problem.
        
        Args:
            problem: Problem description dictionary
            
        Returns:
            SolverSelection with selected solver and metadata
            
        Raises:
            RuntimeError: If no solvers registered
        """
        if not self.solvers:
            raise RuntimeError("No solvers registered in SolverManager")
        
        logger.info(f"Selecting solver for problem: {problem.get('name', 'unnamed')}")
        
        # If auto-selection is disabled, use first available solver
        if not self.enable_auto_selection:
            first_solver = next(iter(self.solvers.values()))
            return SolverSelection(
                solver=first_solver,
                confidence=0.5,
                reason="Auto-selection disabled, using first available solver",
                estimated_cost=self._get_cost_estimate(first_solver, problem),
            )
        
        # Evaluate all solvers
        evaluations = []
        for solver_id, solver in self.solvers.items():
            evaluation = self._evaluate_solver(solver, solver_id, problem)
            evaluations.append(evaluation)
        
        if not evaluations:
            raise RuntimeError("No solvers can solve this problem")
        
        # Sort by score (higher is better)
        evaluations.sort(key=lambda x: x['score'], reverse=True)
        
        best_eval = evaluations[0]
        best_solver = best_eval['solver']
        
        # Calculate confidence based on score difference
        confidence = best_eval['score']
        if len(evaluations) > 1 and best_eval['score'] > 0:
            second_best = evaluations[1]['score']
            score_diff = best_eval['score'] - second_best
            confidence = min(1.0, max(0.1, score_diff * 2))
        
        return SolverSelection(
            solver=best_solver,
            confidence=confidence,
            reason=best_eval['reason'],
            estimated_cost=best_eval['estimated_cost'],
        )
    
    def _get_cost_estimate(self, solver: Solver, problem: Dict[str, Any]) -> Dict[str, float]:
        """Get cost estimate from solver or return default."""
        if hasattr(solver, 'estimate_computation_cost'):
            try:
                return solver.estimate_computation_cost(problem)
            except Exception as e:
                logger.debug(f"Error getting cost estimate: {e}")
        
        return {'time_seconds': 1.0, 'memory_mb': 100, 'complexity': 1.0}
    
    def _evaluate_solver(self, solver: Solver, solver_id: str, 
                        problem: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate how well a solver can handle a problem."""
        # Check basic compatibility
        can_solve = True
        reason = "Compatible"
        
        if hasattr(solver, 'can_solve'):
            try:
                can_solve, reason = solver.can_solve(problem)
            except Exception as e:
                logger.warning(f"Error in can_solve for {solver_id}: {e}")
                can_solve = False
                reason = f"Error checking compatibility: {e}"
        
        if not can_solve:
            return {
                'solver': solver,
                'score': 0.0,
                'reason': f"Cannot solve: {reason}",
                'estimated_cost': {'time_seconds': 0, 'memory_mb': 0, 'complexity': 0},
            }
        
        # Calculate base score
        score = 1.0
        
        # Adjust based on solver priority
        stats = self.solver_stats.get(solver_id, {})
        priority = stats.get('priority', 0)
        score += priority * 0.05  # +5% per priority point
        
        # Adjust based on success rate
        success_rate = self._calculate_success_rate(solver_id)
        score += success_rate * 0.1  # +10% for 100% success rate
        
        # Get cost estimate
        cost_estimate = self._get_cost_estimate(solver, problem)
        
        # Prefer faster solvers (inverse of time)
        time_seconds = cost_estimate.get('time_seconds', 1.0)
        if time_seconds > 0:
            score *= 1.0 / (1.0 + np.log1p(time_seconds))
        
        # NEW: Adjust based on topological complexity match
        problem_complexity = self._estimate_topological_complexity(problem)
        if problem_complexity == 'high' and hasattr(solver, 'supports_topology_analysis'):
            score *= 1.2  # 20% bonus for solvers that support topology analysis
        
        # Cap score between 0 and 2
        score = max(0.0, min(2.0, score))
        
        return {
            'solver': solver,
            'score': score,
            'reason': f"{reason}. Priority: {priority}, Success: {success_rate:.1%}",
            'estimated_cost': cost_estimate,
        }
    
    def _estimate_problem_complexity(self, problem: Dict[str, Any]) -> str:
        """Estimate problem complexity."""
        domain = problem.get('domain', {})
        domain_type = domain.get('type', '1d')
        
        if domain_type == '1d':
            return 'simple'
        elif domain_type == '2d':
            # Check size
            width = domain.get('width', 10e-6)
            height = domain.get('height', 10e-6)
            grid_size = domain.get('grid_size', 0.1e-6)
            
            nx = int(width / grid_size) if width > 0 and grid_size > 0 else 100
            ny = int(height / grid_size) if height > 0 and grid_size > 0 else 100
            
            if nx * ny > 10000:
                return 'complex'
            else:
                return 'medium'
        else:
            return 'complex'
    
    def _estimate_topological_complexity(self, problem: Dict[str, Any]) -> str:
        """
        NEW: Estimate topological complexity of a problem.
        
        Returns:
            'low', 'medium', or 'high' based on expected topological features
        """
        physics = problem.get('physics', [])
        components = problem.get('components', [])
        
        # Check for OAM-related parameters
        has_oam = any('oam' in str(c).lower() for c in components) or \
                  any('vortex' in str(p).lower() for p in physics) or \
                  problem.get('parameters', {}).get('orbital_angular_momentum') is not None
        
        # Check for interference patterns
        has_interference = 'interference' in physics or \
                          any('interfer' in str(c).lower() for c in components)
        
        # Check for resonator structures
        has_resonators = any('resonator' in str(c).lower() or 
                            'ring' in str(c).lower() for c in components)
        
        # Determine complexity level
        if has_oam or (has_interference and has_resonators):
            return 'high'
        elif has_interference or has_resonators:
            return 'medium'
        else:
            return 'low'
    
    def solve(self, problem: Dict[str, Any]) -> FieldSolution:
        """
        Solve a problem using automatic solver selection.
        
        Args:
            problem: Problem description dictionary
            
        Returns:
            FieldSolution with results
            
        Raises:
            RuntimeError: If no solver can solve the problem
        """
        logger.info(f"SolverManager solving problem: {problem.get('name', 'unnamed')}")
        
        # Select best solver
        selection = self.select_solver(problem)
        solver = selection.solver
        
        # Get solver ID
        solver_id = None
        for sid, s in self.solvers.items():
            if s is solver:
                solver_id = sid
                break
        
        if solver_id is None:
            solver_id = f"unknown_{id(solver)}"
        
        if selection.confidence < 0.1:
            logger.warning(f"Low confidence ({selection.confidence:.2f}) "
                          f"for solver selection: {selection.reason}")
        
        # Update statistics
        if solver_id in self.solver_stats:
            self.solver_stats[solver_id]['usage_count'] += 1
            self.solver_stats[solver_id]['last_used'] = time.time()
        
        # Solve the problem
        start_time = time.time()
        try:
            result = solver.solve(problem)
            elapsed = time.time() - start_time
            
            # Record success
            if solver_id in self.solver_stats:
                self.solver_stats[solver_id]['success_count'] += 1
                self.solver_stats[solver_id]['total_time'] += elapsed
            
            # ===== НАЧАЛО ШАГА 1: ТОПОЛОГИЧЕСКИЙ АНАЛИЗ =====
            # Проводим анализ топологических особенностей решения
            result = self._analyze_topology(result, problem, solver_id)
            # ===== КОНЕЦ ШАГА 1 =====
            
            # Log performance
            self._log_performance({
                'problem_name': problem.get('name', 'unnamed'),
                'solver': solver.__class__.__name__,
                'solver_id': solver_id,
                'selection_confidence': selection.confidence,
                'selection_reason': selection.reason,
                'actual_time': elapsed,
                'estimated_time': selection.estimated_cost.get('time_seconds', 0),
                'success': True,
                'topology_analyzed': 'topology' in getattr(result, 'metadata', {}),  # NEW
            })
            
            # Add manager metadata to result
            if not hasattr(result, 'metadata'):
                result.metadata = {}
            
            result.metadata['solver_manager'] = {
                'selected_solver': solver.__class__.__name__,
                'selection_confidence': selection.confidence,
                'selection_reason': selection.reason,
                'estimated_cost': selection.estimated_cost,
                'actual_time': elapsed,
                'timestamp': time.time(),
                'topology_analysis_performed': True,  # NEW
            }
            
            logger.info(f"Problem solved by {solver.__class__.__name__} "
                       f"in {elapsed:.3f}s (confidence: {selection.confidence:.2f})")
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            
            # Log failure
            self._log_performance({
                'problem_name': problem.get('name', 'unnamed'),
                'solver': solver.__class__.__name__,
                'solver_id': solver_id,
                'selection_confidence': selection.confidence,
                'selection_reason': selection.reason,
                'actual_time': elapsed,
                'estimated_time': selection.estimated_cost.get('time_seconds', 0),
                'success': False,
                'error': str(e),
            })
            
            logger.error(f"Solver {solver.__class__.__name__} failed: {e}")
            raise RuntimeError(
                f"Solver {solver.__class__.__name__} failed to solve problem: {e}"
            ) from e
    
    def _analyze_topology(self, 
                         solution: FieldSolution, 
                         problem: Dict[str, Any],
                         solver_id: str) -> FieldSolution:
        """
        NEW: Analyze topological features of a field solution.
        
        This is the foundation for topological protection, fractality,
        and self-healing analysis.
        
        Args:
            solution: Field solution to analyze
            problem: Original problem description
            solver_id: ID of the solver that produced the solution
            
        Returns:
            FieldSolution enriched with topological metadata
        """
        # Ensure solution has metadata
        if not hasattr(solution, 'metadata'):
            solution.metadata = {}
        
        # Initialize topology section
        if 'topology' not in solution.metadata:
            solution.metadata['topology'] = {
                'features': [],
                'complexity': 'unknown',
                'requires_stitching': False,
                'singularity_count': 0,
                'stability_index': 1.0,  # Default: perfectly stable
            }
        
        # Update solver statistics
        if solver_id in self.solver_stats:
            self.solver_stats[solver_id]['topology_analysis_count'] = \
                self.solver_stats[solver_id].get('topology_analysis_count', 0) + 1
        
        # Estimate topological complexity
        topo_complexity = self._estimate_topological_complexity(problem)
        solution.metadata['topology']['complexity'] = topo_complexity
        
        # Check if stitching will be required
        domain = problem.get('domain', {})
        solution.metadata['topology']['requires_stitching'] = (
            domain.get('type', '1d') in ['2d', '3d'] or
            'subdomains' in problem or
            problem.get('decomposition_strategy') is not None
        )
        
        # ===== АНАЛИЗ ФАЗОВЫХ СИНГУЛЯРНОСТЕЙ (ВИХРЕЙ) =====
        # Это первая конкретная реализация топологического анализа
        
        # Проверяем, есть ли у решения данные о поле
        if hasattr(solution, 'amplitude') and hasattr(solution, 'phase'):
            try:
                # Если фаза представлена как массив
                if isinstance(solution.phase, np.ndarray) and solution.phase.ndim >= 2:
                    features = self._detect_phase_singularities(solution.phase)
                    solution.metadata['topology']['features'].extend(features)
                    solution.metadata['topology']['singularity_count'] = len(features)
                    
                    # Рассчитываем индекс стабильности на основе распределения вихрей
                    if features:
                        stability = self._calculate_topological_stability(features, solution.phase.shape)
                        solution.metadata['topology']['stability_index'] = stability
                        
                        logger.info(f"Detected {len(features)} phase singularities "
                                   f"with stability index {stability:.3f}")
                
                # Если есть поле OAM, анализируем его
                if hasattr(solution, 'oam_distribution'):
                    oam_features = self._analyze_oam_topology(solution)
                    solution.metadata['topology']['features'].extend(oam_features)
                    
            except Exception as e:
                logger.warning(f"Topology analysis failed: {e}")
                # Не прерываем выполнение из-за ошибки анализа
        
        # ===== АНАЛИЗ ГРАНИЧНЫХ УСЛОВИЙ =====
        # Определяем, насколько граничные условия способствуют устойчивости
        boundary_stability = self._analyze_boundary_stability(problem, solution)
        solution.metadata['topology']['boundary_stability'] = boundary_stability
        
        # Кэшируем результаты для будущего использования
        cache_key = f"{problem.get('name', 'unknown')}_{solver_id}_{int(time.time())}"
        self.topology_cache[cache_key] = solution.metadata['topology']['features'].copy()
        
        # Ограничиваем размер кэша
        if len(self.topology_cache) > 100:
            # Удаляем самые старые записи
            oldest_keys = sorted(self.topology_cache.keys())[:10]
            for key in oldest_keys:
                del self.topology_cache[key]
        
        return solution
    
    def _detect_phase_singularities(self, phase_field: np.ndarray) -> List[TopologicalFeature]:
        """
        Detect phase singularities (vortices) in a 2D phase field.
        
        Args:
            phase_field: 2D numpy array of phase values
            
        Returns:
            List of detected topological features
        """
        features = []
        
        if phase_field.ndim != 2:
            return features  # Только для 2D полей
        
        # Нормализуем фазу к диапазону [0, 2π)
        phase_norm = phase_field % (2 * np.pi)
        
        # Ищем вихри через анализ циркуляции фазы вокруг каждой точки
        height, width = phase_norm.shape
        
        # Минимальный размер для анализа
        if height < 3 or width < 3:
            return features
        
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Вычисляем циркуляцию фазы по маленькому квадрату 3x3
                phase_corners = [
                    phase_norm[y-1, x-1], phase_norm[y-1, x], phase_norm[y-1, x+1],
                    phase_norm[y, x+1], phase_norm[y+1, x+1], phase_norm[y+1, x],
                    phase_norm[y+1, x-1], phase_norm[y, x-1], phase_norm[y-1, x-1]
                ]
                
                # Вычисляем разности фаз (учитываем переход через 2π)
                phase_diffs = []
                for i in range(8):
                    diff = phase_corners[i+1] - phase_corners[i]
                    # Корректируем разность для переходов через 2π
                    if diff > np.pi:
                        diff -= 2 * np.pi
                    elif diff < -np.pi:
                        diff += 2 * np.pi
                    phase_diffs.append(diff)
                
                # Суммарное изменение фазы (должно быть кратно 2π для вихря)
                total_phase_change = sum(phase_diffs)
                
                # Вихрь определяется ненулевым целым числом оборотов
                winding_number = round(total_phase_change / (2 * np.pi))
                
                if winding_number != 0:
                    # Вычисляем силу вихря (чем ближе winding_number к целому, тем сильнее)
                    strength = abs(winding_number)
                    
                    # Оцениваем стабильность по локальному градиенту фазы
                    grad_y = phase_norm[y+1, x] - phase_norm[y-1, x]
                    grad_x = phase_norm[y, x+1] - phase_norm[y, x-1]
                    gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
                    
                    # Стабильность выше при плавном изменении фазы вокруг вихря
                    stability = 1.0 / (1.0 + gradient_magnitude)
                    
                    feature = TopologicalFeature(
                        feature_type='vortex',
                        position=(float(x), float(y)),
                        strength=strength,
                        stability_index=stability,
                        metadata={
                            'winding_number': winding_number,
                            'gradient_magnitude': float(gradient_magnitude),
                        }
                    )
                    features.append(feature)
        
        return features
    
    def _calculate_topological_stability(self, 
                                        features: List[TopologicalFeature],
                                        field_shape: Tuple[int, int]) -> float:
        """
        Calculate overall topological stability of a field.
        
        Args:
            features: List of topological features
            field_shape: Shape of the field (height, width)
            
        Returns:
            Stability index from 0.0 (unstable) to 1.0 (stable)
        """
        if not features:
            return 1.0  # Нет вихрей = стабильно
        
        height, width = field_shape
        total_area = height * width
        
        # 1. Рассчитываем среднюю стабильность вихрей
        avg_feature_stability = np.mean([f.stability_index for f in features])
        
        # 2. Рассчитываем равномерность распределения вихрей
        # Более равномерное распределение = более стабильная система
        positions = np.array([f.position for f in features])
        
        if len(features) > 1:
            # Вычисляем минимальные попарные расстояния
            from scipy.spatial import distance
            dist_matrix = distance.cdist(positions, positions)
            np.fill_diagonal(dist_matrix, np.inf)  # Исключаем диагональ
            min_distances = np.min(dist_matrix, axis=1)
            avg_min_distance = np.mean(min_distances)
            
            # Нормализуем расстояние (идеально ~10% от размера поля)
            optimal_distance = 0.1 * min(height, width)
            distance_score = np.exp(-((avg_min_distance - optimal_distance) / optimal_distance)**2)
        else:
            distance_score = 1.0  # Один вихрь - нейтрально
        
        # 3. Учитываем общее количество вихрей
        # Слишком много вихрей = нестабильно, слишком мало = может быть неустойчиво к возмущениям
        optimal_count = total_area / 100  # Эвристика: 1 вихрь на 100 пикселей
        count_ratio = len(features) / optimal_count if optimal_count > 0 else 1.0
        count_score = np.exp(-(count_ratio - 1.0)**2)
        
        # Комбинируем оценки
        stability = 0.4 * avg_feature_stability + 0.3 * distance_score + 0.3 * count_score
        
        return float(np.clip(stability, 0.0, 1.0))
    
    def _analyze_oam_topology(self, solution: FieldSolution) -> List[TopologicalFeature]:
        """
        Analyze OAM (orbital angular momentum) topology.
        
        Args:
            solution: Field solution with OAM distribution
            
        Returns:
            List of OAM-related topological features
        """
        features = []
        
        # Проверяем наличие OAM-распределения
        if not hasattr(solution, 'oam_distribution'):
            return features
        
        oam_field = solution.oam_distribution
        
        if not isinstance(oam_field, np.ndarray) or oam_field.ndim != 2:
            return features
        
        # Ищем области с постоянным OAM
        # (В будущем здесь будет более сложный анализ)
        
        return features
    
    def _analyze_boundary_stability(self, 
                                   problem: Dict[str, Any], 
                                   solution: FieldSolution) -> float:
        """
        Analyze how boundary conditions affect topological stability.
        
        Args:
            problem: Problem description
            solution: Field solution
            
        Returns:
            Boundary stability index from 0.0 to 1.0
        """
        # Базовая реализация
        boundary_type = problem.get('parameters', {}).get('boundary_conditions', 'absorbing')
        
        # Разные типы граничных условий дают разную устойчивость
        stability_map = {
            'periodic': 0.9,      # Периодические - очень стабильные
            'absorbing': 0.7,     # Поглощающие - умеренно стабильные
            'reflecting': 0.5,    # Отражающие - могут создавать стоячие волны
            'dirichlet': 0.6,     # Условия Дирихле
            'neumann': 0.65,      # Условия Неймана
            'open': 0.4,          # Открытые - наименее стабильные
        }
        
        return stability_map.get(boundary_type.lower(), 0.5)
    
    def solve_with_specific_solver(self, 
                                  solver_id: str, 
                                  problem: Dict[str, Any]) -> FieldSolution:
        """
        Solve a problem using a specific solver.
        
        Args:
            solver_id: ID of the solver to use
            problem: Problem description dictionary
            
        Returns:
            FieldSolution with results
            
        Raises:
            KeyError: If solver_id is not found
            ValueError: If solver cannot solve the problem
        """
        if solver_id not in self.solvers:
            available = list(self.solvers.keys())
            raise KeyError(f"Solver '{solver_id}' not found. Available: {available}")
        
        solver = self.solvers[solver_id]
        
        # Check compatibility
        can_solve = True
        if hasattr(solver, 'can_solve'):
            try:
                can_solve, reason = solver.can_solve(problem)
                if not can_solve:
                    raise ValueError(f"Solver {solver.__class__.__name__} "
                                    f"cannot solve this problem: {reason}")
            except Exception as e:
                logger.warning(f"Error checking solver compatibility: {e}")
                # Continue anyway
        
        return solver.solve(problem)
    
    def decompose_problem(self, 
                         problem: Dict[str, Any],
                         decomposition_strategy: str = 'auto') -> List[HybridProblemPart]:
        """
        Decompose a complex problem into parts for different solvers.
        
        Args:
            problem: Complex problem description
            decomposition_strategy: Strategy for decomposition ('auto', 'spatial', 'physical')
            
        Returns:
            List of problem parts for different solvers
        """
        # Basic implementation - can be extended for complex decompositions
        parts = []
        
        if decomposition_strategy == 'auto':
            # For now, just return the whole problem as one part
            parts.append(HybridProblemPart(
                domain_id='full_domain',
                problem_description=problem,
            ))
        
        elif decomposition_strategy == 'spatial':
            # Spatial decomposition based on domain
            domain = problem.get('domain', {})
            domain_type = domain.get('type', '1d')
            
            if domain_type == '2d':
                # Simple 2x2 spatial decomposition
                width = domain.get('width', 10e-6)
                height = domain.get('height', 10e-6)
                
                subdomains = [
                    ('bottom_left', {'x_min': 0, 'x_max': width/2, 
                                    'y_min': 0, 'y_max': height/2}),
                    ('bottom_right', {'x_min': width/2, 'x_max': width, 
                                     'y_min': 0, 'y_max': height/2}),
                    ('top_left', {'x_min': 0, 'x_max': width/2, 
                                 'y_min': height/2, 'y_max': height}),
                    ('top_right', {'x_min': width/2, 'x_max': width, 
                                  'y_min': height/2, 'y_max': height}),
                ]
                
                for domain_id, bounds in subdomains:
                    sub_problem = problem.copy()
                    sub_problem['domain'] = {**domain, **bounds, 'type': '2d'}
                    parts.append(HybridProblemPart(
                        domain_id=domain_id,
                        problem_description=sub_problem,
                    ))
            else:
                # 1D or simple domain
                parts.append(HybridProblemPart(
                    domain_id='full_domain',
                    problem_description=problem,
                ))
        
        return parts
    
    def solve_hybrid(self, 
                    problem: Dict[str, Any],
                    decomposition_strategy: str = 'auto') -> FieldSolution:
        """
        Solve a problem using hybrid approach with multiple solvers.
        
        Note: This is a placeholder for future implementation.
        Currently uses single solver selection.
        
        Args:
            problem: Problem description
            decomposition_strategy: How to decompose the problem
            
        Returns:
            FieldSolution with results
        """
        logger.info(f"Solving with hybrid approach (strategy: {decomposition_strategy})")
        
        # For Phase 2, just use single solver selection
        # Future: implement actual hybrid decomposition and stitching
        return self.solve(problem)
    
    def _log_performance(self, data: Dict[str, Any]) -> None:
        """Log performance data."""
        self.performance_log.append(data)
        
        # Keep log size manageable
        if len(self.performance_log) > 1000:
            self.performance_log = self.performance_log[-500:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report."""
        if not self.performance_log:
            return {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'success_rate': 0.0,
                'total_time': 0.0,
                'average_time': 0.0,
                'recent_runs': [],
            }
        
        total_runs = len(self.performance_log)
        successful = sum(1 for entry in self.performance_log 
                        if entry.get('success', False))
        total_time = sum(entry.get('actual_time', 0) 
                        for entry in self.performance_log)
        
        return {
            'total_runs': total_runs,
            'successful_runs': successful,
            'failed_runs': total_runs - successful,
            'success_rate': successful / total_runs if total_runs > 0 else 0.0,
            'total_time': total_time,
            'average_time': total_time / total_runs if total_runs > 0 else 0.0,
            'recent_runs': self.performance_log[-
