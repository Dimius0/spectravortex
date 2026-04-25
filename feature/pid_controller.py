"""
Универсальный ПИД-регулятор для адаптивной настройки параметров.
"""

import numpy as np
from collections import deque
from dataclasses import dataclass

@dataclass
class PIDConfig:
    """Конфигурация ПИД-регулятора"""
    Kp: float = 0.1
    Ki: float = 0.01
    Kd: float = 0.05
    setpoint: float = 0.0
    output_min: float = 0.1
    output_max: float = 4.0
    buffer_size: int = 50

class PIDController:
    """Универсальный ПИД-регулятор с буфером для усреднения ошибки"""
    
    def __init__(self, name: str, config: PIDConfig = None):
        self.name = name
        self.config = config or PIDConfig()
        
        # Состояние регулятора
        self.integral = 0.0
        self.prev_error = 0.0
        self.output = 1.0  # начальное значение
        
        # Буфер для усреднения ошибки (анти-самовозбуждение)
        self.error_buffer = deque(maxlen=self.config.buffer_size)
        
        # Статистика
        self.step_count = 0
        self.history = []
        
    def update(self, current_value: float, dt: float = 1.0) -> float:
        """
        Обновить состояние регулятора и вернуть новое output значение.
        
        Args:
            current_value: текущее значение управляемой переменной
            dt: шаг по времени (для интегральной/дифференциальной составляющих)
        """
        self.step_count += 1
        
        # 1. Вычисляем сырую ошибку
        raw_error = current_value - self.config.setpoint
        
        # 2. Добавляем в буфер
        self.error_buffer.append(raw_error)
        
        # 3. Используем усреднённую ошибку (только если буфер заполнен)
        if len(self.error_buffer) == self.config.buffer_size:
            error = np.mean(self.error_buffer)
        else:
            error = raw_error
        
        # 4. Пропорциональная составляющая
        P = self.config.Kp * error
        
        # 5. Интегральная составляющая
        self.integral += error * dt
        I = self.config.Ki * self.integral
        
        # 6. Дифференциальная составляющая
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        D = self.config.Kd * derivative
        self.prev_error = error
        
        # 7. Суммарная поправка
        delta = P + I + D
        
        # 8. Применяем поправку
        self.output += delta
        
        # 9. Ограничиваем выход
        self.output = max(self.config.output_min, min(self.config.output_max, self.output))
        
        # 10. Сохраняем историю
        self.history.append({
            'step': self.step_count,
            'raw_error': raw_error,
            'avg_error': error if len(self.error_buffer) == self.config.buffer_size else None,
            'P': P, 'I': I, 'D': D,
            'output': self.output
        })
        
        return self.output
    
    def reset(self):
        """Сбросить состояние регулятора"""
        self.integral = 0.0
        self.prev_error = 0.0
        self.output = 1.0
        self.error_buffer.clear()
        self.step_count = 0
        self.history = []
    
    def get_stats(self) -> dict:
        """Получить статистику работы регулятора"""
        if not self.history:
            return {}
        return {
            'name': self.name,
            'final_output': self.output,
            'steps': self.step_count,
            'avg_error': np.mean([h['avg_error'] for h in self.history if h['avg_error'] is not None]),
            'output_change': self.output - self.history[0]['output'],
        }