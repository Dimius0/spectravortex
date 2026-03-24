"""
Audio Input — распознавание речи через Whisper
"""

import tempfile
import os
import wave
import time
from typing import Optional

import numpy as np


class AudioInput:
    """Распознавание речи из аудиофайлов и микрофона"""
    
    def __init__(self, model_size: str = "base"):
        """
        model_size: 'tiny' (39 MB), 'base' (74 MB), 'small' (244 MB)
        """
        self.model_size = model_size
        self._model = None
        self._sample_rate = 16000
    
    def _load_model(self):
        """Ленивая загрузка модели Whisper"""
        if self._model is None:
            try:
                import whisper
                print(f"   🎤 Загрузка модели Whisper ({self.model_size})...")
                self._model = whisper.load_model(self.model_size)
                print(f"   ✅ Модель загружена")
            except ImportError:
                raise ImportError("Установите openai-whisper: pip install openai-whisper")
        return self._model
    
    def transcribe_file(self, audio_path: str, language: str = None) -> Optional[str]:
        """
        Распознаёт речь из аудиофайла
        language: 'ru', 'en' или None (автоопределение)
        """
        try:
            model = self._load_model()
            result = model.transcribe(audio_path, language=language)
            text = result["text"].strip()
            if text:
                return text
            return None
        except Exception as e:
            print(f"   ⚠️ Ошибка распознавания: {e}")
            return None
    
    def record_and_transcribe(self, duration: float = 5.0, 
                               sample_rate: int = 16000,
                               language: str = None) -> Optional[str]:
        """
        Записывает с микрофона и распознаёт
        duration: длительность записи в секундах
        """
        try:
            import pyaudio
            
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            
            p = pyaudio.PyAudio()
            stream = p.open(format=format,
                          channels=channels,
                          rate=sample_rate,
                          input=True,
                          frames_per_buffer=chunk)
            
            print(f"   🎙️ Запись {duration} сек...")
            frames = []
            for _ in range(0, int(sample_rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wf = wave.open(tmp.name, 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(format))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                tmp_path = tmp.name
            
            # Распознаём
            text = self.transcribe_file(tmp_path, language)
            
            # Удаляем временный файл
            os.unlink(tmp_path)
            
            if text:
                print(f"   📝 Распознано: {text[:80]}...")
            else:
                print(f"   ⚠️ Речь не распознана")
            
            return text
            
        except ImportError:
            print("   ⚠️ pyaudio не установлен. pip install pyaudio")
            return None
        except Exception as e:
            print(f"   ⚠️ Ошибка записи: {e}")
            return None
    
    def transcribe_from_bytes(self, audio_bytes: bytes, sample_rate: int = 16000) -> Optional[str]:
        """Распознаёт речь из аудиобайтов (WAV)"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wf = wave.open(tmp.name, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_bytes)
            wf.close()
            tmp_path = tmp.name
        
        text = self.transcribe_file(tmp_path)
        os.unlink(tmp_path)
        return text