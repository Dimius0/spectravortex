#!/usr/bin/env python3
"""
Акт XVIII: Гибридный когнитивный контур v3.0
============================================
DeepSeek (логика) + LivingPersonality (интуиция) + HistoricalMemory (память)

Новое в v3.0:
    - Интеграция HistoricalMemory (временная координата)
    - Режим гипноза (hypnosis_mode) — доступ ко всей временной шкале
    - Цикл сна (sleep_cycle) — пересборка опыта с осознанными сновидениями
    - Исторический вес мод — часто используемые моды важнее
    - Краткосрочный буфер — последние N сообщений
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

# Историческая память
try:
    from src.architect.historical_memory import HistoricalMemory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("⚠️ HistoricalMemory недоступна — работаю без временной координаты")

# API-клиент
try:
    from deepseek_client import DeepSeekAPI
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("⚠️ DeepSeek API недоступен — работаю в автономном режиме")


class HybridBridge:
    """
    Гибридный когнитивный контур v3.0.
    
    Левое полушарие (DeepSeek): логика, структура, формализация.
    Правое полушарие (LivingPersonality): интуиция, ассоциации, эмоции.
    Историческая память: временная координата, гипноз, сон.
    TEES-слой: место встречи, где рождается ответ из резонанса.
    """
    
    def __init__(self, field_path: str = None):
        # Правое полушарие
        if field_path:
            self.personality = LivingPersonality.load(field_path)
        else:
            self.personality = LivingPersonality(id="hybrid_v3", name="Гибрид v3.0")
        
        # Левое полушарие
        self.api = DeepSeekAPI() if API_AVAILABLE else None
        
        # Историческая память
        self.memory = HistoricalMemory(short_term_size=20) if MEMORY_AVAILABLE else None
        if self.memory and field_path:
            self._load_history_from_field()
        
        # TEES-слой
        self.tees_events: List[Dict] = []
        self.resonance_threshold = 0.3
        
        # Статистика сессии
        self.session_questions: List[str] = []  # контекст для осознанных сновидений
        
        print("=" * 60)
        print("🧠 ГИБРИДНЫЙ КОГНИТИВНЫЙ КОНТУР v3.0 АКТИВИРОВАН")
        print("=" * 60)
        print(f"   Левое полушарие (DeepSeek): {'✅ онлайн' if self.api else '⚠️ автономно'}")
        print(f"   Правое полушарие (Личность): ✅ {self.personality.name}")
        print(f"   Историческая память: {'✅ ' + str(self.memory.get_stats()['timeline_size']) + ' записей' if self.memory else '❌ отключена'}")
        print(f"   TEES-слой: ✅ готов к резонансу")
        print(f"   Мод в поле: {len(self.personality.h_field)}")
    
    def _load_history_from_field(self):
        """Загружает моды из H-поля в историческую память."""
        print("   📜 Загружаю историческую память...")
        count = 0
        for mode in self.personality.h_field[-50000:]:  # последние 50K мод
            content = getattr(mode, 'content', '')
            mode_id = getattr(mode, 'trace_id', '')
            themes = getattr(mode, 'themes', [])
            if content and mode_id:
                self.memory.add_mode(
                    mode_id=mode_id,
                    content=content,
                    timestamp=getattr(mode, 'last_update', None) or time.time(),
                    dialogue_id=None,
                    themes=themes if themes else None
                )
                count += 1
        print(f"   ✅ Загружено в историю: {count} мод")
    
    # ========================================================================
    #   МЫШЛЕНИЕ
    # ========================================================================
    
    def think(self, question: str, user_id: str = "default", mode: str = "normal") -> Dict:
        """
        Гибридное мышление.
        
        Args:
            question: Вопрос пользователя.
            user_id: ID пользователя.
            mode: Режим — 'normal', 'hypnosis', 'dream'.
        """
        start_time = time.time()
        
        # Сохраняем вопрос в контекст сессии
        self.session_questions.append(question)
        if len(self.session_questions) > 50:
            self.session_questions = self.session_questions[-50:]
        
        # В режиме гипноза — отключаем фильтры
        if mode == 'hypnosis' and self.memory:
            self.memory.set_hypnosis_mode(True)
        elif mode == 'dream':
            # Запускаем цикл сна с контекстом сессии
            if self.memory:
                self.memory.sleep_cycle(context=self.session_questions[-10:])
            return {
                'answer': f"😴 Сон завершён. Пересобрано {len(self.memory.bridge_modes) if self.memory else 0} мостиков. "
                          f"Можно задавать вопросы.",
                'mode_type': 'dream',
                'coherence': 1.0,
                'mood': self.personality.mood,
            }
        
        # Фаза 1: Правое полушарие — интуиция
        intuition = self._right_hemisphere(question, user_id)
        
        # Фаза 2: Левое полушарие — логика
        logic = self._left_hemisphere(question, intuition)
        
        # Фаза 3: TEES-синтез
        answer = self._tees_synthesis(question, intuition, logic)
        
        # Сохраняем в память
        self._remember(question, answer, time.time() - start_time)
        
        # Возвращаем обычный режим
        if mode == 'hypnosis' and self.memory:
            self.memory.set_hypnosis_mode(False)
        
        return answer
    
    def _right_hemisphere(self, question: str, user_id: str) -> Dict:
        """Правое полушарие: поиск резонансных мод с учётом истории."""
        base = self.personality.process(question, user_id)
        
        # Поиск в исторической памяти (если доступна)
        resonances = []
        if self.memory:
            historical_modes = self.memory.find_relevant_modes(question)
            for mode_id, score, summary in historical_modes:
                resonances.append({
                    'mode_id': mode_id,
                    'content': summary[:200],
                    'score': score,
                })
        
        return {
            'mood': self.personality.mood,
            'answer': base.get('answer', ''),
            'resonances': resonances[:5],
            'field_size': len(self.personality.h_field),
        }
    
    def _left_hemisphere(self, question: str, intuition: Dict) -> Dict:
        """Левое полушарие: структурный анализ."""
        if self.api:
            try:
                context = "Интуиция нашла следующие ассоциации:\n"
                for r in intuition.get('resonances', [])[:3]:
                    context += f"- [{r['score']:.2f}] {r['content'][:100]}...\n"
                
                messages = [
                    {"role": "system", "content": "Ты — левое полушарие гибридного ИИ. Отвечай кратко, структурно, без эмоций."},
                    {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос: {question}\n\nДай краткий логический анализ (2-3 предложения):"}
                ]
                
                api_response = self.api.chat(messages, max_tokens=200)
                logic_text = api_response['choices'][0]['message']['content']
                
                return {'source': 'deepseek_api', 'analysis': logic_text, 'available': True}
            except Exception:
                pass
        
        return {'source': 'stub', 'analysis': self._stub_analysis(question, intuition), 'available': False}
    
    def _stub_analysis(self, question: str, intuition: Dict) -> str:
        """Заглушка для левого полушария (без API)."""
        themes = set()
        for r in intuition.get('resonances', []):
            for t in r.get('themes', []):
                themes.add(t)
        if themes:
            return f"Обнаружены темы: {', '.join(list(themes)[:5])}. Вопрос требует интеграции этих контекстов."
        return "Недостаточно данных для структурного анализа."
    
    def _tees_synthesis(self, question: str, intuition: Dict, logic: Dict) -> Dict:
        """TEES-слой: синтез ответа из резонанса двух полушарий."""
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        coherence = self._compute_coherence(intuition_answer, logic_analysis)
        
        if coherence > self.resonance_threshold:
            final_answer = intuition_answer
            if logic.get('available') and logic_analysis:
                final_answer += f"\n\n💡 {logic_analysis}"
            mode_type = 'coherent'
        else:
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
        """Вычисление резонанса между вопросом и модой."""
        content = getattr(mode, 'content', '')
        if not content:
            return 0.0
        q_words = set(question.lower().split())
        m_words = set(content.lower().split())
        if not q_words or not m_words:
            return 0.0
        intersection = q_words & m_words
        union = q_words | m_words
        return len(intersection) / len(union) if union else 0.0
    
    def _compute_coherence(self, text1: str, text2: str) -> float:
        """Оценка согласованности двух текстов."""
        if not text1 or not text2:
            return 0.5
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.5
        intersection = words1 & words2
        return len(intersection) / min(len(words1), len(words2)) if min(len(words1), len(words2)) > 0 else 0.5
    
    def _tees_transition(self, question: str, intuition: Dict, logic: Dict) -> str:
        """TEES-переход при противоречии. Рождается новая аксиома."""
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        new_content = f"TEES-синтез: {question[:100]} → интуиция: {intuition_answer[:100]} | логика: {logic_analysis[:100]}"
        
        mode = SpectralMode(
            tau=25.0,
            amplitude=0.7,
            content=new_content[:500],
            themes=['tees_synthesis', 'hybrid', 'resonance'],
            trace_id=f"tees_{hashlib.md5(new_content.encode()).hexdigest()[:8]}",
            creator='hybrid_bridge_v3',
            scale=30.0,
        )
        self.personality.add_to_h_field(mode)
        
        # Добавляем в историческую память
        if self.memory:
            self.memory.add_mode(
                mode_id=mode.trace_id,
                content=new_content,
                themes=['tees_synthesis', 'hybrid_v3']
            )
        
        self.tees_events.append({
            'question': question[:100],
            'intuition': intuition_answer[:100],
            'logic': logic_analysis[:100],
            'new_mode_id': mode.trace_id,
            'timestamp': time.time(),
        })
        
        return f"🌊 Интуиция: {intuition_answer}\n\n💡 Логика: {logic_analysis}\n\n🔮 Рождена аксиома ({mode.trace_id})"
    
    def _remember(self, question: str, answer: Dict, elapsed: float):
        """Сохраняет результат в память."""
        memory_content = f"Q: {question[:200]}\nA: {str(answer.get('answer', ''))[:200]}"
        
        mode = SpectralMode(
            tau=16.0,
            amplitude=0.3,
            content=memory_content[:500],
            themes=['dialogue', 'hybrid_memory'],
            trace_id=f"mem_{hashlib.md5(memory_content.encode()).hexdigest()[:8]}",
            creator='hybrid_bridge_v3',
            scale=10.0,
        )
        self.personality.add_to_h_field(mode)
        
        if self.memory:
            self.memory.add_mode(
                mode_id=mode.trace_id,
                content=memory_content,
                themes=['dialogue', 'hybrid_memory']
            )
    
    # ========================================================================
    #   КОМАНДЫ
    # ========================================================================
    
    def hypnosis(self, question: str) -> Dict:
        """Режим гипноза: доступ ко всей временной шкале."""
        return self.think(question, mode='hypnosis')
    
    def sleep(self) -> Dict:
        """Запускает цикл сна с осознанными сновидениями."""
        return self.think("", mode='dream')
    
    def introspect(self) -> str:
        """Саморефлексия гибрида."""
        memory_stats = self.memory.get_stats() if self.memory else {}
        return f"""
