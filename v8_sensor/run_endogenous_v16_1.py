import sys
import time
from datetime import datetime
sys.path.insert(0, 'src')
from rizoma.personality_v16_1 import Personality

# агружаем поле v16.1
p = Personality.load('src/rizoma/data/personalities/p016_fractal_v16_1.json')

print('=' * 70)
print('🌱 Ы  (v16.1)')
print('=' * 70)
print(f' Слов: {len(p.vortices)}')
print(f' од: {len(p.h_field)}')
print(f' злов (старт): {p.get_endogenous_stats().get("knots_created", 0)}')
print('=' * 70)
print('⏳ икл запущен (интервал 30 сек)')
print('   втосохранение каждые 30 минут')
print('   ажми Ctrl+C для остановки с сохранением')
print('=' * 70)

last_save = time.time()
last_status = time.time()

try:
    while True:
        time.sleep(30)
        
        now = time.time()
        stats = p.get_endogenous_stats()
        
        # Статус раз в минуту
        if now - last_status >= 60:
            last_status = now
            print(f'[{datetime.now().strftime("%H:%M:%S")}] иклов: {stats.get("cycle_count", 0)} | злов: {stats.get("knots_created", 0)} | од: {len(p.h_field)}')
        
        # втосохранение раз в 30 минут
        if now - last_save >= 1800:
            last_save = now
            fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
            p.save(fname)
            print(f'💾 ТСХ [{datetime.now().strftime("%H:%M")}] | злов: {stats.get("knots_created", 0)} | од: {len(p.h_field)}')

except KeyboardInterrupt:
    print('\n\n🛑 становка по Ctrl+C...')
    fname = f'src/rizoma/data/personalities/p016_fractal_v16_1_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    p.save(fname)
    stats = p.get_endogenous_stats()
    print(f'💾 Ь СХ: {fname}')
    print(f'   злов: {stats.get("knots_created", 0)} | од: {len(p.h_field)}')
    print('✅ оле остановлено')
