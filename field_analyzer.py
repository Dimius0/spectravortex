#!/usr/bin/env python3
"""
field_analyzer.py — Универсальный анализатор данных для SpectraVortex v3.1
Расширенная потоковая обработка, возобновляемая загрузка, 
многопоточность и прямая интеграция с clean_field.py.
"""

import numpy as np
import hashlib
import json
import os
import mmap
import pickle
import time
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple, Iterator, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# БАЗОВЫЕ СУЩНОСТИ
# ============================================================================

class DataNature(Enum):
    TEXT = "text"
    BINARY = "binary"
    ENCRYPTED = "encrypted"
    COMPRESSED = "compressed"
    HASH = "hash"
    PROTOCOL = "protocol"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class ProcessingState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class ChunkProgress:
    """Прогресс обработки чанка."""
    chunk_id: int
    bytes_processed: int
    total_bytes: int
    percentage: float
    new_grams: int
    new_transitions: int
    timestamp: float = field(default_factory=time.time)

@dataclass
class FieldReport:
    """Полный отчёт об анализе поля."""
    data_nature: DataNature
    entropy: float
    structure_index: float
    complexity_score: float
    n_gram_size: int
    total_lemmas: int = 0
    total_exchanges: int = 0
    unique_grams: int = 0
    transition_density: float = 0.0
    total_rules: int = 0
    total_patterns: int = 0
    grammar_confidence: float = 0.0
    dominant_eigenvalue: float = 0.0
    spectral_gap: float = 0.0
    mixing_time: float = 0.0
    nodes: List[Dict] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)
    grammar: Dict = field(default_factory=dict)
    anomalies: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['data_nature'] = self.data_nature.value
        return result
    
    def summary(self) -> str:
        return f"""
╔══════════════════════════════════════════════╗
║         FIELD ANALYSIS REPORT               ║
╠══════════════════════════════════════════════╣
║ Nature: {self.data_nature.value:<35} ║
║ Entropy: {self.entropy:.2f} bits/byte{' '*25} ║
║ Structure: {self.structure_index:.3f}{' '*30} ║
║ Complexity: {self.complexity_score:.3f}{' '*29} ║
╠══════════════════════════════════════════════╣
║ n-gram: {self.n_gram_size:<34} ║
║ Unique grams: {self.unique_grams:<29} ║
║ Trans density: {self.transition_density:.4f}{' '*25} ║
║ Grammar conf: {self.grammar_confidence:.3f}{' '*26} ║
║ Processing: {self.processing_time:.1f}s{' '*28} ║
╚══════════════════════════════════════════════╝"""

# ============================================================================
# РАСШИРЕННЫЙ ПОТОКОВЫЙ ЗАГРУЗЧИК
# ============================================================================

