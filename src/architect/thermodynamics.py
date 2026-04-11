"""
Термодинамический модуль для SpectraVortex.
Интеграция температуры (T) и давления (P) в расчёты поля H.

Основан на формулах из файлов ВММП:
- ВММП_часть2 (1)2грав.doc
- вихревая модель электроотрицательности.doc
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List

# Фундаментальные константы
k_B = 8.617333262145e-5  # eV/K
k_B_SI = 1.380649e-23     # J/K
hbar = 6.582119569e-16    # eV·s
m_e = 0.51099895e6        # eV/c²
c = 2.99792458e8          # m/s

@dataclass
class ThermodynamicState:
    """Термодинамическое состояние системы"""
    temperature: float  # K
    pressure: float     # GPa
    
    # Параметры конденсата (из ВММП)
    T_lambda: float = 450.0     # K (температура "фазового перехода")
    K0: float = 200.0           # GPa (модуль сжимаемости)
    alpha_T: float = 0.15       # коэффициент температурного расширения
    beta_P: float = 0.005       # коэффициент барического сжатия
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Проверка физичности параметров"""
        if self.temperature < 0:
            raise ValueError("Temperature must be >= 0")
        if self.pressure < 0:
            raise ValueError("Pressure must be >= 0")
    
    @property
    def thermal_energy(self) -> float:
        """Тепловая энергия в eV"""
        return k_B * self.temperature
    
    @property
    def temperature_factor(self) -> float:
        """
        Температурный фактор для энергии взаимодействия.
        Из ВММП: f_T = 1 - α·(T/T_λ)² при T < T_λ, иначе 0
        """
        if self.temperature < self.T_lambda:
            return 1.0 - self.alpha_T * (self.temperature / self.T_lambda)**2
        else:
            # Выше T_λ - экспоненциальное падение (фазовый переход конденсата)
            return np.exp(-(self.temperature - self.T_lambda) / self.T_lambda)
    
    @property
    def pressure_factor(self) -> float:
        """
        Барический фактор для энергии взаимодействия.
        Из ВММП: f_P = 1 + P/K0
        """
        return 1.0 + self.pressure / self.K0
    
    @property
    def volume_factor(self) -> float:
        """
        Фактор изменения объёма под давлением.
        Уравнение состояния: V(P) = V0 / (1 + P/K0)^(1/n)
        """
        n = 3.0  # показатель политропы для конденсата
        return (1.0 + self.pressure / self.K0) ** (-1.0 / n)
    
    def get_equilibrium_distance(self, d0: float) -> float:
        """
        Равновесное расстояние при данных T и P.
        d(T,P) = d0 * (1 + β_T·T) * (1 - β_P·P)
        """
        beta_T = 1.2e-5  # 1/K (коэффициент теплового расширения)
        beta_P = 0.005   # 1/GPa (сжимаемость)
        
        d_T = d0 * (1.0 + beta_T * self.temperature)
        d_P = d_T * (1.0 - beta_P * self.pressure)
        
        return d_P
    
    def get_critical_pressure(self, r0: float) -> float:
        """
        Критическое давление синтеза интерметаллида.
        Из ВММП: P_crit = ħ² / (m_e · r0⁵)
        
        Args:
            r0: характерное расстояние (Å)
        Returns:
            P_crit в GPa
        """
        r0_m = r0 * 1e-10  # Å → m
        
        # ħ² / m_e в единицах СИ
        hbar_si = 1.0545718e-34  # J·s
        m_e_si = 9.1093837e-31   # kg
        
        P_crit_si = hbar_si**2 / (m_e_si * r0_m**5)
        P_crit_GPa = P_crit_si * 1e-9  # Pa → GPa
        
        return P_crit_GPa


