"""
Data Interface for Hybrid Solver Architecture.
Defines the common data structures exchanged between solvers.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
import numpy as np


@dataclass
class FieldSolution:
    """
    Universal container for the result of any photonic field solver.
    This is the common language that all solvers (linear, nonlinear, etc.)
    will use to exchange data.
    """
    # Core field data
    amplitude: np.ndarray          # Field amplitude (e.g., sqrt(intensity))
    phase: np.ndarray              # Field phase in radians
    spatial_dim: int               # 1 for 1D, 2 for 2D simulation
    
    # Spatial grid (critical for interpolation between solvers)
    grid_x: Optional[np.ndarray] = None   # X-coordinates
    grid_y: Optional[np.ndarray] = None   # Y-coordinates (for 2D)
    
    # Physical parameters
    wavelength: float = 1.55e-6     # Default: 1550 nm in meters
    intensity: Optional[np.ndarray] = None  # Optional cached intensity
    
    # Metadata for solver coordination
    solver_used: str = "unknown"    # Tag identifying which solver created this
    metadata: Dict[str, Any] = field(default_factory=dict) # Flexible dict for nonlinear flags, energy, etc.
    
    def __post_init__(self):
        """Ensure consistency after initialization."""
        # Auto-calculate intensity if not provided
        if self.intensity is None:
            self.intensity = self.amplitude ** 2
        
        # Validate grid dimensions
        if self.spatial_dim == 1:
            if self.grid_x is None:
                # Create a default grid if none provided
                self.grid_x = np.arange(self.amplitude.shape[0])
        elif self.spatial_dim == 2:
            if self.grid_x is None or self.grid_y is None:
                # Create default 2D grids
                shape = self.amplitude.shape
                self.grid_x = np.arange(shape[0])
                self.grid_y = np.arange(shape[1])
        else:
            raise ValueError(f"Unsupported spatial_dim: {self.spatial_dim}. Must be 1 or 2.")

    @property
    def complex_field(self) -> np.ndarray:
        """Return the complex field representation (amplitude * exp(i*phase))."""
        return self.amplitude * np.exp(1j * self.phase)

    @classmethod
    def from_complex_array(cls, 
                          complex_array: np.ndarray, 
                          wavelength: float = 1.55e-6,
                          grid_x: Optional[np.ndarray] = None,
                          grid_y: Optional[np.ndarray] = None,
                          solver_tag: str = "legacy"):
        """
        Create a FieldSolution from a complex field array.
        This is the primary migration path for existing code.
        
        Args:
            complex_array: Complex numpy array representing the field
            wavelength: Wavelength in meters
            grid_x: Optional x-grid coordinates
            grid_y: Optional y-grid coordinates (for 2D)
            solver_tag: Identifier for the solver that produced this
            
        Returns:
            FieldSolution instance
        """
        amplitude = np.abs(complex_array)
        phase = np.angle(complex_array)
        
        # Determine spatial dimension
        if complex_array.ndim == 1:
            spatial_dim = 1
        elif complex_array.ndim == 2:
            spatial_dim = 2
        else:
            raise ValueError(f"Array must be 1D or 2D, got {complex_array.ndim}D")
        
        return cls(
            amplitude=amplitude,
            phase=phase,
            spatial_dim=spatial_dim,
            grid_x=grid_x,
            grid_y=grid_y,
            wavelength=wavelength,
            solver_used=solver_tag,
            metadata={"origin": "complex_array_conversion"}
        )

    def get_boundary_values(self, boundary: str = 'right') -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract field values at a specific boundary.
        Essential for stitching solutions from different solvers.
        
        Args:
            boundary: 'left', 'right' (for 1D), or 'top', 'bottom' (for 2D)
            
        Returns:
            Tuple of (amplitude_slice, phase_slice) at the boundary
        """
        if self.spatial_dim == 1:
            if boundary == 'left':
                idx = 0
            elif boundary == 'right':
                idx = -1
            else:
                raise ValueError("For 1D, boundary must be 'left' or 'right'")
            return self.amplitude[idx:idx+1], self.phase[idx:idx+1]
        
        elif self.spatial_dim == 2:
            if boundary == 'left':
                slice_amp = self.amplitude[:, 0]
                slice_phase = self.phase[:, 0]
            elif boundary == 'right':
                slice_amp = self.amplitude[:, -1]
                slice_phase = self.phase[:, -1]
            elif boundary == 'top':
                slice_amp = self.amplitude[0, :]
                slice_phase = self.phase[0, :]
            elif boundary == 'bottom':
                slice_amp = self.amplitude[-1, :]
                slice_phase = self.phase[-1, :]
            else:
                raise ValueError("For 2D, boundary must be 'left', 'right', 'top', or 'bottom'")
            return slice_amp, slice_phase
        
        raise RuntimeError(f"Unsupported spatial_dim: {self.spatial_dim}")


@dataclass
class SimulationDomain:
    """
    Describes a region of the photonic circuit assigned to a specific solver.
    """
    domain_id: str
    solver_type: str                 # 'linear_wave', 'nonlinear_gpe', etc.
    bounds: Dict[str, float]         # Spatial boundaries: {'x_min': 0, 'x_max': 1, ...}
    parameters: Dict[str, Any]       # Physics parameters for this domain
    
    # Reference to neighboring domains for coordination
    neighbors: Dict[str, str] = field(default_factory=dict)  # Maps direction to neighbor domain_id
