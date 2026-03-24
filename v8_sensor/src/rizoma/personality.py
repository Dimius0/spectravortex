"""
Personality — ядро личности, поле H, фуркации
Версия 8.0 — с поддержкой сенсорного ввода
"""

import json
import hashlib
import random
import time
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class SpectralMode:
    """Спектральная мода поля H"""
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
    creator: str = "unknown"
    embedding: Optional[List[float]] = None  # для семантического поиска
    
    def __post_init__(self):
        if not self.trace_id:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.trace_id = f"mode_{content_hash}"
    
    @property
    def effective_amplitude(self):
        frequency_factor = 1.0 + 0.05 * self.usage_count
        return min(1.0, self.amplitude * frequency_factor)
    
    def register_use(self, resonance: float = 0.5, success: bool = True):
        self.usage_count += 1
        self.last_used = datetime.now()
        self._update_amplitude(resonance, success)
    
    def _update_amplitude(self, resonance: float, success: bool):
        if success:
            delta = resonance * 0.2 * (1 - self.amplitude)
            self.amplitude = min(1.0, self.amplitude + delta)
        else:
            self.amplitude *= 0.95
    
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
            "creator": self.creator
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
            furcation_count=data.get("furcation_count", 0),
            creator=data.get("creator", "unknown")
        )
        if data.get("last_used"):
            mode.last_used = datetime.fromisoformat(data["last_used"])
        return mode


