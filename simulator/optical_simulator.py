"""
Optical Simulator for SpectraVortex.
Main simulation engine for photonic circuits.
Now updated with hybrid solver architecture data interface.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
import logging

from .core.data_interface import FieldSolution, SimulationDomain

logger = logging.getLogger(__name__)


class OpticalSimulator:
    """
    Main simulator for photonic circuits.
    """
    
    def __init__(self, grid_size: float = 0.1, wavelength: float = 1.55e-6):
        """
        Initialize the optical simulator.
        
        Args:
            grid_size: Discretization size in meters
            wavelength: Operating wavelength in meters
        """
        self.grid_size = grid_size
        self.wavelength = wavelength
        self.grid = None
        self.field = None
        
        logger.info(f"OpticalSimulator initialized with λ={wavelength*1e9:.1f} nm, grid={grid_size}")
    
    def create_grid(self, width: float, height: float = 0.0) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Create a simulation grid.
        
        Args:
            width: Grid width in meters
            height: Grid height in meters (0 for 1D simulation)
            
        Returns:
            Tuple of (x_grid, y_grid or None)
        """
        nx = int(width / self.grid_size)
        x_grid = np.linspace(0, width, nx)
        
        if height > 0:
            ny = int(height / self.grid_size)
            y_grid = np.linspace(0, height, ny)
            self.grid = (x_grid, y_grid)
            logger.debug(f"Created 2D grid: {nx}x{ny} points")
            return x_grid, y_grid
        else:
            self.grid = (x_grid, None)
            logger.debug(f"Created 1D grid: {nx} points")
            return x_grid, None
    
    def simulate_wave_propagation(self, 
                                  initial_field: Optional[np.ndarray] = None,
                                  components: list = None,
                                  distance: float = 1e-3) -> FieldSolution:
        """
        Simulate wave propagation through optical components.
        
        Args:
            initial_field: Initial complex field (if None, creates Gaussian beam)
            components: List of optical components to simulate
            distance: Propagation distance in meters
            
        Returns:
            FieldSolution containing the simulation results
        """
        # Default components if none provided
        if components is None:
            components = []
        
        # Create or use initial field
        if initial_field is None:
            field = self._create_gaussian_beam()
        else:
            field = initial_field
        
        # Simulate each component
        for i, component in enumerate(components):
            logger.debug(f"Simulating component {i}: {component.get('type', 'unknown')}")
            field = self._apply_component(field, component)
        
        # Apply propagation if distance > 0
        if distance > 0:
            field = self._propagate(field, distance)
        
        # Convert to FieldSolution
        x_grid, y_grid = self.grid if self.grid else (None, None)
        
        if field.ndim == 1:
            spatial_dim = 1
            grid_y = None
        else:
            spatial_dim = 2
            grid_y = y_grid
        
        solution = FieldSolution(
            amplitude=np.abs(field),
            phase=np.angle(field),
            spatial_dim=spatial_dim,
            grid_x=x_grid,
            grid_y=grid_y,
            wavelength=self.wavelength,
            solver_used="optical_simulator_v1",
            metadata={
                "propagation_distance": distance,
                "num_components": len(components),
                "grid_size": self.grid_size
            }
        )
        
        logger.info(f"Simulation completed. Field shape: {field.shape}")
        return solution
    
    def _create_gaussian_beam(self, width: float = 2e-6) -> np.ndarray:
        """Create a Gaussian beam initial condition."""
        if self.grid[1] is None:  # 1D case
            x = self.grid[0]
            center = x[len(x)//2]
            field = np.exp(-((x - center)**2) / (2 * (width**2)))
        else:  # 2D case
            x, y = self.grid
            X, Y = np.meshgrid(x, y, indexing='ij')
            center_x = x[len(x)//2]
            center_y = y[len(y)//2]
            field = np.exp(-((X - center_x)**2 + (Y - center_y)**2) / (2 * (width**2)))
        
        return field
    
    def _apply_component(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Apply an optical component to the field."""
        comp_type = component.get('type', 'phase_shifter')
        
        if comp_type == 'phase_shifter':
            phase = component.get('phase', 0.0)
            return field * np.exp(1j * phase)
        
        elif comp_type == 'attenuator':
            attenuation = component.get('attenuation', 0.5)
            return field * attenuation
        
        elif comp_type == 'waveguide':
            # Simple waveguide model
            length = component.get('length', 1e-4)
            beta = 2 * np.pi / self.wavelength  # Propagation constant
            return field * np.exp(1j * beta * length)
        
        else:
            logger.warning(f"Unknown component type: {comp_type}. Passing through unchanged.")
            return field
    
    def _propagate(self, field: np.ndarray, distance: float) -> np.ndarray:
        """Simple propagation using Fourier optics (for demonstration)."""
        # For a real implementation, this would use proper beam propagation methods
        logger.debug(f"Propagating field by {distance*1e6:.2f} μm")
        
        if field.ndim == 1:
            # 1D Fourier propagation
            nx = len(field)
            kx = 2 * np.pi * np.fft.fftfreq(nx, d=self.grid_size)
            spectrum = np.fft.fft(field)
            propagated_spectrum = spectrum * np.exp(1j * kx * distance)
            return np.fft.ifft(propagated_spectrum)
        else:
            # 2D case - simplified
            return field * np.exp(1j * 2 * np.pi / self.wavelength * distance)
    
    def legacy_simulate(self, circuit_description: Dict[str, Any]) -> np.ndarray:
        """
        Legacy simulation method for backward compatibility.
        Converts result to FieldSolution internally but returns complex array.
        
        Args:
            circuit_description: Circuit description dictionary
            
        Returns:
            Complex field array (for backward compatibility)
        """
        # Extract parameters
        distance = circuit_description.get('distance', 1e-3)
        components = circuit_description.get('components', [])
        
        # Run simulation using new method
        solution = self.simulate_wave_propagation(
            initial_field=None,
            components=components,
            distance=distance
        )
        
        # Return complex array for backward compatibility
        return solution.complex_field


# Factory function for backward compatibility
def create_simulator(grid_size: float = 0.1, wavelength: float = 1.55e-6) -> OpticalSimulator:
    """
    Factory function to create an OpticalSimulator.
    Maintains backward compatibility with existing code.
    """
    return OpticalSimulator(grid_size=grid_size, wavelength=wavelength)


# Legacy function for direct access
def simulate_circuit(circuit_description: Dict[str, Any], 
                    grid_size: float = 0.1,
                    wavelength: float = 1.55e-6) -> np.ndarray:
    """
    Legacy one-function interface for circuit simulation.
    
    Args:
        circuit_description: Dictionary describing the circuit
        grid_size: Discretization size
        wavelength: Operating wavelength
        
    Returns:
        Complex field array
    """
    simulator = OpticalSimulator(grid_size=grid_size, wavelength=wavelength)
    width = circuit_description.get('width', 10e-6)
    height = circuit_description.get('height', 0.0)
    
    simulator.create_grid(width, height)
    return simulator.legacy_simulate(circuit_description)
