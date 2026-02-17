#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ: КОЛОНИЗАТОР
Задача: подтягивать фронт к цели, захватывая промежуточные острова
"""
import sys
import time
import random
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

def colonize_test(target, from_n):
    """Имитация захвата промежуточных островов"""
    distance = abs(target - from_n)
    success = random.random() > (distance / 50)  # Чем ближе, тем выше шанс
    energy = 20000 + distance * 100 + random.randint(-2000, 2000)
    
    status = "✅" if success else "❌"
    print(f"   🏗️ Колонизатор: {from_n}->{target} {status} (энергия {energy:.0f})")
    
    return success, energy

class ColonizerModule:
    def __init__(self, intel):
        self.intel = intel
        self.name = "colonizer"

    def run(self):
        print("\n🏗️ КОЛОНИЗАТОР приступил к расширению плацдарма")
        
        while True:
            front = self.intel.get('front_line', 138)
            target = self.intel.get('primary_target', 1000)
            
            # Если фронт уже у цели — спим
            if front >= target:
                print(f"🏗️ Колонизатор: цель {target} достигнута. Жду новой цели...")
                time.sleep(60)
                continue
            
            # Пробуем прыгнуть как можно ближе к цели
            next_step = min(front + random.choice([1, 2, 3, 5, 8, 13]), target)
            
            success, energy = colonize_test(next_step, front)
            
            if success:
                # Захватили новый остров
                islands = self.intel.get('islands', {})
                if next_step not in islands:
                    islands[str(next_step)] = []
                islands[str(next_step)].append(round(energy, 2))
                self.intel.update('islands', islands)
                
                # Двигаем фронт
                if next_step > front:
                    self.intel.update('front_line', next_step)
            
            # Пауза между попытками
            time.sleep(3)