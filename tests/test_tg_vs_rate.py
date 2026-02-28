#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест 1: Зависимость температуры стеклования Tg от скорости охлаждения.
Главный результат: чем выше скорость, тем выше Tg.
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

def simulate_cooling(cooling_rates, T_start=1.0, T_end=0.0, n_steps=200):
    results = []
    
    for rate in cooling_rates:
        T_values = np.linspace(T_start, T_end, n_steps)
        config = 0.3
        Tg_found = T_end
        glass_transition_detected = False
        
        for i, T in enumerate(T_values):
            config, W, tau = lipzik_glass(T, rate, config)
            
            if W == 0 and not glass_transition_detected and i > 0:
                T_prev = T_values[i-1]
                Tg_found = (T_prev + T) / 2
                glass_transition_detected = True
        
        if not glass_transition_detected:
            Tg_found = T_end
        
        results.append({'rate': rate, 'Tg': Tg_found})
    
    return results

def plot_results(results):
    plt.figure(figsize=(8, 6))
    
    rates = [r['rate'] for r in results]
    Tgs = [r['Tg'] for r in results]
    
    plt.semilogx(rates, Tgs, 'ro-', linewidth=2, markersize=8)
    plt.xlabel('Скорость охлаждения (лог. шкала)')
    plt.ylabel('Tg (температура стеклования)')
    plt.title('Зависимость Tg от скорости охлаждения')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('tg_vs_rate.png', dpi=150)
    plt.show()
    
    print("\n=== Tg vs cooling rate ===")
    print(f"{'Скорость':>12} {'Tg':>8}")
    print("-" * 25)
    for r in results:
        print(f"{r['rate']:12.4f} {r['Tg']:8.3f}")

if __name__ == "__main__":
    cooling_rates = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0]
    results = simulate_cooling(cooling_rates)
    plot_results(results)