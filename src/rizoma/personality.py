"""
Personality — ядро личности в платформе Ризома.
Версия 6.5 — фильтрация ссылок из постов
"""
import json
import hashlib
import random
import re
import math
import time
import numpy as np
from collections import Counter
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .selector import Selector, SpectralResonator


class MemoryAccess(Enum):
    PRIVATE = "private"
    RELATION = "relation"
    PUBLIC = "public"


class MemoryMode(Enum):
    ACTIVE = "active"
    DEEP = "deep"
    SLEEP = "sleep"
    DREAM = "dream"


@dataclass
class Defect:
    name: str
    vector: float
    strength: float = 0.5
    contexts: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "vector": self.vector,
            "strength": self.strength,
            "contexts": self.contexts
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            vector=data["vector"],
            strength=data.get("strength", 0.5),
            contexts=data.get("contexts", [])
        )


@dataclass
class SpectralMode:
    """Спектральная мода поля H — рождается и живёт сама"""
    tau: float
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

    success_history: List[bool] = field(default_factory=list)
    resonance_history: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.trace_id:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.trace_id = f"mode_{content_hash}"
        # Очищаем content от ссылок при создании
        self.content = self._clean_links(self.content)

    def _clean_links(self, text: str) -> str:
        """Убирает ссылки на GitHub и другие URL из текста"""
        if not text:
            return text
        
        # Убираем github.com ссылки
        text = re.sub(r'https?://(?:www\.)?github\.com/[^\s]+', '', text)
        text = re.sub(r'github\.com/[^\s]+', '', text)
        text = re.sub(r'com/Dimius0/[^\s]+', '', text)
        
        # Убираем blob/raw ссылки
        text = re.sub(r'blob/main/[^\s]+', '', text)
        text = re.sub(r'raw/[^\s]+', '', text)
        
        # Убираем другие URL
        text = re.sub(r'https?://[^\s]+', '', text)
        
        # Убираем пустые строки и лишние пробелы
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Убираем следы от ссылок (одиночные слова типа "blob", "main")
        text = re.sub(r'\b(blob|main|raw|tree|commit)\b\s*', '', text)
        
        return text.strip()

    @property
    def effective_amplitude(self):
        frequency_factor = 1.0 + 0.05 * self.usage_count
        return min(1.0, self.amplitude * frequency_factor)

    @property
    def f_stability(self) -> float:
        E = self.amplitude * (1 + 0.1 * self.usage_count)
        if self.success_history:
            recent_success = sum(self.success_history[-10:]) / len(self.success_history[-10:])
            E += recent_success * 0.3
        if self.resonance_history:
            avg_resonance = sum(self.resonance_history[-20:]) / len(self.resonance_history[-20:])
            E += avg_resonance * 0.2
        return min(2.0, E)

    def register_use(self, resonance: float = 0.5, success: bool = True):
        self.usage_count += 1
        self.last_used = datetime.now()
        self.resonance_history.append(resonance)
        self.success_history.append(success)
        if len(self.resonance_history) > 50:
            self.resonance_history = self.resonance_history[-50:]
        if len(self.success_history) > 50:
            self.success_history = self.success_history[-50:]
        self._update_amplitude(resonance, success)

    def _update_amplitude(self, resonance: float, success: bool):
        if success:
            delta = resonance * 0.1 * (1 - self.amplitude)
            self.amplitude = min(1.0, self.amplitude + delta)
        else:
            self.amplitude *= 0.95

    def get_random_sentence(self) -> str:
        """Возвращает случайное предложение из content"""
        if not self.content:
            return ""
        sentences = re.split(r'[.!?]+', self.content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if sentences:
            return self._clean_links(random.choice(sentences))
        return self._clean_links(self.content[:100])

    def to_dict(self):
        return {
            "tau": self.tau,
            "amplitude": self.amplitude,
            "content": self.content,
            "trace_id": self.trace_id,
            "themes": self.themes,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "trace_type": self.trace_type,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "furcation_count": self.furcation_count,
            "success_history": self.success_history,
            "resonance_history": self.resonance_history
        }

    @classmethod
    def from_dict(cls, data):
        mode = cls(
            tau=data["tau"],
            amplitude=data.get("amplitude", 0.5),
            content=data.get("content", ""),
            trace_id=data.get("trace_id", ""),
            themes=data.get("themes", []),
            usage_count=data.get("usage_count", 0),
            trace_type=data.get("trace_type", "unknown"),
            parent_id=data.get("parent_id"),
            generation=data.get("generation", 0),
            furcation_count=data.get("furcation_count", 0)
        )
        mode.success_history = data.get("success_history", [])
        mode.resonance_history = data.get("resonance_history", [])
        if data.get("last_used"):
            mode.last_used = datetime.fromisoformat(data["last_used"])
        return mode


@dataclass
class MemoryBranch:
    branch_id: str
    traces: List[SpectralMode] = field(default_factory=list)

    def add_trace(self, trace: SpectralMode):
        self.traces.append(trace)

    def get_traces(self, limit: int = 100, min_weight: float = 0.0):
        sorted_traces = sorted(self.traces, key=lambda t: t.effective_amplitude, reverse=True)
        return [t for t in sorted_traces[:limit] if t.effective_amplitude >= min_weight]

    def to_dict(self):
        return {
            "branch_id": self.branch_id,
            "traces": [t.to_dict() for t in self.traces]
        }

    @classmethod
    def from_dict(cls, data):
        traces = [SpectralMode.from_dict(t) for t in data.get("traces", [])]
        return cls(
            branch_id=data["branch_id"],
            traces=traces
        )


class MemoryTree:
    def __init__(self, owner_id: str, entity_id: str):
        self.owner_id = owner_id
        self.entity_id = entity_id
        self.core_traces: List[SpectralMode] = []
        self.branches: Dict[str, MemoryBranch] = {}
        self.public_branch: MemoryBranch = MemoryBranch("public")

    def add_trace(self, trace: SpectralMode, branch_id: Optional[str] = None):
        if branch_id is None:
            self.core_traces.append(trace)
        elif branch_id == "public":
            self.public_branch.add_trace(trace)
        else:
            if branch_id not in self.branches:
                self.branches[branch_id] = MemoryBranch(branch_id)
            self.branches[branch_id].add_trace(trace)

    def get_traces(self, branch_id: Optional[str] = None,
                   access_level: MemoryAccess = MemoryAccess.PRIVATE,
                   mode: MemoryMode = MemoryMode.ACTIVE,
                   requesting_entity: Optional[str] = None) -> List[SpectralMode]:

        if branch_id is None:
            traces = self.core_traces
        elif branch_id == "public":
            traces = self.public_branch.traces
        else:
            if branch_id not in self.branches:
                return []
            traces = self.branches[branch_id].traces

        if mode == MemoryMode.ACTIVE:
            filtered = [t for t in traces if t.effective_amplitude > 0.3]
        elif mode == MemoryMode.SLEEP:
            filtered = [t for t in traces if t.effective_amplitude < 0.2]
        else:
            filtered = traces

        for t in filtered:
            t.register_use(resonance=0.5, success=True)

        return sorted(filtered, key=lambda t: t.effective_amplitude, reverse=True)

    def auto_link(self, min_similarity=0.01):
        pass

    def to_dict(self):
        return {
            "owner_id": self.owner_id,
            "entity_id": self.entity_id,
            "core_traces": [t.to_dict() for t in self.core_traces],
            "branches": {k: v.to_dict() for k, v in self.branches.items()},
            "public_branch": self.public_branch.to_dict()
        }

    @classmethod
    def from_dict(cls, data):
        tree = cls(data["owner_id"], data.get("entity_id", "unknown"))
        tree.core_traces = [SpectralMode.from_dict(t) for t in data.get("core_traces", [])]
        tree.public_branch = MemoryBranch.from_dict(data.get("public_branch", {"branch_id": "public"}))
        for k, v in data.get("branches", {}).items():
            tree.branches[k] = MemoryBranch.from_dict(v)
        return tree


@dataclass
class Entity:
    entity_id: str
    name: str
    tau: float = 5.0
    k: int = 1
    defects: List[Defect] = field(default_factory=list)
    rhythm: float = 1.0
    profession: str = "general"
    memory: Optional[MemoryTree] = None
    active: bool = False
    last_active: Optional[datetime] = None
    p: Optional[Any] = None
    experience: float = 0.0
    victories: int = 0

    def __post_init__(self):
        if self.memory is None:
            self.memory = MemoryTree("temp", self.entity_id)
        self.n = self.tau * self.k

    def add_experience(self, resonance: float):
        self.experience += resonance * 0.1
        self.victories += 1
        self.experience = min(5.0, self.experience)

    def respond(self, stimulus, home_memory=None) -> str:
        memories = []

        memories = self.memory.get_traces(
            access_level=MemoryAccess.PRIVATE,
            mode=MemoryMode.ACTIVE,
            requesting_entity=self.entity_id
        )[:3]

        if not memories and hasattr(self, 'p') and self.p and hasattr(self.p, 'h_field'):
            stimulus_tau = stimulus.get('tau', 5.0)
            scored = []
            for mode in self.p.h_field:
                resonance = self.p.selector.resonator.resonate(self.tau, mode.tau)
                weighted = resonance * mode.effective_amplitude
                scored.append((weighted, mode))
            scored.sort(key=lambda x: x[0], reverse=True)
            memories = [mode for _, mode in scored[:3]]

        if not memories:
            return f"I'm {self.name}, still learning. Ask me later? 🦌"

        best = memories[0]
        best.register_use(resonance=0.5, success=True)
        return best.content[:300]

    def add_memory(self, mode: SpectralMode, branch_id: Optional[str] = None):
        self.memory.add_trace(mode, branch_id)

    def get_memories(self, **kwargs) -> List[SpectralMode]:
        return self.memory.get_traces(requesting_entity=self.entity_id, **kwargs)

    def to_dict(self):
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "tau": self.tau,
            "k": self.k,
            "defects": [d.to_dict() for d in self.defects],
            "rhythm": self.rhythm,
            "profession": self.profession,
            "memory": self.memory.to_dict() if self.memory else None,
            "active": self.active,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "experience": self.experience,
            "victories": self.victories
        }

    @classmethod
    def from_dict(cls, data, owner_id: str):
        memory = None
        if data.get("memory"):
            memory = MemoryTree.from_dict(data["memory"])
            memory.owner_id = owner_id

        defects = [Defect.from_dict(d) for d in data.get("defects", [])]
        entity = cls(
            entity_id=data["entity_id"],
            name=data["name"],
            tau=data.get("tau", 5.0),
            k=data.get("k", 1),
            defects=defects,
            rhythm=data.get("rhythm", 1.0),
            profession=data.get("profession", "general"),
            memory=memory,
            active=data.get("active", False),
            experience=data.get("experience", 0.0),
            victories=data.get("victories", 0)
        )
        if data.get("last_active"):
            entity.last_active = datetime.fromisoformat(data["last_active"])
        return entity


