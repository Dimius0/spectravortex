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

        # Сжатие поля
        self.compression_level = 0.0
        self.compression_active = False
        self.compression_phase = 'normal'  # normal/expansion/collapse/supercompression/released
        self.shock_events = []

        # Кеш для оптимизации
        self._sorted_nodes_cache = None
        self._sorted_nodes_tick = -1
        self._node_index_cache = {}
    
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
        """Кеш core_radius — обновляется раз в 50 тиков + сортировка."""
        if self._core_radius_tick != self.tick_count // 50:
            # Обновляем сортированный кеш
            self._sorted_nodes_cache = sorted(self.nodes.values(), key=lambda n: n.radius)
            self._sorted_nodes_tick = self.tick_count
            self._node_index_cache = {
                id(n): i for i, n in enumerate(self._sorted_nodes_cache)
            }
            
            self._core_radius_cache = self.emergent_core_radius()
            self._core_radius_tick = self.tick_count // 50
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
    
    def exchange_coupling(self, node: VirtualNode, sample_size: int = None) -> float:
        """
        D) Exchange coupling — разряженная выборка.
        
        Принцип Бернштейна-Вазирани с равномерным покрытием:
        - Не случайная выборка.
        - А — разряженная по радиусу.
        - Покрытие — всё поле.
        - Точность — выше при том же k.
        
        sample_size:
        - None → авто: min(√N, 50)
        - int → фиксированный
        """
        if not self.nodes:
            return 0.0
        
        total_nodes = len(self.nodes)
        if total_nodes < 2:
            return 0.0
        
        # Размер выборки
        if sample_size is None:
            sample_size = max(5, int(math.sqrt(total_nodes)))
            sample_size = min(sample_size, 50)
        
        # Используем сортированный кеш (обновляется в _get_core_radius_cache)
        if self._sorted_nodes_cache is None:
            self._sorted_nodes_cache = sorted(self.nodes.values(), key=lambda n: n.radius)
            self._node_index_cache = {
                id(n): i for i, n in enumerate(self._sorted_nodes_cache)
            }
        
        sorted_nodes = self._sorted_nodes_cache
        idx = self._node_index_cache.get(id(node))
        if idx is None:
            return 0.0
        
        # Равномерный шаг по отсортированному массиву
        # Берём sample_size точек, равномерно распределённых
        step = max(1, total_nodes // sample_size)
        
        candidates = []
        
        # Идём влево и вправо от idx с шагом
        # Это даёт разряженную выборку по всему полю
        i = idx - step * (sample_size // 2)
        count = 0
        
        while count < sample_size:
            if 0 <= i < total_nodes:
                other = sorted_nodes[i]
                if other is not node:
                    dr = abs(other.radius - node.radius)
                    if dr < self.radius_coupling_range:
                        candidates.append((other, dr))
            i += step
            count += 1
            # Зацикливаемся, если вышли за границы
            if i >= total_nodes:
                i = 0
        
        if not candidates:
            return 0.0
        
        # Один «запрос» — суммируем влияние выборки
        total = 0.0
        for other, dr in candidates:
            local_strength = self.exchange_strength * math.exp(-dr / self.exchange_range)
            delta_phi = (other.phase - node.phase) % (2 * math.pi)
            total += local_strength * math.sin(delta_phi)
        
        return total / len(candidates)
    
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
    # Сжатие поля и полевой удар
    # ═══════════════════════════════════════════════════════════
    
    def compress(self, force: float = 0.1, dt: float = 0.1):
        """
        Сжатие поля внешним полем.
        
        Физика (как в сонолюминесценции):
        
        Фаза 1 — поглощение энергии:
          - Вихрь раздувается.
          - Радиус растёт.
          - Электрон — на дальней орбитали.
          - Состояние нестабильно.
        
        Фаза 2 — коллапс:
          - Нестабильность возвращает.
          - Радиус падает.
          - Проскакивает равновесие.
          - Идёт в сверхсжатие.
        
        Фаза 3 — сверхсжатие:
          - Радиус минимальный.
          - Плотность максимальная.
          - Готовность к удару.
        
        force — сила внешнего поля (0.0-1.0).
        dt — шаг времени.
        """
        if not self.nodes:
            return
        
        # Уровень сжатия — накопление
        self.compression_level = min(1.0, self.compression_level + force)
        
        # Фаза 1 — раздувание (пока уровень < 0.5)
        if self.compression_level < 0.5:
            self.compression_phase = 'expansion'
            # Радиусы растут
            for node in self.nodes.values():
                node.radius = min(1.0, node.radius * (1.0 + force * 0.5))
        
        # Фаза 2 — коллапс (0.5 ≤ уровень < 0.8)
        elif self.compression_level < 0.8:
            self.compression_phase = 'collapse'
            # Радиусы падают
            for node in self.nodes.values():
                node.radius = max(0.0, node.radius * (1.0 - force * 0.7))
        
        # Фаза 3 — сверхсжатие (уровень ≥ 0.8)
        else:
            self.compression_phase = 'supercompression'
            # Радиусы минимальные
            for node in self.nodes.values():
                node.radius = max(0.0, node.radius * (1.0 - force * 0.3))
        
        self.compression_active = True
        
        # Сдвиг фаз — синхронизация (на всех фазах)
        avg_phase = sum(n.phase for n in self.nodes.values()) / len(self.nodes)
        for node in self.nodes.values():
            delta = (avg_phase - node.phase) % (2 * math.pi)
            if delta > math.pi:
                delta -= 2 * math.pi
            node.phase = (node.phase + delta * force * dt) % (2 * math.pi)
        
        # Сброс кеша core_radius
        self._core_radius_tick = -1
    
    def release(self) -> dict:
        """
        Обратный ход — полевой удар.
        
        После сверхсжатия:
          - Резкое расширение.
          - Ударная волна.
          - Фронт волны — фотон.
          - Новая TEES — структура фронта.
        """
        if not self.nodes:
            return {'shock': False}
        
        was_compressed = self.compression_active
        level_at_release = self.compression_level
        phase_at_release = getattr(self, 'compression_phase', 'unknown')
        
        self.compression_active = False
        self.compression_level = 0.0
        self.compression_phase = 'released'
        
        if not was_compressed:
            return {'shock': False, 'level': 0.0}
        
        # Амплитуда удара
        shock_amplitude = level_at_release * len(self.nodes)
        
        # Фронт волны — структура
        shock_front = []
        
        for node in self.nodes.values():
            # Импульс — расширение
            # Направление — от центра наружу
            radial_impulse = shock_amplitude * 0.01
            node.radius = min(1.0, node.radius * (1.0 + radial_impulse))
            
            # Импульс фазы — расхождение
            phase_impulse = (random.random() - 0.5) * shock_amplitude * 0.1
            node.phase = (node.phase + phase_impulse) % (2 * math.pi)
            
            shock_front.append({
                'node_id': node.id,
                'radial_impulse': radial_impulse,
                'phase_impulse': phase_impulse,
                'new_radius': node.radius,
                'new_phase': node.phase,
            })
        
        # Создаём новый фронт — TEES фронта
        # Собираем "genome" фронта из импульсов
        front_signature = sum(f['phase_impulse'] for f in shock_front) % (2 * math.pi)
        
        event = {
            'shock': True,
            'phase': phase_at_release,
            'level': level_at_release,
            'amplitude': shock_amplitude,
            'front_size': len(shock_front),
            'front_signature': front_signature,
            'time': self.time,
        }
        
        # В лог
        self.shock_events.append(event)
        if len(self.shock_events) > 100:
            self.shock_events = self.shock_events[-100:]
        
        # Сброс кеша
        self._core_radius_tick = -1
        
        return event                  
    
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
        Уровень 1б (phase_coherence): средняя синхронность фаз (0..1).
        Уровень 2 (role_parity): парность ролей.
        """
        if not self.nodes:
            return {
                'phase_balance': True,
                'phase_coherence': 1.0,
                'total_phase': 0.0,
                'role_parity': True,
                'roles': {},
            }
        
        # Уровень 1 — баланс фаз
        total_phase = sum(n.phase for n in self.nodes.values()) % (2 * math.pi)
        phase_balance = abs(total_phase) < 1e-6 or abs(total_phase - 2 * math.pi) < 1e-6
        
        # Уровень 1б — средняя синхронность фаз
        # Векторная сумма всех фаз, нормированная на N
        # 0 = хаос, 1 = полная синхронизация
        phases = [n.phase for n in self.nodes.values()]
        sum_cos = sum(math.cos(p) for p in phases)
        sum_sin = sum(math.sin(p) for p in phases)
        phase_coherence = math.sqrt(sum_cos ** 2 + sum_sin ** 2) / len(phases)
        
        # Уровень 2 — парность ролей
        dist = self.role_distribution()
        core_edge_ok = dist.get('core', 0) == dist.get('edge', 0)
        bridge_periph_ok = dist.get('bridge', 0) == dist.get('periphery', 0)
        role_parity = core_edge_ok and bridge_periph_ok
        
        return {
            'phase_balance': phase_balance,
            'phase_coherence': phase_coherence,
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