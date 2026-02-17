#!/usr/bin/env python3
import sys, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class ScoutUnit:
    def __init__(self, name, power, target_range, intel, coord):
        self.name = name
        self.power = power
        self.range = target_range
        self.intel = intel
        self.coord = coord
        self.target = None
        self.running = True
        
    def run(self):
        print(f"   scout {self.name}")
        while self.running:
            if not self.coord.sync.should_act(self.name):
                time.sleep(60)
                continue
                
            if self.target is None:
                front = self.intel.get('front_line', 0)
                self.target = front + 1000 * self.power
                
            if not self.target:
                time.sleep(300)
                continue
                
            front = self.intel.get('front_line', 0)
            ok = random.random() > 0.4
            en = random.randint(20000, 30000)
            
            if ok:
                print(f"? {self.name} took {self.target} ({en})")
                self.intel.dict_add('islands', self.target, en)
                if self.target > front:
                    self.intel.update('front_line', self.target)
                self.target = None
            else:
                print(f"? {self.name} fail {self.target}")
                self.coord.buffer.add(self.target, en)
                self.target = None
                
            time.sleep(60 * self.power)
    
    def stop(self):
        self.running = False
