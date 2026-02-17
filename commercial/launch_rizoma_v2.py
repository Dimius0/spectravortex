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
for name,p in [("L1",1),("L2",1),("M1",2),("M2",2),("H1",3),("H2",3)]:
    def make(name,p):
        class W:
            def __init__(self,i,c): self.u = ScoutUnit(name,p,[0,50000],i,c)
            def run(self): self.u.run()
        return W
    hq.register_module(name, make(name,p))

for n,m in hq.modules.items():
    threading.Thread(target=m.run, daemon=True).start()

print(f"\nfront: {hq.intel.get('front_line')}\n")
try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    hq.intel.save(); print("\nsaved")
