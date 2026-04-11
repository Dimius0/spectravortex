"""
CLI Channel — командная строка
"""

import sys
import threading
from typing import Optional

from .base import BaseChannel, Message, Response


class CLIChannel(BaseChannel):
    """Канал командной строки"""
    
    def __init__(self, personality, config=None):
        super().__init__(personality, config)
        self._input_thread = None
        self._running = False
        self._debug = config.get('debug', True) if config else True
    
    def start(self):
        """Запускает CLI интерфейс"""
        self._running = True
        self._input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self._input_thread.start()
        print("\n💬 CLI канал запущен. Введите сообщение (exit для выхода):")
        if self._debug:
            print("   (режим отладки: будет показана выбранная мода и τ)")
    
    def stop(self):
        """Останавливает CLI"""
        self._running = False
        print("\n💬 CLI канал остановлен")
    
    def send(self, message: str, user_id: str = "cli", thread_id: str = None) -> bool:
        """Отправляет сообщение в консоль"""
        print(f"\n🤖 {message}")
        return True
    
    def _input_loop(self):
        """Цикл чтения ввода"""
        while self._running:
            try:
                user_input = input("\n👤 > ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("До свидания!")
                    self.stop()
                    break
                
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                    continue
                
                # Создаём сообщение
                msg = Message(
                    text=user_input,
                    user_id="cli_user",
                    user_name="CLI User",
                    channel="cli"
                )
                
                # Обрабатываем
                response = self._process_message(msg)
                if response:
                    self.send(response.text)
                    if self._debug and hasattr(response, 'context'):
                        ctx = response.context
                        print(f"   [debug: мода={ctx.get('mode_used')}, τ={ctx.get('tau'):.2f}, "
                              f"вопрос_τ={ctx.get('question_tau'):.2f}, "
                              f"резонанс={ctx.get('resonance'):.2f}]")
                
            except KeyboardInterrupt:
                print("\n")
                self.stop()
                break
            except Exception as e:
                print(f"⚠️ Ошибка: {e}")
    
    def _handle_command(self, cmd: str):
        """Обрабатывает команды"""
        cmd = cmd[1:].lower()
        
        if cmd == "help":
            print("\n📋 Команды:")
            print("   /help     - показать это сообщение")
            print("   /status   - состояние поля H")
            print("   /vector   - текущий вектор эволюции")
            print("   /debug    - переключить режим отладки")
            print("   /clear    - очистить экран")
            print("   /exit     - выйти")
        
        elif cmd == "status":
            stats = {
                "modes": len(self.p.h_field),
                "threshold": self.p._furcation_threshold,
                "context": self.p.get_current_context()
            }
            print(f"\n📊 Состояние:")
            print(f"   Мод: {stats['modes']}")
            print(f"   Порог фуркации: {stats['threshold']:.2f}")
            print(f"   Контекст: {stats['context']}")
        
        elif cmd == "vector":
            vec = self.p.evolution_vector
            print(f"\n🧭 Вектор эволюции:")
            print(f"   Целевая τ: {vec['target_tau']}")
            print(f"   Целевые темы: {vec['target_themes']}")
            print(f"   Интенсивность: {vec['intensity']}")
        
        elif cmd == "debug":
            self._debug = not self._debug
            print(f"   🐞 Режим отладки: {'включен' if self._debug else 'выключен'}")
        
        elif cmd == "clear":
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
        
        elif cmd == "exit":
            self.stop()
        
        else:
            print(f"⚠️ Неизвестная команда: /{cmd}")