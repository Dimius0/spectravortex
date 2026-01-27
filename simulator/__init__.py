"""
SpectraVortex Simulator v0.3.0+
Photonic Computing Simulator with Hybrid Solver Architecture
"""

__version__ = "0.3.0"  # Updated for hybrid architecture
__author__ = "SpectraVortex Team"
__license__ = "MIT"

# ============================================================================
# 1. IMPORT LEGACY CORE SIMULATOR COMPONENTS
# ============================================================================
from .interpreter import Interpreter
from .matrix_ops import MatrixOperations

# ============================================================================
# 2. IMPORT HYBRID ARCHITECTURE COMPONENTS WITH GRACEFUL FALLBACK
# ============================================================================

# FieldSolution from data interface
try:
    from .core.data_interface import FieldSolution
    HYBRID_DATA_AVAILABLE = True
except ImportError:
    HYBRID_DATA_AVAILABLE = False
    # Create placeholder for FieldSolution
    class FieldSolution:
        def __init__(self, *args, **kwargs):
            raise ImportError("FieldSolution requires core.data_interface module")

# Abstract Solver interface
try:
    from .core.solver import Solver
    HYBRID_SOLVER_AVAILABLE = True
except ImportError:
    HYBRID_SOLVER_AVAILABLE = False
    # Create placeholder for Solver
    class Solver:
        def __init__(self, *args, **kwargs):
            raise ImportError("Solver requires core.solver module")

# LinearWaveSolver concrete implementation
try:
    from .solvers.linear_wave_solver import LinearWaveSolver, create_linear_wave_solver
    LINEAR_WAVE_SOLVER_AVAILABLE = True
except ImportError:
    LINEAR_WAVE_SOLVER_AVAILABLE = False
    # Create placeholders
    class LinearWaveSolver:
        def __init__(self, *args, **kwargs):
            raise ImportError("LinearWaveSolver requires solvers.linear_wave_solver module")
    
    def create_linear_wave_solver(**kwargs):
        raise ImportError("create_linear_wave_solver requires LinearWaveSolver")

# OpticalSimulator (legacy interface, kept for backward compatibility)
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

# ============================================================================
# 3. IMPORT SOLVER MANAGER (PHASE 2 CORE COMPONENT)
# ============================================================================
try:
    from .core.solver_manager import (
        SolverManager, 
        SolverSelection, 
        HybridProblemPart,
        create_solver_manager
    )
    SOLVER_MANAGER_AVAILABLE = True
except ImportError:
    SOLVER_MANAGER_AVAILABLE = False
    # Create placeholders for SolverManager components
    class SolverManager:
        def __init__(self, *args, **kwargs):
            raise ImportError("SolverManager requires core.solver_manager module")
    
    class SolverSelection:
        def __init__(self, *args, **kwargs):
            raise ImportError("SolverSelection requires core.solver_manager module")
    
    class HybridProblemPart:
        def __init__(self, *args, **kwargs):
            raise ImportError("HybridProblemPart requires core.solver_manager module")
    
    def create_solver_manager(**kwargs):
        raise ImportError("create_solver_manager requires SolverManager")

# ============================================================================
# 4. CALCULATE ARCHITECTURE AVAILABILITY
# ============================================================================
# Full hybrid architecture requires all core components
HYBRID_ARCHITECTURE_AVAILABLE = (
    HYBRID_DATA_AVAILABLE and
    HYBRID_SOLVER_AVAILABLE and
    LINEAR_WAVE_SOLVER_AVAILABLE and
    SOLVER_MANAGER_AVAILABLE
)

# ============================================================================
# 5. EXPORT LIST - ALL PUBLICLY AVAILABLE SYMBOLS
# ============================================================================
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
    
    # SolverManager exports (Phase 2)
    "SolverManager",
    "SolverSelection",
    "HybridProblemPart",
    "create_solver_manager",
    
    # Availability flags
    "HYBRID_ARCHITECTURE_AVAILABLE",
    "HYBRID_DATA_AVAILABLE",
    "HYBRID_SOLVER_AVAILABLE",
    "LINEAR_WAVE_SOLVER_AVAILABLE",
    "OPTICAL_SIMULATOR_AVAILABLE",
    "SOLVER_MANAGER_AVAILABLE",
]

# ============================================================================
# 6. GLOBAL SOLVER MANAGER INSTANCE (SINGLETON PATTERN)
# ============================================================================
_global_solver_manager = None

