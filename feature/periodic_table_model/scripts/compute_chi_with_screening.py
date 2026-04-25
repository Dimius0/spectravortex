"""
Вычисление эффективной электроотрицательности χ_eff из первых принципов ВММП
с учётом экранировки атомным радиусом.
Сравнение с эмпирической шкалой Полинга.
"""

import json
import numpy as np
from math import sqrt, exp

# ========== КОНСТАНТЫ ==========
k = 0.0608
alpha = 0.01
max_neighbor_dist = 5.0

# Калибровочные константы для перехода к шкале Полинга
CHI_0 = 0.5
A = 0.3

# Атомные радиусы (Å)
ATOMIC_RADII = {
    1: 0.53, 2: 0.31, 3: 1.67, 4: 1.12, 5: 0.87, 6: 0.67, 7: 0.56, 8: 0.48, 9: 0.42, 10: 0.38,
    11: 1.90, 12: 1.45, 13: 1.18, 14: 1.11, 15: 0.98, 16: 0.88, 17: 0.79, 18: 0.71,
    19: 2.43, 20: 1.94, 21: 1.84, 22: 1.76, 23: 1.71, 24: 1.66, 25: 1.61, 26: 1.56,
    27: 1.52, 28: 1.49, 29: 1.45, 30: 1.42, 31: 1.36, 32: 1.25, 33: 1.14, 34: 1.03,
    35: 0.94, 36: 0.88, 37: 2.65, 38: 2.19, 39: 2.12, 40: 2.06, 41: 1.98, 42: 1.90,
    43: 1.83, 44: 1.78, 45: 1.73, 46: 1.69, 47: 1.65, 48: 1.61, 49: 1.56, 50: 1.45,
    51: 1.33, 52: 1.23, 53: 1.15, 54: 1.08, 55: 2.98, 56: 2.53, 57: 1.95,
    58: 1.85, 59: 1.82, 60: 1.81, 61: 1.80, 62: 1.79, 63: 2.04, 64: 1.79, 65: 1.77,
    66: 1.75, 67: 1.74, 68: 1.73, 69: 1.72, 70: 1.94, 71: 1.72,
    72: 1.75, 73: 1.70, 74: 1.62, 75: 1.55, 76: 1.49, 77: 1.44, 78: 1.39, 79: 1.46, 80: 1.50,
    81: 1.70, 82: 1.75, 83: 1.60, 84: 1.90, 85: 1.27, 86: 1.20, 87: 3.10, 88: 2.15,
    89: 1.95, 90: 1.80, 91: 1.63, 92: 1.56, 93: 1.55, 94: 1.59, 95: 1.73, 96: 1.74,
    97: 1.70, 98: 1.86, 99: 1.86, 100: 2.00, 101: 2.00, 102: 2.00, 103: 2.00
}

# Эмпирическая шкала Полинга
CHI_PAULING = {
    1: 2.20, 2: 0.00, 3: 0.98, 4: 1.57, 5: 2.04, 6: 2.55, 7: 3.04, 8: 3.44, 9: 3.98, 10: 0.00,
    11: 0.93, 12: 1.31, 13: 1.61, 14: 1.90, 15: 2.19, 16: 2.58, 17: 3.16, 18: 0.00,
    19: 0.82, 20: 1.00, 21: 1.36, 22: 1.54, 23: 1.63, 24: 1.66, 25: 1.55, 26: 1.83,
    27: 1.88, 28: 1.91, 29: 1.90, 30: 1.65, 31: 1.81, 32: 2.01, 33: 2.18, 34: 2.55,
    35: 2.96, 36: 0.00, 37: 0.82, 38: 0.95, 39: 1.22, 40: 1.33, 41: 1.60, 42: 2.16,
    43: 1.90, 44: 2.20, 45: 2.28, 46: 2.20, 47: 1.93, 48: 1.69, 49: 1.78, 50: 1.96,
    51: 2.05, 52: 2.10, 53: 2.66, 54: 0.00, 55: 0.79, 56: 0.89, 57: 1.10,
    72: 1.30, 73: 1.50, 74: 2.36, 75: 1.90, 76: 2.20, 77: 2.20, 78: 2.28, 79: 2.54, 80: 2.00,
    81: 1.80, 82: 2.33, 83: 2.02, 84: 2.00, 85: 2.20, 86: 0.00, 87: 0.70, 88: 0.90,
    89: 1.10, 90: 1.30, 91: 1.50, 92: 1.38, 93: 1.36, 94: 1.28, 95: 1.30, 96: 1.30,
    97: 1.30, 98: 1.30, 99: 1.30, 100: 1.30, 101: 1.30, 102: 1.30, 103: 1.30
}

def zeta(Z):
    Z = int(Z)
    return 1.4 * (1 + 10/(Z+2))**(-1)

