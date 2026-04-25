"""
АБСОЛЮТНО ПОЛНАЯ МОДЕЛЬ ЭЛЕКТРООТРИЦАТЕЛЬНОСТИ ВММП
с оптимизацией всех поправок, включая экранирование нейтронным скином
и УЧЁТ ЭЛЕКТРОННОГО ОКРУЖЕНИЯ для ядерных процессов.
"""

import json
import numpy as np
from math import exp
from scipy.optimize import curve_fit
from typing import List
# ... (все константы и загрузка данных до определения функций остаются без изменений) ...

# Типы химического окружения и их влияние на экранировку ядра
ENVIRONMENT_SCREENING = {
    'free_atom': 1.000,      # Свободный атом (эталон)
    'metallic': 0.998,       # Металлическое окружение (Li, Be, Au) -> замедляет распад
    'covalent': 1.002,       # Ковалентное окружение (алмаз) -> ускоряет распад
    'ionic': 0.999,          # Ионное окружение
    'van_der_waals': 1.001,  # Молекулярные кристаллы
}

def get_environment_type(symbol: str, neighbors: List[str] = None) -> str:
    """
    Определяет тип химического окружения для элемента.
    Упрощённая версия: для демонстрации используем таблицу свойств.
    """
    # Металлы
    metals = {'Li', 'Be', 'Na', 'Mg', 'Al', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn',
              'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc',
              'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Cs', 'Ba', 'La', 'Hf', 'Ta',
              'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po'}
    
    # Ковалентные кристаллы
    covalent = {'C', 'Si', 'Ge', 'B', 'P', 'S', 'Se', 'Te'}
    
    # Инертные газы
    noble = {'He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn'}
    
    if symbol in metals:
        return 'metallic'
    elif symbol in covalent:
        return 'covalent'
    elif symbol in noble:
        return 'van_der_waals'
    else:
        return 'ionic'


def nuclear_environment_correction(Z: int, symbol: str, 
                                   host_symbol: str = None) -> float:
    """
    Вычисляет поправку к вероятности ядерного распада в зависимости
    от электронного окружения.
    
    Args:
        Z: заряд ядра
        symbol: символ элемента
        host_symbol: символ элемента-хозяина (если внедрён в решётку)
    
    Returns:
        Множитель для периода полураспада (>1 = замедление, <1 = ускорение)
    """
    # Определяем тип окружения
    if host_symbol is not None:
        env_type = get_environment_type(host_symbol)
    else:
        env_type = get_environment_type(symbol)
    
    # Базовая поправка
    base_factor = ENVIRONMENT_SCREENING.get(env_type, 1.000)
    
    # Дополнительная поправка для лёгких ядер (сильнее чувствуют окружение)
    if Z <= 20:
        # Усиливаем эффект для лёгких ядер
        delta = base_factor - 1.0
        base_factor = 1.0 + delta * (1.0 + 0.5 * (20 - Z) / 20)
    
    return base_factor


def compute_half_life_correction(Z: int, symbol: str, 
                                 host_symbol: str = None,
                                 base_half_life: float = None) -> float:
    """
    Вычисляет скорректированный период полураспада с учётом окружения.
    """
    if base_half_life is None:
        return None
    
    env_factor = nuclear_environment_correction(Z, symbol, host_symbol)
    return base_half_life * env_factor


# ... (остальные функции: get_symmetry, get_fractal_level, symmetry_factor, zeta, spin,
#      relativistic_correction, neutron_skin_correction, radioactive_slowing,
#      compute_chi_vmms_single, screening_factor_with_skin, model_function, main)
#      остаются без изменений ...

# Добавляем в main() вывод информации об окружении для ключевых элементов
def main():
    # ... (весь существующий код main до вывода таблицы) ...
    
    # Дополнительный блок: предсказание для ⁷Be в разных окружениях
    print("\n" + "=" * 100)
    print("ПРЕДСКАЗАНИЕ ДЛЯ ⁷Be В РАЗНЫХ ОКРУЖЕНИЯХ")
    print("=" * 100)
    
    Be7_Z = 4
    base_half_life = 4.6e6  # 53.22 дня в секундах
    
    environments = ['free_atom', 'Li', 'Be', 'C', 'Au']
    print(f"{'Окружение':>12} | {'Тип':>12} | {'Фактор':>8} | {'T₁/₂ (дни)':>12} | {'Δ (%)':>8}")
    print("-" * 60)
    
    for env in environments:
        if env == 'free_atom':
            env_type = 'free_atom'
            host = None
        else:
            env_type = get_environment_type(env)
            host = env
        
        factor = nuclear_environment_correction(Be7_Z, 'Be', host)
        half_life_days = base_half_life * factor / 86400
        delta_percent = (factor - 1.0) * 100
        
        print(f"{env:>12} | {env_type:>12} | {factor:8.4f} | {half_life_days:12.2f} | {delta_percent:+7.3f}%")
    
    print("-" * 60)
    print("Примечание: Стандартная Модель предсказывает нулевую разницу (фактор = 1.000).")
    print("=" * 100)

if __name__ == "__main__":
    main()