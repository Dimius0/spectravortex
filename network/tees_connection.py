#!/usr/bin/env python3
"""
🔗 TEES Connection Module
Установление и поддержание связи между маяками.
Этапы:
1. Поиск частоты (16 Гц)
2. PLL синхронизация
3. Достижение когерентности
4. Поддержание связи
"""

import time
import numpy as np
import threading
import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

@dataclass
class ConnectionStatus:
    """Статус соединения."""
    connected: bool
    channel: float
    frequency_coherence: float
    amplitude_coherence: float
    total_coherence: float
    sync_time: float
    last_update: float


class PLL:
    """Phase-Locked Loop для частотной синхронизации."""
    
    def __init__(self, target_freq=16.0, sample_rate=100):
        self.target_freq = target_freq
        self.sample_rate = sample_rate
        self.current_phase = 0.0
        self.phase_error = 0.0
        
        # Параметры PLL
        self.loop_bandwidth = 0.1
        self.vco_gain = 1.0
        self.loop_filter = 0.01
        
        # История для когерентности
        self.history = []
        self.max_history = 100
        self.coherence = 0.0
        
    def update(self, input_signal):
        """
        Обновление PLL.
        Возвращает текущую фазу.
        """
        # Опорный сигнал
        reference = np.sin(2 * np.pi * self.target_freq * time.time() + self.current_phase)
        
        # Ошибка фазы
        phase_error = input_signal * reference
        
        # Фильтр
        self.phase_error = self.phase_error * (1 - self.loop_filter) + phase_error * self.loop_filter
        
        # Обновление фазы (плавное!)
        self.current_phase += self.vco_gain * self.phase_error
        
        # Нормализация фазы
        self.current_phase = self.current_phase % (2 * np.pi)
        
        # Оценка когерентности
        self._update_coherence(input_signal, reference)
        
        return self.current_phase
    
    def _update_coherence(self, input_signal, reference):
        """Оценка когерентности через корреляцию."""
        self.history.append((input_signal, reference))
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        if len(self.history) >= 10:
            inputs = np.array([h[0] for h in self.history])
            references = np.array([h[1] for h in self.history])
            
            correlation = np.corrcoef(inputs, references)[0, 1]
            self.coherence = abs(correlation)
    
    def get_coherence(self):
        """Текущая когерентность PLL."""
        return self.coherence


class FrequencyScanner:
    """Сканер частот для поиска канала связи."""
    
    def __init__(self, beacon):
        self.beacon = beacon
        self.found_frequencies = []
        self.scan_count = 0
        
    def scan_band(self, freq_min, freq_max, duration=10, sample_rate=100):
        """Сканирование частотного диапазона."""
        samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            samples.append(self.beacon.glow)
            time.sleep(1.0 / sample_rate)
        
        if len(samples) < 100:
            return []
        
        # FFT
        spectrum = np.abs(np.fft.fft(samples)) ** 2
        freqs = np.fft.fftfreq(len(samples), 1.0 / sample_rate)
        
        # Фильтрация
        mask = (freqs >= freq_min) & (freqs <= freq_max) & (freqs > 0)
        band_freqs = freqs[mask]
        band_spectrum = spectrum[mask]
        
        if len(band_freqs) == 0:
            return []
        
        # Нормализация
        if np.max(band_spectrum) > 0:
            spectrum_norm = band_spectrum / np.max(band_spectrum)
        else:
            spectrum_norm = band_spectrum
        
        # Поиск пиков
        percentile_80 = np.percentile(spectrum_norm, 80)
        signals = []
        
        for i in range(1, len(band_spectrum) - 1):
            if spectrum_norm[i] > percentile_80:
                if spectrum_norm[i] > spectrum_norm[i-1] and spectrum_norm[i] > spectrum_norm[i+1]:
                    significance = band_spectrum[i] / np.mean(band_spectrum) if np.mean(band_spectrum) > 0 else 0
                    signals.append({
                        'frequency': float(band_freqs[i]),
                        'significance': float(significance)
                    })
        
        signals.sort(key=lambda x: x['significance'], reverse=True)
        return signals
    
    def find_frequency(self, target_freq=16.0, tolerance=0.5, max_time=600):
        """Поиск целевой частоты."""
        print(f"\n📡 Поиск частоты {target_freq} Гц...")
        
        start_time = time.time()
        found = []
        
        while time.time() - start_time < max_time:
            self.scan_count += 1
            elapsed = time.time() - start_time
            
            # Оптимальные параметры для поиска
            sample_rate = 100
            duration = 10
            freq_min = target_freq - 5
            freq_max = target_freq + 5
            
            signals = self.scan_band(freq_min, freq_max, duration, sample_rate)
            
            if signals:
                print(f"\n[{elapsed:.0f} сек] Скан {self.scan_count}:")
                for sig in signals[:5]:
                    print(f"  {sig['frequency']:8.2f} Гц | {sig['significance']:.1f}x")
                
                # Ищем целевую частоту
                for sig in signals:
                    if abs(sig['frequency'] - target_freq) <= tolerance:
                        found.append(sig['frequency'])
                        
                        if len(found) >= 3:
                            avg_freq = np.mean(found)
                            std_freq = np.std(found)
                            
                            print(f"\n🎯 Частота найдена!")
                            print(f"   Среднее: {avg_freq:.2f} Гц")
                            print(f"   Std: {std_freq:.3f} Гц")
                            
                            return avg_freq
            
            time.sleep(2)
        
        print(f"\n❌ Частота {target_freq} Гц не найдена")
        return None


