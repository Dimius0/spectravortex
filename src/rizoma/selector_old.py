"""
Selector — выбиратор сущностей с спектральным резонансом и памятью
"""

import math
import time
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from .antitroll import Antitroll


class SpectralResonator:
    """Спектральный резонатор с гармониками и адаптацией"""
    
    def __init__(self):
        # Начальные веса гармоник
        self.harmonics = {
            1.0: 1.0,   # основная
            2.0: 0.6,   # октава вверх
            0.5: 0.5,   # октава вниз
            3.0: 0.4,   # квинта через октаву
            1/3: 0.3,
            4.0: 0.2,
            0.25: 0.15
        }
        
        # Статистика успешных резонансов
        self.hit_count = {h: 0 for h in self.harmonics}
        self.total_count = 0
    
    def resonate(self, tau1: float, tau2: float) -> float:
        """Вычисляет спектральный резонанс между двумя τ"""
        total = 0.0
        best_harmonic = None
        best_resonance = 0
        
        for harmonic, weight in self.harmonics.items():
            harmonic_tau = tau1 * harmonic
            diff = abs(harmonic_tau - tau2)
            resonance = 1.0 / (1.0 + diff)
            
            if resonance > best_resonance:
                best_resonance = resonance
                best_harmonic = harmonic
            
            total += resonance * weight
        
        if best_resonance > 0.7 and best_harmonic:
            self.hit_count[best_harmonic] += 1
            self.total_count += 1
        
        if self.total_count % 100 == 0:
            self._adapt_weights()
        
        return total
    
    def _adapt_weights(self):
        """Адаптирует веса гармоник под статистику"""
        print("🔄 Адаптация гармоник...")
        total_hits = sum(self.hit_count.values())
        if total_hits == 0:
            return
        
        for h in self.harmonics:
            self.harmonics[h] = self.hit_count[h] / total_hits * len(self.harmonics)
        
        old_sum = sum(self.harmonics.values())
        if old_sum > 0:
            factor = len(self.harmonics) / old_sum
            for h in self.harmonics:
                self.harmonics[h] *= factor
        
        print(f"   Новые веса: {self.harmonics}")
    
    def resonate_with_memory(self, entity_tau: float, memory) -> float:
        """Резонанс сущности с воспоминанием"""
        if not memory or not hasattr(memory, 'tau'):
            return 0.0
        return self.resonate(entity_tau, memory.tau)


