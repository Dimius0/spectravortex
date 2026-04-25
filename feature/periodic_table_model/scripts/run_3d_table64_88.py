"""
Запуск 3D моделирования таблицы Менделеева с использованием BiharmonicSolver3D.
ПОЛНАЯ ВЕРСИЯ: 103 элемента, все фрактальные уровни, сетка 64³, 20 итераций.
"""

import json
import sys
import os
import numpy as np

# Добавляем путь к нашему 3D-движку
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src', 'architect'))

from biharmonic_3d import TopologicalArchitect3D

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def fractal_spiral_placement_3d(Z, grid_size, fractal_level=1):
    """
    Фрактальное размещение элементов в 3D с учётом фрактального уровня.
    Чем выше уровень, тем больше радиус и сложнее траектория.
    """
    golden_angle = 137.508
    r_scale = grid_size / 20.0
    
    # Радиус зависит от Z и фрактального уровня
    r = r_scale * np.sqrt(Z) * (1 + 0.1 * fractal_level)
    
    # Углы с учётом фрактального уровня
    theta = np.radians(Z * golden_angle + fractal_level * 15)
    phi = np.radians(Z * 87.3 + fractal_level * 25)
    
    x = r * np.sin(phi) * np.cos(theta) + grid_size / 2
    y = r * np.sin(phi) * np.sin(theta) + grid_size / 2
    z = r * np.cos(phi) + grid_size / 2
    
    return np.array([x, y, z])

def load_all_elements(elements_config):
    """
    Загрузить все 103 элемента, включая фрактально-генерируемые.
    """
    all_elements = []
    
    # 1. Явно заданные элементы (Z=1-31)
    for elem in elements_config['vortex_components']:
        all_elements.append(elem)
    
    # 2. Фрактально-генерируемые элементы (Z=32-103)
    if 'fractal_elements_Z_31_103' in elements_config:
        fractal_config = elements_config['fractal_elements_Z_31_103']
        
        # Словарь базовых элементов для копирования свойств
        base_elements = {e['Z']: e for e in elements_config['vortex_components']}
        
        for rule in fractal_config['generation_rules']:
            z_start, z_end = rule['Z_range']
            base_z_start, base_z_end = rule['base_Z']
            level_shift = rule['fractal_level_increment']
            chi_scale = rule['chi_scaling']
            freq_scale = rule['frequency_scaling']
            
            for i, symbol in enumerate(rule['elements']):
                Z = z_start + i
                base_Z = base_z_start + (i % (base_z_end - base_z_start + 1))
                
                if base_Z in base_elements:
                    base = base_elements[base_Z].copy()
                    base['symbol'] = symbol
                    base['Z'] = Z
                    base['component_id'] = f"{symbol}_{Z}"
                    base['fractal_level'] = base.get('fractal_level', 1) + level_shift
                    base['electronegativity'] = base.get('electronegativity', 1.0) * chi_scale
                    base['base_frequency_hz'] = base.get('base_frequency_hz', 1e15) * freq_scale
                    
                    # Масштабируем позиции узлов
                    if 'node_positions_relative' in base:
                        scale = 1.0 + 0.2 * level_shift
                        base['node_positions_relative'] = [
                            [x * scale for x in node] 
                            for node in base['node_positions_relative']
                        ]
                    
                    all_elements.append(base)
    
    # Сортируем по Z
    all_elements.sort(key=lambda x: x['Z'])
    return all_elements

