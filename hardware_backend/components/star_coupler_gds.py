"""
GDSII layout generation for Star Coupler.
"""

import gdspy
import numpy as np
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class StarCouplerGDS:
    """Generate GDSII geometry for a star coupler."""
    
    def __init__(self, 
                 library: gdspy.GdsLibrary,
                 parameters: Dict[str, Any]):
        self.lib = library
        self.params = parameters
        
        # GDSII layers (example - adjust based on your PDK)
        self.layers = {
            'waveguide': 1,
            'etch': 2,
            'metal': 3
        }
        
        # Create cell for this component
        self.cell = gdspy.Cell(f"STAR_COUPLER_OAM{parameters.get('topological_charge', 1)}")
    
    def generate_geometry(self) -> gdspy.Cell:
        """Generate all geometric elements."""
        
        ports = self.params.get('ports', 26)
        radius = self.params.get('radius', 15e-6)
        wg_width = self.params.get('waveguide_width', 0.5e-6)
        
        # 1. Input waveguide
        input_length = 10e-6
        input_wg = gdspy.Path(wg_width, (0, 0))
        input_wg.segment(input_length, direction='+x')
        self.cell.add(input_wg)
        
        # 2. Free propagation region (sector)
        sector_angle = 60  # degrees (typical for star couplers)
        sector = self._create_sector(radius, sector_angle)
        self.cell.add(sector)
        
        # 3. Output waveguides (fan-out)
        self._create_output_waveguides(ports, radius, wg_width, sector_angle)
        
        # 4. Add ports for connection to other components
        self._define_ports(input_length, radius, ports)
        
        logger.info(f"Generated StarCoupler GDS: {ports} ports, radius {radius*1e6:.1f}um")
        return self.cell
    
    def _create_sector(self, radius: float, angle: float) -> gdspy.Polygon:
        """Create the free propagation sector region."""
        
        # Create sector polygon
        theta = np.radians(angle / 2)
        
        # Points: tip at origin, arc at radius
        points = [(0, 0)]
        
        # Generate arc points
        n_points = 50
        angles = np.linspace(-theta, theta, n_points)
        for a in angles:
            x = radius * np.cos(a)
            y = radius * np.sin(a)
            points.append((x, y))
        
        points.append((0, 0))  # Close polygon
        
        sector = gdspy.Polygon(points, layer=self.layers['waveguide'])
        return sector
    
    def _create_output_waveguides(self, 
                                 ports: int, 
                                 radius: float, 
                                 wg_width: float,
                                 sector_angle: float):
        """Create output waveguides at the edge of the sector."""
        
        angles = np.linspace(-sector_angle/2, sector_angle/2, ports)
        
        for i, angle_deg in enumerate(angles):
            angle_rad = np.radians(angle_deg)
            
            # Start point at sector edge
            x_start = radius * np.cos(angle_rad)
            y_start = radius * np.sin(angle_rad)
            
            # Direction radial outward
            x_end = (radius + 5e-6) * np.cos(angle_rad)
            y_end = (radius + 5e-6) * np.sin(angle_rad)
            
            # Create waveguide
            wg = gdspy.Path(wg_width, (x_start, y_start))
            wg.segment(5e-6, direction=(np.cos(angle_rad), np.sin(angle_rad)))
            
            # Add to cell with label for this port
            self.cell.add(wg)
            
            # Add port label (useful for routing)
            label = gdspy.Label(
                f"OUT_{i}",
                (x_end, y_end),
                layer=self.layers['metal']
            )
            self.cell.add(label)
    
    def _define_ports(self, input_length: float, radius: float, ports: int):
        """Define input and output ports for circuit connections."""
        
        # Input port
        input_port = {
            'name': 'IN',
            'position': (0, 0),
            'direction': 180,  # degrees, pointing left
            'width': self.params.get('waveguide_width', 0.5e-6)
        }
        
        # Output ports
        output_ports = []
        angles = np.linspace(-30, 30, ports)  # ±30 degree sector
        
        for i, angle in enumerate(angles):
            angle_rad = np.radians(angle)
            output_length = 5e-6
            
            port = {
                'name': f'OUT_{i}',
                'position': (
                    (radius + output_length) * np.cos(angle_rad),
                    (radius + output_length) * np.sin(angle_rad)
                ),
                'direction': angle,  # Radial outward
                'width': self.params.get('waveguide_width', 0.5e-6),
                'phase': self.params.get('topological_charge', 1) * angle_rad
            }
            output_ports.append(port)
        
        # Store port definitions in cell properties
        self.cell.properties['ports'] = {
            'input': input_port,
            'outputs': output_ports
        }

def create_star_coupler_from_svx(parameters: Dict[str, Any]) -> gdspy.Cell:
    """
    Factory function to create star coupler from SpectraVortex parameters.
    
    This function would be called by the chip_designer.py backend when
    it encounters a StarCoupler component in the SVX code.
    """
    
    # Create a temporary library
    lib = gdspy.GdsLibrary()
    
    # Generate the component
    generator = StarCouplerGDS(lib, parameters)
    cell = generator.generate_geometry()
    
    return cell
