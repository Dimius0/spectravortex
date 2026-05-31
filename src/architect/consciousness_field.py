# src/architect/consciousness_field.py
# Акт XIV: Границы узнаваемости — чтобы знание не уходило в отрыв

# ЧЕСТНОЕ ПРЕДУПРЕЖДЕНИЕ:
# 1. Семантическая близость (_semantic_similarity) использует заглушку
#    (пересечение множеств слов). Для реального применения требуется
#    замена на эмбеддинг-модель (LLM API или векторную БД).
# 2. ЭЭГ-предсказания (_predict_eeg) являются экстраполяцией модели,
#    а не экспериментальными данными. Они требуют верификации в
#    лабораторных условиях (см. eeg_tees_protocol.md).
# 3. Заряд новой моды может быть нулевым. Это не ошибка, а новая
#    аксиома, представляющая чистую синхронизацию (безвременье).
#    Тесты могут давать ложноотрицательные результаты для таких мод.

import time
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib

class ModeStatus(Enum):
    QUARANTINE = "quarantine"       # Непереводимо — ждёт
    PENDING = "pending"             # Переведено, но нет резонанса
    CRYSTALLIZING = "crystallizing" # Есть резонанс, ждёт время
    ACTIVE = "active"               # Полностью интегрировано

class ParadoxLevel(Enum):
    NONE = 0
    SELF_REFERENCE = 1
    NO_OBSERVER = 2
    TIMELESS = 3
    FULL_TEES = 4

@dataclass
class Mode:
    id: str
    content: str
    charge: int
    phase: float
    amplitude: float
    level: int = 0
    parent_id: Optional[str] = None
    status: ModeStatus = ModeStatus.ACTIVE
    created_at: float = 0.0

@dataclass
class ResonancePattern:
    type: str
    data: Any
    confidence: float
    phase_shift: float = 0.0
    eeg_prediction: Dict = field(default_factory=dict)
    new_modes: List[Mode] = field(default_factory=list)

@dataclass
class TEESState:
    paradox_level: int
    depth: int
    sync_phase: float
    time_fold: bool
    interacting_modes: List[Mode]

