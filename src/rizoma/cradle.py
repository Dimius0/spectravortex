"""
Загрузчик «Колыбель» — превращает сырые тексты в спектральные моды памяти.
Версия 2.0 — спектральный анализ, поле H.
"""

import os
import re
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# для анализа тональности (заглушка, позже подключим нормальную модель)
try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    print("⚠️  TextBlob не установлен. Эмоциональный анализ будет заглушкой.")
    print("   Установите: pip install textblob")

# импортируем наши структуры
from .personality import SpectralMode, MemoryAccess, Personality


class CradleLoader:
    """
    Загрузчик контента для цифровой личности.
    Превращает сырые тексты в спектральные моды поля H.
    """
    
    def __init__(self, personality: Personality):
        self.personality = personality
        self.known_people = self._extract_known_people()
        
    def _extract_known_people(self) -> List[str]:
        """Извлекает список известных людей из связей личности"""
        if hasattr(self.personality, 'relations'):
            return list(self.personality.relations.keys())
        return []
    
    def _simple_sentiment(self, text: str) -> float:
        """
        Простейший анализ тональности.
        Позже заменить на нормальную модель.
        """
        if HAS_TEXTBLOB:
            blob = TextBlob(text)
            return blob.sentiment.polarity  # от -1 до 1
        
        # Простая эвристика
        positive = ["good", "great", "nice", "cool", "awesome", "хорошо", "отлично"]
        negative = ["bad", "wrong", "error", "problem", "плохо", "ошибка"]
        
        text_lower = text.lower()
        score = 0.0
        for w in positive:
            if w in text_lower:
                score += 0.2
        for w in negative:
            if w in text_lower:
                score -= 0.2
        return max(-1.0, min(1.0, score))
    
    def _compute_tau(self, text: str, trace_type: str, themes: List[str]) -> float:
        """
        Вычисляет τ (топологический заряд) для текста.
        """
        base_tau = {
            'discovery': 5.5,
            'alchemy': 6.5,
            'prediction': 7.0,
            'memory': 5.0,
            'dialog': 5.0
        }.get(trace_type, 5.0)
        
        # Коррекция по длине
        length_factor = min(0.5, len(text) / 1000)
        base_tau += length_factor
        
        # Коррекция по темам
        theme_adjust = 0.0
        for theme in themes:
            if theme in ['VMMS', 'monism', 'priority']:
                theme_adjust -= 0.2
            if theme in ['lipzik', 'formula', 'prediction']:
                theme_adjust += 0.2
            if theme in ['vortex', 'alchemy']:
                theme_adjust += 0.1
        
        tau = base_tau + theme_adjust
        return max(3.0, min(9.0, tau))
    
    def _extract_themes(self, text: str) -> List[str]:
        """Извлекает темы из текста"""
        keywords = [
            "vmms", "vortex", "furcation", "topological", "spacetime", "model",
            "memory", "resonance", "spectral", "harmonic", "field",
            "alchemy", "lipzik", "boris", "moose"
        ]
        found = []
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                found.append(kw.capitalize())
        if not found:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text_lower)
            from collections import Counter
            counter = Counter(words)
            found = [word.capitalize() for word, count in counter.most_common(3)]
        return found
    
    def text_to_mode(self, content: str, trace_type: str = "memory",
                     themes: List[str] = None, emotion: float = None,
                     source: str = None) -> SpectralMode:
        """
        Превращает текст в спектральную моду поля H.
        """
        if themes is None:
            themes = self._extract_themes(content)
        
        if emotion is None:
            emotion = self._simple_sentiment(content)
        
        tau = self._compute_tau(content, trace_type, themes)
        
        trace_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        mode = SpectralMode(
            tau=tau,
            amplitude=0.5 + abs(emotion) * 0.3,
            content=content,
            trace_id=f"mode_{trace_id}",
            themes=themes,
            trace_type=trace_type
        )
        
        if source:
            mode.content = f"[{source}] {mode.content}"
        
        return mode
    
    def load_text(self, content: str, trace_type: str = "memory",
                  themes: List[str] = None, emotion: float = None,
                  source: str = None) -> SpectralMode:
        """
        Загружает текст в поле H личности.
        """
        mode = self.text_to_mode(content, trace_type, themes, emotion, source)
        self.personality.add_to_h_field(mode)
        return mode
    
    def load_texts_from_folder(self, folder_path: str,
                                trace_type: str = "memory",
                                pattern: str = "*.txt") -> List[SpectralMode]:
        """
        Загружает все тексты из папки.
        """
        modes = []
        folder = Path(folder_path)
        if not folder.exists():
            print(f"⚠️ Папка не найдена: {folder_path}")
            return modes
        
        for file_path in folder.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                mode = self.load_text(
                    content=content,
                    trace_type=trace_type,
                    source=file_path.name
                )
                modes.append(mode)
                print(f"  ✅ Загружен: {file_path.name}")
            except Exception as e:
                print(f"  ⚠️ Ошибка загрузки {file_path.name}: {e}")
        
        return modes


# для обратной совместимости
def load_texts_to_personality(personality: Personality, folder_path: str,
                               trace_type: str = "memory") -> List[SpectralMode]:
    """
    Загружает тексты из папки в личность.
    """
    loader = CradleLoader(personality)
    return loader.load_texts_from_folder(folder_path, trace_type)