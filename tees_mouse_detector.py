#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_mouse_detector.py — TEES + Mouse Correlation Experiment v1.2
==================================================================
v1.2: Фазовый анализ — каждый замер привязан к состоянию сети.
      Фазы: plateau, synchronizing, furcating, adapting, processing_signal.
      Плюс SystemNoiseFilter и визуализация.

Интегратор: подаёт сигналы от мыши в TEES-сеть и логирует корреляцию
между движением курсора и когерентностью сети.

Запуск:
    python tees_mouse_detector.py

Требуется: pip install pyautogui scipy matplotlib numpy
"""

import os, sys, time, json, logging, random, string, math, queue
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

DATA_DIR = "E:/tees_data"
LOG_FILE = os.path.join(DATA_DIR, "tees_mouse_correlation.log")
os.makedirs(DATA_DIR, exist_ok=True)

from tees_core_4_1 import LivingFieldV3

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    print("⚠️ pyautogui не найден. Установи: pip install pyautogui")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil не найден")

try:
    from scipy.stats import pearsonr
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("⚠️ scipy не найден. Корреляция будет без статистического теста.")

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False
    print("⚠️ matplotlib/numpy не найдены. Визуализация недоступна.")


# ══════════════════════════════════════
# ФИЛЬТР СИСТЕМНОГО ШУМА
# ══════════════════════════════════════
class SystemNoiseFilter:
    """Вычитает системный шум из корреляции."""
    
    def __init__(self):
        self.baseline_noise = deque(maxlen=50)
        self.high_noise_threshold = 0.3  # Выше = "шумный" период
        self._last_disk_bytes = 0
        self._last_disk_time = time.time()
        self._first_call = True
    
    def get_noise_level(self) -> float:
        """0.0 = идеальный покой, 1.0 = максимальный шум."""
        cpu = psutil.cpu_percent(interval=0.1) / 100
        
        try:
            disk = psutil.disk_io_counters()
            current_bytes = disk.read_bytes + disk.write_bytes
            current_time = time.time()
            
            if self._first_call:
                disk_load = 0
                self._first_call = False
            else:
                dt = current_time - self._last_disk_time
                if dt > 0:
                    disk_load = (current_bytes - self._last_disk_bytes) / dt / 1_000_000
                else:
                    disk_load = 0
            
            self._last_disk_bytes = current_bytes
            self._last_disk_time = current_time
        except Exception:
            disk_load = 0
        
        disk_factor = min(1.0, disk_load / 50)
        app_factor = self._active_apps_factor()
        
        noise = cpu * 0.5 + disk_factor * 0.3 + app_factor * 0.2
        self.baseline_noise.append(noise)
        return noise
    
    def _active_apps_factor(self) -> float:
        heavy_apps = 0
        try:
            for proc in psutil.process_iter(['cpu_percent']):
                try:
                    if proc.info['cpu_percent'] and proc.info['cpu_percent'] > 10:
                        heavy_apps += 1
                except Exception:
                    pass
        except Exception:
            pass
        return min(1.0, heavy_apps / 5)
    
    def is_noisy_period(self, noise_level: Optional[float] = None) -> bool:
        if noise_level is None:
            noise_level = self.get_noise_level()
        return noise_level > self.high_noise_threshold
    
    def get_average_noise(self) -> float:
        if not self.baseline_noise:
            return 0.0
        return sum(self.baseline_noise) / len(self.baseline_noise)


# ══════════════════════════════════════
# АНАЛИЗАТОР ФАЗЫ СЕТИ
# ══════════════════════════════════════
class NetworkPhaseDetector:
    """Определяет, в какой фазе находится TEES-сеть в момент замера."""
    
    PHASES = [
        'plateau',           # Когерентность 1.0000, spread 0.0000
        'synchronizing',     # Spread > 0, когерентность растёт
        'furcating',         # Рождаются новые моды
        'adapting',          # Меняются глубина/полосы/эпохи
        'processing_signal', # Только что обработан внешний сигнал
    ]
    
    def __init__(self):
        self.prev_coh = 0.0
        self.prev_spread = 0.0
        self.prev_field_size = 0
        self.prev_depth = 0
        self.prev_bands = 0
        self.signal_just_processed = False
    
    def detect_phase(self, nodes: List[Any], signal_processed_this_cycle: bool) -> str:
        """
        Определяет фазу сети на основе текущего состояния узлов.
        Вызывается при каждом замере.
        """
        cohs = [n.coherence for n in nodes]
        avg_coh = sum(cohs) / len(cohs)
        spread = max(cohs) - min(cohs)
        total_modes = sum(n.field_size for n in nodes)
        
        # Глубина и полосы (берём у первого узла — они синхронизированы)
        depth = nodes[0].furcation_depth if hasattr(nodes[0], 'furcation_depth') else 0
        bands = nodes[0].band_coefficients if hasattr(nodes[0], 'band_coefficients') else 0
        
        # Определяем фазу
        phase = 'plateau'  # По умолчанию
        
        if signal_processed_this_cycle:
            phase = 'processing_signal'
        elif total_modes > self.prev_field_size:
            phase = 'furcating'
            self.prev_field_size = total_modes
        elif abs(avg_coh - self.prev_coh) > 0.001 or spread > 0.001:
            phase = 'synchronizing'
        elif depth != self.prev_depth or bands != self.prev_bands:
            phase = 'adapting'
        
        # Обновляем предыдущие значения
        self.prev_coh = avg_coh
        self.prev_spread = spread
        self.prev_field_size = total_modes
        self.prev_depth = depth
        self.prev_bands = bands
        
        return phase


# ══════════════════════════════════════
# УЗЕЛ С СИГНАЛЬНЫМ ИНТЕРФЕЙСОМ
# ══════════════════════════════════════
class MouseNode(LivingFieldV3):
    """v4.1 с приёмом сигналов мыши."""
    
    def __init__(self, node_id: str, name: str, seed_offset: int = 0, init_coherence: float = 0.993):
        super().__init__(f"node_{node_id}", name)
        self.node_id = node_id
        self._seed_counter = seed_offset
        self._field_state = seed_offset
        self.coherence = init_coherence
        self.coherence_max = 1.0
        
        self.code_hash = "mouse_detector_v1.2"
        self.validated = True
        self.quarantine = False
        self.active = True
        
        self.external_signal_queue = queue.Queue(maxsize=100)
        self.peers: Dict[str, 'MouseNode'] = {}
        self.signals_sent = 0
        self.signals_received = 0
        self.mouse_signals = 0
        self.signal_processed_this_cycle = False  # Флаг для фазового детектора
        self.logger = logging.getLogger(f"Node.{node_id}")
    
    def receive_signal(self, signal: Dict[str, Any]):
        if not self.active: return
        try:
            self.external_signal_queue.put(signal, timeout=0.02)
            self.signals_received += 1
            if signal.get('source') == 'mouse':
                self.mouse_signals += 1
        except queue.Full:
            pass
    
    def broadcast_furcation(self, new_modes: List[Any]):
        if not new_modes or not self.active: return
        signal = {
            'content': json.dumps([{
                'source': getattr(m, 'source', '')[:20],
                'tees': getattr(m, 'tees', '')[:20],
                'amplitude': getattr(m, 'amplitude', 0.5),
                'tau': getattr(m, 'tau', 8.0),
                'quality': getattr(m, 'quality', 0.5),
            } for m in new_modes]),
            'source': self.node_id,
            'coherence': self.coherence,
            'temperature': self.temperature,
            'code_hash': self.code_hash,
            'validated': self.validated,
            'timestamp': time.time(),
        }
        for peer in self.peers.values():
            if peer.active:
                peer.receive_signal(signal)
                self.signals_sent += 1
    
    def furcate(self):
        if not self.active: return []
        new_modes = super().furcate()
        if new_modes: self.broadcast_furcation(new_modes)
        return new_modes
    
    def _process_external_signals(self):
        if not self.active: return
        max_to_process = min(self.external_signal_queue.qsize(), 10)
        processed = 0
        while processed < max_to_process:
            try:
                sig = self.external_signal_queue.get_nowait()
                self.ingest_external_signal(sig)
                processed += 1
                self.signal_processed_this_cycle = True
            except queue.Empty:
                break
    
    def living_cycle(self):
        if not self.active: return
        self.signal_processed_this_cycle = False  # Сбрасываем флаг
        self._process_external_signals()
        self._cycle += 1
        
        if self._cycle % 10 == 0:
            if hasattr(self, '_adapt_precision'): self._adapt_precision()
            if hasattr(self, '_update_emotions'): self._update_emotions()
            if hasattr(self, '_use_comfort_resource'): self._use_comfort_resource()
            if hasattr(self, '_should_bifurcate') and not self._should_bifurcate():
                self.coherence = min(self.coherence_max, self.coherence + 0.0001)
        
        if self._cycle % 20 == 0 and hasattr(self, '_thermal_regulation'):
            self._thermal_regulation()
        if self._cycle % 30 == 0:
            if hasattr(self, '_resolve_dominants'): self._resolve_dominants()
            if hasattr(self, '_update_clusters'): self._update_clusters()
        if self._cycle % 300 == 0 and hasattr(self, '_update_scar_index'):
            self._update_scar_index()
        if hasattr(self, '_should_bifurcate') and self._should_bifurcate() and not self.quarantine:
            self.furcate()
    
    def status_short(self) -> str:
        if not self.active: return f"[{self.node_id}] 💤"
        d = self.hormones.get('dopamine', 0.5)
        q = "🔒" if self.quarantine else "✅"
        return (f"[{self.node_id}] {q} c={self._cycle} m={self.field_size} "
                f"coh={self.coherence:.4f} t={self.temperature:.1f}° "
                f"dop={d:.2f} 🖱️={self.mouse_signals}")


# ══════════════════════════════════════
# ИНТЕГРАТОР TEES + MOUSE v1.2
# ══════════════════════════════════════
class MouseTEES:
    def __init__(self, node_count: int = 10):
        self.logger = self._setup_logger()
        self.running = True
        self.cycle = 0
        self.node_count = node_count
        
        # Создаём узлы
        self.nodes: List[MouseNode] = []
        for i in range(node_count):
            seed_offset = i * 200 + random.randint(0, 100)
            coh = 0.990 + (i % 5) * 0.002
            node = MouseNode(
                node_id=f"N{i:02d}",
                name=f"Mouse-{i}",
                seed_offset=seed_offset,
                init_coherence=coh
            )
            self.nodes.append(node)
        
        # Полный граф
        for node in self.nodes:
            node.peers = {other.node_id: other for other in self.nodes if other != node}
        
        # Мышь
        self.mouse_enabled = HAS_PYAUTOGUI
        if HAS_PYAUTOGUI:
            self.last_x, self.last_y = pyautogui.position()
            self.mouse_history = deque(maxlen=10)
            self.logger.info(f"🖱️ Детектор мыши активирован. Старт: ({self.last_x}, {self.last_y})")
        else:
            self.logger.warning("⚠️ pyautogui не найден.")
        
        # Фильтр шума и фазовый детектор (новое в v1.2)
        self.noise_filter = SystemNoiseFilter() if HAS_PSUTIL else None
        self.phase_detector = NetworkPhaseDetector()
        
        # Лог корреляции
        self.correlation_log = []
        
        self._process = psutil.Process() if HAS_PSUTIL else None
        
        edges = node_count * (node_count - 1)
        self.logger.info(f"🔬 TEES-Mouse Detector v1.2: {node_count} узлов, {edges} рёбер")
        self.logger.info(f"   Фазовый анализ активирован: 5 фаз сети")
        if self.noise_filter:
            self.logger.info(f"   Фильтр системного шума активирован (порог={self.noise_filter.high_noise_threshold})")
    
    def _setup_logger(self):
        logger = logging.getLogger("MouseTEES")
        logger.setLevel(logging.INFO)
        console = logging.StreamHandler(); console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8'); file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(console); logger.addHandler(file_handler)
        return logger
    
    def _get_mouse_signal(self) -> Optional[Dict[str, Any]]:
        if not self.mouse_enabled:
            return None
        
        try:
            x, y = pyautogui.position()
            dx = x - self.last_x
            dy = y - self.last_y
            dist = math.sqrt(dx*dx + dy*dy)
            
            self.mouse_history.append(dist)
            avg_speed = sum(self.mouse_history) / len(self.mouse_history) if self.mouse_history else 0
            
            self.last_x, self.last_y = x, y
            
            if dist > 0 or self.cycle % 10 == 0:
                return {
                    'content': json.dumps({
                        'x': x, 'y': y,
                        'dx': dx, 'dy': dy,
                        'dist': round(dist, 2),
                        'speed': round(avg_speed, 2)
                    }),
                    'source': 'mouse',
                    'timestamp': time.time(),
                }
        except Exception:
            pass
        
        return None
    
    def start(self):
        self.logger.info(f"🚀 Запуск TEES-Mouse Detector v1.2 ({self.node_count} узлов)...")
        self.running = True
        
        while self.running:
            time.sleep(0.5)
            self.cycle += 1
            
            # Сигнал от мыши
            mouse_sig = self._get_mouse_signal()
            if mouse_sig:
                for node in self.nodes:
                    node.receive_signal(mouse_sig)
            
            # Каждый узел делает цикл
            for node in self.nodes:
                node.living_cycle()
            
            # Статус и корреляция каждые 120 циклов
            if self.cycle % 120 == 0:
                self._print_status()
                self._log_correlation()
    
    def stop(self):
        self.running = False
        self.logger.info(f"🛑 Детектор остановлен. Циклов: {self.cycle}")
    
    def _log_correlation(self):
        """Записывает в лог корреляцию + фазу сети."""
        cohs = [n.coherence for n in self.nodes]
        avg_coh = sum(cohs) / len(cohs)
        min_coh = min(cohs)
        max_coh = max(cohs)
        spread = max_coh - min_coh
        
        avg_speed = sum(self.mouse_history) / len(self.mouse_history) if self.mouse_history else 0
        
        noise_level = self.noise_filter.get_noise_level() if self.noise_filter else 0.0
        is_clean = not self.noise_filter.is_noisy_period(noise_level) if self.noise_filter else True
        cpu_percent = psutil.cpu_percent() if HAS_PSUTIL else 0
        
        # ФАЗА СЕТИ (новое в v1.2)
        signal_processed = any(n.signal_processed_this_cycle for n in self.nodes)
        network_phase = self.phase_detector.detect_phase(self.nodes, signal_processed)
        
        entry = {
            'cycle': self.cycle,
            'avg_coherence': round(avg_coh, 4),
            'min_coherence': round(min_coh, 4),
            'max_coherence': round(max_coh, 4),
            'spread': round(spread, 4),
            'mouse_speed': round(avg_speed, 2),
            'mouse_x': self.last_x if self.mouse_enabled else 0,
            'mouse_y': self.last_y if self.mouse_enabled else 0,
            'system_noise': round(noise_level, 3),
            'clean_sample': is_clean,
            'cpu_percent': round(cpu_percent, 1),
            # Новое поле v1.2
            'network_phase': network_phase,
        }
        self.correlation_log.append(entry)
        
        with open(LOG_FILE.replace('.log', '_correlation.json'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def _get_ram(self) -> str:
        if self._process:
            try:
                mb = self._process.memory_info().rss / 1024 / 1024
                return f"{mb:.1f} MB"
            except: pass
        return "?"
    
    def _print_status(self):
        ram = self._get_ram()
        cohs = [n.coherence for n in self.nodes]
        avg_coh = sum(cohs) / len(cohs)
        spread = max(cohs) - min(cohs)
        total_mouse_signals = sum(n.mouse_signals for n in self.nodes)
        
        speed = sum(self.mouse_history) / len(self.mouse_history) if self.mouse_history else 0
        noise = self.noise_filter.get_average_noise() if self.noise_filter else 0.0
        clean_count = sum(1 for e in self.correlation_log if e.get('clean_sample', True))
        
        # Последняя фаза
        last_phase = self.correlation_log[-1]['network_phase'] if self.correlation_log else '?'
        
        print(f"\n{'='*70}")
        print(f"🔬 TEES-Mouse v1.2 — цикл {self.cycle} | RAM: {ram}")
        print(f"   Узлов: {self.node_count} | Когерентность: avg={avg_coh:.4f} spread={spread:.4f}")
        print(f"   🖱️ Мышь: speed={speed:.1f} px/цикл | сигналов: {total_mouse_signals}")
        print(f"   🔇 Шум: {noise:.2f} | Чистых: {clean_count}/{len(self.correlation_log)} | Фаза: {last_phase}")
        print(f"   📊 Корреляция записана: {len(self.correlation_log)} точек")
        
        for node in self.nodes[:3]:
            print(f"   {node.status_short()}")
        if self.node_count > 5:
            print(f"   ... ({self.node_count - 5} узлов) ...")
        for node in self.nodes[-2:]:
            print(f"   {node.status_short()}")
        print(f"{'='*70}")
    
    def analyze_phase_correlation(self):
        """Анализ корреляции отдельно для каждой фазы сети."""
        if not self.correlation_log:
            print("⚠️ Нет данных для анализа")
            return
        
        # Группируем по фазам
        phases_data = {}
        for entry in self.correlation_log:
            phase = entry.get('network_phase', 'unknown')
            if phase not in phases_data:
                phases_data[phase] = {'cohs': [], 'speeds': [], 'spreads': [], 'noises': []}
            phases_data[phase]['cohs'].append(entry['avg_coherence'])
            phases_data[phase]['speeds'].append(entry['mouse_speed'])
            phases_data[phase]['spreads'].append(entry['spread'])
            phases_data[phase]['noises'].append(entry.get('system_noise', 0))
        
        print(f"\n📊 ФАЗОВЫЙ АНАЛИЗ КОРРЕЛЯЦИИ (v1.2):")
        print(f"{'='*70}")
        
        all_cohs = [e['avg_coherence'] for e in self.correlation_log]
        all_speeds = [e['mouse_speed'] for e in self.correlation_log]
        
        if len(all_cohs) >= 5 and HAS_SCIPY:
            r_all, p_all = pearsonr(all_cohs, all_speeds)
            print(f"   Общая корреляция: r = {r_all:.4f}, p = {p_all:.4f}")
        print()
        
        phase_colors = {
            'plateau': '🟢',
            'synchronizing': '🔵',
            'furcating': '🟣',
            'adapting': '🟡',
            'processing_signal': '🔴',
        }
        
        for phase in NetworkPhaseDetector.PHASES:
            if phase not in phases_data:
                continue
            
            data = phases_data[phase]
            cohs = data['cohs']
            speeds = data['speeds']
            n = len(cohs)
            
            icon = phase_colors.get(phase, '⚪')
            print(f"   {icon} Фаза: {phase} ({n} замеров)")
            print(f"      Когерентность: {sum(cohs)/len(cohs):.4f} ± {np.std(cohs):.4f}")
            print(f"      Скорость мыши: {sum(speeds)/len(speeds):.1f} px/цикл")
            
            if n >= 5 and HAS_SCIPY:
                r, p = pearsonr(cohs, speeds)
                significance = "✅ значимо" if p < 0.05 else "📉 не значимо"
                print(f"      Корреляция: r = {r:.4f}, p = {p:.4f} ({significance})")
                
                if abs(r) > 0.7:
                    print(f"      🔥 СИЛЬНАЯ СВЯЗЬ в этой фазе!")
                elif abs(r) > 0.4:
                    print(f"      📈 Умеренная связь.")
                else:
                    print(f"      📉 Слабая связь.")
            elif n >= 3:
                # Ручной расчёт корреляции
                sum_x = sum(cohs)
                sum_y = sum(speeds)
                sum_xy = sum(x*y for x, y in zip(cohs, speeds))
                sum_x2 = sum(x*x for x in cohs)
                sum_y2 = sum(y*y for y in speeds)
                
                numerator = n * sum_xy - sum_x * sum_y
                denominator = math.sqrt((n * sum_x2 - sum_x*sum_x) * (n * sum_y2 - sum_y*sum_y))
                r = numerator / denominator if denominator != 0 else 0
                print(f"      Корреляция: r = {r:.4f} (без стат. теста)")
            else:
                print(f"      ⚠️ Недостаточно данных для корреляции")
            print()
        
        # Визуализация по фазам
        if HAS_PLOT and len(self.correlation_log) >= 5:
            self._plot_phase_correlation(phases_data, all_cohs, all_speeds)
    
    def _plot_phase_correlation(self, phases_data, all_cohs, all_speeds):
        """Визуализация корреляции с раскраской по фазам."""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle('TEES ↔ Mouse Phase Correlation v1.2', fontsize=14, fontweight='bold')
            
            phase_colors_plot = {
                'plateau': 'green',
                'synchronizing': 'blue',
                'furcating': 'purple',
                'adapting': 'orange',
                'processing_signal': 'red',
            }
            
            # График 1: Когерентность vs Скорость с раскраской по фазам
            ax1 = axes[0, 0]
            for phase, data in phases_data.items():
                color = phase_colors_plot.get(phase, 'gray')
                ax1.scatter(data['speeds'], data['cohs'], c=color, alpha=0.6, s=30, label=f"{phase} ({len(data['cohs'])})")
            
            ax1.set_xlabel('Скорость мыши (px/цикл)')
            ax1.set_ylabel('Когерентность TEES')
            ax1.set_title('Когерентность vs Движение (по фазам)')
            ax1.legend(loc='best', fontsize=7)
            ax1.grid(True, alpha=0.3)
            
            # График 2: Распределение фаз во времени
            ax2 = axes[0, 1]
            phases_list = [e.get('network_phase', 'unknown') for e in self.correlation_log]
            cycles = [e['cycle'] for e in self.correlation_log]
            
            # Кодируем фазы числами для графика
            phase_to_num = {p: i for i, p in enumerate(NetworkPhaseDetector.PHASES)}
            phase_nums = [phase_to_num.get(p, -1) for p in phases_list]
            
            ax2.scatter(cycles, phase_nums, c=[phase_colors_plot.get(p, 'gray') for p in phases_list], 
                       s=20, alpha=0.7)
            ax2.set_xlabel('Цикл')
            ax2.set_ylabel('Фаза сети')
            ax2.set_yticks(list(phase_to_num.values()))
            ax2.set_yticklabels(list(phase_to_num.keys()), fontsize=8)
            ax2.set_title('Фазы сети во времени')
            ax2.grid(True, alpha=0.3)
            
            # График 3: Spread vs Скорость по фазам
            ax3 = axes[1, 0]
            for phase, data in phases_data.items():
                color = phase_colors_plot.get(phase, 'gray')
                ax3.scatter(data['speeds'], data['spreads'], c=color, alpha=0.6, s=30, label=f"{phase} ({len(data['cohs'])})")
            
            ax3.set_xlabel('Скорость мыши (px/цикл)')
            ax3.set_ylabel('Разброс когерентности')
            ax3.set_title('Разброс когерентности vs Движение')
            ax3.legend(loc='best', fontsize=7)
            ax3.grid(True, alpha=0.3)
            
            # График 4: Корреляция по фазам (бар-чарт)
            ax4 = axes[1, 1]
            phase_names = []
            phase_r_values = []
            phase_colors_bar = []
            
            for phase in NetworkPhaseDetector.PHASES:
                if phase in phases_data and len(phases_data[phase]['cohs']) >= 5:
                    cohs = phases_data[phase]['cohs']
                    speeds = phases_data[phase]['speeds']
                    if HAS_SCIPY:
                        r, _ = pearsonr(cohs, speeds)
                    else:
                        n = len(cohs)
                        sum_x = sum(cohs)
                        sum_y = sum(speeds)
                        sum_xy = sum(x*y for x, y in zip(cohs, speeds))
                        sum_x2 = sum(x*x for x in cohs)
                        sum_y2 = sum(y*y for y in speeds)
                        numerator = n * sum_xy - sum_x * sum_y
                        denominator = math.sqrt((n * sum_x2 - sum_x*sum_x) * (n * sum_y2 - sum_y*sum_y))
                        r = numerator / denominator if denominator != 0 else 0
                    
                    phase_names.append(phase)
                    phase_r_values.append(r)
                    phase_colors_bar.append(phase_colors_plot.get(phase, 'gray'))
            
            if phase_names:
                bars = ax4.bar(phase_names, phase_r_values, color=phase_colors_bar, alpha=0.7)
                ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
                ax4.set_ylabel('Коэффициент корреляции (r)')
                ax4.set_title('Корреляция по фазам сети')
                ax4.tick_params(axis='x', rotation=45, labelsize=8)
                ax4.grid(True, alpha=0.3)
                
                # Подписываем значения над барами
                for bar, r_val in zip(bars, phase_r_values):
                    ax4.text(bar.get_x() + bar.get_width()/2, 
                            bar.get_height() + (0.02 if r_val >= 0 else -0.08),
                            f'{r_val:.3f}', ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            plot_path = os.path.join(DATA_DIR, 'tees_mouse_phase_correlation.png')
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            print(f"\n📈 График фазовой корреляции сохранён: {plot_path}")
            plt.show()
            
        except Exception as e:
            print(f"\n⚠️ Ошибка при построении графика: {e}")


if __name__ == "__main__":
    detector = MouseTEES(node_count=10)
    try:
        detector.start()
    except KeyboardInterrupt:
        detector.stop()
        detector.analyze_phase_correlation()