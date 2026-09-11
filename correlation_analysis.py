# correlation_analysis.py
import numpy as np

pairs = [
    ('2008_TC3 ↔ 2018_LA', 0.5577, 0.223, 0.099),
    ('2008_TC3 ↔ Chelyabinsk', 0.5925, 0.649, 0.183),
    ('2008_TC3 ↔ Tunguska', 0.5247, 0.545, 0.180),
    ('2018_LA ↔ Chelyabinsk', 0.5684, 0.426, 0.084),
    ('2018_LA ↔ Tunguska', 0.5457, 0.322, 0.081),
    ('Chelyabinsk ↔ Tunguska', 0.5156, 0.104, 0.003),
]

tees = np.array([p[1] for p in pairs])
dT_J = np.array([p[2] for p in pairs])
dT_E = np.array([p[3] for p in pairs])

# Корреляция
r_J = np.corrcoef(tees, dT_J)[0, 1]
r_E = np.corrcoef(tees, dT_E)[0, 1]

print(f"Корреляция TEES vs ΔT_J: {r_J:.4f}")
print(f"Корреляция TEES vs ΔT_E: {r_E:.4f}")

# Антикорреляция (инверсия)
r_J_inv = np.corrcoef(tees, -dT_J)[0, 1]
print(f"\nАнтикорреляция TEES vs -ΔT_J: {r_J_inv:.4f}")