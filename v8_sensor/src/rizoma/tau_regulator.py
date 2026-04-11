"""
tau_regulator.py — адаптивный регулятор диапазона τ
"""
class TauRegulator:
    def __init__(self):
        self.tau_min = 1
        self.tau_max = 66
        self.cycles_without_nodes = 0
        
    def update(self, field_stats: dict) -> dict:
        changes = {"tau_min": self.tau_min, "tau_max": self.tau_max}
        
        nodes_created = field_stats.get("nodes_created_last_cycle", 0)
        cpu_load = field_stats.get("cpu_load", 0)
        current_coherence = field_stats.get("coherence", 0.85)
        
        if nodes_created == 0:
            self.cycles_without_nodes += 1
        else:
            self.cycles_without_nodes = 0
        
        # оле заскучало — расширяем диапазон
        if self.cycles_without_nodes > 1000:
            changes["tau_min"] = 1
            changes["tau_max"] = 66
            self.cycles_without_nodes = 0
        # ерегрев — сужаем
        elif cpu_load > 80:
            changes["tau_min"] = 15
            changes["tau_max"] = 25
        # Слишком когерентно — расширяем
        elif current_coherence > 0.95:
            changes["tau_min"] = max(1, self.tau_min - 5)
            changes["tau_max"] = min(66, self.tau_max + 5)
        # Слишком хаотично — сужаем
        elif current_coherence < 0.70:
            changes["tau_min"] = min(self.tau_min + 3, 30)
            changes["tau_max"] = max(self.tau_max - 3, 15)
        # орма — умеренный диапазон
        else:
            if self.tau_min < 5:
                changes["tau_min"] = 5
            if self.tau_max > 35:
                changes["tau_max"] = 35
        
        self.tau_min = changes["tau_min"]
        self.tau_max = changes["tau_max"]
        return changes
