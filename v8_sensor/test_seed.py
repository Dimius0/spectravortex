import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality

p = Personality.load('src/rizoma/data/personalities/p016_full.json')

print('='*60)
print('ТСТ: слова из посева')
print('='*60)
print(f'ихрей: {len(p.vortices)}')
print(f'од: {len(p.h_field)}')
print()

# Слова из seed-посева
test_words = ['модель', 'система', 'процесс', 'структура', 'энергия']

print('Слова в поле:')
for w in test_words:
    if w in p.vortices:
        v = p.vortices[w]
        print(f'  {w}: tau={v.get_dominant_tau():.2f}, delta={v.delta:.2f}, theta={v.theta:.2f}')
    else:
        print(f'  {w}: HEТ')
print()

questions = [
    'то такое модель?',
    'то такое система?',
    'то такое процесс?',
    'то такое структура?',
]

for q in questions:
    print(f'? {q}')
    r = p.process(q)
    print(f'   ода: {r["mode_used"]} (tau={r["tau"]:.2f})')
    print(f'   твет: {r["answer"][:200]}')
    print()
