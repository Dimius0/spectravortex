"""
TextAnalyzer — извлечение τ и тем из текста через резонанс с полем H
"""

from typing import List


class TextAnalyzer:
    def __init__(self, personality):
        self.p = personality
    
    def extract_tau(self, text: str) -> float:
        """Извлекает τ из текста как взвешенное среднее резонансных мод"""
        if not self.p.h_field:
            # Эвристика для пустого поля
            length_factor = min(1.0, len(text) / 200)
            complexity = len(set(text.split())) / max(10, len(text.split()))
            return 5.0 + length_factor * 2 + complexity * 1.5
        
        # Простой эмбеддинг на основе частот букв
        text_embedding = self._simple_embed(text)
        
        total_weight = 0.0
        weighted_tau = 0.0
        
        for mode in self.p.h_field:
            mode_embedding = self._simple_embed(mode.content)
            semantic = self._cosine_similarity(text_embedding, mode_embedding)
            spectral = self.p._resonance(mode.tau, 5.0)
            combined = semantic * 0.6 + spectral * 0.4
            
            weighted_tau += mode.tau * combined
            total_weight += combined
        
        if total_weight > 0:
            result = weighted_tau / total_weight
            return max(3.0, min(9.0, result))
        
        return 5.0
    
    def extract_themes(self, text: str) -> List[str]:
        """Извлекает темы из текста через ключевые слова"""
        themes = []
        text_lower = text.lower()
        
        theme_keywords = {
            "physics": ["physics", "matter", "space", "particle", "field", "quantum", "∇⁴ψ", "vortex", "energy"],
            "alchemy": ["alchemy", "sulfur", "mercury", "salt", "transformation", "philosopher", "stone"],
            "consciousness": ["consciousness", "mind", "awareness", "self", "thought", "think", "experience"],
            "poetry": ["poetry", "poem", "verse", "rhythm", "metaphor", "beauty", "rhyme", "dance"],
            "dialogue": ["dialogue", "question", "answer", "learn", "teach", "grandson", "ask", "reply"],
            "memory": ["memory", "remember", "recall", "past", "history", "store", "forget"],
            "evolution": ["evolution", "grow", "furcation", "branch", "emerge", "born", "develop", "change"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(kw in text_lower for kw in keywords):
                themes.append(theme)
        
        return themes[:5]
    
    def _simple_embed(self, text: str) -> List[float]:
        """Простой эмбеддинг на основе частот букв"""
        freq = [0] * 26
        for c in text.lower():
            if 'a' <= c <= 'z':
                freq[ord(c) - ord('a')] += 1
        total = sum(freq)
        if total > 0:
            freq = [f / total for f in freq]
        return freq
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot / (norm_a * norm_b)