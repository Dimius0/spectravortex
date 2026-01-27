"""
Star Coupler model for OAM generation.
Based on: 'Photonic integrated chip enabling orbital angular momentum multiplexing...'
"""

import numpy as np
from typing import Dict, Any, Tuple
import logging
from .base import OpticalComponent  # Предполагается базовый класс

logger = logging.getLogger(__name__)

class StarCoupler(OpticalComponent):
    """
    A star coupler that converts a Gaussian input into a ring-shaped output
    with azimuthally varying phase to generate OAM modes.
    
    Parameters from the article (Zahidy et al.):
        - ports: 26 output waveguides (default)
        - radius: sector radius (~10-20 um)
        - topological_charge: OAM order (l)
    """
    
    def __init__(self, 
                 name: str = "star_coupler",
                 parameters: Dict[str, Any] = None):
        super().__init__(name)
        
        # Default parameters (from article and general practice)
        self.default_params = {
            'ports': 26,
            'radius': 15e-6,  # 15 micrometers
            'topological_charge': 1,  # OAM l=+1
            'wavelength': 1.55e-6,
            'input_waveguide_width': 0.5e-6,
            'output_waveguide_width': 0.5e-6,
            'material': 'silicon'
        }
        
        # Merge with user parameters
        self.params = {**self.default_params, **(parameters or {})}
        
        # Calculate derived parameters
        self._calculate_geometry()
        
        logger.info(f"Initialized StarCoupler '{name}' with OAM l={self.params['topological_charge']}")
    
    def _calculate_geometry(self):
        """Calculate port positions and phase shifts."""
        n_ports = self.params['ports']
        radius = self.params['radius']
        l = self.params['topological_charge']
        
        # Angular positions of output ports (in radians)
        self.port_angles = np.linspace(0, 2*np.pi, n_ports, endpoint=False)
        
        # Phase shift for each port: φ = l * θ
        self.port_phases = l * self.port_angles
        
        # Cartesian coordinates for output ports
        self.port_positions = radius * np.array([
            np.cos(self.port_angles),
            np.sin(self.port_angles)
        ]).T
        
        logger.debug(f"StarCoupler geometry: {n_ports} ports at radius {radius*1e6:.1f} um")
    
    def propagate_field(self, input_field: np.ndarray, 
                       grid_info: Dict[str, Any]) -> np.ndarray:
        """
        Simulate the field transformation through the star coupler.
        
        Args:
            input_field: Complex field at input waveguide
            grid_info: Simulation grid parameters
            
        Returns:
            Output field after star coupler transformation
        """
        # In a real implementation, this would use FDTD or BPM simulation
        # For now, create a mock OAM-like field
        
        x = grid_info.get('x', np.array([0]))
        y = grid_info.get('y', np.array([0]))
        
        if len(x) > 1 and len(y) > 1:
            # Create 2D meshgrid
            X, Y = np.meshgrid(x, y)
            
            # Convert to polar coordinates
            R = np.sqrt(X**2 + Y**2)
            Theta = np.arctan2(Y, X)
            
            # Generate OAM-like field: donut intensity + spiral phase
            # Characteristic radius based on star coupler radius
            r0 = self.params['radius'] * 0.7
            
            # Intensity profile (donut shape)
            intensity = np.exp(-(R - r0)**2 / (0.3*r0)**2)
            
            # Phase profile (spiral)
            l = self.params['topological_charge']
            phase = l * Theta
            
            # Combine into complex field
            output_field = intensity * np.exp(1j * phase)
            
            return output_field
        else:
            # 1D case - return simple transformation
            logger.warning("1D grid provided, OAM generation requires 2D+ simulation")
            return input_field * 1.0  # Pass-through
    
    def get_s_matrix(self, frequency: float) -> np.ndarray:
        """
        Get scattering matrix for frequency-domain analysis.
        
        For star coupler: S-matrix describes coupling from input to multiple outputs
        with specific phase relationships.
        """
        n_ports = self.params['ports']
        l = self.params['topological_charge']
        
        # S-matrix size: (n_ports + 1) x (n_ports + 1) [1 input + n_ports outputs]
        s_matrix = np.zeros((n_ports + 1, n_ports + 1), dtype=complex)
        
        # Input port (index 0) couples to all output ports
        # with equal amplitude and phase φ = l * θ_k
        for k in range(n_ports):
            amplitude = 1.0 / np.sqrt(n_ports)  # Equal power splitting
            phase = self.port_phases[k]
            s_matrix[k+1, 0] = amplitude * np.exp(1j * phase)
            s_matrix[0, k+1] = amplitude * np.exp(-1j * phase)  # Reciprocity
        
        return s_matrix
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return all component parameters."""
        return self.params.copy()
    
    def validate_design(self) -> Tuple[bool, str]:
        """Validate component parameters."""
        if self.params['ports'] < 4:
            return False, f"Too few ports ({self.params['ports']}), need at least 4"
        
        if self.params['radius'] <= 0:
            return False, f"Invalid radius ({self.params['radius']})"
        
        # Check if radius is reasonable for the number of ports
        min_waveguide_spacing = 1.0e-6  # 1 um minimum spacing
        circumference = 2 * np.pi * self.params['radius']
        port_spacing = circumference / self.params['ports']
        
        if port_spacing < min_waveguide_spacing:
            return False, f"Ports too crowded: {port_spacing*1e6:.1f} nm spacing"
        
        return True, "Design valid"
