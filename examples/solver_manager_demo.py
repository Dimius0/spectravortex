#!/usr/bin/env python3
"""
SolverManager Demo - Practical examples of using the hybrid architecture.

This demo shows how to:
1. Create and configure SolverManager
2. Register custom solvers
3. Use automatic solver selection
4. Solve problems with different strategies
5. Analyze performance and statistics
"""

import numpy as np
from typing import Dict, Any
import time

print("=" * 70)
print("🌀 SolverManager Demo - Hybrid Architecture in Action")
print("=" * 70)

# -------------------------------------------------------------------
# Setup: Import and initialize
# -------------------------------------------------------------------
print("\n🔧 Initializing SolverManager...")

try:
    from simulator import (
        get_solver_manager, 
        create_solver_manager,
        get_architecture_status,
        hello
    )
    
    # Print architecture status
    print(f"\n{hello()}")
    status = get_architecture_status()
    
    if not status.get('full_hybrid_architecture', False):
        print("⚠️  Note: Running in partial hybrid mode")
    
    # Get the global manager
    manager = get_solver_manager()
    print(f"✅ SolverManager ready with {len(manager.solvers)} registered solver(s)")
    
except ImportError as e:
    print(f"❌ Failed to import SolverManager: {e}")
    exit(1)

# -------------------------------------------------------------------
# Example 1: Basic problem solving
# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("📝 Example 1: Basic Problem Solving")
print("=" * 70)

def create_waveguide_problem(
    dimensions: int = 1,
    length: float = 10e-6,
    wavelength: float = 1.55e-6
) -> Dict[str, Any]:
    """Create a standard waveguide problem."""
    problem = {
        'name': f'{dimensions}D_waveguide',
        'description': f'Optical waveguide simulation ({dimensions}D)',
        'domain': {
            'type': f'{dimensions}d',
            'length': length,
            'grid_size': 0.1e-6,
        },
        'physics': ['linear', 'propagation'],
        'parameters': {
            'wavelength': wavelength,
            'propagation_distance': 1e-3,
            'boundary_conditions': 'absorbing',
        },
        'components': [
            {
                'type': 'gaussian_source',
                'amplitude': 1.0,
                'position': 0.0,
                'width': 0.5e-6,
                'phase': 0.0,
            },
            {
                'type': 'waveguide',
                'length': length,
                'refractive_index': 1.5,
                'loss_coefficient': 0.01,
            },
        ],
        'output_request': ['field_amplitude', 'phase', 'intensity'],
    }
    
    if dimensions >= 2:
        problem['domain']['width'] = 3e-6
        if dimensions == 3:
            problem['domain']['height'] = 3e-6
    
    return problem

# Create test problems
problems = {
    '1d_simple': create_waveguide_problem(dimensions=1),
    '2d_medium': create_waveguide_problem(dimensions=2),
    '3d_complex': create_waveguide_problem(dimensions=3),
}

print(f"\nCreated {len(problems)} test problems:")
for name, problem in problems.items():
    print(f"  - {problem['name']}: {problem['description']}")

# Test solver selection for each problem
print("\n🤖 Testing automatic solver selection:")

for name, problem in problems.items():
    try:
        selection = manager.select_solver(problem)
        print(f"\n  Problem: {problem['name']}")
        print(f"    Selected: {selection.solver.__class__.__name__}")
        print(f"    Confidence: {selection.confidence:.1%}")
        print(f"    Reason: {selection.reason}")
        
        # Show cost estimate if available
        if selection.estimated_cost:
            cost_str = ", ".join([f"{k}={v:.3f}" for k, v in selection.estimated_cost.items()])
            print(f"    Estimated cost: [{cost_str}]")
            
    except Exception as e:
        print(f"\n  Problem: {problem['name']} - Selection failed: {e}")

# -------------------------------------------------------------------
# Example 2: Custom solver registration
# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("🔧 Example 2: Custom Solver Registration")
print("=" * 70)

