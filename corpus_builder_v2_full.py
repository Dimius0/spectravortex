#!/usr/bin/env python3
"""
corpus_builder_v2_full.py — Полный сборщик корпуса (50+ текстов)
==================================================================
Источники:
  1. ArXiv API (научные статьи)
  2. Wikipedia (тематические статьи) — ИСПРАВЛЕНО: добавлен User-Agent
  3. Gutenberg (художественные тексты)
  4. Ручные тексты (ГАРАНТИРОВАННО включаются)
  5. Локальные файлы (если есть)
"""

import json
import re
import time
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import Counter
import sys

# ============================================================================
# 1. КОНФИГУРАЦИЯ
# ============================================================================

# User-Agent для Wikipedia (ОБЯЗАТЕЛЬНО!)
HEADERS = {
    'User-Agent': 'TeesKnowledgeEngine/4.0 (research project; contact@example.com)'
}

class CorpusBuilderV2:
    """
    Сборщик корпуса из 50+ текстов.
    
    ИСПРАВЛЕНИЯ:
    - User-Agent для Wikipedia (без него 403)
    - Ручные тексты ВСЕГДА добавляются первыми
    - Правильный порядок: ручные → локальные → API
    """
    
    def __init__(self, output_dir: Path = Path("./corpus")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.corpus = {}
        self.metadata = {}
        self.stats = Counter()
        self.seen_hashes = set()
    
    def _hash_text(self, text: str) -> str:
        """Хеш текста для дедупликации."""
        sample = text[:500].encode('utf-8')
        return hashlib.md5(sample).hexdigest()
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от мусора."""
        if not text:
            return ""
        
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'https?://\S+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20]
        text = ' '.join(lines)
        
        if len(text) < 100:
            return ""
        
        return text.strip()
    
    def _add_article(self, article: Dict, force: bool = False) -> bool:
        """
        Добавляет статью в корпус.
        Если force=True, добавляет даже при достижении лимита.
        """
        text = self._clean_text(article.get('text', ''))
        if not text:
            return False
        
        text_hash = self._hash_text(text)
        if text_hash in self.seen_hashes:
            self.stats['duplicates'] += 1
            return False
        
        self.seen_hashes.add(text_hash)
        
        source = article.get('source', 'unknown')
        title = article.get('title', 'untitled')
        key = f"{source}_{title}"
        key = re.sub(r'[^a-zA-Zа-яА-Я0-9_]', '_', key)[:100]
        
        if key in self.corpus:
            key = f"{key}_{text_hash[:8]}"
        
        self.corpus[key] = text
        self.metadata[key] = {
            'title': title,
            'source': source,
            'lang': article.get('lang', 'unknown'),
            'category': article.get('category', 'unknown'),
            'length': len(text),
            'added': datetime.now().isoformat()
        }
        
        self.stats['added'] += 1
        return True
    
    def _retry_request(self, url: str, max_retries: int = 3, **kwargs) -> Optional[requests.Response]:
        """Запрос с повторными попытками и User-Agent."""
        timeout = kwargs.pop('timeout', 30)
        headers = kwargs.pop('headers', HEADERS)
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=timeout, **kwargs)
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"    ⚠️ HTTP 403 (доступ запрещён) для {url[:60]}...")
                    break  # 403 не исправится повторными попытками
                elif response.status_code == 429:
                    wait = (attempt + 1) * 5
                    print(f"    ⏳ Rate limit, ждём {wait}с...")
                    time.sleep(wait)
                elif response.status_code == 404:
                    print(f"    ⚠️ HTTP 404 (не найдено): {url[:60]}...")
                    break
                else:
                    print(f"    ⚠️ HTTP {response.status_code}, попытка {attempt+1}")
                    time.sleep(1)
            except requests.exceptions.Timeout:
                print(f"    ⏰ Таймаут (попытка {attempt+1}/{max_retries})")
                time.sleep(2)
            except requests.exceptions.ConnectionError:
                print(f"    🔌 Ошибка соединения (попытка {attempt+1}/{max_retries})")
                time.sleep(3)
            except Exception as e:
                print(f"    ❌ {type(e).__name__}: {e}")
                break
        
        return None
    
    # ========================================================================
    # ArXiv API
    # ========================================================================
    
    def fetch_arxiv_articles(self, query: str, max_results: int = 10) -> List[Dict]:
        """Скачивает статьи с ArXiv."""
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        response = self._retry_request(base_url, params=params)
        if not response:
            print(f"  ⚠️ ArXiv не ответил для '{query}'")
            return []
        
        content = response.text
        articles = []
        entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
        
        for entry in entries[:max_results]:
            try:
                title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                title = title_match.group(1).strip() if title_match else "No title"
                title = re.sub(r'\s+', ' ', title)
                
                summary_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                summary = summary_match.group(1).strip() if summary_match else ""
                summary = re.sub(r'\s+', ' ', summary)
                
                categories = re.findall(r'<category term="([^"]+)"', entry)
                
                if summary and len(summary) > 100:
                    articles.append({
                        'title': title[:200],
                        'text': summary,
                        'category': categories[0] if categories else "unknown",
                        'source': 'arxiv',
                        'lang': 'en',
                        'query': query
                    })
            except Exception as e:
                continue
        
        if articles:
            print(f"  ✅ ArXiv '{query}': {len(articles)} статей")
        return articles
    
    # ========================================================================
    # Wikipedia — ИСПРАВЛЕНО!
    # ========================================================================
    
    def fetch_wikipedia(self, topics: List[str]) -> List[Dict]:
        """
        Скачивает статьи с Wikipedia.
        ИСПРАВЛЕНИЕ: всегда передаёт User-Agent заголовок.
        """
        articles = []
        
        for topic in topics:
            topic_clean = topic.replace(' ', '_')
            
            # Русская Wikipedia
            url_ru = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{topic_clean}"
            response = self._retry_request(url_ru, headers=HEADERS)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    text = data.get('extract', '')
                    if text and len(text) > 100:
                        articles.append({
                            'title': data.get('title', topic),
                            'text': text,
                            'lang': 'ru',
                            'source': 'wikipedia',
                            'category': 'science'
                        })
                        print(f"  ✅ Wikipedia RU: {topic}")
                        time.sleep(0.3)
                        continue
                except:
                    pass
            
            # Английская Wikipedia
            url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic_clean}"
            response = self._retry_request(url_en, headers=HEADERS)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    text = data.get('extract', '')
                    if text and len(text) > 100:
                        articles.append({
                            'title': data.get('title', topic),
                            'text': text,
                            'lang': 'en',
                            'source': 'wikipedia',
                            'category': 'science'
                        })
                        print(f"  ✅ Wikipedia EN: {topic}")
                except:
                    pass
            elif response:
                print(f"  ⚠️ Wikipedia: HTTP {response.status_code} для '{topic}'")
            
            time.sleep(0.5)
        
        return articles
    
    # ========================================================================
    # Gutenberg
    # ========================================================================
    
    def fetch_gutenberg(self, book_ids: List[int]) -> List[Dict]:
        """Скачивает книги с Project Gutenberg."""
        articles = []
        
        for book_id in book_ids:
            # Основной URL
            url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
            response = self._retry_request(url, max_retries=2)
            
            # Альтернативный URL
            if not response:
                url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
                response = self._retry_request(url, max_retries=2)
            
            if not response:
                print(f"  ❌ Gutenberg #{book_id}: недоступен")
                continue
            
            try:
                text = response.text[:5000]
                
                start_markers = [
                    r'\*\*\* START OF.*?\*\*\*',
                    r'\*\*\*START OF.*?\*\*\*',
                    r'START OF.*?PROJECT GUTENBERG',
                ]
                for marker in start_markers:
                    text = re.sub(f'^.*?{marker}', '', text, flags=re.DOTALL)
                
                end_markers = [
                    r'\*\*\* END OF.*?\*\*\*.*$',
                    r'\*\*\*END OF.*?\*\*\*.*$',
                    r'END OF.*?PROJECT GUTENBERG.*$',
                ]
                for marker in end_markers:
                    text = re.sub(f'{marker}.*$', '', text, flags=re.DOTALL)
                
                text = text.strip()
                
                if text and len(text) > 200:
                    articles.append({
                        'title': f"Gutenberg_{book_id}",
                        'text': text,
                        'lang': 'en',
                        'source': 'gutenberg',
                        'category': 'literature'
                    })
                    print(f"  ✅ Gutenberg #{book_id}: {len(text)} символов")
            
            except Exception as e:
                print(f"  ❌ Gutenberg #{book_id}: {e}")
            
            time.sleep(1)
        
        return articles
    
    # ========================================================================
    # Ручные тексты (ГАРАНТИРОВАННОЕ НАПОЛНЕНИЕ)
    # ========================================================================
    
    def create_manual_texts(self) -> List[Dict]:
        """Создаёт 12 тестовых текстов с перекрёстными понятиями."""
        return [
            {
                'title': 'physics_energy',
                'text': (
                    "Энергия является фундаментальной физической величиной, которая характеризует "
                    "способность материи совершать работу. Она не создаётся из ничего и не уничтожается "
                    "бесследно, а только переходит из одной формы в другую. Кинетическая энергия связана "
                    "с движением тел. Потенциальная энергия определяется положением тела в силовом поле. "
                    "Термодинамика описывает превращение энергии в макроскопических системах. Первый закон "
                    "термодинамики утверждает сохранение энергии. Второй закон говорит о неизбежном росте "
                    "энтропии в замкнутых системах. Теплота передаётся от более нагретого тела к менее "
                    "нагретому. Энергия может запасаться в химических связях. Ядерная энергия высвобождается "
                    "при делении или синтезе атомных ядер."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'physics'
            },
            {
                'title': 'physics_quantum',
                'text': (
                    "Квантовая механика описывает поведение материи на микроскопическом уровне. "
                    "В квантовом мире энергия квантуется и принимает дискретные значения. Частицы "
                    "обладают волновыми свойствами, а волны проявляют корпускулярные характеристики. "
                    "Принцип неопределённости Гейзенберга устанавливает фундаментальные ограничения "
                    "на одновременное измерение координаты и импульса. Квантовая запутанность связывает "
                    "частицы независимо от расстояния между ними. Измерение квантовой системы необратимо "
                    "влияет на её состояние."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'physics'
            },
            {
                'title': 'physics_thermodynamics',
                'text': (
                    "Термодинамика изучает законы превращения энергии в физических системах. "
                    "Первый закон термодинамики является формой закона сохранения энергии. "
                    "Второй закон вводит понятие энтропии и утверждает, что в изолированной системе "
                    "энтропия не убывает. Третий закон говорит о недостижимости абсолютного нуля "
                    "температуры. Тепловые машины преобразуют теплоту в механическую работу. "
                    "Цикл Карно описывает идеальный термодинамический процесс."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'physics'
            },
            {
                'title': 'biology_evolution',
                'text': (
                    "Эволюция представляет собой процесс изменения наследственных признаков популяций "
                    "организмов в ряду поколений. Естественный отбор является основным механизмом "
                    "эволюции, предложенным Чарльзом Дарвином. Организмы с признаками, полезными "
                    "для выживания и размножения, оставляют больше потомства. Адаптация связывает "
                    "организм со средой обитания. Мутации создают генетическое разнообразие."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'biology'
            },
            {
                'title': 'biology_cell',
                'text': (
                    "Клетка является структурной и функциональной единицей всех живых организмов. "
                    "Клеточная теория утверждает, что все организмы состоят из клеток. ДНК хранит "
                    "генетическую информацию в последовательности нуклеотидов. Репликация ДНК "
                    "обеспечивает передачу наследственной информации. Транскрипция преобразует ДНК "
                    "в матричную РНК. Трансляция синтезирует белки на рибосомах."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'biology'
            },
            {
                'title': 'biology_dna',
                'text': (
                    "ДНК является молекулой, хранящей генетическую информацию во всех известных "
                    "живых организмах. Двойная спираль ДНК состоит из двух комплементарных цепей. "
                    "Нуклеотиды аденин, тимин, гуанин и цитозин образуют генетический алфавит. "
                    "Ген представляет собой участок ДНК, кодирующий определённый белок."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'biology'
            },
            {
                'title': 'linguistics_grammar',
                'text': (
                    "Грамматика описывает правила построения предложений в языке. Язык является "
                    "системой знаков для коммуникации между людьми. Синтаксис связывает слова "
                    "в предложения согласно определённым правилам. Морфология изучает структуру "
                    "слов и их изменения. Семантика исследует значение языковых выражений."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'linguistics'
            },
            {
                'title': 'linguistics_semantics',
                'text': (
                    "Семантика изучает значение в языке. Лексическая семантика исследует значение "
                    "отдельных слов. Композициональная семантика описывает, как значение целого "
                    "выражения складывается из значений его частей. Полисемия представляет собой "
                    "многозначность слова. Синонимия связывает слова с близким значением."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'linguistics'
            },
            {
                'title': 'philosophy_meaning',
                'text': (
                    "Смысл возникает из связей между понятиями в системе знаний. Язык описывает "
                    "структуру реальности, но не является её точной копией. Мышление связывает "
                    "представления в целостную картину мира. Сознание отражает реальность, "
                    "но всегда через призму субъективного опыта. Смысл всегда контекстуален "
                    "и зависит от системы отсчёта."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'philosophy'
            },
            {
                'title': 'philosophy_consciousness',
                'text': (
                    "Сознание является одной из величайших загадок науки и философии. "
                    "Трудная проблема сознания спрашивает, почему физические процессы в мозге "
                    "сопровождаются субъективным опытом. Квалиа представляют собой качественные "
                    "аспекты сознательного опыта. Нейронаука изучает нейронные корреляты сознания."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'philosophy'
            },
            {
                'title': 'math_topology',
                'text': (
                    "Топология изучает свойства пространств, сохраняющиеся при непрерывных "
                    "деформациях. Гомеоморфизм связывает топологически эквивалентные пространства. "
                    "Топологический заряд характеризует отображения между пространствами. "
                    "Гомотопические группы классифицируют отображения сфер."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'mathematics'
            },
            {
                'title': 'cs_neural_networks',
                'text': (
                    "Нейронные сети представляют собой вычислительные модели, вдохновлённые "
                    "биологическими нейронными сетями. Искусственный нейрон получает входные "
                    "сигналы, вычисляет взвешенную сумму и применяет функцию активации. "
                    "Обучение нейронной сети заключается в настройке весов связей."
                ),
                'lang': 'ru', 'source': 'manual', 'category': 'computer_science'
            },
        ]
    
    # ========================================================================
    # Локальные файлы
    # ========================================================================
    
    def load_local_files(self, directory: Path) -> List[Dict]:
        """Загружает тексты из локальной директории."""
        articles = []
        directory = Path(directory)
        
        if not directory.exists():
            print(f"  ⚠️ Директория не найдена: {directory}")
            return articles
        
        for file_path in directory.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if len(text) > 100:
                    articles.append({
                        'title': file_path.stem,
                        'text': text,
                        'lang': 'unknown',
                        'source': 'local',
                        'category': 'user'
                    })
                    print(f"  ✅ Локальный файл: {file_path.name}")
            except Exception as e:
                print(f"  ⚠️ Ошибка чтения {file_path}: {e}")
        
        return articles
    
    # ========================================================================
    # Единый метод сборки
    # ========================================================================
    
    def build(self, target: int = 50, local_dir: Path = None) -> Dict:
        """
        Сборка полного корпуса.
        
        ВАЖНО: Ручные тексты добавляются ВСЕГДА, даже если target достигнут.
        Порядок: ручные → локальные → ArXiv → Wikipedia → Gutenberg
        """
        print("📚 СБОРКА КОРПУСА")
        print("=" * 70)
        print(f"Цель: {target}+ текстов")
        print(f"Время запуска: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # ЭТАП 0: Ручные тексты ВСЕГДА ПЕРВЫМИ
        print("✍️ [0/5] Ручные тексты (гарантированное наполнение)...")
        manual_articles = self.create_manual_texts()
        for article in manual_articles:
            self._add_article(article)
        print(f"  ✅ Добавлено: {len(manual_articles)} русскоязычных текстов")
        
        # ЭТАП 1: Локальные файлы
        if local_dir:
            print(f"\n📁 [1/5] Локальные файлы из {local_dir}...")
            local_articles = self.load_local_files(local_dir)
            for article in local_articles:
                if len(self.corpus) < target:
                    self._add_article(article)
            print(f"  ✅ Добавлено: {len(local_articles)}")
        else:
            print("\n📁 [1/5] Локальные файлы: не указаны, пропускаем")
        
        # ЭТАП 2: ArXiv
        if len(self.corpus) < target:
            print(f"\n📡 [2/5] ArXiv API (собрано {len(self.corpus)}/{target})...")
            arxiv_queries = [
                ("energy physics", 5),
                ("quantum mechanics", 5),
                ("evolution biology", 5),
                ("language linguistics", 5),
                ("consciousness neuroscience", 5),
                ("thermodynamics entropy", 3),
                ("molecular biology", 3),
                ("neural networks deep learning", 3),
                ("cosmology universe", 3),
                ("topology mathematics", 3),
            ]
            
            for query, count in arxiv_queries:
                if len(self.corpus) >= target:
                    break
                articles = self.fetch_arxiv_articles(query, count)
                for article in articles:
                    if len(self.corpus) >= target:
                        break
                    self._add_article(article)
                time.sleep(2)
        
        # ЭТАП 3: Gutenberg
        if len(self.corpus) < target:
            print(f"\n📚 [3/5] Project Gutenberg (собрано {len(self.corpus)}/{target})...")
            gutenberg_ids = [1342, 2600, 11, 35, 74, 84, 145, 168, 219, 2701, 4300]
            
            for book_id in gutenberg_ids:
                if len(self.corpus) >= target:
                    break
                articles = self.fetch_gutenberg([book_id])
                for article in articles:
                    if len(self.corpus) >= target:
                        break
                    self._add_article(article)
        
        # ЭТАП 4: Wikipedia (с User-Agent!)
        if len(self.corpus) < target:
            print(f"\n📖 [4/5] Wikipedia (собрано {len(self.corpus)}/{target})...")
            wiki_topics = [
                "Energy", "Thermodynamics", "Quantum_mechanics",
                "Evolution", "DNA", "Cell_(biology)",
                "Language", "Grammar", "Semantics",
                "Consciousness", "Philosophy", "Artificial_intelligence",
                "Gravity", "Star", "Galaxy",
                "Ecosystem", "Entropy", "Time",
                "Neural_network", "Genetics",
            ]
            
            for topic in wiki_topics:
                if len(self.corpus) >= target:
                    break
                articles = self.fetch_wikipedia([topic])
                for article in articles:
                    if len(self.corpus) >= target:
                        break
                    self._add_article(article)
        
        # Сохранение
        print(f"\n{'='*70}")
        print("💾 СОХРАНЕНИЕ")
        print(f"{'='*70}")
        
        corpus_path = self.output_dir / "corpus.json"
        metadata_path = self.output_dir / "metadata.json"
        stats_path = self.output_dir / "stats.json"
        
        with open(corpus_path, 'w', encoding='utf-8') as f:
            json.dump(self.corpus, f, ensure_ascii=False, indent=2)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        # Статистика
        total_chars = sum(len(v) for v in self.corpus.values())
        sources = Counter(m['source'] for m in self.metadata.values())
        langs = Counter(m['lang'] for m in self.metadata.values())
        categories = Counter(m['category'] for m in self.metadata.values())
        
        stats = {
            'total_texts': len(self.corpus),
            'total_chars': total_chars,
            'avg_length': total_chars // max(len(self.corpus), 1),
            'sources': dict(sources),
            'languages': dict(langs),
            'categories': dict(categories),
            'build_stats': dict(self.stats),
            'build_time': datetime.now().isoformat()
        }
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Итоги
        print(f"\n{'='*70}")
        print("✅ КОРПУС СОБРАН!")
        print(f"{'='*70}")
        print(f"  📊 Текстов:      {len(self.corpus)}")
        print(f"  📏 Символов:     {total_chars:,}")
        print(f"  📐 Средняя длина: {total_chars // max(len(self.corpus), 1):,} символов")
        print(f"\n  📊 По источникам:")
        for source, count in sources.most_common():
            print(f"     - {source}: {count}")
        print(f"\n  🌐 По языкам:")
        for lang, count in langs.most_common():
            print(f"     - {lang}: {count}")
        print(f"\n  📂 По категориям:")
        for cat, count in categories.most_common()[:10]:
            print(f"     - {cat}: {count}")
        
        return self.corpus


# ============================================================================
# 2. ЗАПУСК
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Сборщик корпуса TEES")
    parser.add_argument("--target", type=int, default=50, help="Целевое количество текстов")
    parser.add_argument("--output", type=str, default="./corpus", help="Директория вывода")
    parser.add_argument("--local", type=str, default=None, help="Директория с локальными .txt файлами")
    
    args = parser.parse_args()
    
    builder = CorpusBuilderV2(output_dir=Path(args.output))
    corpus = builder.build(
        target=args.target,
        local_dir=Path(args.local) if args.local else None
    )
    
    # Всегда выводим подсказку
    print(f"\n🎯 Готово! Запускайте конвейер:")
    print(f"   python tees_knowledge_engine_v4_vmpp.py")
    
    # Проверка на русскоязычные тексты
    ru_count = sum(1 for m in builder.metadata.values() if m.get('lang') == 'ru')
    if ru_count == 0:
        print(f"\n⚠️ В корпусе нет русскоязычных текстов!")
        print(f"   Ручные тексты должны были добавиться. Проверьте corpus/corpus.json")