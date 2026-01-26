"""
Chip Designer: Convert SpectraVortex AST to photonic chip layouts.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import math

from .component_library import Waveguide, MZIInterferometer, OAMModeConverter, PhotonicComponent
from .gdsii_generator import GDSIIGenerator
from .technology_kits.silicon_photonic_220nm import TECH_220NM, SiliconPhotonic220nm

@dataclass
class DesignMetrics:
    """Metrics for chip design."""
    total_area: float = 0.0  # μm²
    total_loss: float = 0.0  # dB
    component_count: int = 0
    waveguide_length: float = 0.0  # μm
    io_ports: int = 0
    violations: List[str] = field(default_factory=list)

class ChipDesigner:
    """Design photonic chips from SpectraVortex AST."""
    
    def __init__(self, technology: str = "silicon_photonic_220nm"):
        """
        Initialize chip designer.
        
        Args:
            technology: Technology process name
        """
        self.technology = technology
        self.components: List[PhotonicComponent] = []
        self.metrics = DesignMetrics()
        self.connections: List[Tuple[str, str]] = []  # Component connections
        
        # Load technology kit
        if technology == "silicon_photonic_220nm":
            self.tech_kit = SiliconPhotonic220nm()
        else:
            raise ValueError(f"Unsupported technology: {technology}")
    
    def design_from_ast(self, ast_node: Any) -> 'ChipDesigner':
        """
        Design chip from SpectraVortex AST.
        
        Args:
            ast_node: Abstract Syntax Tree from SpectraVortex compiler
            
        Returns:
            Self for method chaining
        """
        print("[ChipDesigner] Starting chip design from AST...")
        
        # TODO: Parse actual AST structure
        # For now, create a simple demo design
        
        # Add example components
        self.add_component(
            Waveguide(length=50.0, width=0.5, name="input_waveguide")
        )
        
        self.add_component(
            MZIInterferometer(
                coupling_ratio=0.5,
                phase_shift=0.785,  # 45 degrees
                name="mzi_1"
            )
        )
        
        self.add_component(
            OAMModeConverter(
                target_oam=1,
                efficiency=0.85,
                name="oam_converter_1"
            )
        )
        
        # Calculate metrics
        self._calculate_metrics()
        
        print(f"[ChipDesigner] Design completed: {self.metrics.component_count} components")
        return self
    
    def add_component(self, component: PhotonicComponent) -> None:
        """Add a photonic component to the design."""
        self.components.append(component)
        self.metrics.component_count = len(self.components)
        print(f"[ChipDesigner] Added component: {component.name}")
    
    def _calculate_metrics(self) -> None:
        """Calculate design metrics."""
        # Reset metrics
        self.metrics.total_area = 0.0
        self.metrics.total_loss = 0.0
        self.metrics.waveguide_length = 0.0
        self.metrics.io_ports = 0
        self.metrics.violations = []
        
        # Calculate based on components
        for component in self.components:
            if isinstance(component, Waveguide):
                self.metrics.waveguide_length += component.length
                self.metrics.total_loss += component.calculate_loss()
                # Estimate area: waveguide length * (width + spacing)
                self.metrics.total_area += component.length * 2.0
                
            elif isinstance(component, MZIInterferometer):
                # MZI area approximation: 50x50 μm
                self.metrics.total_area += 2500.0
                self.metrics.total_loss += 0.5  # dB per MZI
                self.metrics.io_ports += 2
                
            elif isinstance(component, OAMModeConverter):
                # OAM converter area approximation: 30x30 μm
                self.metrics.total_area += 900.0
                self.metrics.total_loss += 0.3  # dB
                self.metrics.io_ports += 1
        
        # Add routing area (estimation)
        routing_area = self.metrics.waveguide_length * 3.0
        self.metrics.total_area += routing_area
        
        # Validate against technology rules
        self._validate_design()
    
    def _validate_design(self) -> None:
        """Validate design against technology rules."""
        # Check waveguide widths
        for component in self.components:
            if isinstance(component, Waveguide):
                min_width = self.tech_kit.rules.get('min_width', 0.4)
                if component.width < min_width:
                    self.metrics.violations.append(
                        f"Waveguide {component.name}: width {component.width}μm < min {min_width}μm"
                    )
    
    def export_to_gds(self, generator: GDSIIGenerator) -> Dict:
        """
        Export design to GDSII format.
        
        Args:
            generator: GDSIIGenerator instance
            
        Returns:
            GDSII data as dictionary
        """
        print("[ChipDesigner] Exporting to GDSII format...")
        
        # Create components in GDS
        x_pos, y_pos = 0, 0
        spacing = 50.0  # μm between components
        
        for i, component in enumerate(self.components):
            if isinstance(component, Waveguide):
                # Draw waveguide as path
                points = [
                    [x_pos, y_pos],
                    [x_pos + component.length, y_pos]
                ]
                generator.add_path(
                    layer=1,
                    points=points,
                    width=component.width,
                    properties={
                        "component": "waveguide",
                        "name": component.name,
                        "length": component.length,
                        "loss": component.calculate_loss()
                    }
                )
                
            elif isinstance(component, MZIInterferometer):
                # Draw MZI as rectangle
                generator.add_rectangle(
                    layer=2,
                    x=x_pos, y=y_pos,
                    width=30.0, height=20.0,
                    properties={
                        "component": "mzi",
                        "name": component.name,
                        "coupling_ratio": component.coupling_ratio
                    }
                )
                
            elif isinstance(component, OAMModeConverter):
                # Draw OAM converter as circle-like polygon
                radius = 15.0
                points = []
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    points.append([
                        x_pos + radius * math.cos(rad),
                        y_pos + radius * math.sin(rad)
                    ])
                
                generator.add_polygon(
                    layer=3,
                    points=points,
                    properties={
                        "component": "oam_converter",
                        "name": component.name,
                        "target_oam": component.target_oam
                    }
                )
            
            # Add component label
            generator.add_text(
                text=component.name,
                x=x_pos, y=y_pos - 5.0,
                layer=10,
                magnification=0.5
            )
            
            # Move position for next component
            x_pos += spacing
            if x_pos > 200:  # New row
                x_pos = 0
                y_pos += spacing
        
        # Add chip border
        border_margin = 20.0
        generator.add_rectangle(
            layer=0,
            x=-border_margin, y=-border_margin,
            width=x_pos + border_margin * 2,
            height=y_pos + border_margin * 2,
            properties={"purpose": "chip_border"}
        )
        
        return generator.to_dict()
    
    def visualize_design(self, output_file: str = "chip_layout.png") -> str:
        """
        Generate visualization of the chip design.
        
        Args:
            output_file: Path to save the visualization image
            
        Returns:
            Path to the saved image file, or empty string if failed
        """
        print(f"[ChipDesigner] Generating visualization...")
        
        try:
            # Import here to avoid circular dependencies
            from .visualize_chip import ChipVisualizer
            
            # Export current design to GDS format
            gds_generator = GDSIIGenerator()
            gds_data = self.export_to_gds(gds_generator)
            
            # Create visualization
            visualizer = ChipVisualizer(scale=1.5)
            visualizer.visualize(gds_data, output_file)
            
            print(f"🎨 Chip visualization saved to: {output_file}")
            return output_file
            
        except ImportError as e:
            print(f"⚠️  Visualization unavailable: {e}")
            print("   Install matplotlib: pip install matplotlib")
            return ""
        except Exception as e:
            print(f"❌ Visualization failed: {e}")
            return ""
    
    def generate_report(self) -> str:
        """Generate design report."""
        report = []
        report.append("=" * 60)
        report.append("CHIP DESIGN REPORT")
        report.append("=" * 60)
        report.append("")
        report.append("DESIGN METRICS:")
        report.append(f"  Total Area: {self.metrics.total_area:.1f} μm²")
        report.append(f"  Total Loss: {self.metrics.total_loss:.2f} dB")
        report.append(f"  Components: {self.metrics.component_count}")
        report.append(f"  Waveguide Length: {self.metrics.waveguide_length:.1f} μm")
        report.append(f"  I/O Ports: {self.metrics.io_ports}")
        
        if self.metrics.violations:
            report.append(f"  Design Rule Violations: {len(self.metrics.violations)}")
            for violation in self.metrics.violations:
                report.append(f"    ⚠️  {violation}")
        else:
            report.append("  Design Rule Violations: 0 ✅")
        
        report.append("")
        report.append("TECHNOLOGY:")
        report.append(f"  Process: {self.technology}")
        report.append(f"  Min waveguide width: {self.tech_kit.rules.get('min_width', 'N/A')}μm")
        report.append(f"  Min bend radius: {self.tech_kit.rules.get('min_bend_radius', 'N/A')}μm")
        
        report.append("")
        report.append("COMPONENTS:")
        for i, component in enumerate(self.components, 1):
            report.append(f"  {i}. {component.name} ({type(component).__name__})")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_design_summary(self) -> Dict:
        """Get design summary as dictionary."""
        return {
            "total_area": self.metrics.total_area,
            "total_loss": self.metrics.total_loss,
            "component_count": self.metrics.component_count,
            "waveguide_length": self.metrics.waveguide_length,
            "io_ports": self.metrics.io_ports,
            "violations": self.metrics.violations,
            "technology": self.technology,
            "components": [comp.name for comp in self.components]
        }
    
    def validate_design(self) -> List[str]:
        """Validate design and return list of issues."""
        self._validate_design()
        return self.metrics.violations
    
    def generate_tech_report(self) -> str:
        """Generate technology report."""
        if hasattr(self.tech_kit, 'generate_tech_report'):
            return self.tech_kit.generate_tech_report()
        return f"Technology: {self.technology}"
