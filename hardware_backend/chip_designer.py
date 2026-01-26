"""
Chip Designer - Converts SpectraVortex AST to photonic chip layout
Main hardware compiler module
"""

import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import numpy as np

from .component_library import Waveguide, MZIInterferometer, OAMModeConverter
from .technology_kits.silicon_photonic_220nm import TECH_220NM


@dataclass
class DesignMetrics:
    """Metrics for chip design"""
    total_area: float = 0.0
    total_loss: float = 0.0
    component_count: int = 0
    waveguide_length: float = 0.0
    port_count: int = 0
    violations: int = 0


class ChipDesigner:
    """Main chip designer class - converts AST to physical layout"""
    
    def __init__(self, technology: str = "silicon_photonic_220nm"):
        self.technology = technology
        self.tech_rules = TECH_220NM
        
        # Design state
        self.components = []  # List of all components
        self.connections = []  # List of waveguide connections
        self.ports = {}  # Chip ports: name -> position
        self.layout = []  # Geometric layout data
        
        # Metrics
        self.metrics = DesignMetrics()
        
        # Design errors and warnings
        self.errors = []
        self.warnings = []
        
        print(f"[ChipDesigner] Initialized with {technology} technology")
    
    def design_from_ast(self, ast_node: Any) -> 'ChipDesigner':
        """Main design entry point - process AST node"""
        print("\n" + "="*60)
        print("SPECTRAVORTEX HARDWARE COMPILER")
        print("="*60)
        
        self._reset()
        
        # Process AST based on node type
        if hasattr(ast_node, '__class__'):
            node_type = ast_node.__class__.__name__
            print(f"[Designer] Processing AST node: {node_type}")
            
            if node_type == 'ProgramNode':
                self._process_program(ast_node)
            elif node_type == 'VortexPhotonNode':
                self._add_vortex_source(ast_node)
            elif node_type == 'VortexBeamNode':
                self._add_vortex_beam(ast_node)
            elif node_type == 'InterfereNode':
                self._design_interferometer(ast_node)
            elif node_type == 'MatrixLiteralNode':
                self._design_matrix_core(ast_node)
            else:
                print(f"[Designer] Skipping unknown node type: {node_type}")
        
        # Finalize design
        self._finalize_design()
        
        return self
    
    def _reset(self) -> None:
        """Reset designer state"""
        self.components = []
        self.connections = []
        self.ports = {}
        self.layout = []
        self.metrics = DesignMetrics()
        self.errors = []
        self.warnings = []
    
    def _process_program(self, program_node: Any) -> None:
        """Process program node"""
        print(f"[Designer] Processing program with {len(program_node.statements)} statements")
        
        for i, stmt in enumerate(program_node.statements):
            print(f"  Statement {i+1}: {stmt.__class__.__name__}")
            self.design_from_ast(stmt)
    
    def _add_vortex_source(self, vortex_node: Any) -> None:
        """Add OAM vortex source to chip"""
        name = getattr(vortex_node, 'name', 'vortex_source')
        oam_charge = getattr(vortex_node, 'oam_charge', 1)
        
        print(f"[Designer] Adding OAM source: {name} (OAM={oam_charge})")
        
        # Create OAM converter
        converter = OAMModeConverter(
            target_oam=oam_charge,
            efficiency=0.85,
            diameter=20.0
        )
        
        # Position: start at (100, 100) and move right for each source
        position = (100 + len(self.components) * 150, 100)
        
        component = {
            'type': 'oam_source',
            'name': name,
            'component': converter,
            'position': position,
            'size': (20.0, 20.0),
            'ports': {
                'output': (position[0] + 10, position[1])
            }
        }
        
        self.components.append(component)
        self.ports[f"{name}_out"] = component['ports']['output']
        self.metrics.component_count += 1
        
        print(f"  ✓ Added at position {position}")
    
    def _add_vortex_beam(self, beam_node: Any) -> None:
        """Add vortex beam (LG mode)"""
        name = getattr(beam_node, 'name', 'lg_beam')
        oam_charge = getattr(beam_node, 'oam_charge', 0)
        
        print(f"[Designer] Adding vortex beam: {name} (OAM={oam_charge})")
        
        position = (100 + len(self.components) * 150, 200)
        
        component = {
            'type': 'vortex_beam',
            'name': name,
            'oam_charge': oam_charge,
            'position': position,
            'size': (15.0, 15.0),
            'ports': {
                'output': (position[0] + 7.5, position[1])
            }
        }
        
        self.components.append(component)
        self.ports[f"{name}_out"] = component['ports']['output']
        self.metrics.component_count += 1
    
    def _design_interferometer(self, interfere_node: Any) -> None:
        """Design interferometer for two beams"""
        print("[Designer] Designing interferometer...")
        
        # Create MZI interferometer
        mzi = MZIInterferometer(
            coupling_ratio=0.5,
            phase_shift=0.0
        )
        
        position = (300, 150)
        
        component = {
            'type': 'mzi_interferometer',
            'name': 'interferometer',
            'component': mzi,
            'position': position,
            'size': (160.0, 50.0),
            'ports': {
                'in1': (position[0], position[1]),
                'in2': (position[0], position[1] + 10),
                'out1': (position[0] + 160, position[1]),
                'out2': (position[0] + 160, position[1] + 10)
            }
        }
        
        self.components.append(component)
        
        # Add connections if we have sources
        if len(self.components) >= 2:
            # Connect last two sources to interferometer
            source1 = self.components[-3]  # First source
            source2 = self.components[-2]  # Second source
            
            # Create waveguides
            wg1 = Waveguide(length=100.0, width=0.5)
            wg2 = Waveguide(length=100.0, width=0.5)
            
            self.connections.append({
                'from': source1['ports']['output'],
                'to': component['ports']['in1'],
                'waveguide': wg1
            })
            
            self.connections.append({
                'from': source2['ports']['output'],
                'to': component['ports']['in2'],
                'waveguide': wg2
            })
            
            self.metrics.waveguide_length += wg1.length + wg2.length
        
        self.metrics.component_count += 1
        print(f"  ✓ MZI interferometer added at {position}")
    
    def _design_matrix_core(self, matrix_node: Any) -> None:
        """Design matrix multiplication core"""
        print("[Designer] Designing matrix core...")
        
        rows = getattr(matrix_node, 'rows', 2)
        cols = getattr(matrix_node, 'cols', 2)
        
        print(f"  Matrix size: {rows}x{cols}")
        
        # For NxN matrix, need N*(N-1)/2 MZIs
        if rows == cols:
            n = rows
            num_mzis = n * (n - 1) // 2
            
            # Create MZI mesh
            start_pos = (400, 100)
            
            for i in range(num_mzis):
                row = i // (n - 1)
                col = i % (n - 1)
                
                position = (
                    start_pos[0] + col * 180,
                    start_pos[1] + row * 80
                )
                
                mzi = MZIInterferometer(
                    coupling_ratio=0.5,
                    phase_shift=0.0
                )
                
                component = {
                    'type': 'mzi_mesh_element',
                    'name': f'mzi_{i+1}',
                    'component': mzi,
                    'position': position,
                    'size': (160.0, 50.0),
                    'ports': {
                        'in1': (position[0], position[1]),
                        'in2': (position[0], position[1] + 10),
                        'out1': (position[0] + 160, position[1]),
                        'out2': (position[0] + 160, position[1] + 10)
                    }
                }
                
                self.components.append(component)
                self.metrics.component_count += 1
            
            print(f"  ✓ Created MZI mesh with {num_mzis} interferometers")
    
    def _finalize_design(self) -> None:
        """Finalize chip design and calculate metrics"""
        print("\n[Designer] Finalizing design...")
        
        # Calculate total area
        max_x, max_y = 0, 0
        for comp in self.components:
            x, y = comp['position']
            width, height = comp['size']
            max_x = max(max_x, x + width)
            max_y = max(max_y, y + height)
        
        self.metrics.total_area = max_x * max_y
        
        # Calculate total loss
        total_loss = 0.0
        for comp in self.components:
            if 'component' in comp and hasattr(comp['component'], 'calculate_loss'):
                total_loss += comp['component'].calculate_loss()
        
        for conn in self.connections:
            total_loss += conn['waveguide'].calculate_loss()
        
        self.metrics.total_loss = total_loss
        self.metrics.port_count = len(self.ports)
        
        # Generate layout data
        self._generate_layout()
        
        # Validate against design rules
        self._validate_design()
    
    def _generate_layout(self) -> None:
        """Generate layout geometry"""
        self.layout = []
        
        # Add components to layout
        for comp in self.components:
            layout_item = {
                'type': comp['type'],
                'name': comp['name'],
                'position': comp['position'],
                'size': comp['size'],
                'layer': 'waveguide'
            }
            
            if 'ports' in comp:
                layout_item['ports'] = comp['ports']
            
            self.layout.append(layout_item)
        
        # Add waveguides to layout
        for i, conn in enumerate(self.connections):
            wg_item = {
                'type': 'waveguide',
                'name': f'wg_{i+1}',
                'from': conn['from'],
                'to': conn['to'],
                'width': conn['waveguide'].width,
                'layer': 'waveguide'
            }
            self.layout.append(wg_item)
    
    def _validate_design(self) -> None:
        """Validate design against technology rules"""
        print("[Designer] Validating design...")
        
        # Check waveguide widths
        for conn in self.connections:
            errors = self.tech_rules.validate_waveguide(
                width=conn['waveguide'].width,
                radius=conn['waveguide'].radius
            )
            
            if errors:
                self.errors.extend(errors)
                self.metrics.violations += len(errors)
        
        # Check component spacing
        for i in range(len(self.components)):
            for j in range(i + 1, len(self.components)):
                comp1 = self.components[i]
                comp2 = self.components[j]
                
                x1, y1 = comp1['position']
                x2, y2 = comp2['position']
                
                if not self.tech_rules.validate_spacing(x1, y1, x2, y2):
                    warning = f"Components {comp1['name']} and {comp2['name']} too close"
                    self.warnings.append(warning)
        
        print(f"  Validation complete: {len(self.errors)} errors, {len(self.warnings)} warnings")
    
    def generate_report(self) -> str:
        """Generate design report"""
        report = "\n" + "="*60 + "\n"
        report += "CHIP DESIGN REPORT\n"
        report += "="*60 + "\n\n"
        
        report += "DESIGN METRICS:\n"
        report += f"  Total Area: {self.metrics.total_area:.1f} μm²\n"
        report += f"  Total Loss: {self.metrics.total_loss:.2f} dB\n"
        report += f"  Components: {self.metrics.component_count}\n"
        report += f"  Waveguide Length: {self.metrics.waveguide_length:.1f} μm\n"
        report += f"  Ports: {self.metrics.port_count}\n"
        report += f"  Design Rule Violations: {self.metrics.violations}\n\n"
        
        report += "COMPONENTS:\n"
        for comp in self.components:
            report += f"  {comp['type']}: {comp['name']} at {comp['position']}\n"
        
        if self.connections:
            report += "\nCONNECTIONS:\n"
            for conn in self.connections:
                report += f"  {conn['from']} → {conn['to']}\n"
        
        if self.errors:
            report += "\nERRORS:\n"
            for error in self.errors:
                report += f"  ✗ {error}\n"
        
        if self.warnings:
            report += "\nWARNINGS:\n"
            for warning in self.warnings:
                report += f"  ⚠ {warning}\n"
        
        return report
    
    def get_design_summary(self) -> Dict:
        """Get design summary as dictionary"""
        return {
            'technology': self.technology,
            'metrics': {
                'total_area': self.metrics.total_area,
                'total_loss': self.metrics.total_loss,
                'component_count': self.metrics.component_count,
                'waveguide_length': self.metrics.waveguide_length,
                'port_count': self.metrics.port_count,
                'violations': self.metrics.violations,
            },
            'components': len(self.components),
            'connections': len(self.connections),
            'errors': len(self.errors),
            'warnings': len(self.warnings),
        }


# Example usage
if __name__ == "__main__":
    print("Chip Designer Module - Standalone Test")
    designer = ChipDesigner()
    print("✅ Chip Designer initialized successfully")
