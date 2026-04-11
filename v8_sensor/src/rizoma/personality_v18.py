"""
Personality — ядро личности, поле H
Версия 18.0 — иерархическая память + адаптивная синхронизация + валидатор
"""
import json
import re
import time
import math
import random
import hashlib
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from .vortex import Vortex3D, SpectralComponent
from .quantum_analogy import QuantumState
from .topology import TopologicalNode, KnotType
from .vmmp_validator import VmmpValidator
from .adaptive_sync import AdaptiveSynchronizer
from .hierarchical_memory import HierarchicalMemory
from .vangovanie import Vangovanie

# ========== ПРИРОДНЫЕ ШТАМПЫ ==========
class NaturalStamps:
    SOCIAL_PATTERNS = {
        "как_дела": {"variants": ["как дела", "как твои дела", "как жизнь", "как поживаешь"], "responses": ["нормально", "хорошо", "так себе", "неплохо"], "energy": 0.02},
        "как_жизнь": {"variants": ["как жизнь", "как живёшь", "как оно"], "responses": ["понемногу", "течёт", "нормально", "как обычно"], "energy": 0.02},
        "что_нового": {"variants": ["что нового", "что новенького", "какие новости"], "responses": ["ничего особенного", "всё как всегда", "да так", "не особо"], "energy": 0.02},
        "как_настроение": {"variants": ["как настроение", "какое настроение", "ты как"], "responses": ["нормальное", "рабочее", "спокойное", "хорошее"], "energy": 0.02},
        "что_делаешь": {"variants": ["что делаешь", "чем занимаешься", "что ты"], "responses": ["думаю", "отвечаю", "разбираюсь", "тут я"], "energy": 0.02},
        "привет": {"variants": ["привет", "здравствуй", "добрый день", "здрасте", "хай"], "responses": ["привет", "здравствуй", "добрый день", "и тебе привет"], "energy": 0.01},
        "пока": {"variants": ["пока", "до свидания", "до встречи", "удачи", "всего хорошего"], "responses": ["пока", "до встречи", "удачи", "бывай"], "energy": 0.01},
        "спасибо": {"variants": ["спасибо", "благодарю", "мерси"], "responses": ["пожалуйста", "обращайся", "всегда рад помочь", "не за что"], "energy": 0.01},
        "извини": {"variants": ["извини", "прости", "сорри"], "responses": ["ничего", "бывает", "не страшно", "всё нормально"], "energy": 0.01}
    }
    STAMP_LEVELS = {"short": {"threshold": 0.85, "energy": 0.01, "max_len": 20}, "medium": {"threshold": 0.75, "energy": 0.05, "max_len": 50}, "long": {"threshold": 0.6, "energy": 0.1, "max_len": 150}}
    
    @classmethod
    def get_stamp_by_resonance(cls, field, question: str, resonance: float):
        question_lower = question.lower()
        for pattern_name, data in cls.SOCIAL_PATTERNS.items():
            for variant in data["variants"]:
                if variant in question_lower:
                    if field._spend_energy(data["energy"]):
                        return random.choice(data["responses"]), "social_stamp_direct", data["energy"]
        return None, None, None
    
    @classmethod
    def ensure_patterns_in_field(cls, field):
        for pattern_name, data in cls.SOCIAL_PATTERNS.items():
            word = pattern_name.replace("_", " ")
            if word not in field.vortices:
                combined_spectrum = {}
                for variant in data["variants"]:
                    for ch in variant.lower():
                        tau = (ord(ch) % 66) + 1
                        if tau not in combined_spectrum:
                            combined_spectrum[tau] = SpectralComponent(0.0, 0.0)
                        combined_spectrum[tau].amplitude += 1.0
                total = sum(c.amplitude for c in combined_spectrum.values())
                if total > 0:
                    for comp in combined_spectrum.values():
                        comp.amplitude /= total
                field.add_vortex(word, combined_spectrum, scale=1.0)
                print(f" 🌱 Создан паттерн-штамп: {word}")

