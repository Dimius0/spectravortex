"""
GDSII Generator - Creates GDSII files for photonic chips
Industry-standard format for chip fabrication
"""

import struct
import numpy as np
from typing import List, Dict, Tuple, Any, BinaryIO
import math
import json
from datetime import datetime


class GDSIIGenerator:
    """Generate GDSII files for photonic integrated circuits"""
    
    # GDSII format constants
    HEADER = 0x0002
    BGNLIB = 0x0102
    LIBNAME = 0x0206
    UNITS = 0x0305
    BGNSTR = 0x0502
    STRNAME = 0x0606
    BOUNDARY = 0x0800
    PATH = 0x0900
    SREF = 0x0A00
    AREF = 0x0B00
    TEXT = 0x0C00
    ENDEL = 0x1100
    ENDSTR = 0x0700
    ENDLIB = 0x0400
    
    def __init__(self, technology):
        self.technology = technology
        self.data = bytearray()
        self.current_layer = 1
        self.current_datatype = 0
        self.scale = 1000  # 1μm = 1000 GDSII units
        
        # Layer mapping
        self.layer_map = {
            'waveguide': (1, 0),
            'heater': (10, 0),
            'metal': (11, 0),
            'via': (12, 0),
            'grating': (20, 0),
            'metasurface': (30, 0),
            'detector': (40, 0),
        }
        
        print(f"[GDSII] Generator initialized for {technology}")
    
    def _write_record(self, record_type: int, data: bytes = b'') -> None:
        """Write a GDSII record"""
        length = 4 + len(data)
        if length % 2 != 0:
            data += b'\0'  # Pad to even length
            length += 1
        
        self.data += struct.pack('>H', length)
        self.data += struct.pack('>H', record_type)
        self.data += data
    
    def _write_int16(self, value: int) -> bytes:
        """Write 16-bit integer in GDSII format"""
        return struct.pack('>h', value)
    
    def _write_int32(self, value: int) -> bytes:
        """Write 32-bit integer in GDSII format"""
        return struct.pack('>l', value)
    
    def _write_real8(self, value: float) -> bytes:
        """Write 8-byte real in GDSII format"""
        # Convert to GDSII real format
        if value == 0:
            return bytes([0] * 8)
        
        # Get sign and magnitude
        sign = 0 if value >= 0 else 0x80
        value = abs(value)
        
        # Normalize to scientific notation
        exponent = 0
        while value >= 1:
            value /= 16
            exponent += 1
        while value < 0.0625:  # 1/16
            value *= 16
            exponent -= 1
        
        # Convert to bytes
        mantissa = int(value * (1 << 56))
        result = bytearray([sign | (exponent + 64)])
        result += mantissa.to_bytes(7, 'big')
        
        return bytes(result)
    
    def set_layer(self, layer_name: str) -> None:
        """Set current layer for drawing"""
        if layer_name in self.layer_map:
            self.current_layer, self.current_datatype = self.layer_map[layer_name]
        else:
            print(f"[GDSII] Warning: Layer {layer_name} not found, using waveguide")
            self.current_layer, self.current_datatype = self.layer_map['waveguide']
    
    def add_waveguide(self, start: Tuple[float, float], end: Tuple[float, float], 
                     width: float = 0.5) -> None:
        """Add a waveguide segment"""
        print(f"[GDSII] Adding waveguide: {start} → {end}, width={width}μm")
        
        # Convert to GDSII units
        x1, y1 = int(start[0] * self.scale), int(start[1] * self.scale)
        x2, y2 = int(end[0] * self.scale), int(end[1] * self.scale)
        w = int(width * self.scale)
        
        # PATH record
        self._write_record(self.PATH)
        
        # Layer
        self._write_record(0x0D02, self._write_int16(self.current_layer))
        
        # Datatype
        self._write_record(0x0E02, self._write_int16(self.current_datatype))
        
        # Width
        self._write_record(0x0F03, self._write_int32(w))
        
        # XY coordinates
        xy_data = self._write_int32(x1) + self._write_int32(y1) + \
                  self._write_int32(x2) + self._write_int32(y2)
        self._write_record(0x1003, xy_data)
        
        # ENDEL
        self._write_record(self.ENDEL)
    
    def add_rectangle(self, position: Tuple[float, float], 
                     width: float, height: float) -> None:
        """Add a rectangle (for components)"""
        x, y = position
        x1 = int((x - width/2) * self.scale)
        y1 = int((y - height/2) * self.scale)
        x2 = int((x + width/2) * self.scale)
        y2 = int((y + height/2) * self.scale)
        
        print(f"[GDSII] Adding rectangle at ({x},{y}), {width}x{height}μm")
        
        # BOUNDARY record
        self._write_record(self.BOUNDARY)
        
        # Layer
        self._write_record(0x0D02, self._write_int16(self.current_layer))
        
        # Datatype
        self._write_record(0x0E02, self._write_int16(self.current_datatype))
        
        # XY coordinates (rectangle)
        xy_data = (
            self._write_int32(x1) + self._write_int32(y1) +
            self._write_int32(x2) + self._write_int32(y1) +
            self._write_int32(x2) + self._write_int32(y2) +
            self._write_int32(x1) + self._write_int32(y2) +
            self._write_int32(x1) + self._write_int32(y1)
        )
        self._write_record(0x1003, xy_data)
        
        # ENDEL
        self._write_record(self.ENDEL)
    
    def add_circle(self, center: Tuple[float, float], radius: float, 
                  num_points: int = 64) -> None:
        """Add a circle (for rounded components)"""
        cx, cy = center
        cx_gds = int(cx * self.scale)
        cy_gds = int(cy * self.scale)
        r_gds = int(radius * self.scale)
        
        print(f"[GDSII] Adding circle at ({cx},{cy}), radius={radius}μm")
        
        # Generate circle points
        xy_data = bytes()
        for i in range(num_points + 1):
            angle = 2 * math.pi * i / num_points
            x = cx_gds + int(r_gds * math.cos(angle))
            y = cy_gds + int(r_gds * math.sin(angle))
            xy_data += self._write_int32(x) + self._write_int32(y)
        
        # BOUNDARY record
        self._write_record(self.BOUNDARY)
        
        # Layer
        self._write_record(0x0D02, self._write_int16(self.current_layer))
        
        # Datatype
        self._write_record(0x0E02, self._write_int16(self.current_datatype))
        
        # XY coordinates
        self._write_record(0x1003, xy_data)
        
        # ENDEL
        self._write_record(self.ENDEL)
    
    def add_text_label(self, position: Tuple[float, float], text: str,
                      height: float = 10.0) -> None:
        """Add text label for component names"""
        x, y = position
        x_gds = int(x * self.scale)
        y_gds = int(y * self.scale)
        h_gds = int(height * self.scale)
        
        # TEXT record
        self._write_record(self.TEXT)
        
        # Layer
        self._write_record(0x0D02, self._write_int16(self.current_layer))
        
        # Text type (0 = normal)
        self._write_record(0x1602, b'\x00\x00')
        
        # Presentation (centered)
        self._write_record(0x1701, b'\x00')
        
        # Path type
        self._write_record(0x2102, b'\x00\x00')
        
        # Width
        self._write_record(0x0F03, self._write_int32(0))
        
        # XY position
        xy_data = self._write_int32(x_gds) + self._write_int32(y_gds)
        self._write_record(0x1003, xy_data)
        
        # String
        encoded = text.encode('ascii', 'replace') + b'\x00'
        self._write_record(0x1906, encoded)
        
        # ENDEL
        self._write_record(self.ENDEL)
    
    def add_component(self, component: Dict) -> None:
        """Add a component to GDSII"""
        comp_type = component.get('type', 'unknown')
        name = component.get('name', 'unnamed')
        position = component.get('position', (0, 0))
        
        print(f"[GDSII] Adding component: {name} ({comp_type}) at {position}")
        
        # Set layer based on component type
        if 'waveguide' in comp_type or 'mzi' in comp_type:
            self.set_layer('waveguide')
        elif 'heater' in comp_type or 'thermal' in comp_type:
            self.set_layer('heater')
        elif 'detector' in comp_type:
            self.set_layer('detector')
        elif 'metasurface' in comp_type or 'oam' in comp_type:
            self.set_layer('metasurface')
        else:
            self.set_layer('waveguide')
        
        # Draw component based on type
        if 'waveguide' in comp_type:
            # Draw as path
            if 'from' in component and 'to' in component:
                start = component['from']
                end = component['to']
                width = component.get('width', 0.5)
                self.add_waveguide(start, end, width)
        
        elif 'rectangle' in comp_type or 'mzi' in comp_type:
            # Draw as rectangle
            size = component.get('size', (10.0, 10.0))
            width, height = size
            self.add_rectangle(position, width, height)
            
            # Add text label
            self.set_layer('metal')  # Text on metal layer
            self.add_text_label(position, name, height=5.0)
        
        elif 'circle' in comp_type or 'oam_source' in comp_type:
            # Draw as circle
            diameter = component.get('diameter', 20.0)
            self.add_circle(position, diameter / 2)
            
            # Add OAM charge label
            if 'oam_charge' in component:
                label = f"OAM={component['oam_charge']}"
                self.set_layer('metal')
                text_pos = (position[0], position[1] + diameter/2 + 5)
                self.add_text_label(text_pos, label, height=3.0)
    
    def generate_from_design(self, designer) -> None:
        """Generate GDSII from ChipDesigner output"""
        print(f"[GDSII] Generating from design with {len(designer.layout)} items")
        
        # Add all layout items
        for item in designer.layout:
            self.add_component(item)
    
    def write_file(self, filename: str) -> None:
        """Write GDSII file to disk"""
        print(f"[GDSII] Writing GDSII file: {filename}")
        
        # Start library
        self._write_record(self.HEADER, self._write_int16(600))
        
        # BGNLIB
        now = datetime.now()
        mod_time = (now.year, now.month, now.day, now.hour, now.minute, now.second)
        create_time = mod_time
        self._write_record(self.BGNLIB, 
                          self._write_int16(create_time[0]) + self._write_int16(create_time[1]) +
                          self._write_int16(create_time[2]) + self._write_int16(create_time[3]) +
                          self._write_int16(create_time[4]) + self._write_int16(create_time[5]) +
                          self._write_int16(mod_time[0]) + self._write_int16(mod_time[1]) +
                          self._write_int16(mod_time[2]) + self._write_int16(mod_time[3]) +
                          self._write_int16(mod_time[4]) + self._write_int16(mod_time[5]))
        
        # LIBNAME
        lib_name = f"SPECTRAVORTEX_{self.technology}".ljust(32)[:32]
        self._write_record(self.LIBNAME, lib_name.encode('ascii') + b'\x00')
        
        # UNITS
        self._write_record(self.UNITS, 
                          self._write_real8(1e-9) +  # User units per meter
                          self._write_real8(1e-12))  # Database units per meter
        
        # Begin structure (main cell)
        self._write_record(self.BGNSTR,
                          self._write_int16(create_time[0]) + self._write_int16(create_time[1]) +
                          self._write_int16(create_time[2]) + self._write_int16(create_time[3]) +
                          self._write_int16(create_time[4]) + self._write_int16(create_time[5]) +
                          self._write_int16(mod_time[0]) + self._write_int16(mod_time[1]) +
                          self._write_int16(mod_time[2]) + self._write_int16(mod_time[3]) +
                          self._write_int16(mod_time[4]) + self._write_int16(mod_time[5]))
        
        # Structure name
        cell_name = "MAIN_CHIP".ljust(32)[:32]
        self._write_record(self.STRNAME, cell_name.encode('ascii') + b'\x00')
        
        # Write all the geometry data (already in self.data)
        
        # ENDSTR
        self._write_record(self.ENDSTR)
        
        # ENDLIB
        self._write_record(self.ENDLIB)
        
        # Write to file
        try:
            with open(filename, 'wb') as f:
                f.write(self.data)
            print(f"✅ GDSII file written successfully: {filename}")
            print(f"   File size: {len(self.data)} bytes")
        except Exception as e:
            print(f"❌ Error writing GDSII file: {e}")
    
    def generate_summary(self, designer) -> str:
        """Generate summary of GDSII generation"""
        summary = "\n" + "="*60 + "\n"
        summary += "GDSII GENERATION SUMMARY\n"
        summary += "="*60 + "\n\n"
        
        summary += f"Technology: {self.technology}\n"
        summary += f"Scale: 1μm = {self.scale} GDSII units\n"
        summary += f"Layers defined: {len(self.layer_map)}\n"
        
        # Count geometry elements
        num_waveguides = sum(1 for item in designer.layout if 'waveguide' in item.get('type', ''))
        num_components = len(designer.layout) - num_waveguides
        
        summary += f"\nGeometry Elements:\n"
        summary += f"  Components: {num_components}\n"
        summary += f"  Waveguides: {num_waveguides}\n"
        summary += f"  Total: {len(designer.layout)}\n"
        
        # Layer usage
        summary += f"\nLayer Usage:\n"
        layer_counts = {}
        for item in designer.layout:
            layer = item.get('layer', 'waveguide')
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
        for layer, count in layer_counts.items():
            summary += f"  {layer}: {count} elements\n"
        
        return summary


