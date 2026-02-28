#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест 2: Динамика стеклования — эволюция структуры, окно W, время релаксации.
Для одной скорости охлаждения (или нескольких, для сравнения).
"""
import numpy as np
import matplotlib.pyplot as plt

# Константы
k_B = 1.0

def energy_ideal(config):
    return config**2

def entropy(config):
    if config <= 0 or config >= 1:
        return 0
    return -k_B * (config * np.log(config) + (1-config) * np.log(1-config))

def relaxation_time(T, Tg0=0.5, C1=10, C2=50, T0=0.01):
    if T <= T0:
        return np.inf
    if T >= Tg0 + C2:
        return 1.0
    log_shift = -C1 * (T - Tg0) / (C2 + T - Tg0)
    tau_vlf = np.exp(log_shift)
    freeze_factor = np.exp(10 * (Tg0/T - 1))
    return tau_vlf * freeze_factor

def window_glass(T, cooling_rate, tau):
    t_exp = 1.0 / cooling_rate if cooling_rate > 0 else 1e6
    return 1.0 if tau < t_exp else 0.0

def memory_term(prev_config, config, decay=0.9):
    return decay * prev_config + (1-decay) * config

def lipzik_glass(T, cooling_rate, prev_config, alpha=0.1, gamma=0.1):
    best_config = None
    best_F = np.inf
    
    for config in np.linspace(0, 1, 100):
        E = energy_ideal(config)
        S = entropy(config)
        H = memory_term(prev_config, config)
        F = E + alpha * S + gamma * H
        
        if F < best_F:
            best_F = F
            best_config = config
    
    tau = relaxation_time(T)
    W = window_glass(T, cooling_rate, tau)
    
    return best_config, W, tau

def simulate_one_rate(rate, T_start=1.0, T_end=0.0, n_steps=200):
    T_values = np.linspace(T_start, T_end, n_steps)
    config = 0.3
    
    config_history = []
    W_history = []
    tau_history = []
    
    for T in T_values:
        config, W, tau = lipzik_glass(T, rate, config)
        config_history.append(config)
        W_history.append(W)
        tau_history.append(tau)
    
    return {
        'T_values': T_values,
        'config': config_history,
        'W': W_history,
        'tau': tau_history,
        'rate': rate
    }

def plot_dynamics(results, rates_to_plot=None):
    """Строит динамику для выбранных скоростей"""
    if rates_to_plot is None:
        rates_to_plot = [0.001, 0.01, 0.1, 1.0]
    
    # Отбираем нужные результаты
    plot_data = [r for r in results if r['rate'] in rates_to_plot]
    
    plt.figure(figsize=(12, 8))
    
    # График 1: Эволюция config
    plt.subplot(2, 2, 1)
    for data in plot_data:
        plt.plot(data['T_values'], data['config'], 
                label=f'rate={data["rate"]:.3f}')
    plt.xlabel('Температура')
    plt.ylabel('Параметр порядка config')
    plt.title('Структура при охлаждении')
    plt.legend()
    plt.grid(True)
    
    # График 2: Окно стеклования
    plt.subplot(2, 2, 2)
    for data in plot_data:
        plt.plot(data['T_values'], data['W'], 
                label=f'rate={data["rate"]:.3f}')
    plt.xlabel('Температура')
    plt.ylabel('Окно W')
    plt.title('Переход жидкость (1) → стекло (0)')
    plt.legend()
    plt.grid(True)
    
    # График 3: Время релаксации
    plt.subplot(2, 2, 3)
    T_range = np.linspace(0.05, 1.0, 100)
    tau_vals = [relaxation_time(T) for T in T_range]
    plt.plot(T_range, tau_vals, 'b-', linewidth=2, label='τ(T)')
    
    for rate in rates_to_plot:
        t_exp = 1.0/rate
        plt.axhline(y=t_exp, linestyle='--', color='gray', alpha=0.5)
        plt.text(0.6, t_exp*1.5, f'rate={rate}', fontsize=8)
    
    plt.yscale('log')
    plt.xlabel('Температура')
    plt.ylabel('Время релаксации τ')
    plt.title('Условие стеклования: τ = t_exp')
    plt.grid(True)
    plt.legend()
    
    # График 4: Финальная структура при разных скоростях
    plt.subplot(2, 2, 4)
    final_configs = [data['config'][-1] for data in plot_data]
    rates_plot = [data['rate'] for data in plot_data]
    plt.semilogx(rates_plot, final_configs, 'go-', linewidth=2, markersize=8)
    plt.xlabel('Скорость охлаждения')
    plt.ylabel('config при T→0')
    plt.title('Конечная структура')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('glass_dynamics.png', dpi=150)
    plt.show()

if __name__ == "__main__":
    # Моделируем для всех скоростей
    cooling_rates = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0]
    results = [simulate_one_rate(rate) for rate in cooling_rates]
    
    # Строим динамику для избранных
    plot_dynamics(results, rates_to_plot=[0.001, 0.01, 0.1, 1.0])