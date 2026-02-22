#!/usr/bin/env python3
"""
Тест для сравнения колебательных мод разных ядер.
Версия 2.2 — с релятивистскими поправками из первых принципов,
деформацией (с правильным знаком из теории жидкой капли)
и адаптивным шагом сетки.
"""

import sys
import os
import math
import numpy as np
from datetime import datetime

# Для красивых таблиц и графиков
try:
    import matplotlib.pyplot as plt
    from tabulate import tabulate
    HAS_PLOTS = True
except ImportError:
    HAS_PLOTS = False
    print("⚠️ Для графиков установи: pip install matplotlib tabulate")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.architect.component import Component
    from src.architect.spectral_analyzer import SpectralAnalyzer
    from src.architect.temporal_state import TemporalState
    print("✅ Импорт модулей")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# ============================================================
# КОНСТАНТЫ И КАЛИБРОВКИ
# ============================================================

CALIB = 7.65 / 0.005  # 1530 МэВ на единицу частоты (из ¹²C)

# ============================================================
# ФИЗИЧЕСКИЕ ПОПРАВКИ (ИЗ ПЕРВЫХ ПРИНЦИПОВ)
# ============================================================

def relativistic_correction(Z):
    """
    Релятивистская поправка из первых принципов.
    γ = 1 + (Zα)²/2, α = 1/137.036
    """
    alpha = 1/137.036
    return 1 + 0.5 * (Z * alpha)**2

def deformation_correction(beta2, mode_type='breathing'):
    """
    Поправка на деформацию ядра.
    beta2: параметр квадрупольной деформации
    mode_type: тип моды ('breathing', 'quadrupole', 'dipole')
    
    Для дыхательной моды из теории жидкой капли:
    ω/ω₀ ≈ 1 - (1/3)β₂²  (частота падает с деформацией)
    """
    if beta2 == 0:
        return 1.0
    
    if mode_type == 'breathing':
        c = -0.33  # минус — деформация затрудняет дыхание
    elif mode_type == 'quadrupole':
        c = 1.5    # плюс — квадрупольные моды растут
    else:
        c = 0.0
    
    return 1.0 + c * beta2**2

# ============================================================
# ДАННЫЕ ПО ЯДРАМ
# ============================================================

NUCLEI = {
    # Лёгкие (Z ≤ 20)
    "¹²C": {
        "name": "Carbon-12",
        "Z": 6,
        "radius_fm": 2.47,
        "beta2": 0.0,
        "color": "blue",
        "modes": [
            {"name": "Хойл", "E_mev": 7.65, "note": "дыхательная"}
        ]
    },
    "¹⁶O": {
        "name": "Oxygen-16",
        "Z": 8,
        "radius_fm": 2.71,
        "beta2": 0.0,
        "color": "cyan",
        "modes": [
            {"name": "0⁺₁", "E_mev": 6.06, "note": "ротационная"},
            {"name": "0⁺₆ (4α)", "E_mev": 12.05, "note": "4α-конденсат"}
        ]
    },
    "⁴⁰Ca": {
        "name": "Calcium-40",
        "Z": 20,
        "radius_fm": 3.48,
        "beta2": 0.0,
        "color": "green",
        "modes": [
            {"name": "0⁺₁", "E_mev": 3.35, "note": "дыхательная"},
            {"name": "0⁺₂", "E_mev": 5.2, "note": "обертон"}
        ]
    },
    "⁴⁸Ca": {
        "name": "Calcium-48",
        "Z": 20,
        "radius_fm": 3.63,
        "beta2": 0.0,
        "color": "lime",
        "modes": [
            {"name": "0⁺₁", "E_mev": 4.284, "note": "дых. 1"},
            {"name": "0⁺₂", "E_mev": 5.461, "note": "дых. 2"},
            {"name": "0⁺₃", "E_mev": 11.945, "note": "дых. 3"},
            {"name": "0⁺₄", "E_mev": 12.318, "note": "дых. 4"},
            {"name": "0⁺₅", "E_mev": 12.565, "note": "дых. 5"},
            {"name": "0⁺₆", "E_mev": 12.869, "note": "дых. 6"}
        ]
    },
    
    # Средние и тяжёлые (Z > 20)
    "⁵⁶Fe": {
        "name": "Iron-56",
        "Z": 26,
        "radius_fm": 4.6,
        "beta2": 0.0,
        "color": "orange",
        "modes": [
            {"name": "0⁺₁", "E_mev": 4.5, "note": "гигантский резонанс?"}
        ]
    },
    "¹³²Sn": {
        "name": "Tin-132",
        "Z": 50,
        "radius_fm": 5.4,
        "beta2": 0.0,
        "color": "red",
        "modes": [
            {"name": "0⁺₁", "E_mev": 4.0, "note": "дважды маг."},
            {"name": "0⁺₂", "E_mev": 5.2, "note": ""}
        ]
    },
    "²⁰⁸Pb": {
        "name": "Lead-208",
        "Z": 82,
        "radius_fm": 7.1,
        "beta2": 0.0,
        "color": "purple",
        "modes": [
            {"name": "0⁺₁", "E_mev": 4.85, "note": "дыхательная"},
            {"name": "0⁺₂", "E_mev": 5.5, "note": "обертон"}
        ]
    },
    "²³⁸U": {
        "name": "Uranium-238",
        "Z": 92,
        "radius_fm": 7.4,
        "beta2": 0.3,  # из таблиц деформации ядер
        "color": "brown",
        "modes": [
            {"name": "0⁺₁", "E_mev": 4.9, "note": "деформационная?"},
            {"name": "0⁺₂", "E_mev": 5.2, "note": ""}
        ]
    }
}

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def create_cluster(n_components, base_freq, charge_per_component=1.0):
    """Создаёт кластер из n компонентов"""
    components = []
    for i in range(n_components):
        comp = Component(id=i, charge=charge_per_component, health=1.0)
        
        # Разные начальные фазы для возбуждения мод
        comp.temporal = TemporalState(
            phase=2 * math.pi * i / max(1, n_components),
            frequency=base_freq,
            amplitude=1.0,
            stability=1.0
        )
        
        # Расставляем по окружности (упрощённо для симметрии)
        angle = 2 * math.pi * i / max(1, n_components)
        r = 1.0
        comp.position = np.array([r * math.cos(angle), r * math.sin(angle), 0])
        
        components.append(comp)
    
    return components

