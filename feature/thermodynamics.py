"""
Термодинамический модуль для SpectraVortex.
Интеграция температуры (T) и давления (P) в расчёты поля H.
Включает динамическую стабильность решётки (фононный спектр).
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List, Callable
from scipy.optimize import bisect

# ... (весь существующий код до класса ThermodynamicState остаётся без изменений) ...

@dataclass
class ThermodynamicState:
    temperature: float  # K
    pressure: float     # GPa
    
    T_lambda: float = 450.0
    K0: float = 200.0
    alpha_T: float = 0.15
    beta_P: float = 0.005
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        if self.temperature < 0:
            raise ValueError("Temperature must be >= 0")
        if self.pressure < 0:
            raise ValueError("Pressure must be >= 0")
    
    @property
    def thermal_energy(self) -> float:
        return 8.617e-5 * self.temperature
    
    @property
    def temperature_factor(self) -> float:
        if self.temperature < self.T_lambda:
            return 1.0 - self.alpha_T * (self.temperature / self.T_lambda)**2
        else:
            return np.exp(-(self.temperature - self.T_lambda) / self.T_lambda)
    
    @property
    def pressure_factor(self) -> float:
        return 1.0 + self.pressure / self.K0
    
    @property
    def volume_factor(self) -> float:
        n = 3.0
        return (1.0 + self.pressure / self.K0) ** (-1.0 / n)
    
    def get_equilibrium_distance(self, d0: float) -> float:
        beta_T = 1.2e-5
        beta_P = 0.005
        d_T = d0 * (1.0 + beta_T * self.temperature)
        d_P = d_T * (1.0 - beta_P * self.pressure)
        return d_P
    
    def get_critical_pressure_geometric(self, r0: float) -> float:
        """Геометрическое критическое давление (старая формула)."""
        r0_m = r0 * 1e-10
        hbar_si = 1.0545718e-34
        m_e_si = 9.1093837e-31
        P_crit_si = hbar_si**2 / (m_e_si * r0_m**5)
        return P_crit_si * 1e-9


class ThermodynamicCalculator:
    """Калькулятор термодинамических свойств материалов."""
    
    def __init__(self, state: ThermodynamicState):
        self.state = state
    
    # ... (методы formation_enthalpy, stability_score, half_life_temperature_correction остаются без изменений) ...

    def get_critical_pressure(self, 
                              r0: float,
                              energy_function: Optional[Callable] = None,
                              positions: Optional[np.ndarray] = None,
                              elements: Optional[List] = None) -> float:
        """
        Вычисляет критическое давление синтеза с учётом динамической стабильности.
        
        Если energy_function и positions переданы, выполняется проверка фононного спектра.
        Давление увеличивается до тех пор, пока все мнимые моды не исчезнут.
        """
        # 1. Геометрическая оценка (нижняя граница)
        P_geom = self.state.get_critical_pressure_geometric(r0)
        
        # 2. Если нет данных для динамического анализа, возвращаем геометрическую оценку
        if energy_function is None or positions is None:
            return P_geom
        
        # 3. Проверка динамической стабильности
        def is_stable_at_pressure(P_test: float) -> bool:
            """Проверяет, стабильна ли структура при давлении P_test."""
            test_state = ThermodynamicState(self.state.temperature, P_test)
            return check_phonon_stability(positions, elements, energy_function, test_state)
        
        # 4. Если уже при геометрическом давлении структура стабильна, возвращаем его
        if is_stable_at_pressure(P_geom):
            return P_geom
        
        # 5. Иначе ищем минимальное давление, при котором структура становится стабильной
        # Используем метод бисекции для поиска корня
        P_high = P_geom * 100  # Верхняя граница (на два порядка выше)
        
        # Проверяем, что при P_high структура стабильна
        if not is_stable_at_pressure(P_high):
            # Если даже при P_high нестабильна, возвращаем P_high как оценку
            return P_high
        
        try:
            P_crit = bisect(
                lambda P: 1.0 if is_stable_at_pressure(P) else -1.0,
                P_geom, P_high, xtol=0.1 * P_geom, maxiter=50
            )
            return P_crit
        except ValueError:
            return P_high


def check_phonon_stability(positions: np.ndarray,
                           elements: List,
                           energy_function: Callable,
                           state: ThermodynamicState,
                           displacement: float = 0.01) -> bool:
    """
    Проверяет динамическую стабильность структуры путём анализа фононного спектра.
    
    Args:
        positions: (N, 3) массив координат атомов
        elements: список словарей с данными элементов (нужен для energy_function)
        energy_function: функция, возвращающая энергию системы E(positions)
        state: термодинамическое состояние (T, P)
        displacement: величина смещения для численного дифференцирования (Å)
    
    Returns:
        True, если структура динамически стабильна (нет мнимых частот)
    """
    N = len(positions)
    if N < 2:
        return True  # Одиночный атом всегда "стабилен"
    
    # 1. Строим гессиан (матрицу силовых констант) численным дифференцированием
    hessian = np.zeros((3*N, 3*N))
    
    # Базовая энергия
    E0 = energy_function(positions, elements, state)
    
    # Шаг смещения
    delta = displacement
    
    for i in range(N):
        for alpha in range(3):  # x, y, z
            idx = 3*i + alpha
            
            # Смещение вперёд
            pos_forward = positions.copy()
            pos_forward[i, alpha] += delta
            E_forward = energy_function(pos_forward, elements, state)
            
            # Смещение назад
            pos_backward = positions.copy()
            pos_backward[i, alpha] -= delta
            E_backward = energy_function(pos_backward, elements, state)
            
            # Диагональный элемент гессиана (вторая производная)
            hessian[idx, idx] = (E_forward - 2*E0 + E_backward) / (delta**2)
            
            # Смешанные производные
            for j in range(i, N):
                for beta in range(3):
                    if i == j and beta <= alpha:
                        continue
                    jdx = 3*j + beta
                    
                    # Смещение обоих атомов
                    pos_pp = positions.copy()
                    pos_pp[i, alpha] += delta
                    pos_pp[j, beta] += delta
                    E_pp = energy_function(pos_pp, elements, state)
                    
                    pos_pm = positions.copy()
                    pos_pm[i, alpha] += delta
                    pos_pm[j, beta] -= delta
                    E_pm = energy_function(pos_pm, elements, state)
                    
                    pos_mp = positions.copy()
                    pos_mp[i, alpha] -= delta
                    pos_mp[j, beta] += delta
                    E_mp = energy_function(pos_mp, elements, state)
                    
                    pos_mm = positions.copy()
                    pos_mm[i, alpha] -= delta
                    pos_mm[j, beta] -= delta
                    E_mm = energy_function(pos_mm, elements, state)
                    
                    # Смешанная производная
                    hessian[idx, jdx] = (E_pp - E_pm - E_mp + E_mm) / (4 * delta**2)
                    hessian[jdx, idx] = hessian[idx, jdx]
    
    # 2. Приводим гессиан к динамической матрице (делим на массы)
    masses = np.array([elem.get('mass', 1.0) for elem in elements])
    mass_matrix = np.zeros((3*N, 3*N))
    for i in range(N):
        for alpha in range(3):
            idx = 3*i + alpha
            mass_matrix[idx, idx] = 1.0 / np.sqrt(masses[i])
    
    dynamical_matrix = mass_matrix @ hessian @ mass_matrix
    
    # 3. Находим собственные значения
    eigenvalues = np.linalg.eigvalsh(dynamical_matrix)
    
    # 4. Первые 3 моды — трансляции (должны быть ~0)
    # Проверяем, что нет отрицательных собственных значений (мнимых частот)
    acoustic_threshold = -1e-3  # Допуск для численного шума
    
    for i, ev in enumerate(eigenvalues):
        if i < 3:
            # Трансляционные моды — должны быть около нуля
            if ev < -1e-2:
                return False
        else:
            # Оптические моды — должны быть положительными
            if ev < acoustic_threshold:
                return False
    
    return True


def compute_cluster_energy(positions: np.ndarray, 
                           elements: List[Dict], 
                           state: ThermodynamicState) -> float:
    """
    Вычисляет энергию кластера для использования в check_phonon_stability.
    Это упрощённая версия, использующая только кулоновское и вихревое взаимодействие.
    """
    energy = 0.0
    N = len(positions)
    
    for i in range(N):
        for j in range(i+1, N):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < 1e-6:
                continue
            
            # Заряды
            q1 = elements[i].get('Z', 1)
            q2 = elements[j].get('Z', 1)
            
            # Кулоновское отталкивание
            E_coulomb = q1 * q2 / dist
            
            # Вихревое притяжение (упрощённо)
            sym1 = elements[i].get('symmetry_group', 'C∞v')
            sym2 = elements[j].get('symmetry_group', 'C∞v')
            sym_compat = 1.0 if sym1 == sym2 else 0.5
            
            n1 = elements[i].get('vortex_number', 1)
            n2 = elements[j].get('vortex_number', 1)
            E_vortex = -sym_compat * n1 * n2 / (dist**2)
            
            # Термодинамические поправки
            f_T = state.temperature_factor
            f_P = state.pressure_factor
            
            energy += (E_coulomb + E_vortex) * f_T * f_P
    
    return energy