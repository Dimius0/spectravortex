import numpy as np

class SimpleVortex:
    def __init__(self, pos):
        self.position = np.array(pos, dtype=np.float64)

class SimpleSolver:
    def __init__(self):
        self.vortices = [SimpleVortex([25,25,25]), SimpleVortex([30,30,30])]
        self.nx = self.ny = self.nz = 32
        self.dx = self.dy = self.dz = 50/32
        self.Lx = self.Ly = self.Lz = 50
    
    def relax_vortices(self, state=None, thermal_scale=0.3):
        if state is None:
            class State: pass
            state = State()
            state.temperature = 300
            state.pressure = 0.1
        
        pressure_force_factor = 1.0 + state.pressure / 200.0
        thermal_amplitude = thermal_scale * np.sqrt(state.temperature / 300.0) * 2.76
        
        print(f"pressure_force_factor type: {type(pressure_force_factor)}")
        print(f"thermal_amplitude type: {type(thermal_amplitude)}")
        
        for vortex in self.vortices:
            # ????????? ?????????
            grad = np.array([1.0, 2.0, 3.0], dtype=np.float64)
            
            force = -grad * pressure_force_factor
            print(f"force type after multiply: {force.dtype}")
            
            if state.temperature > 0:
                noise = np.random.randn(3).astype(np.float64) * thermal_amplitude
                print(f"noise type: {noise.dtype}")
                force = force + noise
                print(f"force type after add: {force.dtype}")
            
            vortex.position += 0.05 * force
            print(f"position type: {vortex.position.dtype}")
        
        return {'final_energy': 0}

solver = SimpleSolver()
class State:
    temperature = 300
    pressure = 0.1

result = solver.relax_vortices(State())
print("SUCCESS - no type error!")
