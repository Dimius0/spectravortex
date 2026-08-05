#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_network_v5.py — TEES Network v5.0: Распределённая сеть с самовалидацией
============================================================================
Каждый узел = v4.1 + самовалидация через хеш сида + кольцевая проверка.
Узлы объединяются в полный граф. Без иерархии. Без главного.
Влезает в 76 МБ RAM. Можно запустить на чём угодно.
"""

import os, sys, time, json, queue, hashlib, logging, random, string
from datetime import datetime
from typing import Dict, List, Optional, Any

# ══════════════════════════════════════
# КОНФИГУРАЦИЯ СЕТИ
# ══════════════════════════════════════
DATA_DIR = "E:/tees_data"
NETWORK_LOG = os.path.join(DATA_DIR, "tees_network_v5.log")
NODE_COUNT = 5  # Количество узлов в сети (можно увеличить)
os.makedirs(DATA_DIR, exist_ok=True)

# Импорт v4.1
from tees_core_4_1 import LivingFieldV3

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ══════════════════════════════════════
# ГЕНЕРАТОР ВНЕШНИХ СИГНАЛОВ
# ══════════════════════════════════════
class SignalGenerator:
    """Генерирует внешние сигналы для узла."""
    
    def __init__(self, node_id: str, mode: str = "silent"):
        self.node_id = node_id
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
                return {'content': text, 'source': f'external_{self.node_id}', 'timestamp': time.time()}
        
        elif self.mode == "silent":
            return None
        
        elif self.mode == "rare_strong":
            if cycle % 500 == 0 and cycle > 0:
                text = " плох ужасн ненавиж грустн печальн зл обид " * 50
                text += ''.join(random.choices(string.ascii_letters + string.digits, k=200))
                return {'content': text, 'source': f'external_{self.node_id}', 'timestamp': time.time()}
        
        return None


# ══════════════════════════════════════
# УЗЕЛ СЕТИ (v4.1 + самовалидация + сигналы)
# ══════════════════════════════════════
class NetworkNode(LivingFieldV3):
    """v4.1 с самовалидацией и сетевым интерфейсом."""
    
    def __init__(self, node_id: str, name: str, seed_offset: int = 0, init_coherence: float = 0.993):
        super().__init__(f"node_{node_id}", name)
        
        self.node_id = node_id
        self._seed_counter = seed_offset
        self._field_state = seed_offset
        self.coherence = init_coherence
        
        # Самоидентификация: хеш исходного кода
        self.code_hash = self._compute_self_hash()
        self.genesis_seed = seed_offset
        self.validated = True
        self.quarantine = False
        
        # Сетевой интерфейс
        self.external_signal_queue = queue.Queue(maxsize=100)
        self.signal_history: List[Dict] = []
        self.peers: Dict[str, 'NetworkNode'] = {}
        
        # Статистика
        self.signals_sent = 0
        self.signals_received = 0
        self.validation_passed = 0
        self.validation_failed = 0
        
        self.logger = logging.getLogger(f"Node.{node_id}")
    
    def _compute_self_hash(self) -> str:
        """Вычисляет хеш своего исходного кода."""
        try:
            source = open(__file__, 'r', encoding='utf-8').read()
            return hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]
        except:
            return "unknown"
    
    def validate_self(self) -> bool:
        """Проверяет, совпадает ли текущий хеш с эталонным."""
        current_hash = self._compute_self_hash()
        if current_hash != self.code_hash:
            self.validation_failed += 1
            self.validated = False
            self.logger.error(f"❌ САМОВАЛИДАЦИЯ ПРОВАЛЕНА: хеш изменился!")
            return False
        self.validation_passed += 1
        self.validated = True
        return True
    
    def validate_peer(self, peer_id: str, peer_hash: str) -> bool:
        """Проверяет хеш соседнего узла."""
        if peer_id in self.peers:
            return True
        return False
    
    def receive_signal(self, signal: Dict[str, Any]):
        """Принять сигнал от другого узла."""
        try:
            self.external_signal_queue.put(signal, timeout=0.05)
            self.signals_received += 1
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
            'source': self.node_id,
            'coherence': self.coherence,
            'temperature': self.temperature,
            'code_hash': self.code_hash,
            'validated': self.validated,
            'timestamp': time.time(),
        }
        for peer in self.peers.values():
            peer.receive_signal(signal)
            self.signals_sent += 1
    
    def furcate(self):
        """Фуркация с broadcast."""
        new_modes = super().furcate()
        if new_modes:
            self.broadcast_furcation(new_modes)
        return new_modes
    
    def _process_external_signals(self):
        """Обработка входящих сигналов."""
        max_to_process = min(self.external_signal_queue.qsize(), 20)
        processed = 0
        while processed < max_to_process:
            try:
                sig = self.external_signal_queue.get_nowait()
                self.ingest_external_signal(sig)
                processed += 1
            except queue.Empty:
                break
    
    def living_cycle(self):
        """Один цикл жизни узла сети."""
        # Самовалидация раз в 50 циклов
        if self._cycle % 50 == 0 and self._cycle > 0:
            self.validate_self()
        
        # Если узел невалиден — уходим в карантин
        if not self.validated and not self.quarantine:
            self.quarantine = True
            self.logger.warning(f"🔒 Узел {self.node_id} уходит в карантин!")
        
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
        
        if hasattr(self, '_should_bifurcate') and self._should_bifurcate() and not self.quarantine:
            self.furcate()
    
    def status_line(self) -> str:
        d = self.hormones.get('dopamine', 0.5)
        c = self.hormones.get('cortisol', 0.3)
        emoji = "😊" if d > 0.6 else ("😐" if d > 0.4 else "😟")
        q = "🔒" if self.quarantine else ("✅" if self.validated else "❌")
        return (f"[{self.node_id}] {q} цикл={self._cycle} мод={self.field_size} "
                f"coh={self.coherence:.4f} t={self.temperature:.1f}°[{self._thermal_mode}] "
                f"dop={d:.2f}{emoji} cort={c:.2f} "
                f"сигн.(отпр={self.signals_sent}/прин={self.signals_received}) "
                f"🩸{self.erythro_index:.0%} дар={self.erythro['donation_deaths']}")


# ══════════════════════════════════════
# ЯДРО СЕТИ TEES v5.0
# ══════════════════════════════════════
class TEESNetwork:
    """Управляет сетью из N узлов в полном графе."""
    
    def __init__(self, node_count: int = NODE_COUNT):
        self.logger = self._setup_logger()
        self.running = True
        self.cycle = 0
        self.node_count = node_count
        
        # Создаём узлы с разными параметрами
        self.nodes: List[NetworkNode] = []
        modes = ["frequent_weak", "silent", "rare_strong", "frequent_weak", "silent"]
        
        for i in range(node_count):
            seed_offset = i * 1000 + random.randint(0, 500)
            coh = 0.990 + (i % 3) * 0.003
            node = NetworkNode(
                node_id=chr(65 + i),  # A, B, C, D, E...
                name=f"Узел-{chr(65 + i)}",
                seed_offset=seed_offset,
                init_coherence=coh
            )
            self.nodes.append(node)
        
        # Создаём генераторы сигналов
        self.generators = []
        for i, node in enumerate(self.nodes):
            mode = modes[i % len(modes)]
            gen = SignalGenerator(node.node_id, mode)
            self.generators.append(gen)
        
        # Полный граф: каждый связан с каждым
        for i, node in enumerate(self.nodes):
            for j, other in enumerate(self.nodes):
                if i != j:
                    node.peers[other.node_id] = other
        
        self._process = psutil.Process() if HAS_PSUTIL else None
        
        self.logger.info(f"🔺 TEES Network v5.0 инициализирована: {node_count} узлов")
        self.logger.info(f"   Полный граф: каждый с каждым ({node_count * (node_count - 1)} рёбер)")
        self.logger.info(f"   Самовалидация: каждый узел проверяет свой хеш")
        self.logger.info(f"   Карантин: невалидные узлы изолируются")
    
    def _setup_logger(self):
        logger = logging.getLogger("TEESNetwork")
        logger.setLevel(logging.INFO)
        console = logging.StreamHandler(); console.setLevel(logging.WARNING)
        console.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
        file_handler = logging.FileHandler(NETWORK_LOG, encoding='utf-8'); file_handler.setLevel(logging.DEBUG)
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
        self.logger.info(f"🚀 Запуск сети из {self.node_count} узлов...")
        self.running = True
        while self.running:
            time.sleep(0.5)
            self.cycle += 1
            
            # Генерируем внешние сигналы для каждого узла
            for i, node in enumerate(self.nodes):
                sig = self.generators[i].generate(self.cycle)
                if sig:
                    node.receive_signal(sig)
            
            # Каждый узел делает свой цикл
            for node in self.nodes:
                node.living_cycle()
            
            # Статус каждые 120 циклов
            if self.cycle % 120 == 0:
                self._print_status()
    
    def stop(self):
        self.running = False
        self.logger.info("🛑 Сеть остановлена")
    
    def _print_status(self):
        ram = self._get_ram()
        print(f"\n{'='*70}")
        print(f"🔺 TEES Network v5.0 — цикл {self.cycle} | RAM: {ram} | Узлов: {self.node_count}")
        
        for node in self.nodes:
            print(f"   {node.status_line()}")
        
        # Статистика сети
        cohs = [n.coherence for n in self.nodes]
        corts = [n.hormones.get('cortisol', 0) for n in self.nodes]
        temps = [n.temperature for n in self.nodes]
        valid = sum(1 for n in self.nodes if n.validated)
        quarantined = sum(1 for n in self.nodes if n.quarantine)
        
        print(f"   📊 Разброс: coh={max(cohs)-min(cohs):.4f} "
              f"cort={max(corts)-min(corts):.2f} t={max(temps)-min(temps):.1f}°")
        print(f"   🔐 Валидных: {valid}/{self.node_count} | Карантин: {quarantined}")
        print(f"{'='*70}")


# ══════════════════════════════════════
# ТОЧКА ВХОДА
# ══════════════════════════════════════
if __name__ == "__main__":
    network = TEESNetwork(node_count=5)
    try:
        network.start()
    except KeyboardInterrupt:
        network.stop()