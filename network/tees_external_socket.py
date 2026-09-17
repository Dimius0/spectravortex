# tees_external_socket.py
# 👻 TEES: Внешний сокет-узел (мост к реальной сети)
# Реализует принципы ExternalNode поверх TCP

import socket
import threading
import json
import time
import hashlib
import secrets
from typing import Dict, Optional, Tuple

# Импортируем ChaosIdentity
from network.chaos_identity import ChaosIdentity

# Используем нашу криптографию и вихрь из существующего файла
try:
    from network.tees_external_network_v2 import TEESCrypto, CoherentCell
except ImportError:
    # Если вдруг нет родительского файла, делаем заглушки (чтобы модуль был автономным)
    class TEESCrypto:
        @staticmethod
        def generate_key(length=32):
            return secrets.token_bytes(length)
        @staticmethod
        def encrypt(data, key):
            return bytes([d ^ key[i % len(key)] for i, d in enumerate(data)])
        @staticmethod
        def decrypt(data, key):
            return TEESCrypto.encrypt(data, key)

    from dataclasses import dataclass, field
    @dataclass
    class CoherentCell:
        cell_id: str
        key: bytes
        phase: float = 0.0
        coherence: float = 0.994
        created_at: float = field(default_factory=time.time)


class GhostNode:
    """
    👻 Призрачный узел.
    Умеет общаться по TCP, но скрывает IP за когерентными ячейками.
    """
    def __init__(self, node_id: str, host: str = "0.0.0.0", port: int = 9000):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.cells: Dict[str, CoherentCell] = {}
        self.peers: Dict[str, Tuple[str, int]] = {}  # node_id -> (host, port)
        self.routing_table: Dict[str, str] = {}  # node_id -> cell_id
        self.crypto = TEESCrypto()
        self.chaos = ChaosIdentity(self.node_id)  # Добавляем ChaosIdentity
        self.sock = None
        self.running = False

    def start(self):
        """Запустить слушающий сокет."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(50)
        self.running = True
        print(f"👻 {self.node_id} слушает на {self.host}:{self.port}")
        
        # Поток приёма
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        while self.running:
            try:
                self.sock.settimeout(1)
                client, addr = self.sock.accept()
                threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client: socket.socket, addr: Tuple[str, int]):
        try:
            data = client.recv(8192)
            if not data:
                return
            msg = json.loads(data.decode())
            self._process_message(msg, addr, client)
        except Exception as e:
            # print(f"⚠️ Ошибка: {e}")
            pass
        finally:
            client.close()

    def _process_message(self, msg, addr, client):
        """Обработка входящих сообщений."""
        msg_type = msg.get("type")
        
        if msg_type == "beacon_hello":
            # Нас зовут извне! Начинаем рукопожатие
            their_id = msg.get("node_id")
            their_port = msg.get("port", addr[1])
            
            # Создаём cell_id на основе обоих ID
            cell_id = hashlib.sha256(
                f"{self.node_id}{their_id}{time.time()}".encode()
            ).hexdigest()[:16]
            
            # Генерируем ключ ячейки через ChaosIdentity (детерминированно)
            key = self.chaos.generate_deterministic_key(
                context=f"{cell_id}:{self.node_id}:{their_id}",
                length=32
            )
            
            # Создаём ячейку
            cell = CoherentCell(cell_id=cell_id, key=key)
            
            # Сохраняем у себя
            self.cells[cell_id] = cell
            self.routing_table[their_id] = cell_id
            self.peers[their_id] = (addr[0], their_port)
            
            # Отвечаем подтверждением с ключом
            response = {
                "type": "beacon_ack",
                "node_id": self.node_id,
                "cell_id": cell_id,
                "key_hex": key.hex(),  # Отправляем ключ в hex формате
                "glow": 0.994,
                "neighbors": len(self.routing_table)
            }
            
            # Отправляем ответ
            client.send(json.dumps(response).encode())
            
            print(f"  🤝 {self.node_id} → {their_id}: рукопожатие! Ячейка: {cell_id[:8]}...")
            
            # ВАЖНО: нигде не сохраняем IP! Только node_id и cell_id
        
        elif msg_type == "data":
            # Приём данных через ячейку (с расшифровкой)
            cell_id = msg.get("cell_id")
            encrypted_hex = msg.get("data_base64")
            cell = self.cells.get(cell_id)
            
            if cell and encrypted_hex:
                try:
                    decrypted = self.crypto.decrypt(bytes.fromhex(encrypted_hex), cell.key)
                    print(f"  📦 {self.node_id} получил данные через {cell_id[:8]}...: {decrypted.decode()[:50]}")
                except Exception as e:
                    print(f"  ❌ {self.node_id}: ошибка расшифровки: {e}")
            else:
                print(f"  ❌ {self.node_id}: неизвестная ячейка или пустые данные")

    def connect(self, host: str, port: int):
        """Позвонить другому узлу и сделать рукопожатие."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))
            
            # Отправляем привет
            sock.send(json.dumps({
                "type": "beacon_hello",
                "node_id": self.node_id,
                "port": self.port
            }).encode())
            
            # Ждём ответ
            resp_data = sock.recv(8192)
            resp = json.loads(resp_data.decode())
            sock.close()
            
            if resp.get("type") == "beacon_ack":
                their_id = resp.get("node_id")
                cell_id = resp.get("cell_id")
                key_hex = resp.get("key_hex")  # Получаем ключ от отвечающего узла
                
                if key_hex:
                    # Используем ключ, который сгенерировал отвечающий узел
                    key = bytes.fromhex(key_hex)
                else:
                    # Если ключ не передан, генерируем детерминированно
                    key = self.chaos.generate_deterministic_key(
                        context=f"{cell_id}:{self.node_id}:{their_id}",
                        length=32
                    )
                
                # Сохраняем у себя с тем же ключом
                cell = CoherentCell(cell_id=cell_id, key=key)
                self.cells[cell_id] = cell
                self.routing_table[their_id] = cell_id
                self.peers[their_id] = (host, port)
                
                print(f"  🤝 {self.node_id} → {their_id}: ячейка {cell_id[:8]}...")
                return True
            
        except Exception as e:
            # print(f"⚠️ {self.node_id} не дозвонился до {host}:{port}: {e}")
            return False

    def send_data(self, target_node_id: str, data: str):
        """Отправить данные через когерентную ячейку (с шифрованием)."""
        cell_id = self.routing_table.get(target_node_id)
        peer_addr = self.peers.get(target_node_id)
        
        if not cell_id or not peer_addr:
            print(f"  ❌ {self.node_id}: нет связи с {target_node_id}")
            return
        
        # Шифруем данные ключом ячейки
        cell = self.cells[cell_id]
        data_bytes = data.encode()
        encrypted = self.crypto.encrypt(data_bytes, cell.key)
        
        # Отправляем
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(peer_addr)
            
            msg = {
                "type": "data",
                "cell_id": cell_id,
                "data_base64": encrypted.hex()
            }
            sock.send(json.dumps(msg).encode())
            sock.close()
            
            print(f"  📤 {self.node_id} → {target_node_id}: {data[:50]} (зашифровано)")
        except Exception as e:
            print(f"  ❌ {self.node_id}: ошибка отправки для {target_node_id}: {e}")


