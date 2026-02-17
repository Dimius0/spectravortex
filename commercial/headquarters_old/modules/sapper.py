#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ: САПЁР
"""
import sys
import time
import random
from pathlib import Path

# Путь к ядру гравицапы
BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

# Заглушка для тестов (чтобы код работал без основного ядра)
def dummy_test(target, from_n, jump):
    """Имитация теста, пока нет связи с реальным safe_benchmark"""
    success = random.random() > 0.7  # 30% успеха для имитации
    energy = random.randint(20000, 30000)
    print(f"   💣 Сапёр: пробую {from_n}->{target} ({'+' if jump>0 else ''}{jump}) -> {'✅' if success else '❌'}")
    return success, energy

class SapperModule:
    def __init__(self, intel):
        self.intel = intel
        self.name = "sapper"

    def run(self):
        print("\n💣 Сапёр заступил на дежурство.")
        while True:
            front = self.intel.data.get('front_line', 138)

            # Исследуем ближние подступы
            for direction in [1, 2, 3, 5, -1, -2]:
                target = front + direction
                if target < 100:
                    continue

                # Имитация работы (позже заменим на реальный вызов)
                success, energy = dummy_test(target, front, direction)

                if success:
                    # Нашли новый остров
                    if target > self.intel.data.get('front_line', 0):
                        self.intel.update('front_line', target)
                    print(f"   🏝️ Сапёр: найден новый остров {target} (энергия {energy})")

                time.sleep(2)  # Пауза между попытками

            print(f"💣 Сапёр: цикл разведки завершён. Сплю 30 сек...")
            time.sleep(30)