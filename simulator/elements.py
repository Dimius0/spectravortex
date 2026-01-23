"""
Optical elements for SpectraVortex simulator
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from .field import OpticalField, PhotonState, Polarization

@dataclass
class Lens:
    """Optical lens element"""
    focal_length: float  # meters
    diameter: float      # meters
    material: str = "SiO2"
    
    def apply(self, field: OpticalField) -> OpticalField:
        """Apply lens to optical field (simplified - phase shift)"""
        result_states = []
        
        for state in field.states:
            # Simple thin lens approximation: φ = -πr²/(λf)
            # For now, just add a constant phase shift
            wavelength = state.wavelength()
            phase_shift = -np.pi / (wavelength * self.focal_length)  # simplified
            
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

@dataclass
class Beamsplitter:
    """Beam splitter element"""
    ratio: float          # transmission ratio [0, 1]
    phase_shift: float = 0.0  # phase shift on reflection
    
    def split(self, field: OpticalField) -> Tuple[OpticalField, OpticalField]:
        """Split beam into transmitted and reflected parts"""
        transmitted_states = []
        reflected_states = []
        
        for state in field.states:
            # Transmitted beam
            trans_state = PhotonState(
                frequency=state.frequency,
                amplitude=state.amplitude * np.sqrt(self.ratio),
                phase=state.phase,
                oam_charge=state.oam_charge,
                polarization=state.polarization,
                duration=state.duration
            )
            transmitted_states.append(trans_state)
            
            # Reflected beam
            refl_state = PhotonState(
                frequency=state.frequency,
                amplitude=state.amplitude * np.sqrt(1 - self.ratio),
                phase=(state.phase + self.phase_shift + np.pi) % (2 * np.pi),  # π phase shift on reflection
                oam_charge=state.oam_charge,
                polarization=state.polarization,
                duration=state.duration
            )
            reflected_states.append(refl_state)
        
        return OpticalField(transmitted_states), OpticalField(reflected_states)

@dataclass
class MachZehnderInterferometer:
    """Mach-Zehnder interferometer"""
    arm_length_difference: float = 0.0  # meters
    coupling_ratio: float = 0.5         # beam splitter ratio
    
    def process(self, input_field: OpticalField) -> OpticalField:
        """Process field through MZI"""
        # First beamsplitter
        bs1 = Beamsplitter(ratio=self.coupling_ratio)
        arm1, arm2 = bs1.split(input_field)
        
        # Arm length difference (phase shift)
        c = 299792458  # speed of light
        if arm1.states:
            freq = arm1.states[0].frequency
            phase_shift = 2 * np.pi * freq * self.arm_length_difference / c
            
            # Apply phase shift to arm2
            shifted_arm2_states = []
            for state in arm2.states:
                new_state = PhotonState(
                    frequency=state.frequency,
                    amplitude=state.amplitude,
                    phase=(state.phase + phase_shift) % (2 * np.pi),
                    oam_charge=state.oam_charge,
                    polarization=state.polarization,
                    duration=state.duration
                )
                shifted_arm2_states.append(new_state)
            
            shifted_arm2 = OpticalField(shifted_arm2_states)
        else:
            shifted_arm2 = arm2
        
        # Second beamsplitter and interference
        bs2 = Beamsplitter(ratio=0.5)
        output1, output2 = bs2.split(arm1.interfere(shifted_arm2))
        
        # Return output1 (could be either output)
        return output1

@dataclass
class OAMGenerator:
    """OAM (Orbital Angular Momentum) mode generator"""
    target_charge: int      # desired OAM charge
    efficiency: float = 0.8  # conversion efficiency
    
    def apply(self, field: OpticalField) -> OpticalField:
        """Convert field to specific OAM mode"""
        result_states = []
        
        for state in field.states:
            new_state = PhotonState(
                frequency=state.frequency,
                amplitude=state.amplitude * self.efficiency,
                phase=state.phase,
                oam_charge=self.target_charge,
                polarization=state.polarization,
                duration=state.duration
            )
            result_states.append(new_state)
        
        return OpticalField(result_states)

@dataclass
class Detector:
    """Optical detector"""
    quantum_efficiency: float = 0.9  # detector efficiency
    noise_level: float = 0.01        # relative noise level
    
    def measure(self, field: OpticalField) -> float:
        """Measure field intensity"""
        total_intensity = field.total_intensity()
        
        # Add detector noise
        noise = np.random.normal(0, self.noise_level * total_intensity)
        measured = total_intensity * self.quantum_efficiency + noise
        
        return max(measured, 0)  # intensity can't be negative

def test_elements():
    """Test optical elements"""
    print("Testing Optical Elements...")
    
    # Create test photon
    test_photon = PhotonState(
        frequency=193.414e12,
        amplitude=1.0,
        phase=0.0,
        oam_charge=0,
        polarization=Polarization.LINEAR,
        duration=100e-12
    )
    
    field = OpticalField([test_photon])
    
    # Test lens
    lens = Lens(focal_length=0.1, diameter=0.01)
    focused = lens.apply(field)
    print(f"Lens applied. Original phase: {field.states[0].phase:.3f}, "
          f"After lens: {focused.states[0].phase:.3f}")
    
    # Test beamsplitter
    bs = Beamsplitter(ratio=0.5)
    trans, refl = bs.split(field)
    print(f"Beamsplitter: Transmitted intensity: {trans.total_intensity():.3f}, "
          f"Reflected: {refl.total_intensity():.3f}")
    
    # Test MZI
    mzi = MachZehnderInterferometer(arm_length_difference=0.001)  # 1 mm difference
    mzi_output = mzi.process(field)
    print(f"MZI output intensity: {mzi_output.total_intensity():.3f}")
    
    # Test OAM generator
    oam_gen = OAMGenerator(target_charge=+2)
    oam_field = oam_gen.apply(field)
    print(f"OAM generated. Charge: {oam_field.states[0].oam_charge}")
    
    # Test detector
    detector = Detector()
    measurement = detector.measure(field)
    print(f"Detector measurement: {measurement:.3f}")
    
    return {
        'lens': focused,
        'beamsplitter': (trans, refl),
        'mzi': mzi_output,
        'oam': oam_field,
        'measurement': measurement
    }

if __name__ == "__main__":
    test_elements()
