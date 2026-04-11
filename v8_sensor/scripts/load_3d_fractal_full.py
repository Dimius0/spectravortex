#!/usr/bin/env python3
"""
3D-ФРАКТАЛЬНЫЙ ЗАГРУЗЧИК (ПОЛНАЯ ВЕРСИЯ v2)
- Каждое слово → спектр (τ + гармоники)
- Каждое слово → 3D-координаты (τ, δ, θ)
- Иерархия строится ОДНОВРЕМЕННО с загрузкой
- Порог слияния мод: 0.9
- Сохранение после каждого файла
- Сразу 3D-резонанс при добавлении мод
"""
import sys
import os
import re
import math
import json
import time
from collections import defaultdict
from pdf2image import convert_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality, SpectralMode

# ========== НАСТРОЙКА ==========
SOURCE_PATH = r"C:\Users\Dim\Documents\vmms_texts\russian_classics"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')

# Параметры
MAX_SPECTRUM_SIZE = 10          # хранить только топ-10 τ в спектре
RESONANCE_3D_WEIGHTS = {          # веса для 3D-резонанса
    "tau": 1.0,
    "delta": 10.0,
    "theta": 1.0
}
# ===============================

print("="*70)
print("🌀 3D-ФРАКТАЛЬНЫЙ ЗАГРУЗЧИК v2")
print(" Иерархия строится одновременно с загрузкой")
print(" Порог слияния мод: 0.9")
print("="*70)

start_time = time.time()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def extract_text_from_pdf(filepath):
    """Извлекает текст из PDF с обработкой ошибок"""
    try:
        images = convert_from_path(filepath, dpi=150, poppler_path=POPPLER_PATH)
        text_parts = []
        total_pages = len(images)
        for i, img in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(img, lang='rus+eng', timeout=60)
                if page_text.strip():
                    text_parts.append(page_text)
            except Exception as e:
                print(f"      ⚠️ Страница {i+1}/{total_pages}: {e}")
                continue
        return "\n\n".join(text_parts) if text_parts else None
    except Exception as e:
        print(f"   ⚠️ Ошибка PDF: {e}")
        return None

