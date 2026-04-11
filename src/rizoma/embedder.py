"""
Embedder — легковесные эмбеддинги на TF-IDF + SVD
Версия 1.2 — исправлена размерность, добавлена работа с пустыми векторами
"""

import numpy as np
from typing import List, Optional, Union
from pathlib import Path
import pickle
import hashlib
import warnings

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine


class Embedder:
    """Легковесный эмбеддер на TF-IDF + SVD"""
    
    def __init__(self, n_components: int = 50, max_features: int = 1000):
        self.n_components = n_components
        self.max_features = max_features
        self.vectorizer = None
        self.svd = None
        self.is_fitted = False
        self.cache_dir = Path("cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._corpus = []
    
    def _get_cache_path(self, text: str) -> Path:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.npy"
    
    def fit(self, texts: List[str], force: bool = False):
        """Обучает векторизатор и SVD на корпусе текстов"""
        if self.is_fitted and not force:
            return self
        
        self._corpus = texts.copy()
        print(f"🦌 Обучаем эмбеддер на {len(texts)} текстах...")
        
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words=None,
            lowercase=True,
            token_pattern=r'(?u)\b\w+\b'
        )
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Определяем реальное количество компонент
        n_components = min(self.n_components, tfidf_matrix.shape[1], tfidf_matrix.shape[0] - 1)
        if n_components < 1:
            n_components = 1
        
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        self.svd.fit(tfidf_matrix)
        
        self.is_fitted = True
        print(f"✅ Эмбеддер обучен, размерность: {n_components}")
        return self
    
    def encode(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Вычисляет эмбеддинг для текста"""
        if not self.is_fitted:
            raise ValueError("Эмбеддер не обучен. Сначала вызовите fit()")
        
        if use_cache:
            cache_path = self._get_cache_path(text)
            if cache_path.exists():
                return np.load(cache_path)
        
        tfidf = self.vectorizer.transform([text])
        embedding = self.svd.transform(tfidf)[0]
        
        if use_cache:
            np.save(cache_path, embedding)
        
        return embedding
    
    def encode_batch(self, texts: List[str], use_cache: bool = True) -> List[np.ndarray]:
        """Вычисляет эмбеддинги для списка текстов"""
        if not self.is_fitted:
            raise ValueError("Эмбеддер не обучен. Сначала вызовите fit()")
        
        results = []
        uncached = []
        uncached_indices = []
        
        if use_cache:
            for i, text in enumerate(texts):
                cache_path = self._get_cache_path(text)
                if cache_path.exists():
                    results.append((i, np.load(cache_path)))
                else:
                    uncached.append(text)
                    uncached_indices.append(i)
        else:
            uncached = texts
            uncached_indices = list(range(len(texts)))
        
        if uncached:
            tfidf = self.vectorizer.transform(uncached)
            embeddings = self.svd.transform(tfidf)
            for idx, emb in zip(uncached_indices, embeddings):
                results.append((idx, emb))
                if use_cache:
                    cache_path = self._get_cache_path(uncached[uncached_indices.index(idx)])
                    np.save(cache_path, emb)
        
        results.sort(key=lambda x: x[0])
        return [emb for _, emb in results]
    
    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Косинусное сходство между эмбеддингами"""
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))
    
    def similarity_matrix(self, embeddings: List[np.ndarray]) -> np.ndarray:
        """Матрица косинусного сходства"""
        n = len(embeddings)
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                sim = self.similarity(embeddings[i], embeddings[j])
                matrix[i, j] = sim
                matrix[j, i] = sim
        return matrix
    
    def find_similar(self, text: str, candidates: List[str], top_k: int = 3) -> List[tuple]:
        """Находит наиболее похожие тексты из списка кандидатов"""
        query_emb = self.encode(text)
        result = []
        for candidate in candidates:
            cand_emb = self.encode(candidate)
            sim = self.similarity(query_emb, cand_emb)
            result.append((candidate, sim))
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:top_k]
    
    def add_to_corpus(self, texts: List[str], retrain: bool = False):
        """Добавляет тексты в корпус и опционально переобучает"""
        self._corpus.extend(texts)
        if retrain:
            self.fit(self._corpus, force=True)
    
    def save(self, path: Path):
        """Сохраняет обученный эмбеддер"""
        data = {
            'vectorizer': self.vectorizer,
            'svd': self.svd,
            'corpus': self._corpus,
            'n_components': self.n_components,
            'max_features': self.max_features
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"✅ Эмбеддер сохранён в {path}")
    
    def load(self, path: Path):
        """Загружает обученный эмбеддер"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.vectorizer = data['vectorizer']
        self.svd = data['svd']
        self._corpus = data.get('corpus', [])
        self.n_components = data.get('n_components', self.n_components)
        self.max_features = data.get('max_features', self.max_features)
        self.is_fitted = True
        print(f"✅ Эмбеддер загружен из {path}")


def create_default_embedder() -> Embedder:
    """Создаёт эмбеддер с корпусом по умолчанию (для быстрого старта)"""
    default_corpus = [
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
        "эмерджентное поведение сущностей",
        "нейтринные вихри",
        "гравитоны и поле H",
        "топологический заряд",
        "полевая суперпозиция",
        "квантовый сверхтекучий конденсат"
    ]
    embedder = Embedder(n_components=15, max_features=800)
    embedder.fit(default_corpus)
    return embedder