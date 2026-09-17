# tees_cluster.py
# ⚛️ TEES-кластер: кубиты-специалисты, round-robin, TSP, Гровер

import hashlib
import math
import os
import threading
import time
from typing import Dict, List, Any, Optional, Tuple


class Qubit:
    """
    ⚛️ Кубит — лёгкая вычислительная единица.
    Специализируется на типах задач, ведёт статистику.
    """
    
    def __init__(self, qubit_id: str, core_id: int):
        self.id = qubit_id
        self.core_id = core_id
        self.active = True
        self.coherence = 1.0
        self.tasks_completed = 0
        self.last_task_time = None
        self.created_at = time.time()
        
        # Самоназначение: статистика по типам задач
        self.task_history: Dict[str, int] = {}
        self.avg_time: Dict[str, float] = {}
        
        self.lock = threading.Lock()
    
    def compute(self, task: Dict[str, Any]) -> Optional[str]:
        if not self.active:
            return None
        
        task_type = task.get('type', '')
        task_data = task.get('data', '')
        
        start_time = time.time()
        result = None
        
        if task_type == 'sha256':
            result = hashlib.sha256(task_data.encode()).hexdigest()
        elif task_type == 'md5':
            result = hashlib.md5(task_data.encode()).hexdigest()
        elif task_type == 'tsp':
            cities = task.get('cities', [])
            if hasattr(self, 'solve_tsp'):
                route, distance = self.solve_tsp(cities)
                result = f"distance={distance:.2f}"
            else:
                result = None
        
        elapsed = time.time() - start_time
        
        with self.lock:
            if result:
                self.tasks_completed += 1
                self.last_task_time = time.time()
                self.task_history[task_type] = self.task_history.get(task_type, 0) + 1
                
                if task_type in self.avg_time:
                    self.avg_time[task_type] = 0.8 * self.avg_time[task_type] + 0.2 * elapsed
                else:
                    self.avg_time[task_type] = elapsed
        
        return result
    
    def get_specialty_score(self, task_type: str) -> float:
        with self.lock:
            count = self.task_history.get(task_type, 0)
            avg = self.avg_time.get(task_type, 0)
        
        if count == 0:
            return 0.0
        
        speed_score = 1.0 / (1.0 + avg) if avg > 0 else 1.0
        return count * 0.7 + speed_score * 0.3
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'id': self.id,
                'core': self.core_id,
                'active': self.active,
                'coherence': self.coherence,
                'tasks_completed': self.tasks_completed,
                'specialties': dict(self.task_history),
                'age': time.time() - self.created_at
            }


