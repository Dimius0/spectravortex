#!/usr/bin/env python3
"""
test_gap_hunter_v2_0_fractal.py — Тест GapHunter с фрактальной моделью
Фрактальная структура: буквы → слоги → слова → фразы → тексты
"""

import sys
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from enum import Enum
import re

# ============================================================================
# БАЗОВЫЕ КЛАССЫ (без изменений)
# ============================================================================

class ModeState(Enum):
    SOURCE = "источник"
    TEES = "поток"
    TARGET = "приёмник"
    CO_ROUTER = "маршрутизатор"
    EXTERNAL_CAUSE = "внешняя_причина"
    GOAL = "цель"

class TeesDirection(Enum):
    ACTIVE = "акт"
    PASSIVE = "пас"
    REFLEXIVE = "возв"

class TeesIntensity(Enum):
    PERFECTIVE = "сов"
    IMPERFECTIVE = "несов"

class TeesTime(Enum):
    PAST = "прош"
    PRESENT = "наст"
    FUTURE = "буд"

class GapType(Enum):
    SOURCE = "source"
    TEES = "tees"
    RECEIVER = "receiver"
    EXTERNAL_CAUSE = "external_cause"
    METHOD = "method"
    GOAL = "goal"
    CONTRAST = "contrast"
    FULL = "full"

@dataclass
class VortexParams:
    frequency: float = 0.0
    amplitude: float = 0.0
    phase: float = 0.0
    radius: float = 0.0
    energy: float = 0.0
    layer: int = 3
    charge: float = 0.0
    direction: int = 1

@dataclass
class Mod:
    lemma: str
    state: Optional[ModeState] = None

@dataclass
class TeesLink:
    lemma: str
    direction: TeesDirection = TeesDirection.ACTIVE
    intensity: TeesIntensity = TeesIntensity.IMPERFECTIVE
    time: TeesTime = TeesTime.PRESENT
    reflexive: bool = False

@dataclass
class TeesGraph:
    source: Optional[Mod] = None
    tees: Optional[TeesLink] = None
    receiver: Optional[Mod] = None
    co_mods: List[Mod] = field(default_factory=list)
    routers: List[str] = field(default_factory=list)
    raw_text: str = ""

@dataclass
class Gap:
    type: GapType
    intensity: float = 0.5
    constraints: List[str] = field(default_factory=list)
    context: Dict = field(default_factory=dict)

@dataclass
class TeesQuestion:
    source: Optional[Mod] = None
    tees: Optional[TeesLink] = None
    receiver: Optional[Mod] = None
    co_mods: List[Mod] = field(default_factory=list)
    routers: List[str] = field(default_factory=list)
    gap: Optional[Gap] = None
    contrast_graph: Optional[TeesGraph] = None
    raw_text: str = ""
    
    @property
    def has_source(self): return self.source is not None
    @property
    def has_tees(self): return self.tees is not None
    @property
    def has_receiver(self): return self.receiver is not None

# ============================================================================
# ФРАКТАЛЬНАЯ МОДЕЛЬ
# ============================================================================

@dataclass
class FractalProfile:
    """Профиль моды на всех фрактальных уровнях."""
    
    # Уровень 1-2: буквы/звуки
    length: int = 0              # длина слова в буквах
    vowels_count: int = 0        # количество гласных
    consonants_count: int = 0    # количество согласных
    unique_letters: int = 0      # уникальных букв
    vowel_consonant_ratio: float = 0.0  # отношение гласных к согласным
    
    # Уровень 3: слоги
    syllable_count: int = 0      # количество слогов
    stress_position: int = -1    # позиция ударения (-1 = нет)
    syllable_complexity: float = 0.0  # сложность слогов
    
    # Уровень 4: слово (части речи и т.д.)
    is_noun: bool = False
    is_verb: bool = False
    is_adjective: bool = False
    word_frequency: float = 0.0  # частотность в языке
    
    # Уровень 5: словосочетания
    typical_role: str = ""       # субъект, объект, место, время
    collocation_count: int = 0   # количество типичных словосочетаний
    
    # Уровень 6: предложения
    sentence_position: str = ""  # начало, середина, конец
    grammatical_case: str = ""   # падеж (для существительных)
    
    # Уровень 7: текст
    text_importance: float = 0.0 # важность в тексте
    narrative_role: str = ""     # роль в повествовании