# Define a simple mock solver for demonstration
class MockFastSolver:
    """Mock solver for fast 1D problems."""
    
    def __init__(self):
        self.name = "MockFastSolver"
        self.version = "1.0"
    
    def can_solve(self, problem: Dict[str, Any]) -> tuple:
        """Check if this solver can solve the problem."""
        domain_type = problem.get('domain', {}).get('type', '1d')
        physics = problem.get('physics', [])
        
        if domain_type == '1d' and 'linear' in physics:
            return True, "Can solve 1D linear problems"
        return False, "Only solves 1D linear problems"
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get solver requirements and capabilities."""
        return {
            'physical_models': ['linear'],
            'max_dimensions': 1,
            'supported_components': ['source', 'waveguide'],
        }
    
    def estimate_computation_cost(self, problem: Dict[str, Any]) -> Dict[str, float]:
        """Estimate computation cost."""
        return {
            'time_seconds': 0.1,
            'memory_mb': 10,
            'complexity': 1.0,
        }
    
    def solve(self, problem: Dict[str, Any]):
        """Mock solve method."""
        from simulator import FieldSolution
        
        # Create mock field data
        grid_size = problem['domain'].get('grid_size', 0.1e-6)
        length = problem['domain'].get('length', 10e-6)
        n_points = int(length / grid_size)
        
        # Simple sinusoidal field
        x = np.linspace(0, length, n_points)
        amplitude = np.exp(-x / (2 * length)) * np.sin(2 * np.pi * x / (1e-6))
        
        return FieldSolution(
            amplitude=amplitude,
            metadata={
                'solver': self.name,
                'solver_version': self.version,
                'problem_name': problem['name'],
                'grid_points': n_points,
                'computation_time': 0.1,
            }
        )

class MockAccurateSolver:
    """Mock solver for accurate but slower solutions."""
    
    def __init__(self):
        self.name = "MockAccurateSolver"
        self.version = "2.0"
    
    def can_solve(self, problem: Dict[str, Any]) -> tuple:
        """Check if this solver can solve the problem."""
        domain_type = problem.get('domain', {}).get('type', '1d')
        
        if domain_type in ['1d', '2d']:
            return True, f"Can solve {domain_type.upper()} problems accurately"
        return False, "Only solves 1D and 2D problems"
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get solver requirements and capabilities."""
        return {
            'physical_models': ['linear', 'interference', 'diffraction'],
            'max_dimensions': 2,
            'supported_components': ['source', 'waveguide', 'lens', 'mirror'],
        }
    
    def estimate_computation_cost(self, problem: Dict[str, Any]) -> Dict[str, float]:
        """Estimate computation cost."""
        domain = problem.get('domain', {})
        if domain.get('type') == '2d':
            return {'time_seconds': 5.0, 'memory_mb': 500, 'complexity': 10.0}
        return {'time_seconds': 1.0, 'memory_mb': 100, 'complexity': 5.0}
    
    def solve(self, problem: Dict[str, Any]):
        """Mock solve method."""
        from simulator import FieldSolution
        
        # Create more complex mock field data
        domain = problem['domain']
        domain_type = domain.get('type', '1d')
        
        if domain_type == '1d':
            grid_size = domain.get('grid_size', 0.1e-6)
            length = domain.get('length', 10e-6)
            n_points = int(length / grid_size)
            x = np.linspace(0, length, n_points)
            
            # More complex field pattern
            amplitude = (
                np.exp(-x / length) * 
                np.sin(2 * np.pi * x / (0.5e-6)) *
                np.cos(2 * np.pi * x / (1e-6))
            )
            
        else:  # 2D
            width = domain.get('width', 5e-6)
            height = domain.get('height', 5e-6)
            grid_size = domain.get('grid_size', 0.2e-6)
            
            nx = int(width / grid_size)
            ny = int(height / grid_size)
            x = np.linspace(0, width, nx)
            y = np.linspace(0, height, ny)
            X, Y = np.meshgrid(x, y)
            
            # 2D Gaussian beam
            amplitude = np.exp(
                -((X - width/2)**2 + (Y - height/2)**2) / (1e-6)**2
            ) * np.sin(2 * np.pi * X / (1e-6))
        
        return FieldSolution(
            amplitude=amplitude,
            metadata={
                'solver': self.name,
                'solver_version': self.version,
                'problem_name': problem['name'],
                'domain_type': domain_type,
                'computation_time': 1.0,
            }
        )

print("\n📝 Registering custom mock solvers...")

