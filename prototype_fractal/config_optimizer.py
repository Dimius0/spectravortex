# config_optimizer.py
"""
НАСТРОЙКА И ОПТИМИЗАЦИЯ ПАРАМЕТРОВ СИСТЕМЫ
Для эффективной работы с InternalState и IntuitionEngine
"""

import numpy as np
from typing import Dict, List, Tuple
import json
from pathlib import Path

class SystemOptimizer:
    """Оптимизатор параметров системы для максимальной адаптивности"""
    
    # БАЗОВЫЕ ПАРАМЕТРЫ ДЛЯ НАСТРОЙКИ
    DEFAULT_CONFIG = {
        # Параметры FractalUnit
        'unit': {
            'base_transfer_rate': 0.08,      # Была 0.05 - увеличиваем на 60%
            'health_recovery_rate': 0.02,    # Скорость восстановления здоровья
            'max_load': 1.0,                 # Максимальная нагрузка
            'min_health': 0.1,               # Минимальное здоровье
            'history_length': 50,            # Длина истории
        },
        
        # Параметры InternalState
        'internal_state': {
            'need_update_rate': 0.15,        # Скорость обновления потребностей (было 0.1)
            'modulator_update_rate': 0.08,   # Скорость обновления модуляторов (было 0.05)
            'stability_calculation_interval': 0.5,  # Интервал расчёта стабильности (сек)
            'max_need_sum': 2.0,             # Максимальная сумма потребностей
            'safety_threshold': 0.3,         # Порог для режима самосохранения
        },
        
        # Параметры IntuitionEngine
        'intuition': {
            'min_confidence_threshold': 0.4,  # Минимальная уверенность для учёта (было 0.3)
            'override_threshold': 0.75,       # Порог переопределения (было 0.7)
            'learning_rate': 0.12,            # Скорость обучения (было 0.1)
            'max_engrams': 120,               # Максимум энграмм (было 100)
            'engram_similarity_threshold': 0.6,  # Порог схожести энграмм
        },
        
        # Параметры сети
        'network': {
            'simulation_steps_per_second': 10,  # Шагов в секунду
            'target_load_range': (0.5, 0.7),    # Диапазон целевой нагрузки
            'auto_restructure': True,           # Автоматическая перестройка связей
            'restructure_threshold': 0.15,      # Порог для перестройки
        },
        
        # Коэффициенты для разных режимов
        'mode_multipliers': {
            'SELF_PRESERVATION': {
                'transfer_rate': 2.5,      # Агрессивная разгрузка
                'risk_tolerance': 0.1,     # Минимальный риск
                'health_recovery': 1.5,    # Ускоренное восстановление
            },
            'RISK_AVERSION': {
                'transfer_rate': 1.3,
                'risk_tolerance': 0.3,
                'health_recovery': 1.2,
            },
            'ENERGY_CONSERVATION': {
                'transfer_rate': 0.7,
                'risk_tolerance': 0.8,     # Можно рисковать, чтобы отдохнуть
                'health_recovery': 2.0,    # Максимальное восстановление
            },
            'OPPORTUNISTIC': {
                'transfer_rate': 1.8,
                'risk_tolerance': 0.7,
                'health_recovery': 0.9,
            },
            'COOPERATIVE': {
                'transfer_rate': 1.4,
                'risk_tolerance': 0.6,
                'health_recovery': 1.1,
            },
            'EXPLORATORY': {
                'transfer_rate': 1.6,
                'risk_tolerance': 0.9,     # Максимальный риск для исследования
                'health_recovery': 0.8,
            },
        }
    }
    
    def __init__(self, config_path: str = None):
        """Инициализация с конфигурацией из файла или по умолчанию"""
        if config_path and Path(config_path).exists():
            self.config = self.load_config(config_path)
            print(f"[Optimizer] Загружена конфигурация из {config_path}")
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            print("[Optimizer] Используется конфигурация по умолчанию")
    
    def load_config(self, filepath: str) -> Dict:
        """Загрузка конфигурации из файла"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_config(self, filepath: str):
        """Сохранение конфигурации в файл"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"[Optimizer] Конфигурация сохранена в {filepath}")
    
    def apply_to_unit(self, unit):
        """Применение оптимизированных параметров к FractalUnit"""
        if not hasattr(unit, 'state'):
            return
        
        # Увеличиваем базовую скорость передачи
        unit.base_transfer_rate = self.config['unit']['base_transfer_rate']
        
        # Настраиваем параметры InternalState
        if hasattr(unit.state, '_update_needs'):
            # Можно было бы настроить, но нужен доступ к приватным методам
            pass
        
        # Настраиваем параметры IntuitionEngine
        if hasattr(unit, 'intuition'):
            unit.intuition.min_confidence_threshold = self.config['intuition']['min_confidence_threshold']
            unit.intuition.override_threshold = self.config['intuition']['override_threshold']
            unit.intuition.learning_rate = self.config['intuition']['learning_rate']
            unit.intuition.max_engrams = self.config['intuition']['max_engrams']
    
    def get_mode_multipliers(self, mode: str) -> Dict:
        """Возвращает множители для указанного режима"""
        return self.config['mode_multipliers'].get(mode, {
            'transfer_rate': 1.0,
            'risk_tolerance': 0.5,
            'health_recovery': 1.0
        })
    
    def optimize_for_scenario(self, scenario: str) -> Dict:
        """Оптимизация параметров для конкретного сценария"""
        
        optimized = self.config.copy()
        
        if scenario == "fast_recovery":
            # Оптимизация для быстрого восстановления после сбоев
            optimized['unit']['base_transfer_rate'] = 0.12  # +50%
            optimized['unit']['health_recovery_rate'] = 0.03
            optimized['internal_state']['need_update_rate'] = 0.2
            optimized['mode_multipliers']['SELF_PRESERVATION']['transfer_rate'] = 3.0
            optimized['mode_multipliers']['SELF_PRESERVATION']['health_recovery'] = 2.0
            
        elif scenario == "stable_operation":
            # Оптимизация для стабильной работы
            optimized['unit']['base_transfer_rate'] = 0.06  # Более плавно
            optimized['internal_state']['need_update_rate'] = 0.1
            optimized['intuition']['min_confidence_threshold'] = 0.5  # Более консервативно
            optimized['network']['target_load_range'] = (0.6, 0.7)    # Ужекий диапазон
            
        elif scenario == "high_stress":
            # Оптимизация для работы под высокой нагрузкой
            optimized['unit']['base_transfer_rate'] = 0.1
            optimized['internal_state']['safety_threshold'] = 0.4  # Раньше включаем самосохранение
            optimized['mode_multipliers']['RISK_AVERSION']['transfer_rate'] = 1.5
            
        elif scenario == "learning_focused":
            # Оптимизация для быстрого обучения
            optimized['intuition']['learning_rate'] = 0.2
            optimized['intuition']['max_engrams'] = 200
            optimized['intuition']['engram_similarity_threshold'] = 0.5  # Более широкое распознавание
        
        return optimized
    
    def run_auto_tuning(self, test_function, iterations: int = 100):
        """
        Автоматическая настройка параметров методом поиска по сетке
        
        Args:
            test_function: Функция, возвращающая оценку эффективности (0-1)
            iterations: Количество итераций настройки
        """
        print("\n" + "="*60)
        print("АВТОМАТИЧЕСКАЯ НАСТРОЙКА ПАРАМЕТРОВ")
        print("="*60)
        
        best_score = 0
        best_config = self.config.copy()
        
        # Параметры для настройки и их диапазоны
        tuning_params = {
            'unit.base_transfer_rate': (0.05, 0.15, 0.01),  # мин, макс, шаг
            'unit.health_recovery_rate': (0.01, 0.05, 0.005),
            'internal_state.need_update_rate': (0.05, 0.25, 0.025),
            'intuition.learning_rate': (0.05, 0.25, 0.025),
            'intuition.override_threshold': (0.6, 0.9, 0.05),
        }
        
        for i in range(iterations):
            # Случайное изменение параметров
            temp_config = self.config.copy()
            
            for param_path, (min_val, max_val, step) in tuning_params.items():
                # Получаем текущее значение
                parts = param_path.split('.')
                current = temp_config
                for part in parts[:-1]:
                    current = current[part]
                
                # Изменяем значение
                current[parts[-1]] = np.clip(
                    current[parts[-1]] + np.random.uniform(-step, step),
                    min_val, max_val
                )
            
            # Тестируем новую конфигурацию
            self.config = temp_config
            score = test_function()
            
            print(f"Итерация {i+1:3d}/{iterations}: Оценка = {score:.4f}")
            
            if score > best_score:
                best_score = score
                best_config = temp_config.copy()
                print(f"  🎯 Новый лучший результат: {score:.4f}")
        
        # Восстанавливаем лучшую конфигурацию
        self.config = best_config
        
        print("\n" + "="*60)
        print(f"НАИЛУЧШАЯ ОЦЕНКА: {best_score:.4f}")
        print("Оптимизированные параметры:")
        for param_path in tuning_params.keys():
            parts = param_path.split('.')
            value = self.config
            for part in parts:
                value = value[part]
            print(f"  {param_path}: {value}")
        print("="*60)
        
        return best_score, best_config

# Утилита для применения оптимизированной конфигурации
def apply_optimized_config():
    """Применение оптимизированной конфигурации ко всей системе"""
    
    optimizer = SystemOptimizer()
    
    # Оптимизируем для быстрого восстановления
    optimized_config = optimizer.optimize_for_scenario("fast_recovery")
    
    # Создаём файл конфигурации
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "optimized_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(optimized_config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Оптимизированная конфигурация создана: {config_file}")
    print("\nКлючевые изменения:")
    print(f"  • Базовая скорость передачи: {optimized_config['unit']['base_transfer_rate']} (+60%)")
    print(f"  • Скорость восстановления здоровья: {optimized_config['unit']['health_recovery_rate']}")
    print(f"  • Режим самосохранения: передача x{optimized_config['mode_multipliers']['SELF_PRESERVATION']['transfer_rate']}")
    
    return config_file

if __name__ == "__main__":
    apply_optimized_config()