# test_scaling2.py
# ⚛️ Тест масштабирования TEES-кластера с multiprocessing + батчинг
# Обход GIL — реальный параллелизм на ядрах!

import time
import os
import json
import math
import signal
import sys
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Dict, List, Any, Tuple, Optional


# ═══════════════════════════════════════════════════════════════
# 🌐 ГЛОБАЛЬНЫЕ ФУНКЦИИ ДЛЯ MULTIPROCESSING
# ═══════════════════════════════════════════════════════════════

# Глобальный список активных кластеров для graceful shutdown
active_clusters = []


def global_compute_sha256(data: str) -> str:
    """Глобальная функция для multiprocessing (можно сериализовать)."""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()


def global_batch_sha256(data_list: List[str]) -> List[str]:
    """
    Глобальная функция для батч-обработки SHA-256.
    Один вызов — пачка задач!
    """
    import hashlib
    return [hashlib.sha256(d.encode()).hexdigest() for d in data_list]


def global_batch_md5(data_list: List[str]) -> List[str]:
    """Батч-обработка MD5."""
    import hashlib
    return [hashlib.md5(d.encode()).hexdigest() for d in data_list]


def signal_handler(sig, frame):
    """Обработчик сигналов для graceful shutdown."""
    print('\n⚠️ Прерывание... Закрываю все пулы...')
    for cluster in active_clusters:
        try:
            cluster.close()
        except:
            pass
    print('✅ Все пулы закрыты. Выход.')
    sys.exit(0)


# ═══════════════════════════════════════════════════════════════
# 📊 УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════

