"""
Optical Simulator for SpectraVortex.
Main simulation engine for photonic circuits with hybrid solver architecture support.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, Union, List
import logging

# Import the new hybrid architecture data interface
try:
    from .core.data_interface import FieldSolution, SimulationDomain
    HYBRID_ARCH_AVAILABLE = True
except ImportError:
    # Fallback for when hybrid architecture is not fully implemented yet
    HYBRID_ARCH_AVAILABLE = False
    logging.warning("Hybrid architecture modules not available, using fallback mode")

logger = logging.getLogger(__name__)


class OpticalSimulator:
    """
    Main simulator for photonic circuits with hybrid architecture support.
    
    Features:
    - Supports both legacy (complex array) and new (FieldSolution) output formats
    - Compatible with existing SpectraVortex infrastructure
    - Ready for integration with multiple solver types
    - Improved error handling and logging
    """
    
    # Class constants for configuration
    DEFAULT_GRID_SIZE = 0.1e-6  # 100 nm default grid
    DEFAULT_WAVELENGTH = 1.55e-6  # 1550 nm telecom wavelength
    DEFAULT_PROPAGATION_DISTANCE = 1e-3  # 1 mm default
    
    def __init__(self, 
                 grid_size: Optional[float] = None,
                 wavelength: Optional[float] = None,
                 use_hybrid_output: bool = True):
        """
        Initialize the optical simulator with hybrid architecture support.
        
        Args:
            grid_size: Discretization size in meters (default: 100nm)
            wavelength: Operating wavelength in meters (default: 1550nm)
            use_hybrid_output: If True, returns FieldSolution when possible
        """
        self.grid_size = grid_size or self.DEFAULT_GRID_SIZE
        self.wavelength = wavelength or self.DEFAULT_WAVELENGTH
        self.use_hybrid_output = use_hybrid_output and HYBRID_ARCH_AVAILABLE
        
        # State management
        self.grid = None
        self.field_history = []  # For tracking field evolution
        
        # Component registry for extensibility
        self._component_handlers = self._register_default_handlers()
        
        logger.info(f"OpticalSimulator initialized: λ={self.wavelength*1e9:.1f} nm, "
                   f"grid={self.grid_size*1e9:.1f} nm, "
                   f"hybrid_output={self.use_hybrid_output}")

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
    
    def create_grid(self, 
                   width: float, 
                   height: float = 0.0,
                   force_recreate: bool = False) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Create or reuse a simulation grid.
        
        Args:
            width: Grid width in meters
            height: Grid height in meters (0 for 1D simulation)
            force_recreate: If True, forces recreation even if grid exists
            
        Returns:
            Tuple of (x_grid, y_grid or None)
            
        Raises:
            ValueError: If width or height are invalid
        """
        if width <= 0:
            raise ValueError(f"Width must be positive, got {width}")
        if height < 0:
            raise ValueError(f"Height must be non-negative, got {height}")
        
        # Reuse existing grid if possible
        if not force_recreate and self.grid is not None:
            existing_width = self.grid[0][-1] - self.grid[0][0] if len(self.grid[0]) > 1 else self.grid[0][0]
            existing_height = 0 if self.grid[1] is None else (self.grid[1][-1] - self.grid[1][0])
            
            if (abs(existing_width - width) < 1e-12 and 
                abs(existing_height - height) < 1e-12):
                logger.debug(f"Reusing existing grid: {self.grid[0].shape} points")
                return self.grid
        
        # Create new grid
        nx = max(2, int(np.ceil(width / self.grid_size)))
        x_grid = np.linspace(0, width, nx)
        
        if height > 0:
            ny = max(2, int(np.ceil(height / self.grid_size)))
            y_grid = np.linspace(0, height, ny)
            self.grid = (x_grid, y_grid)
            logger.debug(f"Created 2D grid: {nx}x{ny} = {nx*ny:,} points")
            return x_grid, y_grid
        else:
            self.grid = (x_grid, None)
            logger.debug(f"Created 1D grid: {nx} points")
            return x_grid, None
    
    def simulate(self, 
                circuit_config: Dict[str, Any],
                return_format: str = 'auto') -> Union[np.ndarray, 'FieldSolution']:
        """
        Main simulation method with flexible output format.
        
        Args:
            circuit_config: Circuit configuration dictionary with:
                - width (float): Simulation width in meters
                - height (float, optional): Simulation height (0 for 1D)
                - components (list): List of optical components
                - initial_field (np.ndarray, optional): Initial field
                - propagation_distance (float, optional): Propagation distance
            return_format: One of:
                - 'auto': Choose based on use_hybrid_output setting
                - 'complex': Return complex numpy array (legacy)
                - 'fieldsolution': Return FieldSolution (hybrid)
                
        Returns:
            Complex field array or FieldSolution
            
        Raises:
            ValueError: For invalid configuration or return_format
        """
        # Validate return format
        valid_formats = ['auto', 'complex', 'fieldsolution']
        if return_format not in valid_formats:
            raise ValueError(f"return_format must be one of {valid_formats}, got '{return_format}'")
        
        # Determine actual return format
        if return_format == 'auto':
            actual_return_format = 'fieldsolution' if self.use_hybrid_output else 'complex'
        else:
            actual_return_format = return_format
        
        logger.info(f"Starting simulation (format: {actual_return_format})")
        
        # Extract and validate configuration
        width = circuit_config.get('width', 10e-6)
        height = circuit_config.get('height', 0.0)
        components = circuit_config.get('components', [])
        initial_field = circuit_config.get('initial_field')
        propagation_distance = circuit_config.get('propagation_distance', self.DEFAULT_PROPAGATION_DISTANCE)
        
        # Create grid
        self.create_grid(width, height)
        
        # Initialize field
        if initial_field is not None:
            field = self._validate_and_prepare_field(initial_field, width, height)
        else:
            field = self._create_default_field()
        
        # Store initial state
        self.field_history = [field.copy() if hasattr(field, 'copy') else field]
        
        # Process components
        for i, component in enumerate(components):
            logger.debug(f"Processing component {i+1}/{len(components)}: {component.get('type', 'unknown')}")
            try:
                field = self._apply_component(field, component)
                self.field_history.append(field.copy() if hasattr(field, 'copy') else field)
            except Exception as e:
                logger.error(f"Failed to apply component {i}: {e}")
                raise
        
        # Apply propagation if needed
        if propagation_distance > 0:
            logger.debug(f"Propagating field by {propagation_distance*1e6:.2f} μm")
            field = self._propagate_field(field, propagation_distance)
            self.field_history.append(field.copy() if hasattr(field, 'copy') else field)
        
        # Return in requested format
        if actual_return_format == 'fieldsolution' and HYBRID_ARCH_AVAILABLE:
            return self._create_field_solution(field, circuit_config)
        else:
            # Legacy complex array format
            logger.debug(f"Returning complex array (shape: {field.shape})")
            return field
    
    def simulate_wave_propagation(self, 
                                 initial_field: Optional[np.ndarray] = None,
                                 components: Optional[List[Dict[str, Any]]] = None,
                                 distance: float = 1e-3) -> Union[np.ndarray, 'FieldSolution']:
        """
        Legacy-compatible simulation method.
        
        Args:
            initial_field: Initial complex field
            components: List of optical components
            distance: Propagation distance in meters
            
        Returns:
            FieldSolution if use_hybrid_output=True, else complex array
        """
        circuit_config = {
            'width': 10e-6 if self.grid is None else (self.grid[0][-1] - self.grid[0][0]),
            'height': 0.0 if self.grid is None or self.grid[1] is None else (self.grid[1][-1] - self.grid[1][0]),
            'components': components or [],
            'initial_field': initial_field,
            'propagation_distance': distance
        }
        
        return self.simulate(circuit_config, return_format='auto')
    
    def _validate_and_prepare_field(self, 
                                   field: np.ndarray, 
                                   expected_width: float,
                                   expected_height: float = 0.0) -> np.ndarray:
        """
        Validate and prepare initial field.
        
        Args:
            field: Input field array
            expected_width: Expected width in meters
            expected_height: Expected height in meters
            
        Returns:
            Validated and prepared field array
        """
        if not isinstance(field, np.ndarray):
            field = np.array(field, dtype=complex)
        
        if not np.iscomplexobj(field):
            logger.warning(f"Initial field is not complex, converting")
            field = field.astype(complex)
        
        # Check dimensions
        expected_points_x = int(np.ceil(expected_width / self.grid_size))
        
        if expected_height > 0:
            expected_points_y = int(np.ceil(expected_height / self.grid_size))
            expected_shape = (expected_points_x, expected_points_y)
        else:
            expected_shape = (expected_points_x,)
        
        if field.shape != expected_shape:
            logger.warning(f"Field shape {field.shape} doesn't match expected {expected_shape}. "
                          f"Attempting interpolation...")
            # Simple nearest-neighbor interpolation for demonstration
            # In production, use proper interpolation
            if len(field.shape) == len(expected_shape):
                # Simple resize for same dimensionality
                from scipy.ndimage import zoom
                zoom_factors = [exp/act for exp, act in zip(expected_shape, field.shape)]
                field = zoom(field, zoom_factors, order=0)
        
        return field
    
    def _create_default_field(self) -> np.ndarray:
        """Create a default Gaussian field."""
        if self.grid is None:
            raise RuntimeError("Grid must be created before creating default field")
        
        x_grid, y_grid = self.grid
        
        if y_grid is None:  # 1D case
            x = x_grid
            center = np.mean(x)
            sigma = (x[-1] - x[0]) / 6  # Cover ~3 sigma
            return np.exp(-(x - center)**2 / (2 * sigma**2))
        else:  # 2D case
            X, Y = np.meshgrid(x_grid, y_grid, indexing='ij')
            center_x, center_y = np.mean(x_grid), np.mean(y_grid)
            sigma_x = (x_grid[-1] - x_grid[0]) / 6
            sigma_y = (y_grid[-1] - y_grid[0]) / 6
            return np.exp(-((X - center_x)**2/(2*sigma_x**2) + 
                           (Y - center_y)**2/(2*sigma_y**2)))
    
    def _apply_component(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Apply an optical component to the field using registered handlers."""
        comp_type = component.get('type', 'unknown')
        
        handler = self._component_handlers.get(comp_type)
        if handler:
            return handler(field, component)
        else:
            logger.warning(f"No handler for component type '{comp_type}', passing through")
            return field
    
    # Component handlers
    def _handle_phase_shifter(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Handle phase shifter component."""
        phase = component.get('phase', 0.0)
        return field * np.exp(1j * phase)
    
    def _handle_attenuator(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Handle attenuator component."""
        attenuation = component.get('attenuation', 1.0)
        if not 0 <= attenuation <= 1:
            logger.warning(f"Attenuation {attenuation} outside [0, 1], clamping")
            attenuation = np.clip(attenuation, 0, 1)
        return field * attenuation
    
    def _handle_waveguide(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Handle waveguide component."""
        length = component.get('length', 1e-4)
        refractive_index = component.get('refractive_index', 1.5)
        beta = 2 * np.pi * refractive_index / self.wavelength
        return field * np.exp(1j * beta * length)
    
    def _handle_beamsplitter(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Handle beamsplitter component (simplified 50/50)."""
        reflection = component.get('reflection', 0.5)
        transmission = np.sqrt(1 - reflection**2)
        return field * transmission  # Simplified - only transmission
    
    def _handle_mirror(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Handle mirror component."""
        reflection = component.get('reflection', 0.99)
        return field * reflection
    
    def _handle_lens(self, field: np.ndarray, component: Dict[str, Any]) -> np.ndarray:
        """Handle lens component (phase profile)."""
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
        """Propagate field using appropriate method based on dimensionality."""
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
        
        # Shift to center for propagation
        field_shifted = np.fft.ifftshift(field)
        spectrum = np.fft.fft(field_shifted)
        
        # Propagate
        kz = np.sqrt((2 * np.pi / self.wavelength)**2 - kx**2)
        # Handle evanescent waves
        kz = np.where(np.isreal(kz), kz, 0)
        
        propagated_spectrum = spectrum * np.exp(1j * kz * distance)
        
        # Shift back
        return np.fft.fftshift(np.fft.ifft(propagated_spectrum))
    
    def _propagate_2d(self, field: np.ndarray, distance: float) -> np.ndarray:
        """2D Fourier propagation (simplified for demonstration)."""
        nx, ny = field.shape
        dx = dy = self.grid_size
        
        kx = 2 * np.pi * np.fft.fftfreq(nx, d=dx)
        ky = 2 * np.pi * np.fft.fftfreq(ny, d=dy)
        
        KX, KY = np.meshgrid(kx, ky, indexing='ij')
        
        # Shift to center
        field_shifted = np.fft.ifftshift(field)
        spectrum = np.fft.fft2(field_shifted)
        
        # Propagate (angular spectrum method)
        kz = np.sqrt((2 * np.pi / self.wavelength)**2 - KX**2 - KY**2)
        # Handle evanescent waves
        kz = np.where(np.isreal(kz), kz, 0)
        
        propagated_spectrum = spectrum * np.exp(1j * kz * distance)
        
        # Shift back
        return np.fft.fftshift(np.fft.ifft2(propagated_spectrum))
    
    def _create_field_solution(self, 
                              field: np.ndarray, 
                              config: Dict[str, Any]) -> 'FieldSolution':
        """Create a FieldSolution from simulation results."""
        if not HYBRID_ARCH_AVAILABLE:
            raise RuntimeError("FieldSolution requires hybrid architecture modules")
        
        x_grid, y_grid = self.grid
        
        metadata = {
            'simulator_version': '2.0',
            'grid_size': self.grid_size,
            'wavelength': self.wavelength,
            'config_summary': {
                k: str(v) if not isinstance(v, (int, float, str, bool)) else v
                for k, v in config.items()
                if not k.startswith('_') and not callable(v)
            },
            'field_history_length': len(self.field_history),
            'timestamp': np.datetime64('now'),
        }
        
        return FieldSolution(
            amplitude=np.abs(field),
            phase=np.angle(field),
            spatial_dim=field.ndim,
            grid_x=x_grid,
            grid_y=y_grid,
            wavelength=self.wavelength,
            solver_used="OpticalSimulator_v2",
            metadata=metadata
        )
    
    def get_field_history(self) -> List[np.ndarray]:
        """Get the history of field evolution during simulation."""
        return self.field_history.copy()
    
    def reset(self):
        """Reset the simulator state."""
        self.grid = None
        self.field_history = []
        logger.debug("Simulator reset")
    
    def register_component_handler(self, 
                                  component_type: str, 
                                  handler: callable) -> None:
        """
        Register a custom component handler.
        
        Args:
            component_type: Type identifier for the component
            handler: Function that takes (field, component_config) and returns modified field
        """
        if not callable(handler):
            raise ValueError("Handler must be callable")
        
        self._component_handlers[component_type] = handler
        logger.debug(f"Registered handler for component type: {component_type}")
    
    # Legacy methods for backward compatibility
    def legacy_simulate(self, circuit_description: Dict[str, Any]) -> np.ndarray:
        """
        Legacy simulation method for backward compatibility.
        
        Args:
            circuit_description: Circuit description dictionary
            
        Returns:
            Complex field array
        """
        logger.warning("Using legacy_simulate() - consider switching to simulate()")
        return self.simulate(circuit_description, return_format='complex')


# Factory functions
def create_simulator(grid_size: Optional[float] = None,
                    wavelength: Optional[float] = None,
                    use_hybrid_output: bool = True) -> OpticalSimulator:
    """
    Factory function to create an OpticalSimulator.
    
    Args:
        grid_size: Discretization size in meters
        wavelength: Operating wavelength in meters
        use_hybrid_output: If True, enables FieldSolution output
        
    Returns:
        OpticalSimulator instance
    """
    return OpticalSimulator(
        grid_size=grid_size,
        wavelength=wavelength,
        use_hybrid_output=use_hybrid_output
    )


def simulate_circuit(circuit_description: Dict[str, Any],
                    grid_size: Optional[float] = None,
                    wavelength: Optional[float] = None,
                    return_complex: bool = False) -> Union[np.ndarray, 'FieldSolution']:
    """
    High-level function for circuit simulation.
    
    Args:
        circuit_description: Circuit description dictionary
        grid_size: Discretization size in meters
        wavelength: Operating wavelength in meters
        return_complex: If True, returns complex array instead of FieldSolution
        
    Returns:
        Simulation results in requested format
    """
    simulator = create_simulator(
        grid_size=grid_size,
        wavelength=wavelength,
        use_hybrid_output=not return_complex
    )
    
    return_format = 'complex' if return_complex else 'auto'
    return simulator.simulate(circuit_description, return_format=return_format)


# Quick test function
def test_simulator() -> None:
    """Quick test of the simulator functionality."""
    print("Testing OpticalSimulator...")
    
    try:
        # Create simulator
        sim = create_simulator(grid_size=0.2e-6, wavelength=1.55e-6)
        
        # Test configuration
        config = {
            'width': 5e-6,
            'components': [
                {'type': 'phase_shifter', 'phase': np.pi/4},
                {'type': 'attenuator', 'attenuation': 0.8}
            ],
            'propagation_distance': 1e-3
        }
        
        # Run simulation
        result = sim.simulate(config)
        
        print(f"✅ Simulation successful!")
        if hasattr(result, 'amplitude'):  # FieldSolution
            print(f"   Result type: FieldSolution")
            print(f"   Amplitude shape: {result.amplitude.shape}")
            print(f"   Solver used: {result.solver_used}")
        else:  # Complex array
            print(f"   Result type: complex array")
            print(f"   Shape: {result.shape}")
            print(f"   Dtype: {result.dtype}")
        
        print(f"   Field history: {len(sim.get_field_history())} steps")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run test if module is executed directly
    test_simulator()
