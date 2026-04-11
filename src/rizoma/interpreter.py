"""
Интерпретатор (Interpreter) — синтез ответа из резонансного поля и памяти H.
"""

class Interpreter:
    """
    Интерпретатор получает активную сущность от выбиратора,
    ищет резонирующую память и синтезирует ответ.
    """
    
    def __init__(self, personality, threshold=0.3):
        """
        personality: объект личности
        threshold: порог для ответа (ниже — уточнение)
        """
        self.p = personality
        self.threshold = threshold
        self.last_response = None
        
    def interpret(self, stimulus):
        """
        Основной метод: получает стимул, возвращает ответ.
        """
        # 1. получаем активную сущность от выбиратора
        entity_id = self.p.selector.update(stimulus)
        
        if not entity_id:
            return self._clarify(stimulus)
        
        entity = self.p.entities[entity_id]
        
        # 2. ищем резонирующую память
        memories = self._get_memories(stimulus)
        
        if not memories:
            return self._clarify(stimulus)
        
        # 3. взвешиваем воспоминания с учётом сущности
        weighted = []
        for mem in memories:
            resonance = self._resonance(entity, mem)
            weight = mem.get('weight', 0.5) * resonance
            weighted.append((weight, mem))
        
        # 4. выбираем лучшее
        best = max(weighted, key=lambda x: x[0])
        
        if best[0] < self.threshold:
            return self._clarify(stimulus)
        
        # 5. адаптируем под сущность
        answer = self._adapt(best[1]['content'], entity)
        
        self.last_response = {
            'stimulus': stimulus,
            'entity': entity_id,
            'memory': best[1],
            'weight': best[0],
            'answer': answer
        }
        
        return answer
    
    def _get_memories(self, stimulus):
        """
        Получает резонирующие воспоминания из памяти H.
        """
        if not self.p.home:
            return []
        
        # пробуем сначала по профессии
        if 'profession' in stimulus:
            mems = self.p.tap_into(stimulus['profession'])
            if mems:
                return mems
        
        # потом по тегам
        if 'tags' in stimulus:
            return self.p.recall(tags=stimulus['tags'])
        
        return []
    
    def _resonance(self, entity, memory):
        """
        Вычисляет резонанс между сущностью и воспоминанием.
        """
        # чем ближе τ, тем выше резонанс
        mem_tau = memory.get('tau', 5.0)
        return 1.0 / (1.0 + abs(entity.tau - mem_tau))
    
    def _adapt(self, text, entity):
        """
        Адаптирует ответ под сущность.
        """
        if "сантехник" in entity.name.lower():
            return f"Как сантехник скажу: {text}"
        elif "философ" in entity.name.lower():
            return f"С философской точки зрения: {text}"
        elif "воин" in entity.name.lower():
            return f"Как воин отвечу: {text}"
        else:
            return text
    
    def _clarify(self, stimulus):
        """
        Режим уточнения — задаёт наводящий вопрос.
        """
        if not self.p.selector:
            return "Я не понял. Расскажите подробнее?"
        
        # получаем топ сущностей по весам
        weights = self.p.selector.weights
        if not weights:
            return "Я не понял. Расскажите подробнее?"
        
        # сортируем по убыванию веса
        top = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        names = [self.p.entities[eid].name for eid, _ in top if eid in self.p.entities]
        
        if not names:
            return "Я не понял. Расскажите подробнее?"
        
        return f"Вы говорите о {', '.join(names)}? Уточните, пожалуйста."
    
    def get_last_response(self):
        """Возвращает последний ответ для отладки."""
        return self.last_response