"""
FractalUnit - ФИКСИРОВАННАЯ версия: повреждённые узлы НЕ принимают нагрузку.
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
    
    def transfer_load(self, base_rate: float = 0.1, use_intuition: bool = True) -> float:  # Увеличена до 0.1
        transferred_total = 0.0
        
        # ОПРЕДЕЛЯЕМ РЕЖИМ
        is_critical = self.health < 0.4
        is_damaged = self.health < 0.7
        is_healthy = self.health >= 0.7
        
        # КРИТИЧЕСКИЕ И ПОВРЕЖДЁННЫЕ УЗЛЫ ТОЛЬКО ОТДАЮТ НАГРУЗКУ
        if is_critical or is_damaged:
            # ТОЛЬКО ОТДАЁМ, НЕ ПРИНИМАЕМ
            for neighbor in self.neighbors:
                # Выбираем только здоровых соседей (health > 0.7)
                if neighbor.health < 0.7:
                    continue
                    
                potential_diff = self.local_potential - neighbor.local_potential
                if potential_diff > 0:
                    # АГРЕССИВНО ОТДАЁМ
                    transfer_amount = base_rate * potential_diff * self.load
                    
                    # МНОЖИТЕЛИ
                    if is_critical:
                        multiplier = 5.0  # Критические отдают максимально
                    else:
                        multiplier = 3.0  # Повреждённые активно отдают
                    
                    safe_amount = transfer_amount * multiplier
                    
                    # ОГРАНИЧЕНИЯ
                    max_transfer = self.load * 0.98  # Почти всю нагрузку
                    neighbor_capacity = (1.0 - neighbor.load) * 2.0
                    
                    safe_amount = min(
                        safe_amount,
                        max_transfer,
                        neighbor_capacity,
                        0.5  # Максимум за шаг
                    )
                    
                    if safe_amount > 0.001:
                        self.load -= safe_amount
                        neighbor.load += safe_amount
                        transferred_total += safe_amount
        
        else:
            # ЗДОРОВЫЕ УЗЛЫ МОГУТ КАК ОТДАВАТЬ, ТАК И ПРИНИМАТЬ
            for neighbor in self.neighbors:
                potential_diff = self.local_potential - neighbor.local_potential
                
                if abs(potential_diff) < 0.01:
                    continue
                
                if potential_diff > 0:
                    # ОТДАЁМ НАГРУЗКУ
                    transfer_amount = base_rate * potential_diff * self.load * 1.5
                else:
                    # ПРИНИМАЕМ ТОЛЬКО ОТ ПОВРЕЖДЁННЫХ
                    if neighbor.health >= 0.7:
                        continue  # Не принимаем от здоровых
                    transfer_amount = base_rate * abs(potential_diff) * self.load * 0.8
                
                safe_amount = min(
                    transfer_amount,
                    self.load * 0.7 if potential_diff > 0 else (1.0 - self.load) * 0.5,
                    neighbor.load * 0.8 if potential_diff > 0 else (1.0 - neighbor.load) * 0.8
                )
                
                if safe_amount > 0.001:
                    if potential_diff > 0:
                        self.load -= safe_amount
                        neighbor.load += safe_amount
                    else:
                        self.load += safe_amount
                        neighbor.load -= safe_amount
                    transferred_total += safe_amount
        
        # УСИЛЕННОЕ ВОССТАНОВЛЕНИЕ
        if transferred_total > 0 and self.health < 1.0:
            base_recovery = 0.04  # Увеличен базовый коэффициент
            
            if is_critical:
                recovery = base_recovery * 4.0
            elif is_damaged:
                recovery = base_recovery * 2.5
            else:
                recovery = base_recovery * 1.2
            
            # Дополнительный бонус за успешную разгрузку
            load_reduction_bonus = min(2.0, transferred_total * 20.0)
            recovery *= load_reduction_bonus
            
            self.health = min(1.0, self.health + recovery)
        
        # ПАССИВНОЕ ВОССТАНОВЛЕНИЕ ДЛЯ СИЛЬНО ПОВРЕЖДЁННЫХ
        if self.health < 0.4:
            self.health = min(0.4, self.health + 0.02)
        
        return transferred_total
    
    def sabotage(self, damage: float = 0.5, extra_load: float = 0.3):
        self.health = max(0.1, self.health - damage)
        self.load = min(1.0, self.load + extra_load)
    
    def __repr__(self):
        return f"FractalUnit(id={self.id}, load={self.load:.2f}, health={self.health:.2f})"
        