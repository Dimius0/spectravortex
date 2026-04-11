"""
Простой тест эмбеддингов
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from rizoma.embedder import Embedder

print("🦌 Запускаем эмбеддер...")
embedder = Embedder()

texts = [
    "Hello, world!",
    "Привет, мир!",
    "What is the meaning of life?",
    "∇⁴ψ = 0 — the biharmonic equation"
]

print(f"\n📝 Кодируем {len(texts)} текстов...")
embeddings = embedder.encode_batch(texts)
print(f"✅ Получено {len(embeddings)} эмбеддингов, размер: {embeddings[0].shape}")

print("\n🔍 Сходство текстов:")
for i in range(len(texts)):
    for j in range(i+1, len(texts)):
        sim = embedder.similarity(embeddings[i], embeddings[j])
        print(f"   '{texts[i][:25]}' vs '{texts[j][:25]}': {sim:.3f}")

print("\n🦌 Тест завершён!")