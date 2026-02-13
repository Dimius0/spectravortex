#!/usr/bin/env python3
"""
SpectraVortex Chip Visualizer
Convert GDSII JSON files into beautiful 2D chip visualizations.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Any, Optional
import argparse
import os
import sys

class ChipVisualizer:
    """Photonic chip visualizer for GDSII JSON format."""
    
    # Colors for different component types
    COLORS = {
        'waveguide': '#3498db',      # Blue - waveguides
        'mzi': '#e74c3c',            # Red - MZI interferometers
        'oam_source': '#9b59b6',     # Purple - OAM sources
        'grating_coupler': '#2ecc71', # Green - grating couplers
        'text': '#34495e',           # Dark gray - text
        'default': '#95a5a6'         # Gray - default
    }
    
    # Line styles
    LINE_STYLES = {
        'waveguide': '-',     # Solid line
        'path': '-',          # Solid
        'rectangle': '--',    # Dashed
        'text': ':'           # Dotted
    }
    
    def __init__(self, scale: float = 1.0):
        """
        Initialize the visualizer.
        
        Args:
            scale: Display scale (1.0 = 1 pixel per micron)
        """
        self.scale = scale
        self.fig = None
        self.ax = None
        self.layers_visible = {}  # Which layers to show
        
    def load_gds_json(self, filename: str) -> Dict:
        """Load GDSII JSON file."""
        if not os.path.exists(filename):
            print(f"❌ Error: File {filename} not found!")
            sys.exit(1)
            
        with open(filename, 'r') as f:
            data = json.load(f)
            
        print(f"✅ Loaded file: {filename}")
        print(f"   Format: {data.get('format', 'Unknown')}")
        print(f"   Scale: {data.get('scale', 1000)} units/μm")
        print(f"   Layers: {len(data.get('layers', {}))}")
        
        return data
    
    def _get_component_color(self, shape: Dict) -> str:
        """Determine component color based on its properties."""
        props = shape.get('properties', {})
        
        if 'component' in props:
            comp_type = props['component']
            if 'waveguide' in comp_type:
                return self.COLORS['waveguide']
            elif 'mzi' in comp_type:
                return self.COLORS['mzi']
            elif 'oam' in comp_type:
                return self.COLORS['oam_source']
            elif 'grating' in comp_type:
                return self.COLORS['grating_coupler']
                
        return self.COLORS.get(shape.get('type', 'default'), self.COLORS['default'])
    
    def _draw_waveguide(self, shape: Dict, layer_id: str):
        """Draw a waveguide."""
        points = shape.get('points', [])
        width = shape.get('width', 0.5)
        
        if len(points) < 2:
            return
            
        # Convert points to coordinates
        xs, ys = zip(*points)
        
        # Draw line
        color = self._get_component_color(shape)
        linewidth = max(0.5, width * self.scale * 2)
        
        self.ax.plot(xs, ys, 
                    color=color,
                    linewidth=linewidth,
                    linestyle=self.LINE_STYLES.get('waveguide', '-'),
                    alpha=0.8,
                    label=f'Layer {layer_id}: Waveguide' if not self.ax.lines else "")
    
    def _draw_rectangle(self, shape: Dict, layer_id: str):
        """Draw a rectangle."""
        x = shape.get('x', 0)
        y = shape.get('y', 0)
        width = shape.get('width', 10)
        height = shape.get('height', 5)
        
        color = self._get_component_color(shape)
        rect = patches.Rectangle((x, y), width, height,
                                linewidth=1,
                                edgecolor=color,
                                facecolor=color + '20',  # Semi-transparent fill
                                linestyle=self.LINE_STYLES.get('rectangle', '--'),
                                alpha=0.6)
        
        self.ax.add_patch(rect)
        
        # Label for first rectangle
        if len(self.ax.patches) == 1:
            rect.set_label(f'Layer {layer_id}: Rectangle')
    
    def _draw_text(self, shape: Dict, layer_id: str):
        """Draw text annotation."""
        x = shape.get('x', 0) / 1000  # Convert from GDS units
        y = shape.get('y', 0) / 1000
        text = shape.get('text', '')
        
        if text:
            self.ax.text(x, y, text,
                        color=self.COLORS['text'],
                        fontsize=8,
                        alpha=0.7,
                        ha='center',
                        va='center')
    
    def visualize(self, gds_data: Dict, output_file: Optional[str] = None):
        """
        Create chip visualization.
        
        Args:
            gds_data: GDSII JSON data
            output_file: Output filename (if None - display on screen)
        """
        # Create figure
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        
        # Configure axes
        self.ax.set_xlabel('X position (μm)', fontsize=12)
        self.ax.set_ylabel('Y position (μm)', fontsize=12)
        self.ax.set_title('SpectraVortex Photonic Chip Layout', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.set_aspect('equal')
        
        # Draw all layers
        layers = gds_data.get('layers', {})
        total_shapes = 0
        
        for layer_id, shapes in layers.items():
            print(f"   Processing layer {layer_id}: {len(shapes)} objects")
            
            for shape in shapes:
                shape_type = shape.get('type', 'unknown')
                
                if shape_type == 'waveguide' or shape_type == 'path':
                    self._draw_waveguide(shape, layer_id)
                elif shape_type == 'rectangle':
                    self._draw_rectangle(shape, layer_id)
                elif shape_type == 'text':
                    self._draw_text(shape, layer_id)
                
                total_shapes += 1
        
        # Configure legend
        if self.ax.get_legend_handles_labels()[0]:
            self.ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
        
        # Auto-scale
        self.ax.autoscale_view()
        
        # Add info text
        info_text = f"Chip: {gds_data.get('format', 'Unknown')}\n"
        info_text += f"Total layers: {len(layers)}\n"
        info_text += f"Total shapes: {total_shapes}"
        
        self.fig.text(0.02, 0.02, info_text,
                     fontsize=9,
                     color='gray',
                     verticalalignment='bottom',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Save or display
        if output_file:
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"✅ Visualization saved to: {output_file}")
        else:
            print("✅ Visualization ready. Close window to continue...")
            plt.show()
        
        plt.close(self.fig)
    
    def create_simple_demo(self):
        """Create demo visualization (for testing)."""
        demo_data = {
            "format": "GDSII_JSON_DEMO",
            "version": "1.0",
            "scale": 1000,
            "units": "microns",
            "layers": {
                "1": [
                    {
                        "type": "waveguide",
                        "points": [[0, 0], [50, 0], [50, 30], [100, 30]],
                        "width": 0.5,
                        "properties": {"component": "input_waveguide"}
                    },
                    {
                        "type": "rectangle",
                        "x": 20,
                        "y": 40,
                        "width": 15,
                        "height": 10,
                        "properties": {"component": "mzi_1"}
                    }
                ],
                "2": [
                    {
                        "type": "waveguide",
                        "points": [[30, 60], [70, 60]],
                        "width": 0.8,
                        "properties": {"component": "oam_waveguide"}
                    }
                ]
            }
        }
        
        return demo_data

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='SpectraVortex photonic chip visualizer')
    parser.add_argument('input_file', nargs='?', 
                       help='GDSII JSON file (if not specified - creates demo)')
    parser.add_argument('-o', '--output', 
                       help='Output image filename')
    parser.add_argument('--demo', action='store_true',
                       help='Create demo visualization')
    
    args = parser.parse_args()
    
    visualizer = ChipVisualizer(scale=1.5)
    
    if args.demo or not args.input_file:
        print("🎨 Creating demo visualization...")
        gds_data = visualizer.create_simple_demo()
        output = args.output or 'demo_chip.png'
        visualizer.visualize(gds_data, output)
    elif args.input_file:
        gds_data = visualizer.load_gds_json(args.input_file)
        visualizer.visualize(gds_data, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
