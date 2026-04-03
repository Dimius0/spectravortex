"""
load_fractal.py — загрузка текстов с фрактальной разбивкой
Версия 1.0

Создаёт поле H с модами на всех масштабах:
- 0.1 (буквы/символы)
- 0.3 (слоги)
- 1.0 (слова)
- 3.0 (словосочетания)
- 10.0 (предложения)
- 30.0 (абзацы)
- 100.0 (весь текст)
"""
import sys
import os
import re
import time
import math
import json
from typing import Dict, List, Optional, Any
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rizoma.personality import Personality, SpectralMode
from rizoma.vortex import SpectralComponent
from rizoma.fractal_split import fractal_split, FRACTAL_SCALES


# ========== НАСТРОЙКА ==========
SOURCE_PATH = r"C:\Users\Dim\Documents\vmms_texts\russian_classics"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 
                           'personalities', 'p016_fractal_v16.json')
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data',
                             'personalities', 'p016_fractal_progress.json')

# Параметры загрузки
SAVE_INTERVAL_BLOCKS = 200      # сохранять каждые 200 блоков
MAX_WORKERS = 1                  # пока один поток (для простоты)


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_word_spectrum_from_chars(word: str) -> Dict[float, SpectralComponent]:
    """Временная эвристика: слово → спектр из букв"""
    spectrum = {}
    for ch in word.lower():
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


def extract_text(filepath: str) -> Optional[str]:
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


def compute_block_spectrum(words: List[str], field) -> Dict[float, SpectralComponent]:
    """Вычисляет спектр блока по словам"""
    spectrum = {}
    
    for w in set(words):
        if w in field.vortices:
            for tau, comp in field.vortices[w].spectrum.items():
                if tau not in spectrum:
                    spectrum[tau] = SpectralComponent(0.0, 0.0)
                spectrum[tau].amplitude += comp.amplitude
                spectrum[tau].phase = (spectrum[tau].phase + comp.phase) % (2 * math.pi)
        else:
            wspec = get_word_spectrum_from_chars(w)
            for tau, comp in wspec.items():
                if tau not in spectrum:
                    spectrum[tau] = SpectralComponent(0.0, 0.0)
                spectrum[tau].amplitude += comp.amplitude
                spectrum[tau].phase = (spectrum[tau].phase + comp.phase) % (2 * math.pi)
    
    total = sum(c.amplitude for c in spectrum.values())
    if total > 0:
        for comp in spectrum.values():
            comp.amplitude /= total
    
    return spectrum


def get_block_position_hash(block: Dict[str, Any]) -> int:
    """Генерирует хеш для блока (уникальный идентификатор)"""
    return hash(f"{block['scale']}_{block['position']}_{block['content'][:100]}")


# ========== ОСНОВНАЯ ЗАГРУЗКА ==========

def load_progress():
    """Загружает прогресс загрузки"""
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"processed_files": [], "total_blocks": 0}


def save_progress(progress):
    """Сохраняет прогресс"""
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def process_file(filepath: str, filename: str, field: Personality, progress: Dict, verbose: bool = True):
    """Обрабатывает один файл с фрактальной разбивкой"""
    
    if verbose:
        print(f"\n📖 {filename}")
    
    content = extract_text(filepath)
    if not content or len(content) < 100:
        if verbose:
            print(f" ⚠️ Не удалось прочитать или слишком короткий")
        return 0
    
    # Фрактальная разбивка
    blocks = fractal_split(content)
    
    if verbose:
        print(f" Фрактальных блоков: {len(blocks)}")
        # Статистика по масштабам
        scale_counts = {}
        for b in blocks:
            s = b["scale"]
            scale_counts[s] = scale_counts.get(s, 0) + 1
        for s in sorted(scale_counts.keys()):
            print(f"   scale={s:5.1f}: {scale_counts[s]:3d} блоков")
    
    file_blocks = 0
    file_words = set()
    
    for block_data in blocks:
        block = block_data["content"]
        scale = block_data["scale"]
        position = block_data["position"]
        
        if len(block) < 30:
            continue
        
        # Извлекаем слова
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', block.lower())
        if not words:
            continue
        
        file_words.update(words)
        
        # Вычисляем спектр блока
        block_spectrum = compute_block_spectrum(words, field)
        
        if not block_spectrum:
            block_tau = 16.0
        else:
            block_tau = max(block_spectrum.items(), key=lambda x: x[1].amplitude)[0]
        
        # Координаты (эвристика: по τ и позиции)
        theta = position * 2 * math.pi
        phi = (block_tau / 33.0) * math.pi
        r = block_tau / 10.0
        x = r * math.sin(theta) * math.cos(phi)
        y = r * math.sin(theta) * math.sin(phi)
        z = r * math.cos(theta)
        
        # 1. Добавляем слова (вихри)
        for w in set(words):
            if w not in field.vortices:
                wspec = get_word_spectrum_from_chars(w)
                field.add_vortex(w, wspec, x, y, z, scale=1.0)
                field.create_superposition(w, [w])
            else:
                vortex = field.vortices[w]
                vortex.x = vortex.x * 0.9 + x * 0.1
                vortex.y = vortex.y * 0.9 + y * 0.1
                vortex.z = vortex.z * 0.9 + z * 0.1
                vortex.register_use()
        
        # 2. Создаём моду с контентом (с указанием масштаба!)
        mode = SpectralMode(
            tau=block_tau,
            amplitude=0.15,
            content=block[:1500],  # ограничиваем для памяти
            trace_id=f"fractal_{scale}_{int(position*1000)}_{hash(block[:100])}",
            themes=["text", f"scale_{scale}"],
            scale=scale  # ← КЛЮЧЕВОЕ: сохраняем масштаб!
        )
        field.add_to_h_field(mode)
        
        file_blocks += 1
        
        # Периодическое сохранение
        if file_blocks % SAVE_INTERVAL_BLOCKS == 0:
            progress["total_blocks"] += file_blocks
            save_progress(progress)
            field.save(OUTPUT_PATH)
            if verbose:
                print(f" 💾 Сохранено ({file_blocks} блоков)")
    
    if verbose:
        print(f" → {file_blocks} блоков, {len(file_words)} уникальных слов")
    
    return file_blocks


