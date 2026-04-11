"""
hierarchical_memory.py — иерархическая память для поля H
Версия 1.0
"""

class HierarchicalMemory:
    def __init__(self):
        # Frozen scales (не создают новые узлы)
        self.frozen_scales = [0.1, 0.3, 1.0]
        # Growing scales (могут создавать новые узлы и фуркации)
        self.growing_scales = [3.0, 10.0, 30.0, 100.0]
    
    def is_frozen(self, scale: float) -> bool:
        return scale in self.frozen_scales
    
    def is_growing(self, scale: float) -> bool:
        return scale in self.growing_scales
    
    def can_create_node(self, scale: float) -> bool:
        return self.is_growing(scale)
    
    def can_create_furcation(self, scale: float) -> bool:
        return self.is_growing(scale) and scale != 100.0
    
    def get_scale_name(self, scale: float) -> str:
        if scale <= 0.3: return "буквы/слоги"
        if scale <= 1.0: return "слова"
        if scale <= 3.0: return "словосочетания"
        if scale <= 10.0: return "предложения"
        if scale <= 30.0: return "абзацы"
        return "целые тексты"