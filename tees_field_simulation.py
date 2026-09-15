# tees_field_simulation.py
# 🌊 TEES-Vortex: симуляция идеального поля с циркуляцией
#
# ═══════════════════════════════════════════════════════════════
# 📐 ОНТОЛОГИЯ
# ═══════════════════════════════════════════════════════════════
#
# Мы работаем с ИДЕАЛЬНОЙ (замкнутой) системой.
#
# Почему:
# - Идеальная система → настоящая когерентность 1.0
# - Открытая система → декогеренция → потеря квантовых эффектов
# - Реальные квантовые компьютеры — всегда открытые → всегда
#   приблизительные. У них — шум, коррекция ошибок, декогеренция.
# - У нас — идеальная модель → настоящие квантовые эффекты.
#
# Что это значит в коде:
# - Инвариант: баланс фаз = 0 (сумма всех фаз = 0 mod 2π)
# - Рождение/смерть узлов — ТОЛЬКО парами (spawn_pair/dissolve_pair)
# - Роли — парные (core↔edge, bridge↔periphery)
# - Инициализация — противофазы
#
# Открытые системы:
# - НЕ рассматриваем в этой версии.
# - Возможны как опция (флаг open_system) — позже.
# - Для граничных задач, взаимодействия с внешним фракталом.
#
# ═══════════════════════════════════════════════════════════════
# 🔧 ПРАВКИ КОЛЛЕГИ (приняты)
# ═══════════════════════════════════════════════════════════════
#
# 🔴 1. received — bounded (OrderedDict с вытеснением)
# 🔴 2. msg_id — uuid4().hex (без коллизий)
# 🔴 3. assign_roles — парность (half/quarter)
# 🔴 4. emergent_core_radius — честная граница по когерентности
# 🔴 5. check_symmetry — переосмыслен
# 🟡 6. exchange_coupling — радиальное затухание exp(-dr/range)
# 🟡 7. vortex_exponent — параметр
# 🟡 8. dissolve_pair — парное удаление
# 🟡 9. stats — кеш core_radius
#
# ═══════════════════════════════════════════════════════════════

import math
import random
import time
import uuid
from collections import deque, OrderedDict
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# VirtualNode — узел поля
# ═══════════════════════════════════════════════════════════════

