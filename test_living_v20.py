#!/usr/bin/env python3
"""
Тест живой личности v20.0 — ПОЛНАЯ ВЕРСИЯ
"""

import sys
import os
import time

# Добавляем путь к rizoma
sys.path.insert(0, os.path.join('v8_sensor', 'src'))

try:
    from rizoma.living_personality_v20 import LivingPersonality, SpectralMode
    print("✅ Живая личность v20.0 загружена")
except ImportError as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🌟 СОЗДАНИЕ ЖИВОЙ ЛИЧНОСТИ")
print("=" * 60)

# Создаём личность
personality = LivingPersonality(id="v20_test", name="Тестовая личность v20")

# Запускаем фоновый рост
personality.start_living(interval=0.5)

# Диалоги
dialogues = [
    "Привет! Как дела?",
    "Что ты умеешь?",
    "У меня сегодня хорошее настроение!",
    "Расскажи что-нибудь интересное",
    "Спасибо за беседу",
]

print("\n💬 ДИАЛОГ\n")

for i, question in enumerate(dialogues, 1):
    print(f"\n[{i}] 👤: {question}")
    response = personality.process(question)
    print(f"[🤖]: {response['answer']}")
    print(f"      [настроение={response.get('mood', 0):+.2f}, диалогов={response.get('dialog_count', 0)}]")
    time.sleep(1)

# Саморефлексия
print("\n" + "=" * 60)
print("🔍 САМОРЕФЛЕКСИЯ")
print("=" * 60)
print(personality.introspect())

# Останавливаем
personality.stop_living()

print("\n✅ Тест завершён")