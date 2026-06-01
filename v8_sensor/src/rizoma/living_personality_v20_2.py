#!/usr/bin/env python3
"""
Living Personality v20.2 — с ВММП-фильтром (холистическая структура знаний)

Принцип фильтра:
    Знание имеет право на существование в поле, только если оно связано
    с общим полем через общие принципы (∇⁴ψ = 0, TEES, τ-заряды).
    Моды вне ВММП-диапазона (tau 5–11) требуют доказательств важности:
    scale ≥ 10 И amplitude ≥ 0.6.

Новое в v20.2:
    - _passes_vmmp_filter(): структурный фильтр связности
    - Двухпроходный поиск с ВММП-фильтром
    - Холистический принцип: не отсекаем шум, а требуем связности
"""

import sys
import os
import threading
import time
import random
import json
import math
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, OrderedDict
from datetime import datetime

# Добавляем родительскую директорию rizoma в путь
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

# Импортируем из пакета rizoma
from rizoma.personality_v16_1 import Personality as BasePersonality, SpectralMode

print("✅ Загружена personality_v16_1 через пакет rizoma")


class LivingPersonality(BasePersonality):
    """
    Живая личность v20.2 — с ВММП-фильтром (холистическая структура знаний)
    = v16.1 (ответы) + фоновый рост + эмоции + ВММП-фильтр
    """
    
    # ═══════════════════════════════════════════════════════════════════
    #   ВММП-ФИЛЬТР: холистическая структура знаний
    # ═══════════════════════════════════════════════════════════════════
    
    VMMP_TAU_MIN: float = 5.0
    VMMP_TAU_MAX: float = 11.0
    
    def _passes_vmmp_filter(self, mode) -> bool:
        """
        Проверяет, проходит ли мода ВММП-фильтр.
        
        Принцип: мода имеет право на существование в поле, только если она
        связана с общим полем через общие принципы. Моды вне ВММП-диапазона
        (tau 5–11) требуют доказательств важности.
        """
        tau = getattr(mode, 'tau', 0)
        scale = getattr(mode, 'scale', 1.0)
        amplitude = getattr(mode, 'amplitude', 0.5)
        
        # Высокий scale — доверяем полю (целые тексты)
        if scale >= 20.0:
            return True
        
        # Высокая amplitude — эндогенно важная
        if amplitude >= 0.7:
            return True
        
        # В ВММП-диапазоне — проходит
        if self.VMMP_TAU_MIN <= tau <= self.VMMP_TAU_MAX:
            return True
        
        # Вне ВММП-диапазона: только если scale высокий И amplitude высокая
        if tau < self.VMMP_TAU_MIN or tau > self.VMMP_TAU_MAX:
            if scale >= 10.0 and amplitude >= 0.6:
                return True
            return False  # ← ВСЁ ОСТАЛЬНОЕ ВНЕ ДИАПАЗОНА — ШУМ
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════
    #   ДВУХПРОХОДНЫЙ ПОИСК С ВММП-ФИЛЬТРОМ
    # ═══════════════════════════════════════════════════════════════════
    
    def _find_best_mode(self, text: str, preferred_scale: float = None) -> Tuple[Any, float, str]:
        """
        Двухпроходный поиск лучшей моды в H-поле с ВММП-фильтром.
        
        Проход 1: фильтр по tau + предварительный score.
        Проход 2: полный резонанс с phase_coherence.
        
        Returns:
            (mode, score, source) — лучшая мода, её score и источник.
        """
        if not self.h_field:
            return None, 0.0, "empty"
        
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        question_complexity = self._detect_complexity(text)
        
        self.focus["tau"] = self.focus["tau"] * 0.7 + question_tau * 0.3
        
        # ===== ПРОХОД 1: Фильтр по tau + предварительный score =====
        tau_candidates = []
        for mode in self.h_field:
            if not self._passes_vmmp_filter(mode):
                continue
            
            tau_diff = abs(mode.tau - question_tau)
            if tau_diff < 10.0:
                # Быстрый score: только tau-близость + scale_factor
                scale_factor = 1.0
                if preferred_scale is not None:
                    log_ratio = abs(math.log(max(mode.scale, 0.1) / max(preferred_scale, 0.1)))
                    scale_factor = 1.0 / (1.0 + log_ratio)
                
                prelim_score = (1.0 / (1.0 + tau_diff)) * 0.6 + scale_factor * 0.4
                
                if prelim_score > 0.05:
                    tau_candidates.append((mode, prelim_score))
        
        # Сортируем, берём топ-200
        tau_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = tau_candidates[:200]
        
        if not top_candidates:
            return None, 0.0, "no_tau_match"
        
        # ===== ПРОХОД 2: Полный резонанс с phase_coherence =====
        best_mode = None
        best_score = 0.0
        
        for mode, prelim_score in top_candidates:
            if not hasattr(mode, '_cached_spectrum') or mode._cached_spectrum is None:
                mode._cached_spectrum = self.phrase_spectrum(mode.content[:500])
            
            spec_res = self._spectral_coherence(question_spectrum, mode._cached_spectrum)
            phase_res = self._phase_coherence(question_spectrum, mode._cached_spectrum)
            
            complexity_factor = 1.0 / (1.0 + abs(mode.complexity - question_complexity))
            
            score = (
                spec_res * 0.35 +
                phase_res * 0.25 +
                prelim_score * 0.25 +
                complexity_factor * 0.15
            )
            
            if score > best_score:
                best_score = score
                best_mode = mode
        
        if best_mode and best_score > 0.0:
            return best_mode, best_score, "tau_filtered"
        
        return None, 0.0, "no_resonance"
    
    def _detect_complexity(self, text: str) -> int:
        """Определение сложности текста."""
        if len(text) < 30:
            return 1
        if any(word in text.lower() for word in ['tees', 'vmmp', 'τ', '∇', 'бигармонический']):
            return 3
        if any(word in text.lower() for word in ['анализ', 'структура', 'принцип', 'модель']):
            return 2
        return 1
    
    # ═══════════════════════════════════════════════════════════════════
    #   КОНСТРУКТОР
    # ═══════════════════════════════════════════════════════════════════
    
    def __init__(self, id: str = "living_v20_2", name: str = "Живая личность v20.2"):
        super().__init__(id=id, name=name)
        
        # Дополнительные поля
        self.mood = 0.0
        self.energy = 1.0
        self.experience = 0
        self.generation = 0
        
        # Черты характера
        self.traits = {
            'curiosity': 0.7,
            'creativity': 0.5,
            'empathy': 0.6,
            'stability': 0.8
        }
        
        self.mood_history = []
        self.dialog_count = 0
        
        # Фоновый поток
        self._background_running = False
        self._background_thread = None
        
        print(f"\n🌱 {name} активирована")
        print(f"   Мод в памяти: {len(self.h_field)}")
        if hasattr(self, 'vortices'):
            print(f"   Вихрей: {len(self.vortices)}")
    
    # ═══════════════════════════════════════════════════════════════════
    #   ОБРАБОТКА СООБЩЕНИЙ
    # ═══════════════════════════════════════════════════════════════════
    
    def process(self, text: str, user_id: str = "default") -> dict:
        """Обрабатывает сообщение с учётом состояния и ВММП-фильтра."""
        self.dialog_count += 1
        self.experience += 1
        
        sentiment = self._detect_sentiment(text)
        self._update_mood(sentiment)
        
        # Двухпроходный поиск с ВММП-фильтром
        best_mode, best_score, source = self._find_best_mode(text)
        
        if best_mode and best_score > 0.15:
            # Нашли релевантную моду — используем её
            answer = best_mode.content[:800]
            mode_type = source
            
            # ЭЭГ-предсказание
            if best_score > 0.6:
                eeg = "Глубокая синхронизация тета-альфа. Безвременье активно."
            elif best_score > 0.4:
                eeg = "Умеренная синхронизация. Пред-инсайтное состояние."
            else:
                eeg = "Обычная когнитивная нагрузка. Попытка вывода."
            
            response = {
                "answer": answer,
                "mode_used": best_mode.trace_id[:16] if hasattr(best_mode, 'trace_id') else '?',
                "mode_type": mode_type,
                "resonance": best_score,
                "eeg_prediction": eeg,
                "energy_cost": 0.1,
                "is_stamp": False,
                "mood": self.mood,
                "dialog_count": self.dialog_count,
            }
        else:
            # Пробуем базовый ответ от v16.1
            try:
                base_response = super().process(text, user_id)
            except Exception:
                base_response = {"answer": "Интересно...", "mode_type": "fallback"}
            
            response = self._modify_response(base_response, sentiment)
        
        # Сохраняем историю
        if not hasattr(self, 'dialog_history'):
            self.dialog_history = {}
        if user_id not in self.dialog_history:
            self.dialog_history[user_id] = []
        self.dialog_history[user_id].append({
            "question": text,
            "answer": response.get("answer", ""),
            "sentiment": sentiment,
            "mood": self.mood,
            "timestamp": time.time()
        })
        
        return response
    
    def _detect_sentiment(self, text: str) -> float:
        """Простой анализ тональности."""
        positive = ["хорош", "отличн", "прекрасн", "класс", "супер", "люблю", "нравит", "рад"]
        negative = ["плох", "ужасн", "ненавиж", "грустн", "печальн", "зл", "обид"]
        
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        
        if pos + neg == 0:
            return 0.0
        return (pos - neg) / (pos + neg)
    
    def _update_mood(self, sentiment: float):
        """Обновляет настроение."""
        self.mood = self.mood * 0.9 + sentiment * 0.1
        self.mood = max(-1.0, min(1.0, self.mood))
        
        self.mood_history.append(self.mood)
        if len(self.mood_history) > 100:
            self.mood_history = self.mood_history[-100:]
    
    def _modify_response(self, response: dict, sentiment: float) -> dict:
        """Модифицирует ответ."""
        if "answer" not in response:
            response["answer"] = "Интересно..."
        
        answer = response["answer"]
        
        if sentiment < -0.3 and self.traits['empathy'] > 0.5:
            answer = "Понимаю... " + answer.lower()
        
        if random.random() < self.traits['curiosity'] * 0.15:
            answer += " А что вы думаете по этому поводу?"
        
        response["answer"] = answer
        response["mood"] = self.mood
        response["dialog_count"] = self.dialog_count
        
        return response
    
    # ═══════════════════════════════════════════════════════════════════
    #   ФОНОВЫЙ РОСТ
    # ═══════════════════════════════════════════════════════════════════
    
    def start_living(self, interval: float = 0.5):
        """Запускает фоновый рост."""
        if self._background_running:
            return
        
        self._background_running = True
        self._background_thread = threading.Thread(target=self._living_loop, args=(interval,), daemon=True)
        self._background_thread.start()
        print("🌿 Фоновый рост запущен")
    
    def stop_living(self):
        """Останавливает фоновый рост."""
        self._background_running = False
        print("🛑 Фоновый рост остановлен")
    
    def _living_loop(self, interval: float):
        """Фоновый цикл."""
        cycle = 0
        while self._background_running:
            time.sleep(interval)
            cycle += 1
            self._evolve_traits()
            if cycle % 120 == 0:
                self._print_status()
    
    def _evolve_traits(self):
        """Эволюция черт."""
        for trait in self.traits:
            delta = random.uniform(-0.002, 0.002)
            self.traits[trait] = max(0.2, min(0.9, self.traits[trait] + delta))
    
    def _print_status(self):
        """Статус."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🌱 Статус:")
        print(f"   Диалогов: {self.dialog_count} | Мод: {len(self.h_field)}")
        print(f"   Настроение: {self.mood:+.2f}")
        print(f"   Черты: любопытство={self.traits['curiosity']:.2f}, "
              f"эмпатия={self.traits['empathy']:.2f}")
    
    def introspect(self) -> str:
        """Саморефлексия."""
        vortices_count = len(self.vortices) if hasattr(self, 'vortices') else 0
        return f"""
=== САМОРЕФЛЕКСИЯ ===
Я: {self.name}
Диалогов: {self.dialog_count}
Память: {len(self.h_field)} мод, {vortices_count} вихрей

Настроение: {self.mood:+.2f}
Поколение: {self.generation}

Черты:
- Любопытство: {self.traits['curiosity']:.2f}
- Креативность: {self.traits['creativity']:.2f}
- Эмпатия: {self.traits['empathy']:.2f}
- Стабильность: {self.traits['stability']:.2f}

ВММП-фильтр: tau∈[{self.VMMP_TAU_MIN}, {self.VMMP_TAU_MAX}]
"""
    
    def save(self, filepath: str):
        """Сохраняет состояние живой личности."""
        super().save(filepath)
        print(f"💾 Сохранено: {filepath}")


print("=" * 60)
print("✨ Living Personality v20.2 загружена (ВММП-фильтр, холистическая структура)")
print("=" * 60)