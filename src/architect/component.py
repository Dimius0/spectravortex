"""
азовый класс компонента для architect.
"""

from dataclasses import dataclass
import math
import random
from .temporal_state import TemporalState


@dataclass
class Component:
    """азовый компонент системы"""
    id: int
    charge: float = 1.0
    health: float = 1.0
    load: float = 0.3
    temporal: TemporalState = None

    def __post_init__(self):
        """нициализация после создания"""
        self.emergency = 0.0
        self.energy = 1.0
        self.active = True
        self.lifespan = 120
        self.age = 0
        self.mode = "normal"
        if self.temporal is None:
            base_freq = 1.0 / (abs(self.charge) + 0.1)
            self.temporal = TemporalState.random_init(base_freq)

    def check_fly_mode(self, threat_level: float = None):
        """
        роверяет, нужно ли включить режим мухи или черепахи.

        Args:
            threat_level: внешний уровень угрозы (если None, вычисляется из нагрузки)
        """
        if threat_level is None:
            threat = (1.0 - self.health) * 0.7 + self.load * 0.3
        else:
            threat = threat_level

        if threat > 0.6:
            factor = 1.0 + threat * 4.0
            self.temporal.fly_mode(factor)
            self.emergency = factor
            self.mode = "fly"
            return "fly"
        elif threat < 0.2:
            factor = 0.5
            self.temporal.turtle_mode(factor)
            self.emergency = -factor
            self.mode = "turtle"
            return "turtle"
        else:
            self.emergency = 0.0
            self.mode = "normal"
            return "normal"

    def priority_energy_redistribution(self, companions):
        """
        ринцип приоритетного перераспределения энергии:
        слабый ищет, кому передать ресурс, сильный принимает.

        Args:
            companions: список других компонентов

        Returns:
            Component: компонент, который принял ресурс (или None)
        """
        if self.energy < 0.2 and self.health < 0.3 and self.active:
            viable = [c for c in companions if c.id != self.id and c.active]
            if not viable:
                return None

            strong = max(viable,
                        key=lambda c: c.health * abs(c.charge) * len(getattr(c, 'neighbors', [])))

            transfer = self.energy * 0.8
            strong.energy += transfer
            strong.health = min(1.0, strong.health * 1.1)

            self.energy -= transfer
            self.active = False
            self.health = 0.0
            self.mode = "depleted"

            print(f"🔄 {self.id} передал {transfer:.2f} энергии {strong.id}")
            return strong

        return None

    def low_power_mode(self):
        """
        ежим пониженного энергопотребления (спячка).
        ктивируется при энергии < 0.1 и отсутствии доноров.
        """
        if self.energy < 0.1 and self.active:
            self.temporal.frequency = 0.01
            self.temporal.amplitude = 0.1
            self.energy_consumption = 0.01
            self.mode = "low_power"
            return True
        return False

    def graceful_termination(self, memory_pool, energy_pool):
        """
        авершение цикла жизни компонента с передачей опыта и энергии.

        Args:
            memory_pool: пул для сохранения опыта
            energy_pool: пул для возврата энергии

        Returns:
            bool: успешность завершения
        """
        if self.age > self.lifespan and self.active:
            # передаём опыт
            memory_pool.append({
                'id': self.id,
                'charge': self.charge,
                'health_history': getattr(self, 'health_history', []),
                'load_history': getattr(self, 'load_history', [])
            })
            # возвращаем часть энергии
            energy_pool.append(self.energy * 0.3)
            self.active = False
            self.mode = "terminated"
            print(f"✓ омпонент {self.id} завершил цикл, опыт сохранён")
            return True
        return False

    @property
    def viability(self):
        """изнестойкость компонента"""
        return self.health * abs(self.charge) * len(getattr(self, 'neighbors', []))
