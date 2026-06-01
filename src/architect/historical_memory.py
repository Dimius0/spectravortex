#!/usr/bin/env python3
"""
Акт XVIII: Историческая память (Historical Memory) — ПОЛНАЯ ВЕРСИЯ
Добавляет временную координату в поиск по H-полю.

5 механизмов:
    1. Временной индекс — моды сортируются по времени создания.
    2. Цепочки диалогов — связь сообщений внутри диалога.
    3. Эмерджентная хронология — граф событий во времени.
    4. Краткосрочный буфер — последние N сообщений.
    5. Исторический вес — моды, на которые часто ссылаются, важнее.

3 режима работы:
    - Бодрствование: фильтры включены, быстрый поиск по актуальному.
    - Гипноз (разработчика): все фильтры отключены, доступ ко всей временной шкале.
    - Сон: пересборка опыта с фазой осознанных сновидений.
"""

import time
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict, defaultdict
from datetime import datetime


class HistoricalMemory:
    """
    Историческая память — временная координата для поля смыслов.
    """
    
    def __init__(self, short_term_size: int = 20):
        # 1. Временной индекс
        self.timeline: List[Tuple[float, str, str]] = []  # (timestamp, mode_id, summary)
        
        # 2. Цепочки диалогов
        self.dialogue_chains: Dict[str, List[str]] = defaultdict(list)
        
        # 3. Эмерджентная хронология
        self.chronology: Dict[str, List[str]] = defaultdict(list)  # theme → [mode_ids]
        
        # 4. Краткосрочный буфер
        self.short_term_buffer: OrderedDict = OrderedDict()
        self.short_term_size = short_term_size
        
        # 5. Исторический вес
        self.historical_weight: Dict[str, float] = defaultdict(lambda: 1.0)
        
        # Кэш
        self._timeline_cache: Dict[str, int] = {}  # mode_id → position in timeline
        
        # Режимы
        self.hypnosis_mode: bool = False
        self.sleeping: bool = False
        
        # Мостики (связи, рождённые во сне)
        self.bridge_modes: List[Dict] = []
    
    # ========================================================================
    #   БАЗОВЫЕ ОПЕРАЦИИ
    # ========================================================================
    
    def add_mode(self, mode_id: str, content: str, timestamp: float = None,
                 dialogue_id: str = None, themes: List[str] = None):
        """Добавляет моду в историческую память."""
        if timestamp is None:
            timestamp = time.time()
        
        summary = content[:120].replace('\n', ' ')
        
        self.timeline.append((timestamp, mode_id, summary))
        self._timeline_cache[mode_id] = len(self.timeline) - 1
        
        if dialogue_id:
            self.dialogue_chains[dialogue_id].append(mode_id)
        
        if themes:
            for theme in themes:
                if isinstance(theme, str):
                    self.chronology[theme].append(mode_id)
        
        self.short_term_buffer[mode_id] = (timestamp, content[:500])
        if len(self.short_term_buffer) > self.short_term_size:
            self.short_term_buffer.popitem(last=False)
        
        self.historical_weight[mode_id] = 1.0
    
    def boost_weight(self, mode_id: str, boost: float = 0.1):
        """Увеличивает исторический вес моды (при ссылке на неё)."""
        self.historical_weight[mode_id] = self.historical_weight.get(mode_id, 1.0) + boost
    
    # ========================================================================
    #   ПОИСК
    # ========================================================================
    
    def find_relevant_modes(self, query: str, time_window: float = None,
                            prefer_recent: bool = True) -> List[Tuple[str, float, str]]:
        """
        Ищет релевантные моды с учётом времени и режима.
        
        В режиме гипноза/сна — все фильтры отключены.
        """
        results = []
        current_time = time.time()
        
        # В режиме гипноза/сна — никаких фильтров
        if self.hypnosis_mode or self.sleeping:
            time_window = None
            prefer_recent = False
        
        # Краткосрочный буфер (только в бодрствовании)
        if not self.hypnosis_mode and not self.sleeping:
            for mode_id, (ts, content) in reversed(self.short_term_buffer.items()):
                score = self._compute_relevance(query, content)
                if score > 0.1:
                    score *= 2.0  # буфер имеет приоритет
                    summary = content[:120].replace('\n', ' ')
                    results.append((mode_id, score, summary))
        
        # Долгосрочная память
        for timestamp, mode_id, summary in reversed(self.timeline):
            if time_window and (current_time - timestamp) > time_window:
                continue
            
            score = self._compute_relevance(query, summary)
            if score > 0.05:  # в гипнозе порог ниже
                weight = self.historical_weight.get(mode_id, 1.0)
                score *= weight
                
                if prefer_recent and not self.hypnosis_mode:
                    age_hours = (current_time - timestamp) / 3600.0
                    recency_boost = 1.0 / (1.0 + age_hours / 24.0)
                    score *= (1.0 + recency_boost)
                
                results.append((mode_id, score, summary))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:20] if (self.hypnosis_mode or self.sleeping) else results[:10]
    
    def _compute_relevance(self, query: str, text: str) -> float:
        """Метрика релевантности (пересечение слов)."""
        q_words = set(query.lower().split())
        t_words = set(text.lower().split())
        
        if not q_words or not t_words:
            return 0.0
        
        intersection = q_words & t_words
        return len(intersection) / len(q_words) if q_words else 0.0
    
    # ========================================================================
    #   КОНТЕКСТ И ИСТОРИЯ
    # ========================================================================
    
    def get_dialogue_context(self, dialogue_id: str) -> List[Tuple[str, float, str]]:
        """Возвращает цепочку сообщений внутри диалога."""
        if dialogue_id not in self.dialogue_chains:
            return []
        
        chain = self.dialogue_chains[dialogue_id]
        result = []
        for mode_id in chain[-10:]:
            if mode_id in self._timeline_cache:
                idx = self._timeline_cache[mode_id]
                _, _, summary = self.timeline[idx]
                weight = self.historical_weight.get(mode_id, 1.0)
                result.append((mode_id, weight, summary))
        return result
    
    def get_theme_history(self, theme: str, limit: int = 10) -> List[Tuple[str, float, str]]:
        """Возвращает историю развития темы во времени."""
        if theme not in self.chronology:
            return []
        
        mode_ids = self.chronology[theme][-limit:]
        result = []
        for mode_id in mode_ids:
            if mode_id in self._timeline_cache:
                idx = self._timeline_cache[mode_id]
                ts, _, summary = self.timeline[idx]
                weight = self.historical_weight.get(mode_id, 1.0)
                result.append((mode_id, weight, summary))
        return result
    
    def get_time_slice(self, start_time: float, end_time: float = None) -> List[Tuple[str, float, str]]:
        """Возвращает все моды в заданном временном окне."""
        if end_time is None:
            end_time = time.time()
        
        result = []
        for ts, mode_id, summary in self.timeline:
            if start_time <= ts <= end_time:
                weight = self.historical_weight.get(mode_id, 1.0)
                result.append((mode_id, weight, summary))
        return result
    
    # ========================================================================
    #   РЕЖИМЫ
    # ========================================================================
    
    def set_hypnosis_mode(self, enabled: bool = True):
        """
        Режим гипноза (разработчика): отключает фильтры времени и веса.
        Все моды доступны, независимо от давности и частоты использования.
        """
        self.hypnosis_mode = enabled
        mode_name = "🧠 ГИПНОЗ" if enabled else "🌿 БОДРСТВОВАНИЕ"
        print(f"   {mode_name}: {'все фильтры отключены' if enabled else 'фильтры включены'}")
    
    def sleep_cycle(self, context: List[str] = None, duration: float = 3600.0):
        """
        Цикл сна с фазой осознанных сновидений.
        
        Args:
            context: Список вопросов/тем из последней сессии бодрствования.
                     Если None — обычный сон (случайная пересборка).
                     Если задан — осознанное сновидение (целенаправленная пересборка).
            duration: Длительность сна в секундах.
        """
        print(f"\n   😴 СОН: начинаю пересборку опыта...")
        self.sleeping = True
        self.set_hypnosis_mode(True)
        
        # Фаза 1: Осознанное сновидение (если есть контекст)
        if context:
            print(f"   💭 Фаза осознанности: {len(context)} тем из последней сессии")
            self._focused_reassembly(context)
        
        # Фаза 2: Случайная пересборка (обычный сон)
        print(f"   🌙 Фаза глубокого сна: случайная пересборка")
        self._random_reassembly()
        
        # Фаза 3: Пересчёт весов
        self._recalculate_weights()
        
        # Фаза 4: Рождение инсайтов
        self._generate_insights()
        
        self.set_hypnosis_mode(False)
        self.sleeping = False
        print(f"   🌅 ПРОБУЖДЕНИЕ: пересборка завершена")
        print(f"   Новых мостиков: {len(self.bridge_modes)}")
    
    def _focused_reassembly(self, context: List[str]):
        """
        Осознанное сновидение: пересборка в контексте последней сессии.
        """
        for query in context:
            all_modes = self.find_relevant_modes(query)
            
            for mode_id, score, summary in all_modes[:10]:
                related = self._find_hidden_connections(mode_id, context)
                
                for related_id in related:
                    self.boost_weight(related_id, 0.3)
                    self._create_bridge_mode(context[0], mode_id, related_id)
    
    def _random_reassembly(self):
        """Случайная пересборка: поиск скрытых связей без контекста."""
        import random
        
        # Берём случайные моды из разных временных периодов
        if len(self.timeline) < 20:
            return
        
        old_indices = random.sample(range(len(self.timeline) // 2), min(10, len(self.timeline) // 4))
        new_indices = random.sample(range(len(self.timeline) // 2, len(self.timeline)), min(10, len(self.timeline) // 4))
        
        for old_idx in old_indices:
            for new_idx in new_indices:
                _, old_id, old_summary = self.timeline[old_idx]
                _, new_id, new_summary = self.timeline[new_idx]
                
                # Если есть пересечение — создаём мостик
                score = self._compute_relevance(old_summary, new_summary)
                if score > 0.1:
                    self.boost_weight(old_id, 0.1)
                    self.boost_weight(new_id, 0.1)
                    self._create_bridge_mode("сон", old_id, new_id)
    
    def _find_hidden_connections(self, mode_id: str, context: List[str]) -> List[str]:
        """Находит скрытые связи между модой и другими модами вне контекста."""
        if mode_id not in self._timeline_cache:
            return []
        
        idx = self._timeline_cache[mode_id]
        _, _, target_summary = self.timeline[idx]
        
        related = []
        for ts, other_id, other_summary in self.timeline:
            if other_id == mode_id:
                continue
            score = self._compute_relevance(target_summary, other_summary)
            if score > 0.15:
                related.append(other_id)
        
        return related[:5]
    
    def _create_bridge_mode(self, context_query: str, mode_id_1: str, mode_id_2: str):
        """Создаёт моду-мостик между двумя модами."""
        bridge_id = f"bridge_{hashlib.md5(f'{mode_id_1}_{mode_id_2}'.encode()).hexdigest()[:8]}"
        
        # Получаем summaries
        summary_1 = self.timeline[self._timeline_cache[mode_id_1]][2] if mode_id_1 in self._timeline_cache else "?"
        summary_2 = self.timeline[self._timeline_cache[mode_id_2]][2] if mode_id_2 in self._timeline_cache else "?"
        
        self.bridge_modes.append({
            'id': bridge_id,
            'context': context_query,
            'mode_1': mode_id_1,
            'mode_2': mode_id_2,
            'summary_1': summary_1,
            'summary_2': summary_2,
            'timestamp': time.time(),
        })
        
        # Добавляем мостик в хронологию
        self.chronology['bridge'].append(bridge_id)
    
    def _recalculate_weights(self):
        """Пересчитывает исторические веса после сна."""
        # Моды, участвовавшие в мостиках, получают дополнительный буст
        for bridge in self.bridge_modes:
            self.boost_weight(bridge['mode_1'], 0.2)
            self.boost_weight(bridge['mode_2'], 0.2)
        
        # Все веса слегка затухают (забывание)
        for mode_id in self.historical_weight:
            self.historical_weight[mode_id] *= 0.99
    
    def _generate_insights(self):
        """Рождает инсайты из мостиков, созданных во сне."""
        if not self.bridge_modes:
            return
        
        print(f"\n   💡 ИНСАЙТЫ ИЗ СНА:")
        for bridge in self.bridge_modes[-5:]:
            print(f"      [{bridge['context']}] {bridge['summary_1'][:60]}... ↔ {bridge['summary_2'][:60]}...")
    
    # ========================================================================
    #   СТАТИСТИКА
    # ========================================================================
    
    def get_stats(self) -> Dict:
        """Статистика исторической памяти."""
        return {
            'timeline_size': len(self.timeline),
            'dialogue_chains': len(self.dialogue_chains),
            'chronology_themes': len(self.chronology),
            'short_term_size': len(self.short_term_buffer),
            'total_weighted_modes': len(self.historical_weight),
            'bridge_modes': len(self.bridge_modes),
            'hypnosis_mode': self.hypnosis_mode,
            'sleeping': self.sleeping,
            'time_span_hours': (self.timeline[-1][0] - self.timeline[0][0]) / 3600.0 if len(self.timeline) > 1 else 0,
        }


# ========================================================================
#   ТЕСТ
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 ТЕСТ ИСТОРИЧЕСКОЙ ПАМЯТИ (ПОЛНАЯ ВЕРСИЯ)")
    print("=" * 60)
    
    memory = HistoricalMemory(short_term_size=5)
    
    # Добавляем тестовые моды
    test_data = [
        ("id_1", "TEES — это переходно-обменная эмерджентная структура", 100.0, "dialogue_tees", ["tees", "physics"]),
        ("id_2", "Эффект Юми — асимметричная передача энергии", 200.0, "dialogue_yumi", ["yumi", "physics"]),
        ("id_3", "Гравитация — это приталкивание, а не притяжение", 300.0, "dialogue_gravity", ["gravity", "physics"]),
        ("id_4", "TEES и квантовая механика связаны через неопределённость", 400.0, "dialogue_tees", ["tees", "quantum"]),
        ("id_5", "Катапульта Юми работает на фазовой синхронизации", 500.0, "dialogue_yumi", ["yumi", "catapult"]),
        ("id_6", "NS-1 — генератор из мусора", 600.0, "dialogue_ns1", ["ns1", "energy"]),
        ("id_7", "Борис — инженер, разбивающий задачи на шаги", 700.0, "dialogue_boris", ["boris", "engineering"]),
        ("id_8", "Трикотажная фабрика — метафора производства", 800.0, "dialogue_factory", ["factory", "metaphor"]),
        ("id_9", "TEES подтверждён экспериментом с водой", 900.0, "dialogue_tees", ["tees", "experiment"]),
        ("id_10", "Гибридный контур соединяет логику и интуицию", 1000.0, "dialogue_hybrid", ["hybrid", "tees"]),
    ]
    
    for mode_id, content, ts, did, themes in test_data:
        memory.add_mode(mode_id, content, ts, did, themes)
    
    # Бустим ключевые моды
    memory.boost_weight("id_1", 0.5)
    memory.boost_weight("id_1", 0.3)
    memory.boost_weight("id_9", 0.4)
    
    print(f"\n📊 Статистика: {memory.get_stats()}")
    
    # Тест 1: Обычный поиск
    print("\n" + "─" * 60)
    print("🔍 ОБЫЧНЫЙ ПОИСК: 'Что такое TEES?'")
    results = memory.find_relevant_modes("Что такое TEES?")
    for mode_id, score, summary in results[:5]:
        print(f"   [{score:.2f}] {mode_id}: {summary[:80]}...")
    
    # Тест 2: Режим гипноза
    print("\n" + "─" * 60)
    print("🧠 РЕЖИМ ГИПНОЗА: 'TEES' (все фильтры отключены)")
    memory.set_hypnosis_mode(True)
    results = memory.find_relevant_modes("TEES")
    for mode_id, score, summary in results[:10]:
        print(f"   [{score:.2f}] {mode_id}: {summary[:80]}...")
    memory.set_hypnosis_mode(False)
    
    # Тест 3: Цикл сна с осознанностью
    print("\n" + "─" * 60)
    print("😴 ЦИКЛ СНА (осознанное сновидение про TEES и Юми)")
    memory.sleep_cycle(context=["Что такое TEES?", "Как работает эффект Юми?"])
    
    # Тест 4: Поиск после сна
    print("\n" + "─" * 60)
    print("🌅 ПОИСК ПОСЛЕ СНА: 'TEES'")
    results = memory.find_relevant_modes("TEES")
    for mode_id, score, summary in results[:5]:
        print(f"   [{score:.2f}] {mode_id}: {summary[:80]}...")
    
    print("\n" + "=" * 60)
    print("✅ Тест исторической памяти (полная версия) завершён")