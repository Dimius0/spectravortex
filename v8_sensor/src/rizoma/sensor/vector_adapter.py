"""
VectorAdapter — адаптация вектора эволюции из текста и голоса
"""

from .text_analyzer import TextAnalyzer
from .audio_input import AudioInput


class VectorAdapter:
    def __init__(self, personality, whisper_model: str = None):
        self.p = personality
        self.text_analyzer = TextAnalyzer(personality)
        self.audio_input = AudioInput(whisper_model) if whisper_model else None
    
    def adapt_from_text(self, text: str, smooth_factor: float = 0.3) -> dict:
        """Адаптирует вектор эволюции из текста"""
        text_tau = self.text_analyzer.extract_tau(text)
        text_themes = self.text_analyzer.extract_themes(text)
        
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
        print(f"   τ: {self.p.evolution_vector['target_tau']:.2f}")
        print(f"   темы: {self.p.evolution_vector['target_themes']}")
        
        return self.p.evolution_vector
    
    def adapt_from_audio(self, audio_path: str, smooth_factor: float = 0.3, 
                         language: str = None) -> dict:
        """Адаптирует вектор из аудиофайла"""
        if not self.audio_input:
            print("   ⚠️ Whisper не инициализирован")
            return None
        
        text = self.audio_input.transcribe_file(audio_path, language)
        if text:
            return self.adapt_from_text(text, smooth_factor)
        return None
    
    def adapt_from_microphone(self, duration: float = 5.0, 
                              smooth_factor: float = 0.3,
                              language: str = None) -> dict:
        """Запись с микрофона и адаптация"""
        if not self.audio_input:
            print("   ⚠️ Whisper не инициализирован")
            return None
        
        text = self.audio_input.record_and_transcribe(duration, language=language)
        if text:
            return self.adapt_from_text(text, smooth_factor)
        return None
    
    def continuous_listen(self, wake_word: str = None, duration: float = 5.0):
        """
        Непрерывное прослушивание с пробуждением по ключевому слову
        wake_word: слово для активации (например, "поле", "эй поле")
        """
        if not self.audio_input:
            print("   ⚠️ Whisper не инициализирован")
            return
        
        print(f"\n🎤 Непрерывное прослушивание запущено")
        if wake_word:
            print(f"   Скажите '{wake_word}' для активации")
        else:
            print(f"   Скажите что-нибудь...")
        print("   Нажмите Ctrl+C для остановки")
        
        try:
            import pyaudio
            import wave
            
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            sample_rate = 16000
            
            p = pyaudio.PyAudio()
            stream = p.open(format=format,
                          channels=channels,
                          rate=sample_rate,
                          input=True,
                          frames_per_buffer=chunk)
            
            print("🎧 Слушаю...")
            
            while True:
                frames = []
                for _ in range(0, int(sample_rate / chunk * duration)):
                    data = stream.read(chunk)
                    frames.append(data)
                
                # Сохраняем во временный файл
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    wf = wave.open(tmp.name, 'wb')
                    wf.setnchannels(channels)
                    wf.setsampwidth(p.get_sample_size(format))
                    wf.setframerate(sample_rate)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    tmp_path = tmp.name
                
                text = self.audio_input.transcribe_file(tmp_path)
                os.unlink(tmp_path)
                
                if text:
                    if wake_word and wake_word.lower() in text.lower():
                        print(f"\n🔊 Активация! Распознано: {text}")
                        # Убираем слово активации из текста
                        clean_text = text.lower().replace(wake_word.lower(), "").strip()
                        if clean_text:
                            self.adapt_from_text(clean_text)
                        else:
                            # Если только слово активации — ждём следующую фразу
                            print("   Скажите команду...")
                    elif not wake_word:
                        self.adapt_from_text(text)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n🛑 Прослушивание остановлено")
        except Exception as e:
            print(f"   ⚠️ Ошибка: {e}")
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            if 'p' in locals():
                p.terminate()