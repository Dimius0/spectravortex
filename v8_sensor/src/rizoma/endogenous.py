# src/rizoma/endogenous.py
"""
Эндогенный цикл — поле живёт своей жизнью
Версия 1.1 — с демпфированием и защитой от автоколебаний
"""
import time
import threading
import random
import math
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from collections import deque


@dataclass
class EndogenousConfig:
    """Конфигурация эндогенного цикла"""
    enabled: bool = True
    tick_interval: float = 60.0  # секунд между циклами
    max_furcations_per_tick: int = 3
    max_self_dialogue_depth: int = 3
    decay_threshold_days: float = 30.0
    decay_amplitude_threshold: float = 0.2
    cross_scale_threshold: float = 0.6
    verbose: bool = True
    
    # Защита от автоколебаний
    damping_factor: float = 0.3        # сила демпфирования
    max_amplitude_growth: float = 0.1  # макс. рост амплитуды за цикл
    max_resonance_velocity: float = 0.05  # макс. скорость роста резонанса
    cooldown_cycles: int = 3           # сколько циклов отдыхать после перегрева
    max_soliton_energy: float = 2.0    # макс. энергия солитона


class DampedBuffer:
    """Буфер с демпфированием — гасит резкие колебания"""
    
    def __init__(self, size: int = 5, damping: float = 0.3):
        self.size = size
        self.damping = damping
        self.history: deque = deque(maxlen=size)
        self.last_value: float = 0.0
    
    def push(self, value: float) -> float:
        self.history.append(value)
        self.last_value = value
        return self.get_smoothed()
    
    def get_smoothed(self) -> float:
        if not self.history:
            return 0.0
        
        # Взвешенное среднее с затуханием
        weight = 1.0
        total = 0.0
        weight_sum = 0.0
        
        for val in reversed(self.history):
            total += val * weight
            weight_sum += weight
            weight *= self.damping
        
        smoothed = total / weight_sum if weight_sum > 0 else 0.0
        
        # Ограничиваем скорость изменения
        delta = smoothed - self.last_value
        if abs(delta) > 0.1:
            smoothed = self.last_value + 0.1 * (1 if delta > 0 else -1)
        
        return max(0.0, min(1.0, smoothed))
    
    def trend(self) -> float:
        """Тренд: положительный = рост, отрицательный = спад"""
        if len(self.history) < 2:
            return 0.0
        return self.history[-1] - self.history[0]


