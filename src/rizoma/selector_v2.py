"""
Selector V2 — выбиратор сущностей с комбинированным резонансом
Версия 2.0 — с эмбеддингами
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from .resonance_v2 import CombinedResonator
from .embedder import Embedder
from .antitroll import Antitroll


class StimulusAnalyzerV2:
    """Анализатор стимулов — извлекает теги, профессию, τ из текста"""
    
    def __init__(self, embedder: Embedder = None):
        self.embedder = embedder or Embedder()
        self.tag_map = {
            "plumbing": ["plumbing", "pipe", "кран", "сантехник", "water", "leak"],
            "engineering": ["engineering", "engineer", "hardware", "architecture", "boris", "design"],
            "programming": ["programming", "programmer", "code", "algorithm", "software", "bug"],
            "philosophy": ["philosophy", "philosopher", "meaning", "being", "consciousness"],
            "astronomy": ["astronomy", "astronomer", "space", "star", "cosmos"],
            "chemistry": ["chemistry", "chemist", "reaction", "molecule"],
            "physics": ["physics", "physicist", "vortex", "∇", "field"],
            "psychology": ["psychology", "psychologist", "mind", "behavior"],
            "poetry": ["poetry", "poet", "verse", "rhyme"],
            "cooking": ["cooking", "chef", "food", "recipe"],
            "electrical": ["electrical", "electrician", "wire", "circuit"],
            "diplomacy": ["diplomacy", "diplomat", "negotiation", "agreement"],
            "memory": ["memory", "ram", "storage", "trace", "память"],
            "resources": ["resources", "constraints", "limited", "hardware"],
            "architecture": ["architecture", "design", "structure", "system"],
            "vmms": ["vmms", "vortex", "∇⁴ψ", "biharmonic"]
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Анализирует текст и возвращает стимул"""
        text_lower = text.lower()
        
        tags = self._extract_tags(text_lower)
        profession = self._guess_profession(text_lower)
        tau = self._guess_tau(text_lower)
        emotion = self._guess_emotion(text_lower)
        complexity = self._guess_complexity(text_lower)
        embedding = self.embedder.encode(text).tolist()
        
        return {
            "text": text,
            "tags": tags,
            "profession": profession,
            "tau": tau,
            "emotion": emotion,
            "complexity": complexity,
            "themes": tags,
            "embedding": embedding
        }
    
    def _extract_tags(self, text: str) -> List[str]:
        tags = []
        for tag, keywords in self.tag_map.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)
        return tags[:5]
    
    def _guess_profession(self, text: str) -> Optional[str]:
        for prof, keywords in self.tag_map.items():
            if any(kw in text for kw in keywords):
                return prof
        return None
    
    def _guess_tau(self, text: str) -> float:
        length_factor = min(1.0, len(text) / 200)
        complexity_factor = len(set(text.split())) / max(10, len(text.split()))
        return 5.0 + length_factor * 2 + complexity_factor * 1.5
    
    def _guess_emotion(self, text: str) -> float:
        positive = ["good", "great", "nice", "cool", "awesome", "хорошо", "отлично", "interesting"]
        negative = ["bad", "wrong", "error", "problem", "плохо", "ошибка", "fail"]
        score = 0.0
        for w in positive:
            if w in text:
                score += 0.2
        for w in negative:
            if w in text:
                score -= 0.2
        return max(-1.0, min(1.0, score))
    
    def _guess_complexity(self, text: str) -> int:
        words = text.split()
        if len(words) < 5:
            return 1
        if len(words) < 20:
            return 2
        if len(words) < 50:
            return 3
        return 4


