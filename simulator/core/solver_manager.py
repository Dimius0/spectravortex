# simulator/core/solver_manager.py
"""
Solver Manager for Hybrid Architecture.
The "brain" that coordinates multiple solvers and enables automatic solver selection.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import numpy as np
import time

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

class SolverManager:
    """
    Manages multiple solvers and coordinates hybrid computations.
    
    Features:
    - Automatic solver selection based on problem characteristics
    - Solver registry and discovery
    - Hybrid problem decomposition
    - Performance monitoring and logging
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
            'recent_runs': self.performance_log[-10:] if self.performance_log else [],
        }
    
    def get_solver_statistics(self, solver_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for solvers.
        
        Args:
            solver_id: Optional specific solver ID
            
        Returns:
            Dictionary with statistics
        """
        if solver_id:
            if solver_id not in self.solver_stats:
                raise KeyError(f"Solver '{solver_id}' not found")
            return self.solver_stats[solver_id].copy()
        
        # Return all statistics
        summary = {}
        for sid, stats in self.solver_stats.items():
            summary[sid] = {
                'name': stats.get('name', 'unknown'),
                'usage': stats.get('usage_count', 0),
                'success': stats.get('success_count', 0),
                'success_rate': self._calculate_success_rate(sid),
                'total_time': stats.get('total_time', 0.0),
                'last_used': stats.get('last_used'),
            }
        
        return {
            'total_solvers': len(self.solvers),
            'solver_stats': self.solver_stats.copy(),
            'summary': summary,
        }
    
    def reset_statistics(self) -> None:
        """Reset all statistics."""
        for stats in self.solver_stats.values():
            stats['usage_count'] = 0
            stats['success_count'] = 0
            stats['total_time'] = 0.0
            stats['last_used'] = None
        
        self.performance_log.clear()
        logger.info("Statistics reset")


# Factory function
def create_solver_manager(enable_auto_selection: bool = True) -> SolverManager:
    """
    Create a SolverManager instance with default configuration.
    
    Args:
        enable_auto_selection: Whether to enable automatic solver selection
        
    Returns:
        SolverManager instance
    """
    manager = SolverManager(enable_auto_selection=enable_auto_selection)
    manager.register_default_solvers()
    return manager
