#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ: ГЛУБОКИЙ РАЗВЕДЧИК
Цель: 10000. Выживет — закрепится. Нет — даст данные.
"""
import sys
import time
import random
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

def deep_space_test(target):
    """Имитация глубокого космоса"""
    # Чем дальше, тем выше риск, но и потенциальная энергия
    distance_factor = target / 1000
    success = random.random() > (1 - 1/(distance_factor + 1))  # Шанс падает с расстоянием
    energy = 20000 + (target * 5) + random.randint(-5000, 5000)
    
    if success:
        print(f"   🌌 РАЗВЕДЧИК: **УСПЕХ** на {target}! Энергия {energy:.0f}")
    else:
        print(f"   🌌 РАЗВЕДЧИК: {target} -> ❌ (энергия {energy:.0f})")
    
    return success, energy

class DeepScoutModule:
    def __init__(self, intel):
        self.intel = intel
        self.name = "deep_scout"
        self.targets = [500, 1000, 2000, 5000, 7500, 10000]

    def run(self):
        print("\n🌌 ГЛУБОКИЙ РАЗВЕДЧИК вышел в открытый космос")
        
        for target in self.targets:
            front = self.intel.get('front_line', 138)
            
            # Прыгаем прямо с текущего фронта
            success, energy = deep_space_test(target)
            
            # Сохраняем данные
            deep_data = self.intel.get('deep_recon', {})
            deep_data[str(target)] = {
                'energy': energy,
                'success': success,
                'from_front': front
            }
            self.intel.update('deep_recon', deep_data)
            
            # Если успех и это наша главная цель (1000)
            if success and target == self.intel.get('primary_target'):
                print(f"⚡⚡⚡ ГЛАВНАЯ ЦЕЛЬ {target} ДОСТИГНУТА! Переключаю приоритеты!")
                self.intel.update('primary_target', target)
                # Разведчик закрепляется и становится базой
                if target > self.intel.get('front_line'):
                    self.intel.update('front_line', target)
            
            time.sleep(2)
        
        print("🌌 Глубокий разведчик закончил миссию. Данные в штабе.")