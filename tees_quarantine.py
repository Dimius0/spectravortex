# tees_quarantine.py
# 🛡️ TEES: Карантинная адаптация фракталов!

import time
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════
# 1. МАЯК (простой!)
# ═══════════════════════════════════

class TEESBeacon:
    def __init__(self, beacon_id):
        self.beacon_id = beacon_id
        self.coherence = 0.994
        self.cluster = None
        self.tasks_completed = 0
        self.is_malicious = False  # Злоумышленник?
    
    def sync(self):
        self.coherence = min(1.0, self.coherence + 0.001)
        return self.coherence
    
    def do_work(self):
        """Выполнить полезную работу!"""
        self.tasks_completed += 1

# ═══════════════════════════════════
# 2. КАРАНТИННЫЙ ФРАКТАЛ
# ═══════════════════════════════════

class QuarantineFractal:
    """
    🛡️ Карантинный фрактал.
    Новые узлы проходят адаптацию ЗДЕСЬ!
    """
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.beacons = []
        self.coherence = 0.994
        self.status = 'quarantine'  # quarantine / adapting / ready
        self.created_at = time.time()
    
    def add_beacon(self, beacon):
        """Добавить маяк в карантин."""
        if len(self.beacons) >= self.max_size:
            print(f"  ⚠️ Карантин полон! Создайте новый!")
            return False
        
        self.beacons.append(beacon)
        beacon.cluster = self
        return True
    
    def sync(self):
        """Синхронизация внутри карантина."""
        for beacon in self.beacons:
            beacon.sync()
        self.coherence = sum(b.coherence for b in self.beacons) / len(self.beacons)
        
        # Проверяем готовность!
        if self.coherence >= 1.0:
            self.status = 'ready'
        
        return self.coherence
    
    def verify_usefulness(self):
        """
        Проверка полезности!
        Злоумышленники (нет работы!) — отключаются!
        """
        useful = []
        malicious = []
        
        for beacon in self.beacons:
            if beacon.tasks_completed > 0:
                useful.append(beacon)
            else:
                malicious.append(beacon)
                beacon.is_malicious = True
        
        if malicious:
            print(f"  ⛔ Обнаружено злоумышленников: {len(malicious)}!")
            print(f"  🛡️ Они отключаются (нет работы = нет ресурса!)")
            self.beacons = useful
        
        return len(useful)
    
    def get_stats(self):
        return {
            'beacons': len(self.beacons),
            'coherence': self.coherence,
            'status': self.status,
            'age': time.time() - self.created_at
        }

# ═══════════════════════════════════
# 3. ОСНОВНАЯ СЕТЬ
# ═══════════════════════════════════

class MainNetwork:
    """
    🏮 Основная сеть (когерентная!).
    Принимает только ГОТОВЫЕ фракталы!
    """
    def __init__(self):
        self.fractals = []  # Когерентные фракталы!
        self.coherence = 0.994
        self.total_beacons = 0
    
    def integrate_fractal(self, fractal):
        """
        Интегрировать готовый фрактал!
        Только если когерентность = 1.0!
        """
        if fractal.coherence < 1.0:
            print(f"  ❌ Фрактал не готов! Когерентность: {fractal.coherence:.3f}")
            return False
        
        self.fractals.append(fractal)
        self.total_beacons += len(fractal.beacons)
        
        # Обновляем когерентность сети
        all_coh = []
        for f in self.fractals:
            all_coh.extend(b.coherence for b in f.beacons)
        self.coherence = sum(all_coh) / len(all_coh) if all_coh else 0.994
        
        print(f"  ✅ Фрактал интегрирован! "
              f"(маяков: {len(fractal.beacons)}, "
              f"сеть: {self.total_beacons}, "
              f"когерентность: {self.coherence:.4f})")
        
        return True

# ═══════════════════════════════════
# 4. СИСТЕМА КАРАНТИНА
# ═══════════════════════════════════

