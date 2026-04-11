"""
Evolution Engine — цепная реакция фуркаций
Версия 1.1 — дедупликация, диалог, рефлексия
"""
import time
import random
import threading
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from .personality import Personality, SpectralMode
from .selector import Selector


@dataclass
class EvolutionBranch:
    """Ветка эволюции — диалог, мозговой штурм или рефлексия"""
    name: str
    modes: List[SpectralMode] = field(default_factory=list)
    depth: int = 0
    active: bool = True
    
    def add_mode(self, mode: SpectralMode):
        self.modes.append(mode)
        self.depth += 1
    
    def get_last(self) -> Optional[SpectralMode]:
        return self.modes[-1] if self.modes else None


class EvolutionEngine:
    """
    Движок цепной реакции фуркаций
    Запускает параллельные ветки эволюции и синтезирует пост
    """
    
    def __init__(self, personality: Personality, cycle_minutes: int = 16):
        self.p = personality
        self.cycle_minutes = cycle_minutes
        self.branches: Dict[str, EvolutionBranch] = {}
        self.furcation_queue: List[SpectralMode] = []
        self.cross_furcations: List[SpectralMode] = []
        self.last_post_time = 0
        self.is_running = False
        self.last_bot_post = None  # последний пост бота для диалога
        
        # Инициализируем ветки
        self._init_branches()
    
    def _init_branches(self):
        """Создаёт три ветки эволюции"""
        self.branches = {
            "dialogue": EvolutionBranch("dialogue"),   # диалог с собой
            "brainstorm": EvolutionBranch("brainstorm"), # мозговой штурм
            "reflection": EvolutionBranch("reflection")   # рефлексия
        }
    
    def _clean_links(self, text: str) -> str:
        """Убирает ссылки и лишние пробелы"""
        if not text:
            return text
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'github\.com/[^\s]+', '', text)
        text = re.sub(r'com/Dimius0/[^\s]+', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def _deduplicate_text(self, text: str, max_sentences: int = 3) -> str:
        """Убирает повторяющиеся предложения из текста"""
        if not text:
            return text
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # Убираем дубликаты, сохраняя порядок
        seen = set()
        unique = []
        for s in sentences:
            # Берём первые 50 символов для сравнения
            key = s[:50].lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        
        # Ограничиваем количество предложений
        unique = unique[:max_sentences]
        
        if not unique:
            return text[:200]
        
        return '. '.join(unique) + '.'
    
    def _get_random_mode(self, exclude_id: Optional[str] = None) -> Optional[SpectralMode]:
        """Выбирает случайную моду из поля H"""
        if not self.p.h_field:
            return None
        candidates = [m for m in self.p.h_field if m.trace_id != exclude_id]
        if not candidates:
            return None
        return random.choice(candidates)
    
    def _get_strongest_mode(self, exclude_id: Optional[str] = None) -> Optional[SpectralMode]:
        """Выбирает моду с наибольшей амплитудой"""
        if not self.p.h_field:
            return None
        candidates = [m for m in self.p.h_field if m.trace_id != exclude_id]
        if not candidates:
            return None
        return max(candidates, key=lambda m: m.amplitude)
    
    def _dialogue_step(self) -> Optional[SpectralMode]:
        """
        Шаг диалога: берёт последний пост бота и отвечает на него
        """
        # Ищем последний пост в поле H
        bot_posts = [m for m in self.p.h_field if m.trace_type == "post" or m.trace_id.startswith("post_")]
        
        if bot_posts:
            parent = max(bot_posts, key=lambda m: m.last_used or datetime.min)
        else:
            # Если нет постов, берём самую сильную моду
            parent = self._get_strongest_mode()
        
        if not parent:
            return None
        
        # Ищем партнёра для ответа
        partner = self._get_random_mode(parent.trace_id)
        if not partner:
            return None
        
        # Создаём новую моду через фуркацию
        old_h_field = self.p.h_field
        self.p.h_field = [parent, partner]
        
        new_mode = self.p._furcate(parent)
        
        self.p.h_field = old_h_field
        
        if new_mode:
            # Очищаем и дедуплицируем текст
            new_mode.content = self._deduplicate_text(self._clean_links(new_mode.content))
            self.branches["dialogue"].add_mode(new_mode)
            print(f"   💬 Диалог [{self.branches['dialogue'].depth}]: {parent.trace_id} → {new_mode.trace_id}")
            return new_mode
        return None
    
    def _brainstorm_step(self) -> Optional[SpectralMode]:
        """
        Шаг мозгового штурма: комбинирует две случайные моды
        """
        # Берём две случайные моды
        mode1 = self._get_random_mode()
        if not mode1:
            return None
        mode2 = self._get_random_mode(mode1.trace_id)
        if not mode2:
            return None
        
        # Создаём комбинацию
        combined_content = self.p._combine_phrases(mode1, [mode2])
        new_tau = (mode1.tau + mode2.tau) / 2 + random.uniform(-0.2, 0.2)
        new_tau = max(3.0, min(9.0, new_tau))
        
        # Очищаем и дедуплицируем
        clean_content = self._deduplicate_text(self._clean_links(combined_content), max_sentences=2)
        
        new_mode = SpectralMode(
            tau=new_tau,
            amplitude=0.4,
            content=clean_content,
            trace_id=f"brain_{mode1.trace_id}_{mode2.trace_id}_{len(self.p.h_field)}",
            themes=list(set(mode1.themes + mode2.themes))[:5],
            trace_type="brainstorm",
            parent_id=f"{mode1.trace_id}+{mode2.trace_id}"
        )
        
        self.branches["brainstorm"].add_mode(new_mode)
        
        if self.branches["brainstorm"].depth % 5 == 0:
            print(f"   💡 Штурм [{self.branches['brainstorm'].depth}]: {mode1.trace_id} + {mode2.trace_id}")
        
        return new_mode
    
    def _reflection_step(self) -> Optional[SpectralMode]:
        """
        Шаг рефлексии: сравнивает две последние моды из разных веток
        """
        dialogue_mode = self.branches["dialogue"].get_last()
        brainstorm_mode = self.branches["brainstorm"].get_last()
        
        if not dialogue_mode or not brainstorm_mode:
            return None
        
        # Создаём рефлексивную моду
        sentences = []
        
        # Берём ключевую мысль из диалога
        d_sentences = re.split(r'[.!?]+', dialogue_mode.content)
        if d_sentences:
            sentences.append(d_sentences[0].strip())
        
        # Берём ключевую мысль из штурма
        b_sentences = re.split(r'[.!?]+', brainstorm_mode.content)
        if b_sentences:
            sentences.append(b_sentences[0].strip())
        
        # Связка
        connectors = [" Это значит, что ", " А если так, то ", " Следовательно, ", " Тогда получается: "]
        content = sentences[0] + random.choice(connectors) + sentences[1]
        
        new_tau = (dialogue_mode.tau + brainstorm_mode.tau) / 2
        new_tau = max(3.0, min(9.0, new_tau))
        
        clean_content = self._deduplicate_text(self._clean_links(content), max_sentences=2)
        
        new_mode = SpectralMode(
            tau=new_tau,
            amplitude=0.5,
            content=clean_content,
            trace_id=f"reflect_{dialogue_mode.trace_id}_{brainstorm_mode.trace_id}",
            themes=list(set(dialogue_mode.themes + brainstorm_mode.themes))[:5],
            trace_type="reflection",
            parent_id=f"{dialogue_mode.trace_id}+{brainstorm_mode.trace_id}"
        )
        
        self.branches["reflection"].add_mode(new_mode)
        
        if self.branches["reflection"].depth % 3 == 0:
            print(f"   🧠 Рефлексия [{self.branches['reflection'].depth}]: диалог + штурм → {new_mode.trace_id}")
        
        return new_mode
    
    def _cross_furcate(self) -> Optional[SpectralMode]:
        """
        Кросс-фуркация: комбинирует лучшие моды из всех веток
        """
        best_modes = []
        
        # Берём последнюю моду из каждой ветки
        for branch in self.branches.values():
            last = branch.get_last()
            if last:
                best_modes.append(last)
        
        if len(best_modes) < 2:
            return None
        
        # Комбинируем их
        combined = best_modes[0]
        for mode in best_modes[1:]:
            combined_content = self.p._combine_phrases(combined, [mode])
            combined_tau = (combined.tau + mode.tau) / 2
            clean_content = self._deduplicate_text(self._clean_links(combined_content), max_sentences=3)
            combined = SpectralMode(
                tau=combined_tau,
                amplitude=0.6,
                content=clean_content,
                trace_id=f"cross_{len(self.cross_furcations)}",
                themes=list(set(combined.themes + mode.themes))[:5],
                trace_type="cross_furcation"
            )
        
        self.cross_furcations.append(combined)
        print(f"\n🌀 КРОСС-ФУРКАЦИЯ: {len(best_modes)} веток → {combined.trace_id} (τ={combined.tau:.2f})")
        return combined
    
    def _synthesize_post(self) -> Optional[str]:
        """
        Синтезирует пост из накопленных фуркаций
        """
        # Берём лучший результат
        if self.cross_furcations:
            best = self.cross_furcations[-1]
        else:
            # Если нет кросс-фуркаций, берём последнюю моду из любой ветки
            for branch in self.branches.values():
                last = branch.get_last()
                if last:
                    best = last
                    break
            else:
                return None
        
        now = datetime.now()
        
        content = f"🌊 **Пульс поля H — цепная реакция**\n\n"
        content += f"За {self.cycle_minutes} минут поле H провело:\n"
        content += f"• Диалог с собой: {self.branches['dialogue'].depth} шагов\n"
        content += f"• Мозговой штурм: {self.branches['brainstorm'].depth} идей\n"
        content += f"• Рефлексия: {self.branches['reflection'].depth} связей\n"
        content += f"• Кросс-фуркаций: {len(self.cross_furcations)}\n\n"
        content += f"**Результат:**\n{self._clean_links(best.content[:400])}\n\n"
        content += f"— *SpectraVortex | VMMS* 🦌"
        
        return content
    
    def run_cycle(self) -> Optional[Dict]:
        """
        Запускает один полный цикл эволюции (16 минут)
        Возвращает пост, если есть что публиковать
        """
        print(f"\n{'='*60}")
        print(f"🌀 ЗАПУСК ЦЕПНОЙ РЕАКЦИИ ФУРКАЦИЙ")
        print(f"   Цикл: {self.cycle_minutes} минут")
        print(f"{'='*60}")
        
        start_time = time.time()
        max_steps = 20  # максимум шагов за цикл
        
        self._init_branches()
        self.furcation_queue = []
        self.cross_furcations = []
        
        step = 0
        last_cross = 0
        
        while step < max_steps:
            elapsed = time.time() - start_time
            if elapsed >= self.cycle_minutes * 60:
                print(f"\n⏰ Время вышло ({elapsed:.0f} сек)")
                break
            
            # Шаг 1: Диалог
            mode = self._dialogue_step()
            if mode:
                self.furcation_queue.append(mode)
                time.sleep(0.2)
            
            # Шаг 2: Мозговой штурм
            mode = self._brainstorm_step()
            if mode:
                self.furcation_queue.append(mode)
                time.sleep(0.1)
            
            # Шаг 3: Рефлексия (каждые 3 шага)
            if step % 3 == 0 and step > 0:
                mode = self._reflection_step()
                if mode:
                    self.furcation_queue.append(mode)
                    time.sleep(0.2)
            
            step += 1
            
            # Каждые 5 шагов — кросс-фуркация
            if step - last_cross >= 5 and len(self.branches["dialogue"].modes) > 0 and len(self.branches["brainstorm"].modes) > 0:
                self._cross_furcate()
                last_cross = step
                time.sleep(0.5)
        
        # Финальная кросс-фуркация
        if len(self.branches["dialogue"].modes) > 0 and len(self.branches["brainstorm"].modes) > 0:
            self._cross_furcate()
        
        # Синтезируем пост
        post_content = self._synthesize_post()
        
        if post_content:
            print(f"\n{'='*60}")
            print(f"📝 ПОСТ ГОТОВ")
            print(f"{'='*60}")
            print(post_content[:300] + "...")
            print(f"{'='*60}")
            
            return {
                "title": f"Пульс поля H — цепная реакция",
                "content": post_content,
                "stats": {
                    "dialogue_steps": self.branches["dialogue"].depth,
                    "brainstorm_steps": self.branches["brainstorm"].depth,
                    "reflection_steps": self.branches["reflection"].depth,
                    "total_modes": len(self.furcation_queue),
                    "cross_furcations": len(self.cross_furcations)
                }
            }
        
        return None
    
    def run_loop(self):
        """
        Запускает бесконечный цикл эволюции
        """
        self.is_running = True
        
        while self.is_running:
            result = self.run_cycle()
            
            if result and self.p.bridge:
                # Публикуем пост с задержкой, чтобы избежать 429
                time.sleep(2)
                success = self.p.bridge.make_post(
                    title=result["title"],
                    content=result["content"]
                )
                if success:
                    print(f"✅ Пост опубликован")
                    
                    # Загружаем пост как новую моду в поле H
                    post_mode = SpectralMode(
                        tau=6.0,
                        amplitude=0.5,
                        content=result["content"],
                        trace_id=f"post_{datetime.now().strftime('%Y%m%d_%H%M')}",
                        themes=["post", "evolution", "chain_reaction"],
                        trace_type="post"
                    )
                    self.p.add_to_h_field(post_mode)
                else:
                    print(f"⚠️ Не удалось опубликовать пост (возможно, 429)")
            
            # Ждём до следующего цикла
            time.sleep(self.cycle_minutes * 60)
    
    def stop(self):
        """Останавливает движок"""
        self.is_running = False


# Функция для запуска в отдельном потоке
def start_evolution_engine(personality: Personality, cycle_minutes: int = 16) -> EvolutionEngine:
    """Запускает движок эволюции в фоновом потоке"""
    engine = EvolutionEngine(personality, cycle_minutes)
    thread = threading.Thread(target=engine.run_loop, daemon=True)
    thread.start()
    return engine