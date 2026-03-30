#!/usr/bin/env python3
"""
Универсальный загрузчик текстов (архитектура 11.0)
Буквы как ноты, слова как аккорды
"""
import sys
import os
import re
import time
from pdf2image import convert_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality, SpectralMode

# ========== НАСТРОЙКА ==========
SOURCE_PATH = r"C:\Users\Dim\Documents\vmms_texts\physics_small"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')
# ===============================

print("="*70)
print("🌀 УНИВЕРСАЛЬНЫЙ ЗАГРУЗЧИК v11.0")
print(" Буквы как ноты, слова как аккорды")
print(f" Источник: {SOURCE_PATH}")
print("="*70)

start_time = time.time()

# Загружаем поле
try:
    p = Personality.load(OUTPUT_PATH)
    print(f"\n📂 Загружено поле: {len(p.vortices)} слов, {len(p.h_field)} мод")
    print(f"   Символов в алфавите: {len(p.char_tau)}")
except:
    p = Personality(id="p016", name="VMMS Field")
    print(f"\n✨ Создано новое поле")
    print(f"   Базовый алфавит: {len(p.char_tau)} букв (τ=1..33)")

def extract_text_from_pdf(filepath):
    try:
        images = convert_from_path(filepath, dpi=150, poppler_path=POPPLER_PATH)
        text_parts = []
        for img in images:
            page_text = pytesseract.image_to_string(img, lang='rus+eng')
            if page_text.strip():
                text_parts.append(page_text)
        return "\n\n".join(text_parts) if text_parts else None
    except Exception as e:
        print(f" ⚠️ Ошибка PDF: {e}")
        return None

def extract_text_from_txt(filepath):
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
    filepath = os.path.join(SOURCE_PATH, filename)
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.pdf':
        content = extract_text_from_pdf(filepath)
    elif ext in ['.txt', '.md']:
        content = extract_text_from_txt(filepath)
    else:
        continue
    
    if not content or len(content) < 100:
        continue
    
    blocks = re.split(r'\n\s*\n', content)
    print(f"\n📄 {filename}: {len(blocks)} блоков")
    
    file_blocks = 0
    
    for block in blocks:
        block = block.strip()
        if len(block) < 100:
            continue
        
        # 1. Вычисляем спектр блока
        block_spectrum = p.phrase_spectrum(block)
        block_tau = p.get_dominant_tau(block_spectrum) or 1.0
        
        # 2. Обновляем все слова из блока
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ0-9]+\b', block.lower())
        for w in words:
            p.add_word(w, block_spectrum, weight=0.1)
        
        # 3. Создаём моду с контентом
        mode = SpectralMode(
            tau=block_tau,
            amplitude=0.15,
            content=block[:1500],
            trace_id=f"block_{total_files}_{file_blocks}"
        )
        p.add_to_h_field(mode)
        
        file_blocks += 1
        total_blocks += 1
        
        if file_blocks % 100 == 0:
            print(f" Обработано блоков: {file_blocks}")
    
    print(f" → {file_blocks} блоков")
    total_files += 1
    
    p.save(OUTPUT_PATH)
    print(f" 💾 Сохранено (слов: {len(p.vortices)}, мод: {len(p.h_field)}, символов: {len(p.char_tau)})")
    
    elapsed = time.time() - start_time
    print(f" ⏱️ Прошло: {elapsed/60:.1f} мин")

p.save(OUTPUT_PATH)

print("\n" + "="*70)
print("📊 ИТОГОВАЯ СТАТИСТИКА")
print("="*70)
print(f" Файлов: {total_files}")
print(f" Блоков: {total_blocks}")
print(f" Слов в поле: {len(p.vortices)}")
print(f" Мод: {len(p.h_field)}")
print(f" Символов в алфавите: {len(p.char_tau)}")
print(f" Время: {(time.time() - start_time)/60:.1f} мин")

print("\n✅ ЗАГРУЗКА ЗАВЕРШЕНА")