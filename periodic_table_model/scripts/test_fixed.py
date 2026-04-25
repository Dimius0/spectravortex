import sys
import os
import importlib

# Clear module cache
for mod in list(sys.modules.keys()):
    if 'biharmonic' in mod:
        del sys.modules[mod]

# Add correct path (only src, not architect)
sys.path.insert(0, os.path.abspath('../../src'))

# Remove architect from path
sys.path = [p for p in sys.path if 'architect' not in p]

print("=" * 60)
print("FINAL TEST - FORCED RELOAD")
print("=" * 60)
print("Python path (first 5):")
for p in sys.path[:5]:
    print(f"  {p}")

# Import
import biharmonic_3d as b3d
from biharmonic_3d import TopologicalArchitect3D, BiharmonicSolver3D
import inspect

print(f"\nImported from: {b3d.__file__}")

print(f"\nSignature of relax_vortices:")
print(f"  {inspect.signature(BiharmonicSolver3D.relax_vortices)}")

# Check if 'state' parameter exists
sig = inspect.signature(BiharmonicSolver3D.relax_vortices)
has_state = 'state' in sig.parameters
print(f"\nHas 'state' parameter: {has_state}")

if not has_state:
    print("\nERROR: Still old version!")
    sys.exit(1)

print("\n" + "=" * 60)
print("TESTING RELAX_VORTICES")
print("=" * 60)

class TestState:
    def __init__(self, T, P):
        self.temperature = T
        self.pressure = P

arch = TopologicalArchitect3D(grid_shape=(32, 32, 32), box_size=(50, 50, 50))

for z, sym in [(1, 'H'), (6, 'C')]:
    arch.add_component({
        'charge': z,
        'symbol': sym,
        'Z': z,
        'position': [25, 25, 25]
    })

print(f"Created {len(arch.vortices)} vortices")

state1 = TestState(300, 0.1)
print("\n[1] Calling relax_vortices WITH state...")
try:
    result1 = arch.relax_vortices(max_iter=5, learning_rate=0.05, state=state1)
    print(f"    SUCCESS! final_energy = {result1.get('final_energy', 'N/A')}")
    print(f"    d_min(P) = {result1.get('d_min_equilibrium', 'N/A')}")
except TypeError as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 60)
