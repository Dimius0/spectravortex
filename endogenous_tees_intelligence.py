#!/usr/bin/env python3
"""
endogenous_tees_intelligence.py — Эндогенный TEES-диалог и фуркации
Интеллект = навигация в пространстве сдвигов
"""

import numpy as np
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time

# ============================================================================
# ПРОСТОЙ ХЭШ (тот же, что и раньше)
# ============================================================================

def simple_hash(data: bytes, state: int = 0) -> int:
    h = state
    for byte in data:
        h = ((h << 5) + h) ^ byte
        h = (h * 0x45d9f3b) & 0xFFFFFFFF
        h = h ^ (h >> 17)
        h = (h * 0xc6a4a793) & 0xFFFFFFFF
        h = h ^ (h >> 13)
    return h

def word_hash(word: str) -> int:
    h = 0x6a09e667
    for letter in word:
        h = simple_hash(letter.encode(), h)
    return h

def hash_distance(a: int, b: int) -> float:
    xor = a ^ b
    return xor.bit_count() / 32.0

# ============================================================================
# TEES
# ============================================================================

def tees_flow(source: int, receiver: int, modifier: int = 0) -> int:
    combined = (source << 32) | (receiver & 0xFFFFFFFF)
    flow = simple_hash(combined.to_bytes(8, 'big'))
    if modifier:
        flow = simple_hash(flow.to_bytes(4, 'big'), modifier)
    return flow

def apply_tees(source: int, receiver: int, modifier: int = 0) -> Tuple[int, int, float]:
    flow = tees_flow(source, receiver, modifier)
    new_source = simple_hash(source.to_bytes(4, 'big'), flow)
    new_receiver = simple_hash(receiver.to_bytes(4, 'big'), flow)
    shift = hash_distance(new_source, new_receiver) - hash_distance(source, receiver)
    return new_source, new_receiver, shift

# ============================================================================
# ФУРКАЦИЯ — ВЕТВЛЕНИЕ ПУТЕЙ
# ============================================================================

def furcation(state: int, modifiers: List[int]) -> List[Tuple[int, float, int]]:
    """
    Фуркация: из текущего состояния пробуем разные пути.
    Возвращает список (новое_состояние, сдвиг, модификатор).
    """
    branches = []
    for mod in modifiers:
        new_state = simple_hash(state.to_bytes(4, 'big'), mod)
        shift = hash_distance(state, new_state)
        branches.append((new_state, shift, mod))
    return branches

# ============================================================================
# ЭНДОГЕННЫЙ ДИАЛОГ
# ============================================================================

@dataclass
class Thought:
    """Одна мысль в эндогенном диалоге."""
    state: int
    shift: float
    modifier: int
    depth: int
    parent: int = 0

@dataclass  
class Concept:
    """Понятие — устойчивый паттерн сдвигов."""
    word: str
    hash_val: int
    typical_shifts: Dict[str, float] = field(default_factory=dict)
    contexts: Set[str] = field(default_factory=set)
    encounter_count: int = 0
    
    def update(self, context: str, shift: float):
        self.typical_shifts[context] = (
            self.typical_shifts.get(context, 0) * 0.9 + shift * 0.1
        )
        self.contexts.add(context)
        self.encounter_count += 1
    
    @property
    def stability(self) -> float:
        """Стабильность понятия = обратная дисперсия сдвигов."""
        if len(self.typical_shifts) < 2:
            return 1.0
        shifts = list(self.typical_shifts.values())
        return 1.0 / (1.0 + np.std(shifts))

# ============================================================================
# ИНТЕЛЛЕКТ — НАВИГАТОР ПО СДВИГАМ
# ============================================================================

