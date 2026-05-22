#!/usr/bin/env python3
"""
family_vortex.py v3.3 — фрактально-эмерджентная модель с бифуркациями.
Бигармоническое поле. Обменные сущности в зазорах. Фрактальное время.
Динамическая регенерация/деградация.
Бифуркации: рассеяние, рождение малого фрактала, слияние в большой.
"""

import math
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from collections import Counter


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
        self.parent_name = parent_name  # от кого произошёл (для малых фракталов)
        
        # Эмерджентное состояние
        self.tension = 0.0
        self.strain = 0.0
        self.capacity = 1.0
        self.dissolved = False
        self.dissolution_step: Optional[int] = None
        self.born = False
        self.merged_into: Optional[str] = None  # с кем слился (для больших фракталов)
        
        # Счётчик бифуркаций
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
    
    def total_charge(self) -> float:
        return sum(abs(t) for t in self.tau_charges)
    
    def total_original_charge(self) -> float:
        return sum(abs(t) for t in self.original_tau_charges)
    
    def get_center(self) -> np.ndarray:
        return np.mean(self.positions, axis=0)


class BiharmonicField:
    """Бигармоническое поле ψ: ∂ψ/∂t = -∇⁴ψ + источники - γψ."""
    
    def __init__(self, box_size: float = 16.0, grid_size: int = 32, gamma: float = 0.01):
        self.box_size = box_size
        self.grid_size = grid_size
        self.dx = box_size / grid_size
        self.gamma = gamma
        self.base_gamma = gamma
        
        self.psi = np.zeros((grid_size, grid_size, grid_size))
        
        k = np.fft.fftfreq(grid_size, d=self.dx) * 2 * np.pi
        Kx, Ky, Kz = np.meshgrid(k, k, k, indexing='ij')
        self.k_squared = Kx**2 + Ky**2 + Kz**2
        self.k_biharmonic = self.k_squared**2
        self.k_biharmonic[0, 0, 0] = 1.0
        
        self.absorbed_energy = 0.0
    
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
            # Насыщение: эффективный заряд не более 2x от максимума кластера
            max_charge = max(np.max(np.abs(charges)) * 2.0, 1.0)
            effective_charges = np.clip(charges * (1.0 + tension), -max_charge, max_charge)
            for pos, charge in zip(positions, effective_charges):
                i = int(pos[0] / self.dx) % self.grid_size
                j = int(pos[1] / self.dx) % self.grid_size
                k = int(pos[2] / self.dx) % self.grid_size
                rho[i, j, k] += charge
        
        psi_hat = np.fft.fftn(self.psi)
        rho_hat = np.fft.fftn(rho)
        
        # Адаптивная диссипация: γ растёт при большой амплитуде поля
        max_psi = np.max(np.abs(self.psi))
        effective_gamma = self.gamma * (1.0 + max_psi / 10.0)
        
        numerator = psi_hat + dt * rho_hat
        denominator = 1.0 + dt * (self.k_biharmonic + effective_gamma)
        denominator[0, 0, 0] = 1.0
        
        psi_hat_new = numerator / denominator
        psi_hat_new[0, 0, 0] = 0.0
        
        # Инерция: ограничение максимального изменения
        max_change = 5.0
        change = np.abs(psi_hat_new - psi_hat)
        mask = change > max_change * (np.abs(psi_hat) + 1e-6)
        psi_hat_new[mask] = psi_hat[mask] + max_change * (np.abs(psi_hat[mask]) + 1e-6) * np.sign(psi_hat_new[mask] - psi_hat[mask])
        
        self.psi = np.real(np.fft.ifftn(psi_hat_new))
    
    def get_gradient_at(self, position: np.ndarray) -> np.ndarray:
        x = position[0] / self.dx
        y = position[1] / self.dx
        z = position[2] / self.dx
        
        i0 = int(np.floor(x)) % self.grid_size
        j0 = int(np.floor(y)) % self.grid_size
        k0 = int(np.floor(z)) % self.grid_size
        i1 = (i0 + 1) % self.grid_size
        j1 = (j0 + 1) % self.grid_size
        k1 = (k0 + 1) % self.grid_size
        
        fx = x - i0; fy = y - j0; fz = z - k0
        
        v000 = self.psi[i0,j0,k0]; v100 = self.psi[i1,j0,k0]
        v010 = self.psi[i0,j1,k0]; v110 = self.psi[i1,j1,k0]
        v001 = self.psi[i0,j0,k1]; v101 = self.psi[i1,j0,k1]
        v011 = self.psi[i0,j1,k1]; v111 = self.psi[i1,j1,k1]
        
        gx = ((1-fy)*(1-fz)*v100 + fy*(1-fz)*v110 + (1-fy)*fz*v101 + fy*fz*v111 -
              (1-fy)*(1-fz)*v000 - fy*(1-fz)*v010 - (1-fy)*fz*v001 - fy*fz*v011) / self.dx
        
        gy = ((1-fx)*(1-fz)*v010 + fx*(1-fz)*v110 + (1-fx)*fz*v011 + fx*fz*v111 -
              (1-fx)*(1-fz)*v000 - fx*(1-fz)*v100 - (1-fx)*fz*v001 - fx*fz*v101) / self.dx
        
        gz = ((1-fx)*(1-fy)*v001 + fx*(1-fy)*v101 + (1-fx)*fy*v011 + fx*fy*v111 -
              (1-fx)*(1-fy)*v000 - fx*(1-fy)*v100 - (1-fx)*fy*v010 - fx*fy*v110) / self.dx
        
        return np.array([gx, gy, gz])
    
    def get_energy_density_at(self, position: np.ndarray) -> float:
        grad = self.get_gradient_at(position)
        return float(np.dot(grad, grad))
    
    def get_field_value_at(self, position: np.ndarray) -> float:
        x = position[0] / self.dx
        y = position[1] / self.dx
        z = position[2] / self.dx
        
        i0 = int(np.floor(x)) % self.grid_size
        j0 = int(np.floor(y)) % self.grid_size
        k0 = int(np.floor(z)) % self.grid_size
        i1 = (i0 + 1) % self.grid_size
        j1 = (j0 + 1) % self.grid_size
        k1 = (k0 + 1) % self.grid_size
        
        fx = x - i0; fy = y - j0; fz = z - k0
        
        return ((1-fx)*(1-fy)*(1-fz)*self.psi[i0,j0,k0] +
                fx*(1-fy)*(1-fz)*self.psi[i1,j0,k0] +
                (1-fx)*fy*(1-fz)*self.psi[i0,j1,k0] +
                fx*fy*(1-fz)*self.psi[i1,j1,k0] +
                (1-fx)*(1-fy)*fz*self.psi[i0,j0,k1] +
                fx*(1-fy)*fz*self.psi[i1,j0,k1] +
                (1-fx)*fy*fz*self.psi[i0,j1,k1] +
                fx*fy*fz*self.psi[i1,j1,k1])


