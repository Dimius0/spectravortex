#!/usr/bin/env python3
"""
⚡ tees_burst_logger.py
Логгер всплесков поля H.
Записывает ВСЕ всплески с временными метками.
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


class BurstLogger:
    """Логгер всплесков поля H."""
    
    def __init__(self, qubits=100):
        self.qubits = qubits
        self.beacon = None
        self.bursts = []
        self.running = True
        
    def start(self):
        """Запуск."""
        print(f"⚡ Логгер всплесков ({self.qubits} агентов)")
        
        self.beacon = Beacon(scroll="burst_logger", port=9001, test_mode=True)
        self.beacon.lit = True
        threading.Thread(target=self.beacon._run_p2p, daemon=True).start()
        
        time.sleep(5)
        
        from tees_cluster import TeesCluster
        self.beacon.cluster = TeesCluster(
            beacon=self.beacon,
            qubits_per_core=self.qubits
        )
        
        print(f"✅ Готов!")
        
    def monitor(self, duration=120, label="test"):
        """Мониторинг в течение duration секунд."""
        print(f"\n📡 Мониторинг: {label} ({duration} сек)")
        print(f"   Всплески будут записаны...")
        
        start_time = time.time()
        burst_count = 0
        
        while time.time() - start_time < duration:
            # Быстрый сбор 0.5 сек
            samples = []
            sample_start = time.time()
            while time.time() - sample_start < 0.5:
                samples.append(self.beacon.glow)
                
            if len(samples) < 50:
                continue
                
            # FFT
            spectrum = np.abs(np.fft.fft(samples)) ** 2
            freqs = np.fft.fftfreq(len(samples), 1.0 / (len(samples) / 0.5))
            
            mask = freqs > 0
            freqs = freqs[mask]
            spectrum = spectrum[mask]
            
            # Ищем ВСЕ значимые всплески
            threshold = np.mean(spectrum) * 100  # В 100 раз выше среднего!
            
            for i in range(len(spectrum)):
                if spectrum[i] > threshold:
                    burst = {
                        'timestamp': time.time(),
                        'frequency': float(freqs[i]),
                        'amplitude': float(spectrum[i]),
                        'significance': float(spectrum[i] / np.mean(spectrum)),
                        'label': label
                    }
                    self.bursts.append(burst)
                    burst_count += 1
                    
            # Прогресс
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                print(f"\r   [{elapsed:.0f}/{duration} сек] Всплесков: {burst_count}", end='')
                
        print(f"\n✅ Мониторинг завершён! Всего всплесков: {burst_count}")
        
    def save_results(self, filename="bursts.json"):
        """Сохранение результатов."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.bursts, f, indent=2)
        print(f"💾 Всплески сохранены в {filename}")
        
    def compare(self, silent_bursts, click_bursts):
        """Сравнение двух прогонов."""
        print(f"\n{'='*60}")
        print(f"📊 СРАВНЕНИЕ: ТИШИНА vs ЩЕЛЧКИ")
        print(f"{'='*60}")
        
        # Считаем всплески по частотам
        silent_freqs = {}
        for burst in silent_bursts:
            freq = round(burst['frequency'] / 1000) * 1000  # Группируем по кГц
            silent_freqs[freq] = silent_freqs.get(freq, 0) + 1
            
        click_freqs = {}
        for burst in click_bursts:
            freq = round(burst['frequency'] / 1000) * 1000
            click_freqs[freq] = click_freqs.get(freq, 0) + 1
            
        # Сравнение
        all_freqs = set(silent_freqs.keys()) | set(click_freqs.keys())
        
        print(f"\n{'Частота (Гц)':<15} | {'Тишина':<10} | {'Щелчки':<10} | {'Разница':<10}")
        print(f"{'-'*50}")
        
        for freq in sorted(all_freqs):
            silent_count = silent_freqs.get(freq, 0)
            click_count = click_freqs.get(freq, 0)
            diff = click_count - silent_count
            
            if diff != 0:
                print(f"{freq:<15} | {silent_count:<10} | {click_count:<10} | {diff:+<10}")
                
    def cleanup(self):
        """Очистка."""
        self.running = False
        print(f"\n🛑 Остановка...")
        if self.beacon:
            if hasattr(self.beacon, 'cluster'):
                del self.beacon.cluster
            self.beacon.extinguish()
        print(f"✅ Готово")


def main():
    qubits = 100
    
    if len(sys.argv) > 1:
        try:
            qubits = int(sys.argv[1])
        except:
            pass
    
    print("""
    ╔═══════════════════════════════════════╗
    ║    ⚡ ЛОГГЕР ВСПЛЕСКОВ ПОЛЯ H        ║
    ║    Сравнение: тишина vs щелчки       ║
    ╚═══════════════════════════════════════╝
    """)
    
    logger = BurstLogger(qubits=qubits)
    
    try:
        logger.start()
        
        # Прогон 1: Тишина
        print(f"\n{'='*60}")
        print(f"ЭТАП 1: ТИШИНА (не щёлкай!)")
        print(f"{'='*60}")
        input(f"Нажми Enter для начала...")
        
        logger.monitor(duration=120, label="silent")
        silent_bursts = logger.bursts.copy()
        logger.bursts.clear()
        
        # Пауза
        print(f"\n⏸ Пауза 10 секунд...")
        time.sleep(10)
        
        # Прогон 2: Со щелчками
        print(f"\n{'='*60}")
        print(f"ЭТАП 2: ЩЕЛЧКИ (щёлкай пьезозажигалкой!)")
        print(f"{'='*60}")
        input(f"Нажми Enter и начинай щёлкать...")
        
        logger.monitor(duration=120, label="clicks")
        click_bursts = logger.bursts.copy()
        
        # Сравнение
        logger.compare(silent_bursts, click_bursts)
        
        # Сохранение
        logger.save_results("all_bursts.json")
        
    except KeyboardInterrupt:
        print("\n🛑 Прервано")
    finally:
        logger.cleanup()


if __name__ == "__main__":
    main()