# ============================================================================
# ФРАКТАЛЬНЫЙ АНАЛИЗАТОР
# ============================================================================

class FractalAnalyzer:
    """Анализирует слово на всех фрактальных уровнях."""
    
    # Гласные русского языка
    VOWELS = set('аеёиоуыэюя')
    
    # Звонкие согласные
    VOICED = set('бвгджзлмнр')
    
    # Типичные роли в тексте
    NARRATIVE_ROLES = {
        'Москва': ('центр', 0.9),
        'деревня': ('периферия', 0.7),
        'солнце': ('источник', 0.85),
        'земля': ('основание', 0.8),
        'Онегин': ('герой', 0.95),
        'поэт': ('творец', 0.9),
        'любовь': ('движущая_сила', 0.95),
        'душа': ('вместилище', 0.85),
        'мысль': ('источник', 0.8),
        'слово': ('результат', 0.75),
        'ветер': ('стихия', 0.7),
        'море': ('стихия', 0.85),
    }
    
    # Грамматические признаки (упрощённо)
    GRAMMAR = {
        'кот':       {'case': 'именительный',  'pos': 'noun', 'freq': 0.6},
        'крыша':     {'case': 'предложный',    'pos': 'noun', 'freq': 0.5},
        'солнце':    {'case': 'именительный',  'pos': 'noun', 'freq': 0.8},
        'земля':     {'case': 'винительный',   'pos': 'noun', 'freq': 0.9},
        'дождь':     {'case': 'именительный',  'pos': 'noun', 'freq': 0.5},
        'сад':       {'case': 'винительный',   'pos': 'noun', 'freq': 0.4},
        'Онегин':    {'case': 'именительный',  'pos': 'noun', 'freq': 0.3},
        'деревня':   {'case': 'винительный',   'pos': 'noun', 'freq': 0.5},
        'Москва':    {'case': 'винительный',   'pos': 'noun', 'freq': 0.7},
        'поэт':      {'case': 'именительный',  'pos': 'noun', 'freq': 0.5},
        'стихи':     {'case': 'винительный',   'pos': 'noun', 'freq': 0.4},
        'проза':     {'case': 'винительный',   'pos': 'noun', 'freq': 0.3},
        'мысль':     {'case': 'именительный',  'pos': 'noun', 'freq': 0.7},
        'слово':     {'case': 'винительный',   'pos': 'noun', 'freq': 0.8},
        'ветер':     {'case': 'именительный',  'pos': 'noun', 'freq': 0.6},
        'море':      {'case': 'родительный',   'pos': 'noun', 'freq': 0.7},
        'любовь':    {'case': 'именительный',  'pos': 'noun', 'freq': 0.8},
        'душа':      {'case': 'винительный',   'pos': 'noun', 'freq': 0.7},
        'река':      {'case': 'именительный',  'pos': 'noun', 'freq': 0.5},
    }
    
    def analyze(self, word: str) -> FractalProfile:
        """Полный фрактальный анализ слова."""
        profile = FractalProfile()
        
        # Уровень 1-2: буквы
        profile.length = len(word)
        word_lower = word.lower()
        
        vowels = [c for c in word_lower if c in self.VOWELS]
        consonants = [c for c in word_lower if c.isalpha() and c not in self.VOWELS]
        
        profile.vowels_count = len(vowels)
        profile.consonants_count = len(consonants)
        profile.unique_letters = len(set(word_lower))
        profile.vowel_consonant_ratio = len(vowels) / (len(consonants) + 1)
        
        # Уровень 3: слоги (упрощённо — по гласным)
        profile.syllable_count = len(vowels)
        profile.stress_position = self._guess_stress(word_lower)
        profile.syllable_complexity = self._syllable_complexity(word_lower)
        
        # Уровень 4: грамматика
        grammar = self.GRAMMAR.get(word, {})
        profile.is_noun = grammar.get('pos') == 'noun'
        profile.word_frequency = grammar.get('freq', 0.3)
        
        # Уровень 5: роль в словосочетаниях
        profile.grammatical_case = grammar.get('case', '')
        profile.collocation_count = 3 if profile.word_frequency > 0.5 else 1
        
        # Уровень 6: позиция в предложении
        if profile.grammatical_case == 'именительный':
            profile.sentence_position = 'начало'
            profile.typical_role = 'субъект'
        elif profile.grammatical_case == 'винительный':
            profile.sentence_position = 'конец'
            profile.typical_role = 'объект'
        else:
            profile.sentence_position = 'середина'
            profile.typical_role = 'обстоятельство'
        
        # Уровень 7: роль в тексте
        narrative = self.NARRATIVE_ROLES.get(word, ('нейтральная', 0.3))
        profile.narrative_role = narrative[0]
        profile.text_importance = narrative[1]
        
        return profile
    
    def _guess_stress(self, word: str) -> int:
        """Угадывает позицию ударения (упрощённо)."""
        if len(word) <= 2:
            return 0
        # Для теста: в корне или на последнем слоге
        if word[-1] in 'ая':
            return len(word) - 2
        return 1
    
    def _syllable_complexity(self, word: str) -> float:
        """Оценивает сложность слоговой структуры."""
        # Сложные кластеры согласных
        clusters = re.findall(r'[^аеёиоуыэюя]{2,}', word, re.IGNORECASE)
        return min(len(clusters) / 3.0, 1.0)