def get_memory_mb():
    """Текущее использование RAM."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except:
        return 0


def get_cpu_usage():
    """Получить загрузку CPU по ядрам."""
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1, percpu=True)
    except:
        return []


def measure_coherence(cluster):
    """Замер когерентности кубов."""
    cohs = [q.coherence for q in cluster.qubits]
    if not cohs:
        return {'min': 0, 'max': 0, 'avg': 0, 'delta': 0}
    
    min_c = min(cohs)
    max_c = max(cohs)
    avg_c = sum(cohs) / len(cohs)
    delta = max_c - min_c
    
    return {'min': min_c, 'max': max_c, 'avg': avg_c, 'delta': delta}


def wait_minutes(minutes: float, time_scale: float = 1.0):
    """Ожидание с масштабированием."""
    seconds = minutes * 60 * time_scale
    if seconds > 0:
        print(f"  🔥 Прогрев {minutes:.1f} мин...")
        time.sleep(seconds)


def print_fire(fire_level: str, total_qubits: int, coh: Dict[str, float], ram_mb: float):
    """Красивое отображение факела."""
    
    icons = {
        'spark': '✨',
        'flame': '🔥',
        'fire': '⚡',
        'plasma': '💫',
        'torch': '⚛️'
    }
    
    names = {
        'spark': 'Искра синхронизации',
        'flame': 'Пламя когерентности',
        'fire': 'Квантовый огонь',
        'plasma': 'Плазма нирваны',
        'torch': 'КВАНТОВЫЙ ФАКЕЛ'
    }
    
    icon = icons.get(fire_level, '🏮')
    name = names.get(fire_level, 'Свечение')
    
    bar_width = 40
    filled = int(coh['avg'] * bar_width)
    bar = '█' * filled + '░' * (bar_width - filled)
    
    print(f"""
  {icon} {name}
  ├─ Кубитов: {total_qubits}
  ├─ Когерентность: {coh['avg']:.6f}
  ├─ [{bar}]
  ├─ min={coh['min']:.4f} max={coh['max']:.4f} Δ={coh['delta']:.4f}
  └─ RAM: {ram_mb:.1f} MB
    """)


def determine_fire_level(coh_avg: float, total_qubits: int, delta: float) -> str:
    """Определяем уровень факела."""
    if total_qubits < 100:
        return 'spark'
    if coh_avg < 0.99 or delta > 0.1:
        return 'spark'
    if total_qubits < 1000:
        return 'flame'
    if total_qubits < 10000:
        return 'fire'
    if total_qubits < 100000:
        return 'plasma'
    return 'torch'


def plot_coherence_history(history: List[Tuple[float, Dict[str, float]]]):
    """Текстовый график изменения когерентности."""
    print("\n  📈 График когерентности:")
    
    for point, coh in history:
        bar_width = 40
        filled = int(coh['avg'] * bar_width)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        print(f"    t={point:4.1f}мин: [{bar}] {coh['avg']:.6f}")


def print_comparison_table(results: List[Dict[str, Any]]):
    """Улучшенная таблица сравнения с эффективностью."""
    if not results:
        return
    
    print(f"\n{'='*80}")
    print("📊 ЭФФЕКТИВНОСТЬ МАСШТАБИРОВАНИЯ")
    print(f"{'='*80}")
    
    # Таблица производительности
    print(f"\n{'Ядер':<6} {'Кубитов':<10} {'Послед/сек':<12} {'Thread/сек':<12} {'MP/сек':<12} {'MP батч/сек':<14}")
    print("-" * 75)
    
    for r in results:
        print(f"{r['cores']:<6} "
              f"{r['total_qubits']:<10} "
              f"{r['seq_per_sec']:<12.0f} "
              f"{r['thread_per_sec']:<12.0f} "
              f"{r['mp_per_sec']:<12.0f} "
              f"{r['mp_batched_per_sec']:<14.0f}")
    
    # Анализ эффективности
    print(f"\n  📈 Анализ эффективности:")
    
    for r in results:
        theoretical_speedup = r['cores']
        actual_speedup = r['mp_batched_speedup']
        efficiency = (actual_speedup / theoretical_speedup) * 100 if theoretical_speedup > 0 else 0
        
        print(f"\n  {r['cores']} ядер:")
        print(f"    Теоретическое ускорение: x{theoretical_speedup}")
        print(f"    Фактическое (батчинг): x{actual_speedup:.2f}")
        print(f"    Эффективность: {efficiency:.1f}%")
        
        if efficiency < 50:
            print(f"    ⚠️ Низкая эффективность - overhead процессов")
        elif efficiency < 75:
            print(f"    📊 Средняя эффективность")
        else:
            print(f"    🏆 Отличная эффективность!")
    
    # Находим оптимум
    if results:
        best = max(results, key=lambda x: x['mp_batched_per_sec'])
        print(f"\n  🏆 Оптимум: {best['cores']} ядра — {best['mp_batched_per_sec']:.0f}/сек (батчинг)")
        print(f"     Ускорение: x{best['mp_batched_speedup']:.2f} от последовательного")


def save_results(results: List[Dict[str, Any]], filename: str = "scaling_results_mp.json"):
    """Сохранить результаты в JSON."""
    try:
        data = {
            'timestamp': time.time(),
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n  📁 Результаты сохранены в {filename}")
    except Exception as e:
        print(f"\n  ⚠️ Ошибка сохранения: {e}")


# ═══════════════════════════════════════════════════════════════
# 🚀 MULTIPROCESSING ВЕРСИЯ КЛАСТЕРА С БАТЧИНГОМ
# ═══════════════════════════════════════════════════════════════

class MultiprocessingTeesCluster:
    """
    ⚛️ TEES-кластер с multiprocessing и батчингом.
    Обходит GIL — реальный параллелизм!
    Батчинг — минимум IPC overhead.
    """
    
    def __init__(self, cores: Optional[int] = None, qubits_per_core: int = 100):
        available_cores = mp.cpu_count() or 1
        
        if cores is None:
            self.cores = available_cores
        else:
            self.cores = min(cores, available_cores)
            if cores > available_cores:
                print(f"⚠️ Запрошено {cores} ядер, доступно {available_cores}")
                print(f"   Использую {self.cores} ядер")
        
        self.qubits_per_core = qubits_per_core
        self.total_qubits = self.cores * qubits_per_core
        
        # Пул процессов
        try:
            self.pool = mp.Pool(processes=self.cores)
            print(f"✅ Пул создан: {self.cores} процессов")
        except Exception as e:
            print(f"❌ Ошибка создания пула: {e}")
            self.pool = None
        
        # Статистика
        self.tasks_total = 0
        self.tasks_successful = 0
        self.created_at = time.time()
        self.coherence = 1.0
        
        # Потокобезопасный lock
        self._lock = threading.Lock()
        
        active_clusters.append(self)
    
    # ═══════════════════════════════════════════════════════════
    # БЕНЧМАРКИ
    # ═══════════════════════════════════════════════════════════
    
    def benchmark_sha256_sequential(self, count: int = 1000) -> Dict[str, Any]:
        """Бенчмарк SHA-256 последовательно."""
        import hashlib
        
        start_time = time.time()
        
        for i in range(count):
            data = f"TEES benchmark {i}".encode()
            hashlib.sha256(data).hexdigest()
        
        elapsed = time.time() - start_time
        tasks_per_sec = count / elapsed if elapsed > 0 else 0
        
        return {
            'tasks': count,
            'elapsed': elapsed,
            'tasks_per_sec': tasks_per_sec,
            'total_cores': self.cores,
            'method': 'sequential'
        }
    
    def benchmark_sha256_threading(self, count: int = 1000) -> Dict[str, Any]:
        """Бенчмарк SHA-256 через threading."""
        import hashlib
        
        data_list = [f"TEES benchmark {i}" for i in range(count)]
        results = [None] * count
        
        def worker(start_idx, end_idx):
            for i in range(start_idx, end_idx):
                results[i] = hashlib.sha256(data_list[i].encode()).hexdigest()
        
        threads = []
        chunk_size = count // self.cores
        
        for i in range(self.cores):
            start = i * chunk_size
            end = start + chunk_size if i < self.cores - 1 else count
            t = threading.Thread(target=worker, args=(start, end))
            threads.append(t)
        
        start_time = time.time()
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        elapsed = time.time() - start_time
        tasks_per_sec = count / elapsed if elapsed > 0 else 0
        
        return {
            'tasks': count,
            'elapsed': elapsed,
            'tasks_per_sec': tasks_per_sec,
            'total_cores': self.cores,
            'method': 'threading'
        }
    
    def benchmark_sha256_parallel_old(self, count: int = 1000) -> Dict[str, Any]:
        """
        Старый способ: каждая задача — отдельный IPC-вызов.
        Медленно из-за overhead!
        """
        if not self.pool:
            return {'error': 'Pool not initialized', 'tasks_per_sec': 0}
        
        data_list = [f"TEES benchmark {i}" for i in range(count)]
        chunk_size = max(1, count // (self.cores * 4))
        
        start_time = time.time()
        
        try:
            results = self.pool.map(global_compute_sha256, data_list, chunksize=chunk_size)
        except Exception as e:
            print(f"❌ Ошибка бенчмарка: {e}")
            return {'error': str(e), 'tasks_per_sec': 0}
        
        elapsed = time.time() - start_time
        tasks_per_sec = count / elapsed if elapsed > 0 else 0
        
        return {
            'tasks': count,
            'elapsed': elapsed,
            'tasks_per_sec': tasks_per_sec,
            'total_cores': self.cores,
            'chunk_size': chunk_size,
            'method': 'multiprocessing_old'
        }
    
    def benchmark_sha256_parallel_batched(self, count: int = 1000) -> Dict[str, Any]:
        """
        ✅ НОВЫЙ СПОСОБ: батчинг!
        Крупные чанки — минимум IPC overhead.
        """
        if not self.pool:
            return {'error': 'Pool not initialized', 'tasks_per_sec': 0}
        
        data_list = [f"TEES benchmark {i}" for i in range(count)]
        
        # Разбиваем на БОЛЬШИЕ батчи — по одному на процесс
        batch_size = max(1, count // self.cores)
        batches = []
        
        for i in range(0, count, batch_size):
            batches.append(data_list[i:i+batch_size])
        
        start_time = time.time()
        
        try:
            # Один IPC-вызов на батч!
            results_nested = self.pool.map(global_batch_sha256, batches)
        except Exception as e:
            print(f"❌ Ошибка батч-бенчмарка: {e}")
            return {'error': str(e), 'tasks_per_sec': 0}
        
        elapsed = time.time() - start_time
        
        # Разворачиваем результаты
        results = []
        for batch_result in results_nested:
            results.extend(batch_result)
        
        tasks_per_sec = len(results) / elapsed if elapsed > 0 else 0
        
        return {
            'tasks': len(results),
            'elapsed': elapsed,
            'tasks_per_sec': tasks_per_sec,
            'total_cores': self.cores,
            'batches': len(batches),
            'batch_size': batch_size,
            'method': 'multiprocessing_batched'
        }
    
    def benchmark_sha256_parallel_smart(self, count: int = 1000) -> Dict[str, Any]:
        """
        Умный бенчмарк: сам выбирает оптимальный размер батча.
        """
        if not self.pool:
            return {'error': 'Pool not initialized', 'tasks_per_sec': 0}
        
        data_list = [f"TEES benchmark {i}" for i in range(count)]
        
        # Оптимальный размер батча: не слишком маленький (overhead),
        # не слишком большой (неравномерная нагрузка)
        optimal_batch = max(10, count // (self.cores * 2))
        
        batches = []
        for i in range(0, count, optimal_batch):
            batches.append(data_list[i:i+optimal_batch])
        
        start_time = time.time()
        
        try:
            results_nested = self.pool.map(global_batch_sha256, batches)
        except Exception as e:
            return {'error': str(e), 'tasks_per_sec': 0}
        
        elapsed = time.time() - start_time
        
        results = []
        for batch_result in results_nested:
            results.extend(batch_result)
        
        tasks_per_sec = len(results) / elapsed if elapsed > 0 else 0
        
        return {
            'tasks': len(results),
            'elapsed': elapsed,
            'tasks_per_sec': tasks_per_sec,
            'total_cores': self.cores,
            'batches': len(batches),
            'batch_size': optimal_batch,
            'method': 'multiprocessing_smart'
        }
    
    def test_scaling_tasks(self):
        """Тест масштабирования по количеству задач."""
        print("\n📊 Тест масштабирования по задачам:")
        
        task_counts = [100, 1000, 10000, 50000]
        
        for count in task_counts:
            result = self.benchmark_sha256_parallel_batched(count)
            if 'tasks_per_sec' in result and result['tasks_per_sec'] > 0:
                print(f"  {count:6d} задач: {result['tasks_per_sec']:>10.0f}/сек "
                      f"({result['elapsed']:.3f} сек, батчей: {result.get('batches', 0)})")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кластера."""
        cpu_usage = get_cpu_usage()
        
        return {
            'cores': self.cores,
            'qubits_per_core': self.qubits_per_core,
            'total_qubits': self.total_qubits,
            'tasks_total': self.tasks_total,
            'tasks_successful': self.tasks_successful,
            'coherence': self.coherence,
            'uptime': time.time() - self.created_at,
            'cpu_usage': cpu_usage,
            'pool_active': self.pool is not None
        }
    
    def close(self):
        """Закрыть пул процессов."""
        if self.pool:
            try:
                self.pool.close()
                self.pool.join()
                print(f"✅ Пул закрыт ({self.cores} процессов)")
            except Exception as e:
                print(f"⚠️ Ошибка при закрытии пула: {e}")
            finally:
                self.pool = None
        
        if self in active_clusters:
            active_clusters.remove(self)
    
    def __enter__(self):
        """Контекстный менеджер."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие при выходе из контекста."""
        self.close()
    
    def __del__(self):
        """Деструктор - страховка от утечек."""
        try:
            self.close()
        except:
            pass