class ChunkedFieldLoader:
    """
    Потоковый загрузчик с поддержкой:
    - Многопоточной обработки чанков
    - Сохранения/восстановления состояния
    - Адаптивного размера чанка
    - Оценки оставшегося времени
    """
    
    def __init__(self, n: int = 8, chunk_size: int = 1024 * 1024, 
                 overlap: int = 128, num_workers: int = None,
                 checkpoint_file: str = None):
        """
        Args:
            n: Размер n-граммы
            chunk_size: Размер чанка в байтах
            overlap: Перекрытие между чанками
            num_workers: Количество потоков (None = auto)
            checkpoint_file: Файл для сохранения прогресса
        """
        self.n = n
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.num_workers = num_workers or max(1, mp.cpu_count() - 1)
        self.checkpoint_file = checkpoint_file
        
        # Состояние обработки
        self.state = ProcessingState.IDLE
        self.progress_history: List[ChunkProgress] = []
        
        # Накопленные статистики
        self.gram_counter = Counter()
        self.transition_counter = Counter()
        self.total_chunks = 0
        self.total_bytes = 0
        self.entropy_samples = []
        self._last_bytes = b''
        
        # Тайминг
        self.start_time = None
        self.bytes_processed = 0
        
        # Попытка восстановления
        if checkpoint_file and os.path.exists(checkpoint_file):
            self._load_checkpoint()
    
    def process_chunk(self, chunk: bytes) -> ChunkProgress:
        """Обрабатывает один чанк данных."""
        if not chunk:
            return None
        
        # Объединяем с остатком
        if self._last_bytes:
            chunk = self._last_bytes + chunk
            self._last_bytes = b''
        
        # Извлекаем n-граммы
        grams = self._extract_ngrams(chunk)
        if len(grams) < 2:
            self._last_bytes = chunk[-self.n+1:] if len(chunk) > self.n else chunk
            return None
        
        # Обновляем частоты
        self.gram_counter.update(grams)
        
        # Обновляем переходы
        new_transitions = 0
        for i in range(len(grams) - 1):
            pair = (grams[i], grams[i+1])
            self.transition_counter[pair] += 1
            new_transitions += 1
        
        # Обновляем метрики
        entropy = self._calculate_chunk_entropy(chunk)
        self.entropy_samples.append(entropy)
        self.total_chunks += 1
        self.total_bytes += len(chunk)
        self.bytes_processed += len(chunk)
        
        # Сохраняем остаток
        if len(chunk) > self.n:
            self._last_bytes = chunk[-self.n+1:]
        
        return ChunkProgress(
            chunk_id=self.total_chunks,
            bytes_processed=self.bytes_processed,
            total_bytes=0,  # Будет обновлено в process_file
            percentage=0,
            new_grams=len(grams),
            new_transitions=new_transitions,
        )
    
    def process_file(self, filepath: str, 
                    progress_callback: Callable = None,
                    save_checkpoints: bool = True) -> Dict:
        """
        Потоковая обработка файла с многопоточностью.
        
        Args:
            filepath: Путь к файлу
            progress_callback: Функция(chunk_progress) для обновления прогресса
            save_checkpoints: Сохранять ли промежуточные состояния
        """
        self.state = ProcessingState.PROCESSING
        self.start_time = time.time()
        
        file_size = os.path.getsize(filepath)
        
        print(f"📂 Потоковая загрузка: {filepath}")
        print(f"   Размер: {file_size / 1024 / 1024:.1f} МБ")
        print(f"   n-грамма: {self.n}")
        print(f"   Чанк: {self.chunk_size / 1024:.0f} КБ")
        print(f"   Потоков: {self.num_workers}")
        
        try:
            with open(filepath, 'rb') as f:
                # Используем mmap для эффективного доступа
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    
                    # Если один поток — последовательная обработка
                    if self.num_workers == 1:
                        self._process_sequential(mm, file_size, progress_callback)
                    else:
                        self._process_parallel(mm, file_size, progress_callback)
            
            self.state = ProcessingState.COMPLETED
            
        except Exception as e:
            self.state = ProcessingState.ERROR
            print(f"❌ Ошибка обработки: {e}")
            raise
        
        finally:
            # Сохраняем финальный чекпоинт
            if save_checkpoints and self.checkpoint_file:
                self._save_checkpoint()
        
        processing_time = time.time() - self.start_time
        speed = self.total_bytes / processing_time / 1024 / 1024
        
        print(f"\n✅ Загрузка завершена за {processing_time:.1f}с")
        print(f"   Скорость: {speed:.1f} МБ/с")
        
        return self.finalize()
    
    def _process_sequential(self, mm, file_size: int, callback):
        """Последовательная обработка с чанками."""
        offset = 0
        while offset < file_size:
            chunk = mm[offset:offset + self.chunk_size]
            progress = self.process_chunk(bytes(chunk))
            
            if progress:
                progress.total_bytes = file_size
                progress.percentage = (self.bytes_processed / file_size) * 100
                self.progress_history.append(progress)
                
                if callback:
                    callback(progress)
                
                # Оценка времени
                elapsed = time.time() - self.start_time
                if self.bytes_processed > 0:
                    eta = (elapsed / self.bytes_processed) * (file_size - self.bytes_processed)
                    print(f"\r⏳ {progress.percentage:.1f}% | "
                          f"Чанк #{progress.chunk_id} | "
                          f"ETA: {eta:.0f}с", end='', flush=True)
            
            offset += self.chunk_size
            
            # Сохраняем чекпоинт каждые 10 чанков
            if self.checkpoint_file and self.total_chunks % 10 == 0:
                self._save_checkpoint()
    
    def _process_parallel(self, mm, file_size: int, callback):
        """Параллельная обработка чанков."""
        
        def chunk_generator():
            """Генератор чанков."""
            offset = 0
            while offset < file_size:
                yield offset, bytes(mm[offset:offset + self.chunk_size])
                offset += self.chunk_size
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            
            for offset, chunk in chunk_generator():
                future = executor.submit(self._process_chunk_worker, chunk, offset)
                futures.append(future)
                
                # Ограничиваем очередь
                if len(futures) >= self.num_workers * 2:
                    self._collect_results(futures[:self.num_workers], file_size, callback)
                    futures = futures[self.num_workers:]
            
            # Собираем оставшиеся
            if futures:
                self._collect_results(futures, file_size, callback)
    
    def _process_chunk_worker(self, chunk: bytes, offset: int) -> Tuple:
        """Обработчик чанка в отдельном потоке."""
        # Каждый поток имеет свою копию для изоляции
        grams = self._extract_ngrams(chunk)
        transitions = Counter()
        
        for i in range(len(grams) - 1):
            transitions[(grams[i], grams[i+1])] += 1
        
        entropy = self._calculate_chunk_entropy(chunk)
        
        return offset, Counter(grams), transitions, entropy
    
    def _collect_results(self, futures, file_size: int, callback):
        """Сбор результатов из потоков."""
        for future in futures:
            try:
                offset, gram_counter, transition_counter, entropy = future.result()
                
                # Обновляем глобальные счётчики
                self.gram_counter.update(gram_counter)
                self.transition_counter.update(transition_counter)
                self.entropy_samples.append(entropy)
                self.total_chunks += 1
                self.total_bytes += self.chunk_size
                self.bytes_processed += self.chunk_size
                
                progress = ChunkProgress(
                    chunk_id=self.total_chunks,
                    bytes_processed=self.bytes_processed,
                    total_bytes=file_size,
                    percentage=(self.bytes_processed / file_size) * 100,
                    new_grams=sum(gram_counter.values()),
                    new_transitions=sum(transition_counter.values()),
                )
                self.progress_history.append(progress)
                
                if callback:
                    callback(progress)
                
            except Exception as e:
                print(f"❌ Ошибка в потоке: {e}")
    
    def _extract_ngrams(self, data: bytes) -> List[bytes]:
        """Оптимизированное извлечение n-грамм."""
        if len(data) < self.n:
            return []
        arr = np.frombuffer(data, dtype=np.uint8)
        return [bytes(arr[i:i+self.n]) for i in range(len(arr) - self.n + 1)]
    
    def _calculate_chunk_entropy(self, data: bytes) -> float:
        """Энтропия чанка."""
        if not data:
            return 0.0
        byte_counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
        byte_probs = byte_counts[byte_counts > 0] / len(data)
        return -np.sum(byte_probs * np.log2(byte_probs))
    
    def _save_checkpoint(self):
        """Сохраняет состояние для возобновления."""
        if not self.checkpoint_file:
            return
        
        checkpoint = {
            'n': self.n,
            'total_chunks': self.total_chunks,
            'total_bytes': self.total_bytes,
            'bytes_processed': self.bytes_processed,
            'gram_counter': dict(self.gram_counter.most_common(10000)),
            'transition_counter': dict(list(self.transition_counter.items())[:10000]),
            'entropy_samples': self.entropy_samples[-100:],
            'timestamp': time.time(),
        }
        
        with open(self.checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint, f)
    
    def _load_checkpoint(self):
        """Восстанавливает состояние из чекпоинта."""
        try:
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint = pickle.load(f)
            
            self.total_chunks = checkpoint['total_chunks']
            self.total_bytes = checkpoint['total_bytes']
            self.bytes_processed = checkpoint['bytes_processed']
            self.gram_counter = Counter(checkpoint['gram_counter'])
            self.transition_counter = Counter(checkpoint['transition_counter'])
            self.entropy_samples = checkpoint['entropy_samples']
            
            print(f"🔄 Восстановлено состояние: {self.total_chunks} чанков, "
                  f"{self.total_bytes / 1024 / 1024:.1f} МБ")
        except Exception as e:
            print(f"⚠️ Не удалось загрузить чекпоинт: {e}")
    
    def finalize(self) -> Dict:
        """Финальная обработка и возврат результатов."""
        if not self.gram_counter:
            return {'status': 'error', 'message': 'No n-grams found'}
        
        unique_grams = len(self.gram_counter)
        total_grams = sum(self.gram_counter.values())
        total_transitions = sum(self.transition_counter.values())
        avg_entropy = np.mean(self.entropy_samples) if self.entropy_samples else 0
        
        # Строим топ-граммы
        top_grams = self.gram_counter.most_common(2000)
        gram_to_id = {g: i for i, (g, _) in enumerate(top_grams)}
        
        # Строим разреженную матрицу переходов
        transition_matrix = {}
        for (g1, g2), count in self.transition_counter.items():
            if g1 in gram_to_id and g2 in gram_to_id:
                key = f"{gram_to_id[g1]}:{gram_to_id[g2]}"
                transition_matrix[key] = transition_matrix.get(key, 0) + count
        
        # Определяем природу данных
        if avg_entropy < 3.5:
            nature = DataNature.TEXT
        elif avg_entropy < 5.0:
            nature = DataNature.PROTOCOL
        elif avg_entropy < 7.0:
            nature = DataNature.COMPRESSED
        elif avg_entropy < 7.8:
            nature = DataNature.ENCRYPTED
        else:
            nature = DataNature.HASH
        
        return {
            'status': 'success',
            'nature': nature.value,
            'total_bytes': self.total_bytes,
            'total_chunks': self.total_chunks,
            'unique_grams': unique_grams,
            'total_grams': total_grams,
            'total_transitions': total_transitions,
            'avg_entropy': avg_entropy,
            'top_grams': top_grams[:50],
            'gram_to_id': gram_to_id,
            'transition_matrix': transition_matrix,
            'processing_time': time.time() - self.start_time if self.start_time else 0,
        }

