#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_unbound.py — TEES Unbound v1.1: Сеть без искусственных ограничений
=========================================================================
Изменения v1.1:
  - ram_limit_mb = 2500 (было 1500)
  - swap_threshold = 500 (было 200)
  - Своп критичен только при свободной RAM < 1000 MB
  - Скользящее среднее свопа для детекта роста
"""

import os, sys, time, json, queue, hashlib, logging, random, string, math
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

DATA_DIR = "E:/tees_data"
NETWORK_LOG = os.path.join(DATA_DIR, "tees_unbound.log")
STATE_FILE = os.path.join(DATA_DIR, "unbound_state.json")
os.makedirs(DATA_DIR, exist_ok=True)

from tees_core_4_1 import LivingFieldV3

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil не найден")

# ══════════════════════════════════════
# АДАПТИВНАЯ КОНФИГУРАЦИЯ (v1.1)
# ══════════════════════════════════════
class AdaptiveConfig:
    """Динамически вычисляет пределы на основе ресурсов."""
    
    def __init__(self):
        self.process = psutil.Process() if HAS_PSUTIL else None
        self.ram_limit_mb = 2500       # Предел RAM для сети (было 1500)
        self.free_ram_keep_mb = 500    # Оставляем системе
        self.cpu_limit_pct = 80        # Предел CPU
        self.swap_history = deque(maxlen=5)  # Скользящее среднее свопа
    
    def get_ram_mb(self) -> float:
        if self.process:
            return self.process.memory_info().rss / 1024 / 1024
        return 0
    
    def get_free_ram_mb(self) -> float:
        if HAS_PSUTIL:
            return psutil.virtual_memory().available / 1024 / 1024
        return 1000
    
    def get_swap_mb(self) -> float:
        if HAS_PSUTIL:
            return psutil.swap_memory().used / 1024 / 1024
        return 0
    
    def get_swap_trend(self) -> float:
        """Скользящее среднее свопа. Возвращает изменение за 5 проверок."""
        current = self.get_swap_mb()
        self.swap_history.append(current)
        if len(self.swap_history) < 2:
            return 0
        return self.swap_history[-1] - self.swap_history[0]
    
    def get_cpu_pct(self) -> float:
        if self.process:
            return self.process.cpu_percent(interval=0.1)
        return 50
    
    def can_add_nodes(self) -> bool:
        """Можно ли добавлять узлы (v1.1 — умный своп)."""
        ram_ok = self.get_ram_mb() < self.ram_limit_mb * 0.8
        free_ok = self.get_free_ram_mb() > self.free_ram_keep_mb
        
        # Своп критичен только если свободной RAM < 1000 MB И своп > 500 MB
        free_ram = self.get_free_ram_mb()
        swap = self.get_swap_mb()
        swap_trend = self.get_swap_trend()
        
        if free_ram > 1000:
            swap_ok = True  # Много свободной RAM — своп не важен
        elif swap > 500 and swap_trend > 50:
            swap_ok = False  # Мало RAM, своп большой и растёт
        elif swap > 800:
            swap_ok = False  # Очень большой своп — стоп
        else:
            swap_ok = True
        
        cpu_ok = self.get_cpu_pct() < self.cpu_limit_pct
        return ram_ok and free_ok and swap_ok and cpu_ok
    
    def should_remove_nodes(self) -> bool:
        """Нужно ли убирать узлы."""
        ram_critical = self.get_ram_mb() > self.ram_limit_mb * 0.95
        swap_critical = self.get_swap_mb() > 800
        cpu_critical = self.get_cpu_pct() > 95
        return ram_critical or swap_critical or cpu_critical


# ══════════════════════════════════════
# ГЕНЕРАТОР СИГНАЛОВ
# ══════════════════════════════════════
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


# ══════════════════════════════════════
# УЗЕЛ (v4.1 + сигналы + нет потолков)
# ══════════════════════════════════════
class UnboundNode(LivingFieldV3):
    def __init__(self, node_id: str, name: str, seed_offset: int = 0, init_coherence: float = 0.993):
        super().__init__(f"node_{node_id}", name)
        self.node_id = node_id
        self._seed_counter = seed_offset
        self._field_state = seed_offset
        self.coherence = init_coherence
        
        # Без потолка когерентности
        self.coherence_max = 1.0
        
        self.code_hash = hashlib.sha256(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).hexdigest()[:16]
        self.validated = True
        self.quarantine = False
        self.active = True
        
        self.external_signal_queue = queue.Queue(maxsize=100)
        self.peers: Dict[str, 'UnboundNode'] = {}
        self.signals_sent = 0
        self.signals_received = 0
        self.logger = logging.getLogger(f"Node.{node_id}")
    
    def deactivate(self):
        self.active = False
        self.external_signal_queue = queue.Queue(maxsize=1)
        self.peers.clear()
        self.logger.info(f"💤 Узел {self.node_id} деактивирован")
    
    def reactivate(self, peers: Dict[str, 'UnboundNode']):
        self.active = True
        self.external_signal_queue = queue.Queue(maxsize=100)
        self.peers = peers
        self.logger.info(f"🌱 Узел {self.node_id} реактивирован")
    
    def receive_signal(self, signal: Dict[str, Any]):
        if not self.active: return
        try:
            self.external_signal_queue.put(signal, timeout=0.02)
            self.signals_received += 1
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
            except queue.Empty:
                break
    
    def _validate_self(self) -> bool:
        try:
            current_hash = hashlib.sha256(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).hexdigest()[:16]
        except Exception:
            return True
        if current_hash != self.code_hash:
            self.validated = False
            self.logger.error(f"❌ САМОВАЛИДАЦИЯ ПРОВАЛЕНА!")
            return False
        self.validated = True
        return True
    
    def living_cycle(self):
        if not self.active: return
        if self._cycle % 100 == 0 and self._cycle > 0:
            self._validate_self()
        if not self.validated and not self.quarantine:
            self.quarantine = True
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
                f"dop={d:.2f} rx={self.signals_received}")


# ══════════════════════════════════════
# СЕТЬ БЕЗ ГРАНИЦ (v1.1)
# ══════════════════════════════════════
class UnboundNetwork:
    def __init__(self, initial_nodes: int = 10, min_nodes: int = 5):
        self.logger = self._setup_logger()
        self.running = True
        self.cycle = 0
        self.config = AdaptiveConfig()
        
        self.min_nodes = min_nodes
        self.adjustment_interval = 300
        
        self.all_nodes: List[UnboundNode] = []
        self.node_counter = 0
        
        for i in range(initial_nodes):
            self._create_node()
        
        self.generators: List[SignalGenerator] = []
        self._sync_generators()
        self._rebuild_graph()
        
        ram = self.config.get_ram_mb()
        edges = len(self.active_nodes) * (len(self.active_nodes) - 1)
        self.logger.info(f"🌀 TEES Unbound v1.1: {len(self.active_nodes)} узлов, {edges} рёбер, RAM={ram:.1f} MB")
        self.logger.info(f"   Лимит RAM: {self.config.ram_limit_mb} MB | Своб. системе: {self.config.free_ram_keep_mb} MB")
        self.logger.info(f"   Умный своп: критичен только при своб. RAM < 1000 MB")
    
    @property
    def active_nodes(self) -> List[UnboundNode]:
        return [n for n in self.all_nodes if n.active]
    
    def _setup_logger(self):
        logger = logging.getLogger("UnboundNetwork")
        logger.setLevel(logging.INFO)
        console = logging.StreamHandler(); console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
        file_handler = logging.FileHandler(NETWORK_LOG, encoding='utf-8'); file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger.addHandler(console); logger.addHandler(file_handler)
        return logger
    
    def _create_node(self):
        seed_offset = self.node_counter * 200 + random.randint(0, 100)
        coh = 0.990 + (self.node_counter % 5) * 0.002
        node_id = f"N{self.node_counter:04d}"
        node = UnboundNode(node_id=node_id, name=f"U-{self.node_counter}", seed_offset=seed_offset, init_coherence=coh)
        self.all_nodes.append(node)
        self.node_counter += 1
        return node
    
    def _sync_generators(self):
        modes = ["frequent_weak", "silent", "rare_strong"]
        self.generators = []
        for i, node in enumerate(self.all_nodes):
            mode = modes[i % 3] if node.active else "silent"
            self.generators.append(SignalGenerator(node.node_id, mode))
    
    def _rebuild_graph(self):
        active = self.active_nodes
        for node in active:
            node.peers = {other.node_id: other for other in active if other != node}
    
    def _add_nodes(self, count: int):
        added = 0
        deactivated = [n for n in self.all_nodes if not n.active]
        for node in deactivated[:count]:
            node.reactivate({n.node_id: n for n in self.active_nodes if n != node})
            added += 1
        
        for _ in range(count - added):
            if not self.config.can_add_nodes(): break
            self._create_node()
            added += 1
        
        if added > 0:
            self._rebuild_graph()
            self._sync_generators()
            self.logger.info(f"➕ +{added} узлов. Активных: {len(self.active_nodes)}")
    
    def _remove_nodes(self, count: int):
        active = self.active_nodes
        if len(active) <= self.min_nodes: return
        to_remove = min(count, len(active) - self.min_nodes)
        sorted_nodes = sorted(active, key=lambda n: n.signals_received)
        for node in sorted_nodes[:to_remove]:
            node.deactivate()
        self._rebuild_graph()
        self._sync_generators()
        self.logger.info(f"➖ -{to_remove} узлов. Активных: {len(self.active_nodes)}")
    
    def _adaptive_adjustment(self):
        if not HAS_PSUTIL: return
        
        ram = self.config.get_ram_mb()
        active_count = len(self.active_nodes)
        node_ram = ram / max(active_count, 1)
        
        for node in self.active_nodes:
            if ram < self.config.ram_limit_mb * 0.5:
                node.max_depth = max(2, min(10, int(ram / 100)))
            else:
                node.max_depth = min(node.max_depth + 1, 20) if node.coherence > 0.995 else node.max_depth
            
            if self.config.get_cpu_pct() < 50:
                node.max_bands = min(node.max_bands + 2, 64)
            else:
                node.max_bands = max(node.min_bands, node.max_bands - 2)
        
        if self.config.can_add_nodes():
            free = self.config.get_free_ram_mb() - self.config.free_ram_keep_mb
            if free > node_ram * 100:
                self._add_nodes(100)
            elif free > node_ram * 50:
                self._add_nodes(50)
            elif free > node_ram * 10:
                self._add_nodes(10)
            elif free > node_ram:
                count = int(free / node_ram)
                self._add_nodes(count)
        
        elif self.config.should_remove_nodes():
            if self.config.get_swap_mb() > 800:
                self._remove_nodes(10)
            elif self.config.get_ram_mb() > self.config.ram_limit_mb * 0.95:
                self._remove_nodes(5)
            elif self.config.get_cpu_pct() > 95:
                self._remove_nodes(3)
    
    def start(self):
        self.logger.info(f"🚀 Запуск TEES Unbound v1.1 (мин={self.min_nodes} узлов)...")
        self.running = True
        while self.running:
            time.sleep(0.5)
            self.cycle += 1
            
            for i, node in enumerate(self.all_nodes):
                if node.active and i < len(self.generators):
                    sig = self.generators[i].generate(self.cycle)
                    if sig: node.receive_signal(sig)
            
            for node in self.active_nodes:
                node.living_cycle()
            
            if self.cycle % self.adjustment_interval == 0:
                self._adaptive_adjustment()
            
            if self.cycle % 120 == 0:
                self._print_status()
    
    def stop(self):
        self.running = False
        self._save_state()
        self.logger.info(f"🛑 Сеть остановлена. Узлов: {len(self.active_nodes)}/{len(self.all_nodes)}")
    
    def _save_state(self):
        try:
            state = {
                'total_nodes': len(self.all_nodes),
                'active_nodes': len(self.active_nodes),
                'cycle': self.cycle,
                'nodes': [{
                    'id': n.node_id, 'active': n.active,
                    'coherence': n.coherence, 'temperature': n.temperature,
                    'cycle': n._cycle, 'signals_received': n.signals_received,
                } for n in self.all_nodes]
            }
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except: pass
    
    def _print_status(self):
        ram = self.config.get_ram_mb()
        free = self.config.get_free_ram_mb()
        swap = self.config.get_swap_mb()
        swap_trend = self.config.get_swap_trend()
        cpu = self.config.get_cpu_pct()
        active = self.active_nodes
        
        cohs = [n.coherence for n in active]
        valid = sum(1 for n in active if n.validated)
        quars = sum(1 for n in active if n.quarantine)
        inactive = sum(1 for n in self.all_nodes if not n.active)
        
        avg_depth = sum(n.max_depth for n in active) / max(len(active), 1)
        avg_bands = sum(n.max_bands for n in active) / max(len(active), 1)
        
        trend_str = f"↑{swap_trend:.0f}" if swap_trend > 10 else (f"↓{abs(swap_trend):.0f}" if swap_trend < -10 else "→")
        
        print(f"\n{'='*70}")
        print(f"🌀 TEES Unbound v1.1 — цикл {self.cycle} | RAM={ram:.1f} MB | CPU={cpu:.0f}%")
        print(f"   Свободно: {free:.0f} MB | Своп: {swap:.0f} MB {trend_str}")
        print(f"   Узлов: {len(active)} активных + {inactive} 💤 = {len(self.all_nodes)} всего")
        print(f"   Валидных: {valid} | Карантин: {quars}")
        if cohs:
            print(f"   📊 Когерентность: min={min(cohs):.4f} max={max(cohs):.4f} разброс={max(cohs)-min(cohs):.4f}")
        print(f"   ⚙️  Адаптивные: глубина≈{avg_depth:.1f} полос≈{avg_bands:.0f}")
        print(f"   🐁 RAM свободно: {free:.0f} MB — мышка шевелится!")
        
        for node in active[:3]:
            print(f"   {node.status_short()}")
        if len(active) > 6:
            print(f"   ... ({len(active) - 6} узлов) ...")
        for node in active[-3:]:
            print(f"   {node.status_short()}")
        print(f"{'='*70}")


if __name__ == "__main__":
    network = UnboundNetwork(initial_nodes=10, min_nodes=5)
    try:
        network.start()
    except KeyboardInterrupt:
        network.stop()