import clr
import sys

clr.AddReference("System")
clr.AddReference("System.Runtime")
clr.AddReference("System.Collections")
clr.AddReference("System.Threading")

sys.path.append(r"C:\Program Files\SpectraVortex\Bin")
clr.AddReference("RizomaModules")

from SpectraVortex import *
from SpectraVortex.Commercial import PulseProxy

class RizomaCore:
    def __init__(self, freq=60.0):
        print("Initializing core (8 modules)")
        self.tick = TickGenerator(freq)
        self.trace = TraceBuffer(10000)
        self.vlock = VectorLock()
        self.vlock.SetOrder(["Conductor", "PulseProxy", "Historian"])
        self.conductor = Conductor(self.tick, self.trace, self.vlock)
        self.historian = Historian(self.trace)
        self.fractal = FractalLOD()
        self.divider = RealmDivider(self.vlock, self.trace, self.tick)
        self.pulse = PulseProxy(self.tick, self.trace)
        self.running = False
        
    def start(self):
        self.tick.Start()
        self.running = True
        print("Rizoma started (8 modules)")
        
    def stop(self):
        self.tick.Stop()
        self.running = False
        print("Rizoma stopped")
        
    def get_tick(self):
        return self.tick.CurrentTick
        
    def feed_pulse(self, freq):
        self.pulse.Feed(freq)
        
    # ектор только для чтения
    @property
    def vector(self):
        return self.conductor.CurrentVector
        
    def get_status(self):
        """Текущее состояние"""
        return {
            "tick": self.get_tick(),
            "running": self.running,
            "vector": self.conductor.CurrentVector,
            "sync": self.pulse.Synchronized,
            "holder": self.vlock.CurrentHolder
        }

_core_instance = None

def init_core(freq=60.0):
    global _core_instance
    if _core_instance is None:
        _core_instance = RizomaCore(freq)
    return _core_instance

def get_core():
    return _core_instance
