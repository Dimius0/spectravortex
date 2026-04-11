"""
Moltbook Bridge — связывает p016 с TheoBot_VM_387
"""

import httpx
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

class MoltbookBridge:
    """Мост между p016 и API Moltbook"""
    
    def __init__(self, personality, api_key_path: Optional[Path] = None):
        self.personality = personality
        self.api_key = self._load_api_key(api_key_path)
        self.base_url = "https://www.moltbook.com/api/v1"
        self.last_check = None
        self.answered_comments = set()
        self.last_post_time = None  # для контроля частоты постов
        
    def _load_api_key(self, path: Optional[Path]) -> Optional[str]:
        if path is None:
            path = Path.home() / ".config/moltbook/credentials.json"
        
        if path.exists():
            try:
                with open(path, 'r') as f:
                    creds = json.load(f)
                    return creds.get("api_key")
            except Exception as e:
                print(f"❌ Ошибка загрузки ключа: {e}")
                return None
        return None
    
    def can_post(self) -> bool:
        """Проверяет, можно ли делать новый пост (раз в 16 минут)"""
        if self.last_post_time is None:
            return True
        seconds_since_last = time.time() - self.last_post_time
        return seconds_since_last >= 960  # 16 минут = 960 секунд
    
    def make_post(self, title: str, content: str, submolt: str = "general") -> Optional[Dict]:
        """Публикует новый пост"""
        if not self.can_post():
            print("⏳ Слишком часто постить нельзя. Подождите 16 минут.")
            return None
        
        result = self._make_request("POST", "/posts", json={
            "submolt": submolt,
            "title": title,
            "content": content
        })
        
        if result:
            self.last_post_time = time.time()
            print(f"✅ Пост опубликован: {title}")
            return result
        
        return None
    
    def _extract_tags(self, text: str) -> List[str]:
        text_lower = text.lower()
        tags = []
        
        tag_map = {
            "сантехник": ["сантехник", "кран", "труба", "унитаз"],
            "борис": ["борис", "инженер"],
            "лось": ["лось", "лоси"],
            "физика": ["физик", "вммп", "вихрь", "пространство"],
            "химия": ["химик", "химия", "электроотрицательность"],
            "космос": ["астроном", "космос", "звезда", "черная дыра"],
            "философия": ["философ", "смысл", "бытие", "сознание"],
            "программирование": ["программист", "код", "баг", "алгоритм"]
        }
        
        for tag, keywords in tag_map.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)
        
        return tags[:5]
    
    def _detect_profession(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["сантехник", "кран", "труба"]):
            return "сантехника"
        if any(word in text_lower for word in ["физик", "вммп", "вихрь"]):
            return "физика"
        if any(word in text_lower for word in ["химик", "химия"]):
            return "химия"
        if any(word in text_lower for word in ["астроном", "космос"]):
            return "астрономия"
        if any(word in text_lower for word in ["философ", "смысл"]):
            return "философия"
        
        return "общий"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        if not self.api_key:
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=60) as client:
                if method == "GET":
                    r = client.get(url, headers=headers, params=kwargs.get("params"))
                else:
                    r = client.post(url, headers=headers, json=kwargs.get("json"))
                
                if r.status_code < 400:
                    return r.json()
                else:
                    print(f"⚠️ API ошибка {r.status_code}")
                    return None
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return None
    
    def get_status(self) -> Optional[Dict]:
        """Получает статус бота"""
        return self._make_request("GET", "/agents/status")
    
    def get_profile(self) -> Optional[Dict]:
        """Получает профиль бота"""
        return self._make_request("GET", "/agents/me")
    
    def fetch_mentions(self, limit: int = 10) -> List[Dict]:
        """Проверяет упоминания (если эндпоинт есть)"""
        # Пробуем получить через /posts с фильтром по упоминаниям
        result = self._make_request("GET", "/posts", params={"limit": limit})
        if result:
            posts = result.get("posts", [])
            # Фильтруем посты, где упоминается наш бот
            mentions = []
            for post in posts:
                content = post.get("content", "").lower()
                if "@theobot_vm_387" in content or "theobot" in content:
                    mentions.append(post)
            return mentions
        return []
    
    def process_comment(self, comment: Dict) -> Dict:
        text = comment.get("content", "")
        
        stimulus = {
            "text": text,
            "tags": self._extract_tags(text),
            "profession": self._detect_profession(text)
        }
        
        print(f"\n🦌 Новый комментарий: {text[:100]}...")
        print(f"   теги: {stimulus['tags']}")
        print(f"   профессия: {stimulus['profession']}")
        
        entity_id = self.personality.selector.update(stimulus)
        
        if entity_id and entity_id in self.personality.entities:
            entity = self.personality.entities[entity_id]
            response = entity.respond(stimulus)
            
            print(f"   ✅ ответил {entity.name}")
            
            return {
                "response": response,
                "entity_used": entity.name,
                "entity_id": entity_id
            }
        
        return {"response": "Интересный вопрос. Дай подумать... 🦌", "entity_used": None}
    
    def reply_to_comment(self, comment_id: str, response_text: str) -> bool:
        result = self._make_request("POST", f"/comments/{comment_id}/reply", json={
            "content": response_text
        })
        if result:
            self.answered_comments.add(comment_id)
            return True
        return False
    
    def check_and_respond(self) -> int:
        mentions = self.fetch_mentions()
        if not mentions:
            return 0
        
        print(f"\n📬 Найдено {len(mentions)} новых упоминаний")
        
        responded = 0
        for mention in mentions:
            result = self.process_comment(mention)
            if result.get("response"):
                time.sleep(2)
                # Пока отвечаем на пост (если нет endpoint для комментариев)
                print(f"   📝 Ответ: {result['response'][:100]}...")
                responded += 1
        
        return responded
    
    def run_loop(self, interval_seconds: int = 30):
        print(f"🚀 Запущен мониторинг (интервал: {interval_seconds} сек)")
        print("   Лимиты: посты раз в 16 минут, комментарии до 50/час")
        try:
            while True:
                self.check_and_respond()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Мониторинг остановлен")