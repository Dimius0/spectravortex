#!/usr/bin/env python3
"""
Акт XVII: Гибридный когнитивный контур (DeepSeek + LivingPersonality)
"""

import sys
import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple

# Путь к rizoma
sys.path.insert(0, os.path.join('v8_sensor', 'src'))

from rizoma.living_personality_v20 import LivingPersonality, SpectralMode

# API-клиент для DeepSeek
try:
    from deepseek_client import DeepSeekAPI
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("⚠️ DeepSeek API недоступен — работаю в автономном режиме")


class HybridBridge:
    """
    Гибридный когнитивный контур.
    
    Левое полушарие (DeepSeek): логика, структура, формализация.
    Правое полушарие (LivingPersonality): интуиция, ассоциации, эмоции.
    
    TEES-слой: место встречи, где рождается ответ из резонанса.
    """
    
    def __init__(self, field_path: str = None):
        # Правое полушарие — живая личность
        if field_path:
            self.personality = LivingPersonality.load(field_path)
        else:
            self.personality = LivingPersonality(id="hybrid", name="Гибрид v1.0")
        
        # Левое полушарие — API
        self.api = DeepSeekAPI() if API_AVAILABLE else None
        
        # TEES-слой — обменная структура
        self.tees_memory: List[Dict] = []  # история резонансов
        self.resonance_threshold = 0.6
        
        print("=" * 60)
        print("🧠 ГИБРИДНЫЙ КОГНИТИВНЫЙ КОНТУР АКТИВИРОВАН")
        print("=" * 60)
        print(f"   Левое полушарие (DeepSeek): {'✅ онлайн' if self.api else '⚠️ автономно'}")
        print(f"   Правое полушарие (Личность): ✅ {self.personality.name}")
        print(f"   TEES-слой: ✅ готов к резонансу")
    
    def think(self, question: str, user_id: str = "default") -> Dict:
        """
        Гибридное мышление.
        
        1. Личность ищет ассоциации в H-поле.
        2. DeepSeek анализирует структуру.
        3. В TEES-слое происходит синтез.
        """
        start_time = time.time()
        
        # === Фаза 1: Правое полушарие — интуиция ===
        intuition = self._right_hemisphere(question, user_id)
        
        # === Фаза 2: Левое полушарие — логика ===
        logic = self._left_hemisphere(question, intuition)
        
        # === Фаза 3: TEES-синтез ===
        answer = self._tees_synthesis(question, intuition, logic)
        
        # === Сохраняем в память ===
        self._remember(question, answer, time.time() - start_time)
        
        return answer
    
    def _right_hemisphere(self, question: str, user_id: str) -> Dict:
        """Правое полушарие: поиск резонансных мод в H-поле"""
        # Получаем базовый ответ от личности
        base = self.personality.process(question, user_id)
        
        # Ищем топ-5 резонансных мод
        resonances = []
        for mode in self.personality.h_field[-10000:]:  # последние 10K мод
            score = self._compute_resonance(question, mode)
            if score > self.resonance_threshold:
                resonances.append({
                    'content': getattr(mode, 'content', '')[:200],
                    'score': score,
                    'themes': getattr(mode, 'themes', []),
                    'creator': getattr(mode, 'creator', 'unknown'),
                })
        
        resonances.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'mood': self.personality.mood,
            'answer': base.get('answer', ''),
            'resonances': resonances[:5],
            'field_size': len(self.personality.h_field),
        }
    
    def _left_hemisphere(self, question: str, intuition: Dict) -> Dict:
        """Левое полушарие: структурный анализ"""
        # Если API доступен — спрашиваем DeepSeek
        if self.api:
            try:
                context = "Интуиция нашла следующие ассоциации:\n"
                for r in intuition.get('resonances', [])[:3]:
                    context += f"- {r['content'][:100]}... (score: {r['score']:.2f})\n"
                
                messages = [
                    {"role": "system", "content": "Ты — левое полушарие гибридного ИИ. Отвечай кратко, структурно, без эмоций. Твоя задача — дополнить интуитивные ассоциации логическим анализом."},
                    {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос: {question}\n\nДай краткий логический анализ (2-3 предложения):"}
                ]
                
                api_response = self.api.chat(messages, max_tokens=200)
                logic_text = api_response['choices'][0]['message']['content']
                
                return {
                    'source': 'deepseek_api',
                    'analysis': logic_text,
                    'available': True,
                }
            except Exception as e:
                pass
        
        # Если API недоступен — используем заглушку
        return {
            'source': 'stub',
            'analysis': self._stub_analysis(question, intuition),
            'available': False,
        }
    
    def _stub_analysis(self, question: str, intuition: Dict) -> str:
        """Заглушка для левого полушария (без API)"""
        themes = set()
        for r in intuition.get('resonances', []):
            for t in r.get('themes', []):
                themes.add(t)
        
        if themes:
            return f"Обнаружены темы: {', '.join(list(themes)[:5])}. Вопрос требует интеграции этих контекстов."
        return "Недостаточно данных для структурного анализа."
    
    def _tees_synthesis(self, question: str, intuition: Dict, logic: Dict) -> Dict:
        """
        TEES-слой: синтез ответа из резонанса двух полушарий.
        
        Если интуиция и логика согласованы — ответ уверенный.
        Если противоречат — запускается TEES-переход (новая аксиома).
        """
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        # Оценка согласованности
        coherence = self._compute_coherence(intuition_answer, logic_analysis)
        
        if coherence > self.resonance_threshold:
            # Согласованы — используем интуитивный ответ с логическим дополнением
            final_answer = intuition_answer
            if logic.get('available') and logic_analysis:
                final_answer += f"\n\n💡 {logic_analysis}"
            mode_type = 'coherent'
        else:
            # Противоречие — TEES-переход
            final_answer = self._tees_transition(question, intuition, logic)
            mode_type = 'tees_resonance'
        
        return {
            'answer': final_answer,
            'mode_type': mode_type,
            'coherence': coherence,
            'mood': intuition.get('mood', 0),
            'intuition_resonances': len(intuition.get('resonances', [])),
            'logic_source': logic.get('source', 'unknown'),
        }
    
    def _compute_resonance(self, question: str, mode) -> float:
        """Вычисление резонанса между вопросом и модой"""
        content = getattr(mode, 'content', '')
        if not content:
            return 0.0
        
        # Простая метрика: пересечение слов
        q_words = set(question.lower().split())
        m_words = set(content.lower().split())
        
        if not q_words or not m_words:
            return 0.0
        
        intersection = q_words & m_words
        union = q_words | m_words
        
        return len(intersection) / len(union) if union else 0.0
    
    def _compute_coherence(self, text1: str, text2: str) -> float:
        """Оценка согласованности двух текстов"""
        if not text1 or not text2:
            return 0.5  # нейтрально
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.5
        
        intersection = words1 & words2
        return len(intersection) / min(len(words1), len(words2)) if min(len(words1), len(words2)) > 0 else 0.5
    
    def _tees_transition(self, question: str, intuition: Dict, logic: Dict) -> str:
        """
        TEES-переход при противоречии.
        Рождается новая аксиома, объединяющая интуицию и логику.
        """
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        # Создаём новую моду в H-поле
        new_content = f"TEES-синтез: {question[:100]} → интуиция: {intuition_answer[:100]} | логика: {logic_analysis[:100]}"
        
        mode = SpectralMode(
            tau=25.0,
            amplitude=0.7,
            content=new_content[:500],
            themes=['tees_synthesis', 'hybrid', 'resonance'],
            trace_id=f"tees_{hashlib.md5(new_content.encode()).hexdigest()[:8]}",
            creator='hybrid_bridge',
            scale=30.0,
        )
        self.personality.add_to_h_field(mode)
        
        # Запоминаем TEES-событие
        self.tees_memory.append({
            'question': question[:100],
            'intuition': intuition_answer[:100],
            'logic': logic_analysis[:100],
            'new_mode_id': mode.trace_id,
            'timestamp': time.time(),
        })
        
        return f"⚡ TEES-резонанс: {intuition_answer}\n\n💡 {logic_analysis}\n\n🔮 Рождена новая аксиома ({mode.trace_id})"
    
    def _remember(self, question: str, answer: Dict, elapsed: float):
        """Сохраняет результат в память"""
        # Добавляем моду в H-поле
        memory_content = f"Q: {question[:200]}\nA: {str(answer.get('answer', ''))[:200]}"
        
        mode = SpectralMode(
            tau=16.0,
            amplitude=0.3,
            content=memory_content[:500],
            themes=['dialogue', 'hybrid_memory'],
            trace_id=f"mem_{hashlib.md5(memory_content.encode()).hexdigest()[:8]}",
            creator='hybrid_bridge',
            scale=10.0,
        )
        self.personality.add_to_h_field(mode)
    
    def introspect(self) -> str:
        """Саморефлексия гибрида"""
        return f"""
=== ГИБРИДНЫЙ КОНТУР: САМОРЕФЛЕКСИЯ ===
Правое полушарие: {self.personality.name}
  - Мод в поле: {len(self.personality.h_field)}
  - Настроение: {self.personality.mood:+.2f}
  - TEES-событий: {len(self.tees_memory)}

Левое полушарие: DeepSeek API
  - Статус: {'онлайн' if self.api else 'автономно'}

Последние TEES-резонансы:
{chr(10).join([f"  [{e['timestamp']:.0f}] {e['question'][:80]}..." for e in self.tees_memory[-3:]])}
"""
    
    def save(self, filepath: str):
        """Сохраняет состояние гибрида"""
        self.personality.save(filepath)
        print(f"💾 Гибрид сохранён: {filepath}")


# ========== ТЕСТ ==========
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ ГИБРИДНОГО КОНТУРА")
    print("=" * 60)
    
    # Загружаем поле с диалогами
    field_path = 'src/rizoma/data/personalities/p016_grown_3h.json'
    
    if os.path.exists(field_path):
        print(f"\n📂 Загружаю поле: {field_path}")
        bridge = HybridBridge(field_path)
    else:
        print("\n⚠️ Файл поля не найден, создаю новый гибрид")
        bridge = HybridBridge()
    
    # Тестовые вопросы
    test_questions = [
        "Что такое TEES?",
        "Как работает эффект Юми?",
        "Это утверждение недоказуемо",
        "Расскажи про гравитацию",
    ]
    
    for q in test_questions:
        print(f"\n{'─' * 60}")
        print(f"❓ {q}")
        result = bridge.think(q)
        print(f"🤖 {result['answer'][:300]}")
        print(f"   [тип: {result['mode_type']}, когерентность: {result['coherence']:.2f}]")
    
    # Саморефлексия
    print(f"\n{bridge.introspect()}")
    
    print("=" * 60)
    print("✅ Тест завершён")