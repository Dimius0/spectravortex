# simulator/oam_physics.py
"""
Physical models for OAM (Orbital Angular Momentum) light
"""

import math
from typing import List, Dict, Tuple, Optional, Any

class OAMPhysics:
    """Physical models for vortex light and OAM operations"""
    
    @staticmethod
    def laguerre_gaussian_intensity(
        r: float, 
        phi: float, 
        oam_charge: int,  # Changed from 'l' to 'oam_charge'
        p: int = 0,  # Radial order
        w0: float = 1.0,  # Waist
        wavelength: float = 1550e-9
    ) -> float:
        """
        Calculate LG beam intensity at point (r, phi)
        
        Args:
            r: Radial coordinate
            phi: Azimuthal angle
            oam_charge: OAM charge (topological charge)
            p: Radial order
            w0: Beam waist
            wavelength: Wavelength in meters
            
        Returns:
            intensity: Normalized intensity
        """
        # Rayleigh range (commented out since not used, or use it)
        # z_r = math.pi * w0**2 / wavelength
        
        # Simplified LG mode (at beam waist z=0)
        if oam_charge == 0 and p == 0:
            # Gaussian beam
            return math.exp(-2 * r**2 / w0**2)
        
        # For OAM beams, include azimuthal phase
        r_norm = math.sqrt(2) * r / w0
        
        # Calculate associated Laguerre polynomial
        laguerre_poly = OAMPhysics._laguerre_poly(p, abs(oam_charge), r_norm**2)
        
        # LG mode intensity profile
        intensity = (
            (r_norm**(2 * abs(oam_charge))) * 
            math.exp(-r_norm**2) * 
            (laguerre_poly**2)
        )
        
        # Normalization factor
        norm = math.sqrt(2 * math.factorial(p) / (math.pi * math.factorial(p + abs(oam_charge))))
        
        return intensity * (norm**2)
    
    @staticmethod
    def _laguerre_poly(p: int, abs_oam: int, x: float) -> float:  # Changed 'l' to 'abs_oam'
        """Calculate associated Laguerre polynomial L_p^l(x)"""
        if p == 0:
            return 1
        elif p == 1:
            return 1 + abs_oam - x
        elif p == 2:
            return (x**2 - 2*(abs_oam+2)*x + (abs_oam+1)*(abs_oam+2)) / 2
        
        # For higher orders, use recursion
        L_prev2 = 1
        L_prev1 = 1 + abs_oam - x
        
        for n in range(2, p + 1):
            L_current = ((2*n - 1 + abs_oam - x) * L_prev1 - (n - 1 + abs_oam) * L_prev2) / n
            L_prev2, L_prev1 = L_prev1, L_current
        
        return L_prev1
    
    @staticmethod
    def interfere_beams(
        beam1_oam: int,
        beam2_oam: int,
        phase_diff: float = 0.0
    ) -> Tuple[float, int]:
        """
        Calculate interference of two OAM beams
        
        Returns:
            visibility: Interference visibility (0 to 1)
            resulting_oam: OAM charge of resulting beam
        """
        if beam1_oam == beam2_oam:
            # Same OAM - perfect interference (up to phase)
            visibility = 1.0
            resulting_oam = beam1_oam
        elif beam1_oam == -beam2_oam:
            # Opposite OAM - can interfere with forked interferometer
            visibility = 0.7
            resulting_oam = 0  # Can result in Gaussian-like beam
        else:
            # Different OAM - reduced interference
            oam_diff = abs(beam1_oam - beam2_oam)
            visibility = max(0.1, 1.0 - 0.1 * oam_diff)  # Decreases with OAM difference
            # Result takes OAM of stronger beam (simplified model)
            resulting_oam = beam1_oam if abs(beam1_oam) >= abs(beam2_oam) else beam2_oam
        
        # Adjust for phase difference
        visibility *= abs(math.cos(phase_diff))
        
        return visibility, resulting_oam
    
    @staticmethod
    def multiplex_oam_modes(
        beams: List[Dict[str, Any]],
        method: str = "mode"
    ) -> Dict[str, Any]:
        """
        Multiplex multiple OAM modes
        
        Args:
            beams: List of beam dictionaries with 'oam_charge' key
            method: 'spatial', 'mode', 'wavelength', or 'polarization'
            
        Returns:
            multiplexed: Combined beam information
        """
        if not beams:
            return {
                'type': 'multiplexed',
                'oam_charges': [],
                'method': method,
                'capacity': 0,
                'efficiency': 0.0,
                'total_power': 0.0
            }
        
        oam_charges = []
        total_power = 0.0
        
        for beam in beams:
            if isinstance(beam, dict) and 'oam_charge' in beam:
                oam_charges.append(beam['oam_charge'])
                total_power += beam.get('power', 1.0)
        
        # Calculate based on multiplexing method
        unique_charges = len(set(oam_charges))
        total_modes = len(oam_charges)
        
        if method == "spatial":
            # Spatial multiplexing (different locations)
            capacity = unique_charges * 2  # Each OAM can have ± charge
            efficiency = 0.9
            
        elif method == "mode":
            # Mode division multiplexing
            capacity = total_modes
            efficiency = 0.8
            
        elif method == "wavelength":
            # Wavelength division + OAM
            capacity = unique_charges * 4  # Multiple wavelengths
            efficiency = 0.7
            
        elif method == "polarization":
            # Polarization + OAM multiplexing
            capacity = unique_charges * 2  # Two polarizations
            efficiency = 0.85
            
        else:
            capacity = 1
            efficiency = 0.5
        
        # Efficiency decreases with more modes
        efficiency = efficiency * (0.95 ** min(total_modes - 1, 10))
        
        return {
            'type': 'multiplexed',
            'oam_charges': oam_charges,
            'method': method,
            'capacity': capacity,
            'efficiency': max(0.1, efficiency),
            'total_power': total_power,
            'unique_modes': unique_charges,
            'total_modes': total_modes
        }
    
    @staticmethod
    def calculate_oam_spectrum(
        beams: List[Dict[str, Any]],
        max_oam: int = 10
    ) -> List[float]:
        """
        Calculate OAM spectrum (distribution of charges)
        
        Args:
            beams: List of beam dictionaries
            max_oam: Maximum absolute OAM to consider
            
        Returns:
            spectrum: Intensity at each OAM value from -max_oam to +max_oam
        """
        spectrum_size = 2 * max_oam + 1
        spectrum = [0.0] * spectrum_size
        
        if not beams:
            return spectrum
        
        for beam in beams:
            if not isinstance(beam, dict):
                continue
                
            oam = beam.get('oam_charge', 0)
            power = beam.get('power', 1.0)
            
            # Map OAM to spectrum index
            idx = oam + max_oam
            if 0 <= idx < spectrum_size:
                spectrum[idx] += power
        
        # Normalize
        total = sum(spectrum)
        if total > 0:
            spectrum = [s / total for s in spectrum]
        
        return spectrum
    
    @staticmethod
    def create_vortex_array(
        oam_charges: List[int],
        spacing: float = 1.0
    ) -> Dict[str, Any]:
        """
        Create array of vortex beams (for OAM multiplexing)
        
        Args:
            oam_charges: List of OAM charges for each beam
            spacing: Spacing between beams (in beam waist units)
            
        Returns:
            vortex_array: Array configuration
        """
        beams = []
        
        for i, charge in enumerate(oam_charges):
            beam = {
                'type': 'vortex_beam',
                'oam_charge': charge,
                'position': i * spacing,
                'power': 1.0 / len(oam_charges),
                'waist': 1.0,
                'wavelength': 1550e-9
            }
            
            # Add phase profile based on OAM
            if charge > 0:
                beam['phase_profile'] = f'helical_left_{charge}'
            elif charge < 0:
                beam['phase_profile'] = f'helical_right_{-charge}'
            else:
                beam['phase_profile'] = 'gaussian'
            
            beams.append(beam)
        
        total_oam = sum(oam_charges)
        avg_oam = total_oam / len(oam_charges) if oam_charges else 0
        
        return {
            'type': 'vortex_array',
            'beams': beams,
            'num_modes': len(oam_charges),
            'total_oam': total_oam,
            'average_oam': avg_oam,
            'spacing': spacing,
            'config': f'{len(oam_charges)}-mode OAM array'
        }
    
    @staticmethod
    def combine_oam_states(
        state1: Dict[str, Any],
        state2: Dict[str, Any],
        operation: str = "add"
    ) -> Dict[str, Any]:
        """
        Combine two OAM states
        
        Args:
            state1: First OAM state
            state2: Second OAM state
            operation: "add", "subtract", or "multiply"
            
        Returns:
            combined: Resulting OAM state
        """
        oam1 = state1.get('oam_charge', 0) if isinstance(state1, dict) else 0
        oam2 = state2.get('oam_charge', 0) if isinstance(state2, dict) else 0
        
        if operation == "add":
            result_oam = oam1 + oam2
            desc = f"OAM{oam1} + OAM{oam2}"
        elif operation == "subtract":
            result_oam = oam1 - oam2
            desc = f"OAM{oam1} - OAM{oam2}"
        elif operation == "multiply":
            # For quantum states, this is tensor product
            result_oam = oam1  # Simplified
            desc = f"|OAM{oam1}⟩ ⊗ |OAM{oam2}⟩"
        else:
            result_oam = oam1
            desc = f"OAM{oam1} (unknown operation)"
        
        return {
            'type': 'oam_combination',
            'operation': operation,
            'oam1': oam1,
            'oam2': oam2,
            'result_oam': result_oam,
            'description': desc,
            'is_valid': abs(result_oam) <= 10  # Practical limit
        }
    
    @staticmethod
    def check_oam_conservation(
        input_beams: List[Dict[str, Any]],
        output_beams: List[Dict[str, Any]],
        tolerance: float = 0.1
    ) -> Tuple[bool, float]:
        """
        Check if OAM is conserved in a process
        
        Args:
            input_beams: List of input beams
            output_beams: List of output beams
            tolerance: Allowed fractional error
            
        Returns:
            conserved: Whether OAM is conserved
            error: Fractional error
        """
        input_oam = 0
        input_power = 0
        
        for beam in input_beams:
            if isinstance(beam, dict):
                oam = beam.get('oam_charge', 0)
                power = beam.get('power', 1.0)
                input_oam += oam * power
                input_power += power
        
        output_oam = 0
        output_power = 0
        
        for beam in output_beams:
            if isinstance(beam, dict):
                oam = beam.get('oam_charge', 0)
                power = beam.get('power', 1.0)
                output_oam += oam * power
                output_power += power
        
        if input_power == 0 or output_power == 0:
            return False, 1.0
        
        # Normalize by power
        avg_input_oam = input_oam / input_power
        avg_output_oam = output_oam / output_power
        
        error = abs(avg_input_oam - avg_output_oam) / max(abs(avg_input_oam), 1.0)
        conserved = error <= tolerance
        
        return conserved, error


