"""
АБСОЛЮТНО ПОЛНАЯ МОДЕЛЬ ЭЛЕКТРООТРИЦАТЕЛЬНОСТИ ВММП
с оптимизацией всех поправок, включая экранирование нейтронным скином:
- CHI_0, A (калибровка)
- beta_rel (релятивистская)
- delta_n (нейтронный скин — снижение Z_eff)
- gamma_rad (фрактальное замедление)
- skin_screening (экранирование нейтронным скином — увеличение r_eff)
"""

import json
import numpy as np
from math import exp
from scipy.optimize import curve_fit

# ========== КОНСТАНТЫ ==========
k = 0.0608
alpha = 0.01

# Атомные радиусы (Å) — базовые (без нейтронного скина)
ATOMIC_RADII_CORE = {
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

# Экспериментальная шкала Полинга
CHI_PAULING = {
    1: 2.20, 2: 0.00, 3: 0.98, 4: 1.57, 5: 2.04, 6: 2.55, 7: 3.04, 8: 3.44, 9: 3.98, 10: 0.00,
    11: 0.93, 12: 1.31, 13: 1.61, 14: 1.90, 15: 2.19, 16: 2.58, 17: 3.16, 18: 0.00,
    19: 0.82, 20: 1.00, 21: 1.36, 22: 1.54, 23: 1.63, 24: 1.66, 25: 1.55, 26: 1.83,
    27: 1.88, 28: 1.91, 29: 1.90, 30: 1.65, 31: 1.81, 32: 2.01, 33: 2.18, 34: 2.55,
    35: 2.96, 36: 3.00, 37: 0.82, 38: 0.95, 39: 1.22, 40: 1.33, 41: 1.60, 42: 2.16,
    43: 1.90, 44: 2.20, 45: 2.28, 46: 2.20, 47: 1.93, 48: 1.69, 49: 1.78, 50: 1.96,
    51: 2.05, 52: 2.10, 53: 2.66, 54: 2.60, 55: 0.79, 56: 0.89, 57: 1.10,
    72: 1.30, 73: 1.50, 74: 2.36, 75: 1.90, 76: 2.20, 77: 2.20, 78: 2.28, 79: 2.54, 80: 2.00,
    81: 1.80, 82: 2.33, 83: 2.02, 84: 2.00, 85: 2.20, 86: 0.00, 87: 0.70, 88: 0.90,
    89: 1.10, 90: 1.30, 91: 1.50, 92: 1.38, 93: 1.36, 94: 1.28, 95: 1.30, 96: 1.30,
    97: 1.30, 98: 1.30, 99: 1.30, 100: 1.30, 101: 1.30, 102: 1.30, 103: 1.30
}

# Периоды полураспада (сек)
HALF_LIVES = {
    84: 1.2e7, 85: 8.1*3600, 86: 3.3e5, 87: 1.3e3, 88: 5.0e10, 89: 6.9e8,
    90: 4.4e17, 91: 1.0e12, 92: 1.4e17, 93: 6.6e13, 94: 7.6e11, 95: 2.3e10,
    96: 4.9e15, 97: 4.4e9, 98: 2.8e9, 99: 4.1e7, 100: 8.6e6, 101: 4.4e6,
    102: 3.5e3, 103: 3.9e3
}

# Уточнённые симметрии
SYMMETRIES = {
    1: 'C∞v', 2: 'Ih', 3: 'D3h', 4: 'D4h', 5: 'D3h', 6: 'Td', 7: 'D3h', 8: 'Oh', 9: 'D3h', 10: 'Ih',
    11: 'D3h', 12: 'D4h', 13: 'D3h', 14: 'Td', 15: 'D3h', 16: 'Oh', 17: 'D3h', 18: 'Ih',
    19: 'D3h', 20: 'Oh', 21: 'D3h', 22: 'Td', 23: 'D3h', 24: 'Oh', 25: 'D3h', 26: 'Ih',
    27: 'Ih', 28: 'Ih', 29: 'Ih', 30: 'Ih', 31: 'D3h', 32: 'Td', 33: 'D3h', 34: 'Oh', 35: 'D3h', 36: 'Ih',
    57: 'D3h', 58: 'Oh', 59: 'D3h', 60: 'Td', 61: 'D3h', 62: 'Oh', 63: 'Ih',
    64: 'D3h', 65: 'D4h', 66: 'D3h', 67: 'Oh', 68: 'Td', 69: 'D3h', 70: 'Ih', 71: 'D3h',
    72: 'Oh', 73: 'D3h', 74: 'Td', 75: 'D3h', 76: 'Oh', 77: 'Ih', 78: 'Td', 79: 'Oh', 80: 'Ih',
    81: 'D3h', 82: 'Oh', 83: 'D3h', 84: 'Oh', 85: 'D3h', 86: 'Ih',
    87: 'D3h', 88: 'Oh', 89: 'D3h', 90: 'Td', 91: 'D4h', 92: 'Oh', 93: 'D3h',
    94: 'Ih', 95: 'D3h', 96: 'Oh', 97: 'D3h', 98: 'Td', 99: 'D3h', 100: 'Ih',
    101: 'D3h', 102: 'Oh', 103: 'D3h'
}

NUCLEAR_SPINS = {
    1: 0.5, 2: 0.0, 3: 1.0, 4: 1.5, 5: 3.0, 6: 0.0, 7: 1.0, 8: 0.0, 9: 0.5, 10: 0.0,
    11: 1.5, 12: 0.0, 13: 2.5, 14: 0.0, 15: 0.5, 16: 0.0, 17: 1.5, 18: 0.0,
    19: 1.5, 20: 0.0, 21: 3.5, 22: 0.0, 23: 3.5, 24: 0.0, 25: 2.5, 26: 0.0,
    27: 3.5, 28: 0.0, 29: 1.5, 30: 0.0, 31: 1.5, 32: 0.0, 33: 1.5, 34: 0.0,
    35: 1.5, 36: 0.0, 37: 1.5, 38: 0.0, 39: 0.5, 40: 0.0, 41: 4.5, 42: 0.0,
    43: 4.5, 44: 0.0, 45: 0.5, 46: 0.0, 47: 0.5, 48: 0.0, 49: 4.5, 50: 0.0,
    51: 2.5, 52: 0.0, 53: 2.5, 54: 0.0, 55: 3.5, 56: 0.0, 57: 3.5,
    72: 0.0, 73: 3.5, 74: 0.0, 75: 2.5, 76: 0.0, 77: 1.5, 78: 0.0, 79: 1.5, 80: 0.0,
    81: 0.5, 82: 0.0, 83: 4.5, 84: 0.0, 85: 0.5, 86: 0.0, 87: 1.5, 88: 0.0,
    89: 1.5, 90: 0.0, 91: 1.5, 92: 0.0, 93: 2.5, 94: 0.0, 95: 2.5, 96: 0.0,
    97: 3.5, 98: 0.0, 99: 3.5, 100: 0.0, 101: 0.5, 102: 0.0, 103: 3.5
}

# Массовые числа
MASS_NUMBERS = {
    1: 1, 2: 4, 3: 7, 4: 9, 5: 11, 6: 12, 7: 14, 8: 16, 9: 19, 10: 20,
    11: 23, 12: 24, 13: 27, 14: 28, 15: 31, 16: 32, 17: 35, 18: 40,
    19: 39, 20: 40, 21: 45, 22: 48, 23: 51, 24: 52, 25: 55, 26: 56,
    27: 59, 28: 58, 29: 63, 30: 64, 31: 69, 32: 74, 33: 75, 34: 80,
    35: 79, 36: 84, 37: 85, 38: 88, 39: 89, 40: 90, 41: 93, 42: 98,
    43: 98, 44: 102, 45: 103, 46: 106, 47: 107, 48: 114, 49: 115, 50: 120,
    51: 121, 52: 130, 53: 127, 54: 132, 55: 133, 56: 138, 57: 139,
    58: 140, 59: 141, 60: 142, 61: 145, 62: 152, 63: 153, 64: 158, 65: 159,
    66: 164, 67: 165, 68: 166, 69: 169, 70: 174, 71: 175, 72: 180, 73: 181,
    74: 184, 75: 187, 76: 192, 77: 193, 78: 195, 79: 197, 80: 202, 81: 205,
    82: 208, 83: 209, 84: 209, 85: 210, 86: 222, 87: 223, 88: 226, 89: 227,
    90: 232, 91: 231, 92: 238, 93: 237, 94: 244, 95: 243, 96: 247, 97: 247,
    98: 251, 99: 252, 100: 257, 101: 258, 102: 259, 103: 266
}

def get_symmetry(Z):
    return SYMMETRIES.get(int(Z), 'D3h')

def get_fractal_level(Z):
    Z_int = int(Z)
    if Z_int <= 2: return 1
    elif Z_int <= 10: return 2
    elif Z_int <= 18: return 3
    elif Z_int <= 36: return 4
    elif Z_int <= 54: return 5
    elif Z_int <= 86: return 6
    else: return 7

def symmetry_factor(sym):
    factors = {'Ih': 0.0, 'Oh': 0.5, 'Td': 1.0, 'D3h': 0.7, 'D4h': 0.7, 'C∞v': 0.3}
    return factors.get(sym, 0.5)

def zeta(Z):
    return 1.4 * (1 + 10/(int(Z)+2))**(-1)

def spin(Z):
    return NUCLEAR_SPINS.get(int(Z), 0.5 if int(Z) % 2 == 1 else 0.0)

def relativistic_correction(Z, beta_rel):
    Z_int = int(Z)
    alpha_fs = 1.0 / 137.036
    gamma = np.sqrt(1.0 + (Z_int * alpha_fs)**2)
    return 1.0 + beta_rel * (gamma - 1.0)

def neutron_skin_correction(Z, delta_n):
    """Поправка на нейтронный скин — снижение Z_eff"""
    Z_int = int(Z)
    A = MASS_NUMBERS.get(Z_int, int(Z_int * 2.5))
    N = A - Z_int
    return 1.0 - delta_n * (N - Z_int) / A

def radioactive_slowing(Z, level, gamma_rad):
    Z_int = int(Z)
    if Z_int <= 83:
        return 1.0
    T_half = HALF_LIVES.get(Z_int, 1e10)
    T_0 = 1e10
    slowing = 1.0 + gamma_rad * np.log10(T_0 / (T_half + 1))
    return slowing

def compute_chi_vmms_single(Z, beta_rel, delta_n, gamma_rad):
    Z_int = int(Z)
    sym = get_symmetry(Z_int)
    level = get_fractal_level(Z_int)
    f_sym = symmetry_factor(sym)
    
    delta_omega = (2**(-level)) * f_sym
    S = spin(Z_int)
    spin_corr = 1.0 + alpha * S**2
    
    rel_corr = relativistic_correction(Z_int, beta_rel)
    neutron_corr = neutron_skin_correction(Z_int, delta_n)
    rad_corr = radioactive_slowing(Z_int, level, gamma_rad)
    
    chi = k * delta_omega * Z_int / (zeta(Z_int)**2) * spin_corr
    chi *= rel_corr * neutron_corr * rad_corr
    
    return chi

def screening_factor_with_skin(Z, skin_screening):
    """Экранировка с учётом нейтронного скина"""
    Z_int = int(Z)
    r_core = ATOMIC_RADII_CORE.get(Z_int, 2.0)
    A = MASS_NUMBERS.get(Z_int, int(Z_int * 2.5))
    N = A - Z_int
    r_skin = skin_screening * (N - Z_int) / A * 0.5
    r_eff = r_core + r_skin
    z = zeta(Z_int)
    return exp(-r_eff / z)

def model_function(Z, CHI_0, A, beta_rel, delta_n, gamma_rad, skin_screening):
    chi_vmms = np.array([compute_chi_vmms_single(z, beta_rel, delta_n, gamma_rad) for z in Z])
    screen = np.array([screening_factor_with_skin(z, skin_screening) for z in Z])
    return CHI_0 + A * chi_vmms * screen

def main():
    Z_exp = [z for z in range(1, 104) if z in CHI_PAULING and CHI_PAULING[z] > 0]
    chi_exp = [CHI_PAULING[z] for z in Z_exp]
    
    popt, _ = curve_fit(model_function, np.array(Z_exp), np.array(chi_exp), 
                        p0=[1.31, 25.18, 11.56, 0.85, 0.011, 0.1], maxfev=10000)
    CHI_0_opt, A_opt, beta_opt, delta_opt, gamma_opt, skin_opt = popt
    
    print("=" * 120)
    print("ФИНАЛЬНАЯ МОДЕЛЬ ЭЛЕКТРООТРИЦАТЕЛЬНОСТИ ВММП")
    print("(с экранированием нейтронным скином)")
    print("=" * 120)
    print(f"CHI_0         = {CHI_0_opt:.6f}  (базовый уровень)")
    print(f"A             = {A_opt:.6f}  (масштаб χ_vmms → χ_eff)")
    print(f"beta_rel      = {beta_opt:.6f}  (релятивистская поправка)")
    print(f"delta_n       = {delta_opt:.6f}  (нейтронный скин → снижение Z_eff)")
    print(f"gamma_rad     = {gamma_opt:.6f}  (фрактальное замедление)")
    print(f"skin_screening= {skin_opt:.6f}  (экранирование нейтронным скином)")
    
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
    
    results = []
    for Z in range(1, 104):
        chi_vmms = compute_chi_vmms_single(Z, beta_opt, delta_opt, gamma_opt)
        chi_eff = CHI_0_opt + A_opt * chi_vmms * screening_factor_with_skin(Z, skin_opt)
        chi_exp = CHI_PAULING.get(Z)
        
        results.append({
            'Z': Z, 'symbol': symbols[Z],
            'chi_vmms': round(chi_vmms, 4), 'chi_eff': round(chi_eff, 3), 'chi_exp': chi_exp
        })
    
    print("\n" + "=" * 100)
    print(f"{'Z':>3} | {'Сим':>4} | {'χ_vmms':>8} | {'χ_eff':>8} | {'χ_эксп':>8} | {'Δχ':>8}")
    print("-" * 100)
    
    for r in results:
        Z = r['Z']
        chi_exp = r['chi_exp']
        chi_eff = r['chi_eff']
        if chi_exp is not None:
            delta = chi_eff - chi_exp
            print(f"{Z:3} | {r['symbol']:>4} | {r['chi_vmms']:8.4f} | {chi_eff:8.3f} | {chi_exp:8.3f} | {delta:+8.3f}")
        else:
            print(f"{Z:3} | {r['symbol']:>4} | {r['chi_vmms']:8.4f} | {chi_eff:8.3f} | {'—':>8} | {'—':>8}")
    
    valid = [(r['chi_eff'], r['chi_exp']) for r in results if r['chi_exp'] is not None]
    if valid:
        eff_vals, exp_vals = zip(*valid)
        mae = np.mean(np.abs(np.array(eff_vals) - np.array(exp_vals)))
        corr = np.corrcoef(eff_vals, exp_vals)[0, 1]
        print("-" * 100)
        print(f"MAE = {mae:.4f}")
        print(f"R²  = {corr**2:.4f}")
        
        # Отдельная статистика для тяжёлых элементов
        heavy = [(r['chi_eff'], r['chi_exp']) for r in results if r['Z'] >= 80 and r['chi_exp'] is not None]
        if heavy:
            h_eff, h_exp = zip(*heavy)
            h_mae = np.mean(np.abs(np.array(h_eff) - np.array(h_exp)))
            print(f"\nMAE для Z ≥ 80: {h_mae:.4f}")

if __name__ == "__main__":
    main()