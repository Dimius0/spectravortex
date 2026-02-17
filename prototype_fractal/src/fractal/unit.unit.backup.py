"""
FractalUnit - элементарная единица фрактально-адаптивной системы.
Обновлённая версия с интеграцией InternalState и IntuitionEngine.
"""

import numpy as np
from typing import List, Optional, Dict, Any
import time

# Импорт новых модулей
try:
    from .internal_state import InternalState
    from .intuition import IntuitionEngine
    HAS_NEW_MODULES = True
except ImportError:
    print("[FractalUnit] Предупреждение: новые модули не найдены, используется базовая версия")
    HAS_NEW_MODULES = False

class FractalUnit:
    """
    Базовая единица системы с состоянием и локальными правилами.
    Теперь с поддержкой биологически инспирированных состояний.
    """
    
    def __init__(self, unit_id: str, initial_load: float = 0.0):
        """
        Инициализация фрактальной единицы.
        
        Args:
            unit_id: Уникальный идентификатор единицы
            initial_load: Начальная нагрузка (0.0 - 1.0)
        """
        self.id = unit_id
        
        # БАЗОВЫЕ СОСТОЯНИЯ
        self.load = initial_load
        self.health = 1.0
        self.neighbors: List['FractalUnit'] = []
        self.local_potential = 0.0
        
        # ИСТОРИЯ ДЛЯ АНАЛИЗА ТРЕНДОВ
        self.load_history = [initial_load]
        self.health_history = [1.0]
        self.potential_history = [0.0]
        self.max_history_length = 50
        
        # СТАТИСТИКА И МЕТРИКИ
        self.step_count = 0
        self.total_transferred = 0.0
        self.last_prediction_error = 0.0
        self.successful_transfers = 0
        self.failed_transfers = 0
        
        # НОВЫЕ МОДУЛИ (если доступны)
        if HAS_NEW_MODULES:
            self.state = InternalState(unit_id)
            self.intuition = IntuitionEngine(f"intuition_{unit_id}")
            self.last_intuition_advice = {}
            self._last_state_update = 0
        else:
            self.state = None
            self.intuition = None
        
        # КЭШ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
        self._last_potential_calc = 0
        self._cached_potential = None
        
        print(f"[FractalUnit] Создана единица {unit_id} (новые модули: {HAS_NEW_MODULES})")
    
    def add_neighbor(self, neighbor: 'FractalUnit', bidirectional: bool = True):
        """
        Добавляет связь с соседней единицей.
        
        Args:
            neighbor: Соседняя FractalUnit
            bidirectional: Если True, также добавляет обратную связь
        """
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            
            # Обновляем топологию в InternalState (если есть)
            if self.state and hasattr(self.state, 'topology'):
                self.state.topology['connection_strengths'][neighbor.id] = 0.5
            
            if bidirectional:
                neighbor.add_neighbor(self, bidirectional=False)
    
    def remove_neighbor(self, neighbor: 'FractalUnit', bidirectional: bool = True):
        """Удаляет связь с соседней единицей"""
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)
            
            # Обновляем топологию в InternalState
            if self.state and hasattr(self.state, 'topology'):
                if neighbor.id in self.state.topology['connection_strengths']:
                    del self.state.topology['connection_strengths'][neighbor.id]
            
            if bidirectional:
                neighbor.remove_neighbor(self, bidirectional=False)
    
    def _update_internal_state(self, target_load: float = 0.7):
        """Обновление внутреннего состояния (если доступно)"""
        if not self.state:
            return
        
        current_time = time.time()
        if current_time - self._last_state_update < 0.1:  # Не чаще 10 Гц
            return
        
        self._last_state_update = current_time
        
        # Вычисляем метрики для обновления состояния
        stress = abs(self.load - target_load)
        
        # Анализ тренда нагрузки
        load_trend = 0.0
        if len(self.load_history) >= 3:
            recent = self.load_history[-3:]
            load_trend = (recent[-1] - recent[0]) / 2.0 if recent[0] != 0 else 0.0
        
        # Новизна (изменение состояния)
        novelty = 0.0
        if len(self.potential_history) >= 2:
            novelty = abs(self.potential_history[-1] - self.potential_history[-2])
        
        # Успешность передачи (простая метрика)
        success_rate = 0.5
        total_transfers = self.successful_transfers + self.failed_transfers
        if total_transfers > 0:
            success_rate = self.successful_transfers / total_transfers
        
        # Топологические метрики
        topology_metrics = {
            'isolation_score': 1.0 - (len(self.neighbors) / 10.0) if self.neighbors else 1.0,
            'centrality': min(1.0, len(self.neighbors) / 5.0),
            'clustering_coef': self._calculate_clustering_coefficient()
        }
        
        # Обновление InternalState
        raw_metrics = {
            'load': self.load,
            'health': self.health,
            'stress': stress,
            'prediction_error': self.last_prediction_error,
            'novelty': novelty,
            'success_rate': success_rate,
            'topology_metrics': topology_metrics
        }
        
        self.state.update(raw_metrics)
    
    def _calculate_clustering_coefficient(self) -> float:
        """Вычисляет коэффициент кластеризации узла"""
        if len(self.neighbors) < 2:
            return 0.0
        
        # Считаем связи между соседями
        possible_connections = len(self.neighbors) * (len(self.neighbors) - 1) / 2
        if possible_connections == 0:
            return 0.0
        
        actual_connections = 0
        for i, n1 in enumerate(self.neighbors):
            for n2 in self.neighbors[i+1:]:
                if n2 in n1.neighbors:
                    actual_connections += 1
        
        return actual_connections / possible_connections
    
    def compute_potential(self, target_load: float = 0.7, current_step: int = 0) -> float:
        """
        Вычисляет локальный потенциал как функцию отклонения от цели.
        
        Args:
            target_load: Целевой уровень нагрузки (0.0 - 1.0)
            current_step: Текущий шаг симуляции
        
        Returns:
            Значение локального потенциала (≥ 0.0)
        """
        # КЭШИРОВАНИЕ (если ничего не изменилось)
        cache_key = (self.load, self.health, target_load, current_step // 10)
        if cache_key == self._last_potential_calc and self._cached_potential is not None:
            return self._cached_potential
        
        self._last_potential_calc = cache_key
        
        # 1. ОБНОВЛЯЕМ ВНУТРЕННЕЕ СОСТОЯНИЕ
        self._update_internal_state(target_load)
        
        # 2. ВЫБИРАЕМ ЦЕЛЕВУЮ НАГРУЗКУ (статическую или динамическую)
        effective_target = target_load
        if self.state:
            analytic_data = self.state.get_for_analytics()
            effective_target = analytic_data.get('effective_target_load', target_load)
        
        # 3. ОСНОВНОЙ КОМПОНЕНТ: квадрат отклонения от цели
        load_component = (self.load - effective_target) ** 2
        
        # 4. ШТРАФ ЗА ЗДОРОВЬЕ (умеренный)
        health_penalty = (1.0 - self.health) * 0.5
        
        # 5. ДОПОЛНИТЕЛЬНЫЕ ШТРАФЫ ИЗ СОСТОЯНИЯ
        additional_penalties = 0.0
        
        if self.state:
            # Штраф за неудовлетворённые потребности
            need_penalty = sum(self.state.needs.values()) * 0.05
            
            # Штраф за нестабильность
            stability_penalty = (1.0 - self.state.stability_index) * 0.2
            
            additional_penalties = need_penalty + stability_penalty
        
        # 6. ИТОГОВЫЙ ПОТЕНЦИАЛ
        self.local_potential = load_component + health_penalty + additional_penalties
        
        # 7. СОХРАНЕНИЕ В ИСТОРИЮ
        self.potential_history.append(self.local_potential)
        if len(self.potential_history) > self.max_history_length:
            self.potential_history.pop(0)
        
        # КЭШИРУЕМ РЕЗУЛЬТАТ
        self._cached_potential = self.local_potential
        
        return self.local_potential
    
    def transfer_load(self, base_rate: float = 0.05, 
                      use_intuition: bool = True) -> float:
        """
        Перераспределяет нагрузку среди соседей на основе разницы потенциалов.
        
        Args:
            base_rate: Базовый коэффициент скорости перераспределения
            use_intuition: Использовать ли интуитивный контур
        
        Returns:
            Общий объём переданной нагрузки
        """
        transferred_total = 0.0
        self.step_count += 1
        
        # БАЗОВЫЕ ПАРАМЕТРЫ ПЕРЕДАЧИ
        effective_rate = base_rate
        risk_tolerance = 0.5
        cooperation_bias = 0.5
        
        # 1. ПОЛУЧЕНИЕ ИНТУИТИВНОГО СОВЕТА (если доступно и включено)
        intuition_advice = {}
        if use_intuition and self.state and self.intuition:
            # Получаем данные для интуиции
            intuition_data = self.state.get_for_intuition()
            
            # Оцениваем уверенность аналитики (простая эвристика)
            analytic_confidence = 0.7  # Можно сделать сложнее
            
            # Получаем интуитивный совет
            intuition_advice = self.intuition.assess(intuition_data, analytic_confidence)
            self.last_intuition_advice = intuition_advice
            
            # Получаем аналитические параметры из состояния
            if self.state:
                analytic_data = self.state.get_for_analytics()
                effective_rate = base_rate * analytic_data.get('transfer_aggressiveness', 1.0)
                risk_tolerance = analytic_data.get('risk_tolerance', 0.5)
                cooperation_bias = analytic_data.get('cooperation_bias', 0.5)
        
        # 2. ПОДГОТОВКА АНАЛИТИЧЕСКОГО РЕШЕНИЯ
        analytic_decision = {
            'transfer_rate': effective_rate,
            'risk_tolerance': risk_tolerance,
            'cooperation_bias': cooperation_bias,
            'timestamp': time.time(),
            'confidence': 0.7,  # Уверенность аналитики
            'step': self.step_count
        }
        
        # 3. ПРИМЕНЕНИЕ ИНТУИТИВНОГО УКЛОНА (если есть)
        if intuition_advice:
            analytic_decision = self.intuition.apply_bias_to_decision(
                analytic_decision, intuition_advice
            )
        
        # 4. ВЫЧИСЛЕНИЕ ФИНАЛЬНЫХ ПАРАМЕТРОВ
        final_rate = analytic_decision.get('transfer_rate', effective_rate)
        final_risk_tolerance = analytic_decision.get('risk_tolerance', risk_tolerance)
        
        # 5. ПРОЦЕСС ПЕРЕДАЧИ НАГРУЗКИ
        for neighbor in self.neighbors:
            # Разность потенциалов определяет направление и силу потока
            potential_diff = self.local_potential - neighbor.local_potential
            
            if potential_diff > 0:  # Наш потенциал выше - отдаём нагрузку
                # Объём передачи пропорционален разности потенциалов
                transfer_amount = final_rate * potential_diff * self.load
                
                # ОГРАНИЧЕНИЯ:
                # 1. Не больше текущей нагрузки
                # 2. Не больше свободного места у соседа
                # 3. Учитываем терпимость к риску
                max_to_transfer = self.load * (0.3 + final_risk_tolerance * 0.4)
                neighbor_capacity = (1.0 - neighbor.load) * (0.5 + cooperation_bias * 0.5)
                
                safe_amount = min(
                    transfer_amount,
                    max_to_transfer,
                    neighbor_capacity
                )
                
                # Практически значимый перекос
                if safe_amount > 0.001:
                    # ВЫПОЛНЯЕМ ПЕРЕДАЧУ
                    self.load -= safe_amount
                    neighbor.load += safe_amount
                    transferred_total += safe_amount
                    
                    # ОБНОВЛЯЕМ СТАТИСТИКУ
                    self.successful_transfers += 1
                    self.total_transferred += safe_amount
                    
                    # ОБНОВЛЯЕМ СИЛУ СВЯЗИ (если есть состояние)
                    if self.state and neighbor.id in self.state.topology['connection_strengths']:
                        current_strength = self.state.topology['connection_strengths'][neighbor.id]
                        # Успешная передача укрепляет связь
                        new_strength = min(1.0, current_strength + 0.05)
                        self.state.topology['connection_strengths'][neighbor.id] = new_strength
        
        # 6. СОХРАНЕНИЕ ИСТОРИИ НАГРУЗКИ И ЗДОРОВЬЯ
        self.load_history.append(self.load)
        self.health_history.append(self.health)
        
        if len(self.load_history) > self.max_history_length:
            self.load_history.pop(0)
            self.health_history.pop(0)
        
        # 7. ОБУЧЕНИЕ ИНТУИЦИИ НА ОСНОВЕ РЕЗУЛЬТАТА
        if use_intuition and self.state and self.intuition and intuition_advice:
            # Оценка исхода (упрощённая)
            outcome_score = 0.0
            if transferred_total > 0:
                # Успешная передача
                outcome_score = min(1.0, transferred_total * 10.0)
            else:
                # Неудачная попытка
                outcome_score = -0.2
            
            # Эмоциональная метка
            emotional_tag = "joy" if outcome_score > 0 else "disappointment"
            
            # Обучение интуиции
            intuition_data = self.state.get_for_intuition()
            self.intuition.learn_from_outcome(
                intuition_data,
                analytic_decision,
                outcome_score,
                emotional_tag
            )
        
        return transferred_total
    
    def update_health(self, delta: float):
        """
        Обновляет уровень здоровья единицы.
        
        Args:
            delta: Изменение здоровья (-0.1 до +0.1)
        """
        self.health = max(0.0, min(1.0, self.health + delta))
    
    def sabotage(self, damage: float = 0.5, extra_load: float = 0.3):
        """
        Имитация сбоя/атаки на узел.
        
        Args:
            damage: Урон здоровью (0.0 - 1.0)
            extra_load: Дополнительная нагрузка на узел
        """
        self.health = max(0.1, self.health - damage)
        self.load = min(1.0, self.load + extra_load)
        
        # Логирование
        print(f"[FractalUnit] {self.id}: саботаж! Здоровье: {self.health:.2f}, Нагрузка: {self.load:.2f}")
    
    def heal(self, amount: float = 0.1):
        """Восстановление здоровья"""
        self.health = min(1.0, self.health + amount)
    
    def get_state_report(self) -> Dict:
        """Возвращает отчёт о состоянии единицы"""
        report = {
            'id': self.id,
            'load': self.load,
            'health': self.health,
            'potential': self.local_potential,
            'neighbors': len(self.neighbors),
            'step': self.step_count,
            'total_transferred': self.total_transferred,
            'success_rate': self.successful_transfers / max(1, self.successful_transfers + self.failed_transfers)
        }
        
        if self.state:
            report.update({
                'gestalt': self.state.gestalt,
                'tendency': self.state.behavioral_tendency,
                'stability': self.state.stability_index,
                'dominant_need': max(self.state.needs.items(), key=lambda x: x[1])[0] if self.state.needs else None
            })
        
        if self.intuition:
            stats = self.intuition.get_statistics()
            report['intuition'] = {
                'success_rate': stats.get('success_rate', 0.0),
                'current_bias': stats.get('current_bias', {})
            }
        
        return report
    
    def get_detailed_diagnostics(self) -> str:
        """Возвращает детальную диагностическую информацию"""
        lines = []
        lines.append(f"=== ДИАГНОСТИКА {self.id} ===")
        lines.append(f"Нагрузка: {self.load:.3f}")
        lines.append(f"Здоровье: {self.health:.3f}")
        lines.append(f"Потенциал: {self.local_potential:.3f}")
        lines.append(f"Соседи: {len(self.neighbors)}")
        lines.append(f"Шагов: {self.step_count}")
        lines.append(f"Всего передано: {self.total_transferred:.3f}")
        
        if self.state:
            lines.append("\n--- ВНУТРЕННЕЕ СОСТОЯНИЕ ---")
            lines.append(f"Гештальт: {self.state.gestalt}")
            lines.append(f"Склонность: {self.state.behavioral_tendency}")
            lines.append(f"Стабильность: {self.state.stability_index:.3f}")
            
            lines.append("\nПотребности:")
            for need, value in sorted(self.state.needs.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {need:15}: {value:.3f}")
        
        if self.intuition and self.last_intuition_advice:
            lines.append("\n--- ИНТУИТИВНЫЙ КОНТУР ---")
            advice = self.last_intuition_advice
            lines.append(f"Совет: {advice.get('tendency', 'N/A')}")
            lines.append(f"Уверенность: {advice.get('confidence', 0.0):.3f}")
            lines.append(f"Источник: {advice.get('source', 'N/A')}")
            if 'message' in advice:
                lines.append(f"Сообщение: {advice['message']}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """Строковое представление для отладки"""
        return (f"FractalUnit(id={self.id}, load={self.load:.2f}, "
                f"health={self.health:.2f}, potential={self.local_potential:.3f})")