class EndogenousIntelligence:
    """
    Интеллект = эндогенный TEES-диалог + фуркации + память понятий.
    """
    
    def __init__(self, modifiers: List[int] = None):
        self.modifiers = modifiers or [0x45d9f3b, 0xc6a4a793, 0x6a09e667, 
                                       0xbb67ae85, 0x510e527f]
        self.concepts: Dict[str, Concept] = {}
        self.dialogue_history: List[Thought] = []
        self.total_thoughts = 0
    
    def perceive(self, word: str) -> int:
        """Восприятие: слово → хэш."""
        h = word_hash(word)
        if word not in self.concepts:
            self.concepts[word] = Concept(word=word, hash_val=h)
        return h
    
    def think(self, seed_state: int, depth: int = 3, max_branches: int = 3) -> List[Thought]:
        """
        Мышление: эндогенный TEES-диалог.
        
        На каждом шаге:
        1. Фуркация — пробуем разные пути
        2. Выбираем путь с максимальным сдвигом
        3. Продолжаем с новым состоянием
        """
        thoughts = []
        current = seed_state
        
        for d in range(depth):
            # Фуркация
            branches = furcation(current, self.modifiers)
            
            # Сортируем по величине сдвига (нас интересуют большие изменения)
            branches.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Берём top-N ветвей
            for i, (new_state, shift, mod) in enumerate(branches[:max_branches]):
                thought = Thought(
                    state=new_state,
                    shift=shift,
                    modifier=mod,
                    depth=d,
                    parent=current
                )
                thoughts.append(thought)
                self.dialogue_history.append(thought)
                self.total_thoughts += 1
            
            # Продолжаем с пути с максимальным сдвигом
            current = branches[0][0]
        
        return thoughts
    
    def reflect(self, word: str, context_words: List[str]) -> Dict:
        """
        Рефлексия: как слово взаимодействует с контекстом.
        Вычисляет TEES-сдвиги со всеми словами контекста.
        """
        word_h = self.perceive(word)
        results = {}
        
        for ctx in context_words:
            ctx_h = self.perceive(ctx)
            _, _, shift = apply_tees(word_h, ctx_h)
            results[ctx] = {
                'shift': shift,
                'direction': 'сближение' if shift < 0 else 'расхождение' if shift > 0 else 'нейтрально'
            }
            
            # Обновляем понятие
            if word in self.concepts:
                self.concepts[word].update(ctx, shift)
        
        return results
    
    def understand(self, word: str) -> Dict:
        """
        Понимание: что система «знает» о слове.
        На основе накопленных паттернов сдвигов.
        """
        if word not in self.concepts:
            return {'status': 'неизвестно'}
        
        concept = self.concepts[word]
        
        # Категоризируем контексты по типичным сдвигам
        close_contexts = []
        far_contexts = []
        
        for ctx, shift in concept.typical_shifts.items():
            if shift < -0.03:
                close_contexts.append(ctx)
            elif shift > 0.03:
                far_contexts.append(ctx)
        
        return {
            'word': word,
            'hash': f'{concept.hash_val:08x}',
            'encounters': concept.encounter_count,
            'stability': concept.stability,
            'attracts': close_contexts,  # контексты, к которым тянет
            'repels': far_contexts,      # контексты, от которых отталкивает
            'contexts_known': len(concept.contexts)
        }
    
    def endogenous_dialogue(self, topic: str, depth: int = 5) -> List[Dict]:
        """
        Полный эндогенный диалог на тему.
        
        1. Воспринимаем тему
        2. Запускаем мышление (TEES-диалог)
        3. Рефлексируем — как тема взаимодействует с известными понятиями
        4. Формируем понимание
        """
        # Восприятие
        seed = self.perceive(topic)
        
        # Мышление
        thoughts = self.think(seed, depth=depth)
        
        # Рефлексия — взаимодействуем со всеми известными понятиями
        known_words = list(self.concepts.keys())
        if len(known_words) > 10:
            # Берём выборку если слишком много
            known_words = list(self.concepts.keys())[:10]
        
        reflection = self.reflect(topic, known_words)
        
        # Понимание
        understanding = self.understand(topic)
        
        return {
            'topic': topic,
            'thoughts_count': len(thoughts),
            'max_shift': max(abs(t.shift) for t in thoughts) if thoughts else 0,
            'reflection': reflection,
            'understanding': understanding
        }


# ============================================================================
# ТЕСТЫ
# ============================================================================