def extract_text_from_txt(filepath):
    """Извлекает текст из TXT/MD"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(filepath, 'r', encoding='cp1251') as f:
                return f.read()
        except:
            return None

def compute_delta(text: str) -> float:
    """
    Специализация: 0 (общее) → 1 (узкое)
    """
    text_lower = text.lower()
    
    special_terms = [
        "∇⁴ψ", "∇⁴", "бигармонический", "вихрь", "топологический",
        "квантовый", "фуркация", "спектральный", "резонанс",
        "фрактальный", "гомология", "эмерджентный", "квант",
        "запутанность", "суперпозиция", "коллапс", "символ",
        "алхимия", "сера", "ртуть", "соль", "превращение",
        "дед", "внук", "диалог", "вопрос", "ответ",
        "формула", "уравнение", "теорема", "доказательство",
        "эксперимент", "наблюдение", "гипотеза", "теория"
    ]
    
    count = sum(1 for t in special_terms if t in text_lower)
    return min(1.0, count / 5)

def compute_theta(text: str) -> float:
    """
    Аспект (0–2π):
    0      — определение/суть
    π/2    — свойства/характеристики
    π      — применение/использование
    3π/2   — история/развитие
    """
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["определение", "что такое", "суть", "смысл", "называется", "понятие"]):
        return 0.0
    if any(w in text_lower for w in ["свойство", "характеристика", "особенность", "параметр", "свойства"]):
        return math.pi / 2
    if any(w in text_lower for w in ["применение", "использование", "технология", "практика", "применяется"]):
        return math.pi
    if any(w in text_lower for w in ["история", "развитие", "открытие", "впервые", "происхождение", "кто создал"]):
        return 3 * math.pi / 2
    
    return 0.0

def get_dominant_tau(spectrum):
    """Возвращает доминирующую τ из спектра"""
    if not spectrum:
        return 5.0
    best_tau = 5.0
    best_amp = 0.0
    for tau_key, amp in spectrum.items():
        tau = float(tau_key) if isinstance(tau_key, str) else tau_key
        if amp > best_amp:
            best_amp = amp
            best_tau = tau
    return best_tau

def compute_block_tau(p, words: list, block: str) -> float:
    """Вычисляет τ блока через словарь или эвристику"""
    if hasattr(p, 'word_spectrum') and p.word_spectrum:
        total = 0.0
        count = 0
        for w in words:
            if w in p.word_spectrum:
                total += get_dominant_tau(p.word_spectrum[w])
                count += 1
        if count > 0:
            return total / count
    
    length_factor = min(1.0, len(block) / 200)
    complexity = len(set(words)) / max(10, len(words))
    return max(3.0, min(9.0, 5.0 + length_factor * 2 + complexity * 1.5))

def resonance_3d(p, tau1, delta1, theta1, tau2, delta2, theta2, width=1.0):
    """3D-резонанс"""
    dt = abs(tau1 - tau2) * RESONANCE_3D_WEIGHTS["tau"] / width
    dd = abs(delta1 - delta2) * RESONANCE_3D_WEIGHTS["delta"] / width
    dth = min(abs(theta1 - theta2), 2*math.pi - abs(theta1 - theta2)) * RESONANCE_3D_WEIGHTS["theta"] / width
    return 1.0 / (1.0 + dt + dd + dth)

def update_word_spectrum_with_hierarchy(p, word: str, tau: float, amplitude: float = 0.3):
    """Обновляет спектр слова и сразу строит иерархию"""
    # 1. Обновляем спектр
    if word not in p.word_spectrum:
        p.word_spectrum[word] = {}
    
    old = p.word_spectrum[word].get(tau, 0)
    p.word_spectrum[word][tau] = old * 0.7 + amplitude * 0.3
    
    # Добавляем гармоники
    for h in [2.0, 3.0, 1.5, 0.5, 0.333, 0.666]:
        ht = tau * h
        if 3.0 <= ht <= 9.0:
            harmonic_amp = amplitude * 0.3 / h
            old_h = p.word_spectrum[word].get(ht, 0)
            p.word_spectrum[word][ht] = old_h * 0.7 + harmonic_amp * 0.3
    
    # Ограничиваем спектр
    if len(p.word_spectrum[word]) > MAX_SPECTRUM_SIZE:
        sorted_items = sorted(p.word_spectrum[word].items(), key=lambda x: x[1], reverse=True)
        p.word_spectrum[word] = dict(sorted_items[:MAX_SPECTRUM_SIZE])
    
    # 2. Строим иерархию (ищем родителя среди уже загруженных слов)
    if word not in p.word_parent and len(p.word_spectrum) > 1:
        word_tau = get_dominant_tau(p.word_spectrum[word])
        word_delta = compute_delta(word)
        word_theta = compute_theta(word)
        
        best_parent = None
        best_resonance = 0.0
        
        for existing, spectrum in p.word_spectrum.items():
            if existing == word:
                continue
            existing_tau = get_dominant_tau(spectrum)
            existing_delta = compute_delta(existing)
            existing_theta = compute_theta(existing)
            
            res = resonance_3d(p, word_tau, word_delta, word_theta,
                               existing_tau, existing_delta, existing_theta, 1.0)
            
            if res > best_resonance and res > 0.3:
                best_resonance = res
                best_parent = existing
        
        if best_parent:
            p.word_parent[word] = best_parent
            if best_parent not in p.word_children:
                p.word_children[best_parent] = []
            if word not in p.word_children[best_parent]:
                p.word_children[best_parent].append(word)

# ========== ОСНОВНОЙ ЦИКЛ ЗАГРУЗКИ ==========

# Очищаем поле H перед загрузкой
p = Personality(id="p016", name="VMMS Theory")
p.word_spectrum = {}
p.word_parent = {}
p.word_children = {}
p.word_freq = defaultdict(int)
p.focus = {"tau": 6.2, "delta": 0.0, "theta": 0.0, "width": 1.0, "history": []}

print(f"\n✨ Создано новое поле H")

total_blocks = 0
total_files = 0
files_processed = []

for filename in os.listdir(SOURCE_PATH):
    filepath = os.path.join(SOURCE_PATH, filename)
    ext = os.path.splitext(filename)[1].lower()
    
    print(f"\n📄 {filename}")
    
    if ext == '.pdf':
        content = extract_text_from_pdf(filepath)
    elif ext in ['.txt', '.md']:
        content = extract_text_from_txt(filepath)
    else:
        print(f"   ⚠️ Неподдерживаемый формат: {ext}")
        continue
    
    if not content or len(content) < 100:
        print(f"   ⚠️ Не удалось извлечь текст")
        continue
    
    blocks = re.split(r'\n\s*\n', content)
    print(f"   Блоков: {len(blocks)}")
    
    file_blocks = 0
    file_words = set()
    
    for i, block in enumerate(blocks):
        block = block.strip()
        if len(block) < 100:
            continue
        
        words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{4,}\b', block.lower())
        file_words.update(words)
        
        for w in words:
            p.word_freq[w] += 1
        
        block_tau = compute_block_tau(p, words, block)
        block_delta = compute_delta(block)
        block_theta = compute_theta(block)
        
        # Обновляем спектры слов и иерархию
        for w in set(words):
            update_word_spectrum_with_hierarchy(p, w, block_tau, 0.3)
        
        # Создаём моду
        mode = SpectralMode(
            tau=block_tau,
            delta=block_delta,
            theta=block_theta,
            amplitude=0.15,
            content=block[:1500],
            trace_type="text",
            themes=["fractal_3d"],
            trace_id=f"block_{total_files}_{file_blocks}"
        )
        
        # Добавляем с 3D-резонансом (порог 0.9)
        best_match = None
        best_resonance = 0.0
        for existing in p.h_field:
            res = resonance_3d(p, mode.tau, mode.delta, mode.theta,
                               existing.tau, existing.delta, existing.theta,
                               p.focus["width"])
            if res > best_resonance:
                best_resonance = res
                best_match = existing
        
        if best_match and best_resonance > 0.9:
            best_match.register_use(resonance=best_resonance, success=True)
            print(f" 📈 Усилена {best_match.trace_id} (3D-res={best_resonance:.2f})")
        else:
            p.h_field.append(mode)
            print(f" ✨ Новая мода: τ={mode.tau:.2f}, δ={mode.delta:.2f}, θ={mode.theta:.2f}")
        
        file_blocks += 1
        total_blocks += 1
        
        if file_blocks % 100 == 0:
            print(f"   Обработано блоков: {file_blocks}")
    
    print(f"   → {file_blocks} блоков, {len(file_words)} уникальных слов")
    total_files += 1
    files_processed.append(filename)
    
    p.save(OUTPUT_PATH)
    print(f"   💾 Сохранено (спектров: {len(p.word_spectrum)}, мод: {len(p.h_field)})")
    
    elapsed = time.time() - start_time
    print(f"   ⏱️ Прошло: {elapsed/60:.1f} мин")

# ========== ФИНАЛЬНОЕ СОХРАНЕНИЕ ==========

p.save(OUTPUT_PATH)

# ========== ИТОГОВАЯ СТАТИСТИКА ==========

elapsed = time.time() - start_time

print("\n" + "="*70)
print("📊 ИТОГОВАЯ СТАТИСТИКА")
print("="*70)
print(f" Файлов обработано: {total_files}")
print(f" Блоков загружено: {total_blocks}")
print(f" Мод в поле H: {len(p.h_field)}")
print(f" Слов в 3D-словаре: {len(p.word_spectrum)}")
print(f" Слов с иерархией: {len(p.word_parent)}")
print(f" Всего уникальных слов (встречались): {len(p.word_freq)}")
print(f" Размер файла JSON: ~{os.path.getsize(OUTPUT_PATH)//1024} КБ")
print(f" Время выполнения: {elapsed/60:.1f} мин")

# Распределение τ в спектрах
tau_counts = defaultdict(int)
for spec in p.word_spectrum.values():
    for tau in spec.keys():
        t = float(tau) if isinstance(tau, str) else tau
        tau_counts[round(t, 1)] += 1

print(f"\n📈 Распределение τ в спектрах (топ-10):")
for tau, cnt in sorted(tau_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"   τ≈{tau:.1f}: {cnt} вхождений")

# Распределение мод по δ
delta_counts = defaultdict(int)
theta_counts = defaultdict(int)
for mode in p.h_field:
    delta_counts[round(mode.delta, 2)] += 1
    theta_counts[round(mode.theta, 1)] += 1

print(f"\n📈 Распределение мод по δ:")
for delta, cnt in sorted(delta_counts.items(), reverse=True)[:10]:
    print(f"   δ≈{delta:.2f}: {cnt} мод")

print(f"\n📈 Распределение мод по θ:")
for theta, cnt in sorted(theta_counts.items())[:10]:
    print(f"   θ≈{theta:.1f}: {cnt} мод")

# Показываем примеры иерархии
if p.word_parent:
    print(f"\n🌳 ПРИМЕРЫ ИЕРАРХИИ (первые 15):")
    for word, parent in list(p.word_parent.items())[:15]:
        print(f"   {word} → {parent}")

print("\n" + "="*70)
print("✅ 3D-ФРАКТАЛЬНЫЙ ЗАГРУЗЧИК v2 ЗАВЕРШЁН")
print("="*70)
print("\n🦌 Теперь у каждого слова есть:")
print("   • спектр (τ + гармоники)")
print("   • δ (специализация)")
print("   • θ (аспект)")
print("   • иерархия (родитель-дети) — построена одновременно с загрузкой")
print("\n🦌 У каждой моды есть:")
print("   • τ, δ, θ — 3D-координаты")
print("   • резонанс с другими модами в 3D (порог слияния 0.9)")
print(f"\n💾 Сохранено в: {OUTPUT_PATH}")