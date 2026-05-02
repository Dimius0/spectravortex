import matplotlib.pyplot as plt
import numpy as np

# ========== ДАННЫЕ ИЗ ЛОГА (пятифазный импульс) ==========
steps = list(range(1052, 1093))
d_shockwave = [5.374]*len(steps)  # d не менялся внутри импульса
e_shockwave = [
    1609457594.6, 1609457594.6, 1609459311.3, 1609459311.3,
    1619836828.0, 1619836828.0, 1619837388.7, 1619837388.7,
    1619829228.3, 1619829228.3, 1619830495.1, 1619830495.1,
    1613462311.2, 1613462311.2, 1613461871.1, 1613461871.1,
    1613460885.3, 1613460885.3, 1613460418.8, 1613460418.8,
    1618759898.4, 1618759898.4, 1618761631.4, 1618761631.4,
    1618498145.5, 1618498145.5, 1618496079.1, 1618496079.1,
    1613462813.3, 1613462813.3, 1613460852.6, 1613460852.6,
    1613466711.0, 1613466711.0, 1613466431.0, 1613466431.0,
    1629559699.1, 1629559699.1, 1629557703.3, 1629557703.3,
    1629291327.6
]

# ========== ПАРАМЕТРЫ ИМПУЛЬСА (P, T) ==========
pulse_P = [
    250, 500, 225, -50, 125, 300, 300, 300, 300, 300, 300,
    240, 180, 120.1, 60.1, 0.1
]
pulse_T = [
    25150, 50000, 40000, 30000, 40000, 50000,
    41000, 32000, 23000, 14000, 5000,
    4060, 3120, 2180, 1240, 300
]
pulse_steps = list(range(1056, 1072))

# ========== ПОСТРОЕНИЕ ==========
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# 1. Импульс (P и T)
color = 'tab:red'
ax1.set_ylabel('P (GPa)', color=color)
ax1.plot(pulse_steps, pulse_P, 'o-', color=color, linewidth=2, markersize=6, label='Давление')
ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax1.fill_between(pulse_steps, 0, pulse_P, alpha=0.15, color=color)
ax1.tick_params(axis='y', labelcolor=color)
ax1.legend(loc='upper left')
ax1.set_title('Пятифазный взрывной импульс: P и T', fontsize=13)
ax1.grid(True, alpha=0.3)

ax1b = ax1.twinx()
color_b = 'tab:orange'
ax1b.set_ylabel('T (K)', color=color_b)
ax1b.plot(pulse_steps, pulse_T, 's--', color=color_b, linewidth=2, markersize=6, label='Температура')
ax1b.tick_params(axis='y', labelcolor=color_b)
ax1b.legend(loc='upper right')

# Аннотации фаз
phases = [
    (1056, 'ДЕТОНАЦИЯ'), (1058, 'ВАКУУМ'), (1060, 'ПОВТ. СЖАТИЕ'),
    (1062, 'ЗАМОРОЗКА'), (1067, 'ОСТЫВАНИЕ')
]
for step, name in phases:
    ax1.axvline(x=step, color='green', linestyle=':', alpha=0.5)
    ax1.text(step, max(pulse_P)*0.9, name, rotation=90, fontsize=8, color='green', va='top')

# 2. Энергия
ax2.plot(steps, [e/1e9 for e in e_shockwave], 'b.-', linewidth=1.5, markersize=4)
ax2.set_ylabel('E (×10⁹)', color='blue')
ax2.tick_params(axis='y', labelcolor='blue')
ax2.set_title('Энергия системы', fontsize=13)
ax2.grid(True, alpha=0.3)

# Отмечаем фазы на графике энергии
for step, name in phases:
    if step in steps:
        idx = steps.index(step)
        ax2.annotate(name, (steps[idx], e_shockwave[idx]/1e9),
                    textcoords="offset points", xytext=(0,15), ha='center',
                    fontsize=7, color='green',
                    arrowprops=dict(arrowstyle="->", color='green', lw=0.8))

# 3. d_min (ступеньки)
ax3.plot(steps, d_shockwave, 'g.-', linewidth=1.5, markersize=4)
ax3.set_ylabel('d_min', color='green')
ax3.set_xlabel('Шаг')
ax3.tick_params(axis='y', labelcolor='green')
ax3.set_title('Ступенька (d_min)', fontsize=13)
ax3.grid(True, alpha=0.3)

# Отмечаем, что d_min не менялся
ax3.annotate('d_min стабилен\n(5.374)', xy=(1060, 5.374), fontsize=10,
            ha='center', color='darkgreen',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))

plt.tight_layout()
plt.savefig('shockwave_analysis.png', dpi=150)
print("График сохранён как shockwave_analysis.png")