"""
Модуль резонансного ПИД-регулятора для ВММП.
Управляет фазовым состоянием системы через Буфер Безвременья.
"""

import numpy as np
from collections import deque

class ResonancePIDController:
    """
    ПИД-регулятор для резонансного управления через Буфер Безвременья.
    Вычисляет энергию "пинка", необходимую для приближения текущего d_min
    к целевому d_target.
    """

    def __init__(self, target_d: float, Kp: float = 1.0, Ki: float = 0.01, Kd: float = 0.1,
                 target_level: int = 5, resonance_Q: float = 10.0, resonance_width: float = 0.05):
        """
        Параметры:
        - target_d: целевое значение d_min
        - Kp, Ki, Kd: коэффициенты ПИД-регулятора
        - target_level: фрактальный уровень, на который оказывается воздействие (1-7)
        - resonance_Q: добротность резонанса (усиление амплитуды)
        - resonance_width: относительная ширина резонансного пика
        """
        self.target_d = target_d
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.target_level = target_level
        self.resonance_Q = resonance_Q
        self.resonance_width = resonance_width

        # Состояние ПИД
        self._prev_error = 0.0
        self._integral = 0.0
        self._error_history = deque(maxlen=100)

        # Флаги активности
        self.is_active = True
        self._step_counter = 0

    def _resonance_factor(self, T: float) -> float:
        """
        Вычисляет резонансный множитель для тепловой амплитуды.
        omega_level ~ 2^(-k * delta) для уровня k.
        """
        # omega_level ~ 2^(-0.7 * k)
        omega_level = 2.0 ** (-0.7 * self.target_level)
        # omega_T ~ T (нормировка на T=300K, пик резонанса около omega_level)
        omega_T = (T / 300.0) * omega_level

        detuning = (omega_T - omega_level) / (self.resonance_width * omega_level)
        factor = 1.0 + self.resonance_Q / (1.0 + detuning**2)
        return factor

    def calculate(self, current_d: float, T: float = 300.0) -> float:
        """
        Вычисляет управляющий сигнал (энергию пинка) на основе ошибки d_min.
        Возвращает величину energy_kick (в относительных единицах).
        """
        if not self.is_active:
            return 0.0

        error = self.target_d - current_d
        self._error_history.append(error)

        # ПИД-составляющие
        P = self.Kp * error

        self._integral += error
        # Ограничение интегрального насыщения
        self._integral = np.clip(self._integral, -10.0, 10.0)
        I = self.Ki * self._integral

        D = self.Kd * (error - self._prev_error)
        self._prev_error = error

        # Базовый управляющий сигнал
        u_raw = P + I + D

        # Применяем резонансный множитель
        resonance = self._resonance_factor(T)
        u_resonant = u_raw * resonance

        # Ограничиваем амплитуду пинка
        max_kick = 0.5
        energy_kick = np.clip(u_resonant, -max_kick, max_kick)

        self._step_counter += 1
        
        # === ШАМАНСКИЙ ОТЛАДОЧНЫЙ PRINT ===
        if self._step_counter % 10 == 0:  # печатаем не на каждом шагу, чтобы не спамить
            print(f"[ПИД-Шаман] Шаг: {self._step_counter:4d} | "
                  f"Текущее d: {current_d:.3f} | Цель: {self.target_d:.3f} | "
                  f"Ошибка: {error:+.3f} | P={P:+.3f} I={I:+.3f} D={D:+.3f} | "
                  f"Резонанс: {resonance:.2f} | Пинок: {energy_kick:+.4f}")
        # =================================
        
        return energy_kick

    def reset(self):
        """Сброс состояния регулятора."""
        self._prev_error = 0.0
        self._integral = 0.0
        self._error_history.clear()
        self._step_counter = 0

    def get_statistics(self) -> dict:
        """Возвращает статистику работы регулятора."""
        if len(self._error_history) == 0:
            return {}
        errors = np.array(self._error_history)
        return {
            'mean_error': float(np.mean(errors)),
            'std_error': float(np.std(errors)),
            'last_error': float(errors[-1]),
            'integral': float(self._integral),
            'steps': self._step_counter
        }