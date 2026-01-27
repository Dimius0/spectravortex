SOLVER MANAGER - HYBRID ARCHITECTURE CORE
=========================================

PURPOSE
-------
Automatically select the best solver for each problem.
Coordinate multiple solvers for complex computations.

QUICK START
-----------

1. Import and check:
```python
from simulator import get_solver_manager, hello
print(hello())  # Check architecture status
manager = get_solver_manager()  # Global manager instance
