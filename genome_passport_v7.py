#!/usr/bin/env python3
"""
🧬 TEES Genome Passport v7.0 — Full Edition
═══════════════════════════════════════
Все функции:
  • --fast режим (Jaccard + кэш)
  • CSV экспорт
  • Эталон популяции
  • TSP-поиск ближайшего родственника
  • Визуализация тепловой карты

Использование:
  python genome_passport_v7.py genome1.fasta genome2.fasta [genome3.fasta ...]
  
Опции:
  --fast          Быстрый режим (только Jaccard)
  --window N      Размер окна (по умолчанию: 1000)
  --step N        Шаг окна (по умолчанию: 500)
  --csv           Экспорт в CSV
  --reference     Создать эталон популяции
  --find HASH     Найти ближайшего родственника по хешу
"""

import numpy as np
import sys
import os
import csv
import hashlib
import sqlite3
import json
import random
from datetime import datetime
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

# ============ ЗАГРУЗКА ============

def load_fasta(filepath):
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
    mapping = {'A': 1+0j, 'C': 0+1j, 'G': -1+0j, 'T': 0-1j, 'U': 0-1j, 'N': 0+0j}
    complex_seq = np.array([mapping.get(c, 0+0j) for c in seq], dtype=np.complex64)
    
    phase_portrait = []
    for i in range(len(complex_seq) - window + 1):
        window_sum = np.sum(complex_seq[i:i+window])
        phase_portrait.append(window_sum / window)
    
    return np.array(phase_portrait, dtype=np.complex64)

# ============ TEES РЕЗОНАНС ============

def tees_resonance_absolute(v1, v2):
    n = min(len(v1), len(v2))
    if n < 10:
        return 0.0
    
    v1 = v1[:n]
    v2 = v2[:n]
    
    v1_centered = v1 - np.mean(v1)
    v2_centered = v2 - np.mean(v2)
    
    if np.std(np.abs(v1_centered)) < 1e-10 or np.std(np.abs(v2_centered)) < 1e-10:
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

# ============ ОСНОВНОЙ КЛАСС ============

