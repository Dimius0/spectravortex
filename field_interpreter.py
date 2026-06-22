#!/usr/bin/env python3
"""
field_interpreter.py — Нарративный интерпретатор полей v2.0
Превращает числовые отчёты в осмысленные истории о природе данных.
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# ============================================================================
# СУЩНОСТИ ИНТЕРПРЕТАЦИИ
# ============================================================================

class InterpretationConfidence(Enum):
    VERY_HIGH = "очень высокая"
    HIGH = "высокая"
    MEDIUM = "средняя"
    LOW = "низкая"
    SPECULATIVE = "предположительная"

class NarrativeStyle(Enum):
    SCIENTIFIC = "scientific"
    DETECTIVE = "detective"
    EDUCATIONAL = "educational"
    TECHNICAL = "technical"

@dataclass
class Evidence:
    """Доказательство для интерпретации."""
    fact: str
    value: float
    interpretation: str
    strength: float  # 0..1

@dataclass
class InterpretedResult:
    """Полный интерпретированный результат."""
    # Основной вердикт
    verdict: str
    subtitle: str
    confidence: InterpretationConfidence
    
    # Нарратив
    narrative: str
    narrative_style: NarrativeStyle
    
    # Структурированная информация
    data_identity: Dict
    behavior_patterns: List[str]
    evidence: List[Evidence]
    comparisons: List[Dict]
    
    # Рекомендации
    recommendations: List[Dict]
    next_steps: List[str]
    warnings: List[str]
    
    # Метаданные интерпретации
    interpretation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    interpreter_version: str = "2.0"

# ============================================================================
# БАЗА ЗНАНИЙ О ТИПАХ ДАННЫХ
# ============================================================================

class DataKnowledgeBase:
    """База знаний о характеристиках различных типов данных."""
    
    # Эталонные профили для сравнения
    PROFILES = {
        "natural_text": {
            "description": "Естественный текст (книги, статьи, код)",
            "entropy_range": (3.5, 5.0),
            "structure_range": (0.5, 0.9),
            "transition_density": (0.1, 0.5),
            "grammar_confidence": (0.5, 1.0),
            "typical_n": 4,
            "examples": "Литература, исходный код, логи",
        },
        "compressed_data": {
            "description": "Сжатые данные (ZIP, GZIP, изображения)",
            "entropy_range": (6.5, 7.8),
            "structure_range": (0.1, 0.4),
            "transition_density": (0.01, 0.1),
            "grammar_confidence": (0.0, 0.3),
            "typical_n": 8,
            "examples": "Архивы, JPEG, PNG, MP3",
        },
        "encrypted_data": {
            "description": "Зашифрованные данные (AES, RSA, шифротексты)",
            "entropy_range": (7.5, 8.0),
            "structure_range": (0.0, 0.1),
            "transition_density": (0.0, 0.01),
            "grammar_confidence": (0.0, 0.1),
            "typical_n": 16,
            "examples": "Шифротексты, криптографические ключи",
        },
        "protocol_data": {
            "description": "Сетевые протоколы и структурированные форматы",
            "entropy_range": (4.0, 6.5),
            "structure_range": (0.4, 0.8),
            "transition_density": (0.05, 0.3),
            "grammar_confidence": (0.3, 0.7),
            "typical_n": 8,
            "examples": "TCP/IP пакеты, биткоин-блоки, базы данных",
        },
        "hash_data": {
            "description": "Хеш-суммы и криптографические отпечатки",
            "entropy_range": (7.8, 8.0),
            "structure_range": (0.0, 0.05),
            "transition_density": (0.0, 0.001),
            "grammar_confidence": (0.0, 0.05),
            "typical_n": 32,
            "examples": "SHA-256, MD5 хеши, блокчейн заголовки",
        },
        "executable_code": {
            "description": "Исполняемый код (машинные инструкции)",
            "entropy_range": (5.0, 6.5),
            "structure_range": (0.3, 0.6),
            "transition_density": (0.05, 0.2),
            "grammar_confidence": (0.2, 0.5),
            "typical_n": 8,
            "examples": "PE/ELF файлы, shellcode, байт-код",
        },
    }
    
    # Паттерны поведения
    BEHAVIOR_PATTERNS = {
        "strong_clustering": {
            "condition": lambda r: r.spectral_gap > 0.4,
            "description": "Выраженная кластеризация — данные группируются в чёткие блоки",
            "implication": "Возможно, данные состоят из независимых сегментов (пакеты, записи)",
        },
        "rapid_mixing": {
            "condition": lambda r: r.mixing_time < 2.0,
            "description": "Быстрое перемешивание — информация быстро распространяется",
            "implication": "Данные хорошо перемешаны, нет изолированных областей",
        },
        "hidden_regularity": {
            "condition": lambda r: r.entropy > 6.5 and r.structure_index > 0.2,
            "description": "Скрытая регулярность в высокоэнтропийных данных",
            "implication": "Подозрение на стеганографию или структурированное шифрование",
        },
        "grammar_emergence": {
            "condition": lambda r: r.total_rules > 5 and r.grammar_confidence > 0.5,
            "description": "Возникновение грамматики — найдены повторяющиеся правила",
            "implication": "Данные следуют определённому протоколу или формату",
        },
    }
    
    @classmethod
    def find_best_match(cls, report) -> Tuple[str, float]:
        """Находит наиболее подходящий профиль данных."""
        best_match = None
        best_score = 0.0
        
        for profile_name, profile in cls.PROFILES.items():
            score = cls._match_score(report, profile)
            if score > best_score:
                best_score = score
                best_match = profile_name
        
        return best_match, best_score
    
    @classmethod
    def _match_score(cls, report, profile) -> float:
        """Вычисляет степень соответствия профилю."""
        scores = []
        
        # Энтропия
        e_min, e_max = profile["entropy_range"]
        if e_min <= report.entropy <= e_max:
            scores.append(1.0)
        else:
            distance = min(abs(report.entropy - e_min), abs(report.entropy - e_max))
            scores.append(max(0, 1 - distance / 2))
        
        # Структура
        s_min, s_max = profile["structure_range"]
        if s_min <= report.structure_index <= s_max:
            scores.append(1.0)
        else:
            distance = min(abs(report.structure_index - s_min), 
                         abs(report.structure_index - s_max))
            scores.append(max(0, 1 - distance))
        
        # Плотность переходов
        t_min, t_max = profile["transition_density"]
        if t_min <= report.transition_density <= t_max:
            scores.append(1.0)
        else:
            distance = min(abs(report.transition_density - t_min), 
                         abs(report.transition_density - t_max))
            scores.append(max(0, 1 - distance * 10))
        
        # Грамматическая уверенность
        g_min, g_max = profile["grammar_confidence"]
        if g_min <= report.grammar_confidence <= g_max:
            scores.append(1.0)
        else:
            distance = min(abs(report.grammar_confidence - g_min), 
                         abs(report.grammar_confidence - g_max))
            scores.append(max(0, 1 - distance))
        
        return np.mean(scores)

# ============================================================================
# НАРРАТИВНЫЙ ДВИЖОК
# ============================================================================

class NarrativeEngine:
    """Генерирует человекочитаемые описания на основе метрик."""
    
    @staticmethod
    def generate_scientific_narrative(report, match_name: str, match_score: float) -> str:
        """Научный стиль повествования."""
        
        profile = DataKnowledgeBase.PROFILES.get(match_name, {})
        profile_desc = profile.get("description", "неизвестный тип данных")
        
        narrative = f"""
