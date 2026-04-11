import sys
import json
import os

sys.path.insert(0, 'src')

files = [
    'src/rizoma/data/personalities/p016_fractal_v16_1_checkpoint.json',
    'src/rizoma/data/personalities/p016_fractal_v16_1.json'
]

print("=" * 60)
print("  Я H")
print("=" * 60)

for f in files:
    if not os.path.exists(f):
        print(f'\n❌ айл не найден: {f}')
        continue
    
    size_mb = os.path.getsize(f) / 1024 / 1024
    print(f'\n📁 {f}')
    print(f'   азмер: {size_mb:.1f} ')
    
    try:
        with open(f, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        
        modes_count = len(data.get('h_field', []))
        print(f'   ✅ JSON валиден! од: {modes_count}')
        
        if modes_count > 0:
            m = data['h_field'][0]
            print(f'   📝 ример: tau={m.get("tau", "?")}, scale={m.get("scale", "?")}, complexity={m.get("complexity", "?")}')
            
    except json.JSONDecodeError as e:
        print(f'   ❌ JSON ТЫ! шибка: {e}')
    except Exception as e:
        print(f'   ❌ шибка: {e}')

print("\n" + "=" * 60)
