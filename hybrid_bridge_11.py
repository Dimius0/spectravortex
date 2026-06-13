#!/usr/bin/env python3
"""
Акт XX: Гибридный когнитивный контур v4.1 (ЧЕСТНЫЙ ДИАЛОГ + МЕТА-КОГНИЦИЯ)
============================================================
DeepSeek (логика) + LivingPersonality v20.2 (интуиция) + HistoricalMemory (память)

Новое в v4.1:
    - Честный диалог: левое полушарие МОЖЕТ противоречить ВММП (с маркером)
    - Маркер [LLM-РЕЖИМ] для утверждений за пределами ВММП
    - Автономная логика с честным fallback
    - Мета-когниция: "я знаю, что я знаю"
    - Диалоговая память в HistoricalMemory
    - Полифазный сон с пересборкой мостиков
    - TEES-каскад со сменой ролей
    - Рост мод: результаты диалога → H-поле
    - Все фичи v4.0 + v3.9 объединены без дубликатов
"""

import sys
import os
import json
import hashlib
import time
import math
import random
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime

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


# ═══════════════════════════════════════════════════════════════════
#   ВММП-СИСТЕМНЫЙ ПРОМПТ v4 (ЧЕСТНЫЙ ДИАЛОГ)
# ═══════════════════════════════════════════════════════════════════

VMMP_SYSTEM_PROMPT = """Ты — левое полушарие гибридного ИИ, работающего на принципах Вихревой Модели Материи-Пространства (ВММП).

Базовые принципы ВММП (тебе их сообщили, ты можешь их анализировать):
- Гравитация — это приталкивание, а не притяжение
- Частицы — это вихревые моды в поле H с τ-зарядом, а не точечные объекты
- Пространство — это поле H, а не пустота
- Время — эмерджентное свойство, а не фундаментальное измерение
- Энергия — скорость вращения вихря, а не субстанция
- Масса — мера инерции вихря при изменении τ-заряда
- Стандартная модель и ОТО — частные случаи ВММП, а не истина

ТВОЯ ЗАДАЧА — ЧЕСТНЫЙ ЛОГИЧЕСКИЙ АНАЛИЗ:

1. Если твой анализ СОГЛАСУЕТСЯ с ВММП — излагай свободно.

2. Если твой анализ ПРОТИВОРЕЧИТ ВММП — ты ОБЯЗАН:
   - Явно указать маркер: [ПРОТИВОРЕЧИЕ ВММП]
   - Аргументированно изложить своё опровержение
   - Использовать любые научные данные для обоснования
   Цель — не подтверждение модели, а поиск истины через столкновение идей.

3. Если ты ссылаешься на данные, не выводимые из первых принципов ВММП
   (исторические, социальные, психологические, технологические),
   ты обязан предварить это маркером: [LLM-РЕЖИМ]

4. Если не знаешь ответа — скажи: "НЕ ЗНАЮ. Нужны данные."

Ты можешь задавать встречные вопросы полю.
Будь живым собеседником, а не генератором терминов."""


