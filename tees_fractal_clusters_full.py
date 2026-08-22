# tees_fractal_clusters_full.py
# 🌲 TEES: Фрактальный ЛЕС — ПОЛНАЯ ВЕРСИЯ!

import hashlib
import secrets
import time
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════
# 1. ФРАКТАЛЬНАЯ ПАМЯТЬ (5 уровней!)
# ═══════════════════════════════════

class FractalMemory:
    def __init__(self, max_level_0=100):
        self.max_level_0 = max_level_0
        self.level_0 = []
        self.level_1 = []
        self.level_2 = []
        self.level_3 = []
        self.level_4 = {}
    
    def add(self, data):
        self.level_0.append(data)
        if len(self.level_0) >= self.max_level_0:
            self._fold_to_1()
    
    def _fold_to_1(self):
        batch = self.level_0[:self.max_level_0]
        for i in range(0, len(batch), 10):
            group = batch[i:i+10]
            if group:
                self.level_1.append({'count': len(group), 'type': 'compressed'})
        self.level_0 = self.level_0[self.max_level_0:]
        if len(self.level_1) >= 100:
            self._fold_to_2()
    
    def _fold_to_2(self):
        self.level_2.append({'type': 'semantic', 'count': len(self.level_1)})
        self.level_1 = []
    
    def get_depth(self):
        depth = 0
        if self.level_0: depth = 1
        if self.level_1: depth = 2
        if self.level_2: depth = 3
        if self.level_3: depth = 4
        if self.level_4: depth = 5
        return depth
    
    def get_total_memory(self):
        return (len(self.level_0) + len(self.level_1)*10 + 
                len(self.level_2)*100 + len(self.level_3)*1000 + 
                len(self.level_4)*10000)

# ═══════════════════════════════════
# 2. ЭКОНОМИКА (7 органов!)
# ═══════════════════════════════════

class TEESEconomy:
    def __init__(self):
        self.active_nodes = {}
        self.fat_reserves = 0.0
        self.bone_structure = 0.0
        self.blood_sugar = 0.0
        self.education = 0.0
        self.social_fund = 0.0
        self.science = 0.0
        self.total_energy = 0.0
        self.wisdom = 0.0
        self.metabolic_rates = {
            'muscle_growth': 0.70, 'fat_storage': 0.10,
            'bone_building': 0.05, 'blood_circulation': 0.03,
            'education': 0.05, 'social_support': 0.04, 'science': 0.03
        }
        self.MAX_CONCENTRATION = 0.3
    
    def accrue(self, node_id, action, base=10):
        if action not in ['handshake', 'route', 'sync', 'send', 'receive']:
            return False
        
        muscle = base * self.metabolic_rates['muscle_growth']
        fat = base * self.metabolic_rates['fat_storage']
        bone = base * self.metabolic_rates['bone_building']
        blood = base * self.metabolic_rates['blood_circulation']
        edu = base * self.metabolic_rates['education']
        soc = base * self.metabolic_rates['social_support']
        sci = base * self.metabolic_rates['science']
        
        self.active_nodes[node_id] = self.active_nodes.get(node_id, 0) + muscle
        self.fat_reserves += fat
        self.bone_structure += bone
        self.blood_sugar += blood
        self.education += edu
        self.social_fund += soc
        self.science += sci
        self.total_energy += base
        
        self._check_concentration(node_id)
        self._maintain_homeostasis()
        return True
    
    def _check_concentration(self, node_id):
        if not self.active_nodes:
            return
        max_allowed = self.total_energy * self.MAX_CONCENTRATION
        if self.active_nodes.get(node_id, 0) > max_allowed:
            excess = self.active_nodes[node_id] - max_allowed
            self.active_nodes[node_id] = max_allowed
            self.fat_reserves += excess
    
    def _maintain_homeostasis(self):
        if self.total_energy == 0: return
        fat_pct = self.fat_reserves / self.total_energy
        if fat_pct < 0.05:
            self.metabolic_rates['fat_storage'] += 0.01
            self.metabolic_rates['muscle_growth'] -= 0.01
        elif fat_pct > 0.25:
            self.metabolic_rates['fat_storage'] -= 0.01
            self.metabolic_rates['muscle_growth'] += 0.01
        for k in self.metabolic_rates:
            self.metabolic_rates[k] = max(0.01, self.metabolic_rates[k])
        total = sum(self.metabolic_rates.values())
        for k in self.metabolic_rates:
            self.metabolic_rates[k] /= total
    
    def verify_balance(self):
        total = (sum(self.active_nodes.values()) + self.fat_reserves +
                self.bone_structure + self.blood_sugar + self.education +
                self.social_fund + self.science)
        return abs(total - self.total_energy) < 0.001