def format_table(data, headers):
    """Форматирует таблицу через tabulate, если есть"""
    if HAS_PLOTS:
        return tabulate(data, headers=headers, tablefmt="grid", floatfmt=".3f")
    else:
        lines = []
        lines.append(" | ".join(headers))
        lines.append("-" * len(lines[0]))
        for row in data:
            lines.append(" | ".join(str(x) for x in row))
        return "\n".join(lines)

# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ АНАЛИЗА
# ============================================================

def analyze_nucleus(nucleus_name, nucleus_data):
    """Анализирует спектр для данного ядра"""
    print(f"\n{'='*70}")
    print(f"🔬 Анализ {nucleus_data['name']} ({nucleus_name})")
    print(f"   Z = {nucleus_data['Z']}, R = {nucleus_data['radius_fm']} фм")
    
    # Релятивистская поправка
    gamma = relativistic_correction(nucleus_data['Z'])
    print(f"   Релятивистская поправка: {gamma:.3f}")
    
    # Поправка на деформацию
    beta2 = nucleus_data.get('beta2', 0)
    deform = deformation_correction(beta2, mode_type='breathing')
    print(f"   Деформация β₂ = {beta2:.2f}, поправка: {deform:.3f}")
    
    # Полная поправка
    total_correction = gamma * deform
    print(f"   Полная поправка: {total_correction:.3f}")
    print(f"{'='*70}")
    
    # Создаём кластер
    n_components = max(4, nucleus_data['Z'] // 2)
    base_freq = nucleus_data['modes'][0]['E_mev'] / (CALIB * total_correction)
    
    components = create_cluster(n_components, base_freq)
    
    # Анализатор
    analyzer = SpectralAnalyzer()
    
    # Подбираем steps для хорошего разрешения
    dt = 0.05
    target_freq = base_freq
    steps_needed = int(1 / (dt * target_freq)) if target_freq > 0 else 4000
    
    # Для тяжёлых ядер (Z > 50) увеличиваем steps в 2 раза для лучшего разрешения
    if nucleus_data['Z'] > 50:
        steps_needed = steps_needed * 2
    
    steps = max(1000, ((steps_needed + 500) // 1000) * 1000)
    
    print(f"\n📊 Параметры анализа:")
    print(f"   Компонентов: {n_components}")
    print(f"   Базовая частота: {base_freq:.6f}")
    print(f"   steps = {steps}, dt = {dt}")
    print(f"   df = {1/(steps*dt):.6f}")
    
    # Запускаем анализ
    result = analyzer.find_modes(components, steps=steps, dt=dt)
    
    # Собираем данные для таблицы
    table_data = []
    for mode in nucleus_data['modes']:
        E_exp = mode['E_mev']
        f_exp = E_exp / (CALIB * total_correction)
        
        # Ищем ближайшую расчётную частоту
        if result['component_modes']:
            freqs = [m['frequency'] for m in result['component_modes']]
            energies = [m['energy_mev'] for m in result['component_modes']]
            
            if freqs:
                idx = np.argmin([abs(f - f_exp) for f in freqs])
                f_calc = freqs[idx]
                E_calc = energies[idx]
                delta_E = E_calc - E_exp
                delta_percent = (delta_E / E_exp) * 100 if E_exp != 0 else 0
            else:
                f_calc = 0
                E_calc = 0
                delta_E = 0
                delta_percent = 0
        else:
            f_calc = 0
            E_calc = 0
            delta_E = 0
            delta_percent = 0
        
        table_data.append([
            mode['name'],
            f"{E_exp:.3f}",
            f"{f_exp:.6f}",
            f"{f_calc:.6f}",
            f"{E_calc:.3f}",
            f"{delta_E:+.3f}",
            f"{delta_percent:+.1f}%",
            mode.get('note', '')
        ])
    
    # Выводим таблицу
    headers = ["Мода", "E_эксп", "f_эксп", "f_расч", "E_расч", "ΔE", "Δ%", "Прим."]
    print("\n📈 Результаты:")
    print(format_table(table_data, headers))
    
    # Дыхательная мода
    breath = result['breathing_mode']
    print(f"\n💨 Дыхательная мода (средняя):")
    print(f"   f = {breath['frequency']:.6f}, E = {breath['energy_mev']:.2f} МэВ")
    
    return {
        'name': nucleus_name,
        'data': nucleus_data,
        'result': result,
        'table': table_data,
        'correction': total_correction
    }

# ============================================================
# ГРАФИКИ
# ============================================================

def plot_results(all_results):
    """Строит графики по результатам"""
    if not HAS_PLOTS:
        print("\n⚠️ Для графиков установи matplotlib и tabulate")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Ядерные колебательные моды в ВММП\n{datetime.now().strftime('%Y-%m-%d %H:%M')}", fontsize=14)
    
    # 1. Энергия мод по ядрам
    ax1 = axes[0, 0]
    x_pos = []
    x_labels = []
    colors = []
    exp_energies = []
    calc_energies = []
    
    for i, (name, res) in enumerate(all_results.items()):
        for mode in res['data']['modes']:
            x_pos.append(len(x_pos))
            x_labels.append(f"{name}\n{mode['name']}")
            colors.append(res['data']['color'])
            exp_energies.append(mode['E_mev'])
            
            # Ищем расчётную
            f_exp = mode['E_mev'] / (CALIB * res['correction'])
            if res['result']['component_modes']:
                freqs = [m['frequency'] for m in res['result']['component_modes']]
                if freqs:
                    idx = np.argmin([abs(f - f_exp) for f in freqs])
                    calc_energies.append(res['result']['component_modes'][idx]['energy_mev'])
                else:
                    calc_energies.append(0)
            else:
                calc_energies.append(0)
    
    width = 0.35
    ax1.bar([p - width/2 for p in x_pos], exp_energies, width, label='Эксперимент', color='navy', alpha=0.7)
    ax1.bar([p + width/2 for p in x_pos], calc_energies, width, label='ВММП', color='crimson', alpha=0.7)
    ax1.set_xlabel('Моды')
    ax1.set_ylabel('Энергия (МэВ)')
    ax1.set_title('Сравнение эксперимента и ВММП')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=8)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Отклонения
    ax2 = axes[0, 1]
    deviations = []
    dev_labels = []
    dev_colors = []
    
    for i, (name, res) in enumerate(all_results.items()):
        for mode, row in zip(res['data']['modes'], res['table']):
            deviations.append(float(row[5]))
            dev_labels.append(f"{name}-{mode['name']}")
            dev_colors.append(res['data']['color'])
    
    bars = ax2.bar(range(len(deviations)), deviations, color=dev_colors, alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.axhline(y=0.5, color='red', linestyle='--', linewidth=0.5, alpha=0.5, label='±0.5 МэВ')
    ax2.axhline(y=-0.5, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.set_xlabel('Моды')
    ax2.set_ylabel('ΔE (МэВ)')
    ax2.set_title('Отклонения ВММП от эксперимента')
    ax2.set_xticks([])
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Зависимость частоты от радиуса
    ax3 = axes[1, 0]
    radii = []
    freqs_exp = []
    z_vals = []
    
    for name, res in all_results.items():
        for mode in res['data']['modes']:
            radii.append(res['data']['radius_fm'])
            f_exp = mode['E_mev'] / (CALIB * res['correction'])
            freqs_exp.append(f_exp)
            z_vals.append(res['data']['Z'])
    
    ax3.scatter(radii, freqs_exp, c=z_vals, cmap='viridis', s=100, alpha=0.7)
    ax3.set_xlabel('Радиус ядра (фм)')
    ax3.set_ylabel('Частота (модельные ед.)')
    ax3.set_title('Зависимость частоты от радиуса')
    ax3.grid(True, alpha=0.3)
    cbar = plt.colorbar(ax3.collections[0], ax=ax3)
    cbar.set_label('Z (заряд ядра)')
    
    # 4. Фрактальное масштабирование
    ax4 = axes[1, 1]
    r0 = NUCLEI["¹²C"]['radius_fm']
    f0 = NUCLEI["¹²C"]['modes'][0]['E_mev'] / (CALIB * all_results["¹²C"]['correction'])
    
    r_ratios = []
    f_ratios = []
    p_values = []
    
    for name, res in all_results.items():
        if name == "¹²C":
            continue
        r_ratio = res['data']['radius_fm'] / r0
        f_ratio = (res['data']['modes'][0]['E_mev'] / (CALIB * res['correction'])) / f0
        p = -math.log(f_ratio) / math.log(r_ratio) if r_ratio != 1 else 0
        
        r_ratios.append(r_ratio)
        f_ratios.append(f_ratio)
        p_values.append(p)
        
        ax4.scatter(r_ratio, f_ratio, s=100, label=f"{name} (p={p:.2f})", alpha=0.7)
    
    if p_values:
        p_avg = np.mean(p_values)
        r_line = np.linspace(min(r_ratios), max(r_ratios), 100)
        f_line = r_line ** (-p_avg)
        ax4.plot(r_line, f_line, 'r--', label=f'f ∼ R⁻{p_avg:.2f}', alpha=0.5)
    
    ax4.set_xlabel('R/R₀')
    ax4.set_ylabel('f/f₀')
    ax4.set_title('Фрактальное масштабирование')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('nuclear_modes_comparison.png', dpi=150)
    print("\n📊 График сохранён: nuclear_modes_comparison.png")
    plt.show()

# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():
    """Главная функция"""
    print("\n" + "="*70)
    print("🧪 ТЕСТ ЯДЕРНЫХ КОЛЕБАТЕЛЬНЫХ МОД v2.2")
    print("="*70)
    print(f"Калибровка: 7.65 МэВ = 0.005 → коэффициент {CALIB:.0f}")
    print(f"Релятивистские поправки: γ = 1 + (Zα)²/2, α = 1/137.036")
    print(f"Поправка на деформацию: ω/ω₀ = 1 - 0.33·β₂² (теория жидкой капли)")
    print("="*70)
    
    # Анализируем все ядра
    all_results = {}
    for name, data in NUCLEI.items():
        all_results[name] = analyze_nucleus(name, data)
    
    # Сводная таблица
    print("\n" + "="*70)
    print("📊 СВОДНАЯ ТАБЛИЦА ПО ВСЕМ ЯДРАМ")
    print("="*70)
    
    all_rows = []
    for name, res in all_results.items():
        for row in res['table']:
            all_rows.append([name] + row)
    
    headers = ["Ядро", "Мода", "E_эксп", "f_эксп", "f_расч", "E_расч", "ΔE", "Δ%", "Прим."]
    print(format_table(all_rows, headers))
    
    # Статистика
    deltas = [float(row[6]) for row in all_rows if row[6] != 'nan']
    if deltas:
        print(f"\n📈 Статистика отклонений:")
        print(f"   Среднее ΔE: {np.mean(deltas):+.3f} МэВ")
        print(f"   Среднее |ΔE|: {np.mean(np.abs(deltas)):.3f} МэВ")
        print(f"   Станд. отклонение: {np.std(deltas):.3f} МэВ")
        print(f"   Макс. отклонение: {np.max(np.abs(deltas)):.3f} МэВ")
    
    # Графики
    plot_results(all_results)
    
    print("\n" + "="*70)
    print("✅ ТЕСТ ЗАВЕРШЁН")
    print("="*70)

if __name__ == "__main__":
    main()