class Personality:
    def __init__(self, id: str, name: str, tau: float = 5.0, k: int = 1):
        self.id = id
        self.name = name
        self.tau = tau
        self.k = k
        self.h_field: List[SpectralMode] = []
        
        self._furcation_threshold = 0.7
        self._adaptation_counter = 0
        self._tau_history: List[float] = []
        
        self.evolution_vector = {
            "target_tau": None,
            "target_themes": [],
            "intensity": 0.5
        }
        
        # Для сенсорного ввода
        self.sensor_adapter = None
    
    def set_sensor_adapter(self, adapter):
        """Устанавливает адаптер сенсоров"""
        self.sensor_adapter = adapter
    
    def _auto_adjust_thresholds(self):
        if len(self.h_field) < 2:
            return
        
        avg_amplitude = sum(m.amplitude for m in self.h_field) / len(self.h_field)
        
        stability_bonus = 0.5
        if len(self.h_field) > 5:
            recent_amps = [m.amplitude for m in self.h_field[-5:]]
            volatility = np.std(recent_amps) if len(recent_amps) > 1 else 0.2
            stability_bonus = max(0.1, 1.0 - volatility * 2)
        
        new_threshold = max(0.2, avg_amplitude * 0.5 * stability_bonus)
        self._furcation_threshold = self._furcation_threshold * 0.6 + new_threshold * 0.4
        
        self._adaptation_counter += 1
        if self._adaptation_counter % 5 == 0:
            print(f"   🔧 Адаптация: порог={self._furcation_threshold:.2f}")
    
    def _calculate_volatility(self) -> float:
        if len(self.h_field) < 3:
            return 0.5
        recent_taus = [m.tau for m in self.h_field[-5:]]
        if len(recent_taus) < 2:
            return 0.5
        return np.std(recent_taus)
    
    def _resonance(self, tau1: float, tau2: float) -> float:
        return 1.0 / (1.0 + abs(tau1 - tau2))
    
    def _find_partners(self, parent: SpectralMode) -> List[SpectralMode]:
        if len(self.h_field) < 2:
            return []
        
        partners = []
        for mode in self.h_field:
            if mode.trace_id == parent.trace_id:
                continue
            
            gen_distance = abs(mode.generation - parent.generation)
            resonance = self._resonance(parent.tau, mode.tau)
            if gen_distance > 2:
                resonance *= 1.5
            
            if self.evolution_vector["target_themes"] and mode.themes:
                theme_match = len(set(mode.themes) & set(self.evolution_vector["target_themes"]))
                resonance *= (1 + theme_match * 0.5)
            
            if resonance > 0.2:
                partners.append((resonance, mode))
        
        partners.sort(key=lambda x: x[0], reverse=True)
        return [mode for _, mode in partners[:3]]
    
    def _combine_phrases(self, parent: SpectralMode, partners: List[SpectralMode]) -> str:
        texts = [parent.content]
        for p in partners:
            texts.append(p.content)
        
        combined = " ".join(texts[:3])
        
        sentences = combined.split('. ')
        unique = []
        seen = set()
        for s in sentences:
            key = s[:40].lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        
        combined = '. '.join(unique[:3])
        
        if "poetry" in self.evolution_vector["target_themes"]:
            poetry_ratio = sum(1 for m in self.h_field if "poetry" in m.themes) / max(1, len(self.h_field))
            prob = max(0.2, 0.6 - poetry_ratio)
            
            if random.random() < prob:
                poetic_connectors = [
                    "Как ритм, пронизывающий тишину,",
                    "Словно метафора, рождающая смысл,",
                    "Подобно стиху, что ищет свою рифму,",
                    "Как отражение в зеркале воды,",
                    "Точно луч света, преломлённый в капле,"
                ]
                connector = random.choice(poetic_connectors)
                combined = connector + " " + combined.lower()
                combined = combined[0].upper() + combined[1:]
        
        if len(combined) > 400:
            combined = combined[:400] + "..."
        
        return combined
    
    def _combine_themes(self, parent: SpectralMode, partners: List[SpectralMode]) -> List[str]:
        themes = set(parent.themes)
        for p in partners:
            themes.update(p.themes)
        
        if self.evolution_vector["target_themes"]:
            gen_factor = min(0.6, parent.generation * 0.12)
            vector_themes_count = sum(
                1 for m in self.h_field 
                if any(t in m.themes for t in self.evolution_vector["target_themes"])
            )
            adoption_factor = min(0.7, vector_themes_count / max(1, len(self.h_field)))
            
            prob = 0.25 + gen_factor + adoption_factor * 0.3
            prob = min(0.75, prob)
            
            if random.random() < prob:
                new_theme = random.choice(self.evolution_vector["target_themes"])
                if new_theme not in themes:
                    themes.add(new_theme)
                    print(f"      ✨ Добавлена тема: {new_theme}")
        
        return list(themes)[:6]
    
    def _apply_vector_to_tau(self, parent: SpectralMode) -> float:
        if self.evolution_vector["target_tau"] is None:
            return parent.tau + random.uniform(-0.3, 0.3)
        
        target = self.evolution_vector["target_tau"]
        gap = abs(parent.tau - target)
        intensity_by_gap = min(0.85, gap / 3.5)
        volatility = self._calculate_volatility()
        stability_factor = max(0.3, 1.0 - volatility)
        maturity = min(0.7, parent.generation * 0.1)
        
        intensity = intensity_by_gap * stability_factor + maturity
        intensity = max(0.25, min(0.85, intensity))
        
        variation = random.uniform(-0.2, 0.2)
        directed = (target - parent.tau) * intensity
        new_tau = parent.tau + variation + directed
        return max(3.0, min(9.0, new_tau))
    
    def _strengthen_old_modes(self):
        for mode in self.h_field:
            if mode.generation > 0 and mode.usage_count > 3:
                bonus = 0.04 * min(3, mode.usage_count // 3)
                if bonus > 0:
                    mode.amplitude = min(1.0, mode.amplitude + bonus)
    
    def _apoptosis(self):
        new_h_field = []
        for mode in self.h_field:
            dead = False
            if mode.amplitude < 0.05 and mode.usage_count == 0:
                dead = True
            if mode.last_used and (time.time() - mode.last_used.timestamp()) > 7200:
                dead = True
            if mode.furcation_count > 8 and mode.amplitude < 0.12:
                dead = True
            
            if not dead:
                new_h_field.append(mode)
            else:
                print(f"💀 Апоптоз: {mode.trace_id}")
        
        self.h_field = new_h_field
    
    def _furcate(self, parent: SpectralMode) -> Optional[SpectralMode]:
        if len(self.h_field) < 2:
            return None
        
        self._auto_adjust_thresholds()
        
        if parent.amplitude < self._furcation_threshold:
            return None
        
        partners = self._find_partners(parent)
        if not partners:
            return None
        
        selected = random.sample(partners, min(3, len(partners)))
        new_tau = self._apply_vector_to_tau(parent)
        content = self._combine_phrases(parent, selected)
        themes = self._combine_themes(parent, selected)
        
        child = SpectralMode(
            tau=new_tau,
            amplitude=parent.amplitude * 0.75,
            content=content,
            trace_id=f"furc_{parent.trace_id}_{len(self.h_field)}",
            themes=themes,
            trace_type="furcation",
            parent_id=parent.trace_id,
            generation=parent.generation + 1,
            creator=self.id
        )
        
        parent.amplitude *= 0.75
        parent.furcation_count += 1
        parent.register_use(resonance=0.8, success=True)
        
        print(f"\n🌀 ФУРКАЦИЯ! {parent.trace_id} → {child.trace_id} (τ={child.tau:.2f})")
        return child
    
    def add_to_h_field(self, mode: SpectralMode):
        for existing in self.h_field:
            resonance = self._resonance(mode.tau, existing.tau)
            if resonance > 0.8:
                existing.register_use(resonance=resonance, success=True)
                print(f" 📈 Усилена {existing.trace_id}")
                return
        
        self.h_field.append(mode)
        print(f" ✨ Новая мода: τ={mode.tau:.2f}, {mode.trace_id}")
    
    def set_evolution_vector(self, target_tau: float = None, target_themes: List[str] = None):
        self.evolution_vector["target_tau"] = target_tau
        self.evolution_vector["target_themes"] = target_themes or []
        print(f"\n🧭 ВЕКТОР: τ={target_tau}, темы={target_themes}")
    
    def run_evolution_cycle(self, steps: int = 10):
        print(f"\n{'='*50}")
        print(f"🌀 ЭВОЛЮЦИЯ ({steps} шагов)")
        print(f"{'='*50}")
        
        for i in range(steps):
            print(f"\n--- ШАГ {i+1} ---")
            self._auto_adjust_thresholds()
            
            if not self.h_field:
                break
            
            parent = max(self.h_field, key=lambda m: m.amplitude)
            child = self._furcate(parent)
            
            if child:
                self.h_field.append(child)
            else:
                for mode in self.h_field:
                    if mode.trace_id != parent.trace_id:
                        child = self._furcate(mode)
                        if child:
                            self.h_field.append(child)
                            break
                else:
                    print("   ⚠️ Фуркация не удалась")
        
        self._strengthen_old_modes()
        self._apoptosis()
        
        print(f"\n📊 ИТОГ: {len(self.h_field)} мод")
    
    def save(self, filepath: str):
        data = {
            "id": self.id,
            "name": self.name,
            "h_field": [m.to_dict() for m in self.h_field],
            "evolution_vector": self.evolution_vector,
            "_furcation_threshold": self._furcation_threshold
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено: {filepath}")
    
    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        p = cls(data["id"], data["name"])
        p.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]
        p.evolution_vector = data.get("evolution_vector", {"target_tau": None, "target_themes": []})
        p._furcation_threshold = data.get("_furcation_threshold", 0.7)
        return p