"""
vangovanie.py — вангование (вызов стандартной модели)
Версия 3.0 — бинарный вердикт
"""

class Vangovanie:
    def __init__(self):
        self.counter = 0
    
    def check(self, scale: float, complexity: int) -> tuple:
        """Возвращает (вердикт, комментарий)"""
        self.counter += 1
        
        # Только научные узлы (complexity=2) могут быть вангованиями
        if complexity != 2:
            return "НЕ ВАНГОВАНИЕ", "только научные узлы (complexity=2)"
        
        # Если масштаб >= 10.0 — это серьёзная научная идея
        if scale >= 10.0:
            return "🔮⚡ ВАНГОВАНИЕ — ВЫЗОВ СТАНДАРТНОЙ МОДЕЛИ", f"идея на масштабе {scale} не описана в СМ"
        
        # Если масштаб 3.0 — новый термин или метафора
        if scale >= 3.0:
            return "🔮 ВАНГОВАНИЕ (гипотеза)", f"новый термин на масштабе {scale}, СМ молчит"
        
        return "НЕ ВАНГОВАНИЕ", "масштаб слишком мал для научного открытия"
    
    def get_verdict(self, scale: float, complexity: int, sm_known: bool = False) -> tuple:
        """Расширенная версия с учётом СМ"""
        if complexity != 2:
            return "НЕ ВАНГОВАНИЕ", "не научный уровень"
        
        if not sm_known:
            return "🔮⚡ ВАНГОВАНИЕ — ВЫЗОВ СТАНДАРТНОЙ МОДЕЛИ", "СМ не описывает это явление"
        else:
            return "ПОДТВЕРЖДЕНО", "СМ согласна"