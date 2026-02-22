import matplotlib.pyplot as plt
import numpy as np

# Данные: N (число нейтронов) и E_exp (МэВ)
data = {
    20: 3.35,  # 40Ca
    22: 1.84,  # 42Ca
    24: 1.88,  # 44Ca
    26: 4.76,  # 46Ca
    28: 4.284, # 48Ca
}

N_vals = np.array(sorted(data.keys()))
E_exp = np.array([data[n] for n in N_vals])

# Построение графика
plt.figure(figsize=(10, 6))
plt.plot(N_vals, E_exp, 'o-', color='navy', linewidth=2, markersize=8, label='Эксперимент')

# Оформление
plt.title('Энергия первого 0⁺ состояния в изотопах кальция', fontsize=14)
plt.xlabel('Число нейтронов N', fontsize=12)
plt.ylabel('Энергия E(0⁺₁), МэВ', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()
plt.xticks(N_vals)
plt.xlim(18, 30)

# Добавим подписи точек
for i, txt in enumerate(E_exp):
    plt.annotate(f'{E_exp[i]:.2f}', (N_vals[i], E_exp[i]), textcoords="offset points", xytext=(0,10), ha='center')

plt.tight_layout()
plt.savefig('ca_isotopes_comparison.png', dpi=150)
print("✅ График сохранён: ca_isotopes_comparison.png")
plt.show()