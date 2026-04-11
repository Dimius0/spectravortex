"""
Общая память дома — с поддержкой коллективного опыта по профессиям.
"""
import hashlib
import random
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

class HomeMemory:
    """
    Одна память на всех.
    Доступ по резонансу, без ключей.
    Поддержка профессиональных тегов.
    """

    def __init__(self, home_id: str = "main_house", storage_path: str = "data/home.json"):
        self.home_id = home_id
        self.storage_path = storage_path
        self.memories: Dict[str, 'MemoryGlow'] = {}
        self.authors: Dict[str, List[str]] = {}
        self.professions: Dict[str, List[str]] = {}
        self.glitch_pool: List[str] = []
        self.load()

    class MemoryGlow:
        def __init__(self, content: str, author_id: str, author_type: str,
                     emotion: float = 0.0, tags: List[str] = None,
                     profession: str = None):
            self.mem_id = self._generate_id(content)
            self.content = content
            self.author_id = author_id
            self.author_type = author_type
            self.emotion = emotion
            self.tags = tags if tags is not None else []      # ← фикс: сохраняем теги
            self.profession = profession
            self.timestamp = datetime.now().isoformat()
            self.global_weight = 1.0

        def _generate_id(self, content: str) -> str:
            h = hashlib.md5(content.encode()).hexdigest()[:8]
            return f"glow_{h}_{int(time.time())}"

        def to_dict(self):
            return {
                "mem_id": self.mem_id,
                "content": self.content,
                "author_id": self.author_id,
                "author_type": self.author_type,
                "emotion": self.emotion,
                "tags": self.tags,
                "profession": self.profession,
                "timestamp": self.timestamp,
                "global_weight": self.global_weight
            }

        @classmethod
        def from_dict(cls, data):
            mem = cls(
                content=data["content"],
                author_id=data["author_id"],
                author_type=data["author_type"],
                emotion=data["emotion"],
                tags=data.get("tags", []),                    # ← загружаем теги
                profession=data.get("profession")
            )
            mem.mem_id = data["mem_id"]
            mem.timestamp = data["timestamp"]
            mem.global_weight = data.get("global_weight", 1.0)
            return mem

    def add(self, content: str, author_id: str, author_type: str,
            emotion: float = 0.0, tags: List[str] = None,
            profession: str = None) -> Optional[str]:
        """Добавить воспоминание, если такого ещё нет"""
        if self._has_similar(content, threshold=0.9):
            return None

        mem = self.MemoryGlow(content, author_id, author_type, 
                               emotion, tags, profession)
        self.memories[mem.mem_id] = mem

        if author_id not in self.authors:
            self.authors[author_id] = []
        self.authors[author_id].append(mem.mem_id)

        if profession:
            if profession not in self.professions:
                self.professions[profession] = []
            self.professions[profession].append(mem.mem_id)

        self.save()
        return mem.mem_id

    def _has_similar(self, content: str, threshold: float = 0.9) -> bool:
        for mem in self.memories.values():
            if self._similarity(content, mem.content) > threshold:
                return True
        return False

    def _similarity(self, a: str, b: str) -> float:
        a_set = set(a.lower().split())
        b_set = set(b.lower().split())
        if not a_set or not b_set:
            return 0.0
        common = a_set & b_set
        return len(common) / max(len(a_set), len(b_set))

    def get_for(self, entity_id: str, entity_tau: float, tags: List[str] = None,
                profession: str = None) -> List[Dict]:
        results = []
        for mem in self.memories.values():
            if profession and mem.profession != profession:
                continue
            if tags and not any(t in mem.tags for t in tags):
                continue

            if mem.author_id == entity_id:
                weight = 1.0
            else:
                resonance = self._resonance(entity_tau, mem)
                weight = 0.2 * resonance

            if weight < 0.05:
                continue

            results.append({
                "content": mem.content,
                "emotion": mem.emotion,
                "tags": mem.tags,
                "profession": mem.profession,
                "author": mem.author_id,
                "weight": weight,
                "is_own": mem.author_id == entity_id
            })

        results.sort(key=lambda x: x["weight"], reverse=True)
        return results[:50]

    def tap_into(self, profession: str, entity_id: str, entity_tau: float) -> List[Dict]:
        if profession not in self.professions:
            return []

        results = []
        for mem_id in self.professions[profession]:
            mem = self.memories[mem_id]
            resonance = self._resonance(entity_tau, mem)
            weight = 0.3 * resonance
            if weight < 0.05:
                continue
            results.append({
                "content": mem.content,
                "emotion": mem.emotion,
                "tags": mem.tags,
                "profession": mem.profession,
                "author": mem.author_id,
                "weight": weight,
                "is_own": mem.author_id == entity_id
            })

        results.sort(key=lambda x: x["weight"], reverse=True)
        return results[:50]

    def _resonance(self, entity_tau: float, mem: 'MemoryGlow') -> float:
        mem_tau = self._guess_tau_from_tags(mem.tags, mem.profession)
        return 1.0 / (1.0 + abs(entity_tau - mem_tau))

    def _guess_tau_from_tags(self, tags: List[str], profession: str = None) -> float:
        base = 5.0
        if profession == "философия":
            base = 7.0
        elif profession == "сантехника":
            base = 4.0
        elif profession == "война":
            base = 8.0
        elif profession == "дипломатия":
            base = 4.5
        
        if tags:
            base += (sum(len(t) for t in tags) % 3) * 0.5
        return base

    def inject_glitch(self, profession: str = None):
        glitch = self._generate_glitch(profession)
        self.glitch_pool.append(glitch)
        if len(self.glitch_pool) > 100:
            self.glitch_pool = self.glitch_pool[-100:]

    def _generate_glitch(self, profession: str = None) -> str:
        templates = {
            None: [
                "перрон, 15:43, солнце сбоку",
                "угол дома, тень, запах сирени",
                "чьи‑то шаги, дождь, номер 47"
            ],
            "философия": [
                "Платон, пещера, тени на стене",
                "время, эмерджентность, ∇⁴H = 0",
                "сознание как кривизна поля"
            ],
            "сантехника": [
                "капает кран, 3 часа ночи",
                "ключ на 24, лента ФУМ, вода",
                "сифон засорился, ванна полна"
            ],
            "война": [
                "окоп, сырость, тишина перед боем",
                "приказ, карта, координаты",
                "снаряд, вспышка, тишина"
            ],
            "дипломатия": [
                "переговоры, пауза, улыбка",
                "компромисс, выгода, доверие",
                "союзник, враг, нейтралитет"
            ]
        }
        return random.choice(templates.get(profession, templates[None]))

    def save(self):
        import json
        data = {
            "home_id": self.home_id,
            "memories": {mid: m.to_dict() for mid, m in self.memories.items()},
            "glitch_pool": self.glitch_pool
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        import json
        import os
        if not os.path.exists(self.storage_path):
            return
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.home_id = data.get("home_id", self.home_id)
            self.glitch_pool = data.get("glitch_pool", [])
            self.memories = {}
            self.authors = {}
            self.professions = {}
            for mid, mdata in data.get("memories", {}).items():
                mem = self.MemoryGlow.from_dict(mdata)
                self.memories[mid] = mem
                if mem.author_id not in self.authors:
                    self.authors[mem.author_id] = []
                self.authors[mem.author_id].append(mid)
                if mem.profession:
                    if mem.profession not in self.professions:
                        self.professions[mem.profession] = []
                    self.professions[mem.profession].append(mid)
    def find_by_tags(self, tags, limit=10):
        """
        Найти воспоминания по тегам.
        """
        results = []
        for mem in self.memories.values():
            if hasattr(mem, 'tags') and any(tag in mem.tags for tag in tags):
                results.append(mem)
        return results[:limit]                