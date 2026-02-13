"""
IntuitionEngine - интуитивный контур принятия решений.
Работает с гештальтами из InternalState, обеспечивает быстрые целостные оценки.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

@dataclass
class Engram:
    """Энграмма - сжатое воспоминание о ситуации"""
    id: str
    gestalt_pattern: str
    context_hash: str
    decision_made: Dict
    outcome_score: float  # -1.0 (провал) до +1.0 (успех)
    timestamp: float
    confidence: float
    emotional_tag: str  # "fear", "joy", "surprise", "disgust"
    
    def similarity_to(self, other_gestalt: str, context_hash: str) -> float:
        """Вычисляет сходство с текущей ситуацией"""
        # Простое сравнение гештальтов (можно усложнить)
        if self.gestalt_pattern == other_gestalt:
            gestalt_sim = 1.0
        elif self.gestalt_pattern in other_gestalt or other_gestalt in self.gestalt_pattern:
            gestalt_sim = 0.7
        else:
            gestalt_sim = 0.0
        
        # Сравнение контекстных хэшей
        context_sim = 1.0 if self.context_hash == context_hash else 0.0
        
        # Общая схожесть (вес гештальта выше)
        return gestalt_sim * 0.8 + context_sim * 0.2

class Archetype:
    """Архетип - глубинный шаблон ситуации"""
    
    def __init__(self, name: str, pattern: Dict, typical_response: Dict):
        self.name = name
        self.pattern = pattern  # {параметр: условие}
        self.typical_response = typical_response
        self.activation_count = 0
        self.success_rate = 0.5
        
    def matches(self, state_data: Dict) -> Tuple[bool, float]:
        """Проверяет соответствие архетипу текущему состоянию"""
        match_score = 0.0
        total_conditions = 0
        
        for param, condition in self.pattern.items():
            total_conditions += 1
            
            if param in state_data:
                value = state_data[param]
                
                # Разные типы условий
                if isinstance(condition, (int, float)):
                    # Простое сравнение значений
                    if isinstance(value, (int, float)):
                        if abs(value - condition) < 0.1:
                            match_score += 1.0
                
                elif isinstance(condition, str):
                    # Строковое соответствие
                    if condition in str(value):
                        match_score += 1.0
                
                elif callable(condition):
                    # Функция-условие
                    if condition(value):
                        match_score += 1.0
        
        confidence = match_score / total_conditions if total_conditions > 0 else 0.0
        return confidence > 0.7, confidence

class IntuitionEngine:
    """
    Двигатель интуиции - быстрый, целостный, опытный контур принятия решений.
    Работает с гештальтами, а не с точными числами.
    """
    
    def __init__(self, engine_id: str = "default"):
        self.engine_id = engine_id
        
        # БИБЛИОТЕКА АРХЕТИПОВ (глубинные шаблоны)
        self.archetypes = self._initialize_archetypes()
        
        # БИБЛИОТЕКА ЭНГРАММ (личный опыт)
        self.engram_library: List[Engram] = []
        self.max_engrams = 100
        
        # ТЕКУЩЕЕ СОСТОЯНИЕ
        self.current_bias = {
            'tendency': 'neutral',
            'urgency': 0.0,
            'confidence': 0.0,
            'archetype': None,
            'engram_match': None,
            'override_power': 0.0
        }
        
        # СТАТИСТИКА
        self.total_decisions = 0
        self.successful_intuitions = 0
        self.failed_intuitions = 0
        
        # НАСТРОЙКИ
        self.min_confidence_threshold = 0.2
        self.override_threshold = 0.7
        self.learning_rate = 0.15
        
        print(f"[IntuitionEngine] Создан {engine_id}")
    
    def _initialize_archetypes(self) -> Dict[str, Archetype]:
        """Инициализация библиотеки архетипов"""
        
        archetypes = {}
        
                # 0. АРХЕТИП КРИТИЧЕСКОГО ПОВРЕЖДЕНИЯ (новый)
        archetypes['critical_damage'] = Archetype(
            name="critical_damage",
            pattern={
                'gestalt': lambda g: 'CRITICAL' in g or 'VULNERABLE' in g,
                'health': lambda h: h < 0.4,
                'load': lambda l: l > 0.8,
                'urgency': lambda u: u > 0.6
            },
            typical_response={
                'action_bias': 'SELF_PRESERVATION',
                'transfer_multiplier': 3.0,
                'health_recovery_bonus': 2.0,
                'message': "🚨 КРИТИЧЕСКОЕ ПОВРЕЖДЕНИЕ! Максимальная разгрузка!"
            }
        )
        
        # 1. АРХЕТИП КАСКАДНОГО ОТКАЗА
        archetypes['cascade_failure'] = Archetype(
            name="cascade_failure",
            pattern={
                'gestalt': lambda g: 'CRITICAL' in g and 'STRESSED' in g,
                'urgency': lambda u: u > 0.8,
                'dominant_need': 'safety',
                'modulator_profile.norepinephrine': lambda n: n > 0.7
            },
            typical_response={
                'action_bias': 'SELF_PRESERVATION',
                'transfer_multiplier': 2.0,
                'risk_tolerance': 0.1,
                'message': "⚠️ Каскадный отказ! Приоритет: выживание"
            }
        )
        
        # 2. АРХЕТИП ТИХОЙ ДЕГРАДАЦИИ
        archetypes['silent_degradation'] = Archetype(
            name="silent_degradation",
            pattern={
                'gestalt': lambda g: 'UNSTABLE' in g and 'ISOLATED' in g,
                'stability': lambda s: 0.3 < s < 0.6,
                'dominant_need': 'connection',
                'modulator_profile.serotonin': lambda s: s < 0.4
            },
            typical_response={
                'action_bias': 'COOPERATIVE',
                'transfer_multiplier': 1.3,
                'seek_connections': True,
                'message': "🔍 Тихая деградация. Укрепляй связи."
            }
        )
        
        # 3. АРХЕТИП СТАБИЛЬНОГО РОСТА
        archetypes['stable_growth'] = Archetype(
            name="stable_growth",
            pattern={
                'gestalt': lambda g: 'STABLE' in g and ('OPTIMISTIC' in g or 'CONNECTED' in g),
                'stability': lambda s: s > 0.7,
                'dominant_need': 'efficiency',
                'modulator_profile.dopamine': lambda d: d > 0.6
            },
            typical_response={
                'action_bias': 'OPPORTUNISTIC',
                'transfer_multiplier': 1.5,
                'exploration_bonus': 0.3,
                'message': "📈 Стабильный рост. Исследуй возможности."
            }
        )
        
        # 4. АРХЕТИП РЕЗОНАНСНОЙ УГРОЗЫ
        archetypes['resonance_threat'] = Archetype(
            name="resonance_threat",
            pattern={
                'gestalt': lambda g: 'VULNERABLE' in g and 'ISOLATED' in g,
                'urgency': lambda u: u > 0.6,
                'topology_summary.connections': lambda c: c < 2,
                'modulator_profile.norepinephrine': lambda n: n > 0.5
            },
            typical_response={
                'action_bias': 'RISK_AVERSION',
                'transfer_multiplier': 0.7,
                'consolidate_resources': True,
                'message': "🎯 Резонансная угроза. Консолидируй ресурсы."
            }
        )
        
        # 5. АРХЕТИП СОЦИАЛЬНОЙ ГАРМОНИИ
        archetypes['social_harmony'] = Archetype(
            name="social_harmony",
            pattern={
                'gestalt': lambda g: 'CONNECTED' in g and 'STABLE' in g,
                'dominant_need': 'connection',
                'modulator_profile.oxytocin': lambda o: o > 0.7,
                'topology_summary.isolation': lambda i: i < 0.3
            },
            typical_response={
                'action_bias': 'COOPERATIVE',
                'transfer_multiplier': 1.2,
                'share_resources': True,
                'message': "🤝 Социальная гармония. Делись ресурсами."
            }
        )
        
        return archetypes
    
    def _create_context_hash(self, state_data: Dict) -> str:
        """Создаёт хэш контекста для сравнения ситуаций"""
        # Селективные параметры для хэширования
        context_parts = [
            state_data.get('gestalt', ''),
            state_data.get('dominant_need', ''),
            str(round(state_data.get('urgency', 0), 2)),
            str(state_data.get('topology_summary', {}).get('connections', 0))
        ]
        
        context_string = '|'.join(context_parts)
        return hashlib.md5(context_string.encode()).hexdigest()[:8]
    
    def assess(self, state_data: Dict, analytic_confidence: float = 0.5) -> Dict:
        """
        Основной метод оценки ситуации. Возвращает интуитивный совет.
        
        Args:
            state_data: Данные из InternalState.get_for_intuition()
            analytic_confidence: Уверенность аналитических контуров (0-1)
        
        Returns:
            Словарь с интуитивным советом
        """
        self.total_decisions += 1
        
        # 1. СОЗДАНИЕ КОНТЕКСТНОГО ХЭША
        context_hash = self._create_context_hash(state_data)
        current_gestalt = state_data.get('gestalt', 'UNKNOWN')
        
        # 2. ПОИСК В ЭНГРАММАХ (личный опыт)
        engram_advice = self._consult_engrams(current_gestalt, context_hash)
        
        # 3. ПОИСК АРХЕТИПОВ (глубинные шаблоны)
        archetype_advice = self._consult_archetypes(state_data)
        
        # 4. РАНЖИРОВАНИЕ И ВЫБОР ЛУЧШЕГО СОВЕТА
        final_advice = self._resolve_advice(
            engram_advice, 
            archetype_advice, 
            state_data, 
            analytic_confidence
        )
        
        # 5. ОБНОВЛЕНИЕ ТЕКУЩЕГО СОСТОЯНИЯ
        self.current_bias = final_advice
        
        return final_advice
    
    def _consult_engrams(self, current_gestalt: str, context_hash: str) -> Optional[Dict]:
        """Консультация с библиотекой личного опыта (энграмм)"""
        if not self.engram_library:
            return None
        
        best_match = None
        best_similarity = 0.0
        
        for engram in self.engram_library:
            similarity = engram.similarity_to(current_gestalt, context_hash)
            
            if similarity > best_similarity and similarity > 0.5:
                best_similarity = similarity
                best_match = engram
        
        if best_match:
            # Учитываем исход предыдущего опыта
            outcome_weight = abs(best_match.outcome_score)  # Абсолютное значение
            confidence = best_similarity * outcome_weight
            
            advice = {
                'tendency': best_match.decision_made.get('bias', 'neutral'),
                'urgency': best_match.outcome_score < 0.0,  # Отрицательный исход → срочно
                'confidence': min(1.0, confidence),
                'archetype': None,
                'engram_match': best_match.id,
                'override_power': confidence if best_match.outcome_score < -0.5 else 0.0,
                'source': 'engram',
                'message': f"Похоже на ситуацию {best_match.id} (исход: {best_match.outcome_score:.2f})"
            }
            
            # Эмоциональная окраска
            if best_match.emotional_tag == "fear" and best_match.outcome_score < 0:
                advice['urgency'] *= 1.5
            
            return advice
        
        return None
    
    def _consult_archetypes(self, state_data: Dict) -> Optional[Dict]:
        """Консультация с библиотекой архетипов"""
        matched_archetypes = []
        
        for archetype_name, archetype in self.archetypes.items():
            matches, confidence = archetype.matches(state_data)
            
            if matches and confidence > self.min_confidence_threshold:
                matched_archetypes.append((archetype, confidence))
                archetype.activation_count += 1
        
        if matched_archetypes:
            # Выбираем архетип с наибольшей уверенностью
            best_archetype, best_confidence = max(matched_archetypes, key=lambda x: x[1])
            
            advice = best_archetype.typical_response.copy()
            advice.update({
                'tendency': advice.get('action_bias', 'neutral'),
                'confidence': best_confidence,
                'archetype': best_archetype.name,
                'engram_match': None,
                'override_power': best_confidence * best_archetype.success_rate,
                'source': 'archetype',
                'message': advice.get('message', f"Распознан архетип: {best_archetype.name}")
            })
            
            return advice
        
        return None
    
    def _resolve_advice(self, engram_advice: Optional[Dict], 
                       archetype_advice: Optional[Dict],
                       state_data: Dict,
                       analytic_confidence: float) -> Dict:
        """Разрешение конфликта между разными источниками советов"""
        
        # БАЗОВЫЙ СОВЕТ (если нет других)
        base_advice = {
            'tendency': 'ADAPTIVE',
            'urgency': state_data.get('urgency', 0.0),
            'confidence': 0.3,
            'archetype': None,
            'engram_match': None,
            'override_power': 0.0,
            'source': 'intuition_default',
            'message': "Интуиция: ситуация неопределённа, действуй адаптивно"
        }
        
        candidates = []
        
        # 1. ЭНГРАММЫ (личный опыт) - высший приоритет
        if engram_advice and engram_advice['confidence'] > 0.6:
            candidates.append((engram_advice, 1.0))
        
        # 2. АРХЕТИПЫ (глубинные шаблоны) - средний приоритет
        if archetype_advice and archetype_advice['confidence'] > 0.5:
            archetype = self.archetypes.get(archetype_advice['archetype'])
            if archetype:
                # Учитываем успешность архетипа
                priority = archetype_advice['confidence'] * archetype.success_rate
                candidates.append((archetype_advice, priority))
        
        # 3. ВЫБОР ЛУЧШЕГО КАНДИДАТА
        if candidates:
            best_advice, best_priority = max(candidates, key=lambda x: x[1])
            
            # КОРРЕКЦИЯ НА ОСНОВЕ АНАЛИТИЧЕСКОЙ УВЕРЕННОСТИ
            if analytic_confidence < 0.3:
                # Аналитика неуверенна - усиливаем интуицию
                best_advice['override_power'] = min(1.0, best_advice['override_power'] * 1.5)
                best_advice['message'] += " [Аналитика неуверенна, доверяй интуиции]"
            elif analytic_confidence > 0.8:
                # Аналитика уверена - ослабляем интуицию
                best_advice['override_power'] *= 0.5
                best_advice['message'] += " [Аналитика уверена, интуиция как дополнение]"
            
            return best_advice
        
        # 4. КОГДА НЕТ ЯСНЫХ СОВЕТОВ - адаптивный режим
        base_advice['urgency'] = state_data.get('urgency', 0.0)
        base_advice['confidence'] = 0.1  # Низкая уверенность
        
        return base_advice
    
    def learn_from_outcome(self, state_data: Dict, decision: Dict, 
                          outcome_score: float, emotional_tag: str = "neutral"):
        """
        Обучение на основе исхода решения.
        
        Args:
            state_data: Состояние при принятии решения
            decision: Принятое решение
            outcome_score: Оценка исхода (-1.0 до +1.0)
            emotional_tag: Эмоциональная метка
        """
        # 1. СОЗДАНИЕ НОВОЙ ЭНГРАММЫ
        gestalt = state_data.get('gestalt', 'UNKNOWN')
        context_hash = self._create_context_hash(state_data)
        
        engram_id = f"engram_{len(self.engram_library)}_{hashlib.md5(gestalt.encode()).hexdigest()[:6]}"
        
        new_engram = Engram(
            id=engram_id,
            gestalt_pattern=gestalt,
            context_hash=context_hash,
            decision_made=decision.copy(),
            outcome_score=outcome_score,
            timestamp=time.time(),
            confidence=decision.get('confidence', 0.5),
            emotional_tag=emotional_tag
        )
        
        # 2. ДОБАВЛЕНИЕ В БИБЛИОТЕКУ
        self.engram_library.append(new_engram)
        
        # 3. ОБНОВЛЕНИЕ АРХЕТИПОВ
        if decision.get('archetype'):
            archetype_name = decision['archetype']
            if archetype_name in self.archetypes:
                archetype = self.archetypes[archetype_name]
                # Обновляем успешность архетипа
                old_rate = archetype.success_rate
                archetype.success_rate = (1 - self.learning_rate) * old_rate + self.learning_rate * (outcome_score * 0.5 + 0.5)
        
        # 4. ОБНОВЛЕНИЕ СТАТИСТИКИ
        if outcome_score > 0:
            self.successful_intuitions += 1
        elif outcome_score < 0:
            self.failed_intuitions += 1
        
        # 5. ОЧИСТКА СТАРЫХ ЭНГРАММ
        if len(self.engram_library) > self.max_engrams:
            # Удаляем наименее полезные (близкие к нейтральному исходу)
            self.engram_library.sort(key=lambda e: abs(e.outcome_score), reverse=True)
            self.engram_library = self.engram_library[:self.max_engrams]
    
    def apply_bias_to_decision(self, analytic_decision: Dict, 
                               intuition_advice: Dict) -> Dict:
        """
        Применяет интуитивный уклон к аналитическому решению.
        
        Args:
            analytic_decision: Решение аналитических контуров
            intuition_advice: Совет интуитивного контура
        
        Returns:
            Модифицированное решение
        """
        if intuition_advice['override_power'] < 0.1:
            # Интуиция слишком слаба, чтобы влиять
            analytic_decision['intuition_tag'] = {
                'applied': False,
                'reason': 'insufficient_confidence'
            }
            return analytic_decision
        
        # КОПИРУЕМ РЕШЕНИЕ ДЛЯ МОДИФИКАЦИИ
        biased_decision = analytic_decision.copy()
        
        # ДОБАВЛЯЕМ ИНТУИТИВНУЮ МЕТКУ
        biased_decision['intuition_tag'] = {
            'applied': True,
            'tendency': intuition_advice['tendency'],
            'confidence': intuition_advice['confidence'],
            'archetype': intuition_advice['archetype'],
            'override_strength': intuition_advice['override_power'],
            'source': intuition_advice['source'],
            'message': intuition_advice.get('message', '')
        }
        
        tendency = intuition_advice['tendency']
        override_power = intuition_advice['override_power']
        
        # МОДИФИКАЦИЯ ПАРАМЕТРОВ В ЗАВИСИМОСТИ ОТ СКЛОННОСТИ
        if tendency == 'SELF_PRESERVATION':
            # Максимальная осторожность
            if 'transfer_rate' in biased_decision:
                biased_decision['transfer_rate'] *= (1.0 + override_power * 1.0)
            if 'risk_tolerance' in biased_decision:
                biased_decision['risk_tolerance'] *= (1.0 - override_power * 0.8)
            biased_decision['priority'] = 'CRITICAL'
            
        elif tendency == 'RISK_AVERSION':
            # Избегание рисков
            if 'transfer_rate' in biased_decision:
                biased_decision['transfer_rate'] *= (1.0 - override_power * 0.3)
            if 'exploration_bonus' in biased_decision:
                biased_decision['exploration_bonus'] *= (1.0 - override_power * 0.5)
                
        elif tendency == 'OPPORTUNISTIC':
            # Активные действия
            if 'transfer_rate' in biased_decision:
                biased_decision['transfer_rate'] *= (1.0 + override_power * 0.5)
            if 'exploration_bonus' in biased_decision:
                biased_decision['exploration_bonus'] *= (1.0 + override_power * 0.3)
                
        elif tendency == 'COOPERATIVE':
            # Социальная ориентация
            if 'cooperation_bias' in biased_decision:
                biased_decision['cooperation_bias'] = min(1.0, 
                    biased_decision.get('cooperation_bias', 0.5) + override_power * 0.3)
            if 'max_neighbors' in biased_decision:
                biased_decision['max_neighbors'] = min(10, 
                    biased_decision['max_neighbors'] + int(override_power * 2))
        
        # КРИТИЧЕСКИЙ ПЕРЕОПРЕДЕЛЕНИЕ (если интуиция очень уверена)
        if override_power > self.override_threshold and analytic_decision.get('confidence', 1.0) < 0.4:
            biased_decision['final_authority'] = 'INTUITION_OVERRIDE'
            biased_decision['override_reason'] = 'high_intuition_confidence_low_analytic_confidence'
        
        return biased_decision
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику работы интуитивного контура"""
        total = self.successful_intuitions + self.failed_intuitions
        success_rate = self.successful_intuitions / total if total > 0 else 0.0
        
        archetype_stats = {}
        for name, archetype in self.archetypes.items():
            archetype_stats[name] = {
                'activations': archetype.activation_count,
                'success_rate': archetype.success_rate
            }
        
        return {
            'total_decisions': self.total_decisions,
            'successful_intuitions': self.successful_intuitions,
            'failed_intuitions': self.failed_intuitions,
            'success_rate': success_rate,
            'engram_library_size': len(self.engram_library),
            'archetype_statistics': archetype_stats,
            'current_bias': self.current_bias
        }
    
    def save_to_file(self, filepath: str):
        """Сохранение состояния в файл"""
        data = {
            'engram_library': [
                {
                    'id': e.id,
                    'gestalt_pattern': e.gestalt_pattern,
                    'context_hash': e.context_hash,
                    'decision_made': e.decision_made,
                    'outcome_score': e.outcome_score,
                    'timestamp': e.timestamp,
                    'confidence': e.confidence,
                    'emotional_tag': e.emotional_tag
                }
                for e in self.engram_library
            ],
            'archetypes': {
                name: {
                    'activation_count': arch.activation_count,
                    'success_rate': arch.success_rate
                }
                for name, arch in self.archetypes.items()
            },
            'statistics': self.get_statistics()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: str):
        """Загрузка состояния из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загрузка энграмм
            self.engram_library = []
            for e_data in data.get('engram_library', []):
                engram = Engram(
                    id=e_data['id'],
                    gestalt_pattern=e_data['gestalt_pattern'],
                    context_hash=e_data['context_hash'],
                    decision_made=e_data['decision_made'],
                    outcome_score=e_data['outcome_score'],
                    timestamp=e_data['timestamp'],
                    confidence=e_data['confidence'],
                    emotional_tag=e_data['emotional_tag']
                )
                self.engram_library.append(engram)
            
            # Загрузка статистики архетипов
            for name, arch_data in data.get('archetypes', {}).items():
                if name in self.archetypes:
                    self.archetypes[name].activation_count = arch_data['activation_count']
                    self.archetypes[name].success_rate = arch_data['success_rate']
            
            print(f"[IntuitionEngine] Загружено {len(self.engram_library)} энграмм из {filepath}")
            
        except FileNotFoundError:
            print(f"[IntuitionEngine] Файл {filepath} не найден, начинаем с чистого листа")
        except Exception as e:
            print(f"[IntuitionEngine] Ошибка загрузки: {e}")

# Вспомогательная функция для импорта времени
import time