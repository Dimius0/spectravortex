# unit_enhanced.py
enhanced_code = '''
"""
FractalUnit - УСИЛЕННАЯ версия с улучшенной адаптацией.
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
    
    def transfer_load(self, base_rate: float = 0.08, use_intuition: bool = True) -> float:
        transferred_total = 0.0
        
        # ОПРЕДЕЛЯЕМ СОСТОЯНИЕ УЗЛА
        is_critical = self.health < 0.4
        is_damaged = self.health < 0.7
        is_healthy = self.health >= 0.7
        
        for neighbor in self.neighbors:
            potential_diff = self.local_potential - neighbor.local_potential
            
            # КРИТИЧЕСКИЕ УЗЛЫ ТОЛЬКО ОТДАЮТ НАГРУЗКУ
            if is_critical and potential_diff <= 0:
                continue  # Не принимаем нагрузку
            
            # РАСЧЁТ ОБЪЁМА ПЕРЕДАЧИ
            if potential_diff > 0:
                # МЫ ОТДАЁМ НАГРУЗКУ
                transfer_amount = base_rate * potential_diff * self.load
                
                # УСИЛЕНИЕ ДЛЯ КРИТИЧЕСКИХ И ПОВРЕЖДЁННЫХ
                if is_critical:
                    multiplier = 4.0  # Критические агрессивно отдают
                elif is_damaged:
                    multiplier = 2.5  # Повреждённые активно отдают
                else:
                    multiplier = 1.8  # Здоровые умеренно отдают
                    
                safe_amount = transfer_amount * multiplier
                
                # АДАПТИВНЫЕ ОГРАНИЧЕНИЯ
                max_transfer = self.load * 0.95 if is_critical else self.load * 0.85
                neighbor_capacity = (1.0 - neighbor.load) * (2.0 if neighbor.health > 0.7 else 1.0)
                
                safe_amount = min(
                    safe_amount,
                    max_transfer,
                    neighbor_capacity,
                    self.health * 3.0  # Чем здоровее, тем больше может отдать
                )
                
            elif is_damaged and potential_diff < 0:
                # ПОВРЕЖДЁННЫЕ УЗЛЫ МОГУТ ПРИНИМАТЬ, НО ОГРАНИЧЕННО
                transfer_amount = base_rate * abs(potential_diff) * self.load * 0.2
                safe_amount = min(transfer_amount, (1.0 - self.load) * 0.3)
            else:
                continue
            
            if safe_amount > 0.001:
                self.load -= safe_amount if potential_diff > 0 else -safe_amount
                neighbor.load += safe_amount if potential_diff > 0 else -safe_amount
                transferred_total += safe_amount
        
        # УСИЛЕННОЕ ВОССТАНОВЛЕНИЕ ЗДОРОВЬЯ
        if transferred_total > 0 and self.health < 1.0:
            # БАЗОВОЕ ВОССТАНОВЛЕНИЕ
            health_recovery = 0.03 * transferred_total * 15.0
            
            # БОНУСЫ В ЗАВИСИМОСТИ ОТ СОСТОЯНИЯ
            if self.health < 0.3:
                health_recovery *= 4.0  # Очень быстрое восстановление для критических
            elif self.health < 0.5:
                health_recovery *= 2.5  # Быстрое восстановление
            elif self.health < 0.7:
                health_recovery *= 1.5  # Умеренное восстановление
            
            self.health = min(1.0, self.health + health_recovery)
        
        # ПАССИВНОЕ ВОССТАНОВЛЕНИЕ ДЛЯ СИЛЬНО ПОВРЕЖДЁННЫХ
        if self.health < 0.4 and transferred_total == 0:
            self.health = min(0.4, self.health + 0.015)
        
        # ШТРАФ ЗА ПЕРЕГРУЗКУ
        if self.load > 0.8 and self.health > 0.2:
            overload_penalty = (self.load - 0.8) * 0.15
            self.health = max(0.2, self.health - overload_penalty)
        
        return transferred_total
    
    def sabotage(self, damage: float = 0.5, extra_load: float = 0.3):
        self.health = max(0.1, self.health - damage)
        self.load = min(1.0, self.load + extra_load)
    
    def __repr__(self):
        status = "CRITICAL" if self.health < 0.4 else "DAMAGED" if self.health < 0.7 else "HEALTHY"
        return f"FractalUnit(id={self.id}, load={self.load:.2f}, health={self.health:.2f}, status={status})"
'''

# Сохраняем улучшенную версию
with open('src/fractal/unit_enhanced.py', 'w', encoding='utf-8') as f:
    f.write(enhanced_code)

print("✅ Усиленная версия создана: src/fractal/unit_enhanced.py")