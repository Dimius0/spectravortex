"""
Минимальный тест эмбеддингов
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rizoma.embedder import Embedder

print("1. Создаём эмбеддер...")
embedder = Embedder()

print("2. Кодируем один текст...")
text = "Hello, world!"
emb = embedder.encode(text)

print(f"3. Размер эмбеддинга: {emb.shape}")
print(f"4. Первые 5 значений: {emb[:5]}")

print("\n🦌 Тест завершён!")