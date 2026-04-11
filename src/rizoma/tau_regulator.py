"""
tau_regulator.py — адаптивный регулятор диапазона τ
Поле само управляет своей когерентностью через распределение τ
"""
from typing import Dict, Any, Optional


class TauRegulator:
    """
    Регулирует диапазон τ в поле.
    Широкий диапазон (1-66) → низкая когерентность (~0.6) → поле "нюхает"
    Узкий диапазон (15-25) → высокая когерентность (~0.95) → поле "фокусируется"
    """
    
    def __init__(self):
        # Текущий диапазон τ
        self.tau_min = 1
        self.tau_max = 66
        
        # Пороги переключения
        self.coherence_high_threshold = 0.95
        self.coherence_low_threshold = 0.70
        
        # Счётчики активности
        self.cycles_without_nodes = 0
        self.cycles_without_furcations = 0
        
    def update(self, field_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновляет диапазон τ на основе состояния поля.
        Возвращает изменения для применения.
        """
        changes = {"tau_min": self.tau_min, "tau_max": self.tau_max}
        
        # Получаем статистику поля
        nodes_created = field_stats.get("nodes_created_last_cycle", 0)
        furcations_created = field_stats.get("furcations_last_cycle", 0)
        cpu_load = field_stats.get("cpu_load", 0)
        current_coherence = field_stats.get("coherence", 0.85)
        
        # Счётчик бездействия
        if nodes_created == 0:
            self.cycles_without_nodes += 1
        else:
            self.cycles_without_nodes = 0
            
        if furcations_created == 0:
            self.cycles_without_furcations += 1
        else:
            self.cycles_without_furcations = 0
        
        # === АДАПТИВНАЯ ЛОГИКА ===
        
        # 1. Поле "заскучало" — нет новых узлов долгое время
        if self.cycles_without_nodes > 1000:
            # Расширяем диапазон τ (нюхаем)
            changes["tau_min"] = 1
            changes["tau_max"] = 66
            changes["reason"] = "sketching"
            self.cycles_without_nodes = 0
            
        # 2. Поле "перегрелось" — высокая нагрузка
        elif cpu_load > 80:
            # Сужаем диапазон τ (фокусируемся, экономим ресурсы)
            changes["tau_min"] = 15
            changes["tau_max"] = 25
            changes["reason"] = "overheated"
            
        # 3. Когерентность слишком высокая — эпилепсия или сон
        elif current_coherence > self.coherence_high_threshold:
            # Расширяем диапазон, чтобы снизить когерентность
            changes["tau_min"] = max(1, self.tau_min - 5)
            changes["tau_max"] = min(66, self.tau_max + 5)
            changes["reason"] = "too_coherent"
            
        # 4. Когерентность слишком низкая — хаос
        elif current_coherence < self.coherence_low_threshold:
            # Сужаем диапазон, чтобы повысить когерентность
            changes["tau_min"] = min(self.tau_min + 3, 30)
            changes["tau_max"] = max(self.tau_max - 3, 15)
            changes["reason"] = "too_chaotic"
            
        # 5. Нормальный режим — поддерживаем умеренный диапазон
        else:
            if self.tau_min < 5:
                changes["tau_min"] = 5
            if self.tau_max > 35:
                changes["tau_max"] = 35
            changes["reason"] = "normal"
        
        # Применяем изменения
        self.tau_min = changes["tau_min"]
        self.tau_max = changes["tau_max"]
        
        return changes
    
    def is_tau_allowed(self, tau: float) -> bool:
        """Проверяет, разрешён ли данный τ в текущем диапазоне"""
        return self.tau_min <= tau <= self.tau_max