"""
Тест легковесного эмбеддера (без кэша)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from rizoma.embedder import Embedder

print("🦌 Тестируем легковесный эмбеддер...")

corpus = [
    "Hello, world!",
    "Привет, мир!",
    "What is the meaning of life?",
    "В чём смысл жизни?",
    "∇⁴ψ = 0 — the biharmonic equation",
    "почини кран",
    "ремонт сантехники",
    "свобода воли и детерминизм",
    "температурная зависимость распада",
    "состояние Хойла 7.65 МэВ",
    "вихревая электроотрицательность",
    "фрактальный уровень k",
    "окна возможностей",
    "материальная память",
    "алхимия как предтеча ВММП",
    "интерметаллиды как новые сущности",
    "спектры как отпечаток структуры",
    "сверхпроводники при комнатной температуре",
    "борьба с переобучением",
    "эмерджентное поведение сущностей"
]

embedder = Embedder(n_components=10, max_features=500)
embedder.fit(corpus, force=True)  # force=True — переобучить

print(f"\n📝 Кодируем тексты (без кэша)...")
embeddings = []
for text in corpus:
    emb = embedder.encode(text, use_cache=False)
    embeddings.append(emb)
print(f"✅ Получено {len(embeddings)} эмбеддингов, размер: {embeddings[0].shape}")

print("\n🔍 Сходство текстов:")
for i in range(len(corpus)):
    for j in range(i+1, len(corpus)):
        sim = embedder.similarity(embeddings[i], embeddings[j])
        if sim > 0.2:
            print(f"   '{corpus[i][:25]}' vs '{corpus[j][:25]}': {sim:.3f}")

print("\n🦌 Тест завершён!")