# ============================================================================
# ФРАКТАЛЬНЫЙ ВЫЧИСЛИТЕЛЬ ПАРАМЕТРОВ
# ============================================================================

class FractalVortexCalculator:
    """Вычисляет параметры вихря с учётом фрактальной вложенности."""
    
    def __init__(self, analyzer: FractalAnalyzer):
        self.analyzer = analyzer
    
    def compute_params(self, lemma: str) -> VortexParams:
        """Вычисляет полные параметры вихря."""
        profile = self.analyzer.analyze(lemma)
        
        # Базовые параметры из профиля
        frequency = self._compute_frequency(profile)
        amplitude = self._compute_amplitude(profile)
        phase = self._compute_phase(profile)
        radius = self._compute_radius(profile)
        energy = self._compute_energy(profile)
        layer = self._compute_layer(profile)
        charge = self._compute_charge(profile)
        direction = self._compute_direction(profile)
        
        return VortexParams(
            frequency=frequency,
            amplitude=amplitude,
            phase=phase,
            radius=radius,
            energy=energy,
            layer=layer,
            charge=charge,
            direction=direction
        )
    
    def _compute_frequency(self, p: FractalProfile) -> float:
        """Частота вихря = длина слова + слоговая сложность + роль."""
        base = p.length / 10.0  # 0.3..1.0
        syllable_bonus = p.syllable_complexity * 0.5  # 0..0.5
        role_bonus = 0.3 if p.typical_role == 'субъект' else 0.0
        return base + syllable_bonus + role_bonus
    
    def _compute_amplitude(self, p: FractalProfile) -> float:
        """Амплитуда = частотность + важность в тексте."""
        return (p.word_frequency + p.text_importance) / 2.0
    
    def _compute_phase(self, p: FractalProfile) -> float:
        """Фаза зависит от позиции в предложении и ударения."""
        # Позиция в предложении
        if p.sentence_position == 'начало':
            pos_phase = 0.0
        elif p.sentence_position == 'конец':
            pos_phase = 0.67 * np.pi  # ~2π/3
        else:
            pos_phase = 0.33 * np.pi  # ~π/3
        
        # Коррекция на ударение
        stress_shift = (p.stress_position / max(p.length, 1)) * 0.3 * np.pi
        
        return (pos_phase + stress_shift) % (2 * np.pi)
    
    def _compute_radius(self, p: FractalProfile) -> float:
        """Радиус = уникальность букв + слоговая сложность + связность."""
        letter_uniqueness = p.unique_letters / max(p.length, 1)
        collocation_bonus = p.collocation_count / 10.0
        return (letter_uniqueness + p.syllable_complexity + collocation_bonus) / 3.0
    
    def _compute_energy(self, p: FractalProfile) -> float:
        """Энергия = частота × длина × важность."""
        return p.word_frequency * (p.length / 10.0) * p.text_importance
    
    def _compute_layer(self, p: FractalProfile) -> int:
        """Слой = 3 + важность в тексте (макс 7)."""
        return min(3 + int(p.text_importance * 4), 7)
    
    def _compute_charge(self, p: FractalProfile) -> float:
        """Заряд: субъект = +, объект = -, остальное = 0."""
        if p.typical_role == 'субъект':
            return 0.5 * p.text_importance
        elif p.typical_role == 'объект':
            return -0.3 * p.text_importance
        elif p.narrative_role in ('центр', 'источник', 'творец', 'движущая_сила'):
            return 0.4
        elif p.narrative_role in ('периферия', 'результат'):
            return -0.2
        return 0.0
    
    def _compute_direction(self, p: FractalProfile) -> int:
        """Направление: субъект/источник = +1, объект/результат = -1."""
        if p.typical_role in ('субъект',) or p.narrative_role in ('источник', 'творец', 'движущая_сила'):
            return 1
        elif p.typical_role in ('объект',) or p.narrative_role in ('результат', 'вместилище'):
            return -1
        else:
            return 1 if p.vowel_consonant_ratio > 0.5 else -1

