#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import random
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

class DeepScoutModule:
    def __init__(self, intel):
        self.intel = intel
        self.targets = [500, 1000, 2000, 5000, 10000]

    def run(self):
        print("🌌 Разведчик стартовал")
        for t in self.targets:
            success = random.random() > 0.5
            energy = 20000 + t * 2
            print(f"   {t} -> {'✅' if success else '❌'} ({energy:.0f})")
            self.intel.update('deep_recon', {str(t): {'energy': energy, 'success': success}})
            time.sleep(2)