class TSPQubit(Qubit):
    """
    🗺️ Кубит-коммивояжёр.
    """
    
    def __init__(self, qubit_id: str, core_id: int):
        super().__init__(qubit_id, core_id)
        self.best_route = None
        self.best_distance = float('inf')
        self.tsp_experience = 0
    
    def solve_tsp(self, cities: List[Tuple[float, float]]) -> Tuple[List[int], float]:
        if not cities or len(cities) < 2:
            return [], 0.0
        
        # 🔑 Для больших групп — быстрый nearest neighbor без 2-opt
        if len(cities) > 1000:
            route = self._nearest_neighbor_fast(cities)
            distance = self._calculate_distance(route, cities)
        else:
            route = self._nearest_neighbor(cities)
            route = self._two_opt(route, cities)
            distance = self._calculate_distance(route, cities)
        
        if distance < self.best_distance:
            self.best_distance = distance
            self.best_route = route.copy()
            self.tsp_experience += 1
        
        return route, distance
    
    def _nearest_neighbor(self, cities: List[Tuple[float, float]]) -> List[int]:
        n = len(cities)
        unvisited = set(range(1, n))
        route = [0]
        current = 0
        
        while unvisited:
            next_city = min(unvisited, key=lambda c: self._distance(cities[current], cities[c]))
            route.append(next_city)
            unvisited.remove(next_city)
            current = next_city
        
        return route
    
    def _nearest_neighbor_fast(self, cities: List[Tuple[float, float]], grid_size: int = 100) -> List[int]:
        """
        🔑 БЫСТРЫЙ nearest neighbor через пространственную сетку.
        Вместо O(n²) — почти O(n).
        """
        n = len(cities)
        if n < 2:
            return [0] if n == 1 else []
        
        # Находим границы
        min_x = min(c[0] for c in cities)
        max_x = max(c[0] for c in cities)
        min_y = min(c[1] for c in cities)
        max_y = max(c[1] for c in cities)
        
        range_x = max(max_x - min_x, 0.001)
        range_y = max(max_y - min_y, 0.001)
        
        cell_size_x = range_x / grid_size
        cell_size_y = range_y / grid_size
        
        # Строим сетку
        grid: Dict[Tuple[int, int], List[int]] = {}
        
        for i, (x, y) in enumerate(cities):
            cell_x = int((x - min_x) / cell_size_x)
            cell_y = int((y - min_y) / cell_size_y)
            cell_x = min(cell_x, grid_size - 1)
            cell_y = min(cell_y, grid_size - 1)
            key = (cell_x, cell_y)
            if key not in grid:
                grid[key] = []
            grid[key].append(i)
        
        route = [0]
        unvisited = set(range(1, n))
        current = 0
        
        while unvisited:
            cx, cy = cities[current]
            cell_x = int((cx - min_x) / cell_size_x)
            cell_y = int((cy - min_y) / cell_size_y)
            cell_x = min(cell_x, grid_size - 1)
            cell_y = min(cell_y, grid_size - 1)
            
            best_city = None
            best_dist = float('inf')
            
            # Ищем в расширяющейся окрестности
            radius = 1
            while best_city is None and radius < grid_size:
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        key = (cell_x + dx, cell_y + dy)
                        if key in grid:
                            for c in grid[key]:
                                if c in unvisited:
                                    d = self._distance(cities[current], cities[c])
                                    if d < best_dist:
                                        best_dist = d
                                        best_city = c
                radius += 1
            
            # Fallback: если не нашли — перебор
            if best_city is None:
                for c in unvisited:
                    d = self._distance(cities[current], cities[c])
                    if d < best_dist:
                        best_dist = d
                        best_city = c
            
            route.append(best_city)
            unvisited.remove(best_city)
            current = best_city
        
        return route
    
    def _two_opt(self, route: List[int], cities: List[Tuple[float, float]]) -> List[int]:
        improved = True
        best_route = route.copy()
        best_distance = self._calculate_distance(best_route, cities)
        
        while improved:
            improved = False
            
            for i in range(1, len(best_route) - 2):
                for j in range(i + 1, len(best_route)):
                    if j - i == 1:
                        continue
                    
                    new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                    new_distance = self._calculate_distance(new_route, cities)
                    
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
                        break
                
                if improved:
                    break
        
        return best_route
    
    def _calculate_distance(self, route: List[int], cities: List[Tuple[float, float]]) -> float:
        total = 0.0
        for i in range(len(route)):
            city_a = cities[route[i]]
            city_b = cities[route[(i + 1) % len(route)]]
            total += self._distance(city_a, city_b)
        return total
    
    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.sqrt(dx * dx + dy * dy)


class GroverQubit(Qubit):
    """
    🔍 Кубит Гровера — специализируется на поиске.
    """
    
    def __init__(self, qubit_id: str, core_id: int):
        super().__init__(qubit_id, core_id)
        self.search_count = 0
        self.found_count = 0
    
    def search(self, data: List[Any], target: Any) -> Optional[Any]:
        self.search_count += 1
        
        for i, item in enumerate(data):
            if item == target:
                self.found_count += 1
                return i
        
        return None
    
    def search_many(self, data: List[Any], targets: List[Any]) -> Dict[Any, int]:
        self.search_count += 1
        results = {}
        targets_set = set(targets)
        
        for i, item in enumerate(data):
            if item in targets_set:
                results[item] = i
                targets_set.remove(item)
                if not targets_set:
                    break
        
        if results:
            self.found_count += len(results)
        
        return results


class AdaptiveAgents:
    """
    🧠 Адаптивный автомат: учится на опыте.
    """
    
    def __init__(self, cluster):
        self.cluster = cluster
        self.history = []
    
    def get_optimal_percent(self, n_cities, current_coh=1.0):
        similar = []
        for h in self.history:
            if abs(h['n_cities'] - n_cities) < n_cities * 0.2:
                similar.append(h)
        
        if similar:
            best = min(similar, key=lambda h: h['time'])
            base_percent = best['percent']
        else:
            base_percent = 10
        
        if current_coh < 0.9:
            base_percent = max(5, int(base_percent * 0.5))
        elif current_coh > 0.99:
            base_percent = min(100, int(base_percent * 1.2))
        
        return base_percent
    
    def record(self, n_cities, percent, elapsed):
        self.history.append({
            'n_cities': n_cities,
            'percent': percent,
            'time': elapsed
        })
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
    
    def get_stats(self):
        if not self.history:
            return {'experiments': 0, 'best_percent': 0, 'best_time': 0, 'avg_time': 0}
        
        best = min(self.history, key=lambda h: h['time'])
        avg_time = sum(h['time'] for h in self.history) / len(self.history)
        
        return {
            'experiments': len(self.history),
            'best_percent': best['percent'],
            'best_time': best['time'],
            'avg_time': avg_time
        }


