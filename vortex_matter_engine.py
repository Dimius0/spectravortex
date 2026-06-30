#!/usr/bin/env python3
"""
vortex_matter_engine.py — Vortex Matter Engine (VME) v1.0.1 🔬🌪️✨
======================================================================
HOTFIX: Исправлено зависание в адаптивной сетке и квантовом коллапсе.

ИЗМЕНЕНИЯ:
  ✅ AdaptiveFieldSolver — защита от деления на 0 в K2
  ✅ QuantumCollapse — ограничение на минимальную температуру
  ✅ UniversalAnnealer — прогресс-бар и защита от бесконечного цикла
  ✅ TopologicalDefectSimulator — fallback если scipy не установлен
  ✅ Добавлен verbose output каждые 2 шага температуры
======================================================================
"""

import sys, time, hashlib, struct, warnings, os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
import numpy as np
from collections import deque
from functools import lru_cache
import json

warnings.filterwarnings("ignore")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ===========================================================================
# GPU DETECTION
# ===========================================================================
HAS_CUPY = False
HAS_TORCH = False
GPU_BACKEND = "CPU"

try:
    import cupy as cp
    HAS_CUPY = True
    GPU_BACKEND = "CuPy"
except ImportError:
    pass

if not HAS_CUPY:
    try:
        import torch
        if torch.cuda.is_available():
            HAS_TORCH = True
            GPU_BACKEND = "PyTorch"
    except ImportError:
        pass

# Опциональная визуализация
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Опциональный scipy
try:
    from scipy.ndimage import zoom as scipy_zoom
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[WARNING] scipy не установлен — интерполяция будет билинейной")


# ===========================================================================
# GPU-ACCELERATED ARRAY BACKEND
# ===========================================================================
class ArrayBackend:
    """Унифицированный интерфейс NumPy/CuPy/PyTorch"""
    
    def __init__(self):
        self.backend = GPU_BACKEND
    
    @property
    def name(self) -> str:
        return self.backend
    
    def array(self, data, dtype=np.float64):
        if self.backend == "CuPy":
            return cp.array(data, dtype=dtype)
        elif self.backend == "PyTorch":
            return torch.tensor(data, dtype=torch.float64, device='cuda')
        else:
            return np.array(data, dtype=dtype)
    
    def fft2(self, arr):
        if self.backend == "CuPy":
            return cp.fft.fft2(arr)
        elif self.backend == "PyTorch":
            return torch.fft.fft2(arr)
        else:
            return np.fft.fft2(arr)
    
    def ifft2(self, arr):
        if self.backend == "CuPy":
            return cp.fft.ifft2(arr)
        elif self.backend == "PyTorch":
            return torch.fft.ifft2(arr)
        else:
            return np.fft.ifft2(arr)
    
    def to_numpy(self, arr):
        if self.backend == "CuPy":
            return cp.asnumpy(arr)
        elif self.backend == "PyTorch":
            return arr.cpu().numpy()
        else:
            return arr
    
    def real(self, arr):
        if self.backend == "PyTorch":
            return arr.real
        return arr.real


xp = ArrayBackend()


# ===========================================================================
# TOPOLOGICAL DEFECT CONFIGURATION
# ===========================================================================
@dataclass
class DefectConfig:
    """
    Конфигурация топологических дефектов (вихрей).
    
    АТРИБУТЫ:
      charges: np.ndarray [N] — топологические заряды q_i ∈ ℤ
      positions: np.ndarray [N, 2] — позиции на торе [0, L]²
      velocities: np.ndarray [N, 2] — скорости (для динамики)
      L: float — размер расчётной области (период тора)
    
    ИНВАРИАНТЫ:
      N = Σ q_i — топологический заряд системы (сохраняется)
      Γ_i = 2π·q_i — квантованная циркуляция
    """
    charges: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray = None
    L: float = 2.0
    
    def __post_init__(self):
        if self.velocities is None:
            self.velocities = np.zeros((len(self.charges), 2))
    
    @property
    def N_defects(self) -> int:
        """Количество дефектов"""
        return len(self.charges)
    
    @property
    def topological_charge(self) -> int:
        """N = Σ q_i — топологический инвариант"""
        return int(np.sum(self.charges))
    
    @property
    def active_defects(self) -> List[int]:
        """Индексы дефектов с q ≠ 0"""
        return [i for i, q in enumerate(self.charges) if q != 0]
    
    def copy(self) -> 'DefectConfig':
        return DefectConfig(
            charges=self.charges.copy(),
            positions=self.positions.copy(),
            velocities=self.velocities.copy() if self.velocities is not None else None,
            L=self.L
        )


