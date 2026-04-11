"""
PDF OCR — извлечение текста из масштабированных и сканированных PDF
"""

import os
import tempfile
from typing import Optional

# Попытка импорта с обработкой ошибок
try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


def extract_text_from_scanned_pdf(filepath: str, dpi: int = 300, lang: str = 'rus+eng') -> Optional[str]:
    """
    Извлекает текст из масштабированного/сканированного PDF через OCR
    
    Args:
        filepath: путь к PDF
        dpi: разрешение для конвертации (по умолч. 300)
        lang: языки для OCR ('rus+eng', 'rus', 'eng')
    
    Returns:
        извлечённый текст или None при ошибке
    """
    if not HAS_OCR:
        print("   ⚠️ OCR не доступен. Установите: pip install pytesseract pdf2image")
        return None
    
    try:
        # Конвертируем PDF в изображения
        print(f"      🖼️ Конвертация PDF в изображения (dpi={dpi})...")
        images = convert_from_path(filepath, dpi=dpi)
        
        text_parts = []
        for i, img in enumerate(images):
            print(f"      📄 Страница {i+1}/{len(images)}...")
            # OCR распознавание
            page_text = pytesseract.image_to_string(img, lang=lang)
            if page_text.strip():
                text_parts.append(page_text)
        
        if not text_parts:
            print("      ⚠️ Текст не распознан")
            return None
        
        return "\n\n".join(text_parts)
        
    except Exception as e:
        print(f"      ⚠️ Ошибка OCR: {e}")
        return None


def extract_text_from_pdf(filepath: str, use_ocr: bool = True) -> Optional[str]:
    """
    Универсальное извлечение текста из PDF
    
    Сначала пробует стандартное извлечение (pdfplumber),
    если не получается или текст пустой — использует OCR
    """
    # Сначала пробуем стандартное извлечение
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"      ⚠️ Ошибка стандартного извлечения: {e}")
    
    # Если текст не извлёкся или пустой — пробуем OCR
    if use_ocr:
        print(f"      🔍 Стандартное извлечение не дало текста, пробуем OCR...")
        return extract_text_from_scanned_pdf(filepath)
    
    return None