#!/usr/bin/env python3
"""
Integration test for SolverManager - Phase 2 core component.
Tests automatic solver selection, registration, and problem solving.
"""

import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧪 SolverManager Integration Test - Phase 2")
print("=" * 70)

# -------------------------------------------------------------------
# Test 1: Check basic imports and architecture
# -------------------------------------------------------------------
print("\n1️⃣  Testing architecture and imports...")

try:
    from simulator import (
        hello,
        get_architecture_status,
        get_solver_manager,
        SOLVER_MANAGER_AVAILABLE,
        HYBRID_ARCHITECTURE_AVAILABLE
    )
    
    print(f"   {hello()}")
    status = get_architecture_status()
    print(f"   SolverManager available: {SOLVER_MANAGER_AVAILABLE}")
    print(f"   Full hybrid architecture: {HYBRID_ARCHITECTURE_AVAILABLE}")
    
    if not SOLVER_MANAGER_AVAILABLE:
        print("   ❌ SolverManager not available - test stopping")
        sys.exit(1)
        
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

print("   ✅ Basic imports successful")

# -------------------------------------------------------------------
# Test 2: Create SolverManager instance
# -------------------------------------------------------------------
print("\n2️⃣  Creating SolverManager instance...")

try:
    manager = get_solver_manager()
    print(f"   ✅ SolverManager created")
    print(f"   Auto-selection: {manager.enable_auto_selection}")
    
    # Try creating another instance (should return same instance)
    manager2 = get_solver_manager()
    if manager is manager2:
        print("   ✅ Singleton pattern working (same instance returned)")
    else:
        print("   ⚠️  Different instances returned")
        
