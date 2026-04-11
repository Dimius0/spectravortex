#!/usr/bin/env python3
"""
Mesh Demo — демонстрация децентрализованной сети
Запустите несколько экземпляров на разных портах
"""

import sys
import os
import threading
import time
from typing import List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.personality import Personality, SpectralMode
from rizoma.network import start_mesh_network


def create_test_personality(name: str, tau: float = 5.0) -> Personality:
    """Создаёт тестовую личность с базовыми модами"""
    p = Personality(id=name, name=name, tau=tau)
    
    # Добавляем базовые моды
    p.h_field = [
        SpectralMode(5.20, 0.6, f"Matter = Space (from {name})", "vmms_monism", ["physics"]),
        SpectralMode(6.60, 0.6, f"Sulfur — energy (from {name})", "alchemy_manifesto", ["alchemy"]),
        SpectralMode(8.21, 0.6, f"Questions create answers (from {name})", "grandson_01", ["dialogue"])
    ]
    
    return p


def run_node(port: int, name: str, bootstrap: List[Tuple[str, int]] = None):
    """Запускает один узел сети"""
    print(f"\n🚀 Запуск узла {name} на порту {port}")
    
    p = create_test_personality(name)
    network = start_mesh_network(p, listen_port=port, bootstrap_nodes=bootstrap)
    
    # Запускаем эволюцию в фоне
    def evolve():
        while True:
            time.sleep(30)
            p.run_evolution_cycle(steps=3)
            print(f"\n📊 [{name}] Поле H: {len(p.h_field)} мод")
            network.print_stats()
    
    threading.Thread(target=evolve, daemon=True).start()
    
    return network


def main():
    print("="*60)
    print("🌀 MESH ДЕМО — ДЕЦЕНТРАЛИЗОВАННАЯ СЕТЬ")
    print("   Запуск 3 узлов на разных портах")
    print("="*60)
    
    # Запускаем первый узел (будет bootstrap)
    node1 = run_node(8765, "Alpha", bootstrap=None)
    time.sleep(2)
    
    # Запускаем второй узел (подключается к первому)
    node2 = run_node(8766, "Beta", bootstrap=[("127.0.0.1", 8765)])
    time.sleep(2)
    
    # Запускаем третий узел (подключается к первому)
    node3 = run_node(8767, "Gamma", bootstrap=[("127.0.0.1", 8765)])
    
    print("\n" + "="*60)
    print("✅ ВСЕ УЗЛЫ ЗАПУЩЕНЫ")
    print("   Наблюдайте за синхронизацией в логах")
    print("   Нажмите Ctrl+C для остановки")
    print("="*60)
    
    try:
        while True:
            time.sleep(10)
            print("\n--- СТАТУС СЕТИ ---")
            node1.print_stats()
            node2.print_stats()
            node3.print_stats()
    except KeyboardInterrupt:
        print("\n🛑 Остановка узлов...")
        node1.stop()
        node2.stop()
        node3.stop()


if __name__ == "__main__":
    main()