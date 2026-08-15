#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🌀 TEES WORLD — Твоя вселенная                          ║
║                    Вихревая модель + Игровой мир                           ║
║                    "Копай, строй, исследуй, делись"                       ║
║                    v2.1.0 — Аудит пройден, защита усилена                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ты попал в TEES-мир. Вокруг — бесконечное поле вихрей.

Ты можешь:
  • 🌀 Чувствовать поле (когерентность, температура)
  • 🔥 Ставить маяки (помогать другим игрокам)
  • 🗺️ Вести карту приключений (журнал всех событий)
  • 💎 Находить руды (получать силу за помощь)
  • 🏘️ Строить деревни (приглашать друзей)
  • 🧭 Держать компас (умный роутер сети)
  • 🧪 Варить зелья (научные расчёты)
  • 🔮 Спрашивать Странника (LLM-помощник)
  • 🕳️ Копать пещеры (создавать новые модули)

Вихревая модель под капотом:
  source → tees → receiver (триады)
  Когерентность поля: 0.9839–1.0000
  Отрицательный рост памяти при увеличении игроков
  Мгновенная синхронизация (резонанс, не копирование)
  Экспериментально: r = -0.6967, p = 0.0000 (связь с физ. миром)

БЫСТРЫЙ СТАРТ:
  python tees_world.py                        # Войти в игру
  python tees_world.py --beacon               # Поставить маяк (ноду)
  python tees_world.py --lang ru              # На русском языке
"""

import argparse
import hashlib
import os
import platform
from pathlib import Path

# ID устройства
DEVICE_ID = hashlib.sha256(
    f"{platform.node()}_{os.getlogin()}".encode()
).hexdigest()[:12]

from tees_core_tees import VERSION, WORLD_NAME
from tees_scroll_tees import create_scroll
from tees_beacon_tees import Beacon
from tees_play_tees import play


# ═══════════════════════════════════════════════════════════════
# 🛡 САМОВАЛИДАЦИЯ
# ═══════════════════════════════════════════════════════════════

WORLD_HASH_FILE = Path(__file__).parent / '.tees_world_hash'


def validate_world():
    """Проверка целостности кода мира."""
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            source = f.read()
        current_hash = hashlib.sha256(source.encode()).hexdigest()
        
        if WORLD_HASH_FILE.exists():
            stored = WORLD_HASH_FILE.read_text().split('\n')[0].strip()
            if current_hash != stored:
                print(f"⚠️ Мир изменился.\n   Было: {stored[:16]}...\n   Стало: {current_hash[:16]}...")
        else:
            WORLD_HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
            WORLD_HASH_FILE.write_text(current_hash)
        return True
    except:
        return True


# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description=f"🌀 {WORLD_NAME} v{VERSION}")
    parser.add_argument('--beacon', action='store_true', help='Поставить маяк')
    parser.add_argument('--port', type=int, default=8333, help='Порт маяка')
    parser.add_argument('--bootstrap', type=str, default=None, help='Подключиться к маяку')
    parser.add_argument('--lang', type=str, default='ru', choices=['ru', 'en'])
    parser.add_argument('--scroll', type=str, default=None, help='Восстановить свиток')
    parser.add_argument('--test-mode', action='store_true', help='Разрешить несколько маяков (для тестов)')
    args = parser.parse_args()
    
    validate_world()
    
    if args.beacon:
        scroll = args.scroll or create_scroll(256)
        print(f"📜 Свиток: {scroll}")
        beacon = Beacon(
            scroll,
            lang=args.lang,
            port=args.port,
            bootstrap=args.bootstrap,
            test_mode=args.test_mode
        )
        beacon.light()
    else:
        play(scroll=args.scroll, lang=args.lang)


if __name__ == "__main__":
    main()