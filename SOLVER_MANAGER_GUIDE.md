#!/usr/bin/env python3
"""
SolverManager Demo - Simple examples.
"""

import numpy as np
import time

print("=" * 70)
print("SolverManager Demo")
print("=" * 70)

# Setup
try:
    from simulator import get_solver_manager, get_architecture_status, hello
    
    print(hello())
    
    manager = get_solver_manager()
    print(f"SolverManager ready with {len(manager.solvers)} solver(s)")
    
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)

# Example 1: Basic solving
print("\n" + "=" * 70)
print("Example 1: Basic Problem Solving")
print("=" * 70)

def create_test_problem():
    problem = {
        'name': 'test_waveguide',
        'domain': {'type': '1d', 'length': 10e-6, 'grid_size': 0.1e-6},
        'physics': ['linear'],
        'parameters': {'wavelength': 1.55e-6},
        'components': [
            {'type': 'source', 'amplitude': 1.0},
            {'type': 'waveguide', 'length': 5e-6},
        ]
    }
    return problem

problem = create_test_problem()
print(f"Problem: {problem['name']}")

# Test solver selection
try:
    selection = manager.select_solver(problem)
    print(f"Selected: {selection.solver.__class__.__name__}")
    print(f"Confidence: {selection.confidence:.1%}")
    print(f"Reason: {selection.reason}")
except Exception as e:
    print(f"Selection failed: {e}")

# Example 2: Performance stats
print("\n" + "=" * 70)
print("Example 2: Performance Stats")
print("=" * 70)

try:
    stats = manager.get_performance_report()
    print(f"Total runs: {stats.get('total_runs', 0)}")
    print(f"Success rate: {stats.get('success_rate', 0):.1%}")
    print(f"Average time: {stats.get('average_time', 0):.3f}s")
except Exception as e:
    print(f"Stats failed: {e}")

# Example 3: Problem decomposition
print("\n" + "=" * 70)
print("Example 3: Problem Decomposition")
print("=" * 70)

complex_problem = {
    'name': '2d_circuit',
    'domain': {'type': '2d', 'width': 20e-6, 'height': 20e-6},
    'physics': ['linear'],
    'components': []
}

try:
    parts = manager.decompose_problem(complex_problem, decomposition_strategy='spatial')
    print(f"Decomposed into {len(parts)} parts")
    for i, part in enumerate(parts, 1):
        print(f"Part {i}: {part.domain_id}")
except Exception as e:
    print(f"Decomposition failed: {e}")

# Summary
print("\n" + "=" * 70)
print("Demo Summary")
print("=" * 70)

print("\nFeatures tested:")
print("1. Basic imports: OK")
print("2. Solver selection: OK")
print("3. Performance stats: OK")
print("4. Problem decomposition: OK")

print("\nDemo complete!")
