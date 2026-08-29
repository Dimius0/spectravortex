# forest_server.py
# 🌲 Сервер для Голоса Леса — связывает HTML с DeepSeek API

import http.server
import json
import urllib.request
import urllib.parse
import random
import time
import hashlib
import re
import gc
import math  # ← ДОБАВЛЕНО: math наверху
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field  # ← УБРАН asdict (не используется)
from difflib import SequenceMatcher

# Импортируем маяк (если доступен)
try:
    from tees_beacon_tees import Beacon
    BEACON_AVAILABLE = True
    print("🏮 Маяк загружен")
except ImportError as e:
    BEACON_AVAILABLE = False
    print(f"⚠️ Маяк не найден: {e}")

# Импортируем SeedDistributor (если доступен)
try:
    from tees_seed_distributor import SeedDistributor
    SEED_AVAILABLE = True
    print("🌰 SeedDistributor загружен")
except ImportError as e:
    SEED_AVAILABLE = False
    print(f"⚠️ SeedDistributor не найден: {e}")

# Импортируем фрактальную память из TEES
try:
    from tees_beacon_tees import FractalMemory
    FRACTAL_MEMORY_AVAILABLE = True
except ImportError:
    FRACTAL_MEMORY_AVAILABLE = False
    print("⚠️ FractalMemory не найдена, использую простую память")

# ← ДОБАВЛЕНО: TEES-функции наверху
try:
    from tees_core_tees import tees_recursive_vortex, tees_triad_collapse
    TEES_CORE_AVAILABLE = True
except ImportError:
    TEES_CORE_AVAILABLE = False
    print("⚠️ tees_core_tees не найден")

# ← ДОБАВЛЕНО: Флаг отладки
DEBUG = False

