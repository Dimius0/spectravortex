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
        rotation: float = 0.0,
        properties: Optional[Dict] = None
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
            properties: Optional component properties dictionary
        """
        # Convert to database units
        x_gds = int(x * self.scale)
        y_gds = int(y * self.scale)

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

        if properties is not None:
            text_record["properties"] = properties

        if layer not in self.layers:
            self.layers[layer] = []
        self.layers[layer].append(text_record)

    def add_rectangle(
        self,
        layer: int,
        x: float,
        y: float,
        width: float,
        height: float,
        datatype: int = 0,
        properties: Optional[Dict] = None
    ) -> None:
        """
        Add a rectangle to GDSII layout.

        Args:
            layer: GDSII layer number
            x, y: Bottom-left corner position in microns
            width: Rectangle width in microns
            height: Rectangle height in microns
            datatype: GDSII datatype
            properties: Optional component properties dictionary
        """
        # Convert to database units
        x_gds = int(x * self.scale)
        y_gds = int(y * self.scale)
        width_gds = int(width * self.scale)
        height_gds = int(height * self.scale)

        rect_record = {
            "type": "rectangle",
            "layer": layer,
            "datatype": datatype,
            "x": x_gds,
            "y": y_gds,
            "width": width_gds,
            "height": height_gds
        }

        if properties is not None:
            rect_record["properties"] = properties

        if layer not in self.layers:
            self.layers[layer] = []
        self.layers[layer].append(rect_record)

    def add_polygon(
        self,
        layer: int,
        points: List[Tuple[float, float]],
        datatype: int = 0,
        properties: Optional[Dict] = None
    ) -> None:
        """
        Add a polygon to GDSII layout.

        Args:
            layer: GDSII layer number
            points: List of (x, y) coordinates in microns
            datatype: GDSII datatype
            properties: Optional component properties dictionary
        """
        # Convert to database units
        points_gds = [(int(x * self.scale), int(y * self.scale)) for x, y in points]

        polygon_record = {
            "type": "polygon",
            "layer": layer,
            "datatype": datatype,
            "points": points_gds
        }

        if properties is not None:
            polygon_record["properties"] = properties

        if layer not in self.layers:
            self.layers[layer] = []
        self.layers[layer].append(polygon_record)

    def add_path(
        self,
        layer: int,
        points: List[Tuple[float, float]],
        width: float,
        datatype: int = 0,
        properties: Optional[Dict] = None
    ) -> None:
        """
        Add a path (waveguide) to GDSII layout.

        Args:
            layer: GDSII layer number
            points: List of (x, y) coordinates in microns
            width: Path width in microns
            datatype: GDSII datatype
            properties: Optional component properties dictionary
        """
        # Convert to database units
        points_gds = [(int(x * self.scale), int(y * self.scale)) for x, y in points]
        width_gds = int(width * self.scale)

        path_record = {
            "type": "path",
            "layer": layer,
            "datatype": datatype,
            "points": points_gds,
            "width": width_gds
        }

        if properties is not None:
            path_record["properties"] = properties

        if layer not in self.layers:
            self.layers[layer] = []
        self.layers[layer].append(path_record)
    def add_circle(
        self,
        layer: int,
        center_x: float,
        center_y: float,
        radius: float,
        datatype: int = 0,
        vertices: int = 64,
        properties: Optional[Dict] = None
    ) -> None:
        """
        Add a circle (approximated as polygon) to GDSII layout.

        Args:
            layer: GDSII layer number
            center_x, center_y: Circle center in microns
            radius: Circle radius in microns
            datatype: GDSII datatype
            vertices: Number of vertices to approximate circle
            properties: Optional component properties dictionary
        """
        points = []
        for i in range(vertices):
            angle = 2 * math.pi * i / vertices
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))

        self.add_polygon(layer, points, datatype, properties)

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

    def to_dict(self) -> Dict:
        """
        Convert GDSII data to dictionary.
        Used by chip_designer.export_to_gds() for compatibility.
        """
        return {
            "format": "GDSII_JSON",
            "version": "1.0",
            "scale": self.scale,
            "units": "microns",
            "layers": self.layers,
            "structures": self.structures
        }

    def save(self, filename: str) -> None:
        """Save GDSII data to JSON file."""
        with open(filename, 'w') as f:
            f.write(self.to_json())
        print(f"✅ GDSII JSON saved to {filename}")