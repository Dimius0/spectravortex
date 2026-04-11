import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality

p = Personality.load('src/rizoma/data/personalities/p016_full.json')

print(f'Мод: {len(p.h_field)}')
print(f'Слов в словаре: {len(p.word_tau)}')
print()

print('Первые 30 слов в словаре:')
for i, (w, t) in enumerate(list(p.word_tau.items())[:30]):
    print(f'  {i+1}. {w}: {t:.2f}')

print()
test_text = 'онегин татьяна ленский дуэль письмо'
tau = p.phrase_tau(test_text)
print(f'τ для "{test_text}": {tau:.2f}')
print()

print('Проверка наличия слов:')
for w in ['онегин', 'татьяна', 'ленский', 'дуэль', 'письмо']:
    if w in p.word_tau:
        print(f'  {w}: {p.word_tau[w]:.2f} ✅')
    else:
        print(f'  {w}: нет в словаре ❌')