# ═══════════════════════════════════════════════════════════════
# 🧪 ТЕСТ
# ═══════════════════════════════════════════════════════════════

def run_multiprocessing_test():
    """
    Тест multiprocessing vs threading vs sequential с батчингом.
    """
    print("🚀 TEES-кластер: multiprocessing тест с батчингом")
    print("=" * 60)
    
    cores = mp.cpu_count()
    print(f"  Ядер: {cores}")
    print(f"  GIL обходится через multiprocessing")
    print(f"  Батчинг минимизирует IPC overhead")
    print(f"  ОС: {sys.platform}")
    if sys.platform == 'win32':
        print(f"  ⚠️ На Windows multiprocessing использует spawn")
    print("=" * 60)
    
    configs = [
        (2, 100),    # 2 ядра
        (4, 100),    # 4 ядра
        (8, 100),    # 8 ядер (если есть)
    ]
    
    results = []
    
    for n_cores, qubits_per_core in configs:
        if n_cores > cores:
            print(f"\n  ⚠️ Пропускаю {n_cores} ядер (доступно {cores})")
            continue
        
        total_qubits = n_cores * qubits_per_core
        
        print(f"\n{'='*60}")
        print(f"⚛️ Конфигурация: {n_cores} ядра × {qubits_per_core} = {total_qubits} кубитов")
        print(f"{'='*60}")
        
        with MultiprocessingTeesCluster(cores=n_cores, qubits_per_core=qubits_per_core) as cluster:
            
            # ═══════════════════════════════════════
            # SHA-256 БЕНЧМАРКИ
            # ═══════════════════════════════════════
            
            test_count = 10000  # Больше задач для честного теста
            
            print(f"\n  📊 SHA-256 бенчмарки ({test_count} задач):")
            
            # Последовательный
            seq = cluster.benchmark_sha256_sequential(test_count)
            print(f"  🐌 Последовательно: {seq['tasks_per_sec']:>10.0f}/сек ({seq['elapsed']:.3f} сек)")
            
            # Threading
            thread = cluster.benchmark_sha256_threading(test_count)
            print(f"  🧵 Threading: {thread['tasks_per_sec']:>10.0f}/сек ({thread['elapsed']:.3f} сек)")
            
            # Multiprocessing — старый способ
            mp_old = cluster.benchmark_sha256_parallel_old(test_count)
            print(f"  🚀 MP (старый): {mp_old['tasks_per_sec']:>10.0f}/сек ({mp_old['elapsed']:.3f} сек)")
            
            # Multiprocessing — батчинг
            mp_batched = cluster.benchmark_sha256_parallel_batched(test_count)
            print(f"  📦 MP (батчинг): {mp_batched['tasks_per_sec']:>10.0f}/сек ({mp_batched['elapsed']:.3f} сек)")
            
            # Multiprocessing — умный
            mp_smart = cluster.benchmark_sha256_parallel_smart(test_count)
            print(f"  🧠 MP (умный): {mp_smart['tasks_per_sec']:>10.0f}/сек ({mp_smart['elapsed']:.3f} сек)")
            
            # Сравнение
            if seq['tasks_per_sec'] > 0:
                thread_speedup = thread['tasks_per_sec'] / seq['tasks_per_sec']
                mp_old_speedup = mp_old['tasks_per_sec'] / seq['tasks_per_sec']
                mp_batched_speedup = mp_batched['tasks_per_sec'] / seq['tasks_per_sec']
                mp_smart_speedup = mp_smart['tasks_per_sec'] / seq['tasks_per_sec']
                
                print(f"\n  📈 Ускорение (vs последовательный):")
                print(f"  Threading:    x{thread_speedup:.2f}")
                print(f"  MP (старый):  x{mp_old_speedup:.2f}")
                print(f"  MP (батчинг): x{mp_batched_speedup:.2f}")
                print(f"  MP (умный):   x{mp_smart_speedup:.2f}")
                
                # Лучший результат
                best_method = max([
                    ('threading', thread_speedup),
                    ('mp_old', mp_old_speedup),
                    ('mp_batched', mp_batched_speedup),
                    ('mp_smart', mp_smart_speedup)
                ], key=lambda x: x[1])
                
                print(f"\n  🏆 Лучший: {best_method[0]} — x{best_method[1]:.2f}")
            
            # Тест масштабирования по задачам
            cluster.test_scaling_tasks()
            
            # RAM и CPU
            ram_mb = get_memory_mb()
            cpu_usage = get_cpu_usage()
            print(f"\n  💾 RAM: {ram_mb:.1f} MB")
            if cpu_usage:
                print(f"  🔧 CPU: {cpu_usage}")
            
            results.append({
                'cores': n_cores,
                'total_qubits': total_qubits,
                'seq_per_sec': seq['tasks_per_sec'],
                'thread_per_sec': thread['tasks_per_sec'],
                'mp_per_sec': mp_old['tasks_per_sec'],
                'mp_batched_per_sec': mp_batched['tasks_per_sec'],
                'mp_smart_per_sec': mp_smart['tasks_per_sec'],
                'ram_mb': ram_mb,
                'thread_speedup': thread_speedup,
                'mp_speedup': mp_old_speedup,
                'mp_batched_speedup': mp_batched_speedup,
                'mp_smart_speedup': mp_smart_speedup
            })
    
    # ═══════════════════════════════════════════════
    # ИТОГОВОЕ СРАВНЕНИЕ
    # ═══════════════════════════════════════════════
    
    print_comparison_table(results)
    save_results(results, "scaling_results_mp.json")
    
    print(f"\n{'='*60}")
    print("✅ Multiprocessing тест с батчингом завершён!")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # На Windows нужен if __name__ == '__main__' для multiprocessing!
    mp.freeze_support()
    
    try:
        run_multiprocessing_test()
    except KeyboardInterrupt:
        print("\n⚠️ Прерывание пользователем")
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        signal_handler(None, None)