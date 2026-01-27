#!/usr/bin/env python3
"""
Simple SolverManager Demo
"""

print("=" * 50)
print("SolverManager Demo")
print("=" * 50)

# 1. Import check
try:
    from simulator import get_solver_manager, hello
    print(hello())
    manager = get_solver_manager()
    print(f"Manager created")
except Exception as e:
    print(f"Import error: {e}")
    exit(1)

# 2. Create simple problem
problem = {
    'name': 'test',
    'domain': {'type': '1d', 'length': 10e-6},
    'physics': ['linear'],
    'components': []
}

# 3. Try solver selection
try:
    selection = manager.select_solver(problem)
    print(f"\nSelected solver: {selection.solver.__class__.__name__}")
    print(f"Confidence: {selection.confidence:.1%}")
except Exception as e:
    print(f"\nSelection error: {e}")

# 4. Try stats
try:
    stats = manager.get_performance_report()
    print(f"\nTotal runs: {stats.get('total_runs', 0)}")
except Exception as e:
    print(f"\nStats error: {e}")

# 5. Summary
print("\n" + "=" * 50)
print("Demo done")
print("=" * 50)
