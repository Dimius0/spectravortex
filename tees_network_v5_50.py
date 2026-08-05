#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_network_v5_50.py — TEES Network v5.0: 50 узлов
"""
import os, sys, time, json, queue, hashlib, logging, random, string
from datetime import datetime
from typing import Dict, List, Optional, Any

DATA_DIR = "E:/tees_data"
NETWORK_LOG = os.path.join(DATA_DIR, "tees_network_v5_50.log")
NODE_COUNT = 50
os.makedirs(DATA_DIR, exist_ok=True)

from tees_core_4_1 import LivingFieldV3

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class SignalGenerator:
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


class NetworkNode(LivingFieldV3):
    def __init__(self, node_id: str, name: str, seed_offset: int = 0, init_coherence: float = 0.993):
        super().__init__(f"node_{node_id}", name)
        self.node_id = node_id
        self._seed_counter = seed_offset
        self._field_state = seed_offset
        self.coherence = init_coherence
        self.code_hash = hashlib.sha256(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).hexdigest()[:16]
        self.validated = True
        self.quarantine = False
        self.external_signal_queue = queue.Queue(maxsize=50)  # Меньше для 50 узлов
        self.signal_history: List[Dict] = []
        self.peers: Dict[str, 'NetworkNode'] = {}
        self.signals_sent = 0
        self.signals_received = 0
        self.logger = logging.getLogger(f"Node.{node_id}")
    
    def validate_self(self) -> bool:
        current_hash = hashlib.sha256(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).hexdigest()[:16]
        if current_hash != self.code_hash:
            self.validated = False
            self.logger.error(f"❌ САМОВАЛИДАЦИЯ ПРОВАЛЕНА!")
            return False
        self.validated = True
        return True
    
    def receive_signal(self, signal: Dict[str, Any]):
        try:
            self.external_signal_queue.put(signal, timeout=0.02)
            self.signals_received += 1
        except queue.Full:
            pass
    
    def broadcast_furcation(self, new_modes: List[Any]):
        if not new_modes or not self.peers: return
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
        new_modes = super().furcate()
        if new_modes: self.broadcast_furcation(new_modes)
        return new_modes
    
    def _process_external_signals(self):
        max_to_process = min(self.external_signal_queue.qsize(), 10)
        processed = 0
        while processed < max_to_process:
            try:
                sig = self.external_signal_queue.get_nowait()
                self.ingest_external_signal(sig)
                processed += 1
            except queue.Empty:
                break
    
    def living_cycle(self):
        if self._cycle % 100 == 0 and self._cycle > 0:
            self.validate_self()
        if not self.validated and not self.quarantine:
            self.quarantine = True
        self._process_external_signals()
        self._cycle += 1
        if self._cycle % 10 == 0:
            if hasattr(self, '_adapt_precision'): self._adapt_precision()
            if hasattr(self, '_update_emotions'): self._update_emotions()
            if hasattr(self, '_use_comfort_resource'): self._use_comfort_resource()
            if hasattr(self, '_should_bifurcate') and not self._should_bifurcate():
                self.coherence = min(0.998, self.coherence + 0.0001)
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
        d = self.hormones.get('dopamine', 0.5)
        q = "🔒" if self.quarantine else "✅"
        return (f"[{self.node_id}] {q} c={self._cycle} m={self.field_size} "
                f"coh={self.coherence:.4f} t={self.temperature:.1f}° "
                f"dop={d:.2f} cort={self.hormones.get('cortisol', 0):.2f} "
                f"rx={self.signals_received}")


class TEESNetwork:
    def __init__(self, node_count: int = NODE_COUNT):
        self.logger = self._setup_logger()
        self.running = True
        self.cycle = 0
        self.node_count = node_count
        self.nodes: List[NetworkNode] = []
        modes = ["frequent_weak", "silent", "rare_strong"]
        
        for i in range(node_count):
            seed_offset = i * 200 + random.randint(0, 100)
            coh = 0.990 + (i % 5) * 0.002
            node_id = f"N{i:02d}"
            node = NetworkNode(node_id=node_id, name=f"Узел-{i}", seed_offset=seed_offset, init_coherence=coh)
            self.nodes.append(node)
        
        self.generators = []
        for i, node in enumerate(self.nodes):
            mode = modes[i % 3]
            self.generators.append(SignalGenerator(node.node_id, mode))
        
        # Полный граф
        for i, node in enumerate(self.nodes):
            for j, other in enumerate(self.nodes):
                if i != j:
                    node.peers[other.node_id] = other
        
        self._process = psutil.Process() if HAS_PSUTIL else None
        edges = node_count * (node_count - 1)
        self.logger.info(f"🔺 TEES Network v5.0: {node_count} узлов, {edges} рёбер")
        self.logger.info(f"   Полный граф + самовалидация + карантин")
    
    def _setup_logger(self):
        logger = logging.getLogger("TEESNetwork")
        logger.setLevel(logging.WARNING)
        console = logging.StreamHandler(); console.setLevel(logging.WARNING)
        console.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
        file_handler = logging.FileHandler(NETWORK_LOG, encoding='utf-8'); file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(console); logger.addHandler(file_handler)
        return logger
    
    def _get_ram(self) -> str:
        if self._process:
            try: return f"{self._process.memory_info().rss / 1024 / 1024:.1f} MB"
            except: pass
        return "?"
    
    def start(self):
        self.logger.info(f"🚀 Запуск сети из {self.node_count} узлов...")
        self.running = True
        while self.running:
            time.sleep(0.5)
            self.cycle += 1
            
            for i, node in enumerate(self.nodes):
                sig = self.generators[i].generate(self.cycle)
                if sig: node.receive_signal(sig)
            
            for node in self.nodes:
                node.living_cycle()
            
            if self.cycle % 120 == 0:
                self._print_status()
    
    def stop(self):
        self.running = False
        self.logger.info("🛑 Сеть остановлена")
    
    def _print_status(self):
        ram = self._get_ram()
        cohs = [n.coherence for n in self.nodes]
        valid = sum(1 for n in self.nodes if n.validated)
        quars = sum(1 for n in self.nodes if n.quarantine)
        
        print(f"\n{'='*70}")
        print(f"🔺 Сеть 50 узлов — цикл {self.cycle} | RAM: {ram} | Валидных: {valid}/{self.node_count} | Карантин: {quars}")
        print(f"   📊 coh: min={min(cohs):.4f} max={max(cohs):.4f} разброс={max(cohs)-min(cohs):.4f}")
        
        # Показываем первых 5 и последних 3
        for node in self.nodes[:5]:
            print(f"   {node.status_short()}")
        if self.node_count > 8:
            print(f"   ... ({self.node_count - 8} узлов) ...")
        for node in self.nodes[-3:]:
            print(f"   {node.status_short()}")
        print(f"{'='*70}")


if __name__ == "__main__":
    network = TEESNetwork(node_count=50)
    try:
        network.start()
    except KeyboardInterrupt:
        network.stop()