class TeesCluster:
    """
    ⚛️ TEES-кластер — кубиты-специалисты с самоназначением.
    """
    
    QUBITS_PER_CORE = 250
    MAX_GROUP_SIZE = 5000  # 🔑 Ограничение размера группы для TSP
    
    def __init__(self, beacon=None, cores: Optional[int] = None, qubits_per_core: Optional[int] = None):
        if qubits_per_core is not None:
            self.QUBITS_PER_CORE = qubits_per_core
        
        self.beacon = beacon
        self.cores = cores or os.cpu_count() or 1
        self.total_qubits = self.cores * self.QUBITS_PER_CORE
        
        self.qubits: List[Qubit] = []
        self.lock = threading.Lock()
        
        self.tsp_qubits: List[TSPQubit] = []
        self.grover_qubits: List[GroverQubit] = []
        
        self._init_qubits()
        
        self.tasks_total = 0
        self.tasks_successful = 0
        self.created_at = time.time()
        
        self.adaptive = AdaptiveAgents(self)
        
        self.result_cache: Dict[str, Any] = {}
        self.MAX_CACHE_SIZE = 1000
    
    def _init_qubits(self):
        qubit_index = 0
        
        for core_id in range(self.cores):
            for i in range(self.QUBITS_PER_CORE):
                qubit_id = f"Q{core_id:02d}_{i:03d}"
                
                if i < 10:
                    qubit = TSPQubit(qubit_id, core_id)
                    self.tsp_qubits.append(qubit)
                elif i < 20:
                    qubit = GroverQubit(qubit_id, core_id)
                    self.grover_qubits.append(qubit)
                else:
                    qubit = Qubit(qubit_id, core_id)
                
                self.qubits.append(qubit)
                qubit_index += 1
    
    def compute(self, task: Dict[str, Any]) -> List[Optional[str]]:
        with self.lock:
            self.tasks_total += 1
            
            for i in range(len(self.qubits)):
                idx = (self.tasks_total + i) % len(self.qubits)
                qubit = self.qubits[idx]
                if qubit.active:
                    break
            else:
                return [None]
        
        result = qubit.compute(task)
        
        if result:
            with self.lock:
                self.tasks_successful += 1
        
        return [result]
    
    def compute_many(self, tasks: List[Dict[str, Any]]) -> List[Optional[str]]:
        results = []
        task_index = 0
        total_tasks = len(tasks)
        
        while task_index < total_tasks:
            with self.lock:
                qubit = self.qubits[(self.tasks_total + task_index) % len(self.qubits)]
            
            result = qubit.compute(tasks[task_index])
            results.append(result)
            task_index += 1
        
        return results
    
    def compute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Optional[str]]:
        results = [None] * len(tasks)
        tasks_per_core = math.ceil(len(tasks) / self.cores)
        
        def worker(core_id: int):
            start_idx = core_id * tasks_per_core
            end_idx = min(start_idx + tasks_per_core, len(tasks))
            
            for i in range(start_idx, end_idx):
                qubit = self.qubits[(self.tasks_total + i) % len(self.qubits)]
                results[i] = qubit.compute(tasks[i])
        
        threads = []
        for core_id in range(min(self.cores, len(tasks))):
            t = threading.Thread(target=worker, args=(core_id,), daemon=True)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        return results
    
    def solve_tsp(self, cities: List[Tuple[float, float]]) -> Dict[str, Any]:
        if not cities or len(cities) < 2:
            return {'route': [], 'distance': 0.0, 'qubit': None}
        
        best_qubit = None
        best_score = -1
        
        for qubit in self.tsp_qubits:
            if not qubit.active:
                continue
            score = qubit.tsp_experience * 0.7 + qubit.get_specialty_score('tsp') * 0.3
            if score > best_score:
                best_score = score
                best_qubit = qubit
        
        if best_qubit is None:
            best_qubit = self.tsp_qubits[0]
        
        route, distance = best_qubit.solve_tsp(cities)
        
        return {
            'route': route,
            'distance': distance,
            'qubit': best_qubit.id,
            'qubit_experience': best_qubit.tsp_experience
        }
    
    def solve_tsp_parallel(self, cities: List[Tuple[float, float]], n_partitions: int = 10) -> Dict[str, Any]:
        n_cities = len(cities)
        
        if n_cities <= n_partitions:
            return self.solve_tsp(cities)
        
        partition_size = n_cities // n_partitions
        partitions = []
        
        for i in range(n_partitions):
            start = i * partition_size
            end = start + partition_size if i < n_partitions - 1 else n_cities
            partitions.append(cities[start:end])
        
        results = [None] * len(partitions)
        
        def solve_partition(idx: int):
            results[idx] = self.solve_tsp(partitions[idx])
        
        threads = []
        for i in range(len(partitions)):
            t = threading.Thread(target=solve_partition, args=(i,), daemon=True)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        full_route = []
        total_distance = 0.0
        
        for i, result in enumerate(results):
            offset = i * partition_size
            
            if i > 0:
                prev_last = full_route[-1]
                curr_first = result['route'][0] + offset
                transition = math.sqrt(
                    (cities[prev_last][0] - cities[curr_first][0])**2 +
                    (cities[prev_last][1] - cities[curr_first][1])**2
                )
                total_distance += transition
            
            for city_idx in result['route']:
                full_route.append(city_idx + offset)
            
            total_distance += result['distance']
        
        if full_route:
            closing = math.sqrt(
                (cities[full_route[-1]][0] - cities[full_route[0]][0])**2 +
                (cities[full_route[-1]][1] - cities[full_route[0]][1])**2
            )
            total_distance += closing
        
        return {
            'route': full_route,
            'distance': total_distance,
            'qubits_used': len(results),
            'partitions': n_partitions
        }
    
    def solve_tsp_massive_parallel(self, cities, agents_percent=100):
        """
        ⚡ Массивное параллельное TSP с ограничением размера групп.
        """
        n_cities = len(cities)
        n_agents = max(2, int(len(self.qubits) * agents_percent / 100))
        
        if n_cities <= 1:
            return {'route': [], 'distance': 0.0, 'agents_used': 0}
        
        # 🔑 Ограничиваем размер группы — чтобы O(n²) не взрывался
        cities_per_agent = min(
            max(2, n_cities // n_agents),
            self.MAX_GROUP_SIZE
        )
        
        n_agents_used = min(n_agents, max(1, n_cities // cities_per_agent))
        
        groups = []
        for i in range(n_agents_used):
            start = i * cities_per_agent
            end = min(start + cities_per_agent, n_cities)
            if start < n_cities and end > start:
                groups.append((i, cities[start:end]))
        
        results = []
        for i, group in groups:
            if len(group) < 2:
                continue
            
            qubit = self.qubits[i % len(self.qubits)]
            
            if hasattr(qubit, 'solve_tsp'):
                route, dist = qubit.solve_tsp(group)
            else:
                route, dist = self._simple_tsp(group)
            
            results.append((i, route, dist))
        
        full_route = []
        total_distance = 0.0
        
        for group_idx, route, dist in results:
            offset = group_idx * cities_per_agent
            for city_idx in route:
                full_route.append(city_idx + offset)
            total_distance += dist
        
        for i in range(len(results) - 1):
            if i + 1 < len(results):
                last_city = results[i][1][-1] + results[i][0] * cities_per_agent
                first_city = results[i+1][1][0] + results[i+1][0] * cities_per_agent
                
                if last_city < len(cities) and first_city < len(cities):
                    dx = cities[last_city][0] - cities[first_city][0]
                    dy = cities[last_city][1] - cities[first_city][1]
                    total_distance += math.sqrt(dx**2 + dy**2)
        
        return {
            'route': full_route,
            'distance': total_distance,
            'agents_used': len(results)
        }
    
    def _simple_tsp(self, cities):
        if len(cities) < 2:
            return [], 0.0
        
        n = len(cities)
        unvisited = set(range(1, n))
        route = [0]
        current = 0
        
        while unvisited:
            next_city = min(unvisited, 
                          key=lambda c: (cities[current][0] - cities[c][0])**2 + 
                                       (cities[current][1] - cities[c][1])**2)
            route.append(next_city)
            unvisited.remove(next_city)
            current = next_city
        
        dist = 0.0
        for i in range(len(route)):
            a = cities[route[i]]
            b = cities[route[(i+1) % len(route)]]
            dist += math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)
        
        return route, dist
    
    def grover_search(self, data: List[Any], target: Any) -> Dict[str, Any]:
        best_qubit = None
        best_score = -1
        
        for qubit in self.grover_qubits:
            if not qubit.active:
                continue
            score = qubit.get_specialty_score('grover_search')
            if score > best_score:
                best_score = score
                best_qubit = qubit
        
        if best_qubit is None:
            best_qubit = self.grover_qubits[0]
        
        index = best_qubit.search(data, target)
        
        return {
            'found': index is not None,
            'index': index,
            'qubit': best_qubit.id,
            'searches': best_qubit.search_count
        }
    
    def grover_search_parallel(self, data: List[Any], target: Any, n_partitions: int = None) -> Dict[str, Any]:
        n_data = len(data)
        
        if n_partitions is None:
            n_partitions = min(len(self.grover_qubits), self.cores * 10)
        
        if n_data <= n_partitions:
            return self.grover_search(data, target)
        
        partition_size = n_data // n_partitions
        partitions = []
        
        for i in range(n_partitions):
            start = i * partition_size
            end = start + partition_size if i < n_partitions - 1 else n_data
            partitions.append((start, data[start:end]))
        
        results = [None] * len(partitions)
        
        def search_partition(idx: int):
            start, partition = partitions[idx]
            
            best_qubit = None
            best_score = -1
            
            for qubit in self.grover_qubits:
                if not qubit.active:
                    continue
                score = qubit.get_specialty_score('grover_search')
                if score > best_score:
                    best_score = score
                    best_qubit = qubit
            
            if best_qubit is None:
                best_qubit = self.grover_qubits[idx % len(self.grover_qubits)]
            
            local_idx = best_qubit.search(partition, target)
            
            if local_idx is not None:
                results[idx] = start + local_idx
        
        threads = []
        for i in range(len(partitions)):
            t = threading.Thread(target=search_partition, args=(i,), daemon=True)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        for idx in results:
            if idx is not None:
                return {'found': True, 'index': idx, 'partitions': n_partitions}
        
        return {'found': False, 'index': None, 'partitions': n_partitions}
    
    def benchmark_sha256(self, count: int = 1000) -> Dict[str, Any]:
        tasks = [{'type': 'sha256', 'data': f"TEES benchmark {i}"} for i in range(count)]
        
        start_time = time.time()
        results = self.compute_many(tasks)
        elapsed = time.time() - start_time
        
        successful = sum(1 for r in results if r)
        tasks_per_sec = successful / elapsed if elapsed > 0 else 0
        
        return {
            'tasks': successful,
            'elapsed': elapsed,
            'tasks_per_sec': tasks_per_sec,
            'total_qubits': self.total_qubits,
            'success_rate': successful / count if count > 0 else 0
        }
    
    def benchmark_tsp(self, n_cities: int = 50) -> Dict[str, Any]:
        import random
        random.seed(42)
        
        cities = [(random.random() * 100, random.random() * 100) for _ in range(n_cities)]
        
        start_time = time.time()
        result = self.solve_tsp(cities)
        elapsed = time.time() - start_time
        
        return {
            'cities': n_cities,
            'distance': result['distance'],
            'elapsed': elapsed,
            'qubit': result['qubit']
        }
    
    def benchmark_grover(self, n_items: int = 100000, target: Any = None) -> Dict[str, Any]:
        import random
        random.seed(42)
        
        data = list(range(n_items))
        if target is None:
            target = n_items - 1
        
        start_time = time.time()
        result = self.grover_search_parallel(data, target)
        elapsed = time.time() - start_time
        
        return {
            'items': n_items,
            'found': result['found'],
            'elapsed': elapsed,
            'partitions': result.get('partitions', 1)
        }
    
    def check_health(self) -> int:
        dead_count = 0
        recovered = []
        
        for qubit in self.qubits:
            if not qubit.active:
                dead_count += 1
                qubit.active = True
                qubit.coherence = 1.0
                recovered.append(qubit.id)
        
        if recovered:
            print(f"  ⚛️ Восстановлено кубитов: {len(recovered)}")
            if len(recovered) <= 5:
                for qid in recovered:
                    print(f"     {qid}")
        
        return dead_count
    
    def measure_balance(self):
        tasks_per_agent = [q.tasks_completed for q in self.qubits]
        
        if not tasks_per_agent:
            return {'avg': 0, 'max': 0, 'min': 0, 'imbalance': 0, 'efficiency': 0}
        
        avg = sum(tasks_per_agent) / len(tasks_per_agent)
        max_load = max(tasks_per_agent)
        min_load = min(tasks_per_agent)
        imbalance = max_load - avg
        
        efficiency = avg / max_load if max_load > 0 else 0
        
        return {
            'avg': avg,
            'max': max_load,
            'min': min_load,
            'imbalance': imbalance,
            'efficiency': efficiency,
            'total_agents': len(tasks_per_agent)
        }
    
    def measure_internal_coherence(self):
        coherences = [q.coherence for q in self.qubits]
        
        if not coherences:
            return {'min': 0, 'max': 0, 'avg': 0, 'delta': 0, 'n': 0}
        
        min_c = min(coherences)
        max_c = max(coherences)
        avg_c = sum(coherences) / len(coherences)
        delta = max_c - min_c
        
        return {'min': min_c, 'max': max_c, 'avg': avg_c, 'delta': delta, 'n': len(coherences)}
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'cores': self.cores,
            'qubits_per_core': self.QUBITS_PER_CORE,
            'total_qubits': self.total_qubits,
            'active_qubits': sum(1 for q in self.qubits if q.active),
            'tsp_qubits': len(self.tsp_qubits),
            'grover_qubits': len(self.grover_qubits),
            'tasks_total': self.tasks_total,
            'tasks_successful': self.tasks_successful,
            'uptime': time.time() - self.created_at
        }
    
    def get_qubit_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [q.get_stats() for q in self.qubits[:limit]]


if __name__ == "__main__":
    print("⚛️ TEES-кластер — тесты")
    print("=" * 60)
    
    cluster = TeesCluster()
    stats = cluster.get_stats()
    
    print(f"Ядер: {stats['cores']}")
    print(f"Кубитов: {stats['total_qubits']} ({stats['qubits_per_core']}/ядро)")
    print(f"TSP-кубитов: {stats['tsp_qubits']}")
    print(f"Гровер-кубитов: {stats['grover_qubits']}")
    print()
    
    print("📊 SHA-256 бенчмарк...")
    bench = cluster.benchmark_sha256(1000)
    print(f"  Задач: {bench['tasks']}")
    print(f"  Время: {bench['elapsed']:.3f} сек")
    print(f"  Скорость: {bench['tasks_per_sec']:.0f} задач/сек")
    print()
    
    print("🗺️ TSP тест (50 городов)...")
    tsp_bench = cluster.benchmark_tsp(50)
    print(f"  Городов: {tsp_bench['cities']}")
    print(f"  Дистанция: {tsp_bench['distance']:.2f}")
    print(f"  Время: {tsp_bench['elapsed']:.3f} сек")
    print(f"  Кубит: {tsp_bench['qubit']}")
    print()
    
    print("🗺️ TSP параллельный (100 городов, 10 групп)...")
    import random
    random.seed(42)
    cities_100 = [(random.random() * 100, random.random() * 100) for _ in range(100)]
    start = time.time()
    tsp_par = cluster.solve_tsp_parallel(cities_100, n_partitions=10)
    tsp_par_time = time.time() - start
    print(f"  Дистанция: {tsp_par['distance']:.2f}")
    print(f"  Время: {tsp_par_time:.3f} сек")
    print(f"  Кубитов: {tsp_par['qubits_used']}")
    print()
    
    print("🔍 Гровер поиск (100,000 элементов)...")
    grover_bench = cluster.benchmark_grover(100000)
    print(f"  Элементов: {grover_bench['items']}")
    print(f"  Найден: {grover_bench['found']}")
    print(f"  Время: {grover_bench['elapsed']:.4f} сек")
    print(f"  Партиций: {grover_bench['partitions']}")
    print()
    
    print("🔍 Первые 5 кубитов:")
    for q in cluster.get_qubit_stats(5):
        specialties = q.get('specialties', {})
        spec_str = ", ".join(f"{k}:{v}" for k, v in specialties.items()) or "нет"
        print(f"  {q['id']}: core={q['core']}, tasks={q['tasks_completed']}, спец: {spec_str}")
    
    print()
    print("✅ Тесты завершены!")