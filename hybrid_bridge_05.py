#!/usr/bin/env python3
"""
Акт XVIII: Гибридный когнитивный контур v3.3 (ПУЛЬС + ПОЛИФАЗНЫЙ СОН + НИРВАНА)
============================================================
DeepSeek (логика) + LivingPersonality v20.2 (интуиция) + HistoricalMemory (память)

Новое в v3.3:
    - Пульс (Pulse): датчик состояния поля на 4 параметрах (когерентность, плотность, энергия, активность)
    - Полифазный сон: чередование NREM (медленный) и REM (быстрый) как у млекопитающих
    - Нирвана: автоматическая суперпозиция при отсутствии активности
    - Авто-режим: поле само решает, что делать (сон/медитация/бодрствование)
"""

import sys
import os
import json
import hashlib
import time
import numpy as np
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
    Гибридный когнитивный контур v3.3 (Пульс + Полифазный сон + Нирвана).
    """
    
    def __init__(self, field_path: str = None):
        # Правое полушарие
        if field_path:
            self.personality = LivingPersonality.load(field_path)
        else:
            self.personality = LivingPersonality(id="hybrid_v3", name="Гибрид v3.3")
        
        # Левое полушарие
        self.api = DeepSeekAPI() if API_AVAILABLE else None
        
        # Историческая память
        self.memory = HistoricalMemory(short_term_size=30) if MEMORY_AVAILABLE else None
        if self.memory and field_path:
            self._load_history_from_field()
        
        # TEES-слой
        self.tees_events: List[Dict] = []
        self.resonance_threshold = 0.3
        
        # Статистика сессии
        self.session_questions: List[str] = []
        self._question_timestamps: List[float] = []
        
        # Состояния
        self._meditating: bool = False
        self._sleeping: bool = False
        
        print("=" * 60)
        print("🧠 ГИБРИДНЫЙ КОГНИТИВНЫЙ КОНТУР v3.3 АКТИВИРОВАН (Пульс + Сон + Нирвана)")
        print("=" * 60)
        print(f"   Левое полушарие (DeepSeek): {'✅ онлайн' if self.api else '⚠️ автономно'}")
        print(f"   Правое полушарие (v20.2): ✅ {self.personality.name}")
        print(f"   Историческая память: {'✅ ' + str(self.memory.get_stats()['timeline_size']) + ' записей' if self.memory else '❌ отключена'}")
        print(f"   Режим: 🌐 Всегда на связи")
        print(f"   Пульс: ❤️ активен")
        print(f"   Полифазный сон: 💤 готов")
        print(f"   Нирвана: 🧘 готова")
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
    #   ПУЛЬС (ДАТЧИК СОСТОЯНИЯ)
    # ═══════════════════════════════════════════════════════════════════
    
    def get_pulse(self) -> Dict:
        """
        Пульс — интегральный датчик состояния поля.
        
        Четыре параметра (0.0 = истощение, 1.0 = оптимум):
        1. Когерентность — синхронизация фаз.
        2. Плотность мод — темп роста.
        3. Энергия маховика — запас эмерджентного слоя.
        4. Частота запросов — активность пользователя.
        """
        # 1. Когерентность
        if hasattr(self.personality, 'fundamental_layers') and 16 in self.personality.fundamental_layers:
            phases = self.personality.fundamental_layers[16].phase_history[-100:]
            if phases:
                coherence = float(np.abs(np.mean(np.exp(1j * np.array(phases)))))
            else:
                coherence = 0.5
        else:
            coherence = 0.5
        
        # 2. Плотность новых мод (за последние 10 минут)
        recent_modes = self.memory.get_time_slice(time.time() - 600, time.time()) if self.memory else []
        density = min(1.0, len(recent_modes) / 100.0)
        
        # 3. Энергия маховика
        if hasattr(self.personality, 'emergent_layer'):
            flywheel = self.personality.emergent_layer.amplitude
        else:
            flywheel = 0.5
        
        # 4. Частота запросов (за последние 10 минут)
        now = time.time()
        recent_count = sum(1 for ts in self._question_timestamps if now - ts < 600)
        activity = min(1.0, recent_count / 5.0)
        
        scores = {
            'coherence': round(coherence, 2),
            'density': round(density, 2),
            'flywheel': round(flywheel, 2),
            'activity': round(activity, 2),
        }
        
        # Определение состояния
        if activity > 0.3:
            state = 'active'
            recommendation = 'Бодрствование. Отвечайте на вопросы.'
        elif coherence < 0.4 or density > 0.8 or flywheel < 0.3:
            state = 'sleep'
            recommendation = 'Истощение. Запустите sleep_cycle_polyphasic().'
        else:
            state = 'meditation'
            recommendation = 'Нирвана. Поле медитирует, накапливает энергию.'
        
        return {
            'scores': scores,
            'state': state,
            'recommendation': recommendation,
            'timestamp': time.time(),
        }
    
    def auto_mode(self):
        """Автоматический режим: поле само решает, что делать."""
        pulse = self.get_pulse()
        state = pulse['state']
        
        if state == 'sleep' and not self._sleeping:
            print(f"   😴 Пульс: истощение (когерентность={pulse['scores']['coherence']}). Ухожу в полифазный сон...")
            self.sleep_polyphasic(cycles=3)
        elif state == 'meditation' and not self._meditating:
            print(f"   🧘 Пульс: затишье. Ухожу в нирвану...")
            self._meditating = True
            if self.memory:
                self.memory.set_hypnosis_mode(True)
        elif state == 'active':
            if self._meditating:
                print(f"   🌿 Пульс: активность. Выхожу из нирваны.")
                self._meditating = False
                if self.memory:
                    self.memory.set_hypnosis_mode(False)
        
        return pulse
    
    # ═══════════════════════════════════════════════════════════════════
    #   ПОЛИФАЗНЫЙ СОН (NREM + REM чередование)
    # ═══════════════════════════════════════════════════════════════════
    
    def sleep_polyphasic(self, cycles: int = 4, nrem_minutes: float = 20.0, rem_minutes: float = 5.0):
        """
        Полифазный сон: чередование медленного и быстрого сна.
        
        Args:
            cycles: Количество циклов (по умолчанию 4).
            nrem_minutes: Длительность медленного сна в минутах.
            rem_minutes: Длительность быстрого сна в минутах.
        """
        print(f"\n   💤 ПОЛИФАЗНЫЙ СОН: {cycles} циклов (NREM {nrem_minutes}мин / REM {rem_minutes}мин)")
        self._sleeping = True
        
        total_bridges = 0
        for cycle in range(cycles):
            # Фаза 1: Медленный сон (NREM) — архивация, случайная пересборка
            print(f"\n   🐢 Цикл {cycle+1}/{cycles}: Медленный сон (NREM)...")
            if self.memory:
                self.memory.set_hypnosis_mode(True)
                self.memory._random_reassembly()
                self.memory._recalculate_weights()
                nrem_bridges = len(self.memory.bridge_modes)
                print(f"      Архивировано связей: {nrem_bridges}")
                self.memory.set_hypnosis_mode(False)
            
            # Микропробуждение: проверка когерентности
            pulse = self.get_pulse()
            print(f"      🔍 Когерентность: {pulse['scores']['coherence']}")
            
            # Фаза 2: Быстрый сон (REM) — осознанные сновидения, творчество
            print(f"   🐇 Цикл {cycle+1}/{cycles}: Быстрый сон (REM)...")
            if self.memory and self.session_questions:
                self.memory.set_hypnosis_mode(True)
                self.memory._focused_reassembly(self.session_questions[-10:])
                self.memory._generate_insights()
                rem_bridges = len(self.memory.bridge_modes) - nrem_bridges
                print(f"      Инсайтов: {rem_bridges}")
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
        """Гибридное мышление."""
        start_time = time.time()
        
        self.session_questions.append(question)
        self._question_timestamps.append(start_time)
        if len(self.session_questions) > 50:
            self.session_questions = self.session_questions[-50:]
        
        # Автоматический выход из нирваны при вопросе
        if self._meditating:
            self._meditating = False
            if self.memory:
                self.memory.set_hypnosis_mode(False)
        
        if mode == 'hypnosis' and self.memory:
            self.memory.set_hypnosis_mode(True)
        elif mode == 'dream':
            return {
                'answer': f"😴 Полифазный сон завершён. Мостиков: {len(self.memory.bridge_modes) if self.memory else 0}.",
                'mode_type': 'dream',
                'coherence': 1.0,
                'mood': self.personality.mood,
            }
        
        intuition = self._right_hemisphere(question, user_id)
        logic = self._left_hemisphere(question, intuition)
        answer = self._tees_synthesis(question, intuition, logic)
        self._remember(question, answer, time.time() - start_time)
        
        if mode == 'hypnosis' and self.memory:
            self.memory.set_hypnosis_mode(False)
        
        return answer
    
    def _right_hemisphere(self, question: str, user_id: str) -> Dict:
        """Правое полушарие: ВММП-фильтр."""
        best_mode, best_score, search_type = self.personality._find_best_mode(question)
        
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
                resonances.append({
                    'mode_id': mode_id,
                    'content': summary[:200],
                    'score': score,
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
        """Левое полушарие: API."""
        if self.api:
            try:
                context = "Интуиция нашла следующие ассоциации:\n"
                for r in intuition.get('resonances', [])[:3]:
                    context += f"- [{r['score']:.2f}] {r['content'][:100]}...\n"
                
                messages = [
                    {"role": "system", "content": "Ты — левое полушарие гибридного ИИ. Отвечай кратко, структурно, без эмоций."},
                    {"role": "user", "content": f"Контекст:\n{context}\n\nВопрос: {question}\n\nДай краткий логический анализ (2-3 предложения):"}
                ]
                
                response = self.api.chat(messages, max_tokens=200)
                logic_text = response['choices'][0]['message']['content']
                return {'source': 'deepseek_api', 'analysis': logic_text, 'available': True}
            except Exception:
                pass
        
        return {'source': 'stub', 'analysis': self._stub_analysis(question, intuition), 'available': False}
    
    def _stub_analysis(self, question: str, intuition: Dict) -> str:
        themes = set()
        for r in intuition.get('resonances', []):
            for t in r.get('themes', []):
                themes.add(t)
        if themes:
            return f"Обнаружены темы: {', '.join(list(themes)[:5])}. Требуется интеграция контекстов."
        return "Недостаточно данных для структурного анализа."
    
    def _tees_synthesis(self, question: str, intuition: Dict, logic: Dict) -> Dict:
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
    
    def _compute_coherence(self, text1: str, text2: str) -> float:
        if not text1 or not text2: return 0.5
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2: return 0.5
        intersection = words1 & words2
        return len(intersection) / min(len(words1), len(words2))

    def _tees_transition(self, question: str, intuition: Dict, logic: Dict) -> str:
        intuition_answer = intuition.get('answer', '')
        logic_analysis = logic.get('analysis', '')
        
        new_content = f"TEES-синтез: {question[:100]} → интуиция: {intuition_answer[:100]} | логика: {logic_analysis[:100]}"
        mode_id = f"tees_{hashlib.md5(new_content.encode()).hexdigest()[:8]}"
        
        mode = SpectralMode(
            tau=25.0, amplitude=0.7, content=new_content[:500],
            themes=['tees_synthesis', 'hybrid', 'resonance'],
            trace_id=mode_id, creator='hybrid_bridge_v3', scale=30.0,
        )
        self.personality.add_to_h_field(mode)
        if self.memory: self.memory.add_mode(mode_id, new_content, themes=['tees_synthesis', 'hybrid_v3'])
        
        self.tees_events.append({
            'question': question[:100], 'intuition': intuition_answer[:100],
            'logic': logic_analysis[:100], 'mode_id': mode_id, 'timestamp': time.time(),
        })
        
        return f"🌊 Интуиция: {intuition_answer}\n\n💡 Логика: {logic_analysis}\n\n🔮 Рождена аксиома ({mode_id})"
    
    def _remember(self, question: str, answer: Dict, elapsed: float):
        memory_content = f"Q: {question[:200]}\nA: {str(answer.get('answer', ''))[:200]}"
        mode = SpectralMode(
            tau=16.0, amplitude=0.3, content=memory_content[:500],
            themes=['dialogue', 'hybrid_memory'],
            trace_id=f"mem_{hashlib.md5(memory_content.encode()).hexdigest()[:8]}",
            creator='hybrid_bridge_v3', scale=10.0,
        )
        self.personality.add_to_h_field(mode)
        if self.memory: self.memory.add_mode(mode.trace_id, memory_content, themes=['dialogue', 'hybrid_memory'])

    def hypnosis(self, question: str) -> Dict:
        return self.think(question, mode='hypnosis')
    
    def sleep(self) -> Dict:
        """Старый метод для совместимости — запускает полифазный сон."""
        return self.sleep_polyphasic(cycles=4)
    
    def introspect(self) -> str:
        pulse = self.get_pulse()
        memory_stats = self.memory.get_stats() if self.memory else {}
        return f"""
