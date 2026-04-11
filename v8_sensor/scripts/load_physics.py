#!/usr/bin/env python3
"""
Загрузка физических текстов ВММП с τ=5.2
Фундамент для поля H
"""
import sys
import os
import re
from pdf2image import convert_from_path, pdfinfo_from_path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality, SpectralMode

# ========== НАСТРОЙКА ==========
PHYSICS_PATH = r"C:\Users\Dim\Documents\vmms_texts\physics"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
# ===============================

print("="*60)
print("📚 ЗАГРУЗКА ФИЗИЧЕСКИХ ТЕКСТОВ ВММП")
print(" τ=5.2 — фундамент поля H")
print("="*60)

# Создаём новое поле H (чистое, без старых мод)
p = Personality(id="p016", name="VMMS Physics")
print(f"\n✨ Создано новое поле H")

# Проверяем папку с физикой
if not os.path.exists(PHYSICS_PATH):
    print(f"\n❌ Папка {PHYSICS_PATH} не найдена!")
    print(" Создайте её и положите туда физические тексты.")
    sys.exit(1)

def extract_text_from_pdf(filepath):
    """Извлекает текст из PDF через OCR"""
    try:
        images = convert_from_path(filepath, dpi=150, poppler_path=POPPLER_PATH)
        text_parts = []
        for img in images:
            page_text = pytesseract.image_to_string(img, lang='rus+eng')
            if page_text.strip():
                text_parts.append(page_text)
        return "\n\n".join(text_parts) if text_parts else None
    except Exception as e:
        print(f" ⚠️ Ошибка: {e}")
        return None

def extract_text_from_doc(filepath):
    """Извлекает текст из .doc (упрощённо)"""
    try:
        import olefile
        if not olefile.isOleFile(filepath):
            return None
        ole = olefile.OleFileIO(filepath)
        if ole.exists('WordDocument'):
            data = ole.openstream('WordDocument').read()
            text = data.decode('utf-16-le', errors='ignore')
            text = re.sub(r'[^\w\s\.,!?;:\(\)\[\]\-\—\«\»\№\n]', '', text)
            return text
        return None
    except:
        return None

def extract_text_from_txt(filepath):
    """Извлекает текст из .txt"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='cp1251') as f:
            return f.read()
    except:
        return None

total_blocks = 0
total_files = 0

for filename in os.listdir(PHYSICS_PATH):
    filepath = os.path.join(PHYSICS_PATH, filename)
    ext = os.path.splitext(filename)[1].lower()
    
    print(f"\n📄 {filename}")
    
    # Извлекаем текст в зависимости от формата
    if ext == '.pdf':
        content = extract_text_from_pdf(filepath)
    elif ext == '.doc':
        content = extract_text_from_doc(filepath)
    elif ext in ['.txt', '.md']:
        content = extract_text_from_txt(filepath)
    else:
        print(f" ⚠️ Неподдерживаемый формат: {ext}")
        continue
    
    if not content or len(content) < 100:
        print(f" ⚠️ Не удалось извлечь текст")
        continue
    
    # Разбиваем на блоки
    blocks = re.split(r'\n\s*\n', content)
    print(f" Блоков: {len(blocks)}")
    
    file_blocks = 0
    for block in blocks:
        block = block.strip()
        if len(block) < 80:
            continue
        
        # Очистка
        block = re.sub(r'[^\w\s\.,!?;:\(\)\[\]\-\—\«\»\№\n]', '', block)
        if not block:
            continue
        
        # Фиксированная τ=5.2 для физики
        mode = SpectralMode(
            tau=5.2,
            amplitude=0.15,  # небольшая амплитуда, чтобы не доминировали
            content=block[:1500],
            trace_type="physics",
            themes=["physics", "vmms"],
            trace_id=f"phys_{total_files}_{file_blocks}"
        )
        p.add_to_h_field(mode)
        file_blocks += 1
        total_blocks += 1
    
    print(f" → {file_blocks} блоков загружено")
    total_files += 1

# Сохраняем
save_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_physics.json')
p.save(save_path)

print("\n" + "="*60)
print("📊 ИТОГ")
print("="*60)
print(f" Файлов обработано: {total_files}")
print(f" Блоков загружено: {total_blocks}")
print(f" Мод в поле H: {len(p.h_field)}")
print(f" Слов в словаре: {len(p.word_tau)}")

if p.word_tau:
    print(f"\n Первые 30 слов в словаре (физика):")
    for i, (word, tau) in enumerate(list(p.word_tau.items())[:30]):
        print(f" {word}: {tau:.2f}")

print("\n✅ ФИЗИЧЕСКИЙ ФУНДАМЕНТ ЗАГРУЖЕН")
print("\n🦌 Теперь поле H знает физику ВММП.")