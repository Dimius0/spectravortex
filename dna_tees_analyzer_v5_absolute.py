#!/usr/bin/env python3
"""
🧬 TEES DNA Analyzer v5.0 — Абсолютная версия
═══════════════════════════════════════
Принципы:
  • Абсолютный детерминизм — структура, а не статистика
  • Энтропия 1.0 — равномерное распределение информации
  • Нет шума — есть недостаток данных

Технологии:
  • TEES — когерентный резонанс через фазовый портрет
  • BIP2100 CHAOS — сжатие ДНК в 12 слов
  • SHA-256 — мгновенная идентификация структуры
  • TSP-поиск — ближайший резонанс в базе
  • SQLite — кэширование результатов
"""

import numpy as np
import sys
import os
import json
import sqlite3
import hashlib
from datetime import datetime
from itertools import product
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# ============ BIP2100 CHAOS ============

class ChaosIdentity:
    """Генератор хаос-фраз (BIP2100)"""
    
    def __init__(self, seed=None):
        self.seed = seed
        self.words = self._generate_chaos_words()
        self.phrase = None
        self.hybrid_id = None
    
    def _generate_chaos_words(self, count=2100):
        """Генерация 2100 хаос-слов (BIP2100)"""
        import random
        if self.seed:
            random.seed(self.seed)
        
        words = []
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for _ in range(count):
            length = random.randint(5, 14)
            word = ''.join(random.choice(chars) for _ in range(length))
            words.append(word)
        
        return words
    
    def generate_chaos_phrase(self, num_words=12):
        """Генерация хаос-фразы из num_words слов"""
        import random
        if self.seed:
            random.seed(self.seed)
        
        # Выбираем слова детерминированно
        indices = list(range(len(self.words)))
        random.shuffle(indices)
        selected = [self.words[i] for i in indices[:num_words]]
        
        self.phrase = ' '.join(selected)
        self.hybrid_id = hashlib.sha256(self.phrase.encode()).hexdigest()
        return self.phrase
    
    def get_hybrid_id(self):
        return self.hybrid_id

# ============ ЗАГРУЗКА ДНК ============

def load_fasta(filepath):
    """Загрузка FASTA"""
    seq = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if not line.startswith('>'):
                    seq.append(line.strip())
    except:
        return ""
    seq_text = ''.join(seq).upper()
    return ''.join(c for c in seq_text if c in 'ACGTUN')

# ============ ФАЗОВЫЙ ПОРТРЕТ ============

def dna_to_phase_portrait(seq, window=3):
    """Строит фазовый портрет ДНК (комплексная плоскость)"""
    mapping = {'A': 1+0j, 'C': 0+1j, 'G': -1+0j, 'T': 0-1j, 'U': 0-1j, 'N': 0+0j}
    complex_seq = np.array([mapping.get(c, 0+0j) for c in seq], dtype=np.complex64)
    
    phase_portrait = []
    for i in range(len(complex_seq) - window + 1):
        window_sum = np.sum(complex_seq[i:i+window])
        phase_portrait.append(window_sum / window)
    
    if len(phase_portrait) == 0:
        return np.array([0+0j], dtype=np.complex64)
    
    return np.array(phase_portrait, dtype=np.complex64)

def dna_to_chaos_vector(seq):
    """Кодирует ДНК в хаос-вектор через BIP2100"""
    dna_hash = hashlib.sha256(seq.encode()).hexdigest()
    chaos = ChaosIdentity(seed=dna_hash[:16])
    phrase = chaos.generate_chaos_phrase(12)
    
    words = phrase.split()
    word_hashes = [hashlib.sha256(w.encode()).hexdigest()[:8] for w in words]
    
    return np.array([int(h, 16) / (16**8) for h in word_hashes], dtype=np.float32)

# ============ ТОПОЛОГИЧЕСКИЙ РЕЗОНАНС ============

