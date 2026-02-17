#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ: SCOUT SQUAD HEAVY (дальнобойная эскадрилья)
Задача: 5 разведчиков разной мощности на сверхдальние цели
"""
import sys
import time
import random
import threading
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

class HeavyScoutUnit:
    """Один дальнобойный разведчик со своим калибром"""
    def __init__(self, target, power, intel):
        self.target = target
        self.power = power  # мощность: 1 - лёгкий, 2 - средний, 3 - тяжёлый
        self.intel = intel
        self.name = f"heavy_scout_{target}_{power}"
        self.running = True

    def run(self):
        """Жизненный цикл"""
        while self.running:
            front = self.intel.get('front_line', 138)
            
            # Если фронт обогнал цель — ищем новую
            if front > self.target:
                new_target = self._find_next_target()
                if new_target:
                    print(f"🔭⚡ {self.name}: цель {self.target} пройдена, новая цель {new_target}")
                    self.target = new_target
                else:
                    time.sleep(3600)
                    continue

            # Дальность до цели
            distance = self.target - front
            jump = distance
            
            # Мощность влияет на шанс успеха и потребление ресурсов
            success, energy = self._probe(self.target, front, jump)
            
            if success:
                print(f"🔭⚡ {self.name}: ✅ ЦЕЛЬ {self.target} ВЗЯТА! энергия {energy:.0f}")
                
                # Сохраняем успех
                heavy_recon = self.intel.get('heavy_recon', {})
                if str(self.target) not in heavy_recon:
                    heavy_recon[str(self.target)] = []
                heavy_recon[str(self.target)].append({
                    'energy': energy,
                    'success': True,
                    'power': self.power,
                    'timestamp': time.time()
                })
                self.intel.update('heavy_recon', heavy_recon)
                
                # Двигаем фронт
                if self.target > front:
                    self.intel.update('front_line', self.target)
            else:
                print(f"🔭⚡ {self.name}: {self.target} -> ❌ (энергия {energy:.0f})")
                
                # Сохраняем неудачу
                heavy_recon = self.intel.get('heavy_recon', {})
                if str(self.target) not in heavy_recon:
                    heavy_recon[str(self.target)] = []
                heavy_recon[str(self.target)].append({
                    'energy': energy,
                    'success': False,
                    'power': self.power,
                    'timestamp': time.time()
                })
                self.intel.update('heavy_recon', heavy_recon)

            # Пауза зависит от мощности (тяжёлые отдыхают дольше)
            base_pause = 1800  # 30 мин
            pause = base_pause * self.power
            time.sleep(pause)

    def _probe(self, target, from_n, jump):
        """Тест с учётом мощности разведчика"""
        distance = abs(target - from_n)
        
        # Мощность повышает шанс, но не гарантирует успех
        power_bonus = self.power * 0.15  # +15% за уровень мощности
        base_chance = max(0, 1 - (distance / 5000))  # базовый шанс
        success_chance = min(0.95, base_chance + power_bonus)
        
        success = random.random() < success_chance
        energy = 20000 + distance * 8 + random.randint(-3000, 3000) + (self.power * 2000)
        
        return success, energy

    def _find_next_target(self):
        """Выбирает следующую цель по уровню мощности"""
        # Разные цели для разной мощности
        targets_by_power = {
            1: [2500, 3500, 4500, 5500, 6500],      # лёгкие, ближние
            2: [8000, 12000, 15000, 18000],          # средние
            3: [20000, 25000, 30000, 50000]           # тяжёлые, дальний космос
        }
        
        heavy_recon = self.intel.get('heavy_recon', {})
        candidates = targets_by_power.get(self.power, [])
        
        for c in candidates:
            if str(c) not in heavy_recon:
                return c
        return None

    def stop(self):
        self.running = False


class HeavyScoutSquadModule:
    """Управление эскадрильей дальнобойщиков"""
    def __init__(self, intel):
        self.intel = intel
        self.name = "heavy_scout_squad"
        self.units = []
        self.threads = []
        self.running = True

    def run(self):
        print("\n🔭⚡ ДАЛЬНОБОЙНАЯ ЭСКАДРИЛЬЯ запущена")
        print("   Состав: 1 лёгкий, 2 средних, 2 тяжёлых разведчика")

        # Формируем отряд: мощность, цель
        squad = [
            (1, 2500),   # лёгкий на 2500
            (2, 8000),   # средний на 8000
            (2, 12000),  # средний на 12000
            (3, 20000),  # тяжёлый на 20000
            (3, 30000)   # тяжёлый на 30000
        ]

        for power, target in squad:
            unit = HeavyScoutUnit(target, power, self.intel)
            self.units.append(unit)
            t = threading.Thread(target=unit.run, daemon=True)
            t.start()
            self.threads.append(t)
            power_name = {1: "лёгкий", 2: "средний", 3: "тяжёлый"}[power]
            print(f"   🔭⚡ {power_name} разведчик нацелен на {target}")

        while self.running:
            time.sleep(10)

    def stop(self):
        self.running = False
        for unit in self.units:
            unit.stop()