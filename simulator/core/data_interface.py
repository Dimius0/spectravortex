"""
Data Interface for Hybrid Solver Architecture.
Defines the common data structures exchanged between solvers.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
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
    wavelength: float = 1.55e-6     # Default: 1550 nm
    intensity: Optional[np.ndarray] = None  # Optional cached intensity
    
    # Metadata for solver coordination
    solver_used: str = "unknown"    # Tag identifying which solver created this
    metadata: Dict[str, Any] = None # Flexible dict for nonlinear flags, energy, etc.
    
    def __post_init__(self):
        """Ensure consistency after initialization."""
        if self.metadata is None:
            self.metadata = {}
        
        # Auto-calculate intensity if not provided
        if self.intensity is None:
            self.intensity = self.amplitude ** 2
        
        # Validate grid dimensions
        if self.spatial_dim == 1 and self.grid_x is None:
            raise ValueError("1D simulation requires grid_x")
        elif self.spatial_dim == 2:
            if self.grid_x is None or self.grid_y is None:
                raise ValueError("2D simulation requires both grid_x and grid_y")

    @classmethod
    def from_legacy_array(cls, array: np.ndarray, wavelength: float = 1.55e-6):
        """
        Helper to create a FieldSolution from existing simulation output.
        This allows gradual migration without breaking current code.
        """
        # Assuming array represents complex field: amplitude * exp(i*phase)
        amplitude = np.abs(array)
        phase = np.angle(array)
        
        # Create a simple grid if none exists
        grid = np.arange(array.shape[0])
        
        return cls(
            amplitude=amplitude,
            phase=phase,
            spatial_dim=1,
            grid_x=grid,
            wavelength=wavelength,
            solver_used="legacy_linear",
            metadata={"origin": "legacy_conversion"}
        )

    def get_boundary_values(self, boundary: str = 'right'):
        """
        Extract field values at a specific boundary.
        Essential for stitching solutions from different solvers.
        
        Args:
            boundary: 'left', 'right', 'top', 'bottom'
        
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
            return self.amplitude[idx], self.phase[idx]
        
        # Placeholder for 2D boundary extraction
        raise NotImplementedError("2D boundary extraction coming in next phase")


@dataclass
class SimulationDomain:
    """
    Describes a region of the photonic circuit assigned to a specific solver.
    """
    domain_id: str
    solver_type: str              # 'linear_wave', 'nonlinear_gpe', etc.
    bounds: Dict[str, float]      # Spatial boundaries
    parameters: Dict[str, Any]    # Physics parameters for this domain
    
    # Reference to neighboring domains for coordination
    neighbors: Dict[str, 'SimulationDomain'] = None
