import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# ДАННЫЕ ПО ВСЕМ ГРУППАМ
# ============================================================

# Группа 1: Переходные металлы 4-го периода
group1 = {
    'Ti (Z=22)': {24: 0.0, 25: 0.0, 26: 0.0, 27: 0.0, 28: 0.0},
    'V (Z=23)': {28: 0.0},
    'Cr (Z=24)': {26: 0.0, 28: 0.0, 29: 0.0, 30: 0.0},
    'Mn (Z=25)': {30: 0.0},
    'Fe (Z=26)': {28: 0.0, 30: 0.0, 31: 0.0144, 32: 0.0, 34: 0.0},
}

# Группа 2: Элементы подгруппы титана
group2 = {
    'Ti (Z=22)': {24: 0.0, 25: 0.0, 26: 0.0, 27: 0.0, 28: 0.0},
    'Zr (Z=40)': {50: 0.0, 51: 0.0, 52: 0.0, 54: 0.0, 56: 0.0},
    'Hf (Z=72)': {104: 0.0, 106: 0.0, 108: 0.0, 109: 0.0, 110: 0.0, 111: 0.0, 112: 0.0},
}

# Группа 3: Элементы 5-го периода
group3 = {
    'Mo (Z=42)': {50: 0.0, 52: 0.0, 53: 0.0, 54: 0.0, 55: 0.0, 56: 0.0, 58: 0.0},
    'Ru (Z=44)': {52: 0.0, 54: 0.0, 55: 0.0, 56: 0.0, 57: 0.0, 58: 0.0, 60: 0.0},
    'Rh (Z=45)': {58: 0.0},
    'Pd (Z=46)': {56: 0.0, 58: 0.0, 59: 0.0, 60: 0.0, 62: 0.0, 64: 0.0},
    'Ag (Z=47)': {60: 0.0, 62: 0.0},
}

# Группа 4: Платиноиды
group4 = {
    'Ru (Z=44)': {52: 0.0, 54: 0.0, 55: 0.0, 56: 0.0, 57: 0.0, 58: 0.0, 60: 0.0},
    'Rh (Z=45)': {58: 0.0},
    'Pd (Z=46)': {56: 0.0, 58: 0.0, 59: 0.0, 60: 0.0, 62: 0.0, 64: 0.0},
    'Os (Z=76)': {108: 0.0, 110: 0.0, 111: 0.0, 112: 0.0, 113: 0.0, 114: 0.0, 116: 0.0},
    'Ir (Z=77)': {114: 0.0, 116: 0.0},  # наш "хитрый"
    'Pt (Z=78)': {112: 0.0, 114: 0.0, 116: 0.0, 117: 0.0, 118: 0.0, 120: 0.0},
    'Au (Z=79)': {118: 0.0},
}

# ============================================================
# ФУНКЦИЯ ДЛЯ ПОСТРОЕНИЯ ГРУППЫ
# ============================================================
def plot_group(group_data, group_name, colors, markers, xlim, ylim=( -0.01, 0.1)):
    plt.figure(figsize=(12, 6))
    
    for i, (element, values) in enumerate(group_data.items()):
        N_vals = np.array(sorted(values.keys()))
        E_vals = np.array([values[n] for n in N_vals])
        
        plt.plot(N_vals, E_vals, marker=markers[i % len(markers)], linestyle='-', 
                 linewidth=2, markersize=8, color=colors[i % len(colors)], 
                 label=element, alpha=0.8)
    
    # Магические числа
    magic_N = [20, 28, 40, 50, 82, 126]
    for n in magic_N:
        if xlim[0] <= n <= xlim[1]:
            plt.axvline(x=n, color='gray', linestyle='--', linewidth=1, alpha=0.7)
            plt.text(n, ylim[1]*0.95, f'N={n}', rotation=90, fontsize=9, alpha=0.7)
    
    plt.title(f'Группа {group_name}: энергия первых 0⁺ состояний', fontsize=14, fontweight='bold')
    plt.xlabel('Число нейтронов (N)', fontsize=12)
    plt.ylabel('Энергия E(0⁺₁), МэВ', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='best', fontsize=10)
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.tight_layout()
    plt.savefig(f'group_{group_name.lower().replace(" ", "_")}.png', dpi=150)
    print(f"✅ График группы {group_name} сохранён")

# Цвета и маркеры
colors = ['navy', 'crimson', 'darkorange', 'green', 'purple', 'brown', 'pink']
markers = ['o', 's', '^', 'D', 'v', 'p', '*']

# Строим каждую группу
plot_group(group1, "1 (Ti, V, Cr, Mn, Fe)", colors, markers, (20, 35), ( -0.005, 0.02))
plot_group(group2, "2 (Ti, Zr, Hf)", colors, markers, (20, 120), ( -0.005, 0.02))
plot_group(group3, "3 (Mo, Ru, Rh, Pd, Ag)", colors, markers, (45, 70), ( -0.005, 0.02))
plot_group(group4, "4 (Ru, Rh, Pd, Os, Ir, Pt, Au)", colors, markers, (50, 130), ( -0.005, 0.02))

print("\n✅ Все графики построены!")