#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест формулы Липсика для стеклования.
Моделирует переход жидкость-стекло при разных скоростях охлаждения.
"""
import numpy as np
import matplotlib.pyplot as plt

# Константы
k_B = 1.0

def energy_ideal(config):
    """Энергия: минимум при идеальном порядке (config=0)"""
    return config**2

def entropy(config):
    """Конфигурационная энтропия"""
    if config <= 0 or config >= 1:
        return 0
    return -k_B * (config * np.log(config) + (1-config) * np.log(1-config))

def relaxation_time(T, Tg0=0.5, C1=10, C2=50, T0=0.01):
    """
    Время релаксации с учётом замерзания при T → 0.
    """
    if T <= T0:
        return np.inf
    
    if T >= Tg0 + C2:
        return 1.0  # жидкость
    
    # ВЛФ
    log_shift = -C1 * (T - Tg0) / (C2 + T - Tg0)
    tau_vlf = np.exp(log_shift)
    
    # При низких T добавляем аррениусовский рост
    freeze_factor = np.exp(10 * (Tg0/T - 1))
    return tau_vlf * freeze_factor

def window_glass(T, cooling_rate, tau):
    """
    Окно для стеклования.
    Открыто (1): жидкость (τ < t_exp)
    Закрыто (0): стекло (τ ≥ t_exp)
    """
    t_exp = 1.0 / cooling_rate if cooling_rate > 0 else 1e6
    return 1.0 if tau < t_exp else 0.0

def memory_term(prev_config, config, decay=0.9):
    """Память: предыдущее состояние влияет на текущее"""
    return decay * prev_config + (1-decay) * config

def lipzik_glass(T, cooling_rate, prev_config, alpha=0.1, gamma=0.1):
    """
    Формула Липсика для стеклования.
    F = E + α·S + γ·H
    """
    # Ищем config, минимизирующий F
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
    
    # Оцениваем время релаксации для этой конфигурации
    tau = relaxation_time(T)
    W = window_glass(T, cooling_rate, tau)
    
    return best_config, W, tau

def simulate_cooling(cooling_rates, T_start=1.0, T_end=0.0, n_steps=200):
    """
    Моделирует охлаждение с разными скоростями.
    Возвращает Tg для каждой скорости.
    """
    results = []
    
    for rate in cooling_rates:
        T_values = np.linspace(T_start, T_end, n_steps)
        config = 0.3  # начальное состояние (жидкость)
        Tg_found = T_end
        glass_transition_detected = False
        
        config_history = []
        W_history = []
        
        for i, T in enumerate(T_values):
            config, W, tau = lipzik_glass(T, rate, config)
            config_history.append(config)
            W_history.append(W)
            
            # Фиксируем Tg как температуру, где окно закрылось (W=0)
            if W == 0 and not glass_transition_detected and i > 0:
                T_prev = T_values[i-1]
                Tg_found = (T_prev + T) / 2
                glass_transition_detected = True
        
        # Если стеклование не обнаружено, берём минимальную T
        if not glass_transition_detected:
            Tg_found = T_end
        
        results.append({
            'rate': rate,
            'Tg': Tg_found,
            'config': config_history,
            'W': W_history,
            'T_values': T_values
        })
    
    return results

def plot_results(results):
    """Строит графики зависимости Tg от скорости охлаждения"""
    plt.figure(figsize=(12, 10))
    
    # График 1: Зависимость Tg от скорости охлаждения
    plt.subplot(2, 2, 1)
    rates = [r['rate'] for r in results]
    Tgs = [r['Tg'] for r in results]
    plt.semilogx(rates, Tgs, 'ro-', linewidth=2, markersize=8)
    plt.xlabel('Скорость охлаждения (лог. шкала)')
    plt.ylabel('Tg (температура стеклования)')
    plt.title('Зависимость Tg от скорости охлаждения')
    plt.grid(True)
    
    # График 2: Эволюция config при разных скоростях
    plt.subplot(2, 2, 2)
    for i, r in enumerate(results):
        if i % 2 == 0:
            plt.plot(r['T_values'], r['config'], label=f'rate={r["rate"]:.3f}')
    plt.xlabel('Температура')
    plt.ylabel('Параметр порядка config')
    plt.title('Эволюция структуры при охлаждении')
    plt.legend()
    plt.grid(True)
    
    # График 3: Окно стеклования
    plt.subplot(2, 2, 3)
    for i, r in enumerate(results):
        if i % 2 == 0:
            plt.plot(r['T_values'], r['W'], label=f'rate={r["rate"]:.3f}')
    plt.xlabel('Температура')
    plt.ylabel('Окно W (1 — жидкость, 0 — стекло)')
    plt.title('Переход жидкость-стекло')
    plt.legend()
    plt.grid(True)
    
    # График 4: Время релаксации
    plt.subplot(2, 2, 4)
    T_range = np.linspace(0.05, 1.0, 100)
    tau_vals = [relaxation_time(T) for T in T_range]
    plt.plot(T_range, tau_vals, 'b-', linewidth=2, label='τ(T)')
    
    for rate in [0.001, 0.01, 0.1, 1.0]:
        t_exp = 1.0/rate
        plt.axhline(y=t_exp, linestyle='--', color='gray', alpha=0.5)
        plt.text(0.6, t_exp*1.5, f'rate={rate}', fontsize=8)
    
    plt.yscale('log')
    plt.xlabel('Температура')
    plt.ylabel('Время релаксации τ (лог.)')
    plt.title('τ(T) и условие стеклования')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('glass_transition_test.png', dpi=150)
    plt.show()
    
    # Вывод численных результатов
    print("\n=== РЕЗУЛЬТАТЫ СТЕКЛОВАНИЯ ===")
    print(f"{'Скорость':>12} {'Tg':>8}")
    print("-" * 25)
    for r in results:
        print(f"{r['rate']:12.4f} {r['Tg']:8.3f}")

if __name__ == "__main__":
    cooling_rates = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0]
    results = simulate_cooling(cooling_rates)
    plot_results(results)