class ExchangeEntity:
    """Обменная сущность — живёт в зазоре между тиками."""
    
    def __init__(self, donor_idx: int, acceptor_idx: int,
                 gradient_magnitude: float, field_value: float,
                 donor_tension: float, acceptor_tension: float):
        self.donor_idx = donor_idx
        self.acceptor_idx = acceptor_idx
        self.amplitude = gradient_magnitude * abs(field_value) * (donor_tension + acceptor_tension) * 0.5
        self.lifetime = 0.0
        self.resolved = False
        self.total_transferred = 0.0
    
    def resolve(self, clusters: List[VortexCluster], dt_imaginary: float = 0.05):
        if self.resolved:
            return
        
        decay = math.exp(-self.lifetime * 0.5)
        self.amplitude *= decay
        self.lifetime += dt_imaginary
        
        if self.amplitude < 1e-8:
            self.resolved = True
            return
        
        donor = clusters[self.donor_idx]
        acceptor = clusters[self.acceptor_idx]
        
        if donor.dissolved or acceptor.dissolved or not donor.born or not acceptor.born:
            self.resolved = True
            return
        if donor.merged_into or acceptor.merged_into:
            self.resolved = True
            return
        
        non_zero_donor = [i for i, t in enumerate(donor.tau_charges) if abs(t) > 1e-6]
        if not non_zero_donor:
            self.resolved = True
            return
        
        idx_d = non_zero_donor[np.argmax([abs(donor.tau_charges[i]) for i in non_zero_donor])]
        idx_a = np.argmin([abs(t) for t in acceptor.tau_charges])
        
        transfer = self.amplitude * 0.1
        transfer = min(transfer, abs(donor.tau_charges[idx_d]) * 0.3)
        
        sign = 1.0 if donor.tau_charges[idx_d] > 0 else -1.0
        donor.tau_charges[idx_d] -= sign * transfer
        acceptor.tau_charges[idx_a] += sign * transfer * 0.8
        
        self.total_transferred += transfer
        donor.total_given += transfer
        acceptor.total_received += transfer * 0.8


