#!/usr/bin/env python3
"""
Тест живого поля v19.0
"""

import sys
import time
sys.path.insert(0, 'src')

try:
    from rizoma.personality_v19_living import LivingField
    print("✅ LivingField загружен")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# Создаём живое поле
print("\n" + "=" * 60)
print("🌟 СОЗДАНИЕ ЖИВОГО ПОЛЯ v19.0")
print("=" * 60)

field = LivingField(id="test_001", name="Эхо v19.0")

# Запускаем эндогенный цикл (фон)
field.start_living(interval=0.1)

# Несколько тестовых диалогов
test_dialogues = [
    "Привет! Как дела?",
    "Что ты умеешь?",
    "Расскажи что-нибудь интересное",
    "У меня сегодня плохое настроение...",
    "А ты можешь пошутить?",
    "Что ты думаешь о будущем?",
    "Спасибо за разговор!",
]

print("\n💬 НАЧИНАЮ ДИАЛОГ\n")

for i, question in enumerate(test_dialogues, 1):
    print(f"\n[{i}] Пользователь: {question}")
    response = field.process(question)
    print(f"Поле: {response['answer']}")
    print(f"    [резонанс={response.get('resonance', 0):.2f}, тип={response.get('mode_type', '?')}]")
    time.sleep(1)  # Пауза, чтобы поле "подумало"

# Саморефлексия
print("\n" + "=" * 60)
print("🔍 САМОРЕФЛЕКСИЯ ПОЛЯ")
print("=" * 60)
print(field.introspect())

# Состояние
print("\n📊 ИТОГОВОЕ СОСТОЯНИЕ")
state = field.get_state()
for k, v in state.items():
    print(f"   {k}: {v}")

# Останавливаем фоновый цикл
field.stop_living()

print("\n✅ Тест завершён")