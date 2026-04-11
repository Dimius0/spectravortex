# scripts/load_field_v15_advanced.py
"""
Загрузка текстов в поле H версии 15.0
- Сохранение каждые N блоков
- Паузы для охлаждения
- Контроль памяти
- Многопоточность (8 ядер)
"""

import sys
import os
import re
import json
import time
import math
import threading
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from pathlib import Path

# Импорт psutil с проверкой
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil не установлен. Контроль памяти отключён.")
    print("   Установи: pip install psutil")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality
from rizoma.vortex import SpectralComponent


# ========== НАСТРОЙКА ==========
SOURCE_PATH = r"C:\Users\Dim\Documents\vmms_texts\russian_classics"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full_v15.json')
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_progress_v15.json')

# Параметры загрузки
SAVE_INTERVAL_BLOCKS = 200          # сохранять каждые 200 блоков
COOLDOWN_BLOCKS = 100               # пауза после каждых 100 блоков
COOLDOWN_SECONDS = 15               # длительность паузы (сек)
MAX_MEMORY_MB = 1500                # максимальная память (1.5 ГБ)
MAX_WORKERS = 8                     # количество потоков (8 ядер)
# ===============================


def get_memory_usage_mb() -> float:
    """Возвращает текущее использование памяти в МБ"""
    if HAS_PSUTIL:
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    return 0.0


def check_memory():
    """Проверяет память и делает паузу если нужно"""
    if not HAS_PSUTIL:
        return False
    mem = get_memory_usage_mb()
    if mem > MAX_MEMORY_MB:
        print(f"   ⚠️ Память: {mem:.0f} МБ > {MAX_MEMORY_MB} МБ. Пауза 30 сек...")
        time.sleep(30)
        return True
    return False


def load_progress():
    """Загружает прогресс загрузки"""
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"processed_files": [], "total_blocks": 0, "last_save": 0}


def save_progress(progress):
    """Сохраняет прогресс"""
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def get_word_spectrum_from_chars(word: str) -> Dict[float, SpectralComponent]:
    """Временная эвристика: слово → спектр из букв"""
    spectrum = {}
    for ch in word.lower():
        # τ от 1 до 66 (русские + латиница)
        tau = (ord(ch) % 66) + 1
        if tau not in spectrum:
            spectrum[tau] = SpectralComponent(0.0, 0.0)
        spectrum[tau].amplitude += 1.0
    
    total = sum(c.amplitude for c in spectrum.values())
    if total > 0:
        for tau, comp in spectrum.items():
            comp.amplitude /= total
            comp.phase = (tau * hash(word) % 1000) / 1000 * 2 * math.pi
    
    return spectrum


