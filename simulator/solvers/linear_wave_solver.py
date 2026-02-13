"""
Linear Wave Solver implementation.
Converts the existing OpticalSimulator to the new Solver interface.
"""

import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import logging

from ..core.solver import Solver
from ..core.data_interface import FieldSolution

logger = logging.getLogger(__name__)


class LinearWaveSolver(Solver):
    """
    Linear wave optics solver based on the existing OpticalSimulator.
    
    Solves linear wave equations for photonic circuits using Fourier methods.
    """
    
    def __init__(self, 
                 grid_size: float = 0.1e-6,
                 wavelength: float = 1.55e-6):
        """
        Initialize the linear wave solver.
        
        Args:
            grid_size: Discretization size in meters
            wavelength: Operating wavelength in meters
        """
        super().__init__(name="LinearWaveSolver", version="2.0")
        
        self.grid_size = grid_size
        self.wavelength = wavelength
        self.grid = None
        self.field_history = []
        
        # Initialize component handlers (from OpticalSimulator)
        self._component_handlers = self._register_default_handlers()
        
        logger.info(f"LinearWaveSolver initialized: λ={wavelength*1e9:.1f} nm")
    
    def _register_default_handlers(self) -> Dict[str, callable]:
        """Register default component handlers."""
        return {
            'phase_shifter': self._handle_phase_shifter,
            'attenuator': self._handle_attenuator,
            'waveguide': self._handle_waveguide,
            'beamsplitter': self._handle_beamsplitter,
            'mirror': self._handle_mirror,
            'lens': self._handle_lens,
        }
    
    def solve(self, problem: Dict[str, Any]) -> FieldSolution:
        """
        Solve linear wave propagation problem.
        
        Args:
            problem: Problem description with:
                - domain: Spatial domain specification
                - parameters: Physical parameters
                - components: List of optical components
                - initial_conditions: Initial field (optional)
                - boundary_conditions: Boundary conditions (optional)
        
        Returns:
            FieldSolution with simulation results
        """
        logger.info(f"LinearWaveSolver solving problem: {problem.get('name', 'unnamed')}")
        
        # Extract problem components
        domain = problem.get('domain', {})
        parameters = problem.get('parameters', {})
        components = problem.get('components', [])
        initial_conditions = problem.get('initial_conditions', {})
        # boundary_conditions intentionally not used in this basic implementation
        # but kept in signature for future expansion
        
        # Create grid from domain specification
        self._create_grid_from_domain(domain)
        
        # Prepare initial field
        initial_field = initial_conditions.get('field')
        field = self.prepare_initial_condition(initial_field, domain)
        
        # Store initial state
        self.field_history = [field.copy() if hasattr(field, 'copy') else field]
        
        # Apply components
        for i, component in enumerate(components):
            logger.debug(f"Applying component {i+1}/{len(components)}: {component.get('type', 'unknown')}")
            field = self._apply_component(field, component)
            self.field_history.append(field.copy() if hasattr(field, 'copy') else field)
        
        # Apply propagation if specified
        propagation_distance = parameters.get('propagation_distance', 1e-3)
        if propagation_distance > 0:
            field = self._propagate_field(field, propagation_distance)
            self.field_history.append(field.copy() if hasattr(field, 'copy') else field)
        
        # Create FieldSolution
        return self._create_field_solution(field, problem)
    
    def can_solve(self, problem: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if this solver can handle the problem.
        
        LinearWaveSolver can handle:
        - 1D and 2D domains
        - Linear optical components
        - No nonlinear effects
        - No time dependence
        """
        # Check domain type
        domain = problem.get('domain', {})
        domain_type = domain.get('type', 'unknown')
        
        if domain_type not in ['1d', '2d', 'line', 'rectangle']:
            return False, f"Unsupported domain type: {domain_type}"
        
        # Check for nonlinear parameters
        parameters = problem.get('parameters', {})
        if parameters.get('nonlinear_coefficient', 0) > 0:
            return False, "Nonlinear effects not supported by LinearWaveSolver"
        
        # Check for time dependence
        if parameters.get('time_dependent', False):
            return False, "Time-dependent problems not supported by LinearWaveSolver"
        
        # Check component compatibility
        components = problem.get('components', [])
        for comp in components:
            comp_type = comp.get('type', '')
            if comp_type not in self._component_handlers:
                return False, f"Unsupported component type: {comp_type}"
        
        return True, "Problem compatible with LinearWaveSolver"
    
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get solver requirements and capabilities.
        """
        return {
            'supported_domains': ['1d', '2d', 'line', 'rectangle'],
            'max_dimensions': 2,
            'required_parameters': [],
            'optional_parameters': [
                'wavelength',
                'grid_size', 
                'propagation_distance',
                'refractive_index'
            ],
            'physical_models': [
                'linear_wave_optics',
                'fourier_optics',
                'gaussian_beam_propagation'
            ],
            'performance_hint': 'fast_for_linear_problems',
            'limitations': [
                'no_nonlinear_effects',
                'no_time_dependence',
                'max_2d_simulation'
            ]
        }
    
    def _create_grid_from_domain(self, domain: Dict[str, Any]) -> None:
        """Create simulation grid from domain specification."""
        domain_type = domain.get('type', '1d')
        
        if domain_type in ['1d', 'line']:
            length = domain.get('length', 10e-6)
            grid_size = domain.get('grid_size', self.grid_size)
            nx = max(2, int(np.ceil(length / grid_size)))
            x_grid = np.linspace(0, length, nx)
            self.grid = (x_grid, None)
            
        elif domain_type in ['2d', 'rectangle']:
            width = domain.get('width', 10e-6)
            height = domain.get('height', 10e-6)
            grid_size = domain.get('grid_size', self.grid_size)
            
            nx = max(2, int(np.ceil(width / grid_size)))
            ny = max(2, int(np.ceil(height / grid_size)))
            
            x_grid = np.linspace(0, width, nx)
            y_grid = np.linspace(0, height, ny)
            self.grid = (x_grid, y_grid)
            
        else:
            raise ValueError(f"Unsupported domain type: {domain_type}")
    
    def _apply_component(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Apply an optical component to the field."""
        comp_type = component.get('type', 'unknown')
        handler = self._component_handlers.get(comp_type)
        
        if handler:
            return handler(field, component)
        else:
            logger.warning(f"No handler for component type '{comp_type}', passing through")
            return field
    
    # Component handlers (from OpticalSimulator)
    def _handle_phase_shifter(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        phase = component.get('phase', 0.0)
        return field * np.exp(1j * phase)
    
    def _handle_attenuator(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        attenuation = component.get('attenuation', 1.0)
        if not 0 <= attenuation <= 1:
            logger.warning(f"Attenuation {attenuation} outside [0, 1], clamping")
            attenuation = np.clip(attenuation, 0, 1)
        return field * attenuation
    
    def _handle_waveguide(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        length = component.get('length', 1e-4)
        refractive_index = component.get('refractive_index', 1.5)
        beta = 2 * np.pi * refractive_index / self.wavelength
        return field * np.exp(1j * beta * length)
    
    def _handle_beamsplitter(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        reflection = component.get('reflection', 0.5)
        transmission = np.sqrt(1 - reflection**2)
        return field * transmission
    
    def _handle_mirror(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        reflection = component.get('reflection', 0.99)
        return field * reflection
    
    def _handle_lens(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        focal_length = component.get('focal_length', 1e-2)
        if self.grid[1] is None:  # 1D lens
            x = self.grid[0]
            center = np.mean(x)
            phase_profile = -np.pi * (x - center)**2 / (self.wavelength * focal_length)
        else:  # 2D lens
            x, y = self.grid
            X, Y = np.meshgrid(x, y, indexing='ij')
            center_x, center_y = np.mean(x), np.mean(y)
            phase_profile = -np.pi * ((X - center_x)**2 + (Y - center_y)**2) / (self.wavelength * focal_length)
        return field * np.exp(1j * phase_profile)
    
    def _propagate_field(self, field: np.ndarray, distance: float) -> np.ndarray:
        """Propagate field using Fourier methods."""
        if distance <= 0:
            return field
        
        if field.ndim == 1:
            return self._propagate_1d(field, distance)
        elif field.ndim == 2:
            return self._propagate_2d(field, distance)
        else:
            raise ValueError(f"Unsupported field dimensionality: {field.ndim}")
    
    def _propagate_1d(self, field: np.ndarray, distance: float) -> np.ndarray:
        """1D Fourier propagation."""
        nx = len(field)
        dx = self.grid_size
        kx = 2 * np.pi * np.fft.fftfreq(nx, d=dx)
        
        field_shifted = np.fft.ifftshift(field)
        spectrum = np.fft.fft(field_shifted)
        
        kz = np.sqrt((2 * np.pi / self.wavelength)**2 - kx**2)
        kz = np.where(np.isreal(kz), kz, 0)
        
        propagated_spectrum = spectrum * np.exp(1j * kz * distance)
        return np.fft.fftshift(np.fft.ifft(propagated_spectrum))
    
    def _propagate_2d(self, field: np.ndarray, distance: float) -> np.ndarray:
        """2D Fourier propagation."""
        nx, ny = field.shape
        dx = dy = self.grid_size
        
        kx = 2 * np.pi * np.fft.fftfreq(nx, d=dx)
        ky = 2 * np.pi * np.fft.fftfreq(ny, d=dy)
        KX, KY = np.meshgrid(kx, ky, indexing='ij')
        
        field_shifted = np.fft.ifftshift(field)
        spectrum = np.fft.fft2(field_shifted)
        
        kz = np.sqrt((2 * np.pi / self.wavelength)**2 - KX**2 - KY**2)
        kz = np.where(np.isreal(kz), kz, 0)
        
        propagated_spectrum = spectrum * np.exp(1j * kz * distance)
        return np.fft.fftshift(np.fft.ifft2(propagated_spectrum))
    
    def _create_field_solution(self, field: np.ndarray, problem: Dict[str, Any]) -> FieldSolution:
        """Create FieldSolution from simulation results."""
        x_grid, y_grid = self.grid
        
        metadata = {
            'solver': self.name,
            'solver_version': self.version,
            'problem_name': problem.get('name', 'unnamed'),
            'grid_size': self.grid_size,
            'wavelength': self.wavelength,
            'field_history_length': len(self.field_history),
            'parameters': problem.get('parameters', {}),
        }
        
        return FieldSolution(
            amplitude=np.abs(field),
            phase=np.angle(field),
            spatial_dim=field.ndim,
            grid_x=x_grid,
            grid_y=y_grid,
            wavelength=self.wavelength,
            solver_used=self.name,
            metadata=metadata
        )
    
    def get_field_history(self) -> List[np.ndarray]:
        """Get history of field evolution."""
        return self.field_history.copy()


# Factory function for backward compatibility
def create_linear_wave_solver(**kwargs) -> LinearWaveSolver:
    """Factory function to create LinearWaveSolver instances."""
    return LinearWaveSolver(**kwargs)
