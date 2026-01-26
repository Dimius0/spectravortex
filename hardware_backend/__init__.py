"""
Hardware Backend for SpectraVortex
From high-level code to photonic chips
Version 0.1.0 - Full hardware compilation stack
"""

# Core designer
from .chip_designer import ChipDesigner, DesignMetrics

# Component library
from .component_library import (
    Waveguide,
    MZIInterferometer, 
    OAMModeConverter,
    DirectionalCoupler,
    Photodetector,
    connect,
    calculate_total_loss
)

# GDSII generators
from .gdsii_generator import GDSIIGenerator, SimpleGDSIIWriter

# Technology kits
from .technology_kits.silicon_photonic_220nm import TECH_220NM, SiliconPhotonic220nm

__version__ = "0.1.0"
__author__ = "SpectraVortex Team"
__license__ = "MIT"

__all__ = [
    # Core
    'ChipDesigner',
    'DesignMetrics',
    
    # Components
    'Waveguide',
    'MZIInterferometer',
    'OAMModeConverter', 
    'DirectionalCoupler',
    'Photodetector',
    'connect',
    'calculate_total_loss',
    
    # GDSII
    'GDSIIGenerator',
    'SimpleGDSIIWriter',
    
    # Technology
    'TECH_220NM',
    'SiliconPhotonic220nm',
]


def hello():
    """Welcome message"""
    return f"SpectraVortex Hardware Backend v{__version__} - From Code to Silicon"


def get_capabilities():
    """Get hardware backend capabilities"""
    return {
        "version": __version__,
        "components": [
            "Waveguide",
            "MZIInterferometer", 
            "OAMModeConverter",
            "DirectionalCoupler",
            "Photodetector"
        ],
        "technologies": ["silicon_photonic_220nm"],
        "output_formats": ["GDSII", "JSON"],
        "features": [
            "Chip design from AST",
            "Design rule checking",
            "Component placement",
            "Waveguide routing",
            "Metrics calculation"
        ]
    }


# Test function
def test_hardware_backend():
    """Test hardware backend installation"""
    print("=" * 60)
    print("Testing SpectraVortex Hardware Backend")
    print("=" * 60)
    
    try:
        # Test imports
        from .chip_designer import ChipDesigner
        from .component_library import Waveguide
        from .technology_kits.silicon_photonic_220nm import TECH_220NM
        
        print("✅ All modules imported successfully")
        print(f"✅ Version: {__version__}")
        print(f"✅ Technology available: {TECH_220NM.name}")
        
        # Test basic functionality
        wg = Waveguide(length=100.0, width=0.5)
        print(f"✅ Waveguide created: {wg.get_path()}")
        print(f"✅ Waveguide loss: {wg.calculate_loss():.2f} dB")
        
        designer = ChipDesigner()
        print(f"✅ ChipDesigner initialized")
        
        print("\n✅ Hardware backend test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Hardware backend test FAILED: {e}")
        return False
