"""
Запуск 3D моделирования таблицы Менделеева с термодинамикой и фрактальным временем.
ПОЛНАЯ ВЕРСИЯ: 103 элемента, все фрактальные уровни, поправки на время.
Сетка: 128³

Использование:
    python run_3d_table.py [--steps STEPS] [--grid GRID] [--resume CHECKPOINT]
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

# ========== ИСПРАВЛЕННАЯ ФУНКЦИЯ СОХРАНЕНИЯ JSON ==========

def save_json(path, data):
    """Сохранить JSON с правильной конвертацией numpy типов"""
    def convert(obj):
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, np.int_, np.int32, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float_, np.float32, np.float64)):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, complex):
            return {'real': obj.real, 'imag': obj.imag}
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=convert)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def fractal_spiral_placement_3d(Z, grid_size, fractal_level=1):
    """Фрактальное размещение элементов в 3D"""
    golden_angle = 137.508
    r_scale = grid_size / 20.0
    
    r = r_scale * np.sqrt(Z) * (1 + 0.1 * fractal_level)
    theta = np.radians(Z * golden_angle + fractal_level * 15)
    phi = np.radians(Z * 87.3 + fractal_level * 25)
    
    x = r * np.sin(phi) * np.cos(theta) + grid_size / 2
    y = r * np.sin(phi) * np.sin(theta) + grid_size / 2
    z = r * np.cos(phi) + grid_size / 2
    
    return np.array([x, y, z])

def get_orientation(symmetry_group, vortex_number):
    """Определить ориентацию вихря по симметрии"""
    if symmetry_group in ['Ih', 'Oh']:
        return [1, 0, 0]
    elif symmetry_group in ['Td']:
        return [1, 1, 1]
    elif symmetry_group in ['D4h']:
        return [1, 1, 0]
    elif symmetry_group in ['D3h']:
        return [0, 1, 1]
    elif vortex_number == 1:
        return [0, 0, 1]
    else:
        return [0, 0, 1]

def load_all_elements(elements_config):
    """Загрузить ВСЕ 103 элемента, включая фрактально-генерируемые."""
    all_elements = []
    
    for elem in elements_config['vortex_components']:
        all_elements.append(elem.copy())
    
    base_elements = {e['Z']: e for e in elements_config['vortex_components']}
    
    for z in range(1, 104):
        if z not in base_elements:
            group = ((z - 1) % 18) + 1
            for base_z, base_elem in base_elements.items():
                base_group = ((base_z - 1) % 18) + 1
                if base_group == group:
                    base_elements[z] = base_elem
                    break
            if z not in base_elements:
                base_elements[z] = base_elements[1]
    
    symbols = {
        1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
        11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar',
        19: 'K', 20: 'Ca', 21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co',
        28: 'Ni', 29: 'Cu', 30: 'Zn', 31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr',
        37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr', 41: 'Nb', 42: 'Mo', 43: 'Tc', 44: 'Ru', 45: 'Rh',
        46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn', 51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe',
        55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce', 59: 'Pr', 60: 'Nd', 61: 'Pm', 62: 'Sm', 63: 'Eu',
        64: 'Gd', 65: 'Tb', 66: 'Dy', 67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb', 71: 'Lu', 72: 'Hf',
        73: 'Ta', 74: 'W', 75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg', 81: 'Tl',
        82: 'Pb', 83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th',
        91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf', 99: 'Es',
        100: 'Fm', 101: 'Md', 102: 'No', 103: 'Lr'
    }
    
    for Z in range(32, 104):
        base = base_elements[Z].copy()
        period = (Z - 1) // 18 + 1
        
        base['symbol'] = symbols.get(Z, f'Z{Z}')
        base['Z'] = Z
        base['component_id'] = f"{base['symbol']}_{Z}"
        base['topological_charge'] = Z
        base['fractal_level'] = period
        
        if 'base_frequency_hz' in base:
            base['base_frequency_hz'] = base['base_frequency_hz'] * (0.8 ** (period - 1))
        else:
            base['base_frequency_hz'] = 1e15 * (0.8 ** (period - 1))
            
        if 'electronegativity' in base:
            base['electronegativity'] = base['electronegativity'] * (0.9 ** (period - 1))
        else:
            base['electronegativity'] = 1.0 * (0.9 ** (period - 1))
        
        all_elements.append(base)
    
    all_elements.sort(key=lambda x: x['Z'])
    return all_elements

def compute_vortex_interaction_energy(comp1, comp2, distance, state, level1, level2):
    """Вычислить энергию взаимодействия с учётом T, P и фрактального времени"""
    q1, q2 = comp1['charge'], comp2['charge']
    E_coulomb = q1 * q2 / (distance + 1e-6)
    
    sym_compat = symmetry_compatibility(
        comp1['data'].get('symmetry_group', 'C∞v'),
        comp2['data'].get('symmetry_group', 'C∞v')
    )
    
    n1 = comp1['data'].get('vortex_number', 1)
    n2 = comp2['data'].get('vortex_number', 1)
    E_vortex = -sym_compat * n1 * n2 / (distance**2 + 1e-6)
    
    f1 = comp1['data'].get('base_frequency_hz', 1e15)
    f2 = comp2['data'].get('base_frequency_hz', 1e15)
    freq_factor = np.exp(-(f1/f2 - 1.0)**2 / 0.1) if f2 > 0 else 1.0
    
    E0 = E_coulomb + E_vortex * freq_factor
    
    f_T = state.temperature_factor
    f_P = state.pressure_factor
    
    alpha = 0.25
    level_avg = (level1 + level2) / 2
    time_correction = 2 ** (-alpha * level_avg)
    
    return E0 * f_T * f_P * time_correction

def symmetry_compatibility(sym1, sym2):
    """Оценка совместимости групп симметрии (0-1)"""
    if sym1 == sym2:
        return 1.0
    if sym1 == 'Ih' or sym2 == 'Ih':
        return 0.5
    if sym1 == 'Td' and sym2 in ['Oh', 'D3h']:
        return 0.8
    if sym1 == 'Oh' and sym2 in ['Td', 'D4h']:
        return 0.8
    if sym1 in ['D3h', 'D4h', 'C∞v'] and sym2 in ['D3h', 'D4h', 'C∞v']:
        return 0.7
    return 0.3

def frequency_resonance(comp1, comp2):
    """Оценка резонанса частот (0-1)"""
    f1 = comp1['data'].get('base_frequency_hz', 1e15)
    f2 = comp2['data'].get('base_frequency_hz', 1e15)
    if f1 == 0 or f2 == 0:
        return 0.5
    ratio = f1 / f2
    return np.exp(-(ratio - 1.0)**2 / 0.1)

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

def main():
    parser = argparse.ArgumentParser(description='3D моделирование таблицы Менделеева')
    parser.add_argument('--steps', type=int, default=50, help='Количество шагов эволюции (по умолчанию 50)')
    parser.add_argument('--grid', type=int, default=128, help='Размер сетки (по умолчанию 128)')
    parser.add_argument('--T', type=float, default=300.0, help='Температура (K)')
    parser.add_argument('--P', type=float, default=0.1, help='Давление (GPa)')
    parser.add_argument('--no-save', action='store_true', help='Не сохранять результаты')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    print("=" * 70)
    print("3D МОДЕЛИРОВАНИЕ ТАБЛИЦЫ МЕНДЕЛЕЕВА С ФРАКТАЛЬНЫМ ВРЕМЕНЕМ")
    print("Решатель: BiharmonicSolver3D + Thermodynamics + FractalTime")
    print("=" * 70)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    grid_size = args.grid
    max_steps = args.steps
    T = args.T
    P = args.P
    
    print(f"\nПараметры запуска:")
    print(f"  - Сетка: {grid_size}³ ({grid_size**3:,} ячеек)")
    print(f"  - Шагов эволюции: {max_steps}")
    print(f"  - Температура: {T} K")
    print(f"  - Давление: {P} GPa")
    
    # Уровни и их активация
    level_activation = {}
    for lvl in range(1, 8):
        period = 2 ** lvl
        activations = max_steps // period
        if activations > 0:
            level_activation[lvl] = activations
    print(f"  - Активации уровней: {level_activation}")
    
    thermo_state = ThermodynamicState(T, P)
    thermo_calc = ThermodynamicCalculator(thermo_state)
    
    print(f"  - f_T = {thermo_state.temperature_factor:.4f}")
    print(f"  - f_P = {thermo_state.pressure_factor:.4f}")
    
    # Загрузка элементов
    print("\n[1/4] Загрузка элементов...")
    elements_config = load_json(os.path.join(base_dir, 'data', 'field_H_elements_complete.json'))
    all_elements = load_all_elements(elements_config)
    
    print(f"  - Загружено элементов: {len(all_elements)}")
    
    fractal_levels = {}
    for e in all_elements:
        lvl = e.get('fractal_level', 1)
        fractal_levels[lvl] = fractal_levels.get(lvl, 0) + 1
    print(f"  - Фрактальные уровни: {dict(sorted(fractal_levels.items()))}")
    
    # Инициализация
    print(f"\n[2/4] Инициализация 3D-решателя с фрактальным временем...")
    
    fields_by_level = {}
    components_data = []
    np.random.seed(42)
    
    for elem in all_elements:
        fractal_lvl = elem.get('fractal_level', 1)
        position = fractal_spiral_placement_3d(elem['Z'], 100.0, fractal_lvl)
        orientation = get_orientation(
            elem.get('symmetry_group', 'C∞v'),
            elem.get('vortex_number', 1)
        )
        
        comp_data = {
            'symbol': elem['symbol'],
            'Z': elem['Z'],
            'charge': elem.get('topological_charge', elem['Z']),
            'data': elem,
            'position': position,
            'orientation': orientation,
            'level': fractal_lvl
        }
        components_data.append(comp_data)
        
        if fractal_lvl not in fields_by_level:
            architect = TopologicalArchitect3D(
                grid_shape=(grid_size, grid_size, grid_size),
                box_size=(100.0, 100.0, 100.0)
            )
            fields_by_level[fractal_lvl] = {
                'architect': architect,
                'components': []
            }
        
        architect = fields_by_level[fractal_lvl]['architect']
        architect.add_component({
            'charge': elem.get('topological_charge', elem['Z']),
            'position': position,
            'orientation': orientation,
            'symbol': elem['symbol'],
            'Z': elem['Z']
        })
        fields_by_level[fractal_lvl]['components'].append(comp_data)
    
    print(f"  - Уровней: {len(fields_by_level)}")
    for lvl, data in sorted(fields_by_level.items()):
        print(f"    Уровень {lvl}: {len(data['components'])} элементов, активаций: {level_activation.get(lvl, 0)}")
    
    evolution = FractalTimeEvolution(num_levels=max(fields_by_level.keys()), base_dt=1.0)
    
    for lvl, data in fields_by_level.items():
        wrapped = FractalFieldWrapper(data['architect'], lvl)
        evolution.add_field(lvl, wrapped)
    
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Эволюция
    print(f"\n[3/4] Эволюция с фрактальным временем ({max_steps} шагов)...")
    print("=" * 70)
    print(f"{'Шаг':>4} | {'Энергия':>15} | {'Уровни':>25} | {'Время':>8}")
    print("-" * 70)
    
    energy_history = []
    
    def progress_callback(step, evo):
        total_energy = 0.0
        evolved = []
        for lvl, field in evo.fields.items():
            if hasattr(field, 'compute_energy'):
                total_energy += field.compute_energy()
            if evo.should_evolve(lvl):
                evolved.append(lvl)
        
        energy_history.append(total_energy)
        step_time = (datetime.now() - start_time).total_seconds()
        evolved_str = ','.join(str(l) for l in evolved) if evolved else '-'
        
        print(f"{step:4} | {total_energy:15.2f} | {evolved_str:>25} | {step_time:7.1f}s")
    
    history = evolution.evolve(max_steps, callback=progress_callback)
    print("-" * 70)
    
    # Анализ связей
    print("\n[4/4] Анализ связей с термодинамикой...")
    
    bonds = []
    all_positions = []
    all_components = []
    
    for lvl, data in fields_by_level.items():
        architect = data['architect']
        for comp in architect.components:
            all_positions.append(comp['vortex'].position)
            all_components.append(comp)
    
    for i in range(len(all_positions)):
        for j in range(i+1, len(all_positions)):
            dist = np.linalg.norm(all_positions[i] - all_positions[j])
            if dist < 15.0:
                comp1 = all_components[i]
                comp2 = all_components[j]
                
                comp1_data = next(c for c in components_data if c['symbol'] == comp1['symbol'])
                comp2_data = next(c for c in components_data if c['symbol'] == comp2['symbol'])
                
                E_interaction = compute_vortex_interaction_energy(
                    comp1_data, comp2_data, dist, thermo_state,
                    comp1_data['level'], comp2_data['level']
                )
                
                sym_compat = symmetry_compatibility(
                    comp1_data['data'].get('symmetry_group', 'C∞v'),
                    comp2_data['data'].get('symmetry_group', 'C∞v')
                )
                freq_res = frequency_resonance(comp1_data, comp2_data)
                stability = thermo_calc.stability_score(E_interaction, sym_compat, freq_res)
                P_crit = thermo_state.get_critical_pressure(dist)
                
                bonds.append({
                    'elements': [comp1['symbol'], comp2['symbol']],
                    'Z': [comp1_data['Z'], comp2_data['Z']],
                    'distance': float(dist),
                    'stability': float(stability),
                    'is_stable': bool(stability > 0.5),
                    'P_crit_GPa': float(P_crit),
                    'levels': [comp1_data['level'], comp2_data['level']]
                })
    
    bonds.sort(key=lambda x: x['stability'], reverse=True)
    
    # Сохранение
    if not args.no_save:
        print("\n" + "=" * 70)
        print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
        print("=" * 70)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        results = {
            'metadata': {
                'model': 'VMMS 3D + Fractal Time + Thermodynamics',
                'grid_size': grid_size,
                'steps': max_steps,
                'num_elements': len(all_elements),
                'T_K': T,
                'P_GPa': P,
                'total_time_s': total_time,
                'timestamp': datetime.now().isoformat()
            },
            'level_activations': level_activation,
            'energy_history': energy_history,
            'stable_bonds': [b for b in bonds if b['is_stable']],
            'all_bonds': bonds[:100],
            'elements': [{'symbol': c['symbol'], 'Z': c['Z'], 'level': c['level'], 
                         'position': c['position'].tolist()} for c in components_data]
        }
        
        output_file = os.path.join(results_dir, f'results_fractal_T{T}_P{P}_{grid_size}_{max_steps}steps.json')
        save_json(output_file, results)
        print(f"  ✓ Результаты: {output_file}")
    
    # Итоговый отчёт
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 70)
    print(f"Шагов: {max_steps}")
    print(f"Элементов: {len(all_elements)}")
    print(f"Время: {(datetime.now() - start_time).total_seconds():.1f} сек")
    print(f"\nЭнергия: начальная = {energy_history[0]:.2f}, финальная = {energy_history[-1]:.2f}")
    print(f"Связей: всего {len(bonds)}, стабильных {sum(1 for b in bonds if b['is_stable'])}")
    
    if bonds:
        stable = [b for b in bonds if b['is_stable']]
        if stable:
            print(f"\nТоп-5 стабильных связей:")
            for b in stable[:5]:
                print(f"  {b['elements'][0]:>2}-{b['elements'][1]:<2}: stability={b['stability']:.3f}, d={b['distance']:.2f}")
    
    print("\n" + "=" * 70)
    print("МОДЕЛИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 70)

if __name__ == "__main__":
    main()