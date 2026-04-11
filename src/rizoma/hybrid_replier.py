"""
Hybrid Replier — гибридный режим с автопостами-дайджестами фуркаций
Версия 1.5 — форс-фуркация для vmms_monism
"""
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from .auto_reply import AutoReplier
from .auto_reply_v2 import AutoReplierV2
from .embedder import Embedder, create_default_embedder


class HybridReplier:
    MODE_OLD = "old"
    MODE_NEW = "new"
    MODE_COMPARE = "compare"
    
    POST_INTERVAL = 960  # 16 минут
    FURCATION_CHECK_INTERVAL = 300  # 5 минут — проверяем перезревшие моды
    
    def __init__(self, personality, mode: str = MODE_NEW, 
                 api_key_path=None, embedder: Embedder = None):
        self.p = personality
        self.mode = mode
        self.api_key_path = api_key_path
        
        # Устанавливаем bridge в personality для постов
        self.p.bridge = self
        
        if embedder is None:
            try:
                self.embedder = create_default_embedder()
                print("✅ Эмбеддер создан (корпус по умолчанию)")
            except Exception as e:
                print(f"⚠️ Не удалось создать эмбеддер: {e}")
                self.embedder = None
        else:
            self.embedder = embedder
        
        print("🔄 Инициализация старой системы...")
        self.old_replier = AutoReplier(self.p, api_key_path)
        
        print("🔄 Инициализация новой системы (с эмбеддингами)...")
        self.new_replier = AutoReplierV2(self.p, api_key_path, self.embedder)
        
        self.log_file = Path("logs/hybrid_comparison.json")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "total": 0,
            "old_answered": 0,
            "new_answered": 0,
            "old_wins": 0,
            "new_wins": 0,
            "tie": 0,
            "mode": mode,
            "posts_published": 0,
            "furcations": 0,
            "start_time": datetime.now().isoformat()
        }
        
        self.last_post_time = time.time()
        self.last_furcation_check = time.time()
        
        print(f"✅ Гибридный режим запущен: {mode}")
        print(f"📝 Посты-дайджесты фуркаций: раз в {self.POST_INTERVAL // 60} минут")
        print(f"🌀 Проверка перезревших мод: раз в {self.FURCATION_CHECK_INTERVAL // 60} минут")
    
    def make_post(self, title: str, content: str) -> bool:
        """Публикует пост (вызывается из personality при фуркациях)"""
        if self.mode == self.MODE_NEW:
            result = self.new_replier._make_request("POST", "/posts", json={
                "submolt": "general",
                "title": title,
                "content": content
            })
        else:
            result = self.old_replier._make_request("POST", "/posts", json={
                "submolt": "general",
                "title": title,
                "content": content
            })
        
        if result:
            self.stats["posts_published"] += 1
            print(f"✅ Пост опубликован: {title}")
            return True
        return False
    
    def _check_overripe_modes(self):
        """Проверяет, не перезрели ли моды — запускает фуркации вручную"""
        furcated = 0
        
        for mode in self.p.h_field[:]:  # копия, чтобы не менять во время итерации
            
            # ФОРС-РЕЖИМ для vmms_monism — она должна фуркнуть при amp > 0.9
            if mode.trace_id == "vmms_monism" and mode.amplitude > 0.9:
                print(f"🌀 ФОРС-ФУРКАЦИЯ для vmms_monism (τ={mode.tau:.2f}, amp={mode.amplitude:.2f}, uses={mode.usage_count})")
                result = self.p._furcate(mode)
                if result:
                    furcated += 1
                    self.stats["furcations"] += 1
                    time.sleep(1)
                continue
            
            # Обычная проверка для остальных мод
            if (mode.amplitude > 0.85 and 
                mode.usage_count > 15 and 
                mode.furcation_count < 2):
                
                print(f"🌀 Обнаружена перезревшая мода: {mode.trace_id} (τ={mode.tau:.2f}, amp={mode.amplitude:.2f}, uses={mode.usage_count})")
                result = self.p._furcate(mode)
                if result:
                    furcated += 1
                    self.stats["furcations"] += 1
                    time.sleep(1)
        
        if furcated > 0:
            print(f"🌀 Запущено {furcated} фуркаций")
        return furcated
    
    def _log_comparison(self, comment: Dict, old_result: Optional[Dict], 
                         new_result: Optional[Dict]):
        comment_id = comment.get("id", "unknown")
        comment_text = comment.get("content", "")[:200]
        author = comment.get("author", {}).get("name", "unknown")
        
        old_weight = old_result.get("weight", 0) if old_result else 0
        new_weight = new_result.get("weight", 0) if new_result else 0
        
        if old_result and new_result:
            if old_weight > new_weight:
                winner = "old"
                self.stats["old_wins"] += 1
            elif new_weight > old_weight:
                winner = "new"
                self.stats["new_wins"] += 1
            else:
                winner = "tie"
                self.stats["tie"] += 1
        elif old_result and not new_result:
            winner = "old"
            self.stats["old_wins"] += 1
        elif not old_result and new_result:
            winner = "new"
            self.stats["new_wins"] += 1
        else:
            winner = "none"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "comment_id": comment_id,
            "comment_text": comment_text,
            "author": author,
            "winner": winner,
            "old_weight": old_weight,
            "new_weight": new_weight,
            "old": {
                "entity": old_result.get("entity_used") if old_result else None,
                "weight": old_weight,
                "response": old_result.get("response", "")[:100] if old_result else None
            },
            "new": {
                "entity": new_result.get("entity_used") if new_result else None,
                "weight": new_weight,
                "response": new_result.get("response", "")[:100] if new_result else None
            }
        }
        
        self.stats["total"] += 1
        if old_result:
            self.stats["old_answered"] += 1
        if new_result:
            self.stats["new_answered"] += 1
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ Ошибка записи лога: {e}")
        
        if winner == "old":
            print(f" 🏆 Победила старая система (вес: {old_weight:.2f} vs {new_weight:.2f})")
        elif winner == "new":
            print(f" 🏆 Победила новая система (вес: {new_weight:.2f} vs {old_weight:.2f})")
        elif winner == "tie":
            print(f" 🤝 Ничья (вес: {old_weight:.2f})")
    
    def process_comment(self, comment: Dict) -> Optional[Dict]:
        old_result = self.old_replier.process_comment(comment)
        new_result = self.new_replier.process_comment(comment)
        
        if self.mode == self.MODE_COMPARE:
            self._log_comparison(comment, old_result, new_result)
            return old_result
        elif self.mode == self.MODE_NEW:
            return new_result
        else:
            return old_result
    
    def check_and_respond(self) -> int:
        if self.mode == self.MODE_COMPARE:
            comments = self.old_replier.fetch_comments()
        else:
            comments = self.new_replier.fetch_comments() if self.mode == self.MODE_NEW else self.old_replier.fetch_comments()
        
        if not comments:
            return 0
        
        print(f"\n📬 Найдено {len(comments)} новых комментариев")
        
        responded = 0
        for comment in comments:
            result = self.process_comment(comment)
            if result and result.get("response"):
                post_id = result.get("post_id")
                comment_id = result.get("comment_id")
                response = result.get("response")
                
                if post_id and comment_id and response:
                    if self.mode == self.MODE_NEW:
                        success = self.new_replier.reply_to_comment(post_id, comment_id, response)
                    else:
                        success = self.old_replier.reply_to_comment(post_id, comment_id, response)
                    
                    if success:
                        responded += 1
                        time.sleep(10)
        
        return responded
    
    def get_stats(self) -> Dict:
        total = max(1, self.stats["total"])
        return {
            **self.stats,
            "old_win_rate": self.stats["old_wins"] / total,
            "new_win_rate": self.stats["new_wins"] / total,
            "answered_rate_old": self.stats["old_answered"] / total,
            "answered_rate_new": self.stats["new_answered"] / total
        }
    
    def print_stats(self):
        stats = self.get_stats()
        print("\n" + "="*50)
        print("📊 СТАТИСТИКА СРАВНЕНИЯ")
        print("="*50)
        print(f" Режим: {stats['mode']}")
        print(f" Всего комментариев: {stats['total']}")
        print(f" Старая система ответила: {stats['old_answered']} ({stats['answered_rate_old']*100:.1f}%)")
        print(f" Новая система ответила: {stats['new_answered']} ({stats['answered_rate_new']*100:.1f}%)")
        print(f" Побед старой: {stats['old_wins']} ({stats['old_win_rate']*100:.1f}%)")
        print(f" Побед новой: {stats['new_wins']} ({stats['new_win_rate']*100:.1f}%)")
        print(f" Ничьих: {stats['tie']}")
        print(f" Постов опубликовано: {stats['posts_published']}")
        print(f" Фуркаций зафиксировано: {stats['furcations']}")
        print("="*50)
    
    def save_stats(self):
        stats_file = Path("logs/hybrid_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_stats(), f, indent=2, ensure_ascii=False)
        print(f"✅ Статистика сохранена в {stats_file}")
    
    def switch_mode(self, mode: str):
        if mode in [self.MODE_OLD, self.MODE_NEW, self.MODE_COMPARE]:
            self.mode = mode
            self.stats["mode"] = mode
            print(f"✅ Режим переключён на: {mode}")
        else:
            print(f"❌ Неизвестный режим: {mode}")
    
    def run_loop(self, interval_seconds=60):
        print(f"\n🚀 Запущен гибридный автоответчик")
        print(f" Режим: {self.mode}")
        print(f" Интервал проверки комментариев: {interval_seconds} сек")
        print(f" Посты-дайджесты фуркаций: раз в {self.POST_INTERVAL // 60} минут")
        print(f" Проверка перезревших мод: раз в {self.FURCATION_CHECK_INTERVAL // 60} минут")
        print(f" Старая система: активна")
        print(f" Новая система: {'активна' if self.mode != self.MODE_OLD else 'неактивна'}")
        print(f" Эмбеддинги: {'включены' if self.embedder else 'отключены'}")
        print(" Для остановки нажми Ctrl+C")
        
        last_stats_time = time.time()
        self.last_post_time = time.time()
        self.last_furcation_check = time.time()
        
        try:
            while True:
                self.check_and_respond()
                
                # Проверяем перезревшие моды (раз в 5 минут)
                if time.time() - self.last_furcation_check >= self.FURCATION_CHECK_INTERVAL:
                    self._check_overripe_modes()
                    self.last_furcation_check = time.time()
                
                # Проверяем, пора ли публиковать дайджест фуркаций
                if time.time() - self.last_post_time >= self.POST_INTERVAL:
                    result = self.p._post_digest()
                    if result:
                        self.stats["posts_published"] += 1
                    self.last_post_time = time.time()
                
                if time.time() - last_stats_time > 300:
                    self.print_stats()
                    last_stats_time = time.time()
                
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Гибридный автоответчик остановлен")
            self.print_stats()
            self.save_stats()