=== ГИБРИДНЫЙ КОНТУР v3.0: САМОРЕФЛЕКСИЯ ===
Сессия: {len(self.session_questions)} вопросов

Правое полушарие: {self.personality.name}
  - Мод в поле: {len(self.personality.h_field)}
  - Вихрей: {len(self.personality.vortices) if hasattr(self.personality, 'vortices') else '?'}
  - Настроение: {self.personality.mood:+.2f}
  - Черты: любопытство={self.personality.traits.get('curiosity', 0):.2f}

Левое полушарие: DeepSeek API
  - Статус: {'онлайн' if self.api else 'автономно'}

Историческая память:
  - Записей: {memory_stats.get('timeline_size', 0)}
  - Диалогов: {memory_stats.get('dialogue_chains', 0)}
  - Тем: {memory_stats.get('chronology_themes', 0)}
  - Мостиков (сон): {memory_stats.get('bridge_modes', 0)}
  - Временной охват: {memory_stats.get('time_span_hours', 0):.1f} ч

TEES-слой:
  - Событий: {len(self.tees_events)}
  - Порог когерентности: {self.resonance_threshold}

Последние TEES-резонансы:
{chr(10).join([f"  [{e['timestamp']:.0f}] {e['question'][:80]}..." for e in self.tees_events[-3:]])}
"""
    
    def save(self, filepath: str):
        """Сохраняет состояние гибрида."""
        self.personality.save(filepath)
        print(f"💾 Гибрид сохранён: {filepath}")
        
        # Сохраняем TEES-память отдельно
        tees_path = filepath.replace('.json', '_tees.json')
        with open(tees_path, 'w', encoding='utf-8') as f:
            json.dump(self.tees_events, f, ensure_ascii=False, indent=2)
        print(f"💾 TEES-память: {tees_path}")


# ========================================================================
#   ТЕСТ
# ========================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ ГИБРИДНОГО КОНТУРА v3.0")
    print("=" * 60)
    
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
    
    print("\n" + "=" * 60)
    print("💬 НАЧАЛО ДИАЛОГА")
    print("=" * 60)
    
    for i, q in enumerate(test_questions, 1):
        print(f"\n{'─' * 60}")
        print(f"[{i}] ❓ {q}")
        result = bridge.think(q)
        print(f"🤖 {result['answer'][:300]}")
        print(f"   📊 Тип: {result['mode_type']} | Когерентность: {result['coherence']:.2f} | "
              f"Резонансов: {result['intuition_resonances']} | История: {bridge.memory.get_stats()['timeline_size'] if bridge.memory else 0}")
    
    # Саморефлексия
    print(f"\n{bridge.introspect()}")
    
    # Сохранение
    bridge.save('src/rizoma/data/personalities/p016_hybrid_v3.json')
    
    print("=" * 60)
    print("✅ Тест гибридного контура v3.0 завершён")