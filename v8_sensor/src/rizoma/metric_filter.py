"""
Metric Filter — автоопределение контекста и адаптивный ритм
Версия 1.6 — финальная: принудительное подавление ложной музыки
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ContextProfile:
    """Профиль контекста для метрического фильтра"""
    context_type: str  # poetry, dialogue, science, code, music, prose
    meter: str         # iambic_4, trochee_4, free, prose, indent, 4/4, 3/4
    strictness: float  # 0.0-1.0
    rhyme: str         # cross, paired, none
    confidence: float  # 0.0-1.0
    bpm: int = 120     # для музыки
    time_signature: str = "4/4"  # для музыки


class MetricFilter:
    """
    Автоопределение контекста и адаптивная подстройка ритма
    Поддерживает: поэзию, диалог, науку, код, музыку
    """
    
    def __init__(self):
        self.context_history: List[Tuple[str, float]] = []
        self.last_profile: Optional[ContextProfile] = None
        
        self._context_keywords = {
            "poetry": [
                "стих", "поэзия", "рифма", "метр", "ямб", "хорей", "поэт",
                "verse", "poem", "rhyme", "meter", "iamb", "poetry"
            ],
            "dialogue": [
                "сказал", "спросил", "ответил", "—", "said", "asked",
                "replied", "говорит", "молвил"
            ],
            "science": [
                "исследование", "гипотеза", "данные", "метод", "анализ",
                "research", "hypothesis", "data", "method", "analysis",
                "эксперимент", "теорема", "формула", "уравнение", "∇⁴ψ",
                "архитектура", "модель"
            ],
            "code": [
                "def ", "class ", "import ", "function", "var ", "let ",
                "```", "function(", "return"
            ],
            "music": [
                "нота", "аккорд", "мелодия", "ритм", "темп", "так", "bpm",
                "note", "chord", "melody", "rhythm", "tempo", "beat",
                "до", "ре", "ми", "фа", "соль", "ля", "си",
                "мажор", "минор", "♩", "♪", "♫", "4/4", "3/4", "6/8", "waltz"
            ]
        }
    
    def detect_context(self, text: str) -> ContextProfile:
        """Автоопределение контекста по тексту"""
        
        context_scores = self._score_by_keywords(text)
        structure_scores = self._score_by_structure(text)
        rhythm_info = self._analyze_rhythm(text)
        music_info = self._analyze_music(text)
        
        final_scores = {}
        for ctx in context_scores:
            final_scores[ctx] = context_scores[ctx] * 0.5 + structure_scores.get(ctx, 0) * 0.3
            if rhythm_info and ctx == "poetry":
                final_scores[ctx] += rhythm_info.get("stability", 0) * 0.2
            if music_info and ctx == "music":
                final_scores[ctx] += music_info.get("confidence", 0) * 0.3
        
        if not final_scores:
            return ContextProfile("prose", "free", 0.3, "none", 0.5)
        
        best_context = max(final_scores, key=final_scores.get)
        confidence = final_scores[best_context]
        
        # ========== ПРИНУДИТЕЛЬНОЕ ПОДАВЛЕНИЕ ЛОЖНОЙ МУЗЫКИ ==========
        if best_context == "music":
            music_markers_check = ["нота", "аккорд", "bpm", "♩", "♪", "♫", "4/4", "3/4", "waltz"]
            has_real_music = any(m in text.lower() for m in music_markers_check)
            if not has_real_music:
                # Перенаправляем в науку или прозу
                if any(k in text.lower() for k in ["архитектура", "модель", "исследование", "∇⁴ψ", "∇⁴ψ", "эксперимент"]):
                    best_context = "science"
                else:
                    best_context = "prose"
                confidence = 0.3
        # ==============================================================
        
        meter = "free"
        rhyme = "none"
        strictness = 0.3
        bpm = 120
        time_signature = "4/4"
        
        if best_context == "poetry" and rhythm_info:
            meter = rhythm_info.get("dominant_meter", "free")
            rhyme = rhythm_info.get("rhyme_type", "none")
            stability = rhythm_info.get("stability", 0.5)
            strictness = min(0.9, stability * 0.8 + 0.2)
        elif best_context == "music" and music_info:
            meter = music_info.get("time_signature", "4/4")
            bpm = music_info.get("bpm", 120)
            strictness = 0.7
        elif best_context == "dialogue":
            strictness = 0.2
        elif best_context == "science":
            strictness = 0.6
        elif best_context == "code":
            strictness = 0.95
            meter = "indent"
        
        return ContextProfile(
            context_type=best_context,
            meter=meter,
            strictness=strictness,
            rhyme=rhyme,
            confidence=confidence,
            bpm=bpm,
            time_signature=time_signature
        )
    
    def _score_by_keywords(self, text: str) -> Dict[str, float]:
        text_lower = text.lower()
        scores = {}
        
        for context, keywords in self._context_keywords.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count > 0:
                scores[context] = min(1.0, count / 5)
            else:
                scores[context] = 0.0
        
        return scores
    
    def _score_by_structure(self, text: str) -> Dict[str, float]:
        scores = {"poetry": 0.0, "dialogue": 0.0, "code": 0.0, "science": 0.0, "music": 0.0}
        
        lines = text.split('\n')
        lines = [l.strip() for l in lines if l.strip()]
        
        if not lines:
            return scores
        
        # Поэзия — повышен порог
        avg_line_len = sum(len(l) for l in lines) / len(lines)
        if avg_line_len < 40 and len(lines) > 2:
            rhythm_stable = self._check_rhythm_stability(lines)
            if rhythm_stable > 0.6:
                scores["poetry"] = rhythm_stable
        
        # Диалог — усилен
        dialogue_markers = ["—", "«", "»", "сказал", "спросил", "ответил", "?"]
        dialogue_count = sum(1 for m in dialogue_markers if m in text)
        if dialogue_count > 3:
            scores["dialogue"] = min(0.8, dialogue_count / 10)
        if "—" in text and text.count("\n") > 2:
            scores["dialogue"] += 0.4
        if "?" in text:
            scores["dialogue"] += 0.3
        scores["dialogue"] = min(1.0, scores["dialogue"])
        
        # Код
        if "def " in text or "class " in text or "import " in text:
            scores["code"] = 0.8
        elif "function" in text and "{" in text:
            scores["code"] = 0.6
        
        # Наука
        science_score = 0
        if "∇" in text or "∫" in text or "∑" in text:
            science_score = 0.8
        if "рис." in text.lower() or "табл." in text.lower():
            science_score += 0.3
        if "экспериментальные данные" in text.lower():
            science_score += 0.4
        if "архитектура" in text.lower() or "модель" in text.lower():
            science_score += 0.2
        scores["science"] = min(1.0, science_score)
        
        # Музыка — только явные маркеры
        music_markers = ["нота", "аккорд", "bpm", "beat", "♩", "♪", "♫", "4/4", "3/4", "6/8", "waltz"]
        music_score = sum(1 for m in music_markers if m in text.lower())
        if music_score >= 1:
            scores["music"] = 0.5 + music_score * 0.1
        
        return scores
    
    def _analyze_music(self, text: str) -> Optional[Dict]:
        """Анализирует музыкальные параметры — только если есть явные маркеры"""
        text_lower = text.lower()
        
        explicit_markers = ["нота", "аккорд", "bpm", "beat", "♩", "♪", "♫", "4/4", "3/4", "6/8", "waltz"]
        has_explicit = any(m in text_lower for m in explicit_markers)
        
        if not has_explicit:
            return None
        
        time_signature = "4/4"
        if "3/4" in text_lower or "waltz" in text_lower:
            time_signature = "3/4"
        elif "6/8" in text_lower:
            time_signature = "6/8"
        
        bpm = 120
        match = re.search(r'(\d{2,3})\s*bpm', text_lower)
        if match:
            bpm = int(match.group(1))
        
        confidence = 0.3
        if time_signature != "4/4":
            confidence += 0.3
        if bpm != 120:
            confidence += 0.2
        if any(n in text_lower for n in ["до", "ре", "ми", "фа", "соль", "ля", "си"]):
            confidence += 0.2
        
        return {
            "time_signature": time_signature,
            "bpm": bpm,
            "confidence": min(1.0, confidence)
        }
    
    def _analyze_rhythm(self, text: str) -> Optional[Dict]:
        lines = text.split('\n')
        lines = [l.strip() for l in lines if l.strip() and len(l) > 10]
        
        if len(lines) < 2:
            return None
        
        meters = []
        for line in lines:
            syllables = self._count_syllables_rough(line)
            if syllables in [7, 8, 9]:
                meters.append("iambic_4")
            elif syllables in [5, 6]:
                meters.append("trochee_3")
            elif syllables in [10, 11, 12]:
                meters.append("iambic_5")
            else:
                meters.append("free")
        
        if not meters:
            return None
        
        dominant = max(set(meters), key=meters.count)
        stability = meters.count(dominant) / len(meters)
        rhyme_type = self._detect_rhyme_type(lines)
        
        return {
            "dominant_meter": dominant,
            "stability": stability,
            "rhyme_type": rhyme_type
        }
    
    def _check_rhythm_stability(self, lines: List[str]) -> float:
        lengths = [len(l) for l in lines]
        if not lengths:
            return 0.0
        
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        stability = max(0.0, 1.0 - variance / 200)
        return min(1.0, stability)
    
    def _count_syllables_rough(self, text: str) -> int:
        vowels = "аеёиоуыэюяaeiou"
        count = sum(1 for c in text.lower() if c in vowels)
        return max(1, count)
    
    def _detect_rhyme_type(self, lines: List[str]) -> str:
        if len(lines) < 4:
            return "none"
        
        last_words = []
        for line in lines[:4]:
            words = line.split()
            if words:
                last_words.append(words[-1].lower())
        
        if len(last_words) < 4:
            return "none"
        
        if (last_words[0][-2:] == last_words[2][-2:] and 
            last_words[1][-2:] == last_words[3][-2:]):
            return "cross"
        
        if (last_words[0][-2:] == last_words[1][-2:] and 
            last_words[2][-2:] == last_words[3][-2:]):
            return "paired"
        
        return "none"
    
    def apply_filter(self, text: str, profile: ContextProfile = None) -> str:
        if profile is None:
            profile = self.detect_context(text)
        
        self.context_history.append((profile.context_type, profile.confidence))
        if len(self.context_history) > 10:
            self.context_history.pop(0)
        
        if profile.context_type == "poetry":
            return self._filter_poetry(text, profile)
        elif profile.context_type == "music":
            return self._filter_music(text, profile)
        elif profile.context_type == "dialogue":
            return self._filter_dialogue(text, profile)
        elif profile.context_type == "code":
            return self._filter_code(text, profile)
        elif profile.context_type == "science":
            return self._filter_science(text, profile)
        
        return text
    
    def _filter_poetry(self, text: str, profile: ContextProfile) -> str:
        return text
    
    def _filter_music(self, text: str, profile: ContextProfile) -> str:
        """Фильтр для музыки — добавление ритмической структуры"""
        return f"[{profile.time_signature}, {profile.bpm} BPM] {text}"
    
    def _filter_dialogue(self, text: str, profile: ContextProfile) -> str:
        return text
    
    def _filter_code(self, text: str, profile: ContextProfile) -> str:
        return text
    
    def _filter_science(self, text: str, profile: ContextProfile) -> str:
        return text
    
    def get_adaptive_strictness(self) -> float:
        if not self.context_history:
            return 0.5
        avg_confidence = sum(c for _, c in self.context_history[-5:]) / 5
        return min(0.9, 0.3 + avg_confidence * 0.6)