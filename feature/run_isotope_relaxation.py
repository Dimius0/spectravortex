#!/usr/bin/env python3
"""
run_isotope_relaxation.py — прогон изотопной конфигурации с айкидо-штормом (пятифазный пендель)

Вход:
  - feature/data/isotope_relaxation_frame0.json (200 вихрей, 16³ сетка)
  
Выход:
  - feature/data/isotope_trajectories.json (каждый 10-й шаг, формат плеера)
  - feature/data/isotope_checkpoint.json (последний шаг для возобновления)
"""

import json
import sys
import os
import argparse
import numpy as np
from datetime import datetime

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src', 'architect'))

from biharmonic_3d import TopologicalArchitect3D
from thermodynamics import ThermodynamicState
from fractal_time import FractalTimeEvolution, FractalFieldWrapper
from adaptive_chi_tuner import AdaptiveChiTuner

# ========== КОНСТАНТЫ ВММП ==========
VMMP = {
    "d_opt_default": {1: 0.74, 2: 1.22, 3: 1.52, 4: 1.82, 5: 2.05, 6: 2.20, 7: 2.40},
    "d_env_base": 2.10,
}

# ========== СОХРАНЕНИЕ ==========

def save_json(path, data):
    def convert(obj):
        if isinstance(obj, (np.bool_, bool)): return bool(obj)
        if isinstance(obj, (np.integer, np.int_)): return int(obj)
        if isinstance(obj, (np.floating, np.float_)): return float(obj) if not np.isnan(obj) else None
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, datetime): return obj.isoformat()
        return str(obj)
    def convert_recursive(obj):
        if isinstance(obj, dict): return {k: convert_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)): return [convert_recursive(i) for i in obj]
        else: return convert(obj)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(convert_recursive(data), f, indent=2)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ========== ПЯТИФАЗНЫЙ РЕЗОНАНСНЫЙ ПЕНДЕЛЬ ==========

