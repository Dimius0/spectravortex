#!/usr/bin/env python3
"""
generate_isotope_run.py — конвертер изотопной конфигурации в формат прогона SpectraVortex

Вход:
  - feature/data/isotopes_config.json (изотопы 10 элементов + Mo-Tc-Ru)
  - field_H_elements_complete.json (базовые параметры всех 103 элементов)

Выход:
  - feature/data/isotope_relaxation_frame0.json (начальный кадр для run_3d_table_base.py)

Правила преобразования:
  - Каждый изотоп → отдельный вихрь
  - Базовые параметры (τ, группа, частоты) берутся из field_H_elements_complete.json по Z
  - d_opt из VMMP.d_opt_default[группа]
  - core_radius = d_opt * 0.35, cocoon_radius = d_opt * 0.65
  - Начальные позиции: случайные в simulation box 16x16x16, с лёгким смещением
    для изотопов одного элемента (кучкуются вокруг центра элемента)
  - Нестабильные изотопы (half_life < 1e6 лет) помечаются флагом unstable: true
  - Изобары Mo-Tc-Ru (A=96,98,100) размещаются рядом для проверки правила Маттауха-Щукарева
"""

import json
import random
import math
import os
from typing import Dict, List, Optional, Tuple

# ============ КОНСТАНТЫ ВММП ============
VMMP = {
    "d_opt_default": {1: 0.74, 2: 1.22, 3: 1.52, 4: 1.82, 5: 2.05, 6: 2.20, 7: 2.40},
    "d_env_base": 2.10,
    "group_radius_multipliers": {1: 1.0, 2: 1.2, 3: 1.4, 4: 1.6, 5: 1.8, 6: 2.0, 7: 2.2}
}

# Отображение Z → группа (1-7) по стандартной таблице Менделеева
Z_TO_GROUP = {
    1:1, 2:2,
    3:3, 4:4, 5:5, 6:4, 7:5, 8:6, 9:7, 10:2,
    11:3, 12:4, 13:5, 14:4, 15:5, 16:6, 17:7, 18:2,
    19:3, 20:4, 21:5, 22:4, 23:5, 24:6, 25:7, 26:4, 27:5, 28:6, 29:7, 30:4,
    31:5, 32:4, 33:5, 34:6, 35:7, 36:2,
    37:3, 38:4, 39:5, 40:4, 41:5, 42:6, 43:7, 44:4, 45:5, 46:6, 47:7, 48:4,
    49:5, 50:4, 51:5, 52:6, 53:7, 54:2,
    55:3, 56:4, 57:5, 58:4, 59:5, 60:6, 61:7, 62:4, 63:5, 64:6, 65:7, 66:4,
    67:5, 68:6, 69:7, 70:4, 71:5, 72:4, 73:5, 74:6, 75:7, 76:4, 77:5, 78:6,
    79:7, 80:4, 81:5, 82:6, 83:7, 84:6, 85:7, 86:2,
    87:3, 88:4, 89:5, 90:4, 91:5, 92:6, 93:7, 94:4, 95:5, 96:6, 97:7, 98:4,
    99:5, 100:6, 101:7, 102:4, 103:5, 104:4, 105:5, 106:6, 107:7, 108:4,
    109:5, 110:6, 111:7, 112:4, 113:5, 114:4, 115:5, 116:6, 117:7, 118:2
}

def get_group(z: int) -> int:
    """Определяет номер группы (1-7) по атомному номеру Z"""
    return Z_TO_GROUP.get(z, 4)  # по умолчанию группа 4

def spin_to_tau(spin: float) -> int:
    """Преобразует ядерный спин в топологический заряд τ"""
    if spin == 0.0:
        return 0
    elif abs(spin - 0.5) < 0.01:
        return 1
    elif abs(spin - 1.0) < 0.01:
        return 0
    elif abs(spin - 1.5) < 0.01:
        return -1
    elif abs(spin - 2.0) < 0.01:
        return 0
    elif abs(spin - 2.5) < 0.01:
        return 1
    elif abs(spin - 3.0) < 0.01:
        return 0
    elif abs(spin - 3.5) < 0.01:
        return -1
    elif abs(spin - 4.0) < 0.01:
        return 0
    elif abs(spin - 4.5) < 0.01:
        return 1
    elif abs(spin - 5.0) < 0.01:
        return 0
    elif abs(spin - 5.5) < 0.01:
        return 1
    elif abs(spin - 6.0) < 0.01:
        return 0
    elif abs(spin - 6.5) < 0.01:
        return -1
    elif abs(spin - 7.0) < 0.01:
        return 0
    elif abs(spin - 7.5) < 0.01:
        return -1
    elif abs(spin - 8.0) < 0.01:
        return 0
    elif abs(spin - 8.5) < 0.01:
        return 1
    elif abs(spin - 9.0) < 0.01:
        return 0
    elif abs(spin - 9.5) < 0.01:
        return 1
    else:
        return 0  # неизвестный спин → τ=0

