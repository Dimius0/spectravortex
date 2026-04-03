"""
endogenous_time_growth.py — эндогенный цикл с эмерджентным временем и РЕАЛЬНЫМ РОСТОМ
Версия 4.0 — фазы + синхронизация + фуркации + узлы + кросс-резонансы
"""
import sys
import time
import math
import random
from datetime import datetime
from collections import defaultdict, deque
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality


class PIDRegulator:
    """ПИД-регулятор для управления темпом роста поля"""
    
    def __init__(self, setpoint=0.5, Kp=0.3, Ki=0.1, Kd=0.05):
        self.setpoint = setpoint
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0
        self.last_error = 0
        self.last_output = 0
        self.history = deque(maxlen=20)
        
    def update(self, current_rate, dt):
        error = self.setpoint - current_rate
        self.integral += error * dt
        self.integral = max(-10, min(10, self.integral))
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.last_error = error
        self.last_output = output
        self.history.append(output)
        return output
    
    def get_status(self):
        if not self.history:
            return 0, 0
        return self.last_output, sum(self.history) / len(self.history)


class TemporalEndogenousCycleGrowth:
    """Эндогенный цикл с эмерджентным временем и реальным ростом"""
    
    def __init__(self, field):
        self.field = field
        self.dt = 0.1
        self.sync_threshold = 0.3
        self.neighbor_influence = 0.1
        self.furcation_prob = 0.05
        self.cycle_count = 0
        self.history = []
        
        # ПИД-регулятор
        self.pid = PIDRegulator(setpoint=0.5, Kp=0.3, Ki=0.1, Kd=0.05)
        
        # Счётчики для статистики
        self.last_knots = 0
        self.last_modes = 0
        self.last_furcations = 0
        self.last_cross = 0
        self.last_time = time.time()
        
    def _find_neighbors(self, mode, max_neighbors=5):
        """Находит ближайшие моды по τ и масштабу"""
        neighbors = []
        for other in self.field.h_field:
            if other.trace_id == mode.trace_id:
                continue
            tau_diff = abs(mode.tau - other.tau)
            scale_sim = 1.0 / (1.0 + abs(math.log(mode.scale / other.scale)))
            if tau_diff < 3.0 and scale_sim > 0.5:
                neighbors.append(other)
                if len(neighbors) >= max_neighbors:
                    break
        return neighbors
    
    def _compute_global_phase(self):
        """Вычисляет глобальную фазу"""
        phases = [mode.phase for mode in self.field.h_field[:1000]]
        return sum(phases) / len(phases) if phases else 0.0
    
    def _get_dominant_scale(self):
        """Определяет доминирующий масштаб"""
        scale_counts = defaultdict(int)
        for mode in self.field.h_field[:10000]:
            scale_counts[mode.scale] += 1
        if scale_counts:
            return max(scale_counts.items(), key=lambda x: x[1])[0]
        return 1.0
    
    def _get_growth_rate(self):
        """Вычисляет текущий темп роста узлов (в минуту)"""
        current_knots = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        current_time = time.time()
        dt_min = (current_time - self.last_time) / 60.0
        
        if dt_min > 0:
            rate = (current_knots - self.last_knots) / dt_min
        else:
            rate = 0
        
        self.last_knots = current_knots
        self.last_time = current_time
        return rate
    
    def _apply_pid_correction(self, growth_rate):
        """Применяет корректировку ПИД-регулятора"""
        correction = self.pid.update(growth_rate, self.dt)
        
        if correction > 0:
            self.furcation_prob = min(0.3, self.furcation_prob + correction * 0.01)
            self.neighbor_influence = min(0.5, self.neighbor_influence + correction * 0.05)
            self.dt = min(0.5, self.dt + correction * 0.02)
        else:
            self.furcation_prob = max(0.01, self.furcation_prob + correction * 0.01)
            self.neighbor_influence = max(0.05, self.neighbor_influence + correction * 0.05)
            self.dt = max(0.05, self.dt + correction * 0.02)
        
        return correction
    
    # ========== МЕТОДЫ РОСТА (ВЗЯТЫ ИЗ СТАРОГО ЦИКЛА) ==========
    
    def _spontaneous_furcations(self):
        """Спонтанное рождение новых мод"""
        if not self.field.h_field:
            return 0
        
        furcations = 0
        top_modes = sorted(self.field.h_field, key=lambda m: m.amplitude, reverse=True)[:100]
        
        for mode in top_modes:
            if random.random() > self.furcation_prob:
                continue
            
            # Ищем родителя
            parent = random.choice(top_modes[:20])
            if parent.trace_id == mode.trace_id:
                continue
            
            # Создаём новую моду
            from rizoma.personality_v16_1 import SpectralMode
            new_mode = SpectralMode(
                tau=(mode.tau + parent.tau) / 2,
                amplitude=0.2,
                content=f"Фуркация: {mode.content[:30]}... / {parent.content[:30]}...",
                trace_id=f"furcation_{self.cycle_count}_{random.randint(0,10000)}_{int(time.time())}",
                themes=list(set(mode.themes + parent.themes))[:5],
                scale=(mode.scale + parent.scale) / 2,
                complexity=max(1, min(4, (mode.complexity + parent.complexity) // 2)),
                parent_id=mode.trace_id
            )
            self.field.add_to_h_field(new_mode)
            furcations += 1
        
        return furcations
    
    def _cross_scale_resonance(self):
        """Кросс-масштабный резонанс — связываем разные масштабы"""
        if len(self.field.h_field) < 100:
            return 0
        
        # Группируем по масштабам
        modes_by_scale = {}
        for mode in self.field.h_field[:5000]:
            scale_key = round(mode.scale, 1)
            if scale_key not in modes_by_scale:
                modes_by_scale[scale_key] = []
            modes_by_scale[scale_key].append(mode)
        
        scales = list(modes_by_scale.keys())
        if len(scales) < 2:
            return 0
        
        cross_count = 0
        for _ in range(min(10, len(scales) * 2)):
            s1 = random.choice(scales)
            s2 = random.choice([s for s in scales if s != s1])
            if not modes_by_scale.get(s1) or not modes_by_scale.get(s2):
                continue
            
            mode1 = random.choice(modes_by_scale[s1])
            mode2 = random.choice(modes_by_scale[s2])
            
            # Вычисляем резонанс
            resonance = 1.0 / (1.0 + abs(mode1.tau - mode2.tau))
            scale_factor = 1.0 / (1.0 + abs(math.log(mode1.scale / mode2.scale)))
            total_res = resonance * scale_factor
            
            if total_res > 0.5:
                mode1.amplitude = min(1.0, mode1.amplitude + 0.02)
                mode2.amplitude = min(1.0, mode2.amplitude + 0.02)
                cross_count += 1
        
        return cross_count
    
    def _self_organize(self):
        """Самоорганизация — создание топологических узлов"""
        if len(self.field.h_field) < 100:
            return 0
        
        knots_created = 0
        
        # Ищем кластеры близких мод
        top_modes = sorted(self.field.h_field, key=lambda m: m.amplitude, reverse=True)[:200]
        used = set()
        
        for i, mode in enumerate(top_modes):
            if i in used:
                continue
            
            cluster = [mode]
            used.add(i)
            
            for j, other in enumerate(top_modes[i+1:], i+1):
                if j in used:
                    continue
                
                tau_close = abs(mode.tau - other.tau) < 3
                scale_close = abs(math.log(mode.scale / other.scale)) < 1
                
                if tau_close and scale_close:
                    cluster.append(other)
                    used.add(j)
            
            if len(cluster) >= 3 and random.random() < 0.1:
                try:
                    words = [m.trace_id for m in cluster[:3]]
                    self.field.create_knot(words)
                    knots_created += 1
                except:
                    pass
        
        return knots_created
    
    # ========== ОСНОВНОЙ МЕТОД СИНХРОНИЗАЦИИ ==========
    
    def _update_field(self):
        """Обновляет поле с реальным ростом"""
        
        # Сохраняем состояние ДО
        knots_before = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        modes_before = len(self.field.h_field)
        furcations_before = getattr(self.field, 'furcation_count', 0)
        
        sync_start = time.time()
        
        # ========== РЕАЛЬНЫЙ РОСТ ==========
        furcations = self._spontaneous_furcations()
        cross_count = self._cross_scale_resonance()
        knots_created = self._self_organize()
        
        sync_duration = time.time() - sync_start
        
        # Состояние ПОСЛЕ
        knots_after = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        modes_after = len(self.field.h_field)
        
        knots_growth = knots_after - knots_before
        modes_growth = modes_after - modes_before
        
        # Вычисляем темп роста
        growth_rate = self._get_growth_rate()
        
        # Применяем ПИД-коррекцию
        pid_correction = self._apply_pid_correction(growth_rate)
        pid_output, pid_avg = self.pid.get_status()
        
        dominant_scale = self._get_dominant_scale()
        
        # Сохраняем историю
        phase_data = {
            "number": self.cycle_count + 1,
            "timestamp": datetime.now().isoformat(),
            "duration": sync_duration,
            "dominant_scale": dominant_scale,
            "knots_growth": knots_growth,
            "modes_growth": modes_growth,
            "furcations": furcations,
            "cross_count": cross_count,
            "knots_created": knots_created,
            "growth_rate": growth_rate,
            "pid_correction": pid_correction,
            "params": {
                "dt": self.dt,
                "sync_threshold": self.sync_threshold,
                "neighbor_influence": self.neighbor_influence,
                "furcation_prob": self.furcation_prob
            }
        }
        self.history.append(phase_data)
        
        # КРАСИВЫЙ ВЫВОД
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ СИНХРОНИЗАЦИЯ #{self.cycle_count + 1}                                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Время: {datetime.now().strftime('%H:%M:%S')}                                                          
║ Длительность: {sync_duration:.2f} сек                                                             
║ Масштаб: {dominant_scale}                                                                      
╠══════════════════════════════════════════════════════════════════════════════╣
║ РОСТ:                                                                        ║
║   УЗЛЫ:   +{knots_growth:>3}  │ МОДЫ:   +{modes_growth:>3}  │ ФУРКАЦИИ: {furcations}  │ КРОСС: {cross_count}                    
╠══════════════════════════════════════════════════════════════════════════════╣
║ ТЕМП РОСТА: {growth_rate:.3f} узлов/мин    ЦЕЛЬ: {self.pid.setpoint:.1f} узлов/мин                       
║ ПИД:      {pid_correction:+.3f} (среднее: {pid_avg:+.3f})                                      
╠══════════════════════════════════════════════════════════════════════════════╣
║ ПАРАМЕТРЫ: dt={self.dt:.2f} | порог={self.sync_threshold:.2f} | влияние={self.neighbor_influence:.2f} | фуркации={self.furcation_prob:.2f}
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Автосохранение
        fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_growth_{self.cycle_count + 1}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.field.save(fname)
        print(f'💾 СНАПШОТ: {fname}')
        
        self.cycle_count += 1
    
    def _update_phases(self):
        """Обновляет фазы всех мод"""
        total_modes = len(self.field.h_field)
        report_step = 10000
        
        for i, mode in enumerate(self.field.h_field):
            neighbors = self._find_neighbors(mode)
            if neighbors:
                mode.phase += mode.frequency * self.dt
                for neighbor in neighbors:
                    diff = neighbor.phase - mode.phase
                    mode.phase += self.neighbor_influence * diff * self.dt
            else:
                mode.phase += mode.frequency * self.dt
            
            mode.phase %= 2 * math.pi
            mode.last_update = time.time()
            
            if (i + 1) % report_step == 0:
                print(f"   Обновлено мод: {i + 1}")
    
    def run(self):
        """Запускает цикл с эмерджентным временем и реальным ростом"""
        print("=" * 70)
        print("🌱 ЭНДОГЕННЫЙ ЦИКЛ С ЭМЕРДЖЕНТНЫМ ВРЕМЕНЕМ И РЕАЛЬНЫМ РОСТОМ (v4.0)")
        print("=" * 70)
        print(f" Слов: {len(self.field.vortices)}")
        print(f" Мод: {len(self.field.h_field)}")
        knots_start = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        print(f" Узлов (старт): {knots_start}")
        print("=" * 70)
        print("⏳ Рост происходит в моменты синхронизации")
        print("   ПИД-регулятор автоматически настраивает параметры")
        print("   Нажми Ctrl+C для остановки")
        print("=" * 70)
        
        try:
            while True:
                self._update_phases()
                global_phase = self._compute_global_phase()
                
                if abs(global_phase - math.pi/2) < self.sync_threshold:
                    self._update_field()
                    time.sleep(1)
                
                time.sleep(self.dt)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Остановка по Ctrl+C...")
            
            fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_growth_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            self.field.save(fname)
            
            print("\n" + "=" * 70)
            print("📊 ИТОГОВАЯ СТАТИСТИКА")
            print("=" * 70)
            print(f" Всего синхронизаций: {self.cycle_count}")
            knots_final = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
            print(f" Финальное число узлов: {knots_final}")
            print(f" Финальное число мод: {len(self.field.h_field)}")
            
            if self.history:
                avg_growth = sum(h.get("growth_rate", 0) for h in self.history) / len(self.history)
                print(f" Средний темп роста: {avg_growth:.3f} узлов/мин")
                print(f" Финальные параметры: dt={self.dt:.2f}, furcation_prob={self.furcation_prob:.2f}")
            
            try:
                import psutil
                print(f" RAM: ~{psutil.Process().memory_info().rss / 1024 / 1024:.0f} МБ")
            except:
                pass
            
            print("=" * 70)
            print(f'💾 Финальное сохранение: {fname}')
            print('✅ Поле остановлено')


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("⚠️ psutil не установлен. Установи: pip install psutil")
    
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_1.json')
    cycle = TemporalEndogenousCycleGrowth(p)
    cycle.run()