#!/usr/bin/env python3
import sys, threading, time
from pathlib import Path
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
from headquarters import Coordinator
from headquarters.modules.core_scout import ScoutUnit
from headquarters.modules.pulse_hunter import PulseHunterModule

hq = Coordinator()
hq.register_module('pulse', PulseHunterModule)

scouts = [("L1",1),("L2",1),("M1",2),("M2",2),("H1",3),("H2",3)]
for name,power in scouts:
    def make(name,power):
        class Wrapper:
            def __init__(self,i,c): self.unit = ScoutUnit(name,power,[0,100000],i,c)
            def run(self): self.unit.run()
        return Wrapper
    hq.register_module(name, make(name,power))

for name,mod in hq.modules.items():
    threading.Thread(target=mod.run, daemon=True).start()

print(f"\nfront: {hq.intel.get('front_line')}\n")
try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    hq.intel.save()
    print("\nsaved")