def run_tests():
    print("=" * 70)
    print("🧠 ТЕСТЫ: ЭНДОГЕННЫЙ TEES-ДИАЛОГ И ФУРКАЦИИ")
    print("   Интеллект = навигация в пространстве сдвигов")
    print("=" * 70)
    
    # --------------------------------------------------
    # Тест 1: Базовое восприятие и мышление
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 1: ВОСПРИЯТИЕ И МЫШЛЕНИЕ")
    print("─" * 70)
    
    ai = EndogenousIntelligence()
    
    # Воспринимаем несколько слов
    words = ["Онегин", "деревня", "Москва", "любовь", "душа", "поэт", "стихи"]
    for w in words:
        ai.perceive(w)
    
    print(f"  Понятий в памяти: {len(ai.concepts)}")
    
    # Запускаем мышление на теме "Онегин"
    thoughts = ai.think(word_hash("Онегин"), depth=3, max_branches=2)
    print(f"  Мыслей сгенерировано: {len(thoughts)}")
    print(f"  Максимальный сдвиг: {max(abs(t.shift) for t in thoughts):.3f}")
    
    # --------------------------------------------------
    # Тест 2: Рефлексия — TEES с контекстом
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 2: РЕФЛЕКСИЯ — ВЗАИМОДЕЙСТВИЕ С КОНТЕКСТОМ")
    print("─" * 70)
    
    context = ["деревня", "Москва", "любовь", "душа", "стихи", "проза"]
    reflection = ai.reflect("Онегин", context)
    
    print(f"  {'Контекст':10} {'Сдвиг':>7}  Направление")
    print(f"  {'─'*10} {'─'*7}  {'─'*15}")
    
    for ctx, data in reflection.items():
        direction = "📉 СБЛИЖЕНИЕ" if data['shift'] < -0.03 else \
                   "📈 РАСХОЖДЕНИЕ" if data['shift'] > 0.03 else \
                   "➡️ НЕЙТРАЛЬНО"
        print(f"  {ctx:10} {data['shift']:+7.3f}  {direction}")
    
    # --------------------------------------------------
    # Тест 3: Обучение понятий через повторение
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 3: ОБУЧЕНИЕ ПОНЯТИЙ")
    print("─" * 70)
    
    # Многократное взаимодействие Онегина с деревней и Москвой
    print("  Повторяем TEES-взаимодействия для обучения...")
    for _ in range(10):
        ai.reflect("Онегин", ["деревня", "Москва", "любовь", "душа"])
    
    # Понимание Онегина
    understanding = ai.understand("Онегин")
    print(f"\n  Понимание 'Онегин':")
    print(f"    Хэш: {understanding['hash']}")
    print(f"    Взаимодействий: {understanding['encounters']}")
    print(f"    Стабильность: {understanding['stability']:.2f}")
    print(f"    Притягивает: {understanding['attracts']}")
    print(f"    Отталкивает: {understanding['repels']}")
    
    # --------------------------------------------------
    # Тест 4: Эндогенный диалог на тему
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 4: ЭНДОГЕННЫЙ ДИАЛОГ")
    print("─" * 70)
    
    topics = ["Онегин", "любовь", "поэт"]
    
    for topic in topics:
        result = ai.endogenous_dialogue(topic, depth=3)
        u = result['understanding']
        print(f"\n  Тема: {topic}")
        print(f"    Мыслей: {result['thoughts_count']}")
        print(f"    Макс. сдвиг: {result['max_shift']:.3f}")
        if isinstance(u, dict) and 'attracts' in u:
            print(f"    Притягивает: {u['attracts'][:3]}")
            print(f"    Отталкивает: {u['repels'][:3]}")
    
    # --------------------------------------------------
    # Тест 5: Сравнение понятий
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 5: СРАВНЕНИЕ ПОНЯТИЙ")
    print("─" * 70)
    
    for word in ["Онегин", "деревня", "Москва"]:
        u = ai.understand(word)
        if isinstance(u, dict) and 'stability' in u:
            print(f"\n  {word}:")
            print(f"    Хэш: {u['hash']}")
            print(f"    Стабильность: {u['stability']:.2f}")
            print(f"    Известно контекстов: {u['contexts_known']}")
    
    # --------------------------------------------------
    # Итоги
    # --------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 ИТОГИ")
    print("=" * 70)
    print(f"  Всего мыслей: {ai.total_thoughts}")
    print(f"  Понятий в памяти: {len(ai.concepts)}")
    print(f"  Модель: эндогенный TEES-диалог + фуркации")
    print(f"  Интеллект = навигация по сдвигам")
    print(f"  Понимание = накопленные паттерны сдвигов")
    print(f"  Понятие = устойчивый паттерн + контексты")
    print()


if __name__ == "__main__":
    run_tests()