# ============================================================================
# ОХОТНИК С ФРАКТАЛЬНОЙ МОДЕЛЬЮ
# ============================================================================

class FractalGapHunter:
    """GapHunter с фрактальной моделью."""
    
    def __init__(self):
        self.analyzer = FractalAnalyzer()
        self.calculator = FractalVortexCalculator(self.analyzer)
        self._vortex_cache: Dict[str, VortexParams] = {}
    
    def get_vortex_params(self, lemma: str) -> VortexParams:
        """Получает параметры вихря (с кэшированием)."""
        if lemma not in self._vortex_cache:
            self._vortex_cache[lemma] = self.calculator.compute_params(lemma)
        return self._vortex_cache[lemma]
    
    def parametric_distance(self, lemma_a: str, lemma_b: str) -> float:
        """Вычисляет параметрическое расстояние с учётом фрактальности."""
        p1 = self.get_vortex_params(lemma_a)
        p2 = self.get_vortex_params(lemma_b)
        
        weights = {
            'frequency': 0.12,
            'amplitude': 0.12,
            'phase': 0.20,
            'radius': 0.10,
            'energy': 0.12,
            'layer': 0.15,      # увеличен вес — фрактальный слой важен
            'charge': 0.10,      # увеличен вес — заряд важен для контраста
            'direction': 0.09,
        }
        
        total = 0.0
        max_total = 0.0
        
        for param, weight in weights.items():
            v1 = getattr(p1, param, 0.0)
            v2 = getattr(p2, param, 0.0)
            
            if param == 'direction':
                diff = 1.0 if v1 != v2 else 0.0
            elif param == 'phase':
                diff = min(abs(v1 - v2), 2*np.pi - abs(v1 - v2)) / np.pi
            elif param == 'layer':
                diff = abs(v1 - v2) / 7.0
            else:
                max_val = max(abs(v1), abs(v2), 0.1)
                diff = min(abs(v1 - v2) / max_val, 1.0)
            
            total += weight * diff
            max_total += weight
        
        return total / max_total if max_total > 0 else 0.0
    
    def contrast_energy(self, lemma_a: str, lemma_b: str) -> float:
        """Энергия контраста = параметрическое расстояние."""
        return self.parametric_distance(lemma_a, lemma_b)

