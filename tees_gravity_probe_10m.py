#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_gravity_probe_10m.py
🌀 10 000 000 кубитов.
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
    n_qubits = 10_000_000
    duration = 300

    print(f"🌀 Зонд: {n_qubits:,} кубитов")
    print("=" * 60)

    t0 = time.time()

    depth = 3
    per_layer = n_qubits // depth
    layers = [FractalLayer(per_layer) for _ in range(depth)]

    t1 = time.time()
    print(f"  Создание кубитов: {t1 - t0:.1f} сек")

    readings = deque(maxlen=20000)
    timestamps = deque(maxlen=20000)

    start = time.time()

    while time.time() - start < duration:
        t = time.time() - start

        for layer in layers:
            layer.update()

        avg_coh = sum(L.coherence for L in layers) / len(layers)
        glow = avg_coh + 0.001 * np.sin(2 * np.pi * 16 * t)

        readings.append(glow)
        timestamps.append(t)

        time.sleep(0.005)

    if len(readings) < 100:
        print("  ❌ Мало данных (своп?)")
        return

    dt = np.mean(np.diff(list(timestamps)))
    fs = 1.0 / dt

    signal = np.array(readings) - np.mean(readings)
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), d=dt)
    magnitude = np.abs(spectrum)

    peak_idx = np.argmax(magnitude[1:]) + 1
    peak_freq = freqs[peak_idx]
    peak_power = magnitude[peak_idx]

    print(f"\n📊 Результат:")
    print(f"  Частота дискретизации: {fs:.2f} Гц")
    print(f"  Главная мода: {peak_freq:.2f} Гц")
    print(f"  Мощность: {peak_power:.3f}")


if __name__ == "__main__":
    run_probe()