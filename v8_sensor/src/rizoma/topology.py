"""
topology.py — топологические структуры поля H
Версия 15.0 — узлы, зацепления, петли, монодромия

Топология позволяет полю иметь нетривиальную структуру смыслов:
- Узлы — смыслы, связанные неразрывно
- Зацепления — смыслы, которые нельзя разделить
- Петли — смыслы, возвращающиеся к себе
- Монодромия — обход вокруг смысла меняет его
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time


class KnotType(Enum):
    """Типы топологических узлов"""
    UNKNOT = "unknot"           # тривиальный узел
    TREFOIL = "trefoil"         # трилистник
    FIGURE_EIGHT = "figure_eight"  # восьмёрка
    HOPF_LINK = "hopf_link"     # зацепление Хопфа
    BORROMEAN = "borromean"     # кольца Борромео


@dataclass
class TopologicalNode:
    """Топологический узел — неразрывная связь смыслов"""
    id: str
    words: List[str]            # смыслы в узле
    knot_type: KnotType
    crossing_number: int        # число пересечений
    is_linked: bool             # зацеплен ли с другими
    linked_with: List[str]      # с какими узлами зацеплен
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "words": self.words,
            "knot_type": self.knot_type.value,
            "crossing_number": self.crossing_number,
            "is_linked": self.is_linked,
            "linked_with": self.linked_with,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TopologicalNode':
        knot_type = KnotType(data.get("knot_type", "unknot"))
        return cls(
            id=data["id"],
            words=data["words"],
            knot_type=knot_type,
            crossing_number=data.get("crossing_number", 0),
            is_linked=data.get("is_linked", False),
            linked_with=data.get("linked_with", []),
            created_at=data.get("created_at", time.time())
        )


@dataclass
class TopologicalLoop:
    """Топологическая петля — смысл, возвращающийся к себе"""
    id: str
    word: str
    path: List[Tuple[float, float, float]]  # путь в 3D
    length: float
    closed: bool = True
    monodromy: complex = complex(1, 0)      # изменение при обходе
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "word": self.word,
            "path": self.path,
            "length": self.length,
            "closed": self.closed,
            "monodromy": [self.monodromy.real, self.monodromy.imag],
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TopologicalLoop':
        path = data.get("path", [])
        monodromy = complex(data.get("monodromy", [1, 0])[0], data.get("monodromy", [1, 0])[1])
        return cls(
            id=data["id"],
            word=data["word"],
            path=path,
            length=data.get("length", 0.0),
            closed=data.get("closed", True),
            monodromy=monodromy,
            created_at=data.get("created_at", time.time())
        )


class Topology:
    """
    Топологические структуры поля H
    """
    
    def __init__(self, field=None):
        self.field = field
        self.nodes: Dict[str, TopologicalNode] = {}
        self.loops: Dict[str, TopologicalLoop] = {}
        self.link_history: List[Dict] = []
        
        # Топологические параметры
        self.knot_detection_threshold = 0.7  # порог для обнаружения узла
        
    # ========== УЗЛЫ ==========
    
    def create_knot(self, words: List[str], knot_type: KnotType = KnotType.TREFOIL) -> TopologicalNode:
        """
        Создаёт топологический узел — неразрывную связь смыслов
        """
        node_id = f"knot_{'_'.join(words)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
        node = TopologicalNode(
            id=node_id,
            words=words,
            knot_type=knot_type,
            crossing_number=self._get_crossing_number(knot_type),
            is_linked=False,
            linked_with=[]
        )
        
        self.nodes[node_id] = node
        
        # Регистрируем в поле
        if self.field:
            self._register_knot_in_field(node)
        
        return node
    
    def _get_crossing_number(self, knot_type: KnotType) -> int:
        """Число пересечений для типа узла"""
        mapping = {
            KnotType.UNKNOT: 0,
            KnotType.TREFOIL: 3,
            KnotType.FIGURE_EIGHT: 4,
            KnotType.HOPF_LINK: 2,
            KnotType.BORROMEAN: 6
        }
        return mapping.get(knot_type, 3)
    
    def link_knots(self, knot1_id: str, knot2_id: str):
        """
        Зацепляет два узла — теперь их нельзя разделить
        """
        knot1 = self.nodes.get(knot1_id)
        knot2 = self.nodes.get(knot2_id)
        
        if not knot1 or not knot2:
            return
        
        knot1.is_linked = True
        knot2.is_linked = True
        
        if knot2_id not in knot1.linked_with:
            knot1.linked_with.append(knot2_id)
        if knot1_id not in knot2.linked_with:
            knot2.linked_with.append(knot1_id)
        
        self.link_history.append({
            "knot1": knot1_id,
            "knot2": knot2_id,
            "timestamp": time.time()
        })
    
    def _register_knot_in_field(self, node: TopologicalNode):
        """Регистрирует узел в поле (обновляет вихри)"""
        if not hasattr(self.field, 'vortices'):
            return
        
        # Для каждого слова в узле усиливаем связь
        for word in node.words:
            if word in self.field.vortices:
                vortex = self.field.vortices[word]
                vortex.amplitude *= 1.2
                vortex.energy = vortex.amplitude
    
    # ========== ПЕТЛИ ==========
    
    def create_loop(self, word: str, path: Optional[List[Tuple[float, float, float]]] = None) -> TopologicalLoop:
        """
        Создаёт топологическую петлю — смысл, возвращающийся к себе
        """
        if path is None:
            # Создаём окружность вокруг позиции слова
            vortex = self.field.vortices.get(word) if self.field else None
            center = (vortex.x, vortex.y, vortex.z) if vortex else (0, 0, 0)
            
            path = []
            for t in np.linspace(0, 2*math.pi, 20):
                path.append((
                    center[0] + math.cos(t),
                    center[1] + math.sin(t),
                    center[2]
                ))
        
        # Вычисляем длину пути
        length = 0
        for i in range(len(path)-1):
            dx = path[i+1][0] - path[i][0]
            dy = path[i+1][1] - path[i][1]
            dz = path[i+1][2] - path[i][2]
            length += math.sqrt(dx*dx + dy*dy + dz*dz)
        
        loop_id = f"loop_{word}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
        loop = TopologicalLoop(
            id=loop_id,
            word=word,
            path=path,
            length=length,
            closed=True,
            monodromy=complex(1, 0)
        )
        
        self.loops[loop_id] = loop
        
        return loop
    
    def compute_monodromy(self, loop_id: str) -> complex:
        """
        Вычисляет монодромию — как меняется смысл при обходе петли
        """
        loop = self.loops.get(loop_id)
        if not loop:
            return complex(1, 0)
        
        # Монодромия зависит от кривизны поля вдоль пути
        if self.field and hasattr(self.field, 'phase_dynamics'):
            monodromy = complex(1, 0)
            for point in loop.path:
                phase = self.field.phase_dynamics.get_phase_at(point[0], point[1], point[2])
                monodromy *= complex(math.cos(phase), math.sin(phase))
            loop.monodromy = monodromy
            return monodromy
        
        return complex(1, 0)
    
    # ========== ЗАЦЕПЛЕНИЯ ==========
    
    def detect_linking(self) -> List[Tuple[str, str]]:
        """
        Обнаруживает зацепления между узлами
        """
        links = []
        node_list = list(self.nodes.keys())
        
        for i, id1 in enumerate(node_list):
            for id2 in node_list[i+1:]:
                if self._are_linked(id1, id2):
                    links.append((id1, id2))
        
        return links
    
    def _are_linked(self, node_id1: str, node_id2: str) -> bool:
        """Проверяет, зацеплены ли два узла"""
        node1 = self.nodes.get(node_id1)
        node2 = self.nodes.get(node_id2)
        
        if not node1 or not node2:
            return False
        
        # Проверяем по словам
        common_words = set(node1.words) & set(node2.words)
        if common_words:
            return True
        
        # Проверяем по явной связи
        if node2.id in node1.linked_with:
            return True
        
        return False
    
    # ========== ТОПОЛОГИЧЕСКАЯ ИНВАРИАНТНОСТЬ ==========
    
    def compute_invariant(self, node_id: str) -> int:
        """
        Вычисляет топологический инвариант узла
        (не меняется при непрерывных деформациях)
        """
        node = self.nodes.get(node_id)
        if not node:
            return 0
        
        # Простой инвариант — число пересечений
        return node.crossing_number
    
    def is_topologically_equivalent(self, node1_id: str, node2_id: str) -> bool:
        """
        Проверяет топологическую эквивалентность двух узлов
        """
        node1 = self.nodes.get(node1_id)
        node2 = self.nodes.get(node2_id)
        
        if not node1 or not node2:
            return False
        
        return (node1.knot_type == node2.knot_type and
                node1.crossing_number == node2.crossing_number and
                node1.is_linked == node2.is_linked)
    
    # ========== ЭВОЛЮЦИЯ ==========
    
    def evolve(self, dt: float = 0.1):
        """
        Эволюция топологических структур
        """
        # Петли могут распутываться
        to_remove = []
        for loop_id, loop in self.loops.items():
            # Вычисляем монодромию
            monodromy = self.compute_monodromy(loop_id)
            
            # Если монодромия тривиальна — петля может распуститься
            if abs(monodromy - 1) < 0.1:
                if np.random.random() < 0.01:  # медленное распутывание
                    to_remove.append(loop_id)
        
        for loop_id in to_remove:
            del self.loops[loop_id]
    
    # ========== СОСТОЯНИЕ ==========
    
    def get_state(self) -> Dict:
        """Возвращает топологическое состояние поля"""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "loops": {lid: loop.to_dict() for lid, loop in self.loops.items()},
            "links": self.link_history[-10:],
            "parameters": {
                "detection_threshold": self.knot_detection_threshold
            }
        }
    
    def to_dict(self) -> Dict:
        return self.get_state()
    
    @classmethod
    def from_dict(cls, data: Dict, field=None) -> 'Topology':
        top = cls(field)
        for nid, ndata in data.get("nodes", {}).items():
            top.nodes[nid] = TopologicalNode.from_dict(ndata)
        for lid, ldata in data.get("loops", {}).items():
            top.loops[lid] = TopologicalLoop.from_dict(ldata)
        top.link_history = data.get("links", [])
        return top