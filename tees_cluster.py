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
        self.task_history: Dict[str, int] = {}  # type -> count
        self.avg_time: Dict[str, float] = {}    # type -> avg_time
        
        self.lock = threading.Lock()  # Защита статистики
    
    def compute(self, task: Dict[str, Any]) -> Optional[str]:
        """
        Прямой вызов — без TCP, без сокетов.
        """
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
                
                # Обновляем статистику
                self.task_history[task_type] = self.task_history.get(task_type, 0) + 1
                
                if task_type in self.avg_time:
                    # Экспоненциальное скользящее среднее
                    self.avg_time[task_type] = 0.8 * self.avg_time[task_type] + 0.2 * elapsed
                else:
                    self.avg_time[task_type] = elapsed
        
        return result
    
    def get_specialty_score(self, task_type: str) -> float:
        """
        Оценка специализации кубита на типе задачи.
        Больше опыта + быстрее = выше score.
        """
        with self.lock:
            count = self.task_history.get(task_type, 0)
            avg = self.avg_time.get(task_type, 0)
        
        if count == 0:
            return 0.0
        
        # Нормализуем: опыт * скорость
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
    Специализируется на поиске коротких путей.
    """
    
    def __init__(self, qubit_id: str, core_id: int):
        super().__init__(qubit_id, core_id)
        self.best_route = None
        self.best_distance = float('inf')
        self.tsp_experience = 0
    
    def solve_tsp(self, cities: List[Tuple[float, float]]) -> Tuple[List[int], float]:
        """
        Детерминированный поиск пути: nearest neighbor + 2-opt.
        """
        if not cities or len(cities) < 2:
            return [], 0.0
        
        # 1. Жадный ближайший сосед
        route = self._nearest_neighbor(cities)
        
        # 2. Улучшение через 2-opt
        route = self._two_opt(route, cities)
        
        distance = self._calculate_distance(route, cities)
        
        # Запоминаем лучший результат
        if distance < self.best_distance:
            self.best_distance = distance
            self.best_route = route.copy()
            self.tsp_experience += 1
        
        return route, distance
    
    def _nearest_neighbor(self, cities: List[Tuple[float, float]]) -> List[int]:
        """Жадный алгоритм ближайшего соседа."""
        n = len(cities)
        unvisited = set(range(1, n))
        route = [0]  # Начинаем с города 0
        current = 0
        
        while unvisited:
            # Находим ближайший непосещённый город
            next_city = min(unvisited, key=lambda c: self._distance(cities[current], cities[c]))
            route.append(next_city)
            unvisited.remove(next_city)
            current = next_city
        
        return route
    
    def _two_opt(self, route: List[int], cities: List[Tuple[float, float]]) -> List[int]:
        """
        2-opt улучшение: разворачиваем участки маршрута.
        Детерминированный: всегда проверяем все пары.
        """
        improved = True
        best_route = route.copy()
        best_distance = self._calculate_distance(best_route, cities)
        
        while improved:
            improved = False
            
            for i in range(1, len(best_route) - 2):
                for j in range(i + 1, len(best_route)):
                    if j - i == 1:
                        continue  # Соседние — нет смысла
                    
                    # Пробуем развернуть участок [i..j]
                    new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                    new_distance = self._calculate_distance(new_route, cities)
                    
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
                        
                        # Детерминизм: первое улучшение применяем сразу
                        break
                
                if improved:
                    break
        
        return best_route
    
    def _calculate_distance(self, route: List[int], cities: List[Tuple[float, float]]) -> float:
        """Полная длина маршрута."""
        total = 0.0
        for i in range(len(route)):
            city_a = cities[route[i]]
            city_b = cities[route[(i + 1) % len(route)]]
            total += self._distance(city_a, city_b)
        return total
    
    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """Евклидово расстояние."""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


class GroverQubit(Qubit):
    """
    🔍 Кубит Гровера — специализируется на поиске.
    Детерминированный параллельный поиск.
    """
    
    def __init__(self, qubit_id: str, core_id: int):
        super().__init__(qubit_id, core_id)
        self.search_count = 0
        self.found_count = 0
    
    def search(self, data: List[Any], target: Any) -> Optional[Any]:
        """
        Поиск целевого элемента.
        Возвращает индекс или None.
        """
        self.search_count += 1
        
        for i, item in enumerate(data):
            if item == target:
                self.found_count += 1
                return i
        
        return None
    
    def search_many(self, data: List[Any], targets: List[Any]) -> Dict[Any, int]:
        """
        Поиск нескольких целей за один проход.
        """
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


class TeesCluster:
    """
    ⚛️ TEES-кластер — кубиты-специалисты с самоназначением.
    Внутри — прямые вызовы (когерентность).
    TCP только снаружи.
    """
    
    QUBITS_PER_CORE = 100  # Оптимум из экспериментов
    
    def __init__(self, beacon=None, cores: Optional[int] = None):
        self.beacon = beacon
        self.cores = cores or os.cpu_count() or 1
        self.total_qubits = self.cores * self.QUBITS_PER_CORE
        
        self.qubits: List[Qubit] = []
        self.lock = threading.Lock()
        
        # Специализированные пулы
        self.tsp_qubits: List[TSPQubit] = []
        self.grover_qubits: List[GroverQubit] = []
        
        self._init_qubits()
        
        # Статистика
        self.tasks_total = 0
        self.tasks_successful = 0
        self.created_at = time.time()
        
        # Кэш результатов
        self.result_cache: Dict[str, Any] = {}
        self.MAX_CACHE_SIZE = 1000
    
    def _init_qubits(self):
        """Создаём кубиты — по 100 на ядро."""
        qubit_index = 0
        
        for core_id in range(self.cores):
            for i in range(self.QUBITS_PER_CORE):
                qubit_id = f"Q{core_id:02d}_{i:03d}"
                
                # 10% — TSP-специалисты
                if i < 10:
                    qubit = TSPQubit(qubit_id, core_id)
                    self.tsp_qubits.append(qubit)
                # 10% — Гровер-специалисты
                elif i < 20:
                    qubit = GroverQubit(qubit_id, core_id)
                    self.grover_qubits.append(qubit)
                # 80% — универсальные
                else:
                    qubit = Qubit(qubit_id, core_id)
                
                self.qubits.append(qubit)
                qubit_index += 1
    
    # ═══════════════════════════════════════════════════════════
    # 🔧 ОСНОВНЫЕ ВЫЧИСЛЕНИЯ
    # ═══════════════════════════════════════════════════════════
    
    def compute(self, task: Dict[str, Any]) -> List[Optional[str]]:
        """
        Round-robin с пропуском мёртвых кубитов.
        """
        with self.lock:
            self.tasks_total += 1
            
            # Ищем активного кубита
            for i in range(len(self.qubits)):
                idx = (self.tasks_total + i) % len(self.qubits)
                qubit = self.qubits[idx]
                if qubit.active:
                    break
            else:
                return [None]  # Все кубиты мертвы
        
        result = qubit.compute(task)
        
        if result:
            with self.lock:
                self.tasks_successful += 1
        
        return [result]
    
    def compute_many(self, tasks: List[Dict[str, Any]]) -> List[Optional[str]]:
        """
        Распределяем список задач по кубитам равномерно.
        """
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
        """
        Параллельное вычисление по ядрам.
        Каждое ядро обрабатывает свои кубиты.
        """
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
    
    # ═══════════════════════════════════════════════════════════
    # 🗺️ TSP — ЗАДАЧА КОММИВОЯЖЁРА
    # ═══════════════════════════════════════════════════════════
    
    def solve_tsp(self, cities: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Решение TSP через специализированных кубитов.
        """
        if not cities or len(cities) < 2:
            return {'route': [], 'distance': 0.0, 'qubit': None}
        
        # Находим лучшего TSP-кубита
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
        """
        Параллельное TSP: разбиваем города на группы, решаем каждую отдельно,
        потом сшиваем маршруты.
        """
        n_cities = len(cities)
        
        if n_cities <= n_partitions:
            return self.solve_tsp(cities)
        
        # Разбиваем города на группы
        partition_size = n_cities // n_partitions
        partitions = []
        
        for i in range(n_partitions):
            start = i * partition_size
            end = start + partition_size if i < n_partitions - 1 else n_cities
            partitions.append(cities[start:end])
        
        # Решаем каждую группу параллельно
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
        
        # Сшиваем маршруты с переходами
        full_route = []
        total_distance = 0.0
        
        for i, result in enumerate(results):
            offset = i * partition_size
            
            if i > 0:
                # Добавляем переход от предыдущей группы
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
        
        # Замыкаем маршрут
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
    
    # ═══════════════════════════════════════════════════════════
    # 🔍 ГРОВЕР — ПОИСК
    # ═══════════════════════════════════════════════════════════
    
    def grover_search(self, data: List[Any], target: Any) -> Dict[str, Any]:
        """
        Поиск через специализированных кубитов Гровера.
        """
        # Находим лучшего кубита
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
        """
        Параллельный поиск: разбиваем данные, ищем в каждой части.
        """
        n_data = len(data)
        
        if n_partitions is None:
            n_partitions = min(len(self.grover_qubits), self.cores * 10)
        
        if n_data <= n_partitions:
            return self.grover_search(data, target)
        
        # Разбиваем данные
        partition_size = n_data // n_partitions
        partitions = []
        
        for i in range(n_partitions):
            start = i * partition_size
            end = start + partition_size if i < n_partitions - 1 else n_data
            partitions.append((start, data[start:end]))
        
        # Ищем параллельно
        results = [None] * len(partitions)
        
        def search_partition(idx: int):
            start, partition = partitions[idx]
            
            # Выбираем лучшего свободного кубита
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
        
        # Собираем результат
        for idx in results:
            if idx is not None:
                return {
                    'found': True,
                    'index': idx,
                    'partitions': n_partitions
                }
        
        return {
            'found': False,
            'index': None,
            'partitions': n_partitions
        }
    
    # ═══════════════════════════════════════════════════════════
    # 📊 БЕНЧМАРКИ И СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════
    
    def benchmark_sha256(self, count: int = 1000) -> Dict[str, Any]:
        """Бенчмарк SHA-256 через кластер."""
        tasks = [
            {'type': 'sha256', 'data': f"TEES benchmark {i}"}
            for i in range(count)
        ]
        
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
        """Бенчмарк TSP."""
        import random
        random.seed(42)  # Детерминизм!
        
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
        """Бенчмарк поиска."""
        import random
        random.seed(42)
        
        data = list(range(n_items))
        if target is None:
            target = n_items - 1  # Ищем последний (худший случай)
        
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
        """Восстановление мёртвых кубитов с логами."""
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Полная статистика кластера."""
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
        """Статистика первых N кубитов."""
        return [q.get_stats() for q in self.qubits[:limit]]


# ═══════════════════════════════════════════════════════════════
# 🧪 ТЕСТЫ
# ═══════════════════════════════════════════════════════════════

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
    
    # ═══════════════════════════════════════════════════════════
    # 1. SHA-256 БЕНЧМАРК
    # ═══════════════════════════════════════════════════════════
    print("📊 SHA-256 бенчмарк...")
    bench = cluster.benchmark_sha256(1000)
    print(f"  Задач: {bench['tasks']}")
    print(f"  Время: {bench['elapsed']:.3f} сек")
    print(f"  Скорость: {bench['tasks_per_sec']:.0f} задач/сек")
    print()
    
    # ═══════════════════════════════════════════════════════════
    # 2. TSP ТЕСТ
    # ═══════════════════════════════════════════════════════════
    print("🗺️ TSP тест (50 городов)...")
    tsp_bench = cluster.benchmark_tsp(50)
    print(f"  Городов: {tsp_bench['cities']}")
    print(f"  Дистанция: {tsp_bench['distance']:.2f}")
    print(f"  Время: {tsp_bench['elapsed']:.3f} сек")
    print(f"  Кубит: {tsp_bench['qubit']}")
    print()
    
    # TSP с разбиением
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
    
    # ═══════════════════════════════════════════════════════════
    # 3. ГРОВЕР ТЕСТ
    # ═══════════════════════════════════════════════════════════
    print("🔍 Гровер поиск (100,000 элементов)...")
    grover_bench = cluster.benchmark_grover(100000)
    print(f"  Элементов: {grover_bench['items']}")
    print(f"  Найден: {grover_bench['found']}")
    print(f"  Время: {grover_bench['elapsed']:.4f} сек")
    print(f"  Партиций: {grover_bench['partitions']}")
    print()
    
    # ═══════════════════════════════════════════════════════════
    # 4. ИТОГОВАЯ СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════
    print("🔍 Первые 5 кубитов:")
    for q in cluster.get_qubit_stats(5):
        specialties = q.get('specialties', {})
        spec_str = ", ".join(f"{k}:{v}" for k, v in specialties.items()) or "нет"
        print(f"  {q['id']}: core={q['core']}, tasks={q['tasks_completed']}, спец: {spec_str}")
    
    print()
    print("✅ Тесты завершены!")