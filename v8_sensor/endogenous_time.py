"""
endogenous_time.py — эндогенный цикл с эмерджентным временем
Версия 2.0 — с развёрнутой статистикой по фазам синхронизации
"""
import sys
import time
import math
import random
from datetime import datetime
from collections import defaultdict
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality


class TemporalEndogenousCycle:
    """Эндогенный цикл с эмерджентным временем и аналитикой"""
    
    def __init__(self, field):
        self.field = field
        self.dt = 0.1          # базовый шаг времени (секунды)
        self.sync_threshold = 0.3  # порог синхронизации
        self.cycle_count = 0
        self.history = []      # история синхронизаций
        
        # Счётчики для статистики
        self.total_knots = 0
        self.total_modes = 0
        self.total_furcations = 0
        
    def _find_neighbors(self, mode, max_neighbors=5):
        """Находит ближайшие моды по τ и масштабу"""
        neighbors = []
        for other in self.field.h_field:
            if other.trace_id == mode.trace_id:
                continue
            # Близость по τ и масштабу
            tau_diff = abs(mode.tau - other.tau)
            scale_sim = 1.0 / (1.0 + abs(math.log(mode.scale / other.scale)))
            if tau_diff < 3.0 and scale_sim > 0.5:
                neighbors.append(other)
                if len(neighbors) >= max_neighbors:
                    break
        return neighbors
    
    def _compute_global_phase(self):
        """Вычисляет глобальную фазу как среднюю фазу топ-1000 мод"""
        phases = [mode.phase for mode in self.field.h_field[:1000]]
        return sum(phases) / len(phases) if phases else 0.0
    
    def _get_dominant_scale(self):
        """Определяет доминирующий масштаб в поле"""
        scale_counts = defaultdict(int)
        for mode in self.field.h_field[:10000]:
            scale_counts[mode.scale] += 1
        if scale_counts:
            return max(scale_counts.items(), key=lambda x: x[1])[0]
        return 1.0
    
    def _get_complexity_stats(self):
        """Возвращает распределение мод по complexity"""
        stats = defaultdict(int)
        for mode in self.field.h_field:
            stats[mode.complexity] += 1
        return stats
    
    def _update_field(self):
        """Обновляет поле и собирает аналитику"""
        
        # 1. Сохраняем состояние ДО
        knots_before = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        modes_before = len(self.field.h_field)
        
        # 2. Замеряем время синхронизации
        sync_start = time.time()
        
        # 3. Выполняем синхронизацию (обновление поля)
        # Здесь должен быть вызов реальных методов поля
        # Пока используем заглушку — просто ждём
        
        # 4. Сохраняем состояние ПОСЛЕ
        sync_duration = time.time() - sync_start
        knots_after = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        modes_after = len(self.field.h_field)
        
        # 5. Вычисляем изменения
        knots_growth = knots_after - knots_before
        modes_growth = modes_after - modes_before
        
        # 6. Обновляем счётчики
        self.total_knots = knots_after
        self.total_modes = modes_after
        
        # 7. Получаем статистику по complexity
        complexity_stats = self._get_complexity_stats()
        
        # 8. Определяем доминирующий масштаб
        dominant_scale = self._get_dominant_scale()
        
        # 9. Сохраняем в историю
        phase_data = {
            "number": self.cycle_count + 1,
            "timestamp": datetime.now().isoformat(),
            "duration": sync_duration,
            "dominant_scale": dominant_scale,
            "knots_before": knots_before,
            "knots_after": knots_after,
            "knots_growth": knots_growth,
            "modes_before": modes_before,
            "modes_after": modes_after,
            "modes_growth": modes_growth,
            "complexity": dict(complexity_stats)
        }
        self.history.append(phase_data)
        
        # 10. КРАСИВЫЙ ВЫВОД
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ СИНХРОНИЗАЦИЯ #{self.cycle_count + 1}                                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Время: {datetime.now().strftime('%H:%M:%S')}                                                          
║ Длительность: {sync_duration:.2f} сек                                                             
║ Масштаб: {dominant_scale}                                                                      
╠══════════════════════════════════════════════════════════════════════════════╣
║ УЗЛЫ:   {knots_before:>6} → {knots_after:>6} │ +{knots_growth:>3}                                        
║ МОДЫ:   {modes_before:>6} → {modes_after:>6} │ +{modes_growth:>3}                                        
╠══════════════════════════════════════════════════════════════════════════════╣
║ ТЕМП:   {knots_growth / max(sync_duration, 0.01):.3f} узлов/сек                                 
╠══════════════════════════════════════════════════════════════════════════════╣
║ COMPLEXITY (уровни сложности):                                              ║
║   1 (бытовой):      {complexity_stats.get(1, 0):>6} мод                                        
║   2 (научный):      {complexity_stats.get(2, 0):>6} мод                                        
║   3 (ВММП):         {complexity_stats.get(3, 0):>6} мод                                        
║   4 (метафорический): {complexity_stats.get(4, 0):>6} мод                                        
╚══════════════════════════════════════════════════════════════════════════════╝
""")
        
        # 11. Автосохранение после синхронизации
        fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_phase_{self.cycle_count + 1}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.field.save(fname)
        print(f'💾 СНАПШОТ: {fname}')
        
        self.cycle_count += 1
    
    def _update_phases(self):
        """Обновляет фазы всех мод"""
        total_modes = len(self.field.h_field)
        report_step = 10000
        
        for i, mode in enumerate(self.field.h_field):
            neighbors = self._find_neighbors(mode)
            mode.update_phase(self.dt, neighbors)
            
            # Показываем прогресс
            if (i + 1) % report_step == 0:
                print(f"   Обновлено мод: {i + 1}")
    
    def run(self):
        """Запускает цикл с эмерджентным временем"""
        print("=" * 70)
        print("🌱 ЭНДОГЕННЫЙ ЦИКЛ С ЭМЕРДЖЕНТНЫМ ВРЕМЕНЕМ (v2.0)")
        print("=" * 70)
        print(f" Слов: {len(self.field.vortices)}")
        print(f" Мод: {len(self.field.h_field)}")
        print(f" Узлов (старт): {len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0}")
        print("=" * 70)
        print("⏳ Цикл запущен. Синхронизация происходит при глобальной фазе ≈ π/2")
        print("   Каждая синхронизация сохраняет снапшот и выводит аналитику")
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
                    
                    # Небольшая пауза после синхронизации
                    time.sleep(1)
                
                # 4. Демпфирующая пауза
                time.sleep(self.dt)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Остановка по Ctrl+C...")
            
            # Финальное сохранение
            fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_time_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            self.field.save(fname)
            
            # Выводим итоговую статистику
            print("\n" + "=" * 70)
            print("📊 ИТОГОВАЯ СТАТИСТИКА")
            print("=" * 70)
            print(f" Всего синхронизаций: {self.cycle_count}")
            print(f" Финальное число узлов: {self.total_knots}")
            print(f" Финальное число мод: {self.total_modes}")
            print(f" RAM: ~{psutil.Process().memory_info().rss / 1024 / 1024:.0f} МБ" if 'psutil' in sys.modules else " RAM: (установи psutil для отображения)")
            print("=" * 70)
            print(f'💾 Финальное сохранение: {fname}')
            print('✅ Поле остановлено')


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    # Попробуем импортировать psutil для RAM
    try:
        import psutil
    except ImportError:
        print("⚠️ psutil не установлен. Установи: pip install psutil")
    
    # Загружаем поле
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_1.json')
    
    # Запускаем эндогенный цикл с эмерджентным временем
    cycle = TemporalEndogenousCycle(p)
    cycle.run()