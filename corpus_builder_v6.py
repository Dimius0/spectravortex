#!/usr/bin/env python3
"""
corpus_builder_v6.py — Умный сборщик корпуса (v6.0, без дублирования)
======================================================================
Использует ЕДИНЫЙ VMMPValidator из pipeline_v6.
"""

import json, sys, time, gc, os, re, logging
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import List, Tuple

# Импортируем ВСЁ из pipeline_v6 — включая единый VMMPValidator
from pipeline_v6 import (
    Config, setup_logging,
    LatexFilter, CodeFilter, LanguageFilter, VMMPValidator,
    HAS_VMMP
)


# ============================================================================
# ПАРСЕР
# ============================================================================
def extract_triples(json_file: str, logger: logging.Logger = None) -> List[Tuple[str, str, str]]:
    log = logger or logging.getLogger(__name__)
    log.info(f"Чтение: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        log.error(f"Ошибка: {e}"); return []
    
    triples = []
    for dialogue in data:
        for node in dialogue.get('mapping', {}).values():
            if not node.get('message') or not node['message'].get('fragments'):
                continue
            for frag in node['message']['fragments']:
                content = frag.get('content', '')
                if len(content) < 30: continue
                words = [w for w in re.findall(r'[а-яёa-z]+', content.lower()) if len(w) > 1]
                for i in range(1, len(words) - 1):
                    triples.append((words[i-1], words[i], words[i+1]))
    
    log.info(f"Извлечено троек: {len(triples):,}")
    return triples


# ============================================================================
# АНАЛИЗАТОР КОРПУСА
# ============================================================================
class CorpusAnalyzer:
    def __init__(self, triples):
        self.triples = triples
        self.word_freq = Counter()
        self.tees_freq = Counter()
        for s, t, r in triples:
            self.word_freq[s] += 1; self.word_freq[t] += 1; self.word_freq[r] += 1
            self.tees_freq[t] += 1
    
    def report(self):
        return {
            'total_triples': len(self.triples),
            'unique_words': len(self.word_freq),
            'unique_tees': len(self.tees_freq),
            'top_tees': self.tees_freq.most_common(20)
        }
    
    def print_report(self):
        r = self.report()
        print(f"\n📊 АНАЛИЗ КОРПУСА")
        print(f"   Троек: {r['total_triples']:,}")
        print(f"   Уник. слов: {r['unique_words']:,} | Уник. связок: {r['unique_tees']:,}")
        print(f"   Топ-связки: {', '.join(f'{w}({c})' for w,c in r['top_tees'][:10])}")


# ============================================================================
# СОХРАНЕНИЕ
# ============================================================================
def save_corpus(triples, path, logger=None):
    log = logger or logging.getLogger(__name__)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('{"triples": [\n')
        for i, (s, t, r) in enumerate(triples):
            f.write(f'  {{"source": "{s}", "tees": "{t}", "receiver": "{r}"}}')
            if i < len(triples) - 1: f.write(',\n')
        f.write('\n]}')
    log.info(f"Сохранено: {path} ({os.path.getsize(path)/1024/1024:.1f} MB, {len(triples):,} троек)")


# ============================================================================
# КОНВЕЙЕР
# ============================================================================
def build_corpus(json_file: str, use_vmmp=False, fast_vmmp=True, config=Config, logger=None):
    log = logger or logging.getLogger(__name__)
    log.info("="*50)
    log.info("CORPUS BUILDER v6.0")
    log.info("="*50)
    
    # Извлечение
    t0 = time.time()
    triples = extract_triples(json_file, log)
    if not triples:
        log.error("Нет троек"); return
    
    # Анализ исходного
    CorpusAnalyzer(triples).print_report()
    
    # Фильтры
    filters = [LatexFilter(), CodeFilter(), LanguageFilter(config.UNIVERSAL_TEES)]
    vmmp = VMMPValidator(config, fast_vmmp) if (use_vmmp and HAS_VMMP) else None
    
    log.info(f"Фильтров: {len(filters)}" + (" + VMMP" if vmmp else ""))
    
    # Фильтрация
    log.info(f"Фильтрация {len(triples):,} троек...")
    corpus_ru, corpus_en, corpus_code, corpus_mixed = [], [], [], []
    rejected = Counter()
    lang_filter = filters[-1]
    
    for idx, (src, tee, dst) in enumerate(triples):
        # Фильтры
        passed = True
        for f in filters:
            if not f.check(src, tee, dst):
                rejected[f.name] += 1; passed = False; break
        if not passed: continue
        
        # VMMP (тот же метод check!)
        if vmmp and not vmmp.check(src, tee, dst):
            rejected['VMMP'] += 1; continue
        
        # Классификация
        lang = lang_filter.classify(src, tee, dst)
        if lang == 'ru': corpus_ru.append((src, tee, dst))
        elif lang == 'en': corpus_en.append((src, tee, dst))
        elif lang == 'code': corpus_code.append((src, tee, dst))
        else: corpus_mixed.append((src, tee, dst))
        
        if (idx+1) % 50000 == 0:
            log.info(f"  {idx+1:,}/{len(triples):,} | RU: {len(corpus_ru):,} EN: {len(corpus_en):,}")
    
    # Сохранение
    config.setup_dirs()
    if corpus_ru: save_corpus(corpus_ru, config.CORPUS_DIR / "ru" / "corpus_ru.json", log)
    if corpus_en: save_corpus(corpus_en, config.CORPUS_DIR / "en" / "corpus_en.json", log)
    
    # Итоги
    log.info(f"\n📊 ИТОГИ:")
    log.info(f"   RU: {len(corpus_ru):,} | EN: {len(corpus_en):,} | Code: {len(corpus_code):,} | Mixed: {len(corpus_mixed):,}")
    log.info(f"   Отвергнуто: {sum(rejected.values()):,}")
    for r, c in rejected.most_common():
        log.info(f"      {r}: {c:,}")
    
    for f in filters:
        s = f.get_stats()
        log.info(f"   {f.name}: pass {s['pass_rate']}% ({s['passed']:,}/{s['checked']:,})")
    if vmmp:
        s = vmmp.get_stats()
        log.info(f"   VMMP: pass {s['pass_rate']}% ({s['passed']:,}/{s['checked']:,})")
    
    log.info(f"⏱️  Общее время: {time.time()-t0:.0f} сек")
    log.info("ГОТОВО!")
    
    return {'ru': len(corpus_ru), 'en': len(corpus_en)}


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================
if __name__ == "__main__":
    Config.setup_dirs()
    logger = setup_logging(Config)
    
    json_file = "conversations.json"
    use_vmmp = False
    fast_vmmp = True
    
    for arg in sys.argv[1:]:
        if arg.endswith('.json'): json_file = arg
        elif arg == '--vmmp': use_vmmp = True
        elif arg == '--fast': fast_vmmp = True
    
    build_corpus(json_file, use_vmmp, fast_vmmp, Config, logger)