def tees_resonance_absolute(v1, v2):
    """
    Абсолютный топологический резонанс через свёртку.
    Всегда возвращает значение в [0, 1], где 1 = полная когерентность.
    """
    # Если векторы комплексные — работаем с ними напрямую
    if np.iscomplexobj(v1) or np.iscomplexobj(v2):
        n = min(len(v1), len(v2))
        v1 = v1[:n]
        v2 = v2[:n]
        
        # Центрирование
        v1_centered = v1 - np.mean(v1)
        v2_centered = v2 - np.mean(v2)
        
        if np.std(np.abs(v1_centered)) < 1e-10 or np.std(np.abs(v2_centered)) < 1e-10:
            return 0.0
        
        # БПФ
        f1 = np.fft.fft(v1_centered)
        f2 = np.fft.fft(v2_centered)
        
        # Когерентность
        cross = f1 * np.conj(f2)
        coh = np.abs(cross) / (np.abs(f1) * np.abs(f2) + 1e-12)
        coh = np.clip(coh, 0, 1)
        
        coherence = float(np.mean(coh[1:]))
        
        # Фазовый сдвиг
        phase_diff = np.abs(np.angle(f1) - np.angle(f2))
        phase_shift = float(np.mean(np.minimum(phase_diff, 2*np.pi - phase_diff)) / np.pi)
        
        # Итоговый резонанс
        resonance = coherence * (1.0 - phase_shift)
        
        return float(np.clip(resonance, 0.0, 1.0))
    
    else:
        # Для действительных векторов
        n = min(len(v1), len(v2))
        v1 = v1[:n]
        v2 = v2[:n]
        
        v1_centered = v1 - np.mean(v1)
        v2_centered = v2 - np.mean(v2)
        
        if np.std(v1_centered) < 1e-10 or np.std(v2_centered) < 1e-10:
            return 0.0
        
        f1 = np.fft.fft(v1_centered)
        f2 = np.fft.fft(v2_centered)
        
        cross = f1 * np.conj(f2)
        coh = np.abs(cross) / (np.abs(f1) * np.abs(f2) + 1e-12)
        coh = np.clip(coh, 0, 1)
        
        coherence = float(np.mean(coh[1:]))
        
        phase_diff = np.abs(np.angle(f1) - np.angle(f2))
        phase_shift = float(np.mean(np.minimum(phase_diff, 2*np.pi - phase_diff)) / np.pi)
        
        resonance = coherence * (1.0 - phase_shift)
        
        return float(np.clip(resonance, 0.0, 1.0))

# ============ КЭШ (SQLite) ============

