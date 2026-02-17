#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ: РЕЙНДЖЕР
"""
import sys
import time
import random
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

def dummy_test(target, from_n, jump):
    """Имитация дальнего прыжка"""
    # Чем дальше цель, тем выше шанс коллапса, но и энергия растёт
    distance = abs(target - from_n)
    success = random.random() > (distance / 200)  # Риск растёт с дистанцией
    energy = 20000 + distance * 50 + random.randint(-1000, 1000)
    print(f"   🗡️ Рейнджер: прыжок {from_n}->{target} (+{jump}) -> {'✅' if success else '❌'} (энергия {energy:.0f})")
    return success, energy

class RangerModule:
    def __init__(self, intel):
        self.intel = intel
        self.name = "ranger"
        self.targets = [200, 250, 300, 350, 400, 450, 500]

    def run(self):
        print("\n🗡️ Рейнджер вышел на тропу.")
        target_index = 0

        while target_index < len(self.targets):
            front = self.intel.data.get('front_line', 138)
            target = self.targets[target_index]

            if target <= front:
                target_index += 1
                continue

            jump = target - front
            success, energy = dummy_test(target, front, jump)

            # Записываем результат в общую базу
            if 'target_500_data' not in self.intel.data:
                self.intel.data['target_500_data'] = []

            self.intel.data['target_500_data'].append({
                'target': target,
                'energy': energy,
                'success': success
            })
            self.intel.save()

            # Если успех, двигаем фронт
            if success and target > front:
                self.intel.update('front_line', target)

            # Предвестник гиперпрыжка?
            if not success and energy > 30000:
                print(f"⚡ Рейнджер: ОБНАРУЖЕН ВСПЛЕСК! Энергия {energy:.0f} на {target}")
                self.intel.update('hyper_ready', True)

            target_index += 1
            time.sleep(5)

        print("🗡️ Рейнджер закончил разведку.")