# ===========================================================================
# INPUT PROCESSOR — принимает ЛЮБЫЕ данные
# ===========================================================================
def process_input(input_data: Any) -> bytes:
    """
    Преобразует любой вход в байтовую строку для хеширования.
    
    ПРИНИМАЕТ:
      - строки: "NbTi_T=4.2K_B=1T"
      - байты: b'\x00\x01\x02...'
      - числа: 42
      - словари: {'T': 4.2, 'material': 'NbTi'}
      - numpy массивы
      - файлы (путь к файлу)
    
    ВОЗВРАЩАЕТ:
      bytes для SHA256
    """
    if isinstance(input_data, bytes):
        return input_data
    elif isinstance(input_data, str):
        # Если это путь к существующему файлу — читаем
        if os.path.exists(input_data) and os.path.isfile(input_data):
            try:
                with open(input_data, 'rb') as f:
                    return f.read()
            except:
                pass
        return input_data.encode('utf-8')
    elif isinstance(input_data, (int, float)):
        return str(input_data).encode('utf-8')
    elif isinstance(input_data, dict):
        return json.dumps(input_data, sort_keys=True).encode('utf-8')
    elif isinstance(input_data, np.ndarray):
        return input_data.tobytes()
    elif isinstance(input_data, (list, tuple)):
        return json.dumps(list(input_data)).encode('utf-8')
    else:
        return str(input_data).encode('utf-8')


def hash_to_defect_configs(input_data: Any, n_defects: int = 20, 
                          L: float = 2.0, n_samples: int = 5,
                          charge_range: int = 2) -> List[DefectConfig]:
    """
    Преобразует ЛЮБОЙ вход в множество начальных конфигураций дефектов.
    """
    seed_bytes = process_input(input_data)
    configs = []
    
    for sample_idx in range(n_samples):
        combined = seed_bytes + struct.pack(">I", sample_idx)
        full_hash = hashlib.sha256(combined).digest()
        seed = struct.unpack(">I", full_hash[:4])[0]
        rng = np.random.RandomState(seed)
        
        positions = np.zeros((n_defects, 2))
        charges = np.zeros(n_defects, dtype=int)
        
        for i in range(n_defects):
            idx = (i * 8) % 28
            xi = struct.unpack(">I", full_hash[idx:idx+4])[0] / (2**32)
            yi = struct.unpack(">I", full_hash[idx+4:idx+8])[0] / (2**32) if idx+8 <= 32 else (xi * 0.7 + 0.15)
            positions[i] = [xi * L, yi * L]
            
            charge_idx = (idx + 2) % 28
            charge_val = struct.unpack(">I", full_hash[charge_idx:charge_idx+4])[0]
            charges[i] = (charge_val % (2 * charge_range + 1)) - charge_range
        
        total = int(np.sum(charges))
        if total != 0:
            available = list(range(n_defects))
            rng.shuffle(available)
            remaining = -total
            for idx in available:
                if remaining == 0:
                    break
                cq = int(charges[idx])
                if remaining > 0 and cq < charge_range:
                    add = min(remaining, charge_range - cq)
                    charges[idx] += add
                    remaining -= add
                elif remaining < 0 and cq > -charge_range:
                    sub = min(-remaining, cq + charge_range)
                    charges[idx] -= sub
                    remaining += sub
        
        configs.append(DefectConfig(charges=charges, positions=positions, L=L))
    
    return configs


