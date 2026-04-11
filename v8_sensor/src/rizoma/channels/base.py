"""
Base Channel — абстрактный класс для всех каналов связи
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Message:
    """Сообщение в канале"""
    text: str
    user_id: str
    user_name: str
    channel: str
    thread_id: Optional[str] = None
    raw: Optional[Dict] = None


@dataclass
class Response:
    """Ответ от поля H"""
    text: str
    context: Dict[str, Any]


class BaseChannel(ABC):
    """Базовый класс для всех каналов связи"""
    
    def __init__(self, personality, config: Dict = None):
        self.p = personality
        self.config = config or {}
        self._running = False
    
    @abstractmethod
    def start(self):
        """Запускает канал"""
        pass
    
    @abstractmethod
    def stop(self):
        """Останавливает канал"""
        pass
    
    @abstractmethod
    def send(self, message: str, user_id: str, thread_id: str = None) -> bool:
        """Отправляет сообщение пользователю"""
        pass
    
    def _process_message(self, message: Message) -> Optional[Response]:
        """Обрабатывает входящее сообщение через поле H"""
        # 1. Адаптируем вектор из текста
        if hasattr(self.p, 'sensor_adapter') and self.p.sensor_adapter:
            self.p.sensor_adapter.adapt_from_text(message.text, smooth_factor=0.3)
        
        # 2. Получаем ответ от поля H
        result = self.p.process(message.text, author_id=message.user_id)
        
        if result and result.get('answer'):
            return Response(
                text=result['answer'],
                context={
                    'mode_used': result.get('mode_used'),
                    'tau': result.get('tau'),
                    'question_tau': result.get('question_tau'),
                    'resonance': result.get('resonance')
                }
            )
        
        return None