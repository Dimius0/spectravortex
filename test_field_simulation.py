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

def test_compression():
    """Тест полного цикла сжатия: раздувание → коллапс → сверхсжатие → удар."""
    print("\n" + "=" * 60)
    print("🧪 Тест 4: Сжатие поля — полный цикл")
    print("=" * 60)
    
    field = Field(rotation_speed=0.1, name="compression_test")
    for i in range(100):
        field.add_node(f"V{i:04d}")
    
    # Установившиеся тики
    for _ in range(10):
        field.rotate(dt=0.1)
    
    # Начальное состояние
    sym_before = field.check_symmetry()
    cr_before = field.stats()['core_radius']
    avg_r_before = field.stats()['avg_radius']
    
    print(f"\n📊 До сжатия (нормальное состояние):")
    print(f"  core_radius: {cr_before}")
    print(f"  avg_radius: {avg_r_before:.4f}")
    print(f"  phase_coherence: {sym_before.get('phase_coherence', 0.0):.4f}")
    print(f"  compression_phase: {field.compression_phase}")
    
    # Полный цикл сжатия — 3 фазы
    print(f"\n🗜️ Сжатие поля (полный цикл):")
    
    # Фаза 1 — раздувание (0.0 → 0.5)
    print(f"\n  🔵 Фаза 1: РАЗДУВАНИЕ")
    for step in range(5):
        field.compress(force=0.1, dt=0.1)
        stats = field.stats()
        sym = field.check_symmetry()
        print(f"    шаг {step}: level={field.compression_level:.2f}, "
              f"phase={field.compression_phase}, "
              f"avg_r={stats['avg_radius']:.4f}, "
              f"coherence={sym.get('phase_coherence', 0.0):.4f}")
    
    # Фаза 2 — коллапс (0.5 → 0.8)
    print(f"\n  🔴 Фаза 2: КОЛЛАПС")
    for step in range(3):
        field.compress(force=0.1, dt=0.1)
        stats = field.stats()
        sym = field.check_symmetry()
        print(f"    шаг {step}: level={field.compression_level:.2f}, "
              f"phase={field.compression_phase}, "
              f"avg_r={stats['avg_radius']:.4f}, "
              f"coherence={sym.get('phase_coherence', 0.0):.4f}")
    
    # Фаза 3 — сверхсжатие (0.8 → 1.0)
    print(f"\n  ⚫ Фаза 3: СВЕРХСЖАТИЕ")
    for step in range(5):
        field.compress(force=0.1, dt=0.1)
        stats = field.stats()
        sym = field.check_symmetry()
        print(f"    шаг {step}: level={field.compression_level:.2f}, "
              f"phase={field.compression_phase}, "
              f"avg_r={stats['avg_radius']:.4f}, "
              f"coherence={sym.get('phase_coherence', 0.0):.4f}")
    
    # Состояние перед ударом
    sym_compressed = field.check_symmetry()
    cr_compressed = field.stats()['core_radius']
    avg_r_compressed = field.stats()['avg_radius']
    
    print(f"\n📊 Перед ударом (сверхсжатие):")
    print(f"  core_radius: {cr_compressed}")
    print(f"  avg_radius: {avg_r_compressed:.4f}")
    print(f"  phase_coherence: {sym_compressed.get('phase_coherence', 0.0):.4f}")
    print(f"  compression_level: {field.compression_level:.2f}")
    print(f"  compression_phase: {field.compression_phase}")
    
    # Обратный ход — полевой удар
    print(f"\n💥 ОБРАТНЫЙ ХОД — ПОЛЕВОЙ УДАР:")
    event = field.release()
    print(f"  shock: {event['shock']}")
    print(f"  phase_at_release: {event.get('phase', 'unknown')}")
    print(f"  level: {event['level']:.2f}")
    print(f"  amplitude: {event['amplitude']:.2f}")
    print(f"  front_size: {event['front_size']}")
    print(f"  front_signature: {event.get('front_signature', 0.0):.6f}")
    
    # Состояние после удара
    sym_shock = field.check_symmetry()
    cr_shock = field.stats()['core_radius']
    avg_r_shock = field.stats()['avg_radius']
    
    print(f"\n📊 После удара (расширение):")
    print(f"  core_radius: {cr_shock}")
    print(f"  avg_radius: {avg_r_shock:.4f}")
    print(f"  phase_coherence: {sym_shock.get('phase_coherence', 0.0):.4f}")
    print(f"  compression_phase: {field.compression_phase}")
    
    # Сравнение
    print(f"\n📈 Сравнение:")
    print(f"  avg_radius до:       {avg_r_before:.4f}")
    print(f"  avg_radius при сжатии: {avg_r_compressed:.4f}")
    print(f"  avg_radius после:    {avg_r_shock:.4f}")
    print(f"  coherence до:        {sym_before.get('phase_coherence', 0.0):.4f}")
    print(f"  coherence при сжатии: {sym_compressed.get('phase_coherence', 0.0):.4f}")
    print(f"  coherence после:     {sym_shock.get('phase_coherence', 0.0):.4f}")
    
    # История ударов
    print(f"\n📜 История полевых ударов:")
    for e in field.shock_events[-5:]:
        print(f"  t={e['time']:.2f}: phase={e.get('phase', '?')}, "
              f"level={e['level']:.2f}, amp={e['amplitude']:.2f}, "
              f"sig={e.get('front_signature', 0.0):.6f}")

