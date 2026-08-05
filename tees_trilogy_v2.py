#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_trilogy_v2.py — TEES Trilogy v2.0: Чистый импорт v4.1
============================================================
Три сущности v4.1, импортированные из tees_core_4_1 (переименован).
Только сигнальный интерфейс добавлен. Никаких изменений в механизм фуркаций.
Разные внешние сигналы: A — частые слабые, B — тишина, C — редкие мощные.
"""

import os, sys, time, json, queue, logging, random, string
from datetime import datetime
from typing import Dict, List, Optional, Any

# ══════════════════════════════════════
# КОНФИГУРАЦИЯ
# ══════════════════════════════════════
DATA_DIR = "E:/tees_data"
LOG_FILE = os.path.join(DATA_DIR, "tees_trilogy_v2.log")
os.makedirs(DATA_DIR, exist_ok=True)

# Импортируем v4.1 из переименованного файла
from tees_core_4_1 import LivingFieldV3

# psutil для мониторинга RAM
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ══════════════════════════════════════
# ГЕНЕРАТОРЫ ВНЕШНИХ СИГНАЛОВ
# ══════════════════════════════════════
class SignalGenerator:
    """Генерирует внешние сигналы для сущности."""
    
    def __init__(self, id: str, mode: str = "silent"):
        self.id = id
        self.mode = mode
    
    def generate(self, cycle: int) -> Optional[Dict[str, Any]]:
        if self.mode == "frequent_weak":
            if cycle % 10 == 0:
                length = random.randint(50, 200)
                text = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
                if random.random() > 0.5:
                    text += " хорош отличн класс супер люблю " * random.randint(0, 2)
                else:
                    text += " плох ужасн грустн печальн " * random.randint(0, 1)
                return {
                    'content': text,
                    'source': f'external_{self.id}',
                    'timestamp': time.time(),
                }
        
        elif self.mode == "silent":
            return None
        
        elif self.mode == "rare_strong":
            if cycle % 500 == 0 and cycle > 0:
                text = " плох ужасн ненавиж грустн печальн зл обид " * 50
                text += ''.join(random.choices(string.ascii_letters + string.digits, k=200))
                return {
                    'content': text,
                    'source': f'external_{self.id}',
                    'timestamp': time.time(),
                }
        
        return None


# ══════════════════════════════════════
# УЗЕЛ ТРИЛОГИ (v4.1 + сигнальный интерфейс)
# ══════════════════════════════════════
class TrilogyNode(LivingFieldV3):
    """v4.1 с сигнальным интерфейсом для трилоги."""
    
    def __init__(self, id: str, name: str, seed_offset: int = 0, init_coherence: float = 0.993):
        # Вызываем родительский конструктор
        super().__init__(id, name)
        
        # Переопределяем начальные параметры для разнообразия
        self._seed_counter = seed_offset
        self._field_state = seed_offset
        self.coherence = init_coherence
        
        # Сигнальный интерфейс
        self.external_signal_queue = queue.Queue(maxsize=100)
        self.signal_priority_queue: List[Dict] = []
        self.signal_history: List[Dict] = []
        
        # Соседи по трилоге
        self.peers: Dict[str, 'TrilogyNode'] = {}
        
        # Свой логгер
        self.logger = logging.getLogger(f"Node.{id}")
    
    def receive_signal(self, signal: Dict[str, Any]):
        """Принять сигнал от другой сущности."""
        try:
            self.external_signal_queue.put(signal, timeout=0.05)
        except queue.Full:
            pass
    
    def broadcast_furcation(self, new_modes: List[Any]):
        """Разослать результат фуркации всем соседям."""
        if not new_modes or not self.peers:
            return
        
        signal = {
            'content': json.dumps([{
                'source': getattr(m, 'source', '')[:20],
                'tees': getattr(m, 'tees', '')[:20],
                'amplitude': getattr(m, 'amplitude', 0.5),
                'tau': getattr(m, 'tau', 8.0),
                'quality': getattr(m, 'quality', 0.5),
            } for m in new_modes]),
            'source': self.id,
            'coherence': self.coherence,
            'temperature': self.temperature,
            'timestamp': time.time(),
        }
        for peer in self.peers.values():
            peer.receive_signal(signal)
    
    def furcate(self):
        """Переопределяем furcate, чтобы добавить broadcast."""
        new_modes = super().furcate()
        if new_modes:
            self.broadcast_furcation(new_modes)
        return new_modes
    
    def _process_external_signals(self):
        """Обработка внешних сигналов через существующий ingest_external_signal."""
        max_to_process = min(self.external_signal_queue.qsize(), 20)
        processed = 0
        while processed < max_to_process:
            try:
                sig = self.external_signal_queue.get_nowait()
                # Используем родительский метод для обработки
                self.ingest_external_signal(sig)
                processed += 1
            except queue.Empty:
                break
    
    def living_cycle(self):
        """Один цикл жизни с обработкой внешних сигналов."""
        self._process_external_signals()
        
        self._cycle += 1
        
        if self._cycle % 10 == 0:
            if hasattr(self, '_adapt_precision'):
                self._adapt_precision()
            if hasattr(self, '_update_emotions'):
                self._update_emotions()
            if hasattr(self, '_use_comfort_resource'):
                self._use_comfort_resource()
            if hasattr(self, '_should_bifurcate') and not self._should_bifurcate():
                self.coherence = min(0.998, self.coherence + 0.0001)
        
        if self._cycle % 20 == 0 and hasattr(self, '_thermal_regulation'):
            self._thermal_regulation()
        
        if self._cycle % 30 == 0:
            if hasattr(self, '_resolve_dominants'):
                self._resolve_dominants()
            if hasattr(self, '_update_clusters'):
                self._update_clusters()
        
        if self._cycle % 300 == 0 and hasattr(self, '_update_scar_index'):
            self._update_scar_index()
        
        if hasattr(self, '_should_bifurcate') and self._should_bifurcate():
            self.furcate()
    
    def status_line(self) -> str:
        d = self.hormones.get('dopamine', 0.5)
        c = self.hormones.get('cortisol', 0.3)
        emoji = "😊" if d > 0.6 else ("😐" if d > 0.4 else "😟")
        return (f"[{self.id}] цикл={self._cycle} мод={self.field_size} "
                f"coh={self.coherence:.4f} t={self.temperature:.1f}°[{self._thermal_mode}] "
                f"dop={d:.2f}{emoji} cort={c:.2f} dom={self.active_dominant_count} "
                f"🩸{self.erythro_index:.0%} дар={self.erythro['donation_deaths']}")


# ══════════════════════════════════════
# ЯДРО ТРИЛОГИ v2.0
# ══════════════════════════════════════
class TrilogyCore:
    """Управляет тремя v4.1 с перекрёстными сигналами."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.running = True
        self.cycle = 0
        
        # Три сущности на базе v4.1 со сдвигом по фазе
        self.A = TrilogyNode("A", "Альфа", seed_offset=0, init_coherence=0.990)
        self.B = TrilogyNode("B", "Бета", seed_offset=1000, init_coherence=0.993)
        self.C = TrilogyNode("C", "Гамма", seed_offset=5000, init_coherence=0.996)
        
        # Генераторы внешних сигналов
        self.gen_A = SignalGenerator("A", "frequent_weak")
        self.gen_B = SignalGenerator("B", "silent")
        self.gen_C = SignalGenerator("C", "rare_strong")
        
        # Полный граф
        self.A.peers = {"B": self.B, "C": self.C}
        self.B.peers = {"A": self.A, "C": self.C}
        self.C.peers = {"A": self.A, "B": self.B}
        
        # Мониторинг памяти
        self._process = psutil.Process() if HAS_PSUTIL else None
        
        self.logger.info("🔺 TEES Trilogy v2.0 инициализирована (чистый импорт v4.1)")
        self.logger.info(f"   A↔B, B↔C, C↔A — полный граф, без иерархии")
        self.logger.info(f"   A: частые слабые | B: тишина | C: редкие мощные")
        self.logger.info(f"   Сдвиг по фазе: A(seed=0, coh=0.990) B(seed=1000, coh=0.993) C(seed=5000, coh=0.996)")
    
    def _setup_logger(self):
        logger = logging.getLogger("TrilogyCore")
        logger.setLevel(logging.INFO)
        console = logging.StreamHandler(); console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8'); file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)-12s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(console); logger.addHandler(file_handler)
        return logger
    
    def _get_ram(self) -> str:
        if self._process:
            try:
                mb = self._process.memory_info().rss / 1024 / 1024
                return f"{mb:.1f} MB"
            except: pass
        return "?"
    
    def start(self):
        self.logger.info("🚀 Запуск трилоги v2.0...")
        self.running = True
        while self.running:
            time.sleep(0.5)
            self.cycle += 1
            
            # Генерируем внешние сигналы
            sig_A = self.gen_A.generate(self.cycle)
            sig_B = self.gen_B.generate(self.cycle)
            sig_C = self.gen_C.generate(self.cycle)
            
            # Впрыскиваем внешние сигналы напрямую в очередь
            if sig_A: self.A.receive_signal(sig_A)
            if sig_B: self.B.receive_signal(sig_B)
            if sig_C: self.C.receive_signal(sig_C)
            
            # Каждая сущность делает свой цикл
            self.A.living_cycle()
            self.B.living_cycle()
            self.C.living_cycle()
            
            if self.cycle % 120 == 0:
                self._print_status()
    
    def stop(self):
        self.running = False
        self.logger.info("🛑 Трилога остановлена")
    
    def _print_status(self):
        ram = self._get_ram()
        print(f"\n{'='*60}")
        print(f"🔺 Трилога v2.0 — цикл {self.cycle} | RAM: {ram}")
        print(f"   [A] частые сл. {self.A.status_line()}")
        print(f"   [B] тишина    {self.B.status_line()}")
        print(f"   [C] редк. мощ. {self.C.status_line()}")
        cohs = [self.A.coherence, self.B.coherence, self.C.coherence]
        corts = [self.A.hormones.get('cortisol', 0), self.B.hormones.get('cortisol', 0), self.C.hormones.get('cortisol', 0)]
        temps = [self.A.temperature, self.B.temperature, self.C.temperature]
        print(f"   📊 Разброс: coh={max(cohs)-min(cohs):.4f} cort={max(corts)-min(corts):.2f} t={max(temps)-min(temps):.1f}°")
        print(f"{'='*60}")


# ══════════════════════════════════════
# ТОЧКА ВХОДА
# ══════════════════════════════════════
if __name__ == "__main__":
    trilogy = TrilogyCore()
    try:
        trilogy.start()
    except KeyboardInterrupt:
        trilogy.stop()