#!/usr/bin/env python3
"""
Multichannel Demo — демонстрация работы с несколькими каналами
Версия с спектральным словарём
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.personality import Personality, SpectralMode
from rizoma.channels.manager import ChannelManager


def main():
    print("="*60)
    print("🌀 МУЛЬТИКАНАЛЬНАЯ ДЕМО")
    print("   CLI + Telegram | Поле H + спектральный словарь")
    print("="*60)
    
    # 1. Создаём личность
    print("\n📌 1. Создаём личность...")
    p = Personality(id="multichannel", name="MultiChannel")
    
    # Добавляем базовые моды
    modes = [
        SpectralMode(5.20, 0.6, 
            "Matter = Space. Particles are vortices in condensate. Physics is the study of matter and energy.",
            "vmms_monism", ["physics", "vmms", "matter", "space"]),
        SpectralMode(6.60, 0.6,
            "Sulfur — energy, Mercury — flow, Salt — form. Alchemy is transformation of substances.",
            "alchemy_manifesto", ["alchemy", "transformation", "sulfur", "mercury", "salt"]),
        SpectralMode(8.21, 0.6,
            "Grandson asks, grandfather answers. Questions create answers, answers create questions.",
            "grandson_01", ["dialogue", "learning", "wisdom", "grandson", "grandfather"])
    ]
    
    for mode in modes:
        p.add_to_h_field(mode)
        # Словарь обновляется автоматически в add_to_h_field
    
    print(f"   ✅ Поле H: {len(p.h_field)} мод")
    print(f"   📖 Словарь: {len(p.word_tau)} слов")
    
    # 2. Создаём менеджер каналов
    print("\n📌 2. Создаём менеджер каналов...")
    manager = ChannelManager(p)
    
    # 3. Добавляем CLI
    print("\n📌 3. Добавляем CLI канал...")
    manager.add_cli()
    
    # 4. Добавляем Telegram (если есть токен)
    print("\n📌 4. Добавляем Telegram канал...")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        manager.add_telegram(token)
        print("   ✅ Telegram канал добавлен")
    else:
        print("   ⚠️ TELEGRAM_BOT_TOKEN не задан. Telegram канал не будет запущен")
    
    # 5. Запускаем каналы
    print("\n📌 5. Запускаем каналы...")
    manager.start_all()
    
    print("\n" + "="*60)
    print("✅ ДЕМО ЗАПУЩЕНА")
    print("   CLI: введите сообщение в этой консоли")
    if token:
        print("   Telegram: найдите бота и напишите ему")
    print("   Нажмите Ctrl+C для остановки")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка...")
        manager.stop_all()
        print("✅ Демо завершена")


if __name__ == "__main__":
    main()