def apply_five_phase_pulse(thermo_state, pulse_params):
    """
    Пятифазный импульс «Взрывной синтез»:
    1. Детонация (сжатие)
    2. Вакуум (растяжение) — ключевая фаза для необратимости
    3. Повторное сжатие
    4. Заморозка
    5. Остывание
    """
    P_peak = pulse_params.get('P_peak', 500.0)
    T_peak = pulse_params.get('T_peak', 50000.0)
    P_vacuum = pulse_params.get('P_vacuum', -10.0)
    P_ambient = pulse_params.get('P_ambient', 0.1)
    T_ambient = pulse_params.get('T_ambient', 300.0)

    # Фаза 1: Детонация (сжатие)
    thermo_state.pressure = P_peak
    thermo_state.temperature = T_peak
    if hasattr(thermo_state, 'update_factors'):
        thermo_state.update_factors()
    print(f"  💥 Фаза 1/5: ДЕТОНАЦИЯ (P={P_peak}, T={T_peak})")
    yield 'detonation'

    # Фаза 2: Вакуум (растяжение) — КЛЮЧЕВАЯ
    thermo_state.pressure = P_vacuum
    if hasattr(thermo_state, 'update_factors'):
        thermo_state.update_factors()
    print(f"  🌀 Фаза 2/5: ВАКУУМ (P={P_vacuum}, T={T_peak})")
    yield 'vacuum'

    # Фаза 3: Повторное сжатие
    thermo_state.pressure = P_peak * 0.5
    if hasattr(thermo_state, 'update_factors'):
        thermo_state.update_factors()
    print(f"  📈 Фаза 3/5: ПОВТОРНОЕ СЖАТИЕ (P={P_peak*0.5}, T={T_peak})")
    yield 'recompression'

    # Фаза 4: Заморозка
    thermo_state.pressure = P_peak * 0.8
    thermo_state.temperature = T_ambient
    if hasattr(thermo_state, 'update_factors'):
        thermo_state.update_factors()
    print(f"  ❄️  Фаза 4/5: ЗАМОРОЗКА (P={P_peak*0.8}, T={T_ambient})")
    yield 'freeze'

    # Фаза 5: Остывание (возврат к норме)
    thermo_state.pressure = P_ambient
    thermo_state.temperature = T_ambient
    if hasattr(thermo_state, 'update_factors'):
        thermo_state.update_factors()
    print(f"  🌡️  Фаза 5/5: ОСТЫВАНИЕ (P={P_ambient}, T={T_ambient})")
    yield 'cooldown'

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=100000, help='Максимальное число шагов')
    parser.add_argument('--T', type=float, default=300.0, help='Температура (K)')
    parser.add_argument('--P', type=float, default=0.1, help='Давление (GPa)')
    parser.add_argument('--resume', type=str, help='Путь к чекпоинту')
    parser.add_argument('--no-storm', action='store_true', help='Отключить шторм')
    parser.add_argument('--storm-P', type=float, default=500.0, help='Пиковое давление шторма (GPa)')
    parser.add_argument('--storm-T', type=float, default=50000.0, help='Пиковая температура шторма (K)')
    parser.add_argument('--storm-vacuum', type=float, default=-10.0, help='Давление фазы вакуума (GPa)')
    parser.add_argument('--watchdog-window', type=int, default=5000, help='Окно сторожа релаксации')
    parser.add_argument('--watchdog-tolerance', type=float, default=0.01, help='Допуск сторожа (1%)')
    parser.add_argument('--save-interval', type=int, default=10, help='Интервал сохранения кадров')
    args = parser.parse_args()

    start_time = datetime.now()
    print("=" * 70)
    print("ИЗОТОПНАЯ РЕЛАКСАЦИЯ С ПЯТИФАЗНЫМ АЙКИДО-ПЕНДЕЛЕМ")
    print("Модель: ВММП | Решатель: BiharmonicSolver3D")
    print("=" * 70)

    # Пути
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    feature_dir = os.path.join(base_dir, 'feature', 'data')
    os.makedirs(feature_dir, exist_ok=True)

    input_file = os.path.join(feature_dir, 'isotope_relaxation_frame0.json')
    output_traj = os.path.join(feature_dir, 'isotope_trajectories.json')
    output_checkpoint = os.path.join(feature_dir, 'isotope_checkpoint.json')

    grid_size = 16
    max_steps = args.steps
    T, P = args.T, args.P
    save_interval = args.save_interval

    print(f"\nСетка: {grid_size}³ | Шагов макс: {max_steps} | T: {T}K | P: {P}GPa")
    print(f"Шторм: {'отключён' if args.no_storm else f'пятифазный пендель (P={args.storm_P}, T={args.storm_T}, vac={args.storm_vacuum})'}")
    print(f"Сторож: окно {args.watchdog_window}, допуск {args.watchdog_tolerance*100}%")
    print(f"Сохранение: каждый {save_interval}-й шаг → {output_traj}")

    # Загрузка начальной конфигурации
    print("\n[1/4] Загрузка изотопной конфигурации...")
    frame0_data = load_json(input_file)
    frame0 = frame0_data[0]

    components_meta = []  # метаданные для сохранения кадров
    vortex_index = 0

    for g_str, entries in frame0.get("groups", {}).items():
        g = int(g_str)
        for entry in entries:
            pos = entry["pos"]
            tau = entry.get("tau", 0)
            symbol = entry.get("symbol", "?")
            radius = entry.get("radius", 0.5)
            half_life = entry.get("half_life", None)
            unstable = entry.get("unstable", False)

            components_meta.append({
                "charge": tau if tau != 0 else 1,
                "position": np.array(pos, dtype=np.float64),
                "orientation": [0, 0, 1],
                "symbol": symbol,
                "Z": vortex_index + 1,
                "tau": tau,
                "group": g,
                "radius": radius,
                "half_life": half_life,
                "unstable": unstable,
            })
            vortex_index += 1

    n_vortices = len(components_meta)
    print(f"Загружено вихрей: {n_vortices}")

    # Инициализация решателя
    print("\n[2/4] Инициализация 3D-решателя...")
    architect = TopologicalArchitect3D(
        grid_shape=(grid_size, grid_size, grid_size),
        box_size=(16.0, 16.0, 16.0)
    )

    for comp in components_meta:
        architect.add_component(comp)

    thermo_state = ThermodynamicState(T, P)

    evolution = FractalTimeEvolution(num_levels=7, base_dt=1.0)
    evolution.add_field(1, FractalFieldWrapper(architect, 1))

    chi_tuner = None
    elements_config_path = os.path.join(base_dir, 'data', 'field_H_elements_complete.json')
    if os.path.exists(elements_config_path):
        print("    Тюнер χ активирован")
        chi_tuner = AdaptiveChiTuner(elements_config_path)

    energy_history = []
    min_dist_history = []
    all_trajectories = []
    storm_triggered = False
    prev_min_dist = float('inf')
    start_step = 0

    # Сохраняем кадр 0
    groups_frame0 = {str(g): [] for g in range(1, 8)}
    for comp in components_meta:
        g = str(comp["group"])
        pos = comp["position"]
        groups_frame0[g].append({
            "pos": [round(float(pos[0]), 6), round(float(pos[1]), 6), round(float(pos[2]), 6)],
            "tau": comp["tau"],
            "symbol": comp["symbol"],
            "radius": comp["radius"],
            "half_life": comp.get("half_life"),
            "unstable": comp.get("unstable", False)
        })

    frame0_output = {
        "step": 0,
        "d_min": None,
        "groups": groups_frame0,
        "tau_map": [comp["tau"] for comp in components_meta],
        "symbols": [comp["symbol"] for comp in components_meta],
        "radii": [comp["radius"] for comp in components_meta]
    }
    all_trajectories.append(frame0_output)

    if args.resume and os.path.exists(args.resume):
        print(f"[!] Восстановление из чекпоинта: {args.resume}")
        saved = load_json(args.resume)
        start_step = saved.get("step", 0)
        energy_history = saved.get("energy_history", [])
        min_dist_history = saved.get("min_dist_history", [])
        all_trajectories = saved.get("trajectories", [])
        if "positions" in saved:
            for i, comp in enumerate(architect.components):
                if i < len(saved["positions"]):
                    comp["vortex"].position = np.array(saved["positions"][i])
        print(f"    Продолжаем с шага {start_step + 1}")

    print(f"\n[3/4] Эволюция (шаги {start_step+1}-{max_steps})...")
    print("─" * 75)
    header = f"{'Шаг':>6} | {'Энергия':>12} | {'d_min':>8} | {'Шторм':>5} | {'Время':>8} | {'Сохр':>5}"
    print(header)
    print("─" * 75)

    watchdog_counter = 0
    step = start_step

    def make_frame(step_num, min_d):
        groups = {str(g): [] for g in range(1, 8)}
        for comp in architect.components:
            g = str(comp.get("group", 4))
            pos = comp["vortex"].position
            groups[g].append({
                "pos": [round(float(pos[0]), 6), round(float(pos[1]), 6), round(float(pos[2]), 6)],
                "tau": comp.get("tau", 0),
                "symbol": comp.get("symbol", "?"),
                "radius": comp.get("radius", 0.5),
                "half_life": comp.get("half_life"),
                "unstable": comp.get("unstable", False)
            })
        return {
            "step": step_num,
            "d_min": round(min_d, 4) if min_d < float('inf') else None,
            "groups": groups,
            "tau_map": [comp.get("tau", 0) for comp in architect.components],
            "symbols": [comp.get("symbol", "?") for comp in architect.components],
            "radii": [comp.get("radius", 0.5) for comp in architect.components]
        }

    def compute_min_dist():
        md = float('inf')
        comps = architect.components
        for i in range(len(comps)):
            for j in range(i+1, len(comps)):
                d = np.linalg.norm(comps[i]["vortex"].position - comps[j]["vortex"].position)
                if d < md:
                    md = d
        return md

    def save_checkpoint(step_num):
        positions = [comp["vortex"].position.tolist() for comp in architect.components]
        checkpoint = {
            "step": step_num + 1,
            "energy_history": energy_history,
            "min_dist_history": min_dist_history,
            "trajectories": all_trajectories,
            "positions": positions,
            "T": T,
            "P": P,
        }
        save_json(output_checkpoint, checkpoint)
        save_json(output_traj, all_trajectories)

    while step < max_steps:
        # === АЙКИДО-ШТОРМ (ПЯТИФАЗНЫЙ ПЕНДЕЛЬ) ===
        if not args.no_storm and not storm_triggered and prev_min_dist < float('inf'):
            current_min = min_dist_history[-1] if min_dist_history else float('inf')
            if current_min < prev_min_dist * 0.9:
                storm_triggered = True
                pulse_params = {
                    'P_peak': args.storm_P,
                    'T_peak': args.storm_T,
                    'P_vacuum': args.storm_vacuum,
                    'P_ambient': P,
                    'T_ambient': T,
                }
                print(f"{'':─^75}")
                print(f" ⚡ АЙКИДО-ШТОРМ: d_min={current_min:.3f} → ПЯТИФАЗНЫЙ ПЕНДЕЛЬ")
                pulse_gen = apply_five_phase_pulse(thermo_state, pulse_params)
                for phase_name in pulse_gen:
                    evolution.evolve_step(state=thermo_state)
                    total_energy = architect.compute_energy()
                    energy_history.append(total_energy)
                    min_dist = compute_min_dist()
                    min_dist_history.append(min_dist)
                    prev_min_dist = min_dist
                    step += 1

                    if step % save_interval == 0:
                        all_trajectories.append(make_frame(step, min_dist))

                    step_time = (datetime.now() - start_time).total_seconds()
                    print(f"  [{phase_name}] шаг {step:6} | E={total_energy:12.1f} | d_min={min_dist:8.4f} | {step_time:8.1f}s")

                print(f" 🌤️  Пендель завершён. d_min = {min_dist_history[-1]:.4f}")
                print(f"{'':─^75}")
                continue

        # Обычная эволюция
        evolution.evolve_step(state=thermo_state)
        total_energy = architect.compute_energy()
        energy_history.append(total_energy)

        min_dist = compute_min_dist()
        min_dist_history.append(min_dist)

        if step % save_interval == 0:
            all_trajectories.append(make_frame(step, min_dist))

        prev_min_dist = min_dist
        step += 1

        # Сторож релаксации
        if len(energy_history) >= args.watchdog_window:
            recent = energy_history[-args.watchdog_window:]
            energy_range = max(recent) - min(recent)
            avg_energy = sum(recent) / len(recent)
            rel_range = energy_range / avg_energy if avg_energy > 0 else 0

            if rel_range < args.watchdog_tolerance and min_dist < VMMP["d_env_base"] * 0.5:
                watchdog_counter += 1
            else:
                watchdog_counter = 0

        step_time = (datetime.now() - start_time).total_seconds()
        storm_mark = "👀" if (not storm_triggered and not args.no_storm) else ("⚡" if storm_triggered else "  ")
        saved_mark = "💾" if (step % 1000 == 0 or watchdog_counter >= args.watchdog_window) else ""

        if saved_mark:
            save_checkpoint(step - 1)

        print(f"{step:6} | {total_energy:12.1f} | {min_dist:8.4f} | {storm_mark:>5} | {step_time:8.1f}s | {saved_mark:>5}")

        if watchdog_counter >= args.watchdog_window:
            print(f"\n✅ СТОРОЖ: релаксация стабильна {args.watchdog_window} шагов. Останов.")
            break

        sys.stdout.flush()

    # Финальное сохранение
    save_json(output_traj, all_trajectories)
    save_checkpoint(step - 1)

    print("─" * 75)
    print(f"\n[4/4] ГОТОВО")
    print(f"  Шагов выполнено: {step}")
    print(f"  Сохранено кадров: {len(all_trajectories)}")
    print(f"  Финальная энергия: {energy_history[-1]:.1f}" if energy_history else "  Нет данных")
    print(f"  Финальный d_min: {min_dist_history[-1]:.4f}" if min_dist_history else "  Нет данных")
    print(f"  Траектории: {output_traj}")
    print(f"  Чекпоинт: {output_checkpoint}")

if __name__ == "__main__":
    main()