import sys
import os
import importlib

# ?????? ??? ??????? ????? ????????
for mod in list(sys.modules.keys()):
    if 'biharmonic' in mod:
        del sys.modules[mod]

# ???????? ???? ?? ? ?????????? ????? (?? ? architect)
sys.path.insert(0, os.path.abspath('../../src'))

# ?????? architect ?? ????, ???? ?? ??? ????
sys.path = [p for p in sys.path if 'architect' not in p]

print("=" * 60)
print("FINAL TEST - FORCED RELOAD")
print("=" * 60)
print("Python path:")
for p in sys.path[:5]:
    print(f"  {p}")

# ??????????
from biharmonic_3d import TopologicalArchitect3D, BiharmonicSolver3D
import inspect

print(f"\nImported from: {biharmonic_3d.__file__}")

print(f"\nSignature of relax_vortices:")
print(f"  {inspect.signature(BiharmonicSolver3D.relax_vortices)}")

# ????????, ???? ?? ???????? state
sig = inspect.signature(BiharmonicSolver3D.relax_vortices)
has_state = 'state' in sig.parameters
print(f"\nHas 'state' parameter: {has_state}")

if not has_state:
    print("\nERROR: Still old version!")
    print("Let's try to reload from correct file...")
    
    # ????? ???????? ?? ?????
    import importlib.util
    file_path = os.path.abspath('../../src/biharmonic_3d.py')
    spec = importlib.util.spec_from_file_location("biharmonic_3d_new", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    print(f"\nDirect load from: {file_path}")
    print(f"Signature: {inspect.signature(module.BiharmonicSolver3D.relax_vortices)}")
    
    TopologicalArchitect3D = module.TopologicalArchitect3D

# ?????? ?????????
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
