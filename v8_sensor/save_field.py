import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality
from datetime import datetime

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_auto_20260402_1143.json')

fname = f'src/rizoma/data/personalities/p016_fractal_v16_auto_{datetime.now().strftime("%Y%m%d_%H%M")}_RUNNING.json'
p.save(fname)

stats = p.get_endogenous_stats()
print(f'✅ Сохранено: {fname}')
print(f'   оды: {len(p.h_field)} | злы: {stats.get("knots_created", 0)}')