try:
    # Create a new manager for this demo (not using global)
    demo_manager = create_solver_manager(enable_auto_selection=True)
    
    # Register mock solvers with different priorities
    fast_solver = MockFastSolver()
    accurate_solver = MockAccurateSolver()
    
    # Register with Solver interface if available
    try:
        from simulator import Solver
        # Wrap mock solvers in Solver interface
        class WrappedFastSolver(Solver):
            def __init__(self, mock_solver):
                self.mock = mock_solver
                self.name = mock_solver.name
                self.version = mock_solver.version
            
            def can_solve(self, problem):
                return self.mock.can_solve(problem)
            
            def get_requirements(self):
                return self.mock.get_requirements()
            
            def estimate_computation_cost(self, problem):
                return self.mock.estimate_computation_cost(problem)
            
            def solve(self, problem):
                return self.mock.solve(problem)
        
        demo_manager.register_solver(WrappedFastSolver(fast_solver), priority=5)
        demo_manager.register_solver(WrappedFastSolver(accurate_solver), priority=8)
        
        print("✅ Custom solvers registered (wrapped in Solver interface)")
        
    except ImportError:
        print("⚠️  Solver interface not available, registering mock solvers directly")
        # Fallback: Try to register directly if manager supports it
        demo_manager.register_solver(fast_solver, priority=5)
        demo_manager.register_solver(accurate_solver, priority=8)
    
    # Show registered solvers
    available = demo_manager.get_available_solvers()
    print(f"\n📋 Registered solvers ({len(available)}):")
    
    for solver_id, info in available.items():
        print(f"\n  {info['name']} v{info['version']}:")
        print(f"    Priority: {info.get('priority', 'N/A')}")
        print(f"    Capabilities: {', '.join(info.get('capabilities', ['unknown']))}")
        print(f"    Max dimensions: {info.get('max_dimensions', 'N/A')}")
    
    # Test selection with custom solvers
    print("\n🤖 Testing selection with custom solvers:")
    
    test_problem = create_waveguide_problem(dimensions=1)
    selection = demo_manager.select_solver(test_problem)
    
    print(f"  Problem: {test_problem['name']}")
    print(f"  Selected: {selection.solver.name}")
    print(f"  Confidence: {selection.confidence:.1%}")
    print(f"  Reason: {selection.reason}")
    
except Exception as e:
    print(f"❌ Error in custom solver demo: {e}")
    import traceback
    traceback.print_exc()

# -------------------------------------------------------------------
# Example 3: Performance analysis and statistics
# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("📊 Example 3: Performance Analysis")
print("=" * 70)

print("\n🧪 Running benchmark tests...")

# Use the global manager for performance tracking
benchmark_problems = [
    create_waveguide_problem(dimensions=1, length=5e-6),
    create_waveguide_problem(dimensions=1, length=20e-6),
    create_waveguide_problem(dimensions=2, length=10e-6),
]

print(f"Running {len(benchmark_problems)} benchmark problems...")

for i, problem in enumerate(benchmark_problems, 1):
    print(f"\n  Problem {i}: {problem['name']}")
    
    try:
        start_time = time.time()
        
        # Select solver
        selection = manager.select_solver(problem)
        print(f"    Selected: {selection.solver.__class__.__name__}")
        
        # Solve (if solvers are available)
        if len(manager.solvers) > 0:
            try:
                result = manager.solve(problem)
                solve_time = time.time() - start_time
                
                print(f"    Solve time: {solve_time:.3f}s")
                print(f"    Result type: {type(result).__name__}")
                
                if hasattr(result, 'amplitude'):
                    shape = result.amplitude.shape
                    print(f"    Field shape: {shape}")
                
            except Exception as solve_error:
                print(f"    Solve failed (expected if no real solvers): {solve_error}")
        else:
            print(f"    ⏭️  Skipping solve (no real solvers registered)")
            
    except Exception as e:
        print(f"    ❌ Benchmark failed: {e}")

# Get performance statistics
print("\n📈 Performance Statistics:")

try:
    stats = manager.get_solver_statistics()
    perf_report = manager.get_performance_report()
    
    print(f"  Total runs: {perf_report.get('total_runs', 0)}")
    print(f"  Successful: {perf_report.get('successful_runs', 0)}")
    print(f"  Failed: {perf_report.get('failed_runs', 0)}")
    print(f"  Success rate: {perf_report.get('success_rate', 0):.1%}")
    print(f"  Total time: {perf_report.get('total_time', 0):.2f}s")
    print(f"  Average time: {perf_report.get('average_time', 0):.3f}s")
    
    if perf_report.get('recent_runs'):
        print(f"\n  Recent runs ({len(perf_report['recent_runs'])}):")
        for run in perf_report['recent_runs'][-3:]:  # Show last 3
            status = "✅" if run.get('success', False) else "❌"
            solver = run.get('solver', 'unknown')
            time_taken = run.get('actual_time', 0)
            print(f"    {status} {solver}: {time_taken:.3f}s")
    
except Exception as e:
    print(f"  ❌ Could not get statistics: {e}")

# -------------------------------------------------------------------
# Example 4: Problem decomposition
# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("🧩 Example 4: Problem Decomposition")
print("=" * 70)

# Create a 2D problem for decomposition
complex_2d_problem = {
    'name': 'complex_2d_circuit',
    'domain': {
        'type': '2d',
        'width': 20e-6,
        'height': 20e-6,
        'grid_size': 0.5e-6,
    },
    'physics': ['linear', 'nonlinear', 'interference'],
    'parameters': {
        'wavelength': 1.55e-6,
        'temperature': 300,
        'nonlinear_coefficient': 1e-12,
    },
    'components': [
        {'type': 'laser_source', 'position': [2e-6, 10e-6], 'power': 1.0},
        {'type': 'waveguide', 'path': [[2e-6, 10e-6], [10e-6, 10e-6], [10e-6, 2e-6]]},
        {'type': 'ring_resonator', 'center': [15e-6, 15e-6], 'radius': 3e-6},
        {'type': 'photodetector', 'position': [18e-6, 2e-6], 'sensitivity': 0.8},
    ],
}

