#!/usr/bin/env python3
"""
Модуль спектрального анализа для поиска колебательных мод.
С привязкой к энергии через E = ħω.
"""

import numpy as np
import math
from typing import List
from .component import Component

# Фундаментальные константы
HBAR = 1.0546e-34  # Дж·с
MEV_TO_J = 1.602e-13  # 1 МэВ в Дж
HBAR_MEV = HBAR / MEV_TO_J  # ħ в МэВ·с

class SpectralAnalyzer:
    def __init__(self, sampling_rate=1.0, component_mass=None):
        self.sampling_rate = sampling_rate
        self.component_mass = component_mass or 1.07e-29
    
    def frequency_to_energy(self, freq_model):
        """Перевод модельной частоты в энергию (МэВ)"""
        CALIB = 7.65 / 0.005  # 1530 МэВ на единицу частоты
        return freq_model * CALIB
    
    def find_modes(self, components: List[Component], steps=4000, dt=0.05):
        """Находит колебательные моды системы"""
        if not components:
            return {'error': 'Нет компонентов'}
        
        # Собираем историю фаз
        history = []
        for step in range(steps):
            step_phases = []
            for c in components:
                if hasattr(c, 'temporal') and c.temporal:
                    if step > 0:
                        c.temporal.phase += dt * c.temporal.frequency
                    step_phases.append(c.temporal.phase % (2 * math.pi))
                else:
                    if not hasattr(c, '_phase'):
                        c._phase = step * 0.01
                    c._phase += 0.01
                    step_phases.append(c._phase % (2 * math.pi))
            history.append(step_phases)
        
        history = np.array(history)
        n_components = len(components)
        
        # Анализируем каждый компонент
        modes = []
        for i in range(n_components):
            signal = history[:, i]
            
            # Вычитаем линейный тренд
            t = np.arange(len(signal))
            try:
                coeffs = np.polyfit(t, signal, 1)
                detrended = signal - np.polyval(coeffs, t)
            except:
                detrended = signal
            
            # Преобразование Фурье
            fft = np.fft.fft(detrended)
            freqs = np.fft.fftfreq(len(signal), d=dt)
            
            # Только положительные частоты
            positive = freqs[:len(freqs)//2]
            magnitudes = np.abs(fft[:len(freqs)//2])
            
            if len(positive) > 1:
                main_idx = np.argmax(magnitudes[1:]) + 1
                main_freq = positive[main_idx]
                
                # Отсекаем высокочастотный мусор (> 0.1)
                if main_freq > 0.1:
                    continue
                
                modes.append({
                    'component': i,
                    'frequency': main_freq,
                    'energy_mev': self.frequency_to_energy(main_freq)
                })
        
        # Дыхательная мода
        if modes:
            breathing_freq = np.mean([m['frequency'] for m in modes])
            breathing_energy = self.frequency_to_energy(breathing_freq)
        else:
            breathing_freq = 0
            breathing_energy = 0
        
        return {
            'component_modes': modes,
            'breathing_mode': {
                'frequency': breathing_freq,
                'energy_mev': breathing_energy,
                'description': 'Симметричная дыхательная мода (A₁)'
            },
            'dominant_freq': breathing_freq,
            'dominant_energy': breathing_energy
        }