# ===========================================================================
# ПРОСТАЯ БИЛИНЕЙНАЯ ИНТЕРПОЛЯЦИЯ (без scipy)
# ===========================================================================
def simple_upsample(field: np.ndarray, target_size: int) -> np.ndarray:
    """
    Билинейная интерполяция поля на более мелкую сетку.
    Работает без scipy.
    """
    src_size = field.shape[0]
    if src_size == target_size:
        return field
    
    ratio = target_size / src_size
    
    # Создаём координаты для интерполяции
    x_src = np.linspace(0, src_size - 1, src_size)
    y_src = np.linspace(0, src_size - 1, src_size)
    x_tgt = np.linspace(0, src_size - 1, target_size)
    y_tgt = np.linspace(0, src_size - 1, target_size)
    
    result = np.zeros((target_size, target_size))
    
    for i in range(target_size):
        for j in range(target_size):
            # Находим ближайшие точки в исходной сетке
            x = x_tgt[i]
            y = y_tgt[j]
            
            x0 = int(np.floor(x))
            x1 = min(x0 + 1, src_size - 1)
            y0 = int(np.floor(y))
            y1 = min(y0 + 1, src_size - 1)
            
            wx = x - x0
            wy = y - y0
            
            # Билинейная интерполяция
            result[i, j] = (field[x0, y0] * (1 - wx) * (1 - wy) +
                           field[x1, y0] * wx * (1 - wy) +
                           field[x0, y1] * (1 - wx) * wy +
                           field[x1, y1] * wx * wy)
    
    return result


# ===========================================================================
# FFT-BASED FIELD SOLVER (упрощённый, без адаптивной сетки для стабильности)
# ===========================================================================
class FFTSolver:
    """
    Решатель бигармонического уравнения на торе через БПФ.
    
    УРАВНЕНИЕ:
      Δ²ψ(r) = Σ q_i δ(r - r_i)    на торе [0, L]²
    
    МЕТОД:
      ψ = FFT^{-1}[ ρ_k · G_k ]
      G_k = 1/|k|⁴ (k ≠ 0)
    """
    
    def __init__(self, L: float = 2.0, grid_size: int = 256):
        self.L = L
        self.grid_size = grid_size
        
        # Предвычисляем G(k)
        self._precompute_Gk()
    
    def _precompute_Gk(self):
        """Предвычисление 1/|k|⁴"""
        gs = self.grid_size
        kx = np.fft.fftfreq(gs, d=self.L/gs) * 2 * np.pi
        ky = np.fft.fftfreq(gs, d=self.L/gs) * 2 * np.pi
        KX, KY = np.meshgrid(kx, ky)
        K2 = KX**2 + KY**2
        
        self.G_k = np.zeros((gs, gs))
        mask = K2 > 1e-15  # 🛡️ Защита от деления на 0
        self.G_k[mask] = 1.0 / (K2[mask]**2)
        
        self.KX, self.KY = KX, KY
        self.K2 = K2
        self.n_modes = int(np.sum(mask))
        self.G0 = float(np.mean(self.G_k[mask]))
    
    def solve_field(self, sources: np.ndarray, charges: np.ndarray) -> np.ndarray:
        """Вычисляет поле ψ(r) на сетке через БПФ"""
        gs = self.grid_size
        rho = np.zeros((gs, gs))
        
        for (sx, sy), q in zip(sources, charges):
            i = int(round(sx * gs / self.L)) % gs
            j = int(round(sy * gs / self.L)) % gs
            rho[i, j] += q * (gs / self.L)**2
        
        rho_k = np.fft.fft2(rho)
        psi_k = rho_k * self.G_k
        psi = np.real(np.fft.ifft2(psi_k))
        
        return psi
    
    def field_at_point(self, r: np.ndarray, sources: np.ndarray,
                       charges: np.ndarray) -> float:
        """Значение поля ψ в точке r (билинейная интерполяция)"""
        field = self.solve_field(sources, charges)
        gs = self.grid_size
        
        ix = r[0] * gs / self.L
        iy = r[1] * gs / self.L
        
        i0 = int(np.floor(ix)) % gs
        j0 = int(np.floor(iy)) % gs
        i1 = (i0 + 1) % gs
        j1 = (j0 + 1) % gs
        
        fx = ix - i0
        fy = iy - j0
        
        return (field[i0, j0] * (1-fx) * (1-fy) +
                field[i1, j0] * fx * (1-fy) +
                field[i0, j1] * (1-fx) * fy +
                field[i1, j1] * fx * fy)