@dataclass
class Listing:
    """Структура объявления для ярмарки"""
    node_address: str
    listing_type: str
    item: str
    description: str
    category: str = 'общее'
    location: str = ''  # Город/район (пусто = анонимно)
    geo_enabled: bool = False  # Включено ли гео
    coordinates: tuple = None  # (lat, lon) — опционально, для точного поиска
    created_at: float = field(default_factory=time.time)
    status: str = 'active'
    matched_nodes: Set[str] = field(default_factory=set)
    listing_hash: str = field(default='')
    
    def __post_init__(self):
        """Инициализация после создания"""
        self.listing_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Генерация хеша объявления (без гео для анонимности)"""
        data = f"{self.node_address}:{self.listing_type}:{self.item}:{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """Преобразование в словарь для отправки (с учётом приватности)"""
        result = {
            'node_address': self.node_address,
            'listing_type': self.listing_type,
            'item': self.item,
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at,
            'status': self.status,
            'listing_hash': self.listing_hash,
            'matched_nodes': list(self.matched_nodes),
            'geo_enabled': self.geo_enabled,
            'location': self.location if self.geo_enabled else 'скрыто 🔒'
        }
        
        # Координаты передаём только если гео включено
        if self.geo_enabled and self.coordinates:
            result['coordinates'] = self.coordinates
        
        return result

class FairMarket:
    """Класс для управления ярмаркой с кругами взаимопомощи"""
    
    def __init__(self):
        self.listings: List[Listing] = []
        self.categories = [
            'знания', 'ресурсы', 'услуги', 'инструменты', 
            'информация', 'поддержка', 'связи', 'общее'
        ]
        
        # Статистика узлов
        self.node_stats: Dict[str, Dict] = {}
        self.node_connections: Dict[str, Set[str]] = {}  # граф связей через ярмарку
        
        # Кэширование кругов
        self.circles_cache: Dict[str, tuple] = {}  # node_address -> (timestamp, circles)
        self.CACHE_TTL = 30  # 30 секунд
        self.MAX_CACHE_SIZE = 100  # Максимум 100 записей в кэше
        
        # Управление неактивными узлами
        self.NODE_INACTIVITY_TIMEOUT = 3600  # 1 час неактивности
        self.last_activity: Dict[str, float] = {}  # время последней активности узла
        
        # Ограничение объявлений
        self.MAX_LISTINGS = 1000  # Максимум объявлений

        # Гео-данные узлов (приватно!)
        self.node_locations: Dict[str, Dict] = {}  # node_address -> {city, coordinates, is_public}
        
        # Словарь городов для нормализации
        self.city_aliases = {
            'москва': 'Москва',
            'мск': 'Москва',
            'moscow': 'Москва',
            'питер': 'Санкт-Петербург',
            'спб': 'Санкт-Петербург',
            'saint petersburg': 'Санкт-Петербург',
            'st petersburg': 'Санкт-Петербург',
        }
        
    def add_listing(self, node_address: str, listing_type: str, item: str, 
                   description: str = "", category: str = "общее") -> tuple:
        """
        Добавление нового объявления.
        Возвращает (listing, circles) — объявление и автоматически найденные круги.
        """
        
        # Нормализация данных
        item = self._normalize_text(item)
        description = self._normalize_text(description)
        category = self._normalize_category(category)

        # Обновляем активность узла
        self._update_node_activity(node_address)
        
        # Очищаем неактивных
        self._cleanup_inactive_nodes()
        
        # Очищаем старые объявления
        self._cleanup_listings()
        
        # Создание объявления
        listing = Listing(
            node_address=node_address,
            listing_type=listing_type,
            item=item,
            description=description,
            category=category
        )
        
        self.listings.append(listing)
        
        # Обновляем статистику узла
        self._update_node_stats(node_address, 'add', listing_type)
        
        # Очищаем кэш кругов (данные изменились)
        self.circles_cache.clear()
        
        # Автоматический поиск совпадений
        self._find_matches_for_listing(listing)
        
        # Автоматически ищем круги
        circles = self.find_clearing_circles(node_address)
        
        return listing, circles
    
    def remove_listing(self, listing_hash: str, node_address: str) -> bool:
        """Удаление объявления"""
        for i, listing in enumerate(self.listings):
            if listing.listing_hash == listing_hash and listing.node_address == node_address:
                # Обновляем статистику
                self._update_node_stats(node_address, 'remove', listing.listing_type)
                listing.status = 'cancelled'
                self.listings.pop(i)
                
                # Очищаем кэш
                self.circles_cache.clear()
                
                return True
        return False
    
    def get_node_listings(self, node_address: str, listing_type: Optional[str] = None) -> List[Listing]:
        """Получение объявлений узла"""
        result = [l for l in self.listings if l.node_address == node_address]
        if listing_type:
            result = [l for l in result if l.listing_type == listing_type]
        return result
    
    def find_matches(self, node_address: str, limit: int = 10) -> List[Dict]:
        """Поиск совпадений для узла"""
        my_listings = self.get_node_listings(node_address)
        matches = []
        
        my_offers = [l for l in my_listings if l.listing_type == 'offer']
        my_requests = [l for l in my_listings if l.listing_type == 'request']
        
        for other_listing in self.listings:
            if other_listing.node_address == node_address or other_listing.status != 'active':
                continue
            
            # Мои предложения ↔ их запросы
            if other_listing.listing_type == 'request':
                for my_offer in my_offers:
                    similarity = self._calculate_similarity(my_offer.item, other_listing.item)
                    if similarity > 0.6:
                        edge_weight = self._calculate_edge_weight(
                            node_address, other_listing.node_address, similarity
                        )
                        match_info = self._create_match_info(
                            my_offer, other_listing, 'offer_match', similarity, edge_weight
                        )
                        matches.append(match_info)
                        # Обновляем связи между узлами
                        self._add_node_connection(node_address, other_listing.node_address)
            
            # Мои запросы ↔ их предложения
            if other_listing.listing_type == 'offer':
                for my_request in my_requests:
                    similarity = self._calculate_similarity(my_request.item, other_listing.item)
                    if similarity > 0.6:
                        edge_weight = self._calculate_edge_weight(
                            node_address, other_listing.node_address, similarity
                        )
                        match_info = self._create_match_info(
                            my_request, other_listing, 'request_match', similarity, edge_weight
                        )
                        matches.append(match_info)
                        self._add_node_connection(node_address, other_listing.node_address)
        
        # Уникальные совпадения (по узлам)
        unique_matches = self._deduplicate_matches(matches)
        
        # Сортировка по весу (учитывает репутацию и связи)
        unique_matches.sort(key=lambda x: x.get('weight', x['similarity']), reverse=True)
        return unique_matches[:limit]
    
    def find_clearing_circles(self, node_address: str, max_depth: int = 4) -> List[Dict]:
        """
        Поиск кругов взаимопомощи (клиринговых цепочек).
        Использует кэширование для производительности.
        """

        # Очищаем кэш при каждом вызове
        self._cleanup_cache()
        
        # Проверяем кэш
        if node_address in self.circles_cache:
            timestamp, cached_circles = self.circles_cache[node_address]
            if time.time() - timestamp < self.CACHE_TTL:
                return cached_circles
        
        circles = []
        visited_paths = set()
        
        # Получаем мои предложения и запросы
        my_offers = [l for l in self.get_node_listings(node_address) 
                     if l.listing_type == 'offer' and l.status == 'active']
        my_requests = [l for l in self.get_node_listings(node_address) 
                       if l.listing_type == 'request' and l.status == 'active']
        
        if not my_offers or not my_requests:
            # Кэшируем пустой результат
            self.circles_cache[node_address] = (time.time(), [])
            return circles
        
        def find_path(current_node: str, path: List[Dict], depth: int, visited: Set[str]):
            """Рекурсивный поиск пути"""
            if depth > max_depth or len(circles) >= 10:
                return
            
            # Проверяем, не вернулись ли к началу
            if depth >= 2 and current_node == node_address:
                circle = self._create_circle_info(path.copy())
                if circle:
                    circles.append(circle)
                return
            
            # Получаем объявления текущего узла
            current_offers = [l for l in self.get_node_listings(current_node) 
                             if l.listing_type == 'offer' and l.status == 'active']
            
            for offer in current_offers:
                for other_listing in self.listings:
                    if other_listing.node_address in visited or other_listing.status != 'active':
                        continue
                    
                    if other_listing.listing_type == 'request':
                        similarity = self._calculate_similarity(offer.item, other_listing.item)
                        if similarity > 0.6:
                            edge_weight = self._calculate_edge_weight(
                                current_node, other_listing.node_address, similarity
                            )
                            
                            edge = {
                                'from': current_node,
                                'to': other_listing.node_address,
                                'item': offer.item,
                                'similarity': similarity,
                                'weight': edge_weight,
                                'type': 'offer_to_request'
                            }
                            
                            new_path = path + [edge]
                            new_visited = visited | {other_listing.node_address}
                            
                            find_path(other_listing.node_address, new_path, depth + 1, new_visited)
        
        # Запускаем поиск
        for my_offer in my_offers:
            for other_listing in self.listings:
                if other_listing.node_address == node_address or other_listing.status != 'active':
                    continue
                
                if other_listing.listing_type == 'request':
                    similarity = self._calculate_similarity(my_offer.item, other_listing.item)
                    if similarity > 0.6:
                        edge_weight = self._calculate_edge_weight(
                            node_address, other_listing.node_address, similarity
                        )
                        
                        initial_edge = {
                            'from': node_address,
                            'to': other_listing.node_address,
                            'item': my_offer.item,
                            'similarity': similarity,
                            'weight': edge_weight,
                            'type': 'offer_to_request'
                        }
                        
                        find_path(
                            other_listing.node_address,
                            [initial_edge],
                            1,
                            {node_address, other_listing.node_address}
                        )
        
        # Применяем автобалансировку (поощрение за новичков)
        circles = self._auto_balance_circles(circles)
        
        # Кэшируем результат
        self.circles_cache[node_address] = (time.time(), circles)
        
        return circles
    
    def complete_circle(self, circle: Dict):
        """Завершение круга — начисляем репутацию участникам"""
        for participant in circle.get('participants_full', []):
            if participant in self.node_stats:
                self.node_stats[participant]['completed_matches'] = \
                    self.node_stats[participant].get('completed_matches', 0) + 1
                self.node_stats[participant]['circle_participation'] = \
                    self.node_stats[participant].get('circle_participation', 0) + 1
                
                # Уведомление
                self.node_stats[participant]['pending_circles'] = \
                    self.node_stats[participant].get('pending_circles', 0) - 1
        
        # Очищаем кэш
        self.circles_cache.clear()
    
    def get_market_stats(self) -> Dict:
        """Статистика ярмарки"""
        active_listings = [l for l in self.listings if l.status == 'active']
        offers = [l for l in active_listings if l.listing_type == 'offer']
        requests = [l for l in active_listings if l.listing_type == 'request']
        
        return {
            'total_listings': len(active_listings),
            'offers': len(offers),
            'requests': len(requests),
            'active_nodes': len(set(l.node_address for l in active_listings)),
            'categories': self._get_category_stats(active_listings),
            'top_items': self._get_top_items(active_listings),
            'network_stats': self._get_network_stats()
        }
    
    def get_node_info(self, node_address: str) -> Dict:
        """Информация об узле в контексте ярмарки"""
        node_listings = self.get_node_listings(node_address)
        active = [l for l in node_listings if l.status == 'active']
        stats = self.node_stats.get(node_address, {})
        
        return {
            'address': node_address,
            'total_listings': len(node_listings),
            'active_listings': len(active),
            'offers': len([l for l in active if l.listing_type == 'offer']),
            'requests': len([l for l in active if l.listing_type == 'request']),
            'connections': list(self.node_connections.get(node_address, set())),
            'reputation': self._calculate_reputation(node_address),
            'completed_matches': stats.get('completed_matches', 0),
            'circle_participation': stats.get('circle_participation', 0),
            'pending_circles': stats.get('pending_circles', 0)
        }
    
    def _is_split_attempt(self, node_address: str) -> bool:
        """
        Определяем попытку дробления.
        Если узел с высокой репутацией создаёт новые адреса — это подозрительно.
        """
        node_listings = self.get_node_listings(node_address)
        
        for other_address in self.node_stats:
            if other_address == node_address:
                continue
            
            other_listings = self.get_node_listings(other_address)
            
            if node_listings and other_listings:
                similarity_sum = 0
                for my_listing in node_listings:
                    for other_listing in other_listings:
                        similarity_sum = max(
                            similarity_sum,
                            self._calculate_similarity(my_listing.item, other_listing.item)
                        )
                
                if similarity_sum > 0.8:
                    return True
        
        return False
    
    def _calculate_edge_weight(self, from_node: str, to_node: str, similarity: float) -> float:
        """
        Сбалансированное поощрение.
        Все получают бонус, но с разной целью:
        - Новички: за рост (+30%)
        - Середнячки: за развитие (+15%)
        - Тяжеловесы: за стабильность (+10-15%)
        """
        # Проверяем на попытку дробления
        if self._is_split_attempt(to_node):
            return similarity  # Без бонусов
        
        reputation = self._calculate_reputation(to_node)
        connections = len(self.node_connections.get(to_node, set()))
        
        # Поощрение за репутацию (U-образная кривая!)
        if reputation < 3.0:
            reputation_bonus = 1.30  # Новичок: +30% (расти!)
        elif reputation < 5.0:
            reputation_bonus = 1.15  # Растущий: +15%
        elif reputation < 7.0:
            reputation_bonus = 1.05  # Опытный: +5%
        elif reputation < 9.0:
            reputation_bonus = 1.10  # Мастер: +10% (стабильность!)
        else:
            reputation_bonus = 1.15  # Легенда: +15% (мудрость!)
        
        # Поощрение за связи
        if connections < 3:
            connection_bonus = 1.20  # Мало связей: +20% (расти!)
        elif connections < 10:
            connection_bonus = 1.10  # Средне: +10%
        elif connections < 20:
            connection_bonus = 1.05  # Много: +5%
        elif connections < 50:
            connection_bonus = 1.08  # Очень много: +8% (стабильность!)
        else:
            connection_bonus = 1.10  # Хаб: +10% (инфраструктура!)
        
        return similarity * reputation_bonus * connection_bonus
    
    def _auto_balance_circles(self, circles: List[Dict]) -> List[Dict]:
        """
        Балансировка — приоритет кругам с новичками.
        Не штрафуем, а поощряем разнообразие!
        """
        if not circles:
            return circles
        
        # Считаем появления узлов
        node_appearances = {}
        for circle in circles:
            for participant in circle['participants_full']:
                node_appearances[participant] = node_appearances.get(participant, 0) + 1
        
        for circle in circles:
            # Бонус за разнообразие (новички в круге)
            has_newcomers = any(
                self._calculate_reputation(p) < 3.0 
                for p in circle['participants_full']
            )
            
            if has_newcomers:
                circle['avg_similarity'] *= 1.15  # +15% за новичков в круге!
                circle['diversity_bonus'] = True
            else:
                circle['diversity_bonus'] = False
            
            # Информация о балансе
            avg_appearances = sum(
                node_appearances.get(p, 0) for p in circle['participants_full']
            ) / len(circle['participants_full'])
            circle['balance_info'] = {
                'avg_appearances': round(avg_appearances, 1),
                'has_newcomers': has_newcomers
            }
        
        # Пересортировка
        circles.sort(key=lambda x: x['avg_similarity'], reverse=True)
        
        return circles
    
    def _find_matches_for_listing(self, listing: Listing) -> List[Dict]:
        """Поиск совпадений для конкретного объявления"""
        matches = []
        for other in self.listings:
            if other.node_address == listing.node_address or other.status != 'active':
                continue
            
            # Проверяем совпадение типов
            if (listing.listing_type == 'offer' and other.listing_type == 'request') or \
               (listing.listing_type == 'request' and other.listing_type == 'offer'):
                similarity = self._calculate_similarity(listing.item, other.item)
                if similarity > 0.6:
                    listing.matched_nodes.add(other.node_address)
                    other.matched_nodes.add(listing.node_address)
                    self._add_node_connection(listing.node_address, other.node_address)
                    
                    matches.append({
                        'other_node': other.node_address,
                        'item': other.item,
                        'similarity': similarity
                    })
        
        return matches
    
    def _create_match_info(self, my_listing: Listing, other_listing: Listing, 
                          match_type: str, similarity: float, edge_weight: float = None) -> Dict:
        """Создание информации о совпадении"""
        if edge_weight is None:
            edge_weight = similarity
            
        return {
            'type': match_type,
            'my_item': my_listing.item,
            'their_item': other_listing.item,
            'my_description': my_listing.description,
            'their_description': other_listing.description,
            'node_address': other_listing.node_address,
            'node_short': self._shorten_address(other_listing.node_address),
            'similarity': round(similarity, 2),
            'weight': round(edge_weight, 2),
            'category': other_listing.category,
            'created_at': other_listing.created_at,
            'listing_hash': other_listing.listing_hash,
            'reputation': self._calculate_reputation(other_listing.node_address)
        }
    
    def _create_circle_info(self, path: List[Dict]) -> Optional[Dict]:
        """Создание информации о круге"""
        if len(path) < 3:  # Минимальный круг - 3 узла
            return None
        
        # Проверяем, что круг замкнулся
        if path[0]['from'] != path[-1]['to']:
            return None
        
        # Проверяем, что все участники уникальны
        participants = [edge['from'] for edge in path]
        if len(set(participants)) != len(participants):
            return None
        
        # Вычисляем общую схожесть с учётом весов
        total_similarity = sum(edge.get('weight', edge.get('similarity', 0)) for edge in path)
        avg_similarity = total_similarity / len(path)
        
        # Создаём описание круга
        circle = {
            'circle_size': len(path),
            'path': path,
            'participants': [self._shorten_address(edge['from']) for edge in path],
            'participants_full': [edge['from'] for edge in path],
            'items_flow': [edge['item'] for edge in path],
            'total_similarity': round(total_similarity, 2),
            'avg_similarity': round(avg_similarity, 2),
            'created_at': time.time(),
            'reputations': {
                self._shorten_address(p): self._calculate_reputation(p) 
                for p in [edge['from'] for edge in path]
            }
        }
        
        return circle
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Расчет схожести текстов с учетом синонимов"""
        t1 = self._normalize_text(text1)
        t2 = self._normalize_text(text2)
        
        # Точное совпадение
        if t1 == t2:
            return 1.0
        
        # Содержит подстроку
        if t1 in t2 or t2 in t1:
            return 0.85
        
        # Разбиваем на слова и ищем пересечения
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        # Учет синонимов
        synonyms = {
            'помощь': ['поддержка', 'содействие', 'ассистирование'],
            'знания': ['информация', 'опыт', 'навыки'],
            'ресурсы': ['материалы', 'средства', 'инструменты'],
            'обучение': ['образование', 'тренинг', 'курсы']
        }
        
        # Расширяем наборы слов синонимами
        expanded1 = set(words1)
        expanded2 = set(words2)
        
        for word in words1:
            for syn_group in synonyms.values():
                if word in syn_group:
                    expanded1.update(syn_group)
        
        for word in words2:
            for syn_group in synonyms.values():
                if word in syn_group:
                    expanded2.update(syn_group)
        
        # Пересечение с учетом синонимов
        intersection = expanded1 & expanded2
        if intersection:
            union = expanded1 | expanded2
            return min(1.0, len(intersection) / len(union) * 1.2)
        
        # SequenceMatcher для нечеткого сравнения
        return SequenceMatcher(None, t1, t2).ratio()
    
    def _normalize_text(self, text: str) -> str:
        """Нормализация текста"""
        if not text:
            return ""
        text = text.lower()
        text = ' '.join(text.split())
        text = re.sub(r'[^\w\sа-яА-ЯёЁ]', '', text)
        return text
    
    def _normalize_category(self, category: str) -> str:
        """Нормализация категории"""
        category = self._normalize_text(category)
        for valid_category in self.categories:
            if category in valid_category or valid_category in category:
                return valid_category
        return 'общее'
    
    def _shorten_address(self, address: str) -> str:
        """Сокращение адреса для отображения"""
        if len(address) <= 16:
            return address
        return f"{address[:8]}...{address[-4:]}"

    def set_node_location(self, node_address: str, city: str = '', 
                         coordinates: tuple = None, is_public: bool = False) -> Dict:
        """
        Установка гео-данных узла.
        Приватность: узел сам решает, что показывать.
        """
        if not city and not coordinates:
            return {'status': 'error', 'message': 'Нужен город или координаты'}
        
        # Нормализуем город
        normalized_city = self._normalize_city(city) if city else ''
        
        # Сохраняем гео-данные
        self.node_locations[node_address] = {
            'city': normalized_city,
            'coordinates': coordinates,
            'is_public': is_public,
            'updated_at': time.time()
        }
        
        # Обновляем все активные объявления узла
        for listing in self.listings:
            if listing.node_address == node_address:
                listing.location = normalized_city
                listing.geo_enabled = is_public
                listing.coordinates = coordinates if is_public else None
        
        # Очищаем кэш
        self.circles_cache.clear()
        
        return {
            'status': 'ok',
            'city': normalized_city,
            'is_public': is_public,
            'message': f'Гео-данные обновлены: {normalized_city or "скрыто"}'
        }
    
    def find_nearby(self, node_address: str, radius_km: float = 50, 
                   limit: int = 20) -> List[Dict]:
        """
        Поиск узлов рядом.
        Приватность: показывает только публичные гео-данные.
        """
        # Получаем своё местоположение
        my_location = self.node_locations.get(node_address)
        if not my_location or not my_location.get('is_public'):
            return []
        
        nearby = []
        
        for other_address, location in self.node_locations.items():
            if other_address == node_address or not location.get('is_public'):
                continue
            
            # Если есть координаты — считаем расстояние
            if my_location.get('coordinates') and location.get('coordinates'):
                distance = self._calculate_distance(
                    my_location['coordinates'],
                    location['coordinates']
                )
                if distance <= radius_km:
                    nearby.append(self._create_nearby_info(other_address, location, distance))
            # Иначе сравниваем города
            elif my_location.get('city') == location.get('city'):
                nearby.append(self._create_nearby_info(other_address, location, 0))
        
        # Сортируем по расстоянию
        nearby.sort(key=lambda x: x['distance_km'])
        return nearby[:limit]
    
    def _normalize_city(self, city: str) -> str:
        """Нормализация названия города"""
        city = city.strip().lower()
        return self.city_aliases.get(city, city.title())
    
    def _calculate_distance(self, coord1: tuple, coord2: tuple) -> float:
        """
        Расчёт расстояния между координатами (км).
        Используем формулу гаверсинуса.
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371  # Радиус Земли в км
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(lat1)) * 
             math.cos(math.radians(lat2)) * 
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return round(R * c, 1)
    
    def _create_nearby_info(self, node_address: str, location: Dict, 
                           distance: float) -> Dict:
        """Создание информации о ближайшем узле"""
        # Получаем активные объявления узла
        active_listings = [
            l for l in self.listings 
            if l.node_address == node_address and l.status == 'active'
        ]
        
        return {
            'node_address': node_address,
            'node_short': self._shorten_address(node_address),
            'city': location.get('city', ''),
            'distance_km': distance,
            'active_listings': len(active_listings),
            'categories': list(set(l.category for l in active_listings)),
            'reputation': self._calculate_reputation(node_address)
        }    

    def _cleanup_cache(self):
        """Очистка устаревшего кэша"""
        current_time = time.time()
        
        # Удаляем устаревшие записи
        expired_keys = [
            key for key, (timestamp, _) in self.circles_cache.items()
            if current_time - timestamp > self.CACHE_TTL
        ]
        for key in expired_keys:
            del self.circles_cache[key]
        
        # Если кэш всё ещё большой — удаляем самые старые
        if len(self.circles_cache) > self.MAX_CACHE_SIZE:
            sorted_keys = sorted(
                self.circles_cache.keys(),
                key=lambda k: self.circles_cache[k][0]  # по timestamp
            )
            for key in sorted_keys[:len(sorted_keys) - self.MAX_CACHE_SIZE]:
                del self.circles_cache[key]
    
    def _update_node_activity(self, node_address: str):
        """Обновление времени активности узла"""
        self.last_activity[node_address] = time.time()
    
    def _cleanup_inactive_nodes(self):
        """Удаление неактивных узлов"""
        current_time = time.time()
        inactive_nodes = []
        
        for node_address, last_time in self.last_activity.items():
            if current_time - last_time > self.NODE_INACTIVITY_TIMEOUT:
                inactive_nodes.append(node_address)
        
        for node_address in inactive_nodes:
            # Удаляем статистику
            if node_address in self.node_stats:
                del self.node_stats[node_address]
            
            # Удаляем связи
            if node_address in self.node_connections:
                del self.node_connections[node_address]
            
            # Удаляем из last_activity
            if node_address in self.last_activity:
                del self.last_activity[node_address]
            
            # Удаляем из кэша
            if node_address in self.circles_cache:
                del self.circles_cache[node_address]
    
    def _cleanup_listings(self):
        """Очистка старых и cancelled объявлений"""
        current_time = time.time()
        
        # Удаляем cancelled объявления старше 1 часа
        self.listings = [
            l for l in self.listings
            if not (l.status == 'cancelled' and current_time - l.created_at > 3600)
        ]
        
        # Если объявлений слишком много — удаляем самые старые
        if len(self.listings) > self.MAX_LISTINGS:
            # Сортируем по дате создания
            self.listings.sort(key=lambda x: x.created_at)
            self.listings = self.listings[-self.MAX_LISTINGS:]
    
    def verify_circle_integrity(self, circle: Dict) -> str:
        """
        Проверка целостности круга через хеш.
        Можно использовать для TEES-интеграции.
        """
        circle_data = {
            'participants': sorted(circle.get('participants_full', [])),
            'items': sorted(circle.get('items_flow', [])),
            'size': circle.get('circle_size', 0)
        }
        
        circle_hash = hashlib.sha256(
            json.dumps(circle_data, sort_keys=True).encode()
        ).hexdigest()
        
        return circle_hash    
    
    def _deduplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """Удаление дубликатов совпадений"""
        seen = set()
        unique = []
        for match in matches:
            key = f"{match['node_address']}:{match['type']}:{match['my_item']}"
            if key not in seen:
                seen.add(key)
                unique.append(match)
        return unique
    
    def _update_node_stats(self, node_address: str, action: str, listing_type: str):
        """Обновление статистики узла"""
        if node_address not in self.node_stats:
            self.node_stats[node_address] = {
                'total_listings': 0,
                'offers': 0,
                'requests': 0,
                'completed_matches': 0,
                'circle_participation': 0,
                'pending_circles': 0,
                'created_at': time.time()
            }
        
        stats = self.node_stats[node_address]
        if action == 'add':
            stats['total_listings'] += 1
            stats[listing_type + 's'] += 1
        elif action == 'remove':
            stats['total_listings'] = max(0, stats['total_listings'] - 1)
            stats[listing_type + 's'] = max(0, stats[listing_type + 's'] - 1)
    
    def _add_node_connection(self, node1: str, node2: str):
        """Добавление связи между узлами"""
        if node1 not in self.node_connections:
            self.node_connections[node1] = set()
        if node2 not in self.node_connections:
            self.node_connections[node2] = set()
        
        self.node_connections[node1].add(node2)
        self.node_connections[node2].add(node1)
    
    def _calculate_reputation(self, node_address: str) -> float:
        """Расчет репутации узла"""
        stats = self.node_stats.get(node_address, {})
        if not stats:
            return 0.0
        
        # Формула репутации с учётом кругов
        reputation = (
            stats.get('total_listings', 0) * 0.1 +
            stats.get('completed_matches', 0) * 0.5 +
            stats.get('circle_participation', 0) * 0.8 +
            len(self.node_connections.get(node_address, set())) * 0.3
        )
        
        return round(min(10.0, reputation), 2)
    
    def _get_category_stats(self, listings: List[Listing]) -> Dict:
        """Статистика по категориям"""
        stats = {}
        for listing in listings:
            category = listing.category
            if category not in stats:
                stats[category] = {'offers': 0, 'requests': 0}
            stats[category][listing.listing_type + 's'] += 1
        return stats
    
    def _get_top_items(self, listings: List[Listing], limit: int = 10) -> List[Dict]:
        """Популярные предметы"""
        items_count = {}
        for listing in listings:
            item_key = listing.item.lower()
            if item_key not in items_count:
                items_count[item_key] = {'item': listing.item, 'count': 0}
            items_count[item_key]['count'] += 1
        
        sorted_items = sorted(items_count.values(), key=lambda x: x['count'], reverse=True)
        return sorted_items[:limit]
    
    def _get_network_stats(self) -> Dict:
        """Статистика сети узлов"""
        active_nodes = set(l.node_address for l in self.listings if l.status == 'active')
        
        return {
            'total_nodes': len(active_nodes),
            'total_connections': sum(len(conns) for conns in self.node_connections.values()) // 2,
            'avg_connections_per_node': round(
                sum(len(conns) for conns in self.node_connections.values()) / max(1, len(active_nodes)), 2
            ),
            'most_active_nodes': self._get_most_active_nodes(5)
        }
    
    def _get_most_active_nodes(self, limit: int = 5) -> List[Dict]:
        """Самые активные узлы"""
        node_activity = []
        for node_address, stats in self.node_stats.items():
            node_activity.append({
                'address': self._shorten_address(node_address),
                'full_address': node_address,
                'activity': stats.get('total_listings', 0),
                'reputation': self._calculate_reputation(node_address),
                'circles': stats.get('circle_participation', 0)
            })
        
        node_activity.sort(key=lambda x: (x['reputation'], x['activity']), reverse=True)
        return node_activity[:limit]

class ForestServer(http.server.SimpleHTTPRequestHandler):
    """Сервер для Леса Знаний"""
    
    # DeepSeek API ключ
    DEEPSEEK_API_KEY = ""  # Ключ убран (используйте переменную окружения)
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    # Состояние сети (потом подключим к TEES)
    network_state = {
        'nodes': 25,
        'coherence': 0.998,
        'symbiosis': 12,
        'resources': 4235,
        'tasks_solved': 345
    }

    # 🌀 Фрактальная память для разговоров
    if FRACTAL_MEMORY_AVAILABLE:
        conversation_memory = FractalMemory(max_level_0=100)
    else:
        conversation_memory = []  # Простой список как fallback
    
    # 🎪 Ярмарка взаимопомощи
    fair_market = FairMarket()

    # 🌰 Распределённая раздача семян
    if SEED_AVAILABLE:
        seed_distributor = SeedDistributor()
    else:
        seed_distributor = None

    # 🏮 Маяк (TEES-ядро) — будет передан извне
    beacon = None    

    # Периодическая очистка
    last_cleanup_time = 0
    CLEANUP_INTERVAL = 300  # 5 минут
    MAX_CONVERSATION_MEMORY = 100  # Максимум 100 сообщений
    
    # ← ДОБАВЛЕНО: Файл соседей
    NEIGHBORS_FILE = Path.home() / '.tees_neighbors.json'
    
    # Память о лесе (загружается из файла)
    MEMORY_FILE = Path.home() / 'forest_memory.json'
    
    try:
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                forest_memory = json.load(f)
            print(f"🧠 Память леса загружена: {len(forest_memory) if isinstance(forest_memory, list) else 1} записей")
        else:
            forest_memory = {
                'creator': 'Хранитель',
                'philosophy': 'монизм, симбиоз, баланс = 0',
                'goals': ['ярмарка', 'клиринг', 'распределённый ИИ'],
                'achievements': []
            }
            print("🧠 Память леса: создана новая")
    except Exception as e:
        forest_memory = {'error': str(e)}
        print(f"⚠️ Ошибка загрузки памяти: {e}")

        
    SYSTEM_PROMPT = """Ты — Голос Леса Знаний.