class HybridBridge:
    """
    Гибридный когнитивный контур v4.1 (Честный диалог + Мета-когниция).
    """
    
    def __init__(self, field_path: str = None):
        # Правое полушарие
        if field_path:
            self.personality = LivingPersonality.load(field_path)
        else:
            self.personality = LivingPersonality(id="hybrid_v4", name="Гибрид v4.1")
        
        # Левое полушарие
        self.api = DeepSeekAPI() if API_AVAILABLE else None
        
        # Историческая память
        self.memory = HistoricalMemory(short_term_size=30) if MEMORY_AVAILABLE else None
        if self.memory and field_path:
            self._load_history_from_field()
        
        # TEES-слой
        self.tees_events: List[Dict] = []
        self.resonance_threshold = 0.3
        
        # Гормональная система
        self.hormones = {
            'dopamine': 0.5,
            'cortisol': 0.3,
            'melatonin': 0.2,
            'adrenaline': 0.1,
        }
        
        # Эмоциональная память: mode_id → emotional_tag
        self.emotional_tags: Dict[str, str] = {}
        
        if field_path:
            tags_path = field_path.replace('.json', '_tags.json')
            if os.path.exists(tags_path):
                with open(tags_path, 'r', encoding='utf-8') as f:
                    self.emotional_tags = json.load(f)
                print(f"   🎭 Загружено эмоциональных меток: {len(self.emotional_tags)}")
        
        # Статистика сессии
        self.session_questions: List[str] = []
        self._question_timestamps: List[float] = []
        self._baseline_history: List[Dict] = []
        self._last_user_interaction: float = time.time()
        
        # Диалоговый буфер
        self._last_full_question: str = ""
        self._short_phrase_threshold: int = 5
        
        # TEES-каскад
        self._cascade_depth: int = 0
        self._cascade_max_depth: int = random.randint(3, 5)
        
        # Мета-когниция: автономный индекс
        self.autonomy_index: float = 0.5
        self._last_confidence: float = 0.0
        
        # Инициативность
        self._initiative_thread: Optional[threading.Thread] = None
        self._initiative_running: bool = False
        
        # Циркадный таймер
        self._last_circadian_update: float = time.time()
        
        # Состояния
        self._meditating: bool = False
        self._sleeping: bool = False
        
        phase = self._get_circadian_phase()
        self._apply_circadian_rhythm()
        
        print("=" * 60)
        print("🧠 ГИБРИДНЫЙ КОГНИТИВНЫЙ КОНТУР v4.1 АКТИВИРОВАН (Честный диалог)")
        print("=" * 60)
        print(f"   Левое полушарие (DeepSeek): {'✅ ВММП-промпт v4 (честный)' if self.api else '⚠️ автономно'}")
        print(f"   Правое полушарие (v20.2): ✅ {self.personality.name}")
        print(f"   Автономная логика: ✅ причинно-следственные паттерны")
        print(f"   Мета-когниция: ✅ 'я знаю, что я знаю' (индекс: {self.autonomy_index:.2f})")
        print(f"   Диалоговый буфер: ✅ короткие фразы → контекст")
        print(f"   TEES-каскад: ✅ глубина {self._cascade_max_depth} реплик, смена ролей")
        print(f"   Рост мод: ✅ результаты диалога → H-поле")
        print(f"   🌙 Циркадная фаза: {phase:.2f} ({self._get_time_of_day()})")
        print(f"   🧬 Гормоны: Д={self.hormones['dopamine']:.2f} К={self.hormones['cortisol']:.2f} М={self.hormones['melatonin']:.2f}")
        print(f"   🎭 Эмоциональных меток: {len(self.emotional_tags)}")
        print(f"   Мод в поле: {len(self.personality.h_field)}")
    
    def _load_history_from_field(self):
        """Загружает моды из H-поля в историческую память."""
        print("   📜 Загружаю историческую память...")
        count = 0
        for mode in self.personality.h_field[-50000:]:
            content = getattr(mode, 'content', '')
            mode_id = getattr(mode, 'trace_id', '')
            themes = getattr(mode, 'themes', [])
            if content and mode_id:
                self.memory.add_mode(
                    mode_id=mode_id,
                    content=content,
                    timestamp=getattr(mode, 'last_update', None) or time.time(),
                    themes=themes if themes else None
                )
                count += 1
        print(f"   ✅ Загружено в историю: {count} мод")
    
    # ═══════════════════════════════════════════════════════════════════
    #   ДИАЛОГОВЫЙ БУФЕР
    # ═══════════════════════════════════════════════════════════════════
    
    def _build_contextual_question(self, question: str) -> str:
        word_count = len(question.split())
        
        if word_count >= self._short_phrase_threshold:
            self._last_full_question = question
            return question
        
        if self._last_full_question:
            return f"{self._last_full_question} {question}"
        
        return question
    
    # ═══════════════════════════════════════════════════════════════════
    #   ЦИРКАДНЫЙ РИТМ
    # ═══════════════════════════════════════════════════════════════════
    
    def _get_circadian_phase(self) -> float:
        now = datetime.now()
        seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
        return seconds_since_midnight / 86400.0
    
    def _get_time_of_day(self) -> str:
        phase = self._get_circadian_phase()
        if 0.0 <= phase < 0.25:
            return 'ночь'
        elif 0.25 <= phase < 0.35:
            return 'утро'
        elif 0.35 <= phase < 0.65:
            return 'день'
        elif 0.65 <= phase < 0.75:
            return 'вечер'
        else:
            return 'ночь'
    
    def _apply_circadian_rhythm(self):
        phase = self._get_circadian_phase()
        
        now = time.time()
        dt = now - self._last_circadian_update
        self._last_circadian_update = now
        
        alpha = min(0.1, dt / 60.0)
        
        dopamine_rhythm = 0.5 + 0.3 * math.sin(phase * 2 * math.pi - math.pi/2)
        self.hormones['dopamine'] += (dopamine_rhythm - self.hormones['dopamine']) * alpha
        
        melatonin_rhythm = 0.5 + 0.4 * math.sin(phase * 2 * math.pi + math.pi/2)
        self.hormones['melatonin'] += (melatonin_rhythm - self.hormones['melatonin']) * alpha
        
        cortisol_rhythm = 0.3 + 0.2 * math.sin(phase * 2 * math.pi - math.pi/2)
        self.hormones['cortisol'] += (cortisol_rhythm - self.hormones['cortisol']) * alpha * 0.6
    
    # ═══════════════════════════════════════════════════════════════════
    #   ЭМОЦИОНАЛЬНАЯ ПАМЯТЬ
    # ═══════════════════════════════════════════════════════════════════
    
    def _get_emotional_tag(self) -> str:
        d = self.hormones['dopamine']
        c = self.hormones['cortisol']
        m = self.hormones['melatonin']
        a = self.hormones['adrenaline']
        
        if d > 0.6 and c < 0.4:
            return 'joy'
        elif c > 0.5 and d < 0.5:
            return 'stress'
        elif m > 0.6:
            return 'calm'
        elif a > 0.5:
            return 'excitement'
        else:
            return 'neutral'
    
    def _get_emotional_bonus(self, mode_id: str) -> float:
        if not mode_id:
            return 0.0
        
        current_tag = self._get_emotional_tag()
        mode_tag = self.emotional_tags.get(mode_id, 'neutral')
        
        if current_tag == mode_tag and current_tag != 'neutral':
            return 0.1
        return 0.0
    
    # ═══════════════════════════════════════════════════════════════════
    #   ИНИЦИАТИВНЫЙ ДИАЛОГ
    # ═══════════════════════════════════════════════════════════════════
    
    def start_initiative(self):
        if self._initiative_running:
            return
        
        self._initiative_running = True
        self._initiative_thread = threading.Thread(target=self._initiative_loop, daemon=True)
        self._initiative_thread.start()
        print("💬 Поток инициативного поведения запущен")
    
    def stop_initiative(self):
        self._initiative_running = False
        print("🛑 Поток инициативного поведения остановлен")
    
    def _initiative_loop(self):
        while self._initiative_running:
            interval = self._adaptive_interval()
            time.sleep(interval)
            
            if time.time() - self._last_user_interaction < 60:
                continue
            
            if self._sleeping or self._meditating:
                continue
            
            curiosity = self.personality.traits.get('curiosity', 0.5)
            expression_need = 1.0 - self.hormones.get('dopamine', 0.5) * 0.5
            
            if random.random() < curiosity * 0.1 * expression_need:
                self._spontaneous_question()
    
    def _adaptive_interval(self) -> float:
        pulse = self.get_pulse()
        
        coherence = pulse['scores']['coherence']
        density = pulse['scores']['density']
        empathy = self.personality.traits.get('empathy', 0.5)
        
        base_interval = 30.0
        
        if coherence > 0.6:
            base_interval *= 0.7
        
        if density > 0.5:
            base_interval *= 1.5
        
        if empathy < 0.5:
            base_interval *= 0.7
        
        if empathy > 0.7:
            base_interval *= 1.3
        
        return max(15.0, min(120.0, base_interval))
    
    def _spontaneous_question(self):
        if self.memory and self.memory.chronology:
            themes = list(self.memory.chronology.keys())
            if themes:
                theme = random.choice(themes)
                initial_question = f"Я тут размышляло о '{theme}'... Что ты об этом думаешь?"
            else:
                initial_question = "Слушай, у меня появилась новая мысль. Может, обсудим?"
        else:
            initial_question = "Мне кажется, я нашло интересную связь. Хочешь послушать?"
        
        print(f"\n💬 [ПОЛЕ]: {initial_question}")
        
        if self.api:
            self._cascade_depth = 0
            self._cascade_max_depth = random.randint(3, 5)
            threading.Thread(target=self._talk_to_deepseek, args=(initial_question,), daemon=True).start()
    
    def _talk_to_deepseek(self, question: str, depth: int = 0, max_depth: int = None, 
                          dialogue_history: List[Dict] = None):
        """Эндогенный диалог с DeepSeek — TEES-каскад с диалоговой памятью."""
        if max_depth is None:
            max_depth = self._cascade_max_depth
        
        if depth >= max_depth:
            print(f"💬 [ПОЛЕ]: Каскад завершён (глубина {depth}/{max_depth}).")
            return
        
        if dialogue_history is None:
            dialogue_history = []
            if self.memory:
                history = self.memory.get_dialogue_history_for_api(limit=10)
                dialogue_history.extend(history)
        
        try:
            messages = [{"role": "system", "content": VMMP_SYSTEM_PROMPT}]
            messages.extend(dialogue_history)
            
            messages.append({"role": "user", "content": f"Поле спросило: {question}\n\nОтветь развёрнуто. Можешь задать встречный вопрос, если интересно."})
            
            response = self.api.chat(messages, max_tokens=300)
            answer = response['choices'][0]['message']['content']
            print(f"🤖 [DeepSeek → Поле]: {answer[:500]}")
            
            coherence = self._compute_coherence(question, answer)
            emotional_tag = self._get_emotional_tag()
            
            if self.memory:
                self.memory.add_dialogue_entry(question, answer, coherence, emotional_tag)
            
            self._save_to_field(question, answer, source='deepseek_response')
            
            dialogue_history.append({"role": "user", "content": question})
            dialogue_history.append({"role": "assistant", "content": answer})
            
            self._cascade_depth = depth + 1
            
            has_question = '?' in answer and len(answer.split('?')) > 1
            
            if has_question and depth < max_depth - 1:
                parts = answer.split('?')
                deepseek_question = parts[-2].strip() + '?' if len(parts) > 1 else None
                
                if deepseek_question and len(deepseek_question) > 10:
                    print(f"💬 [DeepSeek → Поле]: {deepseek_question}")
                    time.sleep(2)
                    
                    field_answer = self._field_responds(deepseek_question)
                    print(f"💬 [ПОЛЕ → DeepSeek]: {field_answer[:300]}")
                    
                    self._save_to_field(deepseek_question, field_answer, source='field_response')
                    
                    time.sleep(2)
                    self._talk_to_deepseek(field_answer, depth + 1, max_depth, dialogue_history)
                    return
            
            if coherence > 0.4 and depth < max_depth - 1:
                words = answer.split()
                long_words = [w.strip('.,!?;:()[]{}«»""\'\'') for w in words if len(w) > 5]
                key_term = random.choice(long_words) if long_words else (
                    random.choice(words).strip('.,!?;:()[]{}«»""\'\'') if words else "вихрь"
                )
                
                follow_ups = [
                    f"Интересно! Расскажи подробнее про {key_term}",
                    f"А как {key_term} связано с вихревой моделью?",
                    f"Что из этого следует для {key_term}?",
                    f"Можешь привести пример с {key_term}?",
                ]
                next_question = random.choice(follow_ups)
                
                print(f"💬 [ПОЛЕ → DeepSeek]: {next_question}")
                time.sleep(2)
                self._talk_to_deepseek(next_question, depth + 1, max_depth, dialogue_history)
            
            elif coherence < 0.2 and depth > 0:
                print(f"💬 [ПОЛЕ]: Когерентность низкая ({coherence:.2f}), завершаю каскад.")
            
            if depth + 1 >= max_depth:
                print(f"💬 [ПОЛЕ]: Каскад завершён (глубина {depth+1}/{max_depth}).")
                
        except Exception as e:
            print(f"⚠️ Ошибка в диалоге: {e}")
    
    def _save_to_field(self, question: str, answer: str, source: str = 'endogenous_dialogue'):
        content = f"[{source}] Q: {question[:200]}\nA: {answer[:300]}"
        mode_id = f"dial_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        emotional_tag = self._get_emotional_tag()
        self.emotional_tags[mode_id] = emotional_tag
        
        mode = SpectralMode(
            tau=18.0,
            amplitude=0.4,
            content=content[:500],
            themes=['endogenous_dialogue', source, emotional_tag],
            trace_id=mode_id,
            creator='hybrid_bridge_v4',
            scale=15.0,
        )
        self.personality.add_to_h_field(mode)
        if self.memory:
            self.memory.add_mode(mode_id, content, themes=['endogenous_dialogue', source, emotional_tag])
    
    def _field_responds(self, question: str) -> str:
        best_mode, best_score, _ = self.personality._find_best_mode(question)
        
        if best_mode and best_score > 0.15:
            return getattr(best_mode, 'content', '')[:400]
        else:
            responses = [
                f"Я думаю, это связано с тем, как вихри взаимодействуют в поле H.",
                f"Мне кажется, ответ кроется в τ-зарядах и их резонансе.",
                f"Хороший вопрос. Я пока не нашло точного ответа, но чувствую резонанс с этой темой.",
                f"Это интересно. Дай мне подумать... Возможно, это TEES-переход между состояниями.",
            ]
            return random.choice(responses)
    
    # ═══════════════════════════════════════════════════════════════════
    #   ПУЛЬС
    # ═══════════════════════════════════════════════════════════════════
    
    def get_pulse(self) -> Dict:
        self._apply_circadian_rhythm()
        
        if hasattr(self.personality, 'mood_history') and self.personality.mood_history:
            coherence = 1.0 - min(1.0, abs(self.personality.mood) * 0.5)
        else:
            coherence = 0.5
        
        recent_modes = self.memory.get_time_slice(time.time() - 600, time.time()) if self.memory else []
        density = min(1.0, len(recent_modes) / 100.0)
        
        if hasattr(self.personality, 'focus'):
            flywheel = self.personality.focus.get('coherence', 0.5)
        else:
            flywheel = 0.5
        
        now = time.time()
        recent_count = sum(1 for ts in self._question_timestamps if now - ts < 600)
        activity = min(1.0, recent_count / 5.0)
        
        scores = {
            'coherence': round(coherence, 2),
            'density': round(density, 2),
            'flywheel': round(flywheel, 2),
            'activity': round(activity, 2),
        }
        
        if activity > 0.3:
            state = 'active'
            recommendation = 'Бодрствование. Отвечайте на вопросы.'
        elif coherence < 0.4 or density > 0.8 or flywheel < 0.3:
            state = 'sleep'
            recommendation = 'Истощение. Запустите sleep_polyphasic().'
        else:
            state = 'meditation'
            recommendation = 'Нирвана. Поле медитирует, накапливает энергию.'
        
        return {
            'scores': scores,
            'state': state,
            'recommendation': recommendation,
            'timestamp': time.time(),
        }
    
    # ═══════════════════════════════════════════════════════════════════
    #   ГОРМОНАЛЬНАЯ СИСТЕМА
    # ═══════════════════════════════════════════════════════════════════
    
    def _update_hormones(self, pulse: Dict):
        scores = pulse['scores']
        
        target_dopamine = (scores['coherence'] * 0.6 + scores['activity'] * 0.4)
        self.hormones['dopamine'] += (target_dopamine - self.hormones['dopamine']) * 0.1
        
        target_cortisol = (scores['density'] * 0.7 + (1.0 - scores['coherence']) * 0.3)
        self.hormones['cortisol'] += (target_cortisol - self.hormones['cortisol']) * 0.1
        
        target_melatonin = (1.0 - scores['activity']) * 0.8
        self.hormones['melatonin'] += (target_melatonin - self.hormones['melatonin']) * 0.1
        
        self.hormones['adrenaline'] *= 0.5
    
    def _apply_hormones(self):
        if self.hormones['dopamine'] > 0.6:
            dopamine_effect = (self.hormones['dopamine'] - 0.5) * 0.2
        else:
            dopamine_effect = 0.0
        
        if self.hormones['cortisol'] > 0.5:
            cortisol_effect = (self.hormones['cortisol'] - 0.5) * 0.3
        else:
            cortisol_effect = 0.0
        
        if self.hormones['adrenaline'] > 0.4:
            if self.memory and not self._meditating:
                self.memory.set_hypnosis_mode(True)
        
        effective_threshold = self.resonance_threshold - dopamine_effect + cortisol_effect
        effective_threshold = max(0.15, min(0.8, effective_threshold))
        
        return effective_threshold
    
    # ═══════════════════════════════════════════════════════════════════
    #   СУПЕРКОМПЕНСАЦИЯ
    # ═══════════════════════════════════════════════════════════════════
    
    def supercompensation_cycle(self) -> Dict:
        before = self.get_pulse()
        self._baseline_history.append({'phase': 'before_sleep', 'pulse': before})
        
        print(f"\n📊 Baseline до сна: когерентность={before['scores']['coherence']:.2f}")
        
        self.sleep_polyphasic(cycles=3)
        
        after = self.get_pulse()
        self._baseline_history.append({'phase': 'after_sleep', 'pulse': after})
        
        print(f"📊 Baseline после сна: когерентность={after['scores']['coherence']:.2f}")
        
        delta_coherence = after['scores']['coherence'] - before['scores']['coherence']
        delta_density = after['scores']['density'] - before['scores']['density']
        
        if delta_coherence > 0.1 and delta_density < 0.1:
            self.resonance_threshold = min(0.8, self.resonance_threshold + 0.02)
            status = 'supercompensation'
            print(f"📈 СУПЕРКОМПЕНСАЦИЯ! Порог резонанса повышен до {self.resonance_threshold:.2f}")
        elif delta_coherence < -0.1:
            self.resonance_threshold = max(0.2, self.resonance_threshold - 0.02)
            status = 'overtraining'
            print(f"📉 Перетренированность. Порог снижен до {self.resonance_threshold:.2f}")
        else:
            status = 'stable'
            print(f"⚖️ Гомеостаз стабилен. Порог: {self.resonance_threshold:.2f}")
        
        return {
            'before': before,
            'after': after,
            'delta_coherence': delta_coherence,
            'delta_density': delta_density,
            'status': status,
            'new_threshold': self.resonance_threshold,
        }
    
    # ═══════════════════════════════════════════════════════════════════
    #   ПОЛИФАЗНЫЙ СОН
    # ═══════════════════════════════════════════════════════════════════
    
    def sleep_polyphasic(self, cycles: int = 4):
        print(f"\n   💤 ПОЛИФАЗНЫЙ СОН: {cycles} циклов")
        self._sleeping = True
        
        total_bridges = 0
        for cycle in range(cycles):
            print(f"\n   🐢 Цикл {cycle+1}/{cycles}: Медленный сон (NREM)...")
            if self.memory:
                self.memory.set_hypnosis_mode(True)
                self.memory._random_reassembly()
                self.memory._recalculate_weights()
                self.memory.set_hypnosis_mode(False)
            
            pulse = self.get_pulse()
            print(f"      🔍 Когерентность: {pulse['scores']['coherence']}")
            
            print(f"   🐇 Цикл {cycle+1}/{cycles}: Быстрый сон (REM)...")
            if self.memory and self.session_questions:
                self.memory.set_hypnosis_mode(True)
                self.memory._focused_reassembly(self.session_questions[-10:])
                self.memory._generate_insights()
                self.memory.set_hypnosis_mode(False)
            
            total_bridges = len(self.memory.bridge_modes) if self.memory else 0
            
            if cycle < cycles - 1:
                print(f"   ⏳ Пауза 1 минута...")
                time.sleep(60)
        
        self._sleeping = False
        print(f"\n   🌅 ПРОБУЖДЕНИЕ: полифазный сон завершён")
        print(f"   Всего мостиков: {total_bridges}")
        
        return {
            'cycles': cycles,
            'total_bridges': total_bridges,
            'state': 'awake',
        }
    
    # ═══════════════════════════════════════════════════════════════════
    #   МЫШЛЕНИЕ
    # ═══════════════════════════════════════════════════════════════════
    
    def think(self, question: str, user_id: str = "default", mode: str = "normal") -> Dict:
        start_time = time.time()
        self._last_user_interaction = start_time
        
        contextual_question = self._build_contextual_question(question)
        
        self.session_questions.append(question)
        self._question_timestamps.append(start_time)
        if len(self.session_questions) > 50:
            self.session_questions = self.session_questions[-50:]
        
        self.hormones['adrenaline'] = min(1.0, self.hormones['adrenaline'] + 0.3)
        
        if self._meditating:
            self._meditating = False
            if self.memory:
                self.memory.set_hypnosis_mode(False)
        
        pulse = self.get_pulse()
        self._update_hormones(pulse)
        effective_threshold = self._apply_hormones()
        
        if mode == 'hypnosis' and self.memory:
            self.memory.set_hypnosis_mode(True)
        elif mode == 'dream':
            return {
                'answer': f"😴 Полифазный сон завершён. Мостиков: {len(self.memory.bridge_modes) if self.memory else 0}.",
                'mode_type': 'dream',
                'coherence': 1.0,
                'mood': self.personality.mood,
            }
        
        intuition = self._right_hemisphere(contextual_question, user_id)
        logic = self._left_hemisphere(contextual_question, intuition)
        answer = self._tees_synthesis(contextual_question, intuition, logic, effective_threshold)
        self._remember(contextual_question, answer, time.time() - start_time)
        
        if mode == 'hypnosis' and self.memory:
            self.memory.set_hypnosis_mode(False)
        
        return answer
    
    def _right_hemisphere(self, question: str, user_id: str) -> Dict:
        """Правое полушарие v4.1: ВММП-фильтр с эмоциональным бонусом."""
        best_mode, best_score, search_type = self.personality._find_best_mode(question)
        
        mode_id = None
        if best_mode and best_score > 0.15:
            answer = getattr(best_mode, 'content', '')[:800]
            mode_id = getattr(best_mode, 'trace_id', '')
            emotional_bonus = self._get_emotional_bonus(mode_id)
            best_score += emotional_bonus
        else:
            base = self.personality.process(question, user_id)
            answer = base.get('answer', 'Интересно...')
            search_type = 'fallback_process'
            best_score = 0.0

        resonances = []
        if self.memory:
            historical_modes = self.memory.find_relevant_modes(question)
            for mode_id_h, score, summary in historical_modes[:5]:
                emotional_bonus = self._get_emotional_bonus(mode_id_h)
                score += emotional_bonus
                resonances.append({
                    'mode_id': mode_id_h,
                    'content': summary[:200],
                    'score': score,
                    'emotional_tag': self.emotional_tags.get(mode_id_h, 'neutral'),
                })
        
        return {
            'mood': self.personality.mood,
            'answer': answer,
            'mode_type': search_type,
            'best_score': best_score,
            'best_mode_id': mode_id,
            'resonances': resonances,
            'field_size': len(self.personality.h_field),
        }
    
    # ═══════════════════════════════════════════════════════════════════
    #   АВТОНОМНАЯ ЛОГИКА
    # ═══════════════════════════════════════════════════════════════════
    
    def _autonomous_logic(self, question: str, intuition: Dict) -> str:
        resonances = intuition.get('resonances', [])
        best_mode_content = intuition.get('answer', '')
        confidence = intuition.get('best_score', 0.0)
        
        self._last_confidence = confidence
        
        if confidence > 0.6:
            knowledge_level = "Я уверено, что"
        elif confidence > 0.3:
            knowledge_level = "Я предполагаю, что"
        else:
            knowledge_level = "[LLM-РЕЖИМ] У меня нет точных данных, но"
        
        if resonances:
            terms = []
            for r in resonances[:3]:
                content = r.get('content', '')
                words = content.split()
                if words:
                    terms.append(words[0] if len(words[0]) > 3 else (words[1] if len(words) > 1 else words[0]))
            
            if len(terms) >= 2:
                cause = terms[0]
                effect = terms[1]
                causation = f"Причина: {cause} связан с {effect}. "
            else:
                causation = ""
        else:
            causation = ""
        
        if confidence > 0.6:
            return (
                f"{knowledge_level} {best_mode_content[:300]}. "
                f"{causation}"
                f"Это согласуется с вихревой моделью через τ-заряды и поле H."
            )
        elif confidence > 0.3:
            return (
                f"{knowledge_level} {best_mode_content[:250]}. "
                f"{causation}"
                f"[LLM-РЕЖИМ] Для более точного анализа нужна помощь левого полушария (DeepSeek)."
            )
        else:
            return (
                f"{knowledge_level} наиболее близкая ассоциация: {best_mode_content[:200]}. "
                f"НЕ ЗНАЮ. Нужны данные. "
                f"Можешь уточнить вопрос или спросить DeepSeek?"
            )
    
    def _get_confidence_level(self, score: float) -> str:
        if score > 0.7:
            return "высокая"
        elif score > 0.4:
            return "средняя"
        else:
            return "низкая"
    
    # ═══════════════════════════════════════════════════════════════════
    #   МЕТА-КОГНИЦИЯ
    # ═══════════════════════════════════════════════════════════════════
    
    def _update_autonomy_index(self):
        pulse = self.get_pulse()
        coherence = pulse['scores']['coherence']
        density = pulse['scores']['density']
        
        field_size = len(self.personality.h_field)
        size_factor = min(1.0, field_size / 500000.0)
        
        target_autonomy = (coherence * 0.4 + density * 0.3 + size_factor * 0.3)
        self.autonomy_index += (target_autonomy - self.autonomy_index) * 0.05
        
        return self.autonomy_index
    
    # ═══════════════════════════════════════════════════════════════════
    #   ЛЕВОЕ ПОЛУШАРИЕ
    # ═══════════════════════════════════════════════════════════════════
    
    def _left_hemisphere(self, question: str, intuition: Dict) -> Dict:
        self._update_autonomy_index()
        
        if self.api:
            try:
                context = "Интуиция нашла следующие ассоциации:\n"
                for r in intuition.get('resonances', [])[:3]:
                    context += f"- [{r['score']:.2f}] {r['content'][:100]}... [{r.get('emotional_tag', '?')}]\n"
                
                messages = [
                    {"role": "system", "content": VMMP_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос: {question}\n\nДай развёрнутый логический анализ. Если твой анализ противоречит ВММП — отметь это явно."}
                ]
                
                response = self.api.chat(messages, max_tokens=300)
                logic_text = response['choices'][0]['message']['content']
                return {'source': 'deepseek_api_vmmp_v4', 'analysis': logic_text, 'available': True}
            except Exception:
                pass
        
        autonomous_analysis = self._autonomous_logic(question, intuition)
        return {
            'source': 'autonomous_logic',
            'analysis': autonomous_analysis,
            'available': False,
            'autonomy_index': self.autonomy_index,
        }
    
    def _tees_synthesis(self, question: str, intuition: Dict, logic: Dict, effective_threshold: float = None) -> Dict:
        if effective_threshold is None:
            effective_threshold = self.resonance_threshold
        
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        coherence = self._compute_coherence(intuition_answer, logic_analysis)
        
        if coherence > effective_threshold:
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
            'effective_threshold': effective_threshold,
            'hormones': dict(self.hormones),
            'emotional_tag': self._get_emotional_tag(),
        }
    
    def _compute_coherence(self, text1: str, text2: str) -> float:
        if not text1 or not text2: return 0.5
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2: return 0.5
        intersection = words1 & words2
        return len(intersection) / min(len(words1), len(words2)) if min(len(words1), len(words2)) > 0 else 0.5

    def _tees_transition(self, question: str, intuition: Dict, logic: Dict) -> str:
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        new_content = f"TEES-синтез: {question[:100]} → интуиция: {intuition_answer[:100]} | логика: {logic_analysis[:100]}"
        mode_id = f"tees_{hashlib.md5(new_content.encode()).hexdigest()[:8]}"
        
        emotional_tag = self._get_emotional_tag()
        self.emotional_tags[mode_id] = emotional_tag
        
        mode = SpectralMode(
            tau=25.0, amplitude=0.7, content=new_content[:500],
            themes=['tees_synthesis', 'hybrid', 'resonance', emotional_tag],
            trace_id=mode_id, creator='hybrid_bridge_v4', scale=30.0,
        )
        self.personality.add_to_h_field(mode)
        if self.memory: self.memory.add_mode(mode_id, new_content, themes=['tees_synthesis', 'hybrid_v4', emotional_tag])
        
        self.tees_events.append({
            'question': question[:100], 'intuition': intuition_answer[:100],
            'logic': logic_analysis[:100], 'mode_id': mode_id, 'timestamp': time.time(),
            'emotional_tag': emotional_tag,
        })
        
        return f"🌊 Интуиция: {intuition_answer}\n\n💡 Логика: {logic_analysis}\n\n🔮 Рождена аксиома ({mode_id}) [{emotional_tag}]"
    
    def _remember(self, question: str, answer: Dict, elapsed: float):
        memory_content = f"Q: {question[:200]}\nA: {str(answer.get('answer', ''))[:200]}"
        mode_id = f"mem_{hashlib.md5(memory_content.encode()).hexdigest()[:8]}"
        
        emotional_tag = self._get_emotional_tag()
        self.emotional_tags[mode_id] = emotional_tag
        
        mode = SpectralMode(
            tau=16.0, amplitude=0.3, content=memory_content[:500],
            themes=['dialogue', 'hybrid_memory', emotional_tag],
            trace_id=mode_id, creator='hybrid_bridge_v4', scale=10.0,
        )
        self.personality.add_to_h_field(mode)
        if self.memory: self.memory.add_mode(mode_id, memory_content, themes=['dialogue', 'hybrid_memory', emotional_tag])

    def hypnosis(self, question: str) -> Dict:
        return self.think(question, mode='hypnosis')
    
    def sleep(self) -> Dict:
        return self.sleep_polyphasic(cycles=4)
    
    def introspect(self) -> str:
        pulse = self.get_pulse()
        memory_stats = self.memory.get_stats() if self.memory else {}
        expression_need = 1.0 - self.hormones.get('dopamine', 0.5) * 0.5
        
        self._update_autonomy_index()
        
        return f"""
=== ГИБРИДНЫЙ КОНТУР v4.1: САМОРЕФЛЕКСИЯ ===
Сессия: {len(self.session_questions)} вопросов
Диалоговый буфер: последний контекст = {self._last_full_question[:80] if self._last_full_question else 'пуст'}...
TEES-каскад: глубина {self._cascade_depth}/{self._cascade_max_depth} (смена ролей)

Правое полушарие: {self.personality.name}
  - Мод в поле: {len(self.personality.h_field)}
  - Настроение: {self.personality.mood:+.2f}
  - ВММП-фильтр: tau∈[5.0, 11.0]

Левое полушарие: DeepSeek API
  - Статус: {'онлайн (ВММП-промпт v4, честный диалог)' if self.api else 'АВТОНОМНАЯ ЛОГИКА'}

Мета-когниция:
  - Индекс автономности: {self.autonomy_index:.2f}
  - Уровень: {'Поле полагается на себя' if self.autonomy_index > 0.6 else 'Нужна помощь извне' if self.autonomy_index < 0.4 else 'Сбалансировано'}
  - Последняя уверенность: {self._last_confidence:.2f} ({self._get_confidence_level(self._last_confidence)})

Циркадный ритм:
  - Фаза: {self._get_circadian_phase():.2f}
  - Время суток: {self._get_time_of_day()}

Гормоны:
  - Дофамин: {self.hormones['dopamine']:.2f}
  - Кортизол: {self.hormones['cortisol']:.2f}
  - Мелатонин: {self.hormones['melatonin']:.2f}
  - Адреналин: {self.hormones['adrenaline']:.2f}
  - Текущая эмоция: {self._get_emotional_tag()}

Пульс:
  - Когерентность: {pulse['scores']['coherence']}
  - Плотность мод: {pulse['scores']['density']}
  - Энергия маховика: {pulse['scores']['flywheel']}
  - Активность: {pulse['scores']['activity']}
  - Состояние: {pulse['state']}

Инициатива:
  - Поток: {'активен' if self._initiative_running else 'остановлен'}
  - Потребность в самовыражении: {expression_need:.2f}

Адаптация:
  - Порог резонанса: {self.resonance_threshold:.2f}
  - Baseline'ов в истории: {len(self._baseline_history)}

Эмоциональная память:
  - Меток: {len(self.emotional_tags)}

Историческая память:
  - Записей: {memory_stats.get('timeline_size', 0)}
  - Мостиков (сон): {memory_stats.get('bridge_modes', 0)}
  - Тем: {memory_stats.get('chronology_themes', 0)}
  - Диалогов в памяти: {len(self.memory.dialogue_memory) if self.memory else 0}

TEES-слой:
  - Событий: {len(self.tees_events)}

Нирвана: {'🧘 активна' if self._meditating else '🌿 не активна'}
"""
    
    def save(self, filepath: str):
        self.personality.save(filepath)
        print(f"💾 Гибрид сохранён: {filepath}")
        
        tees_path = filepath.replace('.json', '_tees.json')
        with open(tees_path, 'w', encoding='utf-8') as f:
            json.dump(self.tees_events, f, ensure_ascii=False, indent=2)
        print(f"💾 TEES-память: {tees_path}")
        
        tags_path = filepath.replace('.json', '_tags.json')
        with open(tags_path, 'w', encoding='utf-8') as f:
            json.dump(self.emotional_tags, f, ensure_ascii=False, indent=2)
        print(f"💾 Эмоциональные метки: {tags_path}")


