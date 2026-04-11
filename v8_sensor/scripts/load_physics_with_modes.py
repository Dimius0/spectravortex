#!/usr/bin/env python3
"""
3D-ФРАКТАЛЬНЫЙ ЗАГРУЗЧИК ФИЗИКИ
Вихри + моды одновременно
"""
import sys
import os
import re
import math
import time
from collections import defaultdict
from pdf2image import convert_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality, SpectralMode

# ========== НАСТРОЙКА ==========
PHYSICS_PATH = r"C:\Users\Dim\Documents\vmms_texts\physics"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_physics_3d.json')
# ===============================

print("="*70)
print("🌀 3D-ФРАКТАЛЬНЫЙ ЗАГРУЗЧИК ФИЗИКИ")
print(" Вихри + моды одновременно")
print(" τ=5.2 — базовый слой")
print("="*70)

start_time = time.time()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

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

def extract_text_from_doc(filepath):
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
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(filepath, 'r', encoding='cp1251') as f:
                return f.read()
        except:
            return None

def compute_delta(text: str) -> float:
    text_lower = text.lower()
    special_terms = [
        "∇⁴ψ", "∇⁴", "бигармонический", "вихрь", "топологический",
        "квантовый", "фуркация", "спектральный", "резонанс",
        "фрактальный", "гомология", "эмерджентный", "квант"
    ]
    count = sum(1 for t in special_terms if t in text_lower)
    return min(1.0, count / 5)

def compute_theta(text: str) -> float:
    text_lower = text.lower()
    if any(w in text_lower for w in ["определение", "что такое", "суть", "смысл"]):
        return 0.0
    if any(w in text_lower for w in ["свойство", "характеристика", "особенность"]):
        return math.pi / 2
    if any(w in text_lower for w in ["применение", "использование", "технология"]):
        return math.pi
    if any(w in text_lower for w in ["история", "развитие", "открытие"]):
        return 3 * math.pi / 2
    return 0.0

# ========== ОСНОВНОЙ ЦИКЛ ==========

p = Personality(id="p016", name="VMMS Physics")
print(f"\n✨ Создано новое поле H (физика, τ=5.2)")

total_blocks = 0
total_files = 0

for filename in os.listdir(PHYSICS_PATH):
    filepath = os.path.join(PHYSICS_PATH, filename)
    ext = os.path.splitext(filename)[1].lower()
    
    print(f"\n📄 {filename}")
    
    if ext == '.pdf':
        content = extract_text_from_pdf(filepath)
    elif ext == '.doc':
        content = extract_text_from_doc(filepath)
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
    file_words = set()
    
    for i, block in enumerate(blocks):
        block = block.strip()
        if len(block) < 100:
            continue
        
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', block.lower())
        file_words.update(words)
        
        # Физика — фиксированная τ=5.2
        block_tau = 5.2
        block_delta = compute_delta(block)
        block_theta = compute_theta(block)
        
        # 1. СОЗДАЁМ/ОБНОВЛЯЕМ ВИХРИ
        for w in set(words):
            p.add_vortex(w, block_tau, block_delta, block_theta, amplitude=0.15)
        
        # 2. СОЗДАЁМ МОДУ С КОНТЕНТОМ
        mode = SpectralMode(
            tau=block_tau,
            delta=block_delta,
            theta=block_theta,
            amplitude=0.15,
            content=block[:1500],
            trace_type="physics",
            themes=["physics", "vmms"],
            trace_id=f"phys_{total_files}_{file_blocks}"
        )
        p.add_to_h_field(mode)
        
        file_blocks += 1
        total_blocks += 1
        
        if file_blocks % 10 == 0:
            print(f"   Обработано блоков: {file_blocks}")
    
    print(f"   → {file_blocks} блоков, {len(file_words)} уникальных слов")
    total_files += 1
    
    p.save(OUTPUT_PATH)
    print(f"   💾 Сохранено (вихрей: {len(p.vortices)}, мод: {len(p.h_field)})")
    
    elapsed = time.time() - start_time
    print(f"   ⏱️ Прошло: {elapsed/60:.1f} мин")

# ========== ФИНАЛ ==========

p.save(OUTPUT_PATH)
elapsed = time.time() - start_time

print("\n" + "="*70)
print("📊 ИТОГОВАЯ СТАТИСТИКА")
print("="*70)
print(f" Файлов обработано: {total_files}")
print(f" Блоков загружено: {total_blocks}")
print(f" Вихрей в поле H: {len(p.vortices)}")
print(f" Мод в поле H: {len(p.h_field)}")

print("\n🌊 ПРИМЕРЫ ВИХРЕЙ (первые 15):")
for i, (word, vortex) in enumerate(list(p.vortices.items())[:15]):
    print(f"   {word}: τ={vortex.tau:.2f}, δ={vortex.delta:.2f}, θ={vortex.theta:.2f}")

print("\n📦 ПРИМЕРЫ МОД (первые 5):")
for i, mode in enumerate(p.h_field[:5]):
    print(f"   {mode.trace_id}: τ={mode.tau:.2f}, δ={mode.delta:.2f}, θ={mode.theta:.2f}")
    print(f"      {mode.content[:100]}...")

print("\n" + "="*70)
print("✅ ФИЗИЧЕСКИЙ БАЗОВЫЙ СЛОЙ ЗАГРУЖЕН")
print(f"\n💾 Сохранено в: {OUTPUT_PATH}")