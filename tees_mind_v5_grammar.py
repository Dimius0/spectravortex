#!/usr/bin/env python3
"""
tees_mind_v5_grammar.py — TEES-интеллект v5: + грамматическое согласование через обмен окончаниями
Интеграция протокола обрезания окончаний в генератор фраз
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import random
import time
import math
import re
import sys
import os

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

# ============================================================================
# ТАБЛИЦА ОБМЕНОВ ОКОНЧАНИЯМИ (из протокола)
# ============================================================================

class EndingExchangeTable:
    """
    TEES-грамматика = таблица обменов окончаниями.
    Из протокола обрезания окончаний v3.9.
    """
    
    # Частотные паттерны обмена окончаниями (извлечены из корпуса)
    EXCHANGE_PATTERNS = {
        # (окончание источника, окончание приёмника) → (новое_окончание_источника, новое_окончание_приёмника)
        ('ая', 'ой'): ('ая', 'ую'),   # светская → светскую
        ('ая', 'ий'): ('ой', 'ий'),   # златоглавая → златоглавой
        ('ый', 'ой'): ('ый', 'ую'),   # чудесный → чудесную
        ('ий', 'е'): ('ий', 'я'),     # синий → синего? (контекстно)
        ('ой', 'е'): ('ой', 'я'),     # молодой → молодого
        ('а', 'у'): ('а', 'у'),       # она → её (местоимения)
        ('о', 'а'): ('о', 'а'),       # окно → окна
        ('е', 'я'): ('е', 'я'),       # поле → поля
        ('я', 'и'): ('я', 'и'),       # земля → земли
        ('ь', 'и'): ('ь', 'и'),       # любовь → любви
        ('', 'а'): ('', 'а'),         # стол → стола
        ('', 'у'): ('', 'у'),         # стол → столу
        ('а', ''): ('у', ''),         # вода → воду
        ('я', ''): ('ю', ''),         # земля → землю
        ('ь', ''): ('ь', ''),         # любовь → любовь (вин.пад.)
        ('ой', ''): ('ую', ''),       # светской → светскую
    }
    
    # Роутеры (предлоги), влияющие на обмен
    ROUTERS = {
        'в': 'винительный',    # в деревню
        'на': 'винительный',   # на крышу
        'от': 'родительный',   # от света
        'из': 'родительный',   # из дома
        'к': 'дательный',      # к дому
        'о': 'предложный',     # о любви
    }
    
    @classmethod
    def get_ending(cls, word: str) -> str:
        """Извлекает окончание слова (упрощённо)."""
        vowels = 'аеёиоуыэюя'
        # Ищем окончание из 2-3 последних букв
        for length in [3, 2, 1]:
            if len(word) >= length:
                ending = word[-length:]
                # Проверяем, что это похоже на окончание
                if any(c in vowels for c in ending):
                    return ending
        return ''
    
    @classmethod
    def apply_exchange(cls, source: str, receiver: str, router: Optional[str] = None) -> Tuple[str, str]:
        """
        Применяет TEES-обмен окончаниями к паре слов.
        Возвращает грамматически согласованную пару.
        """
        src_ending = cls.get_ending(source)
        rcv_ending = cls.get_ending(receiver)
        
        # Учитываем роутер (предлог)
        if router and router in cls.ROUTERS:
            case = cls.ROUTERS[router]
            # Для винительного падежа после предлога
            if case == 'винительный' and rcv_ending in ['а', 'я']:
                receiver = receiver[:-1] + ('у' if rcv_ending == 'а' else 'ю')
            elif case == 'родительный' and rcv_ending in ['а', '']:
                if rcv_ending == 'а':
                    receiver = receiver[:-1] + 'ы'
                else:
                    receiver = receiver + 'а'
        
        # Ищем точный паттерн
        pattern = cls.EXCHANGE_PATTERNS.get((src_ending, rcv_ending))
        if pattern:
            new_src_end, new_rcv_end = pattern
            if new_src_end and src_ending:
                source = source[:-len(src_ending)] + new_src_end if source.endswith(src_ending) else source
            if new_rcv_end and rcv_ending:
                receiver = receiver[:-len(rcv_ending)] + new_rcv_end if receiver.endswith(rcv_ending) else receiver
        
        return source, receiver
    
    @classmethod
    def learn_from_corpus(cls, sentences: List[str]):
        """
        Обучается на корпусе: извлекает паттерны обмена окончаниями.
        (Упрощённая версия — в реальности нужно больше данных)
        """
        patterns = Counter()
        
        for sent in sentences:
            words = re.findall(r'[а-яё]+', sent.lower())
            for i in range(len(words) - 1):
                w1, w2 = words[i], words[i+1]
                e1, e2 = cls.get_ending(w1), cls.get_ending(w2)
                if e1 or e2:
                    patterns[(e1, e2)] += 1
        
        # Оставляем только частотные паттерны
        for (e1, e2), count in patterns.most_common(50):
            if count >= 2:
                cls.EXCHANGE_PATTERNS[(e1, e2)] = (e1, e2)  # сохраняем как есть
        
        print(f"  📚 Выучено {len(cls.EXCHANGE_PATTERNS)} обменных паттернов из корпуса")


# ============================================================================
# ПОНЯТИЕ
# ============================================================================

@dataclass
class Concept:
    word: str
    hash_val: int
    connections: Dict[str, float] = field(default_factory=dict)
    phrases: List[List[str]] = field(default_factory=list)
    encounter_count: int = 0
    last_used: float = 0.0
    emotional_valence: float = 0.0
    attention_weight: float = 1.0
    prediction_error: float = 0.0
    predicted_shift: Optional[float] = None
    
    def reinforce_connection(self, other: str, shift: float, current_time: float):
        old = self.connections.get(other, 0.0)
        self.connections[other] = old * 0.9 + (1.0 / (1.0 + abs(shift))) * 0.1
        self.last_used = current_time
        self.encounter_count += 1
        self.emotional_valence = self.emotional_valence * 0.95 + (-shift) * 0.05
    
    def add_phrase(self, words: List[str]):
        self.phrases.append(words)
        if len(self.phrases) > 100:
            self.phrases = self.phrases[-50:]
    
    def predict_shift(self, other_hash: int) -> float:
        strength = self.connections.get(str(other_hash), 0.0)
        predicted = 0.5 - strength * 0.5
        self.predicted_shift = predicted
        return predicted
    
    def decay(self, current_time: float, decay_rate: float = 0.001):
        time_since = current_time - self.last_used
        factor = math.exp(-decay_rate * time_since)
        for other in list(self.connections.keys()):
            self.connections[other] *= factor
            if abs(self.connections[other]) < 0.01:
                del self.connections[other]
        self.attention_weight *= factor
    
    def consolidate(self):
        for other in self.connections:
            if abs(self.connections[other]) > 0.3:
                self.connections[other] *= 1.1
        for other in list(self.connections.keys()):
            if abs(self.connections[other]) < 0.03:
                del self.connections[other]
        self.attention_weight = min(1.0, self.attention_weight * 1.2)
    
    def deep_connect(self, other_concept: 'Concept', current_time: float):
        _, _, shift = apply_tees(self.hash_val, other_concept.hash_val)
        if abs(shift) > 0.2:
            self.reinforce_connection(other_concept.word, shift, current_time)
            other_concept.reinforce_connection(self.word, shift, current_time)
    
    @property
    def strongest_connections(self) -> List[Tuple[str, float]]:
        sorted_conns = sorted(self.connections.items(), key=lambda x: abs(x[1]), reverse=True)
        return sorted_conns[:5]
    
    @property
    def mood(self) -> str:
        if self.emotional_valence > 0.1: return "😊"
        elif self.emotional_valence < -0.1: return "😞"
        else: return "😐"


# ============================================================================
# ГЕНЕРАТОР ФРАЗ v5 — с грамматическим согласованием
# ============================================================================

class PhraseGeneratorV5:
    """Генерирует связные, грамматически согласованные ответы."""
    
    def __init__(self, mind: 'FullTeesMindV5'):
        self.mind = mind
        self.exchange_table = EndingExchangeTable()
    
    def generate_answer(self, question_words: List[str], max_length: int = 10) -> str:
        """Генерирует ответ-фразу с грамматическим согласованием."""
        
        known = [(w, self.mind.concepts[w]) for w in question_words if w in self.mind.concepts]
        if not known:
            return "не знаю"
        
        # 1. Ищем готовую фразу
        exact_match = self._find_exact_match(question_words)
        if exact_match:
            return self._apply_grammar(exact_match, question_words)
        
        # 2. Строим цепочку
        chain = self._build_chain(known, max_length)
        if chain:
            return self._apply_grammar(" ".join(chain), question_words)
        
        # 3. Генерируем из связей
        return self._generate_from_connections(known)
    
    def _find_exact_match(self, question_words: List[str]) -> Optional[str]:
        best_match = None
        best_score = 0
        
        for word in question_words:
            if word in self.mind.concepts:
                for phrase in self.mind.concepts[word].phrases:
                    overlap = len(set(phrase) & set(question_words))
                    if overlap > best_score and overlap >= 2:
                        best_score = overlap
                        best_match = " ".join(phrase)
        
        return best_match
    
    def _build_chain(self, known: List[Tuple[str, 'Concept']], max_length: int) -> Optional[List[str]]:
        chain = [known[0][0]]
        current = known[0][1]
        used = {known[0][0]}
        
        for _ in range(max_length - 1):
            best_next = None
            best_strength = 0
            
            for conn_word, strength in current.connections.items():
                if conn_word not in used and conn_word in self.mind.concepts:
                    if abs(strength) > best_strength:
                        best_strength = abs(strength)
                        best_next = conn_word
            
            if best_next is None:
                break
            
            chain.append(best_next)
            used.add(best_next)
            current = self.mind.concepts[best_next]
        
        return chain if len(chain) >= 2 else None
    
    def _apply_grammar(self, phrase: str, question_words: List[str]) -> str:
        """
        Применяет TEES-обмен окончаниями для грамматического согласования.
        Это ключевое улучшение v5!
        """
        words = phrase.split()
        if len(words) < 2:
            return phrase
        
        # Извлекаем предлоги из вопроса для контекста
        routers_in_question = [w for w in question_words if w in EndingExchangeTable.ROUTERS]
        
        # Применяем обмен окончаниями к каждой паре
        result = [words[0]]
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i+1]
            
            # Определяем роутер (предлог перед словом)
            router = None
            if w1 in EndingExchangeTable.ROUTERS:
                router = w1
            
            # Применяем TEES-обмен
            new_w1, new_w2 = EndingExchangeTable.apply_exchange(w1, w2, router)
            
            # Обновляем если изменилось
            if i == 0:
                result[0] = new_w1
            result.append(new_w2)
        
        return " ".join(result)
    
    def _generate_from_connections(self, known: List[Tuple[str, 'Concept']]) -> str:
        """Генерирует фразу из ближайших связей с грамматикой."""
        parts = []
        
        for word, concept in known[:3]:
            strongest = concept.strongest_connections
            if strongest:
                conn_word, strength = strongest[0]
                # Применяем грамматическое согласование
                src, rcv = EndingExchangeTable.apply_exchange(word, conn_word)
                parts.append(f"{src} {rcv}")
        
        if parts:
            return ", ".join(parts)
        
        return "недостаточно связей"


# ============================================================================
# ЗАГРУЗЧИК ТЕКСТОВ
# ============================================================================

class TextLoader:
    @staticmethod
    def load_file(filepath: str) -> List[str]:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        sentences = re.split(r'[.!?…]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    @staticmethod
    def load_text(text: str) -> List[str]:
        sentences = re.split(r'[.!?…]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    @staticmethod
    def tokenize(sentence: str) -> List[str]:
        return re.findall(r'[а-яёa-z]+', sentence.lower())


# ============================================================================
# ПОЛНОЦЕННОЕ СОЗНАНИЕ v5
# ============================================================================

class FullTeesMindV5:
    def __init__(self, name: str):
        self.name = name
        self.concepts: Dict[str, Concept] = {}
        self.birth_time = time.time()
        self.total_interactions = 0
        self.sleep_cycles = 0
        self.generator = PhraseGeneratorV5(self)
        self.modifiers = [0x45d9f3b, 0xc6a4a793, 0x6a09e667, 0xbb67ae85, 0x510e527f]
    
    @property
    def current_time(self) -> float:
        return time.time() - self.birth_time
    
    def learn_word(self, word: str) -> Concept:
        if word not in self.concepts:
            self.concepts[word] = Concept(word=word, hash_val=word_hash(word), last_used=self.current_time)
        return self.concepts[word]
    
    def learn_phrase(self, phrase: str):
        words = TextLoader.tokenize(phrase)
        if len(words) < 2:
            return
        
        for w in words:
            self.learn_word(w)
        
        for w in words:
            self.concepts[w].add_phrase(words)
        
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i+1]
            c1, c2 = self.concepts[w1], self.concepts[w2]
            _, _, shift = apply_tees(c1.hash_val, c2.hash_val)
            c1.reinforce_connection(w2, shift, self.current_time)
            c2.reinforce_connection(w1, shift, self.current_time)
            self.total_interactions += 1
    
    def load_text(self, text: str):
        sentences = TextLoader.load_text(text)
        for sent in sentences:
            self.learn_phrase(sent)
        # Обучаем таблицу обменов на загруженном тексте
        EndingExchangeTable.learn_from_corpus(sentences)
        print(f"  📖 {self.name}: загружено {len(sentences)} предложений, {len(self.concepts)} понятий")
    
    def load_file(self, filepath: str):
        if not os.path.exists(filepath):
            print(f"  ❌ Файл не найден: {filepath}")
            return
        sentences = TextLoader.load_file(filepath)
        for sent in sentences:
            self.learn_phrase(sent)
        EndingExchangeTable.learn_from_corpus(sentences)
        print(f"  📂 {self.name}: загружен {filepath} ({len(sentences)} предложений, {len(self.concepts)} понятий)")
    
    def focus_attention(self, topic: str, context_words: List[str]):
        if topic not in self.concepts:
            return
        self.concepts[topic].attention_weight = 1.0
        for ctx in context_words:
            if ctx in self.concepts:
                self.concepts[ctx].attention_weight = min(1.0, self.concepts[ctx].attention_weight + 0.3)
        for word, concept in self.concepts.items():
            if word != topic and word not in context_words:
                concept.attention_weight *= 0.9
    
    def answer_question(self, question: str) -> str:
        words = TextLoader.tokenize(question)
        known = [w for w in words if w in self.concepts]
        if known:
            self.focus_attention(known[0], known[1:] if len(known) > 1 else [])
        return self.generator.generate_answer(words)
    
    def decay_memory(self):
        for concept in self.concepts.values():
            concept.decay(self.current_time)
    
    def slow_sleep(self):
        print(f"  💤 {self.name}: медленный сон...")
        for concept in self.concepts.values():
            concept.consolidate()
        for concept in self.concepts.values():
            concept.emotional_valence *= 0.9
    
    def rem_sleep(self):
        print(f"  🎭 {self.name}: быстрый сон (REM)...")
        words = list(self.concepts.keys())
        if len(words) < 2:
            return
        
        associations = min(20, len(words) * 2)
        for _ in range(associations):
            w1, w2 = random.sample(words, 2)
            if w2 not in self.concepts[w1].connections:
                self.concepts[w1].deep_connect(self.concepts[w2], self.current_time)
        
        new_phrases = 0
        for _ in range(min(10, len(words))):
            w = random.choice(words)
            if self.concepts[w].phrases:
                phrase = random.choice(self.concepts[w].phrases)
                strong = self.concepts[w].strongest_connections
                if strong:
                    variant = phrase.copy()
                    for i, pw in enumerate(variant):
                        if pw == w:
                            variant[i] = strong[0][0]
                            break
                    if variant != phrase:
                        for pw in variant:
                            if pw in self.concepts:
                                self.concepts[pw].add_phrase(variant)
                        new_phrases += 1
        
        print(f"     Новых ассоциаций: {associations}, новых фраз: {new_phrases}")
    
    def sleep(self, cycles: int = 1):
        for cycle in range(cycles):
            print(f"\n  🌙 {self.name}: цикл сна {self.sleep_cycles + 1}")
            self.decay_memory()
            self.slow_sleep()
            self.rem_sleep()
            self.sleep_cycles += 1
        print(f"  ✅ {self.name} проснулся после {cycles} циклов")
    
    @property
    def average_mood(self) -> str:
        if not self.concepts:
            return "😐"
        avg = np.mean([c.emotional_valence for c in self.concepts.values()])
        if avg > 0.05: return f"😊 ({avg:+.2f})"
        elif avg < -0.05: return f"😞 ({avg:+.2f})"
        else: return f"😐 ({avg:+.2f})"
    
    def summary(self):
        print(f"\n  🧠 {self.name}:")
        print(f"     Понятий: {len(self.concepts)}")
        print(f"     Взаимодействий: {self.total_interactions}")
        print(f"     Циклов сна: {self.sleep_cycles}")
        total_connections = sum(len(c.connections) for c in self.concepts.values())
        print(f"     Всего связей: {total_connections}")
        print(f"     Настроение: {self.average_mood}")


# ============================================================================
# ДИАЛОГ v5
# ============================================================================

class FullDialogueV5:
    def __init__(self, mind_a: FullTeesMindV5, mind_b: FullTeesMindV5):
        self.mind_a = mind_a
        self.mind_b = mind_b
    
    def ask(self, asker: FullTeesMindV5, question: str) -> Tuple[str, str]:
        other = self.mind_b if asker == self.mind_a else self.mind_a
        answer = other.answer_question(question)
        print(f"\n  [{asker.name}] ❓ {question}")
        print(f"  [{other.name}] 💡 {answer}")
        return other.name, answer
    
    def dialogue_cycle(self, questions: List[str]):
        print(f"\n{'='*70}")
        print(f"💬 ДИАЛОГ v5: {self.mind_a.name} ↔ {self.mind_b.name}")
        print(f"{'='*70}")
        for i, question in enumerate(questions):
            asker = self.mind_a if i % 2 == 0 else self.mind_b
            self.ask(asker, question)
    
    def sleep_both(self, cycles: int = 3):
        print(f"\n{'='*70}")
        print(f"💤 СОН: {cycles} циклов для каждого")
        print(f"{'='*70}")
        for mind in [self.mind_a, self.mind_b]:
            mind.sleep(cycles)


# ============================================================================
# ТЕСТ
# ============================================================================

def run_v5_test():
    print("=" * 70)
    print("🧠💤 TEES-ИНТЕЛЛЕКТ v5: + ГРАММАТИЧЕСКОЕ СОГЛАСОВАНИЕ")
    print("   Интеграция протокола обрезания окончаний")
    print("=" * 70)
    
    pushkin = FullTeesMindV5("ПушкинЪ")
    reader = FullTeesMindV5("Читатель")
    dialogue = FullDialogueV5(pushkin, reader)
    
    print("\n📂 ЗАГРУЗКА ТЕКСТОВ:")
    pushkin.load_text("""
    Онегин едет в деревню к умирающему дяде. Он устал от света и хочет покоя.
    Поэт пишет стихи о любви и природе. Мороз и солнце день чудесный.
    Буря мглою небо кроет вихри снежные крутя. Любовь волнует душу нежно.
    Зима крестьянин торжествуя на дровнях обновляет путь.
    Я помню чудное мгновенье передо мной явилась ты.
    """)
    
    reader.load_text("""
    Онегин устал от светской жизни и уехал в деревню. Москва златоглавая ждёт его.
    Поэт читает прозу и думает о смысле жизни. Душа просит покоя и тишины.
    Чудное мгновенье прошло но осталась память. Солнце светит ярко над городом.
    Небо чистое голубое весной радует глаз. Крестьянин работает в поле.
    """)
    
    questions = [
        "почему Онегин едет в деревню",
        "зачем поэт пишет стихи",
        "почему любовь волнует душу",
        "зачем Онегин устал от света",
        "почему Москва златоглавая",
        "зачем душа просит покоя",
    ]
    dialogue.dialogue_cycle(questions)
    
    dialogue.sleep_both(cycles=3)
    
    print(f"\n{'='*70}")
    print(f"💬 ДИАЛОГ ПОСЛЕ СНА")
    print(f"{'='*70}")
    new_questions = [
        "почему чудное мгновенье прошло",
        "зачем крестьянин торжествуя",
        "почему мороз и солнце",
        "зачем буря мглою небо кроет",
    ]
    dialogue.dialogue_cycle(new_questions)
    
    print(f"\n{'='*70}")
    print(f"📊 ФИНАЛ")
    print(f"{'='*70}")
    pushkin.summary()
    reader.summary()
    
    print(f"\n✅ ТЕСТ ЗАВЕРШЁН")


if __name__ == "__main__":
    run_v5_test()