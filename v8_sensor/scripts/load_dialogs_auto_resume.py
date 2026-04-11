#!/usr/bin/env python3
"""
Загрузка PDF-диалога в поле H через OCR
АВТООПРЕДЕЛЕНИЕ τ через словарь
С АВТОСОХРАНЕНИЕМ и ВОЗМОЖНОСТЬЮ ПРОДОЛЖЕНИЯ
"""
import sys
import os
import re
import json
from pdf2image import convert_from_path, pdfinfo_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rizoma.personality import Personality, SpectralMode

# ========== НАСТРОЙКА ==========
PDF_PATH = r"C:\Users\Dim\Documents\vmms_texts\base_dialogs\current_dialogue.pdf"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
PHYSICS_SAVE_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_physics_v8.json')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_progress.json')

SAVE_INTERVAL = 10  # сохранять каждые 10 страниц
# ===============================

def load_progress():
    """Загружает сохранённый прогресс"""
    if os.path.exists(PROGRESS_PATH):
        try:
            with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"last_page": 0, "total_blocks": 0}

def save_progress(last_page, total_blocks):
    """Сохраняет прогресс"""
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump({"last_page": last_page, "total_blocks": total_blocks}, f, ensure_ascii=False, indent=2)

def load_field_h():
    """Загружает поле H — либо продолжает, либо начинает с физики"""
    if os.path.exists(OUTPUT_PATH):
        print(f"\n📂 Найден сохранённый прогресс! Загружаем поле H...")
        p = Personality.load(OUTPUT_PATH)
        progress = load_progress()
        print(f"   Последняя обработанная страница: {progress['last_page']}")
        print(f"   Уже загружено блоков: {progress['total_blocks']}")
        print(f"   Мод в поле H: {len(p.h_field)}")
        print(f"   Слов в словаре: {len(p.word_tau)}")
        return p, progress
    else:
        print(f"\n📂 Начинаем с физического фундамента...")
        if not os.path.exists(PHYSICS_SAVE_PATH):
            print(f"\n❌ Файл с физикой не найден: {PHYSICS_SAVE_PATH}")
            print(" Сначала запусти load_physics_v8.py")
            sys.exit(1)
        p = Personality.load(PHYSICS_SAVE_PATH)
        print(f"   Мод: {len(p.h_field)}")
        print(f"   Слов в словаре: {len(p.word_tau)}")
        return p, {"last_page": 0, "total_blocks": 0}

def fallback_tau(block: str) -> float:
    """Эвристика для fallback"""
    length_factor = min(1.0, len(block) / 200)
    words = set(block.split())
    complexity = len(words) / max(10, len(block.split()))
    return 5.0 + length_factor * 2 + complexity * 1.5

print("="*60)
print("📚 ЗАГРУЗКА PDF-ДИАЛОГА (АВТОСОХРАНЕНИЕ)")
print(" Сохранение каждые 10 страниц. Можно прервать и продолжить.")
print("="*60)

# Загружаем поле H и прогресс
p, progress = load_field_h()
last_page = progress["last_page"]
total_blocks = progress["total_blocks"]

# Проверяем PDF
if not os.path.exists(PDF_PATH):
    print(f"\n❌ PDF не найден: {PDF_PATH}")
    sys.exit(1)

if not os.path.exists(POPPLER_PATH):
    print(f"\n⚠️ Poppler не найден: {POPPLER_PATH}")
    sys.exit(1)

# Получаем количество страниц
print(f"\n📄 Получение информации о PDF...")
try:
    info = pdfinfo_from_path(PDF_PATH, poppler_path=POPPLER_PATH)
    total_pages = info.get('Pages', info.get('pages', 0))
    print(f"   Страниц: {total_pages}")
    print(f"   Начинаем со страницы: {last_page + 1}")
except Exception as e:
    print(f"   ⚠️ Не удалось получить количество страниц: {e}")
    total_pages = None

# Начинаем с последней сохранённой страницы
page_num = last_page + 1
pages_processed_since_save = 0

while True:
    print(f"\n🖼️ Страница {page_num} / {total_pages if total_pages else '?'}...")
    
    try:
        images = convert_from_path(
            PDF_PATH,
            dpi=150,
            first_page=page_num,
            last_page=page_num,
            poppler_path=POPPLER_PATH
        )
    except Exception as e:
        print(f"   ⚠️ Ошибка конвертации страницы {page_num}: {e}")
        break
    
    if not images:
        break
    
    img = images[0]
    
    print(f"   OCR...")
    try:
        page_text = pytesseract.image_to_string(img, lang='rus+eng')
    except Exception as e:
        print(f"   ⚠️ Ошибка OCR: {e}")
        page_text = ""
    
    if page_text.strip():
        blocks = re.split(r'\n\s*\n', page_text)
        page_blocks = 0
        
        for block in blocks:
            block = block.strip()
            if len(block) < 100:
                continue
            
            # Автоопределение τ через словарь
            tau = p.phrase_tau(block)
            
            if abs(tau - 5.0) < 0.1:
                tau = fallback_tau(block)
                tau = max(3.0, min(9.0, tau))
            
            mode = SpectralMode(
                tau=tau,
                amplitude=0.1,
                content=block[:1500],
                trace_type="dialogue",
                themes=["dialogue", "vmms"],
                trace_id=f"dialogue_{page_num}_{page_blocks}"
            )
            p.add_to_h_field(mode)
            page_blocks += 1
            total_blocks += 1
        
        print(f"   Блоков: {page_blocks} (всего: {total_blocks})")
    else:
        print(f"   ⚠️ Текст не распознан")
    
    del images
    del img
    
    pages_processed_since_save += 1
    page_num += 1
    
    # АВТОСОХРАНЕНИЕ
    if pages_processed_since_save >= SAVE_INTERVAL:
        print(f"\n💾 АВТОСОХРАНЕНИЕ (страница {page_num - 1})...")
        p.save(OUTPUT_PATH)
        save_progress(page_num - 1, total_blocks)
        pages_processed_since_save = 0
        print(f"   Сохранено. Всего мод: {len(p.h_field)}, слов: {len(p.word_tau)}")
    
    if total_pages and page_num > total_pages:
        break

# Финальное сохранение
print(f"\n💾 ФИНАЛЬНОЕ СОХРАНЕНИЕ...")
p.save(OUTPUT_PATH)
save_progress(page_num - 1, total_blocks)

print(f"\n✅ Загружено {total_blocks} блоков")
print(f"\n📊 ИТОГ")
print("="*60)
print(f" Мод в поле H: {len(p.h_field)}")
print(f" Слов в словаре: {len(p.word_tau)}")

# Показываем распределение τ
taus = {}
for word, tau in p.word_tau.items():
    taus[tau] = taus.get(tau, 0) + 1

print(f"\n Распределение τ в словаре:")
for tau, cnt in sorted(taus.items()):
    print(f"   τ={tau:.2f}: {cnt} слов")

print("\n🦌 Поле H сохранено. Можно продолжить позже с той же страницы.")