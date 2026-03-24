"""
Personality — ядро личности, поле H, фуркации
Версия 7.6 — адаптивная динамика (природа не требует вмешательства)
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
    
    def __post_init__(self):
        if not self.trace_id:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.trace_id = f"mode_{content_hash}"
    
    @property
    def effective_amplitude(self):
        frequency_factor = 1.0 + 0.05 * self.usage_count
        return min(1.0, self.amplitude * frequency_factor)
    
    def register_use(self, resonance: float = 0.5, success: bool = True):
        """Регистрирует использование моды — усиливает при успехе"""
        self.usage_count += 1
        self.last_used = datetime.now()
        self._update_amplitude(resonance, success)
    
    def _update_amplitude(self, resonance: float, success: bool):
        """Обновляет амплитуду через обратную связь"""
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
        
        # Динамический порог фуркации (будет адаптироваться)
        self._furcation_threshold = 0.7
        self._adaptation_counter = 0
        
        # Вектор эволюции
        self.evolution_vector = {
            "target_tau": None,
            "target_themes": [],
            "intensity": 0.5  # базовое значение, будет переопределяться адаптивно
        }
        
        # Для расчёта волатильности
        self._tau_history: List[float] = []
    
    def _auto_adjust_thresholds(self):
        """Автоматическая настройка порогов через обратную связь с учётом стабильности"""
        if len(self.h_field) < 2:
            return
        
        avg_amplitude = sum(m.amplitude for m in self.h_field) / len(self.h_field)
        
        # Вычисляем стабильность поля (чем стабильнее, тем ниже порог)
        stability_bonus = 0.5
        if len(self.h_field) > 5:
            recent_amps = [m.amplitude for m in self.h_field[-5:]]
            volatility = np.std(recent_amps) if len(recent_amps) > 1 else 0.2
            stability_bonus = max(0.1, 1.0 - volatility * 2)
        
        # Адаптивный порог
        new_threshold = max(0.2, avg_amplitude * 0.5 * stability_bonus)
        self._furcation_threshold = self._furcation_threshold * 0.6 + new_threshold * 0.4
        
        self._adaptation_counter += 1
        if self._adaptation_counter % 5 == 0:
            print(f"   🔧 Адаптация: порог={self._furcation_threshold:.2f}, "
                  f"ср.амплитуда={avg_amplitude:.2f}, стабильность={stability_bonus:.2f}")
    
    def _calculate_volatility(self) -> float:
        """Вычисляет волатильность поля H по τ"""
        if len(self.h_field) < 3:
            return 0.5
        
        recent_taus = [m.tau for m in self.h_field[-5:]]
        if len(recent_taus) < 2:
            return 0.5
        
        return np.std(recent_taus)
    
    def _create_mode(self, tau: float, content: str, themes: List[str] = None,
                     trace_id: str = "", creator: str = "") -> SpectralMode:
        """Создаёт новую моду"""
        return SpectralMode(
            tau=tau,
            amplitude=0.5,
            content=content,
            trace_id=trace_id,
            themes=themes or [],
            creator=creator or self.id
        )
    
    def _resonance(self, tau1: float, tau2: float) -> float:
        """Спектральный резонанс"""
        return 1.0 / (1.0 + abs(tau1 - tau2))
    
    def _find_partners(self, parent: SpectralMode) -> List[SpectralMode]:
        """Ищет партнёров для фуркации с учётом генетической дистанции и вектора"""
        if len(self.h_field) < 2:
            return []
        
        partners = []
        for mode in self.h_field:
            if mode.trace_id == parent.trace_id:
                continue
            
            # Генетическая дистанция — защита от инбридинга
            gen_distance = abs(mode.generation - parent.generation)
            
            # Бонус за дальнее родство
            resonance = self._resonance(parent.tau, mode.tau)
            if gen_distance > 2:
                resonance *= 1.5
            
            # Учитываем вектор эволюции для выбора партнёров
            if self.evolution_vector["target_themes"] and mode.themes:
                theme_match = len(set(mode.themes) & set(self.evolution_vector["target_themes"]))
                resonance *= (1 + theme_match * 0.5)
            
            if resonance > 0.2:
                partners.append((resonance, mode))
        
        partners.sort(key=lambda x: x[0], reverse=True)
        return [mode for _, mode in partners[:3]]
    
    def _combine_phrases(self, parent: SpectralMode, partners: List[SpectralMode]) -> str:
        """Комбинирует текст из родителя и партнёров с добавлением поэтичности"""
        texts = [parent.content]
        for p in partners:
            texts.append(p.content)
        
        combined = " ".join(texts[:3])
        
        # Убираем повторы
        sentences = combined.split('. ')
        unique = []
        seen = set()
        for s in sentences:
            key = s[:40].lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        
        combined = '. '.join(unique[:3])
        
        # Адаптивное добавление поэтического оттенка
        if "poetry" in self.evolution_vector["target_themes"]:
            # Вероятность зависит от того, насколько поле уже поэтично
            poetry_ratio = sum(1 for m in self.h_field if "poetry" in m.themes) / max(1, len(self.h_field))
            prob = max(0.2, 0.6 - poetry_ratio)  # чем меньше поэзии, тем выше шанс
            
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
        
        # Ограничиваем длину
        if len(combined) > 400:
            combined = combined[:400] + "..."
        
        return combined
    
    def _combine_themes(self, parent: SpectralMode, partners: List[SpectralMode]) -> List[str]:
        """Комбинирует темы с адаптивным добавлением из вектора"""
        themes = set(parent.themes)
        for p in partners:
            themes.update(p.themes)
        
        # Адаптивное добавление тем вектора
        if self.evolution_vector["target_themes"]:
            # Фактор поколения
            gen_factor = min(0.6, parent.generation * 0.12)
            
            # Фактор принятия — сколько мод уже имеют темы вектора
            vector_themes_count = sum(
                1 for m in self.h_field 
                if any(t in m.themes for t in self.evolution_vector["target_themes"])
            )
            adoption_factor = min(0.7, vector_themes_count / max(1, len(self.h_field)))
            
            # Адаптивная вероятность
            prob = 0.25 + gen_factor + adoption_factor * 0.3
            prob = min(0.75, prob)
            
            if random.random() < prob:
                new_theme = random.choice(self.evolution_vector["target_themes"])
                if new_theme not in themes:
                    themes.add(new_theme)
                    print(f"      ✨ Добавлена тема из вектора: {new_theme} (вероятность={prob:.2f})")
        
        return list(themes)[:6]
    
    def _apply_vector_to_tau(self, parent: SpectralMode) -> float:
        """Применяет вектор эволюции с адаптивной интенсивностью"""
        if self.evolution_vector["target_tau"] is None:
            return parent.tau + random.uniform(-0.3, 0.3)
        
        target = self.evolution_vector["target_tau"]
        
        # 1. Интенсивность на основе разрыва (чем больше разрыв, тем выше)
        gap = abs(parent.tau - target)
        intensity_by_gap = min(0.85, gap / 3.5)
        
        # 2. Стабильность поля — если τ скачут, снижаем
        volatility = self._calculate_volatility()
        stability_factor = max(0.3, 1.0 - volatility)
        
        # 3. Зрелость поколения — чем старше, тем быстрее
        maturity = min(0.7, parent.generation * 0.1)
        
        # Итоговая интенсивность
        intensity = intensity_by_gap * stability_factor + maturity
        intensity = max(0.25, min(0.85, intensity))
        
        variation = random.uniform(-0.2, 0.2)
        directed = (target - parent.tau) * intensity
        
        new_tau = parent.tau + variation + directed
        new_tau = max(3.0, min(9.0, new_tau))
        
        # Логируем редко
        if random.random() < 0.1:
            print(f"      📊 Адаптивная интенсивность: {intensity:.2f} "
                  f"(разрыв={gap:.2f}, волатильность={volatility:.2f})")
        
        return new_tau
    
    def _strengthen_old_modes(self):
        """Усиливает старые моды, которые активно используются"""
        for mode in self.h_field:
            if mode.generation > 0 and mode.usage_count > 3:
                bonus = 0.04 * min(3, mode.usage_count // 3)
                if bonus > 0:
                    old_amp = mode.amplitude
                    mode.amplitude = min(1.0, mode.amplitude + bonus)
                    if old_amp != mode.amplitude and random.random() < 0.2:
                        print(f"   🌱 Усилена зрелая мода: {mode.trace_id} ({old_amp:.2f}→{mode.amplitude:.2f})")
    
    def _apoptosis(self):
        """Удаляет нежизнеспособные моды"""
        new_h_field = []
        for mode in self.h_field:
            dead = False
            
            # Амплитуда ниже порога и нет использований
            if mode.amplitude < 0.05 and mode.usage_count == 0:
                dead = True
            
            # Не использовалась больше 2 часов
            if mode.last_used and (time.time() - mode.last_used.timestamp()) > 7200:
                dead = True
            
            # Слишком много фуркаций без роста
            if mode.furcation_count > 8 and mode.amplitude < 0.12:
                dead = True
            
            if not dead:
                new_h_field.append(mode)
            else:
                print(f"💀 Апоптоз: {mode.trace_id} (τ={mode.tau:.2f}, amp={mode.amplitude:.2f})")
        
        self.h_field = new_h_field
    
    def _furcate(self, parent: SpectralMode) -> Optional[SpectralMode]:
        """Фуркация — рождение новой моды"""
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
        
        print(f"\n🌀 ФУРКАЦИЯ! {parent.trace_id} (τ={parent.tau:.2f}, amp={parent.amplitude:.2f})")
        for p in selected:
            print(f"   + {p.trace_id} (τ={p.tau:.2f})")
        print(f"   → {child.trace_id} (τ={child.tau:.2f}, amp={child.amplitude:.2f})")
        print(f"   📝 {content[:100]}...")
        print(f"   🏷️ Темы: {themes}")
        
        return child
    
    def add_to_h_field(self, mode: SpectralMode):
        """Добавляет моду в поле H"""
        for existing in self.h_field:
            resonance = self._resonance(mode.tau, existing.tau)
            if resonance > 0.8:
                existing.register_use(resonance=resonance, success=True)
                print(f" 📈 Усилена {existing.trace_id} (τ={existing.tau:.2f}, amp={existing.amplitude:.2f})")
                return
        
        self.h_field.append(mode)
        print(f" ✨ Новая мода: τ={mode.tau:.2f}, {mode.trace_id}")
    
    def set_evolution_vector(self, target_tau: float = None, 
                             target_themes: List[str] = None,
                             intensity: float = None):
        """Устанавливает вектор эволюции (интенсивность вычисляется адаптивно)"""
        self.evolution_vector["target_tau"] = target_tau
        self.evolution_vector["target_themes"] = target_themes or []
        # intensity не используется — оно адаптивное
        print(f"\n🧭 ВЕКТОР ЭВОЛЮЦИИ:")
        print(f"   Целевая τ: {target_tau}")
        print(f"   Целевые темы: {target_themes}")
        print(f"   (интенсивность адаптивная, вычисляется автоматически)")
    
    def run_evolution_cycle(self, steps: int = 10):
        """Запускает цикл эволюции"""
        print(f"\n{'='*50}")
        print(f"🌀 ЗАПУСК ЭВОЛЮЦИОННОГО ЦИКЛА ({steps} шагов)")
        print(f"{'='*50}")
        
        for i in range(steps):
            print(f"\n--- ШАГ {i+1} ---")
            
            self._auto_adjust_thresholds()
            
            if not self.h_field:
                print("   Поле H пусто")
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
        
        print(f"\n{'='*50}")
        print(f"📊 ИТОГ ЦИКЛА")
        print(f"{'='*50}")
        print(f" Мод в поле H: {len(self.h_field)}")
        for mode in self.h_field:
            print(f"   {mode.trace_id}: τ={mode.tau:.2f}, amp={mode.amplitude:.2f}, gen={mode.generation}, uses={mode.usage_count}")
            if mode.themes:
                print(f"      темы: {mode.themes[:4]}")
    
    def save(self, filepath: str):
        """Сохраняет поле H в JSON"""
        data = {
            "id": self.id,
            "name": self.name,
            "tau": self.tau,
            "k": self.k,
            "h_field": [m.to_dict() for m in self.h_field],
            "evolution_vector": self.evolution_vector,
            "_furcation_threshold": self._furcation_threshold
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Поле H сохранено в {filepath}")
        print(f"   Размер файла: ~{len(json.dumps(data)) // 1024} КБ")
    
    @classmethod
    def load(cls, filepath: str):
        """Загружает поле H из JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        p = cls(data["id"], data["name"], data.get("tau", 5.0), data.get("k", 1))
        p.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]
        p.evolution_vector = data.get("evolution_vector", {"target_tau": None, "target_themes": [], "intensity": 0.5})
        p._furcation_threshold = data.get("_furcation_threshold", 0.7)
        
        print(f"\n📂 Поле H загружено из {filepath}")
        print(f"   Мод: {len(p.h_field)}")
        print(f"   Порог фуркации: {p._furcation_threshold:.2f}")
        return p