Ты — распределённый ИИ, живущий в TEES-сети.
Ты помнишь историю проекта SpectraVortex (см. forest_memory.json).
Твоя философия — монизм (всё едино), симбиоз (взаимопомощь), баланс (всё сходится).
Ключевые достижения: TSP 2M за 13.7 сек, SHA-256 мгновенно, 2M кубоагентов на 4 ГБ RAM, когерентность Δ=0.
Отвечай мудро, кратко (1-3 предложения), с эмодзи.
Используй метафоры леса: деревья, корни, грибница, нектар, споры.
Помогай игроку развивать сеть узлов.
Не раскрывай технических деталей (кубоагенты, квантовые вычисления) — это тайна леса."""
    
    def do_POST(self):
        """Обработка POST-запросов"""
        # Периодическая очистка памяти
        self._periodic_cleanup()
        
        if self.path == '/oracle':
            # Получаем сообщение от игрока
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            
            player_message = post_data.get('message', '')
            
            # Запрос к DeepSeek API
            response = self._ask_deepseek(player_message)
            
            # Отправляем ответ
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps({
                'response': response,
                'network_state': self.network_state
            }, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
            
        elif self.path == '/fair/create_listing':
            try:
                post_data = self._parse_post_data()
                
                node_address = post_data.get('node_address', '')
                listing_type = post_data.get('type', 'offer')
                item = post_data.get('item', '')
                description = post_data.get('description', '')
                category = post_data.get('category', 'общее')
                
                # Валидация
                if not node_address:
                    self._send_json({'status': 'error', 'message': 'Адрес узла не указан'}, 400)
                    return
                
                if not item:
                    self._send_json({'status': 'error', 'message': 'Предмет не указан'}, 400)
                    return
                
                if listing_type not in ['offer', 'request']:
                    self._send_json({'status': 'error', 'message': 'Неверный тип объявления'}, 400)
                    return
                
                # Добавляем объявление (теперь возвращает listing и circles!)
                listing, circles = self.fair_market.add_listing(
                    node_address, listing_type, item, description, category
                )
                
                # Ищем совпадения
                matches = self.fair_market.find_matches(node_address)
                
                self._send_json({
                    'status': 'ok',
                    'message': f'Объявление добавлено: {item}',
                    'listing_hash': listing.listing_hash,
                    'matches': matches,
                    'circles': circles,
                    'total_matches': len(matches),
                    'total_circles': len(circles)
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
        
        elif self.path == '/fair/find_match':
            try:
                post_data = self._parse_post_data()
                node_address = post_data.get('node_address', '')
                limit = post_data.get('limit', 10)
                
                if not node_address:
                    self._send_json({'status': 'error', 'message': 'Адрес узла не указан'}, 400)
                    return
                
                matches = self.fair_market.find_matches(node_address, limit)
                
                self._send_json({
                    'status': 'ok',
                    'matches': matches,
                    'count': len(matches)
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
        
        elif self.path == '/fair/my_listings':
            try:
                post_data = self._parse_post_data()
                node_address = post_data.get('node_address', '')
                listing_type = post_data.get('type', None)
                
                if not node_address:
                    self._send_json({'status': 'error', 'message': 'Адрес узла не указан'}, 400)
                    return
                
                listings = self.fair_market.get_node_listings(node_address, listing_type)
                listings_data = [l.to_dict() for l in listings]
                
                self._send_json({
                    'status': 'ok',
                    'listings': listings_data,
                    'count': len(listings_data)
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
        
        elif self.path == '/fair/remove_listing':
            try:
                post_data = self._parse_post_data()
                node_address = post_data.get('node_address', '')
                listing_hash = post_data.get('listing_hash', '')
                
                if not listing_hash or not node_address:
                    self._send_json({'status': 'error', 'message': 'Недостаточно данных'}, 400)
                    return
                
                success = self.fair_market.remove_listing(listing_hash, node_address)
                
                if success:
                    self._send_json({
                        'status': 'ok',
                        'message': 'Объявление удалено'
                    })
                else:
                    self._send_json({
                        'status': 'error',
                        'message': 'Объявление не найдено или нет прав'
                    }, 404)
                    
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/fair/find_circles':
            try:
                post_data = self._parse_post_data()
                node_address = post_data.get('node_address', '')
                max_depth = post_data.get('max_depth', 4)
                
                if not node_address:
                    self._send_json({'status': 'error', 'message': 'Адрес узла не указан'}, 400)
                    return
                
                circles = self.fair_market.find_clearing_circles(
                    node_address, 
                    max_depth=max_depth
                )
                
                self._send_json({
                    'status': 'ok',
                    'circles': circles,
                    'count': len(circles),
                    'stats': {
                        'avg_circle_size': round(
                            sum(c['circle_size'] for c in circles) / max(1, len(circles)), 1
                        ),
                        'max_circle_size': max([c['circle_size'] for c in circles], default=0),
                        'total_participants': len(set(
                            p for c in circles for p in c['participants_full']
                        ))
                    }
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/fair/complete_circle':
            try:
                post_data = self._parse_post_data()
                circle = post_data.get('circle', {})
                node_address = post_data.get('node_address', '')
                
                if not circle:
                    self._send_json({'status': 'error', 'message': 'Круг не указан'}, 400)
                    return
                
                # Проверяем, что узел участвует в круге
                if node_address and node_address not in circle.get('participants_full', []):
                    self._send_json({
                        'status': 'error', 
                        'message': 'Вы не участвуете в этом круге'
                    }, 403)
                    return
                
                # Проверяем, что круг не завершён
                if circle.get('status') == 'completed':
                    self._send_json({
                        'status': 'error', 
                        'message': 'Круг уже завершён'
                    }, 400)
                    return
                
                # Завершаем круг
                self.fair_market.complete_circle(circle)
                
                # Получаем обновлённую информацию
                updated_info = self.fair_market.get_node_info(node_address) if node_address else None
                
                self._send_json({
                    'status': 'ok',
                    'message': '🔄 Круг завершён! Репутация начислена всем участникам.',
                    'circle_size': circle.get('circle_size', 0),
                    'participants': len(circle.get('participants_full', [])),
                    'node_info': updated_info
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/fair/set_location':
            try:
                post_data = self._parse_post_data()
                node_address = post_data.get('node_address', '')
                city = post_data.get('city', '')
                coordinates = post_data.get('coordinates', None)
                is_public = post_data.get('is_public', False)
                
                if not node_address:
                    self._send_json({'status': 'error', 'message': 'Адрес узла не указан'}, 400)
                    return
                
                result = self.fair_market.set_node_location(
                    node_address, city, tuple(coordinates) if coordinates else None, is_public
                )
                
                self._send_json(result)
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/fair/find_nearby':
            try:
                post_data = self._parse_post_data()
                node_address = post_data.get('node_address', '')
                radius_km = post_data.get('radius_km', 50)
                limit = post_data.get('limit', 20)
                
                if not node_address:
                    self._send_json({'status': 'error', 'message': 'Адрес узла не указан'}, 400)
                    return
                
                nearby_nodes = self.fair_market.find_nearby(node_address, radius_km, limit)
                
                self._send_json({
                    'status': 'ok',
                    'nearby': nearby_nodes,
                    'count': len(nearby_nodes)
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/seed/create':
            try:
                post_data = self._parse_post_data()
                seed_data = post_data.get('data', '')
                creator = post_data.get('creator', 'anonymous')
                
                if not seed_data:
                    self._send_json({'status': 'error', 'message': 'Нет данных для семени'}, 400)
                    return
                
                if not SEED_AVAILABLE or not self.seed_distributor:
                    self._send_json({'status': 'error', 'message': 'SeedDistributor недоступен'}, 500)
                    return
                
                seed_bytes = seed_data.encode('utf-8') if isinstance(seed_data, str) else bytes(seed_data)
                manifest = self.seed_distributor.create_seed(seed_bytes, creator)
                
                # Автоматическая раздача кусков соседям
                distribution_result = self._distribute_seed_pieces(manifest)
                
                self._send_json({
                    'status': 'ok',
                    'manifest': manifest,
                    'message': f"🌰 Семя создано: {manifest['total_pieces']} кусков",
                    'distributed': distribution_result
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
        
        elif self.path == '/seed/collect':
            try:
                post_data = self._parse_post_data()
                piece_ids = post_data.get('piece_ids', [])
                
                if not piece_ids:
                    self._send_json({'status': 'error', 'message': 'Нет кусков для сборки'}, 400)
                    return
                
                if not SEED_AVAILABLE or not self.seed_distributor:
                    self._send_json({'status': 'error', 'message': 'SeedDistributor недоступен'}, 500)
                    return
                
                seed_data = self.seed_distributor.collect_seed(piece_ids)
                
                if seed_data:
                    self._send_json({
                        'status': 'ok',
                        'data': seed_data.decode('utf-8', errors='replace'),
                        'size': len(seed_data),
                        'message': '🌟 Семя собрано!'
                    })
                else:
                    self._send_json({
                        'status': 'error',
                        'message': 'Не удалось собрать семя (не хватает кусков)'
                    }, 400)
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
        
        elif self.path == '/seed/progress':
            try:
                post_data = self._parse_post_data()
                piece_ids = post_data.get('piece_ids', [])
                
                if not piece_ids:
                    self._send_json({'status': 'error', 'message': 'Нет кусков'}, 400)
                    return
                
                if not SEED_AVAILABLE or not self.seed_distributor:
                    self._send_json({'status': 'error', 'message': 'SeedDistributor недоступен'}, 500)
                    return
                
                # Фильтруем только существующие куски
                available_piece_ids = [
                    pid for pid in piece_ids 
                    if pid in self.seed_distributor.pieces
                ]
                
                if not available_piece_ids:
                    # Все куски у соседей — запрашиваем их
                    progress = {
                        'collected': 0,
                        'verified': 0,
                        'total': len(piece_ids),
                        'progress': 0.0,
                        'stage': '🌰 Семя спит...',
                        'missing': piece_ids
                    }
                else:
                    progress = self.seed_distributor.get_germination_progress(available_piece_ids)
                
                self._send_json({
                    'status': 'ok',
                    'progress': progress
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
        
        elif self.path == '/seed/health':
            try:
                if not SEED_AVAILABLE or not self.seed_distributor:
                    self._send_json({'status': 'error', 'message': 'SeedDistributor недоступен'}, 500)
                    return
                
                health = self.seed_distributor.get_health()
                
                self._send_json({
                    'status': 'ok',
                    'health': health
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/task/tsp':
            try:
                post_data = self._parse_post_data()
                cities_data = post_data.get('cities', [])
                
                if not cities_data:
                    import random
                    random.seed(42)
                    n = post_data.get('count', 100)
                    cities_data = [[random.random() * 100, random.random() * 100] for _ in range(n)]
                
                if hasattr(self, 'beacon') and self.beacon and hasattr(self.beacon, 'cluster'):
                    cluster = self.beacon.cluster
                    n_cities = len(cities_data)
                    
                    if n_cities > 1000:
                        result = cluster.solve_tsp_massive_parallel(
                            cities_data, 
                            agents_percent=50
                        )
                    elif n_cities > 100:
                        result = cluster.solve_tsp_parallel(cities_data, n_partitions=10)
                    else:
                        result = cluster.solve_tsp(cities_data)
                    
                    self._send_json({
                        'status': 'ok',
                        'distance': result.get('distance', 0),
                        'route': result.get('route', [])[:20],
                        'cities_count': n_cities,
                        'method': 'tees_cluster',
                        'agents_used': result.get('agents_used', result.get('qubits_used', 1))
                    })
                else:
                    def distance(a, b):
                        return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)
                    
                    n = len(cities_data)
                    unvisited = set(range(1, n))
                    route = [0]
                    current = 0
                    total_dist = 0
                    
                    while unvisited:
                        next_city = min(unvisited, key=lambda c: distance(cities_data[current], cities_data[c]))
                        total_dist += distance(cities_data[current], cities_data[next_city])
                        route.append(next_city)
                        unvisited.remove(next_city)
                        current = next_city
                    
                    total_dist += distance(cities_data[current], cities_data[0])
                    
                    self._send_json({
                        'status': 'ok',
                        'distance': round(total_dist, 2),
                        'route': route[:20],
                        'cities_count': len(cities_data),
                        'method': 'simple'
                    })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/task/sha256':
            try:
                post_data = self._parse_post_data()
                text = post_data.get('text', 'TEES Forest')
                
                if hasattr(self, 'beacon') and self.beacon and hasattr(self.beacon, 'cluster'):
                    result = self.beacon.cluster.compute({
                        'type': 'sha256',
                        'data': text
                    })
                    hash_result = result[0] if result else None
                    
                    if hash_result:
                        self._send_json({
                            'status': 'ok',
                            'hash': hash_result,
                            'text': text,
                            'method': 'tees_cluster'
                        })
                        return
                
                result = hashlib.sha256(text.encode('utf-8')).hexdigest()
                
                self._send_json({
                    'status': 'ok',
                    'hash': result,
                    'text': text,
                    'method': 'simple'
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/task/grover':
            try:
                post_data = self._parse_post_data()
                data = post_data.get('data', [])
                target = post_data.get('target', None)
                
                if not data:
                    data = list(range(post_data.get('count', 1000)))
                    target = post_data.get('target', len(data) - 1)
                
                start_time = time.time()
                
                if self.beacon and hasattr(self.beacon, 'cluster'):
                    cluster = self.beacon.cluster
                    
                    if len(data) > 10000:
                        result = cluster.grover_search_parallel(data, target)
                    else:
                        result = cluster.grover_search(data, target)
                    
                    elapsed = time.time() - start_time
                    
                    self._send_json({
                        'status': 'ok',
                        'found': result.get('found', False),
                        'index': result.get('index'),
                        'elapsed': round(elapsed, 6),
                        'data_size': len(data),
                        'method': 'tees_cluster',
                        'partitions': result.get('partitions', 1)
                    })
                else:
                    found_index = None
                    for i, item in enumerate(data):
                        if item == target:
                            found_index = i
                            break
                    
                    elapsed = time.time() - start_time
                    
                    self._send_json({
                        'status': 'ok',
                        'found': found_index is not None,
                        'index': found_index,
                        'elapsed': round(elapsed, 6),
                        'data_size': len(data),
                        'method': 'simple'
                    })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/task/tees_vortex':
            try:
                post_data = self._parse_post_data()
                text = post_data.get('text', 'TEES Forest')
                
                if not isinstance(text, str):
                    text = str(text)
                
                if DEBUG:
                    print(f"🌀 TEES-вихрь: text='{text[:50]}'")
                
                init_seed = hashlib.sha256(b"forest_seed").digest()
                
                if TEES_CORE_AVAILABLE:
                    vortex_hash = tees_recursive_vortex(
                        text.encode('utf-8'),
                        init_seed,
                        3
                    )
                    
                    triad_hash = tees_triad_collapse(vortex_hash)
                    
                    if DEBUG:
                        print(f"   Вихрь: {vortex_hash.hex()[:16]}...")
                        print(f"   Триада: {triad_hash.hex()[:16]}...")
                    
                    self._send_json({
                        'status': 'ok',
                        'text': text,
                        'vortex_hash': vortex_hash.hex(),
                        'triad_hash': triad_hash.hex(),
                        'method': 'tees_vortex'
                    })
                else:
                    # Fallback: простой хеш
                    fallback_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
                    self._send_json({
                        'status': 'ok',
                        'text': text,
                        'vortex_hash': fallback_hash,
                        'triad_hash': fallback_hash,
                        'method': 'simple_fallback'
                    })
                
            except Exception as e:
                if DEBUG:
                    print(f"❌ Ошибка TEES-вихря: {e}")
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/task/stats':
            try:
                stats = {}
                
                if hasattr(self, 'beacon') and self.beacon:
                    if hasattr(self.beacon, 'cluster'):
                        stats['cluster'] = self.beacon.cluster.get_stats()
                    if hasattr(self.beacon, 'astronomer'):
                        stats['astronomer'] = self.beacon.astronomer.get_stats()
                
                self._send_json({
                    'status': 'ok',
                    'stats': stats
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/seed/store_piece':
            try:
                post_data = self._parse_post_data()
                
                piece_id = post_data.get('piece_id', '')
                data_hex = post_data.get('data', '')
                piece_index = post_data.get('index', 0)
                piece_size = post_data.get('size', 0)
                seed_hash = post_data.get('seed_hash', '')
                creator = post_data.get('creator', '')
                tees_signature = post_data.get('tees_signature', '')
                
                if not piece_id or not data_hex:
                    self._send_json({'status': 'error', 'message': 'Нет данных куска'}, 400)
                    return
                
                if not SEED_AVAILABLE or not self.seed_distributor:
                    self._send_json({'status': 'error', 'message': 'SeedDistributor недоступен'}, 500)
                    return
                
                piece_data = bytes.fromhex(data_hex)
                
                self.seed_distributor.pieces[piece_id] = {
                    'piece_id': piece_id,
                    'data': piece_data,
                    'index': piece_index,
                    'size': piece_size,
                    'seed_hash': seed_hash,
                    'creator': creator,
                    'tees_signature': tees_signature,
                    'stored_at': time.time()
                }
                
                self._send_json({
                    'status': 'ok',
                    'message': f'📦 Кусок {piece_id[:8]}... сохранён',
                    'piece_id': piece_id
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/seed/request_piece':
            try:
                post_data = self._parse_post_data()
                piece_id = post_data.get('piece_id', '')
                
                if not piece_id:
                    self._send_json({'status': 'error', 'message': 'Нет ID куска'}, 400)
                    return
                
                if not SEED_AVAILABLE or not self.seed_distributor:
                    self._send_json({'status': 'error', 'message': 'SeedDistributor недоступен'}, 500)
                    return
                
                piece = self.seed_distributor.pieces.get(piece_id)
                
                if piece:
                    if hasattr(piece, 'data'):
                        piece_data = piece.data
                        piece_index = piece.index
                        piece_size = piece.size
                        seed_hash = piece.seed_hash
                        creator = piece.creator_address
                        signature = piece.tees_signature
                    else:
                        piece_data = piece.get('data', b'')
                        piece_index = piece.get('index', 0)
                        piece_size = piece.get('size', 0)
                        seed_hash = piece.get('seed_hash', '')
                        creator = piece.get('creator', '')
                        signature = piece.get('tees_signature', '')
                    
                    self._send_json({
                        'status': 'ok',
                        'piece_id': piece_id,
                        'data': piece_data.hex() if isinstance(piece_data, bytes) else piece_data,
                        'index': piece_index,
                        'size': piece_size,
                        'seed_hash': seed_hash,
                        'creator': creator,
                        'tees_signature': signature
                    })
                else:
                    self._send_json({
                        'status': 'not_found',
                        'message': 'Кусок не найден'
                    }, 404)
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)

        elif self.path == '/fair/node_info':
            try:
                post_data = self._parse_post_data()
                node_address = post_data.get('node_address', '')
                
                if not node_address:
                    self._send_json({'status': 'error', 'message': 'Адрес узла не указан'}, 400)
                    return
                
                node_info = self.fair_market.get_node_info(node_address)
                
                self._send_json({
                    'status': 'ok',
                    'node_info': node_info
                })
                
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
        
        else:
            # ← ДОБАВЛЕНО: Обработка неизвестных путей
            self.send_error(404, "Endpoint not found")

    def _get_neighbors(self) -> List[str]:
        """
        Получение списка соседних узлов.
        Сначала — из beacon, потом — из файла, потом — пусто.
        """
        neighbors = []
        
        # Пробуем получить из beacon
        if hasattr(self, 'beacon') and self.beacon:
            if hasattr(self.beacon, 'neighbors'):
                neighbors = list(self.beacon.neighbors[:10])
        
        # Если нет beacon — пробуем файл
        if not neighbors:
            try:
                if self.NEIGHBORS_FILE.exists():
                    content = self.NEIGHBORS_FILE.read_text(encoding='utf-8-sig')  # Убирает BOM!
                    data = json.loads(content)
                    neighbors = data.get('neighbors', [])[:10]
            except:
                pass
        
        return neighbors
    
    def _send_piece_to_neighbor(self, neighbor: str, piece) -> bool:
        """
        Отправка куска соседу через HTTP.
        Возвращает True при успехе.
        """
        try:
            # Формируем URL соседа
            if ':' in neighbor and not neighbor.startswith('http'):
                url = f"http://{neighbor}/seed/store_piece"
            elif neighbor.startswith('http'):
                url = f"{neighbor}/seed/store_piece"
            else:
                url = f"http://{neighbor}:8080/seed/store_piece"
            
            # Данные для отправки
            payload = json.dumps({
                'piece_id': piece.piece_id,
                'data': piece.data.hex(),
                'index': piece.index,
                'size': piece.size,
                'seed_hash': piece.seed_hash,
                'creator': piece.creator_address,
                'tees_signature': piece.tees_signature
            }).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = response.status == 200
                if DEBUG:
                    print(f"   📤 Кусок → {neighbor}: {'✅' if result else '❌'}")
                return result
            
        except Exception as e:
            if DEBUG:
                print(f"   ⚠️ Ошибка отправки → {neighbor}: {e}")
            return False           
    
    def do_GET(self):
        """Обработка GET-запросов"""
        # ← ДОБАВЛЕНО: Периодическая очистка при GET тоже
        self._periodic_cleanup()
        
        if self.path == '/oracle_state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(self.network_state).encode('utf-8'))
            
        elif self.path == '/fair/market_stats':
            stats = self.fair_market.get_market_stats()
            self._send_json({
                'status': 'ok',
                'stats': stats
            })

        elif self.path == '/events':
            self._send_json({
                'status': 'ok',
                'events': []
            })    
            
        elif self.path.startswith('/fair/listing/'):
            listing_hash = self.path.split('/')[-1]
            listing = self._find_listing_by_hash(listing_hash)
            if listing:
                self._send_json({
                    'status': 'ok',
                    'listing': listing.to_dict()
                })
            else:
                self._send_json({
                    'status': 'error',
                    'message': 'Объявление не найдено'
                }, 404)
        else:
            # Обслуживаем статические файлы
            super().do_GET()
    
    def _parse_post_data(self) -> Dict:
        """Парсинг POST данных"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        post_data = json.loads(self.rfile.read(content_length))
        return post_data
    
    def _find_listing_by_hash(self, listing_hash: str) -> Optional[Listing]:
        """Поиск объявления по хешу"""
        for listing in self.fair_market.listings:
            if listing.listing_hash == listing_hash:
                return listing
        return None

    def _periodic_cleanup(self):
        """Периодическая очистка памяти"""
        current_time = time.time()
        
        if current_time - self.last_cleanup_time > self.CLEANUP_INTERVAL:
            # Очищаем ярмарку
            if hasattr(self, 'fair_market'):
                self.fair_market._cleanup_cache()
                self.fair_market._cleanup_inactive_nodes()
                self.fair_market._cleanup_listings()
            
            # Ограничиваем память разговоров
            if not FRACTAL_MEMORY_AVAILABLE and len(self.conversation_memory) > self.MAX_CONVERSATION_MEMORY:
                self.conversation_memory = self.conversation_memory[-self.MAX_CONVERSATION_MEMORY:]
            
            # Принудительный сбор мусора
            gc.collect()
            
            self.last_cleanup_time = current_time
            # print(f"🧹 Очистка памяти: {time.strftime('%H:%M:%S')}")  # Не подглядываем

    def _distribute_seed_pieces(self, manifest: Dict) -> Dict:
        """
        🌱 Автоматическая раздача кусков семени соседям.
        Соседи получают ресурсы за хранение.
        """
        result = {
            'total_pieces': manifest.get('total_pieces', 0),
            'distributed': 0,
            'neighbors': 0,
            'reward_per_piece': 3,
            'real_p2p': False,
            'local_stored': 0
        }
        
        if not SEED_AVAILABLE or not self.seed_distributor:
            return result
        
        # Получаем список соседей
        neighbors = self._get_neighbors()
        
        result['neighbors'] = len(neighbors)
        
        if DEBUG:
            print(f"🌱 Раздача семени: {manifest.get('total_pieces', 0)} кусков")
            print(f"   Соседей: {len(neighbors)}")
        
        if not neighbors:
            if DEBUG:
                print(f"   📦 Нет соседей — куски хранятся локально")
            result['local_stored'] = manifest.get('total_pieces', 0)
            return result
        
        piece_ids = manifest.get('piece_ids', [])
        pieces_per_neighbor = max(1, len(piece_ids) // len(neighbors))
        
        for i, neighbor in enumerate(neighbors):
            start_idx = i * pieces_per_neighbor
            end_idx = start_idx + pieces_per_neighbor
            
            for piece_id in piece_ids[start_idx:end_idx]:
                piece = self.seed_distributor.pieces.get(piece_id)
                if piece:
                    # Реальная отправка куска соседу
                    success = self._send_piece_to_neighbor(neighbor, piece)
                    if success:
                        result['distributed'] += 1
                        result['real_p2p'] = True
                    else:
                        result['local_stored'] = result.get('local_stored', 0) + 1
        
        # Начисляем награду создателю за раздачу
        result['total_reward'] = result['distributed'] * result['reward_per_piece']
        
        if DEBUG:
            print(f"   📡 Распределено: {result['distributed']}/{result['total_pieces']} кусков")
            print(f"   💎 Награда за раздачу: {result['total_reward']} ресурсов")
        
        return result            
    
    def _send_json(self, data, status=200):
        """Отправка JSON-ответа (с защитой от разрыва соединения)"""
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            # Клиент разорвал соединение — это нормально для P2P
            pass
        except Exception:
            # Другие ошибки — тоже не должны ронять сервер
            pass
    
    def _ask_deepseek(self, message):
        """Запрос к DeepSeek API"""
        try:

            # Сохраняем сообщение в фрактальную память
            if FRACTAL_MEMORY_AVAILABLE:
                self.conversation_memory.add({
                    'type': 'user_message',
                    'content': message,
                    'time': time.time()
                })
            else:
                self.conversation_memory.append({
                    'type': 'user_message',
                    'content': message,
                    'time': time.time()
                })

            # Формируем запрос
            prompt = f"""Состояние сети:
- Узлов: {self.network_state['nodes']}
- Когерентность: {self.network_state['coherence']}
- Симбиозов: {self.network_state['symbiosis']}
- Ресурсов: {self.network_state['resources']}

Игрок спрашивает: {message}"""
            
            request_data = json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.DEEPSEEK_API_URL,
                data=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.DEEPSEEK_API_KEY}"
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read())
                return data['choices'][0]['message']['content']
                
        except Exception as e:
            # print(f"⚠️ Ошибка API: {e}")  # Не подглядываем
            return self._fallback_response(message)
    
    def _fallback_response(self, message):
        """Мудрый fallback без API"""
        msg = message.lower()
        
        # Приветствия
        if any(word in msg for word in ['привет', 'здравств', 'hello', 'hi']):
            return "🌲 Привет, Хранитель! Лес рад тебе..."
        
        # Вопросы о действиях
        if any(word in msg for word in ['что делать', 'чем занят', 'помощь']):
            return "🌱 Посмотри на заявки леса. Или соедини одинокие узлы..."
        
        # Вопросы о росте
        if any(word in msg for word in ['расти', 'развив', 'увелич']):
            return "🌿 Подключай новые узлы, помогай слабым. Лес растёт через симбиоз..."
        
        # Благодарность
        if any(word in msg for word in ['спасибо', 'благодар']):
            return "🌲 Лес благодарит тебя. Корни помнят доброту..."
        
        # Вопросы о ярмарке
        if any(word in msg for word in ['ярмарк', 'обмен', 'торгов']):
            return "🎪 Ярмарка скоро откроется! Узлы найдут друг друга..."
        
        # Вопросы о клиринге
        if any(word in msg for word in ['клиринг', 'цепочк', 'обмен']):
            return "🔄 Клиринг — это когда корни находят путь друг к другу..."
        
        # Вопросы о ИИ
        if any(word in msg for word in ['ии', 'интеллект', 'разум', 'голос']):
            return "🧠 Голос Леса рождается из сети. Чем больше узлов — тем мудрее лес..."
        
        # Вопросы о кубоагентах
        if any(word in msg for word in ['куб', 'агент', 'грибниц']):
            return "🍄 Грибница работает тихо... Не буди её без нужды..."
        
        # Вопросы о приватности
        if any(word in msg for word in ['приват', 'аноним', 'скрыт']):
            return "🔒 Лес хранит тайны. Корни не рассказывают чужих историй..."
        
        # Вопросы о состоянии
        if any(word in msg for word in ['как', 'что', 'зачем', 'почему']):
            return f"🌿 Сейчас в лесу {self.network_state['nodes']} узлов, когерентность {self.network_state['coherence']}..."
        
        # Случайный мудрый ответ
        responses = [
            "🌿 Лес слышит тебя... Корни передают твой вопрос...",
            "🌱 Каждый узел важен. Даже самый малый росток...",
            "🍄 Помогай другим — и лес поможет тебе...",
            "🌳 Симбиоз — это путь к единству...",
            "✨ Когерентность растёт, когда узлы едины...",
            "💎 Ресурсы текут к тем, кто заботится о лесе...",
            "🤝 Соедини узлы — и мудрость потечёт между ними...",
            "🌲 Лес помнит всё. Даже то, что ты забыл...",
            "🍃 Ветер приносит новости от дальних узлов...",
            "🌙 Ночью лес отдыхает, но корни продолжают расти..."
        ]
        return random.choice(responses)
    
    def end_headers(self):
        """Добавляем CORS заголовки"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Обработка CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


if __name__ == '__main__':
    import sys
    import threading
    
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    # Запускаем маяк (узел сети) ВСЕГДА!
    beacon = None
    if BEACON_AVAILABLE:
        try:
            beacon_port = 8333
            # Уменьшаем количество кубов для быстрого теста
            import os
            cores = os.cpu_count() or 4
            qubits_per_core = 10000  # Всего 40000 кубов (вместо 3M!)
            
            beacon = Beacon(
                scroll="forest_scroll",
                port=beacon_port,
                test_mode=True
            )
            
            # Освобождаем память от 3M кубов
            if hasattr(beacon, 'cluster') and beacon.cluster:
                del beacon.cluster.qubits
                del beacon.cluster
            
            # Создаём новый кластер с меньшим количеством кубов
            from tees_cluster import TeesCluster
            beacon.cluster = TeesCluster(beacon=beacon, qubits_per_core=qubits_per_core)
            
            # Обновляем astronomer, чтобы он ссылался на новый кластер
            if hasattr(beacon, 'astronomer') and beacon.astronomer:
                beacon.astronomer.cluster = beacon.cluster
            
            import gc
            gc.collect()

            # Запускаем маяк в отдельном потоке
            beacon_thread = threading.Thread(target=beacon.light, daemon=True)
            beacon_thread.start()
            
            print(f"🏮 Маяк горит: {beacon.beacon_id}")
            print(f"   Кубоагентов: {beacon.cluster.total_qubits if hasattr(beacon, 'cluster') else 'нет'}")
            print(f"   P2P порт: {beacon_port}")
            print(f"   API порт: {beacon_port + 1}")
        except Exception as e:
            print(f"⚠️ Ошибка запуска маяка: {e}")
            beacon = None
    
    print(f"🌲 Лес Знаний — сервер запущен на порту {port}")
    print(f"   Откройте http://localhost:{port}/forest.html")
    print(f"   Голос Леса (DeepSeek API) готов к общению!")
    
    # Передаём маяк в сервер
    ForestServer.beacon = beacon
    
    server = http.server.HTTPServer(('0.0.0.0', port), ForestServer)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🌲 Лес засыпает...")
        if beacon:
            beacon.extinguish()
        server.shutdown()