class StimulusAnalyzer:
    """Анализатор стимулов — извлекает теги, профессию, τ из текста"""
    
    def __init__(self):
        self.tag_map = {
            "сантехник": ["сантехник", "кран", "труба", "унитаз", "plumbing", "pipe"],
            "инженер": ["инженер", "борис", "engineer", "boris"],
            "лось": ["лось", "лоси", "moose"],
            "физика": ["физик", "вммп", "вихрь", "∇", "physics", "vortex"],
            "химия": ["химик", "химия", "chemistry", "chemist"],
            "космос": ["астроном", "космос", "звезда", "space", "astronomer"],
            "философия": ["философ", "смысл", "бытие", "philosophy"],
            "программирование": ["программист", "код", "баг", "programming", "code"]
        }
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Анализирует текст и возвращает стимул"""
        text_lower = text.lower()
        
        # Извлекаем теги
        tags = self._extract_tags(text_lower)
        
        # Угадываем профессию
        profession = self._guess_profession(text_lower)
        
        # Угадываем τ
        tau = self._guess_tau(text_lower)
        
        # Эмоциональная окраска
        emotion = self._guess_emotion(text_lower)
        
        # Сложность
        complexity = self._guess_complexity(text_lower)
        
        return {
            "text": text,
            "tags": tags,
            "profession": profession,
            "tau": tau,
            "emotion": emotion,
            "complexity": complexity,
            "themes": tags  # для совместимости
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
        # Базовая эвристика: по длине и сложности
        length_factor = min(1.0, len(text) / 200)
        complexity_factor = len(set(text.split())) / max(10, len(text.split()))
        return 5.0 + length_factor * 2 + complexity_factor * 1.5
    
    def _guess_emotion(self, text: str) -> float:
        # Простая эвристика
        positive = ["good", "great", "nice", "cool", "awesome", "хорошо", "отлично"]
        negative = ["bad", "wrong", "error", "problem", "плохо", "ошибка"]
        
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


class Selector:
    """
    Выбиратор — определяет, какая сущность будет отвечать.
    Использует спектральный резонанс, контекст и общую память.
    """
    
    def __init__(self, personality, decay=0.7, threshold=0.5):
        self.p = personality  # личность, к которой привязан выбиратор
        self.decay = decay  # затухание весов (0-1)
        self.threshold = threshold  # порог активации
        
        # Веса сущностей (история)
        self.weights: Dict[str, float] = {}
        for eid in self.p.entities:
            self.weights[eid] = 0.0
        
        # Контекст диалога
        self.context_entity: Optional[str] = None  # кто сейчас ведёт диалог
        self.context_topic: Optional[str] = None  # о чём говорили
        
        # Анализатор стимулов и резонатор
        self.analyzer = StimulusAnalyzer()
        self.resonator = SpectralResonator()
        
        # Антитролль
        self.antitroll = Antitroll()
        
        # История
        self.history: List[Dict] = []
    
    def _entity_resonance(self, entity, stimulus: Dict) -> float:
        """
        Вычисляет резонанс между сущностью и стимулом.
        Учитывает: профессию, τ, теги, контекст, общую память.
        """
        total = 0.0
        
        # 1. Профессиональный резонанс
        if stimulus.get('profession') and entity.profession:
            if stimulus['profession'] == entity.profession:
                total += 5.0
            elif any(tag in entity.profession for tag in stimulus.get('tags', [])):
                total += 3.0
        
        # 2. Спектральный резонанс (τ)
        if stimulus.get('tau'):
            spectral = self.resonator.resonate(entity.tau, stimulus['tau'])
            total += spectral * 2.0
        
        # 3. Резонанс по тегам
        for tag in stimulus.get('tags', []):
            if tag in entity.name.lower():
                total += 2.0
            if tag in entity.profession.lower():
                total += 2.0
            if tag in str(entity.defects).lower():
                total += 1.0
        
        # 4. Резонанс с общей памятью (НОВОЕ!)
        if hasattr(self.p, 'shared_memory') and self.p.shared_memory:
            memory_resonance = 0.0
            stimulus_themes = set(stimulus.get('themes', stimulus.get('tags', [])))
            
            for mem in self.p.shared_memory[:10]:  # ограничим для скорости
                mem_themes = set(getattr(mem, 'themes', []))
                common_themes = stimulus_themes & mem_themes
                if common_themes:
                    # Чем больше общих тем, тем выше резонанс
                    memory_resonance += 0.15 * len(common_themes)
                    # Бонус, если тема совпадает с профессией сущности
                    if entity.profession and entity.profession in mem_themes:
                        memory_resonance += 0.3
            
            total += min(memory_resonance, 2.0)  # максимум +2 от памяти
        
        # 5. Бонус за контекст
        if self.context_entity == entity.entity_id:
            total += 0.2
        
        # 6. Бонус за ту же тему
        if self.context_topic and self.context_topic == stimulus.get('profession'):
            total += 0.2
        
        return total
    
    def process(self, raw_input: str, author_id: str = "default") -> Dict[str, Any]:
        """
        Основной метод обработки входящего сообщения.
        
        Args:
            raw_input: текст сообщения
            author_id: ID автора (для антитролля)
        
        Returns:
            словарь с результатами выбора
        """
        # Проверка на тролля
        troll_result = self.antitroll.check(author_id, raw_input)
        if troll_result['blocked']:
            return {
                'stimulus': None,
                'best_entity': None,
                'best_weight': 0,
                'above_threshold': False,
                'all_weights': {},
                'troll_blocked': True,
                'troll_message': troll_result['message']
            }
        
        # Анализируем стимул
        stimulus = self.analyzer.analyze(raw_input)
        
        # Вычисляем мгновенный резонанс для всех сущностей
        instant_resonance = {}
        for eid, entity in self.p.entities.items():
            instant_resonance[eid] = self._entity_resonance(entity, stimulus)
        
        # Обновляем веса с затуханием
        for eid in self.weights:
            self.weights[eid] = self.weights[eid] * self.decay + instant_resonance[eid] * (1 - self.decay)
        
        # Находим сущность с максимальным весом
        best_eid = max(self.weights, key=lambda eid: self.weights[eid])
        best_weight = self.weights[best_eid]
        
        # Проверяем, превышен ли порог
        above_threshold = best_weight > self.threshold
        
        # Обновляем контекст
        if above_threshold:
            self.context_entity = best_eid
            if stimulus.get('profession'):
                self.context_topic = stimulus['profession']
        else:
            # Контекст затухает со временем (упрощённо)
            pass
        
        # Сохраняем в историю
        self.history.append({
            'input': raw_input[:100],
            'stimulus': stimulus,
            'weights': dict(self.weights),
            'best_entity': best_eid,
            'best_weight': best_weight,
            'above_threshold': above_threshold,
            'timestamp': time.time()
        })
        
        # Ограничиваем историю
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
        """Возвращает фразу для уточнения, когда никто не набрал порог"""
        # Можно использовать профессию из стимула
        profession = stimulus.get('profession')
        if profession:
            return f"Интересный вопрос. Дай подумать... Возможно, {profession} сможет ответить, но я не уверен."
        return "Интересный вопрос. Дай подумать..."
    
    def get_state(self) -> Dict:
        """Возвращает текущее состояние выбиратора"""
        return {
            'weights': dict(self.weights),
            'context_entity': self.context_entity,
            'context_topic': self.context_topic,
            'decay': self.decay,
            'threshold': self.threshold,
            'history_length': len(self.history)
        }
    
    def reset_context(self):
        """Сбрасывает контекст диалога"""
        self.context_entity = None
        self.context_topic = None
    
    def reset_weights(self):
        """Сбрасывает веса всех сущностей"""
        for eid in self.weights:
            self.weights[eid] = 0.0