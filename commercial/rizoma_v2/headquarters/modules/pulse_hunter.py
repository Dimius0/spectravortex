#!/usr/bin/env python3
import sys, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class PulseHunterModule:
    def __init__(self, intel, coord):
        self.intel = intel
        self.coord = coord
        self.target = 1000
        self.running = True
        
    def run(self):
        print("\npulse hunter start")
        while self.running:
            ok = random.random() > 0.3
            en = random.randint(20000, 30000) if ok else 0
            self.coord.phase.record_pulse(ok, en)
            if ok:
                print(f"pulse ? {self.target} ({en})")
                self.intel.dict_add('islands', self.target, en)
            else:
                print(f"pulse ? {self.target}")
                self.coord.homeo.register_collapse(self.target, en)
            time.sleep(300)
    
    def stop(self):
        self.running = False