def test_oam_physics():
    """Test OAM physics functions"""
    print("Testing OAM Physics...")
    
    physics = OAMPhysics()
    
    # Test interference
    print("\n1. Testing beam interference:")
    
    # Same OAM
    vis1, oam1 = physics.interfere_beams(+1, +1)
    print(f"   OAM+1 ⊕ OAM+1 → visibility={vis1:.2f}, resulting OAM={oam1}")
    
    # Different OAM
    vis2, oam2 = physics.interfere_beams(+1, -2)
    print(f"   OAM+1 ⊕ OAM-2 → visibility={vis2:.2f}, resulting OAM={oam2}")
    
    # Test multiplexing
    print("\n2. Testing OAM multiplexing:")
    
    beams = [
        {'oam_charge': +1, 'power': 0.5},
        {'oam_charge': -2, 'power': 0.5},
        {'oam_charge': 0, 'power': 0.5}
    ]
    
    multiplexed = physics.multiplex_oam_modes(beams, "mode")
    print(f"   Multiplexed {multiplexed['total_modes']} modes")
    print(f"   Capacity: {multiplexed['capacity']} channels")
    print(f"   Efficiency: {multiplexed['efficiency']:.1%}")
    
    # Test OAM spectrum
    print("\n3. Testing OAM spectrum calculation:")
    
    spectrum = physics.calculate_oam_spectrum(beams)
    print(f"   Spectrum length: {len(spectrum)}")
    print(f"   Non-zero bins: {sum(1 for s in spectrum if s > 0)}")
    
    # Test vortex array
    print("\n4. Testing vortex array creation:")
    
    vortex_array = physics.create_vortex_array([+1, -2, +3, 0])
    print(f"   Created array with {vortex_array['num_modes']} modes")
    print(f"   Total OAM: {vortex_array['total_oam']}")
    
    # Test OAM conservation
    print("\n5. Testing OAM conservation:")
    
    conserved, error = physics.check_oam_conservation(beams, beams)
    print(f"   Self-conservation: {conserved} (error={error:.3f})")
    
    print("\n✅ OAM physics tests completed!")


if __name__ == "__main__":
    test_oam_physics()
