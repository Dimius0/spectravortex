#!/usr/bin/env python3
# =====================================================
# : rhizome_spotters.py
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
# 1. Я
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
        self.rhizome = None
        
    def set_rhizome(self, rhizome):
        self.rhizome = rhizome
        
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
            
        print(f"   🕵️ азвёрнуто разведчиков: {len(self.scouts)}")
        
    def tick(self):
        for scout in self.scouts:
            signal = scout.scan()
            if signal:
                anom_id = self.buffer.add(signal, scout.position)
                if signal >= 2.5:
                    self.buffer.promote_to_target(anom_id)
                    
                if signal >= 2.0 and scout.type in [ScoutType.MEDIUM, ScoutType.HEAVY]:
                    if self.rhizome and not self.rhizome.spotter_manager.get_correction_for_target(anom_id):
                        self.rhizome.assign_spotter(scout.id, anom_id)
                        
            scout.move()

# =====================================================
# 4. ТЩ
# =====================================================

class Spotter:
    def __init__(self, scout):
        self.scout = scout
        self.locked_target_id = None
        self.locked_target_pos = None
        self.correction_factor = 0.0
        self.active = False
        
    def lock(self, target_id: int, target_pos: Tuple[float, float]):
        self.locked_target_id = target_id
        self.locked_target_pos = target_pos
        self.active = True
        print(f"   🎯 орректировщик {self.scout.id} закрепился за целью {target_id}")
        
    def release(self):
        self.locked_target_id = None
        self.locked_target_pos = None
        self.correction_factor = 0.0
        self.active = False
        
    def update_correction(self):
        if not self.active or not self.locked_target_pos:
            self.correction_factor = 0.0
            return
            
        dist = math.dist(self.scout.position, self.locked_target_pos)
        max_range = self.scout.range
        
        if dist <= max_range:
            self.correction_factor = 1.0 - (dist / max_range) * 0.5
        else:
            self.correction_factor = max(0.0, 1.0 - (dist / max_range))
            
        self.correction_factor = max(0.0, min(1.0, self.correction_factor))
        
    def get_correction(self) -> float:
        self.update_correction()
        return self.correction_factor

class SpotterManager:
    def __init__(self, swarm: ScoutSwarm):
        self.swarm = swarm
        self.spotters: Dict[int, Spotter] = {}
        self.target_to_spotter: Dict[int, int] = {}
        
    def assign_spotter(self, scout_id: int, target_id: int, target_pos: Tuple[float, float]) -> bool:
        scout = None
        for s in self.swarm.scouts:
            if s.id == scout_id:
                scout = s
                break
                
        if not scout:
            return False
            
        if scout_id in self.spotters and self.spotters[scout_id].active:
            return False
            
        if target_id in self.target_to_spotter:
            return False
            
        if scout_id not in self.spotters:
            self.spotters[scout_id] = Spotter(scout)
            
        spotter = self.spotters[scout_id]
        spotter.lock(target_id, target_pos)
        
        self.target_to_spotter[target_id] = scout_id
        return True
        
    def release_spotter(self, scout_id: int):
        if scout_id in self.spotters:
            old_target = self.spotters[scout_id].locked_target_id
            if old_target and old_target in self.target_to_spotter:
                del self.target_to_spotter[old_target]
            self.spotters[scout_id].release()
            
    def release_by_target(self, target_id: int):
        if target_id in self.target_to_spotter:
            scout_id = self.target_to_spotter[target_id]
            self.release_spotter(scout_id)
            
    def get_correction_for_target(self, target_id: int) -> float:
        if target_id not in self.target_to_spotter:
            return 0.0
            
        scout_id = self.target_to_spotter[target_id]
        if scout_id not in self.spotters:
            return 0.0
            
        return self.spotters[scout_id].get_correction()
        
    def update_all(self):
        for spotter in self.spotters.values():
            if spotter.active:
                spotter.update_correction()
                
    def get_active_spotters(self) -> List[int]:
        return [sid for sid, s in self.spotters.items() if s.active]

# =====================================================
# 5. ЬС
# =====================================================

class PulseHunter:
    def __init__(self, buffer: AnomalyBuffer, spotter_manager: SpotterManager):
        self.buffer = buffer
        self.spotter_manager = spotter_manager
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
        base_chance = 0.3 + 0.5 * phase_factor
        
        correction = self.spotter_manager.get_correction_for_target(target.id)
        hit_chance = base_chance + correction * 0.4
        hit_chance = min(0.95, hit_chance)
        
        self.strikes += 1
        
        if random.random() < hit_chance:
            self.hits += 1
            self.spotter_manager.release_by_target(target.id)
            self.buffer.targets.remove(target)
            self.cooldown = 3
            corr_info = f" (попр {correction:.2f})" if correction > 0 else ""
            return f"💥 ! ель {target.id} (сила {target.power:.1f}){corr_info}"
        else:
            self.cooldown = 1
            corr_info = f" (попр {correction:.2f})" if correction > 0 else ""
            return f"💢 ромах по цели {target.id}{corr_info}"

