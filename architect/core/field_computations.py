"""
Вычисления с полями.
"""

import numpy as np

def compute_gradient(field):
    """Вычисляет градиент поля."""
    return np.gradient(field)

def compute_energy_density(field, spacing=(1.0, 1.0, 1.0)):
    """Вычисляет плотность энергии."""
    grad = np.gradient(field)
    energy_density = sum(g**2 for g in grad)
    return energy_density