АНАЛИЗ СТРУКТУРЫ ПОЛЯ

Исследуемый образец демонстрирует характеристики, с вероятностью {match_score:.0%} 
соответствующие профилю "{profile_desc}". 

Энтропийный анализ показывает значение {report.entropy:.2f} бит/байт, что 
{
    "значительно ниже" if report.entropy < 4 else
    "находится в среднем диапазоне" if report.entropy < 6 else
    "приближается к теоретическому максимуму" if report.entropy > 7.5 else
    "находится в высоком диапазоне"
} для данного типа данных.

Индекс структурированности составляет {report.structure_index:.2f}, указывая на 
{
    "высокоорганизованную" if report.structure_index > 0.7 else
    "умеренно организованную" if report.structure_index > 0.4 else
    "слабо организованную" if report.structure_index > 0.2 else
    "практически отсутствующую"
} внутреннюю структуру.

Грамматический анализ выявил {report.total_rules} правил трансформации и 
{report.total_patterns} обменных паттернов, с общей уверенностью {report.grammar_confidence:.2f}.
{
    "Это указывает на наличие устойчивого протокола или формата данных." 
    if report.grammar_confidence > 0.5 else
    "Грамматическая структура выражена слабо, что характерно для случайных или зашифрованных данных."
    if report.grammar_confidence < 0.2 else
    "Обнаружены отдельные грамматические элементы, но целостная структура не выявлена."
}

