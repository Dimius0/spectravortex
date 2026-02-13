"""
Photonic Component Library
Basic building blocks for chip design
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import math


@dataclass
class PhotonicComponent:
    """Base class for all photonic components."""
    name: str = "unnamed"
    layer: str = "default"
    
    def get_info(self) -> str:
        """Return basic component information."""
        return f"{self.__class__.__name__}: {self.name}"
    
    def calculate_loss(self) -> float:
        """Default loss calculation (override in child classes)."""
        return 0.0


@dataclass
class Waveguide(PhotonicComponent):
    """Optical waveguide - basic building block"""
    # ВАЖНО: length теперь имеет значение по умолчанию
    length: float = 100.0  # in micrometers (добавлено значение по умолчанию)
    width: float = 0.5     # standard 500nm
    radius: float = 0.0    # bend radius (0 = straight)
    
    def __post_init__(self):
        """Initialize after dataclass creation"""
        self.layer = "waveguide"
        if self.name == "unnamed":
            self.name = f"waveguide_{self.length}um"
    
    def calculate_loss(self) -> float:
        """Calculate total waveguide loss"""
        # Simplified model: 2 dB/cm
        return (self.length / 10000.0) * 2.0
    
    def get_path(self) -> str:
        """Get description of waveguide path"""
        if self.radius > 0:
            return f"Bent waveguide: length={self.length}μm, radius={self.radius}μm"
        else:
            return f"Straight waveguide: length={self.length}μm"


@dataclass  
class MZIInterferometer(PhotonicComponent):
    """Mach-Zehnder Interferometer - basic matrix operation unit"""
    coupling_ratio: float = 0.5  # 50/50 coupler
    phase_shift: float = 0.0     # phase difference in radians
    
    def __post_init__(self):
        """Initialize after dataclass creation"""
        self.layer = "mzi"
        if self.name == "unnamed":
            self.name = f"mzi_{self.phase_shift:.2f}rad"
    
    def get_transfer_matrix(self) -> np.ndarray:
        """Calculate 2x2 transfer matrix"""
        k = np.sqrt(self.coupling_ratio)
        t = np.sqrt(1 - self.coupling_ratio)
        
        # Directional coupler matrix
        coupler = np.array([[t, 1j*k], [1j*k, t]])
        
        # Phase shifter matrix
        phase = np.array([[np.exp(1j*self.phase_shift), 0], 
                          [0, 1]])
        
        # Full MZI matrix: coupler * phase * coupler
        return coupler @ phase @ coupler
    
    def set_for_matrix(self, matrix_2x2: np.ndarray) -> None:
        """Configure MZI to implement given 2x2 unitary matrix"""
        # Simplified: just extract phase from first element
        self.phase_shift = np.angle(matrix_2x2[0, 0])
        print(f"MZI configured with phase shift: {self.phase_shift:.3f} rad")


@dataclass
class OAMModeConverter(PhotonicComponent):
    """OAM mode converter (metasurface/hologram)"""
    target_oam: int = 1      # OAM charge
    efficiency: float = 0.85 # conversion efficiency
    diameter: float = 20.0   # in micrometers
    
    def __post_init__(self):
        """Initialize after dataclass creation"""
        self.layer = "oam_converter"
        if self.name == "unnamed":
            self.name = f"oam_l{self.target_oam}"
    
    def generate_phase_pattern(self) -> np.ndarray:
        """Generate spiral phase plate pattern"""
        # Simple demonstration pattern
        size = 100
        pattern = np.zeros((size, size))
        
        center = size // 2
        for i in range(size):
            for j in range(size):
                dx = i - center
                dy = j - center
                angle = np.arctan2(dy, dx)
                pattern[i, j] = self.target_oam * angle
        
        return pattern
    
    def get_info(self) -> str:
        """Get converter information"""
        return f"OAM Converter: charge={self.target_oam}, efficiency={self.efficiency:.1%}"


# Utility functions
def connect(comp1: Any, port1: str, comp2: Any, port2: str) -> Waveguide:
    """Create waveguide connection between two components"""
    print(f"Connecting {comp1} [{port1}] -> {comp2} [{port2}]")
    return Waveguide(length=100.0, width=0.5)


def calculate_total_loss(components: List[Any]) -> float:
    """Calculate total loss in circuit"""
    total = 0.0
    for comp in components:
        if hasattr(comp, 'calculate_loss'):
            total += comp.calculate_loss()
    return total


print("✅ Photonic Component Library v0.1 loaded")