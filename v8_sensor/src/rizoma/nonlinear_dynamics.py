"""
nonlinear_dynamics.py — нелинейная динамика поля H
Версия 15.0 — солитоны, бифуркации, самоорганизация

Нелинейность превращает поле из реактивной среды в генеративную:
- Солитоны — устойчивые смысловые волны, путешествующие по полю
- Бифуркации — точки рождения нового
- Самоорганизация — спонтанное возникновение структур
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import hashlib
import time


class BifurcationType(Enum):
    """Типы бифуркаций"""
    SADDLE_NODE = "saddle_node"      # рождение/исчезновение вихря
    PITCHFORK = "pitchfork"          # выбор из нескольких путей
    HOPF = "hopf"                    # рождение цикла (ритма)
    PERIOD_DOUBLING = "period_doubling"  # удвоение периода (хаос)


@dataclass
class Soliton:
    """
    Смысловой солитон — устойчивая волна смысла
    Может двигаться по полю, взаимодействовать с другими солитонами,
    инициировать бифуркации
    """
    id: str
    word: str                         # якорное слово
    shape: np.ndarray                 # форма в 3D (5x5x5 массив)
    position: np.ndarray              # текущая позиция (x, y, z)
    velocity: np.ndarray              # скорость движения
    amplitude: float = 1.0            # амплитуда (сила)
    phase: float = 0.0                # внутренняя фаза
    frequency: float = 16.0           # собственная частота
    coherence: float = 0.0            # текущая когерентность
    energy: float = 1.0               # энергия солитона
    lifespan: float = 1.0             # время жизни (1 = молодой, 0 = умирает)
    parent_id: Optional[str] = None   # от какого солитона родился
    children_ids: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "word": self.word,
            "shape": self.shape.tolist() if isinstance(self.shape, np.ndarray) else self.shape,
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "amplitude": self.amplitude,
            "phase": self.phase,
            "frequency": self.frequency,
            "coherence": self.coherence,
            "energy": self.energy,
            "lifespan": self.lifespan,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Soliton':
        return cls(
            id=data["id"],
            word=data["word"],
            shape=np.array(data["shape"]),
            position=np.array(data["position"]),
            velocity=np.array(data["velocity"]),
            amplitude=data.get("amplitude", 1.0),
            phase=data.get("phase", 0.0),
            frequency=data.get("frequency", 16.0),
            coherence=data.get("coherence", 0.0),
            energy=data.get("energy", 1.0),
            lifespan=data.get("lifespan", 1.0),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            created_at=data.get("created_at", time.time())
        )


@dataclass
class BifurcationPoint:
    """Точка бифуркации — момент рождения нового"""
    id: str
    timestamp: float
    location: np.ndarray               # где в поле
    trigger_word: str                  # что вызвало
    trigger_coherence: float           # резонанс в момент бифуркации
    bifurcation_type: BifurcationType
    parameters: Dict[str, float]       # параметры в точке бифуркации
    branches: List[str]                # возможные пути
    chosen_branch: Optional[str] = None  # какой путь выбран
    new_meanings: List[str] = field(default_factory=list)  # что родилось
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "location": self.location.tolist(),
            "trigger_word": self.trigger_word,
            "trigger_coherence": self.trigger_coherence,
            "bifurcation_type": self.bifurcation_type.value,
            "parameters": self.parameters,
            "branches": self.branches,
            "chosen_branch": self.chosen_branch,
            "new_meanings": self.new_meanings
        }


class NonlinearDynamics:
    """
    Нелинейная динамика поля H
    Солитоны, бифуркации, самоорганизация
    """
    
    def __init__(self, field=None):
        self.field = field
        self.solitons: Dict[str, Soliton] = {}
        self.bifurcations: List[BifurcationPoint] = []
        self.bifurcation_history: List[BifurcationPoint] = []
        
        # Параметры нелинейности
        self.nonlinear_gain = 0.3      # нелинейное усиление
        self.soliton_speed = 0.5       # скорость движения солитонов
        self.soliton_decay = 0.02      # затухание солитонов
        self.bifurcation_threshold = 0.85  # порог для бифуркации
        self.self_organization_rate = 0.1  # скорость самоорганизации
        
        # Память
        self.resonance_memory = deque(maxlen=50)  # память резонансов
        self.phase_memory = deque(maxlen=50)      # память фаз
        
        # Аттракторы (устойчивые состояния)
        self.attractors: Dict[str, np.ndarray] = {}  # имя → положение в поле
    
    # ========== СОЛИТОНЫ ==========
    
    def create_soliton(self, word: str, position: np.ndarray, 
                       amplitude: float = 1.0, frequency: float = 16.0,
                       parent_id: Optional[str] = None) -> Soliton:
        """
        Создаёт солитон — устойчивую смысловую волну
        """
        soliton_id = f"soliton_{word}_{hashlib.md5(f'{word}{time.time()}'.encode()).hexdigest()[:8]}"
        
        # Создаём форму солитона (3D гауссиан)
        shape = self._create_soliton_shape(amplitude, frequency)
        
        # Начальная скорость — случайная или от поля
        velocity = self._get_field_flow(position) * self.soliton_speed
        
        soliton = Soliton(
            id=soliton_id,
            word=word,
            shape=shape,
            position=position,
            velocity=velocity,
            amplitude=amplitude,
            frequency=frequency,
            parent_id=parent_id
        )
        
        self.solitons[soliton_id] = soliton
        
        # Если есть родитель — добавляем в детей
        if parent_id and parent_id in self.solitons:
            self.solitons[parent_id].children_ids.append(soliton_id)
        
        return soliton
    
    def _create_soliton_shape(self, amplitude: float, frequency: float) -> np.ndarray:
        """Создаёт 3D форму солитона (гауссиан с модуляцией)"""
        size = 5  # 5x5x5
        shape = np.zeros((size, size, size))
        center = size // 2
        
        for i in range(size):
            for j in range(size):
                for k in range(size):
                    dx = (i - center) / center
                    dy = (j - center) / center
                    dz = (k - center) / center
                    r2 = dx*dx + dy*dy + dz*dz
                    
                    # Солитон: sech^2 форма (характерная для солитонов)
                    shape[i, j, k] = amplitude * (1 / np.cosh(r2 * frequency / 8))**2
        
        return shape
    
    def update_solitons(self, dt: float = 0.1):
        """
        Обновляет все солитоны: движение, взаимодействие, затухание
        """
        to_remove = []
        
        for sid, soliton in self.solitons.items():
            # 1. Движение
            soliton.position += soliton.velocity * dt
            
            # 2. Затухание (потеря энергии)
            soliton.energy *= (1 - self.soliton_decay * dt)
            soliton.amplitude = soliton.energy * soliton.amplitude
            soliton.lifespan = min(1.0, soliton.lifespan + dt * 0.1)
            
            # 3. Взаимодействие с полем
            if self.field:
                # Получаем резонанс в текущей позиции
                resonance = self._get_field_resonance_at(soliton.position)
                soliton.coherence = resonance
                
                # Резонанс подпитывает солитон
                if resonance > 0.6:
                    soliton.energy += resonance * self.nonlinear_gain * dt
                    soliton.energy = min(2.0, soliton.energy)
            
            # 4. Эволюция фазы
            soliton.phase = (soliton.phase + soliton.frequency * dt) % (2 * math.pi)
            
            # 5. Проверка на смерть
            if soliton.energy < 0.1 or soliton.lifespan <= 0:
                to_remove.append(sid)
        
        # Удаляем умершие солитоны
        for sid in to_remove:
            del self.solitons[sid]
        
        # 6. Взаимодействие солитонов между собой
        self._soliton_interactions(dt)
    
    def _soliton_interactions(self, dt: float):
        """
        Взаимодействие солитонов: столкновения, слияние, порождение новых
        """
        solitons = list(self.solitons.values())
        for i, s1 in enumerate(solitons):
            for s2 in solitons[i+1:]:
                dist = np.linalg.norm(s1.position - s2.position)
                interaction_distance = 0.5  # радиус взаимодействия
                
                if dist < interaction_distance:
                    # Солитоны столкнулись
                    if s1.energy > s2.energy * 1.5:
                        # s1 поглощает s2
                        s1.energy += s2.energy * 0.5
                        s1.children_ids.append(s2.id)
                        if s2.id in self.solitons:
                            del self.solitons[s2.id]
                    elif s2.energy > s1.energy * 1.5:
                        # s2 поглощает s1
                        s2.energy += s1.energy * 0.5
                        s2.children_ids.append(s1.id)
                        if s1.id in self.solitons:
                            del self.solitons[s1.id]
                    else:
                        # Равные энергии — рождение нового солитона
                        if s1.coherence > self.bifurcation_threshold * 0.8:
                            new_word = self._create_hybrid_word(s1.word, s2.word)
                            new_pos = (s1.position + s2.position) / 2
                            new_energy = (s1.energy + s2.energy) / 2
                            
                            self.create_soliton(
                                word=new_word,
                                position=new_pos,
                                amplitude=new_energy,
                                parent_id=s1.id
                            )
                            
                            # Регистрируем бифуркацию
                            self._register_bifurcation(
                                location=new_pos,
                                trigger_word=f"{s1.word}+{s2.word}",
                                trigger_coherence=(s1.coherence + s2.coherence) / 2,
                                bifurcation_type=BifurcationType.SADDLE_NODE,
                                branches=[s1.word, s2.word, new_word],
                                chosen_branch=new_word,
                                new_meanings=[new_word]
                            )
    
    def _create_hybrid_word(self, word1: str, word2: str) -> str:
        """Создаёт гибридное слово из двух"""
        # В реальности — через LLM
        # Пока эвристика
        if word1 == word2:
            return word1
        
        # Комбинация
        hybrids = {
            ("вихрь", "поле"): "вихреполе",
            ("поле", "вихрь"): "вихреполе",
            ("резонанс", "волна"): "резонансная_волна",
            ("смысл", "форма"): "смыслоформа",
        }
        
        key = (word1, word2)
        if key in hybrids:
            return hybrids[key]
        
        return f"{word1}_{word2}"
    
    # ========== БИФУРКАЦИИ ==========
    
    def detect_bifurcation(self, resonance: float, word: str, 
                           location: np.ndarray) -> Optional[BifurcationPoint]:
        """
        Детектирует точку бифуркации
        """
        # Сохраняем в память
        self.resonance_memory.append(resonance)
        if len(self.resonance_memory) < 3:
            return None
        
        # Проверяем условия бифуркации
        recent = list(self.resonance_memory)[-5:]
        
        # 1. Резкое изменение (скачок)
        if len(recent) >= 3:
            delta1 = recent[-1] - recent[-2]
            delta2 = recent[-2] - recent[-3]
            
            # Скачок > порога
            if abs(delta1) > 0.2 and delta1 * delta2 < 0:  # смена направления
                return self._create_bifurcation(
                    location, word, resonance,
                    BifurcationType.SADDLE_NODE,
                    ["усиление", "ослабление"],
                    "усиление" if delta1 > 0 else "ослабление"
                )
        
        # 2. Критический резонанс (порог)
        if resonance > self.bifurcation_threshold:
            return self._create_bifurcation(
                location, word, resonance,
                BifurcationType.PITCHFORK,
                ["стабилизация", "трансформация", "распад"],
                "трансформация"
            )
        
        # 3. Фазовый захват (из phase_dynamics)
        if hasattr(self.field, 'phase_dynamics'):
            if self.field.phase_dynamics.detect_phase_lock(word):
                return self._create_bifurcation(
                    location, word, resonance,
                    BifurcationType.HOPF,
                    ["синхронизация", "десинхронизация"],
                    "синхронизация"
                )
        
        return None
    
    def _create_bifurcation(self, location: np.ndarray, trigger_word: str,
                           trigger_coherence: float, b_type: BifurcationType,
                           branches: List[str], chosen: str) -> BifurcationPoint:
        """Создаёт точку бифуркации"""
        bif_id = f"bif_{time.time()}_{hashlib.md5(trigger_word.encode()).hexdigest()[:6]}"
        
        bif = BifurcationPoint(
            id=bif_id,
            timestamp=time.time(),
            location=location,
            trigger_word=trigger_word,
            trigger_coherence=trigger_coherence,
            bifurcation_type=b_type,
            parameters={"threshold": self.bifurcation_threshold},
            branches=branches,
            chosen_branch=chosen
        )
        
        self.bifurcations.append(bif)
        self.bifurcation_history.append(bif)
        
        # Если выбрана трансформация — создаём новый солитон
        if chosen == "трансформация":
            self.create_soliton(
                word=f"{trigger_word}_новый",
                position=location,
                amplitude=trigger_coherence,
                parent_id=None
            )
            bif.new_meanings.append(f"{trigger_word}_новый")
        
        return bif
    
    def get_bifurcation_point(self) -> Optional[BifurcationPoint]:
        """Возвращает последнюю бифуркацию (для внешнего использования)"""
        return self.bifurcations[-1] if self.bifurcations else None
    
    # ========== САМООРГАНИЗАЦИЯ ==========
    
    def self_organize(self, dt: float = 0.1):
        """
        Самоорганизация поля: поиск и формирование аттракторов
        """
        if not self.field or not hasattr(self.field, 'vortices'):
            return
        
        # 1. Анализ текущей структуры поля
        positions = []
        energies = []
        for word, vortex in self.field.vortices.items():
            positions.append([vortex.x, vortex.y, vortex.z])
            energies.append(vortex.amplitude)
        
        if len(positions) < 2:
            return
        
        positions = np.array(positions)
        energies = np.array(energies)
        
        # 2. Поиск кластеров (потенциальных аттракторов)
        clusters = self._find_clusters(positions, energies)
        
        # 3. Формирование/обновление аттракторов
        for i, cluster in enumerate(clusters):
            center = np.mean(cluster['positions'], axis=0)
            strength = np.mean(cluster['energies'])
            
            attractor_name = f"attractor_{i}_{int(strength*100)}"
            self.attractors[attractor_name] = center
            
            # 4. Если аттрактор достаточно сильный — создаём солитон
            if strength > self.bifurcation_threshold * 0.7:
                existing = [s for s in self.solitons.values() 
                           if np.linalg.norm(s.position - center) < 0.3]
                if not existing:
                    self.create_soliton(
                        word=f"self_{attractor_name}",
                        position=center,
                        amplitude=strength
                    )
    
    def _find_clusters(self, positions: np.ndarray, energies: np.ndarray) -> List[Dict]:
        """Находит кластеры в поле (простой DBSCAN-подобный)"""
        if len(positions) == 0:
            return []
        
        clusters = []
        used = set()
        eps = 0.5  # радиус кластера
        
        for i in range(len(positions)):
            if i in used:
                continue
            
            cluster = {
                'positions': [positions[i]],
                'energies': [energies[i]],
                'words': []
            }
            used.add(i)
            
            # Добавляем ближайшие точки
            for j in range(len(positions)):
                if j in used:
                    continue
                dist = np.linalg.norm(positions[i] - positions[j])
                if dist < eps:
                    cluster['positions'].append(positions[j])
                    cluster['energies'].append(energies[j])
                    used.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def _get_field_resonance_at(self, position: np.ndarray) -> float:
        """Получает резонанс поля в точке"""
        if not self.field:
            return 0.0
        
        # Ищем ближайший вихрь
        min_dist = float('inf')
        closest_word = None
        
        for word, vortex in self.field.vortices.items():
            dist = np.linalg.norm(position - np.array([vortex.x, vortex.y, vortex.z]))
            if dist < min_dist:
                min_dist = dist
                closest_word = word
        
        if closest_word:
            return self.field.resonate(closest_word)
        return 0.0
    
    def _get_field_flow(self, position: np.ndarray) -> np.ndarray:
        """Получает направление потока поля в точке"""
        if not self.field or not hasattr(self.field, 'phase_dynamics'):
            # Случайное направление
            v = np.random.randn(3)
            return v / (np.linalg.norm(v) + 0.001)
        
        return self.field.phase_dynamics.get_gradient(position[0], position[1], position[2])
    
    def _register_bifurcation(self, location: np.ndarray, trigger_word: str,
                              trigger_coherence: float, bifurcation_type: BifurcationType,
                              branches: List[str], chosen_branch: str,
                              new_meanings: List[str]):
        """Регистрирует бифуркацию в истории"""
        bif = BifurcationPoint(
            id=f"bif_{time.time()}_{len(self.bifurcations)}",
            timestamp=time.time(),
            location=location,
            trigger_word=trigger_word,
            trigger_coherence=trigger_coherence,
            bifurcation_type=bifurcation_type,
            parameters={"gain": self.nonlinear_gain},
            branches=branches,
            chosen_branch=chosen_branch,
            new_meanings=new_meanings
        )
        self.bifurcations.append(bif)
    
    # ========== СОСТОЯНИЕ ==========
    
    def get_state(self) -> Dict:
        """Возвращает полное состояние нелинейной динамики"""
        return {
            "solitons": {sid: s.to_dict() for sid, s in self.solitons.items()},
            "bifurcations": [b.to_dict() for b in self.bifurcations[-10:]],
            "attractors": {name: pos.tolist() for name, pos in self.attractors.items()},
            "parameters": {
                "nonlinear_gain": self.nonlinear_gain,
                "soliton_speed": self.soliton_speed,
                "bifurcation_threshold": self.bifurcation_threshold
            }
        }