def main():
    print("=" * 60)
    print("3D МОДЕЛИРОВАНИЕ ТАБЛИЦЫ МЕНДЕЛЕЕВА (ПОЛНАЯ ВЕРСИЯ)")
    print("Решатель: BiharmonicSolver3D (∇⁴H = 0)")
    print("Сетка: 64³ | Итераций: 20 | Элементов: 103")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Загрузка элементов
    print("\n[1/3] Загрузка элементов...")
    elements_config = load_json(os.path.join(base_dir, 'data', 'field_H_elements_complete.json'))
    all_elements = load_all_elements(elements_config)
    
    # ЯВНО ЗАДАЁМ ПАРАМЕТРЫ
    grid_size = 64
    max_iter = 20
    temperature = 0.1
    
    print(f"  - Загружено элементов: {len(all_elements)}")
    print(f"  - Сетка: {grid_size}³")
    print(f"  - Итераций: {max_iter}")
    
    # Статистика по фрактальным уровням
    fractal_levels = {}
    for e in all_elements:
        lvl = e.get('fractal_level', 1)
        fractal_levels[lvl] = fractal_levels.get(lvl, 0) + 1
    print(f"  - Распределение по фрактальным уровням: {fractal_levels}")
    
    # Создаём 3D архитектор
    print(f"\n[2/3] Инициализация 3D-решателя...")
    architect = TopologicalArchitect3D(
        grid_shape=(grid_size, grid_size, grid_size),
        box_size=(100.0, 100.0, 100.0)
    )
    
    # Добавляем ВСЕ элементы
    np.random.seed(42)
    
    for elem in all_elements:
        fractal_lvl = elem.get('fractal_level', 1)
        position = fractal_spiral_placement_3d(elem['Z'], 100.0, fractal_lvl)
        
        # Ориентация вихря зависит от симметрии
        symmetry = elem.get('symmetry_group', 'C∞v')
        if symmetry in ['Ih', 'Oh']:
            orientation = [1, 0, 0]  # Сферические вихри
        elif symmetry in ['Td', 'D4h']:
            orientation = [1, 1, 0]  # Тетраэдрические/квадратные
        else:
            orientation = [0, 0, 1]  # Линейные/треугольные
        
        architect.add_component({
            'charge': elem['topological_charge'],
            'position': position,
            'orientation': orientation,
            'symbol': elem['symbol'],
            'Z': elem['Z']
        })
    
    print(f"  Загружено компонентов: {len(architect.components)}")
    
    # Запуск оптимизации
    print(f"\n[3/3] Оптимизация ({max_iter} итераций)...")
    print("-" * 40)
    
    solution = architect.optimize(
        max_iterations=max_iter,
        temperature=temperature
    )
    
    # Сохранение результатов
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)
    print(f"Финальная энергия: {solution.energy:.2f}")
    print(f"Минимальное расстояние: {solution.min_distance:.2f}")
    print(f"Коэффициент упаковки: {solution.packing_coefficient:.3f}")
    print(f"Суммарный заряд: {solution.total_charge}")
    
    # Финальное поле
    architect.solve_biharmonic(max_iter=30)
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Сохраняем позиции ВСЕХ элементов
    elements_output = {
        'metadata': {
            'model': 'VMMS 3D',
            'grid_size': grid_size,
            'iterations': max_iter,
            'num_elements': len(all_elements),
            'fractal_levels': fractal_levels
        },
        'elements': [
            {
                'symbol': c['symbol'],
                'Z': c['Z'],
                'position': [float(x) for x in c['vortex'].position],
                'charge': float(c['vortex'].charge)
            }
            for c in architect.components
        ]
    }
    
    output_file = os.path.join(results_dir, 'elements_3d_full_103.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(elements_output, f, indent=2)
    
    print(f"\nРезультаты сохранены в: {output_file}")
    
    # Находим ядра вихрей
    cores = architect.find_vortex_cores(threshold=0.3)
    print(f"\nОбнаружено ядер вихря: {len(cores)}")
    if cores:
        print("  Топ-10 по силе:")
        for pos, strength in cores[:10]:
            print(f"    ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}): {strength:.2f}")
    
    # Анализ связей
    print("\n" + "=" * 60)
    print("АНАЛИЗ СВЯЗЕЙ")
    print("=" * 60)
    
    positions = [c['vortex'].position for c in architect.components]
    symbols = [c['symbol'] for c in architect.components]
    
    bonds = []
    for i in range(len(positions)):
        for j in range(i+1, len(positions)):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < 15.0:
                bonds.append({
                    'elements': [symbols[i], symbols[j]],
                    'distance': float(dist)
                })
    
    bonds.sort(key=lambda x: x['distance'])
    
    print(f"Найдено {len(bonds)} потенциальных связей (dist < 15.0)")
    if bonds:
        print("\n  Топ-20 ближайших пар:")
        for bond in bonds[:20]:
            print(f"    {bond['elements'][0]}-{bond['elements'][1]}: {bond['distance']:.2f}")
    
    # Группировка связей по известным интерметаллидам
    known_bonds = load_json(os.path.join(base_dir, 'data', 'field_H_intermetallides_known.json'))
    known_formulas = set(b['formula'] for b in known_bonds['bonds'])
    
    predicted_known = []
    for bond in bonds:
        formula1 = f"{bond['elements'][0]}{bond['elements'][1]}"
        formula2 = f"{bond['elements'][1]}{bond['elements'][0]}"
        if formula1 in known_formulas or formula2 in known_formulas:
            predicted_known.append(bond)
    
    if predicted_known:
        print(f"\n  Из них {len(predicted_known)} совпадают с известными интерметаллидами:")
        for bond in predicted_known[:10]:
            print(f"    ✓ {bond['elements'][0]}-{bond['elements'][1]}")
    
    print("\n" + "=" * 60)
    print("МОДЕЛИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
    print("=" * 60)

if __name__ == "__main__":
    main()