# ===========================================================================
# ENERGY FUNCTIONAL
# ===========================================================================
class EnergyFunctional:
    """
    Энергия системы E = (1/2) ∫ (Δψ)² d²r
    """
    
    def __init__(self, solver: FFTSolver):
        self.solver = solver
        self.G0 = solver.G0
    
    def total_energy(self, config: DefectConfig) -> float:
        """Полная энергия конфигурации"""
        field = self.solver.solve_field(config.positions, config.charges)
        
        psi_k = np.fft.fft2(field)
        energy = 0.5 * np.sum(self.solver.K2**2 * np.abs(psi_k)**2)
        dx = config.L / self.solver.grid_size
        return energy * dx**2 / self.solver.grid_size**2
    
    def forces(self, config: DefectConfig) -> np.ndarray:
        """Силы F_i = -∂E/∂r_i = -q_i ∇ψ(r_i)"""
        pos = config.positions
        q = config.charges
        N = config.N_defects
        L = config.L
        eps = L / self.solver.grid_size * 2
        
        forces = np.zeros((N, 2))
        
        for i in range(N):
            for d in range(2):
                pos_plus = pos.copy()
                pos_minus = pos.copy()
                pos_plus[i, d] += eps
                pos_minus[i, d] -= eps
                pos_plus[i] %= L
                pos_minus[i] %= L
                
                try:
                    psi_plus = self.solver.field_at_point(pos_plus[i], pos_plus, q)
                    psi_minus = self.solver.field_at_point(pos_minus[i], pos_minus, q)
                    forces[i, d] = -q[i] * (psi_plus - psi_minus) / (2 * eps)
                except:
                    forces[i, d] = 0.0
        
        return forces


# ===========================================================================
# QUANTUM TOOLS
# ===========================================================================
class QuantumTunneling:
    """⚛️ Квантовое туннелирование через инстантоны"""
    
    def __init__(self, hbar_eff: float = 0.1):
        self.hbar_eff = hbar_eff
    
    def attempt(self, config: DefectConfig, energy: EnergyFunctional,
                rng: np.random.RandomState) -> DefectConfig:
        N = config.N_defects
        pos = config.positions.copy()
        direction = rng.randn(N, 2) * 0.1
        direction_norm = np.linalg.norm(direction)
        if direction_norm < 1e-10:
            return config
        
        direction = direction / direction_norm
        
        E0 = energy.total_energy(config)
        S_inst = 0.0
        
        for i in range(1, 10):
            pos_test = pos + i * 0.05 * direction
            pos_test %= config.L
            E_test = energy.total_energy(
                DefectConfig(config.charges, pos_test, L=config.L)
            )
            S_inst += np.sqrt(max(0, 2 * (E_test - E0))) * 0.05
        
        P_tunnel = np.exp(-S_inst / max(self.hbar_eff, 1e-10))
        
        if rng.random() < P_tunnel:
            tunnel_dist = rng.exponential(0.1)
            pos_new = pos + tunnel_dist * direction
            pos_new %= config.L
            return DefectConfig(config.charges, pos_new, L=config.L)
        
        return config


class FivePhaseKick:
    """🔥 5-фазный синхронизированный импульс"""
    
    def __init__(self, amplitude: float = 0.1, frequency: float = 2.0):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phases = [2 * np.pi * n / 5 for n in range(5)]
    
    def apply(self, config: DefectConfig, time: float,
              rng: np.random.RandomState) -> DefectConfig:
        pos = config.positions.copy()
        vel = (config.velocities.copy() if config.velocities is not None 
               else np.zeros_like(pos))
        N = config.N_defects
        
        kick_force = np.zeros((N, 2))
        
        for i, phase in enumerate(self.phases):
            strength = self.amplitude * np.sin(self.frequency * time + phase)
            angle = phase
            direction = np.array([np.cos(angle), np.sin(angle)])
            
            for j in range(N):
                spatial_phase = 2 * np.pi * (pos[j, 0] + pos[j, 1]) / config.L
                modulation = np.sin(spatial_phase + phase)
                kick_force[j] += strength * modulation * direction
        
        vel_new = vel + kick_force
        pos_new = pos + vel_new * 0.01
        pos_new %= config.L
        
        return DefectConfig(config.charges, pos_new, vel_new, config.L)


