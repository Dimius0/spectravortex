#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_gravity_probe_v2.py
🌀 Информационная гравитация — замер сдвига.
Без psutil. Без лишнего. Только поле и частота.
"""

import time
import numpy as np
from collections import deque


class LightQubit:
    """Лёгкий кубит."""
    __slots__ = ('coherence',)

    def __init__(self, coh=0.994):
        self.coherence = coh


class FractalLayer:
    """Фрактальный слой кубитов."""
    def __init__(self, n_qubits):
        self.qubits = [LightQubit() for _ in range(n_qubits)]
        self.coherence = 0.994

    def update(self):
        if not self.qubits:
            return 0.994
        self.coherence = sum(q.coherence for q in self.qubits) / len(self.qubits)
        return self.coherence


def run_probe(n_qubits, duration=8):
    print(f"\n🌀 Зонд: {n_qubits:,} кубитов")
    print("-" * 50)

    # Строим слои
    depth = 3
    per_layer = max(1, n_qubits // depth)
    layers = [FractalLayer(per_layer) for _ in range(depth)]

    # Буферы
    readings = deque(maxlen=3000)
    timestamps = deque(maxlen=3000)

    start = time.time()
    cycle = 0

    while time.time() - start < duration:
        t = time.time() - start

        # Обновляем слои
        for layer in layers:
            layer.update()

        # Общая когерентность
        avg_coh = sum(L.coherence for L in layers) / len(layers)

        # Поле
        glow = avg_coh + 0.001 * np.sin(2 * np.pi * 16 * t)
        readings.append(glow)
        timestamps.append(t)

        cycle += 1
        time.sleep(0.005)

    # Анализ
    if len(readings) < 100:
        print("  Мало данных")
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

    print(f"  Частота дискретизации: {fs:.2f} Гц")
    print(f"  Главная мода: {peak_freq:.2f} Гц")
    print(f"  Мощность: {peak_power:.3f}")
    print(f"  Когерентность: {avg_coh:.6f}")

    return {
        'n_qubits': n_qubits,
        'fs': fs,
        'peak_freq': peak_freq,
        'peak_power': peak_power,
        'coherence': avg_coh,
    }


if __name__ == "__main__":
    print("🌀 Информационная гравитация — зонд")
    print("=" * 60)

    results = []

    for n in [10_000, 50_000, 100_000, 500_000, 1_000_000]:
        try:
            res = run_probe(n, duration=8)
            if res:
                results.append(res)
        except MemoryError:
            print(f"  ❌ Не хватило памяти на {n:,}")
            break

    print("\n" + "=" * 60)
    print("📊 СВОДКА:")
    print(f"  {'Кубитов':>12} | {'Мода':>8} | {'Мощность':>8} | {'Когер.':>8}")
    print("-" * 50)

    for r in results:
        print(f"  {r['n_qubits']:>12,} | "
              f"{r['peak_freq']:>7.2f}Гц | "
              f"{r['peak_power']:>8.3f} | "
              f"{r['coherence']:>8.6f}")