class FractalClock:
    """Фрактальные часы."""
    
    def __init__(self, n_levels: int = 3):
        self.base_dt = 0.1
        self.level_scales = [1, 2, 4]
        self.global_step = 0
    
    def should_evolve(self, fractal_level: int) -> bool:
        scale = self.level_scales[min(fractal_level - 1, len(self.level_scales) - 1)]
        return self.global_step % scale == 0
    
    def get_dt(self, fractal_level: int) -> float:
        scale = self.level_scales[min(fractal_level - 1, len(self.level_scales) - 1)]
        return self.base_dt * scale
    
    def get_imaginary_dt(self, fractal_level: int) -> float:
        scale = self.level_scales[min(fractal_level - 1, len(self.level_scales) - 1)]
        return 0.05 / scale


class ResonanceDetector:
    """Ищет резонансы между кластерами."""
    
    def __init__(self, rng: np.random.RandomState):
        self.rng = rng
    
    def find_resonances(self, clusters, field):
        entities = []
        born = [c for c in clusters if c.born and not c.dissolved and not c.merged_into]
        if len(born) < 2:
            return entities
        
        for i, c1 in enumerate(clusters):
            if not c1.born or c1.dissolved or c1.merged_into:
                continue
            for j, c2 in enumerate(clusters):
                if i >= j or not c2.born or c2.dissolved or c2.merged_into:
                    continue
                
                tension_sum = c1.tension + c2.tension
                if tension_sum < 0.3:
                    continue
                
                tension_diff = abs(c1.tension - c2.tension)
                if tension_diff > 0.3 * tension_sum:
                    continue
                
                pos1 = c1.get_center()
                pos2 = c2.get_center()
                midpoint = (pos1 + pos2) / 2
                
                gradient = field.get_gradient_at(midpoint)
                field_value = field.get_field_value_at(midpoint)
                gradient_mag = float(np.linalg.norm(gradient))
                
                if gradient_mag < 0.01:
                    continue
                
                entity = ExchangeEntity(
                    donor_idx=i if c1.tension > c2.tension else j,
                    acceptor_idx=j if c1.tension > c2.tension else i,
                    gradient_magnitude=gradient_mag,
                    field_value=field_value,
                    donor_tension=c1.tension if c1.tension > c2.tension else c2.tension,
                    acceptor_tension=c2.tension if c1.tension > c2.tension else c1.tension
                )
                entities.append(entity)
        
        return entities


class ExternalPulse:
    """Внешний импульс."""
    
    def __init__(self, period_steps: int, amplitude: float, phase: float = 0.0):
        self.period = period_steps
        self.amplitude = amplitude
        self.phase = phase
    
    def get_force(self, step: int) -> np.ndarray:
        value = self.amplitude * math.sin(2 * math.pi * step / self.period + self.phase)
        direction = np.array([math.cos(self.phase), math.sin(self.phase), 0.0])
        return direction * value


class FactorX:
    """Крыло бабочки."""
    
    def __init__(self, amplitude: float = 0.01, threshold: float = 0.1, seed: int = 123):
        self.amplitude = amplitude
        self.threshold = threshold
        self.rng = np.random.RandomState(seed)
    
    def get_force(self, energy_density: float) -> Tuple[np.ndarray, bool]:
        if energy_density < self.threshold:
            direction = self.rng.randn(3)
            norm = np.linalg.norm(direction)
            if norm > 1e-6:
                direction = direction / norm
            magnitude = self.amplitude * self.rng.exponential(1.0)
            return direction * magnitude, True
        return np.zeros(3), False


