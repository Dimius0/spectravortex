# test_field_simulation.py
# 🧪 Тест поля: baseline vs циркуляция

from tees_field_simulation import Field
import time


def test_basic():
    """Простой тест — 100 узлов, 100 тиков."""
    print("=" * 60)
    print("🧪 Тест 1: 100 узлов, 100 тиков")
    print("=" * 60)
    
    # Baseline — без циркуляции
    field_baseline = Field(rotation_speed=0.0, name="baseline")
    for i in range(100):
        field_baseline.add_node(f"V{i:04d}")
    
    # С циркуляцией
    field_circ = Field(rotation_speed=0.1, name="circulation")
    for i in range(100):
        field_circ.add_node(f"V{i:04d}")
    
    print("\n📊 Начальное состояние:")
    print(f"  Baseline:    {field_baseline.stats()['nodes']} узлов")
    print(f"  Circulation: {field_circ.stats()['nodes']} узлов")
    
    # 100 тиков
    t0 = time.time()
    for _ in range(100):
        field_baseline.rotate(dt=0.1)
        field_circ.rotate(dt=0.1)
    elapsed = time.time() - t0
    
    print(f"\n⏱️ 100 тиков за {elapsed:.3f} сек")
    
    # Роли
    field_baseline.assign_roles()
    field_circ.assign_roles()
    
    print("\n📊 Роли (baseline):")
    for role, count in sorted(field_baseline.role_distribution().items()):
        print(f"  {role}: {count}")
    
    print("\n📊 Роли (circulation):")
    for role, count in sorted(field_circ.role_distribution().items()):
        print(f"  {role}: {count}")
    
    # Симметрия
    sym_baseline = field_baseline.check_symmetry()
    sym_circ = field_circ.check_symmetry()
    
    print("\n📐 Симметрия (baseline):")
    print(f"  phase_balance: {sym_baseline['phase_balance']}")
    print(f"  total_phase: {sym_baseline['total_phase']:.4f}")
    print(f"  role_parity: {sym_baseline['role_parity']}")
    
    print("\n📐 Симметрия (circulation):")
    print(f"  phase_balance: {sym_circ['phase_balance']}")
    print(f"  total_phase: {sym_circ['total_phase']:.4f}")
    print(f"  role_parity: {sym_circ['role_parity']}")
    
    # Статистика
    print("\n📊 Stats (baseline):")
    stats = field_baseline.stats()
    for k, v in stats.items():
        if k != 'roles':
            print(f"  {k}: {v}")
    
    print("\n📊 Stats (circulation):")
    stats = field_circ.stats()
    for k, v in stats.items():
        if k != 'roles':
            print(f"  {k}: {v}")


def test_broadcast():
    """Тест полевой передачи."""
    print("\n" + "=" * 60)
    print("🧪 Тест 2: Полевая передача (100 узлов)")
    print("=" * 60)
    
    field = Field(rotation_speed=0.1, name="broadcast_test")
    for i in range(100):
        field.add_node(f"V{i:04d}")
    
    # Отправка от V0000
    sender = field.nodes['V0000']
    msg = sender.send("тестовое сообщение")
    
    delivered = sum(1 for n in field.nodes.values() if msg['id'] in n.received)
    
    print(f"\n📡 Broadcast от V0000:")
    print(f"  Сообщение: {msg['id'][:16]}...")
    print(f"  Доставлено: {delivered}/100")
    print(f"  Stats:")
    for k, v in field.stats().items():
        if k != 'roles':
            print(f"    {k}: {v}")

def test_scaling():
    """Тест масштабирования: 100, 500, 1000 узлов."""
    print("\n" + "=" * 60)
    print("🧪 Тест 3: Масштабирование")
    print("=" * 60)
    
    for N in [100, 500, 1000]:
        print(f"\n📊 N = {N}")
        
        # Baseline
        f_base = Field(rotation_speed=0.0, name=f"base_{N}")
        for i in range(N):
            f_base.add_node(f"V{i:05d}")
        
        # Circulation
        f_circ = Field(rotation_speed=0.1, name=f"circ_{N}")
        for i in range(N):
            f_circ.add_node(f"V{i:05d}")
        
        t0 = time.time()
        for _ in range(50):
            f_base.rotate(dt=0.1)
            f_circ.rotate(dt=0.1)
        elapsed = time.time() - t0
        
        f_base.assign_roles()
        f_circ.assign_roles()
        
        sym_base = f_base.check_symmetry()
        sym_circ = f_circ.check_symmetry()
        
        cr_base = f_base.stats()['core_radius']
        cr_circ = f_circ.stats()['core_radius']
        
        if isinstance(cr_base, tuple):
            w_base = cr_base[1] - cr_base[0]
            print(f"  baseline:    core_radius=[{cr_base[0]:.4f}, {cr_base[1]:.4f}] ширина {w_base:.4f}")
        else:
            print(f"  baseline:    core_radius={cr_base:.4f}")
        
        if isinstance(cr_circ, tuple):
            w_circ = cr_circ[1] - cr_circ[0]
            print(f"  circulation: core_radius=[{cr_circ[0]:.4f}, {cr_circ[1]:.4f}] ширина {w_circ:.4f}")
        else:
            print(f"  circulation: core_radius={cr_circ:.4f}")
        
        print(f"  ⏱️ 50 тиков: {elapsed:.3f} сек")
        print(f"  role_parity (base): {sym_base['role_parity']}")
        print(f"  role_parity (circ): {sym_circ['role_parity']}")            


if __name__ == "__main__":
    test_basic()
    test_broadcast()
    test_scaling()
    print("\n" + "=" * 60)
    print("✅ Тесты завершены")
    print("=" * 60)