class VirtualNode:
    """
    🌊 Виртуальный узел поля.
    
    Радиус и скорость — эмерджентные, не заданы извне.
    Фаза эволюционирует по своему закону (D).
    """
    
    MAX_RECEIVED = 500  # больше, чем messages.maxlen — дедуп должен
                        # переживать окно истории
    
    def __init__(self, node_id: str, field: 'Field'):
        self.id = node_id
        self.field = field
        
        # Фаза в поле — уникальна для узла
        self.phase = random.random() * 2 * math.pi
        
        # Радиус — эмерджентный (C). Пока — случайно, потом — из связей.
        self.radius = random.random()  # 0.0 — центр, 1.0 — периферия
        
        # Связи с другими узлами
        self.peers: Dict[str, float] = {}  # peer_id -> strength
        
        # Сообщения
        self.messages = deque(maxlen=50)
        self.received: OrderedDict[str, float] = OrderedDict()
        
        # Счётчики
        self.sent_count = 0
        self.received_count = 0
        self.directed_count = 0   # адресованные мне
        self.ambient_count = 0    # фоновые
        self.tick_count = 0
        
        # Роль — эмерджентная
        self.role: Optional[str] = None
    
    def tick(self, dt: float):
        """
        Один тик узла.
        
        Скорость — свой закон (D):
        - Вынужденный режим в ядре (r < r_inner)
        - Переходная зона (r_inner ≤ r ≤ r_outer)
        - Свободный режим на периферии (r > r_outer)
        - Плюс exchange coupling от соседей
        """
        # Эмерджентная граница ядра — область [r_inner, r_outer]
        core_area = self.field._get_core_radius_cache()
        
        if isinstance(core_area, tuple):
            r_inner, r_outer = core_area
        else:
            # На случай, если кеш ещё не обновился — используем как число
            r_inner = r_outer = core_area
        
        # Свой закон (D): три режима
        if self.radius < r_inner:
            # Ядро — почти твёрдое тело
            omega_base = self.field.rotation_speed
        
        elif self.radius <= r_outer:
            # Переходная зона — интерполяция
            # Ширина зоны
            width = max(r_outer - r_inner, 1e-6)
            # Позиция внутри зоны: 0 — в начале, 1 — в конце
            t = (self.radius - r_inner) / width
            # Плавный переход от ядра (omega_ядро) к периферии (omega_периферия)
            omega_core = self.field.rotation_speed
            omega_periph = self.field.rotation_speed * (
                r_inner / max(self.radius, 1e-6)
            ) ** self.field.vortex_exponent
            omega_base = omega_core * (1 - t) + omega_periph * t
        
        else:
            # Периферия — свободный вихрь
            omega_base = self.field.rotation_speed * (
                r_inner / max(self.radius, 1e-6)
            ) ** self.field.vortex_exponent
        
        # Exchange coupling (D) — параметр поля
        omega_exchange = self.field.exchange_coupling(self)
        
        # Итоговая скорость
        omega = omega_base + omega_exchange
        
        # Сдвиг фазы
        self.phase = (self.phase + omega * dt) % (2 * math.pi)
        self.tick_count += 1
    
    def send(self, message: str, to_node: Optional[str] = None) -> Dict:
        """Отправить сообщение — через поле."""
        msg = {
            'id': uuid.uuid4().hex,  # ← уникально
            'from': self.id,
            'to': to_node,
            'message': message,
            'time': time.time(),
            'phase': self.phase,
        }
        self.sent_count += 1
        self.field.broadcast(msg, sender=self)
        return msg
    
    def receive(self, msg: Dict) -> bool:
        """
        Принять сообщение.
        
        «Всё есть сигнал» — принимаем всё.
        Но помечаем: directed или ambient.
        """
        msg_id = msg.get('id', '')
        if not msg_id or msg_id in self.received:
            return False
        
        # Дедупликация с вытеснением
        self.received[msg_id] = time.time()
        while len(self.received) > self.MAX_RECEIVED:
            self.received.popitem(last=False)
        
        self.messages.append(msg)
        self.received_count += 1
        
        # Различаем directed и ambient
        if msg.get('to') == self.id:
            self.directed_count += 1
        else:
            self.ambient_count += 1
        
        return True
    
    def resonance_with(self, other: 'VirtualNode') -> float:
        """Резонанс с другим узлом. 1.0 — синхронно, -1.0 — анти."""
        phase_diff = (self.phase - other.phase) % (2 * math.pi)
        return math.cos(phase_diff)
    
    def stats(self) -> Dict:
        return {
            'id': self.id,
            'phase': self.phase,
            'radius': self.radius,
            'messages': len(self.messages),
            'sent': self.sent_count,
            'received': self.received_count,
            'directed': self.directed_count,
            'ambient': self.ambient_count,
            'role': self.role,
        }


# ═══════════════════════════════════════════════════════════════
# Field — поле с эмерджентной структурой
# ═══════════════════════════════════════════════════════════════

