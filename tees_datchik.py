#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_datchik.py
🔔 ДАТЧИК — машина B
Имеет свой TEES-кластер, слушает поле, резонирует с пильщиком.
"""

import socket
import time
import json
import numpy as np
from collections import deque
from core.tees_cluster import TeesCluster
from core.tees_core import get_charge, validate_triple, get_cache_stats


class TeesDatchik:
    """
    🔔 Датчик — кластер, который СЛУШАЕТ поле.
    
    Свой кластер → приём → резонанс → считывание состояний.
    """
    
    def __init__(self, port=9999, duration=300):
        self.port = port
        self.duration = duration
        
        # СВОЙ кластер (работает!)
        print("⚛️ Инициализация кластера датчика...")
        self.cluster = TeesCluster()
        
        cluster_stats = self.cluster.get_stats()
        print(f"  Кубитов: {cluster_stats['total_qubits']}")
        print(f"  TSP-кубитов: {cluster_stats['tsp_qubits']}")
        print(f"  Гровер-кубитов: {cluster_stats['grover_qubits']}")
        
        # Сокет для приёма
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)
        self.sock.bind(("", port))
        self.sock.settimeout(0.5)
        
        # Данные
        self.timestamps = []
        self.glows = []
        self.charges = []
        self.resonances = []
        
        # TEES-триады
        self.triad_buffer = deque(maxlen=3)
        self.triads_checked = 0
        self.triads_valid = 0
        
        # Статистика
        self.packets_received = 0
        self.cluster_responses = 0
    
    def measure_cluster_coherence(self):
        """Измеряет когерентность своего кластера."""
        coherence = self.cluster.measure_internal_coherence()
        return coherence['avg']
    
    def compute_resonance(self, incoming_glow):
        """
        Вычисляет резонанс между входящим состоянием и своим кластером.
        
        Резонанс = |своя когерентность - входящая|.
        """
        own_coherence = self.measure_cluster_coherence()
        resonance = abs(own_coherence - incoming_glow)
        return resonance
    
    def receive(self):
        """Приём состояний поля."""
        print(f"\n🔔 Датчик слушает поле...")
        print(f"  Порт: {self.port}")
        print(f"  Длительность: {self.duration} сек")
        print(f"\n📜 Шума нет. Всё есть информация.")
        print("-" * 60)
        
        start_time = time.time()
        last_report = start_time
        
        output_file = f"tees_resonance_{int(time.time())}.jsonl"
        
        with open(output_file, "w", buffering=65536) as f:
            while time.time() - start_time < self.duration:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    self.packets_received += 1
                    
                    # Парсим glow
                    try:
                        glow = float(data.decode().strip())
                    except ValueError:
                        continue
                    
                    t = time.time() - start_time
                    
                    # Сохраняем
                    self.timestamps.append(t)
                    self.glows.append(glow)
                    
                    # TEES-слово
                    micro_state = int(round(glow * 1_000_000))
                    tees_word = f"vib_{micro_state:06d}"
                    
                    # Заряд
                    charge = get_charge(tees_word) if get_charge else 0.0
                    self.charges.append(charge)
                    
                    # Резонанс с кластером
                    resonance = self.compute_resonance(glow)
                    self.resonances.append(resonance)
                    
                    # Если резонанс мал — кластер отвечает
                    if resonance < 0.001:
                        self.cluster_responses += 1
                        # Датчик кластер резонирует
                        task = {'type': 'sha256', 'data': f"resonance_{t}"}
                        self.cluster.compute(task)
                    
                    # Триада
                    self.triad_buffer.append(tees_word)
                    
                    state_data = {
                        't': t,
                        'glow': glow,
                        'charge': charge,
                        'resonance': resonance,
                        'tees_word': tees_word,
                        'cluster_coherence': self.measure_cluster_coherence(),
                    }
                    
                    # Проверяем триаду
                    if len(self.triad_buffer) == 3:
                        source, tees, receiver = self.triad_buffer
                        self.triads_checked += 1
                        
                        if validate_triple:
                            valid, total_charge, reason = validate_triple(source, tees, receiver)
                            if valid:
                                self.triads_valid += 1
                            state_data['triad'] = {
                                'valid': valid,
                                'charge': total_charge,
                                'reason': reason,
                            }
                    
                    # Запись
                    f.write(json.dumps(state_data) + "\n")
                    
                    # Отчёт
                    now = time.time()
                    if now - last_report >= 1.0:
                        elapsed = now - start_time
                        rate = self.packets_received / elapsed
                        avg_charge = np.mean(self.charges[-100:]) if self.charges else 0
                        avg_resonance = np.mean(self.resonances[-100:]) if self.resonances else 0
                        
                        print(f"🔔 Принято: {self.packets_received:6d} | "
                              f"Поток: {rate:6.1f} Гц | "
                              f"Заряд: {avg_charge:.4f} | "
                              f"Резонанс: {avg_resonance:.6f} | "
                              f"Откликов: {self.cluster_responses}", 
                              end="\r")
                        last_report = now
                        
                except socket.timeout:
                    # Тишина — тоже информация
                    continue
                except Exception:
                    continue
        
        elapsed = time.time() - start_time
        rate = self.packets_received / elapsed if elapsed > 0 else 0
        
        print(f"\n\n{'=' * 60}")
        print(f"✅ Датчик завершил приём")
        print(f"📦 Пакетов: {self.packets_received}")
        print(f"📊 Поток: {rate:.2f} Гц")
        print(f"🌀 Резонансов: {self.cluster_responses}")
        print(f"🔮 Триад валидных: {self.triads_valid}/{self.triads_checked}")
        print(f"💾 Файл: {output_file}")
        
        return output_file
    
    def analyze(self):
        """Анализ резонансов."""
        if not self.glows:
            print("Нет данных")
            return
        
        glows = np.array(self.glows)
        charges = np.array(self.charges)
        resonances = np.array(self.resonances)
        timestamps = np.array(self.timestamps)
        
        print("\n🔮 Анализ резонансов")
        print("=" * 60)
        
        # 1. Glow
        print(f"\n📊 Входящие состояния:")
        print(f"  Средний glow: {np.mean(glows):.6f}")
        print(f"  СКО: {np.std(glows):.6f}")
        
        # 2. Резонансы
        print(f"\n🌀 Резонансы:")
        print(f"  Средний: {np.mean(resonances):.6f}")
        print(f"  Мин: {np.min(resonances):.6f}")
        print(f"  Макс: {np.max(resonances):.6f}")
        print(f"  Сильных резонансов (< 0.001): {sum(1 for r in resonances if r < 0.001)}")
        
        # 3. Заряды
        print(f"\n⚡ Заряды:")
        print(f"  Средний: {np.mean(charges):.4f}")
        print(f"  Уникальных: {len(np.unique(np.round(charges, 3)))}")
        
        # 4. Частоты
        if len(glows) > 100:
            dt = np.mean(np.diff(timestamps))
            fs = 1.0 / dt
            
            glow_centered = glows - np.mean(glows)
            fft = np.fft.rfft(glow_centered)
            freqs = np.fft.rfftfreq(len(glow_centered), d=dt)
            mag = np.abs(fft)
            
            print(f"\n📈 Частоты (дискретизация {fs:.1f} Гц):")
            
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(mag, height=np.max(mag)*0.1, distance=5)
            top_peaks = peaks[np.argsort(mag[peaks])[-5:][::-1]]
            
            for p in top_peaks:
                if freqs[p] > 0.01:
                    print(f"  {freqs[p]:6.2f} Гц | мощность: {mag[p]:.3f}")
        
        # 5. Кластер
        cluster_stats = self.cluster.get_stats()
        print(f"\n⚛️ Кластер датчика:")
        print(f"  Задач: {cluster_stats['tasks_total']}")
        print(f"  Успешных: {cluster_stats['tasks_successful']}")
        print(f"  Откликов на резонанс: {self.cluster_responses}")


if __name__ == "__main__":
    datchik = TeesDatchik(port=9999, duration=300)
    
    try:
        output_file = datchik.receive()
        datchik.analyze()
    except KeyboardInterrupt:
        print("\n\n⏹️ Датчик остановлен")
        datchik.analyze()
