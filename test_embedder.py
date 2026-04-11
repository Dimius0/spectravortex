"""
Тест эмбеддингов
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rizoma.embedder import Embedder

def test_embedder():
    print("🦌 Тестируем эмбеддер...")
    
    embedder = Embedder()
    
    texts = [
        "Hello, world!",
        "Привет, мир!",
        "What is the meaning of life?",
        "В чём смысл жизни?",
        "∇⁴ψ = 0 — the biharmonic equation"
    ]
    
    print(f"\n📝 Тестируем {len(texts)} текстов...")
    
    # Одиночное кодирование
    emb1 = embedder.encode(texts[0])
    print(f"✅ Эмбеддинг '{texts[0][:20]}...' размер: {emb1.shape}")
    
    # Пакетное кодирование
    embeddings = embedder.encode_batch(texts)
    print(f"✅ Пакетное кодирование: {len(embeddings)} эмбеддингов")
    
    # Проверка сходства
    print("\n🔍 Сходство текстов:")
    for i in range(min(3, len(texts))):
        for j in range(i+1, min(3, len(texts))):
            sim = embedder.similarity(embeddings[i], embeddings[j])
            print(f"   '{texts[i][:30]}...' vs '{texts[j][:30]}...': {sim:.3f}")
    
    # Проверка кэша
    emb1_cached = embedder.encode(texts[0])
    if np.array_equal(emb1, emb1_cached):
        print("✅ Кэш работает")
    else:
        print("❌ Кэш не работает")
    
    print("\n🦌 Тест эмбеддинга завершён!")

if __name__ == "__main__":
    test_embedder()