def get_solver_manager() -> SolverManager:
    """
    Get or create the global SolverManager instance.
    
    Returns:
        SolverManager: Global instance with default solvers registered
        
    Raises:
        ImportError: If SolverManager is not available
    """
    global _global_solver_manager
    
    if not SOLVER_MANAGER_AVAILABLE:
        raise ImportError(
            "SolverManager is not available. "
            "Check that core.solver_manager module is installed."
        )
    
    if _global_solver_manager is None:
        _global_solver_manager = create_solver_manager(enable_auto_selection=True)
    
    return _global_solver_manager

def reset_solver_manager() -> None:
    """
    Reset the global SolverManager instance.
    Useful for testing or reconfiguration.
    """
    global _global_solver_manager
    _global_solver_manager = None

# ============================================================================
# 7. UTILITY FUNCTIONS
# ============================================================================
def hello() -> str:
    """
    Get a welcome message with architecture status.
    
    Returns:
        Welcome message string with version and architecture info
    """
    base_message = f"SpectraVortex Simulator v{__version__}"
    
    if HYBRID_ARCHITECTURE_AVAILABLE and SOLVER_MANAGER_AVAILABLE:
        return f"{base_message} with Hybrid Solver Architecture ✓ (SolverManager ready)"
    elif HYBRID_ARCHITECTURE_AVAILABLE:
        return f"{base_message} with Hybrid Solver Architecture ✓"
    elif HYBRID_DATA_AVAILABLE or HYBRID_SOLVER_AVAILABLE or LINEAR_WAVE_SOLVER_AVAILABLE:
        # Partial hybrid architecture
        parts = []
        if HYBRID_DATA_AVAILABLE:
            parts.append("FieldSolution")
        if HYBRID_SOLVER_AVAILABLE:
            parts.append("Solver interface")
        if LINEAR_WAVE_SOLVER_AVAILABLE:
            parts.append("LinearWaveSolver")
        if SOLVER_MANAGER_AVAILABLE:
            parts.append("SolverManager")
        
        parts_str = ", ".join(parts)
        return f"{base_message} with partial Hybrid Architecture ({parts_str})"
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
    
    if SOLVER_MANAGER_AVAILABLE:
        modules.append("SolverManager")
    
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
            "solver_manager": SOLVER_MANAGER_AVAILABLE,
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
    
    if not SOLVER_MANAGER_AVAILABLE:
        recommendations.append("Install core.solver_manager for automatic solver coordination")
    
    if HYBRID_ARCHITECTURE_AVAILABLE and SOLVER_MANAGER_AVAILABLE:
        recommendations.append("Hybrid architecture ready! Consider implementing additional solvers")
    
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
    
    elif module_name == "SolverManager":
        module_status["available"] = SOLVER_MANAGER_AVAILABLE
        module_status["message"] = "Solver coordination manager" if SOLVER_MANAGER_AVAILABLE else "Requires core.solver_manager"
    
    else:
        module_status["message"] = f"Unknown module: {module_name}"
    
    return module_status

def test_imports() -> dict:
    """
    Test imports of all modules.
    
    Returns:
        Dictionary with import test results
    """
    import importlib
    
    results = {
        "success": True,
        "modules": {},
        "errors": [],
    }
    
    # Test legacy modules using importlib to avoid unused imports
    # Test Interpreter
    try:
        importlib.import_module('simulator.interpreter', 'simulator')
        results["modules"]["Interpreter"] = {"status": "OK", "version": "unknown"}
    except ImportError as e:
        results["success"] = False
        results["modules"]["Interpreter"] = {"status": "FAILED", "error": str(e)}
        results["errors"].append(f"Interpreter: {e}")
    
    # Test MatrixOperations
    try:
        importlib.import_module('simulator.matrix_ops', 'simulator')
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
    
    if SOLVER_MANAGER_AVAILABLE:
        results["modules"]["SolverManager"] = {"status": "OK", "type": "coordinator"}
    
    return results

# ============================================================================
# 8. QUICK DEMONSTRATION WHEN MODULE IS RUN DIRECTLY
# ============================================================================
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
    
    # Test SolverManager if available
    if SOLVER_MANAGER_AVAILABLE:
        try:
            manager = get_solver_manager()
            available = manager.get_available_solvers()
            print(f"\nSolverManager Status:")
            print(f"  Registered solvers: {len(available)}")
            for solver_id, info in available.items():
                print(f"    - {info['name']}: {info.get('success_rate', 0):.0%} success rate")
        except Exception as e:
            print(f"\nSolverManager test error: {e}")
    
    print("\n" + "=" * 60)
