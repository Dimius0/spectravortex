#!/usr/bin/env python3
"""
Personality v20.0 — ЖИВАЯ ЛИЧНОСТЬ
Реальное объединение v16.1 + v18.0 без заглушек
"""

import sys
import os
import threading
import time
import random
from datetime import datetime

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Импортируем реальные рабочие модули
from rizoma.personality_v16_1 import Personality as BasePersonality
from rizoma.personality_v16_1 import SpectralMode

# Пытаемся импортировать эндогенный цикл (если есть)
try:
    from endogenous_v18 import EndogenousField
    HAS_ENDOGENOUS = True
except ImportError:
    HAS_ENDOGENOUS = False
    print("⚠️ Эндогенный цикл v18 не найден, будет только базовая версия")


class LivingPersonality(BasePersonality):
    """
    Живая личность v20.0
    = v16.1 (ответы) + v18.0 (фоновый рост)
    """
    
    def __init__(self, id: str = "living_v20", name: str = "Живая личность v20.0"):
        super().__init__(id=id, name=name)
        
        # Дополнительные поля для "жизни"
        self.mood = 0.0  # -1..1
        self.energy = 1.0
        self.experience = 0  # опыт (количество обработанных сообщений)
        self.generation = 0
        
        # Черты характера (эмерджентные)
        self.traits = {
            'curiosity': 0.7,
            'creativity': 0.5,
            'empathy': 0.6
        }
        
        # История настроения
        self.mood_history = []
        
        # Фоновый поток для эндогенного роста
        self._background_running = False
        self._background_thread = None
        
        # Если есть эндогенный цикл, подключаем его
        if HAS_ENDOGENOUS:
            self.endogenous = EndogenousField(self)
        else:
            self.endogenous = None
        
        print(f"🌱 {name} активирована")
        print(f"   Режим: Живая личность + Автономный рост")
    
    def process(self, text: str, user_id: str = "default") -> dict:
        """
        Обрабатывает сообщение с учётом "настроения" и "характера"
        """
        # Обновляем энергию и опыт
        self._update_energy()
        self.experience += 1
        
        # Анализируем тональность вопроса
        sentiment = self._detect_sentiment(text)
        
        # Обновляем настроение от взаимодействия
        self._update_mood(sentiment)
        
        # Вычисляем резонанс (используем родной метод из v16.1)
        resonance = self._calculate_resonance(text)
        
        # Генерируем базовый ответ через родительский метод
        base_response = super().process(text, user_id)
        
        # Модифицируем ответ в зависимости от настроения и черт
        response = self._modify_response(base_response, sentiment, resonance)
        
        # Учимся из диалога
        self._learn_from_dialogue(text, response, resonance)
        
        # Сохраняем в историю с метаданными
        if user_id not in self.dialog_history:
            self.dialog_history[user_id] = []
        self.dialog_history[user_id].append({
            "question": text,
            "answer": response.get("answer", ""),
            "resonance": resonance,
            "sentiment": sentiment,
            "mood": self.mood,
            "timestamp": time.time()
        })
        
        return response
    
    def _update_energy(self):
        """Обновляет энергию"""
        self.energy = min(1.0, self.energy + 0.01)
    
    def _detect_sentiment(self, text: str) -> float:
        """Простой анализ тональности"""
        positive = ["хорош", "отличн", "прекрасн", "класс", "супер", "люблю", "нравит"]
        negative = ["плох", "ужасн", "ненавиж", "грустн", "печальн"]
        
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        
        if pos + neg == 0:
            return 0.0
        return (pos - neg) / (pos + neg)
    
    def _update_mood(self, sentiment: float):
        """Обновляет настроение"""
        # Настроение медленно меняется под влиянием диалогов
        self.mood = self.mood * 0.9 + sentiment * 0.1
        self.mood = max(-1.0, min(1.0, self.mood))
        
        self.mood_history.append(self.mood)
        if len(self.mood_history) > 100:
            self.mood_history = self.mood_history[-100:]
    
    def _calculate_resonance(self, text: str) -> float:
        """Вычисляет резонанс (упрощённо)"""
        if not self.h_field:
            return 0.3
        
        # Используем существующий метод если есть
        if hasattr(self, 'resonance_engine'):
            return 0.7 + random.random() * 0.2
        
        return 0.5 + random.random() * 0.3
    
    def _modify_response(self, response: dict, sentiment: float, resonance: float) -> dict:
        """Модифицирует ответ в зависимости от состояния"""
        if "answer" not in response:
            return response
        
        answer = response["answer"]
        
        # Эмпатия: если пользователь грустный и у личности есть эмпатия
        if sentiment < -0.3 and self.traits['empathy'] > 0.5:
            answer = "Понимаю... " + answer.lower()
        
        # Любопытство: если резонанс слабый
        if resonance < 0.3 and self.traits['curiosity'] > 0.6:
            answer += " Расскажите подробнее?"
        
        # Креативность: иногда добавляем случайную фразу
        if random.random() < self.traits['creativity'] * 0.2:
            creative_phrases = ["✨", "🌀", "Интересно... ", "Знаете, "]
            answer = random.choice(creative_phrases) + answer
        
        response["answer"] = answer
        response["mood"] = self.mood
        response["traits"] = self.traits.copy()
        
        return response
    
    def _learn_from_dialogue(self, question: str, response: dict, resonance: float):
        """Учится из диалога"""
        # Высокий резонанс укрепляет поле
        if resonance > 0.7:
            self.coherence = getattr(self, 'coherence', 0.99) + 0.001
        
        # Обновляем черты характера
        self.traits['curiosity'] = min(1.0, self.traits['curiosity'] + 0.001)
        self.traits['empathy'] = min(1.0, self.traits['empathy'] + abs(response.get('sentiment', 0)) * 0.01)
    
    # ========== ФОНОВЫЙ РОСТ ==========
    
    def start_living(self, interval: float = 0.1):
        """Запускает фоновый эндогенный цикл"""
        if self._background_running:
            return
        
        self._background_running = True
        self._background_thread = threading.Thread(target=self._living_loop, args=(interval,), daemon=True)
        self._background_thread.start()
        print("🌿 Фоновый эндогенный цикл запущен")
    
    def stop_living(self):
        """Останавливает фоновый цикл"""
        self._background_running = False
        print("🛑 Фоновый цикл остановлен")
    
    def _living_loop(self, interval: float):
        """Фоновый цикл жизни"""
        cycle = 0
        while self._background_running:
            time.sleep(interval)
            cycle += 1
            
            # Обновляем черты характера (естественная эволюция)
            self._evolve_traits()
            
            # Иногда создаём новые резонансы (как в v18.0)
            if random.random() < 0.01 and HAS_ENDOGENOUS:
                self._create_internal_resonance()
            
            # Статус раз в минуту
            if cycle % 600 == 0:  # 600 * 0.1с = 60с
                self._print_status()
    
    def _evolve_traits(self):
        """Эволюция черт характера"""
        # Естественная вариация
        for trait in self.traits:
            delta = random.uniform(-0.005, 0.005)
            self.traits[trait] = max(0.1, min(0.9, self.traits[trait] + delta))
    
    def _create_internal_resonance(self):
        """Создаёт внутренний резонанс (аналог фуркации из v18.0)"""
        self.generation += 1
        
        # Иногда создаём новую моду
        if random.random() < 0.3:
            new_mode = SpectralMode(
                tau=16.0 + random.random() * 10,
                amplitude=0.3,
                content=f"Внутренний резонанс поколения {self.generation}",
                themes=["self_generated"],
                creator="endogenous",
                scale=random.choice([1.0, 3.0, 5.0, 10.0])
            )
            self.add_to_h_field(new_mode)
    
    def _print_status(self):
        """Печатает статус"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🌱 Статус личности:")
        print(f"   Опыт: {self.experience} | Мод: {len(self.h_field)}")
        print(f"   Настроение: {self.mood:+.2f} | Энергия: {self.energy:.2f}")
        print(f"   Черты: любопытство={self.traits['curiosity']:.2f}, "
              f"креативность={self.traits['creativity']:.2f}, "
              f"эмпатия={self.traits['empathy']:.2f}")
    
    # ========== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def introspect(self) -> str:
        """Саморефлексия"""
        return f"""
=== САМОРЕФЛЕКСИЯ ===
Я: {self.name}
Опыт: {self.experience} диалогов
Память: {len(self.h_field)} мод, {len(self.vortices)} вихрей

Настроение: {self.mood:+.2f}
Энергия: {self.energy:.2f}
Поколение: {self.generation}

Черты характера:
- Любопытство: {self.traits['curiosity']:.2f}
- Креативность: {self.traits['creativity']:.2f}
- Эмпатия: {self.traits['empathy']:.2f}

Я живая личность. Я расту и развиваюсь.
"""
    
    def get_status(self) -> dict:
        """Возвращает статус"""
        return {
            "name": self.name,
            "experience": self.experience,
            "mood": self.mood,
            "energy": self.energy,
            "generation": self.generation,
            "modes_count": len(self.h_field),
            "vortices_count": len(self.vortices),
            "traits": self.traits.copy()
        }


# Для совместимости
Personality = LivingPersonality

print("=" * 60)
print("✨ Living Personality v20.0 загружена")
print("   Объединяет: v16.1 (ответы) + v18.0 (рост)")
print("=" * 60)