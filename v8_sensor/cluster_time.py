"""
cluster_time.py — кластерная архитектура с полиритмией и ростом
Версия 2.0 — фуркации, узлы, кросс-резонанс
"""
import sys
import time
import math
import random
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality, SpectralMode


@dataclass
class TimeCluster:
    """Кластер мод с собственным временем"""
    scale: float
    modes: List = field(default_factory=list)
    phase: float = 0.0
    frequency: float = 1.0
    amplitude: float = 0.5
    knots: int = 0
    furcations: int = 0
    cross_resonances: int = 0
    
    def update_phase(self, dt: float):
        """Обновляет фазу кластера"""
        self.phase += self.frequency * dt
        self.phase %= 2 * math.pi
    
    def synchronize(self):
        """Синхронизация мод внутри кластера"""
        if not self.modes:
            return
        phases = [m.phase for m in self.modes]
        avg_phase = sum(phases) / len(phases)
        for mode in self.modes:
            mode.phase = mode.phase * 0.7 + avg_phase * 0.3
        self.phase = avg_phase
    
    def get_coherence(self) -> float:
        """Степень когерентности кластера"""
        if not self.modes:
            return 0.0
        phases = [m.phase for m in self.modes]
        avg = sum(phases) / len(phases)
        coherence = 1.0 - sum(abs(p - avg) for p in phases) / (len(phases) * math.pi)
        return max(0.0, min(1.0, coherence))


