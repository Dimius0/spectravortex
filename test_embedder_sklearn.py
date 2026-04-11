"""
Тест с TF-IDF + SVD (легковесная альтернатива эмбеддингам)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

print("1. Создаём TF-IDF векторизатор...")
vectorizer = TfidfVectorizer(max_features=500, stop_words=None)

texts = [
    "Hello, world!",
    "Привет, мир!",
    "What is the meaning of life?",
    "В чём смысл жизни?",
    "∇⁴ψ = 0 — the biharmonic equation",
    "почини кран",
    "ремонт сантехники"
]

print(f"2. Обучаем на {len(texts)} текстах...")
tfidf_matrix = vectorizer.fit_transform(texts)
print(f"   Размер матрицы: {tfidf_matrix.shape}")

print("3. Уменьшаем размерность до 50...")
svd = TruncatedSVD(n_components=min(50, len(texts)), random_state=42)
embeddings = svd.fit_transform(tfidf_matrix)
print(f"   Размер эмбеддингов: {embeddings.shape}")

print("\n4. Косинусное сходство:")
for i in range(len(texts)):
    for j in range(i+1, len(texts)):
        sim = cosine_similarity(embeddings[i].reshape(1, -1), embeddings[j].reshape(1, -1))[0][0]
        if sim > 0.3:
            print(f"   '{texts[i][:25]}' vs '{texts[j][:25]}': {sim:.3f}")

print("\n🦌 Тест завершён! Легковесная альтернатива работает.")