class FamilyEvolution:
    """Эволюция семейного кластера v3.3 с бифуркациями."""
    
    def __init__(self, clusters, box_size=16.0, external_pulses=None,
                 factor_x_list=None, noise_seed=42):
        self.clusters = clusters
        self.box_size = box_size
        self.external_pulses = external_pulses or []
        self.factor_x_list = factor_x_list or []
        self.noise_rng = np.random.RandomState(noise_seed)
        
        self.field = BiharmonicField(box_size)
        self.clock = FractalClock()
        self.resonance_detector = ResonanceDetector(self.noise_rng)
        self.global_exchanges: List[Dict] = []
        self.bifurcation_events: List[Dict] = []
        
        self.start_time = min(c.birth_time for c in clusters)
        
        self.birth_steps = {}
        for c in clusters:
            delta = c.birth_time - self.start_time
            self.birth_steps[c.name] = delta.days
        
        for c in clusters:
            if self.birth_steps[c.name] == 0:
                c.born = True
        
        self._initialize_field_for_step(0)
    
    def _get_active_clusters(self, step):
        return [c for c in self.clusters 
                if c.born and not c.dissolved and not c.merged_into]
    
    def _get_cluster_by_name(self, name):
        for c in self.clusters:
            if c.name == name:
                return c
        return None
    
    def _initialize_field_for_step(self, step):
        active = self._get_active_clusters(step)
        if active:
            positions_list = [c.positions for c in active]
            charges_list = [np.array(c.tau_charges) for c in active]
            self.field.solve_stationary(positions_list, charges_list)
    
    def _minimum_image(self, pos):
        return pos % self.box_size
    
    def _create_child_cluster(self, parent: VortexCluster, step: int):
        """Создание малого фрактала: отщепление вихря."""
        if parent.n_vortices < 2:
            return None
        
        # Отщепляем последний вихрь
        child_charge = [parent.tau_charges[-1]]
        parent.tau_charges = parent.tau_charges[:-1]
        parent.n_vortices -= 1
        
        # Позиция ребёнка — рядом с родителем
        child_pos = parent.get_center() + self.noise_rng.randn(3) * 0.5
        
        child_name = f"{parent.name}_child_{parent.bifurcation_count}"
        child = VortexCluster(
            birth_time=self.start_time + timedelta(days=step),
            birth_position=tuple(child_pos),
            tau_charges=child_charge,
            name=child_name,
            fractal_level=parent.fractal_level + 1,
            exchange_potential=parent.exchange_potential * 1.2,
            parent_name=parent.name
        )
        child.born = True
        child.bifurcation_count = 0
        
        self.clusters.append(child)
        self.birth_steps[child_name] = step
        
        return child
    
    def _merge_clusters(self, c1: VortexCluster, c2: VortexCluster, step: int):
        """Слияние в большой фрактал."""
        merged_name = f"{c1.name}_{c2.name}_merged"
        merged_charges = c1.tau_charges + c2.tau_charges
        merged_pos = tuple((c1.get_center() + c2.get_center()) / 2)
        
        merged = VortexCluster(
            birth_time=self.start_time + timedelta(days=step),
            birth_position=merged_pos,
            tau_charges=merged_charges,
            name=merged_name,
            fractal_level=max(c1.fractal_level, c2.fractal_level) + 1,
            exchange_potential=(c1.exchange_potential + c2.exchange_potential) / 2,
            parent_name=f"{c1.name}+{c2.name}"
        )
        merged.born = True
        
        c1.merged_into = merged_name
        c2.merged_into = merged_name
        c1.dissolved = True
        c2.dissolved = True
        c1.dissolution_step = step
        c2.dissolution_step = step
        
        self.clusters.append(merged)
        self.birth_steps[merged_name] = step
        
        return merged
    
    def evolve_step(self, noise_level=0.005):
        self.clock.global_step += 1
        step = self.clock.global_step
        
        # Проверяем рождения
        for c in self.clusters:
            if not c.born and self.birth_steps.get(c.name, -1) == step:
                c.born = True
        
        newborns = [c for c in self.clusters 
                    if c.born and self.birth_steps.get(c.name, -1) == step]
        if newborns:
            self._initialize_field_for_step(step)
        
        active = self._get_active_clusters(step)
        
        # ===== ТИК =====
        for idx, cluster in enumerate(self.clusters):
            if not cluster.born or cluster.merged_into:
                continue
            
            if cluster.dissolved:
                cluster.energy_history.append(0.0)
                cluster.tension_history.append(0.0)
                cluster.strain_history.append(cluster.strain)
                cluster.capacity_history.append(cluster.capacity)
                continue
            
            if not self.clock.should_evolve(cluster.fractal_level):
                if cluster.energy_history:
                    cluster.energy_history.append(cluster.energy_history[-1])
                    cluster.tension_history.append(cluster.tension)
                    cluster.strain_history.append(cluster.strain)
                    cluster.capacity_history.append(cluster.capacity)
                continue
            
            dt = self.clock.get_dt(cluster.fractal_level)
            
            # Движение вихрей
            for i in range(cluster.n_vortices):
                pos = cluster.positions[i]
                charge = cluster.tau_charges[i]
                
                gradient = self.field.get_gradient_at(pos)
                velocity = charge * gradient
                
                for pulse in self.external_pulses:
                    velocity += pulse.get_force(step)
                
                energy_density = self.field.get_energy_density_at(pos)
                for fx in self.factor_x_list:
                    fx_force, _ = fx.get_force(energy_density)
                    velocity += fx_force
                
                velocity += self.noise_rng.randn(3) * noise_level
                
                cluster.positions[i] += velocity * dt
                cluster.positions[i] = self._minimum_image(cluster.positions[i])
            
            # Энергия
            energies = [self.field.get_energy_density_at(p) for p in cluster.positions]
            energy = float(np.mean(energies))
            cluster.energy_history.append(energy)
            
            # Tension
            window = min(50, len(cluster.energy_history))
            if window > 1:
                smoothed = float(np.mean(cluster.energy_history[-window:]))
                if smoothed > 1e-6:
                    cluster.tension = abs(energy - smoothed) / smoothed
                else:
                    cluster.tension = 0.0
            cluster.tension_history.append(cluster.tension)
            
            # Strain
            dissipation = cluster.total_charge() / max(cluster.total_original_charge(), 1e-6)
            cluster.strain += cluster.tension * dt
            cluster.strain -= cluster.strain * dissipation * dt * 0.1
            cluster.strain = max(0.0, cluster.strain)
            cluster.strain_history.append(cluster.strain)
            
            # Capacity
            cluster.capacity = max(0.01, 1.0 - cluster.strain)
            cluster.capacity_history.append(cluster.capacity)
            
            # Динамическая регенерация
            window_t = min(100, len(cluster.tension_history))
            smoothed_tension = float(np.mean(cluster.tension_history[-window_t:])) if window_t > 0 else cluster.tension
            inertia = cluster.tension / max(smoothed_tension, 1e-6)
            
            for i in range(cluster.n_vortices):
                original = cluster.original_tau_charges[i] if i < len(cluster.original_tau_charges) else 1.0
                current = cluster.tau_charges[i]
                deficit = original - current
                
                pos = cluster.positions[i]
                field_value = abs(self.field.get_field_value_at(pos))
                
                deg_rate = cluster.tension * abs(current) / max(cluster.capacity, 0.01)
                regen_rate = abs(deficit) * field_value * cluster.capacity / (1.0 + cluster.strain)
                regen_rate *= 1.0 if deficit > 0 else -1.0
                
                if inertia > 1.0:
                    effective_deg = deg_rate * inertia
                    effective_regen = regen_rate / inertia
                else:
                    effective_deg = deg_rate * inertia
                    effective_regen = regen_rate / max(inertia, 0.1)
                
                deg_sign = 1.0 if current >= 0 else -1.0
                net = effective_regen - effective_deg * deg_sign
                cluster.tau_charges[i] += net * dt * 0.01
                
                if net > 0:
                    cluster.total_absorbed_from_field += net * dt * 0.01
            
            # ===== БИФУРКАЦИЯ =====
            if cluster.strain > 2.0:
                cluster.bifurcation_count += 1
                
                if cluster.capacity < 0.1:
                    # Рассеяние (растворение)
                    cluster.dissolved = True
                    cluster.dissolution_step = step
                    event = {
                        'step': step,
                        'type': 'dissolution',
                        'cluster': cluster.name,
                        'strain': cluster.strain,
                        'capacity': cluster.capacity,
                    }
                    self.bifurcation_events.append(event)
                    cluster.bifurcation_history.append(event)
                    
                elif cluster.tension > 1.0:
                    # Создание малого фрактала
                    child = self._create_child_cluster(cluster, step)
                    if child:
                        event = {
                            'step': step,
                            'type': 'child_created',
                            'parent': cluster.name,
                            'child': child.name,
                            'tension': cluster.tension,
                            'strain': cluster.strain,
                        }
                        self.bifurcation_events.append(event)
                        cluster.bifurcation_history.append(event)
                        cluster.strain = 0.0
                        
                else:
                    # Создание большого фрактала: поиск партнёра
                    # Ищем ближайший кластер с похожим tension
                    best_partner = None
                    best_score = float('inf')
                    
                    for other in self._get_active_clusters(step):
                        if other.name == cluster.name or other.merged_into:
                            continue
                        tension_diff = abs(cluster.tension - other.tension)
                        if tension_diff < 0.3 and other.strain > 1.0:
                            score = tension_diff
                            if score < best_score:
                                best_score = score
                                best_partner = other
                    
                    if best_partner:
                        merged = self._merge_clusters(cluster, best_partner, step)
                        if merged:
                            event = {
                                'step': step,
                                'type': 'merged',
                                'cluster1': cluster.name,
                                'cluster2': best_partner.name,
                                'merged_name': merged.name,
                                'tension': cluster.tension,
                            }
                            self.bifurcation_events.append(event)
                            cluster.bifurcation_history.append(event)
                            best_partner.bifurcation_history.append(event)
                            cluster.strain = 0.0
                    else:
                        # Нет партнёра — сброс напряжения без бифуркации
                        cluster.strain *= 0.5
        
        # ===== ЭВОЛЮЦИЯ ПОЛЯ =====
        active = self._get_active_clusters(step)
        if active:
            positions_list = [c.positions for c in active]
            charges_list = [np.array(c.tau_charges) for c in active]
            tensions = [c.tension for c in active]
            self.field.evolve(positions_list, charges_list, tensions, dt=0.1)
        
        # ===== ЗАЗОР =====
        entities = self.resonance_detector.find_resonances(self.clusters, self.field)
        
        for entity in entities:
            imaginary_dt = self.clock.get_imaginary_dt(
                max(self.clusters[entity.donor_idx].fractal_level,
                    self.clusters[entity.acceptor_idx].fractal_level)
            )
            
            iterations = 0
            while not entity.resolved and iterations < 100:
                entity.resolve(self.clusters, imaginary_dt)
                iterations += 1
            
            if entity.total_transferred > 1e-6:
                self.global_exchanges.append({
                    'step': step,
                    'donor': self.clusters[entity.donor_idx].name,
                    'acceptor': self.clusters[entity.acceptor_idx].name,
                    'amount': entity.total_transferred,
                })


