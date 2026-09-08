#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_probe_dynamics.py
🌀 Динамика моды во времени.
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


def analyze_window(readings, timestamps):
    if len(readings) < 50:
        return None

    dt = np.mean(np.diff(list(timestamps)))
    fs = 1.0 / dt

    signal = np.array(readings) - np.mean(readings)
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), d=dt)
    magnitude = np.abs(spectrum)

    peak_idx = np.argmax(magnitude[1:]) + 1

    return {
        'fs': fs,
        'peak_freq': freqs[peak_idx],
        'peak_power': magnitude[peak_idx],
    }


def run_probe(use_field=False, duration=300, label=""):
    n_qubits = 45_000_000

    print(f"\n🌀 {label}: 45M кубитов | {'С добавкой' if use_field else 'БЕЗ добавки'}")
    print("=" * 60)

    depth = 3
    per_layer = n_qubits // depth
    layers = [FractalLayer(per_layer) for _ in range(depth)]

    readings = deque(maxlen=20000)
    timestamps = deque(maxlen=20000)

    start = time.time()
    prev_glow = 0.994
    last_report = start

    while time.time() - start < duration:
        t = time.time() - start

        for layer in layers:
            layer.update()

        avg_coh = sum(L.coherence for L in layers) / len(layers)

        glow = avg_coh + 0.001 * np.sin(2 * np.pi * 16 * t)

        if use_field:
            field_factor = 1.0 + min(len(layers), 50) * 0.005
            glow = prev_glow + (glow - prev_glow) * field_factor
            prev_glow = glow

        readings.append(glow)
        timestamps.append(t)

        # Каждые 60 секунд — срез
        if time.time() - last_report >= 60:
            res = analyze_window(readings, timestamps)
            if res:
                print(f"  [{int(time.time()-start):3d}с] "
                      f"fs={res['fs']:.2f} | "
                      f"мода={res['peak_freq']:.2f} Гц | "
                      f"мощность={res['peak_power']:.3f}")
            last_report = time.time()

        time.sleep(0.005)

    print(f"\n✅ Завершено: {label}")


if __name__ == "__main__":
    import sys

    use_field = "--field" in sys.argv
    label = "С ДОБАВКОЙ" if use_field else "БЕЗ ДОБАВКИ"
    run_probe(use_field=use_field, duration=1800, label=label)