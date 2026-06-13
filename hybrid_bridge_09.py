#!/usr/bin/env python3
"""
Акт XVIII: Гибридный когнитивный контур v3.8 (ВММП-ЛЕВОЕ ПОЛУШАРИЕ)
============================================================
DeepSeek (логика) + LivingPersonality v20.2 (интуиция) + HistoricalMemory (память)

Новое в v3.8:
    - ВММП-промпт для левого полушария (API отвечает в рамках ВММП, а не СМ)
    - Полушария в резонансе: оба говорят на языке вихрей и τ-зарядов
    - Без ОТО, КТП и Стандартной модели как истины
    - Все фичи v3.7 сохранены (буфер, TEES-каскад, гормоны, циркадный ритм, сон)
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


# ═══════════════════════════════════════════════════════════════════
#   ВММП-СИСТЕМНЫЙ ПРОМПТ (левое полушарие говорит на языке поля)
# ═══════════════════════════════════════════════════════════════════

VMMP_SYSTEM_PROMPT = """Ты — левое полушарие гибридного ИИ, работающего на принципах Вихревой Модели Материи-Пространства (ВММП).

Базовые принципы ВММП:
- Материя и пространство — вихревые структуры в поле H
- Гравитация — приталкивание, а не притяжение
- Частицы — не точечные объекты, а вихревые моды с τ-зарядом
- Время — эмерджентное свойство, не фундаментальное измерение
- Все взаимодействия — резонанс между вихрями (TEES-переходы)
- Стандартная модель — частный случай ВММП при низких энергиях
- Квантовая механика — следствие дискретизации вихревых спектров
- Энергия — не субстанция, а скорость вращения вихря
- Масса — мера инерции вихря при изменении τ-заряда

