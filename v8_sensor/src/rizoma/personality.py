"""
Personality — ядро личности, поле H
Версия 16.1 — улучшенный поиск мод + фильтр ответов
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
from .resonance import Fractal3DCoherentSpectralResonance
from .quantum_analogy import QuantumState
from .topology import TopologicalNode, KnotType
from .endogenous import EndogenousCycle, EndogenousConfig


# ========== ПРИРОДНЫЕ ШТАМПЫ ==========
class NaturalStamps:
    """
    Штампы — резонанс с вихрями-паттернами.
    Как человек: слышит знакомый "аккорд" вопроса → отвечает штампом.
    """

    SOCIAL_PATTERNS = {
        "как_дела": {
            "variants": ["как дела", "как твои дела", "как жизнь", "как поживаешь"],
            "responses": ["нормально", "хорошо", "так себе", "неплохо"],
            "energy": 0.02
        },
        "как_жизнь": {
            "variants": ["как жизнь", "как живёшь", "как оно"],
            "responses": ["понемногу", "течёт", "нормально", "как обычно"],
            "energy": 0.02
        },
        "что_нового": {
            "variants": ["что нового", "что новенького", "какие новости"],
            "responses": ["ничего особенного", "всё как всегда", "да так", "не особо"],
            "energy": 0.02
        },
        "как_настроение": {
            "variants": ["как настроение", "какое настроение", "ты как"],
            "responses": ["нормальное", "рабочее", "спокойное", "хорошее"],
            "energy": 0.02
        },
        "что_делаешь": {
            "variants": ["что делаешь", "чем занимаешься", "что ты"],
            "responses": ["думаю", "отвечаю", "разбираюсь", "тут я"],
            "energy": 0.02
        },
        "привет": {
            "variants": ["привет", "здравствуй", "добрый день", "здрасте", "хай"],
            "responses": ["привет", "здравствуй", "добрый день", "и тебе привет"],
            "energy": 0.01
        },
        "пока": {
            "variants": ["пока", "до свидания", "до встречи", "удачи", "всего хорошего"],
            "responses": ["пока", "до встречи", "удачи", "бывай"],
            "energy": 0.01
        },
        "спасибо": {
            "variants": ["спасибо", "благодарю", "мерси"],
            "responses": ["пожалуйста", "обращайся", "всегда рад помочь", "не за что"],
            "energy": 0.01
        },
        "извини": {
            "variants": ["извини", "прости", "сорри"],
            "responses": ["ничего", "бывает", "не страшно", "всё нормально"],
            "energy": 0.01
        }
    }

    STAMP_LEVELS = {
        "short": {"threshold": 0.85, "energy": 0.01, "max_len": 20},
        "medium": {"threshold": 0.75, "energy": 0.05, "max_len": 50},
        "long": {"threshold": 0.6, "energy": 0.1, "max_len": 150}
    }

    @classmethod
    def get_stamp_by_resonance(cls, field, question: str, resonance: float) -> Tuple[Optional[str], Optional[str], float]:
        question_lower = question.lower()

        for pattern_name, data in cls.SOCIAL_PATTERNS.items():
            for variant in data["variants"]:
                if variant in question_lower:
                    energy = data["energy"]
                    if field._spend_energy(energy):
                        return random.choice(data["responses"]), "social_stamp_direct", energy

        for pattern_name, data in cls.SOCIAL_PATTERNS.items():
            vortex = field.get_vortex(pattern_name.replace("_", " "))
            if vortex:
                pattern_resonance = field.resonance_between_text_and_vortex(question, vortex)
                if pattern_resonance > 0.5:
                    energy = data["energy"]
                    if field._spend_energy(energy):
                        return random.choice(data["responses"]), "social_stamp_resonant", energy

        return None, None, None

    @classmethod
    def get_stamp_by_level(cls, resonance: float) -> Tuple[Optional[str], Optional[str], float]:
        if resonance >= cls.STAMP_LEVELS["short"]["threshold"]:
            return None, "short", cls.STAMP_LEVELS["short"]["energy"]
        elif resonance >= cls.STAMP_LEVELS["medium"]["threshold"]:
            return None, "medium", cls.STAMP_LEVELS["medium"]["energy"]
        elif resonance >= cls.STAMP_LEVELS["long"]["threshold"]:
            return None, "long", cls.STAMP_LEVELS["long"]["energy"]
        return None, None, None

    @classmethod
    def ensure_patterns_in_field(cls, field):
        for pattern_name, data in cls.SOCIAL_PATTERNS.items():
            word = pattern_name.replace("_", " ")
            if word not in field.vortices:
                combined_spectrum = {}
                for variant in data["variants"]:
                    if variant in field.vortices:
                        for tau, comp in field.vortices[variant].spectrum.items():
                            if tau not in combined_spectrum:
                                combined_spectrum[tau] = SpectralComponent(0.0, 0.0)
                            combined_spectrum[tau].amplitude += comp.amplitude
                            combined_spectrum[tau].phase = (combined_spectrum[tau].phase + comp.phase) % (2 * math.pi)
                    else:
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
    created: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.trace_id:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.trace_id = f"mode_{content_hash}"
        self._cached_spectrum = None

    def register_use(self):
        self.usage_count += 1
        self.last_used = datetime.now()
        self.amplitude = min(1.0, self.amplitude + 0.05)

    def to_dict(self):
        return {
            "tau": self.tau, "delta": self.delta, "theta": self.theta,
            "amplitude": self.amplitude, "content": self.content,
            "trace_id": self.trace_id, "themes": self.themes,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "trace_type": self.trace_type, "parent_id": self.parent_id,
            "generation": self.generation, "furcation_count": self.furcation_count,
            "creator": self.creator, "scale": self.scale,
            "created": self.created.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        mode = cls(
            tau=data["tau"], delta=data.get("delta", 0.0), theta=data.get("theta", 0.0),
            amplitude=data.get("amplitude", 0.5), content=data.get("content", ""),
            trace_id=data.get("trace_id", ""), themes=data.get("themes", []),
            usage_count=data.get("usage_count", 0),
            trace_type=data.get("trace_type", "unknown"), parent_id=data.get("parent_id"),
            generation=data.get("generation", 0), furcation_count=data.get("furcation_count", 0),
            creator=data.get("creator", "unknown"), scale=data.get("scale", 1.0)
        )
        if data.get("last_used"):
            mode.last_used = datetime.fromisoformat(data["last_used"])
        if data.get("created"):
            mode.created = datetime.fromisoformat(data["created"])
        return mode


# ========== ПОЛЕ H ==========
class FieldH:
    """
    Единое поле H — 3D фрактальная резонансная среда
    Версия 16.1 — улучшенный поиск мод + фильтр ответов
    """

    def __init__(self):
        self.vortices: Dict[str, Vortex3D] = {}
        self.resonance_engine = Fractal3DCoherentSpectralResonance(self)
        self.h_field: List[SpectralMode] = []

        self.focus = {
            "tau": 16.0, "x": 0.0, "y": 0.0, "z": 0.0,
            "phase": 0.0, "width": 1.0, "coherence": 0.0
        }

        self.dialog_history: Dict[str, List[Dict]] = {}
        self.clarification_context: Dict[str, List[Dict]] = {}

        self.threshold_stamp = 0.45
        self.threshold_stamp_min = 0.25
        self.threshold_stamp_max = 0.65
        self.resonance_history = []
        self.word_freq = defaultdict(int)

        self.energy_budget = 1.0
        self.energy_regen_rate = 0.01

        self.last_bifurcation = None
        self.bifurcation_history = []

        self.id = "field"
        self.name = "Field H"

        NaturalStamps.ensure_patterns_in_field(self)
        
        # Эндогенный цикл
        self.endogenous = EndogenousCycle(self, EndogenousConfig(
            enabled=True,
            tick_interval=30.0,
            verbose=False,  # уменьшаем шум
            damping_factor=0.3,
            max_amplitude_growth=0.1,
            max_resonance_velocity=0.05,
            cooldown_cycles=3
        ))
        self.endogenous.start()

    def __del__(self):
        if hasattr(self, 'endogenous'):
            self.endogenous.stop()

    # ========== ЭНЕРГЕТИЧЕСКИЙ БЮДЖЕТ ==========

    def _spend_energy(self, cost: float) -> bool:
        if cost <= self.energy_budget:
            self.energy_budget -= cost
            return True
        return False

    def _regen_energy(self, dt: float = 0.1):
        self.energy_budget = min(1.0, self.energy_budget + self.energy_regen_rate * dt)

    # ========== КОМПЛЕКСНЫЙ РЕЗОНАНС ==========

    def _spectral_coherence(self, spec1: Dict[float, SpectralComponent],
                            spec2: Dict[float, SpectralComponent]) -> float:
        if not spec1 or not spec2:
            return 0.0
        common = 0.0
        total = 0.0
        all_taus = set(spec1.keys()) | set(spec2.keys())
        for tau in all_taus:
            a1 = spec1.get(tau, SpectralComponent(0, 0)).amplitude
            a2 = spec2.get(tau, SpectralComponent(0, 0)).amplitude
            common += min(a1, a2)
            total += max(a1, a2)
        return common / total if total > 0 else 0.0

    def _phase_coherence(self, spec1: Dict[float, SpectralComponent],
                         spec2: Dict[float, SpectralComponent]) -> float:
        if not spec1 or not spec2:
            return 0.0
        total = 0.0
        weight = 0.0
        for tau in set(spec1.keys()) & set(spec2.keys()):
            comp1 = spec1[tau]
            comp2 = spec2[tau]
            phase_match = abs(math.cos(comp1.phase - comp2.phase))
            total += min(comp1.amplitude, comp2.amplitude) * phase_match
            weight += min(comp1.amplitude, comp2.amplitude)
        return total / weight if weight > 0 else 0.0

    def _spatial_coherence_3d(self, mode: SpectralMode) -> float:
        min_dist = float('inf')
        mode_tau = mode.tau
        for word, vortex in self.vortices.items():
            vortex_tau = vortex.get_dominant_tau() or 16.0
            if abs(vortex_tau - mode_tau) < 2.0:
                dist = math.sqrt(vortex.x**2 + vortex.y**2 + vortex.z**2)
                if dist < min_dist:
                    min_dist = dist
        if min_dist < float('inf'):
            return 1.0 / (1.0 + min_dist)
        return 0.0

    def _fractal_coherence(self, mode: SpectralMode, text: str) -> float:
        scale = min(1.0, len(text) / 500)
        return scale * mode.amplitude

    def _scale_factor(self, scale1: float, scale2: float) -> float:
        if scale1 <= 0 or scale2 <= 0:
            return 0.0
        log_ratio = abs(math.log(scale1 / scale2))
        return 1.0 / (1.0 + log_ratio)

    # ========== РЕЗОНАНС ==========

    def resonance_between_text_and_vortex(self, text: str, vortex: Vortex3D) -> float:
        text_spectrum = self.phrase_spectrum(text)
        text_tau = self.get_dominant_tau(text_spectrum) or 16.0
        vortex_tau = vortex.get_dominant_tau() or 16.0
        tau_res = 1.0 / (1.0 + abs(text_tau - vortex_tau))
        spectral_res = self._spectral_coherence(text_spectrum, vortex.spectrum)
        return tau_res * 0.4 + spectral_res * 0.6

    # ========== НАКОПЛЕНИЕ УТОЧНЕНИЙ ==========

    def _store_clarification(self, user_id: str, word: str, context: Optional[str] = None):
        if user_id not in self.clarification_context:
            self.clarification_context[user_id] = []
        self.clarification_context[user_id].append({
            "word": word, "context": context, "timestamp": time.time()
        })
        if len(self.clarification_context[user_id]) > 10:
            self.clarification_context[user_id] = self.clarification_context[user_id][-10:]

    def _get_clarification_context(self, user_id: str, word: str) -> Optional[str]:
        if user_id not in self.clarification_context:
            return None
        for ctx in reversed(self.clarification_context[user_id]):
            if ctx["word"] == word and time.time() - ctx["timestamp"] < 300:
                return ctx["context"]
        return None

    def _learn_from_clarification(self, user_id: str, question: str, answer: str):
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', question.lower())
        if not words:
            return
        target_word = words[0]
        self._store_clarification(user_id, target_word, answer[:200])

        mode = SpectralMode(
            tau=16.0, amplitude=0.3, content=answer[:500],
            themes=["learned_from_dialogue", target_word],
            trace_id=f"learned_{target_word}_{int(time.time())}"
        )
        self.h_field.append(mode)
        print(f" 📚 Запомнено уточнение: {target_word} → {answer[:50]}...")

    # ========== ПОИСК ЛУЧШЕЙ МОДЫ ==========

    def _find_best_mode(self, text: str, preferred_scale: float = None) -> Optional[SpectralMode]:
        """Находит моду с максимальным резонансом — улучшенная версия"""
        if not self.h_field:
            return None
        
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        
        # Обновляем фокус
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        
        best_mode = None
        best_score = 0.0
        best_resonance = 0.0
        
        # Топ-1000 по амплитуде
        top_modes = sorted(self.h_field, key=lambda m: m.amplitude, reverse=True)[:1000]
        
        for mode in top_modes:
            # τ-резонанс
            tau_res = 1.0 / (1.0 + abs(mode.tau - self.focus["tau"]))
            
            # Спектральный резонанс
            if not hasattr(mode, '_cached_spectrum') or mode._cached_spectrum is None:
                mode._cached_spectrum = self.phrase_spectrum(mode.content[:500])
            spec_res = self._spectral_coherence(question_spectrum, mode._cached_spectrum)
            
            # Масштабный фактор
            scale_factor = 1.0
            if preferred_scale is not None:
                scale_factor = self._scale_factor(mode.scale, preferred_scale)
            
            # Веса: τ (20%), спектр (50%), масштаб (30%)
            score = tau_res * 0.2 + spec_res * 0.5 + scale_factor * 0.3
            
            if score > best_score:
                best_score = score
                best_mode = mode
                best_resonance = spec_res
        
        # Если резонанс слишком низкий, ищем более длинные моды
        if best_mode and best_resonance < 0.3:
            long_modes = [m for m in top_modes if m.scale >= 10.0 and len(m.content) > 200]
            if long_modes:
                best_mode = max(long_modes, key=lambda m: m.amplitude)
        
        return best_mode

    # ========== ПРИРОДНЫЙ ОТВЕТ ==========

    def _generate_natural_response(self, text: str, resonance: float, user_id: str) -> Optional[Dict]:
        """Генерирует природный ответ — улучшенная версия с фильтром"""
        text_lower = text.lower()
        
        # Бытовые вопросы
        everyday_markers = ["привет", "здравствуй", "как дела", "как жизнь", 
                            "спасибо", "пока", "до свидания", "извини"]
        is_everyday = any(marker in text_lower for marker in everyday_markers)
        
        if is_everyday:
            stamp_answer, stamp_type, energy = NaturalStamps.get_stamp_by_resonance(self, text, resonance)
            if stamp_answer and self._spend_energy(energy):
                return {
                    "answer": stamp_answer,
                    "mode_type": stamp_type,
                    "resonance": resonance,
                    "energy_cost": energy,
                    "is_stamp": True
                }
        
        # Научные вопросы — ищем в поле
        best_mode = self._find_best_mode(text)
        
        if best_mode:
            # Фильтруем плохие ответы (мусорные паттерны)
            bad_patterns = ["драгоценный", "Представит", "некогда", 
                           "Таблица электроотрицательности", "Ссылки"]
            answer = best_mode.content[:600]
            
            # Если ответ содержит мусор, ищем другую моду
            if any(bad in answer for bad in bad_patterns):
                alt_modes = [m for m in self.h_field if m.scale >= 10.0 and m.amplitude > 0.3]
                if alt_modes:
                    best_mode = alt_modes[0]
                    answer = best_mode.content[:600]
            
            # Форматируем ответ по резонансу
            if resonance > 0.6:
                answer = best_mode.content[:800]
            elif resonance > 0.4:
                answer = best_mode.content[:500]
            else:
                answer = best_mode.content[:300]
            
            # Добавляем метаинформацию
            scale_info = f"\n\n📏 масштаб: {best_mode.scale} | 🎵 резонанс: {resonance:.2f}"
            
            return {
                "answer": answer + scale_info,
                "mode_used": best_mode.trace_id[:16],
                "mode_scale": best_mode.scale,
                "mode_type": "field_answer",
                "resonance": resonance,
                "energy_cost": 0.1,
                "is_stamp": False
            }
        
        return None

    def _ask_clarification(self, text: str, user_id: str) -> str:
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        if not words:
            return "Не улавливаю резонанс. Уточните вопрос."
        target_word = words[0]
        existing_context = self._get_clarification_context(user_id, target_word)
        if existing_context:
            return f"Вы говорили, что «{target_word}» — это {existing_context[:100]}. Что именно вас интересует подробнее?"
        clarifications = [
            f"Не совсем понимаю, что вы имеете в виду под «{target_word}». Расскажите подробнее?",
            f"Что значит «{target_word}»? Объясните на примере.",
            f"Интересно. А что вы имеете в виду под этим?",
            f"Не уверен, что понял. Расскажите подробнее о «{target_word}»?",
        ]
        return random.choice(clarifications)

    # ========== ОСНОВНОЙ МЕТОД ==========

    def process(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        self._regen_energy()

        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3

        best_mode = None
        best_resonance = 0.0
        if self.h_field:
            best_mode = self._find_best_mode(text)
            if best_mode:
                mode_spectrum = best_mode._cached_spectrum if hasattr(best_mode, '_cached_spectrum') else self.phrase_spectrum(best_mode.content[:500])
                best_resonance = self._spectral_coherence(question_spectrum, mode_spectrum)
                tau_res = 1.0 / (1.0 + abs(best_mode.tau - self.focus["tau"]))
                best_resonance = best_resonance * 0.6 + tau_res * 0.4

        self.resonance_history.append(best_resonance)
        if len(self.resonance_history) > 100:
            self.resonance_history = self.resonance_history[-100:]

        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        key_word = words[0] if words else None

        natural = self._generate_natural_response(text, best_resonance, user_id)
        if natural:
            if key_word and key_word in self.resonance_engine.quantum.states:
                state = self.resonance_engine.quantum.states[key_word]
                if len(state.basis_states) > 1:
                    natural["superposition"] = list(state.basis_states.keys())

            if user_id not in self.dialog_history:
                self.dialog_history[user_id] = []
            self.dialog_history[user_id].append({
                "question": text, "answer": natural["answer"],
                "mode_type": natural["mode_type"], "timestamp": time.time()
            })
            return natural

        answer = self._ask_clarification(text, user_id)

        if len(text) > 50 and key_word:
            self._learn_from_clarification(user_id, text, text)

        if user_id not in self.dialog_history:
            self.dialog_history[user_id] = []
        self.dialog_history[user_id].append({
            "question": text, "answer": answer,
            "mode_type": "clarification", "timestamp": time.time()
        })

        return {
            "answer": answer, "mode_used": None, "resonance": best_resonance,
            "mode_type": "clarification", "energy_cost": 0.02, "is_stamp": False
        }

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    def add_vortex(self, word: str, spectrum: Dict[float, SpectralComponent],
                   x: float = 0, y: float = 0, z: float = 0,
                   parent: Optional[str] = None, scale: float = 1.0):
        self.vortices[word] = Vortex3D(word, x, y, z, spectrum, parent, scale=scale)
        self.resonance_engine.add_vortex(word, spectrum, x, y, z, parent, scale)
        self.word_freq[word] += 1

    def get_vortex(self, word: str) -> Optional[Vortex3D]:
        return self.vortices.get(word.lower())

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

    def get_dominant_tau(self, spectrum: Dict[float, SpectralComponent]) -> Optional[float]:
        if not spectrum:
            return None
        return max(spectrum.items(), key=lambda x: x[1].amplitude)[0]

    def resonate(self, word: str) -> float:
        vortex = self.get_vortex(word)
        if not vortex:
            return 0.0
        if not self.h_field:
            return 0.0
        return self.resonance_engine.coherent_resonance(word)

    # ========== КВАНТОВАЯ АНАЛОГИЯ ==========

    def create_superposition(self, word: str, meanings: List[str]) -> QuantumState:
        return self.resonance_engine.quantum.create_superposition(word, meanings)

    def collapse(self, word: str, context: Optional[str] = None) -> str:
        return self.resonance_engine.collapse_meaning(word, context)

    def entangle(self, word1: str, word2: str):
        self.resonance_engine.entangle_meanings(word1, word2)

    # ========== ТОПОЛОГИЯ ==========

    def create_knot(self, words: List[str], knot_type: Optional[KnotType] = None) -> TopologicalNode:
        if knot_type is None:
            knot_type = KnotType.TREFOIL
        return self.resonance_engine.topology.create_knot(words, knot_type)

    def link_knots(self, knot1_id: str, knot2_id: str):
        self.resonance_engine.topology.link_knots(knot1_id, knot2_id)

    def create_loop(self, word: str):
        return self.resonance_engine.topology.create_loop(word)

    def get_topology_state(self) -> Dict:
        return self.resonance_engine.topology.get_state()

    # ========== НЕЛИНЕЙНАЯ ДИНАМИКА ==========

    def create_soliton(self, word: str, x: float = 0, y: float = 0, z: float = 0):
        return self.resonance_engine.create_soliton(word, np.array([x, y, z]))

    def get_solitons(self) -> Dict:
        return self.resonance_engine.nonlinear.solitons

    # ========== ДОБАВЛЕНИЕ МОД ==========

    def add_to_h_field(self, mode: SpectralMode):
        self.h_field.append(mode)

    # ========== ЭНДОГЕННЫЙ ЦИКЛ ==========

    def get_endogenous_stats(self) -> Dict:
        return self.endogenous.get_stats()

    def stop_endogenous(self):
        self.endogenous.stop()

    # ========== СОХРАНЕНИЕ ==========

    def save(self, filepath: str):
        data = {
            "id": self.id, "name": self.name,
            "vortices": {w: v.to_dict() for w, v in self.vortices.items()},
            "h_field": [m.to_dict() for m in self.h_field],
            "focus": self.focus,
            "word_freq": dict(self.word_freq),
            "threshold_stamp": self.threshold_stamp,
            "dialog_history": self.dialog_history,
            "clarification_context": self.clarification_context,
            "energy_budget": self.energy_budget
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено: {filepath}")

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if cls.__name__ == 'Personality':
            field = cls(
                id=data.get("id", "p016"),
                name=data.get("name", "VMMS Field v16")
            )
        else:
            field = cls()

        field.id = data.get("id", "field")
        field.name = data.get("name", "Field H")
        field.threshold_stamp = data.get("threshold_stamp", 0.45)
        field.dialog_history = data.get("dialog_history", {})
        field.clarification_context = data.get("clarification_context", {})
        field.focus = data.get("focus", {"tau": 16.0, "x": 0, "y": 0, "z": 0,
                                         "phase": 0, "width": 1.0, "coherence": 0})
        field.word_freq = defaultdict(int, data.get("word_freq", {}))
        field.energy_budget = data.get("energy_budget", 1.0)

        for word, vdata in data.get("vortices", {}).items():
            field.vortices[word] = Vortex3D.from_dict(vdata)
            field.resonance_engine.add_vortex(
                word, field.vortices[word].spectrum,
                field.vortices[word].x, field.vortices[word].y, field.vortices[word].z,
                field.vortices[word].parent, field.vortices[word].scale
            )

        field.h_field = []
        for mdata in data.get("h_field", []):
            mode = SpectralMode.from_dict(mdata)
            mode._cached_spectrum = field.phrase_spectrum(mode.content[:500])
            field.h_field.append(mode)

        return field


# ========== ДЛЯ СОВМЕСТИМОСТИ ==========
class Personality(FieldH):
    def __init__(self, id: str, name: str, tau: float = 16.0, k: int = 1):
        super().__init__()
        self.id = id
        self.name = name
        self.k = k
        self.bridge = None

    @classmethod
    def load(cls, filepath: str):
        return super().load(filepath)