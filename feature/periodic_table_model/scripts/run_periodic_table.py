"""
Скрипт для запуска эндогенного моделирования фрактальной 3D таблицы Менделеева
на основе платформы SpectraVortex.
"""

import json
import sys
import os
import numpy as np

# Добавляем пути к локальным модулям SpectraVortex
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src', 'architect'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'simulator'))

# Пробуем импортировать из локальных модулей
try:
    from architect import TopologicalArchitect
    from field import ScalarFieldH
    from adaptive_router import AdaptiveRouter
    from component import VortexComponent
    print("✓ Модули загружены из локальных исходников")
except ImportError as e1:
    try:
        from src.architect import TopologicalArchitect, ScalarFieldH, AdaptiveRouter
        from src.architect.component import VortexComponent
        print("✓ Модули загружены из src.architect")
    except ImportError as e2:
        try:
            from spectravortex import TopologicalArchitect, ScalarFieldH, AdaptiveRouter
            from spectravortex.components import VortexComponent
            print("✓ Модули загружены из пакета spectravortex")
        except ImportError as e3:
            print(f"Ошибка импорта: {e3}")
            print("\nПроверяем наличие файлов:")
            import glob
            for pattern in ['src/architect/*.py', 'simulator/*.py']:
                files = glob.glob(os.path.join(PROJECT_ROOT, pattern))
                print(f"  {pattern}: {len(files)} файлов")
            sys.exit(1)

