# scripts/load_field_correct.py
"""
Правильная загрузка поля H — вихри и моды одновременно
"""
import sys
import os
import re
import time
import math
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rizoma.personality import Personality, SpectralMode
from rizoma.vortex import SpectralComponent

# ========== НАСТРОЙКА ==========
SOURCE_PATH = r"C:\Users\Dim\Documents\vmms_texts\russian_classics"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full_v15.json')
# ===============================

print("="*70)
print("🌀 ПРАВИЛЬНАЯ ЗАГРУЗКА ПОЛЯ H (ВИХРИ + МОДЫ)")
print(f" Источник: {SOURCE_PATH}")
print("="*70)

# Создаём новое поле
p = Personality(id="p016", name="VMMS Field v15")

def get_word_spectrum(word: str) -> Dict[float, SpectralComponent]:
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

def extract_text(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(filepath, 'r', encoding='cp1251') as f:
                return f.read()
        except:
            return None

total_blocks = 0
total_files = 0

for filename in os.listdir(SOURCE_PATH):
    if not filename.endswith(('.txt', '.md')):
        continue
    
    filepath = os.path.join(SOURCE_PATH, filename)
    print(f"\n📖 {filename}")
    
    content = extract_text(filepath)
    if not content:
        continue
    
    blocks = re.split(r'\n\s*\n', content)
    print(f"   Блоков: {len(blocks)}")
    
    file_blocks = 0
    for block in blocks:
        block = block.strip()
        if len(block) < 100:
            continue
        
        # Извлекаем слова
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', block.lower())
        
        # Вычисляем спектр блока
        block_spectrum = {}
        for w in words:
            wspec = get_word_spectrum(w)
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
        
        # Координаты (эвристика)
        theta = (hash(block) % 360) * math.pi / 180
        phi = ((hash(block) // 360) % 180) * math.pi / 180
        r = block_tau / 10.0
        x = r * math.sin(theta) * math.cos(phi)
        y = r * math.sin(theta) * math.sin(phi)
        z = r * math.cos(theta)
        
        # 1. СОЗДАЁМ ВИХРИ (слова)
        for w in set(words):
            if w not in p.vortices:
                wspec = get_word_spectrum(w)
                p.add_vortex(w, wspec, x, y, z, scale=1.0)
                p.create_superposition(w, [w])
            else:
                vortex = p.vortices[w]
                vortex.x = vortex.x * 0.9 + x * 0.1
                vortex.y = vortex.y * 0.9 + y * 0.1
                vortex.z = vortex.z * 0.9 + z * 0.1
                vortex.register_use()
        
        # 2. СОЗДАЁМ МОДУ С КОНТЕНТОМ (это ключевое!)
        mode = SpectralMode(
            tau=block_tau,
            amplitude=0.15,
            content=block[:1500],
            trace_id=f"block_{total_files}_{file_blocks}",
            themes=["text"]
        )
        p.add_to_h_field(mode)
        
        file_blocks += 1
        total_blocks += 1
        
        if file_blocks % 100 == 0:
            print(f"      Обработано блоков: {file_blocks}")
    
    print(f"   → {file_blocks} блоков")
    total_files += 1
    
    p.save(OUTPUT_PATH)
    print(f"   💾 Сохранено (слов: {len(p.vortices)}, мод: {len(p.h_field)})")

print("\n" + "="*70)
print("📊 ИТОГОВАЯ СТАТИСТИКА")
print("="*70)
print(f" Файлов: {total_files}")
print(f" Блоков: {total_blocks}")
print(f" Слов: {len(p.vortices)}")
print(f" Мод: {len(p.h_field)}")

p.save(OUTPUT_PATH)
print("\n✅ ЗАГРУЗКА ЗАВЕРШЕНА")