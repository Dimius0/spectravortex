"""
load_fractal_v16_1.py — загрузка текстов с фрактальной разбивкой
ерсия 16.1 — с поддержкой complexity и  С  
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

from rizoma.personality_v16_1 import Personality, SpectralMode
from rizoma.vortex import SpectralComponent
from rizoma.fractal_split_v16_1 import fractal_split, FRACTAL_SCALES
from rizoma.complexity_utils import detect_complexity


# ========== СТ ==========
SOURCE_PATH = r"C:\Users\Dim\Documents\vmms_texts\russian_classics"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_v16_1.json')
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_fractal_progress_v16_1.json')

SAVE_INTERVAL_BLOCKS = 200
MAX_WORKERS = 1


# ========== СТЬЫ  ==========

def get_word_spectrum_from_chars(word: str) -> Dict[float, SpectralComponent]:
    """ременная эвристика: слово → спектр из букв"""
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
    """звлекает текст из TXT или MD"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(filepath, 'r', encoding='cp1251') as f:
                return f.read()
        except:
            return None


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"processed_files": [], "total_blocks": 0, "added_words": set()}


def save_progress(progress):
    # реобразуем set в list для JSON
    progress_copy = progress.copy()
    if "added_words" in progress_copy:
        progress_copy["added_words"] = list(progress_copy["added_words"])
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress_copy, f, ensure_ascii=False, indent=2)


# ========== СЯ  ==========

