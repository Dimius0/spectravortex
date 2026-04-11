"""
Прямой тест sentence-transformers (минуя наш embedder)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("0. Импортируем sentence-transformers напрямую")
from sentence_transformers import SentenceTransformer

print("1. Загружаем модель...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("2. Модель загружена")

print("3. Кодируем текст...")
text = "Hello, world!"
embedding = model.encode(text)
print(f"4. Размер эмбеддинга: {embedding.shape}")
print(f"5. Первые 5 значений: {embedding[:5]}")
print(f"6. Последние 5 значений: {embedding[-5:]}")

print("\n🦌 Тест завершён!")