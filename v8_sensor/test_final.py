import sys
sys.path.insert(0, 'src')
from rizoma.personality import FieldH

p = FieldH.load('src/rizoma/data/personalities/p016_full.json')

print('='*60)
print('ТСТ ТТ С ')
print('='*60)
print(f'Слов в поле: {len(p.vortices)}')
print(f'од: {len(p.h_field)}')
print(f'Символов в алфавите: {len(p.char_tau)}')
print()

# Смотрим несколько слов
test_words = ['вихрь', 'модель', 'алхимия', 'диалог', 'война', 'мир']
print('Спектры слов:')
for w in test_words:
    if w in p.vortices:
        v = p.vortices[w]
        dom = v.get_dominant_tau()
        print(f'  {w}: τ≈{dom:.2f}, ампл={v.amplitude:.2f}, спектр={len(v.spectrum)} частот')
    else:
        print(f'  {w}: нет в поле')
print()

# опросы
questions = [
    'то такое вихрь?',
    'то такое модель?',
    'то такое алхимия?',
    'то такое диалог?',
]

for q in questions:
    print(f'❓ {q}')
    r = p.process(q)
    print(f'   ода: {r["mode_used"]} (τ={r["tau"]:.2f})')
    print(f'   твет: {r["answer"][:300]}')
    print()
