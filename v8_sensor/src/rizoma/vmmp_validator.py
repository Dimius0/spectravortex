"""
vmmp_validator.py — валидатор новых идей на соответствие ВММП
Версия 1.0 (эвристическая, до реального ∇⁴ψ=0)
"""

import re
import math

class VmmpValidator:
    def __init__(self):
        self.vmmp_terms = ['вихрь', 'τ', 'дельта', 'тета', 'поле h', '∇⁴ψ', 'фуркация', 'узел', 'когерентность', 'резонанс']
        self.science_terms = ['квант', 'электрон', 'протон', 'атом', 'молекула', 'энергия', 'масса', 'заряд', 'эксперимент']
    
    def validate(self, content: str, scale: float, complexity: int) -> tuple:
        """Возвращает (True/False, причина)"""
        content_lower = content.lower()
        
        # 1. Проверка длины (не слишком короткое)
        if len(content) < 50:
            return False, "слишком короткий контент (< 50 символов)"
        
        # 2. Проверка на шум (слишком много случайных символов)
        noise = sum(1 for c in content if ord(c) < 32 or ord(c) > 1103)
        if noise > len(content) * 0.1:
            return False, f"высокий уровень шума ({noise/len(content)*100:.0f}%)"
        
        # 3. Для научных узлов (complexity=2) проверяем наличие научных терминов
        if complexity == 2:
            science_score = sum(1 for term in self.science_terms if term in content_lower)
            if science_score < 1:
                return False, "недостаточно научных терминов для уровня complexity=2"
            return True, f"соответствует ВММП (научный уровень, найдено {science_score} терминов)"
        
        # 4. Для ВММП-узлов (complexity=3) проверяем наличие ВММП-терминов
        if complexity == 3:
            vmmp_score = sum(1 for term in self.vmmp_terms if term in content_lower)
            if vmmp_score < 1:
                return False, "недостаточно ВММП-терминов для уровня complexity=3"
            return True, f"соответствует ВММП (ВММП-уровень, найдено {vmmp_score} терминов)"
        
        # 5. Для метафор (complexity=4) — пропускаем с предупреждением
        if complexity == 4:
            return True, "метафорический уровень (верификация не требуется)"
        
        # 6. Для бытовых (complexity=1) — пропускаем
        return True, "бытовой уровень (верификация не требуется)"
    
    def validate_simple(self, scale: float, complexity: int) -> tuple:
        """Упрощённая валидация для быстрого тестирования"""
        if scale < 3.0:
            return False, f"масштаб {scale} frozen (нельзя создавать новые узлы)"
        if complexity == 2:
            return True, "научный уровень, валидация пройдена"
        if complexity == 3:
            return True, "ВММП-уровень, валидация пройдена"
        return True, "валидация пройдена"