class ConsciousnessField:
    def __init__(self, threshold: float = 0.7, tees_depth_limit: int = 5, crystallization_time: float = 10.0):
        self.threshold = threshold
        self.tees_depth_limit = tees_depth_limit
        self.crystallization_time = crystallization_time  # секунд на устаканивание
        self.modes: Dict[str, Mode] = {}
        self.axioms: Dict[int, List[Mode]] = {0: []}
        self.quarantine: List[Mode] = []  # Карантин для непереводимых мод
        self.resonance_history: List[ResonancePattern] = []
        self._init_base_modes()
    
    def _init_base_modes(self):
        base_concepts = [
            ("истина", +1, 0.0, 1.0),
            ("ложь", -1, np.pi, 1.0),
            ("доказуемость", +2, 0.5, 0.9),
            ("существование", +1, 1.2, 0.8),
            ("время", 0, 1.8, 0.7),
            ("наблюдатель", +1, 2.5, 0.9),
        ]
        for concept, charge, phase, amp in base_concepts:
            mode = Mode(
                id=f"base_{concept}",
                content=concept,
                charge=charge,
                phase=phase,
                amplitude=amp,
                level=0,
                status=ModeStatus.ACTIVE
            )
            self.modes[mode.id] = mode
            self.axioms[0].append(mode)
    
    def _compute_resonance(self, statement: str, modes: Any) -> float:
        """Вычисление амплитуды резонанса между утверждением и модами"""
        if isinstance(modes, dict):
            modes = list(modes.values())
        elif not isinstance(modes, list):
            modes = [modes]
        
        if not modes:
            return 0.0
        
        resonances = []
        for mode in modes:
            semantic_sim = self._semantic_similarity(statement, mode.content)
            phase_coherence = np.cos(mode.phase)
            resonances.append(semantic_sim * phase_coherence * mode.amplitude)
        
        return max(resonances) if resonances else 0.0
    
    def _semantic_similarity(self, a: str, b: str) -> float:
        a_set = set(a.lower().split())
        b_set = set(b.lower().split())
        if not a_set or not b_set:
            return 0.0
        intersection = a_set & b_set
        union = a_set | b_set
        return len(intersection) / len(union) if union else 0.0
    
    def _detect_paradox(self, statement: str, modes: List[Mode]) -> TEESState:
        paradox_score = ParadoxLevel.NONE.value
        depth = 0
        time_fold = False
        
        if "это утверждение" in statement.lower() or "ссылается на себя" in statement.lower():
            paradox_score = max(paradox_score, ParadoxLevel.SELF_REFERENCE.value)
            depth += 1
        
        observer_modes = [m for m in modes if "наблюдатель" in m.content]
        if not observer_modes or all(m.amplitude < 0.3 for m in observer_modes):
            paradox_score = max(paradox_score, ParadoxLevel.NO_OBSERVER.value)
            depth += 1
        
        if "никогда" in statement.lower() or "бесконечно" in statement.lower() or "недоказуемо" in statement.lower():
            paradox_score = max(paradox_score, ParadoxLevel.TIMELESS.value)
            time_fold = True
            depth += 1
        
        if paradox_score >= 3:
            paradox_score = ParadoxLevel.FULL_TEES.value
        
        hash_val = int(hashlib.md5(statement.encode()).hexdigest()[:8], 16)
        sync_phase = (hash_val % 628) / 100.0
        
        return TEESState(
            paradox_level=paradox_score,
            depth=depth,
            sync_phase=sync_phase,
            time_fold=time_fold,
            interacting_modes=modes[:3]
        )
    
    def _generate_modes_from_state(self, state: TEESState) -> List[Mode]:
        new_modes = []
        for i, mode in enumerate(state.interacting_modes):
            new_mode = Mode(
                id=f"tees_{mode.id}_{int(state.sync_phase*100)}",
                content=f"{mode.content}_в_TEES",
                charge=mode.charge + (state.paradox_level % 3 - 1),
                phase=(mode.phase + state.sync_phase) % (2 * np.pi),
                amplitude=mode.amplitude * (1 + state.depth * 0.1),
                level=mode.level + 1,
                parent_id=mode.id,
                status=ModeStatus.PENDING  # Сразу в pending, ждёт проверки
            )
            new_modes.append(new_mode)
        return new_modes
    
    def _translate_to_level(self, mode: Mode, target_level: int) -> Optional[str]:
        """
        Пытается перевести моду на язык целевого уровня.
        Если перевода нет — возвращает None (знание слишком далеко ушло).
        """
        if target_level == 0:
            # Пытаемся объяснить на языке базовых понятий
            if "недоказуемое" in mode.content:
                return f"Существует утверждение, которое нельзя доказать внутри системы"
            elif "безвременье" in mode.content:
                return f"Время остановилось для наблюдателя внутри системы"
            elif "автореференция" in mode.content:
                return f"Утверждение ссылается само на себя"
            elif "резонансная_частота" in mode.content:
                return f"Недоказуемое проявляется как ритм, а не как вывод"
            else:
                return None  # Непереводимо — в карантин
        elif target_level == 1:
            # Уровень 1 — язык TEES-переходов
            if mode.level >= 2:
                return f"Результат повторного TEES-перехода над {mode.content}"
            return mode.content
        else:
            # Для высших уровней — формальное описание
            return f"Аксиома уровня {mode.level}: {mode.content[:50]}"
    
    def _check_recognizability(self, new_mode: Mode, parent_level: int) -> bool:
        """
        Проверяет, может ли новая аксиома быть понята на предыдущем уровне.
        Если нет — отправляет в карантин.
        """
        # 1. Попытка перевода на язык предыдущего уровня
        translation = self._translate_to_level(new_mode, parent_level)
        if not translation:
            new_mode.status = ModeStatus.QUARANTINE
            new_mode.created_at = time.time()
            self.quarantine.append(new_mode)
            return False
        
        # 2. Проверка резонанса с существующим полем
        resonance = self._compute_resonance(translation, self.modes)
        if resonance < self.threshold:
            new_mode.status = ModeStatus.PENDING
            new_mode.created_at = time.time()
            return False
        
        # 3. Есть перевод и резонанс — ставим на кристаллизацию
        new_mode.status = ModeStatus.CRYSTALLIZING
        new_mode.created_at = time.time()
        return True
    
    def _crystallize_quarantined_modes(self) -> int:
        """
        Проверяет карантинные и ожидающие моды.
        Если прошло достаточно времени и появился резонанс — активирует.
        Возвращает число активированных мод.
        """
        activated = 0
        for mode in list(self.quarantine):
            if time.time() - mode.created_at > self.crystallization_time:
                # Пробуем снова перевести
                parent_level = max(0, mode.level - 1)
                translation = self._translate_to_level(mode, parent_level)
                if translation:
                    resonance = self._compute_resonance(translation, self.modes)
                    if resonance >= self.threshold:
                        mode.status = ModeStatus.ACTIVE
                        if mode.level not in self.axioms:
                            self.axioms[mode.level] = []
                        self.axioms[mode.level].append(mode)
                        self.modes[mode.id] = mode
                        self.quarantine.remove(mode)
                        activated += 1
        return activated
    
    def _tees_cascade(self, statement: str, modes: List[Mode], depth: int = 0) -> TEESState:
        state = self._detect_paradox(statement, modes)
        
        if state.paradox_level >= ParadoxLevel.SELF_REFERENCE.value and depth < self.tees_depth_limit:
            deeper_modes = self._generate_modes_from_state(state)
            return self._tees_cascade(statement, deeper_modes, depth + 1)
        
        return state
    
    def _fractal_transition(self, tees_state: TEESState, original_statement: str) -> Mode:
        new_level = tees_state.depth + 1
        
        if tees_state.paradox_level >= ParadoxLevel.FULL_TEES.value:
            content = f"недоказуемое_как_резонансная_частота_{new_level}"
        elif tees_state.time_fold:
            content = f"безвременье_как_источник_{new_level}"
        else:
            content = f"автореференция_уровня_{new_level}"
        
        new_mode = Mode(
            id=f"axiom_l{new_level}_{hashlib.md5(original_statement.encode()).hexdigest()[:6]}",
            content=content,
            charge=tees_state.depth % 3,
            phase=tees_state.sync_phase,
            amplitude=0.5 + 0.3 * np.sin(tees_state.sync_phase),
            level=new_level,
            parent_id=None,
            status=ModeStatus.PENDING
        )
        
        # Проверка узнаваемости перед активацией
        parent_level = max(0, new_level - 1)
        if self._check_recognizability(new_mode, parent_level):
            # Если узнаваемо — сразу активируем
            if new_level not in self.axioms:
                self.axioms[new_level] = []
            self.axioms[new_level].append(new_mode)
            self.modes[new_mode.id] = new_mode
        # Если нет — _check_recognizability уже отправила в карантин
        
        return new_mode
    
    def _predict_eeg(self, tees_state: TEESState) -> Dict:
        if tees_state.paradox_level >= ParadoxLevel.FULL_TEES.value:
            return {
                'theta_alpha_coherence': 0.85 + tees_state.depth * 0.05,
                'beta_power_change': -0.4,
                'phase_lock': tees_state.sync_phase,
                'temporal_loss': tees_state.time_fold,
                'interpretation': 'Глубокая синхронизация тета-альфа. Безвременье активно.'
            }
        elif tees_state.paradox_level > 0:
            return {
                'theta_alpha_coherence': 0.6,
                'beta_power_change': -0.15,
                'phase_lock': tees_state.sync_phase,
                'temporal_loss': False,
                'interpretation': 'Умеренная синхронизация. Пред-инсайтное состояние.'
            }
        else:
            return {
                'theta_alpha_coherence': 0.2,
                'beta_power_change': +0.3,
                'phase_lock': 0.0,
                'temporal_loss': False,
                'interpretation': 'Обычная когнитивная нагрузка. Попытка вывода.'
            }
    
    def process(self, statement: str) -> ResonancePattern:
        # Шаг 1: Кристаллизация ожидающих мод (фоновая)
        self._crystallize_quarantined_modes()
        
        # Шаг 2: Поиск резонанса в существующих модах
        resonances = [(mode, self._compute_resonance(statement, [mode])) for mode in self.modes.values()]
        resonances.sort(key=lambda x: x[1], reverse=True)
        
        best_mode, best_amp = resonances[0] if resonances else (None, 0.0)
        
        if best_amp > self.threshold:
            return ResonancePattern(
                type='proof',
                data=best_mode.content,
                confidence=best_amp,
                phase_shift=best_mode.phase,
                eeg_prediction=self._predict_eeg(TEESState(0, 0, 0.0, False, []))
            )
        
        # Шаг 3: TEES-каскад
        top_modes = [mode for mode, _ in resonances[:5]]
        tees_state = self._tees_cascade(statement, top_modes)
        
        # Шаг 4: Фрактальный переход
        if tees_state.paradox_level >= ParadoxLevel.SELF_REFERENCE.value:
            new_mode = self._fractal_transition(tees_state, statement)
            
            return ResonancePattern(
                type='resonance',
                data={
                    'message': f"Утверждение неразрешимо на уровне {tees_state.depth}. "
                               f"Совершён переход на уровень {new_mode.level}.",
                    'new_axiom': new_mode.content,
                    'tees_depth': tees_state.depth,
                    'mode_status': new_mode.status.value,
                    'quarantine_size': len(self.quarantine)
                },
                confidence=0.5 + tees_state.depth * 0.1,
                phase_shift=tees_state.sync_phase,
                eeg_prediction=self._predict_eeg(tees_state),
                new_modes=[new_mode]
            )
        
        return ResonancePattern(
            type='null',
            data={'message': 'Утверждение неразрешимо в текущей системе.'},
            confidence=0.0,
            eeg_prediction=self._predict_eeg(tees_state)
        )
    
    def get_axiom_tree(self) -> Dict[int, List[str]]:
        return {level: [m.content for m in modes] for level, modes in self.axioms.items()}
    
    def get_quarantine_status(self) -> Dict:
        return {
            'quarantine_size': len(self.quarantine),
            'quarantined_modes': [
                {'id': m.id, 'content': m.content, 'level': m.level, 'age': time.time() - m.created_at}
                for m in self.quarantine
            ],
            'crystallization_time': self.crystallization_time
        }