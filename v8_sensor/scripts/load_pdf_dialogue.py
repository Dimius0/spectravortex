#!/usr/bin/env python3
"""
Загрузка PDF-диалога в поле H через OCR
АВТООПРЕДЕЛЕНИЕ τ через словарь (после загрузки физики)
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
PDF_PATH = r"C:\Users\Dim\Documents\vmms_texts\base_dialogs\current_dialogue.pdf"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
PHYSICS_SAVE_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_physics_v8.json')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')
# ===============================

print("="*60)
print("📚 ЗАГРУЗКА PDF-ДИАЛОГА (АВТООПРЕДЕЛЕНИЕ τ)")
print(" Загружаем поле H с физикой, затем добавляем диалоги")
print("="*60)

# 1. Загружаем поле H с физикой
if not os.path.exists(PHYSICS_SAVE_PATH):
    print(f"\n❌ Файл с физикой не найден: {PHYSICS_SAVE_PATH}")
    print(" Сначала запусти load_physics_v8.py")
    sys.exit(1)

p = Personality.load(PHYSICS_SAVE_PATH)
print(f"\n📂 Загружено поле H с физикой:")
print(f"   Мод: {len(p.h_field)}")
print(f"   Слов в словаре: {len(p.word_tau)}")

# 2. Проверяем PDF
if not os.path.exists(PDF_PATH):
    print(f"\n❌ PDF не найден: {PDF_PATH}")
    sys.exit(1)

if not os.path.exists(POPPLER_PATH):
    print(f"\n⚠️ Poppler не найден: {POPPLER_PATH}")
    sys.exit(1)

# 3. Получаем количество страниц
print(f"\n📄 Получение информации о PDF...")
try:
    info = pdfinfo_from_path(PDF_PATH, poppler_path=POPPLER_PATH)
    total_pages = info.get('Pages', info.get('pages', 0))
    print(f"   Страниц: {total_pages}")
except Exception as e:
    print(f"   ⚠️ Не удалось получить количество страниц: {e}")
    total_pages = None

# 4. Эвристика для fallback
def fallback_tau(block: str) -> float:
    length_factor = min(1.0, len(block) / 200)
    words = set(block.split())
    complexity = len(words) / max(10, len(block.split()))
    return 5.0 + length_factor * 2 + complexity * 1.5

count_blocks = 0
page_num = 1

while True:
    print(f"\n🖼️ Страница {page_num}...")
    
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
            
            # ========== ГЛАВНОЕ: АВТООПРЕДЕЛЕНИЕ τ ЧЕРЕЗ СЛОВАРЬ ==========
            tau = p.phrase_tau(block)
            
            # Если словарь не дал точного τ (вернул 5.0) — используем эвристику
            if abs(tau - 5.0) < 0.1:
                tau = fallback_tau(block)
                tau = max(3.0, min(9.0, tau))
            
            # Амплитуда 0.1 — чтобы не доминировали
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
            count_blocks += 1
        
        print(f"   Блоков: {page_blocks} (всего: {count_blocks})")
    else:
        print(f"   ⚠️ Текст не распознан")
    
    del images
    del img
    
    page_num += 1
    
    if total_pages and page_num > total_pages:
        break
    
    if page_num > 50:
        print("\n⚠️ Остановлено после 50 страниц для теста")
        break

print(f"\n✅ Загружено {count_blocks} блоков")

# 5. Сохраняем
p.save(OUTPUT_PATH)

print(f"\n📊 ИТОГ")
print("="*60)
print(f" Мод в поле H: {len(p.h_field)}")
print(f" Слов в словаре: {len(p.word_tau)}")

# Показываем распределение τ в словаре
taus = {}
for word, tau in p.word_tau.items():
    taus[tau] = taus.get(tau, 0) + 1

print(f"\n Распределение τ в словаре:")
for tau, cnt in sorted(taus.items()):
    print(f"   τ={tau:.2f}: {cnt} слов")

if p.word_tau:
    print(f"\n Первые 30 новых слов (из диалогов):")
    # Показываем слова, которых не было в физике
    physics_words = set()
    for word, tau in p.word_tau.items():
        if tau == 5.2:
            physics_words.add(word)
    
    new_words = [(w, t) for w, t in p.word_tau.items() if w not in physics_words][:30]
    for word, tau in new_words:
        print(f"   {word}: {tau:.2f}")

print("\n🦌 PDF-диалог загружен. Поле H готово к работе!")