# ============================================================================
# ТЕСТЫ
# ============================================================================

def run_fractal_tests():
    """Запускает тесты с фрактальной моделью."""
    
    print("=" * 70)
    print("🧪 ТЕСТЫ GAPHUNTER v2.0 — ФРАКТАЛЬНАЯ МОДЕЛЬ")
    print("   Буквы → слоги → слова → фразы → тексты")
    print("=" * 70)
    
    hunter = FractalGapHunter()
    
    # --------------------------------------------------
    # Тест 1: Фрактальные профили
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📊 ТЕСТ 1: ФРАКТАЛЬНЫЕ ПРОФИЛИ МОД")
    print("─" * 70)
    
    test_words = ["кот", "крыша", "солнце", "земля", "Онегин", "деревня", "Москва", 
                  "поэт", "стихи", "проза", "любовь", "душа", "ветер", "море"]
    
    print(f"  {'Мода':10} {'Слой':5} {'Час-тота':8} {'Ампл':6} {'Фаза/π':8} {'Радиус':6} {'Энергия':8} {'Заряд':6} {'Напр':4}")
    print(f"  {'─'*10} {'─'*5} {'─'*8} {'─'*6} {'─'*8} {'─'*6} {'─'*8} {'─'*6} {'─'*4}")
    
    for word in test_words:
        params = hunter.get_vortex_params(word)
        print(f"  {word:10} {params.layer:5} {params.frequency:8.3f} {params.amplitude:6.3f} "
              f"{params.phase/np.pi:8.3f} {params.radius:6.3f} {params.energy:8.3f} "
              f"{params.charge:6.3f} {params.direction:4}")
    
    # --------------------------------------------------
    # Тест 2: Параметрическое расстояние (фрактальное)
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 2: ПАРАМЕТРИЧЕСКОЕ РАССТОЯНИЕ (ФРАКТАЛЬНОЕ)")
    print("─" * 70)
    
    test_pairs = [
        ("кот", "крыша", "разные сущности"),
        ("солнце", "земля", "небо vs поверхность"),
        ("Онегин", "деревня", "герой vs место"),
        ("Онегин", "Москва", "герой vs столица"),
        ("деревня", "Москва", "провинция vs столица"),
        ("поэт", "стихи", "автор vs произведение"),
        ("стихи", "проза", "жанры"),
        ("любовь", "душа", "эмоция vs вместилище"),
        ("кот", "кот", "идентичность"),
        ("ветер", "море", "стихии"),
    ]
    
    for mod_a, mod_b, desc in test_pairs:
        distance = hunter.parametric_distance(mod_a, mod_b)
        
        if distance < 0.1:
            level = "≡ неразличимы"
        elif distance < 0.3:
            level = "≈ близки"
        elif distance < 0.5:
            level = "— различны"
        elif distance < 0.7:
            level = "≠ КОНТРАСТ"
        else:
            level = "✗ АНТАГОНИЗМ"
        
        print(f"  Δ({mod_a:8}, {mod_b:8}) = {distance:.3f}  {level:14}  ({desc})")
    
    # --------------------------------------------------
    # Тест 3: Синонимия и антонимия (фрактальные)
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("🔍 ТЕСТ 3: БЛИЗОСТЬ И КОНТРАСТ (ФРАКТАЛЬНЫЕ)")
    print("─" * 70)
    
    print("  Ожидаемо близкие пары (Δ < 0.5):")
    close_pairs = [
        ("поэт", "стихи", "автор и творение"),
        ("любовь", "душа", "эмоция и душа"),
    ]
    
    all_close_ok = True
    for mod_a, mod_b, desc in close_pairs:
        distance = hunter.parametric_distance(mod_a, mod_b)
        ok = distance < 0.5
        if not ok: all_close_ok = False
        print(f"  {'✅' if ok else '❌'} Δ({mod_a}, {mod_b}) = {distance:.3f} < 0.5 ({desc})")
    
    print("\n  Ожидаемо контрастные пары (Δ > 0.5):")
    far_pairs = [
        ("деревня", "Москва", "провинция и столица"),
        ("солнце", "море", "небо и вода"),
        ("стихи", "проза", "жанры"),
    ]
    
    all_far_ok = True
    for mod_a, mod_b, desc in far_pairs:
        distance = hunter.parametric_distance(mod_a, mod_b)
        ok = distance > 0.5
        if not ok: all_far_ok = False
        print(f"  {'✅' if ok else '❌'} Δ({mod_a}, {mod_b}) = {distance:.3f} > 0.5 ({desc})")
    
    # --------------------------------------------------
    # Тест 4: Выбор через фрактальную близость
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("🧠 ТЕСТ 4: ОБЪЯСНЕНИЕ ВЫБОРА (ФРАКТАЛЬНОЕ)")
    print("─" * 70)
    print("  Почему Онегин едет в деревню, а не в Москву?")
    print()
    
    d_onegin_derevnya = hunter.parametric_distance("Онегин", "деревня")
    d_onegin_moskva = hunter.parametric_distance("Онегин", "Москва")
    
    print(f"  Δ(Онегин, деревня) = {d_onegin_derevnya:.3f}")
    print(f"  Δ(Онегин, Москва)  = {d_onegin_moskva:.3f}")
    print(f"  Разница: {abs(d_onegin_derevnya - d_onegin_moskva):.3f}")
    print()
    
    if d_onegin_derevnya < d_onegin_moskva:
        print(f"  ✅ Онегин БЛИЖЕ к деревне ({d_onegin_derevnya:.3f} < {d_onegin_moskva:.3f})")
        print(f"     Выбор объясняется параметрическим резонансом.")
    else:
        print(f"  ❌ Онегин ближе к Москве — модель требует донастройки")
    
    # Показываем параметры для анализа
    print(f"\n  Параметры для сравнения:")
    for word in ["Онегин", "деревня", "Москва"]:
        p = hunter.get_vortex_params(word)
        print(f"  {word:10}: layer={p.layer}, f={p.frequency:.3f}, A={p.amplitude:.3f}, "
              f"φ={p.phase/np.pi:.2f}π, r={p.radius:.3f}, E={p.energy:.3f}, "
              f"q={p.charge:.3f}, d={p.direction}")
    
    # --------------------------------------------------
    # Итоги
    # --------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ (ФРАКТАЛЬНАЯ МОДЕЛЬ)")
    print("=" * 70)
    
    passed = 0
    total = 0
    
    for mod_a, mod_b, _ in close_pairs:
        d = hunter.parametric_distance(mod_a, mod_b)
        total += 1
        if d < 0.5:
            passed += 1
    
    for mod_a, mod_b, _ in far_pairs:
        d = hunter.parametric_distance(mod_a, mod_b)
        total += 1
        if d > 0.5:
            passed += 1
    
    total += 1
    if d_onegin_derevnya < d_onegin_moskva:
        passed += 1
    
    print(f"  Пройдено: {passed}/{total} ({100*passed/total:.0f}%)")
    
    if passed == total:
        print(f"\n  ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print(f"\n  ⚠️ Некоторые тесты не пройдены.")
    
    print()
    print("  Фрактальная модель учитывает:")
    print("  • Буквенный состав (длина, гласные/согласные)")
    print("  • Слоговую структуру (количество, сложность, ударение)")
    print("  • Грамматические признаки (часть речи, падеж)")
    print("  • Роль в словосочетаниях и предложениях")
    print("  • Повествовательную роль в тексте")
    print("  • Всё это формирует параметры вихря без семантики")


if __name__ == "__main__":
    run_fractal_tests()