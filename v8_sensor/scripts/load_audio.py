# scripts/load_audio.py
"""
Загрузка аудиофайлов с распознаванием речи через Whisper
"""
import sys
import os
import re
import tempfile
import subprocess
import whisper

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality, SpectralMode

AUDIO_PATH = r"C:\Users\Dim\Documents\vmms_texts\audio"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')

print("="*60)
print("🎤 ЗАГРУЗКА АУДИОФАЙЛОВ")
print(" Распознавание речи через Whisper")
print("="*60)

# Загружаем существующее поле H
p = Personality.load(OUTPUT_PATH)
print(f"\n📂 Загружено поле H: {len(p.h_field)} мод, {len(p.word_tau)} слов")

# Загружаем модель Whisper
print("\n🎤 Загрузка модели Whisper...")
model = whisper.load_model("base")
print("   Модель загружена")

def transcribe_audio(filepath):
    """Распознаёт речь из аудиофайла"""
    try:
        ext = os.path.splitext(filepath)[1].lower()
        
        # Конвертируем в WAV если нужно
        if ext != '.wav':
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            cmd = ['ffmpeg', '-i', filepath, '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', tmp_path, '-y']
            subprocess.run(cmd, capture_output=True)
            audio_path = tmp_path
        else:
            audio_path = filepath
        
        # Распознаём
        result = model.transcribe(audio_path)
        text = result["text"].strip()
        
        # Удаляем временный файл
        if ext != '.wav' and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        return text
    except Exception as e:
        print(f"   ⚠️ Ошибка: {e}")
        return None

def fallback_tau(block: str) -> float:
    length_factor = min(1.0, len(block) / 200)
    words = set(block.split())
    complexity = len(words) / max(10, len(block.split()))
    return 5.0 + length_factor * 2 + complexity * 1.5

total_blocks = 0
total_files = 0

for filename in os.listdir(AUDIO_PATH):
    filepath = os.path.join(AUDIO_PATH, filename)
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.opus']:
        continue
    
    print(f"\n🎵 {filename}")
    
    # Распознаём речь
    text = transcribe_audio(filepath)
    if not text or len(text) < 50:
        print(f"   ⚠️ Не удалось распознать речь")
        continue
    
    print(f"   Распознано: {len(text)} символов")
    print(f"   Первые 100 символов: {text[:100]}...")
    
    # Разбиваем на блоки
    blocks = re.split(r'\n\s*\n', text)
    print(f"   Блоков: {len(blocks)}")
    
    file_blocks = 0
    for i, block in enumerate(blocks):
        block = block.strip()
        if len(block) < 80:
            continue
        
        # Автоопределение τ через словарь
        tau = p.phrase_tau(block)
        if abs(tau - 5.0) < 0.1:
            tau = fallback_tau(block)
            tau = max(3.0, min(9.0, tau))
        
        mode = SpectralMode(
            tau=tau,
            amplitude=0.15,
            content=block[:1500],
            trace_type="audio",
            themes=["audio", "speech"],
            trace_id=f"audio_{total_files}_{i}"
        )
        p.add_to_h_field(mode)
        file_blocks += 1
        total_blocks += 1
    
    print(f"   → {file_blocks} блоков загружено")
    total_files += 1
    
    # Сохраняем после каждого файла
    p.save(OUTPUT_PATH)
    print(f"   💾 Сохранено")

print("\n" + "="*60)
print("📊 ИТОГ")
print("="*60)
print(f" Файлов обработано: {total_files}")
print(f" Блоков загружено: {total_blocks}")
print(f" Мод в поле H: {len(p.h_field)}")
print(f" Слов в словаре: {len(p.word_tau)}")
print("\n🦌 Аудио загружено!")