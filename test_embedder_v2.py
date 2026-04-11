"""
Тест легковесного эмбеддера
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rizoma.embedder import Embedder

print("🦌 Тестируем легковесный эмбеддер...")

# Обучаем на корпусе
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
embedder.fit(corpus)

print(f"\n📝 Кодируем тексты...")
embeddings = embedder.encode_batch(corpus)
print(f"✅ Получено {len(embeddings)} эмбеддингов, размер: {embeddings[0].shape}")

print("\n🔍 Сходство текстов:")
for i in range(len(corpus)):
    for j in range(i+1, len(corpus)):
        sim = embedder.similarity(embeddings[i], embeddings[j])
        if sim > 0.2:
            print(f"   '{corpus[i][:25]}' vs '{corpus[j][:25]}': {sim:.3f}")

# Тест нового текста
print("\n🆕 Тест нового текста:")
new_text = "сантехник чинит трубу"
emb = embedder.encode(new_text)
print(f"   '{new_text}' → эмбеддинг размером {emb.shape}")

# Поиск похожего
best_sim = 0
best_idx = 0
for i, emb_i in enumerate(embeddings):
    sim = embedder.similarity(emb, emb_i)
    if sim > best_sim:
        best_sim = sim
        best_idx = i
print(f"   Наиболее похож на: '{corpus[best_idx]}' (сходство: {best_sim:.3f})")

print("\n🦌 Тест завершён!")