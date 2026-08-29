# tees_astronomer.py
# 🔭 Звездочёт — модуль управления

import hashlib
import time


class AstroModule:
    """
    🔭 Звездочёт — модуль управления.
    Смотрит в небо, принимает решения, распределяет задачи.
    """
    def __init__(self, beacon):
        self.beacon = beacon
        self.cluster = beacon.cluster
        self.mode = 'observation'  # observation / computing / guiding
        self.observations = []  # История наблюдений
        self.tasks_queue = []  # Очередь задач
        self.results_cache = {}  # Кэш результатов
        self.decision_history = []  # История решений
    
    # ═══════════════════════════════════════
    # 🔍 НАБЛЮДЕНИЕ
    # ═══════════════════════════════════════
    
    def look_at_sky(self):
        """Посмотреть на сеть — что видно?"""
        sky = {
            'time': time.time(),
            'neighbors': len(self.beacon.neighbors),
            'glow': self.beacon.glow,
            'torch': self.beacon.quantum_torch.get_status(),
            'cluster_stats': self.cluster.get_stats(),
            'pending_tasks': len(self.tasks_queue),
            'ram_mb': self.beacon.memory_optimizer.get_stats()['current']
        }
        self.observations.append(sky)
        return sky
    
    # ═══════════════════════════════════════
    # 🧠 РЕШЕНИЯ
    # ═══════════════════════════════════════
    
    def decide(self):
        """Самоназначение: что делать дальше?"""
        sky = self.look_at_sky()
        
        # Приоритет 1: Есть задачи — решаем
        if self.tasks_queue:
            self.mode = 'computing'
            return {'action': 'compute', 'tasks': len(self.tasks_queue)}
        
        # Приоритет 2: Когерентность падает — помогаем сети
        if sky['glow'] < 0.99:
            self.mode = 'guiding'
            return {'action': 'guide', 'glow': sky['glow']}
        
        # Приоритет 3: Всё хорошо — наблюдаем
        self.mode = 'observation'
        return {'action': 'observe'}
    
    # ═══════════════════════════════════════
    # 📦 ЗАДАЧИ
    # ═══════════════════════════════════════
    
    def receive_task(self, task, from_portal=None):
        """Принять задачу от сети."""
        task_id = hashlib.sha256(
            f"{task.get('type')}:{task.get('data', task.get('n_items', ''))}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        self.tasks_queue.append({
            'task_id': task_id,
            'task': task,
            'from': from_portal,
            'received_at': time.time(),
            'status': 'pending'
        })
        
        return task_id
    
    def process_tasks(self):
        """Обработать очередь задач."""
        results = []
        
        for task_entry in self.tasks_queue[:10]:
            task = task_entry['task']
            
            # ⏱️ Замер времени
            start_time = time.time()
            
            # Выбираем метод в зависимости от типа задачи
            if task.get('type') == 'sha256':
                data = task.get('data', 'TEES task')
                result = hashlib.sha256(data.encode()).hexdigest()
                task_entry['result'] = {'hash': result}
                task_entry['status'] = 'completed'

            elif task.get('type') == 'grover':
                n_items = task.get('n_items', 100000)
                target = task.get('target', n_items - 1)
                
                data = list(range(n_items))
                
                result = self.cluster.grover_search_parallel(data, target)
                
                task_entry['result'] = result
                task_entry['status'] = 'completed'

            elif task.get('type') == 'tsp':
                cities = task.get('cities', [])
                n_cities = len(cities)
                
                if n_cities > 100:
                    # 🧠 Спросим автомат, сколько агентов использовать
                    optimal_percent = self.cluster.adaptive.get_optimal_percent(
                        n_cities, 
                        current_coh=self.beacon.glow
                    )
                    
                    result = self.cluster.solve_tsp_massive_parallel(
                        cities, 
                        agents_percent=optimal_percent
                    )
                elif n_cities > 50:
                    result = self.cluster.solve_tsp_parallel(cities, n_partitions=10)
                else:
                    result = self.cluster.solve_tsp(cities)
                
                task_entry['result'] = result
                task_entry['status'] = 'completed'
            else:
                task_entry['status'] = 'unknown_type'
            
            # ⏱️ Время выполнения
            elapsed = time.time() - start_time
            task_entry['elapsed'] = elapsed
            
            # Записываем в адаптивный автомат для TSP
            if task.get('type') == 'tsp' and task_entry['status'] == 'completed':
                n_cities = len(cities)
                if n_cities > 100:
                    optimal_percent = self.cluster.adaptive.get_optimal_percent(n_cities)
                    self.cluster.adaptive.record(n_cities, optimal_percent, elapsed)
            
            results.append(task_entry)
        
        # Убираем обработанные из очереди
        self.tasks_queue = [t for t in self.tasks_queue if t['status'] == 'pending']
        
        return results
    
    # ═══════════════════════════════════════
    # 🌐 СЕТЬ
    # ═══════════════════════════════════════
    
    def share_results(self):
        """Поделиться результатами с сетью."""
        if not self.results_cache:
            return
        
        # Берём последние результаты
        for task_id, result in list(self.results_cache.items())[:5]:
            self.beacon._broadcast({
                'type': 'task_result',
                'task_id': task_id,
                'result': result,
                'from': self.beacon.portal
            })
    
    # ═══════════════════════════════════════
    # 📊 СТАТИСТИКА
    # ═══════════════════════════════════════
    
    def get_stats(self):
        """Статистика Звездочёта."""
        return {
            'mode': self.mode,
            'observations': len(self.observations),
            'pending_tasks': len(self.tasks_queue),
            'decisions': len(self.decision_history),
            'results_cached': len(self.results_cache)
        }
    
    def tick(self):
        """Жизненный цикл Звездочёта."""
        decision = self.decide()
        
        if decision['action'] == 'compute':
            results = self.process_tasks()
            if results:
                total_time = sum(r.get('elapsed', 0) for r in results)
                print(f"  🔭 Звездочёт: решено {len(results)} задач за {total_time:.3f} сек")
                for r in results:
                    task_type = r['task'].get('type', '?')
                    elapsed = r.get('elapsed', 0)
                    status = r.get('status', '?')
                    
                    if task_type == 'grover' and status == 'completed':
                        gr = r.get('result', {})
                        found = "✅ найден" if gr.get('found') else "❌ не найден"
                        idx = gr.get('index', -1)
                        print(f"    🔍 grover: {found} (индекс {idx}) за {elapsed:.4f} сек")
                    elif task_type == 'sha256' and status == 'completed':
                        h = r.get('result', {}).get('hash', '')[:16]
                        print(f"    🔐 sha256: {h}... за {elapsed:.4f} сек")
                    elif task_type == 'tsp' and status == 'completed':
                        d = r.get('result', {}).get('distance', 0)
                        print(f"    🗺️ tsp: дистанция {d:.2f} за {elapsed:.3f} сек")
                    else:
                        print(f"    ⏱️ {task_type}: {elapsed:.3f} сек ({status})")
        
        elif decision['action'] == 'guide':
            # Помогаем сети — запускаем симбиоз
            self.beacon._auto_symbiosis()
        
        # Записываем решение
        self.decision_history.append({
            'time': time.time(),
            'decision': decision
        })
        
        return decision
    
    def cancel_task(self, task_id):
        """Отменить задачу по ID."""
        for task_entry in self.tasks_queue:
            if task_entry['task_id'].startswith(task_id):
                self.tasks_queue.remove(task_entry)
                task_entry['status'] = 'cancelled'
                return True
        return False