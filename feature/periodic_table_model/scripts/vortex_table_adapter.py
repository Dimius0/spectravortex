"""
Адаптер для моделирования фрактальной 3D таблицы Менделеева
на основе реального API SpectraVortex.
"""

import json
import sys
import os
import numpy as np

# Добавляем пути к модулям SpectraVortex
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Добавляем корень проекта в sys.path
sys.path.insert(0, PROJECT_ROOT)

# Создаём пустые __init__.py если их нет (для корректной работы пакетов)
def ensure_init(path):
    init_file = os.path.join(path, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Auto-generated\n')

ensure_init(os.path.join(PROJECT_ROOT, 'src'))
ensure_init(os.path.join(PROJECT_ROOT, 'src', 'architect'))
ensure_init(os.path.join(PROJECT_ROOT, 'router'))

# Теперь импортируем как нормальные пакеты
from src.architect.architect import TopologicalArchitect
from src.architect.component import Component
from src.architect.temporal_state import TemporalState
from router.adaptive_router import AStarRouter

print("✓ Модули SpectraVortex загружены")

class ElementComponent(Component):
    """
    Расширение базового Component для химических элементов.
    Добавляет вихревые параметры из ВММП.
    """
    
    def __init__(self, element_data, position=None):
        # Базовые параметры Component
        super().__init__(
            id=element_data['Z'],
            charge=element_data['topological_charge'],
            health=1.0,
            load=0.1,
            temporal=TemporalState()
        )
        
        # Вихревые параметры из ВММП
        self.symbol = element_data['symbol']
        self.Z = element_data['Z']
        self.symmetry_group = element_data['symmetry_group']
        self.vortex_number = element_data['vortex_number']
        self.fractal_level = element_data['fractal_level']
        self.coherence_length = element_data['coherence_length_fm']
        self.base_frequency = element_data['base_frequency_hz']
        self.electronegativity = element_data['electronegativity']
        self.node_positions = np.array(element_data['node_positions_relative'])
        self.thermodynamics = element_data['thermodynamics']
        self.isotopes = element_data.get('isotopes', [])
        
        # Позиция в 3D пространстве
        self.position = position if position is not None else np.zeros(3)
        
        # Состояние вихря
        self.vortex_phase = 0.0
        self.vortex_energy = 0.0
        
    def get_vortex_radius(self):
        """Радиус вихря в условных единицах"""
        return self.coherence_length * (1 + 0.1 * np.log(self.Z + 1))
    
    def get_interaction_potential(self, other, distance):
        """
        Потенциал взаимодействия между двумя вихрями.
        Основан на топологической совместимости и резонансе частот.
        """
        if distance < 1e-6:
            return 1e10  # Отталкивание при совпадении
        
        # Совместимость симметрий
        sym_compat = self._symmetry_compatibility(other)
        
        # Резонанс частот
        freq_ratio = self.base_frequency / other.base_frequency if other.base_frequency > 0 else 1.0
        freq_resonance = np.exp(-(freq_ratio - 1.0)**2 / 0.1)
        
        # Кулоновское отталкивание
        coulomb = self.charge * other.charge / distance
        
        # Вихревое взаимодействие (притяжение при совместимости, отталкивание иначе)
        vortex = -sym_compat * freq_resonance * self.vortex_number * other.vortex_number / distance**2
        
        return coulomb + vortex
    
    def _symmetry_compatibility(self, other):
        """Оценка совместимости групп симметрии"""
        if self.symmetry_group == other.symmetry_group:
            return 1.0
        if self.symmetry_group == 'Ih' or other.symmetry_group == 'Ih':
            return 0.5
        if self.symmetry_group == 'Td' and other.symmetry_group in ['Oh', 'D3h']:
            return 0.8
        if self.symmetry_group == 'Oh' and other.symmetry_group in ['Td', 'D4h']:
            return 0.8
        if self.symmetry_group in ['D3h', 'D4h', 'C∞v'] and other.symmetry_group in ['D3h', 'D4h', 'C∞v']:
            return 0.7
        return 0.3
    
    def __repr__(self):
        return f"ElementComponent({self.symbol}, Z={self.Z}, pos={self.position.round(1)})"


class VortexFieldSimulator:
    """
    Симулятор поля H на основе TopologicalArchitect.
    """
    
    def __init__(self, grid_size=512):
        self.grid_size = grid_size
        self.architect = TopologicalArchitect(
            grid_shape=(grid_size, grid_size, grid_size),
            interaction_kernel='biharmonic',
            convergence_tolerance=1e-6
        )
        self.components = []
        self.router = AStarRouter()
        
    def load_elements(self, elements_config):
        """Загрузка элементов из конфига"""
        self.components = []
        np.random.seed(42)
        
        for elem_data in elements_config['vortex_components']:
            # Начальное размещение по фрактальной спирали
            position = self._fractal_spiral_placement(elem_data['Z'])
            comp = ElementComponent(elem_data, position)
            self.components.append(comp)
        
        print(f"Загружено {len(self.components)} элементов")
        return self.components
    
    def _fractal_spiral_placement(self, Z):
        """Фрактальное размещение по спирали"""
        golden_angle = 137.508
        r_scale = self.grid_size / 20.0
        
        r = r_scale * np.sqrt(Z)
        theta = np.radians(Z * golden_angle)
        z = (Z - 52) * 2.0
        
        x = r * np.cos(theta) + self.grid_size / 2
        y = r * np.sin(theta) + self.grid_size / 2
        z = z + self.grid_size / 2
        
        return np.array([x, y, z])
    
    def calculate_total_energy(self):
        """Расчёт полной энергии системы вихрей"""
        energy = 0.0
        n = len(self.components)
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(self.components[i].position - self.components[j].position)
                energy += self.components[i].get_interaction_potential(self.components[j], dist)
        
        return energy
    
    def relax(self, iterations=1000, temperature=300.0, pressure=0.1):
        """
        Релаксация системы к минимуму энергии.
        Использует метод градиентного спуска с тепловым шумом.
        """
        print(f"\nРелаксация: T={temperature}K, P={pressure}GPa, итераций={iterations}")
        
        k_thermal = temperature / 300.0  # Нормировка теплового шума
        pressure_factor = 1.0 + pressure / 100.0  # Влияние давления
        
        positions = np.array([c.position for c in self.components])
        charges = np.array([c.charge for c in self.components])
        vortex_numbers = np.array([c.vortex_number for c in self.components])
        
        energy_history = []
        
        for iteration in range(iterations):
            # Вычисляем силы
            forces = np.zeros_like(positions)
            n = len(positions)
            
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    
                    r_vec = positions[i] - positions[j]
                    dist = np.linalg.norm(r_vec)
                    
                    if dist < 1e-6:
                        continue
                    
                    # Кулоновская сила (отталкивание)
                    f_coulomb = charges[i] * charges[j] * r_vec / dist**3
                    
                    # Вихревая сила
                    sym_compat = self.components[i]._symmetry_compatibility(self.components[j])
                    f_vortex = -sym_compat * vortex_numbers[i] * vortex_numbers[j] * r_vec / dist**4
                    
                    # Давление (сжимает систему)
                    f_pressure = -pressure_factor * r_vec / dist**2
                    
                    forces[i] += f_coulomb + f_vortex + f_pressure
            
            # Тепловой шум
            noise = k_thermal * np.random.randn(*positions.shape)
            
            # Обновление позиций
            learning_rate = 0.01 * (1 - iteration / iterations)
            positions += learning_rate * forces + 0.001 * noise
            
            # Граничные условия (отражение от стенок)
            positions = np.clip(positions, 10, self.grid_size - 10)
            
            # Обновляем позиции компонентов
            for i, comp in enumerate(self.components):
                comp.position = positions[i]
            
            # Логирование
            if iteration % 100 == 0:
                energy = self.calculate_total_energy()
                energy_history.append(energy)
                print(f"  Итерация {iteration}: энергия = {energy:.2f}")
        
        # Финальная энергия
        final_energy = self.calculate_total_energy()
        energy_history.append(final_energy)
        
        return {
            'final_energy': final_energy,
            'energy_history': energy_history,
            'positions': positions.tolist()
        }
    
    def find_bonds(self, threshold=0.5):
        """
        Поиск связей (интерметаллидов) между элементами.
        Связь образуется, если потенциал взаимодействия отрицателен
        и расстояние меньше порога.
        """
        bonds = []
        n = len(self.components)
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(self.components[i].position - self.components[j].position)
                potential = self.components[i].get_interaction_potential(self.components[j], dist)
                
                # Порог для образования связи
                threshold_dist = (self.components[i].get_vortex_radius() + 
                                 self.components[j].get_vortex_radius()) * 1.5
                
                if dist < threshold_dist and potential < 0:
                    bond = {
                        'elements': [self.components[i].symbol, self.components[j].symbol],
                        'distance': float(dist),
                        'potential': float(potential),
                        'strength': float(-potential / dist),
                        'predicted_structure': self._predict_structure(self.components[i], self.components[j])
                    }
                    bonds.append(bond)
        
        return bonds
    
    def _predict_structure(self, comp1, comp2):
        """Предсказание кристаллической структуры интерметаллида"""
        sym_compat = comp1._symmetry_compatibility(comp2)
        
        if sym_compat > 0.9:
            return 'B2'
        elif sym_compat > 0.7:
            return 'L1₂' if comp1.vortex_number > comp2.vortex_number else 'L1₀'
        else:
            return 'C14'
    
    def save_results(self, results_dir, bonds, relax_result):
        """Сохранение результатов"""
        os.makedirs(results_dir, exist_ok=True)
        
        # Сохраняем позиции элементов
        elements_output = {
            'metadata': {'model': 'VMMS', 'grid_size': self.grid_size},
            'elements': [
                {
                    'symbol': c.symbol,
                    'Z': c.Z,
                    'position': c.position.tolist(),
                    'symmetry': c.symmetry_group,
                    'vortex_number': c.vortex_number,
                    'electronegativity': c.electronegativity
                }
                for c in self.components
            ]
        }
        with open(os.path.join(results_dir, 'elements_positions.json'), 'w', encoding='utf-8') as f:
            json.dump(elements_output, f, indent=2)
        
        # Сохраняем связи
        bonds_output = {
            'metadata': {'total_bonds': len(bonds)},
            'bonds': bonds
        }
        with open(os.path.join(results_dir, 'bonds_discovered.json'), 'w', encoding='utf-8') as f:
            json.dump(bonds_output, f, indent=2)
        
        # Сохраняем статистику релаксации
        stats_output = {
            'final_energy': relax_result['final_energy'],
            'energy_history': relax_result['energy_history'],
            'total_elements': len(self.components),
            'total_bonds': len(bonds)
        }
        with open(os.path.join(results_dir, 'relaxation_stats.json'), 'w', encoding='utf-8') as f:
            json.dump(stats_output, f, indent=2)
        
        print(f"\nРезультаты сохранены в: {results_dir}")


def main():
    print("=" * 60)
    print("МОДЕЛИРОВАНИЕ 3D ТАБЛИЦЫ МЕНДЕЛЕЕВА НА SPECTRAVORTEX")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Загрузка конфигов
    print("\n[1/4] Загрузка конфигураций...")
    
    def load_json(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    elements_config = load_json(os.path.join(base_dir, 'data', 'field_H_elements_complete.json'))
    process_config = load_json(os.path.join(base_dir, 'configs', 'endogenic_process_config.json'))
    
    print(f"  - Элементов: {len(elements_config['vortex_components'])}")
    
    # Создание симулятора
    print("\n[2/4] Инициализация симулятора...")
    grid_size = process_config['initialization']['grid_size']
    simulator = VortexFieldSimulator(grid_size=grid_size)
    
    # Загрузка элементов
    print("\n[3/4] Загрузка элементов и релаксация...")
    simulator.load_elements(elements_config)
    
    # Релаксация по фазам
    all_bonds = []
    for phase in process_config['relaxation_phases']:
        relax_result = simulator.relax(
            iterations=phase['iterations'],
            temperature=phase['temperature_K'],
            pressure=phase['pressure_GPa']
        )
        
        if phase.get('adaptive_routing', {}).get('enabled', False):
            bonds = simulator.find_bonds(
                threshold=phase['adaptive_routing']['gradient_threshold']
            )
            all_bonds.extend(bonds)
            print(f"    Найдено связей: {len(bonds)}")
    
    # Удаляем дубликаты связей
    unique_bonds = []
    seen = set()
    for bond in all_bonds:
        key = tuple(sorted(bond['elements']))
        if key not in seen:
            seen.add(key)
            unique_bonds.append(bond)
    
    # Сохранение результатов
    print("\n[4/4] Сохранение результатов...")
    results_dir = os.path.join(base_dir, 'results')
    simulator.save_results(results_dir, unique_bonds, relax_result)
    
    # Итоговый отчёт
    print("\n" + "=" * 60)
    print("МОДЕЛИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
    print(f"Элементов: {len(simulator.components)}")
    print(f"Финальная энергия: {relax_result['final_energy']:.2f}")
    print(f"Обнаружено связей: {len(unique_bonds)}")
    
    if unique_bonds:
        print("\nТоп-10 связей по силе:")
        top_bonds = sorted(unique_bonds, key=lambda x: x['strength'], reverse=True)[:10]
        for bond in top_bonds:
            print(f"  {bond['elements'][0]}-{bond['elements'][1]}: "
                  f"d={bond['distance']:.1f}, strength={bond['strength']:.3f}, "
                  f"structure={bond['predicted_structure']}")


if __name__ == "__main__":
    main()