def generate_initial_positions(
    n_vortices: int,
    box_size: float = 16.0,
    element_center: Optional[Tuple[float, float, float]] = None,
    spread: float = 2.0,
    seed: int = 42
) -> List[Tuple[float, float, float]]:
    """
    Генерирует начальные позиции вихрей.
    Если element_center задан — вихри кучкуются вокруг него с разбросом spread.
    Иначе — случайные позиции по всему box.
    """
    random.seed(seed + n_vortices)  # разные seed для разных групп
    positions = []
    
    if element_center is not None:
        cx, cy, cz = element_center
        for _ in range(n_vortices):
            x = cx + random.uniform(-spread, spread)
            y = cy + random.uniform(-spread, spread)
            z = cz + random.uniform(-spread, spread)
            # Не выходим за границы box
            x = max(0.5, min(box_size - 0.5, x))
            y = max(0.5, min(box_size - 0.5, y))
            z = max(0.5, min(box_size - 0.5, z))
            positions.append((x, y, z))
    else:
        for _ in range(n_vortices):
            x = random.uniform(0.5, box_size - 0.5)
            y = random.uniform(0.5, box_size - 0.5)
            z = random.uniform(0.5, box_size - 0.5)
            positions.append((x, y, z))
    
    return positions

def generate_frame0(
    isotopes_config_path: str,
    elements_config_path: str,
    output_path: str,
    box_size: float = 16.0,
    seed: int = 42
) -> Dict:
    """
    Основная функция: читает два JSON, генерирует начальный кадр.
    """
    random.seed(seed)
    
    # Загрузка данных
    with open(isotopes_config_path, 'r', encoding='utf-8') as f:
        isotopes_data = json.load(f)
    
    # Загрузка базовых параметров элементов (если файл существует)
    elements_data = None
    if os.path.exists(elements_config_path):
        with open(elements_config_path, 'r', encoding='utf-8') as f:
            elements_data = json.load(f)
    
    isotopes = isotopes_data.get("isotopes", [])
    
    # Группируем изотопы по элементам (по Z)
    element_groups: Dict[int, List[Dict]] = {}
    for iso in isotopes:
        z = iso["Z"]
        if z not in element_groups:
            element_groups[z] = []
        element_groups[z].append(iso)
    
    # Собираем все элементы, которых ещё нет в isotopes_config, из elements_config
    existing_z = set(element_groups.keys())
    if elements_data:
        for comp in elements_data.get("vortex_components", []):
            z = comp["Z"]
            if z not in existing_z:
                # Добавляем стабильные изотопы этого элемента
                element_groups[z] = []
                for mass_num in comp.get("isotopes", []):
                    # Создаём запись изотопа из данных элемента
                    iso = {
                        "symbol": comp["symbol"],
                        "A": mass_num,
                        "Z": z,
                        "N": mass_num - z,
                        "mass": mass_num,
                        "spin": 0.0,
                        "tau": comp.get("topological_charge", 0) if mass_num == comp.get("isotopes", [mass_num])[0] else 0,
                        "half_life": None,
                        "group": get_group(z)
                    }
                    element_groups[z].append(iso)
                existing_z.add(z)
    
    # Генерируем позиции для центра каждого элемента
    element_centers: Dict[int, Tuple[float, float, float]] = {}
    for z in element_groups:
        cx = random.uniform(1.0, box_size - 1.0)
        cy = random.uniform(1.0, box_size - 1.0)
        cz = random.uniform(1.0, box_size - 1.0)
        element_centers[z] = (cx, cy, cz)
    
    # Специальная обработка для изобар Mo-Tc-Ru (Z=42,43,44)
    # Размещаем их рядом для проверки правила Маттауха-Щукарева
    if 42 in element_groups and 43 in element_groups and 44 in element_groups:
        base_x, base_y, base_z = element_centers.get(42, (8.0, 8.0, 8.0))
        element_centers[42] = (base_x - 0.5, base_y, base_z)
        element_centers[43] = (base_x, base_y, base_z)
        element_centers[44] = (base_x + 0.5, base_y, base_z)
    
    # Строим кадр
    groups = {str(g): [] for g in range(1, 8)}
    tau_map = []
    symbols = []
    radii = []
    
    for z, isos in sorted(element_groups.items()):
        group = get_group(z)
        center = element_centers.get(z, (box_size/2, box_size/2, box_size/2))
        
        # Для стабильных изотопов — компактная кучка, для нестабильных — шире
        stable_isos = [iso for iso in isos if iso.get("half_life") is None]
        unstable_isos = [iso for iso in isos if iso.get("half_life") is not None]
        
        # Сортируем: сначала стабильные, потом нестабильные
        sorted_isos = stable_isos + unstable_isos
        
        n_isos = len(sorted_isos)
        if n_isos == 1:
            positions = [center]
        else:
            spread = 1.0 if n_isos <= 5 else 2.0
            positions = generate_initial_positions(n_isos, box_size, center, spread, seed + z)
        
        for i, iso in enumerate(sorted_isos):
            x, y, z_pos = positions[i] if i < len(positions) else center
            
            # Определяем параметры
            tau = iso.get("tau", 0)
            if tau == 0 and iso.get("spin", 0) != 0:
                tau = spin_to_tau(iso.get("spin", 0))
            
            d_opt = VMMP["d_opt_default"].get(group, 2.0)
            core_radius = d_opt * 0.35
            cocoon_radius = d_opt * 0.65
            
            # Если радиус задан явно — используем его
            if "radius" in iso:
                core_radius = iso["radius"]
            
            # Формируем запись позиции
            pos_entry = {
                "pos": [round(x, 6), round(y, 6), round(z_pos, 6)],
                "tau": tau,
                "symbol": iso["symbol"],
                "radius": round(core_radius, 4)
            }
            
            # Добавляем информацию о нестабильности
            half_life = iso.get("half_life")
            if half_life is not None:
                pos_entry["half_life"] = half_life
                pos_entry["unstable"] = True
            
            groups[str(group)].append(pos_entry)
            tau_map.append(tau)
            symbols.append(iso["symbol"])
            radii.append(round(core_radius, 4))
    
    # Вычисляем d_min для кадра 0 (приблизительно)
    all_positions = []
    for g in range(1, 8):
        for entry in groups[str(g)]:
            all_positions.append(entry["pos"])
    
    d_min = None
    if len(all_positions) >= 2:
        min_dist = float('inf')
        for i in range(len(all_positions)):
            for j in range(i+1, len(all_positions)):
                dx = all_positions[i][0] - all_positions[j][0]
                dy = all_positions[i][1] - all_positions[j][1]
                dz = all_positions[i][2] - all_positions[j][2]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                if dist < min_dist:
                    min_dist = dist
        d_min = round(min_dist, 4)
    
    # Собираем выходной кадр
    frame = {
        "step": 0,
        "d_min": d_min,
        "groups": groups,
        "tau_map": tau_map,
        "symbols": symbols,
        "radii": radii
    }
    
    # Сохраняем
    output = [frame]  # массив кадров, совместимый с плеером
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Статистика
    total_vortices = sum(len(v) for v in groups.values())
    print(f"Сгенерирован кадр 0: {total_vortices} вихрей")
    print(f"  d_min = {d_min}")
    for g in range(1, 8):
        n = len(groups[str(g)])
        if n > 0:
            syms = set(entry["symbol"] for entry in groups[str(g)])
            print(f"  Группа {g}: {n} вихрей, элементы: {sorted(syms)}")
    
    return frame

if __name__ == "__main__":
    # Пути к файлам
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir) if "feature" in script_dir else script_dir
    
    isotopes_path = os.path.join(repo_root, "feature", "data", "isotopes_config.json")
    elements_path = os.path.join(repo_root, "field_H_elements_complete.json")
    output_path = os.path.join(repo_root, "feature", "data", "isotope_relaxation_frame0.json")
    
    # Если isotopes_config.json не в feature/data, ищем в корне
    if not os.path.exists(isotopes_path):
        isotopes_path = os.path.join(repo_root, "isotopes_config.json")
    if not os.path.exists(elements_path):
        elements_path = os.path.join(repo_root, "data", "field_H_elements_complete.json")
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Изотопы: {isotopes_path}")
    print(f"Элементы: {elements_path}")
    print(f"Выход: {output_path}")
    print()
    
    try:
        frame = generate_frame0(isotopes_path, elements_path, output_path)
        print(f"\nФайл сохранён: {output_path}")
        print("Готово. Можно загружать в плеер или передавать в run_3d_table_base.py")
    except FileNotFoundError as e:
        print(f"Ошибка: файл не найден — {e}")
    except Exception as e:
        print(f"Ошибка: {e}")