#!/usr/bin/env python3
# =====================================================
# : rhizome_real_pulse.py
# С: python rhizome_real_pulse.py
# СТТС: 
# =====================================================

import time
import threading
import random
import math
from collections import deque
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
import os
import signal
import sys

# =====================================================
# 1. Я (CORE) - с реальным пульсом
# =====================================================

@dataclass
class PulseBeat:
    tick: int
    timestamp: float
    phase: float

class RealTimeSynchronizer:
    def __init__(self, ticks_per_second: float = 100.0, sync_word: int = 11895):
        self.ticks_per_second = ticks_per_second
        self.sync_word = sync_word
        self.current_tick = 0
        self.beats = deque(maxlen=1000)
        self.last_beat_time = None
        self.boot_time = self._get_boot_time()
        
    def _get_boot_time(self) -> float:
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('btime'):
                        return float(line.split()[1])
        except:
            return time.time() - 3600
    
    def _get_uptime(self) -> float:
        try:
            with open('/proc/uptime', 'r') as f:
                return float(f.read().split()[0])
        except:
            # ля Windows - эмуляция uptime
            return time.time() - self.boot_time
    
    def beat(self) -> PulseBeat:
        uptime = self._get_uptime()
        expected_tick = int(uptime * self.ticks_per_second)
        
        if expected_tick > self.current_tick:
            self.current_tick = expected_tick
            
        phase = (uptime * self.ticks_per_second) % 1.0
        
        beat = PulseBeat(
            tick=self.current_tick,
            timestamp=time.time(),
            phase=phase
        )
        
        self.beats.append(beat)
        self.last_beat_time = time.time()
        
        return beat

# =====================================================
# 2.  
# =====================================================

@dataclass
class Anomaly:
    id: int
    power: float
    position: Tuple[float, float]
    timestamp: float
    target: bool = False

class AnomalyBuffer:
    def __init__(self, capacity: int = 1000):
        self.buffer: List[Anomaly] = []
        self.targets: List[Anomaly] = []
        self.capacity = capacity
        self.counter = 0
        
    def add(self, power: float, position: Tuple[float, float]) -> int:
        anom = Anomaly(self.counter, power, position, time.time())
        self.buffer.append(anom)
        self.counter += 1
        
        if len(self.buffer) > self.capacity:
            self.buffer = self.buffer[-self.capacity:]
            
        return anom.id
    
    def promote_to_target(self, anomaly_id: int):
        for anom in self.buffer:
            if anom.id == anomaly_id:
                anom.target = True
                self.targets.append(anom)
                break
                
    def get_active_targets(self) -> List[Anomaly]:
        now = time.time()
        self.targets = [t for t in self.targets if now - t.timestamp < 10.0]
        return self.targets

# =====================================================
# 3. 
# =====================================================

class ScoutType:
    LIGHT = 1
    MEDIUM = 2
    HEAVY = 3

class Scout:
    def __init__(self, scout_id: int, scout_type: int, position: Tuple[float, float]):
        self.id = scout_id
        self.type = scout_type
        self.position = position
        self.active = True
        self.range = {1: 10.0, 2: 30.0, 3: 100.0}[scout_type]
        
    def scan(self) -> Optional[float]:
        if not self.active:
            return None
            
        dist = math.sqrt(self.position[0]**2 + self.position[1]**2)
        prob = 0.3 * (1.0 - min(1.0, dist / 500.0))
        
        if random.random() < prob:
            return self.type + random.gauss(0, 0.2)
        return None
    
    def move(self):
        drift = (random.gauss(0, 0.5), random.gauss(0, 0.5))
        self.position = (self.position[0] + drift[0], self.position[1] + drift[1])

class ScoutSwarm:
    def __init__(self, buffer: AnomalyBuffer):
        self.buffer = buffer
        self.scouts: List[Scout] = []
        self.next_id = 0
        
    def deploy(self, count_light: int, count_medium: int, count_heavy: int):
        for _ in range(count_light):
            pos = (random.uniform(-50, 50), random.uniform(-50, 50))
            self.scouts.append(Scout(self.next_id, ScoutType.LIGHT, pos))
            self.next_id += 1
            
        for _ in range(count_medium):
            pos = (random.uniform(-100, 100), random.uniform(-100, 100))
            self.scouts.append(Scout(self.next_id, ScoutType.MEDIUM, pos))
            self.next_id += 1
            
        for _ in range(count_heavy):
            pos = (random.uniform(-200, 200), random.uniform(-200, 200))
            self.scouts.append(Scout(self.next_id, ScoutType.HEAVY, pos))
            self.next_id += 1
            
        print(f"   азвёрнуто разведчиков: {len(self.scouts)}")
        
    def tick(self):
        for scout in self.scouts:
            signal = scout.scan()
            if signal:
                anom_id = self.buffer.add(signal, scout.position)
                if signal >= 2.5:
                    self.buffer.promote_to_target(anom_id)
            scout.move()

# =====================================================
# 4. ЬС (HUNTER)
# =====================================================

