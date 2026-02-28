#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест формулы Липсика для реальных структур.
Сравниваем идеальный кристалл (только энергия) и реальный (с учётом энтропии, окон, памяти).
Модельный пример: осаждение меди в разных условиях.
"""
import numpy as np
import matplotlib.pyplot as plt

# Константы (в условных единицах)
k_B = 1.0  # постоянная Больцмана (нормирована)

def energy_ideal(config):
    """
    Энергия идеальной структуры.
    Для простоты: чем ближе к идеальной решётке, тем меньше энергия.
    config: параметр порядка (0 = идеальный кристалл, 1 = полный хаос)
    """
    return config**2  # минимум при config=0

def entropy(config):
    """
    Энтропийный вклад.
    Чем больше хаос, тем больше энтропия.
    """
    return -k_B * (config * np.log(config + 1e-10) + (1 - config) * np.log(1 - config + 1e-10))

def window_function(config, T, T_open, T_close):
    """
    Функция окна: 1 если условия внутри окна, иначе 0.
    Здесь окно по температуре.
    """
    if T_open <= T <= T_close:
        return 1.0
    else:
        return 0.0

def lifetime(config, T):
    """
    Характерное время жизни структуры.
    Зависит от температуры и степени упорядоченности.
    """
    # Чем ближе к идеалу и чем ниже T, тем дольше живёт
    return np.exp(-config / T)  # упрощённо

def history_term(config, prev_config):
    """
    Память материала: вклад от предыдущего состояния.
    """
    return 0.1 * abs(config - prev_config)  # чем больше изменилось, тем больше "память"

def lipzik_fitness(config, T, T_open, T_close, prev_config, alpha=0.1, beta=0.05, gamma=0.01):
    """
    Полная формула Липсика.
    F = E + α·S + β·W·τ + γ·H
    """
    E = energy_ideal(config)
    S = entropy(config)
    W = window_function(config, T, T_open, T_close)
    tau = lifetime(config, T)
    H = history_term(config, prev_config)
    
    F = E + alpha * S + beta * W * tau + gamma * H
    return F, E, S, W, tau, H

# ----------------------------------------------------------------------
# Тест: сравниваем идеальный рост и реальный при разных температурах
# ----------------------------------------------------------------------
def run_test():
    # Параметры окна (температура, при которой возможен идеальный рост)
    T_open = 0.3
    T_close = 0.7
    
    # Диапазон температур
    T_values = np.linspace(0.05, 1.0, 100)  # увеличенное разрешение для хвостика
    
    # Для каждого T ищем конфигурацию, минимизирующую F
    results = []
    prev_config = 0.5  # начальное состояние (некое среднее)
    
    for T in T_values:
        best_config = None
        best_F = np.inf
        best_terms = None
        
        # Перебираем возможные конфигурации (config от 0 до 1)
        for config in np.linspace(0, 1, 200):  # увеличенное разрешение
            F, E, S, W, tau, H = lipzik_fitness(config, T, T_open, T_close, prev_config)
            if F < best_F:
                best_F = F
                best_config = config
                best_terms = (E, S, W, tau, H)
        
        results.append({
            'T': T,
            'config': best_config,
            'F': best_F,
            'E': best_terms[0],
            'S': best_terms[1],
            'W': best_terms[2],
            'tau': best_terms[3],
            'H': best_terms[4]
        })
        
        # Обновляем историю для следующего шага
        prev_config = best_config
    
    return results

def plot_results(results):
    # Визуализация
    T_vals = [r['T'] for r in results]
    config_vals = [r['config'] for r in results]
    F_vals = [r['F'] for r in results]
    E_vals = [r['E'] for r in results]
    S_vals = [r['S'] for r in results]
    
    plt.figure(figsize=(12, 10))
    
    plt.subplot(2, 3, 1)
    plt.plot(T_vals, config_vals, 'b-', linewidth=2)
    plt.axvspan(0.3, 0.7, alpha=0.2, color='green', label='окно идеального роста')
    plt.xlabel('Температура (усл. ед.)')
    plt.ylabel('Оптимальная конфигурация config')
    plt.title('Что выгоднее: идеальный кристалл (0) или хаос (1)')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(2, 3, 2)
    plt.plot(T_vals, F_vals, 'r-', label='F (полная)')
    plt.plot(T_vals, E_vals, 'g--', label='E (энергия)')
    plt.plot(T_vals, S_vals, 'm--', label='α·S (энтропия)')
    plt.xlabel('Температура')
    plt.ylabel('Вклад в F')
    plt.title('Составляющие формулы Липсика')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(2, 3, 3)
    plt.plot(T_vals, [r['W'] for r in results], 'c-', label='W (окно)')
    plt.plot(T_vals, [r['tau'] for r in results], 'y-', label='τ (время жизни)')
    plt.xlabel('Температура')
    plt.ylabel('W, τ')
    plt.title('Окно и время жизни')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(2, 3, 4)
    plt.plot(T_vals, [r['H'] for r in results], 'k-', label='H (история)')
    plt.xlabel('Температура')
    plt.ylabel('H')
    plt.title('Память материала')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(2, 3, 5)
    # Фокус на низкие температуры (хвостик)
    T_low = [t for t in T_vals if t < 0.4]
    config_low = [r['config'] for r in results if r['T'] < 0.4]
    
    plt.plot(T_low, config_low, 'b-', linewidth=2, label='config')
    plt.xlabel('Температура (низкие)')
    plt.ylabel('config')
    plt.title('Хвостик: область низких температур')
    plt.grid(True)
    plt.legend()
    
    plt.subplot(2, 3, 6)
    # Дополнительный график для наглядности
    plt.plot(T_vals, config_vals, 'b-', linewidth=1, alpha=0.5, label='config')
    plt.fill_between(T_vals, 0, config_vals, where=[(t<0.3 or t>0.7) for t in T_vals], 
                     color='gray', alpha=0.3, label='вне окна')
    plt.xlabel('Температура')
    plt.ylabel('config')
    plt.title('Области стабильности')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('lipzik_formula_test.png', dpi=150)
    plt.show()
    
    print("\nТест формулы Липсика завершён. График сохранён в lipzik_formula_test.png")

if __name__ == "__main__":
    results = run_test()
    plot_results(results)