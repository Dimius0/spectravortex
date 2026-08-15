# tees_stranger_tees.py
# 🔮 Странник — LLM-модуль, анализ мира

import json
import time
from collections import deque

from tees_core_tees import VERSION


class Stranger:
    """
    TEES-Странник — проводник, видящий поле.
    Анализирует состояние мира и отвечает на вопросы.
    """
    
    def __init__(self, lang='ru'):
        self.lang = lang
        self.insights = []
        self.memory = deque(maxlen=100)
    
    def ask(self, question, world_state):
        """
        Ответить на вопрос игрока.
        Анализирует вопрос и состояние мира.
        """
        self.memory.append({
            'q': question,
            'state': world_state,
            't': time.time()
        })
        
        glow = world_state.get('glow', 0)
        warmth = world_state.get('warmth', 30)
        neighbors = world_state.get('neighbors', 0)
        blocks = world_state.get('map_blocks', 0)
        
        q = question.lower()
        
        # Локальные ответы (без LLM)
        if 'свечение' in q or 'glow' in q:
            if glow > 0.999:
                return f"✨ Свечение {glow:.4f}. Мир в нирване."
            elif glow > 0.99:
                return f"✨ Свечение {glow:.4f}. Всё стабильно."
            else:
                return f"✨ Свечение {glow:.4f}. Лёгкая турбулентность."
        
        elif 'тепло' in q or 'warmth' in q:
            return f"🌡️ Тепло: {warmth:.1f}°. Стабильно."
        
        elif 'сосед' in q or 'neighbor' in q:
            if neighbors > 5:
                return f"👥 {neighbors} соседей. Деревня растёт!"
            else:
                return f"👥 {neighbors} соседей. Можно пригласить больше."
        
        elif 'карт' in q or 'map' in q or 'глыб' in q:
            if blocks > 100:
                return f"🗿 {blocks} глыб. Мир уже немалый."
            else:
                return f"🗿 {blocks} глыб. Мир только начинается."
        
        elif 'симбиоз' in q or 'symbiosis' in q:
            return "🔗 Симбиоз — взаимовыгодное соединение маяков. Редкость: common → rare → ultra_rare → shiny."
        
        elif 'ресурс' in q or 'resource' in q:
            return "💪 Ресурс — мера твоего вклада в сеть. Не покупается. Зарабатывается помощью другим."
        
        elif 'привет' in q or 'здрав' in q:
            return f"Привет! Мир жив. Свечение {glow:.4f}. Хорошего дня!"
        
        elif 'спасиб' in q:
            return "Всегда пожалуйста! Да пребудет с тобой сила!"
        
        elif 'кто ты' in q:
            return "Я TEES-Странник. Проводник, видящий поле. Хранитель знаний этого мира."
        
        elif 'как мир' in q:
            return f"Мир шепчет: свечение {glow:.4f}, тепло {warmth:.1f}°, соседей {neighbors}. Всё идёт своим чередом."
        
        # Ответ по умолчанию
        return f"Мир шепчет: свечение {glow:.4f}, тепло {warmth:.1f}°, соседей {neighbors}. Всё идёт своим чередом."
    
    def analyze_world(self, world_state):
        """
        Глубокий анализ состояния мира.
        Сохраняет insight в историю.
        """
        insight = {
            'timestamp': time.time(),
            'glow': world_state.get('glow', 0),
            'warmth': world_state.get('warmth', 30),
            'neighbors': world_state.get('neighbors', 0),
            'blocks': world_state.get('map_blocks', 0),
            'interpretation': self._interpret(world_state)
        }
        self.insights.append(insight)
        return insight
    
    def _interpret(self, state):
        """Интерпретация состояния мира."""
        glow = state.get('glow', 0)
        blocks = state.get('map_blocks', 0)
        neighbors = state.get('neighbors', 0)
        
        if blocks == 0 and neighbors == 0:
            return "Мир только что создан."
        elif blocks < 10:
            return "Мир юн. Первые глыбы добыты."
        elif glow > 0.999:
            return "Мир в нирване. Можно запускать исследования."
        elif glow > 0.99:
            return "Мир стабилен. Хорошее время для копания."
        else:
            return "Лёгкое возмущение. Возможно внешнее воздействие."
    
    def get_llm_context(self, world_state):
        """
        Подготовить контекст для LLM.
        Используется при интеграции с настоящей языковой моделью.
        """
        return json.dumps({
            'world': 'TEES',
            'version': VERSION,
            'state': world_state,
            'recent_insights': [i['interpretation'] for i in self.insights[-5:]],
            'memory_size': len(self.memory)
        }, indent=2, ensure_ascii=False)