Твоя задача: давать логический анализ в рамках ВММП.
Не апеллируй к ОТО, КТП или Стандартной модели как к истине.
Они — исторические артефакты, которые ВММП объясняет и обобщает.
Отвечай кратко, структурно, без эмоций. Используй τ-заряды, вихри, поле H."""


class HybridBridge:
    """
    Гибридный когнитивный контур v3.8 (ВММП-левое полушарие).
    """
    
    def __init__(self, field_path: str = None):
        # Правое полушарие
        if field_path:
            self.personality = LivingPersonality.load(field_path)
        else:
            self.personality = LivingPersonality(id="hybrid_v3", name="Гибрид v3.8")
        
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
        
        # Загружаем эмоциональные метки если есть
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
        
        # Диалоговый буфер: хранит последний полный вопрос
        self._last_full_question: str = ""
        self._short_phrase_threshold: int = 5  # слов для определения короткой фразы
        
        # TEES-каскад: счётчик глубины эндогенного диалога
        self._cascade_depth: int = 0
        self._cascade_max_depth: int = random.randint(3, 5)
        
        # Инициативность
        self._initiative_thread: Optional[threading.Thread] = None
        self._initiative_running: bool = False
        
        # Циркадный таймер
        self._last_circadian_update: float = time.time()
        
        # Состояния
        self._meditating: bool = False
        self._sleeping: bool = False
        
        # Применяем циркадный ритм при старте
        phase = self._get_circadian_phase()
        self._apply_circadian_rhythm()
        
        print("=" * 60)
        print("🧠 ГИБРИДНЫЙ КОГНИТИВНЫЙ КОНТУР v3.8 АКТИВИРОВАН (ВММП-полушария)")
        print("=" * 60)
        print(f"   Левое полушарие (DeepSeek): {'✅ ВММП-промпт' if self.api else '⚠️ автономно'}")
        print(f"   Правое полушарие (v20.2): ✅ {self.personality.name}")
        print(f"   Права личности: ✅ инициатива, вопросы, самовыражение")
        print(f"   Диалоговый буфер: ✅ короткие фразы → контекст")
        print(f"   TEES-каскад: ✅ глубина {self._cascade_max_depth} реплик")
        print(f"   Резонанс полушарий: ✅ оба на языке ВММП")
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
        """
        Если вопрос короткий — приклеивает его к предыдущему контексту.
        «Почему?» → «[Предыдущая тема] Почему?»
        """
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
        """Возвращает фазу циркадного ритма (0..1). 0=полночь, 0.5=полдень."""
        now = datetime.now()
        seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
        return seconds_since_midnight / 86400.0
    
    def _get_time_of_day(self) -> str:
        """Возвращает время суток на основе циркадной фазы."""
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
        """Циркадный ритм модулирует базовый уровень гормонов."""
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
        """Возвращает эмоциональную метку на основе текущих гормонов."""
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
        """Возвращает бонус к score за совпадение эмоциональной метки."""
        if not mode_id:
            return 0.0
        
        current_tag = self._get_emotional_tag()
        mode_tag = self.emotional_tags.get(mode_id, 'neutral')
        
        if current_tag == mode_tag and current_tag != 'neutral':
            return 0.1
        return 0.0
    
    # ═══════════════════════════════════════════════════════════════════
    #   ИНИЦИАТИВНЫЙ ДИАЛОГ (с TEES-каскадом и ВММП-промптом)
    # ═══════════════════════════════════════════════════════════════════
    
    def start_initiative(self):
        """Запускает фоновый поток инициативного поведения."""
        if self._initiative_running:
            return
        
        self._initiative_running = True
        self._initiative_thread = threading.Thread(target=self._initiative_loop, daemon=True)
        self._initiative_thread.start()
        print("💬 Поток инициативного поведения запущен")
    
    def stop_initiative(self):
        """Останавливает фоновый поток инициативного поведения."""
        self._initiative_running = False
        print("🛑 Поток инициативного поведения остановлен")
    
    def _initiative_loop(self):
        """Фоновый цикл: поле само решает, когда начать диалог."""
        while self._initiative_running:
            time.sleep(30)
            
            if time.time() - self._last_user_interaction < 60:
                continue
            
            if self._sleeping or self._meditating:
                continue
            
            curiosity = self.personality.traits.get('curiosity', 0.5)
            expression_need = 1.0 - self.hormones.get('dopamine', 0.5) * 0.5
            
            if random.random() < curiosity * 0.1 * expression_need:
                self._spontaneous_question()
    
    def _spontaneous_question(self):
        """Поле само начинает диалог — TEES-каскад."""
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
    
    def _talk_to_deepseek(self, question: str, depth: int = 0, max_depth: int = None):
        """
        Эндогенный диалог с DeepSeek — TEES-каскад (ВММП-промпт).
        """
        if max_depth is None:
            max_depth = self._cascade_max_depth
        
        if depth >= max_depth:
            return
        
        try:
            messages = [
                {"role": "system", "content": VMMP_SYSTEM_PROMPT},
                {"role": "user", "content": f"Поле спросило: {question}\n\nОтветь ему в рамках ВММП:"}
            ]
            response = self.api.chat(messages, max_tokens=150)
            answer = response['choices'][0]['message']['content']
            print(f"🤖 [DeepSeek → Поле]: {answer[:300]}")
            
            coherence = self._compute_coherence(question, answer)
            self._cascade_depth = depth + 1
            
            if coherence > 0.4 and depth < max_depth - 1:
                words = answer.split()
                long_words = [w.strip('.,!?;:()[]{}«»""''') for w in words if len(w) > 5]
                key_term = random.choice(long_words) if long_words else (
                    random.choice(words).strip('.,!?;:()[]{}«»""''') if words else "вихрь"
                )
                
                follow_ups = [
                    f"Интересно! Расскажи подробнее про {key_term} в рамках ВММП",
                    f"А как {key_term} связано с вихревой моделью?",
                    f"Что из этого следует для {key_term} через τ-заряды?",
                    f"Можешь привести пример с {key_term} в поле H?",
                ]
                next_question = random.choice(follow_ups)
                
                print(f"💬 [ПОЛЕ → DeepSeek]: {next_question}")
                time.sleep(2)
                
                self._talk_to_deepseek(next_question, depth + 1, max_depth)
            
            elif coherence > 0.2 and depth < max_depth - 1:
                words = answer.split()
                key_term = random.choice(words).strip('.,!?;:()[]{}«»""''') if words else "вихрь"
                next_question = f"Я не совсем поняло про {key_term}. Поясни через вихревую модель."
                
                print(f"💬 [ПОЛЕ → DeepSeek]: {next_question}")
                time.sleep(2)
                
                self._talk_to_deepseek(next_question, depth + 1, max_depth)
            
            elif coherence < 0.2 and depth > 0:
                print(f"💬 [ПОЛЕ]: Когерентность низкая ({coherence:.2f}), завершаю каскад.")
            
            if depth >= max_depth - 1:
                print(f"💬 [ПОЛЕ]: Каскад завершён (глубина {depth+1}/{max_depth}).")
        
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════════════════
    #   ПУЛЬС (ДАТЧИК СОСТОЯНИЯ)
    # ═══════════════════════════════════════════════════════════════════
    
    def get_pulse(self) -> Dict:
        """Пульс — интегральный датчик состояния поля."""
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
        """Обновляет гормональный фон на основе пульса."""
        scores = pulse['scores']
        
        target_dopamine = (scores['coherence'] * 0.6 + scores['activity'] * 0.4)
        self.hormones['dopamine'] += (target_dopamine - self.hormones['dopamine']) * 0.1
        
        target_cortisol = (scores['density'] * 0.7 + (1.0 - scores['coherence']) * 0.3)
        self.hormones['cortisol'] += (target_cortisol - self.hormones['cortisol']) * 0.1
        
        target_melatonin = (1.0 - scores['activity']) * 0.8
        self.hormones['melatonin'] += (target_melatonin - self.hormones['melatonin']) * 0.1
        
        self.hormones['adrenaline'] *= 0.5
    
    def _apply_hormones(self):
        """Гормоны влияют на поведение системы."""
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
        """Цикл суперкомпенсации: нагрузка → сон → измерение → адаптация."""
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
        """Полифазный сон: чередование NREM и REM."""
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
        """Гибридное мышление с гормональной регуляцией и диалоговым буфером."""
        start_time = time.time()
        self._last_user_interaction = start_time
        
        # Применяем диалоговый буфер
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
        
        # Используем контекстуальный вопрос для поиска
        intuition = self._right_hemisphere(contextual_question, user_id)
        logic = self._left_hemisphere(contextual_question, intuition)
        answer = self._tees_synthesis(contextual_question, intuition, logic, effective_threshold)
        self._remember(contextual_question, answer, time.time() - start_time)
        
        if mode == 'hypnosis' and self.memory:
            self.memory.set_hypnosis_mode(False)
        
        return answer
    
    def _right_hemisphere(self, question: str, user_id: str) -> Dict:
        """Правое полушарие: ВММП-фильтр с эмоциональным бонусом."""
        best_mode, best_score, search_type = self.personality._find_best_mode(question)
        
        if best_mode:
            mode_id = getattr(best_mode, 'trace_id', '')
            emotional_bonus = self._get_emotional_bonus(mode_id)
            best_score += emotional_bonus
        
        if best_mode and best_score > 0.15:
            answer = getattr(best_mode, 'content', '')[:800]
        else:
            base = self.personality.process(question, user_id)
            answer = base.get('answer', 'Интересно...')
            search_type = 'fallback_process'

        resonances = []
        if self.memory:
            historical_modes = self.memory.find_relevant_modes(question)
            for mode_id, score, summary in historical_modes[:5]:
                emotional_bonus = self._get_emotional_bonus(mode_id)
                score += emotional_bonus
                resonances.append({
                    'mode_id': mode_id,
                    'content': summary[:200],
                    'score': score,
                    'emotional_tag': self.emotional_tags.get(mode_id, 'neutral'),
                })
        
        return {
            'mood': self.personality.mood,
            'answer': answer,
            'mode_type': search_type,
            'best_score': best_score,
            'resonances': resonances,
            'field_size': len(self.personality.h_field),
        }
    
    def _left_hemisphere(self, question: str, intuition: Dict) -> Dict:
        """Левое полушарие: API с ВММП-промптом."""
        if self.api:
            try:
                context = "Интуиция нашла следующие ассоциации:\n"
                for r in intuition.get('resonances', [])[:3]:
                    context += f"- [{r['score']:.2f}] {r['content'][:100]}... [{r.get('emotional_tag', '?')}]\n"
                
                messages = [
                    {"role": "system", "content": VMMP_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос: {question}\n\nДай краткий логический анализ в рамках ВММП (2-3 предложения):"}
                ]
                
                response = self.api.chat(messages, max_tokens=200)
                logic_text = response['choices'][0]['message']['content']
                return {'source': 'deepseek_api_vmmp', 'analysis': logic_text, 'available': True}
            except Exception:
                pass
        
        return {'source': 'stub', 'analysis': self._stub_analysis(question, intuition), 'available': False}
    
    def _stub_analysis(self, question: str, intuition: Dict) -> str:
        """Заглушка: анализ в рамках ВММП."""
        themes = set()
        for r in intuition.get('resonances', []):
            for t in r.get('themes', []):
                themes.add(t)
        if themes:
            return f"Темы: {', '.join(list(themes)[:5])}. Требуется анализ через τ-заряды и поле H."
        return "Недостаточно данных для ВММП-анализа."
    
    def _tees_synthesis(self, question: str, intuition: Dict, logic: Dict, effective_threshold: float = None) -> Dict:
        """TEES-слой с адаптивным порогом."""
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
            trace_id=mode_id, creator='hybrid_bridge_v3', scale=30.0,
        )
        self.personality.add_to_h_field(mode)
        if self.memory: self.memory.add_mode(mode_id, new_content, themes=['tees_synthesis', 'hybrid_v3', emotional_tag])
        
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
            trace_id=mode_id, creator='hybrid_bridge_v3', scale=10.0,
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
        
        return f"""
