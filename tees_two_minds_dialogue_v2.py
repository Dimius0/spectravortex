#!/usr/bin/env python3
"""
tees_two_minds_dialogue_v2.py — Диалог двух TEES-сознаний v2.0
Исправление: слова не модифицируются через хэш-фуркации.
Новые понятия образуются только через TEES-взаимодействие с существующими.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import random
import time

# ============================================================================
# ПРОСТОЙ ХЭШ
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

def furcation(state: int, modifiers: List[int]) -> List[Tuple[int, float, int]]:
    branches = []
    for mod in modifiers:
        new_state = simple_hash(state.to_bytes(4, 'big'), mod)
        shift = hash_distance(state, new_state)
        branches.append((new_state, shift, mod))
    return branches

# ============================================================================
# ПОНЯТИЕ
# ============================================================================

@dataclass
class Concept:
    word: str
    hash_val: int
    typical_shifts: Dict[str, float] = field(default_factory=dict)
    encounter_count: int = 0
    definition: str = ""  # Что означает это понятие
    
    def update_shift(self, context: str, shift: float):
        self.typical_shifts[context] = (
            self.typical_shifts.get(context, 0) * 0.9 + shift * 0.1
        )
        self.encounter_count += 1
    
    @property
    def stability(self) -> float:
        if len(self.typical_shifts) < 2:
            return 1.0
        shifts = list(self.typical_shifts.values())
        return 1.0 / (1.0 + np.std(shifts))
    
    @property
    def closest_contexts(self) -> List[Tuple[str, float]]:
        """Контексты, отсортированные по сдвигу (отрицательный = сближение)."""
        sorted_items = sorted(self.typical_shifts.items(), key=lambda x: x[1])
        return [(c, s) for c, s in sorted_items if s < -0.01]

    @property
    def connections(self) -> List[str]:
        """Все известные связи этого понятия."""
        return list(self.typical_shifts.keys())


# ============================================================================
# СОЗНАНИЕ v2 — без модификации слов
# ============================================================================

class TeesMindV2:
    """Сознание v2: слова фиксированы, понятия образуются через TEES-связи."""
    
    def __init__(self, name: str, modifiers: List[int] = None):
        self.name = name
        self.modifiers = modifiers or [0x45d9f3b, 0xc6a4a793, 0x6a09e667, 
                                       0xbb67ae85, 0x510e527f]
        self.concepts: Dict[str, Concept] = {}
        self.total_thoughts = 0
    
    def learn_word(self, word: str) -> int:
        """Запомнить слово (без модификации!)."""
        if word not in self.concepts:
            self.concepts[word] = Concept(word=word, hash_val=word_hash(word))
        return self.concepts[word].hash_val
    
    def learn_phrase(self, phrase: str):
        """Запомнить фразу — все слова + TEES-связи между ними."""
        words = phrase.split()
        for w in words:
            self.learn_word(w)
        
        # Строим TEES-связи между соседними словами
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i+1]
            src_h = self.concepts[w1].hash_val
            dst_h = self.concepts[w2].hash_val
            _, _, shift = apply_tees(src_h, dst_h)
            
            # Обновляем связи в обе стороны
            self.concepts[w1].update_shift(w2, shift)
            self.concepts[w2].update_shift(w1, shift)
            
            # Определение через связь
            if not self.concepts[w1].definition:
                self.concepts[w1].definition = f"связано с {w2}"
            if not self.concepts[w2].definition:
                self.concepts[w2].definition = f"связано с {w1}"
    
    def think(self, topic: str, depth: int = 3) -> List[float]:
        """Эндогенный диалог."""
        if topic not in self.concepts:
            self.learn_word(topic)
        
        seed = self.concepts[topic].hash_val
        current = seed
        shifts = []
        
        for d in range(depth):
            branches = furcation(current, self.modifiers)
            branches.sort(key=lambda x: abs(x[1]), reverse=True)
            current = branches[0][0]
            shifts.append(branches[0][1])
            self.total_thoughts += 1
        
        return shifts
    
    def answer_question(self, question_words: List[str], asker_name: str) -> str:
        """
        Ответить на вопрос, используя ТОЛЬКО существующие слова.
        
        Стратегия:
        1. Найти понятия, связанные со словами вопроса
        2. Найти общие связи между ними
        3. Если связей нет — создать НОВУЮ СВЯЗЬ между существующими словами
        4. Никогда не модифицировать слова через хэш!
        """
        # Извлекаем значимые слова из вопроса
        known_words = [w for w in question_words if w in self.concepts]
        
        if not known_words:
            return "не понимаю"
        
        # Ищем общие связи между всеми словами вопроса
        all_connections = []
        for w in known_words:
            concept = self.concepts[w]
            all_connections.extend(concept.connections)
        
        # Считаем частоту связей
        from collections import Counter
        connection_counts = Counter(all_connections)
        
        # Находим слова, которые связывают несколько слов вопроса
        bridging_words = [w for w, count in connection_counts.items() 
                         if count >= 2 and w not in known_words and w in self.concepts]
        
        if bridging_words:
            # Есть общая связь — используем её как ответ
            bridge = bridging_words[0]
            return f"{bridge} (связывает {', '.join(known_words[:2])})"
        
        # Нет общей связи — создаём НОВУЮ СВЯЗЬ между существующими словами
        if len(known_words) >= 2:
            w1, w2 = known_words[0], known_words[-1]
            if w1 != w2:
                # Вычисляем TEES-сдвиг между ними
                h1 = self.concepts[w1].hash_val
                h2 = self.concepts[w2].hash_val
                _, _, shift = apply_tees(h1, h2)
                
                # Создаём связь
                self.concepts[w1].update_shift(w2, shift)
                self.concepts[w2].update_shift(w1, shift)
                
                direction = "сближает" if shift < 0 else "разделяет" if shift > 0 else "связывает"
                return f"{w1} {direction} с {w2} (новая связь, сдвиг {shift:+.3f})"
        
        # Только одно слово — ищем ближайший контекст
        if len(known_words) == 1:
            concept = self.concepts[known_words[0]]
            closest = concept.closest_contexts
            if closest:
                return f"связано с {closest[0][0]} (сдвиг {closest[0][1]:.3f})"
        
        return "недостаточно связей"


# ============================================================================
# ДИАЛОГ v2
# ============================================================================

class TeesDialogueV2:
    """Диалог между двумя TEES-сознаниями v2."""
    
    def __init__(self, mind_a: TeesMindV2, mind_b: TeesMindV2):
        self.mind_a = mind_a
        self.mind_b = mind_b
        self.conversation: List[Tuple[str, str, str, str]] = []  # (кто, кому, вопрос, ответ)
    
    def teach_both(self, knowledge: Dict[str, List[str]]):
        """Обучить оба сознания."""
        for mind_name, phrases in knowledge.items():
            mind = self.mind_a if mind_name == self.mind_a.name else self.mind_b
            for phrase in phrases:
                mind.learn_phrase(phrase)
    
    def ask(self, asker: TeesMindV2, question: str) -> Tuple[str, str]:
        """Один спрашивает другого."""
        other = self.mind_b if asker == self.mind_a else self.mind_a
        words = question.split()
        answer = other.answer_question(words, asker.name)
        self.conversation.append((asker.name, other.name, question, answer))
        return other.name, answer
    
    def dialogue_cycle(self, questions: List[str], cycles: int = 3):
        """Цикл диалога."""
        print(f"\n{'='*70}")
        print(f"💬 ДИАЛОГ v2: {self.mind_a.name} ↔ {self.mind_b.name}")
        print(f"   Слова не модифицируются — только TEES-связи!")
        print(f"{'='*70}")
        
        for cycle in range(cycles):
            print(f"\n{'─'*70}")
            print(f"🔄 ЦИКЛ {cycle + 1}")
            print(f"{'─'*70}")
            
            for i, question in enumerate(questions):
                asker = self.mind_a if i % 2 == 0 else self.mind_b
                who_answered, answer = self.ask(asker, question)
                
                print(f"\n  [{asker.name}] ❓ {question}")
                print(f"  [{who_answered}] 💡 {answer}")
            
            # Эндогенный диалог после обмена
            for mind in [self.mind_a, self.mind_b]:
                mind.think("общение", depth=2)
    
    def summary(self):
        """Итоги диалога."""
        print(f"\n{'='*70}")
        print(f"📊 ИТОГИ ДИАЛОГА v2")
        print(f"{'='*70}")
        
        for mind in [self.mind_a, self.mind_b]:
            print(f"\n  Сознание: {mind.name}")
            print(f"  Понятий: {len(mind.concepts)}")
            print(f"  Мыслей: {mind.total_thoughts}")
            print(f"  Примеры связей:")
            for word, concept in list(mind.concepts.items())[:8]:
                if concept.connections:
                    print(f"    • {word}: {concept.connections[:3]}")
        
        print(f"\n  Всего реплик: {len(self.conversation)}")
        
        # Показываем новые связи
        print(f"\n  Новые связи, обнаруженные в диалоге:")
        new_connections = [c for c in self.conversation if "новая связь" in c[3]]
        for asker, answerer, question, answer in new_connections:
            print(f"    [{asker}→{answerer}] {question}")
            print(f"    → {answer}")


# ============================================================================
# ТЕСТ
# ============================================================================

def run_dialogue_v2_test():
    print("=" * 70)
    print("🧠💬 ДИАЛОГ ДВУХ TEES-СОЗНАНИЙ v2.0")
    print("   Слова фиксированы — образуются только TEES-связи")
    print("=" * 70)
    
    # Создаём два сознания
    pushkin = TeesMindV2("ПушкинЪ")
    reader = TeesMindV2("Читатель")
    
    # Разные знания
    knowledge = {
        "ПушкинЪ": [
            "Онегин едет в деревню",
            "поэт пишет стихи",
            "любовь волнует душу",
            "зима крестьянин торжествуя",
            "я помню чудное мгновенье",
        ],
        "Читатель": [
            "Онегин устал от света",
            "Москва златоглавая",
            "поэт читает прозу",
            "душа просит покоя",
            "чудное мгновенье прошло",
        ]
    }
    
    dialogue = TeesDialogueV2(pushkin, reader)
    dialogue.teach_both(knowledge)
    
    print(f"\n  ПушкинЪ знает слов: {len(pushkin.concepts)}")
    print(f"  Читатель знает слов: {len(reader.concepts)}")
    
    # Вопросы
    questions = [
        "почему Онегин едет в деревню",
        "зачем поэт пишет стихи",
        "почему любовь волнует душу",
        "зачем Онегин устал от света",
        "почему Москва златоглавая",
        "зачем душа просит покоя",
    ]
    
    dialogue.dialogue_cycle(questions, cycles=3)
    
    # Дополнительный цикл
    print(f"\n{'─'*70}")
    print(f"🔄 ДОПОЛНИТЕЛЬНЫЙ ЦИКЛ")
    print(f"{'─'*70}")
    
    new_questions = [
        "почему чудное мгновенье прошло",
        "зачем крестьянин торжествуя",
    ]
    dialogue.dialogue_cycle(new_questions, cycles=1)
    
    dialogue.summary()
    print()


if __name__ == "__main__":
    run_dialogue_v2_test()