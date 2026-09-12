# tees_fractal_search.py
# 🔍 Поиск фракталов — только структура

from typing import List, Dict, Any, Optional
from tees_fractal_image import FractalImage
from tees_listing import Listing
from tees_cluster import TeesCluster


# Стоп-слова (только для слов)
STOP_WORDS = frozenset({
    'в', 'на', 'с', 'по', 'из', 'от', 'к', 'у', 'за',
    'и', 'а', 'но', 'или', 'что', 'как', 'так', 'же', 'бы', 'ли',
    'не', 'ни', 'то', 'это', 'все', 'всё', 'для', 'при', 'под',
    'над', 'об', 'без', 'до', 'со', 'the', 'a', 'an', 'in', 'on',
    'at', 'to', 'for', 'of', 'from', 'and', 'or', 'but', 'if', 'so',
})


def units_similarity(img1: FractalImage, img2: FractalImage) -> float:
    """
    Jaccard по единицам (без лемм).
    Единицы: слова, фразы, предложения.
    """
    units1 = set()
    units2 = set()
    
    for level_num in img1.levels:
        if level_num not in img2.levels:
            continue
        name = img1.levels[level_num]['name']
        if name not in ('words', 'phrases', 'sentences', 'text'):
            continue
        
        for u in img1.levels[level_num]['units']:
            for w in u.lower().split():
                if w not in STOP_WORDS:
                    units1.add(w)
        
        for u in img2.levels[level_num]['units']:
            for w in u.lower().split():
                if w not in STOP_WORDS:
                    units2.add(w)
    
    if not units1 or not units2:
        return 0.0
    
    inter = len(units1 & units2)
    union = len(units1 | units2)
    return inter / union if union > 0 else 0.0


def structure_similarity(img1: FractalImage, img2: FractalImage) -> float:
    """Совпадение по структуре."""
    s1 = [img1.levels[l]['count'] for l in sorted(img1.levels.keys())]
    s2 = [img2.levels[l]['count'] for l in sorted(img2.levels.keys())]
    n = min(len(s1), len(s2))
    s1 = s1[:n]
    s2 = s2[:n]
    if not s1 or not s2:
        return 0.0
    matches = 0
    for a, b in zip(s1, s2):
        if max(a, b) == 0:
            continue
        diff = abs(a - b) / max(a, b)
        if diff < 0.2:
            matches += 1
    return matches / n if n > 0 else 0.0


def fractal_similarity(img1: FractalImage, img2: FractalImage) -> float:
    """Общий процент совпадения (структура + единицы)."""
    u = units_similarity(img1, img2)
    s = structure_similarity(img1, img2)
    return 0.6 * u + 0.4 * s


class FractalSearch:
    """
    🔍 Поиск фракталов.
    
    1. Гровер — точное совпадение генома
    2. fractal_similarity — процент (> 50%)
    3. Сортировка по проценту
    """
    
    VALID_THRESHOLD = 0.5
    
    def __init__(self, cluster: Optional[TeesCluster] = None):
        self.cluster = cluster or TeesCluster()
        self.listings: Dict[str, Listing] = {}
    
    def add_listing(self, listing: Listing):
        self.listings[listing.node_id] = listing
    
    def find_exact(self, text: str) -> Optional[Dict[str, Any]]:
        """Точный поиск через Гровер."""
        query_img = FractalImage(text)
        target_genome = query_img.get_genome()
        
        all_genomes = []
        genome_map = []
        
        for node_id, listing in self.listings.items():
            for i, genome in enumerate(listing.get_genomes()):
                all_genomes.append(genome)
                genome_map.append((node_id, i))
        
        if not all_genomes:
            return None
        
        result = self.cluster.grover_search_parallel(all_genomes, target_genome)
        
        if result['found']:
            node_id, variant_index = genome_map[result['index']]
            listing = self.listings[node_id]
            return {
                'node_id': node_id,
                'variant': listing.variants[variant_index],
                'similarity': 1.0,
                'is_exact': True,
            }
        
        return None
    
    def find_similar(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск похожих (структура + единицы)."""
        query_img = FractalImage(text)
        results = []
        
        for node_id, listing in self.listings.items():
            best_sim = 0.0
            best_variant = None
            
            for i, variant in enumerate(listing.variants):
                img = listing.fractals[i]
                sim = fractal_similarity(query_img, img)
                if sim > best_sim:
                    best_sim = sim
                    best_variant = variant
            
            if best_sim > self.VALID_THRESHOLD:
                results.append({
                    'node_id': node_id,
                    'best_variant': best_variant,
                    'similarity': best_sim,
                    'variants_count': len(listing.variants),
                })
        
        results.sort(key=lambda x: -x['similarity'])
        return results[:limit]
    
    def find_full(self, text: str, limit: int = 10) -> Dict[str, Any]:
        """Полный поиск."""
        exact = self.find_exact(text)
        similar = self.find_similar(text, limit)
        
        if exact:
            similar = [s for s in similar if s['node_id'] != exact['node_id']]
        
        return {
            'exact': exact,
            'similar': similar,
            'count': len(similar),
        }
    
    def list_all(self) -> List[Dict[str, Any]]:
        return [l.to_dict() for l in self.listings.values()]