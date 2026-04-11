import sys
import time
from datetime import datetime
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

print("=" * 60)
print(" СХЯ ")
print("=" * 60)

# агружаем текущее поле
p = Personality.load('src/rizoma/data/personalities/p016_fractal_v17_0_20260403_173544.json')

# роверяем узлы
if hasattr(p.resonance_engine, 'topology'):
    knots = len(p.resonance_engine.topology.nodes)
    print(f'злов в загруженном поле: {knots}')
else:
    print('Топология не найдена')
    knots = 0

# Сохраняем копию
fname = f'src/rizoma/data/personalities/test_knots_{datetime.now().strftime("%H%M%S")}.json'
p.save(fname)
print(f'Сохранена копия: {fname}')

# роверяем, что сохранилось
p2 = Personality.load(fname)
if hasattr(p2.resonance_engine, 'topology'):
    knots2 = len(p2.resonance_engine.topology.nodes)
    print(f'злов в сохранённой копии: {knots2}')
else:
    print('Топология не найдена в копии')

print("=" * 60)