# ============================================================================
# ИНТЕГРАЦИЯ С CLEAN_FIELD (УЛУЧШЕННАЯ)
# ============================================================================

class CleanFieldStreamingAdapter:
    """
    Улучшенный адаптер для потоковой загрузки в clean_field.
    Поддерживает:
    - Возобновляемую загрузку
    - Многопоточность
    - Сохранение промежуточных результатов
    """
    
    def __init__(self, field_instance=None, work_dir: str = "./field_work"):
        self.field = field_instance
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        
        self.loader = None
        self.report = None
        self.current_file = None
    
    def stream_load(self, filepath: str, n: int = None, 
                   chunk_size: int = 1024 * 1024,
                   num_workers: int = None,
                   resume: bool = True) -> Optional[FieldReport]:
        """
        Потоковая загрузка файла в clean_field.
        
        Args:
            filepath: Путь к файлу
            n: Размер n-граммы (None = автоопределение)
            chunk_size: Размер чанка
            num_workers: Количество потоков
            resume: Возобновить предыдущую загрузку
        """
        
        # Определяем n если не указан
        if n is None:
            n = self._determine_optimal_n(filepath)
        
        # Файл чекпоинта
        checkpoint_file = self.work_dir / f"{Path(filepath).stem}_checkpoint.pkl"
        
        # Создаём загрузчик
        self.loader = ChunkedFieldLoader(
            n=n, 
            chunk_size=chunk_size,
            num_workers=num_workers,
            checkpoint_file=str(checkpoint_file) if resume else None
        )
        
        self.current_file = filepath
        
        # Прогресс-коллбек
        def progress_callback(progress: ChunkProgress):
            print(f"\r⏳ {progress.percentage:.1f}% | "
                  f"Грамм: {progress.new_grams} | "
                  f"Переходов: {progress.new_transitions}", end='', flush=True)
        
        # Обрабатываем файл
        stats = self.loader.process_file(
            filepath, 
            progress_callback=progress_callback,
            save_checkpoints=True
        )
        
        if stats.get('status') == 'error':
            print(f"\n❌ Ошибка: {stats['message']}")
            return None
        
        # Строим отчёт
        self.report = self._build_report(stats)
        
        # Обновляем clean_field
        if self.field:
            self._update_field(stats)
        
        # Сохраняем финальный отчёт
        report_file = self.work_dir / f"{Path(filepath).stem}_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.report.to_dict(), f, indent=2)
        
        print(f"\n📄 Отчёт сохранён: {report_file}")
        
        return self.report
    
    def _determine_optimal_n(self, filepath: str) -> int:
        """Автоопределение n по первым мегабайтам файла."""
        try:
            with open(filepath, 'rb') as f:
                sample = f.read(1024 * 1024)  # Первый мегабайт
            
            # Быстрый анализ энтропии
            byte_counts = np.bincount(np.frombuffer(sample, dtype=np.uint8), minlength=256)
            byte_probs = byte_counts[byte_counts > 0] / len(sample)
            entropy = -np.sum(byte_probs * np.log2(byte_probs))
            
            if entropy < 3.5:
                return 4
            elif entropy < 5.0:
                return 8
            elif entropy < 7.0:
                return 16
            else:
                return 32
        except:
            return 8
    
    def _build_report(self, stats: Dict) -> FieldReport:
        """Строит отчёт на основе статистик."""
        
        nature = DataNature(stats.get('nature', 'unknown'))
        avg_entropy = stats.get('avg_entropy', 0)
        
        unique_grams = stats.get('unique_grams', 0)
        total_grams = stats.get('total_grams', 1)
        total_transitions = stats.get('total_transitions', 0)
        
        # Индексы
        unique_ratio = unique_grams / max(1, total_grams)
        structure_index = 1.0 - min(1.0, unique_ratio)
        transition_density = total_transitions / max(1, unique_grams)
        
        return FieldReport(
            data_nature=nature,
            entropy=avg_entropy,
            structure_index=structure_index,
            complexity_score=structure_index * 0.8 + transition_density * 0.2,
            n_gram_size=self.loader.n if self.loader else 8,
            total_lemmas=unique_grams,
            total_exchanges=total_transitions,
            unique_grams=unique_grams,
            transition_density=transition_density,
            grammar_confidence=min(1.0, total_transitions / max(1, unique_grams * 2)),
            processing_time=stats.get('processing_time', 0),
        )
    
    def _update_field(self, stats: Dict):
        """Обновляет clean_field."""
        if hasattr(self.field, 'add_streaming_data'):
            self.field.add_streaming_data(
                grams=stats.get('top_grams', []),
                transitions=stats.get('transition_matrix', {}),
                n=stats.get('n', self.loader.n if self.loader else 8),
                entropy=stats.get('avg_entropy', 0),
            )
        else:
            # Сохраняем для последующей загрузки
            data_file = self.work_dir / f"{Path(self.current_file).stem}_field_data.json"
            with open(data_file, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            print(f"💾 Данные поля сохранены: {data_file}")

# ============================================================================
# ДЕМОНСТРАЦИЯ ПОТОКОВОЙ ОБРАБОТКИ
# ============================================================================

def demo_advanced_streaming():
    """Расширенная демонстрация потоковых возможностей."""
    print("╔══════════════════════════════════════════════╗")
    print("║   ПОТОКОВЫЙ АНАЛИЗ ДАННЫХ v3.1             ║")
    print("╚══════════════════════════════════════════════╝")
    
    # Создаём тестовый файл (100 МБ)
    test_file = "test_large_stream.dat"
    file_size_mb = 100
    
    print(f"\n📦 Генерация тестового файла ({file_size_mb} МБ)...")
    
    with open(test_file, 'wb') as f:
        # Текст (30%)
        text_chunk = b"Hello SpectraVortex! This is a test of streaming analysis. " * 1000
        for _ in range(int(file_size_mb * 0.3 * 1024 * 1024 / len(text_chunk))):
            f.write(text_chunk)
        
        # Бинарные данные (40%)
        binary_chunk = b'\x01\x02\x03\x04\x05\x06\x07\x08' * 1000
        for _ in range(int(file_size_mb * 0.4 * 1024 * 1024 / len(binary_chunk))):
            f.write(binary_chunk)
        
        # Случайные данные (30%)
        random_data = np.random.bytes(int(file_size_mb * 0.3 * 1024 * 1024))
        f.write(random_data)
    
    print(f"✅ Файл создан: {os.path.getsize(test_file) / 1024 / 1024:.1f} МБ")
    
    # Тест 1: Последовательная обработка
    print(f"\n{'='*50}")
    print(f"ТЕСТ 1: Последовательная обработка")
    print(f"{'='*50}")
    
    adapter = CleanFieldStreamingAdapter(work_dir="./stream_test_1")
    report = adapter.stream_load(test_file, n=8, num_workers=1)
    
    if report:
        print(report.summary())
    
    # Тест 2: Многопоточная обработка
    print(f"\n{'='*50}")
    print(f"ТЕСТ 2: Многопоточная обработка")
    print(f"{'='*50}")
    
    adapter2 = CleanFieldStreamingAdapter(work_dir="./stream_test_2")
    report2 = adapter2.stream_load(test_file, n=8, num_workers=4)
    
    if report2:
        print(report2.summary())
    
    # Сравнение производительности
    if report and report2:
        speedup = report.processing_time / max(0.1, report2.processing_time)
        print(f"\n📊 Сравнение производительности:")
        print(f"   Последовательно: {report.processing_time:.1f}с")
        print(f"   Многопоточно: {report2.processing_time:.1f}с")
        print(f"   Ускорение: {speedup:.1f}x")
    
    # Очистка
    os.remove(test_file)
    import shutil
    shutil.rmtree("./stream_test_1", ignore_errors=True)
    shutil.rmtree("./stream_test_2", ignore_errors=True)
    
    print(f"\n🧹 Тестовые данные удалены")
    print(f"✅ Демонстрация завершена")

if __name__ == "__main__":
    demo_advanced_streaming()