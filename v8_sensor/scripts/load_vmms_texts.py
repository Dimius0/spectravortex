#!/usr/bin/env python3
"""
Загрузка всех текстов ВММП из внешней папки
Поддержка: .txt, .md, .pdf, .html, .htm, .wav, .mp3, .m4a, .ogg, .flac
С поддержкой OCR для масштабированных PDF
"""

import sys
import os
import re
import hashlib
import tempfile
import subprocess

# Добавляем путь к src (поднимаемся на два уровня вверх от scripts)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rizoma.personality import Personality, SpectralMode

# Импортируем OCR для PDF
try:
    from rizoma.sensor.pdf_ocr import extract_text_from_pdf as ocr_extract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# ========== НАСТРОЙКА ==========
# Укажи путь к папке с текстами
TEXTS_ROOT = r"C:\Users\Dim\Documents\vmms_texts"
# Модель Whisper: 'tiny', 'base', 'small', 'medium', 'large'
WHISPER_MODEL = 'base'
# ===============================

# Глобальная переменная для модели Whisper (ленивая загрузка)
_whisper_model = None


def _get_whisper_model():
    """Ленивая загрузка модели Whisper"""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            print(f"   🎤 Загрузка модели Whisper ({WHISPER_MODEL})...")
            _whisper_model = whisper.load_model(WHISPER_MODEL)
            print(f"   ✅ Модель загружена")
        except ImportError:
            print("   ⚠️ Whisper не установлен. Установите: pip install openai-whisper")
            return None
    return _whisper_model


def extract_text_from_pdf(filepath):
    """Извлекает текст из PDF с поддержкой OCR"""
    # Сначала пробуем стандартное извлечение через pdfplumber
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
    
    # Если не получилось или текст пустой — пробуем OCR
    if HAS_OCR:
        print(f"      🔍 Стандартное извлечение не дало текста, пробуем OCR...")
        return ocr_extract(filepath)
    
    return None


def extract_text_from_html(filepath):
    """Извлекает текст из HTML, убирая теги"""
    try:
        from bs4 import BeautifulSoup
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Убираем script и style
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator='\n')
        # Очищаем от лишних пустых строк
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    except ImportError:
        print("   ⚠️ BeautifulSoup не установлен. Установите: pip install beautifulsoup4")
        return None
    except Exception as e:
        print(f"   ⚠️ Ошибка чтения HTML: {e}")
        return None


def extract_text_from_audio(filepath):
    """Распознаёт речь из аудиофайла через Whisper"""
    model = _get_whisper_model()
    if model is None:
        return None
    
    try:
        ext = os.path.splitext(filepath)[1].lower()
        audio_path = filepath
        
        # Конвертируем в WAV если нужно
        if ext != '.wav':
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            
            cmd = ['ffmpeg', '-i', filepath, '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', tmp_path, '-y']
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                print(f"   ⚠️ Ошибка конвертации аудио: {result.stderr.decode()[:200]}")
                return None
            audio_path = tmp_path
        
        # Распознаём
        result = model.transcribe(audio_path)
        text = result["text"].strip()
        
        # Удаляем временный файл
        if ext != '.wav' and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        return text if text else None
        
    except Exception as e:
        print(f"   ⚠️ Ошибка распознавания аудио: {e}")
        return None


def extract_text_from_doc(filepath):
    """Извлекает текст из .doc (упрощённо)"""
    try:
        import olefile
        if not olefile.isOleFile(filepath):
            return None
        
        ole = olefile.OleFileIO(filepath)
        # Пытаемся прочитать поток WordDocument
        if ole.exists('WordDocument'):
            data = ole.openstream('WordDocument').read()
            # Упрощённое извлечение текста (не идеально, но работает)
            text = data.decode('utf-16-le', errors='ignore')
            # Убираем бинарный мусор
            text = re.sub(r'[^\w\s\.,!?;:\(\)\[\]\-\—\«\»\№\n]', '', text)
            return text
        return None
    except ImportError:
        print("   ⚠️ olefile не установлен. Установите: pip install olefile")
        return None
    except Exception as e:
        print(f"   ⚠️ Ошибка чтения DOC: {e}")
        return None