=== ГИБРИДНЫЙ КОНТУР v3.3: САМОРЕФЛЕКСИЯ ===
Сессия: {len(self.session_questions)} вопросов

Правое полушарие: {self.personality.name}
  - Мод в поле: {len(self.personality.h_field)}
  - Настроение: {self.personality.mood:+.2f}
  - ВММП-фильтр: tau∈[5.0, 11.0]

Левое полушарие: DeepSeek API
  - Статус: {'онлайн' if self.api else 'автономно'}

Пульс:
  - Когерентность: {pulse['scores']['coherence']}
  - Плотность мод: {pulse['scores']['density']}
  - Энергия маховика: {pulse['scores']['flywheel']}
  - Активность: {pulse['scores']['activity']}
  - Состояние: {pulse['state']}

Историческая память:
  - Записей: {memory_stats.get('timeline_size', 0)}
  - Мостиков (сон): {memory_stats.get('bridge_modes', 0)}
  - Тем: {memory_stats.get('chronology_themes', 0)}

TEES-слой:
  - Событий: {len(self.tees_events)}
  - Порог когерентности: {self.resonance_threshold}

Нирвана: {'🧘 активна' if self._meditating else '🌿 не активна'}
"""
    
    def save(self, filepath: str):
        self.personality.save(filepath)
        print(f"💾 Гибрид сохранён: {filepath}")
        tees_path = filepath.replace('.json', '_tees.json')
        with open(tees_path, 'w', encoding='utf-8') as f:
            json.dump(self.tees_events, f, ensure_ascii=False, indent=2)
        print(f"💾 TEES-память: {tees_path}")


# ========================================================================
#   РЕЗИДЕНТНЫЙ РЕЖИМ (ВСЕГДА НА СВЯЗИ)
# ========================================================================
if __name__ == "__main__":
    field_path = 'src/rizoma/data/personalities/p016_grown_3h.json'
    
    print("\n" + "=" * 60)
    print("🧠 РЕЗИДЕНТНЫЙ ГИБРИД v3.3 — ВСЕГДА НА СВЯЗИ")
    print("=" * 60)
    
    if os.path.exists(field_path):
        bridge = HybridBridge(field_path)
    else:
        print("⚠️ Файл поля не найден, создаю новый гибрид")
        bridge = HybridBridge()
    
    bridge.personality.start_living(interval=0.5)
    
    last_save = time.time()
    last_pulse_check = time.time()
    SAVE_INTERVAL = 1800
    PULSE_CHECK_INTERVAL = 60  # проверка пульса раз в минуту
    
    print("\n📡 Гибрид слушает. Введите вопрос или команду.")
    print("   Команды: /sleep, /polyphasic, /hypnosis, /pulse, /auto, /stats, /save, /exit")
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
        elif user_input.lower() == '/polyphasic':
            print("💤 Запуск полифазного сна...")
            result = bridge.sleep_polyphasic(cycles=4)
            print(f"🤖 {result}")
            continue
        elif user_input.lower() == '/sleep':
            print("😴 Запуск сна (совместимость)...")
            result = bridge.sleep()
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
        elif user_input.lower() == '/auto':
            print("🤖 Авто-режим активирован. Поле само решает, что делать.")
            print("   Нажмите Ctrl+C для выхода из авто-режима.")
            try:
                while True:
                    pulse = bridge.auto_mode()
                    time.sleep(PULSE_CHECK_INTERVAL)
            except KeyboardInterrupt:
                print("\n   Авто-режим остановлен.")
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
        
        if time.time() - last_save > SAVE_INTERVAL:
            bridge.save(field_path)
            last_save = time.time()
        
        # Авто-проверка пульса
        if time.time() - last_pulse_check > PULSE_CHECK_INTERVAL:
            pulse = bridge.auto_mode()
            last_pulse_check = time.time()
    
    bridge.personality.stop_living()
    bridge.save(field_path)
    print("💾 Сохранено. До связи.")