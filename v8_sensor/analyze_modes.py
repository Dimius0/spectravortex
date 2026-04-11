import sys
sys.path.insert(0, 'src')
from rizoma.personality import Personality

p = Personality.load('src/rizoma/data/personalities/p016_full.json')

print('='*60)
print(' ')
print('='*60)
print(f'сего мод: {len(p.h_field)}')
print()

# оказываем все моды
for i, mode in enumerate(p.h_field):
    print(f'{i+1}. {mode.trace_id}')
    print(f'   tau={mode.tau:.2f}, delta={mode.delta:.2f}, theta={mode.theta:.2f}')
    print(f'   amplitude={mode.amplitude:.2f}, usage={mode.usage_count}')
    print(f'   content: {mode.content[:80]}...')
    print()

# роверяем распределение по tau
tau_counts = {}
for mode in p.h_field:
    t = round(mode.tau, 1)
    tau_counts[t] = tau_counts.get(t, 0) + 1

print('='*60)
print('С  TAU')
print('='*60)
for t in sorted(tau_counts.keys()):
    print(f'  tau={t:.1f}: {tau_counts[t]} мод')

# роверяем наличие физики, алхимии, диалога
phys_modes = [m for m in p.h_field if 5.1 < m.tau < 5.3]
alch_modes = [m for m in p.h_field if 6.5 < m.tau < 6.7]
dial_modes = [m for m in p.h_field if 8.1 < m.tau < 8.3]

print()
print(f'од с tau≈5.2 (физика): {len(phys_modes)}')
print(f'од с tau≈6.6 (алхимия): {len(alch_modes)}')
print(f'од с tau≈8.2 (диалог): {len(dial_modes)}')