class ThermodynamicCalculator:
    """
    Калькулятор термодинамических свойств материалов.
    """
    
    def __init__(self, state: ThermodynamicState):
        self.state = state
    
    def formation_enthalpy(self, 
                          E_vortex: float,
                          delta_V: float = 0.1) -> float:
        """
        Энтальпия образования соединения при данных T и P.
        ΔH_f(T,P) = ΔH_f(0) + P·ΔV + ∫C_p dT
        
        Args:
            E_vortex: энергия вихревого взаимодействия (eV)
            delta_V: изменение объёма (в долях от V0)
        """
        # Базовая энтальпия (из энергии вихря)
        H0 = -abs(E_vortex)
        
        # Барическая поправка: P·ΔV
        # P в GPa, переводим в eV/Å³: 1 GPa = 0.006242 eV/Å³
        P_eV_per_A3 = self.state.pressure * 0.006242
        V0 = 10.0  # характерный объём Å³
        H_pressure = P_eV_per_A3 * V0 * delta_V
        
        # Температурная поправка: ∫C_p dT
        # Для твёрдых тел C_p ≈ 3k_B на атом
        C_p = 3 * k_B  # eV/K
        H_thermal = C_p * self.state.temperature
        
        return H0 + H_pressure + H_thermal
    
    def stability_score(self, 
                       E_vortex: float,
                       symmetry_compat: float,
                       freq_resonance: float) -> float:
        """
        Оценка стабильности соединения (0-1).
        
        Args:
            E_vortex: энергия вихревого взаимодействия (eV)
            symmetry_compat: совместимость симметрий (0-1)
            freq_resonance: резонанс частот (0-1)
        """
        # Энергетический фактор (чем ниже энергия, тем выше стабильность)
        if E_vortex < 0:
            energy_factor = np.exp(-abs(E_vortex) / self.state.thermal_energy)
        else:
            energy_factor = 0.0
        
        # Температурная дестабилизация
        T_factor = self.state.temperature_factor
        
        # Барическая стабилизация (давление способствует образованию связей)
        P_factor = 1.0 + 0.1 * self.state.pressure
        
        stability = (energy_factor * 
                    symmetry_compat * 
                    freq_resonance * 
                    T_factor * 
                    P_factor)
        
        return min(stability, 1.0)
    
    def is_stable(self, 
                 E_vortex: float,
                 symmetry_compat: float,
                 freq_resonance: float,
                 threshold: float = 0.5) -> bool:
        """Проверка стабильности соединения"""
        return self.stability_score(E_vortex, symmetry_compat, freq_resonance) > threshold
    
    def half_life_temperature_correction(self, 
                                        T_half_300: float,
                                        Z: int) -> float:
        """
        Температурная зависимость периода полураспада.
        Из ВММП: T½(T) = T½(300) · (300/T)^(5/2)
        
        Args:
            T_half_300: период полураспада при 300 K (сек)
            Z: заряд ядра
        Returns:
            Период полураспада при текущей температуре
        """
        if T_half_300 is None or T_half_300 == float('inf'):
            return float('inf')
        
        # Базовый показатель степени
        exponent = 2.5
        
        # Поправка для тяжёлых ядер
        if Z > 80:
            exponent *= (1.0 + 0.01 * (Z - 80))
        
        T_corrected = T_half_300 * (300.0 / self.state.temperature) ** exponent
        
        # Экспоненциальный рост выше 1500 K (фазовый переход конденсата)
        if self.state.temperature > 1500.0:
            T_corrected *= np.exp((self.state.temperature - 1500.0) / 200.0)
        
        return T_corrected
    
    def decay_rate(self, T_half_300: float, Z: int) -> float:
        """Скорость распада при текущей температуре (1/сек)"""
        T_half = self.half_life_temperature_correction(T_half_300, Z)
        if T_half == float('inf'):
            return 0.0
        return np.log(2) / T_half
    
    def melting_point_estimate(self, 
                              formation_enthalpy: float,
                              entropy_fusion: float = 10.0) -> float:
        """
        Оценка температуры плавления по энтальпии образования.
        T_m ≈ |ΔH_f| / ΔS_fus
        
        Args:
            formation_enthalpy: энтальпия образования (eV)
            entropy_fusion: энтропия плавления (J/mol·K), по умолчанию 10
        Returns:
            T_m в K
        """
        # eV → J/mol
        H_f_J_per_mol = abs(formation_enthalpy) * 96485.3
        
        return H_f_J_per_mol / entropy_fusion
    
    def predict_synthesis_conditions(self,
                                    elements_data: List[Dict],
                                    bonds: List[Dict]) -> List[Dict]:
        """
        Предсказание оптимальных условий синтеза для связей.
        
        Args:
            elements_data: список словарей с данными элементов
            bonds: список обнаруженных связей
        Returns:
            Список связей с добавленными условиями синтеза
        """
        results = []
        
        for bond in bonds:
            # Получаем данные элементов
            elem1 = next(e for e in elements_data if e['symbol'] == bond['elements'][0])
            elem2 = next(e for e in elements_data if e['symbol'] == bond['elements'][1])
            
            # Характерное расстояние
            r0 = bond['distance']
            
            # Критическое давление
            P_crit = self.state.get_critical_pressure(r0)
            
            # Оптимальная температура (эмпирическое правило)
            T_opt = 0.6 * self.melting_point_estimate(
                abs(elem1.get('electronegativity', 1.0) - elem2.get('electronegativity', 1.0)) * 0.5
            )
            
            # Стабильность при различных условиях
            stability_scores = {}
            for T in [300, 500, 800, 1000, 1200, 1500]:
                for P in [0.1, 1.0, 2.0, 5.0, 10.0]:
                    test_state = ThermodynamicState(T, P)
                    calc = ThermodynamicCalculator(test_state)
                    
                    # Упрощённая оценка энергии связи
                    E_bond = -abs(elem1.get('electronegativity', 1.0) - 
                                  elem2.get('electronegativity', 1.0)) * 0.5
                    
                    score = calc.stability_score(E_bond, 0.8, 0.9)
                    stability_scores[(T, P)] = score
            
            # Находим оптимальные условия
            best_conditions = max(stability_scores, key=stability_scores.get)
            
            results.append({
                **bond,
                'synthesis_conditions': {
                    'T_opt_K': float(best_conditions[0]),
                    'P_opt_GPa': float(best_conditions[1]),
                    'P_crit_GPa': float(P_crit),
                    'stability_score': float(stability_scores[best_conditions])
                },
                'thermodynamics': {
                    'formation_enthalpy_eV': float(self.formation_enthalpy(
                        -abs(elem1.get('electronegativity', 1.0) - 
                             elem2.get('electronegativity', 1.0)) * 0.5
                    )),
                    'melting_point_estimate_K': float(T_opt / 0.6)
                }
            })
        
        return results