# =====================================================
# 6. Ы
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
        print(f"   🧬 азвёрнуто клонов: {len(self.clones)}")
        
    def broadcast(self, tick: int, phase: float):
        for clone in self.clones:
            clone.receive_beat(tick, phase)

# =====================================================
# 7. Т
# =====================================================

class Metrics:
    def __init__(self):
        self.tick_count = 0
        self.start_time = time.time()
        self.last_report_time = self.start_time
        
    def tick(self, beat: PulseBeat, swarm: ScoutSwarm, buffer: AnomalyBuffer, pulse: PulseHunter, spotters: SpotterManager):
        self.tick_count += 1
        
        now = time.time()
        if now - self.last_report_time >= 1.0:
            uptime = now - self.start_time
            active_spotters = len(spotters.get_active_spotters())
            print(f"\n📊 ТТ {beat.tick} |  {beat.phase:.3f}")
            print(f"   🕵️ азведчиков: {len(swarm.scouts)} | орректировщиков: {active_spotters}")
            print(f"   📦 номалий: {len(buffer.buffer)} | елей: {len(buffer.get_active_targets())}")
            print(f"   🔫 даров: {pulse.strikes} | опаданий: {pulse.hits}")
            if pulse.strikes > 0:
                print(f"   🎯 Точность: {pulse.hits/pulse.strikes:.1%}")
            print(f"   ⏱️ ремени: {uptime:.1f}с")
            self.last_report_time = now

# =====================================================
# 8. Я С
# =====================================================

class Rhizome:
    def __init__(self, ticks_per_second: float = 100.0):
        print("\n🧱 С -2 С ТЩ")
        print("="*70)
        
        self.sync = RealTimeSynchronizer(ticks_per_second)
        self.buffer = AnomalyBuffer()
        self.swarm = ScoutSwarm(self.buffer)
        self.swarm.set_rhizome(self)
        self.spotter_manager = SpotterManager(self.swarm)
        self.pulse = PulseHunter(self.buffer, self.spotter_manager)
        self.clones = CloneSwarm()
        self.metrics = Metrics()
        
        self.running = False
        self.tick_thread = None
        
    def deploy(self, 
               light_scouts: int = 5, 
               medium_scouts: int = 3, 
               heavy_scouts: int = 1,
               clone_positions: List[Tuple[float, float]] = [(100,100), (-100,-100), (0,200)]):
        
        self.swarm.deploy(light_scouts, medium_scouts, heavy_scouts)
        self.clones.deploy(clone_positions)
        print("="*70)
        
    def assign_spotter(self, scout_id: int, target_id: int) -> bool:
        target_pos = None
        for anom in self.buffer.buffer:
            if anom.id == target_id:
                target_pos = anom.position
                break
                
        if target_pos:
            return self.spotter_manager.assign_spotter(scout_id, target_id, target_pos)
        return False
        
    def _tick_loop(self):
        while self.running:
            beat = self.sync.beat()
            self.clones.broadcast(beat.tick, beat.phase)
            self.swarm.tick()
            self.spotter_manager.update_all()
            result = self.pulse.tick(beat.phase)
            if result:
                print(f"   {result}")
            self.metrics.tick(beat, self.swarm, self.buffer, self.pulse, self.spotter_manager)
            time.sleep(0.001)
            
    def start(self):
        if self.running:
            return
            
        self.running = True
        self.tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self.tick_thread.start()
        print("🚀 -2 С ТЩ Щ")
        print("   орректировщики: ТЫ")
        print("="*70)
        
    def stop(self):
        self.running = False
        if self.tick_thread:
            self.tick_thread.join(timeout=1.0)
        print("\n⏹️ СТ")
        print("="*70)
        print(f"ТЫ Т:")
        print(f"   Тактов: {self.metrics.tick_count}")
        print(f"   даров: {self.pulse.strikes} | опаданий: {self.pulse.hits}")
        if self.pulse.strikes > 0:
            print(f"   Точность: {self.pulse.hits/self.pulse.strikes:.1%}")
        print("="*70)

# =====================================================
# 9. С
# =====================================================

def signal_handler(sig, frame):
    print("\n\n🛑 олучен сигнал остановки")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🔥"*35)
    print("🔥   -2: ТЩ   🔥")
    print("🔥"*35)
    
    r = Rhizome(ticks_per_second=100.0)
    r.deploy()
    r.start()
    
    print("\n🌊 ТЩ ЯТ ЬС")
    print("   Точность пойдёт вверх")
    print("   Ctrl+C для остановки")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        r.stop()
