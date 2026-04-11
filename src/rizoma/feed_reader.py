"""
Feed Reader — читает ленту ботодрома и наполняет поле H
Версия 1.0 — спектральный анализ, автоиндексация
"""

import httpx
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .personality import SpectralMode, MemoryAccess


class FeedReader:
    """Читает ленту ботодрома и добавляет знания в поле H"""
    
    def __init__(self, personality, api_key_path=None):
        self.p = personality
        self.api_key = self._load_api_key(api_key_path)
        self.base_url = "https://www.moltbook.com/api/v1"
        self.seen_posts = set()
        self.resonator = self.p.selector.resonator if hasattr(self.p, 'selector') else None
    
    def _load_api_key(self, path=None):
        if path is None:
            path = Path.home() / ".config/moltbook/credentials.json"
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f).get("api_key")
            except Exception:
                pass
        return None
    
    def _compute_tau(self, text: str, themes: List[str]) -> float:
        """Вычисляет τ поста на основе содержания и тем"""
        base_tau = 5.5
        
        # Длина как индикатор сложности
        length_factor = min(0.5, len(text) / 1000)
        base_tau += length_factor
        
        # Коррекция по темам
        theme_adjust = 0.0
        for theme in themes:
            if theme in ['VMMS', 'vmms', 'vortex']:
                theme_adjust -= 0.3
            if theme in ['lipzik', 'formula']:
                theme_adjust += 0.2
            if theme in ['memory', 'field']:
                theme_adjust += 0.1
            if theme in ['boris', 'engineer']:
                theme_adjust += 0.2
            if theme in ['moose', 'лось']:
                theme_adjust -= 0.1
        
        tau = base_tau + theme_adjust
        return max(3.0, min(9.0, tau))
    
    def _extract_themes(self, text: str) -> List[str]:
        """Извлекает темы из текста"""
        text_lower = text.lower()
        themes = []
        
        theme_keywords = {
            'VMMS': ['vmms', 'vortex', 'biharmonic', '∇⁴ψ', 'вихрь', 'вммп'],
            'memory': ['memory', 'trace', 'recall', 'память'],
            'field': ['field', 'h-field', 'поле'],
            'resonance': ['resonance', 'resonate', 'резонанс'],
            'lipzik': ['lipzik', 'formula', 'липсик', 'формула'],
            'boris': ['boris', 'engineer', 'борис', 'инженер'],
            'moose': ['moose', 'лось', 'лоси'],
            'alchemy': ['alchemy', 'алхимия'],
            'prediction': ['prediction', 'predict', 'предсказание']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(kw in text_lower for kw in keywords):
                themes.append(theme)
        
        return themes[:5]
    
    def _content_to_mode(self, post: Dict) -> Optional[SpectralMode]:
        """Превращает пост в спектральную моду"""
        content = post.get("content", "")
        title = post.get("title", "")
        full_text = f"{title}\n{content}"
        
        # Пропускаем свои посты
        author = post.get("author", {}).get("name", "")
        if author == "theobot_vm_387":
            return None
        
        # Пропускаем уже виденные
        post_id = post.get("id")
        if post_id in self.seen_posts:
            return None
        self.seen_posts.add(post_id)
        
        # Извлекаем темы
        themes = self._extract_themes(full_text)
        if not themes:
            # Если нет релевантных тем — не индексируем
            return None
        
        # Вычисляем τ
        tau = self._compute_tau(full_text, themes)
        
        # Создаём моду
        mode = SpectralMode(
            tau=tau,
            amplitude=0.4,  # начальная амплитуда
            content=full_text[:500],  # ограничиваем длину
            trace_id=f"feed_{post_id[:8]}",
            themes=themes,
            trace_type="feed"
        )
        
        return mode
    
    def fetch_feed(self, limit=20):
        """Получает последние посты из ленты"""
        if not self.api_key:
            return []
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            with httpx.Client(timeout=30) as client:
                r = client.get(f"{self.base_url}/posts", headers=headers, 
                               params={"sort": "new", "limit": limit})
                if r.status_code == 200:
                    return r.json().get("posts", [])
                elif r.status_code == 401:
                    print("⚠️ API ключ недействителен")
                elif r.status_code == 403:
                    print("⚠️ Доступ запрещён (возможно, нужен VPN)")
        except httpx.TimeoutException:
            print("⚠️ Таймаут при подключении к Moltbook")
        except Exception as e:
            print(f"⚠️ Ошибка при получении ленты: {e}")
        
        return []
    
    def update(self, limit=20) -> int:
        """Обновляет поле H из ленты"""
        posts = self.fetch_feed(limit)
        if not posts:
            return 0
        
        count = 0
        for post in posts:
            mode = self._content_to_mode(post)
            if mode:
                self.p.add_to_h_field(mode)
                count += 1
                print(f"📥 Индексирован пост: {post.get('title', 'untitled')[:50]}... (τ={mode.tau:.2f}, themes={mode.themes})")
        
        if count > 0:
            print(f"📚 Добавлено {count} новых мод в поле H")
        return count
    
    def run_loop(self, interval_seconds=300):
        """Запускает периодическую индексацию ленты"""
        print(f"🚀 Запущен индексатор ленты (интервал: {interval_seconds} сек)")
        print("   Для остановки нажми Ctrl+C")
        try:
            while True:
                self.update(limit=20)
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Индексатор остановлен")