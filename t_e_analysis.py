# t_e_analysis.py
import numpy as np

events = {
    '2008_TC3': {'a': 1.308, 'e': 0.312, 'i': 2.54},
    '2018_LA': {'a': 1.376, 'e': 0.432, 'i': 4.30},
    'Chelyabinsk': {'a': 1.55, 'e': 0.53, 'i': 3.6},
    'Tunguska': {'a': 1.5, 'e': 0.5, 'i': 10.0},
}

tees_resonances = {
    ('2008_TC3', '2018_LA'): 0.5577,
    ('2008_TC3', 'Chelyabinsk'): 0.5925,
    ('2008_TC3', 'Tunguska'): 0.5247,
    ('2018_LA', 'Chelyabinsk'): 0.5684,
    ('2018_LA', 'Tunguska'): 0.5457,
    ('Chelyabinsk', 'Tunguska'): 0.5156,
}

def tisserand(a, e, i, a_planet):
    """Параметр Тиссерана для планеты."""
    i_rad = np.radians(i)
    return a_planet/a + 2 * np.cos(i_rad) * np.sqrt((a/a_planet) * (1 - e**2))

a_J = 5.204  # Юпитер
a_E = 1.0    # Земля
a_V = 0.723  # Венера

print("="*80)
print("СРАВНЕНИЕ TEES vs T_J, T_E, T_V")
print("="*80)

print(f"\n{'Объект':<15} {'T_J':>8} {'T_E':>8} {'T_V':>8}")
print("-"*80)

for name, orb in events.items():
    T_J = tisserand(orb['a'], orb['e'], orb['i'], a_J)
    T_E = tisserand(orb['a'], orb['e'], orb['i'], a_E)
    T_V = tisserand(orb['a'], orb['e'], orb['i'], a_V)
    print(f"{name:<15} {T_J:>8.3f} {T_E:>8.3f} {T_V:>8.3f}")

print(f"\n{'Пара':<30} {'TEES':>8} {'ΔT_J':>8} {'ΔT_E':>8}")
print("-"*80)

for (n1, n2), res in tees_resonances.items():
    o1, o2 = events[n1], events[n2]
    
    T_J1 = tisserand(o1['a'], o1['e'], o1['i'], a_J)
    T_J2 = tisserand(o2['a'], o2['e'], o2['i'], a_J)
    dT_J = abs(T_J1 - T_J2)
    
    T_E1 = tisserand(o1['a'], o1['e'], o1['i'], a_E)
    T_E2 = tisserand(o2['a'], o2['e'], o2['i'], a_E)
    dT_E = abs(T_E1 - T_E2)
    
    print(f"{n1} ↔ {n2:<15} {res:>8.4f} {dT_J:>8.3f} {dT_E:>8.3f}")