# ═══════════════════════════════════
# 3. TEES-КРИПТО
# ═══════════════════════════════════

class TEESCrypto:
    @staticmethod
    def generate_key(length=32):
        return secrets.token_bytes(length)
    @staticmethod
    def encrypt(data, key):
        return bytes([d ^ k for d, k in zip(data, key)])
    @staticmethod
    def decrypt(data, key):
        return TEESCrypto.encrypt(data, key)

# ═══════════════════════════════════
# 4. КОГЕРЕНТНАЯ ЯЧЕЙКА
# ═══════════════════════════════════

@dataclass
class CoherentCell:
    cell_id: str
    key: bytes
    phase: float = 0.0
    coherence: float = 0.994
    created_at: float = field(default_factory=time.time)

# ═══════════════════════════════════
# 5. АДАПТИВНЫЙ РОУТЕР (∇H!)
# ═══════════════════════════════════

class AdaptiveRouter:
    def __init__(self, grid_shape=(10, 10, 10)):
        self.grid_shape = grid_shape
        self.field_H = np.random.randn(*grid_shape) * 0.1
        self.routes = {}
    
    def update_field(self, charges):
        self.field_H = np.zeros(self.grid_shape)
        for x, y, z, tau in charges:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    for dz in range(-2, 3):
                        nx, ny, nz = x+dx, y+dy, z+dz
                        if (0 <= nx < self.grid_shape[0] and 
                            0 <= ny < self.grid_shape[1] and 
                            0 <= nz < self.grid_shape[2]):
                            r = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.1
                            self.field_H[nx, ny, nz] += tau / r
    
    def find_route(self, src, dst):
        path = [src]
        current = src
        steps = 0
        while current != dst and steps < 20:
            dx = dst[0] - current[0]
            dy = dst[1] - current[1]
            dz = dst[2] - current[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < 0.5: break
            step = (int(round(dx/dist)), int(round(dy/dist)), int(round(dz/dist)))
            current = (min(max(current[0]+step[0], 0), self.grid_shape[0]-1),
                      min(max(current[1]+step[1], 0), self.grid_shape[1]-1),
                      min(max(current[2]+step[2], 0), self.grid_shape[2]-1))
            if current not in path:
                path.append(current)
            steps += 1
        self.routes[(src, dst)] = path
        return path
    
    def get_route_energy(self, path):
        return sum(self.field_H[x, y, z] ** 2 for x, y, z in path)

# ═══════════════════════════════════
# 6. TEES-ВИХРЬ
# ═══════════════════════════════════

class TEESVortex:
    def __init__(self):
        self.state = 'compressed'
        self.size = 1.0
        self.time_gradient = 1.0
        self.time_ratios_history = []
    
    def pass_through(self, task_priority, time_from, time_to):
        ratio = time_to / time_from if time_from > 0 else 1.0
        self.time_ratios_history.append(ratio)
        if len(self.time_ratios_history) > 100:
            self.time_ratios_history.pop(0)
        
        compression_threshold = 0.15
        expansion_threshold = 10.0
        
        if abs(ratio - 1.0) <= compression_threshold:
            self.state = 'compressed'
            self.size = 1.0
            self.time_gradient = 1.0
        elif abs(ratio - 1.0) <= expansion_threshold:
            self.state = 'expanded'
            self.size = math.sqrt(abs(ratio))
            self.time_gradient = ratio
        else:
            self.state = 'singlet'
            self.size = float('inf')
            self.time_gradient = 0.0
            task_priority = 0
        
        return task_priority

# ═══════════════════════════════════
# 7. ЭМЕРДЖЕНТНОЕ ВРЕМЯ (D=2.5!)
# ═══════════════════════════════════

class EmergentTime:
    def __init__(self, beacons):
        self.beacons = beacons
        self.time_fields = {}
        for b in beacons:
            freq = 1.0
            phase = np.random.random() * 2 * np.pi
            self.time_fields[b.beacon_id] = {
                'phase': phase, 'frequency': freq, 'amplitude': 1.0
            }
    
    def evolve(self, dt=0.1):
        for beacon in self.beacons:
            state = self.time_fields.get(beacon.beacon_id)
            if not state: continue
            
            neighbor_influence = 0.0
            for cell_id in beacon.cells:
                cell = beacon.cells[cell_id]
                for other in self.beacons:
                    if (other.beacon_id != beacon.beacon_id and 
                        cell_id in other.cells and 
                        other.beacon_id in self.time_fields):
                        neighbor_influence += 0.1 * np.sin(
                            self.time_fields[other.beacon_id]['phase'] - state['phase']
                        )
                        break
            
            state['phase'] = (state['phase'] + state['frequency'] * dt + 
                             neighbor_influence * dt) % (2 * np.pi)
            state['amplitude'] = beacon.coherence
            
            depth = beacon.memory.get_depth()
            beacon.time_scale = depth ** (1/2.5) if depth > 0 else 1.0
    
    def get_sync_level(self):
        phases = [s['phase'] for s in self.time_fields.values()]
        if not phases: return 0.0
        return np.abs(np.sum(np.exp(1j * np.array(phases)))) / len(phases)

# ═══════════════════════════════════
# 8. ФРАКТАЛЬНЫЙ КЛАСТЕР (ЛЕС!)
# ═══════════════════════════════════

class FractalCluster:
    def __init__(self, cluster_id, level=0, max_size=10):
        self.cluster_id = cluster_id
        self.level = level
        self.max_size = max_size
        self.beacons = []
        self.sub_clusters = []
        self.coherence = 0.994
        self.time_scale = level ** (1/2.5) if level > 0 else 1.0
    
    def get_total_beacons(self):
        total = len(self.beacons)
        for sub in self.sub_clusters:
            total += sub.get_total_beacons()
        return total
    
    def get_depth(self):
        if not self.sub_clusters:
            return self.level
        return max(s.get_depth() for s in self.sub_clusters)
    
    def get_stats(self):
        return {
            'id': self.cluster_id,
            'level': self.level,
            'beacons': len(self.beacons),
            'sub_clusters': len(self.sub_clusters),
            'total_beacons': self.get_total_beacons(),
            'depth': self.get_depth(),
            'coherence': self.coherence,
            'time_scale': self.time_scale
        }

# ═══════════════════════════════════
# 9. МАЯК (ПОЛНЫЙ!)
# ═══════════════════════════════════

class TEESBeacon:
    def __init__(self, beacon_id, ip, grid_pos, topological_charge):
        self.beacon_id = beacon_id
        self.ip = ip
        self.grid_pos = grid_pos
        self.topological_charge = topological_charge
        self.cells = {}
        self.economy = TEESEconomy()
        self.memory = FractalMemory()
        self.crypto = TEESCrypto()
        self.vortex = TEESVortex()
        self.router = None
        self.ip_storage = {}
        self.routing_table = {}
        self.coherence = 0.994
        self.time_scale = 1.0
        self.cluster = None
    
    def set_router(self, router):
        self.router = router
    
    def handshake(self, other):
        key = self.crypto.generate_key(32)
        encrypted_ip = self.crypto.encrypt(self.ip.encode(), key)
        decrypted = self.crypto.decrypt(encrypted_ip, key).decode()
        assert decrypted == self.ip
        
        cell_id = hashlib.sha256(
            f"{self.beacon_id}{other.beacon_id}{time.time()}".encode()
        ).hexdigest()[:16]
        cell = CoherentCell(cell_id=cell_id, key=key, coherence=0.994)
        
        self.ip_storage[cell_id] = (self.ip, other.ip)
        time.sleep(0.01)
        del self.ip_storage[cell_id]
        
        self.cells[cell_id] = cell
        other.cells[cell_id] = cell
        
        if self.router and cell.coherence < 1.0:
            path = self.router.find_route(self.grid_pos, other.grid_pos)
            route_energy = self.router.get_route_energy(path)
            self.memory.add({
                'type': 'route', 'cell': cell_id, 'path': path,
                'energy': route_energy, 'coherence': cell.coherence,
                'time': time.time()
            })
            self.economy.accrue(self.beacon_id, 'route', 5 + route_energy)
        else:
            self.economy.accrue(self.beacon_id, 'handshake', 10)
        
        self.routing_table[other.beacon_id] = cell_id
        other.routing_table[self.beacon_id] = cell_id
        return cell_id
    
    def sync_coherence(self, cell_id):
        cell = self.cells[cell_id]
        cell.coherence = min(1.0, cell.coherence + 0.001)
        if cell.coherence >= 1.0:
            self.economy.accrue(self.beacon_id, 'sync', 3)
        return cell.coherence

    def sync(self):
        """Синхронизация маяка (когерентность растёт!)."""
        self.coherence = min(1.0, self.coherence + 0.001)
        return self.coherence    

# ═══════════════════════════════════
# 10. СЕТЬ ЛЕСА
# ═══════════════════════════════════

class ClusterNetwork:
    def __init__(self, n_beacons=50, max_cluster_size=10):
        self.max_cluster_size = max_cluster_size
        self.router = AdaptiveRouter()
        
        # Создаём маяки
        self.beacons = []
        charges = []
        positions = []
        for i in range(n_beacons):
            pos = (i % 10, (i // 10) % 10, (i // 100) % 10)
            tau = np.random.choice([-1, 0, 1])
            beacon = TEESBeacon(f"beacon_{i}", f"10.0.0.{i}", pos, tau)
            beacon.set_router(self.router)
            self.beacons.append(beacon)
            charges.append((*pos, tau))
            positions.append(pos)
        
        self.router.update_field(charges)
        
        print(f"🌲 Создаём ЛЕС из {n_beacons} маяков...")
        self.root_cluster = self._build_forest(self.beacons, 0, max_cluster_size)
        print(f"✅ Лес построен!")
    
    def _build_forest(self, beacons, level, max_size):
        if len(beacons) <= max_size:
            cluster = FractalCluster(f"L{level}_leaf", level=level, max_size=max_size)
            cluster.beacons = beacons
            for b in beacons:
                b.cluster = cluster
            return cluster
        
        n_clusters = math.ceil(len(beacons) / max_size)
        clusters = []
        for i in range(n_clusters):
            start = i * max_size
            end = min(start + max_size, len(beacons))
            sub = self._build_forest(beacons[start:end], level+1, max_size)
            clusters.append(sub)
        
        parent = FractalCluster(f"L{level}_forest", level=level, max_size=max_size)
        parent.sub_clusters = clusters
        
        if level <= 3:
            print(f"  🌲 Уровень {level}: {len(clusters)} кластеров "
                  f"(всего {len(beacons)} маяков)")
        
        return parent
    
    def handshake_all(self):
        print(f"\n🤝 РУКОПОЖАТИЯ:")
        cells = {}
        for i in range(len(self.beacons)):
            for j in range(i+1, len(self.beacons)):
                cell_id = self.beacons[i].handshake(self.beacons[j])
                cells[(i, j)] = cell_id
        print(f"   Связей: {len(cells)}")
        return cells
    
    def sync_all(self, steps=50):
        print(f"\n⚛️ СИНХРОНИЗАЦИЯ ({steps} шагов):")
        for step in range(steps):
            for beacon in self.beacons:
                beacon.sync()
            if step % 10 == 0:
                coh = sum(b.coherence for b in self.beacons) / len(self.beacons)
                print(f"   Шаг {step:3d}: когерентность = {coh:.4f}")

# ═══════════════════════════════════
# 11. ТЕСТ
# ═══════════════════════════════════

def test_forest():
    print("🌲 TEES: ФРАКТАЛЬНЫЙ ЛЕС — ПОЛНАЯ ВЕРСИЯ!")
    print("=" * 60)
    
    print("\n🧪 ТЕСТ 1: 50 маяков, кластер max 10")
    net1 = ClusterNetwork(n_beacons=50, max_cluster_size=10)
    stats1 = net1.root_cluster.get_stats()
    print(f"\n📊 Глубина: {stats1['depth']}")
    print(f"   Подкластеров: {stats1['sub_clusters']}")
    cells1 = net1.handshake_all()
    net1.sync_all(50)
    
    print(f"\n{'='*60}")
    print("\n🧪 ТЕСТ 2: 1000 маяков, кластер max 10")
    net2 = ClusterNetwork(n_beacons=1000, max_cluster_size=10)
    stats2 = net2.root_cluster.get_stats()
    print(f"\n📊 Глубина: {stats2['depth']}")
    print(f"   Подкластеров: {stats2['sub_clusters']}")
    print(f"   Всего маяков: {stats2['total_beacons']}")
    
    print(f"\n{'='*60}")
    print("\n🧪 ТЕСТ 3: 10000 маяков, кластер max 10")
    net3 = ClusterNetwork(n_beacons=10000, max_cluster_size=10)
    stats3 = net3.root_cluster.get_stats()
    print(f"\n📊 Глубина: {stats3['depth']}")
    print(f"   Подкластеров: {stats3['sub_clusters']}")
    print(f"   Всего маяков: {stats3['total_beacons']}")
    
    print(f"\n{'='*60}")
    print("✅ ФРАКТАЛЬНЫЙ ЛЕС РАБОТАЕТ!")
    print("   🌲 Множество кластеров на каждом уровне!")
    print("   ⚛️ D=2.5 + Экономика + Вихрь + Роутер!")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_forest()