class ResonanceCache:
    """Кэш для хранения вычисленных резонансов"""
    
    def __init__(self, db_path='resonance_cache.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resonances (
                hash1 TEXT,
                hash2 TEXT,
                method TEXT,
                resonance REAL,
                phase_shift REAL,
                timestamp TEXT,
                PRIMARY KEY (hash1, hash2, method)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sequences (
                hash TEXT PRIMARY KEY,
                name TEXT,
                length INTEGER,
                chaos_phrase TEXT,
                created TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def get(self, hash1, hash2, method='phase'):
        """Получить резонанс из кэша"""
        if hash1 > hash2:
            hash1, hash2 = hash2, hash1
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT resonance, phase_shift FROM resonances WHERE hash1=? AND hash2=? AND method=?',
            (hash1, hash2, method)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {'resonance': row[0], 'phase_shift': row[1], 'cached': True}
        return None
    
    def put(self, hash1, hash2, method, resonance, phase_shift):
        """Сохранить резонанс в кэш"""
        if hash1 > hash2:
            hash1, hash2 = hash2, hash1
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO resonances (hash1, hash2, method, resonance, phase_shift, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
            (hash1, hash2, method, resonance, phase_shift, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    
    def put_sequence(self, hash_id, name, length, chaos_phrase):
        """Сохранить информацию о последовательности"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO sequences (hash, name, length, chaos_phrase, created) VALUES (?, ?, ?, ?, ?)',
            (hash_id, name, length, chaos_phrase, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    
    def get_all_hashes(self):
        """Получить все хеши из базы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT hash, name, chaos_phrase FROM sequences')
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def get_all_resonances(self, method='phase'):
        """Получить все резонансы для метода"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT hash1, hash2, resonance FROM resonances WHERE method=?',
            (method,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

# ============ ОСНОВНОЙ АНАЛИЗАТОР ============

class DNAAnalyzerAbsolute:
    """Абсолютный TEES-анализатор ДНК"""
    
    def __init__(self, cache=True, db_path='resonance_cache.db'):
        self.sequences = {}
        self.cache = ResonanceCache(db_path) if cache else None
        self.results = {}
        self.sequence_hashes = {}
    
    def load_sequences(self, filepaths):
        """Загрузка последовательностей"""
        for filepath in filepaths:
            if not os.path.exists(filepath):
                print(f"⚠️ Файл не найден: {filepath}")
                continue
            
            name = os.path.basename(filepath).split('.')[0]
            seq = load_fasta(filepath)
            
            if len(seq) < 50:
                print(f"❌ Слишком короткая последовательность: {filepath}")
                continue
            
            self.sequences[name] = seq
            print(f"📁 {name}: {len(seq):,} bp")
    
    def get_sequence_hash(self, seq, method='phase'):
        """Получить SHA-256 хеш последовательности"""
        if method == 'phase':
            portrait = dna_to_phase_portrait(seq)
            real_bytes = np.real(portrait).astype(np.float32).tobytes()
            imag_bytes = np.imag(portrait).astype(np.float32).tobytes()
            return hashlib.sha256(real_bytes + imag_bytes).hexdigest()
        elif method == 'chaos':
            chaos = dna_to_chaos_vector(seq)
            return hashlib.sha256(chaos.tobytes()).hexdigest()
        else:
            return hashlib.sha256(seq.encode()).hexdigest()
    
    def get_chaos_phrase(self, seq):
        """Получить хаос-фразу для последовательности"""
        dna_hash = hashlib.sha256(seq.encode()).hexdigest()
        chaos = ChaosIdentity(seed=dna_hash[:16])
        return chaos.generate_chaos_phrase(12)
    
    def compare_pair(self, seq1, seq2, method='phase', name1='', name2=''):
        """Сравнивает две последовательности"""
        # Нормализация длины
        min_len = min(len(seq1), len(seq2))
        if min_len > 1000:
            seq1 = seq1[:1000]
            seq2 = seq2[:1000]
        
        # Проверяем кэш
        hash1 = self.get_sequence_hash(seq1, method)
        hash2 = self.get_sequence_hash(seq2, method)
        
        if self.cache:
            cached = self.cache.get(hash1, hash2, method)
            if cached:
                return cached
        
        # Вычисляем резонанс
        if method == 'phase':
            v1 = dna_to_phase_portrait(seq1)
            v2 = dna_to_phase_portrait(seq2)
        elif method == 'chaos':
            v1 = dna_to_chaos_vector(seq1)
            v2 = dna_to_chaos_vector(seq2)
        else:
            mapping = {'A': 1, 'C': 2, 'G': 3, 'T': 4, 'U': 4, 'N': 0}
            v1 = np.array([mapping.get(c, 0) for c in seq1], dtype=np.float32)
            v2 = np.array([mapping.get(c, 0) for c in seq2], dtype=np.float32)
        
        resonance = tees_resonance_absolute(v1, v2)
        phase_shift = 1.0 - resonance
        
        # Сохраняем в кэш
        if self.cache:
            self.cache.put(hash1, hash2, method, resonance, phase_shift)
            self.cache.put_sequence(hash1, name1 or 'unknown', len(seq1), self.get_chaos_phrase(seq1))
            self.cache.put_sequence(hash2, name2 or 'unknown', len(seq2), self.get_chaos_phrase(seq2))
        
        return {
            'resonance': resonance,
            'phase_shift': phase_shift,
            'cached': False,
            'hash1': hash1,
            'hash2': hash2
        }
    
    def compare_all(self, methods=['phase', 'chaos']):
        """Сравнивает все последовательности"""
        names = list(self.sequences.keys())
        n = len(names)
        
        for method in methods:
            print(f"\n{'='*80}")
            print(f"🔬 Метод: {method}")
            print(f"{'='*80}")
            
            matrix = np.zeros((n, n))
            phase_matrix = np.zeros((n, n))
            detailed = {}
            
            import time
            start = time.time()
            
            for i, name1 in enumerate(names):
                for j, name2 in enumerate(names):
                    if i == j:
                        matrix[i][j] = 1.0
                        continue
                    
                    result = self.compare_pair(
                        self.sequences[name1],
                        self.sequences[name2],
                        method,
                        name1,  # ← реальное имя
                        name2   # ← реальное имя
                    )
                    
                    matrix[i][j] = result['resonance']
                    phase_matrix[i][j] = result['phase_shift']
                    detailed[f"{name1}_vs_{name2}"] = result
            
            elapsed = time.time() - start
            
            # Вывод матрицы резонанса
            print(f"\n📊 Матрица резонанса:")
            header = "        " + " ".join(f"{n:>14}" for n in names)
            print(header)
            for i, name in enumerate(names):
                row = f"{name:>8} " + " ".join(f"{matrix[i][j]:>14.4f}" for j in range(n))
                print(row)
            
            # Вывод SHA-256 хешей
            print(f"\n🔐 SHA-256 хеши:")
            for name in names:
                seq_hash = self.get_sequence_hash(self.sequences[name], method)
                print(f"  {name}: {seq_hash[:16]}...")
            
            print(f"\n⏱️ Время: {elapsed:.3f} сек")
            
            self.results[method] = {
                'matrix': matrix,
                'phase_matrix': phase_matrix,
                'detailed': detailed,
                'names': names
            }
        
        return self.results
    
    def find_best_match(self, seq, method='phase'):
        """Находит лучший резонанс для последовательности в базе (TSP-поиск)"""
        if not self.cache:
            return None
        
        seq_hash = self.get_sequence_hash(seq, method)
        
        # Все резонансы из базы
        all_resonances = self.cache.get_all_resonances(method)
        all_hashes = self.cache.get_all_hashes()
        
        # Строим словарь хеш -> имя
        hash_to_name = {h: name for h, name, _ in all_hashes}
        
        # Ищем лучший резонанс
        best_match = None
        best_resonance = -1
        
        for h1, h2, res in all_resonances:
            if h1 == seq_hash:
                if res > best_resonance:
                    best_resonance = res
                    best_match = (hash_to_name.get(h2, 'unknown'), h2, res)
            elif h2 == seq_hash:
                if res > best_resonance:
                    best_resonance = res
                    best_match = (hash_to_name.get(h1, 'unknown'), h1, res)
        
        return best_match
    
    def interpret(self, resonance, length):
        """Интерпретация результата с учётом длины"""
        if length < 100:
            return "⚠️ Недостаточно данных для достоверного вывода"
        elif resonance > 0.85:
            return "✅ Когерентность 1.0: Структурно идентичны"
        elif resonance > 0.65:
            return "🔶 Когерентность 0.65-0.85: Общий паттерн, локальные различия"
        elif resonance > 0.40:
            return "🔸 Когерентность 0.40-0.65: Частичное сходство"
        else:
            return "🔴 Низкая когерентность: Разные топологические структуры"
    
    def save_results(self, output_dir='tees_results_absolute'):
        """Сохранение результатов"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        output = {
            'timestamp': timestamp,
            'version': '5.0',
            'sequences': {name: len(seq) for name, seq in self.sequences.items()},
            'results': {}
        }
        
        for method, data in self.results.items():
            output['results'][method] = {
                'matrix': data['matrix'].tolist(),
                'phase_matrix': data['phase_matrix'].tolist(),
                'names': data['names']
            }
        
        json_file = os.path.join(output_dir, f'dna_analysis_absolute_{timestamp}.json')
        with open(json_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Результаты сохранены: {json_file}")
        return output

# ============ ГЛАВНАЯ ============

def main():
    print("""
    🧬 TEES DNA Analyzer v5.0 — Абсолютная версия
    ═══════════════════════════════════════
    Принципы:
      • Абсолютный детерминизм
      • Энтропия 1.0
      • Нет шума — есть недостаток данных
    
    Технологии:
      • TEES-резонанс через фазовый портрет
      • BIP2100 CHAOS — сжатие в 12 слов
      • SHA-256 — мгновенная идентификация
      • SQLite — кэширование
      • TSP-поиск — ближайший резонанс
    """)
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python dna_tees_analyzer_v5_absolute.py <файл1.fasta> [файл2.fasta ...]")
        print("\nОпции:")
        print("  --methods phase,chaos  Выбор методов (по умолчанию: phase,chaos)")
        print("  --no-cache            Отключить кэширование")
        print("  --find HASH           Найти лучший резонанс для хеша")
        return
    
    # Парсинг
    filepaths = []
    methods = ['phase', 'chaos']
    use_cache = True
    find_hash = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--no-cache':
            use_cache = False
        elif arg == '--methods':
            if i + 1 < len(sys.argv):
                methods = sys.argv[i + 1].split(',')
                i += 1
        elif arg == '--find':
            if i + 1 < len(sys.argv):
                find_hash = sys.argv[i + 1]
                i += 1
        elif not arg.startswith('--'):
            filepaths.append(arg)
        i += 1
    
    # Создаём анализатор
    analyzer = DNAAnalyzerAbsolute(cache=use_cache)
    
    if find_hash:
        print(f"\n🔍 Поиск резонанса для хеша: {find_hash}")
        
        if not analyzer.cache:
            print("❌ Кэширование отключено")
            return
        
        # Получаем все хеши
        all_hashes = analyzer.cache.get_all_hashes()
        
        # Ищем по префиксу
        matching = []
        for h, name, phrase in all_hashes:
            if h.startswith(find_hash.lower()):
                matching.append((h, name, phrase))
        
        if not matching:
            print(f"❌ Хеш с префиксом '{find_hash}' не найден в базе")
            print("💡 Доступные хеши:")
            for h, name, _ in all_hashes:
                print(f"  {name}: {h[:32]}...")
            return
        
        print(f"✅ Найдено {len(matching)} совпадений:")
        for h, name, phrase in matching:
            print(f"  {name}: {h}")
        
        # Ищем резонансы
        for method in methods:
            all_resonances = analyzer.cache.get_all_resonances(method)
            
            for target_hash, target_name, _ in matching:
                print(f"\n📊 Резонансы для {target_name} (метод: {method}):")
                
                found = False
                for h1, h2, res in all_resonances:
                    if h1 == target_hash or h2 == target_hash:
                        other = h2 if h1 == target_hash else h1
                        
                        # Ищем имя
                        other_name = None
                        for h, name, _ in all_hashes:
                            if h == other:
                                other_name = name
                                break
                        
                        print(f"  ↔ {other_name or other[:16]}...: {res:.4f}")
                        found = True
                
                if not found:
                    print("  Нет сохранённых резонансов")
        
        return
    
    if len(filepaths) < 2:
        print("❌ Нужно минимум 2 FASTA файла")
        return
    
    # Загрузка
    analyzer.load_sequences(filepaths)
    
    if len(analyzer.sequences) < 2:
        print("❌ Нужно минимум 2 последовательности")
        return
    
    # Анализ
    analyzer.compare_all(methods)
    
    # Вывод интерпретаций
    print("\n🎯 Интерпретация результатов:")
    print("=" * 80)
    
    for method, data in analyzer.results.items():
        print(f"\n🔬 Метод: {method}")
        matrix = data['matrix']
        names = data['names']
        
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                resonance = matrix[i][j]
                length = min(len(analyzer.sequences[names[i]]), len(analyzer.sequences[names[j]]))
                interpretation = analyzer.interpret(resonance, length)
                print(f"  {names[i]} ↔ {names[j]}: {resonance:.4f} — {interpretation}")
    
    # Сохранение
    analyzer.save_results()
    
    print("\n✅ Анализ завершён!")
    if use_cache:
        print("💡 Результаты закэшированы в resonance_cache.db")
    
    # Вывод хаос-фраз
    print("\n🧬 Хаос-фразы (BIP2100):")
    for name, seq in analyzer.sequences.items():
        phrase = analyzer.get_chaos_phrase(seq)
        print(f"  {name}: {phrase[:60]}...")
    
    # Вывод SHA-256 хешей
    print("\n🔐 SHA-256 идентификаторы:")
    for name, seq in analyzer.sequences.items():
        seq_hash = analyzer.get_sequence_hash(seq, 'phase')
        print(f"  {name}: {seq_hash[:32]}...")

if __name__ == "__main__":
    main()