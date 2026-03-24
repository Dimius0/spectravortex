"""
VectorAdapter — адаптация вектора эволюции из сенсорных данных
Поддержка текста и голоса (whisper)
"""

from .text_analyzer import TextAnalyzer


class VectorAdapter:
    def __init__(self, personality):
        self.p = personality
        self.text_analyzer = TextAnalyzer(personality)
        self._whisper_model = None
    
    def _get_whisper_model(self):
        """Ленивая загрузка модели whisper"""
        if self._whisper_model is None:
            try:
                import whisper
                print("   🎤 Загрузка модели whisper (base)...")
                self._whisper_model = whisper.load_model("base")
                print("   ✅ Модель загружена")
            except ImportError:
                print("   ⚠️ Whisper не установлен. pip install openai-whisper")
                return None
        return self._whisper_model
    
    def adapt_from_text(self, text: str, smooth_factor: float = 0.3) -> dict:
        """Адаптирует вектор эволюции из текста"""
        # 1. Извлекаем τ (взвешенное среднее)
        text_tau = self.text_analyzer.extract_tau(text)
        
        # 2. Извлекаем темы
        text_themes = self.text_analyzer.extract_themes(text)
        
        # 3. Плавное обновление вектора
        if self.p.evolution_vector["target_tau"] is None:
            self.p.evolution_vector["target_tau"] = text_tau
        else:
            self.p.evolution_vector["target_tau"] = (
                self.p.evolution_vector["target_tau"] * (1 - smooth_factor) + 
                text_tau * smooth_factor
            )
        
        if text_themes:
            current_themes = set(self.p.evolution_vector["target_themes"])
            current_themes.update(text_themes)
            self.p.evolution_vector["target_themes"] = list(current_themes)[:6]
        
        print(f"\n🎯 АДАПТАЦИЯ ИЗ ТЕКСТА:")
        print(f"   Извлечённая τ: {text_tau:.2f}")
        print(f"   Извлечённые темы: {text_themes}")
        print(f"   → Новый вектор: τ={self.p.evolution_vector['target_tau']:.2f}, "
              f"темы={self.p.evolution_vector['target_themes']}")
        
        return self.p.evolution_vector
    
    def adapt_from_audio(self, audio_path: str, smooth_factor: float = 0.3) -> dict:
        """Адаптирует вектор из аудио (голосовой ввод)"""
        model = self._get_whisper_model()
        if model is None:
            return None
        
        try:
            print(f"\n🎤 Распознаю речь из {audio_path}...")
            result = model.transcribe(audio_path, language="ru")
            text = result["text"].strip()
            
            if not text:
                print("   ⚠️ Речь не распознана")
                return None
            
            print(f"   📝 Распознано: {text[:80]}...")
            return self.adapt_from_text(text, smooth_factor)
            
        except Exception as e:
            print(f"   ⚠️ Ошибка распознавания: {e}")
            return None
    
    def adapt_from_microphone(self, duration: float = 5.0, smooth_factor: float = 0.3) -> dict:
        """Адаптирует вектор из микрофона (запись и распознавание)"""
        try:
            import pyaudio
            import wave
            import tempfile
            import numpy as np
            
            print(f"\n🎤 Запись {duration} сек из микрофона...")
            
            # Параметры записи
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 16000
            
            p = pyaudio.PyAudio()
            stream = p.open(format=format, channels=channels, rate=rate,
                          input=True, frames_per_buffer=chunk)
            
            frames = []
            for _ in range(0, int(rate / chunk * duration)):
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
                wf.setframerate(rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                tmp_path = tmp.name
            
            # Распознаём
            result = self.adapt_from_audio(tmp_path, smooth_factor)
            
            # Удаляем временный файл
            import os
            os.unlink(tmp_path)
            
            return result
            
        except ImportError:
            print("   ⚠️ pyaudio не установлен. pip install pyaudio")
            return None
        except Exception as e:
            print(f"   ⚠️ Ошибка записи: {e}")
            return None