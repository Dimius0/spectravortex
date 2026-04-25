"""
Вычисление электроотрицательности χ из первых принципов ВММП
на основе эталонной 3D-структуры.
С учётом Z-зависимого оптимального расстояния d_opt(Z).
"""

import json
import numpy as np
from math import sqrt

# ========== КОНСТАНТЫ ==========
k = 0.0608               # нормировочный коэффициент (калибровка по H)
alpha = 0.01             # константа спиновой связи
max_neighbor_dist = 5.0  # радиус поиска соседей

# Табличные значения Полинга для сравнения
CHI_PAULING = {
    1: 2.20, 2: 0.00, 3: 0.98, 4: 1.57, 5: 2.04, 6: 2.55, 7: 3.04, 8: 3.44, 9: 3.98, 10: 0.00,
    11: 0.93, 12: 1.31, 13: 1.61, 14: 1.90, 15: 2.19, 16: 2.58, 17: 3.16, 18: 0.00,
    19: 0.82, 20: 1.00,
    21: 1.36, 22: 1.54, 23: 1.63, 24: 1.66, 25: 1.55, 26: 1.83, 27: 1.88, 28: 1.91, 29: 1.90, 30: 1.65,
    31: 1.81, 32: 2.01, 33: 2.18, 34: 2.55, 35: 2.96, 36: 0.00,
    37: 0.82, 38: 0.95, 39: 1.22, 40: 1.33, 41: 1.60, 42: 2.16, 43: 1.90, 44: 2.20, 45: 2.28, 46: 2.20,
    47: 1.93, 48: 1.69, 49: 1.78, 50: 1.96, 51: 2.05, 52: 2.10, 53: 2.66, 54: 0.00,
    55: 0.79, 56: 0.89, 57: 1.10, 72: 1.30, 73: 1.50, 74: 2.36, 75: 1.90, 76: 2.20, 77: 2.20, 78: 2.28,
    79: 2.54, 80: 2.00, 81: 1.80, 82: 2.33, 83: 2.02, 84: 2.00, 85: 2.20, 86: 0.00,
    87: 0.70, 88: 0.90, 89: 1.10, 90: 1.30, 91: 1.50, 92: 1.38, 93: 1.36, 94: 1.28, 95: 1.30, 96: 1.30,
    97: 1.30, 98: 1.30, 99: 1.30, 100: 1.30, 101: 1.30, 102: 1.30, 103: 1.30
}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def zeta(Z):
    """Длина когерентности (фм)"""
    return 1.4 * (1 + 10/(Z+2))**(-1)

def spin(Z):
    """Упрощённый спин ядра: 1/2 для нечётных Z, 0 для чётных"""
    return 0.5 if Z % 2 == 1 else 0.0

def distance(p1, p2):
    """Евклидово расстояние между двумя точками"""
    return sqrt(sum((a-b)**2 for a, b in zip(p1, p2)))

def d_opt(Z):
    """
    Оптимальное расстояние для элемента Z.
    Для стабильных (Z ≤ 20): d_opt = 2.76
    Для остальных: линейно растёт с Z из-за нейтронного скина и кулоновского отталкивания
    """
    if Z <= 20:
        return 2.76
    else:
        # Калибровка по нашим данным: U (Z=92) имеет d_opt ≈ 3.85
        return 2.76 + 0.015 * (Z - 20)

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========

def compute_delta_omega(element, all_elements):
    """
    Вычислить Δω/ω₀ для элемента на основе его окружения.
    Δω/ω₀ = Σ ( (d - d_opt(Z))/d_opt(Z) )² · (Z_neighbor / Z)
    """
    Z = element['Z']
    pos = element['position']
    d_opt_Z = d_opt(Z)
    
    delta = 0.0
    neighbors_found = 0
    
    for other in all_elements:
        if other['symbol'] == element['symbol']:
            continue
        d = distance(pos, other['position'])
        if d < max_neighbor_dist:
            Z_other = other['Z']
            # Отклонение от оптимального расстояния
            deviation = (d - d_opt_Z) / d_opt_Z
            delta += deviation**2 * (Z_other / Z)
            neighbors_found += 1
    
    # Если соседей нет (например, для изолированного элемента), возвращаем 0
    if neighbors_found == 0:
        return 0.0
    
    return delta

def compute_chi(element, all_elements):
    """
    Вычислить χ для элемента по формуле ВММП:
    χ = k · (Δω/ω₀) · Z / ζ(Z)² · (1 + α·S²)
    """
    Z = element['Z']
    delta_omega = compute_delta_omega(element, all_elements)
    
    # Формула ВММП
    chi = k * delta_omega * Z / (zeta(Z)**2) * (1 + alpha * spin(Z)**2)
    
    return chi, delta_omega

def analyze_stability(element, all_elements):
    """
    Анализ стабильности элемента на основе его Δω.
    Возвращает: статус, Δω, порог нестабильности
    """
    Z = element['Z']
    delta_omega = compute_delta_omega(element, all_elements)
    
    # Порог нестабильности зависит от Z
    threshold = 0.05 + 0.002 * (Z - 20) if Z > 20 else 0.05
    
    if delta_omega < threshold:
        status = "СТАБИЛЕН"
    elif delta_omega < 2 * threshold:
        status = "МЕТАСТАБИЛЕН"
    else:
        status = "НЕСТАБИЛЕН (радиоактивен)"
    
    return {
        'status': status,
        'delta_omega': delta_omega,
        'threshold': threshold,
        'd_opt': d_opt(Z)
    }

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========