class PhaseDiagramCalculator:
    """
    Построение фазовых диаграмм P-T.
    """
    
    def __init__(self, base_state: ThermodynamicState = None):
        self.base_state = base_state or ThermodynamicState(300, 0.1)
    
    def calculate_phase_boundary(self,
                                phase1_stability: callable,
                                phase2_stability: callable,
                                T_range: Tuple[float, float] = (300, 2000),
                                P_range: Tuple[float, float] = (0.1, 20.0),
                                resolution: int = 50) -> Dict:
        """
        Расчёт границы фазового перехода.
        
        Args:
            phase1_stability: функция stability(T, P) для фазы 1
            phase2_stability: функция stability(T, P) для фазы 2
            T_range: диапазон температур (K)
            P_range: диапазон давлений (GPa)
            resolution: разрешение сетки
        """
        T = np.linspace(T_range[0], T_range[1], resolution)
        P = np.linspace(P_range[0], P_range[1], resolution)
        
        diagram = np.zeros((resolution, resolution))
        
        for i, t in enumerate(T):
            for j, p in enumerate(P):
                s1 = phase1_stability(t, p)
                s2 = phase2_stability(t, p)
                
                # 0 = фаза 1 стабильнее, 1 = фаза 2 стабильнее
                diagram[i, j] = 1 if s2 > s1 else 0
        
        # Находим границу (где s1 ≈ s2)
        boundary = []
        for i in range(resolution - 1):
            for j in range(resolution - 1):
                if diagram[i, j] != diagram[i+1, j] or diagram[i, j] != diagram[i, j+1]:
                    boundary.append((float(T[i]), float(P[j])))
        
        return {
            'T': T.tolist(),
            'P': P.tolist(),
            'diagram': diagram.tolist(),
            'boundary': boundary
        }
    
    def find_triple_point(self,
                         phase1: callable,
                         phase2: callable,
                         phase3: callable,
                         T_range: Tuple[float, float] = (500, 1500),
                         P_range: Tuple[float, float] = (0.1, 10.0)) -> Optional[Tuple[float, float]]:
        """
        Поиск тройной точки (где стабильны все три фазы).
        """
        best_point = None
        min_diff = float('inf')
        
        for T in np.linspace(T_range[0], T_range[1], 100):
            for P in np.linspace(P_range[0], P_range[1], 100):
                s1 = phase1(T, P)
                s2 = phase2(T, P)
                s3 = phase3(T, P)
                
                # Разность стабильностей должна быть минимальна
                diff = abs(s1 - s2) + abs(s2 - s3) + abs(s3 - s1)
                
                if diff < min_diff:
                    min_diff = diff
                    best_point = (float(T), float(P))
        
        return best_point


