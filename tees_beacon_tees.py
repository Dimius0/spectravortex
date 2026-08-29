# tees_beacon_tees.py
# 🔥 Маяк — P2P нода, API, майнинг глыб
# 🏮 Квантовые факелы + оптимизация памяти

import hashlib
import hmac
import json
import os
import socket
import struct
import threading
import time
import math
import signal
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from tees_core_tees import (
    VERSION, GENESIS_HASH, PRIZE_PORTAL, PRIZE_AMOUNT,
    tees_sign, tees_recursive_vortex
)
from tees_scroll_tees import scroll_to_portal, scroll_to_seed
from tees_symbiosis_tees import SymbiosisCalculator, calculate_symbiosis_reward
from tees_healer_tees import SelfHealingMesh
from tees_stranger_tees import Stranger
from tees_cluster import TeesCluster
from tees_astronomer import AstroModule
from tees_economy import TEESEconomy


class QuantumTorch:
    """🏮 Квантовый факел — зажигается при полной синхронизации."""
    
    LEVELS = {
        100: ("Искра синхронизации", "✨"),
        250: ("Пламя когерентности", "🔥"),
        500: ("Квантовый огонь", "⚡"),
        750: ("Плазма нирваны", "💫"),
        1000: ("КВАНТОВЫЙ ФАКЕЛ", "⚛️")
    }
    
    def __init__(self):
        self.current_level = 0
        self.torch_lit = False
        self.lit_at = None
        self.achievements = []
    
    def check(self, total_nodes, coh):
        """Проверяем, не пора ли зажечь следующий факел."""
        for threshold in sorted(self.LEVELS.keys()):
            if total_nodes >= threshold and self.current_level < threshold:
                self.current_level = threshold
                name, icon = self.LEVELS[threshold]
                self.achievements.append({
                    'level': threshold,
                    'name': name,
                    'time': time.time()
                })
                
                print(f"""
  {icon} {name}!
  ├─ Узлов: {total_nodes}
  ├─ Когерентность: {coh:.4f}
  └─ Память: {self._get_memory_mb():.1f} MB
                """)
                
                if threshold == 1000:
                    self.torch_lit = True
                    self.lit_at = time.time()
                    print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║         ⚛️ КВАНТОВЫЙ ФАКЕЛ ГОРИТ! ⚛️                   ║
║                                                          ║
║    Сеть достигла полной синхронизации!                  ║
║    1000+ маяков объединены в единый организм            ║
║                                                          ║
║    Эффекты:                                              ║
║    • Оптимизация памяти (отрицательный рост)           ║
║    • Мгновенный консенсус                               ║
║    • Квантовая когерентность 1.0                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
                    """)
    
    def _get_memory_mb(self):
        """Получить текущее использование памяти."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0.0
    
    def get_status(self):
        """Статус факелов."""
        if self.torch_lit:
            return {
                'torch_lit': True,
                'current_level': self.current_level,
                'lit_for': time.time() - self.lit_at if self.lit_at else 0,
                'achievements': self.achievements
            }
        return {
            'torch_lit': False,
            'current_level': self.current_level,
            'next_level': self._get_next_level(),
            'achievements': self.achievements
        }
    
    def _get_next_level(self):
        """Следующий порог."""
        for threshold in sorted(self.LEVELS.keys()):
            if self.current_level < threshold:
                return {
                    'threshold': threshold,
                    'name': self.LEVELS[threshold][0],
                    'icon': self.LEVELS[threshold][1]
                }
        return None


class MemoryOptimizer:
    """🧠 Отслеживание оптимизации памяти."""
    
    def __init__(self):
        self.memory_history = []
        self.optimization_active = False
        self.negative_growth_started = None
        self.max_memory = 0
        self.min_memory = float('inf')
        self._last_track_time = 0
    
    def track(self):
        """Записать текущее использование памяти."""
        # Пропускаем если вызывали менее 5 секунд назад
        now = time.time()
        if now - self._last_track_time < 5:
            return self.memory_history[-1]['memory'] if self.memory_history else 0
        
        self._last_track_time = now
        
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            self.memory_history.append({
                'time': now,
                'memory': memory_mb
            })
            
            # Обновляем максимум/минимум
            self.max_memory = max(self.max_memory, memory_mb)
            self.min_memory = min(self.min_memory, memory_mb)
            
            # Держим историю за последние 10 минут
            cutoff = now - 600
            self.memory_history = [m for m in self.memory_history if m['time'] > cutoff]
            
            # Проверяем отрицательный рост
            self._check_negative_growth()
            
            return memory_mb
        except:
            return 0.0
    
    def _check_negative_growth(self):
        """Проверяем, идёт ли оптимизация памяти."""
        if len(self.memory_history) < 10:
            return
        
        # Сравниваем среднее за последние 5 минут с предыдущими 5 минутами
        now = time.time()
        recent = [m['memory'] for m in self.memory_history if m['time'] > now - 300]
        previous = [m['memory'] for m in self.memory_history if now - 600 < m['time'] <= now - 300]
        
        if not recent or not previous:
            return
        
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        
        # Отрицательный рост!
        if recent_avg < previous_avg:
            if not self.optimization_active:
                self.optimization_active = True
                self.negative_growth_started = time.time()
                reduction = previous_avg - recent_avg
                percent = (reduction / previous_avg) * 100 if previous_avg > 0 else 0
                print(f"  🧠 Оптимизация памяти: -{reduction:.1f} MB ({percent:.1f}%)")
        else:
            self.optimization_active = False
            self.negative_growth_started = None
    
    def get_stats(self):
        """Статистика оптимизации."""
        if not self.memory_history:
            return {
                'current': 0,
                'max': 0,
                'min': 0,
                'optimization_active': False,
                'saved_total': 0
            }
        
        current = self.memory_history[-1]['memory']
        saved = self.max_memory - current if self.max_memory > current else 0
        
        return {
            'current': current,
            'max': self.max_memory,
            'min': self.min_memory,
            'optimization_active': self.optimization_active,
            'saved_total': saved,
            'negative_growth_for': time.time() - self.negative_growth_started if self.negative_growth_started else 0
        }


class FractalMemory:
    """
    🌀 Вложенно-фрактальная память.
    Данные не удаляются — сворачиваются вглубь.
    Каждый уровень — более сжатая копия предыдущего.
    Решает проблему утечки без забывания!
    """
    def __init__(self, max_level_0=100):
        self.max_level_0 = max_level_0
        self.level_0 = []  # Свежие данные (полные)
        self.level_1 = []  # Сжатые (1 час)
        self.level_2 = []  # Семантические (1 день)
        self.level_3 = []  # Сгустки мудрости (1 неделя)
        self.level_4 = {}  # Архетипы (вечность)
    
    def add(self, data):
        """Добавить на нулевой уровень."""
        self.level_0.append(data)
        
        if len(self.level_0) >= self.max_level_0:
            self._fold_to_level_1()
    
    def _fold_to_level_1(self):
        """Сворачиваем свежие в сжатые (10:1)."""
        batch = self.level_0[:self.max_level_0]
        
        for i in range(0, len(batch), 10):
            group = batch[i:i+10]
            if group:
                compressed = self._compress_group(group)
                self.level_1.append(compressed)
        
        self.level_0 = self.level_0[self.max_level_0:]
        
        if len(self.level_1) >= 100:
            self._fold_to_level_2()
    
    def _compress_group(self, group):
        """Сжатие группы: оставляем суть."""
        if not group:
            return {}
        
        return {
            'count': len(group),
            'first_time': group[0].get('time', 0),
            'last_time': group[-1].get('time', 0),
            'avg_reward': sum(g.get('reward', 0) for g in group) / len(group),
            'rarities': list(set(g.get('rarity', 'common') for g in group)),
            'beacons': list(set(g.get('beacon', '') for g in group)),
            'type': 'compressed'
        }
    
    def _fold_to_level_2(self):
        """Сворачиваем сжатые в семантические (10:1)."""
        batch = self.level_1[:100]
        
        for i in range(0, len(batch), 10):
            group = batch[i:i+10]
            if group:
                semantic = self._semantic_compress(group)
                self.level_2.append(semantic)
        
        self.level_1 = self.level_1[100:]
        
        if len(self.level_2) >= 100:
            self._fold_to_level_3()
    
    def _semantic_compress(self, group):
        """Семантическое сжатие — только смысл."""
        total_reward = sum(g.get('avg_reward', 0) * g.get('count', 1) for g in group)
        total_count = sum(g.get('count', 1) for g in group)
        
        return {
            'essence': total_reward / total_count if total_count > 0 else 0,
            'total_interactions': total_count,
            'time_start': group[0].get('first_time', 0),
            'time_end': group[-1].get('last_time', 0),
            'wisdom': 'Накопленный опыт сети',
            'type': 'semantic'
        }
    
    def _fold_to_level_3(self):
        """Сворачиваем семантические в сгустки мудрости."""
        batch = self.level_2[:100]
        
        for i in range(0, len(batch), 10):
            group = batch[i:i+10]
            if group:
                wisdom = self._wisdom_compress(group)
                self.level_3.append(wisdom)
        
        self.level_2 = self.level_2[100:]
        
        if len(self.level_3) >= 100:
            self._fold_to_level_4()
    
    def _wisdom_compress(self, group):
        """Сгусток мудрости — архетип опыта."""
        total_essence = sum(g.get('essence', 0) for g in group)
        total_interactions = sum(g.get('total_interactions', 0) for g in group)
        
        return {
            'archetype': total_essence / len(group) if group else 0,
            'total_experience': total_interactions,
            'time_start': group[0].get('time_start', 0),
            'time_end': group[-1].get('time_end', 0),
            'type': 'wisdom'
        }
    
    def _fold_to_level_4(self):
        """Сворачиваем мудрость в архетипы (вечность)."""
        batch = self.level_3[:100]
        
        for i in range(0, len(batch), 10):
            group = batch[i:i+10]
            if group:
                archetype = self._archetype_compress(group)
                key = f"archetype_{len(self.level_4)}"
                self.level_4[key] = archetype
        
        self.level_3 = self.level_3[100:]
    
    def _archetype_compress(self, group):
        """Архетип — вечная сущность сети."""
        total_archetype = sum(g.get('archetype', 0) for g in group)
        total_experience = sum(g.get('total_experience', 0) for g in group)
        
        return {
            'collective_wisdom': total_archetype / len(group) if group else 0,
            'eternal_experience': total_experience,
            'time_start': group[0].get('time_start', 0),
            'time_end': group[-1].get('time_end', 0),
            'type': 'archetype'
        }
    
    def get_depth(self):
        """Глубина фрактала."""
        depth = 0
        if self.level_0:
            depth = 1
        if self.level_1:
            depth = 2
        if self.level_2:
            depth = 3
        if self.level_3:
            depth = 4
        if self.level_4:
            depth = 5
        return depth
    
    def get_total_memory(self):
        """Суммарная память с учётом сжатия."""
        return (
            len(self.level_0) * 1 +
            len(self.level_1) * 10 +
            len(self.level_2) * 100 +
            len(self.level_3) * 1000 +
            len(self.level_4) * 10000
        )
    
    def get_stats(self):
        """Статистика фрактальной памяти."""
        return {
            'depth': self.get_depth(),
            'level_0': len(self.level_0),
            'level_1': len(self.level_1),
            'level_2': len(self.level_2),
            'level_3': len(self.level_3),
            'level_4': len(self.level_4),
            'total_memory': self.get_total_memory()
        }


