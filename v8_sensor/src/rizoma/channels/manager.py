"""
Channel Manager — управление всеми каналами
"""

from typing import Dict, List, Optional
from .base import BaseChannel
from .cli import CLIChannel
from .telegram import TelegramChannel


class ChannelManager:
    """Менеджер каналов связи"""
    
    def __init__(self, personality):
        self.p = personality
        self.channels: Dict[str, BaseChannel] = {}
    
    def add_channel(self, name: str, channel: BaseChannel):
        """Добавляет канал"""
        self.channels[name] = channel
        print(f"📡 Канал {name} добавлен")
    
    def add_cli(self):
        """Добавляет CLI канал"""
        self.add_channel("cli", CLIChannel(self.p))
    
    def add_telegram(self, token: str):
        """Добавляет Telegram канал"""
        self.add_channel("telegram", TelegramChannel(self.p, {"token": token}))
    
    def start_all(self):
        """Запускает все каналы"""
        for name, channel in self.channels.items():
            try:
                channel.start()
            except Exception as e:
                print(f"⚠️ Ошибка запуска канала {name}: {e}")
    
    def stop_all(self):
        """Останавливает все каналы"""
        for name, channel in self.channels.items():
            try:
                channel.stop()
            except Exception as e:
                print(f"⚠️ Ошибка остановки канала {name}: {e}")
    
    def send_to_user(self, channel: str, user_id: str, message: str) -> bool:
        """Отправляет сообщение пользователю через указанный канал"""
        if channel in self.channels:
            return self.channels[channel].send(message, user_id)
        return False