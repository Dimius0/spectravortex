#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ: SCOUT STRATEGIC (стратегическая разведка)
Алгоритм:
1. Лёгкие разведчики (power=1) ищут аномалии (энергия > 30k) в ближнем космосе
2. При обнаружении аномалии — вызывают средних (power=2) для глубокого зондирования
3. Средние подтверждают и расширяют — вызывают тяжёлых (power=3)
4. Тяжёлые берут цель или фиксируют предел
5. Все данные стекаются в штаб, строится карта приоритетов
"""
import sys
import time
import random
import threading
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_PATH))

class StrategicScoutUnit:
    """Разведчик с приоритетами и вызовом подкрепления"""
    def __init__(self, name, power, intel, command_center):
        self.name = name
        self.power = power  # 1 - лёгкий, 2 - средний, 3 - тяжёлый
        self.intel = intel
        self.cmd = command_center  # штаб для вызова подкрепления
        self.current_target = None
        self.anomaly_threshold = 30000  # порог аномалии
        self.running = True

    def run(self):
        print(f"   🔭 {self.name} (power={self.power}) заступил на дежурство")
        
        while self.running:
            # Если нет цели — получаем от штаба
            if self.current_target is None:
                self.current_target = self.cmd.get_next_target(self.power)
                if self.current_target:
                    print(f"🔭 {self.name}: получена цель {self.current_target}")
                else:
                    # Если целей нет — разведываем самостоятельно
                    self.current_target = self._explore()
            
            if not self.current_target:
                time.sleep(60)
                continue

            # Пытаемся взять цель
            front = self.intel.get('front_line', 138)
            success, energy = self._probe(self.current_target, front)
            
            # Докладываем в штаб
            self.cmd.report_result(
                scout_name=self.name,
                power=self.power,
                target=self.current_target,
                success=success,
                energy=energy
            )

            # Если успех — двигаем фронт и ищем новую цель
            if success:
                print(f"🔭 {self.name}: ✅ ЦЕЛЬ {self.current_target} ВЗЯТА! энергия {energy:.0f}")
                if self.current_target > front:
                    self.intel.update('front_line', self.current_target)
                self.current_target = None
            else:
                # Если не успех, но энергия высокая — может быть аномалия
                if energy > self.anomaly_threshold:
                    print(f"🔭 {self.name}: ⚡ АНОМАЛИЯ на {self.current_target} (энергия {energy:.0f})")
                    self.cmd.report_anomaly(self.current_target, energy, self.power)
                
                # Лёгкие и средние могут переключаться, тяжёлые долбят до упора
                if self.power < 3:
                    self.current_target = None
                else:
                    # Тяжёлый делает паузу и бьёт снова
                    time.sleep(1800)  # 30 мин

            # Пауза между попытками (зависит от мощности)
            time.sleep(600 * self.power)

    def _probe(self, target, from_n):
        """Тест с учётом мощности"""
        distance = abs(target - from_n)
        
        # Базовый шанс падает с расстоянием
        base_chance = max(0, 1 - (distance / 10000))
        # Мощность повышает шанс
        power_bonus = self.power * 0.1
        success = random.random() < min(0.95, base_chance + power_bonus)
        
        # Энергия растёт с расстоянием и мощностью
        energy = 20000 + distance * 5 + random.randint(-2000, 2000) + self.power * 2000
        
        return success, energy

    def _explore(self):
        """Самостоятельная разведка (когда нет целей от штаба)"""
        if self.power == 1:
            # Лёгкие щупают ближний космос
            candidates = [2000, 3000, 4000, 5000, 6000, 7000]
        elif self.power == 2:
            # Средние — средний
            candidates = [8000, 9000, 10000, 12000, 15000]
        else:
            # Тяжёлые — дальний
            candidates = [20000, 25000, 30000, 40000, 50000]
        
        # Берём случайную неразведанную цель
        recon = self.intel.get('strategic_recon', {})
        for c in random.sample(candidates, len(candidates)):
            if str(c) not in recon:
                return c
        return None

    def stop(self):
        self.running = False


class CommandCenter:
    """Штаб стратегической разведки"""
    def __init__(self, intel):
        self.intel = intel
        self.anomalies = []  # список аномалий для приоритетной обработки
        self.target_queue = {
            1: [],  # цели для лёгких
            2: [],  # для средних
            3: []   # для тяжёлых
        }
        self.results = []

    def report_result(self, scout_name, power, target, success, energy):
        """Фиксируем результат разведки"""
        result = {
            'scout': scout_name,
            'power': power,
            'target': target,
            'success': success,
            'energy': energy,
            'timestamp': time.time()
        }
        self.results.append(result)
        
        # Сохраняем в общую память
        recon = self.intel.get('strategic_recon', {})
        if str(target) not in recon:
            recon[str(target)] = []
        recon[str(target)].append({
            'success': success,
            'energy': energy,
            'power': power
        })
        self.intel.update('strategic_recon', recon)

    def report_anomaly(self, target, energy, discovered_by_power):
        """Аномалия найдена — ставим в приоритет для разведки следующих уровней"""
        self.anomalies.append({
            'target': target,
            'energy': energy,
            'discovered_by': discovered_by_power,
            'timestamp': time.time()
        })
        
        # Если аномалию нашёл лёгкий (power=1) — ставим в очередь средним
        if discovered_by_power == 1:
            self.target_queue[2].append(target + 2000)  # средний идёт глубже
            self.target_queue[2].append(target + 5000)
        # Если средний — ставим тяжёлым
        elif discovered_by_power == 2:
            self.target_queue[3].append(target + 5000)
            self.target_queue[3].append(target + 10000)

    def get_next_target(self, for_power):
        """Выдаём следующую цель для разведчика данного уровня"""
        # Сначала приоритетные цели из очереди
        if self.target_queue[for_power]:
            return self.target_queue[for_power].pop(0)
        
        # Если очередь пуста — None (разведчик ищет сам)
        return None


class StrategicScoutSquadModule:
    """Управление стратегической разведкой"""
    def __init__(self, intel):
        self.intel = intel
        self.cmd = CommandCenter(intel)
        self.units = []
        self.threads = []
        self.running = True

    def run(self):
        print("\n🔭 СТРАТЕГИЧЕСКАЯ РАЗВЕДКА запущена")
        print("   Состав: 2 лёгких, 2 средних, 2 тяжёлых разведчика")
        print("   Алгоритм: лёгкие ищут аномалии → средние подтверждают → тяжёлые добивают")

        # Формируем отряд
        squad = [
            ("Лёгкий-1", 1),
            ("Лёгкий-2", 1),
            ("Средний-1", 2),
            ("Средний-2", 2),
            ("Тяжёлый-1", 3),
            ("Тяжёлый-2", 3)
        ]

        for name, power in squad:
            unit = StrategicScoutUnit(name, power, self.intel, self.cmd)
            self.units.append(unit)
            t = threading.Thread(target=unit.run, daemon=True)
            t.start()
            self.threads.append(t)
            print(f"   🔭 {name} (power={power}) в строю")

        while self.running:
            # Каждые 10 минут выводим статистику
            time.sleep(600)
            anomalies = len(self.cmd.anomalies)
            total_targets = len(self.intel.get('strategic_recon', {}))
            print(f"\n📊 СТАТИСТИКА: аномалий {anomalies}, целей разведано {total_targets}")

    def stop(self):
        self.running = False
        for unit in self.units:
            unit.stop()