Спектральный анализ показывает доминирующее собственное значение {report.dominant_eigenvalue:.3f}
и спектральный разрыв {report.spectral_gap:.3f}. 
{
    "Это свидетельствует о наличии выраженных кластеров в данных." 
    if report.spectral_gap > 0.3 else
    "Данные относительно однородны, без выраженной кластеризации."
}
"""
        return narrative
    
    @staticmethod
    def generate_detective_narrative(report, match_name: str, anomalies: List) -> str:
        """Детективный стиль (для поиска аномалий)."""
        
        narrative = f"""
🕵️ ДЕТЕКТИВНЫЙ АНАЛИЗ

Расследуя природу этого файла, я обнаружил следующее:

Первое, что бросается в глаза — энтропия {report.entropy:.2f} бит/байт. 
{
    "Это как идеально перемешанная колода карт — никаких закономерностей."
    if report.entropy > 7.8 else
    "Высокая, но не максимальная — значит, здесь что-то скрыто."
    if report.entropy > 7.0 else
    "Умеренная — уже есть за что зацепиться."
    if report.entropy > 5.0 else
    "Низкая — данные буквально кричат о своей структуре."
}

Индекс структуры {report.structure_index:.2f}. 
{
    "Почти идеальный порядок. Это не случайность." 
    if report.structure_index > 0.8 else
    "Есть явные следы организации. Кто-то здесь наследил."
    if report.structure_index > 0.5 else
    "Структура едва уловима. Возможно, это маскировка."
    if report.structure_index > 0.2 else
    "Хаос. Но в хаосе тоже есть свой порядок..."
}

Я насчитал {report.total_rules} правил и {report.total_patterns} паттернов.
{
    "Это целый язык! У этих данных есть своя грамматика."
    if report.total_rules > 10 else
    "Несколько устойчивых выражений — уже можно составить словарь."
    if report.total_rules > 3 else
    "Почти ничего. Либо это очень простой язык, либо очень сложный шифр."
}
"""
        
        if anomalies:
            narrative += f"\nИ вот что ещё интересно — я нашёл {len(anomalies)} аномалий:\n"
            for anomaly in anomalies[:3]:
                narrative += f"• {anomaly.get('type', 'неизвестная')}: {anomaly.get('description', '')}\n"
            narrative += "\nЭти аномалии — как отпечатки пальцев на месте преступления. Они расскажут нам, что здесь произошло."
        
        return narrative
    
    @staticmethod
    def generate_educational_narrative(report) -> str:
        """Образовательный стиль (для обучения)."""
        
        narrative = f"""
📚 ЧТО ГОВОРИТ НАМ ПОЛЕ H?

Представьте, что данные — это текст на неизвестном языке. Наш анализатор пытается 
понять структуру этого языка, даже не зная его алфавита.

Энтропия ({report.entropy:.2f} бит/байт) — это мера "неожиданности" каждого следующего 
байта. В английском тексте энтропия около 4 бит/байт, потому что буквы предсказуемы. 
В зашифрованных данных — почти 8 бит/байт, потому что каждый байт — сюрприз.

Индекс структуры ({report.structure_index:.2f}) показывает, насколько данные 
"грамматичны". Если бы это был язык, то:
{
    "Это как поэзия с чёткими рифмами и ритмом."
    if report.structure_index > 0.7 else
    "Это как проза — есть структура, но свободная."
    if report.structure_index > 0.4 else
    "Это как случайный набор слов."
    if report.structure_index > 0.1 else
    "Это как белый шум — никакой лингвистической структуры."
}