def extract_text_from_txt(filepath):
    """Извлекает текст из TXT или MD"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(filepath, 'r', encoding='cp1251') as f:
                return f.read()
        except:
            return None


def process_block(block_data):
    """Обрабатывает один блок (для многопоточности)"""
    block, idx, total = block_data
    block = block.strip()
    if len(block) < 100:
        return None
    
    # Извлекаем слова
    words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', block.lower())
    if not words:
        return None
    
    # Вычисляем спектр блока (упрощённо для многопоточности)
    block_tau = 16.0
    
    # Эвристика координат
    theta = (hash(block) % 360) * math.pi / 180
    phi = ((hash(block) // 360) % 180) * math.pi / 180
    r = block_tau / 10.0
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)
    
    return {
        "words": words,
        "x": x, "y": y, "z": z,
        "tau": block_tau,
        "block": block[:500]
    }


def process_file(filepath, filename, p, progress, lock):
    """Обрабатывает один файл"""
    print(f"\n📖 {filename}")
    
    content = extract_text_from_txt(filepath)
    if not content or len(content) < 100:
        print(f"   ⚠️ Не удалось прочитать")
        return 0
    
    # Разбиваем на блоки
    blocks = re.split(r'\n\s*\n', content)
    print(f"   Блоков: {len(blocks)}")
    
    # Подготовка данных для многопоточности
    block_data = [(block, i, len(blocks)) for i, block in enumerate(blocks)]
    
    file_blocks = 0
    file_words = set()
    processed = 0
    
    # Многопоточная обработка блоков
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_block, data): data for data in block_data}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                processed += 1
                file_blocks += 1
                file_words.update(result["words"])
                
                # Обновляем поле (с блокировкой)
                with lock:
                    for w in result["words"]:
                        if w not in p.vortices:
                            wspec = get_word_spectrum_from_chars(w)
                            p.add_vortex(w, wspec, result["x"], result["y"], result["z"], scale=1.0)
                            p.create_superposition(w, [w])
                        else:
                            vortex = p.vortices[w]
                            vortex.x = vortex.x * 0.9 + result["x"] * 0.1
                            vortex.y = vortex.y * 0.9 + result["y"] * 0.1
                            vortex.z = vortex.z * 0.9 + result["z"] * 0.1
                            vortex.register_use()
                
                # Сохраняем по интервалу
                if processed % SAVE_INTERVAL_BLOCKS == 0:
                    with lock:
                        progress["total_blocks"] += file_blocks
                        save_progress(progress)
                        p.save(OUTPUT_PATH)
                    print(f"      💾 Сохранено ({processed} блоков)")
                
                # Пауза для охлаждения
                if processed % COOLDOWN_BLOCKS == 0:
                    print(f"      😴 Пауза {COOLDOWN_SECONDS} сек (охлаждение)")
                    time.sleep(COOLDOWN_SECONDS)
                
                # Контроль памяти
                if check_memory():
                    time.sleep(10)
    
    print(f"   → {file_blocks} блоков, {len(file_words)} уникальных слов")
    return file_blocks


# ========== ОСНОВНОЙ ЦИКЛ ==========
print("="*70)
print("🌀 ЗАГРУЗКА ПОЛЯ H (ВЕРСИЯ 15.0) — УМНАЯ")
print(f" Источник: {SOURCE_PATH}")
print(f" Сохранение: каждые {SAVE_INTERVAL_BLOCKS} блоков")
print(f" Пауза: каждые {COOLDOWN_BLOCKS} блоков на {COOLDOWN_SECONDS} сек")
print(f" Память: макс {MAX_MEMORY_MB} МБ")
print(f" Потоки: {MAX_WORKERS} (на {os.cpu_count()} ядер)")
print("="*70)

# Загружаем прогресс
progress = load_progress()
processed_files = set(progress.get("processed_files", []))
total_blocks_global = progress.get("total_blocks", 0)

# Загружаем или создаём поле
try:
    p = Personality.load(OUTPUT_PATH)
    print(f"\n📂 Загружено поле: {len(p.vortices)} слов")
except:
    p = Personality(id="p016", name="VMMS Field v15")
    print(f"\n✨ Создано новое поле")

start_time = time.time()

# Получаем список файлов
files = [f for f in os.listdir(SOURCE_PATH) 
         if f.endswith(('.txt', '.md')) and f not in processed_files]

print(f"\n📄 Файлов к загрузке: {len(files)}")
print(f"   Уже загружено: {len(processed_files)}")
print(f"   Всего блоков: {total_blocks_global}")

lock = threading.Lock()

for filename in files:
    filepath = os.path.join(SOURCE_PATH, filename)
    
    file_blocks = process_file(filepath, filename, p, progress, lock)
    
    if file_blocks > 0:
        processed_files.add(filename)
        progress["processed_files"] = list(processed_files)
        progress["total_blocks"] = total_blocks_global + file_blocks
        save_progress(progress)
        
        # Сохраняем после файла
        p.save(OUTPUT_PATH)
        print(f"   💾 Сохранено после файла (слов: {len(p.vortices)})")
    
    elapsed = time.time() - start_time
    print(f"   ⏱️ Прошло: {elapsed/60:.1f} мин")

# Финальное сохранение
p.save(OUTPUT_PATH)

print("\n" + "="*70)
print("📊 ИТОГОВАЯ СТАТИСТИКА")
print("="*70)
print(f" Файлов обработано: {len(processed_files)}")
print(f" Блоков загружено: {progress['total_blocks']}")
print(f" Слов в поле: {len(p.vortices)}")
print(f" Квантовых состояний: {len(p.resonance_engine.quantum.states)}")

if os.path.exists(OUTPUT_PATH):
    size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
    print(f" Размер JSON: {size_mb:.1f} МБ")

print(f" Время: {elapsed/60:.1f} мин")

print("\n✅ ЗАГРУЗКА ЗАВЕРШЕНА")