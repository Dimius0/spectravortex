"""
Optical field and photon state simulation for SpectraVortex.
"""

import math
from dataclasses import dataclass
from typing import Tuple
from enum import Enum

class Polarization(str, Enum):
    """Polarization types."""
    LINEAR = "linear"
    CIRCULAR = "circular"
    ELLIPTICAL = "elliptical"

@dataclass
class PhotonState:
    """Represents the quantum state of a photon."""
    frequency: float  # in Hz
    amplitude: float  # normalized to [0, 1]
    phase: float      # in radians, normalized to [0, 2π)
    oam: int          # orbital angular momentum (topological charge)
    polarization: Polarization
    
    def __post_init__(self):
        """Validate photon state parameters."""
        if self.amplitude < 0 or self.amplitude > 1:
            raise ValueError(f"Amplitude must be between 0 and 1, got {self.amplitude}")
        # Нормализуем фазу при создании объекта
        self.phase = self.phase % (2 * math.pi)

class OpticalField:
    """Represents an optical field with spatial properties."""
    
    def __init__(self, state: PhotonState, position: Tuple[float, float] = (0.0, 0.0)):
        self.state = state
        self.position = position
        self.amplitude = state.amplitude
    
    @property
    def wavelength(self) -> float:
        """Calculate wavelength from frequency."""
        # Speed of light in vacuum (m/s)
        c = 299792458.0
        return c / self.state.frequency
    
    @property
    def intensity(self) -> float:
        """Calculate field intensity (proportional to amplitude squared)."""
        return self.amplitude ** 2
    
    def propagate(self, distance: float, refractive_index: float = 1.0) -> "OpticalField":
        """Propagate the field through a medium."""
        # Phase accumulation due to propagation
        k = 2 * math.pi * refractive_index / self.wavelength
        phase_accumulation = k * distance
        
        # Нормализуем новую фазу
        new_phase = (self.state.phase + phase_accumulation) % (2 * math.pi)
        
        new_state = PhotonState(
            frequency=self.state.frequency,
            amplitude=self.amplitude,
            phase=new_phase,
            oam=self.state.oam,
            polarization=self.state.polarization
        )
        
        return OpticalField(new_state, self.position)
    
    def interfere(self, other: "OpticalField") -> "OpticalField":
        """Interfere two optical fields."""
        if self.wavelength != other.wavelength:
            raise ValueError("Can only interfere fields of same wavelength")
        
        # Phase difference
        phase_diff = self.state.phase - other.state.phase
        
        # Resultant phase using phasor addition
        # arctan2(ΣA sin φ, ΣA cos φ)
        sin_sum = (self.amplitude * math.sin(self.state.phase) + 
                  other.amplitude * math.sin(other.state.phase))
        cos_sum = (self.amplitude * math.cos(self.state.phase) + 
                  other.amplitude * math.cos(other.state.phase))
        
        new_phase = math.atan2(sin_sum, cos_sum)
        # Нормализуем фазу
        new_phase = new_phase % (2 * math.pi)
        
        # Resultant amplitude
        new_amplitude = math.sqrt(
            self.amplitude**2 + other.amplitude**2 + 
            2 * self.amplitude * other.amplitude * math.cos(phase_diff)
        )
        
        # ВАЖНО: Нормализуем амплитуду, чтобы не превышала 1.0
        if new_amplitude > 1.0:
            new_amplitude = 1.0
        
        new_state = PhotonState(
            frequency=self.state.frequency,
            amplitude=new_amplitude,
            phase=new_phase,
            oam=self.state.oam,
            polarization=self.state.polarization
        )
        
        return OpticalField(new_state, self.position)
    
    def split(self, ratio: float = 0.5) -> Tuple["OpticalField", "OpticalField"]:
        """Split field into two parts with given intensity ratio."""
        if ratio <= 0 or ratio >= 1:
            raise ValueError(f"Split ratio must be between 0 and 1, got {ratio}")
        
        # Amplitudes after split
        amp1 = self.amplitude * math.sqrt(ratio)
        amp2 = self.amplitude * math.sqrt(1 - ratio)
        
        # Проверяем, что амплитуды не превышают 1.0
        if amp1 > 1.0:
            amp1 = 1.0
        if amp2 > 1.0:
            amp2 = 1.0
        
        # Same phase for both outputs
        field1 = OpticalField(
            PhotonState(
                frequency=self.state.frequency,
                amplitude=amp1,
                phase=self.state.phase,
                oam=self.state.oam,
                polarization=self.state.polarization
            ),
            self.position
        )
        
        field2 = OpticalField(
            PhotonState(
                frequency=self.state.frequency,
                amplitude=amp2,
                phase=self.state.phase,
                oam=self.state.oam,
                polarization=self.state.polarization
            ),
            self.position
        )
        
        return field1, field2
    
    def __add__(self, other: "OpticalField") -> "OpticalField":
        """Overload + operator for interference."""
        return self.interfere(other)
    
    def __str__(self) -> str:
        return (f"OpticalField(λ={self.wavelength*1e9:.1f}nm, "
                f"A={self.amplitude:.3f}, φ={self.state.phase:.3f}rad, "
                f"OAM={self.state.oam})")


# Test functions
def test_field() -> None:
    """Test basic optical field operations."""
    print("Testing OpticalField...")
    
    # Create test fields
    state1 = PhotonState(
        frequency=193.414e12,  # 1550 nm
        amplitude=0.8,
        phase=0.0,
        oam=0,
        polarization=Polarization.LINEAR
    )
    
    state2 = PhotonState(
        frequency=193.414e12,
        amplitude=0.6,
        phase=math.pi,  # 180° phase shift
        oam=0,
        polarization=Polarization.LINEAR
    )
    
    field1 = OpticalField(state1)
    field2 = OpticalField(state2)
    
    print(f"Field 1 intensity: {field1.intensity:.3f}")
    print(f"Field 2 intensity: {field2.intensity:.3f}")
    
    # Test interference
    interfered = field1.interfere(field2)
    print(f"Interfered intensity: {interfered.intensity:.3f}")
    
    # Test propagation
    propagated = field1.propagate(1e-3)  # 1 mm propagation
    print(f"After propagation, phase: {propagated.state.phase:.3f}")
    
    # Test split
    part1, part2 = field1.split(0.3)
    print(f"Split: {part1.amplitude:.3f}, {part2.amplitude:.3f}")


if __name__ == "__main__":
    test_field()
