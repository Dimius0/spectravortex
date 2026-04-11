"""
Personality — ядро личности, поле H
Версия 11.0 — фрактальный алфавит, буквы как ноты, слова как аккорды
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

# Следующий доступный τ для новых символов
NEXT_SYMBOL_TAU = 34

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_char_tau(char: str) -> Optional[float]:
    """Возвращает τ символа (буквы, цифры, знака)"""
    char_lower = char.lower()
    
    # Русский алфавит
    if char_lower in RUSSIAN_ALPHABET:
        return RUSSIAN_ALPHABET[char_lower]
    
    # Латинские буквы — временно, пока не добавим в поле
    # В реальности они получат τ при первом появлении
    return None

def word_spectrum_from_chars(word: str, char_tau_map: Dict[str, float]) -> Dict[float, float]:
    """
    Вычисляет спектр слова из τ его букв.
    Слово — это аккорд. Спектр = τ букв + гармоники от отношений.
    """
    spectrum = {}
    
    # Получаем τ всех букв слова
    char_taus = []
    for ch in word.lower():
        if ch in char_tau_map:
            tau = char_tau_map[ch]
            char_taus.append(tau)
            spectrum[tau] = spectrum.get(tau, 0) + 1.0
    
    if not char_taus:
        return spectrum
    
    # Нормализуем амплитуды
    max_amp = max(spectrum.values()) if spectrum else 1.0
    for tau in spectrum:
        spectrum[tau] /= max_amp
    
    # Добавляем гармоники из отношений между буквами
    for i, tau1 in enumerate(char_taus):
        for j, tau2 in enumerate(char_taus):
            if i >= j:
                continue
            
            # Отношение частот
            ratio = tau1 / tau2 if tau2 != 0 else 1.0
            if 0.3 < ratio < 3.0:
                harmonic_tau = tau1 * ratio
                if 1.0 <= harmonic_tau <= 1000:  # разумный диапазон
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
    spectrum: Dict[float, float] = field(default_factory=dict)  # τ → амплитуда
    amplitude: float = 0.5
    usage_count: int = 0
    last_used: Optional[datetime] = None
    created: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.spectrum:
            # Пустой спектр — слово ещё не проявлено
            pass
    
    def get_dominant_tau(self) -> Optional[float]:
        """Возвращает доминирующую τ или None"""
        if not self.spectrum:
            return None
        return max(self.spectrum.items(), key=lambda x: x[1])[0]
    
    def update_spectrum(self, new_spectrum: Dict[float, float], weight: float = 0.3):
        """Обновляет спектр слова новыми данными"""
        for tau, amp in new_spectrum.items():
            old = self.spectrum.get(tau, 0)
            self.spectrum[tau] = old * 0.7 + amp * weight * 0.3
        
        # Ограничиваем размер спектра
        if len(self.spectrum) > 20:
            sorted_items = sorted(self.spectrum.items(), key=lambda x: x[1], reverse=True)
            self.spectrum = dict(sorted_items[:20])
    
    def resonance_with(self, other: 'Vortex') -> float:
        """Резонанс между двумя словами через их спектры"""
        if not self.spectrum or not other.spectrum:
            return 0.0
        
        # Пересечение спектров
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
        self.char_tau: Dict[str, float] = {}  # символ → τ
        self.next_tau = NEXT_SYMBOL_TAU
        
        self.focus = {
            "tau": 1.0,
            "delta": 0.0,
            "theta": 0.0,
            "width": 1.0
        }
        
        self.word_freq = defaultdict(int)
        self.metric_filter = None
        
        # Инициализация русского алфавита
        for ch, tau in RUSSIAN_ALPHABET.items():
            self.char_tau[ch] = tau
        
        self.id = "field"
        self.name = "Field H"
    
    def get_or_create_char_tau(self, char: str) -> float:
        """Возвращает τ символа, создаёт новый если нет"""
        char_lower = char.lower()
        
        if char_lower in self.char_tau:
            return self.char_tau[char_lower]
        
        # Новый символ — новая нота
        new_tau = self.next_tau
        self.next_tau += 1
        self.char_tau[char_lower] = new_tau
        print(f" 🎵 Новый символ '{char}' → τ={new_tau}")
        return new_tau
    
    def get_word_spectrum(self, word: str) -> Dict[float, float]:
        """Вычисляет спектр слова из его букв"""
        if not word:
            return {}
        
        # Собираем τ букв
        char_taus = {}
        for ch in word.lower():
            if ch in self.char_tau:
                tau = self.char_tau[ch]
                char_taus[ch] = tau
            else:
                # Новая буква — создаём
                tau = self.get_or_create_char_tau(ch)
                char_taus[ch] = tau
        
        # Вычисляем спектр слова
        spectrum = {}
        
        # Базовые частоты букв
        for ch, tau in char_taus.items():
            spectrum[tau] = spectrum.get(tau, 0) + 1.0
        
        # Гармоники от отношений
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
        
        # Нормализация
        if spectrum:
            max_amp = max(spectrum.values())
            for tau in spectrum:
                spectrum[tau] /= max_amp
        
        return spectrum
    
    def add_word(self, word: str, context_spectrum: Dict[float, float] = None, weight: float = 0.3):
        """Добавляет или обновляет слово в поле"""
        word_lower = word.lower()
        
        # Вычисляем спектр слова из букв
        word_spectrum = self.get_word_spectrum(word)
        
        # Если есть контекст — смешиваем
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
        """Вычисляет спектр фразы как сумму спектров слов"""
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]+\b', text.lower())
        result = {}
        
        for w in words:
            if w in self.vortices:
                vortex = self.vortices[w]
                for tau, amp in vortex.spectrum.items():
                    result[tau] = result.get(tau, 0) + amp
            else:
                # Новое слово — вычисляем спектр из букв
                word_spectrum = self.get_word_spectrum(w)
                for tau, amp in word_spectrum.items():
                    result[tau] = result.get(tau, 0) + amp
        
        # Нормализация
        if result:
            max_amp = max(result.values())
            for tau in result:
                result[tau] /= max_amp
        
        return result
    
    def get_dominant_tau(self, spectrum: Dict[float, float]) -> Optional[float]:
        """Возвращает доминирующую τ спектра"""
        if not spectrum:
            return None
        return max(spectrum.items(), key=lambda x: x[1])[0]
    
    def add_to_h_field(self, mode: SpectralMode):
        """Добавляет моду с контентом"""
        # Проверяем на похожую моду
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
        
        # Обновляем слова из контента
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]+\b', mode.content.lower())
        for w in words:
            self.add_word(w, {mode.tau: 1.0}, weight=0.1)
    
    def process(self, text: str) -> Dict[str, Any]:
        """Обрабатывает вопрос и возвращает ответ"""
        # Спектр вопроса
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 1.0
        
        # Обновляем фокус
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        
        if not self.h_field:
            return {"answer": "Поле H пусто. Добавьте тексты.", "error": True}
        
        # Ищем моду с ближайшей τ
        best_mode = min(
            self.h_field,
            key=lambda m: abs(m.tau - self.focus["tau"])
        )
        
        best_mode.register_use()
        
        return {
            "answer": best_mode.content[:500],
            "mode_used": best_mode.trace_id,
            "tau": best_mode.tau,
            "question_tau": question_tau,
            "spectrum_size": len(question_spectrum)
        }
    
    def save(self, filepath: str):
        """Сохраняет поле"""
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
        """Загружает поле"""
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
        field.focus = data.get("focus", {"tau": 1.0, "delta": 0.0, "theta": 0.0, "width": 1.0})
        
        return field


# ========== ДЛЯ СОВМЕСТИМОСТИ ==========
class Personality(FieldH):
    def __init__(self, id: str, name: str, tau: float = 1.0, k: int = 1):
        super().__init__()
        self.id = id
        self.name = name
        self.k = k
        self.bridge = None
    
    @classmethod
    def load(cls, filepath: str):
        return super().load(filepath)