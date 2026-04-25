"""
Фрактальное дискретное время для ВММП.
Каждый фрактальный уровень имеет свой квант времени.
Между тиками происходит мгновенная синхронизация через буфер обмена.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from collections import defaultdict

@dataclass
class TimeQuantum:
    """Квант времени для фрактального уровня"""
    level: int
    base_dt: float = 1.0
    lambda_scale: float = 2.0
    
    @property
    def dt(self) -> float:
        """Шаг времени для этого уровня"""
        return self.base_dt * (self.lambda_scale ** (-self.level))
    
    @property
    def ticks_per_global(self) -> int:
        """Сколько глобальных тиков приходится на один тик уровня"""
        return max(1, int(1 / self.dt)) if self.dt < 1 else 1
    
    @property
    def time_dilation(self) -> float:
        """Замедление времени относительно уровня 1"""
        return self.lambda_scale ** (self.level - 1)


class FractalTimeBuffer:
    """
    Буфер обмена между фрактальными уровнями.
    Обеспечивает мгновенную синхронизацию в "безвременье".
    """
    
    def __init__(self, num_levels: int = 7):
        self.num_levels = num_levels
        self.buffers: Dict[int, Dict] = {k: {} for k in range(1, num_levels + 1)}
        self.tick_counters: Dict[int, int] = {k: 0 for k in range(1, num_levels + 1)}
        self.global_tick: int = 0
        self.exchange_stats: Dict[str, int] = defaultdict(int)
        
    def store_state(self, level: int, state: Dict[str, Any]):
        """Сохранить состояние уровня в буфер"""
        H_field = state.get('H')
        if H_field is None:
            H_field = state.get('H_field')
        
        positions = state.get('positions')
        if positions is None:
            positions = state.get('vortex_positions', [])
        
        normalized_state = {
            'H': H_field,
            'positions': positions,
            'energy': state.get('energy', 0.0),
            'timestamp': self.tick_counters[level],
            'global_tick': self.global_tick
        }
        self.buffers[level] = normalized_state
        self.tick_counters[level] += 1
        
    def retrieve_state(self, level: int) -> Optional[Dict]:
        """Извлечь состояние уровня из буфера"""
        return self.buffers.get(level)
    
    def get_effective_potential(self, from_level: int, to_level: int):
        """Получить эффективный потенциал от низшего уровня для высшего."""
        if from_level >= to_level:
            return None
            
        state_low = self.buffers.get(from_level)
        if state_low is None:
            return None
        
        H_low = state_low.get('H')
        if H_low is None:
            return None
        
        level_diff = to_level - from_level
        coarse_scale = 2 ** level_diff
        
        try:
            from scipy.ndimage import zoom
            zoom_factor = 1.0 / coarse_scale
            H_effective = zoom(H_low, zoom_factor, order=1)
        except (ImportError, ValueError):
            H_effective = H_low[::coarse_scale, ::coarse_scale, ::coarse_scale]
        
        coupling = 1.0 / (1.0 + level_diff)
        self.exchange_stats[f'up_{from_level}_to_{to_level}'] += 1
        
        return H_effective * coupling
    
    def get_boundary_conditions(self, from_level: int, to_level: int) -> Dict:
        """Получить граничные условия от высшего уровня для низшего."""
        if from_level <= to_level:
            return None
            
        state_high = self.buffers.get(from_level)
        if state_high is None:
            return None
            
        H_high = state_high.get('H')
        if H_high is None:
            return None
        
        boundary = {
            'x_min': float(H_high[0, :, :].mean()),
            'x_max': float(H_high[-1, :, :].mean()),
            'y_min': float(H_high[:, 0, :].mean()),
            'y_max': float(H_high[:, -1, :].mean()),
            'z_min': float(H_high[:, :, 0].mean()),
            'z_max': float(H_high[:, :, -1].mean()),
            'mean': float(H_high.mean()),
            'std': float(H_high.std())
        }
        
        self.exchange_stats[f'down_{from_level}_to_{to_level}'] += 1
        return boundary
    
    def synchronize_all(self, fields: Dict[int, Any]) -> Dict[int, Any]:
        """Полная синхронизация всех уровней."""
        self.global_tick += 1
        
        for level in range(1, self.num_levels):
            if level in fields and (level + 1) in fields:
                effective = self.get_effective_potential(level, level + 1)
                if effective is not None and hasattr(fields[level + 1], 'effective_potential'):
                    fields[level + 1].effective_potential = effective
        
        for level in range(self.num_levels, 1, -1):
            if level in fields and (level - 1) in fields:
                boundary = self.get_boundary_conditions(level, level - 1)
                if boundary is not None and hasattr(fields[level - 1], 'boundary_conditions'):
                    fields[level - 1].boundary_conditions = boundary
        
        return fields
    
    def get_statistics(self) -> Dict:
        return {
            'global_ticks': self.global_tick,
            'level_ticks': self.tick_counters.copy(),
            'exchanges': dict(self.exchange_stats)
        }


class FractalFieldWrapper:
    """Обёртка для поля H с поддержкой фрактального времени."""
    
    def __init__(self, field, fractal_level: int):
        self.field = field
        self.fractal_level = fractal_level
        self.time_buffer: Optional[FractalTimeBuffer] = None
        self.time_quantum: Optional[TimeQuantum] = None
        self.local_time: float = 0.0
        self.local_ticks: int = 0
        self.effective_potential = None
        self.boundary_conditions = None
        
    def set_time_buffer(self, buffer: FractalTimeBuffer):
        self.time_buffer = buffer
        
    def set_time_quantum(self, tq: TimeQuantum):
        self.time_quantum = tq
        
    def evolve(self, global_tick: int, state=None):
        """Эволюция поля с учётом фрактального времени и термодинамического состояния."""
        if self.effective_potential is not None:
            self._apply_effective_potential()
        
        if self.boundary_conditions is not None:
            self._apply_boundary_conditions()
        
        if hasattr(self.field, 'evolve_time'):
            dt = self.time_quantum.dt if self.time_quantum else 1.0
            self.field.evolve_time(dt)
        
        # Вызываем relax_vortices с передачей state
        if hasattr(self.field, 'relax_vortices'):
            if state is not None:
                # Новый вызов с термодинамическим состоянием
                self.field.relax_vortices(max_iter=1, learning_rate=0.05, state=state, thermal_scale=0.3)
            else:
                # Старый вызов для обратной совместимости
                self.field.relax_vortices(max_iter=1, learning_rate=0.05)
        
        self._add_quantum_fluctuations()
        
        self.local_time += self.time_quantum.dt if self.time_quantum else 1.0
        self.local_ticks += 1
        
    def _apply_effective_potential(self):
        if self.effective_potential is not None and hasattr(self.field, 'H'):
            try:
                from scipy.ndimage import zoom
                zoom_factor = np.array(self.field.H.shape) / np.array(self.effective_potential.shape)
                potential_resized = zoom(self.effective_potential, zoom_factor, order=1)
                self.field.H += 0.01 * potential_resized
            except (ImportError, ValueError):
                pass
            
    def _apply_boundary_conditions(self):
        if self.boundary_conditions is not None and hasattr(self.field, 'H'):
            bc = self.boundary_conditions
            H = self.field.H
            if 'x_min' in bc: H[0, :, :] = bc['x_min']
            if 'x_max' in bc: H[-1, :, :] = bc['x_max']
            if 'y_min' in bc: H[:, 0, :] = bc['y_min']
            if 'y_max' in bc: H[:, -1, :] = bc['y_max']
            if 'z_min' in bc: H[:, :, 0] = bc['z_min']
            if 'z_max' in bc: H[:, :, -1] = bc['z_max']
            
    def _add_quantum_fluctuations(self):
        if hasattr(self.field, 'H'):
            dt = self.time_quantum.dt if self.time_quantum else 1.0
            amplitude = np.sqrt(dt) * 0.01
            self.field.H += amplitude * np.random.randn(*self.field.H.shape)
    
    def compute_energy(self) -> float:
        if hasattr(self.field, 'compute_energy'):
            return self.field.compute_energy()
        return 0.0


class FractalTimeEvolution:
    """Эволюция системы с дискретным фрактальным временем."""
    
    def __init__(self, num_levels: int = 7, base_dt: float = 1.0, lambda_scale: float = 2.0, resonance_pid=None):
        self.num_levels = num_levels
        self.base_dt = base_dt
        self.lambda_scale = lambda_scale
        
        self.time_quanta = {
            k: TimeQuantum(k, base_dt, lambda_scale) 
            for k in range(1, num_levels + 1)
        }
        
        self.buffer = FractalTimeBuffer(num_levels)
        self.fields: Dict[int, Any] = {}
        self.global_time: float = 0.0
        self.global_ticks: int = 0
        
        # 2. ПРАВИЛЬНОЕ МЕСТО ДЛЯ СОХРАНЕНИЯ ПИД - ЗДЕСЬ, ПОСЛЕ ВСЕХ ОСТАЛЬНЫХ ПРИСВОЕНИЙ
        self.resonance_pid = resonance_pid
        
    def add_field(self, level: int, field: Any):
        self.fields[level] = field
        if hasattr(field, 'set_time_buffer'):
            field.set_time_buffer(self.buffer)
        if hasattr(field, 'set_time_quantum'):
            field.set_time_quantum(self.time_quanta[level])
        
    def should_evolve(self, level: int) -> bool:
        if level not in self.time_quanta:
            return False
        tq = self.time_quanta[level]
        return self.global_ticks % tq.ticks_per_global == 0
    
    def evolve_step(self, state=None) -> Dict[int, Any]:
        """Один шаг глобальной эволюции с передачей термодинамического состояния."""
        self.global_ticks += 1
        self.global_time += self.base_dt
        evolved_levels = []
        
        for level, field in self.fields.items():
            if self.should_evolve(level):
                if hasattr(field, 'evolve'):
                    # Передаём state в метод evolve обёртки
                    field.evolve(self.global_ticks, state)
                
                state_data = {}
                if hasattr(field, 'field') and hasattr(field.field, 'H'):
                    state_data['H'] = field.field.H.copy()
                elif hasattr(field, 'H'):
                    state_data['H'] = field.H.copy()
                    
                if hasattr(field, 'compute_energy'):
                    state_data['energy'] = field.compute_energy()
                elif hasattr(field, 'field') and hasattr(field.field, 'compute_energy'):
                    state_data['energy'] = field.field.compute_energy()
                else:
                    state_data['energy'] = 0.0
                    
                self.buffer.store_state(level, state_data)
                evolved_levels.append(level)
        
        if evolved_levels:
            self.fields = self.buffer.synchronize_all(self.fields)
        
        return self.fields
    
    def evolve(self, num_steps: int, state=None, callback=None) -> Dict:
        """Эволюция на несколько шагов с передачей термодинамического состояния."""
        history = {
            'global_ticks': [],
            'energies': {level: [] for level in self.fields.keys()},
            'evolved_levels': []
        }
        
        for step in range(num_steps):
            self.evolve_step(state)
            history['global_ticks'].append(self.global_ticks)
            history['evolved_levels'].append(
                [l for l in self.fields.keys() if self.should_evolve(l)]
            )
            
            for level, field in self.fields.items():
                if hasattr(field, 'compute_energy'):
                    history['energies'][level].append(field.compute_energy())
                elif hasattr(field, 'field') and hasattr(field.field, 'compute_energy'):
                    history['energies'][level].append(field.field.compute_energy())
            
            if callback:
                callback(step, self)
        
        history['statistics'] = self.buffer.get_statistics()
        history['time_quanta'] = {
            k: {'dt': tq.dt, 'dilation': tq.time_dilation} 
            for k, tq in self.time_quanta.items()
        }
        
        return history


# ========== ТЕСТ ==========

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ФРАКТАЛЬНОГО ВРЕМЕНИ")
    print("=" * 60)
    
    print("\n[1] Кванты времени для уровней 1-7:")
    for k in range(1, 8):
        tq = TimeQuantum(k)
        print(f"    Уровень {k}: dt = {tq.dt:.6f}, замедление = {tq.time_dilation:>2}x, "
              f"тиков/глобальный = {tq.ticks_per_global}")
    
    print("\n[2] Тест буфера обмена:")
    buffer = FractalTimeBuffer(3)
    
    for level in range(1, 4):
        buffer.store_state(level, {
            'H': np.random.randn(4, 4, 4),
            'energy': 100.0 / level
        })
    
    class MockField:
        def __init__(self):
            self.effective_potential = None
            self.boundary_conditions = None
    
    fields = {1: MockField(), 2: MockField(), 3: MockField()}
    buffer.synchronize_all(fields)
    stats = buffer.get_statistics()
    print(f"    Глобальных тиков: {stats['global_ticks']}")
    print(f"    Тики уровней: {stats['level_ticks']}")
    
    print("\n[3] Тест эволюции с фрактальным временем:")
    evolution = FractalTimeEvolution(num_levels=3, base_dt=1.0)
    
    class TestField:
        def __init__(self, level):
            self.level = level
            self.H = np.random.randn(8, 8, 8)
            self.vortices = []
            self.effective_potential = None
            self.boundary_conditions = None
            self.time_buffer = None
            self.time_quantum = None
        
        def set_time_buffer(self, buf): self.time_buffer = buf
        def set_time_quantum(self, tq): self.time_quantum = tq
        def compute_energy(self): return 100.0 / self.level
        def evolve_time(self, dt): self.H += 0.01 * np.random.randn(*self.H.shape)
        def relax_vortices(self, max_iter=1, learning_rate=0.05, state=None, thermal_scale=0.3):
            pass  # Заглушка для теста

    for level in range(1, 4):
        field = TestField(level)
        wrapped = FractalFieldWrapper(field, level)
        evolution.add_field(level, wrapped)

    history = evolution.evolve(10)
    
    print(f"    Глобальных тиков: {evolution.global_ticks}")
    print(f"    Глобальное время: {evolution.global_time}")
    print(f"    Статистика обменов: {history['statistics']['exchanges']}")
    
    print("\n[4] Замедление времени для элементов:")
    elements = [('H', 1), ('He', 1), ('C', 2), ('O', 2), ('Fe', 4), ('Ag', 5), ('Au', 6), ('U', 7)]
    
    for symbol, level in elements:
        tq = TimeQuantum(level)
        print(f"    {symbol:>2} (ур.{level}): время течёт в {tq.time_dilation:>3}x медленнее H")
    
    print("\n[5] Поправка к энергии связи из-за замедления времени:")
    print("    Формула: E_true = E_calc * 2^(-α·k), α ≈ 0.25")
    
    alpha = 0.25
    for k in range(1, 8):
        correction = 2 ** (-alpha * k)
        element = ['H', 'C', 'Si', 'Fe', 'Sn', 'Pb', 'U'][k-1] if k <= 7 else f'Z~{2**k}'
        print(f"    {element:>2} (ур.{k}): поправка = {correction:.3f} ({(1-correction)*100:+.0f}%)")
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)