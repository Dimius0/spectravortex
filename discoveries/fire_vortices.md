import matplotlib.pyplot as plt
import numpy as np

# Данные: для каждого элемента словарь {число_нейтронов_N: энергия_0+_МэВ}
# Данные приблизительные, для демонстрации подхода, требуют уточнения по NNDC!
data = {
    'Ca (Z=20)': {20: 3.35, 22: 1.84, 24: 1.88, 26: 4.76, 28: 4.284},
    'Ni (Z=28)': {30: 1.454, 32: 1.332, 34: 1.172, 36: 1.346},  # Данные по 2⁺, для примера
    'Fe (Z=26)': {28: 0.0, 30: 0.0, 31: 0.0144, 32: 0.0, 34: 0.0}, # ⁵⁷Fe имеет очень низкое возбуждение
    'Sn (Z=50)': {62: 1.2, 64: 1.1, 66: 1.0, 68: 1.1, 70: 1.2, 72: 1.3, 74: 1.4, 76: 1.5}, # Условные данные
    'Pb (Z=82)': {122: 1.5, 124: 1.4, 126: 0.0, 128: 1.6}, # ²⁰⁸Pb (N=126) - основное состояние
}

plt.figure(figsize=(12, 7))

for element, values in data.items():
    N_vals = np.array(sorted(values.keys()))
    E_vals = np.array([values[n] for n in N_vals])
    plt.plot(N_vals, E_vals, 'o-', linewidth=2, markersize=6, label=element)

# Вертикальные линии для магических чисел нейтронов
magic_N = [20, 28, 40, 50, 82, 126]
for n in magic_N:
    plt.axvline(x=n, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)

plt.title('Энергия первых 0⁺ состояний в зависимости от числа нейтронов', fontsize=14)
plt.xlabel('Число нейтронов (N)', fontsize=12)
plt.ylabel('Энергия E(0⁺₁) или аналог, МэВ', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()
plt.xlim(15, 130)
plt.ylim(-0.5, 5)
plt.tight_layout()
plt.savefig('magic_isotopes_comparison.png', dpi=150)
print("✅ Общий график сохранён: magic_isotopes_comparison.png")
plt.show()