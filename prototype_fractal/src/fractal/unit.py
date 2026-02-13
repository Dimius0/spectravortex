"""
FractalUnit - Оптимизированная версия с плавной передачей нагрузки.
Глобальное поле Ψ + умеренные параметры передачи = стабильная балансировка.
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
        
        # Поля для глобального поля Ψ
        self.field_pressure = 0.0
        self.field_gradient = 0.0
        self.network_energy_contribution = 0.0
        
        # Статистика передачи
        self.transfer_stats = {
            'total_transferred': 0.0,
            'successful_transfers': 0,
            'failed_transfers': 0
        }
        
        if HAS_NEW_MODULES:
            self.state = InternalState(unit_id)
            self.intuition = IntuitionEngine(f"intuition_{unit_id}")
    
    def add_neighbor(self, neighbor: "FractalUnit", bidirectional: bool = True):
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            if bidirectional:
                neighbor.add_neighbor(self, bidirectional=False)
    
    def compute_potential(self, target_load: float = 0.6, current_step: int = 0) -> float:
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
    
    def compute_field_charge(self) -> float:
        """Вычисляет 'топологический заряд' τ_i для этого узла"""
        # Базовые компоненты
        load_charge = self.load
        
        # Компонент здоровья: квадратичная зависимость
        health_charge = (1.0 - self.health) ** 2 * 1.5
        
        # Компонент изолированности
        isolation_charge = 0.0
        if len(self.neighbors) < 2:
            isolation_charge = 0.3 * (2 - len(self.neighbors))
        
        # Компонент из InternalState
        state_charge = 0.0
        if HAS_NEW_MODULES and self.state:
            need_sum = sum(self.state.needs.values()) if self.state.needs else 0
            state_charge = min(1.5, need_sum * 0.4)
            
            if hasattr(self.state, 'stability_index'):
                stability_charge = (1.0 - self.state.stability_index) * 0.2
                state_charge += stability_charge
        
        # Итоговый заряд с весами
        total_charge = (
            load_charge * 1.0 +
            health_charge * 0.6 +
            isolation_charge * 0.3 +
            state_charge * 0.2
        )
        
        # Корректировка для критических состояний (умеренная)
        if self.health < 0.3:
            total_charge *= 1.3
        elif self.health < 0.6:
            total_charge *= 1.15
        
        return min(2.0, total_charge)  # Ограничиваем максимум
    
    def update_field_gradient(self):
        """Вычисляет градиент поля Ψ для этого узла"""
        if not self.neighbors:
            self.field_gradient = 0.0
            return
        
        neighbor_pressures = []
        for neighbor in self.neighbors:
            if hasattr(neighbor, 'field_pressure'):
                neighbor_pressures.append(neighbor.field_pressure)
        
        if not neighbor_pressures:
            self.field_gradient = 0.0
            return
        
        avg_neighbor_pressure = np.mean(neighbor_pressures)
        self.field_gradient = self.field_pressure - avg_neighbor_pressure
        
        # Умеренная корректировка на здоровье
        if self.health < 0.4:
            self.field_gradient *= 1.4
        elif self.health < 0.7:
            self.field_gradient *= 1.15
    
    def transfer_load(self, base_rate: float = 0.09, use_intuition: bool = True) -> float:
        """
        Перераспределяет нагрузку на основе градиента поля Ψ.
        УМЕРЕННАЯ версия: предотвращает мгновенную разгрузку.
        """
        transferred_total = 0.0
        
        # 1. ОБНОВЛЯЕМ ГРАДИЕНТ ПОЛЯ
        self.update_field_gradient()
        
        # 2. ИНТУИТИВНЫЙ МНОЖИТЕЛЬ (умеренный)
        intuition_multiplier = 1.0
        if use_intuition and HAS_NEW_MODULES and self.intuition and self.state:
            try:
                intuition_data = self.state.get_for_intuition()
                advice = self.intuition.assess(intuition_data, analytic_confidence=0.6)
                
                if advice.get('tendency') == 'SELF_PRESERVATION':
                    intuition_multiplier = 1.8  # Было 2.5
                elif advice.get('tendency') == 'ENERGY_CONSERVATION':
                    intuition_multiplier = 0.8  # Было 0.7
                elif advice.get('tendency') == 'OPPORTUNISTIC':
                    intuition_multiplier = 1.3  # Было 1.4
                
                confidence = advice.get('confidence', 0.5)
                intuition_multiplier = 1.0 + (intuition_multiplier - 1.0) * confidence * 0.7
            except Exception:
                intuition_multiplier = 1.0
        
        # 3. СТРАТЕГИЯ ПЕРЕДАЧИ (СГЛАЖЕННАЯ!)
        if self.health < 0.7:
            # ПОВРЕЖДЁННЫЕ УЗЛЫ: умеренная разгрузка
            strategy = "MODERATE_UNLOAD"
            transfer_multiplier = 2.0  # Было 3.5
            max_transfer_percent = 0.35  # Было 0.95 (35% вместо 95%!)
            absolute_max_transfer = 0.10  # Макс 10% за шаг
        else:
            # ЗДОРОВЫЕ УЗЛЫ: плавная балансировка
            strategy = "BALANCING"
            transfer_multiplier = 1.3  # Было 1.5
            max_transfer_percent = 0.25  # Было 0.7
            absolute_max_transfer = 0.06  # Макс 6% за шаг
        
        # 4. ПРОЦЕСС ПЕРЕДАЧИ КАЖДОМУ СОСЕДУ
        processed_neighbors = 0
        
        for neighbor in self.neighbors:
            # Пропускаем соседей в ещё худшем состоянии
            if (self.health < 0.4 and neighbor.health < 0.3 and 
                strategy != "MODERATE_UNLOAD"):
                continue
            
            # Получаем градиент соседа
            neighbor_gradient = 0.0
            if hasattr(neighbor, 'field_gradient'):
                neighbor_gradient = neighbor.field_gradient
            
            # Направление потока: только если наш градиент значительно больше
            gradient_diff = self.field_gradient - neighbor_gradient
            
            if gradient_diff > 0.01:  # Порог для передачи
                # БАЗОВЫЙ РАСЧЁТ (умеренный)
                base_transfer = base_rate * gradient_diff * self.load
                
                # ПРИМЕНЯЕМ МНОЖИТЕЛИ (ослабленные)
                transfer_amount = base_transfer * transfer_multiplier
                transfer_amount *= intuition_multiplier
                
                # Множитель здоровья (ослабленный)
                health_bonus = 1.0 + (0.7 - min(self.health, 0.7)) * 0.8  # Было 1.5
                transfer_amount *= health_bonus
                
                # Множитель загрузки (ослабленный)
                if self.load > 0.8:
                    load_bonus = 1.0 + (self.load - 0.8) * 1.0  # Было 2.0
                    transfer_amount *= load_bonus
                
                # ДИНАМИЧЕСКИЕ ОГРАНИЧЕНИЯ (ЖЁСТКИЕ!)
                # 1. Не больше максимального процента
                max_by_percent = self.load * max_transfer_percent
                
                # 2. Абсолютный максимум
                max_by_absolute = absolute_max_transfer
                
                # 3. Возможности соседа
                neighbor_capacity = (1.0 - neighbor.load)
                if neighbor.load < 0.3:
                    neighbor_capacity *= 1.3  # Было 2.0
                if neighbor.health > 0.7:
                    neighbor_capacity *= 1.2  # Было 1.5
                
                # 4. Ограничение по здоровью
                health_limit = self.health * 1.5  # Было 2.0
                
                # ФИНАЛЬНЫЙ РАСЧЁТ БЕЗОПАСНОГО ОБЪЁМА
                safe_amount = min(
                    transfer_amount,
                    max_by_percent,
                    max_by_absolute,      # Ключевое ограничение!
                    neighbor_capacity,
                    health_limit,
                    0.08  # Общий максимум (было 0.25)
                )
                
                # 5. ВЫПОЛНЕНИЕ ПЕРЕДАЧИ
                if safe_amount > 0.001:
                    # Проверяем, не будет ли сосед перегружен
                    new_neighbor_load = neighbor.load + safe_amount
                    if new_neighbor_load <= 0.95:  # Не перегружаем соседа
                        self.load -= safe_amount
                        neighbor.load += safe_amount
                        transferred_total += safe_amount
                        processed_neighbors += 1
                        
                        # Обновляем статистику
                        self.transfer_stats['total_transferred'] += safe_amount
                        self.transfer_stats['successful_transfers'] += 1
                        
                        # Обновляем силу связи (умеренно)
                        if HAS_NEW_MODULES and self.state:
                            if neighbor.id in self.state.topology['connection_strengths']:
                                current = self.state.topology['connection_strengths'][neighbor.id]
                                new_strength = min(1.0, current + 0.04)  # Было 0.08
                                self.state.topology['connection_strengths'][neighbor.id] = new_strength
                    else:
                        self.transfer_stats['failed_transfers'] += 1
        
        # 5. ВОССТАНОВЛЕНИЕ ЗДОРОВЬЯ (СГЛАЖЕННОЕ)
        if transferred_total > 0 and self.health < 1.0:
            # Базовое восстановление (умеренное)
            base_recovery = 0.03 * transferred_total * 8.0  # Было 12.0
            
            # Бонусы (ослабленные)
            volume_bonus = min(2.0, transferred_total * 15.0)  # Было 20.0
            
            strategy_bonus = 1.5 if strategy == "MODERATE_UNLOAD" else 1.0  # Было 2.0
            
            health_bonus = 2.0 if self.health < 0.3 else 1.3 if self.health < 0.5 else 1.0
            
            # Итоговое восстановление
            total_recovery = base_recovery * volume_bonus * strategy_bonus * health_bonus
            
            # Корректировка от InternalState
            if HAS_NEW_MODULES and self.state:
                if self.state.behavioral_tendency == "ENERGY_CONSERVATION":
                    total_recovery *= 1.4  # Было 1.8
                elif self.state.behavioral_tendency == "SELF_PRESERVATION":
                    total_recovery *= 1.6  # Было 2.2
            
            self.health = min(1.0, self.health + total_recovery)
        
        # 6. ПАССИВНОЕ ВОССТАНОВЛЕНИЕ (умеренное)
        if self.health < 0.7 and transferred_total == 0:
            passive_recovery = 0.015 if self.health < 0.4 else 0.008
            self.health = min(0.7, self.health + passive_recovery)
        
        # 7. ШТРАФ ЗА ПЕРЕГРУЗКУ (умеренный)
        if self.load > 0.85 and self.health > 0.2:
            overload_penalty = (self.load - 0.85) * 0.08  # Было 0.12
            self.health = max(0.2, self.health - overload_penalty)
        
        # 8. ИСТОРИЯ И СТАТИСТИКА
        self.load_history.append(self.load)
        if len(self.load_history) > 50:
            self.load_history.pop(0)
        
        # 9. ДИНАМИЧЕСКАЯ КОРРЕКЦИЯ: если передача слишком агрессивна
        if processed_neighbors > 0:
            avg_transfer = transferred_total / processed_neighbors
            if avg_transfer > 0.05:  # Слишком большие передачи
                # Автоматически снижаем агрессивность на следующем шаге
                if hasattr(self, 'base_transfer_rate'):
                    self.base_transfer_rate = max(0.05, self.base_transfer_rate * 0.9)
        
        return transferred_total
    
    def get_transfer_efficiency(self) -> float:
        """Возвращает эффективность передачи нагрузки"""
        total = self.transfer_stats['successful_transfers'] + self.transfer_stats['failed_transfers']
        if total > 0:
            return self.transfer_stats['successful_transfers'] / total
        return 0.0
    
    def sabotage(self, damage: float = 0.5, extra_load: float = 0.3):
        """Имитация сбоя/атаки на узел (модифицированная)"""
        # НЕ добавляем полную нагрузку, а добавляем умеренно
        actual_extra_load = min(extra_load, 1.0 - self.load)
        self.health = max(0.1, self.health - damage)
        self.load = min(1.0, self.load + actual_extra_load * 0.7)  # 70% от запрошенной
        
        print(f"[FractalUnit] {self.id}: САБОТАЖ! "
              f"Здоровье: {self.health:.2f}↓, "
              f"Нагрузка: {self.load:.2f}↑")
    
    def heal(self, amount: float = 0.1):
        """Восстановление здоровья"""
        old_health = self.health
        self.health = min(1.0, self.health + amount)
        
        if self.health > 0.7 and old_health <= 0.7:
            print(f"[FractalUnit] {self.id}: Восстановлен! "
                  f"Здоровье: {self.health:.2f}")
    
    def get_state_summary(self) -> Dict:
        """Возвращает сводку состояния узла"""
        summary = {
            'id': self.id,
            'load': round(self.load, 3),
            'health': round(self.health, 3),
            'field_pressure': round(self.field_pressure, 3),
            'field_gradient': round(self.field_gradient, 3),
            'neighbors': len(self.neighbors),
            'transfer_efficiency': round(self.get_transfer_efficiency(), 3),
            'charge': round(self.compute_field_charge(), 3)
        }
        
        if HAS_NEW_MODULES and self.state:
            summary.update({
                'gestalt': self.state.gestalt,
                'tendency': self.state.behavioral_tendency,
                'stability': round(self.state.stability_index, 3) if hasattr(self.state, 'stability_index') else 0.0,
                'dominant_need': max(self.state.needs.items(), key=lambda x: x[1])[0] if self.state.needs else None
            })
        
        return summary
    
    def __repr__(self):
        """Строковое представление для отладки"""
        status = "CRIT" if self.health < 0.4 else "DAM" if self.health < 0.7 else "OK"
        load_str = f"L={self.load:.2f}"
        health_str = f"H={self.health:.2f}"
        
        # Цветовое кодирование по здоровью
        if self.health < 0.4:
            health_str = f"H=\033[91m{self.health:.2f}\033[0m"  # Красный
        elif self.health < 0.7:
            health_str = f"H=\033[93m{self.health:.2f}\033[0m"  # Жёлтый
        
        field_str = f" Ψ={self.field_pressure:.2f}∇{self.field_gradient:+.2f}"
        return f"{self.id}[\033[1m{status}\033[0m]: {load_str}, {health_str}{field_str}"