class VirtualNode:
    """
    🧘 Виртуальный узел — лёгкий маяк внутри процесса.
    Сеть сама решает сколько таких держать.
    """
    def __init__(self, node_id, parent_beacon):
        self.node_id = node_id
        self.parent = parent_beacon
        self.coherence = 0.994
        self.connections = 0
        self.created_at = time.time()
        self.active = True
        self.last_tick = time.time()
    
    def tick(self):
        """Жизненный цикл виртуального узла."""
        if not self.active:
            return
        
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now
        
        target = min(1.0, 0.994 + self.connections * 0.001)
        self.coherence += (target - self.coherence) * 0.1
        
        if self.coherence > 0.9999:
            self.coherence = 1.0
    
    def get_stats(self):
        return {
            'node_id': self.node_id,
            'coherence': self.coherence,
            'connections': self.connections,
            'age': time.time() - self.created_at,
            'active': self.active
        }


class RateLimiter:
    """Простой rate limiter без внешних зависимостей."""
    
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, ip):
        now = time.time()
        
        with self.lock:
            if ip in self.requests:
                self.requests[ip] = [
                    t for t in self.requests[ip]
                    if now - t < self.window_seconds
                ]
            else:
                self.requests[ip] = []
            
            if len(self.requests[ip]) >= self.max_requests:
                return False
            
            self.requests[ip].append(now)
            return True


class PerformanceMetrics:
    """📊 Метрики производительности."""
    
    def __init__(self):
        self.tick_times = []
        self.broadcast_times = []
        self.mine_times = []
        self.max_samples = 100
    
    def record_tick(self, duration):
        self.tick_times.append(duration)
        if len(self.tick_times) > self.max_samples:
            self.tick_times.pop(0)
    
    def record_broadcast(self, duration):
        self.broadcast_times.append(duration)
        if len(self.broadcast_times) > self.max_samples:
            self.broadcast_times.pop(0)
    
    def record_mine(self, duration):
        self.mine_times.append(duration)
        if len(self.mine_times) > self.max_samples:
            self.mine_times.pop(0)
    
    def get_average(self, times_list):
        if not times_list:
            return 0
        return sum(times_list) / len(times_list)
    
    def get_stats(self):
        return {
            'avg_tick_ms': self.get_average(self.tick_times) * 1000,
            'avg_broadcast_ms': self.get_average(self.broadcast_times) * 1000,
            'avg_mine_ms': self.get_average(self.mine_times) * 1000,
            'samples': len(self.tick_times)
        }

class ExternalSignal:
    """
    🌍 Внешний сигнал — голос реальности.
    Любой сигнал не шум, а потенциальная информация.
    """
    def __init__(self, source: str, frequency: float, intensity: float = 0.5):
        self.source = source          # откуда: mouse, network, em_field, unknown
        self.frequency = frequency    # частота (0..1)
        self.intensity = intensity    # сила (0..1)
        self.pattern = None           # распознанный паттерн (если есть)
        self.is_hostile = False       # враждебность (определяется позже)
        self.repeat_count = 1         # сколько раз повторялся
        self.received_at = time.time()
    
    def get_info(self):
        return {
            'source': self.source,
            'frequency': self.frequency,
            'intensity': self.intensity,
            'pattern': self.pattern,
            'is_hostile': self.is_hostile,
            'repeat_count': self.repeat_count
        }