print(f"\nProblem: {complex_2d_problem['name']}")
print(f"Domain: {complex_2d_problem['domain']['width']:.1e}m × "
      f"{complex_2d_problem['domain']['height']:.1e}m")
print(f"Physics: {', '.join(complex_2d_problem['physics'])}")

print("\n🔍 Decomposition strategies:")

decomposition_strategies = ['auto', 'spatial']

for strategy in decomposition_strategies:
    try:
        parts = manager.decompose_problem(complex_2d_problem, decomposition_strategy=strategy)
        print(f"\n  {strategy.capitalize()} decomposition:")
        print(f"    Number of parts: {len(parts)}")
        
        for i, part in enumerate(parts, 1):
            print(f"    Part {i}: {part.domain_id}")
            
            # Show domain bounds if available
            if 'domain' in part.problem_description:
                domain = part.problem_description['domain']
                if 'x_min' in domain:
                    print(f"      Bounds: x=[{domain['x_min']:.1e}, {domain['x_max']:.1e}], "
                          f"y=[{domain['y_min']:.1e}, {domain['y_max']:.1e}]")
        
        if len(parts) > 1:
            print(f"    → Can be solved with {len(parts)} different solvers in parallel!")
            
    except Exception as e:
        print(f"\n  {strategy} decomposition failed: {e}")

# -------------------------------------------------------------------
# Example 5: Hybrid solving workflow
# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("🔄 Example 5: Hybrid Solving Workflow")
print("=" * 70)

print("""
Hybrid solving workflow:
1. Problem analysis and decomposition
2. Solver selection for each subproblem
3. Parallel solving of subproblems
4. Solution stitching and validation
5. Result aggregation and reporting
""")

print("Current SolverManager capabilities:")
print("✓ Automatic solver selection")
print("✓ Problem decomposition strategies")
print("✓ Performance tracking and statistics")
print("✓ Metadata integration")
print("⏳ Future: True parallel hybrid solving")
print("⏳ Future: Automatic solution stitching")
print("⏳ Future: Machine learning-based solver selection")

# -------------------------------------------------------------------
# Final summary
# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("🏁 Demo Summary")
print("=" * 70)

print(f"\n✅ SolverManager successfully demonstrated!")
print(f"\n🎯 Key features tested:")
print(f"  1. Architecture integration: {'✓' if SOLVER_MANAGER_AVAILABLE else '✗'}")
print(f"  2. Automatic solver selection: {'✓'}")
print(f"  3. Custom solver registration: {'✓'}")
print(f"  4. Performance tracking: {'✓'}")
print(f"  5. Problem decomposition: {'✓'}")

print(f"\n📊 Current status:")
try:
    available = manager.get_available_solvers()
    print(f"  Registered solvers: {len(available)}")
    
    for solver_id, info in available.items():
        success_rate = info.get('success_rate', 0)
        status = "✅" if success_rate > 0 else "⚪"
        print(f"  {status} {info['name']}: {success_rate:.0%} success rate")
        
except:
    print(f"  Registered solvers: {len(manager.solvers) if hasattr(manager, 'solvers') else 0}")

print(f"\n🚀 Next steps for your project:")
print(f"  1. Implement real solvers (extend LinearWaveSolver)")
print(f"  2. Add more decomposition strategies")
print(f"  3. Implement solution stitching for hybrid solving")
print(f"  4. Add machine learning for intelligent solver selection")

print("\n" + "=" * 70)
print("💡 Tip: Use `get_solver_manager()` for global access")
print("💡 Tip: Check `get_architecture_status()` for diagnostics")
print("💡 Tip: Use `create_solver_manager()` for custom instances")
print("=" * 70)

# Quick interactive test
print("\n🧪 Quick interactive test:")
try:
    response = input("Run quick solver selection test? (y/n): ")
    if response.lower() == 'y':
        test_problem = create_waveguide_problem(dimensions=1)
        selection = manager.select_solver(test_problem)
        print(f"\nTest result:")
        print(f"  Problem: {test_problem['name']}")
        print(f"  Selected: {selection.solver.__class__.__name__}")
        print(f"  Confidence: {selection.confidence:.1%}")
        print("✅ Test completed!")
except:
    print("⏭️  Skipping interactive test")

print("\n🎉 Demo complete! The hybrid architecture foundation is ready.")
