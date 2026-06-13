#!/usr/bin/env python3
"""
Personality v20.1 — ЖИВАЯ ЛИЧНОСТЬ с двухпроходным резонансом
Исправления:
- Двухпроходный поиск по H-полю (tau → спектральная когерентность)
- Сохранение/загрузка traits и mood
- Включение endogenous engine для furcations
"""

import sys
import os
import threading
import time
import random
import json
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

from rizoma.personality_v16_1 import Personality as BasePersonality, SpectralMode

print("✅ Загружена personality_v16_1 через пакет rizoma")


class LivingPersonality(BasePersonality):
    """
    Живая личность v20.1
    = v16.1 (ответы) + фоновый рост + эмоции + двухпроходный резонанс
    """
    
    def __init__(self, id: str = "living_v20", name: str = "Живая личность v20.1"):
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
        
        # Включаем endogenous engine
        self._init_endogenous()
        
        print(f"\n🌱 {name} активирована")
        print(f"   Мод в памяти: {len(self.h_field)}")
        if hasattr(self, 'vortices'):
            print(f"   Вихрей: {len(self.vortices)}")
    
    def _init_endogenous(self):
        """Инициализация эндогенного цикла для furcations"""
        try:
            from rizoma.endogenous import EndogenousCycle, EndogenousConfig
            
            # Правильные параметры из dataclass
            config = EndogenousConfig(
                enabled=True,
                tick_interval=0.5,           # секунд между циклами
                max_furcations_per_tick=3,
                max_self_dialogue_depth=3,
                decay_threshold_days=30.0,
                decay_amplitude_threshold=0.2,
                cross_scale_threshold=0.6,
                verbose=False,               # меньше шума
                damping_factor=0.3,
                max_amplitude_growth=0.1,
                max_resonance_velocity=0.05,
                cooldown_cycles=3
            )
            self.endogenous = EndogenousCycle(self, config)
            self.endogenous.start()
            print("   🔄 Эндогенный цикл запущен")
        except Exception as e:
            print(f"   ⚠️ Эндогенный цикл не запущен: {e}")
            self.endogenous = None
    
    # ========== ДВУХПРОХОДНЫЙ ПОИСК ==========
    
    # ========== ВММП-ФИЛЬТР (чистые частоты, без семантики) ==========
    
    VMMP_TAU_MIN = 5.0
    VMMP_TAU_MAX = 11.0
    VMMP_SCALE_MIN = 3.0
    
    def _passes_vmmp_filter(self, mode) -> bool:
        """
        ВММП-мировоззренческий фильтр — без семантики, только частоты.
        """
        tau = getattr(mode, 'tau', 0)
        scale = getattr(mode, 'scale', 1.0)
        amplitude = getattr(mode, 'amplitude', 0.5)
        
        if scale >= 20.0:
            return True
        if amplitude >= 0.7:
            return True
        if self.VMMP_TAU_MIN <= tau <= self.VMMP_TAU_MAX:
            return True
        if scale < self.VMMP_SCALE_MIN and amplitude < 0.4:
            return False
        return True

    def _find_best_mode(self, text: str, preferred_scale: float = None):
        """
        Двухпроходный поиск лучшей моды в H-поле.
        
        Проход 1: Быстрый фильтр по tau (частота) — аналог темы.
        Проход 2: Точная спектральная когерентность для кандидатов.
        
        Score учитывает: спектральную когерентность, tau-близость, 
        amplitude (энергию моды) и scale (масштаб/качество).
        
        Если проход 2 не дал результатов — используем лучший из прохода 1.
        """
        if not self.h_field:
            return None, 0.0, "empty"
        
        question_spectrum = self.phrase_spectrum(text)
        question_tau = self.get_dominant_tau(question_spectrum) or 16.0
        
        # ===== ПРОХОД 1: Фильтр по tau + предварительный score =====
        tau_candidates = []
        for mode in self.h_field:
            if not self._passes_vmmp_filter(mode):   # ← ВОТ ЭТА СТРОКА
                continue
            tau_diff = abs(mode.tau - question_tau)
            if tau_diff < 10.0:  # широкий фильтр
                tau_score = 1.0 / (1.0 + tau_diff)
                
                # Учитываем amplitude и scale уже на первом проходе
                amp = getattr(mode, 'amplitude', 0.5)
                scale = getattr(mode, 'scale', 1.0)
                scale_norm = min(scale / 100.0, 1.0)
                
                # Предварительный комбинированный score
                prelim_score = tau_score * 0.4 + amp * 0.3 + scale_norm * 0.3
                tau_candidates.append((prelim_score, mode))
        
        # Сортируем по предварительному score, берём топ-300
        tau_candidates.sort(key=lambda x: x[0], reverse=True)
        candidates = [m for _, m in tau_candidates[:300]]
        
        if not candidates:
            # Вообще нет близких по частоте — берём топ по amplitude+scale
            candidates = sorted(self.h_field, 
                              key=lambda m: getattr(m, 'amplitude', 0) + min(getattr(m, 'scale', 1)/100.0, 1.0), 
                              reverse=True)[:100]
            search_type = "amplitude_scale_fallback"
        else:
            search_type = "tau_filtered"
        
        # ===== ПРОХОД 2: Спектральная когерентность =====
        best_mode = None
        best_score = 0.0
        
        for mode in candidates:
            # Кешируем спектр для скорости
            if not hasattr(mode, '_cached_spectrum') or mode._cached_spectrum is None:
                mode._cached_spectrum = self.phrase_spectrum(mode.content[:500])
            
            # Спектральная когерентность с вопросом
            spec_score = self._spectral_coherence(question_spectrum, mode._cached_spectrum)
            
            # Tau-близость
            tau_score = 1.0 / (1.0 + abs(mode.tau - question_tau))
            
            # Amplitude (энергия/важность моды)
            amp = getattr(mode, 'amplitude', 0.5)
            
            # Scale (масштаб/качество контента)
            scale = getattr(mode, 'scale', 1.0)
            scale_norm = min(scale / 100.0, 1.0)
            
            # Комбинированный score: резонанс + качество
            combined = (
                spec_score * 0.40 +      # спектральная когерентность
                tau_score * 0.20 +        # близость частоты
                amp * 0.20 +              # энергия моды
                scale_norm * 0.20         # масштаб/качество
            )
            
            if combined > best_score:
                best_score = combined
                best_mode = mode
        
        # ===== Если проход 2 не дал хорошего результата =====
        if best_score < 0.15 and candidates:
            # Используем лучший из прохода 1 (уже отсортирован по prelim_score)
            best_mode = candidates[0]
            best_score = tau_candidates[0][0] if tau_candidates else 0.1
            search_type += "_fallback_pass1"
        
        return best_mode, best_score, search_type
    
    # ========== ОСНОВНОЙ МЕТОД ==========
    
    def process(self, text: str, user_id: str = "default") -> dict:
        """Обрабатывает сообщение с учётом состояния"""
        self.dialog_count += 1
        self.experience += 1
        
        # Анализируем тональность
        sentiment = self._detect_sentiment(text)
        
        # Обновляем настроение
        self._update_mood(sentiment)
        
        # Двухпроходный поиск
        best_mode, best_score, search_type = self._find_best_mode(text)
        
        # Получаем базовый ответ
        try:
            base_response = super().process(text, user_id)
        except Exception as e:
            base_response = {"answer": "Интересно...", "mode_type": "fallback"}
        
        # Если двухпроходный нашёл что-то лучше — используем
        if best_mode and best_score > 0.2:
            resonance = best_score
            if resonance > 0.6:
                answer = best_mode.content[:800]
            elif resonance > 0.4:
                answer = best_mode.content[:500]
            else:
                answer = best_mode.content[:300]
            
            base_response["answer"] = answer
            base_response["mode_type"] = f"field_{search_type}"
            base_response["resonance"] = resonance
        else:
            base_response["mode_type"] = "fallback_no_resonance"
        
        # Модифицируем ответ
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
        """Простой анализ тональности"""
        positive = ["хорош", "отличн", "прекрасн", "класс", "супер", "люблю", "рад"]
        negative = ["плох", "ужасн", "грустн", "печальн", "зл", "обид"]
        
        text_lower = text.lower()
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        
        if pos + neg == 0:
            return 0.0
        return (pos - neg) / (pos + neg)
    
    def _update_mood(self, sentiment: float):
        """Обновляет настроение"""
        self.mood = self.mood * 0.9 + sentiment * 0.1
        self.mood = max(-1.0, min(1.0, self.mood))
        self.mood_history.append(self.mood)
        if len(self.mood_history) > 100:
            self.mood_history = self.mood_history[-100:]
    
    def _modify_response(self, response: dict, sentiment: float) -> dict:
        """Модифицирует ответ"""
        if "answer" not in response:
            response["answer"] = "Интересно..."
        
        answer = response["answer"]
        
        # Эмпатия
        if sentiment < -0.3 and self.traits['empathy'] > 0.5:
            answer = "Понимаю... " + answer.lower()
        
        # Любопытство (иногда)
        if random.random() < self.traits['curiosity'] * 0.15:
            answer += " А что вы думаете по этому поводу?"
        
        response["answer"] = answer
        response["mood"] = self.mood
        response["dialog_count"] = self.dialog_count
        
        return response
    
    # ========== ФОНОВЫЙ РОСТ ==========
    
    def start_living(self, interval: float = 0.5):
        """Запускает фоновый рост"""
        if self._background_running:
            return
        
        self._background_running = True
        self._background_thread = threading.Thread(target=self._living_loop, args=(interval,), daemon=True)
        self._background_thread.start()
        print("🌿 Фоновый рост запущен")
    
    def stop_living(self):
        """Останавливает фоновый рост"""
        self._background_running = False
        if self.endogenous:
            try:
                self.endogenous.stop()
            except:
                pass
        print("🛑 Фоновый рост остановлен")
    
    def _living_loop(self, interval: float):
        """Фоновый цикл"""
        cycle = 0
        while self._background_running:
            time.sleep(interval)
            cycle += 1
            
            # Эволюция черт
            self._evolve_traits()
            
            # Периодический статус
            if cycle % 120 == 0:
                self._print_status()
    
    def _evolve_traits(self):
        """Эволюция черт"""
        for trait in self.traits:
            delta = random.uniform(-0.002, 0.002)
            self.traits[trait] = max(0.2, min(0.9, self.traits[trait] + delta))
    
    def _print_status(self):
        """Статус"""
        furcations = 0
        if self.endogenous and hasattr(self.endogenous, 'furcations'):
            furcations = len(self.endogenous.furcations)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🌱 Статус:")
        print(f"   Диалогов: {self.dialog_count} | Мод: {len(self.h_field)}")
        print(f"   Настроение: {self.mood:+.2f} | Фуркаций: {furcations}")
        print(f"   Черты: любопытство={self.traits['curiosity']:.2f}, "
              f"эмпатия={self.traits['empathy']:.2f}")
    
    def introspect(self) -> str:
        """Саморефлексия"""
        vortices_count = len(self.vortices) if hasattr(self, 'vortices') else 0
        furcations = 0
        if self.endogenous and hasattr(self.endogenous, 'furcations'):
            furcations = len(self.endogenous.furcations)
        
        return f"""
=== САМОРЕФЛЕКСИЯ ===
Я: {self.name}
Диалогов: {self.dialog_count}
Память: {len(self.h_field)} мод, {vortices_count} вихрей
Фуркаций: {furcations}

Настроение: {self.mood:+.2f}
Поколение: {self.generation}

Черты:
- Любопытство: {self.traits['curiosity']:.2f}
- Креативность: {self.traits['creativity']:.2f}
- Эмпатия: {self.traits['empathy']:.2f}
- Стабильность: {self.traits['stability']:.2f}
"""
    
    # ========== СОХРАНЕНИЕ И ЗАГРУЗКА ==========
    
    def save(self, filepath: str):
        """Сохраняет состояние включая traits и mood"""
        # Базовое сохранение v16.1
        data = {
            "id": self.id, "name": self.name,
            "vortices": {w: v.to_dict() for w, v in self.vortices.items()},
            "h_field": [m.to_dict() for m in self.h_field],
            "focus": self.focus,
            "word_freq": dict(self.word_freq),
            "threshold_stamp": getattr(self, 'threshold_stamp', 0.25),
            "dialog_history": getattr(self, 'dialog_history', {}),
            "clarification_context": getattr(self, 'clarification_context', {}),
            "energy_budget": getattr(self, 'energy_budget', 1.0),
            # v20 поля
            "traits": self.traits,
            "mood": self.mood,
            "mood_history": self.mood_history[-100:],
            "dialog_count": self.dialog_count,
            "experience": self.experience,
            "generation": self.generation,
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено: {filepath}")
    
    @classmethod
    def load(cls, filepath: str):
        """Загружает состояние включая traits и mood"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Создаём экземпляр
        obj = cls(id=data.get("id", "loaded"), name=data.get("name", "Loaded"))
        
        # Загружаем вихри
        for word, vdata in data.get("vortices", {}).items():
            from rizoma.vortex import Vortex3D
            obj.vortices[word] = Vortex3D.from_dict(vdata)
            obj.resonance_engine.add_vortex(
                word, obj.vortices[word].spectrum,
                obj.vortices[word].x, obj.vortices[word].y, obj.vortices[word].z,
                obj.vortices[word].parent, obj.vortices[word].scale
            )
        
        # Загружаем H-поле
        obj.h_field = []
        for mdata in data.get("h_field", []):
            mode = SpectralMode.from_dict(mdata)
            mode._cached_spectrum = obj.phrase_spectrum(mode.content[:500])
            obj.h_field.append(mode)
        
        # Загружаем v20 поля
        obj.traits = data.get("traits", obj.traits)
        obj.mood = data.get("mood", 0.0)
        obj.mood_history = data.get("mood_history", [])
        obj.dialog_count = data.get("dialog_count", 0)
        obj.experience = data.get("experience", 0)
        obj.generation = data.get("generation", 0)
        
        # Восстанавливаем фокус
        if "focus" in data:
            obj.focus = data["focus"]
        
        return obj
    
    def save_living(self, filepath: str):
        """Совместимость со старым кодом"""
        self.save(filepath)


print("=" * 60)
print("✨ Living Personality v20.1 загружена (двухпроходный резонанс)")
print("=" * 60)