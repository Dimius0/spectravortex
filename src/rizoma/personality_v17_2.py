"""
personality_v17_2.py — поле H с настоящим резонансом через τ, scale, complexity
Версия 17.2 — БЕЗ RANDOM(). Только детерминированные вычисления.
"""
import sys
import time
import math
from typing import Dict, List, Optional, Any
from collections import defaultdict

sys.path.insert(0, 'src')

from rizoma.tau_resonance import TauResonance
from rizoma.tau_regulator import TauRegulator


class SpectralMode:
    """Мода — без random(), всё от tau"""
    def __init__(self, tau: float, scale: float, complexity: int, content: str = ""):
        self.tau = tau
        self.scale = scale
        self.complexity = complexity
        self.content = content
        self.amplitude = 0.5
        
        # Детерминированная фаза от tau (вместо random)
        self.phase = (tau % 66) * (2 * math.pi / 66)
        
        # Частота от tau
        self.frequency = max(0.1, tau / 10.0)
        
        # Детерминированный trace_id от content
        self.trace_id = f"mode_{abs(hash(content)) % 1000000}" if content else f"mode_{tau}_{scale}"
        self.verified = False


class Personality:
    """
    Поле H v17.2 — с настоящим резонансом.
    НЕТ RANDOM(). Только математика.
    """
    
    def __init__(self, id: str = "p017_2", name: str = "Field H v17.2"):
        self.id = id
        self.name = name
        self.h_field: List[SpectralMode] = []
        self.vortices = {}
        
        # Резонанс и регулятор
        self.resonance_engine = TauResonance()
        self.tau_regulator = TauRegulator()
        
        # Состояние поля
        self.coherence = 0.85
        self.nodes_created_last_cycle = 0
        self.furcations_last_cycle = 0
        self.cpu_load = 0
        
        # Статистика
        self.total_nodes = 0
        self.total_furcations = 0
        self.cycle_count = 0
        
    def load(self, filepath: str):
        """Загружает поле из JSON (совместимость с v16_1)"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for mdata in data.get("h_field", []):
            mode = SpectralMode(
                tau=mdata.get("tau", 16.0),
                scale=mdata.get("scale", 1.0),
                complexity=mdata.get("complexity", 1),
                content=mdata.get("content", "")
            )
            self.h_field.append(mode)
        
        print(f"📂 Загружено поле: {len(self.h_field)} мод")
        return self
    
    def save(self, filepath: str):
        """Сохраняет поле в JSON"""
        import json
        data = {
            "id": self.id,
            "name": self.name,
            "h_field": [
                {
                    "tau": m.tau,
                    "scale": m.scale,
                    "complexity": m.complexity,
                    "content": m.content,
                    "amplitude": m.amplitude
                }
                for m in self.h_field
            ]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено: {filepath}")
    
    def add_mode(self, mode: SpectralMode):
        """Добавляет моду в поле"""
        self.h_field.append(mode)
    
    def compute_pair_resonance(self, mode1: SpectralMode, mode2: SpectralMode) -> float:
        """Вычисляет резонанс между двумя модами"""
        return self.resonance_engine.compute_resonance(mode1, mode2)
    
    def update_coherence(self):
        """Обновляет глобальную когерентность как средний резонанс"""
        if len(self.h_field) < 2:
            self.coherence = 0.85
            return
        
        sample = self.h_field[:1000]
        resonances = []
        
        for i in range(min(100, len(sample))):
            for j in range(i+1, min(100, len(sample))):
                res = self.compute_pair_resonance(sample[i], sample[j])
                resonances.append(res)
        
        self.coherence = self.resonance_engine.get_coherence(resonances)
    
    def adapt_tau_range(self):
        """Адаптирует диапазон τ на основе состояния поля"""
        stats = {
            "nodes_created_last_cycle": self.nodes_created_last_cycle,
            "furcations_last_cycle": self.furcations_last_cycle,
            "cpu_load": self.cpu_load,
            "coherence": self.coherence
        }
        changes = self.tau_regulator.update(stats)
        
        self.resonance_engine.tau_min = changes["tau_min"]
        self.resonance_engine.tau_max = changes["tau_max"]
        
        return changes
    
    def get_state(self) -> Dict[str, Any]:
        """Возвращает текущее состояние поля"""
        return {
            "coherence": self.coherence,
            "total_nodes": self.total_nodes,
            "total_furcations": self.total_furcations,
            "total_modes": len(self.h_field),
            "tau_min": self.resonance_engine.tau_min,
            "tau_max": self.resonance_engine.tau_max,
            "cycle": self.cycle_count
        }