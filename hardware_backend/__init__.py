"""
SpectraVortex Hardware Backend
Photonic Integrated Circuit (PIC) design and GDSII generation.
"""

__version__ = "0.1.0"
__all__ = [
    "Waveguide",
    "MZIInterferometer", 
    "OAMModeConverter",
    "PhotonicComponent",
    "ChipDesigner",
    "TECH_220NM",
    "SiliconPhotonic220nm",
    "GDSIIGenerator",
    "ChipVisualizer",
    "AutoRouter",  # NEW: AutoRouter
]

# Core components
from .component_library import (
    Waveguide,
    MZIInterferometer,
    OAMModeConverter,
    PhotonicComponent,
)

# Chip design
from .chip_designer import ChipDesigner

# Technology kits
from .technology_kits.silicon_photonic_220nm import TECH_220NM, SiliconPhotonic220nm

# GDSII generation
from .gdsii_generator import GDSIIGenerator

# Chip visualization
from .visualize_chip import ChipVisualizer 
# Auto routing
from .auto_router import AutoRouter # NEW IMPORT

# Demo and examples
if __name__ == "__main__":
    print("=" * 60)
    print("SpectraVortex Hardware Backend Demo")
    print("=" * 60)
    
    # 1. Waveguide demo
    print("\n1. Testing Waveguide component...")
    wg = Waveguide(length=100.0, width=0.5)
    print(f"   Created: {wg.get_path()}")
    print(f"   Loss: {wg.calculate_loss():.2f} dB")
    
    # 2. MZI demo
    print("\n2. Testing MZI Interferometer...")
    mzi = MZIInterferometer(coupling_ratio=0.5, phase_shift=0.785)
    matrix = mzi.get_transfer_matrix()
    print(f"   Transfer matrix shape: {matrix.shape}")
    print(f"   Coupling ratio: {mzi.coupling_ratio}")
    
    # 3. OAM converter demo
    print("\n3. Testing OAM Mode Converter...")
    oam = OAMModeConverter(target_oam=2, efficiency=0.85)
    pattern = oam.generate_phase_pattern()
    print(f"   Target OAM: {oam.target_oam}")
    print(f"   Efficiency: {oam.efficiency * 100:.1f}%")
    
    # 4. ChipDesigner demo
    print("\n4. Testing ChipDesigner...")
    designer = ChipDesigner(technology="silicon_photonic_220nm")
    print(f"   Technology: {designer.technology}")
    
    # Show technology rules
    if hasattr(designer, 'tech_kit') and designer.tech_kit:
        rules = designer.tech_kit.rules
        print(f"   Min waveguide width: {rules.get('min_width', 'N/A')}μm")
        print(f"   Min bend radius: {rules.get('min_bend_radius', 'N/A')}μm")
    
    # Generate tech report
    if hasattr(designer, 'generate_tech_report'):
        tech_report = designer.generate_tech_report()
        if len(tech_report) > 100:
            print(f"   Tech report preview: {tech_report[:97]}...")
        else:
            print(f"   Tech report: {tech_report}")
    
    # 5. GDSII generator demo
    print("\n5. Testing GDSII Generator...")
    gds = GDSIIGenerator()
    print(f"   Scale: {gds.scale} database units per micron")
    print(f"   Layer count: {len(gds.layers)}")
    
    # Add test geometry
    gds.add_rectangle(layer=1, x=0, y=0, width=10, height=5)
    print(f"   Added rectangle to layer 1")
    
    # 6. ChipVisualizer demo (NEW)
    print("\n6. Testing Chip Visualizer...")
    try:
        visualizer = ChipVisualizer()
        print(f"   Visualizer initialized successfully")
        print(f"   Supported colors: {len(visualizer.COLORS)} component types")
        
        # Create and visualize demo
        demo_data = visualizer.create_simple_demo()
        print(f"   Created demo with {len(demo_data['layers'])} layers")
        
        # Try to save visualization
        import tempfile
        import os
        temp_file = os.path.join(tempfile.gettempdir(), "demo_visualization.png")
        visualizer.visualize(demo_data, temp_file)
        print(f"   Demo visualization saved to temporary file")
        
    except ImportError as e:
        print(f"   ⚠️  Visualizer dependencies missing: {e}")
        print("   Install with: pip install matplotlib")
    except Exception as e:
        print(f"   ⚠️  Visualizer test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All components initialized successfully!")
    print("=" * 60)
