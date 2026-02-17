"""
Local/Mock API Client for SpectraVortex
Useful for development when real API is not available
"""

import json
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from config import config

logger = logging.getLogger(__name__)

class LocalAPIClient:
    """Local/Mock API client for development"""
    
    def __init__(self):
        """Initialize local client"""
        self.base_url = config.BASE_URL
        self.timeout = config.TIMEOUT
        self._tasks = {}  # Store mock tasks
        self._solutions = {}  # Store mock solutions
        
        logger.info(f"Local API Client initialized (mock mode)")
        logger.info("Note: Using mock responses for development")
    
    def health_check(self) -> bool:
        """Always returns True in local mode"""
        logger.debug("Local health check: always healthy")
        return True
    
    def solve_problem(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock problem submission"""
        problem_type = problem_data.get('problem_type', 'unknown')
        grid_size = problem_data.get('grid_size', [10, 10])
        
        logger.info(f"Local: Submitting problem '{problem_type}' with grid {grid_size}")
        
        # Generate mock task ID
        task_id = f"local_task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Store mock task
        self._tasks[task_id] = {
            'problem': problem_data,
            'status': 'processing',
            'submitted_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        # Generate mock solution (simulate background processing)
        self._generate_mock_solution(task_id, problem_data)
        
        return {
            'status': 'submitted',
            'task_id': task_id,
            'message': 'Problem accepted (local mock)',
            'estimated_time': random.uniform(1.0, 5.0)
        }
    
    def _generate_mock_solution(self, task_id: str, problem_data: Dict[str, Any]):
        """Generate mock solution in background"""
        import threading
        
        def generate():
            time.sleep(0.5)  # Simulate processing time
            
            problem_type = problem_data.get('problem_type', 'quantum_grid')
            grid_size = problem_data.get('grid_size', [10, 10])
            
            # Update task progress
            self._tasks[task_id]['progress'] = 50
            time.sleep(0.5)
            self._tasks[task_id]['progress'] = 100
            self._tasks[task_id]['status'] = 'completed'
            
            # Generate mock solution based on problem type
            if problem_type == 'quantum_grid':
                solution = self._generate_quantum_grid_solution(grid_size)
            elif problem_type == 'spectral_analysis':
                solution = self._generate_spectral_solution(grid_size)
            else:
                solution = self._generate_generic_solution(grid_size)
            
            # Store solution
            self._solutions[task_id] = {
                'solution': solution,
                'execution_time': random.uniform(0.5, 3.0),
                'iterations': random.randint(10, 1000),
                'converged': random.choice([True, True, True, False]),  # Mostly True
                'error': random.uniform(0.0001, 0.1)
            }
            
            logger.debug(f"Local: Generated mock solution for task {task_id}")
        
        # Start generation in background thread
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def _generate_quantum_grid_solution(self, grid_size):
        """Generate mock quantum grid solution"""
        rows, cols = grid_size if isinstance(grid_size, (list, tuple)) else (grid_size, grid_size)
        
        # Generate a simple quantum state matrix
        solution = []
        for i in range(min(rows, 100)):  # Limit size for display
            row = []
            for j in range(min(cols, 100)):
                # Generate complex number (real + imaginary)
                real = random.uniform(-1, 1)
                imag = random.uniform(-1, 1)
                row.append([real, imag])
            solution.append(row)
        
        return {
            'type': 'quantum_state_matrix',
            'data': solution,
            'normalized': True,
            'eigenvalues': [random.uniform(0.5, 2.0) for _ in range(min(rows, cols, 10))]
        }
    
    def _generate_spectral_solution(self, grid_size):
        """Generate mock spectral analysis solution"""
        points = grid_size[0] if isinstance(grid_size, (list, tuple)) else grid_size
        
        return {
            'type': 'spectral_analysis',
            'frequencies': [random.uniform(0, 100) for _ in range(points)],
            'amplitudes': [random.uniform(0, 1) for _ in range(points)],
            'dominant_frequency': random.uniform(0, 50),
            'signal_to_noise': random.uniform(5, 50)
        }
    
    def _generate_generic_solution(self, grid_size):
        """Generate generic solution"""
        return {
            'type': 'generic_solution',
            'result': 'success',
            'grid_size': grid_size,
            'optimized_value': random.uniform(0.5, 0.99),
            'parameters': {
                'alpha': random.uniform(0.1, 0.9),
                'beta': random.uniform(0.1, 0.9),
                'gamma': random.uniform(0.1, 0.9)
            }
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get mock task status"""
        if task_id not in self._tasks:
            return {
                'status': 'error',
                'task_id': task_id,
                'error': 'Task not found'
            }
        
        task = self._tasks[task_id]
        
        return {
            'status': 'success',
            'task_id': task_id,
            'task_status': task['status'],
            'progress': task['progress'],
            'submitted_at': task['submitted_at'],
            'estimated_time_left': random.uniform(0, 2.0) if task['status'] == 'processing' else 0
        }
    
    def get_solution(self, task_id: str, wait: bool = False, poll_interval: int = 1) -> Dict[str, Any]:
        """Get mock solution"""
        if wait:
            # Wait for solution to be ready
            for _ in range(10):  # Max 10 attempts
                status = self.get_task_status(task_id)
                if status.get('task_status') == 'completed':
                    break
                elif status.get('task_status') == 'failed':
                    return {
                        'status': 'error',
                        'task_id': task_id,
                        'error': 'Task failed (mock)'
                    }
                time.sleep(poll_interval)
        
        if task_id not in self._solutions:
            return {
                'status': 'error',
                'task_id': task_id,
                'error': 'Solution not ready yet'
            }
        
        solution_data = self._solutions[task_id]
        
        return {
            'status': 'success',
            'task_id': task_id,
            'solution': solution_data['solution'],
            'execution_time': solution_data['execution_time'],
            'metadata': {
                'iterations': solution_data.get('iterations', 0),
                'converged': solution_data.get('converged', True),
                'final_error': solution_data.get('error', 0.001),
                'source': 'local_mock'
            }
        }
    
    def validate_solution(self, problem_id: str, solution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock validation"""
        logger.debug(f"Local: Validating solution for problem {problem_id}")
        
        # Simple mock validation
        is_valid = random.random() > 0.1  # 90% valid
        
        return {
            'status': 'success',
            'valid': is_valid,
            'score': random.uniform(0.7, 0.99) if is_valid else random.uniform(0.1, 0.6),
            'feedback': 'Solution validated locally (mock)' if is_valid else 'Solution failed local validation (mock)',
            'details': {
                'validation_method': 'local_mock',
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def list_problems(self, problem_type: Optional[str] = None) -> Dict[str, Any]:
        """List mock problems"""
        mock_problems = [
            {'id': 'prob_001', 'type': 'quantum_grid', 'name': 'Quantum Grid 10x10', 'difficulty': 'easy'},
            {'id': 'prob_002', 'type': 'quantum_grid', 'name': 'Quantum Grid 50x50', 'difficulty': 'medium'},
            {'id': 'prob_003', 'type': 'spectral_analysis', 'name': 'Spectral Analysis 100pts', 'difficulty': 'medium'},
            {'id': 'prob_004', 'type': 'optimization', 'name': 'Function Optimization', 'difficulty': 'hard'},
            {'id': 'prob_005', 'type': 'quantum_grid', 'name': 'Quantum Grid 100x100', 'difficulty': 'hard'},
        ]
        
        if problem_type:
            filtered = [p for p in mock_problems if p['type'] == problem_type]
        else:
            filtered = mock_problems
        
        return {
            'status': 'success',
            'problems': filtered,
            'count': len(filtered)
        }

# Create default local client
local_client = LocalAPIClient()

def get_local_client() -> LocalAPIClient:
    """Get local API client instance"""
    return local_client

# Auto-select client based on configuration
def get_auto_client() -> Any:
    """
    Get appropriate client based on configuration
    
    Returns:
        LocalAPIClient if DEBUG=True, else SpectraVortexAPIClient
    """
    if config.DEBUG:
        logger.info("DEBUG mode enabled, using local/mock client")
        return local_client
    else:
        try:
            from api_client import get_api_client
            return get_api_client()
        except ImportError:
            logger.warning("api_client not available, falling back to local client")
            return local_client