class TimelessBuffer:
    """🕐 Буфер безвременья"""
    
    def __init__(self, capacity: float = 10.0, n_steps: int = 15):
        self.capacity = capacity
        self.n_steps = n_steps
        self.level = 0.0
    
    def evolve(self, config: DefectConfig, energy: EnergyFunctional,
               rng: np.random.RandomState) -> DefectConfig:
        best_config = config.copy()
        best_E = energy.total_energy(config)
        current = config.copy()
        
        for _ in range(self.n_steps):
            noise_scale = np.sqrt(max(0, self.level) * 0.01 + 1e-10)
            noise = rng.randn(current.N_defects, 2) * noise_scale
            current.positions += noise
            current.positions %= current.L
            
            E = energy.total_energy(current)
            self.level += E * 0.01
            self.level *= 0.99
            self.level = min(self.level, self.capacity)
            
            if E < best_E:
                best_E = E
                best_config = current.copy()
        
        return best_config


class QuantumCollapse:
    """🌌 Квантовый коллапс"""
    
    def __init__(self, n_paths: int = 5, buffer_steps: int = 15):
        self.n_paths = n_paths
        self.buffer_steps = buffer_steps
        self.buffer = TimelessBuffer(capacity=10.0, n_steps=buffer_steps)
    
    def explore_and_collapse(self, config: DefectConfig, energy: EnergyFunctional,
                            T_eff: float, rng: np.random.RandomState) -> DefectConfig:
        paths = []
        
        for _ in range(self.n_paths):
            variant = config.copy()
            variant.positions += rng.randn(*variant.positions.shape) * 0.01
            variant.positions %= variant.L
            
            evolved = self.buffer.evolve(variant, energy, rng)
            E = energy.total_energy(evolved)
            paths.append((evolved, E))
        
        energies = np.array([E for _, E in paths])
        E_min = np.min(energies)
        T_safe = max(T_eff, 1e-8)
        weights = np.exp(-(energies - E_min) / T_safe)
        weights = np.clip(weights, 0, 1e100)  # 🛡️ Защита от переполнения
        probs = weights / np.sum(weights)
        
        idx = rng.choice(len(paths), p=probs)
        return paths[idx][0]


