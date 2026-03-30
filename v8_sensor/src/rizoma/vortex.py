"""
vortex.py — 3D вихрь с фрактальной структурой
Версия 15.0 — полная, со всеми наработками
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math
import time


@dataclass
class SpectralComponent:
    """Спектральная компонента с амплитудой и фазой"""
    amplitude: float
    phase: float  # 0..2π
    
    def conjugate(self) -> 'SpectralComponent':
        """Комплексное сопряжение (обращение фазы)"""
        return SpectralComponent(self.amplitude, -self.phase)
    
    def __mul__(self, other: 'SpectralComponent') -> complex:
        """Произведение двух компонент (амплитуда * exp(i*разность фаз))"""
        return self.amplitude * other.amplitude * \
               complex(math.cos(self.phase - other.phase), 
                       math.sin(self.phase - other.phase))
    
    def __add__(self, other: 'SpectralComponent') -> 'SpectralComponent':
        """Сложение компонент с учётом фаз"""
        # Преобразуем в комплексные числа
        z1 = self.amplitude * complex(math.cos(self.phase), math.sin(self.phase))
        z2 = other.amplitude * complex(math.cos(other.phase), math.sin(other.phase))
        z = z1 + z2
        return SpectralComponent(abs(z), math.atan2(z.imag, z.real))


@dataclass
class Vortex3D:
    """
    3D вихрь в поле H
    Слово как устойчивая структура в поле
    
    Полная версия со всеми наработками:
    - 3D координаты для геометрии поля
    - Спектр с амплитудами и фазами (когерентность)
    - Фрактальная иерархия (parent-children)
    - Энергия для нелинейной динамики
    - Временные метки для забывания
    """
    word: str
    x: float
    y: float
    z: float
    spectrum: Dict[float, SpectralComponent]  # частота → (амплитуда, фаза)
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    scale: float = 1.0  # фрактальный масштаб (1=слово, 0.1=буква, 10=фраза)
    amplitude: float = 0.5
    energy: float = 1.0  # энергия вихря (для нелинейной динамики)
    usage_count: int = 0
    last_used: Optional[float] = None
    created: float = field(default_factory=time.time)
    
    # Поля для квантовой аналогии (будут заполняться quantum_analogy.py)
    quantum_state: Optional[Dict] = None
    
    # Поля для топологии (будут заполняться topology.py)
    topological_links: List[str] = field(default_factory=list)
    
    def get_dominant_tau(self) -> Optional[float]:
        """Возвращает доминирующую частоту (максимальная амплитуда)"""
        if not self.spectrum:
            return None
        return max(self.spectrum.items(), key=lambda x: x[1].amplitude)[0]
    
    def get_phase_at_tau(self, tau: float) -> float:
        """Возвращает фазу для заданной частоты"""
        comp = self.spectrum.get(tau)
        return comp.phase if comp else 0.0
    
    def register_use(self):
        """Регистрирует использование вихря"""
        self.usage_count += 1
        self.last_used = time.time()
        self.amplitude = min(1.0, self.amplitude + 0.05)
        self.energy = self.amplitude
    
    def decay(self, dt: float = 0.1, rate: float = 0.02):
        """Затухание вихря со временем"""
        self.amplitude *= (1 - rate * dt)
        self.energy = self.amplitude
        # Затухание спектральных компонент
        for comp in self.spectrum.values():
            comp.amplitude *= (1 - rate * dt)
    
    def distance_to(self, other: 'Vortex3D') -> float:
        """Евклидово расстояние до другого вихря"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def phase_coherence_with(self, other: 'Vortex3D') -> float:
        """
        Фазовая когерентность между двумя вихрями
        Возвращает 0..1
        """
        if not self.spectrum or not other.spectrum:
            return 0.0
        
        common_taus = set(self.spectrum.keys()) & set(other.spectrum.keys())
        if not common_taus:
            return 0.0
        
        total = 0.0
        weight = 0.0
        for tau in common_taus:
            comp1 = self.spectrum[tau]
            comp2 = other.spectrum[tau]
            phase_match = abs(math.cos(comp1.phase - comp2.phase))
            total += min(comp1.amplitude, comp2.amplitude) * phase_match
            weight += min(comp1.amplitude, comp2.amplitude)
        
        return total / weight if weight > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Сериализация в JSON"""
        return {
            "word": self.word,
            "x": self.x, "y": self.y, "z": self.z,
            "spectrum": {str(k): {"amplitude": v.amplitude, "phase": v.phase} 
                        for k, v in self.spectrum.items()},
            "parent": self.parent,
            "children": self.children,
            "scale": self.scale,
            "amplitude": self.amplitude,
            "energy": self.energy,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "created": self.created,
            "topological_links": self.topological_links
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Vortex3D':
        """Десериализация из JSON"""
        spectrum = {}
        for k, v in data.get("spectrum", {}).items():
            spectrum[float(k)] = SpectralComponent(
                amplitude=v.get("amplitude", 0.5),
                phase=v.get("phase", 0.0)
            )
        
        vortex = cls(
            word=data["word"],
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            z=data.get("z", 0.0),
            spectrum=spectrum,
            parent=data.get("parent"),
            children=data.get("children", []),
            scale=data.get("scale", 1.0),
            amplitude=data.get("amplitude", 0.5),
            energy=data.get("energy", 1.0),
            usage_count=data.get("usage_count", 0),
            last_used=data.get("last_used"),
            created=data.get("created", time.time())
        )
        vortex.topological_links = data.get("topological_links", [])
        return vortex