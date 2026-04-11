#!/usr/bin/env python3
"""
Универсальная загрузка всех текстов из папки
Поддержка: .pdf, .txt, .md, .doc
"""
import sys
import os
import re
from pdf2image import convert_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality, SpectralMode

# ========== НАСТРОЙКА ==========
SOURCE_PATH = r"C:\Users\Dim\Documents\vmms_texts\forum_new_theory"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')
# ===============================

print("="*60)
print("📚 УНИВЕРСАЛЬНАЯ ЗАГРУЗКА ТЕКСТОВ")
print(f" Источник: {SOURCE_PATH}")
print("="*60)

# Загружаем существующее поле H
try:
    p = Personality.load(OUTPUT_PATH)
    print(f"\n📂 Загружено поле H: {len(p.h_field)} мод, {len(p.word_tau)} слов")
except:
    p = Personality(id="p016", name="VMMS Theory")
    print(f"\n✨ Создано новое поле H")

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
        print(f"   ⚠️ Ошибка PDF: {e}")
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

def fallback_tau(block: str) -> float:
    length_factor = min(1.0, len(block) / 200)
    words_set = set(block.split())
    complexity = len(words_set) / max(10, len(block.split()))
    return max(3.0, min(9.0, 5.0 + length_factor * 2 + complexity * 1.5))

total_blocks = 0
total_files = 0

for filename in os.listdir(SOURCE_PATH):
    filepath = os.path.join(SOURCE_PATH, filename)
    ext = os.path.splitext(filename)[1].lower()
    
    print(f"\n📄 {filename}")
    
    if ext == '.pdf':
        content = extract_text_from_pdf(filepath)
    elif ext in ['.txt', '.md']:
        content = extract_text_from_txt(filepath)
    else:
        print(f"   ⚠️ Неподдерживаемый формат: {ext}")
        continue
    
    if not content or len(content) < 100:
        print(f"   ⚠️ Не удалось извлечь текст")
        continue
    
    blocks = re.split(r'\n\s*\n', content)
    print(f"   Блоков: {len(blocks)}")
    
    file_blocks = 0
    for i, block in enumerate(blocks):
        block = block.strip()
        if len(block) < 100:
            continue
        
        tau = p.phrase_tau(block)
        if abs(tau - 5.0) < 0.1:
            tau = fallback_tau(block)
        
        mode = SpectralMode(
            tau=tau,
            amplitude=0.15,
            content=block[:1500],
            trace_type="text",
            themes=["imported"],
            trace_id=f"file_{total_files}_{i}"
        )
        p.add_to_h_field(mode)
        file_blocks += 1
        total_blocks += 1
    
    print(f"   → {file_blocks} блоков загружено")
    total_files += 1
    p.save(OUTPUT_PATH)
    print(f"   💾 Сохранено")

print("\n" + "="*60)
print("📊 ИТОГ")
print("="*60)
print(f" Файлов обработано: {total_files}")
print(f" Блоков загружено: {total_blocks}")
print(f" Мод в поле H: {len(p.h_field)}")
print(f" Слов в словаре: {len(p.word_tau)}")

print("\n🦌 Загрузка завершена!")