def main():
    print("=" * 70)
    print("🌀 ТЬЯ  Я H (СЯ 16.1)")
    print("   с добавлением слов как мод (масштаб 1.0)")
    print(f" сточник: {SOURCE_PATH}")
    print(f" асштабы: {FRACTAL_SCALES}")
    print("=" * 70)
    
    progress = load_progress()
    processed_files = set(progress.get("processed_files", []))
    added_words = set(progress.get("added_words", []))
    total_blocks = progress.get("total_blocks", 0)
    
    try:
        if os.path.exists(OUTPUT_PATH):
            p = Personality.load(OUTPUT_PATH)
            print(f"\n📂 агружено поле: слов={len(p.vortices)}, мод={len(p.h_field)}")
        else:
            raise FileNotFoundError
    except:
        p = Personality(id="p016", name="VMMS Field v16.1")
        print(f"\n✨ Создано новое поле")
    
    start_time = time.time()
    
    files = [f for f in os.listdir(SOURCE_PATH) 
             if f.endswith(('.txt', '.md')) and f not in processed_files]
    
    print(f"\n📄 айлов к загрузке: {len(files)}")
    print(f" же загружено: {len(processed_files)}")
    print(f" же добавлено слов как мод: {len(added_words)}")
    print(f" сего блоков: {total_blocks}")
    
    for filename in files:
        filepath = os.path.join(SOURCE_PATH, filename)
        print(f"\n📖 {filename}")
        
        content = extract_text(filepath)
        if not content:
            print(f" ⚠️ е удалось прочитать")
            continue
        
        blocks = fractal_split(content)
        print(f" рактальных блоков: {len(blocks)}")
        
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
            
            words = re.findall(r'\b[a-zA-Zа-я-Яё]{4,}\b', block.lower())
            if not words:
                continue
            
            file_words.update(words)
            
            # ычисляем спектр блока
            block_spectrum = {}
            for w in set(words):
                if w in p.vortices:
                    for tau, comp in p.vortices[w].spectrum.items():
                        if tau not in block_spectrum:
                            block_spectrum[tau] = SpectralComponent(0.0, 0.0)
                        block_spectrum[tau].amplitude += comp.amplitude
                        block_spectrum[tau].phase = (block_spectrum[tau].phase + comp.phase) % (2 * math.pi)
                else:
                    wspec = get_word_spectrum_from_chars(w)
                    for tau, comp in wspec.items():
                        if tau not in block_spectrum:
                            block_spectrum[tau] = SpectralComponent(0.0, 0.0)
                        block_spectrum[tau].amplitude += comp.amplitude
                        block_spectrum[tau].phase = (block_spectrum[tau].phase + comp.phase) % (2 * math.pi)
            
            total_amp = sum(c.amplitude for c in block_spectrum.values())
            if total_amp > 0:
                for comp in block_spectrum.values():
                    comp.amplitude /= total_amp
            
            block_tau = max(block_spectrum.items(), key=lambda x: x[1].amplitude)[0] if block_spectrum else 16.0
            
            # оординаты
            theta = position * 2 * math.pi
            phi = (block_tau / 33.0) * math.pi
            r = block_tau / 10.0
            x = r * math.sin(theta) * math.cos(phi)
            y = r * math.sin(theta) * math.sin(phi)
            z = r * math.cos(theta)
            
            # обавляем слова как Х
            for w in set(words):
                if w not in p.vortices:
                    wspec = get_word_spectrum_from_chars(w)
                    p.add_vortex(w, wspec, x, y, z, scale=1.0)
                    p.create_superposition(w, [w])
                else:
                    vortex = p.vortices[w]
                    vortex.x = vortex.x * 0.9 + x * 0.1
                    vortex.y = vortex.y * 0.9 + y * 0.1
                    vortex.z = vortex.z * 0.9 + z * 0.1
                    vortex.register_use()
                
                # Я С  Ы (масштаб 1.0)
                if w not in added_words:
                    word_mode = SpectralMode(
                        tau=block_tau,
                        amplitude=0.1,
                        content=w,
                        trace_id=f"word_{w}_{hash(w)}",
                        themes=["word", "scale_1.0"],
                        scale=1.0,
                        complexity=detect_complexity(w)
                    )
                    p.add_to_h_field(word_mode)
                    added_words.add(w)
            
            # Создаём моду для блока (с complexity)
            mode = SpectralMode(
                tau=block_tau,
                amplitude=0.15,
                content=block[:1500],
                trace_id=f"fractal_{scale}_{int(position*1000)}_{hash(block[:100])}",
                themes=["text", f"scale_{scale}"],
                scale=scale,
                complexity=detect_complexity(block)
            )
            p.add_to_h_field(mode)
            
            file_blocks += 1
            total_blocks += 1
            
            if file_blocks % SAVE_INTERVAL_BLOCKS == 0:
                progress["total_blocks"] = total_blocks
                progress["added_words"] = added_words
                save_progress(progress)
                p.save(OUTPUT_PATH)
                print(f" 💾 Сохранено ({file_blocks} блоков)")
        
        print(f" → {file_blocks} блоков, {len(file_words)} уникальных слов")
        
        processed_files.add(filename)
        progress["processed_files"] = list(processed_files)
        progress["total_blocks"] = total_blocks
        progress["added_words"] = added_words
        save_progress(progress)
        
        p.save(OUTPUT_PATH)
        print(f" 💾 Сохранено после файла (слов: {len(p.vortices)}, мод: {len(p.h_field)})")
        
        elapsed = time.time() - start_time
        print(f" ⏱️ рошло: {elapsed/60:.1f} мин")
    
    p.save(OUTPUT_PATH)
    
    print("\n" + "=" * 70)
    print("📊 ТЯ СТТСТ")
    print("=" * 70)
    print(f" айлов обработано: {len(processed_files)}")
    print(f" локов загружено: {total_blocks}")
    print(f" Слов в поле: {len(p.vortices)}")
    print(f" од в поле: {len(p.h_field)}")
    print(f" обавлено слов как мод: {len(added_words)}")
    
    # Статистика по масштабам
    scale_stats = defaultdict(int)
    for mode in p.h_field:
        scale_stats[mode.scale] += 1
    
    print("\n📊 оды по масштабам:")
    for scale in sorted(scale_stats.keys()):
        print(f"   scale={scale:5.1f}: {scale_stats[scale]:5d} мод")
    
    # Статистика по complexity
    complexity_stats = defaultdict(int)
    for mode in p.h_field:
        if hasattr(mode, 'complexity'):
            complexity_stats[mode.complexity] += 1
        else:
            complexity_stats[0] += 1
    
    print("\n📊 оды по уровню сложности (complexity):")
    names = {0: "не определён", 1: "бытовой", 2: "научный", 3: "", 4: "метафорический"}
    for c in sorted(complexity_stats.keys()):
        print(f"   complexity={c} ({names.get(c, '?')}): {complexity_stats[c]:5d} мод")
    
    if os.path.exists(OUTPUT_PATH):
        size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
        print(f"\n💾 азмер JSON: {size_mb:.1f} ")
    
    print(f"\n⏱️ ремя: {(time.time() - start_time)/60:.1f} мин")
    print("\n✅ ТЬЯ  v16.1 Ш")


if __name__ == "__main__":
    main()