class EventDetector:
    """Детектор событий по tension."""
    
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
        
        jumps = []
        for i in range(1, len(self.energy_history)):
            delta = abs(self.energy_history[i] - self.energy_history[i-1])
            jumps.append({'step': i, 'delta_energy': delta})
        
        if not jumps:
            return []
        
        mean_delta = float(np.mean([j['delta_energy'] for j in jumps]))
        std_delta = float(np.std([j['delta_energy'] for j in jumps]))
        threshold = mean_delta + self.energy_factor * std_delta
        
        significant = [j for j in jumps if j['delta_energy'] > threshold]
        return sorted(significant, key=lambda x: x['delta_energy'], reverse=True)
    
    def classify_peaks(self):
        all_peaks = self.find_peaks()
        if not all_peaks:
            return {'macro': [], 'meso': [], 'micro': []}
        
        mean_val = float(np.mean(self.tension_history))
        std_val = float(np.std(self.tension_history))
        
        macro = [p for p in all_peaks if p['tension'] > mean_val + 4.0 * std_val]
        meso = [p for p in all_peaks if mean_val + 2.0 * std_val < p['tension'] <= mean_val + 4.0 * std_val]
        micro = [p for p in all_peaks if p['tension'] <= mean_val + 2.0 * std_val]
        
        return {'macro': macro, 'meso': meso, 'micro': micro}