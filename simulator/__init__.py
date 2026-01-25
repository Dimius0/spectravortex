"""
SpectraVortex Simulator
Photonic Computing Simulator with Matrix Support
"""

__version__ = "0.2.0"
__author__ = "SpectraVortex Team"
__license__ = "MIT"

# Import core simulator components
from .interpreter import Interpreter
from .matrix_ops import MatrixOperations

# TODO: Import these when they are implemented
# from .elements import OpticalElement
# from .fields import OpticalField
# from .simulator import PhotonicSimulator

__all__ = [
    "Interpreter",
    "MatrixOperations",
    # "OpticalElement", 
    # "OpticalField",
    # "PhotonicSimulator"
]


def hello():
    """Simple test function"""
    return f"SpectraVortex Simulator v{__version__}"


def get_version():
    """Get the current simulator version"""
    return __version__


def get_available_modules():
    """List available modules in the simulator"""
    modules = ["Interpreter", "MatrixOperations"]
    # Add more modules as they become available
    return modules
