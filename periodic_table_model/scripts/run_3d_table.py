"""
Запуск 3D моделирования таблицы Менделеева с термодинамикой, фрактальным временем,
ионизацией и АДАПТИВНОЙ НАСТРОЙКОЙ ЭЛЕКТРООТРИЦАТЕЛЬНОСТИ.
ПОЛНАЯ ВЕРСИЯ: 103 элемента, 7 фрактальных уровней (K-Q оболочки).
Сетка: 128³

Использование:
    python run_3d_table.py [--steps STEPS] [--grid GRID] [--T TEMP] [--P PRESS]
"""

import json
import sys
import os
import argparse
import numpy as np
from datetime import datetime

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src', 'architect'))

from biharmonic_3d import TopologicalArchitect3D
from thermodynamics import (
    ThermodynamicState, 
    ThermodynamicCalculator,
    create_thermodynamic_state
)
from fractal_time import (
    FractalTimeEvolution,
    FractalFieldWrapper,
    TimeQuantum,
    FractalTimeBuffer
)
from adaptive_chi_tuner import AdaptiveChiTuner

# ========== СОХРАНЕНИЕ JSON ==========

def save_json(path, data):
    def convert(obj):
        if isinstance(obj, (np.bool_, bool)): return bool(obj)
        if isinstance(obj, (np.integer, np.int_)): return int(obj)
        if isinstance(obj, (np.floating, np.float_)): return float(obj) if not np.isnan(obj) else None
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, datetime): return obj.isoformat()
        if hasattr(obj, '__dict__'): return obj.__dict__
        return str(obj)
    def convert_recursive(obj):
        if isinstance(obj, dict): return {k: convert_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)): return [convert_recursive(i) for i in obj]
        else: return convert(obj)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(convert_recursive(data), f, indent=2)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ========== ПОПРАВКА НА ИОНИЗАЦИЮ ==========

k_B_eV = 8.617333262145e-5
OMEGA_0 = 27.2

def calculate_ionization_alpha(T: float, Z: int) -> float:
    if T < 1000:
        return 0.0
    n_valence = min(Z, 8)
    omega_n = OMEGA_0 * (Z ** 2) / (n_valence ** 2)
    E_bind = omega_n
    P_ion = np.exp(-E_bind / (k_B_eV * T))
    alpha = 1.0 - np.exp(-P_ion)
    return min(alpha, 1.0)

def apply_ionization_correction(energy: float, Z: int, T: float, beta: float = 1.0) -> float:
    if T == 0:
        return energy
    alpha = calculate_ionization_alpha(T, Z)
    return energy * ((1.0 + beta * alpha) ** 2)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_fractal_level(Z):
    if Z <= 2: return 1
    elif Z <= 10: return 2
    elif Z <= 18: return 3
    elif Z <= 36: return 4
    elif Z <= 54: return 5
    elif Z <= 86: return 6
    else: return 7

def fractal_spiral_placement_3d(Z, grid_size, fractal_level=1):
    golden_angle = 137.508
    r_scale = grid_size / 20.0
    r = r_scale * np.sqrt(Z) * (1 + 0.1 * fractal_level)
    theta = np.radians(Z * golden_angle + fractal_level * 15)
    phi = np.radians(Z * 87.3 + fractal_level * 25)
    return np.array([r * np.sin(phi) * np.cos(theta) + grid_size / 2,
                     r * np.sin(phi) * np.sin(theta) + grid_size / 2,
                     r * np.cos(phi) + grid_size / 2])

def get_orientation(symmetry_group, vortex_number):
    if symmetry_group in ['Ih', 'Oh']: return [1, 0, 0]
    elif symmetry_group in ['Td']: return [1, 1, 1]
    elif symmetry_group in ['D4h']: return [1, 1, 0]
    elif symmetry_group in ['D3h']: return [0, 1, 1]
    elif vortex_number == 1: return [0, 0, 1]
    else: return [0, 0, 1]