class GenomePassport:
    def __init__(self, window_size=1000, step=500, fast_mode=False, cache_db='window_resonance_cache.db'):
        self.window_size = window_size
        self.step = step
        self.fast_mode = fast_mode
        self.genomes = {}
        self.passports = {}
        self.reference = None
        self.cache_db = cache_db
        self._init_cache()
    
    def _init_cache(self):
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS window_resonances (
                hash1 TEXT,
                hash2 TEXT,
                resonance REAL,
                PRIMARY KEY (hash1, hash2)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passport_index (
                name TEXT,
                hash TEXT,
                PRIMARY KEY (name, hash)
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_cached_resonance(self, hash1, hash2):
        if hash1 > hash2:
            hash1, hash2 = hash2, hash1
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('SELECT resonance FROM window_resonances WHERE hash1=? AND hash2=?', (hash1, hash2))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def put_cached_resonance(self, hash1, hash2, resonance):
        if hash1 > hash2:
            hash1, hash2 = hash2, hash1
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO window_resonances VALUES (?, ?, ?)', (hash1, hash2, resonance))
        conn.commit()
        conn.close()
    
    def load_genomes(self, filepaths):
        for filepath in filepaths:
            if not os.path.exists(filepath):
                print(f"⚠️ Файл не найден: {filepath}")
                continue
            
            name = os.path.basename(filepath).split('.')[0]
            seq = load_fasta(filepath)
            
            if len(seq) < 100:
                print(f"❌ Слишком короткий геном: {filepath}")
                continue
            
            self.genomes[name] = seq
            print(f"📁 {name}: {len(seq):,} bp")
        
        # Автоподстройка окна
        if self.genomes:
            min_len = min(len(seq) for seq in self.genomes.values())
            
            if self.window_size > min_len // 2:
                old_window = self.window_size
                self.window_size = max(100, min_len // 3)
                self.step = self.window_size // 2
                print(f"\n⚙️ Автоподстройка: окно {old_window} → {self.window_size} bp")
                print(f"   Шаг: {self.step} bp")

    def auto_window_size(self, min_length):
        """Автоматический выбор размера окна"""
        if min_length < 500:
            return 100
        elif min_length < 2000:
            return 200
        elif min_length < 10000:
            return 500
        else:
            return 1000            
    
    def create_passport(self, name, seq):
        windows = []
        hashes = set()
        
        for i in range(0, len(seq) - self.window_size + 1, self.step):
            window = seq[i:i+self.window_size]
            if 'N' not in window:
                portrait = dna_to_phase_portrait(window)
                real_bytes = np.real(portrait).astype(np.float32).tobytes()
                imag_bytes = np.imag(portrait).astype(np.float32).tobytes()
                window_hash = hashlib.sha256(real_bytes + imag_bytes).hexdigest()
                
                windows.append({
                    'start': i,
                    'end': i + self.window_size,
                    'portrait': portrait,
                    'hash': window_hash
                })
                hashes.add(window_hash)
                
                # Индексация для TSP
                conn = sqlite3.connect(self.cache_db)
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO passport_index VALUES (?, ?)', (name, window_hash))
                conn.commit()
                conn.close()
        
        self.passports[name] = {
            'windows': windows,
            'hashes': hashes,
            'total_windows': len(windows)
        }
        
        print(f"   🧬 {name}: {len(windows)} окон по {self.window_size} bp")
        return self.passports[name]
    
    def jaccard_similarity(self, set1, set2):
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def compare_pair_fast(self, name1, name2):
        """Быстрое сравнение через Jaccard"""
        p1 = self.passports[name1]
        p2 = self.passports[name2]

        # 👇  ПРОВЕРКА
        if p1['total_windows'] == 0 or p2['total_windows'] == 0:
            return {
                'pair': f"{name1} ↔ {name2}",
                'identical_ratio': 0.0,
                'jaccard': 0.0,
                'avg_resonance': 0.0,
                'kinship_index': 0.0,
                'samples': 0,
                'method': 'fast'
            }
        
        jaccard = self.jaccard_similarity(p1['hashes'], p2['hashes'])
        identical_ratio = len(p1['hashes'] & p2['hashes']) / max(p1['total_windows'], p2['total_windows'])
        
        return {
            'pair': f"{name1} ↔ {name2}",
            'identical_ratio': identical_ratio,
            'jaccard': jaccard,
            'avg_resonance': 0.0,
            'kinship_index': 0.5 * jaccard + 0.5 * identical_ratio,
            'samples': 0,
            'method': 'fast'
        }
    
    def compare_pair_full(self, name1, name2):
        """Полное сравнение через TEES-резонанс"""
        p1 = self.passports[name1]
        p2 = self.passports[name2]

        # 👇 ДОБАВЬ ПРОВЕРКУ
        if p1['total_windows'] == 0 or p2['total_windows'] == 0:
            return {
                'pair': f"{name1} ↔ {name2}",
                'identical_ratio': 0.0,
                'jaccard': 0.0,
                'avg_resonance': 0.0,
                'kinship_index': 0.0,
                'samples': 0,
                'method': 'full'
            }
        
        # Идентичные окна
        common_hashes = p1['hashes'] & p2['hashes']
        identical_ratio = len(common_hashes) / max(p1['total_windows'], p2['total_windows'])
        
        # Jaccard
        jaccard = self.jaccard_similarity(p1['hashes'], p2['hashes'])
        
        # TEES-резонанс
        max_samples = min(30, p1['total_windows'], p2['total_windows'])
        
        random.seed(42)
        sample1 = random.sample(p1['windows'], max_samples)
        sample2 = random.sample(p2['windows'], max_samples)
        
        resonances = []
        for w1 in sample1:
            best_res = 0.0
            for w2 in sample2:
                if w1['hash'] == w2['hash']:
                    continue
                
                cached = self.get_cached_resonance(w1['hash'], w2['hash'])
                if cached is not None:
                    res = cached
                else:
                    res = tees_resonance_absolute(w1['portrait'], w2['portrait'])
                    self.put_cached_resonance(w1['hash'], w2['hash'], res)
                
                best_res = max(best_res, res)
            resonances.append(best_res)
        
        avg_resonance = np.mean(resonances) if resonances else 0.0
        
        # Итоговый индекс
        kinship_index = 0.4 * avg_resonance + 0.3 * identical_ratio + 0.3 * jaccard
        
        return {
            'pair': f"{name1} ↔ {name2}",
            'identical_ratio': identical_ratio,
            'jaccard': jaccard,
            'avg_resonance': avg_resonance,
            'kinship_index': kinship_index,
            'samples': len(resonances),
            'method': 'full'
        }
    
    def compare_pair(self, name1, name2):
        """Выбор метода сравнения"""
        if self.fast_mode:
            return self.compare_pair_fast(name1, name2)
        else:
            return self.compare_pair_full(name1, name2)
    
    def compare_all(self):
        names = list(self.genomes.keys())
        results = []
        
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                result = self.compare_pair(names[i], names[j])
                if result:
                    results.append(result)
        
        return results
    
    def create_reference(self):
        """Создание эталона популяции"""
        print("\n👥 Создание эталона популяции...")
        
        all_hashes = set()
        hash_counts = Counter()
        
        for name, data in self.passports.items():
            all_hashes |= data['hashes']
            hash_counts.update(data['hashes'])
        
        n_genomes = len(self.passports)
        
        # Хеши у всех
        common_hashes = set.intersection(*[data['hashes'] for data in self.passports.values()]) if n_genomes > 1 else set()
        
        # Хеши у большинства (>50%)
        majority_hashes = {h for h, c in hash_counts.items() if c > n_genomes / 2}
        
        # Хеши у меньшинства (<50%)
        minority_hashes = {h for h, c in hash_counts.items() if c <= n_genomes / 2}
        
        self.reference = {
            'all': all_hashes,
            'common': common_hashes,
            'majority': majority_hashes,
            'minority': minority_hashes,
            'total_genomes': n_genomes
        }
        
        print(f"   Всего уникальных окон: {len(all_hashes):,}")
        print(f"   Общих для всех: {len(common_hashes):,}")
        print(f"   У большинства (>50%): {len(majority_hashes):,}")
        print(f"   У меньшинства (<50%): {len(minority_hashes):,}")
        
        return self.reference
    
    def compare_to_reference(self, name):
        """Сравнение генома с эталоном"""
        if not self.reference:
            return None
        
        p = self.passports[name]
        
        # Jaccard с эталоном
        jaccard_all = self.jaccard_similarity(p['hashes'], self.reference['all'])
        jaccard_majority = self.jaccard_similarity(p['hashes'], self.reference['majority'])
        
        # Отклонение от нормы
        deviation = 1.0 - jaccard_majority
        
        return {
            'name': name,
            'jaccard_all': jaccard_all,
            'jaccard_majority': jaccard_majority,
            'deviation': deviation,
            'interpretation': 'Норма' if deviation < 0.3 else 'Отклонение' if deviation < 0.5 else 'Аномалия'
        }
    
    def find_nearest_tsp(self, target_hash, top_k=10):
        """TSP-поиск ближайшего родственника по хешу"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Все хеши из базы
        cursor.execute('SELECT name, hash FROM passport_index')
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Группируем хеши по именам
        name_hashes = defaultdict(set)
        for name, hash_val in rows:
            name_hashes[name].add(hash_val)
        
        # Ищем ближайших
        distances = []
        for name, hashes in name_hashes.items():
            jaccard = self.jaccard_similarity({target_hash}, hashes)
            distance = 1.0 - jaccard
            distances.append((name, distance, jaccard))
        
        distances.sort(key=lambda x: x[1])
        return distances[:top_k]
    
    def plot_kinship_matrix(self, results):
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            names = list(self.genomes.keys())
            n = len(names)
            matrix = np.ones((n, n))
            
            for r in results:
                parts = r['pair'].split(' ↔ ')
                i = names.index(parts[0])
                j = names.index(parts[1])
                matrix[i][j] = r['kinship_index']
                matrix[j][i] = r['kinship_index']
            
            plt.figure(figsize=(8, 6))
            sns.heatmap(matrix, annot=True, fmt='.3f', cmap='YlOrRd',
                        xticklabels=names, yticklabels=names,
                        vmin=0, vmax=1, square=True)
            plt.title(f'Kinship Matrix ({self.fast_mode and "Fast" or "Full"} mode)')
            plt.tight_layout()
            plt.savefig(f'kinship_matrix_{"fast" if self.fast_mode else "full"}.png', dpi=150)
            plt.close()
            print(f"📊 Тепловая карта сохранена")
        except ImportError:
            pass
    
    def export_csv(self, results, filename=None):
        if filename is None:
            filename = f'kinship_{"fast" if self.fast_mode else "full"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Pair', 'Identical_Ratio', 'Jaccard', 'Avg_Resonance', 'Kinship_Index', 'Method'])
            
            for r in results:
                writer.writerow([
                    r['pair'],
                    f"{r['identical_ratio']:.6f}",
                    f"{r['jaccard']:.6f}",
                    f"{r['avg_resonance']:.6f}",
                    f"{r['kinship_index']:.6f}",
                    r['method']
                ])
        
        print(f"📄 CSV сохранён: {filename}")
        return filename
    
    def save_passports(self, output_dir='genome_passports'):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for name, data in self.passports.items():
            passport_data = {
                'name': name,
                'total_windows': data['total_windows'],
                'window_size': self.window_size,
                'step': self.step,
                'hashes': list(data['hashes']),
                'timestamp': datetime.now().isoformat()
            }
            
            filename = os.path.join(output_dir, f'passport_{name}.json')
            with open(filename, 'w') as f:
                json.dump(passport_data, f, indent=2)
            
            print(f"💾 Паспорт сохранён: {filename}")

# ============ ГЛАВНАЯ ============

def main():
    print("""
    🧬 TEES Genome Passport v7.0 — Full Edition
    ═══════════════════════════════════════
    Все функции:
      • --fast режим (Jaccard + кэш)
      • CSV экспорт
      • Эталон популяции
      • TSP-поиск ближайшего родственника
    """)
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python genome_passport_v7.py genome1.fasta genome2.fasta [genome3.fasta ...]")
        print("\nОпции:")
        print("  --fast          Быстрый режим (только Jaccard)")
        print("  --window N      Размер окна (по умолчанию: 1000)")
        print("  --step N        Шаг окна (по умолчанию: 500)")
        print("  --csv           Экспорт в CSV")
        print("  --reference     Создать эталон популяции")
        print("  --find HASH     Найти ближайшего родственника")
        return
    
    # Парсинг аргументов
    filepaths = []
    fast_mode = False
    export_csv_flag = False
    create_ref_flag = False
    find_hash = None
    window_size = 1000
    step = 500
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--fast':
            fast_mode = True
        elif arg == '--csv':
            export_csv_flag = True
        elif arg == '--reference':
            create_ref_flag = True
        elif arg == '--window':
            if i + 1 < len(sys.argv):
                window_size = int(sys.argv[i + 1])
                i += 1
        elif arg == '--step':
            if i + 1 < len(sys.argv):
                step = int(sys.argv[i + 1])
                i += 1
        elif arg == '--find':
            if i + 1 < len(sys.argv):
                find_hash = sys.argv[i + 1]
                i += 1
        elif not arg.startswith('--'):
            filepaths.append(arg)
        i += 1
    
    # Создаём анализатор
    analyzer = GenomePassport(window_size=window_size, step=step, fast_mode=fast_mode)
    
    # Режим поиска
    if find_hash:
        print(f"\n🔍 TSP-поиск ближайшего родственника для хеша: {find_hash[:16]}...")
        
        if not os.path.exists('window_resonance_cache.db'):
            print("❌ База не найдена. Сначала создайте паспорта.")
            return
        
        results = analyzer.find_nearest_tsp(find_hash, top_k=5)
        
        if results:
            print("\n🎯 Ближайшие родственники:")
            for name, distance, jaccard in results:
                print(f"  {name}: Jaccard={jaccard:.6f}, Distance={distance:.6f}")
        else:
            print("❌ Не найдено совпадений")
        
        return
    
    if len(filepaths) < 2:
        print("❌ Нужно минимум 2 FASTA файла")
        return
    
    # Загрузка
    analyzer.load_genomes(filepaths)
    
    if len(analyzer.genomes) < 2:
        print("❌ Нужно минимум 2 генома")
        return
    
    # Создание паспортов
    print(f"\n🧬 Создание паспортов (режим: {'FAST' if fast_mode else 'FULL'})...")
    for name, seq in analyzer.genomes.items():
        analyzer.create_passport(name, seq)
    
    # Сравнение
    print("\n🔬 Сравнение геномов...")
    results = analyzer.compare_all()
    
    # Вывод
    print("\n🎯 Результаты:")
    print("=" * 60)
    for r in results:
        print(f"\n{r['pair']}:")
        print(f"  Идентичных окон: {r['identical_ratio']:.2%}")
        print(f"  Jaccard: {r['jaccard']:.4f}")
        if not fast_mode:
            print(f"  Средний резонанс: {r['avg_resonance']:.4f}")
        print(f"  🧬 ИНДЕКС РОДСТВА: {r['kinship_index']:.4f}")
        
        if r['kinship_index'] > 0.85:
            interpretation = "Однояйцевые близнецы"
        elif r['kinship_index'] > 0.45:
            interpretation = "Родитель-ребёнок или сиблинги"
        elif r['kinship_index'] > 0.20:
            interpretation = "Двоюродные родственники"
        elif r['kinship_index'] > 0.10:
            interpretation = "Отдалённое родство"
        else:
            interpretation = "Неродственные"
        print(f"  📌 {interpretation}")
    
    # Эталон популяции
    if create_ref_flag:
        analyzer.create_reference()
        
        print("\n📊 Сравнение с эталоном:")
        for name in analyzer.genomes:
            ref_result = analyzer.compare_to_reference(name)
            if ref_result:
                print(f"  {name}: отклонение={ref_result['deviation']:.4f} ({ref_result['interpretation']})")
    
    # Визуализация
    analyzer.plot_kinship_matrix(results)
    
    # CSV экспорт
    if export_csv_flag:
        analyzer.export_csv(results)
    
    # Сохранение паспортов
    print("\n💾 Сохранение...")
    analyzer.save_passports()
    
    print("\n✅ Анализ завершён!")

if __name__ == "__main__":
    main()