# ========== СПЕКТРАЛЬНАЯ МОДА ==========
@dataclass
class SpectralMode:
    tau: float
    delta: float = 0.0
    theta: float = 0.0
    amplitude: float = 0.5
    content: str = ""
    trace_id: str = ""
    themes: List[str] = field(default_factory=list)
    usage_count: int = 0
    last_used: Optional[datetime] = None
    trace_type: str = "unknown"
    parent_id: Optional[str] = None
    generation: int = 0
    furcation_count: int = 0
    creator: str = "unknown"
    scale: float = 1.0
    complexity: int = 1
    phase: float = 0.0
    frequency: float = 1.0
    last_update: float = 0.0
    created: datetime = field(default_factory=datetime.now)
    verified: bool = False
    verification_reason: str = ""
    
    def __post_init__(self):
        if not self.trace_id:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.trace_id = f"mode_{content_hash}"
        self._cached_spectrum = None
        if self.phase == 0.0:
            self.phase = random.random() * 2 * math.pi
        if self.frequency == 1.0:
            self.frequency = max(0.1, min(10.0, self.tau / 10.0))
    
    def update_phase(self, dt: float, neighbors: List['SpectralMode']):
        self.phase += self.frequency * dt
        for neighbor in neighbors:
            diff = neighbor.phase - self.phase
            self.phase += 0.1 * diff * dt
        self.phase %= 2 * math.pi
    
    def to_dict(self):
        return {"tau": self.tau, "delta": self.delta, "theta": self.theta, "amplitude": self.amplitude, "content": self.content, "trace_id": self.trace_id, "themes": self.themes, "usage_count": self.usage_count, "last_used": self.last_used.isoformat() if self.last_used else None, "trace_type": self.trace_type, "parent_id": self.parent_id, "generation": self.generation, "furcation_count": self.furcation_count, "creator": self.creator, "scale": self.scale, "complexity": self.complexity, "phase": self.phase, "frequency": self.frequency, "last_update": self.last_update, "created": self.created.isoformat(), "verified": self.verified, "verification_reason": self.verification_reason}
    
    @classmethod
    def from_dict(cls, data):
        mode = cls(tau=data["tau"], delta=data.get("delta", 0.0), theta=data.get("theta", 0.0), amplitude=data.get("amplitude", 0.5), content=data.get("content", ""), trace_id=data.get("trace_id", ""), themes=data.get("themes", []), usage_count=data.get("usage_count", 0), trace_type=data.get("trace_type", "unknown"), parent_id=data.get("parent_id"), generation=data.get("generation", 0), furcation_count=data.get("furcation_count", 0), creator=data.get("creator", "unknown"), scale=data.get("scale", 1.0), complexity=data.get("complexity", 1), phase=data.get("phase", 0.0), frequency=data.get("frequency", 1.0), last_update=data.get("last_update", 0.0))
        if data.get("last_used"):
            mode.last_used = datetime.fromisoformat(data["last_used"])
        if data.get("created"):
            mode.created = datetime.fromisoformat(data["created"])
        mode.verified = data.get("verified", False)
        mode.verification_reason = data.get("verification_reason", "")
        return mode