# Simple GDSII writer for testing (doesn't require full GDSII implementation)
class SimpleGDSIIWriter:
    """Simple GDSII writer for testing purposes"""
    
    def __init__(self, technology="silicon_photonic_220nm"):
        self.technology = technology
        self.elements = []
        print(f"[SimpleGDSII] Writer initialized for {technology}")
    
    def add_element(self, element_type: str, data: Dict) -> None:
        """Add design element"""
        self.elements.append({
            'type': element_type,
            'data': data,
            'technology': self.technology
        })
    
    def write(self, filename: str) -> bool:
        """Write simplified GDSII-like format (JSON for now)"""
        try:
            gds_data = {
                'format': 'SPECTRAVORTEX_GDSII_SIMPLIFIED',
                'version': '1.0',
                'technology': self.technology,
                'timestamp': datetime.now().isoformat(),
                'elements': self.elements,
                'units': 'micrometers',
                'scale': 1000
            }
            
            with open(filename, 'w') as f:
                json.dump(gds_data, f, indent=2)
            
            print(f"✅ Simplified GDSII written to: {filename}")
            print(f"   Elements: {len(self.elements)}")
            return True
            
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            return False


# Example usage
if __name__ == "__main__":
    print("GDSII Generator Module - Standalone Test")
    
    # Test simple writer
    writer = SimpleGDSIIWriter()
    writer.add_element('waveguide', {
        'from': (0, 0),
        'to': (100, 0),
        'width': 0.5
    })
    
    writer.write('test_chip.gds.json')
    print("✅ Test completed successfully")
