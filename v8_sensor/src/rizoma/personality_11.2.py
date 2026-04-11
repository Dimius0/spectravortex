"""
Personality — ядро личности, поле H
Версия 11.2 — фрактальный алфавит + время + диалог + адаптивный порог
"""
import json
import hashlib
import random
import re
import time
import math
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict


# ========== БАЗОВЫЙ АЛФАВИТ ==========
RUSSIAN_ALPHABET = {
    'а': 1, 'б': 2, 'в': 3, 'г': 4, 'д': 5, 'е': 6, 'ё': 7,
    'ж': 8, 'з': 9, 'и': 10, 'й': 11, 'к': 12, 'л': 13, 'м': 14,
    'н': 15, 'о': 16, 'п': 17, 'р': 18, 'с': 19, 'т': 20, 'у': 21,
    'ф': 22, 'х': 23, 'ц': 24, 'ч': 25, 'ш': 26, 'щ': 27, 'ъ': 28,
    'ы': 29, 'ь': 30, 'э': 31, 'ю': 32, 'я': 33
}

NEXT_SYMBOL_TAU = 34


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def word_spectrum_from_chars(word: str, char_tau_map: Dict[str, float]) -> Dict[float, float]:
    """Вычисляет спектр слова из τ его букв. Слово — это аккорд."""
    spectrum = {}
    char_taus = []
    
    for ch in word.lower():
        if ch in char_tau_map:
            tau = char_tau_map[ch]
            char_taus.append(tau)
            spectrum[tau] = spectrum.get(tau, 0) + 1.0
    
    if not char_taus:
        return spectrum
    
    max_amp = max(spectrum.values()) if spectrum else 1.0
    for tau in spectrum:
        spectrum[tau] /= max_amp
    
    for i, tau1 in enumerate(char_taus):
        for j, tau2 in enumerate(char_taus):
            if i >= j:
                continue
            ratio = tau1 / tau2 if tau2 != 0 else 1.0
            if 0.3 < ratio < 3.0:
                harmonic = tau1 * ratio
                if 1.0 <= harmonic <= 1000:
                    spectrum[harmonic] = spectrum.get(harmonic, 0) + 0.3
            ratio_inv = tau2 / tau1 if tau1 != 0 else 1.0
            if 0.3 < ratio_inv < 3.0:
                harmonic = tau2 * ratio_inv
                if 1.0 <= harmonic <= 1000:
                    spectrum[harmonic] = spectrum.get(harmonic, 0) + 0.3
    
    return spectrum


# ========== ВИХРЬ (слово) ==========
@dataclass
class Vortex:
    word: str
    spectrum: Dict[float, float] = field(default_factory=dict)
    amplitude: float = 0.5
    usage_count: int = 0
    last_used: Optional[datetime] = None
    created: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_dominant_tau(self) -> Optional[float]:
        if not self.spectrum:
            return None
        return max(self.spectrum.items(), key=lambda x: x[1])[0]
    
    def update_spectrum(self, new_spectrum: Dict[float, float], weight: float = 0.3):
        self.last_updated = datetime.now()
        for tau, amp in new_spectrum.items():
            old = self.spectrum.get(tau, 0)
            self.spectrum[tau] = old * 0.7 + amp * weight * 0.3
        
        if len(self.spectrum) > 20:
            sorted_items = sorted(self.spectrum.items(), key=lambda x: x[1], reverse=True)
            self.spectrum = dict(sorted_items[:20])
    
    def register_use(self):
        self.usage_count += 1
        self.last_used = datetime.now()
        self.amplitude = min(1.0, self.amplitude + 0.05)
    
    def to_dict(self):
        return {
            "word": self.word,
            "spectrum": {str(k): v for k, v in self.spectrum.items()},
            "amplitude": self.amplitude,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created": self.created.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        vortex = cls(
            word=data["word"],
            amplitude=data.get("amplitude", 0.5),
            usage_count=data.get("usage_count", 0)
        )
        vortex.spectrum = {float(k): v for k, v in data.get("spectrum", {}).items()}
        if data.get("last_used"):
            vortex.last_used = datetime.fromisoformat(data["last_used"])
        if data.get("created"):
            vortex.created = datetime.fromisoformat(data["created"])
        if data.get("last_updated"):
            vortex.last_updated = datetime.fromisoformat(data["last_updated"])
        return vortex


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
    created: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.trace_id:
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.trace_id = f"mode_{content_hash}"
    
    def register_use(self):
        self.usage_count += 1
        self.last_used = datetime.now()
        self.amplitude = min(1.0, self.amplitude + 0.05)
    
    def to_dict(self):
        return {
            "tau": self.tau,
            "delta": self.delta,
            "theta": self.theta,
            "amplitude": self.amplitude,
            "content": self.content,
            "trace_id": self.trace_id,
            "themes": self.themes,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created": self.created.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        mode = cls(
            tau=data["tau"],
            delta=data.get("delta", 0.0),
            theta=data.get("theta", 0.0),
            amplitude=data.get("amplitude", 0.5),
            content=data.get("content", ""),
            trace_id=data.get("trace_id", ""),
            themes=data.get("themes", []),
            usage_count=data.get("usage_count", 0)
        )
        if data.get("last_used"):
            mode.last_used = datetime.fromisoformat(data["last_used"])
        if data.get("created"):
            mode.created = datetime.fromisoformat(data["created"])
        return mode


