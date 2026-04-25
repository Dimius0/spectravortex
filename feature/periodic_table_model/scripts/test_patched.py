import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath('../../src'))

# ????-?????? ????? ????? ????????
import biharmonic_3d

# ????????? ???????????? ?????
original_relax = biharmonic_3d.BiharmonicSolver3D.relax_vortices

def patched_relax(self, max_iter=100, learning_rate=0.05, state=None, thermal_scale=0.3):
    """??????, ??????? ????????? ????"""
    if state is None:
        class DefaultState:
            def __init__(self):
                self.temperature = 300.0
                self.pressure = 0.1
        state = DefaultState()
    
    # ???????????? ???????????? ? float
    state.temperature = float(state.temperature)
    state.pressure = float(state.pressure)
    thermal_scale = float(thermal_scale)
    learning_rate = float(learning_rate)
    max_iter = int(max_iter)
    
    # ??????? ???????????? ?????
    return original_relax(self, max_iter, learning_rate, state, thermal_scale)

# ???????? ?????
biharmonic_3d.BiharmonicSolver3D.relax_vortices = patched_relax

from biharmonic_3d import TopologicalArchitect3D

print("=" * 60)
print("TEST WITH MONKEY PATCH")
print("=" * 60)

class TestState:
    def __init__(self, T, P):
        self.temperature = float(T)
        self.pressure = float(P)

arch = TopologicalArchitect3D(grid_shape=(32, 32, 32), box_size=(50, 50, 50))

for z, sym in [(1, 'H'), (6, 'C')]:
    arch.add_component({
        'charge': z,
        'symbol': sym,
        'Z': z,
        'position': [25.0, 25.0, 25.0]
    })

print(f"Created {len(arch.vortices)} vortices")

state1 = TestState(300, 0.1)
print("\n[1] Calling relax_vortices WITH state...")
try:
    result1 = arch.relax_vortices(max_iter=5, learning_rate=0.05, state=state1, thermal_scale=0.3)
    print(f"    SUCCESS! final_energy = {result1.get('final_energy', 'N/A')}")
    print(f"    d_min(P) = {result1.get('d_min_equilibrium', 'N/A')}")
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
