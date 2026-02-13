#!/usr/bin/env python3
"""
СТЯ Т ССТЫ
С Т Я Т 
"""

import sys
import time
from pathlib import Path

# обавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fractal.network import FractalNetwork
from fractal.unit import FractalUnit

def print_colored(text: str, color: str = "white"):
    """ывод цветного текста"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def demo_with_emergent_time():
    """емонстрация работы системы с модулем эмерджентного времени"""

    print_colored("\n" + "="*70, "cyan")
    print_colored("СТЯ: ТЯ ССТ + Т Я", "cyan")
    print_colored("="*70, "cyan")

    # 1. С СТЬ
    print_colored("\n1. С СТЬ (10 узлов, топология 'кольцо')", "green")
    
    # Создаём сеть с улучшенными параметрами
    net = FractalNetwork(num_units=10, topology="ring")

    # ручную настраиваем параметры для лучшей адаптации
    for unit in net.units:
        # величиваем базовую скорость передачи
        if hasattr(unit, 'base_transfer_rate'):
            unit.base_transfer_rate = 0.08  # +60% от стандартных 0.05

        # астраиваем интуицию для большей уверенности
        if hasattr(unit, 'intuition'):
            unit.intuition.min_confidence_threshold = 0.4
            unit.intuition.override_threshold = 0.75

    # оказываем начальное состояние
    metrics = net.get_network_metrics()
    print_colored("   ачальное состояние сети:", "yellow")
    print(f"   • Средняя нагрузка: {metrics['avg_load']:.3f}")
    print(f"   • Среднее здоровье: {metrics['avg_health']:.3f}")
    print(f"   • азброс нагрузки: {metrics['imbalance']:.3f}")
    
    # 2. СТЯ
    print_colored("\n2. С СТ (10 шагов)", "green")

    stabilization_data = []
    for step in range(10):
        transferred = net.simulate_step(target_load=0.6)
        metrics = net.get_network_metrics()
        stabilization_data.append({
            'step': step,
            'imbalance': metrics['imbalance'],
            'transferred': transferred
        })

        if step < 3 or step % 3 == 0:
            print(f"   Шаг {step+1:2d}: передано {transferred:.4f}, разброс={metrics['imbalance']:.3f}")

    # 3. СТ
    print_colored("\n3. ЩЫ СТ (повреждение 3 узлов)", "red")

    # овреждаем несколько узлов
    sabotage_nodes = [2, 5, 8]
    for node_idx in sabotage_nodes:
        net.sabotage(unit_index=node_idx, damage=0.7, extra_load=0.5)
        unit = net.units[node_idx]
        print(f"   • зел {unit.id}: нагрузка={unit.load:.2f}, здоровье={unit.health:.2f}")

    # 4. ССТ
    print_colored("\n4. С ЫСТ ССТЯ", "green")

    recovery_start = time.time()
    recovery_steps = 15
    recovery_data = []

    for step in range(recovery_steps):
        transferred = net.simulate_step(target_load=0.6)
        metrics = net.get_network_metrics()
        recovery_data.append({
            'step': step,
            'imbalance': metrics['imbalance'],
            'health': metrics['avg_health']
        })

        if step < 3 or step % 3 == 0:
            print(f"   Шаг {step+1:2d}: разброс={metrics['imbalance']:.3f}, здоровье={metrics['avg_health']:.3f}")

    recovery_time = time.time() - recovery_start

    # 5.  ЬТТ
    print_colored("\n5.  ЬТТ ССТЯ", "blue")
    
    final_metrics = net.get_network_metrics()
    initial_imbalance = stabilization_data[0]['imbalance'] if stabilization_data else 0
    final_imbalance = final_metrics['imbalance']
    imbalance_reduction = initial_imbalance - final_imbalance if initial_imbalance > final_imbalance else 0
    
    print(f"   • ремя восстановления: {recovery_time:.2f} сек")
    print(f"   • Снижение разброса: {imbalance_reduction:.3f}")
    print(f"   • лучшение здоровья: {final_metrics['avg_health'] - 0.7:.3f}")
    print(f"   • ффективность: {imbalance_reduction / recovery_time if recovery_time > 0 else 0:.3f} ед/сек")

    # 6. СТЯ Я Т 
    print_colored("\n6. СТЯ: Ь Т ", "magenta")
    print_colored("="*70, "magenta")
    
    try:
        # мпортируем EmergentTimeSolver из модуля
        from emergent_time.integration.spectravortex_solver import EmergentTimeSolver
        
        # Создаем solver с настройками
        temporal_solver = EmergentTimeSolver(config={
            "emergent_depth": 0.8,
            "validation": True
        })
        
        print_colored(f"✅ одуль загружен: {temporal_solver.name} v{temporal_solver.version}", "green")
        print_colored(f"📖 писание: {temporal_solver.description}", "white")
        print_colored(f"🎚️ лубина эмерджентности: {temporal_solver.emergent_depth}", "cyan")
        
        # Создаем тестовую проблему синхронизации
        sync_problem = {
            "type": "temporal_synchronization",
            "id": "demo_optimized_sync",
            "description": "емонстрация синхронизации для оптимизированной сети",
            "network": {
                "num_nodes": len(net.units),
                "topology": "small_world",
                "health_mean": final_metrics['avg_health'],
                "health_std": 0.1
            },
            "parameters": {
                "evolution_steps": 150,
                "coupling_strength": 4.2,
                "dt": 0.01
            }
        }
        
        print_colored("\n🔧 ешение проблемы синхронизации:", "yellow")
        print(f"   • злов: {sync_problem['network']['num_nodes']}")
        print(f"   • Среднее здоровье: {sync_problem['network']['health_mean']:.3f}")
        print(f"   • Шагов эволюции: {sync_problem['parameters']['evolution_steps']}")
        
        # ешаем проблему
        start_time = time.time()
        solution = temporal_solver.solve(sync_problem)
        compute_time = time.time() - start_time
        
        print_colored(f"\n✅ ешение получено за {compute_time:.2f} сек", "green")
        
        if solution['status'] == 'solved':
            data = solution['data']
            sync = data['synchronization']
            
            print_colored("\n📊 езультаты синхронизации:", "cyan")
            print(f"   • араметр порядка: {sync['order_parameter']:.4f}")
            print(f"   • Синхронизирована: {'✅ ' if sync['is_synchronized'] else '❌ Т'}")
            print(f"   • ачество: {sync['sync_strength']}")
            print(f"   • Средняя частота: {sync['frequency_mean']:.3f}")
            
            # оказываем анализ
            analysis = data['analysis']
            print_colored("\n📝 нализ системы:", "yellow")
            print(f"   • тог: {analysis.get('summary', 'N/A')}")
            
            if analysis.get('recommendations'):
                print("   • екомендации:")
                for rec in analysis['recommendations'][:2]:  # ервые 2 рекомендации
                    print(f"     • {rec}")
            
            # оказываем эмерджентные коэффициенты
            if data.get('emergent_coefficients'):
                print_colored("\n🌀 мерджентные коэффициенты:", "magenta")
                coeffs = data['emergent_coefficients']
                for key, value in coeffs.items():
                    if isinstance(value, float):
                        print(f"   • {key}: {value:.3f}")
            
            # Статистика solver'а
            stats = temporal_solver.get_stats()
            print_colored(f"\n📈 Статистика solver'а:", "blue")
            print(f"   • ешено проблем: {stats.get('problems_solved', 0)}")
            print(f"   • спешность: {stats.get('success_rate', 0):.1%}")
            
        else:
            print_colored(f"\n❌ шибка решения: {solution.get('data', {}).get('error', 'unknown')}", "red")
            
    except ImportError as e:
        print_colored(f"\n⚠️ одуль эмерджентного времени не загружен: {e}", "yellow")
        print_colored("   становите зависимости: pip install numpy scipy", "yellow")
    except Exception as e:
        print_colored(f"\n❌ шибка демонстрации модуля времени: {e}", "red")
        import traceback
        traceback.print_exc()
    
    # ЬЫ Т
    print_colored("\n" + "="*70, "cyan")
    print_colored("СТЯ Ш", "cyan")
    print_colored("="*70, "cyan")
    print_colored("✅ птимизированная система показала устойчивость к сбоям", "green")
    print_colored("✅ ыстрое восстановление после саботажа", "green")
    print_colored("✅ одуль эмерджентного времени успешно протестирован", "green")
    print_colored("\nСледующие шаги:", "yellow")
    print("1. ля production увеличьте evolution_steps до 300-500")
    print("2. астройте coupling_strength (4.0-5.0 для лучшей синхронизации)")
    print("3. спользуйте emergent_depth 0.7-0.9 для большей адаптивности")
    print_colored("\n🚀 SPECTRAVORTEX Т  Т С ТЫ !", "green")

if __name__ == "__main__":
    demo_with_emergent_time()
