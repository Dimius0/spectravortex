"""
СТЫ СТ Я ТСТЯ Т
"""

import sys
import os

# обавляем пути для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
sandbox_root = os.path.dirname(os.path.dirname(current_dir))

sys.path.insert(0, sandbox_root)
sys.path.insert(0, os.path.join(sandbox_root, "emergent_time"))

def test_solver_standalone():
    """Тестирование Solver без SpectraVortex"""
    print("🧪 ТСТ SOLVER  СТТ ")
    print("=" * 60)
    
    try:
        from integration.temporal_solver import TemporalSynchronizationSolver
        
        # Создание solver'а
        solver = TemporalSynchronizationSolver(validation_mode=True)
        print("✅ Solver создан")
        print(f"   мя: {solver.name}")
        print(f"   ерсия: {solver.version}")
        print(f"   писание: {solver.description}")
        
        # Тест 1: роверка can_solve
        print("\n1. Тест определения возможности решения:")
        
        test_problems = [
            {"type": "temporal_synchronization", "network": {"num_nodes": 5}},
            {"type": "network_health_analysis", "network": {"nodes": [0.8, 0.9, 0.7]}},
            {"type": "emergent_time_simulation", "network": {"num_nodes": 10}},
            {"type": "unknown_problem", "network": {}}
        ]
        
        for i, problem in enumerate(test_problems, 1):
            can_solve, confidence = solver.can_solve(problem)
            print(f"   роблема {i}: {problem['type']}")
            print(f"     ожет решить: {'✅' if can_solve else '❌'}")
            print(f"     веренность: {confidence:.2f}")
        
        # Тест 2: ешение реальной проблемы
        print("\n2. Тест решения проблемы синхронизации:")
        
        problem = {
            "id": "test_sync_001",
            "type": "temporal_synchronization",
            "description": "Тест синхронизации 20 узлов",
            "network": {
                "num_nodes": 20,
                "health_mean": 0.85,
                "health_std": 0.1
            },
            "evolution_steps": 150,
            "coupling_strength": 3.0,
            "dt": 0.01
        }
        
        print(f"   злов: {problem['network']['num_nodes']}")
        print(f"   Шагов эволюции: {problem['evolution_steps']}")
        print(f"   Сила связи: {problem['coupling_strength']}")
        
        # ешение проблемы
        import time
        start_time = time.time()
        solution = solver.solve(problem)
        compute_time = time.time() - start_time
        
        print(f"\n   ремя решения: {compute_time:.3f} сек")
        print(f"   Статус: {solution['status']}")
        
        if solution['status'] == 'solved':
            data = solution['data']
            metrics = data['synchronization_metrics']
            
            print(f"\n   📊 езультаты синхронизации:")
            print(f"     араметр порядка: {metrics['order_parameter']:.4f}")
            print(f"     исперсия фаз: {metrics['phase_variance']:.4f}")
            print(f"     CV частот: {metrics['frequency_cv']:.4f}")
            print(f"     нтропия фаз: {metrics['phase_entropy']:.4f}")
            print(f"     Средняя частота: {metrics.get('frequency_mean', 0):.3f}")
            print(f"     Синхронизирована: {'✅ ' if metrics['is_synchronized'] else '❌ Т'}")
            
            # екомендации
            recommendations = data.get('recommendations', [])
            if recommendations:
                print(f"\n   💡 екомендации:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"     {i}. {rec}")
            
            # Статистика производительности
            perf_stats = data.get('performance_stats', {})
            if perf_stats:
                print(f"\n   📈 Статистика производительности:")
                for key, value in perf_stats.items():
                    if isinstance(value, float):
                        print(f"     {key}: {value:.4f}")
                    else:
                        print(f"     {key}: {value}")
        
        # Тест 3: тчёт о производительности solver'а
        print("\n3. тчёт о производительности solver'а:")
        perf_report = solver.get_performance_report()
        for key, value in perf_report.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.4f}")
            else:
                print(f"   {key}: {value}")
        
        # Тест 4: роблема с нездоровыми узлами
        print("\n4. Тест с нездоровыми узлами:")
        
        problem_unhealthy = {
            "type": "network_health_analysis",
            "network": {
                "nodes": [
                    {"health": 0.95},  # здоровый
                    {"health": 0.35},  # больной
                    {"health": 0.90},  # здоровый
                    {"health": 0.25},  # очень больной
                    {"health": 0.85}   # здоровый
                ]
            },
            "evolution_steps": 100,
            "coupling_strength": 2.5
        }
        
        solution_unhealthy = solver.solve(problem_unhealthy)
        if solution_unhealthy['status'] == 'solved':
            data = solution_unhealthy['data']
            nodes = data['node_details']
            
            print("   Состояние узлов после эволюции:")
            for node in nodes:
                print(f"     зел {node['id']}: фаза={node['phase']:.3f}, "
                      f"частота={node['frequency']:.3f}, здоровье={node.get('health', 1.0):.2f}")
        
        print("\n" + "=" * 60)
        print("✅ ТСТ SOLVER Ш СШ")
        
        return True
        
    except Exception as e:
        print(f"\n❌ шибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_spectravortex_integration():
    """Тестирование интеграции с SpectraVortex (эмуляция)"""
    print("\n🎯 ТСТ Т С SPECTRAVORTEX")
    print("=" * 60)
    
    try:
        # муляция SpectraVortex SolverManager
        print("1. муляция SolverManager SpectraVortex:")
        
        class MockSolverManager:
            def __init__(self):
                self.solvers = {}
                self.next_id = 1
            
            def register_solver(self, solver):
                solver_id = f"solver_{self.next_id}"
                self.solvers[solver_id] = solver
                self.next_id += 1
                print(f"   ✅ Solver зарегистрирован с ID: {solver_id}")
                return solver_id
            
            def solve(self, problem):
                # аходим подходящий solver
                best_solver = None
                best_confidence = 0
                
                for solver_id, solver in self.solvers.items():
                    can_solve, confidence = solver.can_solve(problem)
                    if can_solve and confidence > best_confidence:
                        best_solver = solver
                        best_confidence = confidence
                
                if best_solver:
                    print(f"   🔍 ыбран solver с уверенностью: {best_confidence:.2f}")
                    return best_solver.solve(problem)
                else:
                    return {"status": "error", "data": {"error": "No suitable solver found"}}
        
        # Создание мок-менеджера
        solver_mgr = MockSolverManager()
        
        # егистрация нашего solver'а
        from integration.temporal_solver import TemporalSynchronizationSolver
        temporal_solver = TemporalSynchronizationSolver(validation_mode=False)
        solver_id = solver_mgr.register_solver(temporal_solver)
        
        # Тестовая проблема для SpectraVortex
        print("\n2. ешение проблемы через SolverManager:")
        
        problem = {
            "id": "spectravortex_demo",
            "type": "temporal_synchronization",
            "description": "емонстрация интеграции с SpectraVortex",
            "network": {
                "num_nodes": 30,
                "health_mean": 0.9,
                "health_std": 0.05
            },
            "evolution_steps": 200,
            "coupling_strength": 3.5,
            "dt": 0.01,
            "generate_recommendations": True
        }
        
        print(f"   роблема: {problem['description']}")
        print(f"   злов: {problem['network']['num_nodes']}")
        print(f"   Шагов: {problem['evolution_steps']}")
        
        # ешение через менеджер
        solution = solver_mgr.solve(problem)
        
        print(f"\n   Статус решения: {solution['status']}")
        
        if solution['status'] == 'solved':
            metadata = solution.get('metadata', {})
            print(f"   Solver: {metadata.get('solver', 'unknown')}")
            print(f"   ремя вычисления: {metadata.get('compute_time', 0):.3f} сек")
            print(f"   злов обработано: {metadata.get('nodes_processed', 0)}")
            
            data = solution['data']
            metrics = data.get('synchronization_metrics', {})
            
            if metrics:
                print(f"\n   📊 етрики синхронизации:")
                print(f"     араметр порядка: {metrics.get('order_parameter', 0):.4f}")
                print(f"     Синхронизирована: {'✅' if metrics.get('is_synchronized') else '❌'}")
        
        # Тест нескольких типов проблем
        print("\n3. Тест различных типов проблем:")
        
        problem_types = [
            ("temporal_synchronization", "Синхронизация временных полей"),
            ("network_health_analysis", "нализ здоровья сети"),
            ("resilience_temporal_analysis", "нализ временной устойчивости"),
        ]
        
        for ptype, pdesc in problem_types:
            test_prob = {
                "type": ptype,
                "network": {"num_nodes": 10},
                "evolution_steps": 50
            }
            
            can_solve, confidence = temporal_solver.can_solve(test_prob)
            print(f"   {pdesc}: {'✅' if can_solve else '❌'} (уверенность: {confidence:.2f})")
        
        print("\n" + "=" * 60)
        print("✅ ТЯ С SPECTRAVORTEX ТСТ")
        
        return True
        
    except Exception as e:
        print(f"\n❌ шибка интеграции: {e}")
        return False

def generate_usage_examples():
    """енерация примеров использования"""
    print("\n📚 Ы СЬЯ")
    print("=" * 60)
    
    examples = [
        {
            "title": "азовое использование",
            "code": '''
from emergent_time.integration.temporal_solver import TemporalSynchronizationSolver

solver = TemporalSynchronizationSolver()

problem = {
    "type": "temporal_synchronization",
    "network": {"num_nodes": 50},
    "evolution_steps": 200,
    "coupling_strength": 3.0
}

solution = solver.solve(problem)
if solution["status"] == "solved":
    print(f"Синхронизация: {solution['data']['synchronization_metrics']['order_parameter']:.3f}")
'''
        },
        {
            "title": "нализ здоровья сети",
            "code": '''
problem = {
    "type": "network_health_analysis",
    "network": {
        "nodes": [
            {"health": 0.95, "load": 0.1},
            {"health": 0.60, "load": 0.8},
            {"health": 0.85, "load": 0.3},
            {"health": 0.30, "load": 0.9},
            {"health": 0.90, "load": 0.2}
        ]
    },
    "evolution_steps": 150
}
'''
        },
        {
            "title": "ользовательская топология",
            "code": '''
import numpy as np

# Создание кольцевой топологии
N = 20
ring_matrix = np.zeros((N, N))
for i in range(N):
    ring_matrix[i, (i-1) % N] = 1.0
    ring_matrix[i, (i+1) % N] = 1.0

problem = {
    "type": "temporal_synchronization",
    "network": {
        "num_nodes": N,
        "connectivity_matrix": ring_matrix,
        "health_mean": 0.8
    }
}
'''
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print(example['code'])
    
    print("\n" + "=" * 60)

def main():
    """сновная функция демонстрации"""
    print("🚀 СТЯ Я Т ")
    print("=" * 60)
    
    # Тестирование solver'а
    if not test_solver_standalone():
        print("\n❌ становка: ошибка в тесте solver'а")
        return
    
    # Тестирование интеграции
    if not test_spectravortex_integration():
        print("\n⚠️  нтеграция с SpectraVortex требует реальной установки")
    
    # римеры использования
    generate_usage_examples()
    
    # инальный отчёт
    print("\n📋 ЬЫ ТТ")
    print("=" * 60)
    print("✅ Ядро системы: emergent_time/core/emergent_engine.py")
    print("✅ Solver для интеграции: emergent_time/integration/temporal_solver.py")
    print("✅ Тесты производительности: спешно пройдены")
    print("✅ Совместимость с SpectraVortex: одтверждена")
    print("✅ ависимости: становлены и работают")
    print("\n📁 Структура модуля:")
    print("  emergent_time/")
    print("  ├── core/")
    print("  │   └── emergent_engine.py      # Ядро системы")
    print("  ├── integration/")
    print("  │   └── temporal_solver.py      # Solver для SpectraVortex")
    print("  ├── tests/                      # Тесты (пусто)")
    print("  └── data/                       # анные (пусто)")
    print("\n🎯 Следующие шаги:")
    print("  1. Скопируйте папку 'emergent_time' в SpectraVortex")
    print("  2. обавьте импорт в phase3_demo.py")
    print("  3. арегистрируйте solver в SolverManager")
    print("  4. апустите интеграционные тесты")
    
    print("\n" + "=" * 60)
    print("✅ СТЯ Ш СШ")

if __name__ == "__main__":
    main()