class PulseHunter:
    def __init__(self, buffer: AnomalyBuffer):
        self.buffer = buffer
        self.strikes = 0
        self.hits = 0
        self.cooldown = 0
        
    def tick(self, phase: float):
        if self.cooldown > 0:
            self.cooldown -= 1
            return None
            
        targets = self.buffer.get_active_targets()
        if not targets:
            return None
            
        target = targets[0]
        
        phase_factor = 1.0 - abs(phase - 0.5) * 2
        hit_chance = 0.3 + 0.5 * phase_factor
        
        self.strikes += 1
        
        if random.random() < hit_chance:
            self.hits += 1
            self.buffer.targets.remove(target)
            self.cooldown = 3
            return f"💥 ! ель {target.id} (сила {target.power:.1f})"
        else:
            self.cooldown = 1
            return f"💢 ромах по цели {target.id}"

# =====================================================
# 5. Ы (Ш)
# =====================================================

class Clone:
    def __init__(self, clone_id: int, position: Tuple[float, float]):
        self.id = clone_id
        self.position = position
        self.last_beat = None
        self.active = False
        
    def receive_beat(self, tick: int, phase: float):
        self.last_beat = (tick, phase, time.time())

class CloneSwarm:
    def __init__(self):
        self.clones = []
        
    def deploy(self, positions: List[Tuple[float, float]]):
        for i, pos in enumerate(positions):
            self.clones.append(Clone(i, pos))
        print(f"   азвёрнуто клонов: {len(self.clones)}")
        
    def broadcast(self, tick: int, phase: float):
        for clone in self.clones:
            clone.receive_beat(tick, phase)

# =====================================================
# 6. Т
# =====================================================

class Metrics:
    def __init__(self):
        self.tick_count = 0
        self.start_time = time.time()
        self.last_report_time = self.start_time
        
    def tick(self, beat: PulseBeat, swarm: ScoutSwarm, buffer: AnomalyBuffer, pulse: PulseHunter):
        self.tick_count += 1
        
        now = time.time()
        if now - self.last_report_time >= 1.0:
            uptime = now - self.start_time
            print(f"\n📊 ТТ {beat.tick} |  {beat.phase:.3f}")
            print(f"   азведчиков: {len(swarm.scouts)}")
            print(f"   номалий: {len(buffer.buffer)}")
            print(f"   елей: {len(buffer.get_active_targets())}")
            print(f"   даров: {pulse.strikes} | опаданий: {pulse.hits}")
            if pulse.strikes > 0:
                print(f"   Точность: {pulse.hits/pulse.strikes:.1%}")
            print(f"   ремени прошло: {uptime:.1f}с")
            self.last_report_time = now

# =====================================================
# 7. Я С
# =====================================================

class Rhizome:
    def __init__(self, ticks_per_second: float = 100.0):
        print("\n🧱 С -2")
        print("="*60)
        
        self.sync = RealTimeSynchronizer(ticks_per_second)
        self.buffer = AnomalyBuffer()
        self.swarm = ScoutSwarm(self.buffer)
        self.pulse = PulseHunter(self.buffer)
        self.clones = CloneSwarm()
        self.metrics = Metrics()
        
        self.running = False
        self.tick_thread = None
        
    def deploy(self, 
               light_scouts: int = 3, 
               medium_scouts: int = 2, 
               heavy_scouts: int = 1,
               clone_positions: List[Tuple[float, float]] = [(100,100), (-100,-100)]):
        
        self.swarm.deploy(light_scouts, medium_scouts, heavy_scouts)
        self.clones.deploy(clone_positions)
        print("="*60)
        
    def _tick_loop(self):
        while self.running:
            beat = self.sync.beat()
            self.clones.broadcast(beat.tick, beat.phase)
            self.swarm.tick()
            result = self.pulse.tick(beat.phase)
            if result:
                print(f"   {result}")
            self.metrics.tick(beat, self.swarm, self.buffer, self.pulse)
            time.sleep(0.001)
            
    def start(self):
        if self.running:
            return
            
        self.running = True
        self.tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self.tick_thread.start()
        print("🚀 -2 Щ")
        print("   ульс: реальный (/proc/uptime)")
        print("   астота: {} тактов/сек".format(self.sync.ticks_per_second))
        print("   Слово синхронизации: {}".format(self.sync.sync_word))
        print("="*60)
        
    def stop(self):
        self.running = False
        if self.tick_thread:
            self.tick_thread.join(timeout=1.0)
        print("\n⏹️ -2 СТ")
        print("="*60)
        print(f"тоговые метрики:")
        print(f"   сего тактов: {self.metrics.tick_count}")
        print(f"   даров: {self.pulse.strikes}")
        print(f"   опаданий: {self.pulse.hits}")
        if self.pulse.strikes > 0:
            print(f"   Точность: {self.pulse.hits/self.pulse.strikes:.1%}")
        print(f"   номалий в буфере: {len(self.buffer.buffer)}")
        print("="*60)

# =====================================================
# 8. С
# =====================================================

def signal_handler(sig, frame):
    print("\n\n🛑 олучен сигнал остановки")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n" + "🔥"*30)
    print("🔥   -2: ЬЫ ЬС   🔥")
    print("🔥"*30)
    
    r = Rhizome(ticks_per_second=100.0)
    
    r.deploy(
        light_scouts=5,
        medium_scouts=3,
        heavy_scouts=1,
        clone_positions=[(100,100), (-100,-100), (0,200)]
    )
    
    r.start()
    
    print("\n🌊 ССТ ЫШТ")
    print("   ажми Ctrl+C для остановки")
    print("   аза держится на времени системы")
    print("   лоны слушают")
    print("   азведчики ищут")
    print("   ульс бьёт")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        r.stop()
    
    print("\n✅ Ы")
