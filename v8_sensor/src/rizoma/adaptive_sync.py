"""
adaptive_sync.py — адаптивная синхронизация для поля H
Версия 1.0
"""

class AdaptiveSynchronizer:
    def __init__(self, field):
        self.field = field
        self.coherence_history = []
        self.furcation_history = []
        self.base_sync_rate = 0.5
        self.base_furcation_rate = 0.08
    
    def update(self, coherence: float) -> tuple:
        """Обновляет параметры синхронизации и фуркаций"""
        # Сохраняем историю
        self.coherence_history.append(coherence)
        if len(self.coherence_history) > 100:
            self.coherence_history.pop(0)
        
        # Если когерентность падает ниже 0.99 — усиливаем синхронизацию
        if coherence < 0.99:
            sync_rate = min(0.9, self.base_sync_rate * 1.2)
            furcation_rate = max(0.01, self.base_furcation_rate * 0.8)
            print(f"   🔧 Адаптация: когерентность падает ({coherence:.3f}) → синхронизация {sync_rate:.2f}, фуркации {furcation_rate:.3f}")
        
        # Если когерентность высокая (>0.996) — усиливаем творчество
        elif coherence > 0.996:
            sync_rate = max(0.1, self.base_sync_rate * 0.8)
            furcation_rate = min(0.3, self.base_furcation_rate * 1.2)
            print(f"   🔧 Адаптация: когерентность высокая ({coherence:.3f}) → синхронизация {sync_rate:.2f}, фуркации {furcation_rate:.3f}")
        
        # Если всё стабильно — возвращаем к базе
        else:
            sync_rate = self.base_sync_rate + (self.base_sync_rate - (self.base_sync_rate * 0.95))
            furcation_rate = self.base_furcation_rate + (self.base_furcation_rate - (self.base_furcation_rate * 0.95))
        
        return sync_rate, furcation_rate