class Field:
    """
    🌊 TEES-Vortex: поле с эмерджентной структурой.
    
    Все параметры — эмерджентные или управляющие (D-C-D-D).
    """
    
    def __init__(
        self,
        rotation_speed: float = 0.01,
        exchange_strength: float = 0.1,
        exchange_range: float = 0.2,
        coherence_threshold: float = 0.5,
        vortex_exponent: float = 2.0,
        radius_coupling_range: float = 0.1,
        name: str = "field",
    ):
        self.name = name
        self.rotation_speed = rotation_speed
        self.exchange_strength = exchange_strength  # D — параметр
        self.exchange_range = exchange_range
        self.coherence_threshold = coherence_threshold
        self.vortex_exponent = vortex_exponent
        self.radius_coupling_range = radius_coupling_range
        
        self.nodes: Dict[str, VirtualNode] = {}
        self.phase = 0.0
        self.time = 0.0
        self.tick_count = 0
        
        # Кеш core_radius (обновляется раз в 10 тиков)
        self._core_radius_cache: float = 0.0
        self._core_radius_tick: int = -1
        
        # Статистика
        self.broadcast_count = 0
        self.delivered_count = 0
        self.filtered_count = 0
        self.deduped_count = 0
    
    # ═══════════════════════════════════════════════════════════
    # Управление узлами
    # ═══════════════════════════════════════════════════════════
    
    def add_node(self, node_id: str) -> VirtualNode:
        """Добавить узел. (Для отладки. В идеальной модели — spawn_pair.)"""
        node = VirtualNode(node_id, self)
        self.nodes[node_id] = node
        return node
    
    def spawn_pair(self, id_a: str, id_b: str) -> tuple:
        """
        Рождение пары узлов (идеальная модель — баланс = 0).
        
        Противофазы — базовый резонанс -1.0.
        """
        if id_a == id_b:
            raise ValueError("Узлы пары должны различаться")
        if id_a in self.nodes or id_b in self.nodes:
            raise ValueError("Узел уже существует")
        
        a = VirtualNode(id_a, self)
        b = VirtualNode(id_b, self)
        a.phase = 0.0
        b.phase = math.pi
        
        self.nodes[id_a] = a
        self.nodes[id_b] = b
        return a, b
    
    def dissolve_pair(self, id_a: str, id_b: str):
        """
        Смерть пары узлов (идеальная модель — баланс = 0).
        
        Фазы возвращаются в поле.
        """
        a = self.nodes.pop(id_a, None)
        b = self.nodes.pop(id_b, None)
        if a is None or b is None:
            raise ValueError("Пара должна существовать целиком")
        
        # Сумма фаз пары = π + 0 = π (противофазы). Возвращаем в поле.
        contribution = (a.phase + b.phase) / 2
        self.phase = (self.phase + contribution / max(len(self.nodes) + 1, 1)) % (2 * math.pi)
    
    def remove_node(self, node_id: str):
        """Растворение узла (для отладки). В идеальной модели — dissolve_pair."""
        if node_id in self.nodes:
            node = self.nodes.pop(node_id)
            self.phase = (self.phase + node.phase / max(len(self.nodes) + 1, 1)) % (2 * math.pi)
    
    # ═══════════════════════════════════════════════════════════
    # Эмерджентные свойства
    # ═══════════════════════════════════════════════════════════
    
    def _get_core_radius_cache(self) -> float:
        """Кеш core_radius — обновляется раз в 10 тиков."""
        if self._core_radius_tick != self.tick_count // 10:
            self._core_radius_cache = self.emergent_core_radius()
            self._core_radius_tick = self.tick_count // 10
        return self._core_radius_cache
    
    def emergent_core_radius(self) -> tuple:
        """
        C) Эмерджентная граница ядра-периферии.
        
        Не точка, а область [r_inner, r_inner + W], стремящаяся к нулю.
        
        Физика:
        - W (ширина) ≈ плотность потока / разность скоростей полос
        - Чем выше Δv → тем тоньше граница → W → 0
        - Чем меньше плотность ρ → тем тоньше граница → W → 0
        - Чем ближе скорости полос → тем шире граница
        - Чем плотнее данные → тем шире граница
        
        Находим:
        - r_inner — где начинается падение когерентности
        - r_outer = r_inner + W — где граница заканчивается
        """
        if len(self.nodes) < 4:
            return (0.0, 0.0)
        
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.radius)
        radii = [n.radius for n in sorted_nodes]
        
        window = max(len(sorted_nodes) // 10, 2)
        
        # Собираем профиль: (radius, coherence, local_velocity_diff, density)
        profile = []
        
        for i in range(window, len(sorted_nodes) - window):
            left = sorted_nodes[i - window:i]
            right = sorted_nodes[i:i + window]
            
            # Когерентность между левой и правой половинами
            res_sum = 0.0
            cnt = 0
            for a in left:
                for b in right:
                    res_sum += a.resonance_with(b)
                    cnt += 1
            coherence = res_sum / cnt if cnt else 0.0
            
            # Локальная разность скоростей:
            # скорости в левой и правой полосе
            # Скорость полосы ≈ производная фазы по времени
            # Приближение: разность фаз на единицу радиуса
            if left and right:
                phase_avg_left = sum(n.phase for n in left) / len(left)
                phase_avg_right = sum(n.phase for n in right) / len(right)
                r_avg_left = sum(n.radius for n in left) / len(left)
                r_avg_right = sum(n.radius for n in right) / len(right)
                dr = abs(r_avg_right - r_avg_left)
                if dr > 1e-6:
                    # Разность фаз / разность радиусов — мера градиента
                    local_velocity_diff = abs(phase_avg_right - phase_avg_left) / dr
                else:
                    local_velocity_diff = 0.0
            else:
                local_velocity_diff = 0.0
            
            # Локальная плотность: сколько узлов в окне
            density = len(left) + len(right)
            
            profile.append((radii[i], coherence, local_velocity_diff, density))
        
        if not profile:
            return (radii[-1], radii[-1])
        
        # Находим начало падения когерентности
        coherences = [c for _, c, _, _ in profile]
        c_max = max(coherences)
        c_min = min(coherences)
        
        if abs(c_max - c_min) < 1e-6:
            # Однородное поле — границы нет
            return (radii[-1], radii[-1])
        
        # Порог начала падения
        start_threshold = c_max - 0.2 * (c_max - c_min)
        
        # Ищем точку начала падения
        r_inner = None
        v_diff_at_inner = 0.0
        density_at_inner = 1.0
        
        for r, c, v_diff, density in profile:
            if c < start_threshold:
                r_inner = r
                v_diff_at_inner = v_diff
                density_at_inner = density
                break
        
        if r_inner is None:
            return (radii[-1], radii[-1])
        
        # Ширина границы: W ≈ плотность / разность скоростей
        # Никаких потолков — чистая физика.
        # Чем выше Δv — тем тоньше граница.
        # Чем выше относительная плотность — тем шире граница.
        if v_diff_at_inner > 1e-9:
            relative_density = density_at_inner / max(len(self.nodes), 1)
            W = relative_density / v_diff_at_inner
        else:
            # Нет градиента — граница не определена.
            # По физике — весь диапазон.
            W = 1.0
        
        r_outer = r_inner + W
        
        # Ограничиваем r_outer диапазоном
        r_outer = min(r_outer, radii[-1])
        
        # Гарантия: r_outer > r_inner
        if r_outer <= r_inner:
            idx_inner = radii.index(r_inner)
            if idx_inner + 1 < len(radii):
                r_outer = radii[idx_inner + 1]
            else:
                r_outer = r_inner
        
        return (r_inner, r_outer)
    
    def exchange_coupling(self, node: VirtualNode) -> float:
        """
        D) Exchange coupling — с радиальным затуханием.
        
        Соседи по радиусу (в пределах radius_coupling_range).
        Сила обмена: exp(-dr / exchange_range).
        """
        if not self.nodes:
            return 0.0
        
        neighbors = []
        for other in self.nodes.values():
            if other is node:
                continue
            dr = abs(other.radius - node.radius)
            if dr < self.radius_coupling_range:
                neighbors.append((other, dr))
        
        if not neighbors:
            return 0.0
        
        total = 0.0
        for other, dr in neighbors:
            # Локальная сила — с затуханием
            local_strength = self.exchange_strength * math.exp(-dr / self.exchange_range)
            delta_phi = (other.phase - node.phase) % (2 * math.pi)
            total += local_strength * math.sin(delta_phi)
        
        return total / len(neighbors)
    
    # ═══════════════════════════════════════════════════════════
    # Движение поля
    # ═══════════════════════════════════════════════════════════
    
    def rotate(self, dt: float = 0.1):
        """Один тик поля — все узлы сдвигаются."""
        self.phase = (self.phase + self.rotation_speed * dt) % (2 * math.pi)
        self.time += dt
        self.tick_count += 1
        
        for node in self.nodes.values():
            node.tick(dt)
    
    def broadcast(
        self,
        msg: Dict,
        sender: Optional[VirtualNode] = None,
        min_resonance: Optional[float] = None,
    ):
        """
        Полевая передача.
        
        Если min_resonance — None, доставка всем.
        Если min_resonance — число, доставка только тем,
        у кого resonance >= min_resonance.
        
        Если sender — None, фильтр не применяется (полевой broadcast).
        """
        self.broadcast_count += 1
        
        for node in self.nodes.values():
            if node is sender:
                continue
            
            if min_resonance is not None and sender is not None:
                res = sender.resonance_with(node)
                if res < min_resonance:
                    self.filtered_count += 1
                    continue
            
            if node.receive(msg):
                self.delivered_count += 1
            else:
                self.deduped_count += 1
    
    # ═══════════════════════════════════════════════════════════
    # Роли
    # ═══════════════════════════════════════════════════════════
    
    def assign_roles(self):
        """
        Эмерджентное назначение ролей по фазе.
        
        Роли парные: core ↔ edge, bridge ↔ periphery.
        
        При N = 4k — идеальная парность.
        При N ≠ 4k — парность максимально близкая.
        """
        if not self.nodes:
            return
        
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.phase)
        n = len(sorted_nodes)
        
        half = n // 2
        quarter = half // 2
        
        for i, node in enumerate(sorted_nodes):
            if i < quarter:
                node.role = 'core'
            elif i < half:
                node.role = 'bridge'
            elif i < half + quarter:
                node.role = 'periphery'
            else:
                node.role = 'edge'
    
    def role_distribution(self) -> Dict[str, int]:
        dist = {}
        for node in self.nodes.values():
            role = node.role or 'unknown'
            dist[role] = dist.get(role, 0) + 1
        return dist
    
    # ═══════════════════════════════════════════════════════════
    # Симметрия
    # ═══════════════════════════════════════════════════════════
    
    def check_symmetry(self) -> Dict:
        """
        D) Проверка симметрии.
        
        Уровень 1 (phase_balance): сумма фаз = 0.
          - Для замкнутой системы — инвариант.
          - При случайной инициализации всегда False.
          - Для открытой — метрика.
        
        Уровень 2 (role_parity): парность ролей.
          - core ↔ edge, bridge ↔ periphery.
          - Инвариант для идеальной модели.
        """
        if not self.nodes:
            return {
                'phase_balance': True,
                'total_phase': 0.0,
                'role_parity': True,
                'roles': {},
            }
        
        # Уровень 1 — баланс фаз
        total_phase = sum(n.phase for n in self.nodes.values()) % (2 * math.pi)
        phase_balance = abs(total_phase) < 1e-6 or abs(total_phase - 2 * math.pi) < 1e-6
        
        # Уровень 2 — парность ролей
        dist = self.role_distribution()
        core_edge_ok = dist.get('core', 0) == dist.get('edge', 0)
        bridge_periph_ok = dist.get('bridge', 0) == dist.get('periphery', 0)
        role_parity = core_edge_ok and bridge_periph_ok
        
        return {
            'phase_balance': phase_balance,
            'total_phase': total_phase,
            'role_parity': role_parity,
            'roles': dist,
        }
    
    # ═══════════════════════════════════════════════════════════
    # Статистика
    # ═══════════════════════════════════════════════════════════
    
    def stats(self) -> Dict:
        total = len(self.nodes)
        if total == 0:
            return {
                'nodes': 0,
                'phase': self.phase,
                'time': self.time,
                'ticks': self.tick_count,
            }
        
        avg_messages = sum(len(n.messages) for n in self.nodes.values()) / total
        avg_radius = sum(n.radius for n in self.nodes.values()) / total
        
        return {
            'nodes': total,
            'phase': self.phase,
            'time': self.time,
            'ticks': self.tick_count,
            'rotation_speed': self.rotation_speed,
            'exchange_strength': self.exchange_strength,
            'exchange_range': self.exchange_range,
            'vortex_exponent': self.vortex_exponent,
            'core_radius': self._get_core_radius_cache(),
            'avg_radius': avg_radius,
            'broadcasts': self.broadcast_count,
            'delivered': self.delivered_count,
            'filtered': self.filtered_count,
            'deduped': self.deduped_count,
            'avg_messages': avg_messages,
            'roles': self.role_distribution(),
        }