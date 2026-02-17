"""
Technology Design Rules for 220nm Silicon Photonics
Standard silicon-on-insulator platform specifications
"""

from typing import Dict, List, Tuple, Any
import math


class SiliconPhotonic220nm:
    """Design rules for standard 220nm Silicon Photonics"""
    
    def __init__(self):
        self.name = "Silicon Photonic 220nm"
        self.version = "1.0"
        self.foundry = "Standard SOI Platform"
        
        # Layer definitions for GDSII
        self.layers = {
            "waveguide": {"gds_layer": 1, "datatype": 0, "material": "Si", "thickness": 0.22},
            "heater": {"gds_layer": 10, "datatype": 0, "material": "TiN", "thickness": 0.1},
            "metal": {"gds_layer": 11, "datatype": 0, "material": "Al", "thickness": 0.5},
            "via": {"gds_layer": 12, "datatype": 0, "material": "W", "thickness": 0.5},
            "grating": {"gds_layer": 20, "datatype": 0, "material": "Si", "thickness": 0.22},
        }
        
        # Design rules (minimum values in micrometers)
        self.rules = {
            "min_width": 0.4,          # Minimum waveguide width
            "min_spacing": 0.2,        # Minimum spacing between waveguides
            "min_bend_radius": 5.0,    # Minimum bend radius
            "max_length": 10000.0,     # Maximum chip dimension
            "min_coupler_gap": 0.1,    # Minimum directional coupler gap
            "max_coupler_length": 50.0, # Maximum coupler length
        }
        
        # Material properties
        self.materials = {
            "Si": {
                "refractive_index": 3.47,
                "loss_dB_per_cm": 2.0,
                "thermal_conductivity": 149,  # W/(m·K)
            },
            "SiO2": {
                "refractive_index": 1.44,
                "loss_dB_per_cm": 0.1,
                "thermal_conductivity": 1.4,
            },
            "TiN": {
                "resistivity": 100e-6,  # Ω·cm
                "thermal_conductivity": 30,
            }
        }
    
    def validate_waveguide(self, width: float, radius: float = 0) -> List[str]:
        """Validate waveguide parameters against design rules"""
        errors = []
        
        if width < self.rules["min_width"]:
            errors.append(f"Width too small: {width}μm < {self.rules['min_width']}μm")
        
        if radius > 0 and radius < self.rules["min_bend_radius"]:
            errors.append(f"Bend radius too small: {radius}μm < {self.rules['min_bend_radius']}μm")
        
        return errors
    
    def validate_spacing(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Check if spacing between two points meets design rules"""
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance >= self.rules["min_spacing"]
    
    def get_waveguide_properties(self, width: float = 0.5) -> Dict:
        """Get waveguide optical properties"""
        # Simplified model for 220x500nm waveguide
        if width == 0.5:
            return {
                "effective_index": 2.4,
                "loss_dB_per_cm": 2.0,
                "confinement": 0.8,
                "mode_area": 0.11,  # μm²
            }
        else:
            return {
                "effective_index": 2.4 * (width / 0.5)**0.1,
                "loss_dB_per_cm": 2.0 * (0.5 / width),
                "confinement": 0.8,
                "mode_area": 0.11 * (width / 0.5),
            }
    
    def generate_tech_report(self) -> str:
        """Generate technology report"""
        report = "=" * 60 + "\n"
        report += "SILICON PHOTONIC 220nm TECHNOLOGY REPORT\n"
        report += "=" * 60 + "\n\n"
        
        report += "1. DESIGN RULES:\n"
        for rule, value in self.rules.items():
            report += f"   {rule}: {value} μm\n"
        
        report += "\n2. LAYER DEFINITIONS:\n"
        for layer_name, layer_info in self.layers.items():
            report += f"   {layer_name}: GDS({layer_info['gds_layer']}:{layer_info['datatype']}) "
            report += f"- {layer_info['material']} {layer_info['thickness']}μm\n"
        
        report += "\n3. WAVEGUIDE PROPERTIES (500nm width):\n"
        props = self.get_waveguide_properties(0.5)
        for prop, value in props.items():
            report += f"   {prop}: {value}\n"
        
        return report
    
    def get_layer_info(self, layer_name: str) -> Dict:
        """Get information about specific layer"""
        return self.layers.get(layer_name, {})
    
    def check_component_placement(self, component1: Dict, component2: Dict) -> bool:
        """Check if two components can be placed without violation"""
        # Simplified: just check bounding boxes
        x1, y1 = component1.get("position", (0, 0))
        x2, y2 = component2.get("position", (0, 0))
        return self.validate_spacing(x1, y1, x2, y2)


# Create global instance for easy access
TECH_220NM = SiliconPhotonic220nm()

# Example usage
if __name__ == "__main__":
    print(TECH_220NM.generate_tech_report())