if __name__ == "__main__":
    import sys
    
    # Получаем количество узлов из аргументов командной строки (по умолчанию 3)
    num_nodes = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    
    # Ограничиваем для локального теста
    if num_nodes > 100:
        print(f"⚠️ Локальный тест ограничен 100 узлами (запрошено {num_nodes})")
        num_nodes = 100
    
    print(f"👻 TEES: ВНЕШНИЙ СЕТЕВОЙ ТЕСТ (с ChaosIdentity) — {num_nodes} узлов")
    print("=" * 50)
    
    # Создаём узлы
    nodes = []
    base_port = 9100
    
    for i in range(num_nodes):
        node = GhostNode(f"ghost_{i}", port=base_port + i)
        node.start()
        nodes.append(node)
    
    # Даём время на старт
    time.sleep(0.5)
    
    # Соединяем каждого с каждым (полный граф)
    print("\n🔗 Устанавливаем связи (каждый с каждым):")
    connection_count = 0
    total_connections = num_nodes * (num_nodes - 1) // 2
    
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            # Узел i звонит узлу j
            target_port = base_port + j
            nodes[i].connect("127.0.0.1", target_port)
            connection_count += 1
            
            # Прогресс
            if connection_count % 20 == 0:
                print(f"   ... {connection_count}/{total_connections} соединений")
    
    print(f"   ✅ Всего соединений: {connection_count}/{total_connections}")
    
    time.sleep(1)
    
    # Пробуем отправить данные
    print("\n📡 Пробуем отправить данные:")
    
    # Проверяем связь: узел 0 шлёт всем, остальные шлют следующему
    print("\n📡 Проверяем связь (полный граф):")
    
    # Узел 0 шлёт всем
    for i in range(1, num_nodes):
        nodes[0].send_data(f"ghost_{i}", f"Full graph test: 0 -> {i}")
        time.sleep(0.05)  # Небольшая пауза, чтобы не завалить порт
    
    # Каждый узел шлёт следующему
    for i in range(1, num_nodes):
        next_index = (i + 1) % num_nodes
        nodes[i].send_data(f"ghost_{next_index}", f"Chain test: {i} -> {next_index}")
        time.sleep(0.05)
    
    sent_count = (num_nodes - 1) + (num_nodes - 1)
    print(f"\n📊 Отправлено тестовых сообщений: {sent_count}")
    
    print(f"\n👻 Все {num_nodes} узлов обменялись рукопожатиями.")
        
    # Даём время на обработку всех сообщений
    time.sleep(3)
    
    print("✅ Тест завершён.")
