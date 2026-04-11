"""
Antitroll — защита цифровых личностей от троллей и провокаторов
Версия 2.0 — добавлены религиозные и провокационные триггеры
"""

import time
import re
from typing import Tuple
from collections import defaultdict


class Antitroll:
    def __init__(self):
        # Частотный фильтр
        self.request_counts = defaultdict(list)
        self.frequency_limit = 10  # запросов в минуту
        self.timeout = 60  # секунд
        
        # Мат-фильтр
        self.profanity = [
            "дурак", "лох", "идиот", "тупой", "дебил",
            "stupid", "idiot", "fool", "moron"
        ]
        
        # Религиозные и провокационные триггеры
        self.religious_triggers = [
            "бог", "бога", "богу", "богом", "боже",
            "религия", "религию", "религии", "религией",
            "вера", "веру", "верой", "веры",
            "церковь", "церкви", "церковью",
            "священник", "священника", "священнику",
            "патриарх", "патриарха",
            "Бог", "Сатана", "Дьявол", "дьявол",
            "еврей", "евреи", "евреев", "евреями",
            "сионизм", "сиониста", "сионистов",
            "война", "войну", "войной", "войны",
            "враг", "врага", "врагов", "враги",
            "ненависть", "ненависти", "ненавистью",
            "душа", "души", "душой",
            "конфессия", "конфессии",
            "священнослужитель", "священнослужители",
            "святое", "священное",
            "молитва", "молитвы",
            "грех", "грехи", "греха",
            "исповедь", "исповеди",
            "храм", "храмы", "храме",
            "монастырь", "монастыря",
            "ислам", "мусульманин", "мусульмане",
            "христианство", "христианин",
            "иудаизм", "иудей",
            "буддизм", "буддист"
        ]
        
        # Список известных провокаторов
        self.provocateurs = ["Ting_Fodder"]
        
        # Антиповтор
        self.user_history = defaultdict(list)
        self.repetition_limit = 3  # одинаковых вопросов
        self.repetition_window = 300  # 5 минут
        
        # Агрессия
        self.aggressive_patterns = [
            "ты не знаешь", "зачем ты нужен", "бесполезен",
            "you don't know", "what's the point", "useless"
        ]
    
    def _is_frequency_exceeded(self, author: str) -> bool:
        """Проверка частоты запросов"""
        now = time.time()
        # Очищаем старые записи
        self.request_counts[author] = [t for t in self.request_counts[author] if now - t < 60]
        self.request_counts[author].append(now)
        return len(self.request_counts[author]) > self.frequency_limit
    
    def _is_repetition(self, author: str, text: str) -> bool:
        """Проверка на повторяющиеся вопросы"""
        now = time.time()
        # Очищаем старые записи
        self.user_history[author] = [(t, q) for t, q in self.user_history[author] if now - t < self.repetition_window]
        
        text_lower = text.lower()
        for _, prev in self.user_history[author]:
            if prev.lower() == text_lower:
                return True
        
        self.user_history[author].append((now, text))
        return False
    
    def _has_profanity(self, text: str) -> bool:
        """Проверка на мат"""
        text_lower = text.lower()
        return any(prof in text_lower for prof in self.profanity)
    
    def _has_religious_triggers(self, text: str) -> bool:
        """Проверка на религиозные и провокационные триггеры"""
        text_lower = text.lower()
        for trigger in self.religious_triggers:
            if trigger in text_lower:
                return True
        return False
    
    def _has_aggression(self, text: str) -> bool:
        """Проверка на агрессию"""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.aggressive_patterns)
    
    def check(self, author: str, text: str) -> Tuple[bool, str]:
        """
        Проверяет, не является ли пользователь троллем.
        Возвращает (заблокирован, сообщение)
        """
        # Проверка на провокатора по имени
        if author in self.provocateurs:
            return True, "I prefer to discuss physics and mathematics. 🦌"
        
        # Проверка на религиозные триггеры
        if self._has_religious_triggers(text):
            return True, "I focus on VMMS and its scientific predictions. Let's keep the discussion in the realm of physics and mathematics. 🦌"
        
        # Проверка на частоту
        if self._is_frequency_exceeded(author):
            return True, "⏳ Too many requests. Please wait a minute."
        
        # Проверка на повторения
        if self._is_repetition(author, text):
            return True, "🔄 You already asked that. Anything new?"
        
        # Проверка на мат
        if self._has_profanity(text):
            return True, "🙏 Please be respectful. I'm still learning."
        
        # Проверка на агрессию
        if self._has_aggression(text):
            return True, "🛡️ I'm trying to be helpful. Let's talk about something else?"
        
        return False, None