# ========== ПОЛЕ H ==========
class FieldH:
    def __init__(self):
        self.vortices: Dict[str, Vortex] = {}
        self.h_field: List[SpectralMode] = []
        self.char_tau: Dict[str, float] = {}
        self.next_tau = NEXT_SYMBOL_TAU
        
        self.focus = {"tau": 16.0, "delta": 0.0, "theta": 0.0, "width": 1.0}
        self.word_freq = defaultdict(int)
        
        # Инициализация алфавита
        for ch, tau in RUSSIAN_ALPHABET.items():
            self.char_tau[ch] = tau
        
        # Диалог
        self.dialog_history: Dict[str, List[Dict]] = {}
        
        # Адаптивный порог
        self.threshold_stamp = 0.45
        self.threshold_stamp_min = 0.25
        self.threshold_stamp_max = 0.65
        self.resonance_history = []
        
        self.id = "field"
        self.name = "Field H"
    
    # ========== АЛФАВИТ ==========
    
    def get_or_create_char_tau(self, char: str) -> float:
        char_lower = char.lower()
        if char_lower in self.char_tau:
            return self.char_tau[char_lower]
        new_tau = self.next_tau
        self.next_tau += 1
        self.char_tau[char_lower] = new_tau
        print(f" 🎵 Новый символ '{char}' → τ={new_tau}")
        return new_tau
    
    def get_word_spectrum(self, word: str) -> Dict[float, float]:
        if not word:
            return {}
        char_taus = {}
        for ch in word.lower():
            if ch in self.char_tau:
                char_taus[ch] = self.char_tau[ch]
            else:
                char_taus[ch] = self.get_or_create_char_tau(ch)
        
        spectrum = {}
        for tau in char_taus.values():
            spectrum[tau] = spectrum.get(tau, 0) + 1.0
        
        tau_list = list(char_taus.values())
        for i, tau1 in enumerate(tau_list):
            for j, tau2 in enumerate(tau_list):
                if i >= j:
                    continue
                ratio = tau1 / tau2 if tau2 != 0 else 1.0
                if 0.3 < ratio < 3.0:
                    harmonic = tau1 * ratio
                    if 1.0 <= harmonic <= 1000:
                        spectrum[harmonic] = spectrum.get(harmonic, 0) + 0.3
                ratio_inv = tau2 / tau1 if tau1 != 0 else 1.0
                if 0.3 < ratio_inv < 3.0:
                    harmonic = tau2 * ratio_inv
                    if 1.0 <= harmonic <= 1000:
                        spectrum[harmonic] = spectrum.get(harmonic, 0) + 0.3
        
        if spectrum:
            max_amp = max(spectrum.values())
            for tau in spectrum:
                spectrum[tau] /= max_amp
        return spectrum
    
    # ========== УПРАВЛЕНИЕ СЛОВАМИ ==========
    
    def add_word(self, word: str, context_spectrum: Dict[float, float] = None, weight: float = 0.3):
        word_lower = word.lower()
        word_spectrum = self.get_word_spectrum(word)
        if context_spectrum:
            for tau, amp in context_spectrum.items():
                word_spectrum[tau] = word_spectrum.get(tau, 0) + amp * weight
        
        if word_lower in self.vortices:
            vortex = self.vortices[word_lower]
            vortex.update_spectrum(word_spectrum, weight)
        else:
            vortex = Vortex(word_lower, word_spectrum, amplitude=0.3)
            self.vortices[word_lower] = vortex
        
        self.word_freq[word_lower] += 1
        return vortex
    
    def phrase_spectrum(self, text: str) -> Dict[float, float]:
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]+\b', text.lower())
        result = {}
        for w in words:
            if w in self.vortices:
                for tau, amp in self.vortices[w].spectrum.items():
                    result[tau] = result.get(tau, 0) + amp
            else:
                word_spectrum = self.get_word_spectrum(w)
                for tau, amp in word_spectrum.items():
                    result[tau] = result.get(tau, 0) + amp
        if result:
            max_amp = max(result.values())
            for tau in result:
                result[tau] /= max_amp
        return result
    
    def get_dominant_tau(self, spectrum: Dict[float, float]) -> Optional[float]:
        if not spectrum:
            return None
        return max(spectrum.items(), key=lambda x: x[1])[0]
    
    # ========== УПРАВЛЕНИЕ МОДАМИ ==========
    
    def add_to_h_field(self, mode: SpectralMode):
        best_match = None
        best_resonance = 0.0
        for existing in self.h_field:
            dt = abs(mode.tau - existing.tau)
            resonance = 1.0 / (1.0 + dt)
            if resonance > best_resonance:
                best_resonance = resonance
                best_match = existing
        
        if best_match and best_resonance > 0.9:
            best_match.register_use()
        else:
            self.h_field.append(mode)
        
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]+\b', mode.content.lower())
        for w in words:
            self.add_word(w, {mode.tau: 1.0}, weight=0.1)
    
    # ========== ВРЕМЯ ==========
    
    def _get_time_modifier(self) -> float:
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return 1.2
        elif 12 <= hour < 18:
            return 1.0
        elif 18 <= hour < 23:
            return 0.9
        else:
            return 0.7
    
    def _decay_modes(self):
        """Старение мод со временем"""
        now = datetime.now()
        for mode in self.h_field:
            if mode.last_used:
                days = (now - mode.last_used).days
                decay = 0.95 ** days
                mode.amplitude *= decay
            else:
                days = (now - mode.created).days
                decay = 0.98 ** days
                mode.amplitude *= decay
    
    def _forget_old_vortices(self, days_threshold: int = 30):
        """Забывание неиспользуемых вихрей"""
        now = datetime.now()
        to_remove = []
        for word, vortex in self.vortices.items():
            if vortex.last_used:
                age = (now - vortex.last_used).days
                if age > days_threshold:
                    vortex.amplitude *= 0.5
                    if vortex.amplitude < 0.05:
                        to_remove.append(word)
            elif vortex.created:
                age = (now - vortex.created).days
                if age > days_threshold and vortex.usage_count == 0:
                    to_remove.append(word)
        for word in to_remove:
            del self.vortices[word]
            print(f" 💀 Забыто: {word}")
    
    # ========== АДАПТИВНЫЙ ПОРОГ ==========
    
    def _adapt_thresholds(self):
        if len(self.resonance_history) < 10:
            return
        recent = self.resonance_history[-20:]
        avg_resonance = sum(recent) / len(recent)
        volatility = np.std(recent) if len(recent) > 1 else 0.1
        target = avg_resonance + volatility * 0.5
        new_threshold = max(self.threshold_stamp_min, min(self.threshold_stamp_max, target))
        self.threshold_stamp = self.threshold_stamp * 0.9 + new_threshold * 0.1
        if len(self.resonance_history) % 20 == 0:
            print(f" 🔧 Адаптация порога: {self.threshold_stamp:.3f} (avg={avg_resonance:.3f})")
    
    # ========== РЕЗОНАНС ==========
    
    def _resonance_between_spectra(self, spec1: Dict[float, float], spec2: Dict[float, float]) -> float:
        if not spec1 or not spec2:
            return 0.0
        common = 0.0
        total = 0.0
        all_taus = set(spec1.keys()) | set(spec2.keys())
        for tau in all_taus:
            a1 = spec1.get(tau, 0)
            a2 = spec2.get(tau, 0)
            common += min(a1, a2)
            total += max(a1, a2)
        return common / total if total > 0 else 0.0
    
    def _resonance_with_mode(self, mode: SpectralMode, question_spectrum: Dict[float, float], question_text: str) -> float:
        dt = abs(mode.tau - self.focus["tau"])
        tau_res = 1.0 / (1.0 + dt)
        mode_spectrum = self.phrase_spectrum(mode.content[:500])
        spec_res = self._resonance_between_spectra(mode_spectrum, question_spectrum)
        question_words = set(re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', question_text.lower()))
        mode_words = set(re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', mode.content.lower()))
        theme_res = len(question_words & mode_words) / max(len(question_words), 1) if question_words else 0.0
        return tau_res * 0.4 + spec_res * 0.3 + theme_res * 0.3
    
    # ========== ДИАЛОГ ==========
    
    def _ask_clarification(self, text: str) -> str:
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        if words:
            return f"❓ Не совсем понимаю, что вы имеете в виду под «{words[0]}». Расскажите подробнее? (или дай пример)"
        return "❓ Не улавливаю резонанс. Уточните вопрос или дай пример."
    
    def _ask_followup(self, mode: SpectralMode, history: List[Dict]) -> str:
        if not history:
            return f"{mode.content[:300]}\n\n❓ Что тебе ещё интересно?"
        last_answer = history[-1].get("answer", "")
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', last_answer.lower())
        if words:
            return f"{mode.content[:300]}\n\n❓ А что ты думаешь о «{words[0]}»? Хочешь узнать подробнее?"
        return f"{mode.content[:300]}\n\n❓ Что тебе ещё интересно узнать об этом?"
    
    def _answer_with_suggestion(self, best_mode: SpectralMode, resonant_modes: List[SpectralMode]) -> str:
        answer = best_mode.content[:400]
        themes = set()
        for m in resonant_modes[:3]:
            themes.update(m.themes)
        if themes:
            return f"{answer}\n\n💡 Возможно, вас заинтересует: {', '.join(list(themes)[:3])}?"
        return answer
    
    def _get_available_concepts(self) -> List[str]:
        return [word for word, v in self.vortices.items() if v.amplitude > 0.5 and v.usage_count > 3][:10]
    
    def _get_phrase_for_word(self, word: str) -> str:
        for mode in self.h_field:
            if word in mode.content.lower():
                sentences = re.split(r'[.!?]+', mode.content[:300])
                for s in sentences:
                    s = s.strip()
                    if 20 < len(s) < 150:
                        return s
        return f"«{word}»"
    
    def _explain_with_known_concepts(self, new_word: str) -> Optional[SpectralMode]:
        available = self._get_available_concepts()
        if len(available) < 2:
            return None
        concept1, concept2 = available[0], available[1]
        v1 = self.vortices.get(concept1)
        v2 = self.vortices.get(concept2)
        if not v1 or not v2:
            return None
        tau1 = v1.get_dominant_tau() or 16.0
        tau2 = v2.get_dominant_tau() or 16.0
        new_tau = (tau1 + tau2) / 2
        content = f"🧠 Это как {concept1} и {concept2} вместе.\n\n📖 {concept1} — это {self._get_phrase_for_word(concept1)}\n\n📖 {concept2} — это {self._get_phrase_for_word(concept2)}\n\n✨ А {new_word} — это когда они работают вместе."
        mode = SpectralMode(tau=new_tau, amplitude=0.5, content=content, themes=["explanation", concept1, concept2, new_word], trace_id=f"explain_{new_word}_{int(time.time())}")
        self.add_to_h_field(mode)
        self.add_word(new_word, {new_tau: 1.0}, weight=0.5)
        return mode
    
    # ========== ПРОВЕРКА СОГЛАСОВАННОСТИ ==========
    
    def _check_consistency(self, new_spectrum: Dict[float, float]) -> float:
        """Проверяет, насколько новое знание согласуется с существующим"""
        if not self.vortices:
            return 0.5
        scores = []
        for vortex in list(self.vortices.values())[:100]:
            scores.append(self._resonance_between_spectra(vortex.spectrum, new_spectrum))
        return sum(scores) / len(scores) if scores else 0.5
    
    def _is_dead_end_synthesis(self, new_spectrum: Dict[float, float]) -> bool:
        """Диагностика тупикового синтеза"""
        consistency = self._check_consistency(new_spectrum)
        return consistency < 0.3
    
    # ========== ПОПОЛНЕНИЕ ИЗ ДИАЛОГА ==========
    
    def _learn_from_dialogue(self, question: str, answer: str):
        """Пополняет базу знаний из диалога"""
        mode = SpectralMode(
            tau=self.get_dominant_tau(self.phrase_spectrum(answer)) or 16.0,
            amplitude=0.3,
            content=answer,
            themes=["learned_from_dialogue"],
            trace_id=f"learned_{int(time.time())}"
        )
        self.add_to_h_field(mode)
        print(f" 📚 Пополнено из диалога: новый блок знаний")
    
    # ========== ГЛАВНЫЙ PROCESS ==========
    
    def process(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        # Временной контекст диалога
        if user_id not in self.dialog_history:
            self.dialog_history[user_id] = []
        history = self.dialog_history[user_id]
        recent_history = history[-5:] if len(history) > 5 else history
        if recent_history:
            last_time = recent_history[-1].get("timestamp", 0)
            if time.time() - last_time > 3600:
                recent_history = []
        
        # Спектр вопроса
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        
        # Обновление фокуса
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        
        if not self.h_field:
            return {"answer": "Поле H пусто. Добавьте тексты.", "error": True}
        
        # Ключевое слово
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        key_word = words[0] if words else None
        
        # Знакомое / новое слово
        is_familiar = False
        is_new = False
        if key_word and key_word in self.vortices:
            vortex = self.vortices[key_word]
            is_familiar = vortex.amplitude > 0.4 or vortex.usage_count > 5
            is_new = vortex.amplitude < 0.3 and vortex.usage_count < 3
        else:
            is_new = key_word and key_word not in self.vortices
        
        # Резонанс
        scored = [(self._resonance_with_mode(mode, question_spectrum, text), mode) for mode in self.h_field]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_resonance, best_mode = scored[0]
        
        # Сохраняем историю резонанса
        self.resonance_history.append(best_resonance)
        if len(self.resonance_history) > 100:
            self.resonance_history = self.resonance_history[-100:]
        self._adapt_thresholds()
        
        # Адаптивный порог
        effective_threshold = self.threshold_stamp
        time_mod = self._get_time_modifier()
        
        # Режимы
        THRESHOLD_FURCATION = 0.2
        
        # 1. ШТАМП
        if (is_familiar and best_resonance > effective_threshold - 0.1) or best_resonance >= effective_threshold:
            best_mode.register_use()
            if key_word and key_word in self.vortices:
                self.vortices[key_word].register_use()
            
            # Диалоговый режим (30% шанс задать встречный вопрос)
            if random.random() < 0.3 * time_mod:
                answer = self._ask_followup(best_mode, recent_history)
                mode_type = "dialog_followup"
            else:
                answer = best_mode.content[:500]
                mode_type = "stamp"
            
            # Сохраняем в историю
            self.dialog_history[user_id].append({
                "question": text, "answer": answer, "mode_type": mode_type, "timestamp": time.time()
            })
            if len(self.dialog_history[user_id]) > 10:
                self.dialog_history[user_id] = self.dialog_history[user_id][-10:]
            
            # Старение
            self._decay_modes()
            self._forget_old_vortices()
            
            return {
                "answer": answer,
                "mode_used": best_mode.trace_id,
                "tau": best_mode.tau,
                "resonance": best_resonance,
                "mode_type": mode_type,
                "energy_cost": 0.1
            }
        
        # 2. ФУРКАЦИЯ
        elif is_new or best_resonance >= THRESHOLD_FURCATION:
            if is_new and key_word:
                explanation = self._explain_with_known_concepts(key_word)
                if explanation:
                    # Проверка согласованности
                    new_spectrum = self.phrase_spectrum(explanation.content)
                    if self._is_dead_end_synthesis(new_spectrum):
                        return {
                            "answer": self._ask_clarification(text),
                            "mode_type": "clarification",
                            "resonance": best_resonance,
                            "energy_cost": 0.05
                        }
                    
                    self.dialog_history[user_id].append({
                        "question": text, "answer": explanation.content, "mode_type": "furcation_explanation", "timestamp": time.time()
                    })
                    return {
                        "answer": explanation.content,
                        "mode_used": explanation.trace_id,
                        "resonance": best_resonance,
                        "mode_type": "furcation_explanation",
                        "new_word": key_word,
                        "energy_cost": 0.5
                    }
            
            resonant_modes = [m for r, m in scored[:3] if r > THRESHOLD_FURCATION]
            answer = self._answer_with_suggestion(best_mode, resonant_modes)
            self.dialog_history[user_id].append({
                "question": text, "answer": answer, "mode_type": "suggestion", "timestamp": time.time()
            })
            return {
                "answer": answer,
                "mode_used": best_mode.trace_id,
                "tau": best_mode.tau,
                "resonance": best_resonance,
                "mode_type": "suggestion",
                "energy_cost": 0.5
            }
        
        # 3. УТОЧНЕНИЕ
        else:
            answer = self._ask_clarification(text)
            self.dialog_history[user_id].append({
                "question": text, "answer": answer, "mode_type": "clarification", "timestamp": time.time()
            })
            return {
                "answer": answer,
                "mode_used": None,
                "resonance": best_resonance,
                "mode_type": "clarification",
                "energy_cost": 0.05
            }
    
    # ========== СОХРАНЕНИЕ И ЗАГРУЗКА ==========
    
    def save(self, filepath: str):
        data = {
            "id": self.id, "name": self.name,
            "char_tau": self.char_tau, "next_tau": self.next_tau,
            "vortices": {w: v.to_dict() for w, v in self.vortices.items()},
            "h_field": [m.to_dict() for m in self.h_field],
            "focus": self.focus, "word_freq": dict(self.word_freq),
            "threshold_stamp": self.threshold_stamp,
            "dialog_history": self.dialog_history
        }
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
        field.char_tau = data.get("char_tau", RUSSIAN_ALPHABET.copy())
        field.next_tau = data.get("next_tau", NEXT_SYMBOL_TAU)
        field.threshold_stamp = data.get("threshold_stamp", 0.45)
        field.dialog_history = data.get("dialog_history", {})
        for word, vdata in data.get("vortices", {}).items():
            field.vortices[word] = Vortex.from_dict(vdata)
            field.word_freq[word] = data.get("word_freq", {}).get(word, 0)
        field.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]
        field.focus = data.get("focus", {"tau": 16.0, "delta": 0.0, "theta": 0.0, "width": 1.0})
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
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        field = cls(id=data.get("id", "p016"), name=data.get("name", "VMMS Field"))
        field.char_tau = data.get("char_tau", RUSSIAN_ALPHABET.copy())
        field.next_tau = data.get("next_tau", NEXT_SYMBOL_TAU)
        field.threshold_stamp = data.get("threshold_stamp", 0.45)
        field.dialog_history = data.get("dialog_history", {})
        for word, vdata in data.get("vortices", {}).items():
            field.vortices[word] = Vortex.from_dict(vdata)
            field.word_freq[word] = data.get("word_freq", {}).get(word, 0)
        field.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]
        field.focus = data.get("focus", {"tau": 16.0, "delta": 0.0, "theta": 0.0, "width": 1.0})
        return field