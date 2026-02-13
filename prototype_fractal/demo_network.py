#!/usr/bin/env python3
"""
Демонстрация фрактально-адаптивной сети.
"""
import sys
from pathlib import Path

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fractal.network import FractalNetwork

def demo_basic_network():
    """Демонстрация базовой работы сети."""
    print("="*70)
    print("ДЕМОНСТРАЦИЯ: ФРАКТАЛЬНАЯ АДАПТИВНАЯ СЕТЬ")
    print("="*70)
    
    # 1. Создаём сеть из 8 узлов в кольцевой топологии
    print("\n1. Создаём сеть из 8 узлов (топология: кольцо)...")
    network = FractalNetwork(num_units=8, topology="ring")
    network.print_state()
    
    # 2. Запускаем несколько шагов стабилизации
    print("\n2. Запускаем 5 шагов стабилизации...")
    for step in range(5):
        transferred = network.simulate_step(target_load=0.6)
        print(f"   Шаг {step+1}: перераспределено {transferred:.4f} нагрузки")
    
    network.print_state()
    
    # 3. Визуализируем стабильное состояние
    if len(sys.argv) > 1 and sys.argv[1] == "--no-viz":
        print("\nВизуализация отключена (--no-viz)")
    else:
        print("\n3. Визуализация стабильного состояния...")
        try:
            network.visualize()
        except ImportError as e:
            print(f"   Не удалось визуализировать: {e}")
            print("   Установите: pip install matplotlib networkx")
    
    # 4. САБОТАЖ!
    print("\n4. ИМИТАЦИЯ САБОТАЖА НА УЗЛЕ 2...")
    network.sabotage(unit_index=2, damage=0.6, extra_load=0.4)
    network.print_state()
    
    # 5. Адаптация после сбоя
    print("\n5. ЗАПУСК АДАПТАЦИИ (10 шагов)...")
    for step in range(10):
        transferred = network.simulate_step(target_load=0.6)
        if step < 3 or step % 3 == 0:
            print(f"   Шаг {step+1}: перераспределено {transferred:.4f} нагрузки")
    
    # 6. Финальное состояние
    print("\n6. ФИНАЛЬНОЕ СОСТОЯНИЕ ПОСЛЕ АДАПТАЦИИ:")
    network.print_state()
    
    # 7. Сохранение графика
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        import matplotlib
        save_path = output_dir / "network_final_state.png"
        network.visualize(save_path=save_path)
        print(f"\nГрафик сохранён: {save_path}")
    except ImportError:
        pass
    
    print("\n" + "="*70)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*70)

def demo_topology_comparison():
    """Сравнение разных топологий."""
    print("\n" + "="*70)
    print("СРАВНЕНИЕ ТОПОЛОГИЙ СЕТИ")
    print("="*70)
    
    topologies = ["ring", "mesh", "star", "random"]
    
    for topology in topologies:
        print(f"\n--- Топология: {topology.upper()} ---")
        net = FractalNetwork(num_units=10, topology=topology)
        
        # Сразу после создания
        initial = net.get_network_metrics()["imbalance"]
        
        # После стабилизации
        for _ in range(10):
            net.simulate_step()
        
        final = net.get_network_metrics()
        
        print(f"  Начальный разброс: {initial:.3f}")
        print(f"  Конечный разброс: {final['imbalance']:.3f}")
        print(f"  Общий потенциал: {final['total_potential']:.3f}")
        print(f"  Больных узлов: {final['unhealthy_nodes']}")

if __name__ == "__main__":
    demo_basic_network()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        demo_topology_comparison()