# Константы для типичных материалов (из ВММП)
MATERIAL_CONSTANTS = {
    'FeAl': {
        'T_melt': 1523,      # K
        'delta_H': -0.52,     # eV
        'structure': 'B2',
        'lattice_constant': 2.895  # Å
    },
    'Ni3Al': {
        'T_melt': 1668,
        'delta_H': -0.41,
        'structure': 'L12',
        'lattice_constant': 3.570
    },
    'TiAl': {
        'T_melt': 1733,
        'delta_H': -0.78,
        'structure': 'L10',
        'lattice_constant': 4.000
    },
    'Fe5Al8': {
        'T_melt': 1520,
        'delta_H': -0.47,
        'structure': 'D82',
        'lattice_constant': 5.780
    }
}


def create_thermodynamic_state(T: float = 300.0, P: float = 0.1) -> ThermodynamicState:
    """Фабрика для создания термодинамического состояния"""
    return ThermodynamicState(temperature=T, pressure=P)


def calculate_stability_at_conditions(elements: List[str], 
                                     T: float, 
                                     P: float,
                                     electronegativities: Dict[str, float] = None) -> float:
    """
    Быстрая оценка стабильности соединения при заданных T и P.
    """
    state = ThermodynamicState(T, P)
    calc = ThermodynamicCalculator(state)
    
    # Упрощённая оценка энергии связи через электроотрицательность
    if electronegativities and len(elements) == 2:
        chi1 = electronegativities.get(elements[0], 1.0)
        chi2 = electronegativities.get(elements[1], 1.0)
        E_bond = -abs(chi1 - chi2) * 0.5
    else:
        E_bond = -0.5  # значение по умолчанию
    
    return calc.stability_score(E_bond, 0.8, 0.9)


# ========== ТЕСТЫ ==========

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ТЕРМОДИНАМИЧЕСКОГО МОДУЛЯ")
    print("=" * 60)
    
    # Тест 1: Создание состояния
    print("\n[1] Создание термодинамического состояния:")
    state = ThermodynamicState(300, 0.1)
    print(f"    T = {state.temperature} K")
    print(f"    P = {state.pressure} GPa")
    print(f"    f_T = {state.temperature_factor:.4f}")
    print(f"    f_P = {state.pressure_factor:.4f}")
    
    # Тест 2: Калькулятор
    print("\n[2] Тест калькулятора:")
    calc = ThermodynamicCalculator(state)
    
    stability = calc.stability_score(-0.5, 0.9, 0.95)
    print(f"    Stability (FeAl @ 300K, 0.1GPa) = {stability:.4f}")
    print(f"    Is stable: {calc.is_stable(-0.5, 0.9, 0.95)}")
    
    # Тест 3: Температурная зависимость периода полураспада
    print("\n[3] Температурная зависимость T½ для ²¹⁰Po:")
    T_half_300 = 1.195e7  # 138.4 дня в секундах
    
    for T in [300, 500, 1000, 1500]:
        state_T = ThermodynamicState(T, 0.1)
        calc_T = ThermodynamicCalculator(state_T)
        T_half = calc_T.half_life_temperature_correction(T_half_300, 84)
        days = T_half / 86400
        print(f"    T = {T:4} K: T½ = {days:.1f} дней")
    
    # Тест 4: Критическое давление
    print("\n[4] Критическое давление синтеза:")
    for material, const in MATERIAL_CONSTANTS.items():
        P_crit = state.get_critical_pressure(const['lattice_constant'])
        print(f"    {material}: a = {const['lattice_constant']} Å → P_crit = {P_crit:.1f} GPa")
    
    # Тест 5: Предсказание условий синтеза
    print("\n[5] Предсказание условий синтеза для FeAl:")
    elements_data = [
        {'symbol': 'Fe', 'electronegativity': 1.83},
        {'symbol': 'Al', 'electronegativity': 1.61}
    ]
    bonds = [{'elements': ['Fe', 'Al'], 'distance': 2.895}]
    
    results = calc.predict_synthesis_conditions(elements_data, bonds)
    for r in results:
        print(f"    {r['elements'][0]}-{r['elements'][1]}:")
        print(f"      T_opt = {r['synthesis_conditions']['T_opt_K']:.0f} K")
        print(f"      P_opt = {r['synthesis_conditions']['P_opt_GPa']:.1f} GPa")
        print(f"      Stability = {r['synthesis_conditions']['stability_score']:.3f}")
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)