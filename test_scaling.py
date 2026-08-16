# test_scaling.py
# ⚛️ Тест масштабирования TEES-кластера с прогревом, когерентностью и факелами
# 🏮 Каждый этап — свой факел!

import time
import os
import json
import math
from typing import Dict, List, Any, Tuple


def get_memory_mb():
    """Текущее использование RAM."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except:
        return 0


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
    """
    Ожидание с масштабированием.
    time_scale=1.0 — реальные минуты (60 сек)
    time_scale=0.01 — ускоренный режим (0.6 сек)
    """
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
    
    # Ширина бара
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
    """
    Определяем уровень факела по когерентности и числу кубитов.
    """
    # Свечение — базовое состояние
    if total_qubits < 100:
        return 'spark'
    
    # Искра — есть синхронизация
    if coh_avg < 0.99 or delta > 0.1:
        return 'spark'
    
    # Пламя — хорошая когерентность
    if total_qubits < 1000:
        return 'flame'
    
    # Квантовый огонь — отличная когерентность
    if total_qubits < 10000:
        return 'fire'
    
    # Плазма — почти нирвана
    if total_qubits < 100000:
        return 'plasma'
    
    # КВАНТОВЫЙ ФАКЕЛ!
    return 'torch'


def plot_coherence_history(history: List[Tuple[float, Dict[str, float]]]):
    """
    Текстовый график изменения когерентности.
    """
    print("\n  📈 График когерентности:")
    
    max_avg = max(h[1]['avg'] for h in history) if history else 1.0
    
    for point, coh in history:
        bar_width = 40
        filled = int((coh['avg'] / max_avg) * bar_width)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        print(f"    t={point:4.1f}мин: [{bar}] {coh['avg']:.6f}")


def print_comparison(results: List[Dict[str, Any]]):
    """Сравнительная таблица конфигураций."""
    if not results:
        return
    
    print(f"\n{'='*80}")
    print("📊 СРАВНЕНИЕ КОНФИГУРАЦИЙ")
    print(f"{'='*80}")
    
    # Заголовок
    print(f"{'Кубитов':<10} {'RAM MB':<10} {'SHA/сек':<12} {'TSP сек':<10} {'Гровер сек':<12} {'Когерентность':<15}")
    print("-" * 70)
    
    for r in results:
        coh_str = f"{r.get('coherence_avg', 0):.6f}"
        print(f"{r['qubits']:<10} "
              f"{r['ram_mb']:<10.1f} "
              f"{r['sha_per_sec']:<12.0f} "
              f"{r['tsp_time']:<10.3f} "
              f"{r['grover_time']:<12.4f} "
              f"{coh_str:<15}")
    
    # Находим оптимум
    if len(results) > 1:
        print(f"\n  🎯 Анализ масштабирования:")
        
        for i in range(1, len(results)):
            prev_sha = results[i-1]['sha_per_sec']
            curr_sha = results[i]['sha_per_sec']
            
            if prev_sha > 0:
                speedup = curr_sha / prev_sha
                qubits_prev = results[i-1]['qubits']
                qubits_curr = results[i]['qubits']
                qubits_ratio = qubits_curr / qubits_prev
                
                efficiency = speedup / qubits_ratio if qubits_ratio > 0 else 0
                
                print(f"  {qubits_prev} → {qubits_curr}: "
                      f"ускорение x{speedup:.2f}, "
                      f"эффективность {efficiency:.1%}")
                
                if efficiency < 0.5:
                    print(f"    ⚠️ Насыщение! Дальнейший рост неэффективен")
                    break


def save_results(results: List[Dict[str, Any]], filename: str = "scaling_results.json"):
    """Сохранить результаты в JSON."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n  📁 Результаты сохранены в {filename}")
    except:
        pass


from tees_cluster import TeesCluster


