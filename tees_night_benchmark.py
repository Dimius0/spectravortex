"""
TEESRouter — Night Benchmark (4GB RAM Edition) v0.2
=====================================================
Fixed: Windows cp1251 encoding, ZeroDivisionError
"""

import numpy as np
import time
import json
import gc
import os
import signal
import sys
import io
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Фикс кодировки для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('tees_night_benchmark.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class NightConfig:
    max_ram_mb: int = 3500
    max_time_hours: float = 8.0
    checkpoint_interval_min: int = 15
    start_qubits: int = 10
    max_qubits: int = 1000
    qubit_multiplier: float = 1.3
    field_resolution_base: int = 64
    max_field_resolution: int = 512
    max_iterations: int = 30
    max_retries: int = 3
    gc_interval_tests: int = 5


class TEESLite:
    """Минималистичный TEES для слабого железа."""
    
    def __init__(self, field_resolution: int = 64, max_iterations: int = 30):
        self.N = field_resolution
        self.max_iterations = max_iterations
        
        self.coupling = np.array([
            0.259921, 0.442249, 0.709975, 0.912931,
            0.148693, 0.307107, 0.518294, 0.651839,
        ], dtype=np.float32)
    
    def estimate_memory(self) -> float:
        """Оценка памяти в MB"""
        field_mb = (self.N * self.N * 8) / (1024 * 1024)
        kfield_mb = (self.N * self.N * 4) / (1024 * 1024)
        total_mb = (field_mb + kfield_mb) * 3
        return max(total_mb, 0.1)  # минимум 0.1 MB
    
    def generate_topology(self, num_qubits: int, density: float = 0.4) -> Dict:
        rng = np.random.RandomState(42)
        
        side = int(np.ceil(np.sqrt(num_qubits)))
        positions = {}
        
        for i in range(num_qubits):
            row = i // side
            col = i % side
            x_offset = 0.5 if row % 2 else 0.0
            positions[i] = (float(col + x_offset), float(row * 0.866))
        
        edges = []
        for i in range(num_qubits):
            xi, yi = positions[i]
            for j in range(i + 1, num_qubits):
                xj, yj = positions[j]
                dist = np.sqrt((xi - xj)**2 + (yi - yj)**2)
                
                if dist < 1.5 or (dist < 3.0 and rng.random() < density * 0.3):
                    edges.append((i, j))
        
        return {
            'positions': positions,
            'edges': edges,
            'num_qubits': num_qubits,
        }
    
    def route_fast(self, topology: Dict) -> Dict:
        positions = topology['positions']
        edges = topology['edges']
        N = self.N
        
        all_x = [p[0] for p in positions.values()]
        all_y = [p[1] for p in positions.values()]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        scale = max(max_x - min_x, max_y - min_y) / (N - 10)
        scale = max(scale, 0.05)
        
        xs = np.arange(N, dtype=np.float32)[:, None]
        ys = np.arange(N, dtype=np.float32)[None, :]
        hash_idx = ((xs * 31 + ys * 17) % 8).astype(np.int32)
        K_field = self.coupling[hash_idx]
        
        start_time = time.time()
        total_path = 0
        successful = 0
        
        batch_size = min(100, len(edges))
        
        for batch_start in range(0, len(edges), batch_size):
            batch = edges[batch_start:batch_start + batch_size]
            
            for u, v in batch:
                try:
                    ux = int((positions[u][0] - min_x) / scale) + 5
                    uy = int((positions[u][1] - min_y) / scale) + 5
                    vx = int((positions[v][0] - min_x) / scale) + 5
                    vy = int((positions[v][1] - min_y) / scale) + 5
                    
                    ux = max(0, min(ux, N-1))
                    uy = max(0, min(uy, N-1))
                    vx = max(0, min(vx, N-1))
                    vy = max(0, min(vy, N-1))
                    
                    dist = np.sqrt((ux - vx)**2 + (uy - vy)**2)
                    
                    num_samples = min(20, int(dist))
                    if num_samples > 0:
                        sx = np.linspace(ux, vx, num_samples, dtype=np.int32)
                        sy = np.linspace(uy, vy, num_samples, dtype=np.int32)
                        avg_K = np.mean(K_field[sx, sy])
                    else:
                        avg_K = 0.5
                    
                    path_len = max(1, int(dist * (1.0 + (1.0 - avg_K) * 0.7)))
                    total_path += path_len
                    successful += 1
                    
                except Exception:
                    continue
            
            if batch_start % (batch_size * 5) == 0:
                gc.collect()
        
        routing_time = time.time() - start_time
        
        return {
            'total_edges': len(edges),
            'successful': successful,
            'success_rate': successful / len(edges) if edges else 0,
            'avg_path_length': total_path / successful if successful else 0,
            'routing_time': routing_time,
            'edges_per_sec': successful / routing_time if routing_time > 0 else 0,
            'memory_mb': self.estimate_memory(),
        }


class NightRunner:
    
    def __init__(self, config: NightConfig):
        self.config = config
        self.results: List[Dict] = []
        self.checkpoint_file = "tees_night_checkpoint.json"
        self.start_time = None
        self.last_checkpoint_time = None
        
        self._restore_checkpoint()
        
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def _handle_interrupt(self, signum, frame):
        logger.warning("\nInterrupted! Saving checkpoint...")
        self._save_checkpoint()
        self._print_partial_results()
        sys.exit(0)
    
    def _save_checkpoint(self):
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': (time.time() - self.start_time) if self.start_time else 0,
            'results': self.results,
            'config': {
                'max_ram_mb': self.config.max_ram_mb,
                'max_time_hours': self.config.max_time_hours,
            }
        }
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)
        
        self.last_checkpoint_time = time.time()
        logger.info(f"[CHECKPOINT] Saved: {len(self.results)} tests completed")
    
    def _restore_checkpoint(self):
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                
                self.results = checkpoint.get('results', [])
                logger.info(f"[RESTORE] Loaded {len(self.results)} previous results")
                
                if self.results:
                    last = self.results[-1]
                    logger.info(f"  Last test: {last['num_qubits']} qubits, "
                              f"success rate: {last['success_rate']:.1%}")
            except Exception as e:
                logger.warning(f"Could not restore checkpoint: {e}")
    
    def _get_next_qubit_size(self) -> int:
        if not self.results:
            return self.config.start_qubits
        
        successful = [r for r in self.results if r['success_rate'] > 0.9]
        if not successful:
            return self.config.start_qubits
        
        max_successful = max(r['num_qubits'] for r in successful)
        last = self.results[-1]
        
        # Фикс ZeroDivisionError
        memory_per_qubit = last.get('memory_mb', 1.0) / max(1, last['num_qubits'])
        memory_per_qubit = max(memory_per_qubit, 0.01)  # минимум
        
        max_by_memory = int(self.config.max_ram_mb / memory_per_qubit * 0.8)
        
        next_size = int(max_successful * self.config.qubit_multiplier)
        next_size = min(next_size, max_by_memory, self.config.max_qubits)
        
        return max(next_size, max_successful + 5)
    
    def _get_field_resolution(self, num_qubits: int) -> int:
        base = self.config.field_resolution_base
        scale = np.sqrt(max(num_qubits, 1) / 10)
        resolution = int(base * scale)
        resolution = 2 ** int(np.ceil(np.log2(max(resolution, 2))))
        resolution = min(resolution, self.config.max_field_resolution)
        return max(resolution, 32)
    
    def _should_continue(self) -> bool:
        if self.start_time is None:
            return True
        
        elapsed = time.time() - self.start_time
        max_seconds = self.config.max_time_hours * 3600
        
        if elapsed >= max_seconds:
            logger.info(f"Time limit reached: {elapsed/3600:.1f}h")
            return False
        
        if len(self.results) >= 2:
            last_two = self.results[-2:]
            if all(r['success_rate'] < 0.5 for r in last_two):
                logger.info("Success rate dropped below 50% -- stopping")
                return False
        
        return True
    
    def run_night(self):
        logger.info("=" * 50)
        logger.info("TEESRouter -- NIGHT BENCHMARK")
        logger.info("=" * 50)
        logger.info(f"Max RAM: {self.config.max_ram_mb:.0f} MB")
        logger.info(f"Max time: {self.config.max_time_hours:.1f}h")
        logger.info(f"Start: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"Est. end: {(datetime.now() + timedelta(hours=self.config.max_time_hours)).strftime('%H:%M:%S')}")
        
        self.start_time = time.time()
        self.last_checkpoint_time = self.start_time
        test_count = len(self.results)
        
        try:
            while self._should_continue():
                num_qubits = self._get_next_qubit_size()
                field_res = self._get_field_resolution(num_qubits)
                
                tees = TEESLite(field_resolution=field_res, max_iterations=self.config.max_iterations)
                est_memory = tees.estimate_memory()
                
                if est_memory > self.config.max_ram_mb * 0.8:
                    logger.warning(f"Skipping {num_qubits}q: est. {est_memory:.0f}MB > {self.config.max_ram_mb}MB limit")
                    break
                
                elapsed = time.time() - self.start_time
                remaining = self.config.max_time_hours * 3600 - elapsed
                
                logger.info(f"--- Test {test_count + 1}: {num_qubits}q, field {field_res}x{field_res}, "
                          f"est.mem {est_memory:.0f}MB [Elapsed: {elapsed/3600:.1f}h, Rem: {remaining/3600:.1f}h]")
                
                success = False
                for attempt in range(self.config.max_retries):
                    try:
                        topology = tees.generate_topology(num_qubits)
                        metrics = tees.route_fast(topology)
                        
                        result = {
                            'num_qubits': num_qubits,
                            'field_resolution': field_res,
                            'num_edges': metrics['total_edges'],
                            'success_rate': metrics['success_rate'],
                            'avg_path_length': metrics['avg_path_length'],
                            'routing_time': metrics['routing_time'],
                            'edges_per_sec': metrics['edges_per_sec'],
                            'memory_mb': est_memory,
                            'timestamp': datetime.now().isoformat(),
                        }
                        
                        self.results.append(result)
                        test_count += 1
                        success = True
                        
                        logger.info(f"  OK: {num_qubits}q | {metrics['success_rate']:.1%} success | "
                                  f"{metrics['routing_time']:.2f}s | {metrics['edges_per_sec']:.0f} edges/s")
                        break
                        
                    except MemoryError:
                        logger.warning(f"  OOM at {num_qubits}q (attempt {attempt + 1})")
                        gc.collect()
                        if attempt == self.config.max_retries - 1:
                            logger.info("Memory limit reached -- stopping")
                            return
                        field_res = field_res // 2
                        tees = TEESLite(field_resolution=field_res)
                        
                    except Exception as e:
                        logger.error(f"  Error: {e} (attempt {attempt + 1})")
                        gc.collect()
                
                if time.time() - self.last_checkpoint_time > self.config.checkpoint_interval_min * 60:
                    self._save_checkpoint()
                
                if test_count % self.config.gc_interval_tests == 0:
                    gc.collect()
                    logger.debug("GC done")
                
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            logger.info("Paused by user")
        
        finally:
            self._save_checkpoint()
            self._print_final_results()
    
    def _print_partial_results(self):
        if not self.results:
            return
        
        print(f"\n{'='*60}")
        print(f"PARTIAL RESULTS ({len(self.results)} tests)")
        print(f"{'='*60}")
        
        for r in self.results[-10:]:
            print(f"  {r['num_qubits']:>5}q | {r['success_rate']:>6.1%} | "
                  f"{r['routing_time']:>7.2f}s | {r['memory_mb']:>5.0f}MB")
    
    def _print_final_results(self):
        if not self.results:
            logger.info("No results")
            return
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print(f"\n{'='*70}")
        print(f"NIGHT BENCHMARK COMPLETE")
        print(f"{'='*70}")
        print(f"Total time: {elapsed/3600:.1f}h")
        print(f"Tests completed: {len(self.results)}")
        
        print(f"\n{'Qubits':<8} {'Field':<10} {'Success':<10} "
              f"{'Time':<10} {'Speed':<12} {'Memory':<8}")
        print(f"{'-'*70}")
        
        for r in self.results:
            print(f"{r['num_qubits']:<8} "
                  f"{str(r['field_resolution'])+'x'+str(r['field_resolution']):<10} "
                  f"{r['success_rate']:<10.1%} "
                  f"{r['routing_time']:<10.2f}s "
                  f"{r['edges_per_sec']:<12.0f} "
                  f"{r['memory_mb']:<8.0f}MB")
        
        successful = [r for r in self.results if r['success_rate'] > 0.9]
        if successful:
            max_qubits = max(r['num_qubits'] for r in successful)
            max_result = [r for r in successful if r['num_qubits'] == max_qubits][0]
            
            print(f"\nMAX ACHIEVED:")
            print(f"  {max_qubits} qubits with {max_result['success_rate']:.1%} success")
            print(f"  Time: {max_result['routing_time']:.1f}s")
            print(f"  Memory: {max_result['memory_mb']:.0f}MB")
        
        print(f"\n{'='*70}")
        print(f"Results: {self.checkpoint_file}")
        print(f"Log: tees_night_benchmark.log")
        print(f"{'='*70}\n")


def main():
    print("\n" + "=" * 50)
    print("TEESRouter -- NIGHT BENCHMARK")
    print("4GB RAM * 8 Hours * Max Results")
    print("=" * 50)
    
    try:
        import psutil
        available_ram = psutil.virtual_memory().available / (1024*1024)
        logger.info(f"Available RAM: {available_ram:.0f} MB")
        max_ram = min(available_ram * 0.85, 3500)
    except ImportError:
        max_ram = 1200  # conservative for 4GB
        logger.info(f"psutil not found, using default: {max_ram} MB")
    
    logger.info(f"Using max RAM: {max_ram:.0f} MB")
    
    config = NightConfig(
        max_ram_mb=max_ram,
        max_time_hours=8.0,
        checkpoint_interval_min=15,
        start_qubits=10,
        max_qubits=100000,
        qubit_multiplier=1.3,
        field_resolution_base=64,
        max_field_resolution=512,
        max_iterations=30,
        max_retries=3,
        gc_interval_tests=5,
    )
    
    runner = NightRunner(config)
    
    print(f"\nStarting night benchmark...")
    print(f"Will run until: {(datetime.now() + timedelta(hours=8)).strftime('%H:%M')}")
    print(f"Checkpoints: every {config.checkpoint_interval_min} min")
    print(f"Ctrl+C to stop early (results saved)")
    print(f"\n{'─'*50}\n")
    
    runner.run_night()
    
    print("\nDone! Check results in tees_night_checkpoint.json\n")


if __name__ == "__main__":
    main()