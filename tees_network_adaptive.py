#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tees_network_adaptive.py — TEES Adaptive Network v5.1
=====================================================
Сеть, которая сама регулирует количество узлов в зависимости от RAM/свопа.
Растёт, когда есть ресурсы. Сжимается, когда их не хватает.
Отключённые узлы сохраняются — не умирают.
"""

import os, sys, time, json, queue, hashlib, logging, random, string, math
from datetime import datetime
from typing import Dict, List, Optional, Any

DATA_DIR = "E:/tees_data"
NETWORK_LOG = os.path.join(DATA_DIR, "tees_network_adaptive.log")
STATE_FILE = os.path.join(DATA_DIR, "adaptive_network_state.json")
os.makedirs(DATA_DIR, exist_ok=True)

from tees_core_4_1 import LivingFieldV3

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil не найден. Адаптивность по памяти не работает.")

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
# УЗЕЛ СЕТИ
# ══════════════════════════════════════
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
        self.active = True  # Новое: узел может быть деактивирован
        self.external_signal_queue = queue.Queue(maxsize=50)
        self.peers: Dict[str, 'NetworkNode'] = {}
        self.signals_sent = 0
        self.signals_received = 0
        self.logger = logging.getLogger(f"Node.{node_id}")

    def _validate_self(self) -> bool:
        """Проверяет, совпадает ли текущий хеш кода с эталонным."""
        try:
            current_hash = hashlib.sha256(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).hexdigest()[:16]
        except Exception:
            return True  # Если не можем прочитать файл — считаем валидным
        if current_hash != self.code_hash:
            self.validated = False
            self.logger.error(f"❌ САМОВАЛИДАЦИЯ ПРОВАЛЕНА: хеш изменился!")
            return False
        self.validated = True
        return True    
    
    def deactivate(self):
        """Деактивировать узел (освободить ресурсы, но сохранить состояние)."""
        self.active = False
        self.external_signal_queue = queue.Queue(maxsize=1)  # Минимальная очередь
        self.peers.clear()
        self.logger.info(f"💤 Узел {self.node_id} деактивирован")
    
    def reactivate(self, peers: Dict[str, 'NetworkNode']):
        """Реактивировать узел."""
        self.active = True
        self.external_signal_queue = queue.Queue(maxsize=50)
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
        if not self.active: return f"[{self.node_id}] 💤 деактивирован"
        d = self.hormones.get('dopamine', 0.5)
        q = "🔒" if self.quarantine else "✅"
        return (f"[{self.node_id}] {q} c={self._cycle} m={self.field_size} "
                f"coh={self.coherence:.4f} t={self.temperature:.1f}° "
                f"dop={d:.2f} rx={self.signals_received}")


# ══════════════════════════════════════
# АДАПТИВНАЯ СЕТЬ
# ══════════════════════════════════════
class AdaptiveNetwork:
    def __init__(self, initial_nodes: int = 10, min_nodes: int = 5, max_nodes: int = 100):
        self.logger = self._setup_logger()
        self.running = True
        self.cycle = 0
        
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.free_ram_threshold_mb = 500  # Если свободно больше — добавляем узлы
        self.swap_threshold_mb = 100      # Если своп больше — убираем узлы
        self.adjustment_cooldown = 600    # Циклов между проверками
        
        # Все узлы (и активные, и деактивированные)
        self.all_nodes: List[NetworkNode] = []
        self.node_counter = 0
        
        # Создаём начальные узлы
        for i in range(initial_nodes):
            self._create_node()
        
        # Генераторы
        self.generators: List[SignalGenerator] = []
        self._sync_generators()
        
        # Полный граф для активных
        self._rebuild_graph()
        
        self._process = psutil.Process() if HAS_PSUTIL else None
        edges = len(self.active_nodes) * (len(self.active_nodes) - 1)
        self.logger.info(f"🔺 Адаптивная сеть: {len(self.active_nodes)} активных из {len(self.all_nodes)} всего, {edges} рёбер")
    
    @property
    def active_nodes(self) -> List[NetworkNode]:
        return [n for n in self.all_nodes if n.active]
    
    def _setup_logger(self):
        logger = logging.getLogger("AdaptiveNetwork")
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
        node_id = f"N{self.node_counter:03d}"
        node = NetworkNode(node_id=node_id, name=f"Узел-{self.node_counter}", seed_offset=seed_offset, init_coherence=coh)
        self.all_nodes.append(node)
        self.node_counter += 1
        return node
    
    def _sync_generators(self):
        modes = ["frequent_weak", "silent", "rare_strong"]
        self.generators = []
        for i, node in enumerate(self.all_nodes):
            if node.active:
                mode = modes[i % 3]
                self.generators.append(SignalGenerator(node.node_id, mode))
            else:
                self.generators.append(SignalGenerator(node.node_id, "silent"))
    
    def _rebuild_graph(self):
        """Перестраивает полный граф для активных узлов."""
        active = self.active_nodes
        for node in active:
            node.peers = {}
            for other in active:
                if node != other:
                    node.peers[other.node_id] = other
    
    def _add_nodes(self, count: int):
        """Добавить узлы в сеть."""
        added = 0
        # Сначала пробуем реактивировать деактивированные
        deactivated = [n for n in self.all_nodes if not n.active]
        for node in deactivated[:count]:
            self._rebuild_graph()  # Временно
            node.reactivate({n.node_id: n for n in self.active_nodes if n != node})
            added += 1
        
        # Если не хватило — создаём новые
        for _ in range(count - added):
            if len(self.all_nodes) >= self.max_nodes: break
            self._create_node()
            added += 1
        
        if added > 0:
            self._rebuild_graph()
            self._sync_generators()
            self.logger.info(f"➕ Добавлено {added} узлов. Активных: {len(self.active_nodes)}/{len(self.all_nodes)}")
    
    def _remove_nodes(self, count: int):
        """Деактивировать узлы (с сохранением)."""
        active = self.active_nodes
        if len(active) <= self.min_nodes: return
        
        to_remove = min(count, len(active) - self.min_nodes)
        # Убираем узлы с наименьшим количеством принятых сигналов
        sorted_nodes = sorted(active, key=lambda n: n.signals_received)
        for node in sorted_nodes[:to_remove]:
            node.deactivate()
        
        self._rebuild_graph()
        self._sync_generators()
        self.logger.info(f"➖ Деактивировано {to_remove} узлов. Активных: {len(self.active_nodes)}/{len(self.all_nodes)}")
    
    def _check_resources(self):
        """Проверяет память и адаптирует сеть."""
        if not self._process: return
        
        mem = self._process.memory_info()
        ram_mb = mem.rss / 1024 / 1024
        
        # Свободная RAM (системная)
        if HAS_PSUTIL:
            free_ram = psutil.virtual_memory().available / 1024 / 1024
            swap_used = psutil.swap_memory().used / 1024 / 1024
        else:
            free_ram = 1000
            swap_used = 0
        
        if free_ram > self.free_ram_threshold_mb and len(self.active_nodes) < self.max_nodes:
            # Есть свободная память — добавляем 5 узлов
            self._add_nodes(5)
        elif swap_used > self.swap_threshold_mb and len(self.active_nodes) > self.min_nodes:
            # Своп используется — убираем 5 узлов
            self._remove_nodes(5)
    
    def _get_ram(self) -> str:
        if self._process:
            try:
                mb = self._process.memory_info().rss / 1024 / 1024
                free = psutil.virtual_memory().available / 1024 / 1024 if HAS_PSUTIL else 0
                swap = psutil.swap_memory().used / 1024 / 1024 if HAS_PSUTIL else 0
                return f"{mb:.1f} MB (своб. {free:.0f} MB, своп {swap:.0f} MB)"
            except: pass
        return "?"
    
    def start(self):
        self.logger.info(f"🚀 Запуск адаптивной сети (мин={self.min_nodes}, макс={self.max_nodes})...")
        self.running = True
        while self.running:
            time.sleep(0.5)
            self.cycle += 1
            
            # Генерируем внешние сигналы
            for i, node in enumerate(self.all_nodes):
                if node.active and i < len(self.generators):
                    sig = self.generators[i].generate(self.cycle)
                    if sig: node.receive_signal(sig)
            
            # Каждый активный узел делает цикл
            for node in self.active_nodes:
                node.living_cycle()
            
            # Проверка ресурсов и адаптация
            if self.cycle % self.adjustment_cooldown == 0:
                self._check_resources()
            
            # Статус каждые 120 циклов
            if self.cycle % 120 == 0:
                self._print_status()
    
    def stop(self):
        self.running = False
        # Сохраняем состояние сети
        self._save_state()
        self.logger.info(f"🛑 Сеть остановлена. Всего узлов: {len(self.all_nodes)}, активных: {len(self.active_nodes)}")
    
    def _save_state(self):
        try:
            state = {
                'total_nodes': len(self.all_nodes),
                'active_nodes': len(self.active_nodes),
                'cycle': self.cycle,
                'nodes': []
            }
            for node in self.all_nodes:
                state['nodes'].append({
                    'id': node.node_id,
                    'active': node.active,
                    'coherence': node.coherence,
                    'temperature': node.temperature,
                    'cycle': node._cycle,
                    'signals_received': node.signals_received,
                    'signals_sent': node.signals_sent,
                })
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            self.logger.info(f"💾 Состояние сохранено: {len(self.active_nodes)}/{len(self.all_nodes)} узлов")
        except: pass
    
    def _print_status(self):
        ram = self._get_ram()
        active = self.active_nodes
        cohs = [n.coherence for n in active]
        valid = sum(1 for n in active if n.validated)
        quars = sum(1 for n in active if n.quarantine)
        
        print(f"\n{'='*70}")
        print(f"🔺 Адаптивная сеть — цикл {self.cycle} | RAM: {ram}")
        print(f"   Узлов: {len(active)} активных из {len(self.all_nodes)} всего | Валидных: {valid} | Карантин: {quars}")
        if cohs:
            print(f"   📊 coh: min={min(cohs):.4f} max={max(cohs):.4f} разброс={max(cohs)-min(cohs):.4f}")
        
        # Показываем первых 5 активных
        for node in active[:5]:
            print(f"   {node.status_short()}")
        if len(active) > 8:
            print(f"   ... ({len(active) - 8} узлов) ...")
        for node in active[-3:]:
            print(f"   {node.status_short()}")
        
        # Деактивированные
        inactive = [n for n in self.all_nodes if not n.active]
        if inactive:
            print(f"   💤 Деактивировано: {len(inactive)} узлов (сохранены)")
        print(f"{'='*70}")


# ══════════════════════════════════════
# ТОЧКА ВХОДА
# ══════════════════════════════════════
if __name__ == "__main__":
    network = AdaptiveNetwork(initial_nodes=10, min_nodes=5, max_nodes=50)
    try:
        network.start()
    except KeyboardInterrupt:
        network.stop()