def spin(Z):
    Z = int(Z)
    return 0.5 if Z % 2 == 1 else 0.0

def distance(p1, p2):
    return sqrt(sum((a-b)**2 for a, b in zip(p1, p2)))

def d_opt(Z):
    Z = int(Z)
    if Z <= 20:
        return 2.76
    else:
        return 2.76 + 0.015 * (Z - 20)

def compute_delta_omega(element, all_elements):
    Z = int(element['Z'])
    pos = element['position']
    d_opt_Z = d_opt(Z)
    delta = 0.0
    for other in all_elements:
        if other['symbol'] == element['symbol']:
            continue
        d = distance(pos, other['position'])
        if d < max_neighbor_dist:
            Z_other = int(other['Z'])
            deviation = (d - d_opt_Z) / d_opt_Z
            delta += deviation**2 * (Z_other / Z)
    return delta

def compute_chi_vmms(element, all_elements):
    Z = int(element['Z'])
    delta_omega = compute_delta_omega(element, all_elements)
    chi_vmms = k * delta_omega * Z / (zeta(Z)**2) * (1 + alpha * spin(Z)**2)
    return chi_vmms, delta_omega

def screening_factor(Z):
    r = ATOMIC_RADII.get(Z, 2.0)
    z = zeta(Z)
    return exp(-r / z)

def chi_vmms_to_pauling(chi_vmms, Z):
    return CHI_0 + A * chi_vmms * screening_factor(Z)

def main():
    input_file = '../results/autosave_T300.0_P0.1_128_local_final.json'
    with open(input_file, 'r') as f:
        data = json.load(f)
    elements = data['elements']
    for e in elements:
        e['Z'] = int(e['Z'])
        e['position'] = [float(x) for x in e['position']]
    
    results = []
    for e in elements:
        Z = e['Z']
        chi_vmms, delta_omega = compute_chi_vmms(e, elements)
        chi_eff = chi_vmms_to_pauling(chi_vmms, Z)
        chi_exp = CHI_PAULING.get(Z)
        
        results.append({
            'symbol': e['symbol'],
            'Z': Z,
            'chi_vmms': round(chi_vmms, 3),
            'chi_eff': round(chi_eff, 3),
            'chi_exp': chi_exp,
            'delta_omega': round(delta_omega, 6),
            'd_opt': round(d_opt(Z), 2),
            'radius': ATOMIC_RADII.get(Z, 2.0),
            'zeta': round(zeta(Z), 3),
            'screening': round(screening_factor(Z), 3)
        })
    
    results.sort(key=lambda x: x['Z'])
    
    print("=" * 120)
    print("СРАВНЕНИЕ ЭФФЕКТИВНОЙ ЭЛЕКТРООТРИЦАТЕЛЬНОСТИ (С УЧЁТОМ ЭКРАНИРОВКИ) И ШКАЛЫ ПОЛИНГА")
    print("=" * 120)
    print(f"{'Z':>3} | {'Сим':>4} | {'χ_vmms':>8} | {'r(Å)':>5} | {'ζ(Å)':>5} | {'screen':>6} | {'χ_eff':>8} | {'χ_эксп':>8} | {'Δχ':>8}")
    print("-" * 120)
    
    for r in results:
        Z = r['Z']
        chi_exp = r['chi_exp']
        chi_eff = r['chi_eff']
        
        if chi_exp is not None:
            delta_chi = chi_eff - chi_exp
            exp_str = f"{chi_exp:.3f}"
            delta_str = f"{delta_chi:+.3f}"
        else:
            exp_str = "—"
            delta_str = "—"
        
        print(f"{Z:3} | {r['symbol']:>4} | {r['chi_vmms']:8.3f} | {r['radius']:5.2f} | {r['zeta']:5.3f} | {r['screening']:6.3f} | {chi_eff:8.3f} | {exp_str:>8} | {delta_str:>8}")
    
    print("-" * 120)
    
    valid = [(r['chi_eff'], r['chi_exp']) for r in results if r['chi_exp'] is not None]
    if valid:
        eff_vals = [v[0] for v in valid]
        exp_vals = [v[1] for v in valid]
        mae = np.mean(np.abs(np.array(eff_vals) - np.array(exp_vals)))
        corr = np.corrcoef(eff_vals, exp_vals)[0, 1]
        print(f"\nСТАТИСТИКА:")
        print(f"  Средняя абсолютная ошибка: {mae:.4f}")
        print(f"  Корреляция R²: {corr**2:.4f}")
    
    with open('../results/chi_eff_computed.json', 'w') as f:
        json.dump({'results': results, 'statistics': {'mae': mae, 'R2': corr**2}}, f, indent=2)
    print("\n✓ Результаты сохранены: ../results/chi_eff_computed.json")
    print("=" * 120)

if __name__ == "__main__":
    main()