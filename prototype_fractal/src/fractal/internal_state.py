"""
InternalState - единая модель внутреннего состояния агента.
Объединяет потребности, нейромодуляторы, топологические метрики.
Является центральным источником правды для всех контуров.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time

@dataclass
class StateSnapshot:
    """Снимок состояния для истории и анализа"""
    timestamp: float
    gestalt: str
    needs: Dict[str, float]
    modulators: Dict[str, float]
    stability: float
    tendency: str

class InternalState:
    """Унифицированное внутреннее состояние фрактального агента"""
    
    def __init__(self, unit_id: str):
        self.unit_id = unit_id
        
        # 1. БАЗОВЫЕ ГОМЕОСТАТИЧЕСКИЕ ПОТРЕБНОСТИ (0-1, где 1 = максимальная потребность)
        self.needs = {
            'efficiency': 0.3,      # Стремление быть полезным (растёт при низкой нагрузке)
            'rest': 0.0,           # Потребность в отдыхе (растёт при перегреве/высокой нагрузке)
            'safety': 1.0,         # Потребность в безопасности (падает при низком health)
            'connection': 0.5,      # Потребность в социальных связях (зависит от топологии)
            'novelty': 0.2,        # Потребность в новизне (растёт при монотонии)
        }
        
        # 2. НЕЙРОМОДУЛЯТОРНЫЙ ФОН (0-1, концентрация условных "веществ")
        self.modulators = {
            'dopamine': 0.5,       # Ожидание награды / сигнал ошибки прогноза
            'norepinephrine': 0.2, # Бдительность, реакция на стресс
            'serotonin': 0.7,      # Устойчивость, терпение, стабильность настроения
            'acetylcholine': 0.4,   # Внимание, скорость обучения
            'oxytocin': 0.6,       # Доверие, социальная связь
        }
        
        # 3. ТОПОЛОГИЧЕСКИЕ МЕТРИКИ (обновляется внешне)
        self.topology = {
            'connection_strengths': {},  # Связи {neighbor_id: strength}
            'isolation_score': 0.0,      # Мера изолированности в сети (0-1)
            'centrality': 0.0,           # Центральность узла (0-1)
            'clustering_coef': 0.0,      # Коэффициент кластеризации
        }
        
        # 4. ВЫЧИСЛЕННЫЕ ПОКАЗАТЕЛИ (агрегированные состояния)
        self.gestalt = "undefined"       # Целостный образ для интуиции
        self.stability_index = 1.0       # Общая стабильность (0-1)
        self.behavioral_tendency = "neutral"  # Доминирующая склонность к действию
        
        # 5. ИСТОРИЯ ДЛЯ АНАЛИЗА ТРЕНДОВ
        self.history: List[StateSnapshot] = []
        self.max_history_length = 100
        
        # 6. КЭШ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
        self._last_update_time = time.time()
        self._cached_analytics = {}
        
        print(f"[InternalState] Создано состояние для {unit_id}")
    
    def update(self, raw_metrics: Dict) -> 'InternalState':
        """
        Основной метод обновления. Принимает сырые метрики от FractalUnit
        и пересчитывает все внутренние состояния.
        """
        current_time = time.time()
        time_delta = current_time - self._last_update_time
        self._last_update_time = current_time
        
        # 1. Обновление потребностей на основе сырых данных
        self._update_needs(
            load=raw_metrics.get('load', 0.5),
            health=raw_metrics.get('health', 1.0),
            stress=raw_metrics.get('stress', 0.0),
            time_delta=time_delta
        )
        
        # 2. Обновление модуляторов на основе изменений
        self._update_modulators(
            prediction_error=raw_metrics.get('prediction_error', 0.0),
            novelty=raw_metrics.get('novelty', 0.0),
            success_rate=raw_metrics.get('success_rate', 0.5),
            time_delta=time_delta
        )
        
        # 3. Обновление топологических метрик (если предоставлены)
        if 'topology_metrics' in raw_metrics:
            self._update_topology(raw_metrics['topology_metrics'])
        
        # 4. Вычисление агрегированных показателей
        self.stability_index = self._calculate_stability_index()
        self.gestalt = self._generate_gestalt()
        self.behavioral_tendency = self._resolve_behavioral_tendency()
        
        # 5. Сохранение в историю
        self._save_to_history()
        
        # 6. Инвалидация кэша
        self._cached_analytics = {}
        
        return self
    
    def _update_needs(self, load: float, health: float, stress: float, time_delta: float):
        """Логика обновления потребностей с учётом временного интервала"""
        
        # Параметры адаптации (скорость изменения потребностей)
        alpha = 0.1 * min(1.0, time_delta * 10)  # Нормализация по времени
        
        # 1. Потребность в отдыхе растёт с нагрузкой и стрессом
        rest_need = load * 0.7 + stress * 0.3
        self.needs['rest'] = (1 - alpha) * self.needs['rest'] + alpha * rest_need
        
        # 2. Потребность в безопасности обратно пропорциональна здоровью
        safety_need = health ** 2  # Квадрат для усиления эффекта при низком health
        self.needs['safety'] = (1 - alpha) * self.needs['safety'] + alpha * safety_need
        
        # 3. Потребность в эффективности
        if health > 0.3:
            efficiency_need = 1.0 - load if load > 0.1 else 0.0
        else:
            efficiency_need = 0.0  # Слишком больной для эффективной работы
        self.needs['efficiency'] = (1 - alpha) * self.needs['efficiency'] + alpha * efficiency_need
        
        # 4. Потребность в связи зависит от изоляции
        connection_need = 1.0 - self.topology['isolation_score']
        self.needs['connection'] = (1 - alpha) * self.needs['connection'] + alpha * connection_need
        
        # 5. Потребность в новизне (растёт при стабильности, падает при стрессах)
        novelty_need = self.stability_index * 0.8 * (1.0 - stress)
        self.needs['novelty'] = (1 - alpha) * self.needs['novelty'] + alpha * novelty_need
        
        # Нормализация: суммарная потребность не должна превышать 2.0
        total_need = sum(self.needs.values())
        if total_need > 2.0:
            scale_factor = 2.0 / total_need
            for key in self.needs:
                self.needs[key] *= scale_factor
    
    def _update_modulators(self, prediction_error: float, novelty: float, 
                          success_rate: float, time_delta: float):
        """Логика обновления 'нейрохимического' фона"""
        
        beta = 0.05 * min(1.0, time_delta * 10)  # Скорость изменения модуляторов
        
        # 1. Дофамин: растёт при точных прогнозах и успехах
        dopaminergic_signal = (1.0 - prediction_error) * 0.7 + success_rate * 0.3
        self.modulators['dopamine'] = (1 - beta) * self.modulators['dopamine'] + beta * dopaminergic_signal
        
        # 2. Норадреналин: реакция на новизну и ошибки (стресс)
        norepinephric_signal = novelty * 0.6 + prediction_error * 0.4
        self.modulators['norepinephrine'] = (1 - beta) * self.modulators['norepinephrine'] + beta * norepinephric_signal
        
        # 3. Серотонин: растёт при стабильности и удовлетворении потребности в безопасности
        safety_satisfaction = 1.0 - self.needs['safety']
        self.modulators['serotonin'] = (1 - beta*0.5) * self.modulators['serotonin'] + (beta*0.5) * safety_satisfaction
        
        # 4. Ацетилхолин: внимание, зависит от новизны и норадреналина
        cholinergic_signal = novelty * 0.4 + self.modulators['norepinephrine'] * 0.6
        self.modulators['acetylcholine'] = (1 - beta) * self.modulators['acetylcholine'] + beta * cholinergic_signal
        
        # 5. Окситоцин: социальное доверие, зависит от связей и серотонина
        oxytocic_signal = (1.0 - self.topology['isolation_score']) * 0.5 + self.modulators['serotonin'] * 0.5
        self.modulators['oxytocin'] = (1 - beta*0.3) * self.modulators['oxytocin'] + (beta*0.3) * oxytocic_signal
        
        # Гарантируем границы [0, 1]
        for key in self.modulators:
            self.modulators[key] = max(0.0, min(1.0, self.modulators[key]))
    
    def _update_topology(self, metrics: Dict):
        """Обновление топологических метрик"""
        for key, value in metrics.items():
            if key in self.topology:
                # Плавное обновление топологических метрик
                self.topology[key] = 0.7 * self.topology[key] + 0.3 * value
    
    def _calculate_stability_index(self) -> float:
        """Вычисление общего индекса стабильности (0-1)"""
        
        factors = []
        weights = []
        
        # 1. Стабильность нагрузки (если есть история)
        if len(self.history) >= 3:
            recent_loads = [snap.needs.get('rest', 0.0) for snap in self.history[-3:]]
            load_variance = np.std(recent_loads) if recent_loads else 0.0
            load_stability = 1.0 - min(1.0, load_variance * 5.0)
            factors.append(load_stability)
            weights.append(0.2)
        
        # 2. Стабильность здоровья (из потребности в безопасности)
        health_stability = 1.0 - self.needs['safety']  # Чем выше безопасность, тем стабильнее
        factors.append(health_stability)
        weights.append(0.3)
        
        # 3. Стабильность модуляторов (низкая вариация)
        modulator_values = list(self.modulators.values())
        modulator_variance = np.std(modulator_values) if len(modulator_values) > 1 else 0.0
        modulator_stability = 1.0 - min(1.0, modulator_variance * 3.0)
        factors.append(modulator_stability)
        weights.append(0.2)
        
        # 4. Топологическая стабильность
        topo_stability = 1.0 - self.topology['isolation_score']
        factors.append(topo_stability)
        weights.append(0.3)
        
        # Взвешенное среднее
        if factors and weights:
            stability = np.average(factors, weights=weights[:len(factors)])
            return max(0.0, min(1.0, stability))
        
        return 0.5  # Значение по умолчанию
    
    def _generate_gestalt(self) -> str:
        """
        Генерирует целостный гештальт состояния на основе всех параметров.
        Это ключевой метод для интуитивного контура.
        """
        components = []
        
        # 1. Определяем доминирующие потребности ( > 0.7)
        dominant_needs = []
        for need_name, need_value in self.needs.items():
            if need_value > 0.7:
                dominant_needs.append(need_name.upper())
        
        if dominant_needs:
            components.append(f"NEED_{'_'.join(dominant_needs[:2])}")
        
        # 2. Определяем доминирующие модуляторные состояния
        if self.modulators['norepinephrine'] > 0.7:
            components.append("STRESSED")
        elif self.modulators['dopamine'] > 0.7:
            components.append("OPTIMISTIC")
        elif self.modulators['serotonin'] < 0.3:
            components.append("VULNERABLE")
        elif self.modulators['oxytocin'] > 0.7:
            components.append("CONNECTED")
        
        # 3. Добавляем топологический компонент
        if self.topology['isolation_score'] > 0.8:
            components.append("ISOLATED")
        elif self.topology['centrality'] > 0.7:
            components.append("CENTRAL")
        
        # 4. Общая стабильность
        if self.stability_index > 0.8:
            components.append("STABLE")
        elif self.stability_index < 0.3:
            components.append("CRITICAL")
        elif self.stability_index < 0.6:
            components.append("UNSTABLE")
        
        # 5. Поведенческая склонность
        if self.behavioral_tendency != "neutral":
            components.append(self.behavioral_tendency)
        
        return "-".join(components) if components else "BALANCED"
    
    def _resolve_behavioral_tendency(self) -> str:
        """
        Разрешает конфликт потребностей и модуляторов в единую склонность к действию.
        Приоритет: безопасность > отдых > эффективность.
        """
        
        # Критические состояния (приоритет 1)
        if self.needs['safety'] < 0.3:
            return "SELF_PRESERVATION"  # Выживание - базовая потребность
        
        if self.modulators['norepinephrine'] > 0.8:
            return "RISK_AVERSION"  # Высокий стресс - избегание рисков
        
        # Функциональные состояния (приоритет 2)
        if self.needs['rest'] > 0.8:
            return "ENERGY_CONSERVATION"  # Нужен отдых
        
        if self.needs['efficiency'] > 0.7 and self.modulators['dopamine'] > 0.6:
            return "OPPORTUNISTIC"  # Готов к активной работе
        
        if self.needs['connection'] > 0.7 and self.modulators['oxytocin'] > 0.6:
            return "COOPERATIVE"  # Социально ориентирован
        
        if self.needs['novelty'] > 0.7 and self.modulators['acetylcholine'] > 0.6:
            return "EXPLORATORY"  # Исследовательский настрой
        
        # Нейтральное/адаптивное состояние
        return "ADAPTIVE"
    
    def _save_to_history(self):
        """Сохранение текущего состояния в историю"""
        snapshot = StateSnapshot(
            timestamp=time.time(),
            gestalt=self.gestalt,
            needs=self.needs.copy(),
            modulators=self.modulators.copy(),
            stability=self.stability_index,
            tendency=self.behavioral_tendency
        )
        
        self.history.append(snapshot)
        
        # Ограничение длины истории
        if len(self.history) > self.max_history_length:
            self.history = self.history[-self.max_history_length:]
    
    def get_for_intuition(self) -> Dict:
        """Возвращает структурированные данные для интуитивного контура"""
        if 'intuition' not in self._cached_analytics:
            self._cached_analytics['intuition'] = {
                'gestalt': self.gestalt,
                'tendency': self.behavioral_tendency,
                'urgency': 1.0 - self.stability_index,  # Срочность обратна стабильности
                'modulator_profile': self.modulators.copy(),
                'dominant_need': max(self.needs.items(), key=lambda x: x[1])[0] if self.needs else None,
                'topology_summary': {
                    'isolation': self.topology['isolation_score'],
                    'connections': len(self.topology['connection_strengths']),
                    'centrality': self.topology['centrality']
                }
            }
        return self._cached_analytics['intuition']
    
    def get_for_analytics(self) -> Dict:
        """Возвращает данные для аналитических контуров"""
        if 'analytics' not in self._cached_analytics:
            # Динамическая цель на основе состояния
            base_target = 0.7  # Базовая целевая нагрузка
            rest_adjustment = self.needs['rest'] * 0.3  # Учитываем потребность в отдыхе
            effective_target = base_target * (1.0 - rest_adjustment)
            
            self._cached_analytics['analytics'] = {
                'effective_target_load': max(0.1, min(1.0, effective_target)),
                'transfer_aggressiveness': 0.5 + (self.modulators['norepinephrine'] * 0.5),
                'learning_rate': 0.1 * self.modulators['acetylcholine'],
                'risk_tolerance': self.modulators['serotonin'],
                'cooperation_bias': self.modulators['oxytocin'],
                'exploration_bonus': self.modulators['dopamine'] * self.needs['novelty']
            }
        return self._cached_analytics['analytics']
    
    def get_diagnostic_report(self) -> str:
        """Генерирует диагностический отчёт о состоянии"""
        report = []
        report.append(f"=== ДИАГНОСТИКА {self.unit_id} ===")
        report.append(f"Гештальт: {self.gestalt}")
        report.append(f"Склонность: {self.behavioral_tendency}")
        report.append(f"Стабильность: {self.stability_index:.3f}")
        report.append("\nПотребности:")
        for need, value in sorted(self.needs.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {need:15}: {value:.3f}")
        report.append("\nМодуляторы:")
        for mod, value in sorted(self.modulators.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {mod:15}: {value:.3f}")
        
        return "\n".join(report)
    
    def reset(self):
        """Сброс состояния к начальным значениям (для тестирования)"""
        self.__init__(self.unit_id)