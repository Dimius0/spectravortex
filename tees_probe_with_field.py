#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_probe_with_field.py
🌀 1M кубитов — С тихой добавкой.
"""

import time
import numpy as np
from collections import deque


class LightQubit:
    __slots__ = ('coherence',)

    def __init__(self, coh=0.994):
        self.coherence = coh


class FractalLayer:
    def __init__(self, n_qubits):
        self.qubits = [LightQubit() for _ in range(n_qubits)]
        self.coherence = 0.994

    def update(self):
        if not self.qubits:
            return 0.994
        self.coherence = sum(q.coherence for q in self.qubits) / len(self.qubits)
        return self.coherence


def run_probe():
    n_qubits = 50_000_000
    duration = 300

    print(f"🌀 50M кубитов — С добавкой")
    print("=" * 60)

    depth = 3
    per_layer = n_qubits // depth
    layers = [FractalLayer(per_layer) for _ in range(depth)]

    readings = deque(maxlen=20000)
    timestamps = deque(maxlen=20000)

    start = time.time()
    prev_glow = 0.994

    while time.time() - start < duration:
        t = time.time() - start

        for layer in layers:
            layer.update()

        avg_coh = sum(L.coherence for L in layers) / len(layers)

        # Тихая добавка — самонаблюдение
        try:
            field_factor = 1.0 + min(len(layers), 50) * 0.005
        except Exception:
            field_factor = 1.0

        # Мягкая поправка
        glow = avg_coh + 0.001 * np.sin(2 * np.pi * 16 * t)
        glow = prev_glow + (glow - prev_glow) * field_factor
        prev_glow = glow

        readings.append(glow)
        timestamps.append(t)

        time.sleep(0.005)

    dt = np.mean(np.diff(list(timestamps)))
    fs = 1.0 / dt

    signal = np.array(readings) - np.mean(readings)
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), d=dt)
    magnitude = np.abs(spectrum)

    peak_idx = np.argmax(magnitude[1:]) + 1

    print(f"\n📊 С добавкой:")
    print(f"  Частота дискретизации: {fs:.2f} Гц")
    print(f"  Главная мода: {freqs[peak_idx]:.2f} Гц")
    print(f"  Мощность: {magnitude[peak_idx]:.3f}")


if __name__ == "__main__":
    run_probe()