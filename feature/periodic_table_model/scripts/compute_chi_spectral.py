"""
Вычисление электроотрицательности χ через теоретические частоты вихрей.
Основано на симметрии и фрактальном уровне.
"""

import json
import numpy as np
from math import exp

# ========== КОНСТАНТЫ ==========
k = 0.0608
alpha = 0.01
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

# Симметрии для элементов (из field_H_elements_complete.json)
SYMMETRIES = {
    1: 'C∞v', 2: 'Ih', 3: 'D3h', 4: 'D4h', 5: 'D3h', 6: 'Td', 7: 'D3h', 8: 'Oh', 9: 'D3h', 10: 'Ih',
    11: 'D3h', 12: 'D4h', 13: 'D3h', 14: 'Td', 15: 'D3h', 16: 'Oh', 17: 'D3h', 18: 'Ih',
    19: 'D3h', 20: 'Oh', 21: 'D3h', 22: 'Td', 23: 'D3h', 24: 'Oh', 25: 'D3h', 26: 'Ih',
    27: 'Ih', 28: 'Ih', 29: 'Ih', 30: 'Ih', 31: 'D3h', 32: 'Td', 33: 'D3h', 34: 'Oh', 35: 'D3h', 36: 'Ih'
}

def get_symmetry(Z):
    if Z in SYMMETRIES:
        return SYMMETRIES[Z]
    # Для Z > 36 используем периодический закон
    group = ((Z - 1) % 18) + 1
    base_Z = group if group <= 18 else group - 18
    if base_Z == 0:
        base_Z = 18
    return SYMMETRIES.get(base_Z, 'D3h')

def get_fractal_level(Z):
    if Z <= 2: return 1
    elif Z <= 10: return 2
    elif Z <= 18: return 3
    elif Z <= 36: return 4
    elif Z <= 54: return 5
    elif Z <= 86: return 6
    else: return 7

def symmetry_factor(sym):
    factors = {'Ih': 0.0, 'Oh': 0.5, 'Td': 1.0, 'D3h': 0.7, 'D4h': 0.7, 'C∞v': 0.3}
    return factors.get(sym, 0.5)

def zeta(Z):
    return 1.4 * (1 + 10/(Z+2))**(-1)

def spin(Z):
    return 0.5 if Z % 2 == 1 else 0.0

def compute_delta_omega_theoretical(Z):
    sym = get_symmetry(Z)
    level = get_fractal_level(Z)
    f_sym = symmetry_factor(sym)
    return (2**(-level)) * f_sym

def compute_chi_vmms(Z):
    delta_omega = compute_delta_omega_theoretical(Z)
    chi = k * delta_omega * Z / (zeta(Z)**2) * (1 + alpha * spin(Z)**2)
    return chi, delta_omega

def screening_factor(Z):
    r = ATOMIC_RADII.get(Z, 2.0)
    z = zeta(Z)
    return exp(-r / z)

def chi_vmms_to_pauling(chi_vmms, Z):
    return CHI_0 + A * chi_vmms * screening_factor(Z)

def main():
    results = []
    
    for Z in range(1, 104):
        sym = get_symmetry(Z)
        level = get_fractal_level(Z)
        chi_vmms, delta_omega = compute_chi_vmms(Z)
        chi_eff = chi_vmms_to_pauling(chi_vmms, Z)
        chi_exp = CHI_PAULING.get(Z)
        
        # Символ элемента
        symbols = {1:'H',2:'He',3:'Li',4:'Be',5:'B',6:'C',7:'N',8:'O',9:'F',10:'Ne',
                   11:'Na',12:'Mg',13:'Al',14:'Si',15:'P',16:'S',17:'Cl',18:'Ar',
                   19:'K',20:'Ca',21:'Sc',22:'Ti',23:'V',24:'Cr',25:'Mn',26:'Fe',27:'Co',
                   28:'Ni',29:'Cu',30:'Zn',31:'Ga',32:'Ge',33:'As',34:'Se',35:'Br',36:'Kr',
                   37:'Rb',38:'Sr',39:'Y',40:'Zr',41:'Nb',42:'Mo',43:'Tc',44:'Ru',45:'Rh',
                   46:'Pd',47:'Ag',48:'Cd',49:'In',50:'Sn',51:'Sb',52:'Te',53:'I',54:'Xe',
                   55:'Cs',56:'Ba',57:'La',58:'Ce',59:'Pr',60:'Nd',61:'Pm',62:'Sm',63:'Eu',
                   64:'Gd',65:'Tb',66:'Dy',67:'Ho',68:'Er',69:'Tm',70:'Yb',71:'Lu',72:'Hf',
                   73:'Ta',74:'W',75:'Re',76:'Os',77:'Ir',78:'Pt',79:'Au',80:'Hg',81:'Tl',
                   82:'Pb',83:'Bi',84:'Po',85:'At',86:'Rn',87:'Fr',88:'Ra',89:'Ac',90:'Th',
                   91:'Pa',92:'U',93:'Np',94:'Pu',95:'Am',96:'Cm',97:'Bk',98:'Cf',99:'Es',
                   100:'Fm',101:'Md',102:'No',103:'Lr'}
        symbol = symbols.get(Z, f'Z{Z}')
        
        results.append({
            'symbol': symbol,
            'Z': Z,
            'symmetry': sym,
            'level': level,
            'chi_vmms': round(chi_vmms, 3),
            'delta_omega': round(delta_omega, 6),
            'chi_eff': round(chi_eff, 3),
            'chi_exp': chi_exp
        })
    
    print("=" * 110)
    print("ВЫЧИСЛЕНИЕ χ ЧЕРЕЗ ТЕОРЕТИЧЕСКИЕ ЧАСТОТЫ (СИММЕТРИЯ + ФРАКТАЛЬНЫЙ УРОВЕНЬ)")
    print("=" * 110)
    print(f"{'Z':>3} | {'Сим':>4} | {'Симметрия':>8} | {'Ур':>2} | {'χ_vmms':>8} | {'Δω/ω₀':>8} | {'χ_eff':>8} | {'χ_эксп':>8} | {'Δχ':>8}")
    print("-" * 110)
    
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
        
        print(f"{Z:3} | {r['symbol']:>4} | {r['symmetry']:>8} | {r['level']:2} | {r['chi_vmms']:8.3f} | {r['delta_omega']:8.4f} | {chi_eff:8.3f} | {exp_str:>8} | {delta_str:>8}")
    
    print("-" * 110)
    
    valid = [(r['chi_eff'], r['chi_exp']) for r in results if r['chi_exp'] is not None]
    if valid:
        eff_vals = [v[0] for v in valid]
        exp_vals = [v[1] for v in valid]
        mae = np.mean(np.abs(np.array(eff_vals) - np.array(exp_vals)))
        corr = np.corrcoef(eff_vals, exp_vals)[0, 1]
        print(f"\nСТАТИСТИКА:")
        print(f"  Средняя абсолютная ошибка: {mae:.4f}")
        print(f"  Корреляция R²: {corr**2:.4f}")
    
    with open('../results/chi_spectral_computed.json', 'w') as f:
        json.dump({'results': results, 'statistics': {'mae': mae, 'R2': corr**2}}, f, indent=2)
    print("\n✓ Результаты сохранены: ../results/chi_spectral_computed.json")
    print("=" * 110)

if __name__ == "__main__":
    main()