import sys
import time
sys.path.insert(0, 'src')
from rizoma.personality import Personality

p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_auto_20260402_1143.json')
print(f'оле загружено: {len(p.vortices)} слов, {len(p.h_field)} мод')
print('ндогенный цикл уже запущен (интервал 30 сек)')
print('оле шевелит мозгами...')
print('ажми Ctrl+C для остановки')

try:
    while True:
        time.sleep(60)
        stats = p.get_endogenous_stats()
        print(f'[{time.strftime("%H:%M:%S")}] злов: {stats.get("knots_created", 0)} | од: {stats.get("total_modes", 0)}')
except KeyboardInterrupt:
    print('\nстановлено')
