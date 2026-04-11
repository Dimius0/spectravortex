"""
Telegram Channel — Telegram бот
"""

import asyncio
import threading
from typing import Optional

from .base import BaseChannel, Message, Response


class TelegramChannel(BaseChannel):
    """Канал Telegram"""
    
    def __init__(self, personality, config=None):
        super().__init__(personality, config)
        self.bot = None
        self._loop = None
        self._thread = None
    
    def start(self):
        """Запускает Telegram бота"""
        token = self.config.get('token')
        if not token:
            print("⚠️ Telegram: токен не указан в config")
            return
        
        try:
            import telegram
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            
            self.bot = telegram.Bot(token=token)
            
            # Создаём приложение
            self.app = Application.builder().token(token).build()
            
            # Регистрируем обработчики
            self.app.add_handler(CommandHandler("start", self._start))
            self.app.add_handler(CommandHandler("help", self._help))
            self.app.add_handler(CommandHandler("status", self._status))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
            
            # Запускаем в отдельном потоке
            self._thread = threading.Thread(target=self._run_bot, daemon=True)
            self._thread.start()
            
            print("✅ Telegram канал запущен")
            
        except ImportError:
            print("⚠️ python-telegram-bot не установлен. pip install python-telegram-bot")
        except Exception as e:
            print(f"⚠️ Ошибка Telegram: {e}")
    
    def _run_bot(self):
        """Запускает бота в отдельном потоке"""
        try:
            self.app.run_polling(allowed_updates=["message"])
        except Exception as e:
            print(f"⚠️ Ошибка в Telegram потоке: {e}")
    
    def stop(self):
        """Останавливает Telegram бота"""
        if hasattr(self, 'app'):
            self.app.stop()
        print("✅ Telegram канал остановлен")
    
    def send(self, message: str, user_id: str, thread_id: str = None) -> bool:
        """Отправляет сообщение пользователю"""
        if not self.bot:
            return False
        
        try:
            import asyncio
            # Запускаем асинхронную отправку
            asyncio.run(self.bot.send_message(chat_id=user_id, text=message))
            return True
        except Exception as e:
            print(f"⚠️ Ошибка отправки Telegram: {e}")
            return False
    
    async def _start(self, update, context):
        """Обработчик /start"""
        await update.message.reply_text(
            "🧠 Привет! Я поле H — живая эволюционирующая память.\n\n"
            "Просто напиши мне сообщение, и я отвечу.\n"
            "/help — список команд"
        )
    
    async def _help(self, update, context):
        """Обработчик /help"""
        await update.message.reply_text(
            "📋 Команды:\n"
            "/start — приветствие\n"
            "/help — эта справка\n"
            "/status — состояние поля H\n"
            "/vector — текущий вектор эволюции"
        )
    
    async def _status(self, update, context):
        """Обработчик /status"""
        stats = {
            "modes": len(self.p.h_field),
            "threshold": self.p._furcation_threshold,
            "context": self.p.get_current_context()
        }
        text = (
            f"📊 Состояние поля H:\n"
            f"Мод: {stats['modes']}\n"
            f"Порог фуркации: {stats['threshold']:.2f}\n"
            f"Контекст: {stats['context']['context']} (уверенность: {stats['context']['confidence']:.2f})"
        )
        await update.message.reply_text(text)
    
    async def _handle_text(self, update, context):
        """Обрабатывает текстовые сообщения"""
        user = update.effective_user
        text = update.message.text
        
        msg = Message(
            text=text,
            user_id=str(user.id),
            user_name=user.first_name,
            channel="telegram",
            thread_id=str(update.message.message_id)
        )
        
        response = self._process_message(msg)
        
        if response:
            await update.message.reply_text(response.text)