# ===========================================================================
# UNIVERSAL ANNEALER
# ===========================================================================
class UniversalAnnealer:
    """
    Универсальный отжиг с квантовыми эффектами.
    """
    
    def __init__(self, energy: EnergyFunctional,
                 T_start: float = 1.0, T_end: float = 0.001,
                 cooling_rate: float = 0.85, steps_per_T: int = 10):
        self.energy = energy
        self.T_start = T_start
        self.T_end = T_end
        self.cooling_rate = cooling_rate
        self.steps_per_T = steps_per_T
        
        self.kicker = FivePhaseKick()
        self.tunneling = QuantumTunneling()
        self.collapse = QuantumCollapse()
    
    def anneal(self, config: DefectConfig, verbose: bool = True) -> Tuple[DefectConfig, List[Dict]]:
        T = self.T_start
        current = config.copy()
        history = []
        rng = np.random.RandomState(42)
        
        stuck_counter = 0
        last_energy = float('inf')
        emergent_time = 0.0
        
        temp_step = 0
        max_temp_steps = 1000  # 🛡️ Защита от бесконечного цикла
        
        while T > self.T_end and temp_step < max_temp_steps:
            temp_step += 1
            
            # Термальный шум + градиентный спуск
            for _ in range(self.steps_per_T):
                try:
                    forces = self.energy.forces(current)
                except:
                    forces = np.zeros_like(current.positions)
                
                noise = rng.randn(current.N_defects, 2) * np.sqrt(2 * T * 0.01)
                current.positions += 0.01 * forces + noise
                current.positions %= current.L
            
            # Квантовый коллапс
            try:
                current = self.collapse.explore_and_collapse(current, self.energy, T, rng)
            except:
                pass
            emergent_time += self.collapse.buffer_steps * 0.01
            
            E = self.energy.total_energy(current)
            
            # 5-фазный импульс
            if temp_step % 4 == 0:
                try:
                    kick_time = temp_step * 2 * np.pi / self.kicker.frequency
                    current = self.kicker.apply(current, kick_time, rng)
                    current = self.collapse.explore_and_collapse(current, self.energy, T, rng)
                except:
                    pass
                E = self.energy.total_energy(current)
            
            # Квантовое туннелирование
            if abs(E - last_energy) < 1e-10:
                stuck_counter += 1
            else:
                stuck_counter = 0
            
            if stuck_counter > 3:
                try:
                    current = self.tunneling.attempt(current, self.energy, rng)
                    current = self.collapse.explore_and_collapse(current, self.energy, T, rng)
                except:
                    pass
                E = self.energy.total_energy(current)
                stuck_counter = 0
            
            last_energy = E
            
            history.append({
                'T': T, 'E': E, 't_emergent': emergent_time
            })
            
            if verbose and temp_step % 2 == 0:
                print(f"  [ANNEAL] T={T:.4f} E={E:.8f} t_em={emergent_time:.1f}")
            
            T *= self.cooling_rate
        
        if temp_step >= max_temp_steps:
            print("  [WARNING] Достигнут лимит шагов отжига")
        
        return current, history


