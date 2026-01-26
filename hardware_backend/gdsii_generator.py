"""
GDSII file generator for photonic integrated circuits.
"""

import json
from typing import Dict, List, Tuple, Any, Optional
import math

class GDSIIGenerator:
    """Generate GDSII files (JSON format) for photonic chips."""
    
    def __init__(self, scale: int = 1000):
        """
        Initialize GDSII generator.
        
        Args:
            scale: Database units per micron (default: 1000 = 1nm precision)
        """
        self.scale = scale
        self.layers = {}
        self.structures = []
        self.current_layer = 0
        self.current_datatype = 0
        
    def add_text(
        self,
        text: str,
        x: float,
        y: float,
        layer: int = 0,
        datatype: int = 0,
        magnification: float = 1.0,
        rotation: float = 0.0
    ) -> None:
        """
        Add text annotation to GDSII.
        
        Args:
            text: Text string
            x, y: Position in microns
            layer: GDSII layer number
            datatype: GDSII datatype
            magnification: Text size scaling
            rotation: Text rotation in degrees
        """
        # Convert to database units
        x_gds = int(x * self.scale)
        y_gds = int(y * self.scale)
        # height_gds не используется в текущей реализации, поэтому не сохраняем
        
        text_record = {
            "type": "text",
            "layer": layer,
            "datatype": datatype,
            "text": text,
            "x": x_gds,
            "y": y_gds,
            "magnification": magnification,
            "rotation": rotation
        }
        
        if layer not in self.layers:
            self.layers[layer] = []
        self.layers[layer].append(text_record)
    
    # ... остальные методы остаются без изменений ...
    
    def to_json(self, indent: int = 2) -> str:
        """Convert GDSII data to JSON string."""
        output = {
            "format": "GDSII_JSON",
            "version": "1.0",
            "scale": self.scale,
            "units": "microns",
            "layers": self.layers,
            "structures": self.structures
        }
        return json.dumps(output, indent=indent)
    
    def save(self, filename: str) -> None:
        """Save GDSII data to JSON file."""
        with open(filename, 'w') as f:
            f.write(self.to_json())
        print(f"✅ GDSII JSON saved to {filename}")
