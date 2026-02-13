"""
FractalNetwork - Сеть фрактальных юнитов с поддержкой глобального поля Ψ.
Реализует парадигму SpectraVortex: целостность системы через единое поле давления.
"""

import numpy as np
import random
from typing import List, Dict, Any, Tuple, Optional
import time

try:
    from .unit import FractalUnit
    from .internal_state import InternalState
    from .intuition import IntuitionEngine
    from .network_field import NetworkFieldSolver
    HAS_NEW_MODULES = True
except ImportError:
    HAS_NEW_MODULES = False
    
    # Заглушки для совместимости
    class FractalUnit:
        pass
    
    class NetworkFieldSolver:
        def __init__(self, network):
            self.network = network
            self.field = {}
            self.energy = 0.0
        
        def compute_field(self):
            return {}
        
        def get_pressure_gradient(self, unit_id):
            return 0.0

class FractalNetwork:
    """Сеть взаимодействующих фрактальных юнитов"""
    
    def __init__(self, num_units: int = 8, topology: str = "ring", 
                 initial_load_range: Tuple[float, float] = (0.3, 0.7)):
        """
        Инициализация фрактальной сети.
        
        Args:
            num_units: Количество юнитов в сети
            topology: Топология сети ('ring', 'mesh', 'star', 'random')
            initial_load_range: Диапазон начальной нагрузки юнитов
        """
        self.units: List[FractalUnit] = []
        self.num_units = num_units
        self.topology = topology
        self.step_count = 0
        self.total_transferred_history = []
        self.imbalance_history = []
        self.avg_health_history = []
        self.field_energy_history = []
        
        # Решатель глобального поля Ψ
        self.field_solver = None
        self.last_field_update = 0
        self.field_update_interval = 1  # Обновлять поле каждый шаг
        
        # Инициализация юнитов
        for i in range(num_units):
            unit_id = f"Unit_{i:02d}"
            initial_load = random.uniform(*initial_load_range)
            unit = FractalUnit(unit_id, initial_load)
            self.units.append(unit)
        
        # Создание топологии связей
        self._create_topology(topology)
        
        # Инициализация решателя поля
        if HAS_NEW_MODULES:
            self.field_solver = NetworkFieldSolver(self)
        
        print(f"[FractalNetwork] Создана сеть: {num_units} юнитов, топология '{topology}'")
        if self.field_solver:
            print(f"[FractalNetwork] Решатель глобального поля Ψ инициализирован")
    
    def _create_topology(self, topology: str):
        """Создаёт топологию связей между юнитами"""
        if topology == "ring":
            # Кольцевая топология
            for i in range(self.num_units):
                self.units[i].add_neighbor(self.units[(i + 1) % self.num_units])
                self.units[i].add_neighbor(self.units[(i - 1) % self.num_units])
        
        elif topology == "mesh":
            # Полносвязная сеть (каждый с каждым)
            for i in range(self.num_units):
                for j in range(i + 1, self.num_units):
                    self.units[i].add_neighbor(self.units[j])
        
        elif topology == "star":
            # Звездообразная топология
            center = self.units[0]
            for i in range(1, self.num_units):
                center.add_neighbor(self.units[i])
        
        elif topology == "random":
            # Случайная топология (каждый узел имеет 2-4 случайных соседа)
            for i in range(self.num_units):
                num_neighbors = random.randint(2, min(4, self.num_units - 1))
                possible_neighbors = [j for j in range(self.num_units) if j != i]
                neighbors = random.sample(possible_neighbors, min(num_neighbors, len(possible_neighbors)))
                
                for neighbor_idx in neighbors:
                    self.units[i].add_neighbor(self.units[neighbor_idx])
        
        elif topology == "grid":
            # Двумерная сетка (только для квадратных чисел)
            import math
            grid_size = int(math.sqrt(self.num_units))
            if grid_size * grid_size != self.num_units:
                grid_size = int(math.sqrt(self.num_units)) + 1
            
            for i in range(self.num_units):
                row = i // grid_size
                col = i % grid_size
                
                # Сосед справа
                if col < grid_size - 1 and i + 1 < self.num_units:
                    self.units[i].add_neighbor(self.units[i + 1])
                # Сосед снизу
                if row < grid_size - 1 and i + grid_size < self.num_units:
                    self.units[i].add_neighbor(self.units[i + grid_size])
        
        else:
            raise ValueError(f"Неизвестная топология: {topology}")
    
    def compute_network_field(self) -> Dict[str, float]:
        """
        Вычисляет глобальное поле Ψ для всей сети.
        
        Returns:
            Dict[str, float]: Словарь unit_id -> значение поля Ψ
        """
        if not self.field_solver:
            # Заглушка, если решатель недоступен
            return {unit.id: unit.load for unit in self.units}
        
        # Вычисляем поле
        field = self.field_solver.compute_field()
        
        # Сохраняем энергию поля для истории
        self.field_energy_history.append(self.field_solver.energy)
        if len(self.field_energy_history) > 100:
            self.field_energy_history.pop(0)
        
        # Распределяем значения поля по юнитам
        for unit in self.units:
            if unit.id in field:
                unit.field_pressure = field[unit.id]
            
            # Также обновляем локальный потенциал для обратной совместимости
            unit.compute_potential(target_load=0.6, current_step=self.step_count)
        
        # Вычисляем градиенты для всех юнитов
        for unit in self.units:
            if hasattr(unit, 'update_field_gradient'):
                unit.update_field_gradient()
            elif hasattr(self.field_solver, 'get_pressure_gradient'):
                unit.field_gradient = self.field_solver.get_pressure_gradient(unit.id)
        
        return field
    
    def simulate_step(self, target_load: float = 0.6, use_field: bool = True) -> float:
        """
        Выполняет один шаг симуляции сети с использованием глобального поля Ψ.
        
        Args:
            target_load: Целевой уровень нагрузки для сети
            use_field: Использовать ли глобальное поле Ψ (True) или старую логику (False)
            
        Returns:
            float: Общий объём переданной нагрузки на этом шаге
        """
        self.step_count += 1
        total_transferred = 0.0
        
        # 1. ВЫЧИСЛЕНИЕ ГЛОБАЛЬНОГО ПОЛЯ Ψ (если включено и доступно)
        if use_field and self.field_solver and HAS_NEW_MODULES:
            # Обновляем поле не на каждом шаге (для производительности)
            if self.step_count % self.field_update_interval == 0:
                field = self.compute_network_field()
                self.last_field_update = self.step_count
                
                # Анализ поля
                if field:
                    field_values = list(field.values())
                    max_pressure = max(field_values) if field_values else 0
                    min_pressure = min(field_values) if field_values else 0
                    pressure_range = max_pressure - min_pressure
                    
                    # Автоматическая настройка интервала обновления
                    if pressure_range > 0.8:
                        self.field_update_interval = 1  # Часто при высоком напряжении
                    elif pressure_range > 0.3:
                        self.field_update_interval = 2
                    else:
                        self.field_update_interval = 3  # Редко при уравновешенной сети
        else:
            # Старая логика: вычисляем локальные потенциалы
            for unit in self.units:
                unit.compute_potential(target_load, self.step_count)
        
        # 2. ОПРЕДЕЛЕНИЕ ПОРЯДКА ОБРАБОТКИ ЮНИТОВ
        # Сортируем юниты по приоритету для обработки
        processing_order = self._get_processing_order(use_field)
        
        # 3. ПАРАЛЛЕЛЬНАЯ (ПСЕВДО) ОБРАБОТКА ЮНИТОВ
        # Сохраняем начальные состояния для атомарности
        initial_loads = {unit.id: unit.load for unit in self.units}
        initial_healths = {unit.id: unit.health for unit in self.units}
        
        transferred_per_unit = {}
        
        # Обработка в определённом порядке
        for unit in processing_order:
            # Восстанавливаем начальное состояние для атомарности симуляции
            unit.load = initial_loads[unit.id]
            unit.health = initial_healths[unit.id]
            
            # Выполняем передачу нагрузки
            transferred = unit.transfer_load(
                base_rate=0.1, 
                use_intuition=HAS_NEW_MODULES
            )
            
            transferred_per_unit[unit.id] = transferred
            total_transferred += transferred
        
        # 4. АГРЕГАЦИЯ РЕЗУЛЬТАТОВ И ОБНОВЛЕНИЕ СОСТОЯНИЙ
        # Применяем изменения, вычисленные каждым юнитом
        for unit in self.units:
            # Находим разницу между текущим и начальным состоянием
            load_change = unit.load - initial_loads[unit.id]
            health_change = unit.health - initial_healths[unit.id]
            
            # Применяем изменения к реальному состоянию
            # (в реальной системе это было бы атомарной операцией)
            actual_unit = next((u for u in self.units if u.id == unit.id), None)
            if actual_unit:
                actual_unit.load = max(0.0, min(1.0, actual_unit.load + load_change))
                actual_unit.health = max(0.1, min(1.0, actual_unit.health + health_change))
        
        # 5. СБОР СТАТИСТИКИ И ИСТОРИИ
        self.total_transferred_history.append(total_transferred)
        if len(self.total_transferred_history) > 100:
            self.total_transferred_history.pop(0)
        
        # Обновляем метрики сети
        metrics = self.get_network_metrics()
        self.imbalance_history.append(metrics['imbalance'])
        self.avg_health_history.append(metrics['avg_health'])
        
        # 6. АДАПТИВНАЯ НАСТРОЙКА ПАРАМЕТРОВ
        self._adaptive_parameter_tuning(metrics, total_transferred)
        
        # 7. ДИАГНОСТИЧЕСКИЙ ВЫВОД (каждые N шагов)
        if self.step_count % 10 == 0:
            self._print_step_diagnostics(total_transferred, metrics)
        
        return total_transferred
    
    def _get_processing_order(self, use_field: bool) -> List[FractalUnit]:
        """
        Определяет порядок обработки юнитов для минимизации конфликтов.
        
        Args:
            use_field: Используется ли глобальное поле
            
        Returns:
            List[FractalUnit]: Отсортированный список юнитов для обработки
        """
        if use_field and HAS_NEW_MODULES:
            # При использовании поля Ψ обрабатываем в порядке убывания давления
            # (наиболее "напряжённые" узлы обрабатываются первыми)
            units_with_pressure = []
            for unit in self.units:
                pressure = unit.field_pressure if hasattr(unit, 'field_pressure') else unit.load
                units_with_pressure.append((pressure, unit))
            
            # Сортируем по убыванию давления
            units_with_pressure.sort(key=lambda x: x[0], reverse=True)
            return [unit for _, unit in units_with_pressure]
        
        else:
            # Старая логика: случайный порядок
            order = self.units.copy()
            random.shuffle(order)
            return order
    
    def _adaptive_parameter_tuning(self, metrics: Dict, transferred: float):
        """Адаптивная настройка параметров сети на основе метрик"""
        # Настраиваем интервал обновления поля
        current_imbalance = metrics['imbalance']
        
        if current_imbalance > 0.7:
            # Высокий дисбаланс - частое обновление поля
            self.field_update_interval = 1
        elif current_imbalance > 0.4:
            self.field_update_interval = 2
        else:
            # Низкий дисбаланс - можно обновлять реже
            self.field_update_interval = max(1, 4 - int(metrics['avg_health'] * 2))
        
        # Настраиваем базовую скорость передачи
        avg_health = metrics['avg_health']
        if avg_health < 0.6:
            # Низкое здоровье сети - более агрессивная передача
            for unit in self.units:
                if hasattr(unit, 'base_transfer_rate'):
                    unit.base_transfer_rate = min(0.2, 0.08 + (0.6 - avg_health) * 0.2)
    
    def _print_step_diagnostics(self, transferred: float, metrics: Dict):
        """Вывод диагностической информации о шаге"""
        if self.field_solver and hasattr(self.field_solver, 'energy'):
            field_energy = self.field_solver.energy
            energy_str = f", Ψ-энергия={field_energy:.3f}"
        else:
            energy_str = ""
        
        print(f"[Network] Шаг {self.step_count:3d}: "
              f"передано={transferred:.4f}, "
              f"разброс={metrics['imbalance']:.3f}, "
              f"здоровье={metrics['avg_health']:.3f}"
              f"{energy_str}")
        
        # Вывод информации о критических узлах
        critical_units = [u for u in self.units if u.health < 0.4]
        if critical_units:
            print(f"       Критических узлов: {len(critical_units)}")
            for unit in critical_units[:2]:  # Показываем только первые 2
                print(f"         {unit.id}: H={unit.health:.2f}, L={unit.load:.2f}")
    
    def sabotage(self, unit_index: int, damage: float = 0.5, extra_load: float = 0.3):
        """
        Применяет саботаж к указанному узлу.
        
        Args:
            unit_index: Индекс узла для атаки
            damage: Урон здоровью
            extra_load: Дополнительная нагрузка
        """
        if 0 <= unit_index < len(self.units):
            self.units[unit_index].sabotage(damage, extra_load)
            print(f"[Network] Саботаж применён к {self.units[unit_index].id}")
    
    def get_network_metrics(self) -> Dict[str, float]:
        """
        Вычисляет метрики состояния сети.
        
        Returns:
            Dict[str, float]: Словарь с метриками сети
        """
        loads = [unit.load for unit in self.units]
        healths = [unit.health for unit in self.units]
        
        if not loads:
            return {
                'avg_load': 0.0,
                'avg_health': 0.0,
                'imbalance': 0.0,
                'unhealthy_nodes': 0,
                'critical_nodes': 0
            }
        
        avg_load = np.mean(loads)
        avg_health = np.mean(healths)
        
        # Разброс нагрузки (мера дисбаланса)
        load_std = np.std(loads) if len(loads) > 1 else 0.0
        imbalance = load_std / max(0.1, avg_load) if avg_load > 0 else 0.0
        
        # Критические и повреждённые узлы
        unhealthy_nodes = sum(1 for h in healths if h < 0.7)
        critical_nodes = sum(1 for h in healths if h < 0.4)
        
        # Метрики поля (если доступны)
        field_metrics = {}
        if self.field_solver and hasattr(self.field_solver, 'energy'):
            field_metrics = {
                'field_energy': self.field_solver.energy,
                'field_gradient_max': max([abs(unit.field_gradient) for unit in self.units]) 
                    if hasattr(self.units[0], 'field_gradient') else 0.0
            }
        
        return {
            'avg_load': avg_load,
            'avg_health': avg_health,
            'imbalance': imbalance,
            'unhealthy_nodes': unhealthy_nodes,
            'critical_nodes': critical_nodes,
            'total_units': len(self.units),
            **field_metrics
        }
    
    def get_unit_diagnostics(self, unit_id: str) -> Optional[Dict]:
        """
        Возвращает детальную диагностику указанного юнита.
        
        Args:
            unit_id: Идентификатор юнита
            
        Returns:
            Optional[Dict]: Диагностическая информация или None
        """
        for unit in self.units:
            if unit.id == unit_id:
                diag = {
                    'id': unit.id,
                    'load': unit.load,
                    'health': unit.health,
                    'neighbors': [n.id for n in unit.neighbors],
                    'local_potential': unit.local_potential,
                    'field_pressure': getattr(unit, 'field_pressure', 0.0),
                    'field_gradient': getattr(unit, 'field_gradient', 0.0)
                }
                
                if HAS_NEW_MODULES and hasattr(unit, 'state'):
                    diag.update({
                        'gestalt': unit.state.gestalt,
                        'tendency': unit.state.behavioral_tendency,
                        'stability': getattr(unit.state, 'stability_index', 0.0),
                        'needs': unit.state.needs.copy() if unit.state.needs else {}
                    })
                
                return diag
        
        return None
    
    def get_field_statistics(self) -> Dict:
        """
        Возвращает статистику глобального поля Ψ.
        
        Returns:
            Dict: Статистика поля
        """
        if not self.field_solver or not hasattr(self.field_solver, 'field'):
            return {'available': False}
        
        field_values = list(self.field_solver.field.values())
        if not field_values:
            return {'available': True, 'empty': True}
        
        gradients = [getattr(unit, 'field_gradient', 0.0) for unit in self.units]
        
        return {
            'available': True,
            'energy': getattr(self.field_solver, 'energy', 0.0),
            'field_mean': np.mean(field_values),
            'field_std': np.std(field_values),
            'field_min': min(field_values),
            'field_max': max(field_values),
            'gradient_mean': np.mean(gradients),
            'gradient_std': np.std(gradients),
            'update_interval': self.field_update_interval,
            'last_update': self.last_field_update
        }
    
    def __repr__(self):
        """Строковое представление сети"""
        metrics = self.get_network_metrics()
        return (f"FractalNetwork(units={self.num_units}, "
                f"topology='{self.topology}', "
                f"imbalance={metrics['imbalance']:.3f}, "
                f"health={metrics['avg_health']:.3f})")