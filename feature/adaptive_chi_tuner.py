"""
Адаптивный тюнер электроотрицательности на основе ПИД-регулятора.
"""

import json
import numpy as np
from typing import Dict, List, Optional
from pid_controller import PIDController, PIDConfig

class AdaptiveChiTuner:
    """
    Управляет адаптивной настройкой электроотрицательности для всех элементов.
    """
    
    def __init__(self, elements_config_path: str):
        with open(elements_config_path, 'r', encoding='utf-8') as f:
            self.elements_config = json.load(f)
        
        self.controllers: Dict[str, PIDController] = {}
        self.current_chi: Dict[str, float] = {}
        self.local_energies: Dict[str, List[float]] = {}
        
        # Инициализация регуляторов
        self._init_controllers()
    
    def _init_controllers(self):
        """Создать ПИД-регулятор для каждого элемента (все 103)"""
        # Собираем ВСЕ элементы из конфига
        all_elements = []
        for elem in self.elements_config['vortex_components']:
            all_elements.append(elem.copy())
    
        # Добавляем фрактально-генерируемые элементы Z=32-103
        base_elements = {e['Z']: e for e in self.elements_config['vortex_components']}
        for z in range(1, 104):
            if z not in base_elements:
                group = ((z - 1) % 18) + 1
                for base_z, base_elem in base_elements.items():
                    if ((base_z - 1) % 18) + 1 == group:
                        base_elements[z] = base_elem
                        break
                if z not in base_elements:
                    base_elements[z] = base_elements[1]
    
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
    
        for Z in range(1, 104):
            symbol = symbols.get(Z, f'Z{Z}')
            base = base_elements.get(Z, base_elements[1])
        
            # Начальное значение χ
            if Z <= 31:
                initial_chi = base.get('electronegativity', 1.0)
            else:
                # Для Z>31 масштабируем по периоду
                period = (Z - 1) // 18 + 1
                initial_chi = base.get('electronegativity', 1.0) * (0.9 ** (period - 1))
        
            # Конфигурация регулятора зависит от Z
            config = PIDConfig(
                Kp=0.05 + 0.01 * (Z / 10),
                Ki=0.005,
                Kd=0.02,
                setpoint=0.0,
                output_min=0.1,
                output_max=4.5,
                buffer_size=30
            )
        
            self.controllers[symbol] = PIDController(f"chi_{symbol}", config)
            self.current_chi[symbol] = initial_chi
            self.local_energies[symbol] = []
    
    def update_local_energy(self, symbol: str, energy: float):
        """Сохранить локальную энергию для элемента"""
        self.local_energies[symbol].append(energy)
    
    def tune_all(self, dt: float = 1.0) -> Dict[str, float]:
        """
        Выполнить один шаг настройки для всех элементов.
        Возвращает словарь с новыми значениями χ.
        """
        new_chi = {}
        
        for symbol, controller in self.controllers.items():
            if len(self.local_energies[symbol]) > 0:
                # Используем среднюю энергию за последние шаги
                recent_energies = self.local_energies[symbol][-10:]
                current_energy = np.mean(recent_energies) if recent_energies else 0.0
                
                # Обновляем регулятор
                new_value = controller.update(current_energy, dt)
                new_chi[symbol] = new_value
                self.current_chi[symbol] = new_value
            else:
                new_chi[symbol] = self.current_chi[symbol]
        
        return new_chi
    
    def get_current_chi(self, symbol: str) -> float:
        """Получить текущее значение χ для элемента"""
        return self.current_chi.get(symbol, 1.0)
    
    def get_all_chi(self) -> Dict[str, float]:
        """Получить текущие значения χ для всех элементов"""
        return self.current_chi.copy()
    
    def compute_local_energy(self, 
                             element_position: np.ndarray,
                             all_positions: List[np.ndarray],
                             all_charges: List[float]) -> float:
        """
        Вычислить локальную энергию вихря на основе его окружения.
        """
        energy = 0.0
        for pos, charge in zip(all_positions, all_charges):
            dist = np.linalg.norm(element_position - pos)
            if dist > 1e-6:
                # Кулоновское отталкивание
                energy += charge / dist
                # Вихревое притяжение (упрощённо)
                energy -= 0.5 * charge / (dist ** 1.5)
        return energy
    
    def save_results(self, output_path: str):
        """Сохранить результаты настройки"""
        results = {
            'metadata': {
                'description': 'Adaptive χ values tuned by PID controllers',
                'total_elements': len(self.controllers)
            },
            'chi_values': self.current_chi,
            'statistics': {
                symbol: ctrl.get_stats() for symbol, ctrl in self.controllers.items()
            }
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"✓ Результаты сохранены: {output_path}")
    
    def print_summary(self):
        """Вывести сводку по настройке"""
        print("\n" + "=" * 60)
        print("СВОДКА АДАПТИВНОЙ НАСТРОЙКИ χ")
        print("=" * 60)
        print(f"{'Символ':>6} | {'χ_нач':>8} | {'χ_кон':>8} | {'Δχ':>8} | {'Шагов':>6}")
        print("-" * 60)
        
        for symbol, ctrl in self.controllers.items():
            if ctrl.history:
                initial = ctrl.history[0]['output']
                final = ctrl.output
                delta = final - initial
                print(f"{symbol:>6} | {initial:8.3f} | {final:8.3f} | {delta:+8.3f} | {ctrl.step_count:6}")
        
        print("=" * 60)