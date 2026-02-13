"""
Abstract Solver Interface for Hybrid Architecture.
Defines the common interface for all physical solvers in SpectraVortex.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from .data_interface import FieldSolution


class Solver(ABC):
    """
    Abstract base class for all physical solvers in the hybrid architecture.
    
    This defines the common interface that all solvers (linear, nonlinear, quantum, etc.)
    must implement to work within the SpectraVortex simulation framework.
    """
    
    def __init__(self, name: str, version: str = "1.0"):
        """
        Initialize the solver with basic metadata.
        
        Args:
            name: Unique name identifier for this solver
            version: Solver version string
        """
        self.name = name
        self.version = version
        self.supported_models = []  # To be populated by subclasses
    
    @abstractmethod
    def solve(self, problem: Dict[str, Any]) -> FieldSolution:
        """
        Main solving method. Must be implemented by all concrete solvers.
        
        Args:
            problem: Problem description dictionary containing:
                - domain: Spatial domain specification
                - parameters: Physical parameters
                - initial_conditions: Initial field state
                - boundary_conditions: Boundary conditions
                - metadata: Additional solver-specific information
        
        Returns:
            FieldSolution containing the solved field
        """
        pass
    
    @abstractmethod
    def can_solve(self, problem: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if this solver can handle the given problem.
        
        Args:
            problem: Problem description dictionary
        
        Returns:
            Tuple of (can_solve: bool, reason: str)
            - can_solve: True if solver can handle this problem
            - reason: Explanation if cannot solve
        """
        pass
    
    @abstractmethod
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get requirements and capabilities of this solver.
        
        Returns:
            Dictionary with solver capabilities:
                - supported_domains: List of supported domain types
                - max_dimensions: Maximum spatial dimensions (1, 2, 3)
                - required_parameters: List of required parameter names
                - optional_parameters: List of optional parameter names
                - physical_models: List of supported physical models
                - performance_hint: Estimated performance characteristics
        """
        pass
    
    def validate_problem(self, problem: Dict[str, Any]) -> List[str]:
        """
        Validate a problem description against solver requirements.
        
        Args:
            problem: Problem description dictionary
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for required parameters
        requirements = self.get_requirements()
        required_params = requirements.get('required_parameters', [])
        
        for param in required_params:
            if param not in problem.get('parameters', {}):
                errors.append(f"Missing required parameter: {param}")
        
        # Check domain compatibility
        problem_domain = problem.get('domain', {})
        if not problem_domain:
            errors.append("No domain specification provided")
        
        # Check dimensionality
        max_dims = requirements.get('max_dimensions', 3)
        domain_type = problem_domain.get('type', 'unknown')
        
        if domain_type in ['1d', 'line'] and max_dims < 1:
            errors.append(f"Solver doesn't support 1D domains (max: {max_dims}D)")
        elif domain_type in ['2d', 'rectangle'] and max_dims < 2:
            errors.append(f"Solver doesn't support 2D domains (max: {max_dims}D)")
        
        return errors
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default parameters for this solver.
        
        Returns:
            Dictionary of default parameter values
        """
        return {
            'wavelength': 1.55e-6,  # 1550 nm
            'grid_size': 0.1e-6,    # 100 nm
            'time_step': 1e-15,     # 1 fs (for time-dependent solvers)
        }
    
    def prepare_initial_condition(self, 
                                 initial_field: Optional[np.ndarray] = None,
                                 domain: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Prepare initial condition for simulation.
        
        Args:
            initial_field: Optional initial field array
            domain: Domain specification for creating default field
        
        Returns:
            Prepared initial field array
        """
        if initial_field is not None:
            return initial_field
        
        # Create default Gaussian beam if no initial condition provided
        if domain is None:
            raise ValueError("Domain specification required when no initial field provided")
        
        domain_type = domain.get('type', '1d')
        
        if domain_type in ['1d', 'line']:
            length = domain.get('length', 10e-6)
            grid_size = domain.get('grid_size', 0.1e-6)
            n_points = int(length / grid_size)
            x = np.linspace(0, length, n_points)
            center = length / 2
            sigma = length / 6
            return np.exp(-(x - center)**2 / (2 * sigma**2))
        
        elif domain_type in ['2d', 'rectangle']:
            width = domain.get('width', 10e-6)
            height = domain.get('height', 10e-6)
            grid_size = domain.get('grid_size', 0.1e-6)
            
            nx = int(width / grid_size)
            ny = int(height / grid_size)
            
            x = np.linspace(0, width, nx)
            y = np.linspace(0, height, ny)
            X, Y = np.meshgrid(x, y, indexing='ij')
            
            center_x = width / 2
            center_y = height / 2
            sigma_x = width / 6
            sigma_y = height / 6
            
            return np.exp(-((X - center_x)**2/(2*sigma_x**2) + 
                           (Y - center_y)**2/(2*sigma_y**2)))
        
        else:
            raise ValueError(f"Unsupported domain type: {domain_type}")
    
    def estimate_computation_cost(self, problem: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate computation cost for the given problem.
        
        Args:
            problem: Problem description
        
        Returns:
            Dictionary with cost estimates:
                - memory_mb: Estimated memory usage in MB
                - time_seconds: Estimated computation time
                - complexity: Estimated complexity score
        """
        domain = problem.get('domain', {})
        
        if domain.get('type') in ['1d', 'line']:
            length = domain.get('length', 10e-6)
            grid_size = domain.get('grid_size', 0.1e-6)
            n_points = int(length / grid_size)
            memory_mb = n_points * 16 / (1024**2)  # Complex double: 16 bytes per point
            time_seconds = n_points * 1e-7  # Rough estimate
            
        elif domain.get('type') in ['2d', 'rectangle']:
            width = domain.get('width', 10e-6)
            height = domain.get('height', 10e-6)
            grid_size = domain.get('grid_size', 0.1e-6)
            
            nx = int(width / grid_size)
            ny = int(height / grid_size)
            n_points = nx * ny
            
            memory_mb = n_points * 16 / (1024**2)
            time_seconds = n_points * 1e-6  # 2D is more expensive
            
        else:
            # Conservative default
            memory_mb = 100.0
            time_seconds = 1.0
        
        return {
            'memory_mb': memory_mb,
            'time_seconds': time_seconds,
            'complexity': memory_mb * time_seconds,
            'points': n_points if 'n_points' in locals() else 0
        }
    
    def __str__(self) -> str:
        """String representation of the solver."""
        return f"{self.name} v{self.version}"
    
    def __repr__(self) -> str:
        """Detailed representation of the solver."""
        reqs = self.get_requirements()
        models = ', '.join(reqs.get('physical_models', ['Unknown']))
        return f"{self.name} (models: {models}, max_dim: {reqs.get('max_dimensions', '?')}D)"
