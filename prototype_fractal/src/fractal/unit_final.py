"""
FractalUnit - ФИНАЛЬНАЯ версия: ЗАПРЕТ на передачу в повреждённые узлы.
"""

import numpy as np
from typing import List, Optional, Dict, Any
import time

try:
    from .internal_state import InternalState
    from .intuition import IntuitionEngine
    HAS_NEW_MODULES = True
except ImportError:
    HAS_NEW_MODULES = False

class FractalUnit:
    def __init__(self, unit_id: str, initial_load: float = 0.0):
        self.id = unit_id
        self.load = initial_load
        self.health = 1.0
        self.neighbors: List["FractalUnit"] = []
        self.local_potential = 0.0
        self.load_history = [initial_load]
        
        if HAS_NEW_MODULES:
            self.state = InternalState(unit_id)
            self.intuition = IntuitionEngine(f"intuition_{unit_id}")
    
    def add_neighbor(self, neighbor: "FractalUnit", bidirectional: bool = True):
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            if bidirectional:
                neighbor.add_neighbor(self, bidirectional=False)
    
    def compute_potential(self, target_load: float = 0.7, current_step: int = 0) -> float:
        if HAS_NEW_MODULES and self.state:
            self.state.update({
                "load": self.load,
                "health": self.health,
                "stress": abs(self.load - target_load)
            })
            analytic_data = self.state.get_for_analytics()
            effective_target = analytic_data.get("effective_target_load", target_load)
        else:
            effective_target = target_load
        
        load_component = (self.load - effective_target) ** 2
        health_penalty = (1.0 - self.health) * 0.5
        self.local_potential = load_component + health_penalty
        return self.local_potential
    
    def transfer_load(self, base_rate: float = 0.15, use_intuition: bool = True) -> float:  # 0.15!
        transferred_total = 0.0
        
        # СТРОГИЕ ПРАВИЛА:
        # 1. Повреждённые узлы (health < 0.7) ТОЛЬКО ОТДАЮТ здоровым (health >= 0.7)
        # 2. Здоровые узлы НИКОГДА не отдают повреждённым
        # 3. Здоровые узлы могут обмениваться между собой
        
        if self.health < 0.7:
            # ПОВРЕЖДЁННЫЙ УЗЕЛ - ТОЛЬКО ОТДАЁТ
            for neighbor in self.neighbors:
                # Только здоровым соседям!
                if neighbor.health < 0.7:
                    continue
                    
                # Только если наш потенциал выше
                if self.local_potential <= neighbor.local_potential:
                    continue
                
                # АГРЕССИВНАЯ ОТДАЧА
                transfer_power = 6.0 if self.health < 0.4 else 4.0
                transfer_amount = base_rate * (self.local_potential - neighbor.local_potential) * self.load * transfer_power
                
                # Можем отдать почти всё
                max_give = self.load * 0.99
                # Сосед может принять
                neighbor_can_take = (1.0 - neighbor.load) * 3.0
                
                safe_amount = min(transfer_amount, max_give, neighbor_can_take, 0.3)
                
                if safe_amount > 0.001:
                    self.load -= safe_amount
                    neighbor.load += safe_amount
                    transferred_total += safe_amount
                    
        else:
            # ЗДОРОВЫЙ УЗЕЛ
            for neighbor in self.neighbors:
                # НИКОГДА не отдаём повреждённым!
                if neighbor.health < 0.7:
                    continue
                
                potential_diff = self.local_potential - neighbor.local_potential
                
                if abs(potential_diff) < 0.01:
                    continue
                
                if potential_diff > 0:
                    # Мы отдаём другому здоровому
                    transfer_amount = base_rate * potential_diff * self.load * 0.8
                    
                    safe_amount = min(
                        transfer_amount,
                        self.load * 0.5,  # Здоровые отдают умеренно
                        (1.0 - neighbor.load) * 1.0,
                        0.1
                    )
                    
                    if safe_amount > 0.001:
                        self.load -= safe_amount
                        neighbor.load += safe_amount
                        transferred_total += safe_amount
                else:
                    # Мы принимаем от другого здорового (только немного)
                    transfer_amount = base_rate * abs(potential_diff) * self.load * 0.3
                    
                    safe_amount = min(
                        transfer_amount,
                        (1.0 - self.load) * 0.3,  # Принимаем мало
                        neighbor.load * 0.3,
                        0.05
                    )
                    
                    if safe_amount > 0.001:
                        self.load += safe_amount
                        neighbor.load -= safe_amount
                        transferred_total += safe_amount
        
        # СУПЕР-ВОССТАНОВЛЕНИЕ
        if transferred_total > 0 and self.health < 1.0:
            recovery_base = 0.06  # Ещё больше!
            
            if self.health < 0.3:
                recovery = recovery_base * 6.0
            elif self.health < 0.5:
                recovery = recovery_base * 4.0
            elif self.health < 0.7:
                recovery = recovery_base * 2.5
            else:
                recovery = recovery_base * 1.0
            
            # Бонус за объём переданного
            volume_bonus = min(3.0, transferred_total * 25.0)
            recovery *= volume_bonus
            
            self.health = min(1.0, self.health + recovery)
        
        # СИЛЬНОЕ ПАССИВНОЕ ВОССТАНОВЛЕНИЕ
        if self.health < 0.7 and transferred_total == 0:
            # Даже если не передавали, восстанавливаемся
            passive_recovery = 0.03 if self.health < 0.4 else 0.015
            self.health = min(0.7, self.health + passive_recovery)
        
        return transferred_total
    
    def sabotage(self, damage: float = 0.5, extra_load: float = 0.3):
        self.health = max(0.1, self.health - damage)
        self.load = min(1.0, self.load + extra_load)
    
    def __repr__(self):
        status = "CRIT" if self.health < 0.4 else "DAM" if self.health < 0.7 else "OK"
        return f"{self.id}[{status}]: L={self.load:.2f}, H={self.health:.2f}"