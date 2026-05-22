#!/usr/bin/env python3
"""
family_vortex_v4.py — Ризоматическая эволюция без подгоночных параметров.

Принципы:
- Поле: ∇⁴ψ = 0 (бигармоническое)
- Топология: ∮∇ψ·dl = 2πN (winding number — сохраняется)
- Пульс: Эмерджентное время (модель Курамото, фазовая синхронизация)
- Действие: S = ∫(T - V)dt, бифуркации при ∂²S/∂x² = 0
- Память: Чекпойнты при нарушении инвариантов
- Нет центра: связь только через поле H
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ (единственные во всей модели)
# ═══════════════════════════════════════════════════════════════

HBAR_EFF = 1.0               # квант действия в конденсате
OMEGA_0 = 2.0 * math.pi      # базовая частота пульса
K_POINTS = 20                # точек на период для адаптивного dt
RESONANCE_THRESHOLD = math.pi / 4  # порог синхронизации (45°)
SYNC_DANGER = 0.95           # порог опасной синхронизации
WINDING_JUMP_THRESHOLD = 0.5 # скачок winding → чекпойнт

# ═══════════════════════════════════════════════════════════════
# ВИХРЕВОЙ КЛАСТЕР
# ═══════════════════════════════════════════════════════════════

class VortexCluster:
    """Вихревой кластер — сингулярность в бигармоническом поле."""

    def __init__(self, birth_time: datetime, birth_position: Tuple[float, float, float],
                 tau_charges: List[float], name: str = "Cluster",
                 fractal_level: int = 1,
                 exchange_potential: float = 0.5,
                 parent_name: str = None,
                 seed: int = None):
        self.name = name
        self.birth_time = birth_time
        self.birth_position = np.array(birth_position, dtype=np.float64)
        self.tau_charges = tau_charges.copy()
        self.original_tau_charges = tau_charges.copy()
        self.n_vortices = len(tau_charges)
        self.fractal_level = fractal_level
        self.time_scale = 2.0 ** (fractal_level - 1)
        self.exchange_potential = exchange_potential
        self.parent_name = parent_name

        self.tension = 0.0
        self.strain = 0.0
        self.capacity = 1.0
        self.dissolved = False
        self.dissolution_step: Optional[int] = None
        self.born = False
        self.merged_into: Optional[str] = None

        self.bifurcation_count = 0
        self.bifurcation_history: List[Dict] = []

        if seed is None:
            seed = abs(hash(birth_time.isoformat())) % (2**31 - 1)
        self.rng = np.random.RandomState(seed)

        self.positions = np.array([
            self.birth_position + self.rng.randn(3) * 0.5
            for _ in range(self.n_vortices)
        ], dtype=np.float64)

        self.exchange_history: List[Dict] = []
        self.total_given = 0.0
        self.total_received = 0.0
        self.total_absorbed_from_field = 0.0
        self.energy_history: List[float] = []
        self.tension_history: List[float] = []
        self.strain_history: List[float] = []
        self.capacity_history: List[float] = []
        self.winding_number: Optional[float] = None
        self.winding_history: List[float] = []

    def total_charge(self) -> float:
        return sum(abs(t) for t in self.tau_charges)

    def total_original_charge(self) -> float:
        return sum(abs(t) for t in self.original_tau_charges)

    def get_center(self) -> np.ndarray:
        return np.mean(self.positions[:self.n_vortices], axis=0)

    def get_radius(self) -> float:
        if self.n_vortices < 2:
            return 1.0
        center = self.get_center()
        return float(np.mean([np.linalg.norm(p - center) 
                              for p in self.positions[:self.n_vortices]]))

# ═══════════════════════════════════════════════════════════════
# БИГАРМОНИЧЕСКОЕ ПОЛЕ
# ═══════════════════════════════════════════════════════════════

class BiharmonicField:
    """Бигармоническое поле ψ: ∂ψ/∂t = -∇⁴ψ + источники - γψ."""

    def __init__(self, box_size: float = 16.0, grid_size: int = 32, gamma: float = 0.01):
        self.box_size = box_size
        self.grid_size = grid_size
        self.dx = box_size / grid_size
        self.gamma = gamma

        self.psi = np.zeros((grid_size, grid_size, grid_size))
        self.absorbed_energy = 0.0

        k = np.fft.fftfreq(grid_size, d=self.dx) * 2 * np.pi
        Kx, Ky, Kz = np.meshgrid(k, k, k, indexing='ij')
        self.k_squared = Kx**2 + Ky**2 + Kz**2
        self.k_biharmonic = self.k_squared**2
        self.k_biharmonic[0, 0, 0] = 1.0

    def _grid_positions(self, positions_list, charges_list):
        rho = np.zeros((self.grid_size, self.grid_size, self.grid_size))
        for positions, charges in zip(positions_list, charges_list):
            for pos, charge in zip(positions, charges):
                i = int(pos[0] / self.dx) % self.grid_size
                j = int(pos[1] / self.dx) % self.grid_size
                k = int(pos[2] / self.dx) % self.grid_size
                rho[i, j, k] += charge
        return rho

    def solve_stationary(self, positions_list, charges_list):
        rho = self._grid_positions(positions_list, charges_list)
        rho_hat = np.fft.fftn(rho)
        psi_hat = rho_hat / self.k_biharmonic
        psi_hat[0, 0, 0] = 0.0
        self.psi = np.real(np.fft.ifftn(psi_hat))

    def evolve(self, positions_list, charges_list, tensions, dt=0.1):
        rho = np.zeros((self.grid_size, self.grid_size, self.grid_size))
        for positions, charges, tension in zip(positions_list, charges_list, tensions):
            effective = np.clip(charges * (1.0 + tension), -10.0, 10.0)
            for pos, charge in zip(positions, effective):
                i = int(pos[0] / self.dx) % self.grid_size
                j = int(pos[1] / self.dx) % self.grid_size
                k = int(pos[2] / self.dx) % self.grid_size
                rho[i, j, k] += charge

        psi_hat = np.fft.fftn(self.psi)
        rho_hat = np.fft.fftn(rho)
        eff_gamma = self.gamma * (1.0 + np.max(np.abs(self.psi)) / 10.0)

        numerator = psi_hat + dt * rho_hat
        denominator = 1.0 + dt * (self.k_biharmonic + eff_gamma)
        denominator[0, 0, 0] = 1.0

        psi_hat_new = numerator / denominator
        psi_hat_new[0, 0, 0] = 0.0
        self.psi = np.real(np.fft.ifftn(psi_hat_new))

    def get_gradient_at(self, position: np.ndarray) -> np.ndarray:
        x, y, z = position / self.dx
        i0 = int(np.floor(x)) % self.grid_size
        j0 = int(np.floor(y)) % self.grid_size
        k0 = int(np.floor(z)) % self.grid_size
        i1 = (i0 + 1) % self.grid_size
        j1 = (j0 + 1) % self.grid_size
        k1 = (k0 + 1) % self.grid_size

        fx, fy, fz = x - i0, y - j0, z - k0

        v000=self.psi[i0,j0,k0]; v100=self.psi[i1,j0,k0]
        v010=self.psi[i0,j1,k0]; v110=self.psi[i1,j1,k0]
        v001=self.psi[i0,j0,k1]; v101=self.psi[i1,j0,k1]
        v011=self.psi[i0,j1,k1]; v111=self.psi[i1,j1,k1]

        gx = ((1-fy)*(1-fz)*v100 + fy*(1-fz)*v110 + (1-fy)*fz*v101 + fy*fz*v111
              - (1-fy)*(1-fz)*v000 - fy*(1-fz)*v010 - (1-fy)*fz*v001 - fy*fz*v011) / self.dx
        gy = ((1-fx)*(1-fz)*v010 + fx*(1-fz)*v110 + (1-fx)*fz*v011 + fx*fz*v111
              - (1-fx)*(1-fz)*v000 - fx*(1-fz)*v100 - (1-fx)*fz*v001 - fx*fz*v101) / self.dx
        gz = ((1-fx)*(1-fy)*v001 + fx*(1-fy)*v101 + (1-fx)*fy*v011 + fx*fy*v111
              - (1-fx)*(1-fy)*v000 - fx*(1-fy)*v100 - (1-fx)*fy*v010 - fx*fy*v110) / self.dx

        return np.array([gx, gy, gz])

    def get_field_value_at(self, position: np.ndarray) -> float:
        x, y, z = position / self.dx
        i0 = int(np.floor(x)) % self.grid_size
        j0 = int(np.floor(y)) % self.grid_size
        k0 = int(np.floor(z)) % self.grid_size
        i1, j1, k1 = (i0+1)%self.grid_size, (j0+1)%self.grid_size, (k0+1)%self.grid_size
        fx, fy, fz = x - i0, y - j0, z - k0

        return ((1-fx)*(1-fy)*(1-fz)*self.psi[i0,j0,k0] +
                fx*(1-fy)*(1-fz)*self.psi[i1,j0,k0] +
                (1-fx)*fy*(1-fz)*self.psi[i0,j1,k0] +
                fx*fy*(1-fz)*self.psi[i1,j1,k0] +
                (1-fx)*(1-fy)*fz*self.psi[i0,j0,k1] +
                fx*(1-fy)*fz*self.psi[i1,j0,k1] +
                (1-fx)*fy*fz*self.psi[i0,j1,k1] +
                fx*fy*fz*self.psi[i1,j1,k1])

    def get_energy_density_at(self, position: np.ndarray) -> float:
        g = self.get_gradient_at(position)
        return float(np.dot(g, g))

# ═══════════════════════════════════════════════════════════════
# ТОПОЛОГИЧЕСКИЙ ИНВАРИАНТ: WINDING NUMBER
# ═══════════════════════════════════════════════════════════════

def compute_winding(center: np.ndarray, radius: float, 
                    field: BiharmonicField, n_points: int = 36) -> Tuple[float, float]:
    """Winding number и его вариация по нескольким окружностям."""
    angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
    radii = np.linspace(radius*0.5, radius*1.5, 3)
    windings = []
    
    for r in radii:
        points = center + np.array([[r*np.cos(a), r*np.sin(a), 0.0] for a in angles])
        grads = np.array([field.get_gradient_at(p) for p in points])
        g_angles = np.arctan2(grads[:,1], grads[:,0])
        
        w = 0.0
        for i in range(n_points):
            diff = g_angles[(i+1)%n_points] - g_angles[i]
            diff = (diff + np.pi) % (2*np.pi) - np.pi
            w += diff
        windings.append(w / (2*np.pi))
    
    return float(np.mean(windings)), float(np.std(windings))

# ═══════════════════════════════════════════════════════════════
# ПУЛЬС: ЭМЕРДЖЕНТНОЕ ВРЕМЯ (МОДЕЛЬ КУРАМОТО)
# ═══════════════════════════════════════════════════════════════

class Pulse:
    """Пульс одного кластера — его локальное время."""
    
    def __init__(self, name: str, total_charge: float, 
                 capacity: float = 1.0, strain: float = 0.0,
                 phase: Optional[float] = None):
        self.name = name
        self.total_charge = abs(total_charge)
        self.capacity = capacity
        self.strain = strain
        self.phase = phase if phase is not None else np.random.random() * 2*np.pi
        self.frequency = self._compute_freq()
        self.history: List[float] = [self.phase]
    
    def _compute_freq(self) -> float:
        charge_f = np.sqrt(max(self.total_charge, 0.01))
        health = self.capacity * max(1.0 - self.strain, 0.01)
        return OMEGA_0 * charge_f * health
    
    def update(self, capacity: float, strain: float):
        self.capacity = capacity
        self.strain = strain
        self.frequency = self._compute_freq()
    
    def evolve(self, dt: float, coupling: float = 0.0):
        self.phase = (self.phase + self.frequency*dt + coupling*dt) % (2*np.pi)
        self.history.append(self.phase)
    
    def state(self) -> complex:
        return np.exp(1j * self.phase)
    
    def phase_diff(self, other: 'Pulse') -> float:
        d = abs(self.phase - other.phase) % (2*np.pi)
        return min(d, 2*np.pi - d)


class PulseClock:
    """Эмерджентные часы всей системы."""
    
    def __init__(self):
        self._pulses: Dict[str, Pulse] = {}
    
    def add(self, name: str, charge: float, capacity: float = 1.0, 
            strain: float = 0.0, phase: Optional[float] = None):
        self._pulses[name] = Pulse(name, charge, capacity, strain, phase)
    
    def remove(self, name: str):
        self._pulses.pop(name, None)
    
    def get(self, name: str) -> Optional[Pulse]:
        return self._pulses.get(name)
    
    def active(self) -> List[Pulse]:
        return list(self._pulses.values())
    
    def compute_dt(self) -> float:
        active = self.active()
        if not active:
            return 0.1
        omega_max = max(p.frequency for p in active)
        if omega_max < 1e-6:
            return 0.1
        return 2*np.pi / (omega_max * K_POINTS)
    
    def synchronization(self) -> float:
        """Параметр порядка Курамото: 0 = хаос, 1 = полная синхронизация."""
        active = self.active()
        if not active:
            return 0.0
        order = np.sum([p.state() for p in active])
        return float(abs(order) / len(active))
    
    def evolve_all(self, field: BiharmonicField, positions: Dict[str, np.ndarray]):
        """Эволюция всех пульсов с coupling через поле."""
        dt = self.compute_dt()
        names = list(self._pulses.keys())
        
        for i, name_i in enumerate(names):
            pulse_i = self._pulses[name_i]
            pos_i = positions.get(name_i)
            if pos_i is None:
                pulse_i.evolve(dt, 0.0)
                continue
            
            coupling = 0.0
            for j, name_j in enumerate(names):
                if i >= j:
                    continue
                pulse_j = self._pulses[name_j]
                pos_j = positions.get(name_j)
                if pos_j is None:
                    continue
                
                mid = (pos_i + pos_j) / 2
                grad_mag = float(np.linalg.norm(field.get_gradient_at(mid)))
                dist = float(np.linalg.norm(pos_i - pos_j))
                if dist < 1e-6:
                    continue
                
                dphi = pulse_j.phase - pulse_i.phase
                coupling += grad_mag / dist * np.sin(dphi)
            
            pulse_i.evolve(dt, coupling)

# ═══════════════════════════════════════════════════════════════
# ВАРИАЦИОННЫЙ ПРИНЦИП: ДЕЙСТВИЕ И БИФУРКАЦИИ
# ═══════════════════════════════════════════════════════════════

class ActionAnalyzer:
    """Анализ действия S = ∫(T-V)dt и детектирование бифуркаций."""
    
    def __init__(self):
        self._prev_d2S: Optional[float] = None
    
    def second_derivative(self, cluster: VortexCluster, 
                          field: BiharmonicField,
                          direction: np.ndarray,
                          epsilon: float = 0.1) -> float:
        """∂²S/∂x² конечной разностью."""
        center = cluster.get_center()
        saved = cluster.positions.copy()
        
        shift = direction / (np.linalg.norm(direction) + 1e-6) * epsilon
        
        cluster.positions = saved + shift
        V_plus = sum(abs(cluster.tau_charges[i]) * 
                     field.get_field_value_at(cluster.positions[i])
                     for i in range(cluster.n_vortices))
        
        cluster.positions = saved
        V_0 = sum(abs(cluster.tau_charges[i]) * 
                  field.get_field_value_at(cluster.positions[i])
                  for i in range(cluster.n_vortices))
        
        cluster.positions = saved - shift
        V_minus = sum(abs(cluster.tau_charges[i]) * 
                      field.get_field_value_at(cluster.positions[i])
                      for i in range(cluster.n_vortices))
        
        cluster.positions = saved
        return (V_plus - 2*V_0 + V_minus) / (epsilon**2)
    
    def detect(self, cluster: VortexCluster, 
               field: BiharmonicField) -> Tuple[bool, Optional[str]]:
        """Возвращает (есть_бифуркация, тип)."""
        center = cluster.get_center()
        gradient = field.get_gradient_at(center)
        grad_mag = float(np.linalg.norm(gradient))
        
        direction = gradient / (grad_mag + 1e-6) if grad_mag > 1e-6 else np.array([1.0, 0.0, 0.0])
        
        d2S = self.second_derivative(cluster, field, direction)
        
        result = False, None
        if self._prev_d2S is not None and self._prev_d2S * d2S < 0:
            if abs(d2S) < 1e-3:
                result = True, 'saddle_node'
            elif d2S > 0:
                result = True, 'pitchfork'
            else:
                result = True, 'hopf'
        
        self._prev_d2S = d2S
        return result

# ═══════════════════════════════════════════════════════════════
# ОБМЕННЫЕ СУЩНОСТИ (РЕЗОНАНСНЫЙ ПЕРЕНОС)
# ═══════════════════════════════════════════════════════════════

class ExchangeEntity:
    """Перенос заряда между синхронизированными кластерами."""
    
    def __init__(self, donor_idx: int, acceptor_idx: int,
                 phase_diff: float, gradient_mag: float, field_val: float):
        self.donor_idx = donor_idx
        self.acceptor_idx = acceptor_idx
        self.amplitude = gradient_mag * abs(field_val) * abs(math.sin(phase_diff))
        self.resolved = False
        self.total = 0.0
    
    def resolve(self, clusters: List[VortexCluster], dt: float):
        if self.resolved:
            return
        
        donor = clusters[self.donor_idx]
        acceptor = clusters[self.acceptor_idx]
        
        if donor.dissolved or acceptor.dissolved or donor.merged_into or acceptor.merged_into:
            self.resolved = True
            return
        
        active_d = [i for i, t in enumerate(donor.tau_charges) if abs(t) > 1e-6]
        if not active_d:
            self.resolved = True
            return
        
        idx_d = active_d[np.argmax([abs(donor.tau_charges[i]) for i in active_d])]
        idx_a = np.argmin([abs(t) for t in acceptor.tau_charges])
        
        transfer = min(self.amplitude * dt, abs(donor.tau_charges[idx_d]) * 0.5)
        if transfer < 1e-10:
            self.resolved = True
            return
        
        sign = 1.0 if donor.tau_charges[idx_d] > 0 else -1.0
        donor.tau_charges[idx_d] -= sign * transfer
        acceptor.tau_charges[idx_a] += sign * transfer * 0.8
        self.total += transfer
        
        if self.total > 10.0:
            self.resolved = True

# ═══════════════════════════════════════════════════════════════
# ОСНОВНАЯ ЭВОЛЮЦИЯ: РИЗОМА V4
# ═══════════════════════════════════════════════════════════════

class FamilyEvolutionV4:
    """Ризоматическая эволюция без подгоночных параметров."""
    
    def __init__(self, clusters: List[VortexCluster],
                 box_size: float = 16.0,
                 external_pulses: List = None,
                 factor_x_list: List = None):
        self.clusters = clusters
        self.box_size = box_size
        self.external_pulses = external_pulses or []
        self.factor_x_list = factor_x_list or []
        self.rng = np.random.RandomState(42)
        
        self.field = BiharmonicField(box_size)
        self.clock = PulseClock()
        self.analyzer = ActionAnalyzer()
        
        self.global_step = 0
        self.global_exchanges: List[Dict] = []
        self.bifurcation_events: List[Dict] = []
        self.checkpoints: List[Dict] = []
        
        self.start_time = min(c.birth_time for c in clusters)
        
        self.birth_steps = {}
        for c in clusters:
            delta = c.birth_time - self.start_time
            self.birth_steps[c.name] = delta.days
            if delta.days == 0:
                c.born = True
                self.clock.add(c.name, c.total_charge(), c.capacity, c.strain)
        
        self._prev_total_winding = None
        self._init_field()
    
    def _active(self) -> List[VortexCluster]:
        return [c for c in self.clusters 
                if c.born and not c.dissolved and not c.merged_into]
    
    def _init_field(self):
        active = self._active()
        if active:
            self.field.solve_stationary(
                [c.positions for c in active],
                [np.array(c.tau_charges) for c in active]
            )
    
    def _wrap(self, pos):
        return pos % self.box_size
    
    def _velocities(self, cluster: VortexCluster, dt: float) -> np.ndarray:
        """Скорости вихрей из вариационного принципа."""
        v = np.zeros((cluster.n_vortices, 3))
        delta_V = self.field.dx**3
        noise_scale = math.sqrt(HBAR_EFF / delta_V) if delta_V > 0 else 0.01
        
        for i in range(cluster.n_vortices):
            pos = cluster.positions[i]
            tau = cluster.tau_charges[i]
            
            force = -tau * self.field.get_gradient_at(pos)
            
            for pulse in self.external_pulses:
                force += pulse.get_force(self.global_step)
            
            for fx in self.factor_x_list:
                fx_f, _ = fx.get_force(self.field.get_energy_density_at(pos))
                force += fx_f
            
            force += self.rng.randn(3) * noise_scale * 0.1
            v[i] = force
        
        return v
    
    def _binding_energy(self, cluster: VortexCluster) -> float:
        if cluster.n_vortices < 2:
            return 0.0
        e = 0.0
        for i in range(cluster.n_vortices):
            for j in range(i+1, cluster.n_vortices):
                r = np.linalg.norm(cluster.positions[i] - cluster.positions[j])
                if r > 1e-6:
                    e += cluster.tau_charges[i] * cluster.tau_charges[j] / r
        return e
    
    def _should_dissolve(self, cluster: VortexCluster, velocities: np.ndarray) -> bool:
        E_bind = abs(self._binding_energy(cluster))
        E_kin = 0.5 * sum(abs(cluster.tau_charges[i]) * np.dot(velocities[i], velocities[i])
                         for i in range(cluster.n_vortices))
        return E_kin > E_bind + 0.1
    
    def _find_resonances(self):
        """Поиск резонансов по синхронизации фаз."""
        entities = []
        active = self._active()
        
        for i, c1 in enumerate(active):
            for j, c2 in enumerate(active):
                if i >= j:
                    continue
                
                p1 = self.clock.get(c1.name)
                p2 = self.clock.get(c2.name)
                if not p1 or not p2:
                    continue
                
                dphi = p1.phase_diff(p2)
                if dphi > RESONANCE_THRESHOLD:
                    continue
                
                mid = (c1.get_center() + c2.get_center()) / 2
                grad_mag = float(np.linalg.norm(self.field.get_gradient_at(mid)))
                if grad_mag < 1e-6:
                    continue
                
                fv = self.field.get_field_value_at(mid)
                
                idx1 = self.clusters.index(c1)
                idx2 = self.clusters.index(c2)
                donor, acceptor = (idx1, idx2) if p1.phase > p2.phase else (idx2, idx1)
                
                entities.append(ExchangeEntity(donor, acceptor, dphi, grad_mag, fv))
        
        return entities
    
    def _create_child(self, parent: VortexCluster):
        if parent.n_vortices < 2:
            return None
        
        child_charge = [parent.tau_charges[-1]]
        parent.tau_charges = parent.tau_charges[:-1]
        parent.n_vortices -= 1
        
        child_pos = parent.get_center() + self.rng.randn(3) * parent.get_radius() * 0.5
        child_name = f"{parent.name}_c{parent.bifurcation_count}"
        
        child = VortexCluster(
            birth_time=self.start_time + timedelta(days=self.global_step),
            birth_position=tuple(child_pos),
            tau_charges=child_charge,
            name=child_name,
            fractal_level=parent.fractal_level + 1,
            exchange_potential=parent.exchange_potential * math.sqrt(2),
            parent_name=parent.name
        )
        child.born = True
        
        self.clock.add(child_name, child.total_charge(), child.capacity, child.strain)
        self.clusters.append(child)
        self.birth_steps[child_name] = self.global_step
        
        return child
    
    def _merge(self, c1: VortexCluster, c2: VortexCluster):
        merged_name = f"{c1.name}+{c2.name}"
        merged_charges = c1.tau_charges + c2.tau_charges
        merged_pos = tuple((c1.get_center() + c2.get_center()) / 2)
        
        merged = VortexCluster(
            birth_time=self.start_time + timedelta(days=self.global_step),
            birth_position=merged_pos,
            tau_charges=merged_charges,
            name=merged_name,
            fractal_level=max(c1.fractal_level, c2.fractal_level) + 1,
            exchange_potential=math.sqrt(c1.exchange_potential * c2.exchange_potential),
            parent_name=f"{c1.name}+{c2.name}"
        )
        merged.born = True
        
        c1.merged_into = merged_name
        c2.merged_into = merged_name
        c1.dissolved = True
        c2.dissolved = True
        c1.dissolution_step = self.global_step
        c2.dissolution_step = self.global_step
        
        self.clock.remove(c1.name)
        self.clock.remove(c2.name)
        self.clock.add(merged_name, merged.total_charge(), merged.capacity, merged.strain)
        
        self.clusters.append(merged)
        self.birth_steps[merged_name] = self.global_step
        
        return merged
    
    def _checkpoint(self, reason: str):
        state = {
            'step': self.global_step,
            'reason': reason,
            'sync': self.clock.synchronization(),
            'clusters': [
                {
                    'name': c.name,
                    'charges': c.tau_charges.copy(),
                    'strain': c.strain,
                    'capacity': c.capacity,
                    'winding': c.winding_number,
                    'phase': self.clock.get(c.name).phase if self.clock.get(c.name) else None,
                }
                for c in self.clusters if c.born
            ]
        }
        self.checkpoints.append(state)
    
    def evolve_step(self):
        self.global_step += 1
        
        # Активация новорождённых
        for c in self.clusters:
            if not c.born and self.birth_steps.get(c.name, -1) == self.global_step:
                c.born = True
                self.clock.add(c.name, c.total_charge(), c.capacity, c.strain)
        
        active = self._active()
        if not active:
            return
        
        # 1. Эволюция поля
        dt = self.clock.compute_dt()
        self.field.evolve(
            [c.positions for c in active],
            [np.array(c.tau_charges) for c in active],
            [c.tension for c in active],
            dt
        )
        
        # 2. Пульс
        positions_dict = {c.name: c.get_center() for c in self.clusters if c.born}
        self.clock.evolve_all(self.field, positions_dict)
        
        # 3. Эволюция кластеров
        for cluster in active:
            velocities = self._velocities(cluster, dt)
            
            for i in range(cluster.n_vortices):
                cluster.positions[i] = self._wrap(cluster.positions[i] + velocities[i]*dt)
            
            # Энергия и tension
            energies = [self.field.get_energy_density_at(p) for p in cluster.positions[:cluster.n_vortices]]
            energy = float(np.mean(energies))
            cluster.energy_history.append(energy)
            
            if len(cluster.energy_history) > 50:
                smoothed = float(np.mean(cluster.energy_history[-50:]))
                cluster.tension = abs(energy - smoothed) / (smoothed + 1e-6) if smoothed > 1e-6 else 0.0
            cluster.tension_history.append(cluster.tension)
            
            # Strain и capacity
            if len(cluster.energy_history) > 1:
                dE = abs(cluster.energy_history[-1] - cluster.energy_history[-2])
                cluster.strain = (cluster.strain + dE*dt) * 0.99
            cluster.strain_history.append(cluster.strain)
            cluster.capacity = max(0.001, 1.0/(1.0 + cluster.strain))
            cluster.capacity_history.append(cluster.capacity)
            
            # Обновляем пульс
            pulse = self.clock.get(cluster.name)
            if pulse:
                pulse.update(cluster.capacity, cluster.strain)
            
            # Winding number
            w, _ = compute_winding(cluster.get_center(), cluster.get_radius(), self.field)
            cluster.winding_number = w
            cluster.winding_history.append(w)
            
            # Регенерация/деградация зарядов
            for i in range(cluster.n_vortices):
                orig = cluster.original_tau_charges[i] if i < len(cluster.original_tau_charges) else 1.0
                curr = cluster.tau_charges[i]
                fv = abs(self.field.get_field_value_at(cluster.positions[i]))
                
                regen = (orig - curr) * fv * cluster.capacity * dt * 0.1
                deg = curr * cluster.strain * dt * 0.01
                cluster.tau_charges[i] += regen - deg
                if regen > 0:
                    cluster.total_absorbed_from_field += regen
            
            # Бифуркации
            is_bif, bif_type = self.analyzer.detect(cluster, self.field)
            if is_bif:
                cluster.bifurcation_count += 1
                
                if bif_type == 'saddle_node':
                    if self._should_dissolve(cluster, velocities):
                        cluster.dissolved = True
                        cluster.dissolution_step = self.global_step
                        self.clock.remove(cluster.name)
                        self.bifurcation_events.append({
                            'step': self.global_step, 'type': 'dissolution',
                            'cluster': cluster.name, 'reason': 'saddle_node'
                        })
                
                elif bif_type == 'pitchfork':
                    child = self._create_child(cluster)
                    if child:
                        self.bifurcation_events.append({
                            'step': self.global_step, 'type': 'child_created',
                            'parent': cluster.name, 'child': child.name,
                            'reason': 'pitchfork'
                        })
                        cluster.strain *= 0.5
                
                elif bif_type == 'hopf':
                    pulse_i = self.clock.get(cluster.name)
                    best, best_dphi = None, float('inf')
                    
                    for other in active:
                        if other is cluster or other.merged_into:
                            continue
                        pulse_j = self.clock.get(other.name)
                        if pulse_i and pulse_j:
                            dphi = pulse_i.phase_diff(pulse_j)
                            if dphi < best_dphi:
                                best_dphi = dphi
                                best = other
                    
                    if best and best_dphi < RESONANCE_THRESHOLD:
                        merged = self._merge(cluster, best)
                        if merged:
                            self.bifurcation_events.append({
                                'step': self.global_step, 'type': 'merged',
                                'cluster1': cluster.name, 'cluster2': best.name,
                                'merged_name': merged.name, 'reason': 'hopf'
                            })
        
        # 4. Обмены
        for entity in self._find_resonances():
            entity.resolve(self.clusters, dt)
            if entity.total > 1e-6:
                self.global_exchanges.append({
                    'step': self.global_step,
                    'donor': self.clusters[entity.donor_idx].name,
                    'acceptor': self.clusters[entity.acceptor_idx].name,
                    'amount': entity.total
                })
        
        # 5. Инварианты
        sync = self.clock.synchronization()
        if sync > SYNC_DANGER:
            self._checkpoint('high_sync')
        
        total_w = sum((c.winding_number or 0) for c in active)
        if self._prev_total_winding is not None:
            if abs(total_w - self._prev_total_winding) > WINDING_JUMP_THRESHOLD:
                self._checkpoint('winding_jump')
        self._prev_total_winding = total_w


# ═══════════════════════════════════════════════════════════════
# ВНЕШНИЕ ВОЗДЕЙСТВИЯ (оставлены для обратной совместимости)
# ═══════════════════════════════════════════════════════════════

class ExternalPulse:
    def __init__(self, period_steps: int, amplitude: float, phase: float = 0.0):
        self.period = period_steps
        self.amplitude = amplitude
        self.phase = phase
    
    def get_force(self, step: int) -> np.ndarray:
        val = self.amplitude * math.sin(2*math.pi*step/self.period + self.phase)
        return np.array([math.cos(self.phase), math.sin(self.phase), 0.0]) * val


class FactorX:
    def __init__(self, amplitude: float = 0.01, threshold: float = 0.1, seed: int = 123):
        self.amplitude = amplitude
        self.threshold = threshold
        self.rng = np.random.RandomState(seed)
    
    def get_force(self, energy_density: float) -> Tuple[np.ndarray, bool]:
        if energy_density < self.threshold:
            d = self.rng.randn(3)
            n = np.linalg.norm(d)
            return d / (n+1e-6) * self.amplitude * self.rng.exponential(1.0), True
        return np.zeros(3), False


# ═══════════════════════════════════════════════════════════════
# ДЕТЕКТОР СОБЫТИЙ (для анализа постфактум)
# ═══════════════════════════════════════════════════════════════

class EventDetector:
    def __init__(self, tension_history, energy_history, window=30,
                 threshold_factor=3.5, energy_factor=3.0):
        self.tension_history = tension_history
        self.energy_history = energy_history
        self.window = window
        self.threshold_factor = threshold_factor
        self.energy_factor = energy_factor
    
    def find_peaks(self):
        if len(self.tension_history) < self.window * 2:
            return []
        arr = np.array(self.tension_history)
        smoothed = np.convolve(arr, np.ones(self.window)/self.window, mode='same')
        mean_val = float(np.mean(smoothed[-self.window:]))
        std_val = float(np.std(smoothed[-self.window:]))
        threshold = mean_val + self.threshold_factor * std_val
        
        peaks = []
        for i in range(self.window, len(smoothed) - self.window):
            if smoothed[i] > threshold and smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
                peaks.append({
                    'step': i,
                    'tension': self.tension_history[i],
                    'energy': self.energy_history[i] if i < len(self.energy_history) else None,
                })
        return peaks
    
    def find_jumps(self):
        if len(self.energy_history) < 2:
            return []
        jumps = [{'step': i, 'delta': abs(self.energy_history[i] - self.energy_history[i-1])}
                 for i in range(1, len(self.energy_history))]
        if not jumps:
            return []
        mean_d = float(np.mean([j['delta'] for j in jumps]))
        std_d = float(np.std([j['delta'] for j in jumps]))
        threshold = mean_d + self.energy_factor * std_d
        return sorted([j for j in jumps if j['delta'] > threshold], 
                     key=lambda x: x['delta'], reverse=True)
    
    def classify_peaks(self):
        all_peaks = self.find_peaks()
        if not all_peaks:
            return {'macro': [], 'meso': [], 'micro': []}
        mean_val = float(np.mean(self.tension_history))
        std_val = float(np.std(self.tension_history))
        
        return {
            'macro': [p for p in all_peaks if p['tension'] > mean_val + 4.0*std_val],
            'meso': [p for p in all_peaks if mean_val + 2.0*std_val < p['tension'] <= mean_val + 4.0*std_val],
            'micro': [p for p in all_peaks if p['tension'] <= mean_val + 2.0*std_val],
        }