class TEESConnection:
    """
    🔗 Модуль связи TEES.
    Устанавливает и поддерживает связь между маяками.
    """
    
    def __init__(self, beacon, target_freq=16.0):
        self.beacon = beacon
        self.target_freq = target_freq
        
        # Компоненты
        self.scanner = FrequencyScanner(beacon)
        self.pll = None
        
        # Состояние
        self.channel = None
        self.connected = False
        self.sync_time = None
        self.frequency_coherence = 0.0
        
        # Поток поддержания связи
        self.maintenance_thread = None
        self.maintenance_active = False
        
    def establish(self, max_time=600):
        """
        Установление связи.
        1. Поиск частоты
        2. PLL синхронизация
        3. Достижение когерентности
        """
        print(f"\n🔗 Установление связи...")
        
        # Этап 1: Поиск частоты
        self.channel = self.scanner.find_frequency(
            target_freq=self.target_freq,
            max_time=max_time
        )
        
        if not self.channel:
            return False
        
        # Этап 2: PLL синхронизация
        print(f"\n🔄 PLL синхронизация на {self.channel:.2f} Гц...")
        self.pll = PLL(target_freq=self.channel)
        
        start_time = time.time()
        max_coherence = 0.0
        
        while time.time() - start_time < 60:  # 60 секунд на синхронизацию
            signal = self.beacon.glow
            phase = self.pll.update(signal)
            
            self.frequency_coherence = self.pll.get_coherence()
            
            if self.frequency_coherence > max_coherence:
                max_coherence = self.frequency_coherence
            
            if self.frequency_coherence > 0.8:
                print(f"\n✅ PLL синхронизирован!")
                print(f"   Когерентность: {self.frequency_coherence:.4f}")
                break
            
            time.sleep(0.01)
        
        if self.frequency_coherence < 0.8:
            print(f"\n⚠️ PLL синхронизация слабая: {self.frequency_coherence:.4f}")
        
        # Этап 3: Подключение
        self.connected = True
        self.sync_time = time.time()
        
        print(f"\n🔗 Связь установлена!")
        print(f"   Канал: {self.channel:.2f} Гц")
        print(f"   Частотная когерентность: {self.frequency_coherence:.4f}")
        print(f"   Амплитудная когерентность: {self.beacon.glow:.4f}")
        
        return True
    
    def start_maintenance(self):
        """Запуск поддержания связи."""
        if not self.connected:
            return
        
        self.maintenance_active = True
        
        def maintenance_loop():
            while self.maintenance_active and self.connected:
                # Обновление PLL
                signal = self.beacon.glow
                self.pll.update(signal)
                
                self.frequency_coherence = self.pll.get_coherence()
                
                # Если когерентность упала — переподключение
                if self.frequency_coherence < 0.5:
                    print(f"\n⚠️ Потеря когерентности! Переподключение...")
                    self.connected = False
                    self.establish(max_time=60)
                
                time.sleep(0.1)
        
        self.maintenance_thread = threading.Thread(target=maintenance_loop, daemon=True)
        self.maintenance_thread.start()
        
        print(f"\n🔄 Поддержание связи запущено")
    
    def stop_maintenance(self):
        """Остановка поддержания."""
        self.maintenance_active = False
        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=2)
    
    def get_status(self):
        """Статус соединения."""
        total_coherence = self.frequency_coherence * self.beacon.glow
        
        return ConnectionStatus(
            connected=self.connected,
            channel=self.channel or 0.0,
            frequency_coherence=self.frequency_coherence,
            amplitude_coherence=self.beacon.glow,
            total_coherence=total_coherence,
            sync_time=self.sync_time or 0.0,
            last_update=time.time()
        )
    
    def transmit(self, data):
        """Передача данных по установленному каналу."""
        if not self.connected:
            return False
        
        # Кодирование в сигнал
        encoded = self._encode(data)
        
        # Передача
        for bit in encoded:
            if bit:
                self.beacon.glow = 0.995
            else:
                self.beacon.glow = 0.994
            time.sleep(0.01)
        
        return True
    
    def receive(self, duration=5):
        """Приём данных."""
        if not self.connected:
            return None
        
        bits = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if self.beacon.glow > 0.9945:
                bits.append(1)
            else:
                bits.append(0)
            time.sleep(0.01)
        
        return self._decode(bits)
    
    def _encode(self, data):
        """Кодирование данных в биты."""
        bits = []
        for char in str(data):
            binary = format(ord(char), '08b')
            for bit in binary:
                bits.append(int(bit))
        return bits
    
    def _decode(self, bits):
        """Декодирование битов в данные."""
        if not bits:
            return None
        
        chars = []
        for i in range(0, len(bits) - 7, 8):
            byte = ''.join(str(b) for b in bits[i:i+8])
            try:
                char = chr(int(byte, 2))
                if char.isprintable():
                    chars.append(char)
            except:
                pass
        
        return ''.join(chars) if chars else None


# Тестовый запуск
if __name__ == "__main__":
    print("🔗 TEES Connection Module")
    print("   Импортируйте в свой код:")
    print("   from tees_connection import TEESConnection")