class SelectorV2:
    """
    Выбиратор V2 — определяет, какая сущность будет отвечать.
    Использует комбинированный резонанс (спектральный + семантический).
    """
    
    def __init__(self, personality, decay=0.7, threshold=0.5,
                 spectral_weight=0.5, semantic_weight=0.5):
        self.p = personality
        self.decay = decay
        self.threshold = threshold
        
        self.weights: Dict[str, float] = {}
        for eid in self.p.entities:
            self.weights[eid] = 0.0
        
        self.context_entity: Optional[str] = None
        self.context_topic: Optional[str] = None
        
        self.analyzer = StimulusAnalyzerV2()
        self.resonator = CombinedResonator(spectral_weight, semantic_weight)
        self.antitroll = Antitroll()
        
        self.history: List[Dict] = []
    
    def _entity_resonance(self, entity, stimulus: Dict) -> float:
        """Вычисляет комбинированный резонанс между сущностью и стимулом"""
        total = 0.0
        
        # 1. Профессиональный резонанс
        if stimulus.get('profession') and entity.profession:
            if stimulus['profession'] == entity.profession:
                total += 5.0
            elif any(tag in entity.profession for tag in stimulus.get('tags', [])):
                total += 3.0
        
        # 2. Комбинированный резонанс (спектральный + семантический)
        if stimulus.get('tau'):
            emb1 = np.array(entity.embedding) if hasattr(entity, 'embedding') and entity.embedding else None
            emb2 = np.array(stimulus.get('embedding')) if stimulus.get('embedding') else None
            
            combined = self.resonator.resonate(
                entity.tau, stimulus['tau'],
                emb1, emb2
            )
            total += combined * 2.0
        
        # 3. Резонанс по тегам
        for tag in stimulus.get('tags', []):
            if tag in entity.name.lower():
                total += 2.0
            if tag in entity.profession.lower():
                total += 2.0
            if tag in str(entity.defects).lower():
                total += 1.0
        
        # 4. Бонус за опыт
        if hasattr(entity, 'experience') and entity.experience > 0:
            total += entity.experience * 0.1
        
        # 5. Бонус за контекст
        if self.context_entity == entity.entity_id:
            total += 0.2
        
        # 6. Бонус за ту же тему
        if self.context_topic and self.context_topic == stimulus.get('profession'):
            total += 0.2
        
        return total
    
    def process(self, raw_input: str, author_id: str = "default") -> Dict[str, Any]:
        """Основной метод обработки входящего сообщения"""
        is_blocked, message = self.antitroll.check(author_id, raw_input)
        if is_blocked:
            return {
                'stimulus': None,
                'best_entity': None,
                'best_weight': 0,
                'above_threshold': False,
                'all_weights': {},
                'troll_blocked': True,
                'troll_message': message
            }
        
        stimulus = self.analyzer.analyze(raw_input)
        
        instant_resonance = {}
        for eid, entity in self.p.entities.items():
            inst = self._entity_resonance(entity, stimulus)
            instant_resonance[eid] = inst
        
        for eid in self.weights:
            self.weights[eid] = self.weights[eid] * self.decay + instant_resonance[eid] * (1 - self.decay)
        
        if self.weights:
            best_eid = max(self.weights, key=lambda eid: self.weights[eid])
            best_weight = self.weights[best_eid]
        else:
            best_eid = None
            best_weight = 0.0
        
        above_threshold = best_weight > self.threshold if best_eid else False
        
        if above_threshold and best_eid:
            self.context_entity = best_eid
            if stimulus.get('profession'):
                self.context_topic = stimulus['profession']
        
        self.history.append({
            'input': raw_input[:100],
            'stimulus': stimulus,
            'weights': dict(self.weights),
            'best_entity': best_eid,
            'best_weight': best_weight,
            'above_threshold': above_threshold,
            'timestamp': time.time()
        })
        
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        return {
            'stimulus': stimulus,
            'best_entity': best_eid,
            'best_weight': best_weight,
            'above_threshold': above_threshold,
            'all_weights': dict(self.weights),
            'troll_blocked': False,
            'troll_message': None
        }
    
    def clarify(self, stimulus: Dict) -> str:
        profession = stimulus.get('profession')
        if profession:
            return f"Interesting question. Let me think... Maybe {profession} could answer, but I'm not sure."
        return "Interesting question. Let me think..."
    
    def get_state(self) -> Dict:
        return {
            'weights': dict(self.weights),
            'context_entity': self.context_entity,
            'context_topic': self.context_topic,
            'decay': self.decay,
            'threshold': self.threshold,
            'history_length': len(self.history)
        }