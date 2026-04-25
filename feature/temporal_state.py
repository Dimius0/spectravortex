"""
Модуль эмерджентного времени для architect.
Основан на принципах ВММП и фрактальной временной иерархии.
"""

from dataclasses import dataclass
from enum import Enum
import math
import random


class TimeLayer(Enum):
    """Уровни временной иерархии"""
    UNIT = "unit"        # отдельный компонент
    CLUSTER = "cluster"  # группа синхронизированных компонентов
    NETWORK = "network"  # вся сеть
    SYSTEM = "system"    # глобальное системное время


@dataclass
class TemporalState:
    """
    Временное состояние компонента или системы.
    
    Поля:
        phase: текущая фаза (0-2π)
        frequency: частота (обратное характерное время)
        amplitude: амплитуда (сила влияния на соседей)
        stability: устойчивость временного состояния (0-1)
    """
    phase: float = 0.0
    frequency: float = 1.0
    amplitude: float = 1.0
    stability: float = 1.0
    
    def __post_init__(self):
        """Автоматически вычисляем масштаб времени"""
        self.time_scale = 1.0 / max(0.01, self.frequency)
    
    @classmethod
    def random_init(cls, base_freq: float = 1.0):
        """Случайная инициализация для нового компонента"""
        return cls(
            phase=random.random() * 2 * math.pi,
            frequency=base_freq * (0.8 + 0.4 * random.random()),
            amplitude=random.random() * 0.5 + 0.5,
            stability=random.random() * 0.3 + 0.7
        )
    
    def phase_diff(self, other: 'TemporalState') -> float:
        """Разность фаз с другим состоянием (нормированная)"""
        diff = (self.phase - other.phase + math.pi) % (2 * math.pi) - math.pi
        return diff
    
    def kuramoto_coupling(self, other: 'TemporalState', strength: float = 0.1) -> float:
        """Вклад в изменение фазы по модели Курамото"""
        return strength * math.sin(self.phase_diff(other))
    

    def fly_mode(self, factor: float = 2.0):
        """
        Активирует режим мухи — ускорение времени.
        
        Args:
            factor: коэффициент ускорения (1.0 = норма, >1.0 = быстрее)
        """
        self.frequency *= factor
        self.time_scale = 1.0 / max(0.01, self.frequency)
        # В режиме мухи амплитуда падает (энергия на ускорение)
        self.amplitude *= 0.9
        
    def turtle_mode(self, factor: float = 0.5):
        """
        Активирует режим черепахи — замедление времени.
        
        Args:
            factor: коэффициент замедления (<1.0 = медленнее)
        """
        self.frequency *= factor
        self.time_scale = 1.0 / max(0.01, self.frequency)
        # В режиме черепахи амплитуда растёт (накопление энергии)
        self.amplitude *= 1.1
        
    def emergency_level(self, threat: float) -> float:
        """
        Вычисляет уровень критичности на основе угрозы.
        
        Args:
            threat: уровень угрозы (0-1)
            
        Returns:
            float: коэффициент ускорения (1.0 + threat * 4)
        """
        # При угрозе 1.0 ускоряемся в 5 раз
        return 1.0 + threat * 4.0
    def synchronize_with(self, other: 'TemporalState', dt: float = 0.1):
        """Один шаг синхронизации с соседом"""
        coupling = self.kuramoto_coupling(other)
        self.phase = (self.phase + coupling * dt) % (2 * math.pi)