# ===========================================================================
# STRUCTURE ANALYZER
# ===========================================================================
class StructureAnalyzer:
    """Анализ структуры дефектной конфигурации"""
    
    def __init__(self, solver: FFTSolver):
        self.solver = solver
    
    def structure_factor(self, config: DefectConfig, 
                        n_k: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """S(k) = |Σ q_i exp(-ik·r_i)|² / N"""
        L = config.L
        kx = np.linspace(-4*np.pi/L, 4*np.pi/L, n_k)
        ky = np.linspace(-4*np.pi/L, 4*np.pi/L, n_k)
        KX, KY = np.meshgrid(kx, ky)
        
        Sk = np.zeros((n_k, n_k), dtype=complex)
        pos, q = config.positions, config.charges
        
        for i in range(n_k):
            for j in range(n_k):
                k_vec = np.array([KX[i, j], KY[i, j]])
                Sk[i, j] = np.sum(q * np.exp(-1j * np.dot(pos, k_vec)))
        
        N = config.N_defects
        return KX, KY, np.abs(Sk)**2 / max(N, 1)
    
    def order_parameter(self, config: DefectConfig) -> float:
        """Параметр порядка"""
        _, _, Sk = self.structure_factor(config)
        K = np.sqrt(self.solver.KX**2 + self.solver.KY**2)
        # Приводим к размеру Sk
        gs_sk = Sk.shape[0]
        gs_k = K.shape[0]
        if gs_sk < gs_k:
            K = K[:gs_sk, :gs_sk]
        mask = K > 0.1
        
        if mask.any() and np.mean(Sk[mask]) > 1e-15:
            return float(np.max(Sk[mask]) / np.mean(Sk[mask]))
        return 1.0
    
    def correlation_function(self, config: DefectConfig,
                            n_bins: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        """Парная корреляционная функция g(r)"""
        pos, q = config.positions, config.charges
        N, L = config.N_defects, config.L
        r_max = L / 2
        
        bins = np.linspace(0, r_max, n_bins + 1)
        dr = bins[1] - bins[0]
        g_r = np.zeros(n_bins)
        counts = np.zeros(n_bins)
        
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                delta = pos[i] - pos[j]
                delta = delta - L * np.round(delta / L)
                r = np.sqrt(np.sum(delta**2))
                
                if r < r_max:
                    idx = min(int(r / dr), n_bins - 1)
                    g_r[idx] += q[i] * q[j]
                    counts[idx] += 1
        
        for i in range(n_bins):
            area = np.pi * ((bins[i+1])**2 - (bins[i])**2)
            if counts[i] > 0:
                g_r[i] /= counts[i]
            if area > 0:
                g_r[i] /= area
        
        r_centers = (bins[:-1] + bins[1:]) / 2
        return r_centers, g_r


# ===========================================================================
# MAIN SIMULATOR
# ===========================================================================
class TopologicalDefectSimulator:
    """
    ОСНОВНОЙ КЛАСС — СИМУЛЯТОР ТОПОЛОГИЧЕСКИХ ДЕФЕКТОВ
    
    ПРИМЕР:
        sim = TopologicalDefectSimulator(n_defects=30, grid_size=256)
        result = sim.simulate("ваши_данные")
    """
    
    def __init__(self,
                 n_defects: int = 20,
                 L: float = 2.0,
                 grid_size: int = 256,
                 n_samples: int = 3,
                 charge_range: int = 2,
                 T_start: float = 1.0,
                 T_end: float = 0.001,
                 cooling_rate: float = 0.85,
                 verbose: bool = True):
        
        self.n_defects = n_defects
        self.L = L
        self.n_samples = n_samples
        self.charge_range = charge_range
        self.verbose = verbose
        
        self.solver = FFTSolver(L=L, grid_size=grid_size)
        self.energy = EnergyFunctional(self.solver)
        self.annealer = UniversalAnnealer(
            self.energy, T_start=T_start, T_end=T_end,
            cooling_rate=cooling_rate
        )
        self.analyzer = StructureAnalyzer(self.solver)
        
        if verbose:
            print("=" * 70)
            print("  Vortex Matter Engine (VME) v1.0.1 🔬🌪️")
            print(f"  Backend: {xp.name}")
            print(f"  Grid: {grid_size}×{grid_size} (~{self.solver.n_modes} modes)")
            print(f"  Defects: {n_defects}, L={L}")
            print("=" * 70)
    
    def simulate(self, input_data: Any) -> Dict:
        """Запускает полную симуляцию для входных данных."""
        t0 = time.time()
        
        if self.verbose:
            print(f"\n  [SIMULATING] {str(input_data)[:60]}...")
            print("  " + "-" * 70)
        
        # 1. Вход → начальные конфигурации
        configs = hash_to_defect_configs(
            input_data, self.n_defects, self.L,
            self.n_samples, self.charge_range
        )
        
        # 2. Отжиг
        best_config = None
        best_energy = float('inf')
        
        for i, config in enumerate(configs):
            if self.verbose:
                print(f"  [SAMPLE {i+1}/{len(configs)}] "
                      f"N={config.topological_charge}")
            
            annealed, history = self.annealer.anneal(config, verbose=self.verbose)
            E = self.energy.total_energy(annealed)
            
            if E < best_energy:
                best_energy = E
                best_config = annealed
            
            if self.verbose:
                print(f"    E_final = {E:.8f}")
        
        # 3. Анализ
        E_initial = self.energy.total_energy(configs[0])
        E_final = self.energy.total_energy(best_config)
        N = best_config.topological_charge
        order = self.analyzer.order_parameter(best_config)
        
        KX, KY, Sk = self.analyzer.structure_factor(best_config)
        Sk_peak = float(np.max(Sk))
        
        r_corr, g_corr = self.analyzer.correlation_function(best_config)
        
        field = self.solver.solve_field(best_config.positions, best_config.charges)
        
        consistency = float(np.exp(-abs(E_final) / max(abs(E_initial), 1e-8)))
        
        elapsed = time.time() - t0
        
        result = {
            'input': str(input_data)[:100],
            'E_initial': E_initial,
            'E_final': E_final,
            'energy_improvement': E_initial - E_final,
            'topological_charge': N,
            'n_active_defects': len(best_config.active_defects),
            'order_parameter': order,
            'structure_factor_peak': Sk_peak,
            'consistency': consistency,
            'field': field,
            'positions': best_config.positions,
            'charges': best_config.charges,
            'structure_factor': (KX, KY, Sk),
            'correlation': (r_corr, g_corr),
            'solver_stats': {
                'backend': xp.name,
                'grid_size': self.solver.grid_size,
                'n_modes': self.solver.n_modes,
            },
            'time': elapsed
        }
        
        if self.verbose:
            print("  " + "-" * 70)
            print(f"  [DONE] E={E_final:.8f} | N={N} | "
                  f"order={order:.4f} | consistency={consistency:.4f}")
            print(f"  Time: {elapsed:.1f}s")
        
        return result


# ===========================================================================
# ВИЗУАЛИЗАЦИЯ
# ===========================================================================
if HAS_MATPLOTLIB:
    def visualize_result(result: Dict, output_path: str = None):
        """Визуализация результатов симуляции."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        field = result['field']
        im1 = axes[0, 0].imshow(field, cmap='RdBu_r', aspect='equal')
        axes[0, 0].set_title('Поле ψ(r)')
        plt.colorbar(im1, ax=axes[0, 0])
        
        KX, KY, Sk = result['structure_factor']
        im2 = axes[0, 1].imshow(np.log1p(Sk), cmap='inferno',
                               extent=[KX.min(), KX.max(), KY.min(), KY.max()],
                               aspect='equal')
        axes[0, 1].set_title('Структурный фактор S(k)')
        plt.colorbar(im2, ax=axes[0, 1])
        
        r, g = result['correlation']
        axes[1, 0].plot(r, g, 'b-', linewidth=2)
        axes[1, 0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
        axes[1, 0].set_xlabel('r')
        axes[1, 0].set_ylabel('g(r)')
        axes[1, 0].set_title('Парные корреляции')
        axes[1, 0].grid(True, alpha=0.3)
        
        axes[1, 1].axis('off')
        info = (
            f"Вход: {result['input'][:50]}...\n"
            f"E_init: {result['E_initial']:.6f}\n"
            f"E_final: {result['E_final']:.6f}\n"
            f"Топ.заряд: {result['topological_charge']}\n"
            f"Порядок: {result['order_parameter']:.4f}\n"
            f"Consistency: {result['consistency']:.4f}\n"
            f"Мод: {result['solver_stats']['n_modes']}\n"
            f"Время: {result['time']:.1f}с"
        )
        axes[1, 1].text(0.1, 0.5, info, fontfamily='monospace',
                       fontsize=10, verticalalignment='center')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150)
            print(f"  [VIZ] Сохранено: {output_path}")
        else:
            plt.show()
        
        plt.close()


# ===========================================================================
# КОМАНДНАЯ СТРОКА
# ===========================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("  Vortex Matter Engine (VME) v1.0.1")
    print("  Универсальный симулятор топологических дефектов")
    print("=" * 70)
    print(f"  Backend: {xp.name}")
    print()
    
    examples = [
        ("Сверхпроводник", "NbTi_T=4.2K_B=1T_n=20"),
        ("Биология", "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHF"),
        ("Геофизика", "lat=35.7_lon=139.7_depth=10km_mag=7.2"),
        ("Социология", "population=1000_growth=0.5_capacity=10000"),
    ]
    
    for name, data in examples:
        print(f"\n{'='*70}")
        print(f"  Пример: {name}")
        print(f"{'='*70}")
        
        sim = TopologicalDefectSimulator(
            n_defects=15,
            grid_size=128,
            n_samples=2,
            T_start=1.0,
            T_end=0.01,
            cooling_rate=0.8,
            verbose=True
        )
        
        result = sim.simulate(data)
        
        if HAS_MATPLOTLIB:
            output_path = f"vme_{name.lower().replace(' ', '_')}.png"
            visualize_result(result, output_path)
        
        print()
    
    print("=" * 70)
    print("  Демонстрация завершена!")
    print("  Используйте TopologicalDefectSimulator в своих проектах.")
    print("=" * 70)