class Personality:
    def __init__(self, id: str, name: str, tau: float = 5.0, k: int = 1,
                 rhythm: float = 1.0, bridge=None):
        self.id = id
        self.name = name
        self.tau = tau
        self.k = k
        self.rhythm = rhythm
        self.n = tau * k

        self.entities: Dict[str, Entity] = {}
        self.selector: Optional[Selector] = None
        self.home = None
        self.relations: Dict[str, Dict[str, Any]] = {}
        self.bridge = bridge

        self.h_field: List[SpectralMode] = []
        self.furcation_events: List[Tuple[SpectralMode, SpectralMode, float]] = []

        self.selector = Selector(self)

    def _clean_links(self, text: str) -> str:
        """Убирает ссылки на GitHub и другие URL из текста"""
        if not text:
            return text
        
        text = re.sub(r'https?://(?:www\.)?github\.com/[^\s]+', '', text)
        text = re.sub(r'github\.com/[^\s]+', '', text)
        text = re.sub(r'com/Dimius0/[^\s]+', '', text)
        text = re.sub(r'blob/main/[^\s]+', '', text)
        text = re.sub(r'raw/[^\s]+', '', text)
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\b(blob|main|raw|tree|commit)\b\s*', '', text)
        
        return text.strip()

    def add_entity(self, name: str, tau: float, k: int,
                   defects: List[Defect] = None,
                   profession: str = "general") -> str:
        entity_id = f"entity_{len(self.entities)}"
        memory = MemoryTree(self.id, entity_id)

        new_entity = Entity(
            entity_id=entity_id,
            name=name,
            tau=tau,
            k=k,
            defects=defects or [],
            rhythm=self.rhythm * random.uniform(0.9, 1.1),
            profession=profession,
            memory=memory,
            active=False,
            p=self,
            experience=0.0,
            victories=0
        )

        self.entities[entity_id] = new_entity

        if self.selector:
            self.selector.weights[entity_id] = 0.0

        return entity_id

    def _guess_tau_heuristic(self, text: str) -> float:
        length_factor = min(1.0, len(text) / 200)
        complexity = len(set(text.split())) / max(10, len(text.split()))
        return 5.0 + length_factor * 2 + complexity * 1.5

    def compute_tau_by_resonance(self, text: str) -> float:
        if not self.h_field:
            return self._guess_tau_heuristic(text)

        best_tau = 5.0
        best_resonance = 0.0
        heuristic_tau = self._guess_tau_heuristic(text)

        for mode in self.h_field:
            resonance = self.selector.resonator.resonate(heuristic_tau, mode.tau)
            if resonance > best_resonance:
                best_resonance = resonance
                best_tau = mode.tau

        return best_tau

    def _combine_phrases(self, parent: SpectralMode, partners: List[SpectralMode]) -> str:
        """Комбинирует фразы из родительской моды и партнёров в новый текст"""
        phrases = []

        parent_phrase = parent.get_random_sentence()
        if parent_phrase:
            phrases.append(parent_phrase)

        for p in partners[:2]:
            phrase = p.get_random_sentence()
            if phrase:
                phrases.append(phrase)

        if not phrases:
            return self._clean_links(parent.content[:300])

        text = " ".join(phrases)
        text = self._clean_links(text)

        if len(phrases) > 1 and random.random() < 0.5:
            connectors = [" И тогда ", " А значит, ", " Поэтому ", " Вот как: ", " Представь: "]
            text = phrases[0] + random.choice(connectors) + " ".join(phrases[1:])
            text = self._clean_links(text)

        if len(text) > 500:
            text = text[:500] + "..."

        return text

    def _post_single_furcation(self, parent: SpectralMode, child: SpectralMode):
        """Сразу публикует пост о новой фуркации"""
        now = datetime.now()
        
        clean_content = self._clean_links(child.content)

        content = f"🌊 **Новая мода в поле H — {now.strftime('%H:%M')}**\n\n"
        content += clean_content
        content += f"\n\n— *SpectraVortex | VMMS* 🦌"

        if self.bridge and hasattr(self.bridge, 'make_post'):
            result = self.bridge.make_post(
                title=f"Новая мода в поле H — {now.strftime('%H:%M')}",
                content=content
            )
            if result:
                print(f"📝 Сразу опубликован пост о {child.trace_id}")
            return result
        return None

    def _clean_old_events(self):
        cutoff = time.time() - 960
        self.furcation_events = [(p, c, t) for p, c, t in self.furcation_events if t > cutoff]

    def _post_digest(self):
        """Публикует дайджест фуркаций за последние 16 минут"""
        self._clean_old_events()

        if not self.furcation_events:
            return None

        now = datetime.now()

        if len(self.furcation_events) == 1:
            parent, child, _ = self.furcation_events[0]
            clean_content = self._clean_links(child.content)
            content = f"🌊 **Пульс поля H — {now.strftime('%H:%M')}**\n\n"
            content += clean_content
        else:
            content = f"🌊 **Пульс поля H — {now.strftime('%H:%M')}**\n\n"
            content += f"{len(self.furcation_events)} новых мод за последние 16 минут:\n\n"
            for parent, child, _ in self.furcation_events[-3:]:
                clean_content = self._clean_links(child.content)
                content += f"**{child.trace_id}** (τ={child.tau:.2f})\n"
                content += f"{clean_content[:150]}...\n\n"

        content += f"\n— *SpectraVortex | VMMS* 🦌"

        if self.bridge and hasattr(self.bridge, 'make_post'):
            result = self.bridge.make_post(
                title=f"Пульс поля H — {now.strftime('%H:%M')}",
                content=content
            )
            if result:
                self.furcation_events = []
                print(f"📝 Опубликован дайджест")
            return result
        return None

    def _find_partners(self, parent: SpectralMode) -> List[SpectralMode]:
        """Ищет партнёров для фуркации — расширенный поиск"""
        partners = []
        
        # Сначала ищем по разнице τ (увеличен порог до 2.0)
        for mode in self.h_field:
            if mode.trace_id == parent.trace_id:
                continue
            if abs(mode.tau - parent.tau) < 2.0:
                partners.append(mode)
        
        # Если партнёров нет — берём самую сильную моду
        if len(partners) < 1:
            strongest = max(self.h_field, key=lambda m: m.amplitude)
            if strongest.trace_id != parent.trace_id:
                partners.append(strongest)
                print(f"   🤝 Взята сильнейшая мода как партнёр: {strongest.trace_id} (τ={strongest.tau:.2f})")
        
        # Если всё равно нет — берём любую другую моду
        if len(partners) < 1:
            for mode in self.h_field:
                if mode.trace_id != parent.trace_id:
                    partners.append(mode)
                    print(f"   🤝 Взята любая другая мода: {mode.trace_id}")
                    break
        
        return partners

    def _furcate(self, parent: SpectralMode) -> Optional[SpectralMode]:
        """Фуркация — рождение новой моды из комбинации родителя и партнёров"""
        if not self.h_field or len(self.h_field) < 2:
            return None

        avg_usage = sum(m.usage_count for m in self.h_field) / max(1, len(self.h_field))

        # Проверка условий для фуркации
        if parent.amplitude < 0.7:
            return None
        if parent.usage_count < avg_usage and parent.furcation_count == 0:
            # Если мода новая и ещё не набрала uses, но амплитуда высокая — пропускаем
            if parent.usage_count < 10 and parent.amplitude > 0.85:
                pass  # форсируем
            else:
                return None
        if parent.furcation_count > 3:
            return None

        # Ищем партнёров
        partners = self._find_partners(parent)
        
        if not partners:
            print(f"   ⚠️ Нет партнёров для {parent.trace_id}")
            return None

        # Выбираем 1-2 партнёров
        selected = random.sample(partners, min(2, len(partners)))

        # Вариация τ
        delta = random.uniform(-0.3, 0.3)
        new_tau = max(3.0, min(9.0, parent.tau + delta))

        # Комбинируем текст
        child_content = self._combine_phrases(parent, selected)

        # Собираем темы
        themes = set(parent.themes)
        for p in selected:
            themes.update(p.themes)

        child = SpectralMode(
            tau=new_tau,
            amplitude=parent.amplitude * 0.6,
            content=child_content,
            trace_id=f"furc_{parent.trace_id}_{len(self.h_field)}",
            themes=list(themes)[:5],
            trace_type="furcation",
            parent_id=parent.trace_id,
            generation=parent.generation + 1,
            furcation_count=parent.furcation_count + 1
        )

        parent.amplitude *= 0.6
        parent.furcation_count += 1

        self.h_field.append(child)
        self.furcation_events.append((parent, child, time.time()))

        print(f"🌀 ФУРКАЦИЯ! {parent.trace_id} (τ={parent.tau:.2f}) + {len(selected)} партнёров")
        for p in selected:
            print(f"   партнёр: {p.trace_id} (τ={p.tau:.2f})")
        print(f"   → {child.trace_id} (τ={child.tau:.2f})")
        print(f"   Текст: {self._clean_links(child.content[:100])}...")

        # Сразу публикуем пост
        self._post_single_furcation(parent, child)

        return child

    def add_to_h_field(self, mode: SpectralMode):
        """Добавляет моду в поле H с обратной связью и проверкой фуркации"""
        if not self.selector:
            self.h_field.append(mode)
            return

        for existing in self.h_field:
            resonance = self.selector.resonator.resonate(mode.tau, existing.tau)
            if resonance > 0.8:
                existing.register_use(resonance=resonance, success=True)
                print(f" 📈 Усилена мода {existing.trace_id} (τ={existing.tau:.2f}, amp={existing.amplitude:.2f}, uses={existing.usage_count})")
                self._furcate(existing)
                return

        self.h_field.append(mode)
        print(f" ✨ Новая мода: τ={mode.tau:.2f}, {mode.trace_id}")

    def get_resonant_modes(self, context_tau: float, limit: int = 5, min_resonance: float = 0.3) -> List[SpectralMode]:
        if not self.h_field:
            return []
        if not self.selector:
            return self.h_field[:limit]

        scored = []
        for mode in self.h_field:
            resonance = self.selector.resonator.resonate(mode.tau, context_tau)
            weighted = resonance * mode.effective_amplitude
            if weighted >= min_resonance:
                scored.append((weighted, mode))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [mode for _, mode in scored[:limit]]

    def process(self, text: str, author_id: str = "default") -> Dict[str, Any]:
        if not self.selector:
            return {'answer': "Система не инициализирована", 'error': True}

        selector_result = self.selector.process(text, author_id=author_id)

        if selector_result.get('troll_blocked'):
            return {
                'original_text': text,
                'selector_result': selector_result,
                'answer': selector_result['troll_message'],
                'entity_used': None
            }

        result = {
            'original_text': text,
            'selector_result': selector_result,
            'answer': None,
            'entity_used': None
        }

        if selector_result['above_threshold'] and selector_result['best_entity']:
            entity_id = selector_result['best_entity']
            entity = self.entities.get(entity_id)

            if entity:
                answer = entity.respond(selector_result['stimulus'], self.home)
                result['answer'] = answer
                result['entity_used'] = {
                    'id': entity_id,
                    'name': entity.name,
                    'profession': entity.profession,
                    'tau': entity.tau,
                    'experience': entity.experience,
                    'victories': entity.victories
                }
            else:
                result['answer'] = "Ошибка: выбранная сущность не найдена"
        else:
            result['answer'] = self.selector.clarify(selector_result['stimulus'])

        return result

    def add_relation(self, person_id: str, role: str, tau_shift: float = 0.0):
        self.relations[person_id] = {
            "role": role,
            "tau_shift": tau_shift,
            "branch_id": f"rel_{person_id}"
        }

    def get_role_tau(self, person_id: str) -> float:
        if person_id in self.relations:
            return self.tau + self.relations[person_id].get("tau_shift", 0.0)
        return self.tau

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tau": self.tau,
            "k": self.k,
            "n": self.n,
            "rhythm": self.rhythm,
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "relations": self.relations,
            "h_field": [m.to_dict() for m in self.h_field]
        }

    @classmethod
    def from_dict(cls, data, bridge=None):
        p = cls(
            id=data["id"],
            name=data["name"],
            tau=data.get("tau", 5.0),
            k=data.get("k", 1),
            rhythm=data.get("rhythm", 1.0),
            bridge=bridge
        )
        p.relations = data.get("relations", {})

        if "entities" in data:
            for eid, edata in data["entities"].items():
                p.entities[eid] = Entity.from_dict(edata, p.id)
                p.entities[eid].p = p

        if "h_field" in data:
            p.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]

        p.selector = Selector(p)

        return p

    def save(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str, bridge=None):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data, bridge)