"""
Optical elements simulation for SpectraVortex.
"""

import math
from typing import Tuple, List
from .field import OpticalField, PhotonState, Polarization


class OpticalElement:
    """Base class for all optical elements."""
    
    def __init__(self, name: str):
        self.name = name
    
    def process(self, field: OpticalField) -> OpticalField:
        """Process an optical field through this element."""
        raise NotImplementedError("Subclasses must implement process()")
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


class Lens(OpticalElement):
    """Thin lens element."""
    
    def __init__(self, name: str, focal_length: float):
        super().__init__(name)
        self.focal_length = focal_length
    
    def process(self, field: OpticalField) -> OpticalField:
        """Apply lens phase transformation."""
        # Simplified thin lens formula
        # Phase change = -π*r²/(λ*f)
        x, y = field.position
        r_squared = x**2 + y**2
        
        phase_change = -math.pi * r_squared / (field.wavelength * self.focal_length)
        
        # Нормализуем новую фазу
        new_phase = (field.state.phase + phase_change) % (2 * math.pi)
        
        new_state = PhotonState(
            frequency=field.state.frequency,
            amplitude=field.amplitude,
            phase=new_phase,
            oam=field.state.oam,
            polarization=field.state.polarization
        )
        
        return OpticalField(new_state, field.position)


class BeamSplitter(OpticalElement):
    """Beam splitter element."""
    
    def __init__(self, name: str, transmission: float = 0.5):
        super().__init__(name)
        if not 0 <= transmission <= 1:
            raise ValueError(f"Transmission must be between 0 and 1, got {transmission}")
        self.transmission = transmission
    
    def process(self, field: OpticalField) -> Tuple[OpticalField, OpticalField]:
        """Split input field into transmitted and reflected outputs."""
        # Transmitted amplitude
        amp_t = field.amplitude * math.sqrt(self.transmission)
        
        # Reflected amplitude (with π/2 phase shift for lossless beam splitter)
        amp_r = field.amplitude * math.sqrt(1 - self.transmission)
        
        # Transmitted field (same phase)
        transmitted_state = PhotonState(
            frequency=field.state.frequency,
            amplitude=amp_t,
            phase=field.state.phase,
            oam=field.state.oam,
            polarization=field.state.polarization
        )
        transmitted_field = OpticalField(transmitted_state, field.position)
        
        # Reflected field (π/2 phase shift)
        reflected_phase = (field.state.phase + math.pi/2) % (2 * math.pi)
        reflected_state = PhotonState(
            frequency=field.state.frequency,
            amplitude=amp_r,
            phase=reflected_phase,
            oam=field.state.oam,
            polarization=field.state.polarization
        )
        reflected_field = OpticalField(reflected_state, field.position)
        
        return transmitted_field, reflected_field
    
    def split(self, field: OpticalField) -> Tuple[OpticalField, OpticalField]:
        """Alias for process()."""
        return self.process(field)


class PhaseShifter(OpticalElement):
    """Optical phase shifter."""
    
    def __init__(self, name: str, phase_shift: float):
        super().__init__(name)
        self.phase_shift = phase_shift
    
    def process(self, field: OpticalField) -> OpticalField:
        """Apply phase shift to field."""
        new_phase = (field.state.phase + self.phase_shift) % (2 * math.pi)
        
        new_state = PhotonState(
            frequency=field.state.frequency,
            amplitude=field.amplitude,
            phase=new_phase,
            oam=field.state.oam,
            polarization=field.state.polarization
        )
        
        return OpticalField(new_state, field.position)


class Mirror(OpticalElement):
    """Perfect mirror."""
    
    def __init__(self, name: str):
        super().__init__(name)
    
    def process(self, field: OpticalField) -> OpticalField:
        """Reflect field (π phase shift)."""
        new_phase = (field.state.phase + math.pi) % (2 * math.pi)
        
        new_state = PhotonState(
            frequency=field.state.frequency,
            amplitude=field.amplitude,
            phase=new_phase,
            oam=field.state.oam,
            polarization=field.state.polarization
        )
        
        return OpticalField(new_state, field.position)


class MachZehnderInterferometer(OpticalElement):
    """Mach-Zehnder interferometer."""
    
    def __init__(self, name: str, arm_length_diff: float = 0.0):
        super().__init__(name)
        self.arm_length_diff = arm_length_diff
        self.bs1 = BeamSplitter("BS1", 0.5)
        self.bs2 = BeamSplitter("BS2", 0.5)
        self.phase_shifter = PhaseShifter("PS", 0.0)
    
    def process(self, field: OpticalField) -> Tuple[OpticalField, OpticalField]:
        """Process field through MZI."""
        # First beam splitter
        arm1, arm2 = self.bs1.split(field)
        
        # Arm 2 phase shift (due to path difference)
        phase_shift = 2 * math.pi * self.arm_length_diff / field.wavelength
        self.phase_shifter.phase_shift = phase_shift
        shifted_arm2 = self.phase_shifter.process(arm2)
        
        # Recombine at second beam splitter
        output1, output2 = self.bs2.split(arm1.interfere(shifted_arm2))
        
        return output1, output2


# Test functions
def test_elements() -> None:
    """Test optical elements."""
    print("Testing Optical Elements...")
    
    # Create test photon
    test_photon = PhotonState(
        frequency=193.414e12,  # 1550 nm
        amplitude=1.0,
        phase=0.0,
        oam=0,
        polarization=Polarization.LINEAR
    )
    
    test_field = OpticalField(test_photon)
    
    # Test lens
    lens = Lens("TestLens", focal_length=0.1)
    lens_output = lens.process(test_field)
    print(f"Lens applied. Original phase: {test_field.state.phase:.3f}, "
          f"After lens: {lens_output.state.phase:.3f}")
    
    # Test beam splitter
    bs = BeamSplitter("TestBS", transmission=0.5)
    transmitted, reflected = bs.split(test_field)
    print(f"Beamsplitter: Transmitted intensity: {transmitted.intensity:.3f}, "
          f"Reflected: {reflected.intensity:.3f}")
    
    # Test phase shifter
    ps = PhaseShifter("TestPS", phase_shift=math.pi/4)
    ps_output = ps.process(test_field)
    print(f"Phase shifter: Phase shift: {ps_output.state.phase - test_field.state.phase:.3f}")
    
    # Test mirror
    mirror = Mirror("TestMirror")
    mirror_output = mirror.process(test_field)
    print(f"Mirror: Phase shifted by π: {mirror_output.state.phase:.3f}")
    
    # Test MZI
    mzi = MachZehnderInterferometer("TestMZI", arm_length_diff=1e-6)
    mzi_output1, mzi_output2 = mzi.process(test_field)
    print(f"MZI: Output intensities: {mzi_output1.intensity:.3f}, {mzi_output2.intensity:.3f}")


if __name__ == "__main__":
    test_elements()
