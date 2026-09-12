# tees_listing.py
# 📦 Объявление с вариантами формулировок

from typing import List, Dict, Any, Optional
from tees_fractal_image import FractalImage


class Listing:
    """
    📦 Объявление.
    
    Не одна формулировка. А — набор вариантов.
    Пользователь может добавлять варианты.
    Поиск идёт по всем вариантам.
    """
    
    def __init__(self, node_id: str, item: str, description: str = ""):
        self.node_id = node_id
        self.item = item
        self.description = description
        self.variants: List[str] = [item]
        
        # Фракталы для каждого варианта
        self.fractals: Dict[int, FractalImage] = {}
        self._rebuild()
    
    def add_variant(self, text: str):
        """Добавить вариант формулировки."""
        if text not in self.variants:
            self.variants.append(text)
            self._rebuild()
    
    def remove_variant(self, text: str):
        """Удалить вариант."""
        if text in self.variants and len(self.variants) > 1:
            self.variants.remove(text)
            self._rebuild()
    
    def _rebuild(self):
        """Пересобрать фракталы."""
        self.fractals = {}
        for i, v in enumerate(self.variants):
            self.fractals[i] = FractalImage(v)
    
    def get_genomes(self) -> List[bytes]:
        """Все геномы вариантов."""
        return [f.get_genome() for f in self.fractals.values()]
    
    def get_best_variant(self) -> str:
        """Лучший вариант (первый)."""
        return self.variants[0] if self.variants else ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'item': self.item,
            'description': self.description,
            'variants': self.variants,
            'variants_count': len(self.variants),
        }