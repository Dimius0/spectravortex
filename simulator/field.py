"""
Optical field simulation for SpectraVortex
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class Polarization(Enum):
    LINEAR = "linear"
    CIRCULAR_RIGHT = "circular_right"
    CIRCULAR_LEFT = "circular_left"

@dataclass
class PhotonState:
    """State of a single photon"""
    frequency: float           # Hz
    amplitude: float           # normalized [0, 1]
    phase: float               # radians [0, 2π)
    oam_charge: int            # orbital angular momentum charge
    polarization: Polarization
    duration: float            # seconds
    
    def __post_init__(self):
        """Validate parameters"""
        if not 0 <= self.amplitude <= 1:
            raise ValueError(f"Amplitude must be between 0 and 1, got {self.amplitude}")
        if not 0 <= self.phase < 2 * np.pi:
            raise ValueError(f"Phase must be between 0 and 2π, got {self.phase}")
    
    def to_complex(self) -> complex:
        """Convert to complex amplitude"""
        return self.amplitude * np.exp(1j * self.phase)
    
    def wavelength(self) -> float:
        """Calculate wavelength in meters"""
        c = 299792458  # speed of light in m/s
        return c / self.frequency

class OpticalField:
    """Optical field (superposition of photon states)"""
    
    def __init__(self, states: Optional[List[PhotonState]] = None):
        self.states = states if states is not None else []
        self.grid_size = 256  # for spatial simulations
        
    def add_state(self, state: PhotonState):
        """Add a photon state to the field"""
        self.states.append(state)
    
    def interfere(self, other: 'OpticalField') -> 'OpticalField':
        """Interfere two optical fields"""
        result_states = []
        
        for s1 in self.states:
            for s2 in other.states:
                # Check if photons can interfere (similar frequency and polarization)
                freq_match = np.isclose(s1.frequency, s2.frequency, rtol=1e-6)
                pol_match = s1.polarization == s2.polarization
                
                if freq_match and pol_match:
                    # Coherent interference
                    a1 = s1.to_complex()
                    a2 = s2.to_complex()
                    a_total = a1 + a2
                    
                    new_state = PhotonState(
                        frequency=s1.frequency,
                        amplitude=np.abs(a_total),
                        phase=np.angle(a_total),
                        oam_charge=s1.oam_charge + s2.oam_charge,
                        polarization=s1.polarization,
                        duration=min(s1.duration, s2.duration)
                    )
                    result_states.append(new_state)
        
        return OpticalField(result_states)
    
    def propagate(self, distance: float, refractive_index: float = 1.0) -> 'OpticalField':
        """Propagate field through a medium"""
        c = 299792458  # speed of light
        
        result_states = []
        for state in self.states:
            # Phase shift due to propagation
            k = 2 * np.pi * state.frequency * refractive_index / c
            phase_shift = k * distance
            
            new_state = PhotonState(
                frequency=state.frequency,
                amplitude=state.amplitude,
                phase=(state.phase + phase_shift) % (2 * np.pi),
                oam_charge=state.oam_charge,
                polarization=state.polarization,
                duration=state.duration
            )
            result_states.append(new_state)
        
        return OpticalField(result_states)
    
    def total_intensity(self) -> float:
        """Calculate total intensity of the field"""
        return sum(state.amplitude ** 2 for state in self.states)
    
    def oam_spectrum(self) -> dict:
        """Get OAM charge spectrum"""
        spectrum = {}
        for state in self.states:
            if state.oam_charge in spectrum:
                spectrum[state.oam_charge] += state.amplitude ** 2
            else:
                spectrum[state.oam_charge] = state.amplitude ** 2
        return spectrum
    
    def __str__(self):
        return f"OpticalField with {len(self.states)} photon states"

def test_field():
    """Test function for optical field"""
    print("Testing OpticalField...")
    
    # Create two photon states
    photon1 = PhotonState(
        frequency=193.414e12,  # 1550 nm
        amplitude=0.8,
        phase=0.0,
        oam_charge=0,
        polarization=Polarization.LINEAR,
        duration=100e-12
    )
    
    photon2 = PhotonState(
        frequency=193.414e12,
        amplitude=0.6,
        phase=np.pi,  # 180 degrees out of phase
        oam_charge=0,
        polarization=Polarization.LINEAR,
        duration=100e-12
    )
    
    # Create fields
    field1 = OpticalField([photon1])
    field2 = OpticalField([photon2])
    
    print(f"Field 1 intensity: {field1.total_intensity():.3f}")
    print(f"Field 2 intensity: {field2.total_intensity():.3f}")
    
    # Interfere them
    interfered = field1.interfere(field2)
    print(f"Interfered intensity: {interfered.total_intensity():.3f}")
    
    # Propagate
    propagated = field1.propagate(0.01)  # 1 cm
    print(f"After propagation, phase: {propagated.states[0].phase:.3f}")
    
    return field1, field2, interfered

if __name__ == "__main__":
    test_field()
