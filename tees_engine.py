#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_engine.py — TEES-движок SpectraVortex v4.0
Турбулентность = фрактальные вложенные ламинарные потоки 
                 с TEES/ВММП обменными поверхностями.
Автор: Dimius0, DeepSeek
Дата: 2026-07-22
Лицензия: MIT
"""

import numpy as np
from typing import Tuple, List, Optional, Dict, Set
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

from core.tees_core import (
    get_charge, get_shift, validate_triple,
    TeesValidator, CoreConfig
)


# ============================================
# БАЗОВЫЕ СТРУКТУРЫ
# ============================================

class FlowScale(Enum):
    """Уровни фрактальной иерархии потоков."""
    MACRO = "macro"    # Крупные вихревые структуры
    MESO = "meso"      # Средние ламинарные слои
    MICRO = "micro"    # Микро-обменные поверхности


@dataclass
class CurvatureMode:
    """Одна мода кривизны ламинарного потока."""
    charge: float
    frequency: float
    phase: float
    direction: np.ndarray  # Вектор направления потока


@dataclass
class LaminarFlow:
    """
    Фрактально-вложенный ламинарный поток.
    НЕ хаотический — криволинейный, детерминированный.
    """
    seed_word: str
    depth: int
    scale: float
    position: Tuple[int, int, int]  # Центр потока в сетке
    
    # Кривизна потока (детерминированная, не случайная)
    curvature_modes: List[CurvatureMode] = field(default_factory=list)
    curvature_field: Optional[np.ndarray] = None
    
    # Иерархия вложенности
    parent: Optional['LaminarFlow'] = None
    children: List['LaminarFlow'] = field(default_factory=list)
    
    # Обменные поверхности с соседями того же уровня
    exchange_surfaces: List['ExchangeSurface'] = field(default_factory=list)
    
    # Метаданные
    total_charge: float = 0.0
    information_density: float = 0.0


@dataclass
class ExchangeSurface:
    """
    TEES/ВММП обменная поверхность между ламинарными потоками.
    Это ГРАНИЦА РАЗДЕЛА с информационным обменом, а не шум.
    """
    flow_a: LaminarFlow
    flow_b: LaminarFlow
    exchange_type: str  # "macro-macro", "macro-meso", "meso-micro", etc.
    
    # Геометрия поверхности раздела
    curvature_tensor: Optional[np.ndarray] = None
    normal_field: Optional[np.ndarray] = None
    
    # Характеристики обмена
    charge_gradient: float = 0.0
    tees_shift: float = 0.0
    information_flux: float = 0.0
    
    # Поле градиента (для синтеза)
    gradient_field: Optional[np.ndarray] = None


@dataclass
class TEESFlowState:
    """Состояние TEES-потокового поля."""
    field: np.ndarray
    macro_flows: List[LaminarFlow]
    meso_flows: List[LaminarFlow]
    micro_flows: List[LaminarFlow]
    exchange_surfaces: List[ExchangeSurface]
    
    # Метрики
    total_information: float
    total_exchange_flux: float
    curvature_energy: float
    
    timestamp: int


# ============================================
# ГЕНЕРАТОР КРИВИЗНЫ
# ============================================

class CurvatureGenerator:
    """
    Генерирует криволинейные структуры ламинарных потоков.
    Кривизна детерминирована TEES-грамматикой, а не случайностью.
    """
    
    def __init__(self, grid_shape: Tuple[int, int, int]):
        self.grid_shape = grid_shape
        
        # Предвычисленные координатные сетки
        self._init_coordinate_grids()
    
    def _init_coordinate_grids(self):
        """Инициализирует координатные сетки для генерации мод."""
        x = np.linspace(0, 2*np.pi, self.grid_shape[0])
        y = np.linspace(0, 2*np.pi, self.grid_shape[1])
        z = np.linspace(0, 2*np.pi, self.grid_shape[2])
        
        self.X, self.Y, self.Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Альтернативные координаты для разных типов потоков
        self.R = np.sqrt(self.X**2 + self.Y**2)  # Радиальные
        self.Theta = np.arctan2(self.Y, self.X)   # Угловые
        self.Z_spiral = self.Z + self.Theta * 0.3  # Спиральные
    
    def generate_word_curvature(self, word: str, flow_position: Tuple[int, int, int]) -> List[CurvatureMode]:
        """
        Генерирует моды кривизны из TEES-структуры слова.
        Каждая фонема → одна мода кривизны.
        """
        modes = []
        
        for i, char in enumerate(word):
            charge = get_charge(char)
            
            # Частота зависит от позиции в слове (фрактальное масштабирование)
            frequency = (i + 1) / len(word)
            
            # Фаза от TEES-сдвига с предыдущим символом
            if i > 0:
                shift = get_shift(word[i-1], char)
                phase = shift * np.pi
            else:
                phase = 0.0
            
            # Направление потока от позиции в сетке
            direction = self._compute_flow_direction(flow_position, i, len(word))
            
            mode = CurvatureMode(
                charge=charge,
                frequency=frequency,
                phase=phase,
                direction=direction
            )
            modes.append(mode)
        
        return modes
    
    def _compute_flow_direction(self, position: Tuple[int, int, int], 
                                 char_index: int, word_length: int) -> np.ndarray:
        """Вычисляет направление потока из позиции и TEES-структуры."""
        # Базовое направление от центра сетки
        center = np.array(self.grid_shape) / 2
        pos = np.array(position)
        base_dir = pos - center
        
        if np.linalg.norm(base_dir) < 1e-6:
            base_dir = np.array([1.0, 0.0, 0.0])
        
        base_dir = base_dir / np.linalg.norm(base_dir)
        
        # Вращение от позиции символа в слове
        angle = 2 * np.pi * char_index / word_length
        
        # Матрица поворота вокруг оси Z
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        rotation = np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])
        
        return rotation @ base_dir
    
    def compute_curvature_field(self, modes: List[CurvatureMode], 
                                flow_center: Tuple[int, int, int],
                                scale: float) -> np.ndarray:
        """
        Вычисляет поле кривизны из мод.
        Суперпозиция криволинейных структур, а не случайных флуктуаций.
        """
        field = np.zeros(self.grid_shape)
        
        # Смещение координат к центру потока
        cx, cy, cz = flow_center
        
        for mode in modes:
            # Пространственная модуляция с учетом направления потока
            dx, dy, dz = mode.direction
            
            # Криволинейная аргументная функция
            arg = (self.X - cx) * dx * mode.frequency + \
                  (self.Y - cy) * dy * mode.frequency * 1.5 + \
                  (self.Z - cz) * dz * mode.frequency * 0.7 + \
                  mode.phase
            
            # Нелинейная кривизна (не просто синус — TEES-структура)
            curvature = mode.charge * (
                np.sin(arg) + 
                0.3 * np.sin(2 * arg) +  # Вторая гармоника
                0.1 * np.sin(3 * arg)    # Третья гармоника (фрактально)
            )
            
            # Пространственное затухание от центра потока
            distance = np.sqrt((self.X - cx)**2 + (self.Y - cy)**2 + (self.Z - cz)**2)
            envelope = np.exp(-distance * scale * 0.1)
            
            field += curvature * envelope
        
        return field


# ============================================
# ГЕНЕРАТОР ОБМЕННЫХ ПОВЕРХНОСТЕЙ
# ============================================

class ExchangeSurfaceGenerator:
    """
    Генерирует TEES/ВММП обменные поверхности между потоками.
    """
    
    def __init__(self, grid_shape: Tuple[int, int, int]):
        self.grid_shape = grid_shape
    
    def create_surface(self, flow_a: LaminarFlow, flow_b: LaminarFlow, 
                       exchange_type: str) -> ExchangeSurface:
        """Создает обменную поверхность между двумя потоками."""
        
        # Градиент заряда между потоками
        charge_gradient = flow_a.total_charge - flow_b.total_charge
        
        # TEES-сдвиг между словами-носителями
        tees_shift = get_shift(flow_a.seed_word, flow_b.seed_word)
        
        # Информационный поток через поверхность
        information_flux = charge_gradient * tees_shift
        
        # Геометрия поверхности раздела
        normal_field = self._compute_normal_field(flow_a, flow_b)
        
        # Поле градиента для синтеза
        gradient_field = self._compute_gradient_field(
            flow_a, flow_b, charge_gradient, information_flux
        )
        
        return ExchangeSurface(
            flow_a=flow_a,
            flow_b=flow_b,
            exchange_type=exchange_type,
            normal_field=normal_field,
            charge_gradient=charge_gradient,
            tees_shift=tees_shift,
            information_flux=information_flux,
            gradient_field=gradient_field
        )
    
    def _compute_normal_field(self, flow_a: LaminarFlow, 
                              flow_b: LaminarFlow) -> np.ndarray:
        """
        Вычисляет поле нормалей к поверхности раздела.
        Поверхность проходит посередине между центрами потоков.
        """
        # Вектор между центрами потоков
        center_a = np.array(flow_a.position)
        center_b = np.array(flow_b.position)
        direction = center_b - center_a
        
        if np.linalg.norm(direction) < 1e-6:
            direction = np.array([1.0, 0.0, 0.0])
        
        direction = direction / np.linalg.norm(direction)
        
        # Создаем поле нормалей (постоянное для простоты)
        normal_field = np.tile(direction, self.grid_shape + (1,))
        
        return normal_field
    
    def _compute_gradient_field(self, flow_a: LaminarFlow, flow_b: LaminarFlow,
                                charge_gradient: float, flux: float) -> np.ndarray:
        """
        Вычисляет поле градиента на обменной поверхности.
        Это НЕ шум — это направленный перенос информации.
        """
        # Координаты
        x = np.linspace(0, 2*np.pi, self.grid_shape[0])
        y = np.linspace(0, 2*np.pi, self.grid_shape[1])
        z = np.linspace(0, 2*np.pi, self.grid_shape[2])
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Позиция поверхности (посередине между центрами)
        mid_point = (np.array(flow_a.position) + np.array(flow_b.position)) / 2
        
        # Расстояние до поверхности раздела
        distance = np.sqrt((X - mid_point[0])**2 + 
                          (Y - mid_point[1])**2 + 
                          (Z - mid_point[2])**2)
        
        # Градиентное поле: максимально на поверхности, затухает в стороны
        sigma = 2.0  # Толщина поверхности
        gradient = flux * charge_gradient * np.exp(-distance**2 / (2 * sigma**2))
        
        # Добавляем TEES-структуру (не синус — фрактальный паттерн)
        tees_pattern = (
            np.sin(X * 0.5 + Y * 0.3) * 
            np.cos(Z * 0.7 + X * 0.2) * 
            np.sin(Y * 0.6 - Z * 0.4)
        )
        
        gradient *= (1.0 + 0.3 * tees_pattern)
        
        return gradient


# ============================================
# ОСНОВНОЙ ДВИЖОК TEES-ТУРБУЛЕНТНОСТИ
# ============================================

class TEESEngine:
    """
    Движок TEES-турбулентности v4.0.
    
    Турбулентность = фрактальные вложенные ламинарные потоки 
                     с TEES/ВММП обменными поверхностями.
    
    Заменяет np.random.randn() на иерархическую систему потоков.
    """
    
    def __init__(self, 
                 shape: Tuple[int, int, int],
                 fractal_depth: int = 3,
                 memory_depth: int = 10,
                 seed_words: List[str] = None):
        """
        Инициализация TEES-движка.
        
        Args:
            shape: размерность поля (nx, ny, nz)
            fractal_depth: глубина фрактальной вложенности (1-5)
            memory_depth: глубина памяти состояний
            seed_words: слова-триггеры для генерации потоков
        """
        self.shape = shape
        self.fractal_depth = min(fractal_depth, 5)  # Ограничиваем глубину
        self.memory_depth = memory_depth
        self.seed_words = seed_words or [
            "vortex", "turbulence", "quantum", "space", "time",
            "resonance", "field", "energy", "matter", "consciousness"
        ]
        
        # Генераторы
        self.curvature_gen = CurvatureGenerator(shape)
        self.surface_gen = ExchangeSurfaceGenerator(shape)
        
        # Память состояний
        self.history = deque(maxlen=memory_depth)
        self.current_state: Optional[TEESFlowState] = None
        
        # Счетчик шагов
        self.step = 0
        
        # События высокой информации (вместо отбрасывания)
        self.high_information_events = deque(maxlen=100)
        
        # Статистика потоков (не шума!)
        self.stats = {
            'generations': 0,
            'total_flows': [],
            'exchange_fluxes': [],
            'curvature_energies': [],
            'information_transfers': []
        }
        
        print(f"[TEES-ENGINE v4.0] Инициализирован")
        print(f"  shape: {shape}")
        print(f"  fractal_depth: {fractal_depth}")
        print(f"  memory_depth: {memory_depth}")
        print(f"  seed_words: {self.seed_words[:5]}...")
        print(f"  Принцип: фрактальные вложенные ламинарные потоки")
        print(f"  Обмен: TEES/ВММП поверхности раздела")
    
    def generate_tees_field(self, use_memory: bool = True) -> np.ndarray:
        """
        Генерирует TEES-поле как систему вложенных потоков с обменными поверхностями.
        
        Это замена для np.random.randn(*shape).
        Возвращает НЕ шум, а структурированную информацию.
        """
        
        # 1. Создаем макро-потоки от слов-триггеров
        macro_flows = self._create_macro_flows()
        
        # 2. Рекурсивно вкладываем мезо- и микро-потоки
        meso_flows = self._create_nested_flows(macro_flows, depth=1)
        micro_flows = self._create_nested_flows(meso_flows, depth=2)
        
        # 3. Создаем иерархию обменных поверхностей
        exchange_surfaces = self._create_exchange_hierarchy(
            macro_flows, meso_flows, micro_flows
        )
        
        # 4. Учитываем историю (если есть)
        if use_memory and len(self.history) > 0:
            self._apply_memory_evolution(macro_flows, meso_flows, micro_flows)
        
        # 5. Синтезируем итоговое поле
        field = self._synthesize_field(macro_flows, meso_flows, micro_flows, 
                                       exchange_surfaces)
        
        # 6. Анализируем, но НЕ нормализуем (это информация, не шум!)
        info_metrics = self._analyze_information_content(field)
        
        # 7. Сохраняем состояние
        self.current_state = TEESFlowState(
            field=field.copy(),
            macro_flows=macro_flows,
            meso_flows=meso_flows,
            micro_flows=micro_flows,
            exchange_surfaces=exchange_surfaces,
            total_information=info_metrics['total_information'],
            total_exchange_flux=info_metrics['exchange_flux'],
            curvature_energy=info_metrics['curvature_energy'],
            timestamp=self.step
        )
        self.history.append(self.current_state)
        self.step += 1
        
        # Обновляем статистику
        self.stats['generations'] += 1
        self.stats['total_flows'].append(len(macro_flows) + len(meso_flows) + len(micro_flows))
        self.stats['exchange_fluxes'].append(info_metrics['exchange_flux'])
        self.stats['curvature_energies'].append(info_metrics['curvature_energy'])
        self.stats['information_transfers'].append(info_metrics['total_information'])
        
        return field
    
    def _create_macro_flows(self) -> List[LaminarFlow]:
        """
        Создает макро-потоки из слов-триггеров.
        Каждое слово → ламинарный поток со своей кривизной.
        """
        flows = []
        
        # Выбираем слова для этого шага
        n_flows = min(len(self.seed_words), max(3, self.shape[0] // 4))
        step_words = [
            self.seed_words[(i + self.step) % len(self.seed_words)]
            for i in range(n_flows)
        ]
        
        for i, word in enumerate(step_words):
            # Позиция потока в сетке
            position = (
                int(self.shape[0] * (i + 0.5) / n_flows),
                int(self.shape[1] * 0.5),
                int(self.shape[2] * 0.5)
            )
            
            # Создаем поток
            flow = LaminarFlow(
                seed_word=word,
                depth=0,
                scale=1.0,
                position=position
            )
            
            # Генерируем моды кривизны из TEES-структуры слова
            flow.curvature_modes = self.curvature_gen.generate_word_curvature(
                word, position
            )
            
            # Вычисляем поле кривизны
            flow.curvature_field = self.curvature_gen.compute_curvature_field(
                flow.curvature_modes, position, flow.scale
            )
            
            # Суммарный заряд потока
            flow.total_charge = sum(mode.charge for mode in flow.curvature_modes)
            flow.information_density = flow.total_charge / len(word) if len(word) > 0 else 0
            
            flows.append(flow)
        
        return flows
    
    def _create_nested_flows(self, parent_flows: List[LaminarFlow], 
                             depth: int) -> List[LaminarFlow]:
        """
        Рекурсивно создает вложенные потоки.
        
        Каждый родительский поток порождает дочерние на меньшем масштабе.
        Фрактальное масштабирование: scale = 1 / (2^depth).
        """
        if depth >= self.fractal_depth:
            return []
        
        nested_flows = []
        scale = 1.0 / (2 ** depth)
        
        for parent in parent_flows:
            # Количество дочерних потоков зависит от длины слова-родителя
            n_children = min(len(parent.seed_word), 4)
            
            for i in range(n_children):
                # Позиция дочернего потока смещена относительно родителя
                child_position = (
                    int(parent.position[0] + (i - n_children/2) * self.shape[0] * scale * 0.3),
                    int(parent.position[1] + np.sin(2*np.pi*i/n_children) * self.shape[1] * scale * 0.3),
                    int(parent.position[2] + np.cos(2*np.pi*i/n_children) * self.shape[2] * scale * 0.3)
                )
                
                # Ограничиваем позицию размерами сетки
                child_position = tuple(
                    max(0, min(self.shape[d] - 1, child_position[d]))
                    for d in range(3)
                )
                
                # Слово-наследник: часть слова-родителя
                char_start = i * len(parent.seed_word) // n_children
                char_end = (i + 1) * len(parent.seed_word) // n_children
                child_word = parent.seed_word[char_start:char_end]
                
                if len(child_word) == 0:
                    child_word = parent.seed_word[i % len(parent.seed_word)]
                
                # Создаем дочерний поток
                child_flow = LaminarFlow(
                    seed_word=child_word,
                    depth=depth,
                    scale=scale,
                    position=child_position,
                    parent=parent
                )
                
                # Генерируем моды кривизны (меньший масштаб)
                child_flow.curvature_modes = self.curvature_gen.generate_word_curvature(
                    child_word, child_position
                )
                
                # Вычисляем поле кривизны
                child_flow.curvature_field = self.curvature_gen.compute_curvature_field(
                    child_flow.curvature_modes, child_position, child_flow.scale
                )
                
                # Суммарный заряд
                child_flow.total_charge = sum(mode.charge for mode in child_flow.curvature_modes)
                child_flow.information_density = child_flow.total_charge / max(len(child_word), 1)
                
                # Связываем с родителем
                parent.children.append(child_flow)
                nested_flows.append(child_flow)
        
        return nested_flows
    
    def _create_exchange_hierarchy(self, 
                                   macro_flows: List[LaminarFlow],
                                   meso_flows: List[LaminarFlow],
                                   micro_flows: List[LaminarFlow]) -> List[ExchangeSurface]:
        """
        Создает иерархию обменных поверхностей между ВСЕМИ уровнями.
        
        Уровни обмена:
        - macro ↔ macro (межсловные границы)
        - macro ↔ meso (межуровневые границы)
        - meso ↔ meso (внутрисловные границы)
        - meso ↔ micro (фрактальные границы)
        - micro ↔ micro (фонемные границы)
        """
        surfaces = []
        
        # 1. Межсловные обменные поверхности (macro ↔ macro)
        for i in range(len(macro_flows)):
            for j in range(i + 1, len(macro_flows)):
                surface = self.surface_gen.create_surface(
                    macro_flows[i], macro_flows[j], "macro-macro"
                )
                surfaces.append(surface)
        
        # 2. Межуровневые поверхности (macro ↔ meso)
        for macro_flow in macro_flows:
            for child in macro_flow.children:
                if child.depth == 1:  # meso
                    surface = self.surface_gen.create_surface(
                        macro_flow, child, "macro-meso"
                    )
                    surfaces.append(surface)
        
        # 3. Внутрисловные границы (meso ↔ meso)
        for i in range(len(meso_flows)):
            for j in range(i + 1, len(meso_flows)):
                if meso_flows[i].parent == meso_flows[j].parent:
                    surface = self.surface_gen.create_surface(
                        meso_flows[i], meso_flows[j], "meso-meso"
                    )
                    surfaces.append(surface)
        
        # 4. Фрактальные границы (meso ↔ micro)
        for meso_flow in meso_flows:
            for child in meso_flow.children:
                if child.depth == 2:  # micro
                    surface = self.surface_gen.create_surface(
                        meso_flow, child, "meso-micro"
                    )
                    surfaces.append(surface)
        
        # 5. Фонемные границы (micro ↔ micro)
        for i in range(len(micro_flows)):
            for j in range(i + 1, len(micro_flows)):
                if micro_flows[i].parent == micro_flows[j].parent:
                    surface = self.surface_gen.create_surface(
                        micro_flows[i], micro_flows[j], "micro-micro"
                    )
                    surfaces.append(surface)
        
        return surfaces
    
    def _apply_memory_evolution(self, 
                                macro_flows: List[LaminarFlow],
                                meso_flows: List[LaminarFlow],
                                micro_flows: List[LaminarFlow]):
        """
        Применяет эволюцию с учетом истории.
        Потоки взаимодействуют с предыдущими состояниями.
        """
        if len(self.history) < 2:
            return
        
        prev_state = self.history[-1]
        
        # Коэффициент памяти (затухающий)
        memory_factor = 0.3 * np.exp(-self.step * 0.01)
        
        # Модифицируем макро-потоки с учетом предыдущих
        for flow in macro_flows:
            if flow.curvature_field is not None:
                # Добавляем информацию из предыдущего поля
                prev_field_region = prev_state.field[
                    max(0, flow.position[0]-2):min(self.shape[0], flow.position[0]+3),
                    max(0, flow.position[1]-2):min(self.shape[1], flow.position[1]+3),
                    max(0, flow.position[2]-2):min(self.shape[2], flow.position[2]+3)
                ]
                
                if prev_field_region.size > 0:
                    avg_prev = np.mean(prev_field_region)
                    flow.curvature_field += memory_factor * avg_prev
    
    def _synthesize_field(self,
                          macro_flows: List[LaminarFlow],
                          meso_flows: List[LaminarFlow],
                          micro_flows: List[LaminarFlow],
                          exchange_surfaces: List[ExchangeSurface]) -> np.ndarray:
        """
        Синтезирует итоговое поле из иерархии потоков.
        
        Это СУПЕРПОЗИЦИЯ вложенных ламинарных потоков с обменными поверхностями.
        НЕ сумма + шум!
        """
        field = np.zeros(self.shape)
        
        # 1. Макро-потоки (основа, масштаб 1.0)
        for flow in macro_flows:
            if flow.curvature_field is not None:
                field += flow.curvature_field * flow.scale
        
        # 2. Мезо-потоки (вложенные, масштаб 0.5)
        for flow in meso_flows:
            if flow.curvature_field is not None and flow.parent is not None:
                # Вложенный поток модулирует родительский регион
                field += flow.curvature_field * flow.scale * 0.7
        
        # 3. Микро-потоки (самые вложенные, масштаб 0.25)
        for flow in micro_flows:
            if flow.curvature_field is not None and flow.parent is not None:
                field += flow.curvature_field * flow.scale * 0.5
        
        # 4. Обменные поверхности (градиенты, не шум!)
        for surface in exchange_surfaces:
            if surface.gradient_field is not None:
                # Вклад пропорционален информационному потоку
                weight = np.abs(surface.information_flux) * 0.1
                field += surface.gradient_field * weight
        
        return field
    
    def _analyze_information_content(self, field: np.ndarray) -> Dict[str, float]:
        """
        Анализирует информационное содержание поля.
        
        НЕ фильтрует, НЕ нормализует — только измеряет.
        Сильные сигналы = ВАЖНАЯ информация, а не ошибка.
        """
        metrics = {
            'total_information': float(np.sum(np.abs(field))),
            'max_signal': float(np.max(np.abs(field))),
            'mean_signal': float(np.mean(np.abs(field))),
            'exchange_flux': float(np.sum(np.abs(np.gradient(field)[0]))),
            'curvature_energy': float(np.sum(field ** 2)),
            'info_density': float(np.sum(field ** 2) / field.size)
        }
        
        # Если обнаружена высокоэнергетическая информация — сохраняем
        if metrics['max_signal'] > 5.0:
            self.high_information_events.append({
                'step': self.step,
                'metrics': metrics,
                'field_snapshot': field.copy()
            })
            print(f"[TEES-ENGINE] 🔥 Высокоэнергетическая информация: "
                  f"max={metrics['max_signal']:.1f}, "
                  f"total={metrics['total_information']:.1f}")
        
        return metrics
    
    def get_current_state(self) -> Optional[TEESFlowState]:
        """Возвращает текущее состояние потокового поля."""
        return self.current_state
    
    def get_statistics(self) -> dict:
        """Возвращает потоковую статистику (не шумовую)."""
        if len(self.stats['total_flows']) > 0:
            avg_flows = np.mean(self.stats['total_flows'])
            avg_flux = np.mean(self.stats['exchange_fluxes'])
            avg_curvature = np.mean(self.stats['curvature_energies'])
        else:
            avg_flows = 0.0
            avg_flux = 0.0
            avg_curvature = 0.0
        
        return {
            'generations': self.stats['generations'],
            'memory_size': len(self.history),
            'avg_total_flows': avg_flows,
            'avg_exchange_flux': avg_flux,
            'avg_curvature_energy': avg_curvature,
            'high_information_events': len(self.high_information_events),
            'current_total_information': (
                self.current_state.total_information if self.current_state else 0
            ),
            'current_exchange_flux': (
                self.current_state.total_exchange_flux if self.current_state else 0
            )
        }
    
    def reset(self):
        """Сбрасывает состояние движка."""
        self.history.clear()
        self.current_state = None
        self.step = 0
        self.high_information_events.clear()
        self.stats = {
            'generations': 0,
            'total_flows': [],
            'exchange_fluxes': [],
            'curvature_energies': [],
            'information_transfers': []
        }
        print("[TEES-ENGINE v4.0] Сброшен")


# ============================================
# КЛАСС-ОБЕРТКА ДЛЯ БИГАРМОНИЧЕСКОГО РЕШАТЕЛЯ
# ============================================

class TEESAwareBiharmonicSolver:
    """
    Бигармонический решатель с TEES-турбулентностью.
    Турбулентность = фрактальные вложенные ламинарные потоки.
    """
    
    def __init__(self, 
                 grid_shape: Tuple[int, int, int],
                 fractal_depth: int = 3,
                 use_tees: bool = True,
                 base_solver_module: str = "architect.core.biharmonic_solver"):
        
        self.grid_shape = grid_shape
        self.use_tees = use_tees
        self._has_solver = False
        
        # Импортируем оригинальный решатель
        try:
            import importlib
            module = importlib.import_module(base_solver_module)
            BiharmonicSolver = getattr(module, 'BiharmonicSolver')
            self.base_solver = BiharmonicSolver(grid_shape)
            self._has_solver = True
            print(f"[TEES-SOLVER] Базовый решатель загружен из {base_solver_module}")
        except (ImportError, AttributeError) as e:
            print(f"[TEES-SOLVER] Предупреждение: базовый решатель не найден ({e})")
            self.base_solver = None
        
        # TEES-движок (всегда создаем, даже если use_tees=False)
        self.tees_engine = TEESEngine(
            shape=grid_shape,
            fractal_depth=fractal_depth,
            memory_depth=10
        )
        
        print(f"[TEES-SOLVER] Инициализирован")
        print(f"  grid_shape: {grid_shape}")
        print(f"  use_tees: {use_tees}")
        print(f"  fractal_depth: {fractal_depth}")
    
    def solve(self, vortices: List[Tuple[int, int, int, float]]) -> Tuple[np.ndarray, float]:
        """
        Решает бигармоническое уравнение с TEES-турбулентностью.
        
        Турбулентность здесь = система вложенных ламинарных потоков
                              с обменными поверхностями.
        """
        if not self._has_solver:
            print("[TEES-SOLVER] Ошибка: базовый решатель не инициализирован")
            return np.zeros(self.grid_shape), 0.0
        
        # 1. Базовое решение
        try:
            phi_base = self.base_solver.solve(vortices)
            if phi_base is None:
                print("[TEES-SOLVER] Ошибка: базовый решатель вернул None")
                return np.zeros(self.grid_shape), 0.0
        except Exception as e:
            print(f"[TEES-SOLVER] Ошибка базового решателя: {e}")
            return np.zeros(self.grid_shape), 0.0
        
        # 2. Энергия базового решения
        try:
            energy_base = self.base_solver.compute_energy(phi_base)
        except AttributeError:
            energy_base = np.sum(phi_base ** 2) / phi_base.size
        
        if not self.use_tees:
            return phi_base, energy_base
        
        # 3. Генерируем TEES-потоковое поле
        tees_field = self.tees_engine.generate_tees_field()
        
        # 4. Анализируем силу информации (не шума!)
        info_strength = np.mean(np.abs(tees_field))
        
        # 5. Накладываем TEES-поле на базовое решение
        # БЕЗ нормализации, БЕЗ клиппинга — это информация
        if phi_base.shape != tees_field.shape:
                phi_base = np.transpose(phi_base, (2, 1, 0))
        phi_perturbed = phi_base + tees_field
        
        # 6. Адаптивная релаксация
        # Чем больше нераспознанной информации, тем больше итераций
        if info_strength > 1.0:
            iterations = 50
            print(f"[TEES-SOLVER] Много нераспознанной информации "
                  f"(strength={info_strength:.2f}), глубокий анализ")
        elif info_strength > 0.5:
            iterations = 30
        else:
            iterations = 15
        
        for i in range(iterations):
            phi_perturbed = self._relax_field(phi_perturbed, vortices)
        
        # 7. Финальная энергия
        try:
            energy_final = self.base_solver.compute_energy(phi_perturbed)
        except AttributeError:
            energy_final = np.sum(phi_perturbed ** 2) / phi_perturbed.size
        
        return phi_perturbed, energy_final
    
    def _relax_field(self, phi: np.ndarray, vortices: List) -> np.ndarray:
        """Шаг релаксации с граничными условиями."""
        # Добавляем padding для корректных границ
        padded = np.pad(phi, 1, mode='edge')
        grad = np.gradient(padded)
        
        # Лапласиан
        laplacian = (np.gradient(grad[0])[0] + 
                     np.gradient(grad[1])[1] + 
                     np.gradient(grad[2])[2])
        
        # Убираем padding
        laplacian = laplacian[1:-1, 1:-1, 1:-1]
        
        return phi - 0.01 * laplacian


# ============================================
# ТЕСТ ИНТЕГРАЦИИ
# ============================================

def test_tees_integration():
    """
    Тест интеграции TEES-потоковой турбулентности в бигармонический решатель.
    """
    print("="*60)
    print("🧪 ТЕСТ ИНТЕГРАЦИИ TEES/ВММП v4.0")
    print("   Турбулентность = вложенные ламинарные потоки")
    print("="*60)
    
    # Тестовые вихри
    vortices = [
        (4, 4, 2, 1.0),
        (12, 12, 2, -1.0),
        (8, 8, 4, 0.5),
    ]
    
    # Без TEES
    print("\n📊 БЕЗ TEES (классический решатель):")
    try:
        solver_no_tees = TEESAwareBiharmonicSolver(
            grid_shape=(16, 16, 8),
            use_tees=False
        )
        phi_no, energy_no = solver_no_tees.solve(vortices)
        print(f"  Энергия: {energy_no:.6f}")
        print(f"  Max |phi|: {np.max(np.abs(phi_no)):.4f}")
    except Exception as e:
        print(f"  Ошибка: {e}")
        phi_no = np.zeros((16, 16, 8))
        energy_no = 0.0
    
    # С TEES
    print("\n📊 С TEES (потоковая турбулентность):")
    try:
        solver_tees = TEESAwareBiharmonicSolver(
            grid_shape=(16, 16, 8),
            use_tees=True,
            fractal_depth=3
        )
        phi_tees, energy_tees = solver_tees.solve(vortices)
        print(f"  Энергия: {energy_tees:.6f}")
        print(f"  Max |phi|: {np.max(np.abs(phi_tees)):.4f}")
        
        if energy_no > 0:
            print(f"  Изменение энергии: {(energy_tees - energy_no) / energy_no * 100:.2f}%")
    except Exception as e:
        print(f"  Ошибка: {e}")
        import traceback
        traceback.print_exc()
        phi_tees = np.zeros((16, 16, 8))
        energy_tees = 0.0
    
    # Статистика TEES
    print("\n📈 СТАТИСТИКА TEES-ПОТОКОВ:")
    try:
        stats = solver_tees.tees_engine.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except:
        pass
    
    # Визуализация
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Без TEES
        im0 = axes[0, 0].imshow(phi_no[4, :, :], cmap='RdBu', aspect='auto')
        axes[0, 0].set_title("Без TEES (z=4)")
        plt.colorbar(im0, ax=axes[0, 0])
        
        im1 = axes[0, 1].imshow(phi_no[8, :, :], cmap='RdBu', aspect='auto')
        axes[0, 1].set_title("Без TEES (z=8)")
        plt.colorbar(im1, ax=axes[0, 1])
        
        # С TEES
        im2 = axes[1, 0].imshow(phi_tees[4, :, :], cmap='RdBu', aspect='auto')
        axes[1, 0].set_title("С TEES потоками (z=4)")
        plt.colorbar(im2, ax=axes[1, 0])
        
        im3 = axes[1, 1].imshow(phi_tees[8, :, :], cmap='RdBu', aspect='auto')
        axes[1, 1].set_title("С TEES потоками (z=8)")
        plt.colorbar(im3, ax=axes[1, 1])
        
        plt.suptitle("TEES/ВММП: Турбулентность как вложенные ламинарные потоки", 
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('tees_flow_integration_test.png', dpi=150)
        print("\n📁 График сохранен: tees_flow_integration_test.png")
        plt.show()
        
    except ImportError:
        print("\n⚠️ matplotlib не установлен, визуализация пропущена")
    
    return phi_tees, energy_tees


# ============================================
# ДЕМОНСТРАЦИЯ СТРУКТУРЫ ПОТОКОВ
# ============================================

def demonstrate_flow_structure():
    """
    Демонстрирует иерархическую структуру TEES-потоков.
    """
    print("\n" + "="*60)
    print("🌊 ДЕМОНСТРАЦИЯ ИЕРАРХИИ ПОТОКОВ")
    print("="*60)
    
    engine = TEESEngine(
        shape=(16, 16, 8),
        fractal_depth=3,
        seed_words=["vortex", "quantum", "field", "space", "time"]
    )
    
    # Генерируем поле
    field = engine.generate_tees_field()
    
    state = engine.get_current_state()
    
    if state:
        print(f"\n📊 ИЕРАРХИЯ ПОТОКОВ:")
        print(f"  Макро-потоки: {len(state.macro_flows)}")
        for flow in state.macro_flows:
            print(f"    - '{flow.seed_word}' (charge={flow.total_charge:.2f}, "
                  f"children={len(flow.children)})")
        
        print(f"  Мезо-потоки: {len(state.meso_flows)}")
        print(f"  Микро-потоки: {len(state.micro_flows)}")
        
        print(f"\n📊 ОБМЕННЫЕ ПОВЕРХНОСТИ: {len(state.exchange_surfaces)}")
        # Группируем по типам
        from collections import Counter
        type_counts = Counter(s.exchange_type for s in state.exchange_surfaces)
        for etype, count in type_counts.items():
            print(f"  {etype}: {count}")
        
        print(f"\n📊 ИНФОРМАЦИОННЫЕ МЕТРИКИ:")
        print(f"  Общая информация: {state.total_information:.2f}")
        print(f"  Обменный поток: {state.total_exchange_flux:.2f}")
        print(f"  Энергия кривизны: {state.curvature_energy:.2f}")
    
    # Визуализация обменных поверхностей
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        # Суммарное поле
        im0 = axes[0].imshow(field[4, :, :], cmap='RdBu', aspect='auto')
        axes[0].set_title("Суммарное поле потоков")
        plt.colorbar(im0, ax=axes[0])
        
        # Только обменные поверхности (сумма всех)
        exchange_field = np.zeros_like(field)
        if state:
            for surf in state.exchange_surfaces:
                if surf.gradient_field is not None:
                    exchange_field += surf.gradient_field * 0.1
        
        im1 = axes[1].imshow(exchange_field[4, :, :], cmap='coolwarm', aspect='auto')
        axes[1].set_title("Обменные поверхности")
        plt.colorbar(im1, ax=axes[1])
        
        # Разность (потоки - обмен)
        im2 = axes[2].imshow((field - exchange_field)[4, :, :], cmap='RdBu', aspect='auto')
        axes[2].set_title("Ламинарные потоки (без обмена)")
        plt.colorbar(im2, ax=axes[2])
        
        plt.suptitle("Структура TEES-турбулентности: потоки + обменные поверхности", 
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('tees_flow_structure.png', dpi=150)
        print("\n📁 Структура сохранена: tees_flow_structure.png")
        plt.show()
        
    except ImportError:
        pass


if __name__ == "__main__":
    # Демонстрация структуры
    demonstrate_flow_structure()
    
    # Тест интеграции
    test_tees_integration()
