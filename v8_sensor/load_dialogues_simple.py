import sys
import glob
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality, SpectralMode
from rizoma.complexity_utils import detect_complexity

print("=" * 70)
print("🌀   (10 частей)")
print("=" * 70)

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_20260404_210354.json')
print(f"📂 оле загружено: {len(p.h_field)} мод")

# щем файлы в папке russian_classics
chunk_files = glob.glob(r'C:\Users\Dim\Documents\vmms_texts\russian_classics\part_*.txt')
chunk_files.sort()
print(f"📁 айдено файлов: {len(chunk_files)}")

total_added = 0
for fname in chunk_files:
    print(f"\n📄 бработка: {fname.split('\\')[-1]}")
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"   азмер: {len(content)/1024:.0f} ")
    
    chunk_size = 3000
    blocks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    print(f"   локов: {len(blocks)}")
    
    added = 0
    for i, block in enumerate(blocks):
        if len(block) < 100:
            continue
        mode = SpectralMode(
            tau=16.0,
            amplitude=0.15,
            content=block,
            trace_id=f'dialogue_{total_added + i}',
            themes=['dialogue'],
            scale=10.0,
            complexity=detect_complexity(block[:500])
        )
        p.add_to_h_field(mode)
        added += 1
    
    print(f"   ➕ обавлено мод: {added}")
    total_added += added
    print(f"   📊 сего мод: {len(p.h_field)}")

print(f"\n✅ С добавлено мод: {total_added}")
print(f"📊 инальное число мод: {len(p.h_field)}")

p.save('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues_v2.json')
print("💾 Сохранено: p016_fractal_v17_0_with_dialogues_v2.json")