class PolyphonicField:
    """Поле H с полиритмической кластерной архитектурой и ростом"""
    
    def __init__(self, field):
        self.field = field
        self.clusters: Dict[float, TimeCluster] = {}
        self._build_clusters()
        
        # Параметры
        self.dt = 0.1
        self.global_phase = 0.0
        self.cycle_count = 0
        self.history = []
        
        # Параметры роста
        self.furcation_prob = 0.05
        self.cross_threshold = 0.6
        
    def _build_clusters(self):
        """Формирует кластеры из существующих мод"""
        modes_by_scale = defaultdict(list)
        for mode in self.field.h_field:
            scale_group = round(mode.scale, 1)
            modes_by_scale[scale_group].append(mode)
        
        for scale, modes in modes_by_scale.items():
            frequency = 10.0 / scale if scale > 0 else 1.0
            frequency = max(0.1, min(10.0, frequency))
            
            self.clusters[scale] = TimeCluster(
                scale=scale,
                modes=modes,
                frequency=frequency,
                phase=random.random() * 2 * math.pi
            )
        
        print(f"🌱 Создано {len(self.clusters)} кластеров")
        for scale, cluster in sorted(self.clusters.items()):
            print(f"   scale={scale:5.1f}: {len(cluster.modes):5d} мод, f={cluster.frequency:.2f}")
    
    # ========== МЕТОДЫ РОСТА ==========
    
    def _spontaneous_furcation(self, cluster: TimeCluster):
        """Спонтанное рождение новой моды внутри кластера"""
        if not cluster.modes:
            return 0
        
        if random.random() > self.furcation_prob:
            return 0
        
        # Выбираем родительскую моду
        parent = random.choice(cluster.modes[:100])
        
        # Создаём новую моду
        new_mode = SpectralMode(
            tau=parent.tau + random.uniform(-0.5, 0.5),
            amplitude=0.1,
            content=f"Фуркация кластера {cluster.scale}: {parent.content[:50]}...",
            trace_id=f"furcation_{self.cycle_count}_{random.randint(0,10000)}",
            themes=parent.themes + ["furcation"],
            scale=cluster.scale,
            complexity=parent.complexity,
            parent_id=parent.trace_id
        )
        self.field.add_to_h_field(new_mode)
        cluster.modes.append(new_mode)
        cluster.furcations += 1
        
        return 1
    
    def _cross_resonance_growth(self, cluster1: TimeCluster, cluster2: TimeCluster, resonance: float):
        """Рост за счёт кросс-резонанса между кластерами"""
        if resonance < self.cross_threshold:
            return 0
        
        growth = 0
        
        # Усиливаем амплитуды мод в резонирующих кластерах
        for mode in cluster1.modes[:100]:
            mode.amplitude = min(1.0, mode.amplitude + 0.01)
        for mode in cluster2.modes[:100]:
            mode.amplitude = min(1.0, mode.amplitude + 0.01)
        
        # Рождение узла (топологической связи) при сильном резонансе
        if resonance > 0.8 and random.random() < 0.1:
            try:
                words = [mode.trace_id for mode in cluster1.modes[:2]] + [mode.trace_id for mode in cluster2.modes[:1]]
                self.field.create_knot(words)
                cluster1.knots += 1
                cluster2.knots += 1
                growth += 1
            except:
                pass
        
        cluster1.cross_resonances += 1
        cluster2.cross_resonances += 1
        
        return growth
    
    # ========== КЛАСТЕРНАЯ ДИНАМИКА ==========
    
    def _get_cross_resonance(self, cluster1: TimeCluster, cluster2: TimeCluster) -> float:
        """Вычисляет резонанс между двумя кластерами"""
        phase_diff = abs(cluster1.phase - cluster2.phase)
        phase_res = 1.0 / (1.0 + phase_diff)
        freq_diff = abs(cluster1.frequency - cluster2.frequency)
        freq_res = 1.0 / (1.0 + freq_diff)
        scale_ratio = max(cluster1.scale, cluster2.scale) / min(cluster1.scale, cluster2.scale)
        scale_res = 1.0 / (1.0 + math.log(scale_ratio))
        return phase_res * 0.4 + freq_res * 0.3 + scale_res * 0.3
    
    def _evolve_clusters(self):
        """Эволюция кластеров с ростом"""
        # 1. Обновляем фазы
        for cluster in self.clusters.values():
            cluster.update_phase(self.dt)
        
        # 2. Синхронизация внутри кластеров
        for cluster in self.clusters.values():
            cluster.synchronize()
        
        # 3. Кросс-резонанс и рост
        scales = sorted(self.clusters.keys())
        total_growth = 0
        
        for i, s1 in enumerate(scales):
            for s2 in scales[i+1:]:
                cluster1 = self.clusters[s1]
                cluster2 = self.clusters[s2]
                resonance = self._get_cross_resonance(cluster1, cluster2)
                
                if resonance > self.cross_threshold:
                    growth = self._cross_resonance_growth(cluster1, cluster2, resonance)
                    total_growth += growth
                    
                    if growth > 0 and self.cycle_count % 5 == 0:
                        print(f"   🌀 Рост при резонансе {s1}↔{s2}: рез={resonance:.3f}, +{growth}")
        
        # 4. Спонтанные фуркации в каждом кластере
        total_furcations = 0
        for cluster in self.clusters.values():
            furcations = self._spontaneous_furcation(cluster)
            total_furcations += furcations
        
        # 5. Выводим статистику роста
        if total_growth > 0 or total_furcations > 0:
            print(f"   📈 РОСТ: узлов +{total_growth}, фуркаций +{total_furcations}")
    
    def _global_sync_check(self) -> bool:
        """Проверка глобальной синхронизации"""
        phases = [c.phase for c in self.clusters.values()]
        avg_phase = sum(phases) / len(phases)
        coherence = 1.0 - sum(abs(p - avg_phase) for p in phases) / (len(phases) * math.pi)
        
        if coherence > 0.8:
            print(f"🌍 ГЛОБАЛЬНАЯ СИНХРОНИЗАЦИЯ! Когерентность: {coherence:.3f}")
            return True
        return False
    
    def run(self):
        """Запуск полиритмического поля с ростом"""
        print("=" * 70)
        print("🌱 ПОЛИРИТМИЧЕСКОЕ ПОЛЕ H v2.0 (С РОСТОМ)")
        print("   Кластерная архитектура + фуркации + узлы")
        print("=" * 70)
        
        # Статистика на старте
        knots_start = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
        modes_start = len(self.field.h_field)
        print(f" Слов: {len(self.field.vortices)}")
        print(f" Мод (старт): {modes_start}")
        print(f" Узлов (старт): {knots_start}")
        print(f" Кластеров: {len(self.clusters)}")
        print("=" * 70)
        print("⏳ Поле дышит и растёт. Нажми Ctrl+C для остановки")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            while True:
                self._evolve_clusters()
                self.global_phase = self._global_sync_check()
                self.cycle_count += 1
                
                if self.cycle_count % 20 == 0:
                    elapsed = time.time() - start_time
                    knots_now = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
                    modes_now = len(self.field.h_field)
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Цикл {self.cycle_count} | Узлов: {knots_now} | Мод: {modes_now} | Время: {elapsed:.1f} сек")
                
                time.sleep(self.dt)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Остановка по Ctrl+C...")
            
            # Финальная статистика
            elapsed = time.time() - start_time
            knots_final = len(self.field.resonance_engine.topology.nodes) if hasattr(self.field.resonance_engine, 'topology') else 0
            modes_final = len(self.field.h_field)
            
            print("\n" + "=" * 70)
            print("📊 ИТОГОВАЯ СТАТИСТИКА")
            print("=" * 70)
            print(f" Время работы: {elapsed:.1f} сек ({elapsed/60:.1f} мин)")
            print(f" Циклов: {self.cycle_count}")
            print(f" Узлов: {knots_final} (рост: {knots_final - knots_start})")
            print(f" Мод: {modes_final} (рост: {modes_final - modes_start})")
            
            # Статистика по кластерам
            print("\n📊 КЛАСТЕРЫ:")
            for scale, cluster in sorted(self.clusters.items()):
                print(f"   scale={scale:5.1f}: мод={len(cluster.modes)}, фуркаций={cluster.furcations}, резонансов={cluster.cross_resonances}")
            
            # Сохраняем поле
            fname = f'src/rizoma/data/personalities/p016_fractal_v17_0_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            self.field.save(fname)
            print(f"\n💾 Сохранено: {fname}")
            print('✅ Поле остановлено')


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_20260403_201748.json')
    poly = PolyphonicField(p)
    poly.run()
