import matplotlib.pyplot as plt
import numpy as np

# Данные: для каждого элемента словарь {число_нейтронов_N: энергия_0+_МэВ}
# Основано на экспериментальных данных и модельных оценках
data = {
    'Ca (Z=20)': {20: 3.35, 22: 1.84, 24: 1.88, 26: 4.76, 28: 4.284},
    'Ni (Z=28)': {28: 0.0, 30: 1.454, 32: 1.332, 34: 1.172, 36: 1.346, 40: 0.0},  # ⁵⁶Ni (N=28), ⁶⁸Ni (N=40)
    'Fe (Z=26)': {28: 0.0, 30: 0.0, 31: 0.0144, 32: 0.0, 34: 0.0, 36: 0.0},
    'Sn (Z=50)': {50: 0.0, 62: 1.2, 64: 1.1, 66: 1.0, 68: 1.1, 70: 1.2, 72: 1.3, 74: 1.4, 76: 1.5, 82: 0.0},
    'Pb (Z=82)': {122: 1.5, 124: 1.4, 126: 0.0, 128: 1.6},
}

plt.figure(figsize=(14, 8))

# Цвета для разных элементов
colors = ['navy', 'crimson', 'darkorange', 'green', 'purple']
markers = ['o', 's', '^', 'D', 'v']

for i, (element, values) in enumerate(data.items()):
    N_vals = np.array(sorted(values.keys()))
    E_vals = np.array([values[n] for n in N_vals])
    plt.plot(N_vals, E_vals, marker=markers[i], linestyle='-', linewidth=2, 
             markersize=6, color=colors[i], label=element, alpha=0.8)

# Вертикальные линии для магических чисел нейтронов
magic_N = [20, 28, 40, 50, 82, 126]
for n in magic_N:
    plt.axvline(x=n, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    plt.text(n, plt.ylim()[1]*0.95, f'N={n}', rotation=90, fontsize=8, alpha=0.6)

plt.title('Энергия первых 0⁺ состояний в зависимости от числа нейтронов', fontsize=16, fontweight='bold')
plt.xlabel('Число нейтронов (N)', fontsize=14)
plt.ylabel('Энергия E(0⁺₁) или аналог, МэВ', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)
plt.xlim(15, 130)
plt.ylim(-0.2, 5)
plt.tight_layout()
plt.savefig('magic_isotopes_comparison.png', dpi=150)
print("✅ Общий график магических классов сохранён: magic_isotopes_comparison.png")
plt.show()