Мы нашли {report.total_rules} грамматических правил. В русском языке, например, 
есть правила склонения (окончания -а, -у, -ом). Здесь тоже есть свои "окончания" — 
повторяющиеся последовательности байт, которые меняются по определённым законам.

Обменных паттернов найдено {report.total_patterns}. Это как глаголы в предложении — 
они связывают "подлежащее" и "дополнение", показывая, как данные переходят из одного 
состояния в другое.
"""
        return narrative

# ============================================================================
# ГЛАВНЫЙ ИНТЕРПРЕТАТОР
# ============================================================================

class FieldInterpreter:
    """
    Главный интерпретатор полей.
    Превращает FieldReport в человекочитаемый диагноз с нарративом.
    """
    
    def __init__(self, style: NarrativeStyle = NarrativeStyle.SCIENTIFIC):
        self.style = style
        self.knowledge_base = DataKnowledgeBase()
        self.narrative_engine = NarrativeEngine()
        
        # История интерпретаций для контекста
        self.interpretation_history = []
    
    def interpret(self, report, context: Dict = None) -> InterpretedResult:
        """
        Основной метод интерпретации.
        
        Args:
            report: FieldReport от FieldAnalyzer
            context: Дополнительный контекст (предыдущие анализы, метаданные файла)
        """
        
        # 1. Идентификация данных
        match_name, match_score = DataKnowledgeBase.find_best_match(report)
        profile = DataKnowledgeBase.PROFILES.get(match_name, {})
        
        # 2. Определение уверенности
        confidence = self._assess_confidence(report, match_score)
        
        # 3. Поиск поведенческих паттернов
        behaviors = self._detect_behaviors(report)
        
        # 4. Сбор доказательств
        evidence = self._collect_evidence(report, match_name, match_score)
        
        # 5. Генерация нарратива
        narrative = self._generate_narrative(report, match_name, match_score)
        
        # 6. Сравнение с эталонами
        comparisons = self._make_comparisons(report, match_name)
        
        # 7. Рекомендации
        recommendations, next_steps, warnings = self._make_recommendations(
            report, match_name, behaviors, context
        )
        
        # 8. Формирование вердикта
        verdict, subtitle = self._form_verdict(report, match_name, match_score, behaviors)
        
        # Создаём результат
        result = InterpretedResult(
            verdict=verdict,
            subtitle=subtitle,
            confidence=confidence,
            narrative=narrative,
            narrative_style=self.style,
            data_identity={
                "best_match": match_name,
                "match_score": match_score,
                "profile_description": profile.get("description", "Неизвестный тип"),
                "typical_examples": profile.get("examples", ""),
            },
            behavior_patterns=behaviors,
            evidence=evidence,
            comparisons=comparisons,
            recommendations=recommendations,
            next_steps=next_steps,
            warnings=warnings,
        )
        
        # Сохраняем в историю
        self.interpretation_history.append(result)
        
        return result
    
    def _assess_confidence(self, report, match_score: float) -> InterpretationConfidence:
        """Оценка уверенности в интерпретации."""
        
        # Факторы уверенности
        factors = []
        
        # Соответствие профилю
        factors.append(match_score)
        
        # Согласованность метрик
        consistency = 1.0
        if report.entropy > 7.0 and report.structure_index > 0.5:
            consistency = 0.3  # Необычное сочетание
        elif report.entropy < 4.0 and report.structure_index < 0.2:
            consistency = 0.3  # Тоже необычно
        factors.append(consistency)
        
        # Количество данных
        if hasattr(report, 'total_lemmas'):
            data_factor = min(1.0, report.total_lemmas / 100)
        else:
            data_factor = 0.5
        factors.append(data_factor)
        
        confidence_score = np.mean(factors)
        
        if confidence_score > 0.9:
            return InterpretationConfidence.VERY_HIGH
        elif confidence_score > 0.7:
            return InterpretationConfidence.HIGH
        elif confidence_score > 0.5:
            return InterpretationConfidence.MEDIUM
        elif confidence_score > 0.3:
            return InterpretationConfidence.LOW
        else:
            return InterpretationConfidence.SPECULATIVE
    
    def _detect_behaviors(self, report) -> List[str]:
        """Обнаружение поведенческих паттернов."""
        behaviors = []
        
        for pattern_name, pattern in DataKnowledgeBase.BEHAVIOR_PATTERNS.items():
            try:
                if pattern["condition"](report):
                    behaviors.append(pattern["description"])
            except:
                pass
        
        return behaviors
    
    def _collect_evidence(self, report, match_name: str, match_score: float) -> List[Evidence]:
        """Сбор доказательств для интерпретации."""
        evidence = []
        
        # Энтропия
        evidence.append(Evidence(
            fact=f"Энтропия Шеннона: {report.entropy:.2f} бит/байт",
            value=report.entropy / 8.0,
            interpretation=self._interpret_entropy(report.entropy),
            strength=0.9,
        ))
        
        # Структура
        evidence.append(Evidence(
            fact=f"Индекс структурированности: {report.structure_index:.3f}",
            value=report.structure_index,
            interpretation=self._interpret_structure(report.structure_index),
            strength=0.8,
        ))
        
        # Грамматика
        if hasattr(report, 'grammar_confidence'):
            evidence.append(Evidence(
                fact=f"Грамматическая уверенность: {report.grammar_confidence:.3f}",
                value=report.grammar_confidence,
                interpretation=self._interpret_grammar(report),
                strength=0.7,
            ))
        
        # Спектральный разрыв
        if hasattr(report, 'spectral_gap') and report.spectral_gap > 0:
            evidence.append(Evidence(
                fact=f"Спектральный разрыв: {report.spectral_gap:.3f}",
                value=min(1.0, report.spectral_gap),
                interpretation=f"Указывает на {'наличие' if report.spectral_gap > 0.3 else 'отсутствие'} выраженных кластеров",
                strength=0.6,
            ))
        
        # Соответствие профилю
        evidence.append(Evidence(
            fact=f"Соответствие профилю '{match_name}': {match_score:.0%}",
            value=match_score,
            interpretation=f"Данные {'хорошо' if match_score > 0.7 else 'частично' if match_score > 0.4 else 'слабо'} соответствуют эталонному профилю",
            strength=0.5,
        ))
        
        return evidence
    
    def _interpret_entropy(self, entropy: float) -> str:
        if entropy < 3.5:
            return "Очень низкая — данные высокоизбыточны (текст, логи)"
        elif entropy < 5.0:
            return "Средняя — типично для структурированных бинарных данных"
        elif entropy < 7.0:
            return "Высокая — данные сжаты или частично зашифрованы"
        else:
            return "Максимальная — данные случайны или криптографически защищены"
    
    def _interpret_structure(self, structure: float) -> str:
        if structure > 0.7:
            return "Сильная организация — данные следуют строгому протоколу"
        elif structure > 0.4:
            return "Умеренная организация — есть повторяющиеся паттерны"
        elif structure > 0.2:
            return "Слабая организация — отдельные элементы структуры"
        else:
            return "Организация отсутствует — данные хаотичны"
    
    def _interpret_grammar(self, report) -> str:
        if not hasattr(report, 'total_rules'):
            return "Грамматический анализ не проводился"
        
        if report.total_rules > 10:
            return f"Богатая грамматика: {report.total_rules} правил — данные подобны языку"
        elif report.total_rules > 3:
            return f"Базовая грамматика: {report.total_rules} правил — есть синтаксис"
        else:
            return "Грамматика не обнаружена — данные не структурированы как язык"
    
    def _generate_narrative(self, report, match_name: str, match_score: float) -> str:
        """Генерация нарратива в выбранном стиле."""
        
        if self.style == NarrativeStyle.SCIENTIFIC:
            return self.narrative_engine.generate_scientific_narrative(
                report, match_name, match_score
            )
        elif self.style == NarrativeStyle.DETECTIVE:
            anomalies = getattr(report, 'anomalies', [])
            return self.narrative_engine.generate_detective_narrative(
                report, match_name, anomalies
            )
        elif self.style == NarrativeStyle.EDUCATIONAL:
            return self.narrative_engine.generate_educational_narrative(report)
        else:
            # Технический стиль — просто факты
            return self._generate_technical_narrative(report, match_name)
    
    def _generate_technical_narrative(self, report, match_name: str) -> str:
        """Технический стиль — кратко и по делу."""
        return f"""