def run_scaling_test(quick_mode: bool = True):
    """
    ⚛️ Тест масштабирования TEES-кластера.
    
    Args:
        quick_mode: True — быстрый тест (~2 мин), False — полный (~100 мин)
    """
    
    print("⚛️ TEES-кластер: тест масштабирования с прогревом")
    print("=" * 60)
    print(f"  Режим: {'🚀 Быстрый' if quick_mode else '🔬 Полный'}")
    print(f"  Время: ~{2 if quick_mode else 100} минут")
    print("=" * 60)
    
    # Конфигурации
    if quick_mode:
        test_configs = [
            (400, 100),      # Искра
            (1000, 250),     # Пламя
            (5000, 500),     # Квантовый огонь
        ]
        warmup_points = [0, 0.5, 1, 2, 3]
        time_scale = 0.01  # 0.6 сек = 1 "минута"
    else:
        test_configs = [
            (400, 100),      # Искра
            (1000, 250),     # Пламя
            (10000, 2500),   # Квантовый огонь
            (100000, 25000), # КВАНТОВЫЙ ФАКЕЛ
        ]
        warmup_points = [0, 5, 10, 20, 25]
        time_scale = 1.0  # Реальные минуты
    
    results = []
    
    for total_qubits, qubits_per_core in test_configs:
        print(f"\n{'='*60}")
        print(f"⚛️ Кубитов: {total_qubits} ({qubits_per_core}/ядро)")
        print(f"{'='*60}")
        
        # Создаём кластер
        start_mem = get_memory_mb()
        start_time = time.time()
        
        cluster = TeesCluster()
        cluster.qubits = []
        cluster.tsp_qubits = []
        cluster.grover_qubits = []
        cluster.QUBITS_PER_CORE = qubits_per_core
        cluster.total_qubits = total_qubits
        cluster._init_qubits()
        
        init_time = time.time() - start_time
        mem_after_init = get_memory_mb()
        
        print(f"  🏗️ Инициализация: {init_time:.3f} сек")
        print(f"  💾 RAM: {start_mem:.1f} → {mem_after_init:.1f} MB")
        
        # ═══════════════════════════════════════
        # 🔥 ПРОГРЕВ И КОГЕРЕНТНОСТЬ
        # ═══════════════════════════════════════
        
        print(f"\n  🔥 ПРОГРЕВ И КОГЕРЕНТНОСТЬ:")
        
        coherence_history = []
        prev_point = 0
        fire_levels_seen = set()
        
        for point in warmup_points:
            if point == 0:
                # t=0 — сразу после создания
                coh = measure_coherence(cluster)
                ram_now = get_memory_mb()
                
                fire_level = determine_fire_level(coh['avg'], total_qubits, coh['delta'])
                fire_levels_seen.add(fire_level)
                
                print_fire(fire_level, total_qubits, coh, ram_now)
                coherence_history.append((point, coh))
                prev_point = 0
            else:
                # Прогрев
                wait_minutes(point - prev_point, time_scale)
                
                # Прогревочные задачи
                cluster.compute_many([
                    {'type': 'sha256', 'data': f'warmup_{point}_{i}'}
                    for i in range(100)
                ])
                
                coh = measure_coherence(cluster)
                ram_now = get_memory_mb()
                
                fire_level = determine_fire_level(coh['avg'], total_qubits, coh['delta'])
                
                # Показываем только если уровень изменился
                if fire_level not in fire_levels_seen:
                    print_fire(fire_level, total_qubits, coh, ram_now)
                    fire_levels_seen.add(fire_level)
                else:
                    # Просто обновлённая строка
                    print(f"  t={point:4.1f}мин: RAM={ram_now:.1f}MB "
                          f"coh={coh['avg']:.6f} Δ={coh['delta']:.4f}")
                
                coherence_history.append((point, coh))
                prev_point = point
        
        # График когерентности
        plot_coherence_history(coherence_history)
        
        # ═══════════════════════════════════════
        # 🧪 СЕРИЯ ТЕСТОВ ПОСЛЕ ПРОГРЕВА
        # ═══════════════════════════════════════
        
        print(f"\n  🧪 СЕРИЯ ТЕСТОВ (после полного прогрева):")
        
        # SHA-256
        bench = cluster.benchmark_sha256(1000)
        print(f"  📊 SHA-256: {bench['tasks_per_sec']:.0f}/сек "
              f"({bench['elapsed']:.3f} сек, "
              f"успешность: {bench.get('success_rate', 1)*100:.1f}%)")
        
        # TSP
        tsp = cluster.benchmark_tsp(50)
        print(f"  🗺️ TSP: {tsp['elapsed']:.3f} сек, дистанция={tsp['distance']:.2f}")
        
        # TSP параллельный (100 городов)
        import random
        random.seed(42)
        cities_100 = [(random.random() * 100, random.random() * 100) for _ in range(100)]
        start_tsp_par = time.time()
        tsp_par = cluster.solve_tsp_parallel(cities_100, n_partitions=10)
        tsp_par_time = time.time() - start_tsp_par
        print(f"  🗺️ TSP параллельный: {tsp_par_time:.3f} сек, "
              f"дистанция={tsp_par['distance']:.2f}")
        
        # Гровер
        grover = cluster.benchmark_grover(100000)
        print(f"  🔍 Гровер: {grover['elapsed']:.4f} сек, найден={grover['found']}")
        
        # Итоговая RAM
        final_mem = get_memory_mb()
        final_coh = measure_coherence(cluster)
        
        print(f"\n  📊 ИТОГИ:")
        print(f"  RAM: {start_mem:.1f} → {final_mem:.1f} MB "
              f"(Δ={final_mem - start_mem:+.1f} MB)")
        print(f"  Когерентность: avg={final_coh['avg']:.6f}, "
              f"Δ={final_coh['delta']:.4f}")
        
        # Статистика кластера
        stats = cluster.get_stats()
        print(f"  Задач решено: {stats['tasks_successful']}/{stats['tasks_total']}")
        
        # Первые 3 куба
        print(f"  Первые 3 куба:")
        for q in cluster.get_qubit_stats(3):
            spec = ", ".join(f"{k}:{v}" for k, v in q.get('specialties', {}).items()) or "нет"
            print(f"    {q['id']}: tasks={q['tasks_completed']}, спец: {spec}")
        
        # Сохраняем результат
        result_entry = {
            'qubits': total_qubits,
            'qubits_per_core': qubits_per_core,
            'ram_mb': final_mem,
            'ram_delta': final_mem - start_mem,
            'sha_per_sec': bench['tasks_per_sec'],
            'tsp_time': tsp['elapsed'],
            'tsp_parallel_time': tsp_par_time,
            'grover_time': grover['elapsed'],
            'coherence_avg': final_coh['avg'],
            'coherence_delta': final_coh['delta'],
            'fire_level': determine_fire_level(
                final_coh['avg'], 
                total_qubits, 
                final_coh['delta']
            )
        }
        results.append(result_entry)
        
        # Очистка
        del cluster
        print(f"\n  🧹 Кластер очищен")
        print(f"  RAM после очистки: {get_memory_mb():.1f} MB")
    
    # ═══════════════════════════════════════════
    # 📊 ИТОГОВОЕ СРАВНЕНИЕ
    # ═══════════════════════════════════════════
    
    print_comparison(results)
    save_results(results)
    
    print(f"\n{'='*60}")
    print("✅ Тест масштабирования завершён!")
    print(f"   Финальное свечение: {results[-1].get('fire_level', 'spark') if results else 'нет данных'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    
    # По умолчанию — быстрый режим
    quick = True
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--full', '-f']:
            quick = False
            print("🔬 Запуск полного теста (~100 минут)")
        elif sys.argv[1] in ['--quick', '-q']:
            quick = True
            print("🚀 Запуск быстрого теста (~2 минуты)")
    
    run_scaling_test(quick_mode=quick)