"""
Personality — ядро личности, поле H
Версия 11.1 — фрактальный алфавит + три режима ответа (штамп/фуркация/уточнение)
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
# Русский алфавит (33 буквы) с τ от 1 до 33
RUSSIAN_ALPHABET = {
    'а': 1, 'б': 2, 'в': 3, 'г': 4, 'д': 5, 'е': 6, 'ё': 7,
    'ж': 8, 'з': 9, 'и': 10, 'й': 11, 'к': 12, 'л': 13, 'м': 14,
    'н': 15, 'о': 16, 'п': 17, 'р': 18, 'с': 19, 'т': 20, 'у': 21,
    'ф': 22, 'х': 23, 'ц': 24, 'ч': 25, 'ш': 26, 'щ': 27, 'ъ': 28,
    'ы': 29, 'ь': 30, 'э': 31, 'ю': 32, 'я': 33
}

NEXT_SYMBOL_TAU = 34


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_char_tau(char: str) -> Optional[float]:
    """Возвращает τ символа (буквы, цифры, знака)"""
    char_lower = char.lower()
    if char_lower in RUSSIAN_ALPHABET:
        return RUSSIAN_ALPHABET[char_lower]
    return None


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
    
    # Нормализуем
    max_amp = max(spectrum.values()) if spectrum else 1.0
    for tau in spectrum:
        spectrum[tau] /= max_amp
    
    # Гармоники от отношений между буквами
    for i, tau1 in enumerate(char_taus):
        for j, tau2 in enumerate(char_taus):
            if i >= j:
                continue
            ratio = tau1 / tau2 if tau2 != 0 else 1.0
            if 0.3 < ratio < 3.0:
                harmonic_tau = tau1 * ratio
                if 1.0 <= harmonic_tau <= 1000:
                    spectrum[harmonic_tau] = spectrum.get(harmonic_tau, 0) + 0.3
            ratio_inv = tau2 / tau1 if tau1 != 0 else 1.0
            if 0.3 < ratio_inv < 3.0:
                harmonic_tau = tau2 * ratio_inv
                if 1.0 <= harmonic_tau <= 1000:
                    spectrum[harmonic_tau] = spectrum.get(harmonic_tau, 0) + 0.3
    
    return spectrum


# ========== ВИХРЬ (слово) ==========
@dataclass
class Vortex:
    """Вихрь в поле H — слово как аккорд"""
    word: str
    spectrum: Dict[float, float] = field(default_factory=dict)
    amplitude: float = 0.5
    usage_count: int = 0
    last_used: Optional[datetime] = None
    created: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.spectrum:
            pass
    
    def get_dominant_tau(self) -> Optional[float]:
        if not self.spectrum:
            return None
        return max(self.spectrum.items(), key=lambda x: x[1])[0]
    
    def get_random_sentence(self) -> str:
        """Возвращает случайную фразу из контента (заглушка)"""
        return f"«{self.word}»"
    
    def update_spectrum(self, new_spectrum: Dict[float, float], weight: float = 0.3):
        for tau, amp in new_spectrum.items():
            old = self.spectrum.get(tau, 0)
            self.spectrum[tau] = old * 0.7 + amp * weight * 0.3
        
        if len(self.spectrum) > 20:
            sorted_items = sorted(self.spectrum.items(), key=lambda x: x[1], reverse=True)
            self.spectrum = dict(sorted_items[:20])
    
    def resonance_with(self, other: 'Vortex') -> float:
        if not self.spectrum or not other.spectrum:
            return 0.0
        common = 0.0
        for tau, amp1 in self.spectrum.items():
            amp2 = other.spectrum.get(tau, 0)
            if amp2 > 0:
                common += min(amp1, amp2)
        return common / (len(self.spectrum) + len(other.spectrum) - common + 1)
    
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
            "created": self.created.isoformat()
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
        return vortex


# ========== СПЕКТРАЛЬНАЯ МОДА (для ответов) ==========
@dataclass
class SpectralMode:
    """Слепок контента с координатами"""
    tau: float
    delta: float = 0.0
    theta: float = 0.0
    amplitude: float = 0.5
    content: str = ""
    trace_id: str = ""
    themes: List[str] = field(default_factory=list)
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
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
            "last_used": self.last_used.isoformat() if self.last_used else None
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
        return mode


# ========== ПОЛЕ H ==========
class FieldH:
    """Единое поле H — фрактальный алфавит"""
    
    def __init__(self):
        self.vortices: Dict[str, Vortex] = {}
        self.h_field: List[SpectralMode] = []
        self.char_tau: Dict[str, float] = {}
        self.next_tau = NEXT_SYMBOL_TAU
        
        self.focus = {
            "tau": 16.0,  # центр алфавита (о)
            "delta": 0.0,
            "theta": 0.0,
            "width": 1.0
        }
        
        self.word_freq = defaultdict(int)
        
        # Инициализация русского алфавита
        for ch, tau in RUSSIAN_ALPHABET.items():
            self.char_tau[ch] = tau
        
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
                tau = self.get_or_create_char_tau(ch)
                char_taus[ch] = tau
        
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
                    spectrum[harmonic] = spectrum.get(harmonic, 0) + 0.3
                ratio_inv = tau2 / tau1 if tau1 != 0 else 1.0
                if 0.3 < ratio_inv < 3.0:
                    harmonic = tau2 * ratio_inv
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
    
    # ========== ТРИ РЕЖИМА ОТВЕТА ==========
    
    def _resonance_between_spectra(self, spec1: Dict[float, float], spec2: Dict[float, float]) -> float:
        """Резонанс между двумя спектрами (0..1)"""
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
        """Резонанс между модой и вопросом (τ + спектр + ключевые слова)"""
        
        # 1. τ-резонанс
        dt = abs(mode.tau - self.focus["tau"])
        tau_res = 1.0 / (1.0 + dt)
        
        # 2. Спектральный резонанс
        mode_spectrum = self.phrase_spectrum(mode.content[:500])
        spec_res = self._resonance_between_spectra(mode_spectrum, question_spectrum)
        
        # 3. Тематический резонанс (по ключевым словам)
        question_words = set(re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', question_text.lower()))
        mode_words = set(re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', mode.content.lower()))
        
        if question_words and mode_words:
            common = len(question_words & mode_words)
            theme_res = common / max(len(question_words), 1)
        else:
            theme_res = 0.0
        
        # Комбинируем: τ (40%) + спектр (30%) + темы (30%)
        return tau_res * 0.4 + spec_res * 0.3 + theme_res * 0.3
    
    def _ask_clarification(self, text: str) -> str:
        """Запрашивает уточнение, когда нет резонанса"""
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        if words:
            return f"❓ Не совсем понимаю, что вы имеете в виду под «{words[0]}». Расскажите подробнее? (или дай пример)"
        return "❓ Не улавливаю резонанс. Уточните вопрос или дай пример."
    
    def _answer_with_suggestion(self, best_mode: SpectralMode, resonant_modes: List[SpectralMode]) -> str:
        """Отвечает и предлагает уточнить"""
        answer = best_mode.content[:400]
        
        # Предлагаем связанные темы
        themes = set()
        for m in resonant_modes[:3]:
            themes.update(m.themes)
        
        if themes:
            return f"{answer}\n\n💡 Возможно, вас заинтересует: {', '.join(list(themes)[:3])}?"
        return answer
    
    def _get_available_concepts(self) -> List[str]:
        """Возвращает понятия, которые уже есть в памяти (с высокой амплитудой)"""
        high_amp = [word for word, v in self.vortices.items() 
                    if v.amplitude > 0.5 and v.usage_count > 3]
        return high_amp[:10]
    
    def _get_phrase_for_word(self, word: str) -> str:
        """Находит фразу из контента, где встречается слово"""
        for mode in self.h_field:
            if word in mode.content.lower():
                sentences = re.split(r'[.!?]+', mode.content[:300])
                for s in sentences:
                    s = s.strip()
                    if len(s) > 20 and len(s) < 150:
                        return s
        return f"«{word}»"
    
    def _explain_with_known_concepts(self, new_word: str) -> Optional[SpectralMode]:
        """Объясняет новое слово через уже известные понятия (дед учит внука)"""
        available = self._get_available_concepts()
        if len(available) < 2:
            return None
        
        concept1 = available[0]
        concept2 = available[1]
        
        v1 = self.vortices.get(concept1)
        v2 = self.vortices.get(concept2)
        if not v1 or not v2:
            return None
        
        tau1 = v1.get_dominant_tau() or 16.0
        tau2 = v2.get_dominant_tau() or 16.0
        new_tau = (tau1 + tau2) / 2
        
        phrase1 = self._get_phrase_for_word(concept1)
        phrase2 = self._get_phrase_for_word(concept2)
        
        content = f"🧠 Это как {concept1} и {concept2} вместе.\n\n"
        content += f"📖 {concept1} — это {phrase1}\n\n"
        content += f"📖 {concept2} — это {phrase2}\n\n"
        content += f"✨ А {new_word} — это когда они работают вместе."
        
        mode = SpectralMode(
            tau=new_tau,
            amplitude=0.5,
            content=content,
            themes=["explanation", concept1, concept2, new_word],
            trace_id=f"explain_{new_word}_{int(time.time())}"
        )
        self.add_to_h_field(mode)
        self.add_word(new_word, {new_tau: 1.0}, weight=0.5)
        
        return mode
    
    def process(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Три режима ответа:
        1. Штамп (резонанс > 0.5 ИЛИ слово знакомое с высокой амплитудой)
        2. Фуркация (слово новое ИЛИ резонанс в среднем диапазоне)
        3. Уточнение (абстрактный вопрос ИЛИ резонанс < 0.2)
        """
        # Вычисляем спектр вопроса
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        
        # Обновляем фокус
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        
        if not self.h_field:
            return {"answer": "Поле H пусто. Добавьте тексты.", "error": True}
        
        # Извлекаем ключевое слово из вопроса
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', text.lower())
        key_word = words[0] if words else None
        
        # Проверяем, знакомое ли слово (высокая амплитуда и частое использование)
        is_familiar = False
        is_new = False
        if key_word and key_word in self.vortices:
            vortex = self.vortices[key_word]
            is_familiar = vortex.amplitude > 0.4 or vortex.usage_count > 5
            # Слово считается новым, если амплитуда низкая И мало использовалось
            is_new = vortex.amplitude < 0.3 and vortex.usage_count < 3
        else:
            is_new = key_word and key_word not in self.vortices
        
        # Вычисляем резонанс для всех мод (с учётом тематики)
        scored = []
        for mode in self.h_field:
            res = self._resonance_with_mode(mode, question_spectrum, text)
            scored.append((res, mode))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        best_resonance, best_mode = scored[0]
        
        # ПОРОГИ
        THRESHOLD_STAMP = 0.45
        THRESHOLD_FURCATION = 0.2
        
        # 1. ШТАМП — знакомое слово ИЛИ высокий резонанс
        if (is_familiar and best_resonance > 0.3) or best_resonance >= THRESHOLD_STAMP:
            best_mode.register_use()
            
            # Если слово есть в словаре, повышаем его амплитуду
            if key_word and key_word in self.vortices:
                self.vortices[key_word].register_use()
            
            return {
                "answer": best_mode.content[:500],
                "mode_used": best_mode.trace_id,
                "tau": best_mode.tau,
                "resonance": best_resonance,
                "mode_type": "stamp",
                "energy_cost": 0.1,
                "word": key_word,
                "familiar": is_familiar
            }
        
        # 2. ФУРКАЦИЯ — новое слово ИЛИ средний резонанс
        elif is_new or best_resonance >= THRESHOLD_FURCATION:
            # Если слово новое — объясняем через известные понятия
            if is_new and key_word:
                explanation = self._explain_with_known_concepts(key_word)
                if explanation:
                    return {
                        "answer": explanation.content,
                        "mode_used": explanation.trace_id,
                        "resonance": best_resonance,
                        "mode_type": "furcation_explanation",
                        "new_word": key_word,
                        "energy_cost": 0.5
                    }
            
            # Иначе — отвечаем с предложением
            resonant_modes = [m for r, m in scored[:3] if r > THRESHOLD_FURCATION]
            answer = self._answer_with_suggestion(best_mode, resonant_modes)
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
            return {
                "answer": self._ask_clarification(text),
                "mode_used": None,
                "resonance": best_resonance,
                "mode_type": "clarification",
                "energy_cost": 0.05
            }
    
    # ========== СОХРАНЕНИЕ И ЗАГРУЗКА ==========
    
    def save(self, filepath: str):
        data = {
            "id": self.id,
            "name": self.name,
            "char_tau": self.char_tau,
            "next_tau": self.next_tau,
            "vortices": {w: v.to_dict() for w, v in self.vortices.items()},
            "h_field": [m.to_dict() for m in self.h_field],
            "focus": self.focus,
            "word_freq": dict(self.word_freq)
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
        
        field = cls(
            id=data.get("id", "p016"),
            name=data.get("name", "VMMS Field")
        )
        
        # Восстанавливаем алфавит
        field.char_tau = data.get("char_tau", RUSSIAN_ALPHABET.copy())
        field.next_tau = data.get("next_tau", NEXT_SYMBOL_TAU)
        
        # Восстанавливаем вихри
        for word, vdata in data.get("vortices", {}).items():
            field.vortices[word] = Vortex.from_dict(vdata)
            field.word_freq[word] = data.get("word_freq", {}).get(word, 0)
        
        # Восстанавливаем моды
        field.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]
        
        # Восстанавливаем фокус
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
        
        # Создаём экземпляр с id и name
        field = cls(
            id=data.get("id", "p016"),
            name=data.get("name", "VMMS Field")
        )
        
        # Восстанавливаем алфавит
        field.char_tau = data.get("char_tau", RUSSIAN_ALPHABET.copy())
        field.next_tau = data.get("next_tau", NEXT_SYMBOL_TAU)
        
        # Восстанавливаем вихри
        for word, vdata in data.get("vortices", {}).items():
            field.vortices[word] = Vortex.from_dict(vdata)
            field.word_freq[word] = data.get("word_freq", {}).get(word, 0)
        
        # Восстанавливаем моды
        field.h_field = [SpectralMode.from_dict(m) for m in data.get("h_field", [])]
        
        # Восстанавливаем фокус
        field.focus = data.get("focus", {"tau": 16.0, "delta": 0.0, "theta": 0.0, "width": 1.0})
        
        return field