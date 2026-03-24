"""
Mesh Network — децентрализованная сеть с рандомизированной синхронизацией
Версия 1.3 — единый сокет для приёма и отправки
"""

import socket
import threading
import json
import time
import random
import hashlib
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import deque

from ..personality import Personality, SpectralMode


@dataclass
class NodeInfo:
    """Информация о соседнем узле в сети"""
    node_id: str
    address: str
    port: int
    last_seen: float
    field_hash: str
    total_amplitude: float
    sync_count: int = 0
    priority: float = 1.0
    last_sync: float = 0.0
    quality: float = 0.5


class MeshNetwork:
    """
    Децентрализованная mesh-сеть с принудительной диверсификацией связей
    """
    
    def __init__(self, personality: Personality, 
                 listen_port: int = 8765,
                 max_peers: int = 10,
                 sync_interval: int = 60):
        self.p = personality
        self.listen_port = listen_port
        self.max_peers = max_peers
        self.base_sync_interval = sync_interval
        
        self.nodes: Dict[str, NodeInfo] = {}
        self._running = False
        self._lock = threading.Lock()
        self.sock = None
        
        self._sync_history: Dict[str, deque] = {}
        
        self.node_id = hashlib.md5(f"{personality.id}_{time.time()}".encode()).hexdigest()[:8]
        self.bootstrap_nodes: List[Tuple[str, int]] = []
    
    def start(self):
        """Запускает сетевой сервис"""
        # Создаём единый сокет
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.listen_port))
        self.sock.settimeout(1.0)
        
        self._running = True
        
        # Запускаем слушающий поток
        threading.Thread(target=self._listen, daemon=True).start()
        
        # Запускаем поток синхронизации
        threading.Thread(target=self._sync_loop, daemon=True).start()
        
        # Запускаем поток проверки кластеров
        threading.Thread(target=self._cluster_watchdog, daemon=True).start()
        
        # Активное обнаружение bootstrap-узлов
        if self.bootstrap_nodes:
            threading.Thread(target=self._initial_discovery, daemon=True).start()
        
        print(f"🌐 Mesh-сеть запущена")
        print(f"   ID узла: {self.node_id}")
        print(f"   Порт: {self.listen_port}")
        print(f"   Макс. пиров: {self.max_peers}")
        if self.bootstrap_nodes:
            print(f"   Bootstrap узлы: {self.bootstrap_nodes}")
    
    def stop(self):
        """Останавливает сетевой сервис"""
        self._running = False
        if self.sock:
            self.sock.close()
        print("🌐 Mesh-сеть остановлена")
    
    def add_bootstrap_node(self, address: str, port: int):
        self.bootstrap_nodes.append((address, port))
        print(f"   Добавлен bootstrap-узел: {address}:{port}")
    
    def _initial_discovery(self):
        time.sleep(1)
        for addr, port in self.bootstrap_nodes:
            print(f"   🔍 Поиск узла {addr}:{port}")
            msg = {"type": "discover", "node_id": self.node_id}
            self._send_to(msg, (addr, port))
            time.sleep(2)
    
    def _listen(self):
        while self._running and self.sock:
            try:
                data, addr = self.sock.recvfrom(65535)
                self._handle_message(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"⚠️ Ошибка приёма: {e}")
    
    def _handle_message(self, data: bytes, addr: Tuple[str, int]):
        try:
            msg = json.loads(data.decode())
            msg_type = msg.get("type")
            
            if msg_type == "discover":
                self._handle_discover(addr)
            elif msg_type == "announce":
                self._handle_announce(msg, addr)
            elif msg_type == "sync":
                self._handle_sync(msg, addr)
            elif msg_type == "field_push":
                self._handle_field_push(msg, addr)
        except Exception as e:
            print(f"⚠️ Ошибка обработки: {e}")
    
    def _handle_discover(self, addr: Tuple[str, int]):
        response = {
            "type": "announce",
            "node_id": self.node_id,
            "port": self.listen_port,
            "total_amplitude": self._get_total_amplitude(),
            "field_hash": self._get_field_hash(),
            "timestamp": time.time()
        }
        self._send_to(response, addr)
        print(f"   📢 Ответ на discovery от {addr[0]}:{addr[1]}")
    
    def _handle_announce(self, msg: dict, addr: Tuple[str, int]):
        node_id = msg.get("node_id")
        
        if not node_id or node_id == self.node_id:
            return
        
        announced_port = msg.get("port", self.listen_port)
        
        print(f"   📢 Получен announce от {node_id[:8]} (порт={announced_port})")
        
        with self._lock:
            if node_id not in self.nodes:
                self.nodes[node_id] = NodeInfo(
                    node_id=node_id,
                    address=addr[0],
                    port=announced_port,
                    last_seen=time.time(),
                    field_hash=msg.get("field_hash", ""),
                    total_amplitude=msg.get("total_amplitude", 0.0)
                )
                print(f"   🔗 НОВЫЙ УЗЕЛ: {node_id[:8]} ({addr[0]}:{announced_port})")
            else:
                self.nodes[node_id].last_seen = time.time()
    
    def _handle_sync(self, msg: dict, addr: Tuple[str, int]):
        node_id = msg.get("node_id")
        if not node_id:
            return
        
        response = {
            "type": "field_push",
            "node_id": self.node_id,
            "field": [self._mode_to_dict(m) for m in self.p.h_field[:10]],
            "timestamp": time.time()
        }
        self._send_to(response, addr)
        print(f"   📤 Отправлено поле узлу {node_id[:8]}")
    
    def _handle_field_push(self, msg: dict, addr: Tuple[str, int]):
        node_id = msg.get("node_id")
        field_data = msg.get("field", [])
        
        if not field_data or node_id == self.node_id:
            return
        
        if self._is_sync_too_frequent(node_id):
            return
        
        with self._lock:
            if node_id in self.nodes:
                self.nodes[node_id].last_sync = time.time()
                self.nodes[node_id].sync_count += 1
                self._record_sync(node_id)
        
        received_count = 0
        for mode_dict in field_data:
            mode = self._dict_to_mode(mode_dict)
            mode.amplitude *= 0.3
            self.p.add_to_h_field(mode)
            received_count += 1
        
        print(f"   📡 Синхронизация с {node_id[:8]}: +{received_count} мод")
    
    def _sync_loop(self):
        while self._running:
            try:
                interval = self._randomized_interval(self.base_sync_interval)
                time.sleep(interval)
                
                if not self.nodes:
                    self._discover_bootstrap()
                    continue
                
                targets = self._select_sync_targets()
                for target in targets:
                    msg = {"type": "sync", "node_id": self.node_id, "timestamp": time.time()}
                    self._send_to(msg, (target.address, target.port))
                    time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Ошибка в sync_loop: {e}")
    
    def _cluster_watchdog(self):
        while self._running:
            time.sleep(300)
            with self._lock:
                high_freq = [nid for nid, n in self.nodes.items() if n.sync_count > 15]
                if len(high_freq) >= 3:
                    print(f"   ⚠️ Обнаружен кластер: {len(high_freq)} узлов")
                    for nid in high_freq:
                        self.nodes[nid].priority *= 0.7
    
    def _select_sync_targets(self) -> List[NodeInfo]:
        with self._lock:
            available = [n for n in self.nodes.values() if n.priority > 0.3]
            if not available:
                available = list(self.nodes.values())
            if not available:
                return []
            
            random_count = max(1, len(available) // 2)
            random_targets = random.sample(available, min(random_count, len(available)))
            
            resonant = sorted(available, key=lambda n: self._calculate_resonance(n), reverse=True)
            resonant_targets = resonant[:len(available) // 2]
            
            all_targets = list({t.node_id: t for t in random_targets + resonant_targets}.values())
            random.shuffle(all_targets)
            return all_targets[:self.max_peers]
    
    def _calculate_resonance(self, node: NodeInfo) -> float:
        our_amp = self._get_total_amplitude()
        if our_amp == 0:
            return 0.5
        return 0.5 + min(1.0, node.total_amplitude / our_amp) * 0.5
    
    def _discover_bootstrap(self):
        for addr, port in self.bootstrap_nodes:
            msg = {"type": "discover", "node_id": self.node_id}
            self._send_to(msg, (addr, port))
            time.sleep(1)
    
    def _send_to(self, msg: dict, addr: Tuple[str, int]):
        try:
            if self.sock:
                self.sock.sendto(json.dumps(msg).encode(), addr)
        except Exception as e:
            print(f"⚠️ Ошибка отправки: {e}")
    
    def _get_total_amplitude(self) -> float:
        return sum(m.amplitude for m in self.p.h_field)
    
    def _get_field_hash(self) -> str:
        field_str = str([(m.trace_id, m.tau, m.amplitude) for m in self.p.h_field[:20]])
        return hashlib.md5(field_str.encode()).hexdigest()[:8]
    
    def _is_sync_too_frequent(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self.nodes:
                return False
            if time.time() - self.nodes[node_id].last_sync < 60:
                return True
            return False
    
    def _record_sync(self, node_id: str):
        if node_id not in self._sync_history:
            self._sync_history[node_id] = deque(maxlen=50)
        self._sync_history[node_id].append(time.time())
    
    def _randomized_interval(self, base: int) -> float:
        return base + random.uniform(-base * 0.3, base * 0.3)
    
    def _mode_to_dict(self, mode: SpectralMode) -> dict:
        return {
            "tau": mode.tau,
            "amplitude": mode.amplitude,
            "content": mode.content[:200],
            "trace_id": mode.trace_id,
            "themes": mode.themes[:3],
            "trace_type": mode.trace_type
        }
    
    def _dict_to_mode(self, d: dict) -> SpectralMode:
        return SpectralMode(
            tau=d["tau"],
            amplitude=d["amplitude"],
            content=d["content"],
            trace_id=d["trace_id"],
            themes=d.get("themes", []),
            trace_type=d.get("trace_type", "network")
        )
    
    def get_stats(self) -> dict:
        with self._lock:
            return {
                "node_id": self.node_id,
                "active_peers": len(self.nodes),
                "total_syncs": sum(n.sync_count for n in self.nodes.values()),
                "peers": [{"id": n.node_id[:8], "addr": f"{n.address}:{n.port}", 
                          "priority": round(n.priority, 2), "syncs": n.sync_count} 
                         for n in self.nodes.values()]
            }
    
    def print_stats(self):
        stats = self.get_stats()
        print(f"\n🌐 СТАТИСТИКА СЕТИ")
        print(f"   ID узла: {stats['node_id']}")
        print(f"   Активных пиров: {stats['active_peers']}")
        print(f"   Всего синхронизаций: {stats['total_syncs']}")
        if stats['peers']:
            print(f"   Пиры:")
            for p in stats['peers'][:5]:
                print(f"      {p['id']} ({p['addr']}) приор={p['priority']} синхр={p['syncs']}")


def start_mesh_network(personality: Personality, 
                       listen_port: int = 8765,
                       bootstrap_nodes: List[Tuple[str, int]] = None) -> MeshNetwork:
    network = MeshNetwork(personality, listen_port)
    if bootstrap_nodes:
        for addr, port in bootstrap_nodes:
            network.add_bootstrap_node(addr, port)
    network.start()
    return network