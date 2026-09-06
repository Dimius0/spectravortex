#!/usr/bin/env python3
"""
🌲 tees_light_scanner.py
Лёгкий сканер без свопа.
Только самое необходимое.
"""

import time
import numpy as np
import threading
import sys
import os
import json
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tees_beacon_tees import Beacon


class LightScanner:
    """Лёгкий сканер — не жрёт память!"""
    
    def __init__(self, beacon, max_freq=5000):
        self.beacon = beacon
        self.max_freq = max_freq
        
        # Только 5 диапазонов, без фанатизма
        self.bands = [
            ('infralow', 0.1, 10, 100, 50),      # 50 сек
            ('low', 10, 100, 1000, 20),          # 20 сек
            ('medium', 100, 1000, 5000, 10),     # 10 сек
            ('high', 1000, 5000, 10000, 5),      # 5 сек
        ]
        
        self.results = []
        
    def scan_band(self, band_name, freq_min, freq_max, sample_rate, duration):
        """Сканирование с поиском ВСЕХ пиков."""
        print(f"\n📡 {band_name}: {freq_min}-{freq_max} Гц")
        print(f"   {sample_rate} Гц, {duration} сек")
        
        max_samples = int(sample_rate * duration)
        samples = np.zeros(max_samples, dtype=np.float64)
        
        start_time = time.time()
        idx = 0
        
        while idx < max_samples and time.time() - start_time < duration + 1:
            samples[idx] = self.beacon.glow
            idx += 1
            
        samples = samples[:idx]
        
        if len(samples) < 100:
            print(f"   ❌ Мало данных: {len(samples)}")
            return
            
        # FFT
        spectrum = np.abs(np.fft.fft(samples)) ** 2
        freqs = np.fft.fftfreq(len(samples), 1.0 / sample_rate)
        
        # Фильтруем диапазон
        mask = (freqs >= freq_min) & (freqs <= freq_max) & (freqs > 0)
        band_freqs = freqs[mask]
        band_spectrum = spectrum[mask]
        
        if len(band_freqs) == 0:
            print(f"   ❌ Нет данных")
            return
            
        # Ищем ВСЕ пики выше порога!
        threshold = np.mean(band_spectrum) + 3 * np.std(band_spectrum)
        
        peaks = []
        for i in range(1, len(band_spectrum) - 1):
            if band_spectrum[i] > threshold:
                # Локальный максимум
                if band_spectrum[i] > band_spectrum[i-1] and band_spectrum[i] > band_spectrum[i+1]:
                    significance = band_spectrum[i] / np.mean(band_spectrum)
                    peaks.append({
                        'frequency': float(band_freqs[i]),
                        'significance': float(significance),
                        'amplitude': float(band_spectrum[i])
                    })
        
        # Сортируем по значимости
        peaks.sort(key=lambda x: x['significance'], reverse=True)
        
        # Выводим ВСЕ найденные пики (до 10)
        print(f"   Найдено пиков: {len(peaks)}")
        for peak in peaks[:10]:
            print(f"     {peak['frequency']:.2f} Гц | {peak['significance']:.1f}x")
        
        # Сохраняем ВСЕ пики в лог
        with open('night_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{time.strftime('%H:%M:%S')} | {band_name}\n")
            for peak in peaks[:10]:
                f.write(f"  {peak['frequency']:.2f} Гц | {peak['significance']:.1f}x\n")
        
        # Сохраняем в результаты
        for peak in peaks[:5]:  # Топ-5 в JSON
            self.results.append({
                'timestamp': float(time.time()),
                'band': str(band_name),
                'frequency': peak['frequency'],
                'significance': peak['significance'],
                'has_signal': bool(peak['significance'] > 3)
            })
    
        # Очищаем память
        del samples, spectrum, freqs, band_freqs, band_spectrum
        
    def scan_cycle(self):
        """Один полный цикл."""
        print(f"\n{'='*50}")
        print(f"🔄 Цикл сканирования ({time.strftime('%H:%M:%S')})")
        print(f"{'='*50}")
        
        for band_name, freq_min, freq_max, sample_rate, duration in self.bands:
            self.scan_band(band_name, freq_min, freq_max, sample_rate, duration)
            
        # Сохраняем JSON каждые 10 циклов
        if len(self.results) % 40 == 0:  # 40 результатов = 10 циклов
            with open('night_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
                
    def run_night(self, hours=8):
        """Ночное сканирование."""
        print(f"🌙 Ночное сканирование: {hours} часов")
        
        start_time = time.time()
        duration_seconds = hours * 3600
        
        cycle_count = 0
        
        while time.time() - start_time < duration_seconds:
            cycle_count += 1
            self.scan_cycle()
            
            # Короткая пауза между циклами
            time.sleep(5)
            
        print(f"\n✅ Завершено! Циклов: {cycle_count}")
        
        # Финальное сохранение
        with open('night_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)


class LightForestScanner:
    """Лёгкий лес."""
    
    def __init__(self, qubits=100):
        self.qubits = qubits
        self.beacon = None
        self.scanner = None
        
    def start(self):
        """Запуск."""
        print(f"🌲 Лёгкий лес-сканер ({self.qubits} агентов)")
        
        self.beacon = Beacon(scroll="light_forest", port=9001, test_mode=True)
        self.beacon.lit = True
        threading.Thread(target=self.beacon._run_p2p, daemon=True).start()
        
        time.sleep(5)
        
        from tees_cluster import TeesCluster
        self.beacon.cluster = TeesCluster(
            beacon=self.beacon,
            qubits_per_core=self.qubits
        )
        
        self.scanner = LightScanner(self.beacon, max_freq=5000)
        print(f"✅ Готов!")
        
    def run_night(self, hours=8):
        """Запуск ночного сканирования."""
        self.scanner.run_night(hours)
        
    def stop(self):
        """Остановка."""
        print(f"\n🛑 Остановка...")
        if self.beacon:
            if hasattr(self.beacon, 'cluster'):
                del self.beacon.cluster
            self.beacon.extinguish()
        print(f"✅ Остановлено")


def main():
    qubits = 100
    hours = 8
    
    if len(sys.argv) > 1:
        try:
            qubits = int(sys.argv[1])
        except:
            pass
            
    if len(sys.argv) > 2:
        try:
            hours = float(sys.argv[2])
        except:
            pass
    
    print("""
    ╔═══════════════════════════════════════╗
    ║    🌙 ЛЁГКИЙ НОЧНОЙ СКАНЕР          ║
    ║    Без свопа, только данные         ║
    ╚═══════════════════════════════════════╝
    """)
    
    forest = LightForestScanner(qubits=qubits)
    
    try:
        forest.start()
        forest.run_night(hours=hours)
    except KeyboardInterrupt:
        print("\n🛑 Прервано")
        # Сохраняем что есть
        if forest.scanner:
            with open('night_results.json', 'w', encoding='utf-8') as f:
                json.dump(forest.scanner.results, f, indent=2)
    finally:
        forest.stop()


if __name__ == "__main__":
    main()