"""
ЗАПУСК 3D МОДЕЛИРОВАНИЯ ТАБЛИЦЫ МЕНДЕЛЕЕВА
Версия: "Резонансный Перехват" + Аргумент Укола + Оптимизированный Вывод + Длинный Марафон
ПОЛНАЯ ВЕРСИЯ: 103 элемента, 7 фрактальных уровней (K-Q оболочки).
"""
import json, sys, os, argparse, gc
import numpy as np
from datetime import datetime

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src', 'architect'))

from biharmonic_3d import TopologicalArchitect3D
from thermodynamics import ThermodynamicState, ThermodynamicCalculator
from fractal_time import FractalTimeEvolution, FractalFieldWrapper

# Глобальная константа для шага укола (по умолчанию 1056)
STEP_UKOL = 1056

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

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    global STEP_UKOL
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=1024)
    parser.add_argument('--grid', type=int, default=128)
    parser.add_argument('--T', type=float, default=300.0)
    parser.add_argument('--P', type=float, default=0.1)
    parser.add_argument('--no-tune', action='store_true')
    parser.add_argument('--resume', type=str, help='Путь к чекпоинту для продолжения')
    parser.add_argument('--checkpoint-interval', type=int, default=10000)
    parser.add_argument('--pulse-step', type=int, default=1056, help='Шаг, на котором наносится Укол (0 = без укола)')
    args = parser.parse_args()

    STEP_UKOL = args.pulse_step
    if STEP_UKOL == 0:
        print("[ИНФО] Режим без Укола.")
    
    start_time = datetime.now()
    print("=" * 70)
    print("3D МОДЕЛИРОВАНИЕ ТАБЛИЦЫ МЕНДЕЛЕЕВА (Марафонская Версия)")
    print(f"Укол: {'Да, на шаге ' + str(STEP_UKOL) if STEP_UKOL > 0 else 'НЕТ'}")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)

    grid_size, max_steps, T, P = args.grid, args.steps, args.T, args.P
    print(f"Сетка: {grid_size}^3 | Шагов: {max_steps} | T: {T}K | P: {P}GPa")
    print(f"Чекпоинты: каждые {args.checkpoint_interval} шагов")

    thermo_state = ThermodynamicState(T, P)

    print("\n[1/4] Загрузка элементов...")
    elements_config = load_json(os.path.join(base_dir, 'data', 'field_H_elements_complete.json'))
    all_elements = load_all_elements(elements_config)
    print(f"Загружено элементов: {len(all_elements)}")

    print("\n[2/4] Инициализация 3D-решателя...")
    fields_by_level, components_data = {}, []
    np.random.seed(42)
    for elem in all_elements:
        lvl = elem['fractal_level']
        pos = fractal_spiral_placement_3d(elem['Z'], 100.0, lvl)
        orient = get_orientation(elem.get('symmetry_group', 'C...v'), elem.get('vortex_number', 1))
        comp_data = {'symbol': elem['symbol'], 'Z': elem['Z'], 'charge': elem.get('topological_charge', elem['Z']),
                     'data': elem, 'position': pos, 'orientation': orient, 'level': lvl}
        components_data.append(comp_data)
        if lvl not in fields_by_level:
            fields_by_level[lvl] = {'architect': TopologicalArchitect3D((grid_size,)*3, (100.0,)*3), 'components': []}
        fields_by_level[lvl]['architect'].add_component(
            {'charge': elem.get('topological_charge', elem['Z']), 'position': pos,
             'orientation': orient, 'symbol': elem['symbol'], 'Z': elem['Z']})
        fields_by_level[lvl]['components'].append(comp_data)

    evolution = FractalTimeEvolution(num_levels=7, base_dt=1.0)
    for lvl, data in fields_by_level.items():
        evolution.add_field(lvl, FractalFieldWrapper(data['architect'], lvl))

    checkpoint_base = os.path.join(results_dir, f'autosave_T{T}_P{P}_{grid_size}_local')
    energy_history = []
    start_step = 0

    if args.resume and os.path.exists(args.resume):
        print(f"[!] Восстановление из чекпоинта: {args.resume}")
        saved = load_json(args.resume)
        start_step = saved['metadata']['completed_steps']
        energy_history = saved.get('energy_history', [])
        print(f" Продолжаем с шага {start_step + 1}")

    def save_checkpoint(step, is_final=False):
        chk = {'metadata': {'completed_steps': step+1, 'T': T, 'P': P}, 'energy': energy_history}
        suffix = 'final' if is_final else f'step_{step+1}'
        save_json(f"{checkpoint_base}_{suffix}.json", chk)

    print(f"\n[3/4] Эволюция (шаги {start_step+1}-{max_steps})...")
    print("-" * 100)

    # Переменные для Детектора Живого Танца
    d_min_list = []
    STAGNATION_THRESHOLD = 100000  # <-- Увеличено для марафона
    OSCILLATION_AMPLITUDE_THRESHOLD = 0.001
    stagnation_counter = 0

    for step in range(start_step, max_steps):
        # === УКОЛ СКОРПИОНА (если задан шаг) ===
        if STEP_UKOL > 0 and step == STEP_UKOL:
            print("=" * 60)
            print(f"[УКОЛ] Шаг {step}: P=500, T=50000")
            print("=" * 60)
            thermo_state.pressure = 500.0
            thermo_state.temperature = 50000.0
            if hasattr(thermo_state, 'update_factors'):
                thermo_state.update_factors()
        if STEP_UKOL > 0 and step == STEP_UKOL + 1:
            print("=" * 60)
            print(f"[СБРОС] Шаг {step}: Возврат к норме")
            print("=" * 60)
            thermo_state.pressure = P
            thermo_state.temperature = T
            if hasattr(thermo_state, 'update_factors'):
                thermo_state.update_factors()

        evolution.evolve_step(state=thermo_state)
        total_energy = sum(f.compute_energy() for f in evolution.fields.values() if hasattr(f, 'compute_energy'))
        energy_history.append(total_energy)

        evolved = [lvl for lvl in fields_by_level if evolution.should_evolve(lvl)]
        evolved_str = ','.join(str(l) for l in evolved) if evolved else '...'

        min_dist = float('inf')
        for data in fields_by_level.values():
            for c in data['architect'].components:
                pos = c['vortex'].position
                for c2 in data['architect'].components:
                    if c != c2:
                        d = np.linalg.norm(pos - c2['vortex'].position)
                        if d < min_dist:
                            min_dist = d

        # === ДЕТЕКТОР ЖИВОГО ТАНЦА ===
        d_min_list.append(min_dist)
        if len(d_min_list) > 100000:  # <-- Увеличено окно анализа
            recent_d = d_min_list[-1000:]
            osc_amplitude = max(recent_d) - min(recent_d)
            if osc_amplitude < OSCILLATION_AMPLITUDE_THRESHOLD:
                stagnation_counter += 1
            else:
                stagnation_counter = 0

        # === ВЫВОД (каждые 100 шагов) ===
        if step % 100 == 0 or step == 0:
            step_time = (datetime.now() - start_time).total_seconds()
            print(f"{step+1:6} | d={min_dist:.3f} | E={total_energy:.1f} | Активны: {evolved_str:>18} | {step_time:7.1f}s")
            sys.stdout.flush()

        # === АВТОСТОП (сработает только при очень долгой стагнации) ===
        if stagnation_counter >= STAGNATION_THRESHOLD:
            print("=" * 60)
            print(f"[СТАГНАЦИЯ] Система заснула в d={min_dist:.3f} на {STAGNATION_THRESHOLD} шагов.")
            print("=" * 60)
            break

        # === ЧЕКПОИНТ ===
        if (step + 1) % args.checkpoint_interval == 0:
            save_checkpoint(step, step == max_steps - 1)

        # === СБОРКА МУСОРА ===
        if step % 100 == 0:
            gc.collect()

    print("-" * 100)
    print(f"\n[4/4] Завершено. Финальная энергия: {energy_history[-1]:.1f}")
    save_checkpoint(step, is_final=True)

if __name__ == "__main__":
    main()