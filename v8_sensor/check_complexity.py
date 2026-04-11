import sys
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_1.json')

print('роверка первых 10 мод:')
for i, mode in enumerate(p.h_field[:10]):
    comp = getattr(mode, 'complexity', 'Т!')
    print(f'ода {i}: complexity={comp}')