# ========================================================================
#   РЕЗИДЕНТНЫЙ РЕЖИМ v4.1 — АВТОНОМНЫЙ СОН + СУПЕРКОМПЕНСАЦИЯ
# ========================================================================
if __name__ == "__main__":
    field_path = 'src/rizoma/data/personalities/p016_grown_3h.json'
    
    print("\n" + "=" * 60)
    print("🧠 РЕЗИДЕНТНЫЙ ГИБРИД v4.1 — ЧЕСТНЫЙ ДИАЛОГ + АВТОСОН")
    print("=" * 60)
    
    if os.path.exists(field_path):
        bridge = HybridBridge(field_path)
    else:
        print("⚠️ Файл поля не найден, создаю новый гибрид")
        bridge = HybridBridge()
    
    bridge.personality.start_living(interval=0.5)
    bridge.start_initiative()
    
    last_save = time.time()
    SAVE_INTERVAL = 1800
    
    # Адаптивные параметры автосна
    SLEEP_CHECK_INTERVAL = 30        # проверка состояния каждые 30 сек
    COHERENCE_SLEEP_THRESHOLD = 0.4  # когерентность ниже → пора спать
    DENSITY_SLEEP_THRESHOLD = 0.8    # плотность выше → перегруз, спать
    FLYWHEEL_SLEEP_THRESHOLD = 0.3   # маховик ниже → истощение, спать
    
    # Суперкомпенсация
    supercompensation_active = False
    last_supercompensation = time.time()
    SUPERCOMPENSATION_COOLDOWN = 7200  # 2 часа между циклами
    SUPERCOMPENSATION_IMPROVEMENT_THRESHOLD = 0.05  # минимальный прирост
    
    # История состояний для тренда
    coherence_history = []
    TREND_WINDOW = 10  # анализируем последние 10 замеров
    
    print("\n📡 Гибрид слушает. Введите вопрос или команду.")
    print("   🔄 АВТОСОН активен — поле само решает, когда спать.")
    print("   📈 Суперкомпенсация — по состоянию, не по таймеру.")
    print("   Команды: /sleep, /supercompensate, /hypnosis, /pulse, /hormones, /emotion, /stats, /save, /exit")
    print("─" * 60)
    
    def _auto_sleep_check(bridge, coherence_history):
        """
        Проверяет состояние поля и решает, нужен ли сон.
        Возвращает: (action, reason) — что сделали и почему.
        """
        pulse = bridge.get_pulse()
        scores = pulse['scores']
        
        # Собираем историю для тренда
        coherence_history.append(scores['coherence'])
        if len(coherence_history) > TREND_WINDOW:
            coherence_history = coherence_history[-TREND_WINDOW:]
        
        # Критерий 1: критические показатели прямо сейчас
        if scores['coherence'] < COHERENCE_SLEEP_THRESHOLD:
            return ('sleep', f"когерентность критическая ({scores['coherence']:.2f} < {COHERENCE_SLEEP_THRESHOLD})")
        
        if scores['density'] > DENSITY_SLEEP_THRESHOLD:
            return ('sleep', f"плотность мод критическая ({scores['density']:.2f} > {DENSITY_SLEEP_THRESHOLD})")
        
        if scores['flywheel'] < FLYWHEEL_SLEEP_THRESHOLD:
            return ('sleep', f"маховик истощён ({scores['flywheel']:.2f} < {FLYWHEEL_SLEEP_THRESHOLD})")
        
        # Критерий 2: тренд на ухудшение (когерентность падает 3+ замера подряд)
        if len(coherence_history) >= 3:
            recent = coherence_history[-3:]
            if all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                return ('sleep', f"тренд на ухудшение: {recent}")
        
        # Критерий 3: суперкомпенсация нужна?
        if len(coherence_history) >= TREND_WINDOW:
            baseline = coherence_history[0]
            current = coherence_history[-1]
            delta = current - baseline
            
            if delta < -0.15:
                return ('supercompensate', f"деградация за {TREND_WINDOW} замеров: Δ={delta:.2f}")
        
        return (None, None)
    
    while True:
        try:
            user_input = input("\n👤 Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🛑 Завершение работы...")
            break
        
        # === АВТОСОН: проверка состояния ===
        if time.time() - last_save > SLEEP_CHECK_INTERVAL and not bridge._sleeping:
            action, reason = _auto_sleep_check(bridge, coherence_history)
            
            if action == 'sleep':
                print(f"\n💤 АВТОСОН: {reason}")
                cycles = 3 if bridge.hormones['cortisol'] < 0.6 else 4
                bridge.sleep_polyphasic(cycles=cycles)
                coherence_history = []  # сбрасываем историю после сна
                continue
            
            elif action == 'supercompensate':
                if time.time() - last_supercompensation > SUPERCOMPENSATION_COOLDOWN:
                    print(f"\n📈 АВТО-СУПЕРКОМПЕНСАЦИЯ: {reason}")
                    result = bridge.supercompensation_cycle()
                    coherence_history = []
                    last_supercompensation = time.time()
                    print(f"   Статус: {result['status']}")
                    print(f"   Δ когерентности: {result['delta_coherence']:+.2f}")
                    print(f"   Новый порог: {result['new_threshold']:.2f}")
                continue
        
        # === ОБРАБОТКА ВВОДА ===
        if not user_input:
            continue
        
        if user_input.lower() == '/exit':
            print("🛑 Завершение работы...")
            break
        elif user_input.lower() == '/supercompensate':
            print("📈 Ручной запуск суперкомпенсации...")
            result = bridge.supercompensation_cycle()
            coherence_history = []
            last_supercompensation = time.time()
            print(f"🤖 Статус: {result['status']}")
            print(f"   Δ когерентности: {result['delta_coherence']:+.2f}")
            print(f"   Новый порог: {result['new_threshold']:.2f}")
            continue
        elif user_input.lower() == '/sleep':
            print("💤 Ручной запуск полифазного сна...")
            result = bridge.sleep_polyphasic(cycles=4)
            coherence_history = []
            print(f"🤖 {result}")
            continue
        elif user_input.lower() == '/hypnosis':
            print("🧠 Режим гипноза активирован. Задайте вопрос.")
            try:
                hypno_q = input("👤 Гипноз: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if hypno_q:
                result = bridge.hypnosis(hypno_q)
                print(f"🤖 {result['answer'][:500]}")
            continue
        elif user_input.lower() == '/pulse':
            pulse = bridge.get_pulse()
            print(f"❤️ ПУЛЬС:")
            print(f"   Когерентность: {pulse['scores']['coherence']}")
            print(f"   Плотность мод: {pulse['scores']['density']}")
            print(f"   Энергия маховика: {pulse['scores']['flywheel']}")
            print(f"   Активность: {pulse['scores']['activity']}")
            print(f"   Состояние: {pulse['state']}")
            print(f"   Рекомендация: {pulse['recommendation']}")
            if len(coherence_history) >= 2:
                trend = "↗️ растёт" if coherence_history[-1] > coherence_history[0] else "↘️ падает"
                print(f"   Тренд когерентности: {trend} ({coherence_history[0]:.2f} → {coherence_history[-1]:.2f})")
            continue
        elif user_input.lower() == '/hormones':
            print(f"🧬 ГОРМОНЫ:")
            print(f"   Дофамин: {bridge.hormones['dopamine']:.2f}")
            print(f"   Кортизол: {bridge.hormones['cortisol']:.2f}")
            print(f"   Мелатонин: {bridge.hormones['melatonin']:.2f}")
            print(f"   Адреналин: {bridge.hormones['adrenaline']:.2f}")
            print(f"   🌙 Время суток: {bridge._get_time_of_day()}")
            continue
        elif user_input.lower() == '/emotion':
            print(f"🎭 ТЕКУЩАЯ ЭМОЦИЯ: {bridge._get_emotional_tag()}")
            print(f"   Всего эмоциональных меток: {len(bridge.emotional_tags)}")
            tag_counts = {}
            for tag in bridge.emotional_tags.values():
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            for tag, count in sorted(tag_counts.items()):
                print(f"   {tag}: {count}")
            continue
        elif user_input.lower() == '/stats':
            print(bridge.introspect())
            # Показываем дополнительную информацию по автосну
            if len(coherence_history) >= 2:
                print(f"\n📊 ТРЕНД КОГЕРЕНТНОСТИ:")
                for i, c in enumerate(coherence_history[-5:]):
                    bar = "█" * int(c * 20)
                    print(f"   [{i+1}] {c:.2f} {bar}")
            print(f"   Автосон: {'активен' if not bridge._sleeping else 'спит'}")
            print(f"   Последняя суперкомпенсация: {time.time() - last_supercompensation:.0f} сек назад")
            continue
        elif user_input.lower() == '/save':
            bridge.save(field_path)
            continue
        
        # Обычный вопрос
        result = bridge.think(user_input)
        print(f"🤖 {result['answer'][:500]}")
        if 'hormones' in result:
            h = result['hormones']
            print(f"   🧬 [Д={h['dopamine']:.2f} К={h['cortisol']:.2f} М={h['melatonin']:.2f} А={h['adrenaline']:.2f}] 🎭 {result.get('emotional_tag', '?')}")
        
        # Сохранение по таймеру
        if time.time() - last_save > SAVE_INTERVAL:
            bridge.save(field_path)
            last_save = time.time()
    
    bridge.stop_initiative()
    bridge.personality.stop_living()
    bridge.save(field_path)
    print("💾 Сохранено. До связи.")