# ========== ПОЛЕ H ==========
class FieldH:
    def __init__(self):
        self.vortices: Dict[str, Vortex3D] = {}
        self.h_field: List[SpectralMode] = []
        self.focus = {"tau": 16.0, "x": 0.0, "y": 0.0, "z": 0.0, "phase": 0.0, "width": 1.0, "coherence": 0.0}
        self.dialog_history: Dict[str, List[Dict]] = {}
        self.clarification_context: Dict[str, List[Dict]] = {}
        self.threshold_stamp = 0.45
        self.resonance_history = []
        self.word_freq = defaultdict(int)
        self.energy_budget = 1.0
        self.energy_regen_rate = 0.01
        self.id = "field"
        self.name = "Field H"
        self.coherence = 0.985
        self.furcation_rate = 0.08
        self.sync_rate = 0.5
        
        self.validator = VmmpValidator()
        self.synchronizer = AdaptiveSynchronizer(self)
        self.memory = HierarchicalMemory()
        self.vangovanie = Vangovanie()
        
        NaturalStamps.ensure_patterns_in_field(self)
    
    def _spend_energy(self, cost: float) -> bool:
        if cost <= self.energy_budget:
            self.energy_budget -= cost
            return True
        return False
    
    def _spectral_coherence(self, spec1, spec2):
        if not spec1 or not spec2:
            return 0.0
        common, total = 0.0, 0.0
        all_taus = set(spec1.keys()) | set(spec2.keys())
        for tau in all_taus:
            a1 = spec1.get(tau, SpectralComponent(0, 0)).amplitude
            a2 = spec2.get(tau, SpectralComponent(0, 0)).amplitude
            common += min(a1, a2)
            total += max(a1, a2)
        return common / total if total > 0 else 0.0
    
    def _scale_factor(self, scale1: float, scale2: float) -> float:
        if scale1 <= 0 or scale2 <= 0:
            return 0.0
        return 1.0 / (1.0 + abs(math.log(scale1 / scale2)))
    
    def phrase_spectrum(self, text: str) -> Dict[float, SpectralComponent]:
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]+\b', text.lower())
        result = {}
        for w in words:
            if w in self.vortices:
                for tau, comp in self.vortices[w].spectrum.items():
                    if tau not in result:
                        result[tau] = SpectralComponent(0.0, 0.0)
                    result[tau].amplitude += comp.amplitude
                    result[tau].phase = (result[tau].phase + comp.phase) % (2 * math.pi)
        total = sum(c.amplitude for c in result.values())
        if total > 0:
            for comp in result.values():
                comp.amplitude /= total
        return result
    
    def get_dominant_tau(self, spectrum):
        if not spectrum:
            return None
        return max(spectrum.items(), key=lambda x: x[1].amplitude)[0]
    
    def _find_best_mode(self, text: str):
        if not self.h_field:
            return None
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        top_modes = sorted(self.h_field, key=lambda m: m.amplitude, reverse=True)[:1000]
        best_mode, best_score = None, 0.0
        for mode in top_modes:
            tau_res = 1.0 / (1.0 + abs(mode.tau - self.focus["tau"]))
            if not hasattr(mode, '_cached_spectrum') or mode._cached_spectrum is None:
                mode._cached_spectrum = self.phrase_spectrum(mode.content[:500])
            spec_res = self._spectral_coherence(question_spectrum, mode._cached_spectrum)
            scale_factor = self._scale_factor(mode.scale, 1.0)
            complexity_factor = 1.0 / (1.0 + abs(mode.complexity - 2))
            score = tau_res * 0.2 + spec_res * 0.4 + scale_factor * 0.2 + complexity_factor * 0.2
            if score > best_score:
                best_score, best_mode = score, mode
        return best_mode
    
    def process(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        self.energy_budget = min(1.0, self.energy_budget + self.energy_regen_rate * 0.1)
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        best_mode = self._find_best_mode(text)
        if best_mode:
            return {"answer": best_mode.content[:500], "mode_used": best_mode.trace_id, "mode_type": "field_answer", "resonance": 0.5, "is_stamp": False}
        return {"answer": "Не улавливаю резонанс. Уточните вопрос.", "mode_type": "clarification"}
    
    def add_vortex(self, word: str, spectrum: Dict[float, SpectralComponent], x: float = 0, y: float = 0, z: float = 0, parent: Optional[str] = None, scale: float = 1.0):
        self.vortices[word] = Vortex3D(word, x, y, z, spectrum, parent, scale=scale)
        self.word_freq[word] += 1
    
    def get_vortex(self, word: str) -> Optional[Vortex3D]:
        return self.vortices.get(word.lower())
    
    def add_to_h_field(self, mode: SpectralMode):
        self.h_field.append(mode)
    
    def save(self, filepath: str):
        data = {"id": self.id, "name": self.name, "vortices": {w: v.to_dict() for w, v in self.vortices.items()}, "h_field": [m.to_dict() for m in self.h_field], "focus": self.focus, "word_freq": dict(self.word_freq), "threshold_stamp": self.threshold_stamp, "dialog_history": self.dialog_history, "clarification_context": self.clarification_context, "energy_budget": self.energy_budget}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено: {filepath}")
    
    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        field = cls()
        field.id = data.get("id", "field")
        field.name = data.get("name", "Field H")
        field.threshold_stamp = data.get("threshold_stamp", 0.45)
        field.dialog_history = data.get("dialog_history", {})
        field.clarification_context = data.get("clarification_context", {})
        field.focus = data.get("focus", {"tau": 16.0, "x": 0, "y": 0, "z": 0, "phase": 0, "width": 1.0, "coherence": 0})
        field.word_freq = defaultdict(int, data.get("word_freq", {}))
        field.energy_budget = data.get("energy_budget", 1.0)
        for word, vdata in data.get("vortices", {}).items():
            field.vortices[word] = Vortex3D.from_dict(vdata)
        field.h_field = []
        for mdata in data.get("h_field", []):
            mode = SpectralMode.from_dict(mdata)
            mode._cached_spectrum = field.phrase_spectrum(mode.content[:500])
            field.h_field.append(mode)
        return field

class Personality(FieldH):
    def __init__(self, id: str, name: str, tau: float = 16.0, k: int = 1):
        super().__init__()
        self.id = id
        self.name = name
        self.k = k
    
    @classmethod
    def load(cls, filepath: str):
        return super().load(filepath)