def load_all_elements(elements_config):
    all_elements = []
    for elem in elements_config['vortex_components']:
        all_elements.append(elem.copy())
    base_elements = {e['Z']: e for e in elements_config['vortex_components']}
    for z in range(1, 104):
        if z not in base_elements:
            group = ((z - 1) % 18) + 1
            for base_z, base_elem in base_elements.items():
                if ((base_z - 1) % 18) + 1 == group:
                    base_elements[z] = base_elem
                    break
            if z not in base_elements: base_elements[z] = base_elements[1]
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
    for Z in range(32, 104):
        base = base_elements[Z].copy()
        level = get_fractal_level(Z)
        base.update({'symbol': symbols.get(Z, f'Z{Z}'), 'Z': Z, 'component_id': f"{symbols.get(Z)}_Z",
                     'topological_charge': Z, 'fractal_level': level})
        if 'base_frequency_hz' in base: base['base_frequency_hz'] *= (0.8 ** (level - 1))
        else: base['base_frequency_hz'] = 1e15 * (0.8 ** (level - 1))
        if 'electronegativity' in base: base['electronegativity'] *= (0.9 ** (level - 1))
        else: base['electronegativity'] = 1.0 * (0.9 ** (level - 1))
        all_elements.append(base)
    for elem in all_elements:
        if elem['Z'] <= 31: elem['fractal_level'] = get_fractal_level(elem['Z'])
    return sorted(all_elements, key=lambda x: x['Z'])

def compute_vortex_interaction_energy(comp1, comp2, distance, state, level1, level2):
    q1, q2 = comp1['charge'], comp2['charge']
    E_coulomb = q1 * q2 / (distance + 1e-6)
    sym_compat = 1.0 if comp1['data'].get('symmetry_group') == comp2['data'].get('symmetry_group') else 0.5
    n1, n2 = comp1['data'].get('vortex_number', 1), comp2['data'].get('vortex_number', 1)
    E_vortex = -sym_compat * n1 * n2 / (distance**2 + 1e-6)
    f1 = comp1['data'].get('base_frequency_hz', 1e15)
    f2 = comp2['data'].get('base_frequency_hz', 1e15)
    freq_factor = np.exp(-(f1/f2 - 1.0)**2 / 0.1) if f2 > 0 else 1.0
    E0 = E_coulomb + E_vortex * freq_factor
    f_T, f_P = state.temperature_factor, state.pressure_factor
    time_correction = 2 ** (-0.25 * (level1 + level2) / 2)
    ion_corr = (apply_ionization_correction(1.0, comp1['Z'], state.temperature) +
                apply_ionization_correction(1.0, comp2['Z'], state.temperature)) / 2.0
    return E0 * f_T * f_P * time_correction * ion_corr

def symmetry_compatibility(sym1, sym2):
    if sym1 == sym2: return 1.0
    if sym1 == 'Ih' or sym2 == 'Ih': return 0.5
    if sym1 == 'Td' and sym2 in ['Oh', 'D3h']: return 0.8
    if sym1 == 'Oh' and sym2 in ['Td', 'D4h']: return 0.8
    if sym1 in ['D3h', 'D4h', 'C∞v'] and sym2 in ['D3h', 'D4h', 'C∞v']: return 0.7
    return 0.3

