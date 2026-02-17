"""
FractalCluster — кластер фрактальных единиц как супер-узел.
"""
from typing import List
from .unit import FractalUnit
from .network import FractalNetwork

class FractalCluster(FractalUnit):
    """Кластер единиц, ведущий себя как одна фрактальная единица."""
    
    def __init__(self, cluster_id: str, child_units: List[FractalUnit]):
        """
        Инициализация кластера.
        
        Args:
            cluster_id: Идентификатор кластера
            child_units: Список дочерних единиц
        """
        super().__init__(cluster_id)
        self.child_units = child_units
        self.child_network = None
        
        # Инициализируем внутреннюю сеть
        if len(child_units) > 1:
            self.child_network = FractalNetwork.__new__(FractalNetwork)
            self.child_network.units = child_units
            self.child_network.topology = "mesh"
            self.child_network.step_count = 0
            self.child_network.history = []
    
    @property
    def load(self) -> float:
        """Средняя нагрузка кластера."""
        if not self.child_units:
            return 0.0
        return sum(unit.load for unit in self.child_units) / len(self.child_units)
    
    @load.setter
    def load(self, value: float):
        """Распределение нагрузки по кластеру."""
        if not self.child_units:
            return
        
        # Простое равномерное распределение
        for unit in self.child_units:
            unit.load = value
    
    @property
    def health(self) -> float:
        """Наихудшее здоровье в кластере."""
        if not self.child_units:
            return 1.0
        return min(unit.health for unit in self.child_units)
    
    def compute_potential(self, target_load: float = 0.7) -> float:
        """
        Вычисление потенциала кластера как супер-узла.
        """
        if not self.child_units:
            self.local_potential = 0.0
            return 0.0
        
        # 1. Все дочерние единицы вычисляют свои потенциалы
        child_potentials = []
        for unit in self.child_units:
            child_potentials.append(unit.compute_potential(target_load))
        
        # 2. Внутренняя балансировка (если есть сеть)
        if self.child_network and len(self.child_units) > 1:
            self.child_network.simulate_step(target_load)
        
        # 3. Потенциал кластера = средний потенциал + штраф за неоднородность
        avg_potential = sum(child_potentials) / len(child_potentials)
        
        # Штраф за разброс потенциалов внутри кластера
        if len(child_potentials) > 1:
            max_diff = max(child_potentials) - min(child_potentials)
            imbalance_penalty = max_diff * 0.5
        else:
            imbalance_penalty = 0.0
        
        self.local_potential = avg_potential + imbalance_penalty
        return self.local_potential
    
    def transfer_load(self, transfer_rate: float = 0.05) -> float:
        """
        Передача нагрузки на уровне кластера.
        """
        if not self.child_network or len(self.child_units) <= 1:
            return 0.0
        
        # Внутренняя балансировка
        internal_transferred = 0.0
        for _ in range(3):  # Несколько итераций для лучшей балансировки
            for unit in self.child_units:
                internal_transferred += unit.transfer_load(transfer_rate * 0.5)
        
        return internal_transferred
