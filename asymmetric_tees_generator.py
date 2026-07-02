#!/usr/bin/env python3
"""
asymmetric_tees_generator.py — Генератор несимметричной TEES-поверхности
=========================================================================
v44: Создание несимметричной TEES для варп-двигателя.

Принцип:
  Каждая сущность УЖЕ имеет TEES (свою поверхность).
  Задача — сделать эту поверхность НЕСИММЕТРИЧНОЙ через градиенты:
  
  1. Grid-градиент: мелкий grid спереди → крупный сзади (геометрическое сжатие)
  2. Фазовый градиент: высокая фаза спереди → низкая сзади (темпоральный клин)
  3. Nu-градиент: высокая вязкость спереди → низкая сзади (жёсткость пространства)

  Комбинация трёх градиентов = варп-пузырь!

Ключевые компоненты (из проекта):
  - generate_field_from_address (v25+)
  - apply_vortex_transition (v25+)
  - IntersectionHorizonDetector (v41.1)
  - TransitionDiagnostics (v25+)
  - Адаптивная геометрия через градиенты параметров (НОВОЕ)
"""

import sys, time, hashlib, struct
import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Dict
from collections import deque

# Импорт из проекта
try:
    from tees_biharmonic_v41_1 import (
        generate_field_from_address,
        apply_vortex_transition,
        TEESConfig,
        IntersectionHorizonDetector,
        TransitionDiagnostics,
        FieldSensors
    )
    HAS_TEES = True
    _DETECTOR = IntersectionHorizonDetector(n_peaks=15, min_stability=0.0)
    print("[OK] TEES v41.1 загружен")
except ImportError:
    HAS_TEES = False
    _DETECTOR = None
    print("[WARN] TEES не найден. Будет использован упрощённый режим.")

# ============================================================================
# НЕСИММЕТРИЧНАЯ TEES: ГРАДИЕНТЫ
# ============================================================================

@dataclass
class AsymmetricTEES:
    """Несимметричная TEES-поверхность с градиентами"""
    
    # Поля
    field_initial: np.ndarray      # Исходное поле (симметричная TEES)
    field_asymmetric: np.ndarray   # Несимметричное поле
    field_transitioned: np.ndarray # После вихревого перехода
    tees_surface: np.ndarray       # Разность = TEES-поверхность
    
    # Параметры асимметрии
    N_front: int                   # Топологический заряд спереди
    N_rear: int                    # Топологический заряд сзади
    gradient_type: str             # Тип градиента
    
    # Метрики
    consistency: float = 0.0       # Качество TEES
    convergence: float = 0.0       # Стабильность (из horizon scan)
    ratio_mean: float = 0.0        # Средний ratio вдоль поверхности
    asymmetry_index: float = 0.0   # Индекс асимметрии (0 = симметрично, 1 = макс)
    
    def __repr__(self):
        return (f"AsymmetricTEES(N_front={self.N_front}, N_rear={self.N_rear}, "
                f"gradient={self.gradient_type}, asym={self.asymmetry_index:.2f}, "
                f"cons={self.consistency:.3f})")