# ========== ОСНОВНОЙ ЦИКЛ ==========

def main():
    print("=" * 70)
    print("🌀 ФРАКТАЛЬНАЯ ЗАГРУЗКА ПОЛЯ H (ВЕРСИЯ 16.0)")
    print(f" Источник: {SOURCE_PATH}")
    print(f" Масштабы: {FRACTAL_SCALES}")
    print("=" * 70)
    
    # Загружаем прогресс
    progress = load_progress()
    processed_files = set(progress.get("processed_files", []))
    total_blocks = progress.get("total_blocks", 0)
    
    # Загружаем или создаём поле
    try:
        if os.path.exists(OUTPUT_PATH):
            p = Personality.load(OUTPUT_PATH)
            print(f"\n📂 Загружено поле: слов={len(p.vortices)}, мод={len(p.h_field)}")
        else:
            raise FileNotFoundError
    except:
        p = Personality(id="p016", name="VMMS Field Fractal v16")
        print(f"\n✨ Создано новое поле")
    
    start_time = time.time()
    
    # Получаем список файлов
    files = [f for f in os.listdir(SOURCE_PATH) 
             if f.endswith(('.txt', '.md')) and f not in processed_files]
    
    print(f"\n📄 Файлов к загрузке: {len(files)}")
    print(f" Уже загружено: {len(processed_files)}")
    print(f" Всего блоков: {total_blocks}")
    
    for filename in files:
        filepath = os.path.join(SOURCE_PATH, filename)
        
        file_blocks = process_file(filepath, filename, p, progress)
        
        if file_blocks > 0:
            processed_files.add(filename)
            progress["processed_files"] = list(processed_files)
            progress["total_blocks"] = total_blocks + file_blocks
            save_progress(progress)
            
            # Сохраняем после файла
            p.save(OUTPUT_PATH)
            print(f" 💾 Сохранено после файла (слов: {len(p.vortices)}, мод: {len(p.h_field)})")
        
        elapsed = time.time() - start_time
        print(f" ⏱️ Прошло: {elapsed/60:.1f} мин")
    
    # Финальное сохранение
    p.save(OUTPUT_PATH)
    
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print(f" Файлов обработано: {len(processed_files)}")
    print(f" Блоков загружено: {progress['total_blocks']}")
    print(f" Слов в поле: {len(p.vortices)}")
    print(f" Мод в поле: {len(p.h_field)}")
    
    # Статистика по масштабам
    scale_stats = defaultdict(int)
    for mode in p.h_field:
        scale_stats[mode.scale] += 1
    
    print("\n📊 Моды по масштабам:")
    for scale in sorted(scale_stats.keys()):
        print(f"   scale={scale:5.1f}: {scale_stats[scale]:5d} мод")
    
    if os.path.exists(OUTPUT_PATH):
        size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
        print(f"\n💾 Размер JSON: {size_mb:.1f} МБ")
    
    print(f"\n⏱️ Время: {(time.time() - start_time)/60:.1f} мин")
    print("\n✅ ФРАКТАЛЬНАЯ ЗАГРУЗКА ЗАВЕРШЕНА")


if __name__ == "__main__":
    main()