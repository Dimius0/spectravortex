"""
SpectraVortex Simulator v0.3.0+
Photonic Computing Simulator with Hybrid Solver Architecture
"""

__version__ = "0.3.0"  # Updated for hybrid architecture
__author__ = "SpectraVortex Team"
__license__ = "MIT"

# Import legacy core simulator components
from .interpreter import Interpreter
from .matrix_ops import MatrixOperations

# Import Hybrid Architecture components with graceful fallback
try:
    from .core.data_interface import FieldSolution
    HYBRID_DATA_AVAILABLE = True
except ImportError:
    HYBRID_DATA_AVAILABLE = False
    # Create placeholder for FieldSolution
    class FieldSolution:
        def __init__(self, *args, **kwargs):
            raise ImportError("FieldSolution requires core.data_interface module")

try:
    from .core.solver import Solver
    HYBRID_SOLVER_AVAILABLE = True
except ImportError:
    HYBRID_SOLVER_AVAILABLE = False
    # Create placeholder for Solver
    class Solver:
        def __init__(self, *args, **kwargs):
            raise ImportError("Solver requires core.solver module")

try:
    from .solvers.linear_wave_solver import LinearWaveSolver, create_linear_wave_solver
    LINEAR_WAVE_SOLVER_AVAILABLE = True
except ImportError:
    LINEAR_WAVE_SOLVER_AVAILABLE = False
    # Create placeholder for LinearWaveSolver
    class LinearWaveSolver:
        def __init__(self, *args, **kwargs):
            raise ImportError("LinearWaveSolver requires solvers.linear_wave_solver module")
    
    def create_linear_wave_solver(**kwargs):
        raise ImportError("create_linear_wave_solver requires LinearWaveSolver")

# Import OpticalSimulator (legacy interface, kept for backward compatibility)
try:
    from .optical_simulator import OpticalSimulator, create_simulator, simulate_circuit
    OPTICAL_SIMULATOR_AVAILABLE = True
except ImportError:
    OPTICAL_SIMULATOR_AVAILABLE = False
    # Create placeholders
    class OpticalSimulator:
        def __init__(self, *args, **kwargs):
            raise ImportError("OpticalSimulator not available")
    
    def create_simulator(**kwargs):
        raise ImportError("create_simulator requires OpticalSimulator")
    
    def simulate_circuit(**kwargs):
        raise ImportError("simulate_circuit requires OpticalSimulator")

# Calculate overall hybrid architecture availability
HYBRID_ARCHITECTURE_AVAILABLE = (
    HYBRID_DATA_AVAILABLE and 
    HYBRID_SOLVER_AVAILABLE and 
    LINEAR_WAVE_SOLVER_AVAILABLE
)

__all__ = [
    # Legacy exports (always available)
    "Interpreter",
    "MatrixOperations",
    
    # OpticalSimulator (backward compatibility)
    "OpticalSimulator",
    "create_simulator",
    "simulate_circuit",
    
    # Hybrid Architecture exports (conditional)
    "FieldSolution",
    "Solver",
    "LinearWaveSolver",
    "create_linear_wave_solver",
    
    # Availability flags
    "HYBRID_ARCHITECTURE_AVAILABLE",
    "HYBRID_DATA_AVAILABLE",
    "HYBRID_SOLVER_AVAILABLE",
    "LINEAR_WAVE_SOLVER_AVAILABLE",
    "OPTICAL_SIMULATOR_AVAILABLE",
]


def hello() -> str:
    """
    Get a welcome message with architecture status.
    
    Returns:
        Welcome message string with version and architecture info
    """
    base_message = f"SpectraVortex Simulator v{__version__}"
    
    if HYBRID_ARCHITECTURE_AVAILABLE:
        return f"{base_message} with Hybrid Solver Architecture ✓"
    elif HYBRID_DATA_AVAILABLE or HYBRID_SOLVER_AVAILABLE:
        # Partial hybrid architecture
        parts = []
        if HYBRID_DATA_AVAILABLE:
            parts.append("FieldSolution")
        if HYBRID_SOLVER_AVAILABLE:
            parts.append("Solver interface")
        if LINEAR_WAVE_SOLVER_AVAILABLE:
            parts.append("LinearWaveSolver")
        
        return f"{base_message} with partial Hybrid Architecture ({', '.join(parts)})"
    else:
        return f"{base_message} (legacy mode)"


def get_version() -> str:
    """
    Get the current simulator version.
    
    Returns:
        Version string
    """
    return __version__


def get_available_modules() -> list:
    """
    List all available modules in the simulator.
    
    Returns:
        List of available module names
    """
    modules = ["Interpreter", "MatrixOperations"]
    
    if OPTICAL_SIMULATOR_AVAILABLE:
        modules.append("OpticalSimulator")
    
    if HYBRID_DATA_AVAILABLE:
        modules.append("FieldSolution")
    
    if HYBRID_SOLVER_AVAILABLE:
        modules.append("Solver")
    
    if LINEAR_WAVE_SOLVER_AVAILABLE:
        modules.append("LinearWaveSolver")
    
    return modules


