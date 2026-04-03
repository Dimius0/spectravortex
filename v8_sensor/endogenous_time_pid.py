"""
endogenous_time_pid.py — эндогенный цикл с эмерджентным временем и ПИД-регулятором роста
Версия 3.0 — адаптивная автонастройка параметров для оптимального роста поля
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
        self.setpoint = setpoint      # целевой темп роста (узлов/мин)
        self.Kp = Kp                  # пропорциональный коэффициент
        self.Ki = Ki                  # интегральный коэффициент
        self.Kd = Kd                  # дифференциальный коэффициент
        self.integral = 0
        self.last_error = 0
        self.last_output = 0
        self.history = deque(maxlen=20)
        
    def update(self, current_rate, dt):
        """Обновляет регулятор и возвращает корректировку"""
        error = self.setpoint - current_rate
        self.integral += error * dt
        # Ограничиваем интегральное накопление
        self.integral = max(-10, min(10, self.integral))
        
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.last_error = error
        self.last_output = output
        self.history.append(output)
        
        return output
    
    def get_status(self):
        """Возвращает статус регулятора"""
        if not self.history:
            return 0, 0
        return self.last_output, sum(self.history) / len(self.history)


class TemporalEndogenousCyclePID:
    """Эндогенный цикл с эмерджентным временем и ПИД-регулятором"""
    
    def __init__(self, field):
        self.field = field
        self.dt = 0.1              # базовый шаг времени
        self.sync_threshold = 0.3  # порог синхронизации
        self.neighbor_influence = 0.1  # сила влияния соседей
        self.furcation_prob = 0.05     # вероятность фуркации
        self.cycle_count = 0
        self.history = []
        
        # ПИД-регулятор (цель — 0.5 узлов в минуту)
        self.pid = PIDRegulator(setpoint=0.5, Kp=0.3, Ki=0.1, Kd=0.05)
        
        # Счётчики для статистики
        self.last_knots = 0
        self.last_modes = 0
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
        
        # Адаптируем параметры в зависимости от коррекции
        if correction > 0:
            # Нужно ускорить рост
            self.furcation_prob = min(0.3, self.furcation_prob + correction * 0.01)
            self.neighbor_influence = min(0.5, self.neighbor_influence + correction * 0.05)
            self.dt = min(0.5, self.dt + correction * 0.02)
        else:
            # Нужно замедлить рост
            self.furcation_prob = max(0.01, self.furcation_prob + correction * 0.01)
            self.neighbor_influence = max(0.05, self.neighbor_influence + correction * 0.05)
            self.dt = max(0.05, self.dt + correction * 0.02)
        
        return correction
    
    def _spontaneous_furcation(self):
        """Спонтанное рождение новой моды"""
        # Ищем родительскую моду
        if not self.field.h_field:
            return
        
        parent = random.choice(self.field.h_field[:1000])
        
        # Создаём новую моду — копию родителя с мутацией
        from rizoma.personality_v16_1 import SpectralMode
        new_mode = SpectralMode(
            tau=parent.tau + random.uniform(-0.5, 0.5),
            amplitude=0.1,
            content=f"Фуркация от {parent.trace_id[:16]}",
            trace_id=f"furcation_{self.cycle_count}_{random.randint(0,10000)}",
            themes=parent.themes + ["furcation"],
            scale=parent.scale,
            complexity=parent.complexity,
            parent_id=parent.trace_id
        )
        self.field.add_to_h_field(new_mode)
        return True
    
    def _cross_scale_resonance(self):
        """Кросс-масштабный резонанс"""
        # Ищем пары мод с разными масштабами
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
        for _ in range(min(5, len(scales))):
            s1 = random.choice(scales)
            s2 = random.choice([s for s in scales if s != s1])
            if not modes_by_scale.get(s1) or not modes_by_scale.get(s2):
                continue
            
            mode1 = random.choice(modes_by_scale[s1])
            mode2 = random.choice(modes_by_scale[s2])
            
            # Усиливаем обе моды
            mode1.amplitude = min(1.0, mode1.amplitude + 0.02)
            mode2.amplitude = min(1.0, mode2.amplitude + 0.02)
            cross_count += 1
        
        return cross_count
    
    def _update_field(self):
        """Обновляет поле с учётом ПИД-коррекции"""
        
        # Сохраняем состояние ДО
        knots_before = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        modes_before = len(self.field.h_field)
        
        sync_start = time.time()
        
        # 1. Спонтанные фуркации
        furcations = 0
        if random.random() < self.furcation_prob:
            if self._spontaneous_furcation():
                furcations = 1
        
        # 2. Кросс-масштабный резонанс
        cross_count = self._cross_scale_resonance()
        
        # 3. Обновляем узлы (если есть метод)
        if hasattr(self.field, '_self_organize'):
            self.field._self_organize()
        
        sync_duration = time.time() - sync_start
        
        # Состояние ПОСЛЕ
        knots_after = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        modes_after = len(self.field.h_field)
        
        knots_growth = knots_after - knots_before
        modes_growth = modes_after - modes_before
        
        # Вычисляем текущий темп роста
        growth_rate = self._get_growth_rate()
        
        # Применяем ПИД-коррекцию
        pid_correction = self._apply_pid_correction(growth_rate)
        pid_output, pid_avg = self.pid.get_status()
        
        # Определяем доминирующий масштаб
        dominant_scale = self._get_dominant_scale()
        
        # Сохраняем в историю
        phase_data = {
            "number": self.cycle_count + 1,
            "timestamp": datetime.now().isoformat(),
            "duration": sync_duration,
            "dominant_scale": dominant_scale,
            "knots_growth": knots_growth,
            "modes_growth": modes_growth,
            "furcations": furcations,
            "cross_count": cross_count,
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
║ УЗЛЫ:   +{knots_growth:>3}  │ МОДЫ:   +{modes_growth:>3}  │ ФУРКАЦИИ: {furcations}  │ КРОСС: {cross_count}                    
╠══════════════════════════════════════════════════════════════════════════════╣
║ ТЕМП РОСТА: {growth_rate:.3f} узлов/мин    ЦЕЛЬ: {self.pid.setpoint:.1f} узлов/мин                       
║ ПИД:      {pid_correction:+.3f} (среднее: {pid_avg:+.3f})                                      
╠══════════════════════════════════════════════════════════════════════════════╣
║ ПАРАМЕТРЫ: dt={self.dt:.2f} | порог={self.sync_threshold:.2f} | влияние={self.neighbor_influence:.2f} | фуркации={self.furcation_prob:.2f}
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # Автосохранение
        fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_pid_{self.cycle_count + 1}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.field.save(fname)
        print(f'💾 СНАПШОТ: {fname}')
        
        self.cycle_count += 1
    
    def _update_phases(self):
        """Обновляет фазы всех мод с учётом neighbour_influence"""
        total_modes = len(self.field.h_field)
        report_step = 10000
        
        for i, mode in enumerate(self.field.h_field):
            neighbors = self._find_neighbors(mode)
            if neighbors:
                # Естественная эволюция + влияние соседей
                mode.phase += mode.frequency * self.dt
                for neighbor in neighbors:
                    diff = neighbor.phase - mode.phase
                    mode.phase += self.neighbor_influence * diff * self.dt
            else:
                # Только естественная эволюция
                mode.phase += mode.frequency * self.dt
            
            mode.phase %= 2 * math.pi
            mode.last_update = time.time()
            
            if (i + 1) % report_step == 0:
                print(f"   Обновлено мод: {i + 1}")
    
    def run(self):
        """Запускает цикл с эмерджентным временем и ПИД-регулятором"""
        print("=" * 70)
        print("🌱 ЭНДОГЕННЫЙ ЦИКЛ С ЭМЕРДЖЕНТНЫМ ВРЕМЕНЕМ И ПИД-РЕГУЛЯТОРОМ (v3.0)")
        print("=" * 70)
        print(f" Слов: {len(self.field.vortices)}")
        print(f" Мод: {len(self.field.h_field)}")
        print(f" Узлов (старт): {len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0}")
        print("=" * 70)
        print("⏳ Цель ПИД: поддерживать темп роста 0.5 узлов в минуту")
        print("   Параметры адаптируются автоматически")
        print("   Нажми Ctrl+C для остановки")
        print("=" * 70)
        
        try:
            while True:
                # 1. Обновляем фазы всех мод
                self._update_phases()
                
                # 2. Вычисляем глобальную фазу
                global_phase = self._compute_global_phase()
                
                # 3. Проверяем условие синхронизации
                if abs(global_phase - math.pi/2) < self.sync_threshold:
                    self._update_field()
                    time.sleep(1)
                
                # 4. Демпфирующая пауза
                time.sleep(self.dt)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Остановка по Ctrl+C...")
            
            # Финальное сохранение
            fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_pid_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            self.field.save(fname)
            
            # Выводим итоговую статистику
            print("\n" + "=" * 70)
            print("📊 ИТОГОВАЯ СТАТИСТИКА")
            print("=" * 70)
            print(f" Всего синхронизаций: {self.cycle_count}")
            knots_final = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
            print(f" Финальное число узлов: {knots_final}")
            print(f" Финальное число мод: {len(self.field.h_field)}")
            
            # Статистика ПИД
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
    
    # Загружаем поле
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_1.json')
    
    # Запускаем цикл с ПИД-регулятором
    cycle = TemporalEndogenousCyclePID(p)
    cycle.run()