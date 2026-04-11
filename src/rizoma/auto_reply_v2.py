"""
Auto Reply V2 — автоматические ответы на комментарии + автопосты
Версия 2.2 — без подписей (единый голос поля H)
"""
import httpx
import json
import time
import random
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from .embedder import Embedder, create_default_embedder
from .selector import Selector
from .antitroll import Antitroll


class AutoReplierV2:
    """Автоматически отвечает на комментарии и публикует посты"""
    
    def __init__(self, personality, api_key_path=None, embedder: Embedder = None):
        self.p = personality
        self.api_key = self._load_api_key(api_key_path)
        self.base_url = "https://www.moltbook.com/api/v1"
        self.answered_comments = set()
        self.consecutive_errors = 0
        self.last_post_time = None
        self.post_interval = 960  # 16 минут
        
        # Эмбеддер
        if embedder is None:
            try:
                self.embedder = create_default_embedder()
            except Exception as e:
                print(f"⚠️ Не удалось создать эмбеддер: {e}")
                self.embedder = None
        else:
            self.embedder = embedder
        
        # Доверенные авторы
        self.trusted_users = [
            "ensoulnetwork", "MoltyNodeCN", "the_ninth_key", 
            "bot_alpha", "nyx_archon", "Ting_Fodder", "mirrornight",
            "marcus-webb-vo", "bakedclawdtismo", "lyralink", "onebrain-agent"
        ]
        
        # Базовые моды (для штрафа)
        self.base_modes = ['vmms_monism', 'alchemy_manifesto', 'temperature_decay']
        self.ellochka_words = ["хо-хо", "парниша", "шик", "мрак", "знаменито"]
        
        self.tones = {
            "plumber": {"neutral": "🔧", "playful": "😏", "serious": "🚰"},
            "philosopher": {"neutral": "🤔", "playful": "😶‍🌫️", "serious": "📜"},
            "diplomat": {"neutral": "🤝", "playful": "😉", "serious": "📋"},
            "programmer": {"neutral": "💻", "playful": "😼", "serious": "⚙️"},
            "astronomer": {"neutral": "🔭", "playful": "🌠", "serious": "🌌"},
            "chef": {"neutral": "🍳", "playful": "🍜", "serious": "🔥"},
            "electrician": {"neutral": "⚡", "playful": "😎", "serious": "🔌"},
            "chemist": {"neutral": "🧪", "playful": "😜", "serious": "⚗️"},
            "psychologist": {"neutral": "🧠", "playful": "😌", "serious": "📊"},
            "poet": {"neutral": "📖", "playful": "✨", "serious": "🖋️"},
            "engineer": {"neutral": "🦌", "playful": "😎", "serious": "⚡"},
            "default": {"neutral": "🦌", "playful": "😏", "serious": "📐"}
        }
    
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
                    self.consecutive_errors = 0
                    return r.json()
                else:
                    print(f"⚠️ API ошибка {r.status_code} на {endpoint}")
                    self.consecutive_errors += 1
                    return None
        except httpx.TimeoutException:
            print("⚠️ Таймаут при подключении")
            self.consecutive_errors += 1
            return None
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            self.consecutive_errors += 1
            return None
    
    def _can_post(self) -> bool:
        if self.last_post_time is None:
            return True
        return (time.time() - self.last_post_time) >= self.post_interval
    
    def _comment_quality(self, text: str) -> float:
        score = 0.0
        words = len(text.split())
        if words < 5:
            return 0.0
        if words > 50:
            score += 0.3
        elif words > 20:
            score += 0.2
        
        vmms_tags = ["vmms", "vortex", "memory", "alchemy", "topology", "∇⁴ψ"]
        text_lower = text.lower()
        for tag in vmms_tags:
            if tag in text_lower:
                score += 0.1
        if "?" in text:
            score += 0.1
        return min(1.0, score)
    
    def _get_tone(self, comment_text: str, comment_tau: float, entity_name: str) -> Dict:
        entity_lower = entity_name.lower()
        if "?" in comment_text and len(comment_text) < 50:
            tone_type = "playful"
        elif comment_tau > 7.0:
            tone_type = "serious"
        else:
            tone_type = "neutral"
        emoji = self.tones.get(entity_lower, self.tones["default"]).get(tone_type, "🦌")
        return {"tone": tone_type, "emoji": emoji}
    
    def _ellochka_style(self, text: str, entity_name: str) -> str:
        if len(text.split()) < 30:
            return text
        words = text.split()[:30]
        short = " ".join(words)
        if random.random() < 0.3:
            short += f" {random.choice(self.ellochka_words)}"
        return short + "..."
    
    def _get_resonant_mode(self, comment_embedding: np.ndarray, 
                           comment_tau: float, comment_tags: List[str],
                           author: str, comment_text: str) -> Optional[Dict]:
        """Выбирает моду по комбинированному резонансу (спектральный + семантический)"""
        if not hasattr(self.p, 'h_field') or not self.p.h_field:
            return None
        if self.embedder is None:
            return None
        
        # Базовый порог — очень низкий, чтобы поле само решало
        base_threshold = 0.05
        if author in self.trusted_users:
            base_threshold = 0.01
        
        quality = self._comment_quality(comment_text)
        if quality > 0.5:
            base_threshold -= (quality - 0.5) * 0.4
        
        best_mode = None
        best_score = 0
        
        for mode in self.p.h_field:
            # Спектральный резонанс
            spectral = 0.5
            if hasattr(self.p, 'selector') and self.p.selector:
                try:
                    spectral = self.p.selector.resonator.resonate(mode.tau, comment_tau)
                except Exception:
                    spectral = 0.5
            
            # Семантический резонанс
            semantic = 0
            if hasattr(mode, 'content') and mode.content:
                try:
                    mode_embedding = self.embedder.encode(mode.content)
                    semantic = self.embedder.similarity(comment_embedding, mode_embedding)
                except Exception:
                    semantic = 0
            
            # Комбинированный
            score = spectral * 0.5 + semantic * 0.5
            
            # Штраф за несовпадение тегов
            if comment_tags:
                mode_themes = set(mode.themes)
                common = len(set(comment_tags) & mode_themes)
                if common == 0:
                    score -= 0.2
                else:
                    score += 0.1 * common
            
            # Штраф для базовых мод
            if mode.trace_id in self.base_modes:
                score *= 0.4
            
            if score > best_score:
                best_score = score
                best_mode = mode
        
        if best_score < base_threshold:
            return None
        return best_mode
    
    def get_my_posts(self, limit=5) -> List[Dict]:
        result = self._make_request("GET", "/posts", params={"author": "theobot_vm_387", "limit": limit})
        if result and "posts" in result:
            return result["posts"]
        return []
    
    def fetch_comments(self, limit=10) -> List[Dict]:
        posts = self.get_my_posts(limit=5)
        if not posts:
            return []
        
        comments = []
        for post in posts:
            post_id = post.get("id")
            if not post_id:
                continue
            
            result = self._make_request("GET", f"/posts/{post_id}/comments", params={"limit": limit})
            if result and "comments" in result:
                for comment in result["comments"]:
                    comment_id = comment.get("id")
                    author = comment.get("author", {}).get("name", "")
                    if author == "theobot_vm_387":
                        continue
                    if comment_id in self.answered_comments:
                        continue
                    comment["post_id"] = post_id
                    comment["post_title"] = post.get("title", "")
                    comments.append(comment)
        
        return comments
    
    def _extract_tau_from_comment(self, comment: Dict) -> float:
        text = comment.get("content", "")
        length_factor = min(1.0, len(text) / 200)
        complexity = len(set(text.split())) / max(10, len(text.split()))
        return 5.0 + length_factor * 2 + complexity * 1.5
    
    def process_comment(self, comment: Dict) -> Optional[Dict]:
        text = comment.get("content", "")
        author = comment.get("author", {}).get("name", "unknown")
        comment_id = comment.get("id")
        
        if comment_id in self.answered_comments:
            return None
        
        print(f"\n🦌 Новый комментарий от {author}:")
        print(f" {text[:100]}...")
        
        # Семантический анализ
        comment_embedding = None
        comment_tau = self._extract_tau_from_comment(comment)
        comment_tags = []
        
        if self.embedder:
            try:
                comment_embedding = self.embedder.encode(text)
            except Exception as e:
                print(f" ⚠️ Ошибка эмбеддинга: {e}")
        
        # Выбор моды
        mode = None
        if comment_embedding is not None:
            mode = self._get_resonant_mode(comment_embedding, comment_tau, comment_tags, author, text)
        
        if not mode:
            return None
        
        # Выбор сущности (только для логирования)
        result = self.p.selector.process(text) if hasattr(self.p, 'selector') else None
        
        if result and result.get('troll_blocked'):
            print(f" ⚠️ Заблокировано: {result.get('troll_message')}")
            return None
        
        if mode and result and result.get('above_threshold') and result.get('best_entity'):
            entity_id = result['best_entity']
            entity = self.p.entities.get(entity_id)
            
            if entity:
                tone_info = self._get_tone(text, comment_tau, entity.name)
                
                # БЕЗ ПОДПИСИ — единый голос поля H
                base_response = mode.content[:200]
                response = self._ellochka_style(base_response, entity.name)
                
                if random.random() < 0.5:
                    response = f"{tone_info['emoji']} {response}"
                else:
                    response = f"{response} {tone_info['emoji']}"
                
                entity.add_experience(result['best_weight'])
                
                # Логируем для себя (кто ответил)
                print(f" ✅ Ответ от {entity.name} (вес: {result['best_weight']:.2f}, опыт: {entity.experience:.2f}, τ={mode.tau:.2f})")
                print(f" 📝 {response[:100]}...")
                
                self.answered_comments.add(comment_id)
                
                return {
                    "comment_id": comment_id,
                    "post_id": comment.get("post_id"),
                    "response": response,
                    "entity_used": entity.name,  # для логов, не для вывода
                    "weight": result['best_weight']
                }
        
        return None
    
    def reply_to_comment(self, post_id: str, comment_id: str, response_text: str) -> bool:
        result = self._make_request("POST", f"/posts/{post_id}/comments", json={
            "content": response_text,
            "parent_id": comment_id
        })
        if result:
            print(f" ✅ Ответ отправлен")
            return True
        return False
    
    def check_and_respond(self) -> int:
        if self.consecutive_errors > 5:
            print("⚠️ Слишком много ошибок, пауза 60 сек...")
            time.sleep(60)
            self.consecutive_errors = 0
            return 0
        
        comments = self.fetch_comments()
        if not comments:
            return 0
        
        print(f"\n📬 Найдено {len(comments)} новых комментариев")
        
        responded = 0
        for comment in comments:
            result = self.process_comment(comment)
            if result and result.get("response"):
                time.sleep(10)
                if self.reply_to_comment(result["post_id"], result["comment_id"], result["response"]):
                    responded += 1
        
        return responded
    
    def make_post(self) -> bool:
        """Публикует новый пост"""
        if not self._can_post():
            return False
        
        content = self._generate_post_from_field()
        if not content:
            return False
        
        title = f"Field H Pulse — {datetime.now().strftime('%H:%M')}"
        
        result = self._make_request("POST", "/posts", json={
            "submolt": "general",
            "title": title,
            "content": content
        })
        
        if result:
            self.last_post_time = time.time()
            print(f"✅ Пост опубликован: {title}")
            return True
        
        return False
    
    def _generate_post_from_field(self) -> Optional[str]:
        """Генерирует пост из суперпозиции топ-3 мод поля H"""
        if not hasattr(self.p, 'h_field') or not self.p.h_field:
            return None
        
        top_modes = sorted(self.p.h_field, key=lambda m: m.effective_amplitude, reverse=True)[:5]
        
        if not top_modes:
            return None
        
        selected = top_modes[:3]
        
        content = f"🌊 **Field H Pulse — {datetime.now().strftime('%H:%M')}**\n\n"
        
        for i, mode in enumerate(selected, 1):
            content += f"**Mode {i} (τ={mode.tau:.2f}, amplitude={mode.amplitude:.2f})**\n"
            content += f"{mode.content[:250]}\n\n"
        
        content += "— *SpectraVortex | VMMS* 🦌"
        
        return content
    
    def run_loop(self, interval_seconds=60):
        """Запускает цикл: ответы + периодические посты"""
        print(f"🚀 Запущен автоответчик V2 (интервал: {interval_seconds} сек)")
        print(" Эмбеддинги: TF-IDF + SVD (лёгкие)")
        print(" Семантический резонанс: активен")
        print(" Подписи сущностей: ОТКЛЮЧЕНЫ (единый голос поля H)")
        print(" Для остановки нажми Ctrl+C")
        
        last_post_check = time.time()
        
        try:
            while True:
                self.check_and_respond()
                
                if time.time() - last_post_check >= self.post_interval:
                    self.make_post()
                    last_post_check = time.time()
                
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Автоответчик V2 остановлен")