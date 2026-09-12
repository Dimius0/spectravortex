# tees_fractal_image.py
# 🧠 Фрактал образов — конвейер геномов снизу вверх

import re
from typing import List, Dict, Any
from tees_core_tees import tees_recursive_vortex


def _extract_phase(vortex: bytes) -> float:
    """Фаза из TEES-вихря — детерминированно."""
    val = int.from_bytes(vortex[4:8], 'big')
    return (val % 628) / 100.0


def _make_vortex(data: bytes, seed: bytes) -> bytes:
    """TEES-вихрь от данных с seed."""
    return tees_recursive_vortex(data, seed, 3)


def _split_syllables(text: str) -> List[str]:
    """Слоговой парсер."""
    text = text.lower()
    vowels = 'аеёиоуыэюя'
    syllables = []
    current = ''
    for ch in text:
        if ch in vowels:
            if current:
                current += ch
                syllables.append(current)
                current = ''
            else:
                current = ch
        elif ch.isalpha():
            current += ch
        else:
            if current:
                syllables.append(current)
                current = ''
    if current:
        syllables.append(current)
    return syllables


class FractalImage:
    """
    🧠 Фрактал образов — конвейер геномов снизу вверх.
    
    Уровни:
      0: буквы
      1: слоги
      2: слова
      3: фразы
      4: предложения
      5: текст
    
    Каждый уровень — свой геном (TEES-вихрь).
    Геном уровня = вихрь от геномов единиц (с seed от нижнего уровня).
    Seed верхнего уровня = геном нижнего.
    
    Это — иерархия геномов. Не хеш. А — структурный отпечаток.
    """
    
    LEVELS = [
        (0, 'letters'),
        (1, 'syllables'),
        (2, 'words'),
        (3, 'phrases'),
        (4, 'sentences'),
        (5, 'text'),
    ]
    
    def __init__(self, text: str):
        self.text = text
        self.levels: Dict[int, Dict[str, Any]] = {}
        self._build()
    
    def _build(self):
        """Конвейер: снизу вверх."""
        seed = b'fractal_root'
        
        for level_num, name in self.LEVELS:  # 0, 1, 2, 3, 4, 5
            units = self._extract_units(name)
            if not units:
                continue
            
            # Геном каждой единицы с текущим seed
            unit_vortices = []
            for unit in units:
                v = _make_vortex(unit.encode('utf-8'), seed)
                unit_vortices.append(v)
            
            # Геном уровня = вихрь от геномов единиц
            combined = b''.join(unit_vortices)
            level_vortex = _make_vortex(combined, seed)
            
            # Фаза
            phase = _extract_phase(level_vortex)
            
            self.levels[level_num] = {
                'name': name,
                'units': units,
                'unit_vortices': unit_vortices,
                'count': len(units),
                'vortex': level_vortex,
                'phase': phase,
            }
            
            # Seed для следующего уровня = геном текущего
            seed = level_vortex
    
    def _extract_units(self, level_name: str) -> List[str]:
        """Извлекаем единицы уровня."""
        if level_name == 'text':
            return [self.text.strip()] if self.text.strip() else []
        
        elif level_name == 'sentences':
            return [s.strip() for s in re.split(r'[.!?]+', self.text) if s.strip()]
        
        elif level_name == 'phrases':
            words = re.findall(r'\b[а-яёa-z]+\b', self.text.lower())
            phrases = []
            for i in range(0, len(words) - 2, 2):
                phrases.append(' '.join(words[i:i+3]))
            return phrases
        
        elif level_name == 'words':
            return re.findall(r'\b[а-яёa-z]+\b', self.text.lower())
        
        elif level_name == 'syllables':
            return _split_syllables(self.text)
        
        elif level_name == 'letters':
            return [c for c in self.text.lower() if c.isalpha()]
        
        return []
    
    def get_genome(self) -> bytes:
        """Полный геном фрактала — геном верхнего уровня."""
        if not self.levels:
            return b''
        max_level = max(self.levels.keys())
        return self.levels[max_level]['vortex']
    
    def get_level_genome(self, level_name: str) -> bytes:
        """Геном конкретного уровня."""
        for level_num, data in self.levels.items():
            if data['name'] == level_name:
                return data['vortex']
        return b''