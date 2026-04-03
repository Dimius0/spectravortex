"""
пределение уровня сложности текста
ерсия 1.0 для v16.1
"""

def detect_complexity(text: str) -> int:
    """пределяет уровень сложности текста (1-4)"""
    text_lower = text.lower()
    
    # -термины (уровень 3)
    vmmp_terms = ["вихрь", "τ", "дельта", "тета", "поле h", "фуркация", "узел",
                  "резонанс", "спектр", "когерентность", "∇⁴ψ"]
    if any(term in text_lower for term in vmmp_terms):
        return 3
    
    # аучные термины (уровень 2)
    science_terms = ["квант", "электрон", "протон", "атом", "молекула", "формула",
                     "уравнение", "теория", "эксперимент", "данные"]
    if any(term in text_lower for term in science_terms):
        return 2
    
    # оэтические маркеры (уровень 4)
    poetic_markers = ["стих", "рифма", "метафора", "образ", "душа", "сердце",
                      "любовь", "смерть", "жизнь", "небо", "звезда"]
    if any(marker in text_lower for marker in poetic_markers):
        return 4
    
    # наче — бытовой (уровень 1)
    return 1


def get_complexity_name(complexity: int) -> str:
    """озвращает название уровня сложности"""
    names = {1: "бытовой", 2: "научный", 3: "", 4: "метафорический"}
    return names.get(complexity, "unknown")