class EndogenousCycle:
    """
    Эндогенный цикл — внутренняя жизнь поля.
    С демпфированием и защитой от автоколебаний.
    """
    
    def __init__(self, field, config: Optional[EndogenousConfig] = None):
        self.field = field
        self.config = config or EndogenousConfig()
        self.cycle_count = 0
        self.running = False
        self.thread = None
        self._lock = threading.Lock()
        
        # Буферы для демпфирования
        self.resonance_buffer = DampedBuffer(size=5, damping=self.config.damping_factor)
        self.amplitude_buffer = DampedBuffer(size=3, damping=0.5)
        
        # Состояние защиты
        self.overheated = False
        self.cooldown_remaining = 0
        self.last_resonance = 0.0
        self.last_amplitudes: deque = deque(maxlen=10)
        
        # Статистика
        self.stats = {
            "furcations": 0,
            "cross_resonances": 0,
            "decayed": 0,
            "knots_created": 0,
            "overheat_events": 0,
            "damping_applied": 0,
            "errors": 0
        }
    
    def start(self):
        """Запускает эндогенный цикл в отдельном потоке"""
        if not self.config.enabled:
            print("🌱 Эндогенный цикл отключён")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"🌱 Эндогенный цикл запущен (интервал: {self.config.tick_interval} сек, демпфирование: {self.config.damping_factor})")
    
    def stop(self):
        """Останавливает цикл"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🌱 Эндогенный цикл остановлен")
    
    def _run(self):
        """Основной цикл"""
        while self.running:
            try:
                time.sleep(self.config.tick_interval)
                self._tick()
            except Exception as e:
                self.stats["errors"] += 1
                if self.config.verbose:
                    print(f"⚠️ Ошибка в эндогенном цикле: {e}")
    
    def _check_overheat(self) -> bool:
        """Проверяет, не перегрелось ли поле"""
        # Проверяем амплитуды мод
        if not self.field.h_field:
            return False
        
        amplitudes = [m.amplitude for m in self.field.h_field[:100]]
        avg_amplitude = sum(amplitudes) / len(amplitudes) if amplitudes else 0
        max_amplitude = max(amplitudes) if amplitudes else 0
        
        # Запоминаем историю
        self.last_amplitudes.append(avg_amplitude)
        
        # Проверяем скорость роста
        if len(self.last_amplitudes) >= 3:
            recent = list(self.last_amplitudes)[-3:]
            growth = recent[-1] - recent[0]
            if growth > self.config.max_amplitude_growth:
                self.stats["overheat_events"] += 1
                if self.config.verbose:
                    print(f"⚠️ Обнаружен перегрев: рост амплитуды {growth:.3f} > {self.config.max_amplitude_growth}")
                return True
        
        # Проверяем максимальную амплитуду
        if max_amplitude > 0.95:
            self.stats["overheat_events"] += 1
            return True
        
        return False
    
    def _apply_damping(self):
        """Применяет демпфирование к полю"""
        self.stats["damping_applied"] += 1
        
        # Снижаем амплитуды мод
        for mode in self.field.h_field:
            mode.amplitude *= (1 - self.config.damping_factor * 0.1)
            mode.amplitude = max(0.1, mode.amplitude)
        
        # Снижаем энергию солитонов
        if hasattr(self.field.resonance_engine, 'nonlinear'):
            for soliton in self.field.resonance_engine.nonlinear.solitons.values():
                soliton.energy *= (1 - self.config.damping_factor * 0.2)
                soliton.energy = max(0.1, soliton.energy)
        
        if self.config.verbose:
            print(f"   🛡️ Демпфирование применено (фактор: {self.config.damping_factor})")
    
    def _tick(self):
        """Один такт внутренней жизни поля с защитой"""
        with self._lock:
            self.cycle_count += 1
            
            # Проверка на перегрев
            if self._check_overheat():
                self.overheated = True
                self.cooldown_remaining = self.config.cooldown_cycles
                self._apply_damping()
                return
            
            # Обработка охлаждения
            if self.overheated:
                self.cooldown_remaining -= 1
                if self.cooldown_remaining <= 0:
                    self.overheated = False
                    if self.config.verbose:
                        print("🌡️ Поле остыло, возобновляем нормальную работу")
                else:
                    if self.config.verbose:
                        print(f"🌡️ Охлаждение: осталось {self.cooldown_remaining} циклов")
                    return
            
            if self.config.verbose:
                print(f"\n🌱 Эндогенный цикл #{self.cycle_count}")
            
            # 1. Спонтанные фуркации (с ограничением)
            self._spontaneous_furcations()
            
            # 2. Кросс-масштабный резонанс (с демпфированием)
            self._cross_scale_resonance()
            
            # 3. Самоорганизация солитонов (с ограничением энергии)
            self._self_organize()
            
            # 4. Забывание старых мод
            self._decay_old_modes()
            
            # 5. Самодиалог (редко, с защитой)
            if not self.overheated and random.random() < 0.2:
                self._self_dialogue()
            
            if self.config.verbose:
                self._print_stats()
    
    def _spontaneous_furcations(self):
        """Спонтанное рождение новых мод (с ограничением)"""
        if not self.field.h_field or self.overheated:
            return
        
        # Находим топ-20 мод по амплитуде
        top_modes = sorted(self.field.h_field, key=lambda m: m.amplitude, reverse=True)[:20]
        
        furcations = 0
        for mode in top_modes:
            if furcations >= self.config.max_furcations_per_tick:
                break
            
            # Шанс фуркации зависит от амплитуды, но не более 0.3
            furcation_prob = min(0.3, mode.amplitude * 0.1)
            if random.random() > furcation_prob:
                continue
            
            # Ищем родительскую моду
            parent = self._find_parent_for_furcation(mode)
            if not parent:
                continue
            
            # Создаём новую моду с пониженной амплитудой
            from .personality import SpectralMode
            new_mode = SpectralMode(
                tau=(mode.tau + parent.tau) / 2,
                amplitude=0.2,  # начинаем с малой амплитуды
                content=self._generate_furcation_content(mode, parent)[:500],
                scale=mode.scale,
                trace_type="spontaneous_furcation",
                parent_id=mode.trace_id,
                themes=mode.themes + parent.themes
            )
            
            self.field.add_to_h_field(new_mode)
            furcations += 1
            
            if self.config.verbose:
                print(f"   ✨ Спонтанная фуркация: {new_mode.content[:50]}...")
        
        self.stats["furcations"] += furcations
    
    def _find_parent_for_furcation(self, mode) -> Optional[Any]:
        """Ищет родительскую моду для фуркации"""
        if not self.field.h_field:
            return None
        
        candidates = []
        for other in self.field.h_field:
            if other.trace_id == mode.trace_id:
                continue
            
            tau_diff = abs(other.tau - mode.tau)
            if tau_diff > 5:
                continue
            
            scale_ratio = max(other.scale, mode.scale) / min(other.scale, mode.scale)
            if scale_ratio > 10:
                continue
            
            score = (other.amplitude + mode.amplitude) / (1 + tau_diff)
            candidates.append((score, other))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    def _generate_furcation_content(self, mode, parent) -> str:
        """Генерирует контент для новой моды"""
        mode_content = mode.content[:100] if mode.content else ""
        parent_content = parent.content[:100] if parent.content else ""
        
        if mode_content and parent_content:
            return f"Связь: {mode_content[:50]} ... {parent_content[:50]}"
        elif mode_content:
            return f"Развитие: {mode_content[:80]}"
        elif parent_content:
            return f"Вариация: {parent_content[:80]}"
        return f"Новая мода на масштабе {mode.scale}"
    
    def _cross_scale_resonance(self):
        """Взаимодействие между модами разных масштабов (с демпфированием)"""
        if len(self.field.h_field) < 10 or self.overheated:
            return
        
        modes_by_scale = {}
        for mode in self.field.h_field:
            scale_key = round(mode.scale, 1)
            if scale_key not in modes_by_scale:
                modes_by_scale[scale_key] = []
            modes_by_scale[scale_key].append(mode)
        
        scales = list(modes_by_scale.keys())
        if len(scales) < 2:
            return
        
        cross_count = 0
        for _ in range(min(5, len(scales) * 2)):
            s1 = random.choice(scales)
            s2 = random.choice([s for s in scales if s != s1])
            if not modes_by_scale[s1] or not modes_by_scale[s2]:
                continue
            
            mode1 = random.choice(modes_by_scale[s1])
            mode2 = random.choice(modes_by_scale[s2])
            
            res = self._resonance_between_modes(mode1, mode2)
            res = self.resonance_buffer.push(res)  # демпфируем
            
            if res > self.config.cross_scale_threshold:
                cross_count += 1
                # Усиление с ограничением
                delta = 0.05 * (1 - self.config.damping_factor)
                mode1.amplitude = min(1.0, mode1.amplitude + delta)
                mode2.amplitude = min(1.0, mode2.amplitude + delta)
        
        self.stats["cross_resonances"] += cross_count
        if cross_count > 0 and self.config.verbose:
            print(f"   🌀 Кросс-масштабный резонанс: {cross_count} связей")
    
    def _resonance_between_modes(self, mode1, mode2) -> float:
        """Вычисляет резонанс между двумя модами"""
        tau_res = 1.0 / (1.0 + abs(mode1.tau - mode2.tau))
        
        if hasattr(mode1, 'scale') and hasattr(mode2, 'scale'):
            log_ratio = abs(math.log(mode1.scale / mode2.scale))
            scale_factor = 1.0 / (1.0 + log_ratio)
        else:
            scale_factor = 1.0
        
        return tau_res * 0.6 + scale_factor * 0.4
    
    def _self_organize(self):
        """Самоорганизация — формирование кластеров (с ограничением)"""
        if len(self.field.h_field) < 50 or self.overheated:
            return
        
        clusters = []
        used = set()
        
        for i, mode in enumerate(self.field.h_field[:100]):
            if i in used:
                continue
            
            cluster = [mode]
            used.add(i)
            
            for j, other in enumerate(self.field.h_field[:100]):
                if j in used:
                    continue
                
                tau_close = abs(mode.tau - other.tau) < 3
                scale_close = abs(math.log(mode.scale / other.scale)) < 1
                
                if tau_close and scale_close:
                    cluster.append(other)
                    used.add(j)
            
            if len(cluster) > 2:
                clusters.append(cluster)
        
        knots_created = 0
        for cluster in clusters:
            if len(cluster) >= 3 and random.random() < 0.05:  # реже
                try:
                    words = [m.trace_id for m in cluster[:3]]
                    self.field.create_knot(words)
                    knots_created += 1
                except:
                    pass
        
        self.stats["knots_created"] += knots_created
        if knots_created > 0 and self.config.verbose:
            print(f"   🔗 Создано топологических узлов: {knots_created}")
    
    def _decay_old_modes(self):
        """Забывание старых, слабых мод"""
        import time
        now = time.time()
        
        to_remove = []
        for mode in self.field.h_field:
            if mode.scale >= 30.0:
                continue
            
            last_used = mode.last_used.timestamp() if mode.last_used else mode.created.timestamp()
            age_days = (now - last_used) / 86400
            
            if age_days > self.config.decay_threshold_days and mode.amplitude < self.config.decay_amplitude_threshold:
                to_remove.append(mode.trace_id)
        
        if to_remove:
            self.field.h_field = [m for m in self.field.h_field if m.trace_id not in to_remove]
            self.stats["decayed"] += len(to_remove)
            if self.config.verbose:
                print(f"   💀 Забыто старых мод: {len(to_remove)}")
    
    def _self_dialogue(self):
        """Самодиалог — с защитой от рекурсии"""
        if not self.field.h_field or self.overheated:
            return
        
        mode = random.choice(self.field.h_field[:100])
        words = mode.content[:100].split()[:5]
        if len(words) < 2:
            return
        
        question = f"Что такое {' '.join(words)}?"
        
        try:
            result = self.field.process(question, user_id="_self_")
            if result.get("mode_type") == "field_answer" and self.config.verbose:
                print(f"   💬 Самодиалог: {question[:50]}... → {result['answer'][:50]}...")
        except Exception as e:
            if self.config.verbose:
                print(f"   ⚠️ Ошибка самодиалога: {e}")
    
    def _print_stats(self):
        """Печатает статистику"""
        print(f"   📊 Статистика: фуркаций={self.stats['furcations']}, "
              f"резонансов={self.stats['cross_resonances']}, "
              f"забыто={self.stats['decayed']}, "
              f"узлов={self.stats['knots_created']}")
        if self.stats['damping_applied'] > 0:
            print(f"   🛡️ Демпфирований: {self.stats['damping_applied']}, "
                  f"перегревов: {self.stats['overheat_events']}")
    
    def get_stats(self) -> Dict:
        """Возвращает статистику"""
        with self._lock:
            return {
                "cycle_count": self.cycle_count,
                "overheated": self.overheated,
                **self.stats,
                "total_modes": len(self.field.h_field) if self.field else 0
            }