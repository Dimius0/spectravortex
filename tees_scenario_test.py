# tees_scenario_test.py
# 🎭 СЦЕНАРИЙ: Атака на TEES-сеть!

# Импортируем из tees_ultimate_final
from tees_ultimate_final import *

def scenario_attack():
    print("🎭 СЦЕНАРИЙ: АТАКА НА TEES-СЕТЬ")
    print("=" * 60)
    
    system = QuarantineSystem(quarantine_size=10)
    
    # ═══════════════════════════════
    # АКТ 1: Мирная сеть растёт!
    # ═══════════════════════════════
    print("\n📖 АКТ 1: Мирная сеть растёт!")
    good_nodes = []
    for i in range(30):
        b = TEESBeacon(f"good_{i}", f"10.0.0.{i}", (i%10, i//10, 0), 1)
        b.do_work()
        b.do_work()  # Двойная работа!
        good_nodes.append(b)
    
    system.add_new_nodes(good_nodes[:15])
    system.add_new_nodes(good_nodes[15:])
    
    print(f"\n   Сеть: {len(system.main_beacons)} маяков")
    
    # ═══════════════════════════════
    # АКТ 2: Появляются редиски!
    # ═══════════════════════════════
    print(f"\n{'='*60}")
    print("\n📖 АКТ 2: Появляются редиски!")
    
    # Редиски маскируются!
    sneaky = []
    for i in range(10):
        b = TEESBeacon(f"sneaky_{i}", f"10.0.1.{i}", (i%10, 5, 0), -1)
        # Половина делает вид, что работает!
        if i < 5:
            b.do_work()
        sneaky.append(b)
    
    system.add_new_nodes(sneaky)
    
    print(f"\n   Сеть: {len(system.main_beacons)} маяков")
    
    # ═══════════════════════════════
    # АКТ 3: Массированная атака!
    # ═══════════════════════════════
    print(f"\n{'='*60}")
    print("\n📖 АКТ 3: Массированная атака!")
    
    attack_nodes = []
    for i in range(20):
        b = TEESBeacon(f"attacker_{i}", f"10.0.2.{i}", (i%10, 8, 0), -1)
        # НИКТО не работает!
        attack_nodes.append(b)
    
    system.add_new_nodes(attack_nodes)
    
    print(f"\n   Сеть: {len(system.main_beacons)} маяков")
    
    # ═══════════════════════════════
    # ИТОГИ
    # ═══════════════════════════════
    print(f"\n{'='*60}")
    print("\n📊 ИТОГИ СЦЕНАРИЯ:")
    print(f"   Хороших: {sum(1 for b in system.main_beacons if 'good' in b.beacon_id)}")
    print(f"   Хитрых (притворщиков): {sum(1 for b in system.main_beacons if 'sneaky' in b.beacon_id)}")
    print(f"   Атакующих: {sum(1 for b in system.main_beacons if 'attacker' in b.beacon_id)}")
    print(f"   Всего в сети: {len(system.main_beacons)}")
    print(f"   Баланс=0: {'✅' if all(b.economy.verify_balance() for b in system.main_beacons) else '❌'}")
    
    print(f"\n{'='*60}")
    print("🎭 СЦЕНАРИЙ ЗАВЕРШЁН!")
    print(f"{'='*60}")

if __name__ == "__main__":
    scenario_attack()