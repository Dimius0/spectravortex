import sys
import math
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality, SpectralMode
from rizoma.fractal_split_v16_1 import fractal_split
from rizoma.complexity_utils import detect_complexity

print("=" * 70)
print("🌀     H v17.0")
print("=" * 70)

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_20260404_210354.json')
print(f"📂 оле загружено: {len(p.h_field)} мод")

with open(r'C:\Users\Dim\Documents\vmms_texts\russian_classics\conversations_clean2.txt', 'r', encoding='utf-8') as f:
    content = f.read()
print(f"📄 иалоги: {len(content)/1024/1024:.1f} ")

blocks = fractal_split(content)
print(f"🔪 рактальных блоков: {len(blocks)}")

added = 0
for i, block_data in enumerate(blocks):
    block = block_data['content']
    scale = block_data['scale']
    position = block_data['position']
    if len(block) < 30:
        continue
    
    theta = position * 2 * math.pi
    phi = 16.0 / 33.0 * math.pi
    r = 16.0 / 10.0
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)
    
    mode = SpectralMode(
        tau=16.0,
        amplitude=0.15,
        content=block[:1500],
        trace_id=f'dialogue_{scale}_{i}',
        themes=['dialogue', f'scale_{scale}'],
        scale=scale,
        complexity=detect_complexity(block)
    )
    p.add_to_h_field(mode)
    added += 1
    if added % 5000 == 0:
        print(f"  обавлено блоков: {added}")

print(f"✅ обавлено мод: {added}")
print(f"📊 сего мод в поле: {len(p.h_field)}")

p.save('src/rizoma/data/personalities/p016_fractal_v17_0_with_dialogues.json')
print("💾 Сохранено: p016_fractal_v17_0_with_dialogues.json")
