"""
Отладочный тест эмбеддингов
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("0. Импорт прошёл")

from rizoma.embedder import Embedder

print("1. Создаём эмбеддер...")
embedder = Embedder()
print("2. Эмбеддер создан")

print("3. Пробуем кодировать текст...")
text = "Hello, world!"
print(f"   Текст: {text}")

emb = embedder.encode(text)
print(f"4. Кодирование завершено")
print(f"5. Размер эмбеддинга: {emb.shape}")
print(f"6. Первые 5 значений: {emb[:5]}")
print(f"7. Последние 5 значений: {emb[-5:]}")

print("\n🦌 Тест завершён!")