def frequency_resonance(comp1, comp2):
    f1 = comp1['data'].get('base_frequency_hz', 1e15)
    f2 = comp2['data'].get('base_frequency_hz', 1e15)
    if f1 == 0 or f2 == 0: return 0.5
    return np.exp(-(f1/f2 - 1.0)**2 / 0.1)

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=1024)
    parser.add_argument('--grid', type=int, default=128)
    parser.add_argument('--T', type=float, default=300.0)
    parser.add_argument('--P', type=float, default=0.1)
    parser.add_argument('--resume', type=str, help='Путь к чекпоинту для продолжения')
    parser.add_argument('--checkpoint-interval', type=int, default=25)
    parser.add_argument('--tune-interval', type=int, default=50, help='Интервал настройки χ (шагов)')
    parser.add_argument('--no-tune', action='store_true', help='Отключить адаптивную настройку χ')
    args = parser.parse_args()

    start_time = datetime.now()
    print("=" * 70)
    print("3D МОДЕЛИРОВАНИЕ ТАБЛИЦЫ МЕНДЕЛЕЕВА С АДАПТИВНОЙ НАСТРОЙКОЙ χ")
    print("Решатель: BiharmonicSolver3D + Thermodynamics + FractalTime + PID")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)

    grid_size, max_steps, T, P = args.grid, args.steps, args.T, args.P
    tune_interval = args.tune_interval
    enable_tuning = not args.no_tune

    print(f"\nСетка: {grid_size}³ | Шагов: {max_steps} | T: {T}K | P: {P}GPa")
    print(f"Настройка χ: {'включена' if enable_tuning else 'отключена'} (интервал: {tune_interval})")
    print(f"Чекпоинты: каждые {args.checkpoint_interval} шагов")

    level_activation = {lvl: max_steps // (2**lvl) for lvl in range(1, 8) if max_steps // (2**lvl) > 0}
    shells = ['K', 'L', 'M', 'N', 'O', 'P', 'Q']
    print("Активации: " + ", ".join([f"{shells[l-1]}:{level_activation[l]}" for l in sorted(level_activation)]))

    thermo_state = ThermodynamicState(T, P)
    thermo_calc = ThermodynamicCalculator(thermo_state)

    print("\n[1/5] Загрузка элементов...")
    elements_config = load_json(os.path.join(base_dir, 'data', 'field_H_elements_complete.json'))
    all_elements = load_all_elements(elements_config)
    print(f"Загружено элементов: {len(all_elements)}")

    # Инициализация адаптивного тюнера χ
    chi_tuner = None
    if enable_tuning:
        print("\n[2/5] Инициализация адаптивного тюнера χ...")
        chi_tuner = AdaptiveChiTuner(os.path.join(base_dir, 'data', 'field_H_elements_complete.json'))
        print(f"    Создано регуляторов: {len(chi_tuner.controllers)}")
    else:
        print("\n[2/5] Адаптивная настройка χ отключена")

    print(f"\n[{'3' if enable_tuning else '2'}/5] Инициализация 3D-решателя...")
    fields_by_level, components_data = {}, []
    np.random.seed(42)
    for elem in all_elements:
        lvl = elem['fractal_level']
        pos = fractal_spiral_placement_3d(elem['Z'], 100.0, lvl)
        orient = get_orientation(elem.get('symmetry_group', 'C∞v'), elem.get('vortex_number', 1))
        comp_data = {'symbol': elem['symbol'], 'Z': elem['Z'], 'charge': elem.get('topological_charge', elem['Z']),
                     'data': elem, 'position': pos, 'orientation': orient, 'level': lvl}
        components_data.append(comp_data)
        if lvl not in fields_by_level:
            fields_by_level[lvl] = {'architect': TopologicalArchitect3D((grid_size,)*3, (100.0,)*3), 'components': []}
        fields_by_level[lvl]['architect'].add_component(
            {'charge': elem.get('topological_charge', elem['Z']), 'position': pos,
             'orientation': orient, 'symbol': elem['symbol'], 'Z': elem['Z']})
        fields_by_level[lvl]['components'].append(comp_data)

    print(f"    Уровней: {len(fields_by_level)}")
    evolution = FractalTimeEvolution(num_levels=7, base_dt=1.0)
    for lvl, data in fields_by_level.items():
        evolution.add_field(lvl, FractalFieldWrapper(data['architect'], lvl))

    checkpoint_base = os.path.join(results_dir, f'autosave_T{T}_P{P}_{grid_size}_local')
    energy_history = []
    chi_history = []
    start_step = 0

    if args.resume and os.path.exists(args.resume):
        print(f"[!] Восстановление из чекпоинта: {args.resume}")
        saved = load_json(args.resume)
        start_step = saved['metadata']['completed_steps']
        energy_history = saved.get('energy_history', [])
        print(f"    Продолжаем с шага {start_step + 1}")

    def save_checkpoint(step, is_final=False):
        state = [{'symbol': c['symbol'], 'Z': c['Z'], 'level': lvl, 'position': c['vortex'].position.tolist()}
                 for lvl, data in fields_by_level.items() for c in data['architect'].components]
        chk = {'metadata': {'completed_steps': step+1, 'T': T, 'P': P}, 'energy': energy_history, 'elements': state}
        if chi_tuner:
            chk['chi_values'] = chi_tuner.get_all_chi()
        suffix = 'final' if is_final else f'step_{step+1}'
        save_json(f"{checkpoint_base}_{suffix}.json", chk)

    print(f"\n[{'4' if enable_tuning else '3'}/5] Эволюция (шаги {start_step+1}-{max_steps})...")
    print("─" * 85)
    header = f"{'Шаг':>5} | {'Энергия':>12} | {'d_min':>6} | {'Активны':>18} | {'α(U)':>6} | {'Время':>7} | {'Сохр':>4} | {'Tune':>4}"
    print(header)
    print("─" * 85)

    for step in range(start_step, max_steps):
        evolution.evolve_step()
        total_energy = sum(f.compute_energy() for f in evolution.fields.values() if hasattr(f, 'compute_energy'))
        energy_history.append(total_energy)

        evolved = [lvl for lvl in fields_by_level if evolution.should_evolve(lvl)]
        evolved_str = ','.join(str(l) for l in evolved) if evolved else '···'

        min_dist = float('inf')
        for data in fields_by_level.values():
            for c in data['architect'].components:
                pos = c['vortex'].position
                for c2 in data['architect'].components:
                    if c != c2:
                        d = np.linalg.norm(pos - c2['vortex'].position)
                        if d < min_dist: 
                            min_dist = d

        # Адаптивная настройка χ (только когда нужно)
        tune_mark = ''
        if enable_tuning and chi_tuner and (step + 1) % tune_interval == 0 and step > 0:
            all_positions_global = []
            all_charges_global = []
            for data in fields_by_level.values():
                for c in data['architect'].components:
                    pos = c['vortex'].position
                    all_positions_global.append(pos)
                    charge = c['vortex'].charge if hasattr(c['vortex'], 'charge') else c.get('Z', 1)
                    all_charges_global.append(charge)
            
            for lvl, data in fields_by_level.items():
                architect = data['architect']
                for comp in architect.components:
                    symbol = comp['symbol']
                    pos = comp['vortex'].position
                    local_e = chi_tuner.compute_local_energy(pos, all_positions_global, all_charges_global)
                    chi_tuner.update_local_energy(symbol, local_e)
            
            new_chi = chi_tuner.tune_all()
            chi_history.append({'step': step + 1, 'chi': new_chi.copy()})
            tune_mark = '🎯'

        # Адаптивная настройка χ
        tune_mark = ''
        if enable_tuning and chi_tuner and (step + 1) % tune_interval == 0 and step > 0:
            for lvl, data in fields_by_level.items():
                architect = data['architect']
                for comp in architect.components:
                    symbol = comp['symbol']
                    pos = comp['vortex'].position
                    local_e = chi_tuner.compute_local_energy(pos, all_positions_global, all_charges_global)
                    chi_tuner.update_local_energy(symbol, local_e)
            
            new_chi = chi_tuner.tune_all()
            chi_history.append({'step': step + 1, 'chi': new_chi.copy()})
            tune_mark = '🎯'

        alpha_u = calculate_ionization_alpha(T, 92)
        step_time = (datetime.now() - start_time).total_seconds()
        saved = ''
        if (step + 1) % args.checkpoint_interval == 0 or step == max_steps - 1:
            save_checkpoint(step, step == max_steps - 1)
            saved = '💾'

        progress = (step + 1 - start_step) / (max_steps - start_step)
        bar_length = 15
        filled = int(progress * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"{step+1:5} | {total_energy:12.1f} | {min_dist:6.2f} | {evolved_str:>18} | {alpha_u:6.3f} | {step_time:7.1f}s | {saved:>4} | {tune_mark:>4} [{bar}]")
        sys.stdout.flush()

    print("─" * 85)
    print(f"\n[{'5' if enable_tuning else '4'}/5] Анализ связей...")

    # Сохранение результатов настройки χ
    if enable_tuning and chi_tuner:
        chi_tuner.save_results(os.path.join(results_dir, f'chi_tuned_T{T}_P{P}.json'))
        chi_tuner.print_summary()

    # Финальное сохранение
    save_checkpoint(max_steps - 1, is_final=True)
    print(f"\nГОТОВО. Финальная энергия: {energy_history[-1]:.1f}")

if __name__ == "__main__":
    main()