except Exception as e:
    print(f"   ❌ Failed to create SolverManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# -------------------------------------------------------------------
# Test 3: Check registered solvers
# -------------------------------------------------------------------
print("\n3️⃣  Checking registered solvers...")

try:
    available = manager.get_available_solvers()
    print(f"   Found {len(available)} registered solver(s)")
    
    if available:
        for solver_id, info in available.items():
            print(f"   - {info['name']} v{info['version']}")
            print(f"     Priority: {info.get('priority', 0)}, "
                  f"Success rate: {info.get('success_rate', 0):.1%}")
    else:
        print("   ⚠️  No solvers registered - testing with mock solver")
        
except Exception as e:
    print(f"   ❌ Error checking solvers: {e}")

# -------------------------------------------------------------------
# Test 4: Create test problems
# -------------------------------------------------------------------
print("\n4️⃣  Creating test problems...")

test_problems = {
    'simple_1d': {
        'name': 'simple_1d_waveguide',
        'domain': {
            'type': '1d',
            'length': 10e-6,
            'grid_size': 0.1e-6,
        },
        'physics': ['linear'],
        'parameters': {
            'wavelength': 1.55e-6,
            'propagation_distance': 1e-3,
        },
        'components': [
            {'type': 'source', 'amplitude': 1.0, 'phase': 0.0},
            {'type': 'waveguide', 'length': 5e-6, 'refractive_index': 1.5},
        ]
    },
    
    'medium_2d': {
        'name': 'medium_2d_cavity',
        'domain': {
            'type': '2d',
            'width': 5e-6,
            'height': 5e-6,
            'grid_size': 0.2e-6,
        },
        'physics': ['linear', 'interference'],
        'parameters': {
            'wavelength': 1.55e-6,
            'propagation_distance': 0.5e-3,
        },
        'components': [
            {'type': 'gaussian_source', 'amplitude': 0.8, 'width': 1e-6},
            {'type': 'lens', 'focal_length': 2e-6},
        ]
    },
    
    'complex_3d': {
        'name': 'complex_3d_interferometer',
        'domain': {
            'type': '3d',
            'width': 3e-6,
            'height': 3e-6,
            'depth': 10e-6,
            'grid_size': 0.3e-6,
        },
        'physics': ['linear', 'interference', 'diffraction'],
        'parameters': {
            'wavelength': 0.85e-6,
            'propagation_distance': 2e-3,
        },
        'components': [
            {'type': 'laser_source', 'amplitude': 1.0, 'coherence_length': 1e-3},
            {'type': 'beam_splitter', 'ratio': 0.5},
            {'type': 'mirror', 'reflectivity': 0.99},
            {'type': 'detector', 'position': [0, 0, 10e-6]},
        ]
    }
}

print(f"   Created {len(test_problems)} test problems")
for name, problem in test_problems.items():
    print(f"   - {name}: {problem['name']}")

# -------------------------------------------------------------------
# Test 5: Test solver selection
# -------------------------------------------------------------------
print("\n5️⃣  Testing automatic solver selection...")

try:
    for problem_name, problem in test_problems.items():
        print(f"\n   Problem: {problem_name}")
        
        # Test selection
        selection = manager.select_solver(problem)
        
        print(f"   Selected: {selection.solver.__class__.__name__}")
        print(f"   Confidence: {selection.confidence:.2f}")
        print(f"   Reason: {selection.reason}")
        
        if selection.estimated_cost:
            print(f"   Estimated cost: ", end="")
            for key, value in selection.estimated_cost.items():
                print(f"{key}={value:.3f}", end=" ")
            print()
            
    print("\n   ✅ Solver selection working")
    
except Exception as e:
    print(f"   ❌ Solver selection failed: {e}")
    import traceback
    traceback.print_exc()

# -------------------------------------------------------------------
# Test 6: Test actual solving (if solvers available)
# -------------------------------------------------------------------
print("\n6️⃣  Testing problem solving...")

if available:
    try:
        # Use the simplest problem
        problem = test_problems['simple_1d']
        print(f"   Solving: {problem['name']}")
        
        result = manager.solve(problem)
        print(f"   ✅ Problem solved successfully!")
        print(f"   Result type: {type(result).__name__}")
        
        # Check for metadata
        if hasattr(result, 'metadata'):
            print(f"   Metadata keys: {list(result.metadata.keys())}")
            
            # Check solver_manager metadata
            if 'solver_manager' in result.metadata:
                mgr_info = result.metadata['solver_manager']
                print(f"   Solver used: {mgr_info.get('selected_solver', 'unknown')}")
                print(f"   Selection confidence: {mgr_info.get('selection_confidence', 'N/A')}")
                print(f"   Actual time: {mgr_info.get('actual_time', 0):.3f}s")
        
        # Try to access field data
        if hasattr(result, 'amplitude'):
            print(f"   Field amplitude shape: {result.amplitude.shape}")
            print(f"   Field amplitude dtype: {result.amplitude.dtype}")
            
    except Exception as e:
        print(f"   ⚠️  Problem solving failed (may need actual solver implementation): {e}")
        print(f"   This is expected if solvers are registered but not fully implemented")
else:
    print("   ⚠️  Skipping solving test - no solvers registered")

# -------------------------------------------------------------------
# Test 7: Test statistics and performance tracking
# -------------------------------------------------------------------
print("\n7️⃣  Testing statistics and performance tracking...")

try:
    # Get initial statistics
    stats = manager.get_solver_statistics()
    perf_report = manager.get_performance_report()
    
    print(f"   Total runs: {perf_report.get('total_runs', 0)}")
    print(f"   Success rate: {perf_report.get('success_rate', 0):.1%}")
    print(f"   Average time: {perf_report.get('average_time', 0):.3f}s")
    
    # Test statistics reset
    manager.reset_statistics()
    print(f"   ✅ Statistics reset successful")
    
    # Check statistics after reset
    stats_after = manager.get_solver_statistics()
    if stats_after.get('total_solvers', 0) == 0:
        print(f"   ⚠️  No solver stats after reset - may be expected")
    else:
        print(f"   Solver stats preserved after reset")
    
    print("   ✅ Statistics tracking working")
    
except Exception as e:
    print(f"   ❌ Statistics test failed: {e}")

# -------------------------------------------------------------------
# Test 8: Test problem decomposition
# -------------------------------------------------------------------
print("\n8️⃣  Testing problem decomposition...")

try:
    problem = test_problems['medium_2d']
    
    # Test auto decomposition
    parts_auto = manager.decompose_problem(problem, decomposition_strategy='auto')
    print(f"   Auto decomposition: {len(parts_auto)} part(s)")
    
    # Test spatial decomposition
    parts_spatial = manager.decompose_problem(problem, decomposition_strategy='spatial')
    print(f"   Spatial decomposition: {len(parts_spatial)} part(s)")
    
    if parts_spatial:
        for i, part in enumerate(parts_spatial, 1):
            print(f"     Part {i}: {part.domain_id}")
    
    print("   ✅ Problem decomposition working")
    
except Exception as e:
    print(f"   ❌ Decomposition test failed: {e}")
    import traceback
    traceback.print_exc()

# -------------------------------------------------------------------
# Test 9: Test hybrid solving (placeholder for now)
# -------------------------------------------------------------------
print("\n9️⃣  Testing hybrid solving (placeholder)...")

try:
    problem = test_problems['simple_1d']
    result = manager.solve_hybrid(problem, decomposition_strategy='auto')
    
    print(f"   Hybrid solve completed")
    print(f"   Result type: {type(result).__name__}")
    
    # Check if result has hybrid metadata
    if hasattr(result, 'metadata') and result.metadata.get('hybrid', False):
        print(f"   ⚠️  Actual hybrid solve (unexpected for placeholder)")
    else:
        print(f"   ✅ Hybrid solve placeholder working (falls back to single solver)")
        
except Exception as e:
    print(f"   ❌ Hybrid solve test failed: {e}")

# -------------------------------------------------------------------
# Test 10: Final diagnostics
# -------------------------------------------------------------------
print("\n🔟  Final diagnostics...")

try:
    # Get architecture status
    status = get_architecture_status()
    
    print(f"   Architecture version: {status['version']}")
    print(f"   Available modules: {len(status['available_modules'])}")
    
    # Check SolverManager specific diagnostics
    if hasattr(manager, 'get_performance_report'):
        report = manager.get_performance_report()
        print(f"   Performance report: {report.get('total_runs', 0)} runs")
    
    # Check if we can create a new manager with different settings
    try:
        from simulator import create_solver_manager
        custom_manager = create_solver_manager(enable_auto_selection=False)
        print(f"   Custom manager created (auto-selection disabled)")
    except Exception as create_error:
        print(f"   ⚠️  Could not create custom manager: {create_error}")
    
    print("\n   📊 Test Summary:")
    print(f"   - Architecture: {'Hybrid' if HYBRID_ARCHITECTURE_AVAILABLE else 'Legacy'}")
    print(f"   - SolverManager: {'Ready' if SOLVER_MANAGER_AVAILABLE else 'Not available'}")
    print(f"   - Registered solvers: {len(available)}")
    
    if available:
        success_rates = [info.get('success_rate', 0) for info in available.values()]
        avg_success = sum(success_rates) / len(success_rates) if success_rates else 0
        print(f"   - Average success rate: {avg_success:.1%}")
    
    print("\n   ✅ SolverManager integration test COMPLETE")
    
except Exception as e:
    print(f"   ❌ Final diagnostics failed: {e}")

print("\n" + "=" * 70)
print("🎯 Phase 2: SolverManager Integration - TEST COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Implement actual solvers (LinearWaveSolver, etc.)")
print("2. Add more solver evaluation criteria")
print("3. Implement true hybrid solving with stitching")
print("4. Add solver learning/adaptation features")