def main():
    print("=" * 70)
    print("ВЫЧИСЛЕНИЕ ЭЛЕКТРООТРИЦАТЕЛЬНОСТИ ИЗ ПЕРВЫХ ПРИНЦИПОВ ВММП")
    print("=" * 70)
    
    # Загружаем эталонную структуру
    input_file = 'periodic_table_model/results/autosave_T300.0_P0.1_128_local_final.json'
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: файл {input_file} не найден.")
        print("Попробуем найти другой финальный файл...")
        import glob
        files = glob.glob('periodic_table_model/results/*final*.json')
        if files:
            input_file = files[0]
            print(f"Используем: {input_file}")
            with open(input_file, 'r') as f:
                data = json.load(f)
        else:
            print("Финальный файл не найден.")
            return
    
    elements = data['elements']
    
    # Конвертируем позиции в float
    for e in elements:
        e['position'] = [float(x) for x in e['position']]
    
    print(f"\nЗагружено элементов: {len(elements)}")
    print(f"Источник: {input_file}")
    
    # Вычисляем χ для всех элементов
    results = []
    stability_results = []
    
    for e in elements:
        chi_vmms, delta_omega = compute_chi(e, elements)
        stability = analyze_stability(e, elements)
        
        results.append({
            'symbol': e['symbol'],
            'Z': e['Z'],
            'chi_vmms': round(chi_vmms, 3),
            'delta_omega': round(delta_omega, 6),
            'd_opt': round(d_opt(e['Z']), 2)
        })
        
        stability_results.append({
            'symbol': e['symbol'],
            'Z': e['Z'],
            **stability
        })
    
    # Сортируем по Z
    results.sort(key=lambda x: x['Z'])
    stability_results.sort(key=lambda x: x['Z'])
    
    # ========== ВЫВОД РЕЗУЛЬТАТОВ ==========
    
    print("\n" + "=" * 90)
    print("ВЫЧИСЛЕННЫЕ ЗНАЧЕНИЯ ЭЛЕКТРООТРИЦАТЕЛЬНОСТИ (ВММП)")
    print("=" * 90)
    print(f"{'Z':>3} | {'Сим':>4} | {'χ_vmms':>8} | {'χ_Пол':>8} | {'Δχ':>8} | {'Δω/ω₀':>10} | {'d_opt':>6}")
    print("-" * 90)
    
    chi_pauling_list = []
    chi_vmms_list = []
    
    for r in results:
        Z = r['Z']
        chi_p = CHI_PAULING.get(Z, None)
        chi_v = r['chi_vmms']
        
        if chi_p is not None:
            delta_chi = chi_v - chi_p
            chi_str = f"{chi_p:.3f}"
            delta_str = f"{delta_chi:+.3f}"
            chi_pauling_list.append(chi_p)
            chi_vmms_list.append(chi_v)
        else:
            chi_str = "—"
            delta_str = "—"
        
        print(f"{Z:3} | {r['symbol']:>4} | {chi_v:8.3f} | {chi_str:>8} | {delta_str:>8} | {r['delta_omega']:10.6f} | {r['d_opt']:6.2f}")
    
    print("-" * 90)
    
    # Статистика совпадения
    if chi_pauling_list:
        correlation = np.corrcoef(chi_vmms_list, chi_pauling_list)[0, 1]
        mae = np.mean(np.abs(np.array(chi_vmms_list) - np.array(chi_pauling_list)))
        print(f"\nСТАТИСТИКА СОВПАДЕНИЯ С ПОЛИНГОМ:")
        print(f"  Корреляция R²: {correlation**2:.4f}")
        print(f"  Средняя абсолютная ошибка: {mae:.4f}")
    
    # ========== АНАЛИЗ СТАБИЛЬНОСТИ ==========
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ СТАБИЛЬНОСТИ ЭЛЕМЕНТОВ")
    print("=" * 80)
    print(f"{'Z':>3} | {'Сим':>4} | {'Δω/ω₀':>10} | {'Порог':>8} | {'Статус':>25} | {'d_opt':>6}")
    print("-" * 80)
    
    stable_count = 0
    meta_count = 0
    unstable_count = 0
    
    for s in stability_results:
        if "СТАБИЛЕН" in s['status']:
            stable_count += 1
        elif "МЕТА" in s['status']:
            meta_count += 1
        else:
            unstable_count += 1
        
        print(f"{s['Z']:3} | {s['symbol']:>4} | {s['delta_omega']:10.6f} | {s['threshold']:8.4f} | {s['status']:>25} | {s['d_opt']:6.2f}")
    
    print("-" * 80)
    print(f"\nСТАТИСТИКА СТАБИЛЬНОСТИ:")
    print(f"  Стабильных: {stable_count}")
    print(f"  Метастабильных: {meta_count}")
    print(f"  Нестабильных (радиоактивных): {unstable_count}")
    
    # ========== СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ==========
    
    output = {
        'metadata': {
            'description': 'Electronegativity computed from VMMS first principles',
            'source_file': input_file,
            'formula': 'χ = k · (Δω/ω₀) · Z/ζ(Z)² · (1 + α·S²)',
            'd_opt_formula': 'd_opt(Z) = 2.76 for Z≤20, else 2.76 + 0.015·(Z-20)'
        },
        'results': results,
        'stability_analysis': stability_results,
        'statistics': {
            'correlation_R2': correlation**2 if chi_pauling_list else None,
            'mean_absolute_error': mae if chi_pauling_list else None,
            'stable_count': stable_count,
            'metastable_count': meta_count,
            'unstable_count': unstable_count
        }
    }
    
    output_file = 'periodic_table_model/results/chi_vmms_computed.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Результаты сохранены: {output_file}")
    print("=" * 90)

if __name__ == "__main__":
    main()