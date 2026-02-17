#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ: PULSEHUNTER
Задача: ловить пульс времени — запускать тесты на одной точке (1000)
в разное время, записывать успехи, энергии и таймштампы.
"""
import sys
import time
import random
import csv
from datetime import datetime
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

class PulseHunterModule:
    def __init__(self, intel):
        self.intel = intel
        self.name = "pulsehunter"
        self.target_n = 1000  # фиксированная точка
        self.log_path = BASE_PATH / "results" / "pulse_log.csv"
        self.running = True

    def run(self):
        print("\n⏱️  PulseHunter запущен. Цель: N=1000, ищу пульс...")
        self._init_log()

        while self.running:
            front = self.intel.get('front_line', 138)
            if front < self.target_n:
                print(f"⏱️  PulseHunter: жду, пока фронт ({front}) дойдёт до {self.target_n}...")
                time.sleep(60)
                continue

            # Запускаем тест
            success, energy = self._test_target()
            timestamp = datetime.now().isoformat(timespec='seconds')

            # Логируем
            self._log_result(timestamp, success, energy)

            if success:
                print(f"⏱️  PulseHunter: ✅ УСПЕХ на {self.target_n} | энергия {energy} | {timestamp}")
            else:
                print(f"⏱️  PulseHunter: ❌ коллапс на {self.target_n} | энергия {energy} | {timestamp}")

            # Ждём перед следующим запуском (случайный интервал)
            delay = random.randint(1800, 7200)  # от 30 мин до 2 часов
            print(f"⏱️  PulseHunter: пауза {delay//60} мин...")
            time.sleep(delay)

    def _test_target(self):
        """Имитация теста — позже заменится на реальный вызов run_test"""
        # TODO: заменить на реальный вызов run_test(self.target_n)
        success = random.random() > 0.5
        energy = random.randint(20000, 30000) if success else 0
        return success, energy

    def _init_log(self):
        """Создаёт CSV с заголовками, если файла нет"""
        if not self.log_path.exists():
            with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'target_n', 'success', 'energy'])

    def _log_result(self, timestamp, success, energy):
        """Пишет результат в CSV"""
        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, self.target_n, 1 if success else 0, energy])

    def stop(self):
        self.running = False
        