class AsymmetricTEESGenerator:
    """
    Генератор несимметричных TEES-поверхностей.
    
    Три метода создания асимметрии:
    1. grid_gradient — геометрическое сжатие/расширение
    2. phase_gradient — темпоральный клин
    3. nu_gradient — градиент жёсткости пространства
    4. combined_gradient — все три вместе (варп-пузырь!)
    """
    
    def __init__(self, seed: str = "warp_drive", base_grid: int = 64):
        self.seed = seed
        self.base_grid = base_grid
        self.detector = _DETECTOR
        self.generated_tees: List[AsymmetricTEES] = []
    
    # ─── 1. GRID-ГРАДИЕНТ ───
    def grid_gradient(self, N_front: int = 10, N_rear: int = 2) -> AsymmetricTEES:
        """
        Несимметричная TEES через градиент grid.
        
        Перед: мелкий grid (высокое разрешение) → сжатие пространства.
        Зад:   крупный grid (низкое разрешение) → расширение пространства.
        """
        gs = self.base_grid
        
        # Градиент grid от мелкого (перед) к крупному (зад)
        grid_values = np.linspace(N_front * 10, N_rear * 10, gs, dtype=int)
        grid_values = np.clip(grid_values, 16, 128)
        
        # Создаём поле с градиентом grid
        asymmetric_field = np.zeros((gs, gs))
        
        for i, local_grid in enumerate(grid_values):
            local_config = TEESConfig(
                grid_size=int(local_grid),
                nu_true=0.15,
                gamma_true=2.0,
                dt=4.0
            )
            local_field = generate_field_from_address(
                f"{self.seed}_grid_{i}", local_config
            )
            # Отображаем на общую сетку (интерполяция)
            src_size = local_field.shape[0]
            idx = np.linspace(0, src_size-1, gs).astype(int)
            asymmetric_field[i, :] = local_field[0, idx]
        
        return self._finalize_tees(asymmetric_field, N_front, N_rear, "grid")
    
    # ─── 2. ФАЗОВЫЙ ГРАДИЕНТ ───
    def phase_gradient(self, N_front: int = 10, N_rear: int = 2) -> AsymmetricTEES:
        """
        Несимметричная TEES через градиент фазы.
        
        Высокая фаза спереди → "ускоренное" время.
        Низкая фаза сзади → "замедленное" время.
        Разность фаз = темпоральный клин!
        """
        gs = self.base_grid
        config = TEESConfig(grid_size=gs, nu_true=0.15, gamma_true=2.0, dt=4.0)
        
        # Симметричное поле
        base_field = generate_field_from_address(self.seed, config)
        
        # Применяем фазовый градиент
        phase_values = np.linspace(
            2 * np.pi * N_front / 10,
            2 * np.pi * N_rear / 10,
            gs
        )
        
        asymmetric_field = base_field.copy().astype(complex)
        for i, phase in enumerate(phase_values):
            asymmetric_field[i, :] *= np.exp(1j * phase)
        
        asymmetric_field = np.real(asymmetric_field)
        return self._finalize_tees(asymmetric_field, N_front, N_rear, "phase")
    
    # ─── 3. NU-ГРАДИЕНТ (вязкость) ───
    def viscosity_gradient(self, N_front: int = 10, N_rear: int = 2) -> AsymmetricTEES:
        """
        Несимметричная TEES через градиент вязкости nu.
        
        Высокая вязкость спереди → "жёсткое" пространство (сжатие).
        Низкая вязкость сзади → "мягкое" пространство (расширение).
        """
        gs = self.base_grid
        config = TEESConfig(grid_size=gs, nu_true=0.15, gamma_true=2.0, dt=4.0)
        
        # Симметричное поле
        base_field = generate_field_from_address(self.seed, config)
        
        # Применяем градиент вязкости
        nu_values = np.linspace(0.5/N_front, 0.5/N_rear, gs)
        
        asymmetric_field = base_field.copy()
        for i, nu in enumerate(nu_values):
            # Нелинейная модуляция: высокая вязкость сглаживает поле
            asymmetric_field[i, :] *= np.exp(-nu * asymmetric_field[i, :]**2)
        
        return self._finalize_tees(asymmetric_field, N_front, N_rear, "viscosity")
    
    # ─── 4. КОМБИНИРОВАННЫЙ ГРАДИЕНТ (варп-пузырь!) ───
    def warp_bubble(self, N_front: int = 10, N_rear: int = 2) -> AsymmetricTEES:
        """
        Полноценный варп-пузырь: ВСЕ ТРИ ГРАДИЕНТА ВМЕСТЕ!
        
        Grid + Phase + Nu → максимальная асимметрия → варп-двигатель!
        """
        gs = self.base_grid
        asymmetric_field = np.zeros((gs, gs))
        
        # Градиенты вдоль оси движения
        t_values = np.linspace(0, 1, gs)  # 0 = зад, 1 = перед
        
        for i in range(gs):
            t = t_values[i]
            
            # Интерполяция N
            N_local = N_rear + (N_front - N_rear) * t
            
            # 1. GRID градиент
            local_grid = int(np.clip(30 + N_local * 10, 16, 128))
            
            # 2. NU градиент
            local_nu = np.clip(0.5 / max(1, N_local), 0.01, 0.5)
            
            # 3. PHASE градиент
            local_phase = 2 * np.pi * N_local / 10
            
            # Генерируем локальное поле
            local_config = TEESConfig(
                grid_size=local_grid,
                nu_true=local_nu,
                gamma_true=2.0,
                dt=N_local * 0.5
            )
            local_field = generate_field_from_address(
                f"{self.seed}_warp_{i}", local_config
            )
            
            # Отображаем и применяем фазу
            src_size = local_field.shape[0]
            idx = np.linspace(0, src_size-1, gs).astype(int)
            asymmetric_field[i, :] = local_field[0, idx] * np.cos(local_phase)
        
        return self._finalize_tees(asymmetric_field, N_front, N_rear, "warp_bubble")
    
    # ─── ОБЩИЙ МЕТОД ФИНАЛИЗАЦИИ ───
    def _finalize_tees(self, asymmetric_field, N_front, N_rear, gradient_type):
        """Общая часть для всех градиентов: переход + метрики"""
        
        config = TEESConfig(
            grid_size=self.base_grid,
            nu_true=0.15,
            gamma_true=2.0,
            dt=4.0
        )
        
        # Симметричное поле для сравнения
        field_initial = generate_field_from_address(self.seed, config)
        
        # Вихревой переход
        field_transitioned = apply_vortex_transition(asymmetric_field, config)
        
        # TEES-поверхность = разность
        tees_surface = field_transitioned - asymmetric_field
        
        # Метрики через horizon scan
        consistency = 0.0
        convergence = 0.0
        ratio_mean = 0.0
        
        if HAS_TEES and self.detector:
            try:
                intersections = self.detector.find_intersections(
                    asymmetric_field, field_transitioned, config
                )
                if intersections:
                    convergence = float(intersections[0].convergence)
                    ratio_mean = float(np.mean([i.ratio for i in intersections[:5]]))
                    # Consistency через диагностику
                    diag = TransitionDiagnostics(asymmetric_field, field_transitioned, config)
                    state = diag.compute_all()
                    consistency = state.get('consistency', 0.0)
            except Exception:
                pass
        
        # Индекс асимметрии
        asymmetry_index = self._compute_asymmetry(tees_surface)
        
        tees = AsymmetricTEES(
            field_initial=field_initial,
            field_asymmetric=asymmetric_field,
            field_transitioned=field_transitioned,
            tees_surface=tees_surface,
            N_front=N_front,
            N_rear=N_rear,
            gradient_type=gradient_type,
            consistency=consistency,
            convergence=convergence,
            ratio_mean=ratio_mean,
            asymmetry_index=asymmetry_index
        )
        
        self.generated_tees.append(tees)
        return tees
    
    def _compute_asymmetry(self, tees_surface: np.ndarray) -> float:
        """
        Вычислить индекс асимметрии TEES-поверхности.
        0 = полностью симметрична, 1 = максимально асимметрична.
        """
        gs = tees_surface.shape[0]
        
        # Сравниваем переднюю и заднюю части
        front = tees_surface[:gs//4, :]   # Передняя четверть
        rear = tees_surface[3*gs//4:, :]  # Задняя четверть
        
        # Различие в энергии между передом и задом
        front_energy = np.mean(np.abs(front))
        rear_energy = np.mean(np.abs(rear))
        
        if front_energy + rear_energy > 0:
            asymmetry = abs(front_energy - rear_energy) / (front_energy + rear_energy)
        else:
            asymmetry = 0.0
        
        return float(asymmetry)
    
    def compare_all_methods(self, N_front=10, N_rear=2) -> Dict[str, AsymmetricTEES]:
        """Сравнить все методы генерации несимметричной TEES"""
        results = {}
        
        print(f"\n  [GRID GRADIENT] Создаю TEES с градиентом grid...")
        results['grid'] = self.grid_gradient(N_front, N_rear)
        print(f"    Асимметрия={results['grid'].asymmetry_index:.3f}, "
              f"Consistency={results['grid'].consistency:.3f}")
        
        print(f"\n  [PHASE GRADIENT] Создаю TEES с градиентом фазы...")
        results['phase'] = self.phase_gradient(N_front, N_rear)
        print(f"    Асимметрия={results['phase'].asymmetry_index:.3f}, "
              f"Consistency={results['phase'].consistency:.3f}")
        
        print(f"\n  [VISCOSITY GRADIENT] Создаю TEES с градиентом вязкости...")
        results['viscosity'] = self.viscosity_gradient(N_front, N_rear)
        print(f"    Асимметрия={results['viscosity'].asymmetry_index:.3f}, "
              f"Consistency={results['viscosity'].asymmetry_index:.3f}")
        
        print(f"\n  [WARP BUBBLE] Создаю комбинированный варп-пузырь...")
        results['warp_bubble'] = self.warp_bubble(N_front, N_rear)
        print(f"    Асимметрия={results['warp_bubble'].asymmetry_index:.3f}, "
              f"Consistency={results['warp_bubble'].consistency:.3f}")
        
        return results
    
    def report(self):
        """Отчёт о всех сгенерированных TEES"""
        print(f"\n{'='*70}")
        print(f"  ОТЧЁТ: Сгенерировано {len(self.generated_tees)} TEES-поверхностей")
        print(f"{'='*70}")
        print(f"  {'Тип':<15} {'N_front':<10} {'N_rear':<10} {'Асимметрия':<12} {'Cons':<10} {'Conv':<10}")
        print(f"  {'─'*70}")
        
        for tees in self.generated_tees:
            print(f"  {tees.gradient_type:<15} {tees.N_front:<10} {tees.N_rear:<10} "
                  f"{tees.asymmetry_index:<12.3f} {tees.consistency:<10.3f} {tees.convergence:<10.3f}")

# ============================================================================
# ДЕМОНСТРАЦИЯ
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("  ASYMMETRIC TEES GENERATOR v44")
    print("  Создание несимметричных TEES-поверхностей")
    print("=" * 70)
    
    generator = AsymmetricTEESGenerator(seed="enterprise_ncc_1701")
    
    # Сравниваем все методы
    results = generator.compare_all_methods(N_front=10, N_rear=2)
    
    # Отчёт
    generator.report()
    
    # Какой метод лучше?
    print(f"\n{'='*70}")
    print(f"  ИТОГИ СРАВНЕНИЯ:")
    
    best_asymmetry = max(results, key=lambda k: results[k].asymmetry_index)
    best_consistency = max(results, key=lambda k: results[k].consistency)
    
    print(f"  Максимальная асимметрия: {best_asymmetry} ({results[best_asymmetry].asymmetry_index:.3f})")
    print(f"  Максимальная consistency: {best_consistency} ({results[best_consistency].consistency:.3f})")
    
    if best_asymmetry == best_consistency:
        print(f"\n  ✅ {best_asymmetry.upper()} — лучший метод для варп-двигателя!")
    else:
        print(f"\n  💡 Рекомендация: WARP_BUBBLE (комбинация всех градиентов)")
    
    print(f"\n  Следующий шаг: запустить asymmetric_tees_generator.warp_bubble(N=10,2)")
    print(f"  и скормить результат в IntersectionHorizonDetector для точной настройки!")
    print(f"{'='*70}")