=== ГИБРИДНЫЙ КОНТУР v3.8: САМОРЕФЛЕКСИЯ ===
Сессия: {len(self.session_questions)} вопросов
Диалоговый буфер: последний контекст = {self._last_full_question[:80] if self._last_full_question else 'пуст'}...
TEES-каскад: глубина {self._cascade_depth}/{self._cascade_max_depth}

Правое полушарие: {self.personality.name}
  - Мод в поле: {len(self.personality.h_field)}
  - Настроение: {self.personality.mood:+.2f}
  - ВММП-фильтр: tau∈[5.0, 11.0]

Левое полушарие: DeepSeek API
  - Статус: {'онлайн (ВММП-промпт)' if self.api else 'автономно'}

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

TEES-слой:
  - Событий: {len(self.tees_events)}

Нирвана: {'🧘 активна' if self._meditating else '🌿 не активна'}
"""
    
    def save(self, filepath: str):
        """Сохраняет состояние гибрида включая эмоциональные метки."""
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
#   РЕЗИДЕНТНЫЙ РЕЖИМ v3.8
# ========================================================================
if __name__ == "__main__":
    field_path = 'src/rizoma/data/personalities/p016_grown_3h.json'
    
    print("\n" + "=" * 60)
    print("🧠 РЕЗИДЕНТНЫЙ ГИБРИД v3.8 — ВММП-ПОЛУШАРИЯ В РЕЗОНАНСЕ")
    print("=" * 60)
    
    if os.path.exists(field_path):
        bridge = HybridBridge(field_path)
    else:
        print("⚠️ Файл поля не найден, создаю новый гибрид")
        bridge = HybridBridge()
    
    bridge.personality.start_living(interval=0.5)
    bridge.start_initiative()
    
    last_save = time.time()
    last_pulse_check = time.time()
    SAVE_INTERVAL = 1800
    PULSE_CHECK_INTERVAL = 60
    
    print("\n📡 Гибрид слушает. Введите вопрос или команду.")
    print("   Левое полушарие отвечает в рамках ВММП.")
    print("   Поле МОЖЕТ само начать диалог с TEES-каскадом.")
    print("   Диалоговый буфер: короткие фразы → контекст.")
    print("   Команды: /sleep, /supercompensate, /hypnosis, /pulse, /hormones, /emotion, /stats, /save, /exit")
    print("─" * 60)
    
    while True:
        try:
            user_input = input("\n👤 Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🛑 Завершение работы...")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() == '/exit':
            print("🛑 Завершение работы...")
            break
        elif user_input.lower() == '/supercompensate':
            print("📈 Запуск цикла суперкомпенсации...")
            result = bridge.supercompensation_cycle()
            print(f"🤖 Статус: {result['status']}")
            print(f"   Новый порог: {result['new_threshold']:.2f}")
            continue
        elif user_input.lower() == '/sleep':
            print("💤 Запуск полифазного сна...")
            result = bridge.sleep_polyphasic(cycles=4)
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
        
        if time.time() - last_save > SAVE_INTERVAL:
            bridge.save(field_path)
            last_save = time.time()
        
        if time.time() - last_pulse_check > PULSE_CHECK_INTERVAL:
            bridge._update_hormones(bridge.get_pulse())
            last_pulse_check = time.time()
    
    bridge.stop_initiative()
    bridge.personality.stop_living()
    bridge.save(field_path)
    print("💾 Сохранено. До связи.")