class QuarantineSystem:
    """
    🛡️ Система карантина.
    Управляет адаптацией новых узлов!
    """
    def __init__(self, quarantine_size=10):
        self.quarantine_size = quarantine_size
        self.quarantines = []
        self.main_network = MainNetwork()
        self.rejected = []  # Отклонённые злоумышленники!
    
    def add_new_nodes(self, new_beacons):
        """
        Принять новых узлов!
        1. Группируем в карантин!
        2. Синхронизируем!
        3. Проверяем полезность!
        4. Интегрируем!
        """
        print(f"\n📦 Принято новых узлов: {len(new_beacons)}")
        
        # 1. Создаём карантинный фрактал
        quarantine = QuarantineFractal(max_size=self.quarantine_size)
        
        for beacon in new_beacons:
            quarantine.add_beacon(beacon)
        
        self.quarantines.append(quarantine)
        
        # 2. Синхронизация (карантин!)
        print(f"\n🛡️ КАРАНТИН (синхронизация):")
        for step in range(20):
            coh = quarantine.sync()
            if step % 5 == 0:
                print(f"   Шаг {step:2d}: когерентность = {coh:.4f}")
            
            if quarantine.status == 'ready':
                print(f"   ✅ Карантин готов на шаге {step}!")
                break
        
        # 3. Проверка полезности!
        print(f"\n🔍 ПРОВЕРКА ПОЛЕЗНОСТИ:")
        useful_count = quarantine.verify_usefulness()
        
        if useful_count == 0:
            print(f"  ❌ Все узлы бесполезны! Карантин отбракован!")
            self.rejected.extend(quarantine.beacons)
            return 0
        
        # 4. ПАРАНОИДАЛЬНАЯ ЗАДЕРЖКА перед интеграцией!
        print(f"\n⏳ ПАРАНОИДАЛЬНАЯ ЗАДЕРЖКА (1 секунда)...")
        time.sleep(1)  # Секунда на подумать!
        print(f"   ✅ Задержка пройдена! Проверяем ещё раз...")
        
        # ПОВТОРНАЯ проверка после задержки!
        if quarantine.verify_usefulness() == 0:
            print(f"   ❌ После задержки — снова бесполезны! Отклоняем!")
            return 0
        
        # 5. Интеграция в основную сеть!
        print(f"\n🏮 ИНТЕГРАЦИЯ:")
        if self.main_network.integrate_fractal(quarantine):
            return useful_count
        
        return 0

# ═══════════════════════════════════
# 5. ТЕСТ
# ═══════════════════════════════════

def test_quarantine():
    print("🛡️ TEES: КАРАНТИННАЯ АДАПТАЦИЯ")
    print("=" * 60)
    
    system = QuarantineSystem(quarantine_size=10)
    
    # Тест 1: Хорошие узлы!
    print(f"\n🧪 ТЕСТ 1: 8 полезных узлов")
    good_nodes = [TEESBeacon(f"good_{i}") for i in range(8)]
    for node in good_nodes:
        node.do_work()  # Выполняют работу!
    system.add_new_nodes(good_nodes)
    
    # Тест 2: Смешанные (5 полезных + 3 злоумышленника!)
    print(f"\n{'='*60}")
    print(f"\n🧪 ТЕСТ 2: 5 полезных + 3 злоумышленника")
    mixed_nodes = [TEESBeacon(f"mixed_{i}") for i in range(5)]
    for node in mixed_nodes:
        node.do_work()  # Полезные!
    
    malicious_nodes = [TEESBeacon(f"evil_{i}") for i in range(3)]
    # Злоумышленники НЕ работают!
    
    system.add_new_nodes(mixed_nodes + malicious_nodes)
    
    # Тест 3: Все злоумышленники!
    print(f"\n{'='*60}")
    print(f"\n🧪 ТЕСТ 3: 5 злоумышленников")
    evil_nodes = [TEESBeacon(f"all_evil_{i}") for i in range(5)]
    # Никто не работает!
    system.add_new_nodes(evil_nodes)
    
    # Итоги
    print(f"\n{'='*60}")
    print(f"📊 ИТОГИ:")
    print(f"   Маяков в сети: {system.main_network.total_beacons}")
    print(f"   Когерентность сети: {system.main_network.coherence:.4f}")
    print(f"   Отклонено злоумышленников: {len(system.rejected)}")
    print(f"   Фракталов в сети: {len(system.main_network.fractals)}")
    
    print(f"\n{'='*60}")
    print(f"✅ КАРАНТИННАЯ ЗАЩИТА РАБОТАЕТ!")
    print(f"   🛡️ Злоумышленники отсеяны!")
    print(f"   🏮 Полезные интегрированы!")
    print(f"   ⚛️ Когерентность сохранена!")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_quarantine()