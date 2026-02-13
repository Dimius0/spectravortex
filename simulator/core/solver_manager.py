"""
Solver Manager for Hybrid Photonic Solver Architecture.

This is the central coordination system for Phase 3.1-3.3:
- Phase 3.1: Automatic solver selection based on problem type
- Phase 3.2: Recursive/fractal problem decomposition coordination
- Phase 3.3: Resilience and fallback management
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from simulator.core.solver import Solver
from simulator.core.data_interface import FieldSolution, SimulationDomain

logger = logging.getLogger(__name__)


@dataclass
class SolverPerformance:
    """Tracks performance metrics for a solver."""
    total_calls: int = 0
    successful_calls: int = 0
    total_time: float = 0.0
    last_called: float = 0.0
    last_success: bool = False
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def avg_time(self) -> float:
        """Calculate average execution time."""
        if self.total_calls == 0:
            return 0.0
        return self.total_time / self.total_calls


class SolverManager:
    """
    Central manager for coordinating multiple specialized solvers.
    
    Key responsibilities:
    1. Registry of available solvers
    2. Automatic solver selection based on problem characteristics
    3. Performance tracking and learning
    4. Fallback strategies when primary solver fails
    5. Coordination of multi-solver workflows (stitching, recursion)
    """
    
    def __init__(self, name: str = "SolverManager"):
        self.name = name
        self.solvers: Dict[str, Solver] = {}
        self.solver_history: Dict[str, SolverPerformance] = {}
        self.solver_priorities: Dict[str, int] = {}  # Higher number = higher priority
        self.resilience_mode: bool = False
        self.fallback_strategy: str = "sequential"
        
        # Stitching coordination
        self.stitching_enabled: bool = True
        self.stitching_solver_id: Optional[str] = None
        
        # Recursive decomposition coordination
        self.recursion_enabled: bool = True
        self.recursive_solver_id: Optional[str] = None
        
        logger.info(f"Initialized SolverManager: {name}")
    
    def register_solver(self, solver: Solver, priority: int = 5) -> str:
        """
        Register a solver with the manager.
        
        Args:
            solver: The solver instance to register
            priority: Priority for automatic selection (1-10)
            
        Returns:
            Unique solver ID
        """
        # Generate unique ID
        solver_id = f"{solver.__class__.__name__}_{id(solver)}"
        
        # Register solver
        self.solvers[solver_id] = solver
        self.solver_priorities[solver_id] = min(max(priority, 1), 10)
        
        # Initialize performance tracking
        self.solver_history[solver_id] = SolverPerformance()
        
        # Check for special solver types
        solver_type = solver.__class__.__name__.lower()
        
        if "stitch" in solver_type:
            self.stitching_solver_id = solver_id
            logger.info(f"Registered stitching solver: {solver_id}")
        
        if "recursive" in solver_type:
            self.recursive_solver_id = solver_id
            logger.info(f"Registered recursive solver: {solver_id}")
        
        logger.info(f"Registered solver: {solver_id} (priority: {priority})")
        return solver_id
    
    def unregister_solver(self, solver_id: str) -> bool:
        """
        Unregister a solver.
        
        Args:
            solver_id: ID of the solver to unregister
            
        Returns:
            True if successful, False otherwise
        """
        if solver_id not in self.solvers:
            logger.warning(f"Solver {solver_id} not found for unregistration")
            return False
        
        # Remove from special solver tracking if needed
        if solver_id == self.stitching_solver_id:
            self.stitching_solver_id = None
        if solver_id == self.recursive_solver_id:
            self.recursive_solver_id = None
        
        # Remove solver
        del self.solvers[solver_id]
        del self.solver_priorities[solver_id]
        del self.solver_history[solver_id]
        
        logger.info(f"Unregistered solver: {solver_id}")
        return True
    
    def list_solvers(self) -> List[Dict[str, Any]]:
        """
        List all registered solvers with their capabilities.
        
        Returns:
            List of solver information dictionaries
        """
        solvers_info = []
        
        for solver_id, solver in self.solvers.items():
            info = {
                'id': solver_id,
                'name': solver.name,
                'class': solver.__class__.__name__,
                'priority': self.solver_priorities.get(solver_id, 5),
                'performance': {
                    'total_calls': self.solver_history[solver_id].total_calls,
                    'success_rate': self.solver_history[solver_id].success_rate,
                    'avg_time': self.solver_history[solver_id].avg_time
                }
            }
            
            # Add requirements if available
            if hasattr(solver, 'get_requirements'):
                try:
                    info['requirements'] = solver.get_requirements()
                except Exception as e:
                    logger.debug(f"Error getting requirements for {solver_id}: {e}")
                    info['requirements'] = {}
            
            solvers_info.append(info)
        
        return solvers_info
    
    def _assess_problem_complexity(self, problem: Dict[str, Any]) -> float:
        """
        Assess the complexity of a problem (0-10 scale).
        
        Args:
            problem: Problem dictionary
            
        Returns:
            Complexity score
        """
        complexity = 1.0  # Base complexity
        
        # Size-based complexity
        if 'grid_size' in problem:
            size = problem['grid_size']
            if isinstance(size, tuple):
                complexity += min(sum(size) / 50, 5.0)
            elif isinstance(size, int):
                complexity += min(size / 25, 5.0)
        
        # Nonlinearity increases complexity
        if problem.get('nonlinear', False):
            complexity += 2.0
        
        # Multiple domains increase complexity
        if 'subdomains' in problem:
            complexity += min(len(problem['subdomains']) * 0.5, 3.0)
        
        # Complex boundary conditions
        if 'boundary_conditions' in problem:
            bc_count = len(problem['boundary_conditions'])
            complexity += min(bc_count * 0.3, 2.0)
        
        # Multiple sources
        if 'sources' in problem:
            complexity += min(len(problem['sources']) * 0.4, 2.0)
        
        # Constrain to 1-10 range
        return max(1.0, min(complexity, 10.0))
    
    def _evaluate_solver(self, solver, solver_id, problem):
        """
        Evaluate a solver for a given problem.
        Returns (confidence, reason).
        """
        try:
            # Get solver's self-assessment
            can_solve_result = solver.can_solve(problem)
            
            # Handle different return formats
            if isinstance(can_solve_result, tuple):
                if len(can_solve_result) == 2:
                    can_solve, confidence = can_solve_result
                    reason = "Suitable for problem"
                elif len(can_solve_result) == 3:
                    can_solve, confidence, reason = can_solve_result
                else:
                    can_solve = bool(can_solve_result[0]) if can_solve_result else False
                    confidence = 0.5 if can_solve else 0.0
                    reason = "Unexpected return format"
            else:
                # Single value returned
                can_solve = bool(can_solve_result)
                confidence = 0.5 if can_solve else 0.0
                reason = "Single value return"
            
            if not can_solve:
                return 0.0, reason if isinstance(reason, str) else "Cannot solve problem"
            
            # Adjust confidence based on solver history
            if solver_id in self.solver_history:
                success_rate = self.solver_history[solver_id].success_rate
                confidence = confidence * 0.7 + success_rate * 0.3
            
            # Special handling for recursive solvers
            if "recursive" in solver_id.lower() or (hasattr(solver, 'get_requirements') and 
                                                   solver.get_requirements().get('recursion_support', False)):
                # Check if problem would benefit from recursion
                problem_complexity = self._assess_problem_complexity(problem)
                if problem_complexity > 5:  # Medium complexity or higher
                    confidence *= 1.2  # Boost for complex problems
                    if isinstance(reason, str):
                        reason += " (recursive specialist)"
                    else:
                        reason = "Recursive specialist for complex problem"
                
            return min(confidence, 1.0), reason if isinstance(reason, str) else "Suitable for problem"
            
        except Exception as e:
            logger.error(f"Error evaluating solver {solver_id}: {e}")
            return 0.0, f"Evaluation error: {e}"
    
    def select_solver(self, problem: Dict[str, Any]) -> Tuple[Optional[str], float, str]:
        """
        Select the most appropriate solver for a given problem.
        
        Args:
            problem: Problem dictionary
            
        Returns:
            Tuple of (solver_id, confidence, reason) or (None, 0.0, reason)
        """
        if not self.solvers:
            return None, 0.0, "No solvers registered"
        
        # Special case: stitching problems
        if problem.get('problem_type') == 'stitching' and self.stitching_solver_id:
            stitching_solver = self.solvers.get(self.stitching_solver_id)
            if stitching_solver:
                confidence, reason = self._evaluate_solver(
                    stitching_solver, self.stitching_solver_id, problem
                )
                return self.stitching_solver_id, confidence, reason
        
        # Special case: problems with multiple subdomains
        if ('subdomain_solutions' in problem or 
            (problem.get('subdomains') and len(problem['subdomains']) > 1)):
            if self.stitching_solver_id and self.stitching_enabled:
                stitching_solver = self.solvers.get(self.stitching_solver_id)
                if stitching_solver:
                    confidence, reason = self._evaluate_solver(
                        stitching_solver, self.stitching_solver_id, problem
                    )
                    if confidence > 0.3:
                        return self.stitching_solver_id, confidence, reason
        
        # Evaluate all solvers
        evaluations = []
        for solver_id, solver in self.solvers.items():
            # Skip stitching solver for non-stitching problems (unless explicitly needed)
            if solver_id == self.stitching_solver_id and not problem.get('requires_stitching', False):
                continue
            
            confidence, reason = self._evaluate_solver(solver, solver_id, problem)
            
            # Apply priority boost
            priority = self.solver_priorities.get(solver_id, 5)
            confidence = confidence * (0.8 + priority * 0.04)  # 5% boost per priority level
            
            evaluations.append((solver_id, confidence, reason))
        
        if not evaluations:
            return None, 0.0, "No suitable solvers found"
        
        # Sort by confidence (descending)
        evaluations.sort(key=lambda x: x[1], reverse=True)
        
        # Return best solver
        best_solver_id, best_confidence, best_reason = evaluations[0]
        
        # Apply minimum confidence threshold
        if best_confidence < 0.1:
            return None, best_confidence, f"Low confidence ({best_confidence:.2f}): {best_reason}"
        
        logger.info(f"Selected solver {best_solver_id} with confidence {best_confidence:.2f}: {best_reason}")
        return best_solver_id, best_confidence, best_reason
    
    def solve(self, problem: Dict[str, Any]) -> FieldSolution:
        """
        Solve a problem using the most appropriate solver.
        
        Args:
            problem: Problem dictionary
            
        Returns:
            FieldSolution from the selected solver
            
        Raises:
            RuntimeError: If no solver can solve the problem
        """
        start_time = time.time()
        
        # Add problem ID if not present
        if 'problem_id' not in problem:
            problem['problem_id'] = f"problem_{int(time.time())}_{hash(str(problem)) % 10000}"
        
        # Select solver
        solver_id, confidence, reason = self.select_solver(problem)
        
        if solver_id is None:
            error_msg = f"No suitable solver found for problem: {reason}"
            logger.error(error_msg)
            
            # Create fallback solution
            fallback_solution = FieldSolution(
                amplitude=np.array([[1.0]]),
                phase=np.array([[0.0]]),
                spatial_dim=2,
                solver_used="SolverManager_fallback",
                metadata={
                    'error': error_msg,
                    'problem_id': problem.get('problem_id', 'unknown'),
                    'fallback': True
                }
            )
            
            if self.resilience_mode:
                logger.warning(f"Resilience mode: returning fallback solution for {problem.get('problem_id', 'unknown')}")
                return fallback_solution
            else:
                raise RuntimeError(error_msg)
        
        if confidence < 0.3:
            logger.warning(f"Low confidence ({confidence:.2f}) for solver selection: {reason}")
        
        # Get the solver
        solver = self.solvers[solver_id]
        
        # Update performance tracking
        performance = self.solver_history[solver_id]
        performance.total_calls += 1
        performance.last_called = time.time()
        
        # Attempt to solve
        try:
            logger.info(f"Solving with {solver_id} (confidence: {confidence:.2f})")
            
            result = solver.solve(problem)
            
            # Mark as successful
            performance.successful_calls += 1
            performance.last_success = True
            performance.total_time += time.time() - start_time
            
            # Add solver manager metadata
            if result.metadata is None:
                result.metadata = {}
            
            result.metadata.update({
                'solver_manager_id': self.name,
                'selected_solver': solver_id,
                'selection_confidence': confidence,
                'selection_reason': reason,
                'solver_manager_timestamp': time.time(),
                'total_execution_time': time.time() - start_time
            })
            
            logger.info(f"Solution completed by {solver_id} in {time.time() - start_time:.3f}s")
            return result
            
        except Exception as e:
            # Mark as failed
            performance.last_success = False
            performance.total_time += time.time() - start_time
            
            error_msg = f"Solver {solver_id} failed to solve problem: {e}"
            logger.error(error_msg)
            
            # Fallback strategy
            if self.resilience_mode:
                logger.info(f"Attempting fallback strategy: {self.fallback_strategy}")
                
                if self.fallback_strategy == "sequential":
                    # Try other solvers in order of confidence
                    return self._sequential_fallback(problem, solver_id, start_time)
                elif self.fallback_strategy == "recursive":
                    # Try recursive decomposition
                    return self._recursive_fallback(problem, solver_id, start_time)
                else:
                    # Return fallback solution
                    return self._create_fallback_solution(problem, error_msg, start_time)
            else:
                raise RuntimeError(error_msg) from e
    
    def solve_with_specific_solver(self, solver_id: str, problem: Dict[str, Any]) -> FieldSolution:
        """
        Solve a problem using a specific solver (bypassing automatic selection).
        
        Args:
            solver_id: ID of the solver to use
            problem: Problem dictionary
            
        Returns:
            FieldSolution from the specified solver
            
        Raises:
            ValueError: If solver_id is not found
            RuntimeError: If solver fails
        """
        if solver_id not in self.solvers:
            raise ValueError(f"Solver {solver_id} not found")
        
        solver = self.solvers[solver_id]
        
        # Update performance tracking
        performance = self.solver_history[solver_id]
        performance.total_calls += 1
        performance.last_called = time.time()
        
        # Attempt to solve
        try:
            logger.info(f"Solving with specific solver: {solver_id}")
            result = solver.solve(problem)
            
            # Mark as successful
            performance.successful_calls += 1
            performance.last_success = True
            
            # Add metadata
            if result.metadata is None:
                result.metadata = {}
            
            result.metadata.update({
                'forced_solver': solver_id,
                'solver_manager_id': self.name,
                'forced_solution': True
            })
            
            return result
            
        except Exception as e:
            # Mark as failed
            performance.last_success = False
            
            error_msg = f"Specific solver {solver_id} failed: {e}"
            logger.error(error_msg)
            
            if self.resilience_mode:
                # Fall back to automatic selection
                logger.info(f"Falling back to automatic solver selection")
                return self.solve(problem)
            else:
                raise RuntimeError(error_msg) from e
    
    def _sequential_fallback(self, problem: Dict[str, Any], failed_solver_id: str, start_time: float) -> FieldSolution:
        """Try other solvers in sequence."""
        logger.info(f"Sequential fallback: trying other solvers after {failed_solver_id} failed")
        
        for solver_id, solver in self.solvers.items():
            if solver_id == failed_solver_id:
                continue
            
            try:
                logger.info(f"Trying fallback solver: {solver_id}")
                
                # Check if solver can handle the problem
                can_solve_result = solver.can_solve(problem)
                if isinstance(can_solve_result, tuple):
                    can_solve = can_solve_result[0]
                else:
                    can_solve = bool(can_solve_result)
                
                if not can_solve:
                    logger.debug(f"Solver {solver_id} cannot solve this problem")
                    continue
                
                # Attempt to solve
                result = solver.solve(problem)
                
                # Update performance for successful fallback
                performance = self.solver_history[solver_id]
                performance.total_calls += 1
                performance.successful_calls += 1
                performance.last_success = True
                performance.total_time += time.time() - start_time
                
                # Add fallback metadata
                if result.metadata is None:
                    result.metadata = {}
                
                result.metadata.update({
                    'fallback_solver': solver_id,
                    'original_failure': failed_solver_id,
                    'fallback_success': True,
                    'total_fallback_time': time.time() - start_time
                })
                
                logger.info(f"Fallback successful with {solver_id}")
                return result
                
            except Exception as e:
                logger.debug(f"Fallback solver {solver_id} also failed: {e}")
                # Continue to next solver
        
        # All solvers failed
        error_msg = f"All solvers failed for problem {problem.get('problem_id', 'unknown')}"
        logger.error(error_msg)
        return self._create_fallback_solution(problem, error_msg, start_time)
    
    def _recursive_fallback(self, problem: Dict[str, Any], failed_solver_id: str, start_time: float) -> FieldSolution:
        """Try recursive decomposition as fallback."""
        logger.info(f"Recursive fallback: attempting decomposition after {failed_solver_id} failed")
        
        if not self.recursive_solver_id or self.recursive_solver_id not in self.solvers:
            logger.warning("No recursive solver available for fallback")
            return self._sequential_fallback(problem, failed_solver_id, start_time)
        
        recursive_solver = self.solvers[self.recursive_solver_id]
        
        try:
            # Check if recursive solver can handle the problem
            can_solve_result = recursive_solver.can_solve(problem)
            if isinstance(can_solve_result, tuple):
                can_solve = can_solve_result[0]
            else:
                can_solve = bool(can_solve_result)
            
            if not can_solve:
                logger.debug("Recursive solver cannot solve this problem")
                return self._sequential_fallback(problem, failed_solver_id, start_time)
            
            # Attempt recursive decomposition
            result = recursive_solver.solve(problem)
            
            # Update performance
            performance = self.solver_history[self.recursive_solver_id]
            performance.total_calls += 1
            performance.successful_calls += 1
            performance.last_success = True
            performance.total_time += time.time() - start_time
            
            # Add recursive fallback metadata
            if result.metadata is None:
                result.metadata = {}
            
            result.metadata.update({
                'recursive_fallback': True,
                'original_failure': failed_solver_id,
                'recursive_decomposition': True,
                'total_recursive_time': time.time() - start_time
            })
            
            logger.info(f"Recursive fallback successful")
            return result
            
        except Exception as e:
            logger.error(f"Recursive fallback also failed: {e}")
            return self._sequential_fallback(problem, failed_solver_id, start_time)
    
    def _create_fallback_solution(self, problem: Dict[str, Any], error_msg: str, start_time: float) -> FieldSolution:
        """Create a minimal fallback solution."""
        logger.warning(f"Creating minimal fallback solution for {problem.get('problem_id', 'unknown')}")
        
        # Create simple field
        amplitude = np.ones((10, 10))
        phase = np.zeros((10, 10))
        
        return FieldSolution(
            amplitude=amplitude,
            phase=phase,
            spatial_dim=2,
            solver_used="SolverManager_emergency_fallback",
            metadata={
                'error': error_msg,
                'problem_id': problem.get('problem_id', 'unknown'),
                'emergency_fallback': True,
                'fallback_timestamp': time.time(),
                'total_failure_time': time.time() - start_time
            }
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a performance report for all solvers.
        
        Returns:
            Dictionary with performance statistics
        """
        report = {
            'total_solvers': len(self.solvers),
            'total_calls': sum(p.total_calls for p in self.solver_history.values()),
            'successful_calls': sum(p.successful_calls for p in self.solver_history.values()),
            'overall_success_rate': 0.0,
            'solvers': {}
        }
        
        # Calculate overall success rate
        total_calls = report['total_calls']
        if total_calls > 0:
            report['overall_success_rate'] = report['successful_calls'] / total_calls
        
        # Individual solver statistics
        for solver_id, performance in self.solver_history.items():
            report['solvers'][solver_id] = {
                'total_calls': performance.total_calls,
                'successful_calls': performance.successful_calls,
                'success_rate': performance.success_rate,
                'avg_time': performance.avg_time,
                'last_called': performance.last_called,
                'last_success': performance.last_success
            }
        
        return report
    
    def enable_resilience_mode(self, strategy: str = "sequential"):
        """
        Enable resilience mode with specified fallback strategy.
        
        Args:
            strategy: Fallback strategy ("sequential", "recursive", or "minimal")
        """
        self.resilience_mode = True
        self.fallback_strategy = strategy
        logger.info(f"Resilience mode enabled with strategy: {strategy}")
    
    def disable_resilience_mode(self):
        """Disable resilience mode."""
        self.resilience_mode = False
        logger.info("Resilience mode disabled")
    
    def enable_stitching(self):
        """Enable stitching solver coordination."""
        self.stitching_enabled = True
        logger.info("Stitching coordination enabled")
    
    def disable_stitching(self):
        """Disable stitching solver coordination."""
        self.stitching_enabled = False
        logger.info("Stitching coordination disabled")
    
    def enable_recursion(self):
        """Enable recursive solver coordination."""
        self.recursion_enabled = True
        logger.info("Recursive coordination enabled")
    
    def disable_recursion(self):
        """Disable recursive solver coordination."""
        self.recursion_enabled = False
        logger.info("Recursive coordination disabled")


def create_solver_manager() -> SolverManager:
    """
    Factory function to create a SolverManager with default solvers.
    
    Returns:
        Configured SolverManager instance
    """
    manager = SolverManager("DefaultSolverManager")
    
    # Try to register default solvers
    try:
        from simulator.solvers.linear_wave_solver import LinearWaveSolver
        linear_solver = LinearWaveSolver()
        manager.register_solver(linear_solver, priority=10)
    except ImportError as e:
        logger.warning(f"LinearWaveSolver not available: {e}")
    
    try:
        from simulator.solvers.stitching_solver import StitchingSolver
        stitching_solver = StitchingSolver()
        manager.register_solver(stitching_solver, priority=5)
    except ImportError as e:
        logger.warning(f"StitchingSolver not available: {e}")
    
    try:
        from simulator.solvers.recursive_solver import RecursiveSolver
        recursive_solver = RecursiveSolver()
        manager.register_solver(recursive_solver, priority=8)
    except ImportError as e:
        logger.warning(f"RecursiveSolver not available: {e}")
    
    # Enable resilience by default
    manager.enable_resilience_mode()
    
    return manager


# Need numpy for fallback solutions
import numpy as np