def load_text_file(p, filepath, tau=None, theme=None):
    """Загружает текстовый файл, разбивая на смысловые блоки"""
    ext = os.path.splitext(filepath)[1].lower()
    content = None
    
    # Текстовые форматы
    if ext in ['.txt', '.md', '.py', '.json', '.csv', '.rst']:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='cp1251') as f:
                    content = f.read()
            except:
                print(f"   ⚠️ Не удалось прочитать {filepath}")
                return 0
        if ext == '.md':
            print(f"      MD файл: {len(content)} символов")
    
    # PDF
    elif ext == '.pdf':
        content = extract_text_from_pdf(filepath)
    
    # HTML
    elif ext in ['.html', '.htm']:
        content = extract_text_from_html(filepath)
    
    # Аудио
    elif ext in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.opus', '.aac']:
        content = extract_text_from_audio(filepath)
        if content:
            print(f"      🎤 Распознано: {len(content)} символов")
    
    # DOC
    elif ext == '.doc':
        content = extract_text_from_doc(filepath)
    
    # DOCX (можно добавить позже через python-docx)
    elif ext == '.docx':
        print(f"   ⚠️ DOCX пока не поддерживается, сконвертируйте в PDF или TXT")
        return 0
    
    else:
        # Пропускаем неподдерживаемые форматы
        return 0
    
    if content is None or len(content) < 30:
        return 0
    
    # Разбиваем на блоки (по абзацам)
    blocks = re.split(r'\n\s*\n', content)
    
    if ext == '.md':
        print(f"      Блоков после разбиения: {len(blocks)}")
        for i, block in enumerate(blocks[:3]):
            print(f"         Блок {i}: {len(block)} символов")
    
    count = 0
    for block in blocks:
        block = block.strip()
        if len(block) < 30 or len(block) > 2500:
            continue
        
        # Очищаем от служебных символов
        block = re.sub(r'[^\w\s\.,!?;:\(\)\[\]\-\—\«\»\№\n]', '', block)
        if not block:
            continue
        
        # Создаём моду
        mode = SpectralMode(
            tau=tau or 5.0,
            amplitude=0.3,
            content=block[:1500],
            trace_id=f"text_{hashlib.md5(block.encode()).hexdigest()[:8]}",
            themes=[theme] if theme else ["vmms", "theory"],
            trace_type="text"
        )
        p.add_to_h_field(mode)
        count += 1
    
    return count


def scan_and_load(p, root_dir):
    """Рекурсивно сканирует папку и загружает все тексты"""
    total_files = 0
    total_blocks = 0
    skipped_extensions = set()
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Определяем τ по имени папки
        tau = 5.2
        theme = "vmms"
        
        dir_lower = dirpath.lower()
        if "discover" in dir_lower:
            tau = 5.2
            theme = "discovery"
        elif "alchemy" in dir_lower:
            tau = 6.6
            theme = "alchemy"
        elif "dial" in dir_lower or "dialog" in dir_lower:
            tau = 8.2
            theme = "dialogue"
        elif "brain" in dir_lower:
            tau = 5.2
            theme = "brainstorm"
        elif "physics" in dir_lower or "физик" in dir_lower:
            tau = 5.2
            theme = "physics"
        elif "cosm" in dir_lower or "косм" in dir_lower:
            tau = 7.5
            theme = "cosmology"
        elif "poetry" in dir_lower or "стих" in dir_lower:
            tau = 8.0
            theme = "poetry"
        elif "audio" in dir_lower or "voice" in dir_lower:
            tau = 8.2
            theme = "audio"
        
        for filename in filenames:
            # Пропускаем системные файлы
            if filename.startswith('.'):
                continue
            
            ext = os.path.splitext(filename)[1].lower()
            supported = ['.txt', '.md', '.pdf', '.html', '.htm', '.doc', 
                        '.py', '.json', '.csv', '.rst',
                        '.wav', '.mp3', '.m4a', '.ogg', '.flac', '.opus', '.aac']
            
            if ext in supported:
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, root_dir)
                print(f"   📄 {rel_path}")
                
                count = load_text_file(p, filepath, tau, theme)
                if count > 0:
                    total_blocks += count
                    total_files += 1
                    print(f"      → {count} блоков")
            else:
                skipped_extensions.add(ext)
    
    if skipped_extensions:
        print(f"\n   ⚠️ Пропущены расширения: {sorted(skipped_extensions)}")
    
    return total_files, total_blocks


def main():
    print("="*70)
    print("📚 ЗАГРУЗКА ТЕКСТОВ ВММП В ПОЛЕ H")
    print(f"   Источник: {TEXTS_ROOT}")
    print(f"   OCR: {'доступен' if HAS_OCR else 'не установлен'}")
    print("="*70)
    
    if not os.path.exists(TEXTS_ROOT):
        print(f"\n❌ Папка {TEXTS_ROOT} не найдена!")
        print("   Создайте её и положите туда тексты.")
        return
    
    # Создаём папку для сохранения
    save_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, 'p016_vmms_full.json')
    
    # Загружаем существующее поле H или создаём новое
    try:
        p = Personality.load(save_path)
        print(f"\n📂 Загружено поле H: {len(p.h_field)} мод, {len(p.word_tau)} слов")
    except:
        p = Personality(id="p016", name="VMMS Theory")
        print(f"\n✨ Создано новое поле H")
    
    # Сканируем и загружаем
    print("\n📄 Сканирование и загрузка...")
    print("-"*50)
    
    total_files, total_blocks = scan_and_load(p, TEXTS_ROOT)
    
    # Итог
    print("\n" + "="*70)
    print("📊 ИТОГ ЗАГРУЗКИ")
    print("="*70)
    print(f" Файлов обработано: {total_files}")
    print(f" Блоков загружено: {total_blocks}")
    print(f" Мод в поле H: {len(p.h_field)}")
    print(f" Слов в словаре: {len(p.word_tau)}")
    
    # Сохраняем
    p.save(save_path)
    print(f"\n💾 Поле H сохранено в {save_path}")
    
    print("\n✅ ЗАГРУЗКА ЗАВЕРШЕНА")
    print("\n🦌 Теперь поле H знает ВММП.")


if __name__ == "__main__":
    main()