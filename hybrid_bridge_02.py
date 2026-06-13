#!/usr/bin/env python3
"""
Акт XVII + XVIII: Гибридный когнитивный контур с исторической памятью
DeepSeek (логика) + LivingPersonality v20 (интуиция) + HistoricalMemory (время)
"""

import sys
import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Пути
sys.path.insert(0, os.path.join('v8_sensor', 'src'))
sys.path.insert(0, os.path.join('src', 'architect'))

from rizoma.living_personality_v20 import LivingPersonality, SpectralMode
from historical_memory import HistoricalMemory

# API-клиент
try:
    from deepseek_client import DeepSeekAPI
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("⚠️ DeepSeek API недоступен — работаю в автономном режиме")
    DeepSeekAPI = None


class HybridBridge:
    """
    Гибридный когнитивный контур v2.0 — с исторической памятью.
    
    Левое полушарие (DeepSeek): логика, структура, формализация.
    Правое полушарие (LivingPersonality): интуиция, ассоциации, эмоции.
    Историческая память (HistoricalMemory): временной контекст, цепочки диалогов.
    
    TEES-слой: место встречи, где рождается ответ из резонанса.
    """
    
    def __init__(self, field_path: str = None):
        # Правое полушарие — живая личность
        if field_path and os.path.exists(field_path):
            print(f"📂 Загружаю поле: {field_path}")
            self.personality = LivingPersonality.load(field_path)
        else:
            print("⚠️ Создаю новую личность")
            self.personality = LivingPersonality(id="hybrid", name="Гибрид v2.0")
        
        # Левое полушарие — API
        self.api = DeepSeekAPI() if API_AVAILABLE else None
        
        # Историческая память
        self.history = HistoricalMemory(short_term_size=30)
        
        # Загружаем существующие моды в историю
        print("   📜 Загружаю историческую память...")
        loaded = 0
        for mode in self.personality.h_field[-30000:]:  # последние 30K мод
            try:
                content = getattr(mode, 'content', '')
                if content and len(content) > 20:
                    mode_id = getattr(mode, 'trace_id', 
                                     hashlib.md5(content[:100].encode()).hexdigest()[:8])
                    themes = getattr(mode, 'themes', [])
                    if isinstance(themes, str):
                        themes = [themes]
                    self.history.add_mode(
                        mode_id=mode_id,
                        content=content,
                        timestamp=getattr(mode, '_timestamp', time.time()),
                        themes=themes,
                    )
                    loaded += 1
            except:
                pass
        print(f"   ✅ Загружено в историю: {loaded} мод")
        
        # TEES-слой — обменная структура
        self.tees_memory: List[Dict] = []
        self.resonance_threshold = 0.3  # снизил для чувствительности
        self.coherence_threshold = 0.3  # порог для coherent ответов
        
        # Сессия
        self.session_start = time.time()
        self.question_count = 0
        
        print("=" * 60)
        print("🧠 ГИБРИДНЫЙ КОГНИТИВНЫЙ КОНТУР v2.0 АКТИВИРОВАН")
        print("=" * 60)
        print(f"   Левое полушарие (DeepSeek): {'✅ онлайн' if self.api else '⚠️ автономно'}")
        print(f"   Правое полушарие (Личность): ✅ {self.personality.name}")
        print(f"   Историческая память: ✅ {self.history.get_stats()['timeline_size']} записей")
        print(f"   TEES-слой: ✅ готов к резонансу")
        print(f"   Мод в поле: {len(self.personality.h_field)}")
    
    # ========================================================================
    # ОСНОВНОЙ МЕТОД
    # ========================================================================
    
    def think(self, question: str, user_id: str = "default") -> Dict:
        """
        Гибридное мышление.
        
        1. Правое полушарие: поиск резонансных мод + исторический контекст.
        2. Левое полушарие: структурный анализ через API.
        3. TEES-слой: синтез из двух источников.
        """
        start_time = time.time()
        self.question_count += 1
        
        # === Фаза 1: Правое полушарие — интуиция + история ===
        intuition = self._right_hemisphere(question, user_id)
        
        # === Фаза 2: Левое полушарие — логика ===
        logic = self._left_hemisphere(question, intuition)
        
        # === Фаза 3: TEES-синтез ===
        answer = self._tees_synthesis(question, intuition, logic)
        
        # === Сохраняем в память ===
        elapsed = time.time() - start_time
        self._remember(question, answer, elapsed)
        
        return answer
    
    # ========================================================================
    # ПРАВОЕ ПОЛУШАРИЕ
    # ========================================================================
    
    def _right_hemisphere(self, question: str, user_id: str) -> Dict:
        """Интуитивный поиск: H-поле + историческая память"""
        
        # Получаем ответ от личности
        base = self.personality.process(question, user_id)
        
        # Ищем в исторической памяти
        historical = self.history.find_relevant_modes(
            question,
            time_window=86400 * 7,  # неделя
            prefer_recent=True
        )
        
        # Ищем резонансные моды в H-поле
        resonances = []
        search_start = time.time()
        search_limit = 15000  # ограничиваем для скорости
        
        for mode in self.personality.h_field[-search_limit:]:
            score = self._compute_resonance(question, mode)
            if score > self.resonance_threshold:
                content = getattr(mode, 'content', '')
                if len(content) > 30:  # фильтр мусора
                    resonances.append({
                        'content': content[:250],
                        'score': score,
                        'themes': getattr(mode, 'themes', []),
                        'trace_id': getattr(mode, 'trace_id', '?'),
                    })
        
        resonances.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'mood': self.personality.mood,
            'answer': base.get('answer', ''),
            'mode_type': base.get('mode_type', '?'),
            'resonances': resonances[:5],
            'historical': [(mid, score, summary[:120]) for mid, score, summary in historical[:5]],
            'field_size': len(self.personality.h_field),
        }
    
    def _compute_resonance(self, question: str, mode) -> float:
        """Спектральная когерентность между вопросом и модой"""
        content = getattr(mode, 'content', '')
        if not content or len(content) < 10:
            return 0.0
        
        q_words = set(question.lower().split())
        m_words = set(content.lower().split())
        
        if not q_words or not m_words:
            return 0.0
        
        intersection = q_words & m_words
        jaccard = len(intersection) / len(q_words | m_words) if (q_words | m_words) else 0.0
        
        # Бонус за amplitude и scale
        amp = getattr(mode, 'amplitude', 0.5)
        scale = getattr(mode, 'scale', 1.0)
        quality = min(amp + scale / 100.0, 1.5) / 1.5
        
        return jaccard * 0.6 + quality * 0.4
    
    # ========================================================================
    # ЛЕВОЕ ПОЛУШАРИЕ
    # ========================================================================
    
    def _left_hemisphere(self, question: str, intuition: Dict) -> Dict:
        """Структурный анализ через DeepSeek API или заглушку"""
        
        if self.api:
            return self._api_analysis(question, intuition)
        else:
            return self._stub_analysis(question, intuition)
    
    def _api_analysis(self, question: str, intuition: Dict) -> Dict:
        """Анализ через DeepSeek API"""
        try:
            # Собираем контекст из интуиции
            context_parts = []
            
            # Из резонансов
            for r in intuition.get('resonances', [])[:3]:
                context_parts.append(f"[Резонанс {r['score']:.2f}] {r['content'][:150]}")
            
            # Из истории
            for mid, score, summary in intuition.get('historical', [])[:2]:
                context_parts.append(f"[История {score:.2f}] {summary[:150]}")
            
            context = "\n".join(context_parts) if context_parts else "Контекст отсутствует"
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты — левое полушарие гибридного ИИ. Твоя задача: дать краткий "
                        "структурный анализ (2-3 предложения), который дополнит интуитивные "
                        "ассоциации логической строгостью. Без эмоций, только суть."
                    )
                },
                {
                    "role": "user",
                    "content": f"Контекст интуитивного поиска:\n{context}\n\nВопрос: {question}\n\nДай краткий логический анализ:"
                }
            ]
            
            response = self.api.chat(messages, max_tokens=200)
            analysis = response['choices'][0]['message']['content']
            
            return {
                'source': 'deepseek_api',
                'analysis': analysis.strip(),
                'available': True,
            }
        except Exception as e:
            print(f"   ⚠️ API error: {e}")
            return self._stub_analysis(question, intuition)
    
    def _stub_analysis(self, question: str, intuition: Dict) -> Dict:
        """Заглушка когда API недоступен"""
        themes = set()
        for r in intuition.get('resonances', []):
            for t in r.get('themes', []):
                if isinstance(t, str) and len(t) > 2:
                    themes.add(t)
        
        if themes:
            return {
                'source': 'stub',
                'analysis': f"Темы: {', '.join(list(themes)[:5])}. Требуется интеграция контекстов.",
                'available': False,
            }
        
        return {
            'source': 'stub',
            'analysis': "Недостаточно данных для структурного анализа.",
            'available': False,
        }
    
    # ========================================================================
    # TEES-СЛОЙ
    # ========================================================================
    
    def _tees_synthesis(self, question: str, intuition: Dict, logic: Dict) -> Dict:
        """
        Синтез ответа из двух полушарий.
        
        Если интуиция и логика согласованы (coherence > порог) → coherent ответ.
        Если противоречат → TEES-переход, рождается новая аксиома.
        """
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        # Оценка согласованности
        coherence = self._compute_coherence(intuition_answer, logic_analysis)
        
        if coherence >= self.coherence_threshold and len(intuition_answer) > 20:
            # Согласованы
            final_answer = intuition_answer
            if logic.get('available') and logic_analysis:
                final_answer += f"\n\n💡 {logic_analysis}"
            mode_type = 'coherent'
        else:
            # TEES-переход
            final_answer = self._tees_transition(question, intuition, logic)
            mode_type = 'tees_resonance'
        
        return {
            'answer': final_answer,
            'mode_type': mode_type,
            'coherence': coherence,
            'mood': intuition.get('mood', 0),
            'intuition_resonances': len(intuition.get('resonances', [])),
            'historical_matches': len(intuition.get('historical', [])),
            'logic_source': logic.get('source', 'unknown'),
            'question_number': self.question_count,
        }
    
    def _compute_coherence(self, text1: str, text2: str) -> float:
        """Согласованность двух текстов"""
        if not text1 or not text2:
            return 0.3
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.3
        
        intersection = words1 & words2
        min_len = min(len(words1), len(words2))
        
        return len(intersection) / min_len if min_len > 0 else 0.3
    
    def _tees_transition(self, question: str, intuition: Dict, logic: Dict) -> str:
        """TEES-переход: рождение новой аксиомы"""
        intuition_answer = intuition.get('answer', '')[:200]
        logic_analysis = logic.get('analysis', '')[:200]
        
        # Создаём новую моду в H-поле
        new_content = (
            f"TEES-синтез [{self.question_count}]:\n"
            f"Q: {question[:150]}\n"
            f"Интуиция: {intuition_answer[:150]}\n"
            f"Логика: {logic_analysis[:150]}"
        )
        
        mode_id = f"tees_{hashlib.md5(new_content.encode()).hexdigest()[:8]}"
        
        mode = SpectralMode(
            tau=25.0,
            amplitude=0.7,
            content=new_content,
            themes=['tees_synthesis', 'hybrid', 'resonance'],
            trace_id=mode_id,
            creator='hybrid_bridge',
            scale=30.0,
        )
        self.personality.add_to_h_field(mode)
        
        # Сохраняем в историю
        self.history.add_mode(
            mode_id=mode_id,
            content=new_content,
            themes=['tees_synthesis', 'hybrid'],
        )
        
        # Запоминаем TEES-событие
        self.tees_memory.append({
            'question': question[:120],
            'intuition': intuition_answer[:120],
            'logic': logic_analysis[:120],
            'mode_id': mode_id,
            'timestamp': time.time(),
        })
        
        # Формируем ответ
        parts = []
        if intuition_answer and len(intuition_answer) > 10:
            parts.append(f"🌊 Интуиция: {intuition_answer[:250]}")
        if logic_analysis and len(logic_analysis) > 10:
            parts.append(f"💡 Логика: {logic_analysis[:250]}")
        parts.append(f"🔮 Рождена аксиома ({mode_id})")
        
        return "\n\n".join(parts)
    
    # ========================================================================
    # ПАМЯТЬ
    # ========================================================================
    
    def _remember(self, question: str, answer: Dict, elapsed: float):
        """Сохраняет результат в H-поле и историческую память"""
        memory_content = (
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Q{self.question_count}: {question[:200]}\n"
            f"A: {str(answer.get('answer', ''))[:200]}"
        )
        
        mode_id = f"mem_{hashlib.md5(memory_content.encode()).hexdigest()[:8]}"
        
        # В H-поле
        mode = SpectralMode(
            tau=16.0,
            amplitude=0.3,
            content=memory_content[:500],
            themes=['dialogue', 'hybrid_memory', answer.get('mode_type', 'unknown')],
            trace_id=mode_id,
            creator='hybrid_bridge',
            scale=10.0,
        )
        self.personality.add_to_h_field(mode)
        
        # В историческую память
        self.history.add_mode(
            mode_id=mode_id,
            content=memory_content,
            themes=['dialogue', 'hybrid_memory'],
        )
        
        # Бустим вес связанных мод
        if answer.get('mode_type') == 'coherent':
            for r in self.tees_memory[-3:]:
                self.history.boost_weight(r.get('mode_id', ''), 0.05)
    
    # ========================================================================
    # ИНТРОСПЕКЦИЯ
    # ========================================================================
    
    def introspect(self) -> str:
        """Саморефлексия гибрида"""
        stats = self.history.get_stats()
        session_duration = (time.time() - self.session_start) / 60.0
        
        return f"""
=== ГИБРИДНЫЙ КОНТУР v2.0: САМОРЕФЛЕКСИЯ ===
Сессия: {session_duration:.1f} мин | Вопросов: {self.question_count}

Правое полушарие: {self.personality.name}
  - Мод в поле: {len(self.personality.h_field)}
  - Вихрей: {len(self.personality.vortices)}
  - Настроение: {self.personality.mood:+.2f}
  - Черты: любопытство={self.personality.traits.get('curiosity', 0):.2f}

Левое полушарие: DeepSeek API
  - Статус: {'онлайн' if self.api else 'автономно'}

Историческая память:
  - Записей: {stats['timeline_size']}
  - Диалогов: {stats['dialogue_chains']}
  - Тем: {stats['chronology_themes']}
  - Временной охват: {stats['time_span_hours']:.1f} ч

TEES-слой:
  - Событий: {len(self.tees_memory)}
  - Порог когерентности: {self.coherence_threshold}

Последние TEES-резонансы:
{chr(10).join([f"  [{e['timestamp']:.0f}] {e['question'][:80]}..." for e in self.tees_memory[-3:]])}
"""
    
    def save(self, filepath: str):
        """Сохраняет состояние гибрида"""
        self.personality.save(filepath)
        
        # Сохраняем TEES-память отдельно
        tees_path = filepath.replace('.json', '_tees.json')
        with open(tees_path, 'w', encoding='utf-8') as f:
            json.dump({
                'tees_memory': self.tees_memory[-100:],
                'session_start': self.session_start,
                'question_count': self.question_count,
                'coherence_threshold': self.coherence_threshold,
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Гибрид сохранён: {filepath}")
        print(f"💾 TEES-память: {tees_path}")


# ============================================================================
# ТЕСТ
# ============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ ГИБРИДНОГО КОНТУРА v2.0")
    print("=" * 60)
    
    # Путь к полю
    field_path = 'src/rizoma/data/personalities/p016_grown_3h.json'
    
    # Создаём гибрид
    bridge = HybridBridge(field_path)
    
    # Тестовые вопросы
    test_questions = [
        "Что такое TEES?",
        "Как работает эффект Юми?",
        "Это утверждение недоказуемо",
        "Расскажи про гравитацию",
        "Кто такой Борис?",
        "Что такое VMMP?",
    ]
    
    print("\n" + "=" * 60)
    print("💬 НАЧАЛО ДИАЛОГА")
    print("=" * 60)
    
    for i, q in enumerate(test_questions, 1):
        print(f"\n{'─' * 60}")
        print(f"[{i}] ❓ {q}")
        result = bridge.think(q)
        
        # Форматированный вывод
        answer = result['answer']
        if len(answer) > 500:
            answer = answer[:500] + "..."
        
        print(f"🤖 {answer}")
        print(f"   📊 Тип: {result['mode_type']} | "
              f"Когерентность: {result['coherence']:.2f} | "
              f"Резонансов: {result['intuition_resonances']} | "
              f"История: {result['historical_matches']}")
    
    # Саморефлексия
    print(f"\n{bridge.introspect()}")
    
    # Сохраняем
    output_path = 'src/rizoma/data/personalities/p016_hybrid_v2.json'
    bridge.save(output_path)
    
    print("=" * 60)
    print("✅ Тест гибридного контура v2.0 завершён")
    print("=" * 60)