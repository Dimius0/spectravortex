"""
API Integration for Phase 3 Solvers
Connects StitchingSolver and RecursiveSolver with SpectraVortex API
"""

import time
from typing import Dict, Any, Optional, Tuple
import logging

from config import config
from local_api_client import get_auto_client

logger = logging.getLogger(__name__)

class SolverAPIAdapter:
    """Adapter between Solvers and API"""
    
    def __init__(self, solver_type: str = 'auto'):
        """
        Initialize adapter
        
        Args:
            solver_type: 'stitching', 'recursive', or 'auto'
        """
        self.solver_type = solver_type
        self.api_client = get_auto_client()
        
        # Import solvers
        try:
            from simulator.solvers.stitching_solver import StitchingSolver
            from simulator.solvers.recursive_solver import RecursiveSolver
            
            self.stitching_solver = StitchingSolver()
            self.recursive_solver = RecursiveSolver()
            
            logger.info(f"SolverAPIAdapter initialized with {solver_type} solver")
            
        except ImportError as e:
            logger.error(f"Failed to import solvers: {e}")
            raise
    
    def select_best_solver(self, problem: Dict[str, Any]) -> Tuple[Any, str, float]:
        """
        Select best solver for the problem
        
        Returns:
            (solver_instance, solver_name, confidence)
        """
        # Check which solver can solve the problem
        can_stitch, conf_stitch = self.stitching_solver.can_solve(problem)
        can_recur, conf_recur = self.recursive_solver.can_solve(problem)
        
        logger.debug(f"Solver capabilities - Stitching: {can_stitch} ({conf_stitch:.2f}), "
                    f"Recursive: {can_recur} ({conf_recur:.2f})")
        
        # Select based on solver_type preference
        if self.solver_type == 'stitching' and can_stitch:
            return self.stitching_solver, 'stitching', conf_stitch
        elif self.solver_type == 'recursive' and can_recur:
            return self.recursive_solver, 'recursive', conf_recur
        elif self.solver_type == 'auto':
            # Auto-select based on confidence
            if can_stitch and can_recur:
                if conf_stitch >= conf_recur:
                    return self.stitching_solver, 'stitching', conf_stitch
                else:
                    return self.recursive_solver, 'recursive', conf_recur
            elif can_stitch:
                return self.stitching_solver, 'stitching', conf_stitch
            elif can_recur:
                return self.recursive_solver, 'recursive', conf_recur
        
        # No suitable solver found
        raise ValueError(f"No suitable solver found for problem: {problem.get('problem_type', 'unknown')}")
    
    def solve_with_api(self, problem: Dict[str, Any], use_local: bool = False) -> Dict[str, Any]:
        """
        Solve problem using API
        
        Args:
            problem: Problem definition
            use_local: If True, use local solver instead of API
            
        Returns:
            Solution data
        """
        problem_type = problem.get('problem_type', 'unknown')
        logger.info(f"Solving problem '{problem_type}' with API (local={use_local})")
        
        if use_local or not self.api_client.health_check():
            # Use local solver
            return self._solve_locally(problem)
        
        # Use API
        try:
            # Select best solver
            solver, solver_name, confidence = self.select_best_solver(problem)
            
            # Prepare problem data for API
            api_problem = {
                **problem,
                'solver_type': solver_name,
                'solver_confidence': confidence,
                'metadata': {
                    'client_version': '1.0.0',
                    'timestamp': time.time()
                }
            }
            
            # Submit to API
            logger.info(f"Submitting to API with {solver_name} solver (confidence: {confidence:.2f})")
            submission = self.api_client.solve_problem(api_problem)
            
            if submission['status'] != 'submitted':
                logger.warning(f"API submission failed: {submission}")
                return self._solve_locally(problem)
            
            task_id = submission['task_id']
            logger.info(f"Task submitted successfully. Task ID: {task_id}")
            
            # Wait for and get solution
            solution = self.api_client.get_solution(task_id, wait=True)
            
            if solution['status'] == 'success':
                logger.info(f"Solution received from API for task {task_id}")
                
                # Validate solution if needed
                if config.DEBUG:
                    validation = self.api_client.validate_solution(
                        problem_id=problem_type,
                        solution_data=solution['solution']
                    )
                    
                    if validation.get('valid', False):
                        logger.info(f"Solution validated successfully (score: {validation.get('score', 0):.2f})")
                    else:
                        logger.warning(f"Solution validation failed: {validation.get('feedback', 'Unknown error')}")
                
                return {
                    'status': 'success',
                    'source': 'api',
                    'solver_used': solver_name,
                    'task_id': task_id,
                    'solution': solution['solution'],
                    'execution_time': solution.get('execution_time'),
                    'metadata': solution.get('metadata', {})
                }
            else:
                logger.error(f"API solution failed: {solution}")
                # Fallback to local solver
                return self._solve_locally(problem)
                
        except Exception as e:
            logger.error(f"API solving failed: {e}")
            # Fallback to local solver
            return self._solve_locally(problem)
    
    def _solve_locally(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Solve problem locally (fallback)"""
        logger.info("Using local solver (fallback)")
        
        try:
            # Select best solver
            solver, solver_name, confidence = self.select_best_solver(problem)
            
            logger.info(f"Solving locally with {solver_name} solver (confidence: {confidence:.2f})")
            
            # Measure execution time
            start_time = time.time()
            
            # Call solver's solve method
            if hasattr(solver, 'solve'):
                result = solver.solve(problem)
            elif hasattr(solver, 'solve_locally'):
                result = solver.solve_locally(problem)
            else:
                raise AttributeError(f"Solver {solver_name} has no solve method")
            
            execution_time = time.time() - start_time
            
            return {
                'status': 'success',
                'source': 'local',
                'solver_used': solver_name,
                'solver_confidence': confidence,
                'solution': result,
                'execution_time': execution_time,
                'metadata': {
                    'fallback': True,
                    'local_solution': True
                }
            }
            
        except Exception as e:
            logger.error(f"Local solving failed: {e}")
            return {
                'status': 'error',
                'source': 'local',
                'error': str(e),
                'metadata': {
                    'fallback_failed': True
                }
            }
    
    def batch_solve(self, problems: list, use_api: bool = True) -> Dict[str, Any]:
        """Solve multiple problems"""
        results = []
        successful = 0
        failed = 0
        
        logger.info(f"Starting batch solve for {len(problems)} problems")
        
        for i, problem in enumerate(problems, 1):
            logger.info(f"Processing problem {i}/{len(problems)}: {problem.get('problem_type', 'unknown')}")
            
            try:
                result = self.solve_with_api(problem, use_local=not use_api)
                
                if result['status'] == 'success':
                    successful += 1
                    results.append({
                        'problem_id': i,
                        'status': 'success',
                        'solver_used': result.get('solver_used'),
                        'execution_time': result.get('execution_time')
                    })
                else:
                    failed += 1
                    results.append({
                        'problem_id': i,
                        'status': 'error',
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                failed += 1
                results.append({
                    'problem_id': i,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'total': len(problems),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(problems) if problems else 0,
            'results': results
        }

# Factory function
def get_solver_adapter(solver_type: str = 'auto') -> SolverAPIAdapter:
    """Get solver adapter instance"""
    return SolverAPIAdapter(solver_type=solver_type)

# Default adapter
default_adapter = SolverAPIAdapter()
