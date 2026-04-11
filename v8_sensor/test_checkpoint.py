import sys
sys.path.insert(0, 'src')
from rizoma.personality_v17_2 import Personality

print('=' * 60)
print('🧪 ТСТ v17.2  Т (целый файл)')
print('=' * 60)

# агружаем целый чекпоинт
p = Personality()
p.load('src/rizoma/data/personalities/p016_fractal_v16_1_checkpoint.json')

print(f'\n✅ агружено: {len(p.h_field)} мод')

# Смотрим статистику по масштабам
scales = {}
for mode in p.h_field:
    s = mode.scale
    scales[s] = scales.get(s, 0) + 1

print(f'\n📊 С  СШТ:')
for s in sorted(scales.keys()):
    print(f'   scale={s:5.1f}: {scales[s]:6d} мод')

# Смотрим complexity
comp = {}
for mode in p.h_field:
    c = mode.complexity
    comp[c] = comp.get(c, 0) + 1

print(f'\n📊 С  COMPLEXITY:')
names = {1: 'бытовой', 2: 'научный', 3: '', 4: 'метафорический'}
for c in sorted(comp.keys()):
    print(f'   complexity={c} ({names.get(c, "?")}): {comp[c]:6d} мод')

print(f'\n📊 Состояние поля:')
state = p.get_state()
print(f'   огерентность: {state["coherence"]:.4f}')
print(f'   τ диапазон: {state["tau_min"]}-{state["tau_max"]}')
print(f'   злов: {state["total_nodes"]}')
print(f'   уркаций: {state["total_furcations"]}')

print('\n✅ оле готово к эндогенному циклу')
print('=' * 60)