def get_architecture_status() -> dict:
    """
    Get detailed architecture status report.
    
    Returns:
        Dictionary with architecture status information
    """
    return {
        "version": __version__,
        "full_hybrid_architecture": HYBRID_ARCHITECTURE_AVAILABLE,
        "modules": {
            "data_interface": HYBRID_DATA_AVAILABLE,
            "solver_interface": HYBRID_SOLVER_AVAILABLE,
            "linear_wave_solver": LINEAR_WAVE_SOLVER_AVAILABLE,
            "optical_simulator": OPTICAL_SIMULATOR_AVAILABLE,
        },
        "available_solvers": ["LinearWaveSolver"] if LINEAR_WAVE_SOLVER_AVAILABLE else [],
        "available_modules": get_available_modules(),
        "recommendations": _get_architecture_recommendations(),
    }


def _get_architecture_recommendations() -> list:
    """
    Get recommendations for architecture improvements.
    
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    if not HYBRID_DATA_AVAILABLE:
        recommendations.append("Install core.data_interface for FieldSolution support")
    
    if not HYBRID_SOLVER_AVAILABLE:
        recommendations.append("Install core.solver for abstract solver interface")
    
    if not LINEAR_WAVE_SOLVER_AVAILABLE:
        recommendations.append("Install solvers.linear_wave_solver for linear wave solving")
    
    if HYBRID_ARCHITECTURE_AVAILABLE:
        recommendations.append("Hybrid architecture ready! Consider implementing SolverManager")
    
    return recommendations


def check_module(module_name: str) -> dict:
    """
    Check availability of a specific module.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        Dictionary with module status
    """
    module_status = {
        "available": False,
        "name": module_name,
        "message": "",
    }
    
    if module_name == "Interpreter":
        module_status["available"] = True
        module_status["message"] = "Core interpreter module available"
    
    elif module_name == "MatrixOperations":
        module_status["available"] = True
        module_status["message"] = "Matrix operations module available"
    
    elif module_name == "OpticalSimulator":
        module_status["available"] = OPTICAL_SIMULATOR_AVAILABLE
        module_status["message"] = "Legacy optical simulator" if OPTICAL_SIMULATOR_AVAILABLE else "Not available"
    
    elif module_name == "FieldSolution":
        module_status["available"] = HYBRID_DATA_AVAILABLE
        module_status["message"] = "Hybrid data interface" if HYBRID_DATA_AVAILABLE else "Requires core.data_interface"
    
    elif module_name == "Solver":
        module_status["available"] = HYBRID_SOLVER_AVAILABLE
        module_status["message"] = "Abstract solver interface" if HYBRID_SOLVER_AVAILABLE else "Requires core.solver"
    
    elif module_name == "LinearWaveSolver":
        module_status["available"] = LINEAR_WAVE_SOLVER_AVAILABLE
        module_status["message"] = "Linear wave solver" if LINEAR_WAVE_SOLVER_AVAILABLE else "Requires solvers.linear_wave_solver"
    
    else:
        module_status["message"] = f"Unknown module: {module_name}"
    
    return module_status


def test_imports() -> dict:
    """
    Test imports of all modules.
    
    Returns:
        Dictionary with import test results
    """
    results = {
        "success": True,
        "modules": {},
        "errors": [],
    }
    
    # Test legacy modules
    try:
        from .interpreter import Interpreter
        results["modules"]["Interpreter"] = {"status": "OK", "version": "unknown"}
    except ImportError as e:
        results["success"] = False
        results["modules"]["Interpreter"] = {"status": "FAILED", "error": str(e)}
        results["errors"].append(f"Interpreter: {e}")
    
    try:
        from .matrix_ops import MatrixOperations
        results["modules"]["MatrixOperations"] = {"status": "OK", "version": "unknown"}
    except ImportError as e:
        results["success"] = False
        results["modules"]["MatrixOperations"] = {"status": "FAILED", "error": str(e)}
        results["errors"].append(f"MatrixOperations: {e}")
    
    # Test hybrid architecture modules
    if HYBRID_DATA_AVAILABLE:
        results["modules"]["FieldSolution"] = {"status": "OK", "type": "data_interface"}
    
    if HYBRID_SOLVER_AVAILABLE:
        results["modules"]["Solver"] = {"status": "OK", "type": "abstract_interface"}
    
    if LINEAR_WAVE_SOLVER_AVAILABLE:
        results["modules"]["LinearWaveSolver"] = {"status": "OK", "type": "concrete_solver"}
    
    if OPTICAL_SIMULATOR_AVAILABLE:
        results["modules"]["OpticalSimulator"] = {"status": "OK", "type": "legacy_simulator"}
    
    return results


# Quick demonstration when module is run directly
if __name__ == "__main__":
    print("=" * 60)
    print(hello())
    print("=" * 60)
    
    status = get_architecture_status()
    
    print(f"\nArchitecture Status:")
    print(f"  Version: {status['version']}")
    print(f"  Full Hybrid Architecture: {'✓' if status['full_hybrid_architecture'] else '✗'}")
    
    print(f"\nModule Status:")
    for module, available in status['modules'].items():
        print(f"  {module}: {'✓' if available else '✗'}")
    
    print(f"\nAvailable Modules ({len(status['available_modules'])}):")
    for i, module in enumerate(status['available_modules'], 1):
        print(f"  {i:2d}. {module}")
    
    if status['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(status['recommendations'], 1):
            print(f"  {i:2d}. {rec}")
    
    print("\n" + "=" * 60)