TECHNICAL SUMMARY:
Type: {match_name}
Entropy: {report.entropy:.2f} bits/byte
Structure: {report.structure_index:.3f}
Grammar Rules: {getattr(report, 'total_rules', 'N/A')}
Patterns: {getattr(report, 'total_patterns', 'N/A')}
Dominant Eigenvalue: {getattr(report, 'dominant_eigenvalue', 'N/A')}
"""
    
    def _make_comparisons(self, report, match_name: str) -> List[Dict]:
        """Сравнение с другими профилями."""
        comparisons = []
        
        for profile_name, profile in DataKnowledgeBase.PROFILES.items():
            if profile_name != match_name:
                score = DataKnowledgeBase._match_score(report, profile)
                if score > 0.5:  # Значимое сходство
                    comparisons.append({
                        "profile": profile_name,
                        "description": profile["description"],
                        "similarity": score,
                        "difference_from_best": score - DataKnowledgeBase._match_score(
                            report, DataKnowledgeBase.PROFILES[match_name]
                        ),
                    })
        
        comparisons.sort(key=lambda x: x["similarity"], reverse=True)
        return comparisons[:3]
    
    def _make_recommendations(self, report, match_name: str, 
                             behaviors: List[str], context: Dict = None) -> Tuple:
        """Формирование рекомендаций."""
        
        recommendations = []
        next_steps = []
        warnings = []
        
        # Рекомендации по анализу
        if match_name == "encrypted_data":
            recommendations.append({
                "priority": "high",
                "action": "Проверить на известные шифры",
                "detail": "Сравнить с базами сигнатур шифротекстов",
            })
            next_steps.append("Запустить криптоанализ заголовков")
            warnings.append("Данные могут быть зашифрованы — расшифровка без ключа невозможна")
        
        elif match_name == "compressed_data":
            recommendations.append({
                "priority": "medium",
                "action": "Определить алгоритм сжатия",
                "detail": "Проверить заголовки на известные сигнатуры (PK, 1f8b, etc.)",
            })
            next_steps.append("Попытаться декомпрессию стандартными алгоритмами")
        
        elif match_name == "protocol_data":
            recommendations.append({
                "priority": "high",
                "action": "Извлечь структуру протокола",
                "detail": f"Обнаружено {getattr(report, 'total_rules', 0)} правил — можно восстановить формат",
            })
            next_steps.append("Визуализировать грамматическое дерево протокола")
        
        # Общие рекомендации
        if report.structure_index > 0.5:
            next_steps.append("Исследовать грамматические правила для понимания формата")
        
        if hasattr(report, 'anomalies') and report.anomalies:
            warnings.append(f"Обнаружено {len(report.anomalies)} аномалий — требуется дополнительное исследование")
            next_steps.append("Запустить Error Hunter для анализа аномалий")
        
        # Контекстные рекомендации
        if context and context.get('file_extension'):
            ext = context['file_extension'].lower()
            if ext in ['.exe', '.dll', '.so']:
                recommendations.append({
                    "priority": "high",
                    "action": "Анализ исполняемого файла",
                    "detail": "Проверить на наличие шелл-кода или обфускации",
                })
        
        return recommendations, next_steps, warnings
    
    def _form_verdict(self, report, match_name: str, 
                     match_score: float, behaviors: List[str]) -> Tuple[str, str]:
        """Формирование итогового вердикта."""
        
        profile = DataKnowledgeBase.PROFILES.get(match_name, {})
        profile_desc = profile.get("description", "неизвестный тип")
        
        # Основной вердикт
        if match_score > 0.8:
            verdict = f"Это {profile_desc}"
        elif match_score > 0.6:
            verdict = f"Вероятно, это {profile_desc}"
        elif match_score > 0.4:
            verdict = f"Возможно, это {profile_desc}, но есть признаки других типов"
        else:
            verdict = f"Тип данных не определён однозначно"
        
        # Подзаголовок с деталями
        details = []
        if behaviors:
            details.append(behaviors[0].lower())
        if hasattr(report, 'anomalies') and report.anomalies:
            details.append(f"обнаружено {len(report.anomalies)} аномалий")
        
        subtitle = f"Структура: {report.structure_index:.2f}, " + ", ".join(details) if details else f"Энтропия: {report.entropy:.2f} бит/байт"
        
        return verdict, subtitle

# ============================================================================
# ДЕМОНСТРАЦИЯ ИНТЕРПРЕТАТОРА
# ============================================================================

def demo_full_interpretation():
    """Полная демонстрация всех стилей интерпретации."""
    print("╔══════════════════════════════════════════════════╗")
    print("║   НАРРАТИВНЫЙ ИНТЕРПРЕТАТОР ПОЛЕЙ v2.0        ║")
    print("╚══════════════════════════════════════════════════╝")
    
    # Создаём синтетические отчёты для разных типов данных
    test_cases = [
        {
            "name": "Русский текст (роман)",
            "report": _create_fake_report(
                entropy=4.2, structure=0.78, transition_density=0.25,
                rules=12, patterns=8, grammar_conf=0.76,
                spectral_gap=0.42, anomalies=[
                    {"type": "degree_anomaly", "description": "Высокочастотные n-граммы"},
                ]
            ),
            "style": NarrativeStyle.EDUCATIONAL,
        },
        {
            "name": "Зашифрованный файл",
            "report": _create_fake_report(
                entropy=7.92, structure=0.03, transition_density=0.001,
                rules=0, patterns=0, grammar_conf=0.02,
                spectral_gap=0.01, anomalies=[]
            ),
            "style": NarrativeStyle.DETECTIVE,
        },
        {
            "name": "Биткоин-блок",
            "report": _create_fake_report(
                entropy=5.8, structure=0.65, transition_density=0.15,
                rules=25, patterns=18, grammar_conf=0.68,
                spectral_gap=0.55, anomalies=[
                    {"type": "hidden_structure", "description": "Кластеры транзакций"},
                    {"type": "strong_spectral_gap", "description": "Сегментация блока"},
                ]
            ),
            "style": NarrativeStyle.SCIENTIFIC,
        },
    ]
    
    for case in test_cases:
        print(f"\n{'='*60}")
        print(f"  ТЕСТ: {case['name']}")
        print(f"{'='*60}")
        
        interpreter = FieldInterpreter(style=case['style'])
        result = interpreter.interpret(case['report'])
        
        print(f"\n🎯 ВЕРДИКТ: {result.verdict}")
        print(f"📋 {result.subtitle}")
        print(f"📊 Уверенность: {result.confidence.value}")
        print(f"🆔 Тип: {result.data_identity['best_match']} (соответствие: {result.data_identity['match_score']:.0%})")
        
        print(f"\n📖 НАРРАТИВ ({case['style'].value}):")
        print(result.narrative)
        
        if result.evidence:
            print(f"🔍 КЛЮЧЕВЫЕ ДОКАЗАТЕЛЬСТВА:")
            for ev in result.evidence[:3]:
                print(f"  • {ev.fact}")
                print(f"    → {ev.interpretation}")
        
        if result.warnings:
            print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
            for w in result.warnings:
                print(f"  • {w}")
        
        if result.next_steps:
            print(f"\n💡 СЛЕДУЮЩИЕ ШАГИ:")
            for step in result.next_steps:
                print(f"  • {step}")

def _create_fake_report(**kwargs):
    """Создаёт синтетический отчёт для демонстрации."""
    class FakeReport:
        pass
    
    report = FakeReport()
    for key, value in kwargs.items():
        setattr(report, key, value)
    
    # Добавляем обязательные поля
    if not hasattr(report, 'entropy'):
        report.entropy = 5.0
    if not hasattr(report, 'structure_index'):
        report.structure_index = 0.5
    if not hasattr(report, 'data_nature'):
        from enum import Enum
        class FakeNature(Enum):
            value = "unknown"
        report.data_nature = FakeNature()
    
    return report

if __name__ == "__main__":
    demo_full_interpretation()