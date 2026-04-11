"""
Тест с маленькой моделью
"""

from sentence_transformers import SentenceTransformer
import time

print("1. Загружаем маленькую модель...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("2. Модель загружена")

print("3. Кодируем текст...")
start = time.time()
text = "Hello, world!"
embedding = model.encode(text)
print(f"4. Готово за {time.time()-start:.2f} сек")
print(f"5. Размер эмбеддинга: {embedding.shape}")
print(f"6. Первые 5 значений: {embedding[:5]}")

print("\n🦌 Тест завершён!")