def test_funnel():
    """Тест смесительной воронки."""
    print("\n" + "=" * 60)
    print("🧪 Тест 5: Смесительная воронка")
    print("=" * 60)
    
    import time
    
    for N in [100, 500, 1000]:
        print(f"\n📊 N = {N}")
        
        field = Field(rotation_speed=0.1, name=f"funnel_{N}")
        for i in range(N):
            field.add_node(f"V{i:05d}")
        
        # 10 обычных тиков — установка
        for _ in range(10):
            field.rotate(dt=0.1)
        
        sym_before = field.check_symmetry()
        cr_before = field.stats()['core_radius']
        
        print(f"  До воронки:")
        print(f"    core_radius: {cr_before}")
        print(f"    phase_coherence: {sym_before['phase_coherence']:.4f}")
        print(f"    phase_balance: {sym_before['phase_balance']}")
        
        # Замер воронки
        t0 = time.time()
        for _ in range(10):
            field.funnel()
        elapsed = time.time() - t0
        
        sym_after = field.check_symmetry()
        cr_after = field.stats()['core_radius']
        
        print(f"  После воронки (10 проходов):")
        print(f"    core_radius: {cr_after}")
        print(f"    phase_coherence: {sym_after['phase_coherence']:.4f}")
        print(f"    phase_balance: {sym_after['phase_balance']}")
        print(f"    ⏱️ Время: {elapsed:.3f} сек ({elapsed/10*1000:.1f} мс на проход)")
        print(f"    Изменение coherence: {sym_before['phase_coherence']:.4f} → {sym_after['phase_coherence']:.4f}")

def test_vector_switch():
    """Тест смены вектора потока и выброса информации."""
    print("\n" + "=" * 60)
    print("🧪 Тест 6: Смена вектора → выброс информации")
    print("=" * 60)
    
    field = Field(rotation_speed=0.1, name="vector_switch")
    for i in range(100):
        field.add_node(f"V{i:04d}")
    
    # Установка
    for _ in range(10):
        field.rotate(dt=0.1)
    
    print("\n📊 Сжатие с отслеживанием fraction и coherence:")
    print(f"  {'step':>4} | {'level':>6} | {'frac':>6} | {'coherence':>10} | {'band':>18} | {'avg_r':>8} | {'phase':>18}")
    print("  " + "-" * 90)
    
    # Сжимаем с малым шагом — чтобы увидеть пик
    for step in range(25):
        field.compress(force=0.05, dt=0.1)
        stats = field.stats()
        sym = field.check_symmetry()
        
        frac = field.compression_fraction
        coh = sym['phase_coherence']
        avg_r = stats['avg_radius']
        phase = field.compression_phase
        
        # Полоса срыва
        band_low, band_high = field.compression_band
        in_band = band_low <= coh <= band_high
        
        # Метка: в полосе или нет
        band_str = f"[{band_low:.3f},{band_high:.3f}]"
        marker = " ← В ПОЛОСЕ" if in_band else ""
        
        print(f"  {step:>4} | {field.compression_level:>6.3f} | {frac:>6.3f} | {coh:>10.4f} | {band_str:>18} | {avg_r:>8.4f} | {phase:>18}{marker}")
    
        # TEES-состояние
        joint = field.tees_joint_state()
        if joint['in_joint']:
            print(f"       ⚡ TEES шарнир-смеситель: spiral={joint['spiral_weight']:.2f}, radial={joint['radial_weight']:.2f}, mixed={joint['mixed_weight']:.2f}")    

    # Итоговая полоса срыва
    band_low, band_high = field.compression_band
    print(f"\n📊 Полоса срыва: [{band_low:.4f}, {band_high:.4f}]")
    print(f"   Ширина полосы: {band_high - band_low:.4f}")
    
    # Статистика по полосе
    coh_max = field._coh_max if hasattr(field, '_coh_max') else 0.0
    coh_min = field._coh_min if hasattr(field, '_coh_min') else 1.0
    print(f"   Coherence max: {coh_max:.4f}")
    print(f"   Coherence min: {coh_min:.4f}")

    # Удар
    print("\n💥 Обратный ход — выброс:")
    event = field.release()
    sym = field.check_symmetry()

    # 3D TEES состояние
    s3d = field.tees_3d_state()
    print(f"       3D TEES: z_mean={s3d.get('z_mean', 0):.3f}, "
          f"z_spread={s3d.get('z_spread', 0):.3f}, "
          f"volume={s3d.get('volume', 0):.3f}")
    print(f"                spiral_corr={s3d.get('spiral_corr', 0):.3f}, "
          f"radial_corr={s3d.get('radial_corr', 0):.3f}")

    # Состояние шарнира TEES
    joint = field.tees_joint_state()
    joint_marker = " ⚡ШАРНИР" if joint['in_joint'] else ""
    print(f"       TEES: spiral={joint['spiral_weight']:.2f}, radial={joint['radial_weight']:.2f}, mix={joint['mixing_intensity']:.2f}{joint_marker}")
    
    print(f"  shock: {event['shock']}")
    print(f"  phase_at_release: {event.get('phase', '?')}")
    print(f"  amplitude: {event['amplitude']:.2f}")
    print(f"  front_signature: {event.get('front_signature', 0.0):.6f}")
    print(f"  coherence после: {sym['phase_coherence']:.4f}")
    print(f"  avg_radius после: {field.stats()['avg_radius']:.4f}")




if __name__ == "__main__":
    test_basic()
    test_broadcast()
    test_scaling()
    test_compression()
    test_funnel()
    test_vector_switch()
    print("\n" + "=" * 60)
    print("✅ Тесты завершены")
    print("=" * 60)