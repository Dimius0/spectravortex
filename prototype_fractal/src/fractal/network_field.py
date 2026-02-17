"""
NetworkFieldSolver - Применяет принцип SpectraVortex для вычисления единого поля сети.
Аналог BiharmonicSolver для фрактальной сети юнитов.
"""

import numpy as np
from typing import Dict, List, Tuple
import heapq

class NetworkFieldSolver:
    def __init__(self, network):
        self.network = network
        self.units = network.units
        self.field = {}  # unit_id -> значение поля Psi
        self.energy = 0.0
        
    def compute_unit_charge(self, unit) -> float:
        """Вычисляет 'заряд' юнита τ_i на основе его внутреннего состояния."""
        if not hasattr(unit, 'state'):
            return unit.load  # Базовая версия
        
        # Состояние как вектор: [нагрузка, (1-здоровье), сумма потребностей]
        load = unit.load
        health_factor = 1.0 - unit.health
        need_pressure = sum(unit.state.needs.values()) if unit.state.needs else 0
        
        # "Заряд" узла - его вклад в нестабильность сети
        charge = load + 0.3 * health_factor + 0.2 * min(2.0, need_pressure)
        return charge
    
    def compute_field(self):
        """Вычисляет поле Psi для каждого узла, решая дискретный аналог ∇⁴ψ = Στ."""
        # Шаг 1: Собираем заряды
        charges = {}
        for unit in self.units:
            charges[unit.id] = self.compute_unit_charge(unit)
        
        # Шаг 2: Итеративное решение (упрощённый аналог итерационного решателя)
        # Инициализируем поле значениями зарядов
        field = {uid: charges[uid] for uid in charges}
        
        # Итеративное сглаживание (имитация действия оператора Лапласиана)
        for _ in range(10):  # Несколько итераций
            new_field = {}
            for unit in self.units:
                uid = unit.id
                # Текущий заряд узла
                self_charge = charges[uid]
                
                # Влияние соседей (усреднение)
                neighbor_sum = 0.0
                neighbor_count = 0
                for neighbor in unit.neighbors:
                    neighbor_sum += field.get(neighbor.id, 0.0)
                    neighbor_count += 1
                
                if neighbor_count > 0:
                    neighbor_avg = neighbor_sum / neighbor_count
                    # Новое значение поля - компромисс между собственным зарядом и полем соседей
                    # Это упрощённая дискретная аппроксимация
                    new_field[uid] = 0.7 * self_charge + 0.3 * neighbor_avg
                else:
                    new_field[uid] = self_charge
            
            field = new_field
        
        self.field = field
        
        # Шаг 3: Вычисляем энергию системы (мера дисбаланса)
        field_values = list(field.values())
        if field_values:
            self.energy = np.std(field_values)  # СКО поля как мера неравновесия
        else:
            self.energy = 0.0
        
        return field
    
    def get_pressure_gradient(self, unit_id) -> float:
        """Возвращает 'градиент давления' для узла - разность с усреднённым полем соседей."""
        if unit_id not in self.field:
            return 0.0
        
        unit_value = self.field[unit_id]
        neighbor_values = []
        
        unit = next((u for u in self.units if u.id == unit_id), None)
        if unit:
            for neighbor in unit.neighbors:
                if neighbor.id in self.field:
                    neighbor_values.append(self.field[neighbor.id])
        
        if neighbor_values:
            avg_neighbor = np.mean(neighbor_values)
            return unit_value - avg_neighbor  # Положительно -> надо разгружать
        return 0.0
    
    def find_critical_nodes(self, n=3) -> List[Tuple[str, float]]:
        """Находит n наиболее критичных узлов (с наибольшим значением поля)."""
        nodes = [(value, uid) for uid, value in self.field.items()]
        # Наибольшее значение поля = наибольший "заряд"/напряжение
        return [(uid, value) for value, uid in heapq.nlargest(n, nodes)]