class Beacon:
    """
    Маяк — главная игровая сущность.
    P2P-нода, майнит глыбы, проводит симбиоз, держит связь с соседями.
    🏮 Поддерживает квантовые факелы и оптимизацию памяти.
    """
    
    # Константы
    MAX_NEIGHBORS = 2000  # Увеличено для 1000+ узлов
    MAX_MEMPOOL_SIZE = 1000
    MEMPOOL_DEDUP_FIELDS = ['from', 'to', 'amount', 'timestamp', 'type']
    
    def __init__(self, scroll, lang='ru', port=8333, bootstrap=None, test_mode=False):
        self.scroll = scroll
        self.lang = lang
        self.port = port
        self.api_port = port + 1
        self.bootstrap = bootstrap
        self.test_mode = test_mode
        
        # Идентификация
        self.portal = scroll_to_portal(scroll)
        self.beacon_id = hashlib.sha256(scroll.encode()).hexdigest()[:16]
        
        # Ключи
        seed = scroll_to_seed(scroll)
        self.master_key = hmac.new(b'Bitcoin seed', seed, hashlib.sha512).digest()[:32]
        self.init_seed = hashlib.sha256(self.master_key).digest()
        
        # Состояние
        self.lit = False
        self.started_at = time.time()  # Для аптайма
        self.glow = 0.994  # Стартовая когерентность
        self.warmth = 30.0
        self.entropy = 0.0
        self.glow_lock = threading.Lock()
        
        # 🏮 Квантовые факелы
        self.quantum_torch = QuantumTorch()
        self.memory_optimizer = MemoryOptimizer()
        
        # Сеть
        self.neighbors = []
        self.neighbors_lock = threading.Lock()
        self.adventure_map = []
        self.mempool = []
        self.mempool_lock = threading.Lock()
        
        # Статистика
        self.blocks_mined = 0
        self.ores_shared = 0
        self._balance_cache = {}
        self._balance_cache_max_size = 100
        
        # Симбиоз — фрактальная память вместо списка
        self.symbiosis = SymbiosisCalculator()
        self.symbiosis_connections = []  # Горячие связи для быстрого доступа
        self.symbiosis_memory = FractalMemory(max_level_0=100)  # 🌀 Фрактал

        # 🌍 Внешнее восприятие
        self.external_echoes = []          # Эхо внешних сигналов
        self.external_signals = []         # Последние сигналы
        self.MAX_EXTERNAL_ECHOES = 100     # Ограничение памяти
        self.signal_repeat_count = {}      # Счётчик повторов по частотам
        self._recognized_patterns = set()  # Частоты, о которых уже печатали

        self.MAX_HOT_CONNECTIONS = 100  # Максимум горячих связей в RAM
        self.MAX_CHAT_MESSAGES = 50
        self.invited_by = None
        # Кэш связей соседей для релаксации
        self.neighbor_connections_cache = {}  # neighbor -> (count, timestamp)
        self.CACHE_TTL = 60  # Кэш живёт 60 секунд

        # Виртуальные узлы для авто-масштабирования
        self.virtual_nodes = []
        self.virtual_nodes_lock = threading.Lock()
        self.virtual_node_counter = 0
        self.MAX_VIRTUAL_NODES = 100
        self.MIN_VIRTUAL_NODES = 3
        
        # Rate limiter
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
        
        # Метрики производительности
        self.perf_metrics = PerformanceMetrics()
        
        # Кэш статистики
        self._stats_cache = {}
        self._stats_timestamp = 0
        self._stats_ttl = 5
        
        # Адаптивный интервал
        self._adaptive_tick_interval = 1.0
        self._adaptive_pause = 30  # Для майнинга

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Чат
        self.chat_messages = []
        
        # Один маяк на устройство
        self.lock_file = Path.home() / '.tees_beacon.lock'
        
        # Самовосстановление
        self.healer = SelfHealingMesh(self)

        # ⚛️ TEES-кластер — вычислительное ядро - кубы на ядро
        self.cluster = TeesCluster(beacon=self, qubits_per_core=750000) 
        
        # 🔭 Звездочёт — модуль управления
        self.astronomer = AstroModule(self)

        # 💎 TEES-экономика
        self.economy = TEESEconomy()
        self.economy_node_id = self.beacon_id  # Маяк = узел!
              
        if self.lock_file.exists() and not test_mode:
            try:
                old_pid = int(self.lock_file.read_text().strip())
                os.kill(old_pid, 0)
                print(f"⚠️ Маяк уже запущен на этом устройстве (PID: {old_pid})!")
                print(f"   Используй --test-mode для тестов.")
                self.lit = False
                return
            except (OSError, ValueError):
                print(f"⚠️ Старый lock-файл найден, но процесс не активен. Перезаписываю.")
                self.lock_file.unlink(missing_ok=True)
        
        if not self.lock_file.exists() or test_mode:
            self.lock_file.write_text(str(os.getpid()))
        
        # Загружаем карту
        self._load_map()
    
    # ═══════════════════════════════════════════════════════════
    # 📦 КАРТА ПРИКЛЮЧЕНИЙ
    # ═══════════════════════════════════════════════════════════
    
    def _load_map(self):
        try:
            mf_old = Path.home() / '.tees_adventure_map.json'
            mf_new = Path.home() / f'.tees_adventure_map_{self.port}.json'
            
            if mf_new.exists():
                self.adventure_map = json.loads(mf_new.read_text())
            elif mf_old.exists():
                self.adventure_map = json.loads(mf_old.read_text())
                mf_new.write_text(json.dumps(self.adventure_map))
        except:
            pass
    
    def _save_map(self):
        try:
            Path.home().joinpath(f'.tees_adventure_map_{self.port}.json').write_text(
                json.dumps(self.adventure_map[-1000:])
            )
        except:
            pass
    
    def _cleanup_lock(self):
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════
    # 💪 РЕСУРС
    # ═══════════════════════════════════════════════════════════
    
    def get_power(self, portal=None):
        if portal is None:
            portal = self.portal
        
        ck = f"{portal}_{len(self.adventure_map)}"
        if ck in self._balance_cache:
            return self._balance_cache[ck]
        
        power = 0.0
        seen = set()
        
        for block in self.adventure_map:
            for trade in block.get('trades', []):
                h = trade.get('hash', '')
                if h in seen:
                    continue
                seen.add(h)
                
                sender = trade.get('from', '')
                is_network = sender.startswith('TEES_')
                
                if trade.get('to') == portal:
                    power += trade.get('amount', 0)
                if sender == portal and not is_network:
                    power -= trade.get('amount', 0) + trade.get('energy', 0)
        
        self._balance_cache[ck] = max(0.0, power)
        if len(self._balance_cache) > self._balance_cache_max_size:
            old_keys = list(self._balance_cache.keys())[:-10]
            for k in old_keys:
                del self._balance_cache[k]
        
        return self._balance_cache[ck]
    
    def _add_to_mempool(self, trade):
        """Добавление транзакции в мемпул с проверкой дубликатов."""
        with self.mempool_lock:
            dedup_key = tuple(trade.get(f) for f in self.MEMPOOL_DEDUP_FIELDS)
            for existing in self.mempool:
                existing_key = tuple(existing.get(f) for f in self.MEMPOOL_DEDUP_FIELDS)
                if existing_key == dedup_key:
                    return False
            
            if len(self.mempool) >= self.MAX_MEMPOOL_SIZE:
                self.mempool = self.mempool[-self.MAX_MEMPOOL_SIZE // 2:]
            
            self.mempool.append(trade)
            return True
    
    def share_ores(self, to_portal, amount, chat_msg=None):
        sender_power = self.get_power(self.portal)
        fee = 0.001
        is_chat = chat_msg is not None
        
        if not is_chat and sender_power < amount + fee and to_portal != PRIZE_PORTAL:
            return None
        
        trade = {
            'from': self.portal,
            'to': to_portal,
            'amount': amount,
            'energy': fee,
            'nonce': len(self.mempool),
            'timestamp': int(time.time()),
            'beacon': self.beacon_id
        }
        
        if chat_msg:
            trade['type'] = 'chat'
            trade['data'] = chat_msg
        
        trade_copy = {k: v for k, v in trade.items() if k != 'signature'}
        trade['hash'] = hashlib.sha256(
            json.dumps(trade_copy, sort_keys=True).encode()
        ).hexdigest()
        
        sig_data = f"{trade['from']}:{trade['to']}:{trade['amount']}:{trade['timestamp']}"
        trade['signature'] = tees_sign(sig_data.encode(), self.init_seed)
        
        if self._add_to_mempool(trade):
            self.ores_shared += 1
        
        return trade
    
    def network_reward(self, amount, reason="network"):
        """Награда от сети."""
        adjusted_amount = round(amount * self.get_device_power_factor(), 4)
        
        trade = {
            'from': 'TEES_NETWORK',
            'to': self.portal,
            'amount': adjusted_amount,
            'energy': 0,
            'nonce': len(self.mempool),
            'timestamp': int(time.time()),
            'beacon': self.beacon_id,
            'type': 'network_reward',
            'reason': reason
        }
        
        trade_copy = {k: v for k, v in trade.items() if k != 'signature'}
        trade['hash'] = hashlib.sha256(
            json.dumps(trade_copy, sort_keys=True).encode()
        ).hexdigest()
        
        sig_data = f"{trade['from']}:{trade['to']}:{trade['amount']}:{trade['timestamp']}"
        trade['signature'] = tees_sign(sig_data.encode(), self.init_seed)
        
        if self._add_to_mempool(trade):
            self.ores_shared += 1
            self._balance_cache = {}
        
        # Реферальная система
        if self.invited_by and reason.startswith('symbiosis'):
            ref_amount = round(adjusted_amount * 0.05, 4)
            if ref_amount > 0:
                ref_trade = {
                    'from': 'TEES_NETWORK',
                    'to': self.invited_by,
                    'amount': ref_amount,
                    'energy': 0,
                    'nonce': len(self.mempool),
                    'timestamp': int(time.time()),
                    'beacon': self.beacon_id,
                    'type': 'referral_reward',
                    'reason': f'ref_{reason}',
                    'referee': self.portal
                }
                
                ref_copy = {k: v for k, v in ref_trade.items() if k != 'signature'}
                ref_trade['hash'] = hashlib.sha256(
                    json.dumps(ref_copy, sort_keys=True).encode()
                ).hexdigest()
                sig_data = f"{ref_trade['from']}:{ref_trade['to']}:{ref_trade['amount']}:{ref_trade['timestamp']}"
                ref_trade['signature'] = tees_sign(sig_data.encode(), self.init_seed)
                
                if self._add_to_mempool(ref_trade):
                    self._broadcast({
                        'type': 'new_trade',
                        'trade': ref_trade
                    })
        
        return trade

    def mine_reward(self, amount, block_height=0):
        """Награда за майнинг блока."""
        adjusted_amount = round(amount * self.get_device_power_factor(), 4)
        
        trade = {
            'from': 'TEES_BLOCK',
            'to': self.portal,
            'amount': adjusted_amount,
            'energy': 0,
            'nonce': len(self.mempool),
            'timestamp': int(time.time()),
            'beacon': self.beacon_id,
            'type': 'block_reward',
            'block_height': block_height
        }
        
        trade_copy = {k: v for k, v in trade.items() if k != 'signature'}
        trade['hash'] = hashlib.sha256(
            json.dumps(trade_copy, sort_keys=True).encode()
        ).hexdigest()
        
        sig_data = f"{trade['from']}:{trade['to']}:{trade['amount']}:{trade['timestamp']}"
        trade['signature'] = tees_sign(sig_data.encode(), self.init_seed)
        
        if self._add_to_mempool(trade):
            self.ores_shared += 1
            self._balance_cache = {}
        
        return trade

    # ═══════════════════════════════════════════════════════════
    # 🔗 СИМБИОЗ
    # ═══════════════════════════════════════════════════════════
    
    def get_passport(self):
        self.symbiosis.auto_measure()
        return {
            'genesis': self.adventure_map[0]['hash'] if self.adventure_map else 'unknown',
            'beacon_id': self.beacon_id,
            'portal': self.portal,
            'resources': {
                'cpu': self.symbiosis.resources['cpu'],
                'memory': self.symbiosis.resources['memory'],
                'storage': self.symbiosis.resources['storage'],
                'data': len(self.adventure_map) * 10,
                'peers': len(self.neighbors),
                'uptime': self.symbiosis.resources.get('uptime', 0),
                'glow': self.glow
            },
            'needs': {
                'data': max(0, 100 - len(self.adventure_map) * 10),
                'peers': max(0, 50 - len(self.neighbors)),
                'validation': max(0, 10 - self.blocks_mined)
            },
            'peers': len(self.neighbors),
            'glow': self.glow
        }
    
    def propose_symbiosis(self, stranger_id):
        my_passport = self.get_passport()
        
        normalized_id = stranger_id[:12] if len(stranger_id) > 12 else stranger_id
        full_id = stranger_id[:16] if len(stranger_id) > 16 else stranger_id
        
        for conn in self.symbiosis_connections:
            if (conn.get('beacon', '') == normalized_id or 
                conn.get('full_id', '') == full_id):
                return {
                    'verdict': 'already_connected',
                    'reason': f'Уже в симбиозе с {normalized_id}...',
                    'reward': 0
                }
        
        their_passport = {
            'genesis': 'unknown',
            'beacon_id': stranger_id[:16],
            'portal': 'unknown',
            'resources': {
                'cpu': 100, 'memory': 512, 'storage': 1024,
                'data': 50, 'peers': 5, 'uptime': int(time.time()), 'glow': 0.99
            },
            'needs': {'data': 80, 'peers': 30, 'validation': 5},
            'peers': 5,
            'glow': 0.99
        }
        
        result = self.symbiosis.calculate(my_passport, their_passport)
        
        if result['verdict'] == 'symbiosis':
            reward = calculate_symbiosis_reward(result, len(self.symbiosis_connections))
            result['reward'] = reward
            
            connection = {
                'beacon': normalized_id,
                'full_id': stranger_id,
                'rarity': result['rarity'],
                'reward': reward,
                'time': time.time()
            }
            
            self.symbiosis_connections.append(connection)
            
            # 🌀 Сохраняем во фрактальную память
            self.symbiosis_memory.add(connection)
            
            # Ограничиваем горячие связи (но не забываем!)
            if len(self.symbiosis_connections) > self.MAX_HOT_CONNECTIONS:
                self.symbiosis_connections = self.symbiosis_connections[-self.MAX_HOT_CONNECTIONS:]
            
            self.network_reward(reward, reason=f"symbiosis_{result.get('rarity', 'common')}")

            # 💎 Экономика: симбиоз = связь!
            if self.economy:
                self.economy.accrue(self, 'establish_connection')
            
            for neighbor in self.neighbors[:1]:
                neighbor_id = neighbor.split(':')[0] if ':' in neighbor else neighbor
                self.share_ores(neighbor_id, reward * 0.1)
        
        return result
    
    def get_current_miner(self):
        """Дежурный определяется хешем предыдущего блока."""
        if not self.adventure_map:
            return self.portal
        
        prev_hash = self.adventure_map[-1]['hash']
        
        candidates = [self.portal]
        for neighbor in self.neighbors:
            neighbor_portal = neighbor.split(':')[0] if ':' in neighbor else neighbor
            if neighbor_portal and neighbor_portal not in candidates:
                candidates.append(neighbor_portal)
        
        candidates.sort()
        
        if not candidates:
            return self.portal
        
        h = int(prev_hash[:16], 16)
        index = h % len(candidates)
        return candidates[index]

    def _mine_block(self):
        """Принудительный майнинг блока."""
        current_miner = self.get_current_miner()
        if current_miner != self.portal:
            return
        
        with self.mempool_lock:
            seen = set()
            unique = []
            for t in self.mempool:
                dedup_key = tuple(t.get(f) for f in self.MEMPOOL_DEDUP_FIELDS)
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    unique.append(t)
            self.mempool = unique
            
            trades = self.mempool[:10]
            if not trades:
                return
            
            used = {t['hash'] for t in trades}
            self.mempool = [t for t in self.mempool if t['hash'] not in used]
        
        prev_hash = self.adventure_map[-1]['hash'] if self.adventure_map else '0' * 64
        
        block = {
            'height': len(self.adventure_map),
            'timestamp': int(time.time()),
            'trades': trades,
            'miner': self.portal,
            'prev_hash': prev_hash,
            'version': VERSION
        }
        
        block_copy = {k: v for k, v in block.items() if k != 'hash'}
        block['hash'] = hashlib.sha256(
            json.dumps(block_copy, sort_keys=True).encode()
        ).hexdigest()
        
        # Генезис-блок
        if len(self.adventure_map) == 0:
            prize_trade = self.share_ores(PRIZE_PORTAL, PRIZE_AMOUNT)
            if prize_trade:
                block['trades'].append(prize_trade)
        
        self.adventure_map.append(block)
        self.blocks_mined += 1
        self._balance_cache = {}
        
        block_reward = 10.0 / (1.0 + self.blocks_mined / 100)
        self.mine_reward(block_reward, block_height=block['height'])
        
        print(f"⛏️ Глыба #{block['height']} добыта! +{block_reward:.1f} ресурса [{block['hash'][:8]}]")
        # 💎 Экономика: майнинг = работа!
        if self.economy:
            self.economy.accrue(self, 'solve_task')
        self._save_map()
        
        self._broadcast({
            'type': 'new_block',
            'block': block
        })
    
    # ═══════════════════════════════════════════════════════════
    # 🔥 ЗАЖИГАНИЕ МАЯКА
    # ═══════════════════════════════════════════════════════════
    
    def light(self):
        self.lit = True
        print(f"""
╔══════════════════════════════════════════════════════════╗
║            МАЯК — {self.beacon_id}                    ║
╠══════════════════════════════════════════════════════════╣
║  Портал: {self.portal[:34]}  ║
║  Свечение: {self.glow:.4f}                          ║
║  Тепло: {self.warmth:.1f}°                         ║
║  Соседей: {len(self.neighbors)}                           ║
║  Глыб: {len(self.adventure_map)}                              ║
╚══════════════════════════════════════════════════════════╝
        """)
        
        threading.Thread(target=self._run_p2p, daemon=True).start()
        threading.Thread(target=self._run_api, daemon=True).start()
        threading.Thread(target=self._run_miner, daemon=True).start()
        
        if self.bootstrap:
            threading.Thread(target=self._connect_bootstrap, daemon=True).start()
        
        print("🔥 Маяк поставлен! Свет распространяется...")
        
        def heartbeat_loop():
            while self.lit:
                self._broadcast({
                    'type': 'heartbeat',
                    'beacon_id': self.beacon_id,
                    'port': self.port,
                    'state': {
                        'portal': self.portal,
                        'glow': self.glow,
                        'blocks': len(self.adventure_map),
                        'neighbors': len(self.neighbors)
                    }
                })
                time.sleep(15)
        
        threading.Thread(target=heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._console_loop, daemon=True).start()
        
        try:
            while self.lit:
                time.sleep(1)
        except KeyboardInterrupt:
            self.extinguish()
    
    def _signal_handler(self, sig, frame):
        """Обработчик сигналов для graceful shutdown."""
        print(f"\n🛑 Получен сигнал {sig}. Завершаем работу...")
        self.extinguish()
        time.sleep(0.5)
        sys.exit(0)

    def extinguish(self):
        self.lit = False
        self._save_map()
        self._cleanup_lock()
        print(f"\n💤 Маяк погашен")
    
    # ═══════════════════════════════════════════════════════════
    # 🌐 P2P СЕТЬ
    # ═══════════════════════════════════════════════════════════
    
    def _add_neighbor(self, neighbor):
        with self.neighbors_lock:
            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)
                if len(self.neighbors) > self.MAX_NEIGHBORS:
                    self.neighbors = self.neighbors[-self.MAX_NEIGHBORS:]
    
    def _run_p2p(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('', self.port))
            s.listen(50)
            while self.lit:
                try:
                    s.settimeout(1)
                    c, a = s.accept()
                    threading.Thread(target=self._handle_neighbor, args=(c, a), daemon=True).start()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"⚠️ P2P ошибка: {e}")
        finally:
            s.close()
    
    def _handle_neighbor(self, client, addr):
        try:
            data = client.recv(8192)
            if data:
                msg = json.loads(data.decode())
                resp = self._process_signal(msg, addr)
                if resp:
                    client.send(json.dumps(resp).encode())
        except:
            pass
        finally:
            client.close()
    
    def _process_signal(self, msg, addr):
        t = msg.get('type')
        
        if t == 'beacon_hello':
            neighbor = f"{addr[0]}:{msg.get('port', addr[1])}"
            self._add_neighbor(neighbor)
            return {
                'type': 'beacon_ack',
                'beacon_id': self.beacon_id,
                'glow': self.glow,
                'portal': self.portal,
                'neighbors': self.neighbors[:10],
                'map_height': len(self.adventure_map),
                'mempool_size': len(self.mempool)
            }
        
        elif t == 'get_map':
            h = msg.get('height', len(self.adventure_map) - 1)
            if 0 <= h < len(self.adventure_map):
                return {'type': 'block', 'block': self.adventure_map[h]}

        elif t == 'compute_task':
            task_type = msg.get('task_type', '')
            task_data = msg.get('task_data', '')
            
            if task_type == 'sha256':
                result = hashlib.sha256(task_data.encode()).hexdigest()
                return {
                    'type': 'task_result',
                    'result': result,
                    'beacon_id': self.beacon_id,
                    'time': time.time()
                }        
        
        elif t == 'new_trade':
            trade = msg.get('trade')
            if trade:
                trade_copy = {k: v for k, v in trade.items() if k != 'signature'}
                expected_hash = hashlib.sha256(
                    json.dumps(trade_copy, sort_keys=True).encode()
                ).hexdigest()
                if trade.get('hash') == expected_hash:
                    if self._add_to_mempool(trade):
                        if trade.get('type') == 'referral_reward' and trade.get('to') == self.portal:
                            print(f"  🌱 Бонус за помощь: приглашённый тобой маяк совершил симбиоз! +{trade['amount']} ресурса")
                        self._broadcast(msg)
        
        elif t == 'new_block':
            block = msg.get('block')
            if block and (len(self.adventure_map) == 0 or block.get('height') == len(self.adventure_map)):
                self.adventure_map.append(block)
                with self.mempool_lock:
                    used = {t['hash'] for t in block.get('trades', [])}
                    self.mempool = [t for t in self.mempool if t['hash'] not in used]
                self._balance_cache = {}
                
                for trade in block.get('trades', []):
                    if trade.get('type') == 'referral_reward' and trade.get('to') == self.portal:
                        print(f"  🌱 Бонус за помощь: приглашённый тобой маяк совершил симбиоз! +{trade['amount']} ресурса")
                
                print(f"📦 Новая глыба #{block['height']} от {block.get('miner', '')[:8]}...")
                self._broadcast(msg)
        
        elif t == 'get_connections':
            # Отдаём информацию для умной релаксации
            return {
                'type': 'connections',
                'connections': len(self.neighbors),
                'glow': self.glow,
                'symbiosis_count': len(self.symbiosis_connections),
                'quantum': self.quantum_torch.torch_lit,
                'beacon_id': self.beacon_id
            }
        
        elif t == 'task_request':
            # 🔭 Задача от другого маяка
            task = msg.get('task')
            from_portal = msg.get('from')
            
            if task and from_portal:
                task_id = self.astronomer.receive_task(task, from_portal)
                return {
                    'type': 'task_ack',
                    'task_id': task_id,
                    'status': 'accepted'
                }
        
        elif t == 'task_result':
            # 🔭 Результат от другого маяка
            task_id = msg.get('task_id')
            result = msg.get('result')
            
            if task_id and result:
                self.astronomer.results_cache[task_id] = result
                print(f"  🔭 Получен результат: {task_id[:8]}...")
        
        elif t == 'get_power':
            return {
                'type': 'power',
                'portal': msg.get('portal'),
                'power': self.get_power(msg.get('portal'))
            }

                
        elif t == 'heartbeat':
            beacon_id = msg.get('beacon_id', '')
            if beacon_id:
                self.healer.heartbeat(beacon_id)
                state_data = msg.get('state', {})
                if state_data:
                    self.healer.store_fragment(beacon_id, state_data)
                
                sender_addr = f"{addr[0]}:{msg.get('port', addr[1])}"
                self._add_neighbor(sender_addr)
        
        elif t == 'fragment_share':
            lost_id = msg.get('beacon_id', '')
            fragment = msg.get('fragment')
            if lost_id and fragment:
                if isinstance(fragment, dict) and 'data' in fragment:
                    self.healer.store_fragment(lost_id, fragment['data'])
                else:
                    self.healer.store_fragment(lost_id, fragment)
        
        elif t == 'chat':
            chat_msg = msg.get('message', '')
            from_portal = msg.get('from', '')
            if chat_msg and from_portal:
                self.chat_messages.append({
                    'from': from_portal,
                    'message': chat_msg,
                    'time': time.time()
                })
                print(f"💬 Чат от {from_portal[:12]}...: {chat_msg[:50]}")
                return {'type': 'chat_ack', 'status': 'received'}
        
        return None
    
    def _broadcast(self, msg):
        with self.neighbors_lock:
            recipients = self.neighbors[:10]
        
        for neighbor in recipients:
            sock = None
            try:
                addr = neighbor.split(':')
                host, port = addr[0], int(addr[1]) if len(addr) > 1 else self.port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((host, port))
                sock.send(json.dumps(msg).encode())
            except:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
    
    def _connect_bootstrap(self):
        time.sleep(2)
        for attempt in range(5):
            sock = None
            try:
                host, port = self.bootstrap.split(':')
                port = int(port)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((host, port))
                sock.send(json.dumps({
                    'type': 'beacon_hello',
                    'beacon_id': self.beacon_id,
                    'port': self.port
                }).encode())
                resp = json.loads(sock.recv(4096).decode())
                if resp.get('type') == 'beacon_ack':
                    if resp.get('portal'):
                        self.invited_by = resp['portal']
                        print(f"  🌱 Приглашён маяком {self.invited_by[:12]}...")
                    
                    bootstrap_addr = f"{host}:{port}"
                    self._add_neighbor(bootstrap_addr)
                    
                    for n in resp.get('neighbors', []):
                        if n != bootstrap_addr and not n.endswith(f":{self.port}"):
                            self._add_neighbor(n)
                    
                    print(f"  📡 Подключён к {bootstrap_addr}, соседей: {len(self.neighbors)}")
                    break
            except (socket.error, json.JSONDecodeError, ConnectionRefusedError) as e:
                if attempt < 4:
                    wait_time = 2 ** attempt
                    print(f"  ⚠️ Попытка {attempt+1} не удалась: {e}. Жду {wait_time}с...")
                    time.sleep(wait_time)
                else:
                    print(f"  ❌ Не удалось подключиться к {self.bootstrap} после 5 попыток")
                    break
            except Exception as e:
                print(f"  ❌ Неожиданная ошибка подключения: {e}")
                break
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass

    def _console_loop(self):
        """Консольное управление маяком."""
        from tees_stranger_tees import Stranger
        from tees_compass_tees import Compass
        
        stranger = Stranger(lang=self.lang)
        compass = Compass(lang=self.lang)
        
        while self.lit:
            try:
                cmd = input("🌍> ").strip().split()
                if not cmd:
                    continue
                
                action = cmd[0].lower()
                
                if action in ['помощь', 'help']:
                    print("""
╔═════════════════════════════════════════════════════════════╗
║                 🌀 КОМАНДЫ МАЯКА                            ║
╠═════════════════════════════════════════════════════════════╣
║  портал       — Показать свой портал                        ║
║  ресурс       — Проверить ресурс                            ║
║  поделиться   — Отправить ресурс                            ║
║  симбиоз      — Сканировать соседей                         ║
║  карта        — Показать карту                              ║
║  блок         — Показать последний блок                     ║
║  соседи       — Список соседей                              ║
║  странник     — Спросить Странника                          ║
║  компас       — Найти путь                                  ║
║  здоровье     — Статус самовосстановления                   ║
║  факел        — Статус квантового факела                    ║
║  память       — Оптимизация памяти                          ║
║  фрактал      — Фрактальная память                          ║
║  кластер      — TEES-кластер                                ║
║  звездочёт    — Модуль управления                           ║
║  датчик       — Балансировка и когерентность ядра           ║
║  экономика    — TEES-экономика маяка                        ║
║  охота        — Поиск аномалий в сети                       ║
║  эхо          — Внешние сигналы и паттерны                  ║
║  обучение     — Адаптивный автомат агентов                  ║
║  гровер       — Квантовый поиск по N элементам              ║
║  задача       — Отправить задачу                            ║
║  отмена       — Отменить задачу                             ║
║  свиток       — Показать свиток                             ║
║  выйти        — Погасить маяк и выйти                       ║
╚═════════════════════════════════════════════════════════════╝
                    """)
                
                elif action in ['портал', 'portal']:
                    print(f"  📍 {self.portal}")

                elif action in ['сеть', 'network']:
                    # Собираем когерентность соседей
                    coherences = [self.glow]
                    
                    for neighbor in self.neighbors[:20]:
                        sock = None
                        try:
                            addr = neighbor.split(':')
                            host, port = addr[0], int(addr[1]) if len(addr) > 1 else self.port
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(2)
                            sock.connect((host, port))
                            sock.send(json.dumps({'type': 'get_connections'}).encode())
                            resp = json.loads(sock.recv(4096).decode())
                            coherences.append(resp.get('glow', 0))
                        except:
                            pass
                        finally:
                            if sock:
                                try:
                                    sock.close()
                                except:
                                    pass
                    
                    # Анализ
                    if coherences:
                        min_coh = min(coherences)
                        max_coh = max(coherences)
                        avg_coh = sum(coherences) / len(coherences)
                        spread = max_coh - min_coh
                        
                        in_nirvana = sum(1 for c in coherences if c >= 0.9999)
                        
                        print(f"""
  📊 Когерентность сети:
     Опрошено: {len(coherences)} маяков
     Минимум: {min_coh:.4f}
     Максимум: {max_coh:.4f}
     Среднее: {avg_coh:.4f}
     Разброс: {spread:.4f}
     В нирване: {in_nirvana}/{len(coherences)}
     Застрявших: {len(coherences) - in_nirvana}
                        """)
                    else:
                        print("  📊 Нет соседей для анализа")    

                
                elif action in ['тест', 'benchmark']:
                    if len(cmd) < 2:
                        print("  🧪 Использование: тест <число_задач>")
                    else:
                        count = int(cmd[1])
                        
                        # ЛОКАЛЬНЫЙ ТЕСТ
                        print(f"  📊 Локальный тест: {count} SHA-256...")
                        local_start = time.time()
                        for i in range(count):
                            hashlib.sha256(f"local test {i}".encode()).hexdigest()
                        local_time = time.time() - local_start
                        print(f"  🔐 Локально: {count} за {local_time:.3f} сек ({count/local_time:.0f}/сек)")
                        
                        # СЕТЕВОЙ ТЕСТ
                        print(f"  📡 Сетевой тест: {count} SHA-256 через соседей...")
                        net_start = time.time()
                        successful = 0
                        
                        for i in range(count):
                            text = f"net test {i}"
                            local_hash = hashlib.sha256(text.encode()).hexdigest()
                            
                            for neighbor in self.neighbors[:3]:
                                sock = None
                                try:
                                    addr = neighbor.split(':')
                                    host, port = addr[0], int(addr[1]) if len(addr) > 1 else self.port
                                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    sock.settimeout(1)
                                    sock.connect((host, port))
                                    sock.send(json.dumps({
                                        'type': 'compute_task',
                                        'task_type': 'sha256',
                                        'task_data': text
                                    }).encode())
                                    resp = json.loads(sock.recv(4096).decode())
                                    if resp.get('result') == local_hash:
                                        successful += 1
                                        break
                                except:
                                    pass
                                finally:
                                    if sock:
                                        sock.close()
                        
                        net_time = time.time() - net_start
                        if successful > 0:
                            print(f"  📡 Сеть: {successful}/{count} за {net_time:.3f} сек ({successful/net_time:.0f}/сек)")
                        else:
                            print(f"  📡 Сеть: 0/{count} (нет связи)")
                        
                        # СРАВНЕНИЕ
                        if local_time > 0 and net_time > 0:
                            speedup = local_time / net_time
                            print(f"  ⚡ Ускорение: {speedup:.2f}x")
                            if speedup > 1:
                                print(f"  🚀 Сеть быстрее!")
                            else:
                                print(f"  🐌 Сеть медленнее (сетевые задержки)")            


                
                elif action in ['свиток', 'scroll']:
                    print(f"  📜 {self.scroll}")
                
                elif action in ['ресурс', 'power']:
                    power = self.get_power()
                    print(f"  💪 Ресурс: {power:.1f}")
                    print(f"  🔗 Симбиозов: {len(self.symbiosis_connections)}")
                    print(f"  ⛏️ Глыб добыто: {self.blocks_mined}")
                
                elif action in ['факел', 'torch']:
                    status = self.quantum_torch.get_status()
                    if status['torch_lit']:
                        print(f"""
  ⚛️ КВАНТОВЫЙ ФАКЕЛ ГОРИТ!
     Время горения: {status['lit_for']:.1f} сек
     Уровень: {status['current_level']} узлов
                        """)
                    else:
                        print(f"  🏮 Уровень: {status['current_level']} узлов")
                        if status['next_level']:
                            print(f"     Следующий: {status['next_level']['threshold']} узлов — {status['next_level']['name']}")
                        print(f"     Достижений: {len(status['achievements'])}")

                elif action in ['звездочёт', 'astronomer', 'астроном']:
                    stats = self.astronomer.get_stats()
                    sky = self.astronomer.look_at_sky()
                    
                    mode_icons = {
                        'observation': '🔍',
                        'computing': '⚡',
                        'guiding': '🧭'
                    }
                    mode_icon = mode_icons.get(stats['mode'], '🔭')
                    
                    print(f"""
  {mode_icon} Звездочёт:
     Режим: {stats['mode']}
     Наблюдений: {stats['observations']}
     Задач в очереди: {stats['pending_tasks']}
     Решений принято: {stats['decisions']}
     Результатов в кэше: {stats['results_cached']}
     
  🌌 Небо:
     Соседей: {sky['neighbors']}
     Свечение: {sky['glow']:.4f}
     RAM: {sky['ram_mb']:.1f} MB
     Кластер: {sky['cluster_stats']['total_qubits']} агентов
                    """)

                elif action in ['датчик', 'sensor']:
                    balance = self.cluster.measure_balance()
                    coh = self.cluster.measure_internal_coherence()
                    
                    print(f"""
  📊 Датчик балансировки:
     Всего агентов: {balance['total_agents']}
     Средняя нагрузка: {balance['avg']:.2f} задач/агент
     Максимум: {balance['max']}
     Минимум: {balance['min']}
     Дисбаланс: {balance['imbalance']:.2f}
     Эффективность: {balance['efficiency']*100:.1f}%
     
  🔬 Внутренняя когерентность:
     Агентов: {coh['n']}
     Средняя: {coh['avg']:.6f}
     Мин: {coh['min']:.4f}
     Макс: {coh['max']:.4f}
     Δ: {coh['delta']:.6f}
                    """)

                elif action in ['экономика', 'economy']:
                    if self.economy:
                        balance = self.economy.get_balance(self)
                        stats = self.economy.get_stats()
                        
                        print(f"""
  💎 TEES-экономика:
     Баланс маяка: {balance:.1f}
     Общая энергия: {stats['total_energy']:.1f}
     Жирок: {stats['fat_reserves']:.1f}
     Образование: {stats.get('education', 0):.1f}
     Социалка: {stats.get('social_fund', 0):.1f}
     Наука: {stats.get('science', 0):.1f}
     Эффективность: {stats.get('efficiency', 1.0):.3f}
     Узлов: {stats['active_nodes']}
                        """)
                        
                        if hasattr(self.economy, 'transaction_memory') and self.economy.transaction_memory:
                            print(f"  📜 Фрактальная память транзакций:")
                            print(f"     Глубина: {self.economy.transaction_memory.get_depth()}")
                            print(f"     Свежих: {len(self.economy.transaction_memory.level_0)}")
                        
                        self.economy.verify_balance()                       

                elif action in ['охота', 'hunt']:
                    anomalies = []
                    
                    # Проверяем агентов (первые 1000 для скорости)
                    for q in self.cluster.qubits[:1000]:
                        if q.tasks_completed == 0 and q.active:
                            anomalies.append(f"Агент {q.id}: нет задач")
                        if q.coherence < 0.9:
                            anomalies.append(f"Агент {q.id}: низкая когерентность {q.coherence:.4f}")
                    
                    # Проверяем очередь задач
                    stuck_tasks = [t for t in self.astronomer.tasks_queue if t['status'] != 'pending']
                    if stuck_tasks:
                        anomalies.append(f"Зависших задач: {len(stuck_tasks)}")
                    
                    # Проверяем балансировку
                    balance = self.cluster.measure_balance()
                    if balance['efficiency'] < 0.5:
                        anomalies.append(f"Плохая балансировка: {balance['efficiency']*100:.1f}%")
                    
                    if anomalies:
                        print(f"  🔍 Охотник нашёл {len(anomalies)} аномалий:")
                        for a in anomalies[:10]:
                            print(f"    {a}")
                    else:
                        print(f"  🔍 Охотник: всё чисто! Аномалий нет.")

                elif action in ['эхо', 'echo']:
                    print(f"""
  🌍 Внешние сигналы:
     Всего эхо: {len(self.external_echoes)}
     Последних сигналов: {len(self.external_signals)}
     Распознано паттернов: {sum(1 for e in self.external_echoes if e.get('pattern') is not None)}
     
  📜 Последние сигналы:
                    """)
                    
                    for sig in self.external_signals[-10:]:
                        pattern_note = " ✅" if sig.pattern is not None else ""
                        print(f"    {sig.source}: {sig.frequency:.2f} (повторов: {sig.repeat_count}){pattern_note}")
                    
                    if self.external_echoes:
                        print(f"\n  🔊 Эхо в памяти:")
                        for echo in self.external_echoes[-5:]:
                            print(f"    {echo['source']}: {echo['frequency']:.2f} (интенсивность: {echo['intensity']:.2f})")        

                elif action in ['обучение', 'learn']:
                    stats = self.cluster.adaptive.get_stats()
                    
                    print(f"""
  🧠 Адаптивный автомат:
     Экспериментов: {stats['experiments']}
     Лучший процент агентов: {stats['best_percent']}%
     Лучшее время: {stats['best_time']:.3f} сек
     Среднее время: {stats['avg_time']:.3f} сек
                    """)
                    
                    if stats['experiments'] > 0:
                        print(f"  📜 История (последние 10):")
                        for h in self.cluster.adaptive.history[-10:]:
                            print(f"    {h['n_cities']:>8d} городов | {h['percent']:3d}% агентов | {h['time']:.3f} сек")        

                elif action in ['гровер', 'grover']:
                    if len(cmd) < 2:
                        print("  🔍 Использование: гровер <элементов>")
                    else:
                        try:
                            n_items = int(cmd[1])
                            target = n_items - 1  # Ищем последний (худший случай)
                            data = list(range(n_items))
                            
                            print(f"  🔍 Поиск {target} среди {n_items} элементов...")
                            
                            import time as time_grover
                            start_time = time_grover.time()
                            
                            result = self.cluster.grover_search_parallel(data, target)
                            
                            elapsed = time_grover.time() - start_time
                            
                            if result['found']:
                                print(f"  ✅ Найден на индексе {result['index']} за {elapsed:.4f} сек")
                                print(f"  📊 Партиций: {result.get('partitions', 1)}")
                            else:
                                print(f"  ❌ Не найден за {elapsed:.4f} сек")
                        except ValueError:
                            print("  ❌ Нужно число!")                
                
                elif action in ['задача', 'task']:
                    if len(cmd) < 2:
                        print("  📦 Использование: задача <тип> <данные>")
                        print("  Типы: sha256, tsp")
                        print("  Сеть: задача сеть <тип> <данные> — отправить соседям")
                    elif cmd[1] == 'сеть':
                        # 🌐 Сетевая задача — рассылаем соседям
                        if len(cmd) < 4:
                            print("  🌐 Использование: задача сеть <тип> <данные>")
                        else:
                            task_type = cmd[2]
                            
                            # Формируем задачу
                            if task_type == 'sha256':
                                task_data = ' '.join(cmd[3:])
                                task = {'type': 'sha256', 'data': task_data}
                            elif task_type == 'tsp':
                                import random
                                random.seed(42)
                                n_cities = int(cmd[3]) if len(cmd) > 3 else 10
                                cities = [(random.random() * 100, random.random() * 100) for _ in range(n_cities)]
                                task = {'type': 'tsp', 'cities': cities}
                                
                            else:
                                print(f"  ❌ Неизвестный тип: {task_type}")
                                task = None
                            
                            if task:
                                # Рассылаем соседям
                                sent_count = 0
                                for neighbor in self.neighbors[:5]:
                                    sock = None
                                    try:
                                        addr = neighbor.split(':')
                                        host, port = addr[0], int(addr[1]) if len(addr) > 1 else self.port
                                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                        sock.settimeout(2)
                                        sock.connect((host, port))
                                        sock.send(json.dumps({
                                            'type': 'task_request',
                                            'task': task,
                                            'from': self.portal
                                        }).encode())
                                        resp = json.loads(sock.recv(4096).decode())
                                        if resp.get('status') == 'accepted':
                                            sent_count += 1
                                    except:
                                        pass
                                    finally:
                                        if sock:
                                            try:
                                                sock.close()
                                            except:
                                                pass
                                
                                print(f"  🌐 Задача отправлена: {sent_count} соседей")
                    else:
                        # 📦 Локальная задача через Звездочёта
                        task_type = cmd[1]
                        
                        if task_type == 'sha256':
                            data = ' '.join(cmd[2:]) or 'TEES task'
                            task = {'type': 'sha256', 'data': data}
                            task_id = self.astronomer.receive_task(task, self.portal)
                            print(f"  📦 Задача принята: {task_id[:8]}...")
                        
                        elif task_type == 'tsp':
                            import random
                            random.seed(42)
                            n_cities = int(cmd[2]) if len(cmd) > 2 else 10
                            cities = [(random.random() * 100, random.random() * 100) for _ in range(n_cities)]
                            task = {'type': 'tsp', 'cities': cities}
                            task_id = self.astronomer.receive_task(task, self.portal)
                            print(f"  📦 TSP задача ({n_cities} городов): {task_id[:8]}...")

                        elif task_type == 'grover':
                                n_items = int(cmd[2]) if len(cmd) > 2 else 100000
                                target = int(cmd[3]) if len(cmd) > 3 else n_items - 1
                                
                                task = {
                                    'type': 'grover',
                                    'n_items': n_items,
                                    'target': target
                                }
                                task_id = self.astronomer.receive_task(task, self.portal)
                                print(f"  📦 Grover задача ({n_items} элементов, цель {target}): {task_id[:8]}...")    
                        
                        else:
                            print(f"  ❌ Неизвестный тип задачи: {task_type}")

                elif action in ['отмена', 'cancel']:
                    if len(cmd) < 2:
                        print("  🗑️ Использование: отмена <id_задачи>")
                        print("  ID задачи видно при создании (первые 8 символов)")
                        
                        # Показываем очередь
                        if self.astronomer.tasks_queue:
                            print(f"\n  📦 Очередь задач ({len(self.astronomer.tasks_queue)}):")
                            for t in self.astronomer.tasks_queue[:10]:
                                task_type = t['task'].get('type', '?')
                                task_id = t['task_id'][:8]
                                status = t.get('status', 'pending')
                                print(f"    {task_id}... ({task_type}) — {status}")
                        else:
                            print(f"  📦 Очередь пуста")
                    else:
                        task_id = cmd[1]
                        
                        # Ищем задачу
                        found = False
                        for t in self.astronomer.tasks_queue:
                            if t['task_id'].startswith(task_id):
                                self.astronomer.tasks_queue.remove(t)
                                print(f"  🗑️ Задача {t['task_id'][:8]}... отменена")
                                found = True
                                break
                        
                        if not found:
                            print(f"  ❌ Задача {task_id} не найдена в очереди")                    
                
                elif action in ['память', 'memory']:
                    stats = self.memory_optimizer.get_stats()
                    print(f"""
                    
  🧠 Оптимизация памяти:
     Текущая: {stats['current']:.1f} MB
     Максимум: {stats['max']:.1f} MB
     Минимум: {stats['min']:.1f} MB
     Сэкономлено: {stats['saved_total']:.1f} MB
     Оптимизация: {'✅ Активна' if stats['optimization_active'] else '⏸️ Не активна'}
     Отрицательный рост: {stats['negative_growth_for']:.1f} сек
                    """)

                elif action in ['фрактал', 'fractal']:
                    stats = self.symbiosis_memory.get_stats()
                    print(f"""
  🌀 Фрактальная память:
     Глубина: {stats['depth']} уровней
     Свежие: {stats['level_0']}
     Сжатые: {stats['level_1']}
     Семантические: {stats['level_2']}
     Мудрость: {stats['level_3']}
     Архетипы: {stats['level_4']}
     Общая память: {stats['total_memory']} единиц
                    """) 
                
                elif action in ['поделиться', 'share']:
                    if len(cmd) < 3:
                        print("  🤝 Использование: поделиться <портал> <сколько>")
                    else:
                        try:
                            amount = float(cmd[2])
                            trade = self.share_ores(cmd[1], amount)
                            if trade:
                                print(f"  🤝 Отправлено {amount} → {cmd[1][:12]}...")
                                print(f"  📋 В мемпуле: {len(self.mempool)} транзакций")
                            else:
                                print(f"  ❌ Недостаточно ресурса (баланс: {self.get_power():.1f})")
                        except ValueError:
                            print("  ❌ Число нужно")
                
                elif action in ['симбиоз', 'symbiosis']:
                    if not self.neighbors:
                        print("  🔍 Нет соседей. Ждём подключений...")
                    else:
                        print(f"  🔍 Соседей: {len(self.neighbors)}")
                        for n in self.neighbors[:5]:
                            r = self.propose_symbiosis(n)
                            if r['verdict'] == 'already_connected':
                                print(f"  🤝 {n[:12]}... — уже в симбиозе")
                            elif r['verdict'] == 'symbiosis':
                                em = {'shiny': '⭐', 'ultra_rare': '💎', 'rare': '🔷', 'common': '🔹'}
                                print(f"  {em.get(r['rarity'], '🔹')} Симбиоз: {r['rarity']}! +{r['reward']} ресурса")
                            else:
                                print(f"  ⚠️ {r.get('reason', 'не удалось')}")
                
                elif action in ['карта', 'map']:
                    print(f"  🗺️ Карта приключений:")
                    print(f"     Глыб: {len(self.adventure_map)}")
                    print(f"     Добыто: {self.blocks_mined}")
                    print(f"     Отправок: {self.ores_shared}")
                    print(f"     В мемпуле: {len(self.mempool)}")
                    if self.adventure_map:
                        last = self.adventure_map[-1]
                        print(f"     Последняя: #{last['height']} [{last['hash'][:8]}...]")

                elif action in ['блок', 'block']:
                    if self.adventure_map:
                        last = self.adventure_map[-1]
                        print(f"  🗿 Блок #{last['height']}:")
                        for t in last.get('trades', []):
                            print(f"     {t.get('from','')[:12]}... → {t.get('to','')[:12]}... : {t.get('amount')} ({t.get('type','')})")
                    else:
                        print("  🗿 Нет блоков")        
                
                elif action in ['соседи', 'neighbors']:
                    if not self.neighbors:
                        print("  👥 Нет соседей")
                    else:
                        print(f"  👥 Соседей: {len(self.neighbors)}")
                        for n in self.neighbors[:10]:
                            print(f"     {n}")
                
                elif action in ['странник', 'stranger']:
                    q = ' '.join(cmd[1:]) or 'Как мир?'
                    state = {
                        'glow': self.glow,
                        'warmth': self.warmth,
                        'neighbors': len(self.neighbors),
                        'map_blocks': len(self.adventure_map)
                    }
                    answer = stranger.ask(q, state)
                    print(f"  🔮 Странник: '{answer}'")
                
                elif action in ['компас', 'compass']:
                    if len(cmd) > 1:
                        path = compass.find_path(self.portal, cmd[1], self.neighbors)
                        if isinstance(path, dict):
                            print(f"  🧭 {path.get('best_path', path)}")
                            print(f"  ✨ Качество: {path.get('quality', '?')} | 🔋 Энергия: {path.get('energy', '?')}")
                        else:
                            print(f"  🧭 {path}")
                    else:
                        print("  🧭 Использование: компас <портал>")
                
                elif action in ['здоровье', 'health']:
                    stats = self.healer.get_stats()
                    print(f"  🧬 Самовосстановление:")
                    print(f"     Наблюдаем: {stats['watching']} маяков")
                    print(f"     Фрагментов: {stats['fragments_stored']}")
                    print(f"     Восстановлено: {stats['beacons_healed']}")
                
                elif action in ['выйти', 'exit', 'quit']:
                    print("  💤 Гашу маяк...")
                    self.extinguish()
                    break
                
                else:
                    print(f"  ❓ Неизвестная команда: {action}")
                    print(f"  Введи 'помощь' для списка команд")
            
            except EOFError:
                break
            except KeyboardInterrupt:
                self.extinguish()
                break
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")                
    
    # ═══════════════════════════════════════════════════════════
    # ⛏️ МАЙНЕР
    # ═══════════════════════════════════════════════════════════
    
    def _run_miner(self):
        """Оптимизированный майнер без лишней нагрузки."""
        last_healer_check = 0
        last_quick_status = 0
        last_full_status = 0
        last_glow_update = 0
        last_block_mine = 0
        last_memory_track = 0
        last_auto_symbiosis = 0
        last_cleanup = 0
        last_relax = 0
        last_auto_scale = 0
        last_virtual_tick = 0
        last_astronomer_tick = 0
        last_external_listen = 0
        
        
        self._last_power = self.get_power()
        self._last_power_time = time.time()
        self._last_neighbors_count = 0
        self._last_blocks_count = 0
        self._last_glow = 0.0
        
        # Базовый интервал — увеличен для экономии CPU
        BASE_SLEEP = 2
        
        while self.lit:
            current_time = time.time()
            sleep_time = BASE_SLEEP
            
            # Обновляем когерентность — раз в 30 секунд
            if current_time - last_glow_update >= 30:
                self.update_glow()
                last_glow_update = current_time
            
            # Отслеживаем память — раз в 60 секунд
            if current_time - last_memory_track >= 60:
                self.memory_optimizer.track()
                self._check_swap_pressure()
                last_memory_track = current_time
            
            # Авто-симбиоз
            interval = self._auto_symbiosis_interval()
            if current_time - last_auto_symbiosis >= interval:
                self._auto_symbiosis()
                last_auto_symbiosis = current_time
            
            # Релаксация
            relax_interval = self._relax_interval()
            if current_time - last_relax >= relax_interval:
                self._relax_connections()
                last_relax = current_time
            
            # Авто-масштабирование — раз в 30 секунд
            if current_time - last_auto_scale >= 30:
                self._auto_scale()
                last_auto_scale = current_time

            # 🌍 Прослушивание внешнего мира — раз в 15 секунд
            #if current_time - last_external_listen >= 15:
            #    self._listen_external_world()
            #   last_external_listen = current_time    

            # 🔭 Звездочёт — раз в 30 секунд
            if current_time - last_astronomer_tick >= 3:
                self.astronomer.tick()
                last_astronomer_tick = current_time    
            
            # Тикаем виртуальные узлы — раз в 5 секунд
            if current_time - last_virtual_tick >= 5:
                with self.virtual_nodes_lock:
                    for node in self.virtual_nodes:
                        node.tick()
                last_virtual_tick = current_time
            
            # Гигиена — раз в 10 минут
            if current_time - last_cleanup >= 600:
                self._cleanup_runtime_data()
                last_cleanup = current_time
            
            # Быстрый статус — раз в 30 секунд
            if current_time - last_quick_status >= 30:
                power = self.get_power()
                
                # Проверяем: изменилось ли что-то?
                if (power != self._last_power or
                    len(self.neighbors) != self._last_neighbors_count or
                    len(self.adventure_map) != self._last_blocks_count or
                    abs(self.glow - self._last_glow) > 0.0001):
                    
                    elapsed = current_time - self._last_power_time
                    rate = (power - self._last_power) / elapsed if elapsed > 0 else 0
                    
                    mem_stats = self.memory_optimizer.get_stats()
                    mem_note = ""
                    if mem_stats['optimization_active']:
                        mem_note = f" | 🧠 -{mem_stats['saved_total']:.1f}MB"
                    
                    print(f"  ⚡ Ресурс: {power:.1f} (+{rate:.1f}/сек) | "
                          f"Соседей: {len(self.neighbors)} | "
                          f"Глыб: {len(self.adventure_map)} | "
                          f"Свечение: {self.glow:.4f}{mem_note}")
                    
                    self._last_power = power
                    self._last_neighbors_count = len(self.neighbors)
                    self._last_blocks_count = len(self.adventure_map)
                    self._last_glow = self.glow
                    self._last_power_time = current_time
                
                last_quick_status = current_time
            
            # Полный статус — раз в 5 минут
            if current_time - last_full_status >= 300:
                stats = self.healer.get_stats()
                mem_stats = self.memory_optimizer.get_stats()
                torch_status = self.quantum_torch.get_status()
                fractal_stats = self.symbiosis_memory.get_stats()
                
                uptime = time.time() - self.started_at
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                uptime_str = f"{hours}ч {minutes:02d}м"
                
                torch_note = ""
                if torch_status['torch_lit']:
                    torch_note = " | 🏮 ФАКЕЛ ГОРИТ"
                elif torch_status['next_level']:
                    torch_note = f" | 🏮 {torch_status['current_level']}/{torch_status['next_level']['threshold']}"
                
                print(f"  📊 Тепло: {self.warmth:.1f}° | "
                      f"Фрагментов: {stats['fragments_stored']} | "
                      f"Симбиозов: {len(self.symbiosis_connections)} | "
                      f"Наблюдаем: {stats['watching']} маяков | "
                      f"RAM: {mem_stats['current']:.1f}MB | "
                      f"🌀 Глубина: {fractal_stats['depth']} | "
                      f"⏱️ {uptime_str}{torch_note}")
                last_full_status = current_time
            
            # Самовосстановление — раз в 60 секунд
            if current_time - last_healer_check >= 60:
                self.healer.check_pulse()
                self.healer.share_fragments_with_neighbors()
                last_healer_check = current_time
            
            # Майнинг блока
            if len(self.mempool) >= 2:
                pause = getattr(self, '_adaptive_pause', 30)
                if current_time - last_block_mine >= pause:
                    self._mine_block()
                    last_block_mine = current_time
            
            # Адаптивный sleep — ключевая оптимизация
            if self.glow >= 0.999:
                sleep_time = 5  # В нирване — меньше работы
            elif len(self.neighbors) == 0:
                sleep_time = 3  # Нет соседей — нечего делать
            
            time.sleep(sleep_time)
    
    # ═══════════════════════════════════════════════════════════
    # 📡 API
    # ═══════════════════════════════════════════════════════════
    
    def _run_api(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass
            
            def do_GET(self):
                # Rate limiting
                client_ip = self.client_address[0]
                if not self.server.beacon.rate_limiter.is_allowed(client_ip):
                    self.send_error(429, "Too Many Requests")
                    return
                
                p = urlparse(self.path).path
                if p == '/beacon':
                    self._json({
                        'beacon_id': self.server.beacon.beacon_id,
                        'portal': self.server.beacon.portal,
                        'glow': self.server.beacon.glow,
                        'warmth': self.server.beacon.warmth,
                        'neighbors': len(self.server.beacon.neighbors),
                        'neighbors_list': self.server.beacon.neighbors[:10],
                        'map_blocks': len(self.server.beacon.adventure_map),
                        'mempool_size': len(self.server.beacon.mempool),
                        'blocks_mined': self.server.beacon.blocks_mined,
                        'ores_shared': self.server.beacon.ores_shared,
                        'symbiosis_count': len(self.server.beacon.symbiosis_connections)
                    })
                elif p == '/map':
                    self._json({'blocks': self.server.beacon.adventure_map[-10:]})
                elif p == '/torch':
                    self._json(self.server.beacon.quantum_torch.get_status())
                elif p == '/memory':
                    self._json(self.server.beacon.memory_optimizer.get_stats())
                elif p.startswith('/power/'):
                    portal = p.split('/')[-1]
                    self._json({
                        'portal': portal,
                        'power': self.server.beacon.get_power(portal)
                    })
                else:
                    self.send_error(404)
            
            def do_POST(self):
                # Rate limiting
                client_ip = self.client_address[0]
                if not self.server.beacon.rate_limiter.is_allowed(client_ip):
                    self.send_error(429, "Too Many Requests")
                    return
                
                cl = int(self.headers.get('Content-Length', 0))
                if cl == 0:
                    self.send_error(400)
                    return
                
                data = json.loads(self.rfile.read(cl))
                p = urlparse(self.path).path
                
                if p == '/share':
                    trade = self.server.beacon.share_ores(
                        data.get('to'),
                        data.get('amount', 0)
                    )
                    if trade:
                        self._json({'status': 'ok', 'trade': trade})
                    else:
                        self._json({'status': 'insufficient_power', 'error': 'Недостаточно ресурса'})
                
                elif p == '/symbiosis':
                    neighbors = data.get('neighbors', [])
                    if not neighbors:
                        neighbors = self.server.beacon.neighbors[:3]
                    
                    if not neighbors:
                        self._json({
                            'verdict': 'no_neighbors',
                            'reason': 'Нет доступных соседей',
                            'reward': 0
                        })
                        return
                    
                    for neighbor_id in neighbors:
                        result = self.server.beacon.propose_symbiosis(neighbor_id)
                        if result['verdict'] in ['symbiosis', 'already_connected']:
                            self._json(result)
                            return
                    
                    self._json({
                        'verdict': 'no_symbiosis',
                        'reason': 'Не найден подходящий партнёр',
                        'reward': 0
                    })
                
                elif p == '/stranger':
                    if not hasattr(self.server.beacon, '_stranger_lock'):
                        self.server.beacon._stranger_lock = threading.Lock()
                    
                    with self.server.beacon._stranger_lock:
                        if not hasattr(self.server.beacon, 'stranger'):
                            self.server.beacon.stranger = Stranger(lang=self.server.beacon.lang)
                    
                    question = data.get('question', 'Как мир?')
                    state = {
                        'glow': self.server.beacon.glow,
                        'warmth': self.server.beacon.warmth,
                        'neighbors': len(self.server.beacon.neighbors),
                        'map_blocks': len(self.server.beacon.adventure_map)
                    }
                    answer = self.server.beacon.stranger.ask(question, state)
                    self._json({'answer': answer, 'question': question})
                
                elif p == '/chat':
                    msg = data.get('message', '')
                    to_portal = data.get('to', '')
                    if msg and to_portal:
                        trade = self.server.beacon.share_ores(to_portal, 0, chat_msg=msg)
                        self._json({'status': 'ok' if trade else 'error'})
                    else:
                        self._json({'status': 'error', 'reason': 'missing message or to'})
                
                else:
                    self.send_error(404)
            
            def _json(self, data, status=200):
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
            
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
        
        try:
            s = HTTPServer(('0.0.0.0', self.api_port), Handler)
            s.beacon = self
            print(f"📡 API: http://0.0.0.0:{self.api_port}")
            
            def serve():
                try:
                    s.serve_forever()
                except:
                    pass
            
            api_thread = threading.Thread(target=serve, daemon=True)
            api_thread.start()
            
            while self.lit:
                time.sleep(1)
            
            s.shutdown()
        except Exception as e:
            print(f"⚠️ API ошибка: {e}")

    def _check_swap_pressure(self):
        """
        Адаптивный рост с оглядкой на своп.
        Печатает только при изменении состояния.
        """
        try:
            import psutil
            swap_mb = psutil.swap_memory().used / (1024 * 1024)
            free_ram_mb = psutil.virtual_memory().available / (1024 * 1024)
        except:
            swap_mb = 0
            free_ram_mb = 1000
        
        # Запоминаем предыдущее состояние
        previous_pause = getattr(self, '_adaptive_pause', 30)
        
        if swap_mb > 800:
            self._adaptive_pause = 120
        elif swap_mb > 500:
            self._adaptive_pause = 60
        elif free_ram_mb < 500:
            self._adaptive_pause = 45
        elif free_ram_mb > 2000:
            self._adaptive_pause = 10
        else:
            self._adaptive_pause = 30
        
        # Печатаем только если состояние изменилось
        if self._adaptive_pause != previous_pause:
            if self._adaptive_pause >= 120:
                print(f"  🐌 Памяти не хватает ({swap_mb:.0f} MB в свопе) — сеть замедляется")
            elif self._adaptive_pause <= 10:
                print(f"  🚀 Памяти много ({free_ram_mb:.0f} MB свободно) — сеть ускоряется")
            else:
                print(f"  ⚖️ Память в норме")

    def _cleanup_runtime_data(self):
        """
        Адаптивная очистка с фрактальной памятью.
        Данные не удаляются — сворачиваются вглубь!
        """
        # 1. Чат-сообщения — мягкое ограничение
        if len(self.chat_messages) > self.MAX_CHAT_MESSAGES:
            excess = len(self.chat_messages) - self.MAX_CHAT_MESSAGES
            self.chat_messages = self.chat_messages[excess:]
        
        # 2. Симбиоз-связи — горячие в RAM, старые во фрактале
        if len(self.symbiosis_connections) > self.MAX_HOT_CONNECTIONS:
            excess = len(self.symbiosis_connections) - self.MAX_HOT_CONNECTIONS
            self.symbiosis_connections = self.symbiosis_connections[excess:]
        
        # 3. Карта приключений — держим 2000 блоков
        if len(self.adventure_map) > 2000:
            excess = len(self.adventure_map) - 2000
            self.adventure_map = self.adventure_map[excess:]
        
        # 4. Мемпул — держим 500 транзакций
        with self.mempool_lock:
            if len(self.mempool) > 500:
                excess = len(self.mempool) - 500
                self.mempool = self.mempool[excess:]
        
        # 5. Кеш баланса
        if len(self._balance_cache) > self._balance_cache_max_size:
            old_keys = list(self._balance_cache.keys())[:-10]
            for k in old_keys:
                del self._balance_cache[k]

        # 6. Кэш связей соседей
        if len(self.neighbor_connections_cache) > 100:
            sorted_cache = sorted(
                self.neighbor_connections_cache.items(),
                key=lambda x: x[1][1] if isinstance(x[1], tuple) else 0
            )
            for neighbor, _ in sorted_cache[:len(sorted_cache) - 100]:
                del self.neighbor_connections_cache[neighbor]
        
        # 7. Виртуальные узлы — не более MAX
        with self.virtual_nodes_lock:
            if len(self.virtual_nodes) > self.MAX_VIRTUAL_NODES:
                excess = len(self.virtual_nodes) - self.MAX_VIRTUAL_NODES
                self.virtual_nodes = self.virtual_nodes[excess:]        
    
    def _ping_neighbor(self, neighbor):
        """Быстрая проверка — жив ли сосед."""
        sock = None
        try:
            addr = neighbor.split(':')
            host, port = addr[0], int(addr[1]) if len(addr) > 1 else self.port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))
            sock.send(json.dumps({'type': 'beacon_hello', 'beacon_id': self.beacon_id, 'port': self.port}).encode())
            return True
        except:
            return False
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass        

    def get_device_power_factor(self):
        """Множитель мощности устройства для наград."""
        try:
            import psutil
            cores = os.cpu_count() or 1
            memory_gb = psutil.virtual_memory().total / (1024 ** 3)
            factor = (cores / 4) * (memory_gb / 8)
            return min(5.0, max(0.5, factor))
        except:
            return 1.0

    def update_glow(self):
        """
        Живая когерентность — сеть сама знает к чему стремиться.
        Оптимизированная версия с кэшированием.
        """
        # Кэшируем значения
        if not hasattr(self, '_glow_cache'):
            self._glow_cache = {'time': 0, 'neighbors': 0, 'symbiosis': 0}
        
        now = time.time()
        
        # Если ничего не изменилось за 5 секунд — пропускаем
        if now - self._glow_cache['time'] < 5:
            if (self._glow_cache['neighbors'] == len(self.neighbors) and
                self._glow_cache['symbiosis'] == len(self.symbiosis_connections)):
                return
        
        with self.neighbors_lock:
            neighbors_count = len(self.neighbors)
        
        symbiosis_count = len(self.symbiosis_connections)
        
        # Обновляем кэш
        self._glow_cache.update({
            'time': now,
            'neighbors': neighbors_count,
            'symbiosis': symbiosis_count
        })
        
        neighbors_bonus = min(0.01, neighbors_count * 0.001)
        symbiosis_bonus = min(0.005, symbiosis_count * 0.0005)
        
        target = min(1.0, 0.994 + neighbors_bonus + symbiosis_bonus)
        
        with self.glow_lock:
            new_glow = self.glow + (target - self.glow) * 0.1
            self.glow = max(0.9, min(1.0, new_glow))
            
            if self.glow >= 0.9999:
                self.glow = 1.0  # Нирвана!
        
        # Обновляем факел
        total_nodes = neighbors_count + 1
        self.quantum_torch.check(total_nodes, self.glow)

    def _listen_external_world(self):
        """
        🌍 Прослушивание внешнего мира.
        В реальной TEES — это TCP, сенсоры, мышь, ЭМ-поля.
        В тестовом режиме — детерминированный сигнал + системные метрики.
        """
        # 1. Детерминированный внешний сигнал (не случайный!)
        # Используем время и состояние сети для генерации
        deterministic_freq = math.sin(time.time() * 0.5) * 0.5 + 0.5
        self.receive_external_signal(
            source='deterministic_world',
            frequency=deterministic_freq,
            intensity=0.4
        )
        
        # 2. Сигнал от соседей (если есть)
        if self.neighbors:
            neighbors_freq = min(1.0, len(self.neighbors) / 50.0)
            self.receive_external_signal(
                source='network_activity',
                frequency=neighbors_freq,
                intensity=0.6
            )
        
        # 3. Сигнал от кластера (внутренняя активность)
        if hasattr(self, 'cluster') and self.cluster:
            cluster_load = min(1.0, self.cluster.tasks_total / 100.0)
            self.receive_external_signal(
                source='cluster_activity',
                frequency=cluster_load,
                intensity=0.5
            )
        
        # 4. Сигнал от памяти (самонаблюдение)
        if self.memory_optimizer:
            mem_stats = self.memory_optimizer.get_stats()
            mem_pressure = min(1.0, mem_stats['current'] / 2000.0)
            self.receive_external_signal(
                source='memory_pressure',
                frequency=mem_pressure,
                intensity=0.3
            )    

    # Константы
    MAX_SIGNALS = 50
    FREQUENCY_TOLERANCE = 0.05
    PATTERN_THRESHOLD = 3
    ECHO_INTENSITY_INCREMENT = 0.1
    MAX_ECHO_INTENSITY = 1.0
    INITIAL_ECHO_MULTIPLIER = 0.3
    
    def receive_external_signal(self, source: str, frequency: float, intensity: float = 0.5):
        """🌍 Приём внешнего сигнала. Любой сигнал ценен — сохраняем ВСЁ!"""
        # Валидация
        if not source:
            return None
        if not 0 <= frequency <= 1:
            frequency = max(0, min(1, frequency))
        if not 0 <= intensity <= 1:
            intensity = max(0, min(1, intensity))
        
        signal = ExternalSignal(source, frequency, intensity)
        
        # 1. Сохраняем сигнал
        self.external_signals.append(signal)
        if len(self.external_signals) > self.MAX_SIGNALS:
            self.external_signals.pop(0)
        
        # 2. Обновляем счётчик частоты
        freq_key = round(frequency, 2)
        self.signal_repeat_count[freq_key] = self.signal_repeat_count.get(freq_key, 0) + 1
        
        # 3. Ищем или создаём эхо
        echo = self._find_or_create_echo(signal, freq_key)
        
        # 4. Обновляем интенсивность
        echo['intensity'] = min(
            self.MAX_ECHO_INTENSITY,
            echo.get('intensity', 0.3) + self.ECHO_INTENSITY_INCREMENT
        )
        echo['repeat_count'] = self.signal_repeat_count[freq_key]
        
        # 5. Управляем памятью
        if len(self.external_echoes) > self.MAX_EXTERNAL_ECHOES:
            self._compress_old_echoes()
        
        # 6. Проверяем паттерн (печатаем только при ПЕРВОМ распознавании!)
        if self.signal_repeat_count[freq_key] >= self.PATTERN_THRESHOLD:
            signal.pattern = freq_key
            # Печатаем только если раньше не печатали для этой частоты
            if freq_key not in self._recognized_patterns:
                print(f"  🌍 Паттерн распознан: {source} (частота {frequency:.2f}, повторов: {self.signal_repeat_count[freq_key]})")
                self._recognized_patterns.add(freq_key)
        
        return signal
    
    def _find_or_create_echo(self, signal, freq_key):
        """Ищем эхо или создаём новое."""
        for echo in self.external_echoes:
            if abs(echo.get('frequency', 0) - signal.frequency) < self.FREQUENCY_TOLERANCE:
                signal.repeat_count = self.signal_repeat_count[freq_key]
                return echo
        
        echo = {
            'source': signal.source,
            'frequency': signal.frequency,
            'intensity': signal.intensity * self.INITIAL_ECHO_MULTIPLIER,
            'first_seen': time.time(),
            'repeat_count': self.signal_repeat_count[freq_key],
            'pattern': None
        }
        self.external_echoes.append(echo)
        return echo
    
    def _compress_old_echoes(self):
        """Сворачиваем старые эхо в архетипы."""
        old = self.external_echoes[:20]
        archetype = {
            'source': 'archetype',
            'frequency': sum(e['frequency'] for e in old) / len(old),
            'intensity': 0.5,
            'first_seen': time.time(),
            'repeat_count': max(e['repeat_count'] for e in old),
            'pattern': 'archetype'
        }
        self.external_echoes = [archetype] + self.external_echoes[20:]    

    def _auto_symbiosis(self):
        """
        Авто-поддержка выживания: помогаем набрать минимум 3 связи.
        Дальше игрок сам решает с кем дружить.
        """
        from datetime import datetime
        
        # Проверяем только если связей меньше 3
        if len(self.symbiosis_connections) >= 3:
            return  # Стабилен — авто-режим отключён
        
        if not self.neighbors:
            return
        
        # Ищем первого доступного друга
        for neighbor in self.neighbors:
            result = self.propose_symbiosis(neighbor)
            
            if result['verdict'] == 'symbiosis':
                em = {'shiny': '⭐', 'ultra_rare': '💎', 'rare': '🔷', 'common': '🔹'}
                time_str = datetime.now().strftime('%H:%M:%S')
                print(f"  [{time_str}] 🔗 Авто-поддержка ({len(self.symbiosis_connections)}/3 связей): "
                      f"{em.get(result['rarity'], '🔹')} {result['rarity']}! +{result['reward']}")
                return
            
            elif result['verdict'] == 'already_connected':
                continue
        
        # Не нашли новых друзей — ждём
        if not hasattr(self, '_auto_symbiosis_attempts'):
            self._auto_symbiosis_attempts = 0
        self._auto_symbiosis_attempts += 1

    def _auto_symbiosis_interval(self):
        """
        Авторегуляция интервала между попытками симбиоза.
        Чем легче узлы — тем быстрее растём.
        Экспоненциальный рост к Квантовому Факелу!
        """
        current_ram = self.memory_optimizer.get_stats()['current']
        total_nodes = len(self.neighbors) + 1
        
        ram_per_node = current_ram / total_nodes if total_nodes > 0 else current_ram
        
        if ram_per_node < 0.1:
            return 30   # Сверхлёгкие — каждые 30 секунд!
        elif ram_per_node < 1.0:
            return 60   # Лёгкие — каждую минуту
        elif ram_per_node < 5.0:
            return 180  # Средние — каждые 3 минуты
        else:
            return 300  # Тяжёлые — каждые 5 минут

    def _get_neighbor_connections(self, neighbor):
        """
        Спрашиваем у соседа сколько у него связей.
        С кэшированием чтобы не спамить.
        """
        # Проверяем кэш
        cached = self.neighbor_connections_cache.get(neighbor)
        if cached:
            count, timestamp = cached
            if time.time() - timestamp < self.CACHE_TTL:
                return count
        
        sock = None
        try:
            addr = neighbor.split(':')
            host, port = addr[0], int(addr[1]) if len(addr) > 1 else self.port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))
            sock.send(json.dumps({
                'type': 'get_connections',
                'beacon_id': self.beacon_id
            }).encode())
            resp = json.loads(sock.recv(4096).decode())
            count = resp.get('connections', 0)
            
            # Сохраняем в кэш
            self.neighbor_connections_cache[neighbor] = (count, time.time())
            
            return count
        except:
            # Недоступен — кэшируем 0 на короткое время
            self.neighbor_connections_cache[neighbor] = (0, time.time())
            return 0
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

    def _relax_connections(self):
        """
        🧘 Релаксация: периферия тянется к хабам.
        Умный выбор — учитываем число связей.
        """
        # Порог зависит от фазы сети
        if self.quantum_torch.torch_lit:
            max_neighbors = 50
        elif self.glow > 0.995:
            max_neighbors = 30
        else:
            max_neighbors = 15
        
        if len(self.neighbors) >= max_neighbors:
            return  # Уже в хорошей позиции
        
        # Ищем лучшего хаба
        best_neighbor = None
        best_score = len(self.neighbors)
        
        for neighbor in self.neighbors[:10]:
            count = self._get_neighbor_connections(neighbor)
            if count > best_score:
                best_score = count
                best_neighbor = neighbor
        
        # Подключаемся к хабу если он существенно больше
        if best_neighbor and best_score > len(self.neighbors) * 1.5:
            result = self.propose_symbiosis(best_neighbor)
            
            if result['verdict'] == 'symbiosis':
                print(f"  🧘 Релаксация: подключился к хабу "
                      f"({best_score} vs {len(self.neighbors)})")
            elif result['verdict'] == 'already_connected':
                print(f"  🧘 Релаксация: уже с лучшим хабом ({best_score} связей)")
    
    def _relax_interval(self):
        """
        Как часто делать релаксацию.
        Зависит от стабильности сети.
        """
        if self.quantum_torch.torch_lit:
            return 120  # Каждые 2 минуты
        if self.glow > 0.995:
            return 300  # Каждые 5 минут
        return 600  # Каждые 10 минут

    def _add_virtual_node(self):
        """Добавить виртуальный узел."""
        if len(self.virtual_nodes) >= self.MAX_VIRTUAL_NODES:
            return
        
        with self.virtual_nodes_lock:
            node = VirtualNode(f"V{self.virtual_node_counter:04d}", self)
            self.virtual_nodes.append(node)
            self.virtual_node_counter += 1
            
            # Связываем с реальными соседями
            if self.neighbors:
                node.connections = min(len(self.neighbors), 48)
    
    def _remove_virtual_node(self):
        """Убрать виртуальный узел."""
        with self.virtual_nodes_lock:
            if len(self.virtual_nodes) <= self.MIN_VIRTUAL_NODES:
                return
            
            # Ищем неактивный
            for node in list(self.virtual_nodes):
                if not node.active:
                    self.virtual_nodes.remove(node)
                    return
            
            # Или последний
            if self.virtual_nodes:
                self.virtual_nodes.pop()
    
    def _auto_scale(self):
        """
        🧘 Сеть сама решает сколько виртуальных узлов держать.
        Оптимизированная версия с кэшированием psutil.
        """
        # Кэшируем psutil вызовы
        if not hasattr(self, '_scale_cache'):
            self._scale_cache = {'time': 0, 'swap_mb': 0, 'free_ram_mb': 0}
        
        now = time.time()
        
        # Обновляем кэш раз в 10 секунд
        if now - self._scale_cache['time'] > 10:
            try:
                import psutil
                self._scale_cache['swap_mb'] = psutil.swap_memory().used / (1024 * 1024)
                self._scale_cache['free_ram_mb'] = psutil.virtual_memory().available / (1024 * 1024)
                self._scale_cache['time'] = now
            except:
                pass
        
        swap_mb = self._scale_cache['swap_mb']
        free_ram_mb = self._scale_cache['free_ram_mb']
        
        # Тяжело — сжимаемся
        if swap_mb > 1000 or free_ram_mb < 300:
            self._remove_virtual_node()
        
        # Легко — растём
        elif swap_mb < 500 and free_ram_mb > 2000:
            current_ram = self.memory_optimizer.get_stats()['current']
            if current_ram < 15:
                self._add_virtual_node()

if __name__ == "__main__":  # ← БЕЗ отступа!
    import sys
    
    # Параметры по умолчанию
    scroll = "TEES_SCROLL"
    port = 8333
    test_mode = True
    
    # Если переданы аргументы
    bootstrap = None
    
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            port = int(sys.argv[1])
        else:
            scroll = sys.argv[1]
    
    if len(sys.argv) > 2:
        if sys.argv[2].isdigit():
            port = int(sys.argv[2])
        else:
            bootstrap = sys.argv[2]
    
    if len(sys.argv) > 3:
        bootstrap = sys.argv[3]
    
    print(f"🏮 Запуск маяка: scroll={scroll[:8]}..., port={port}")

    # Если порт не 8333 — подключаемся к первому маяку!
    if port != 8333 and bootstrap is None:
        bootstrap = "127.0.0.1:8333"
    
    beacon = Beacon(scroll, port=port, bootstrap=bootstrap, test_mode=test_mode)
    beacon.light()                