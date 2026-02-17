#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import random
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

class ColonizerModule:
    def __init__(self, intel):
        self.intel = intel

    def run(self):
        print("🏗️ Колонизатор работает")
        while True:
            front = self.intel.data.get('front_line', 138)
            target = self.intel.data.get('primary_target', 1000)
            if front < target:
                front += random.choice([1,2,3])
                self.intel.update('front_line', front)
                print(f"   Фронт: {front}")
            time.sleep(3)