def load_json(filepath):
    """Загрузка JSON файла"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Сохранение JSON файла"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fractal_spiral_placement(Z, grid_size, phase=0.0):
    """
    Фрактальное размещение элементов по спирали.
    Использует угол золотого сечения для равномерного распределения.
    """
    golden_angle = 137.508  # градусов
    r_scale = grid_size / 20.0
    
    r = r_scale * np.sqrt(Z)
    theta = np.radians(Z * golden_angle + phase)
    z = (Z - 52) * 2.0
    
    x = r * np.cos(theta) + grid_size / 2
    y = r * np.sin(theta) + grid_size / 2
    z = z + grid_size / 2
    
    return np.array([x, y, z])

def main():
    print("=" * 60)
    print("ЗАПУСК ЭНДОГЕННОГО МОДЕЛИРОВАНИЯ 3D ТАБЛИЦЫ МЕНДЕЛЕЕВА")
    print("Модель: ВММП (Вихревая Модель Материи-Пространства)")
    print("=" * 60)

    print("\n[1/5] Загрузка конфигурационных файлов...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    elements_config = load_json(os.path.join(base_dir, 'data', 'field_H_elements_complete.json'))
    bonds_config = load_json(os.path.join(base_dir, 'data', 'field_H_intermetallides_known.json'))
    isotopes_config = load_json(os.path.join(base_dir, 'data', 'field_H_isotopes_perturbations.json'))
    process_config = load_json(os.path.join(base_dir, 'configs', 'endogenic_process_config.json'))

    print(f"  - Загружено элементов: {len(elements_config['vortex_components'])}")
    print(f"  - Загружено интерметаллидов: {len(bonds_config['bonds'])}")
    print(f"  - Загружено изотопов: {len(isotopes_config['perturbations'])}")

    print("\n[2/5] Инициализация поля H...")
    grid_size = process_config['initialization']['grid_size']
    
    field = ScalarFieldH(
        grid_shape=(grid_size, grid_size, grid_size),
        boundary_condition='periodic'
    )
    
    architect = TopologicalArchitect(
        grid_shape=(grid_size, grid_size, grid_size),
        interaction_kernel='biharmonic',
        convergence_tolerance=1e-6
    )
    print(f"  - Размер сетки: {grid_size} x {grid_size} x {grid_size}")

    print("\n[3/5] Создание вихревых компонентов...")
    components = []
    np.random.seed(process_config['initialization']['random_seed'])
    initial_phase = np.random.random() * 360.0
    
    for elem in elements_config['vortex_components']:
        position = fractal_spiral_placement(elem['Z'], grid_size, initial_phase)
        
        comp = VortexComponent(
            charge=elem['topological_charge'],
            symmetry=elem['symmetry_group'],
            nodes=elem['node_positions_relative'],
            frequency=elem['base_frequency_hz'],
            coherence_length=elem['coherence_length_fm'],
            position=position
        )
        components.append(comp)
    
    print(f"  - Создано компонентов: {len(components)}")

    print("\n[4/5] Добавление изотопных возмущений...")
    for iso in isotopes_config['perturbations']:
        if iso['delta_nodes'] != 0:
            field.add_perturbation(
                parent_symbol=iso['parent_element'],
                amplitude=iso['field_perturbation']['amplitude'],
                phase_shift=iso['field_perturbation']['phase_shift'],
                frequency_shift=iso['field_perturbation']['frequency_shift']
            )
    
    if 'predicted_isotopes' in isotopes_config:
        for iso in isotopes_config['predicted_isotopes']:
            field.add_furcation(
                parent_symbol=iso['parent_element'],
                delta_mass=iso['mass_number'],
                energy_barrier=iso['delta_energy_MeV']
            )
    
    print(f"  - Добавлено возмущений: {len(isotopes_config['perturbations'])}")

    print("\n[5/5] Запуск эндогенного процесса...")
    print("-" * 60)
    
    all_bonds = []
    solutions = []
    
    for i, phase in enumerate(process_config['relaxation_phases'], 1):
        print(f"\n>>> Фаза {i}: {phase['name']}")
        print(f"    T = {phase['temperature_K']} K, P = {phase['pressure_GPa']} GPa")
        print(f"    Итераций: {phase['iterations']}")
        
        solution = architect.optimize(
            components=components,
            objective=phase['objective'],
            constraints=phase['constraints'],
            max_iterations=phase['iterations'],
            temperature=phase['temperature_K'],
            pressure=phase['pressure_GPa']
        )
        
        components = solution.components
        
        if phase.get('adaptive_routing', {}).get('enabled', False):
            router = AdaptiveRouter(field=field)
            bonds = router.extract_bonds(
                components=components,
                gradient_threshold=phase['adaptive_routing']['gradient_threshold'],
                symmetry_filter=True
            )
            all_bonds.extend(bonds)
            print(f"    Найдено связей: {len(bonds)}")
        
        solutions.append({
            'phase': i,
            'name': phase['name'],
            'energy': solution.energy,
            'min_distance': solution.min_distance,
            'packing_coefficient': solution.packing_coefficient
        })
        
        print(f"    Энергия поля: {solution.energy:.2f}")

    print("\n" + "=" * 60)
    print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    field.save(os.path.join(results_dir, 'field_H_endogenic.h5'))
    print(f"  - Поле H сохранено: field_H_endogenic.h5")
    
    final_solution = {
        'metadata': {'model': 'VMMS', 'grid_size': grid_size},
        'phases': solutions,
        'final_state': {
            'energy': solutions[-1]['energy'] if solutions else None,
            'min_distance': solutions[-1]['min_distance'] if solutions else None,
            'packing_coefficient': solutions[-1]['packing_coefficient'] if solutions else None
        }
    }
    save_json(os.path.join(results_dir, 'solution_final.json'), final_solution)
    print(f"  - Решение сохранено: solution_final.json")
    
    bonds_output = {
        'metadata': {'total_bonds': len(all_bonds)},
        'bonds': all_bonds
    }
    save_json(os.path.join(results_dir, 'bonds_discovered.json'), bonds_output)
    print(f"  - Обнаружено связей: {len(all_bonds)}")
    
    stats = {
        'initial_energy': solutions[0]['energy'] if solutions else None,
        'final_energy': solutions[-1]['energy'] if solutions else None,
        'energy_reduction': (solutions[0]['energy'] - solutions[-1]['energy']) if solutions else 0,
        'total_charge': sum(c.charge for c in components),
    }
    save_json(os.path.join(results_dir, 'statistics.json'), stats)
    print(f"  - Статистика сохранена: statistics.json")

    print("\n" + "=" * 60)
    print("МОДЕЛИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
    print(f"Итоговая энергия поля: {solutions[-1]['energy']:.2f}")
    print(f"Обнаружено связей: {len(all_bonds)}")
    print(f"\nРезультаты сохранены в: {results_dir}")

if __name__ == "__main__":
    main()