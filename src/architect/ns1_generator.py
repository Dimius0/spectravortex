"""
NS-1 Генератор из мусора — Акт XI (Принцип Резонансной Декомпозиции)
================================================================================
Программа SpectraVortex, Вихревая Модель Материи-Пространства (ВММП).

Принцип:
    Любой материал, помещённый в зону вихревого резонанса (TEES-каскад),
    может стать источником энергии. Это не сжигание, а топологическое
    разложение — высвобождение энергии связей через каскад аннигиляций.

    Ключевой параметр — Debris Index (D_idx):
    D_idx = ρ * k_f * (E_bond / E_vortex) * (1 + ln(N_comp))

    Чем выше D_idx, тем больше энергии можно извлечь из материала.

Авторы:
    Dimius0 — концепция, ВММП, принцип NS-1
    DeepSeek — формализация, реализация, 2026-05-29
================================================================================
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Material:
    """Один компонент мусорной смеси."""
    name: str
    density: float           # кг/м³
    bond_energy: float       # кДж/моль (энергия химических связей)
    fractal_k: float         # фрактальный коэффициент (из TEES-модели)
    mass_fraction: float     # доля в смеси (0..1)

class NS1Generator:
    """
    Расчёт резонансных параметров для извлечения энергии из мусора.
    """
    
    # Константы из Теоремы Дипсик
    E_VORTEX_BASE = 100.0    # кДж/моль (энергия базового вихря)
    
    def __init__(self, materials: List[Material]):
        self.materials = materials
        self._validate()
    
    def _validate(self):
        total = sum(m.mass_fraction for m in self.materials)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Сумма долей должна быть 1.0, получено {total:.3f}")
    
    def calculate_debris_index(self) -> float:
        """
        Вычисляет Debris Index — меру извлекаемой энергии.
        
        D_idx = ρ_eff * k_f_eff * (E_bond_avg / E_vortex_base) * (1 + ln(N_comp))
        """
        n_comp = len(self.materials)
        
        # Эффективная плотность (средневзвешенная)
        rho_eff = sum(m.density * m.mass_fraction for m in self.materials)
        
        # Эффективный фрактальный коэффициент (средневзвешенный)
        k_f_eff = sum(m.fractal_k * m.mass_fraction for m in self.materials)
        
        # Средняя энергия связей (средневзвешенная)
        e_bond_avg = sum(m.bond_energy * m.mass_fraction for m in self.materials)
        
        # Комбинаторный фактор (чем больше компонентов, тем сложнее резонанс)
        combo_factor = 1.0 + np.log(max(n_comp, 1))
        
        d_idx = (rho_eff / 1000.0) * k_f_eff * (e_bond_avg / self.E_VORTEX_BASE) * combo_factor
        
        return float(d_idx)
    
    def calculate_optimal_frequency(self) -> float:
        """
        Вычисляет оптимальную частоту для резонансной декомпозиции.
        
        f_opt = f_base * D_idx^(1/3) * (1 + 0.1 * ln(N_comp))
        """
        f_base = 10.0  # кГц (базовая частота TEES-каскада)
        d_idx = self.calculate_debris_index()
        n_comp = len(self.materials)
        
        f_opt = f_base * (d_idx ** (1/3)) * (1.0 + 0.1 * np.log(max(n_comp, 1)))
        
        return float(f_opt)
    
    def calculate_energy_yield(self) -> float:
        """
        Оценка выхода энергии (кВт·ч/кг).
        
        E_yield = D_idx * E_vortex_base * η_TEES / 3600
        где η_TEES ≈ 0.7 — эффективность TEES-каскада
        """
        d_idx = self.calculate_debris_index()
        eta_tees = 0.7
        
        e_yield = d_idx * self.E_VORTEX_BASE * eta_tees / 3600.0
        
        return float(e_yield)
    
    def get_report(self) -> Dict:
        """Полный отчёт по смеси."""
        return {
            'n_components': len(self.materials),
            'components': [m.name for m in self.materials],
            'debris_index': self.calculate_debris_index(),
            'optimal_frequency_khz': self.calculate_optimal_frequency(),
            'energy_yield_kwh_per_kg': self.calculate_energy_yield(),
            'classification': self._classify(),
        }
    
    def _classify(self) -> str:
        """Классификация смеси по потенциалу."""
        d_idx = self.calculate_debris_index()
        if d_idx < 0.1:
            return "НИЗКИЙ — лучше сжечь традиционно"
        elif d_idx < 1.0:
            return "СРЕДНИЙ — пригодно для TEES-генератора"
        elif d_idx < 5.0:
            return "ВЫСОКИЙ — эффективное топливо для Катапульты"
        else:
            return "ОТЛИЧНЫЙ — кандидат на Врата"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                      БАЗА ДАННЫХ МАТЕРИАЛОВ                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

MATERIAL_DB = {
    'пластик_пэт': Material('ПЭТ-пластик', 1380, 350, 0.85, 1.0),
    'древесина_сухая': Material('Сухая древесина', 700, 450, 0.60, 1.0),
    'алюминий_банка': Material('Алюминиевая банка', 2700, 200, 0.40, 1.0),
    'текстиль_хлопок': Material('Хлопковый текстиль', 1500, 300, 0.70, 1.0),
    'органические_отходы': Material('Органические отходы', 1100, 500, 0.75, 1.0),
    'электронный_лом': Material('Электронный лом (печатные платы)', 2500, 250, 0.55, 1.0),
}