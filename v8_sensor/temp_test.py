import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality

p = Personality.load('src/rizoma/data/personalities/p016_full.json')

print('='*60)
print('ТСТ    (посев + тексты)')
print('='*60)
print(f'ихрей: {len(p.vortices)}')
print(f'од: {len(p.h_field)}')
print()

questions = [
    'то такое вихрь?',
    'то такое квантовый конденсат?',
    'то такое алхимия?',
    'ак работает диалог?',
    'то такое модель?',
]

for q in questions:
    print(f'❓ {q}')
    r = p.process(q)
    print(f'   ода: {r["mode_used"]} (tau={r["tau"]:.2f})')
    print(f'   твет: {r["answer"][:300]}')
    print()
