# scripts/load_classics.py
"""
Загрузка русской классики (Пушкин, Толстой и др.)
Автоопределение τ через словарь
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from rizoma.personality import Personality, SpectralMode

CLASSICS_PATH = r"C:\Users\Dim\Documents\vmms_texts\russian_classics"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'rizoma', 'data', 'personalities', 'p016_full.json')

print("="*60)
print("📖 ЗАГРУЗКА РУССКОЙ КЛАССИКИ")
print(" Автоопределение τ через словарь")
print("="*60)

p = Personality.load(OUTPUT_PATH)
print(f"\n📂 Загружено поле H: {len(p.h_field)} мод, {len(p.word_tau)} слов")

def extract_text(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        try:
            with open(filepath, 'r', encoding='cp1251') as f:
                return f.read()
        except:
            return None

def fallback_tau(block: str) -> float:
    length_factor = min(1.0, len(block) / 200)
    words_set = set(block.split())
    complexity = len(words_set) / max(10, len(block.split()))
    return max(3.0, min(9.0, 5.0 + length_factor * 2 + complexity * 1.5))

total_blocks = 0
total_files = 0

for filename in os.listdir(CLASSICS_PATH):
    if not filename.endswith(('.txt', '.md')):
        continue
    
    filepath = os.path.join(CLASSICS_PATH, filename)
    print(f"\n📄 {filename}")
    
    content = extract_text(filepath)
    if not content or len(content) < 100:
        print(f"   ⚠️ Не удалось прочитать")
        continue
    
    # Разбиваем на главы/абзацы
    blocks = re.split(r'\n\s*\n', content)
    print(f"   Блоков: {len(blocks)}")
    
    file_blocks = 0
    for i, block in enumerate(blocks):
        block = block.strip()
        if len(block) < 100:
            continue
        
        # Автоопределение τ
        tau = p.phrase_tau(block)
        if abs(tau - 5.0) < 0.1:
            tau = fallback_tau(block)
        
        mode = SpectralMode(
            tau=tau,
            amplitude=0.15,
            content=block[:1500],
            trace_type="classics",
            themes=["russian_lit", "classics"],
            trace_id=f"classic_{total_files}_{i}"
        )
        p.add_to_h_field(mode)
        file_blocks += 1
        total_blocks += 1
    
    print(f"   → {file_blocks} блоков загружено")
    total_files += 1
    p.save(OUTPUT_PATH)
    print(f"   💾 Сохранено")

print("\n" + "="*60)
print("📊 ИТОГ")
print("="*60)
print(f" Файлов обработано: {total_files}")
print(f" Блоков загружено: {total_blocks}")
print(f" Мод в поле H: {len(p.h_field)}")
print(f" Слов в словаре: {len(p.word_tau)}")

print(f"\n Распределение τ в словаре:")
taus = {}
for w, t in p.word_tau.items():
    taus[round(t, 1)] = taus.get(round(t, 1), 0) + 1
for t, c in sorted(taus.items()):
    print(f"   τ≈{t:.1f}: {c} слов")

print("\n🦌 Классика загружена!")